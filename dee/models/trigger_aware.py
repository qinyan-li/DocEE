import math
import copy
import random
from collections import defaultdict

import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl
import dgl.nn.pytorch as dglnn
from loguru import logger

from dee.models.git import RelGraphConvLayer # import GCN from git
from dee.models.lstmmtl2complete_graph import LSTMMTL2CompleteGraphModel
from dee.modules import (
    MLP,
    MentionTypeEncoder,
    SentencePosEncoder,
    EventTableForSigmoidMultiArgRel,
    MentionTypeConcatEncoder,
    get_doc_arg_rel_info_list,
    directed_trigger_graph_decode,
    directed_trigger_graph_incremental_decode,
    mlp,
    normalize_adj,
    GAT,
    transformer,
    AttentiveReducer,
)
from dee.utils import closest_match, assign_role_from_gold_to_comb


class TriggerAwarePrunedCompleteGraph(LSTMMTL2CompleteGraphModel):
    def __init__(self, config, event_type_fields_pairs, ner_model):
        super().__init__(config, event_type_fields_pairs, ner_model=ner_model)

        if self.config.use_token_role: # qy: 使用NER出来的entity类型 当前true
            if config.ment_feature_type == "concat": # qy: 当前 concat
                self.ment_type_encoder = MentionTypeConcatEncoder(
                    config.ment_type_hidden_size, # qy: 32
                    len(config.ent_type2id), # qy: ChFin为26 
                    dropout=config.dropout,
                )
                self.hidden_size = config.hidden_size + config.ment_type_hidden_size # qy: 768 + 32 = 800
            else:
                self.ment_type_encoder = MentionTypeEncoder(
                    config.hidden_size, config.num_entity_labels, dropout=config.dropout
                )
                self.hidden_size = config.hidden_size
        else:
            self.hidden_size = config.hidden_size

        # qy: 新加AWA 因为要统一hidden_size
        if self.config.seq_reduce_type == "AWA":
            self.doc_token_reducer = AttentiveReducer(
                self.hidden_size, dropout=config.dropout
            )
            self.span_token_reducer = AttentiveReducer(
                self.hidden_size, dropout=config.dropout
            )
            self.span_mention_reducer = AttentiveReducer(
                self.hidden_size, dropout=config.dropout
            )
        else:
            assert self.config.seq_reduce_type in {"MaxPooling", "MeanPooling"}
        # qy: 新加的transformer层 
        if self.config.use_doc_enc:
            # get doc-level context information for every mention and sentence
            self.doc_context_encoder = transformer.make_transformer_encoder(
                config.num_tf_layers, # 4
                self.hidden_size,
                ff_size=config.ff_size,# 1024
                dropout=config.dropout,
            )
        self.start_lstm = (
            self.end_lstm
        ) = self.start_mlp = self.end_mlp = self.biaffine = None

        if self.config.use_span_lstm: # qy: 当前true
            self.span_lstm = nn.LSTM(
                self.hidden_size, # qy: 800
                self.hidden_size // 2, 
                num_layers=self.config.span_lstm_num_layer, # qy: =2
                bias=True,
                batch_first=True,
                dropout=self.config.dropout,
                bidirectional=True,
            )

        if self.config.mlp_before_adj_measure: # qy: 是否需要MLP来算adj mat. 否则用linear
            self.q_w = MLP(
                self.hidden_size, self.hidden_size, dropout=self.config.dropout
            )
            self.k_w = MLP(
                self.hidden_size, self.hidden_size, dropout=self.config.dropout
            )
        else:
            self.q_w = nn.Linear(self.hidden_size, self.hidden_size)
            self.k_w = nn.Linear(self.hidden_size, self.hidden_size)

        if self.config.use_mention_lstm: # qy: 当前false，实验里面true了
            self.mention_lstm = nn.LSTM(
                self.hidden_size, # qy: 800
                self.hidden_size // 2,
                num_layers=self.config.num_mention_lstm_layer, # qy: =1
                bias=True,
                batch_first=True,
                dropout=self.config.dropout,
                bidirectional=True,
            )

        # self.span_att = transformer.SelfAttention(
        #     self.hidden_size,
        #     dropout=self.config.dropout
        # )

        self.event_tables = nn.ModuleList( # qy：既预测事件类型也预测角色类型
            [
                EventTableForSigmoidMultiArgRel(
                    event_type,
                    field_types,
                    self.config.hidden_size,
                    self.hidden_size,
                    min_field_num,
                    use_field_cls_mlp=self.config.use_field_cls_mlp,
                    dropout=self.config.dropout,
                )
                for event_type, field_types, _, min_field_num in self.event_type_fields_pairs # qy: 从event_table中来的 （事件类型，角色名，——，每个事件最少需要的角色）
            ]
        )
        # qy: transformer ner
        self.sent_pos_encoder = SentencePosEncoder(
            config.hidden_size, max_sent_num=config.max_sent_num, dropout=config.dropout
        ) # 768
        
        self.use_git = config.use_git

        if config.use_git:
            ############################### from GIT ##########
            self.full_git = config.full_git
            if config.full_git:
                self.rel_name_lists =  ["m-m", "s-m", "s-s"]
            else:
                self.rel_name_lists =  ["m-m"]#, "s-m", "s-s"]
            self.gcn_layers = config.gcn_layer # qy: 3
            self.GCN_layers = nn.ModuleList(
                [
                    RelGraphConvLayer(
                        self.hidden_size, # qy: 改成了self.hidden_size 800 instead of config 768
                        self.hidden_size,
                        self.rel_name_lists,
                        num_bases=len(self.rel_name_lists), # qy: 有几种edge git有3种
                        activation=nn.ReLU(),
                        self_loop=True,
                        dropout=config.dropout,
                    )
                    for i in range(self.gcn_layers)
                ]
            )
            # different middle layers for sentences and mentions
            if config.full_git:
                self.middle_layer_sent = nn.Sequential(
                    nn.Linear(self.hidden_size * (config.gcn_layer + 1), self.hidden_size),
                    nn.ReLU(),
                    nn.Dropout(config.dropout),
                )
                self.middle_layer_ment = nn.Sequential(
                    nn.Linear(self.hidden_size * (config.gcn_layer + 1), self.hidden_size),
                    nn.ReLU(),
                    nn.Dropout(config.dropout),
                )
            else:
                self.middle_layer = nn.Sequential(
                    nn.Linear(self.hidden_size * (config.gcn_layer + 1), self.hidden_size),
                    nn.ReLU(),
                    nn.Dropout(config.dropout),
                )
            if config.full_git:
                self.sent_embedding = nn.Parameter(torch.randn(self.hidden_size))
            self.mention_embedding = nn.Parameter(torch.randn(self.hidden_size))
            #self.intra_path_embedding = nn.Parameter(torch.randn(self.hidden_size))
            #self.inter_path_embedding = nn.Parameter(torch.randn(self.hidden_size))

            ##############################################

            # dynamic loss ###
        self.dynamic_loss = config.dynamic_loss
        if config.dynamic_loss:
            #self.lambda_1 = nn.Parameter(torch.ones(1))
            #self.lambda_2 = nn.Parameter(torch.ones(1))
            self.lambda_1 = nn.Parameter(torch.tensor([1/self.config.loss_lambda]))
            #self.lambda_2 = 1. #nn.Parameter(torch.tensor([1.]))
            '''
            else:
                self.lambda_1 = self.config.loss_lambda # qy: 0.05
                self.lambda_2 = 1 - self.lambda_1
            '''


    # def pred_adj_mat_reorgnise(self, pred_adj_mat):
    #     """
    #     fill the diag to 1 and make sure the adj_mat is symmetric
    #     """
    #     adj_mat = pred_adj_mat
    #     if not self.config.directed_trigger_graph:
    #         adj_mat = torch.bitwise_and(adj_mat, adj_mat.T)
    #     adj_mat.fill_diagonal_(0)
    #     return adj_mat

    def get_arg_role_loss(self, arg_role_logits, role_types): #qy: 角色预测的loss 
        rt_multihot = torch.zeros_like(arg_role_logits, requires_grad=False)
        for ent_idx, roles in enumerate(role_types):
            if roles is None:
                continue
            for role in roles:
                rt_multihot[ent_idx, role] = 1
        # role_loss = F.binary_cross_entropy(arg_role_logits.reshape(-1), rt_multihot.reshape(-1), reduction='sum')
        role_loss = F.binary_cross_entropy(
            arg_role_logits.reshape(-1), rt_multihot.reshape(-1)
        )
        return role_loss

    def forward(
        self,
        doc_batch_dict,
        doc_features,
        train_flag=True,
        use_gold_span=False,
        teacher_prob=1,
        event_idx2entity_idx2field_idx=None,
        heuristic_type=None,
    ):
        self.losses = dict()

        # Using scheduled sampling to gradually transit to predicted entity spans
        if train_flag and self.config.use_scheduled_sampling:
            # teacher_prob will gradually decrease outside
            if random.random() < teacher_prob:
                use_gold_span = True
            else:
                use_gold_span = False

        # get doc token-level local context # qy: NER?
        (
            doc_token_emb_list, # qy: token embeddings
            doc_token_masks_list,
            doc_token_types_list, # qy: NER的预测结果 BIO标签
            doc_sent_emb_list, # qy: sentence embeddings?
            doc_sent_loss_list, # qy: loss?
        ) = self.get_local_context_info(
            doc_batch_dict,
            train_flag=train_flag,
            use_gold_span=use_gold_span,
        )

        # get doc feature objects
        ex_idx_list = doc_batch_dict["ex_idx"]
        doc_fea_list = [doc_features[ex_idx] for ex_idx in ex_idx_list]

        # get doc span-level info for event extraction
        doc_arg_rel_info_list = get_doc_arg_rel_info_list( # qy: 从刚刚预测出来的BIO标签得到span信息 etc?
            doc_token_types_list,
            doc_fea_list,
            self.event_type_fields_pairs,
            use_gold_span=use_gold_span,
            ent_fix_mode=self.config.ent_fix_mode,
        )

        if train_flag:
            doc_event_loss_list = []
            for batch_idx, ex_idx in enumerate(ex_idx_list):
                doc_event_loss_list.append(
                    self.get_loss_on_doc(
                        doc_token_emb_list[batch_idx],
                        doc_sent_emb_list[batch_idx],
                        doc_fea_list[batch_idx],
                        doc_arg_rel_info_list[batch_idx],
                        use_gold_adj_mat=use_gold_span,
                    )
                )
            mix_loss = self.get_mix_loss(
                doc_sent_loss_list, doc_event_loss_list, doc_arg_rel_info_list
            )
            self.losses.update({"loss": mix_loss})
            #print(self.losses)
            # return mix_loss
            return self.losses
        else:
            # return a list object may not be supported by torch.nn.parallel.DataParallel
            # ensure to run it under the single-gpu mode
            eval_results = []
            for batch_idx, ex_idx in enumerate(ex_idx_list):
                eval_results.append(
                    # self.get_gold_results_on_doc(
                    self.get_eval_on_doc(
                        doc_token_emb_list[batch_idx],
                        doc_sent_emb_list[batch_idx],
                        doc_fea_list[batch_idx],
                        doc_arg_rel_info_list[batch_idx],
                    )
                )
            return eval_results

    def get_doc_span_mention_emb(self, doc_token_emb, doc_arg_rel_info):
        """
        get all the mention representations by aggregating the token representations
        """
        if len(doc_arg_rel_info.mention_drange_list) == 0:
            #print("yesyesyes")
            doc_mention_emb = None
        else:
            #print("nonono")
            mention_emb_list = []
            for sent_idx, char_s, char_e in doc_arg_rel_info.mention_drange_list:
                mention_token_emb = doc_token_emb[
                    sent_idx, char_s:char_e, :
                ]  # [num_mention_tokens, hidden_size]
                if self.config.seq_reduce_type == "AWA":
                    #mention_emb = self.span_token_reducer(
                    #    mention_token_emb
                    #)  # [hidden_size]
                    mention_emb = mention_token_emb.max(dim=0)[0] # qy: 尝试只改后一个AWA 这个token-wise的还是用max pool
                elif self.config.seq_reduce_type == "MaxPooling": # qy: 目前是max pooling
                    mention_emb = mention_token_emb.max(dim=0)[0]
                elif self.config.seq_reduce_type == "MeanPooling":
                    mention_emb = mention_token_emb.mean(dim=0)
                else:
                    raise Exception(
                        "Unknown seq_reduce_type {}".format(self.config.seq_reduce_type)
                    )
                mention_emb_list.append(mention_emb)
            doc_mention_emb = torch.stack(mention_emb_list, dim=0)

            if self.config.use_token_role:
                # get mention type embedding
                if self.config.ment_feature_type == "concat":
                    yy = [
                        self.config.tag_id2tag_name[x]
                        for x in doc_arg_rel_info.mention_type_list # qy: 当前预测出来的mention type
                    ]
                    # there will be 'O' labels for mentions if `OtherType` is not included in the ent list
                    zz = [
                        self.config.ent_type2id[xx[2:] if len(xx) > 2 else xx] # qy: mention type to id map
                        for xx in yy
                    ]
                    doc_mention_emb = self.ment_type_encoder(doc_mention_emb, zz) # qy: (batch_mention_emb, mention_type_ids) 合并mention和type的embedding 得到800维
                else:
                    doc_mention_emb = self.ment_type_encoder(
                        doc_mention_emb, doc_arg_rel_info.mention_type_list
                    )

        return doc_mention_emb

    def get_doc_span_sent_context(  # qy: 这里是一个batch的？
        self, doc_token_emb, doc_sent_emb, doc_fea, doc_arg_rel_info
    ):
        """
        get all the span representations by aggregating mention representations,
        and sentence representations
        """
        doc_mention_emb = self.get_doc_span_mention_emb(doc_token_emb, doc_arg_rel_info) # qy: 得到每个mention的embedding 由mention的和type的合并 800维
        #print(doc_mention_emb.size())# qy: debug [23,800]
        #print("22222")
            ############## 在此处加入GIT? #############
        if (self.use_git and len(doc_arg_rel_info.mention_drange_list)>0):
            #graphs = []
            #node_features = []
            '''
            if (
                    #not train_flag
                    #and not use_gold_span
                    #and 
                    len(doc_arg_rel_info.mention_drange_list) < 1 # qy: 没有提取出mention
                ):
                
                continue
            '''
            sent2mention_id = defaultdict(list)
            d = defaultdict(list)

            # 1. sentence-sentence #sent×#sent
            if self.full_git:
                
                doc_sent_emb += self.sent_embedding
                node_feature = doc_sent_emb # qy: git中的sentence node embedding
                sent_num = node_feature.size(0) # 句子数量
                for i in range(sent_num): # qy: #sentences
                    for j in range(sent_num):
                        if i != j:
                            d[("node", "s-s", "node")].append((i, j))
                            #d[("node","m-m","node")].append((i,j))
                
                # 2. sentence-mention
                #print(doc_arg_rel_info.mention_drange_list)
                for mention_id, (sent_idx, char_s, char_e) in enumerate( # qy: 遍历所有mention 得到第几个句子
                        doc_arg_rel_info.mention_drange_list
                    ):
                    sent2mention_id[sent_idx].append(mention_id+sent_num)
                    d[("node", "s-m", "node")].append((mention_id+sent_num, sent_idx))
                    d[("node", "s-m", "node")].append((sent_idx, mention_id+sent_num))
                    #d[("node", "m-m", "node")].append((mention_id+sent_num, sent_idx))
                    #d[("node", "m-m", "node")].append((sent_idx, mention_id+sent_num))

                doc_mention_emb += self.mention_embedding # qy: 加上一层bias?
                # qy: node_feature其实就是doc_mention_emb
                #print("sent2mentionid")
                #print(sent2mention_id)
                # qy: 合并sent和 mention 的embedding
                node_feature = torch.cat((node_feature, doc_mention_emb), dim=0)

                # 3. intra
                for _, mention_id_list in sent2mention_id.items(): # qy: 同一个sent中的mentions
                    for i in mention_id_list: #range(len(mention_id_list)):
                        for j in mention_id_list: #range(len(mention_id_list)):
                            if i != j:
                                d[("node", "m-m", "node")].append((i, j))
                ##print(doc_arg_rel_info.span_mention_range_list)
                # 4. inter
                for mention_id_b, mention_id_e in doc_arg_rel_info.span_mention_range_list:
                    for i in range(mention_id_b, mention_id_e):
                        for j in range(mention_id_b, mention_id_e):
                            if i != j: # or i==j:
                                d[("node", "m-m", "node")].append((i+sent_num, j+sent_num))
                # 5. default, when lacking of one of the above four kinds edges
                '''
                for rel in self.rel_name_lists:
                    if ("node", rel, "node") not in d:
                        d[("node", rel, "node")].append((0, 0)) # qy:保证每种edge都存在 default 0-0
                        logger.info("add edge: {}".format(rel))
                '''
                graph = dgl.heterograph(d) # qy: graph需要debug 看sent和mention是否是同样的id?
                graph = graph.to(node_feature.device)
                #print("0000000")
                #print(d[("node", "m-m", "node")])
                #print(node_feature.shape)
                feature_bank_sent = [doc_sent_emb]
                feature_bank_ment = [doc_mention_emb]
                for GCN_layer in self.GCN_layers:
                    node_feature = GCN_layer(graph , {"node": node_feature})[
                        "node"
                    ]
                    feature_bank_sent.append(node_feature[:sent_num])
                    feature_bank_ment.append(node_feature[sent_num:])
                feature_bank_sent = torch.cat(feature_bank_sent, dim=-1)
                feature_bank_ment = torch.cat(feature_bank_ment, dim=-1)
                doc_sent_emb = self.middle_layer_sent(feature_bank_sent)
                doc_mention_emb = self.middle_layer_ment(feature_bank_ment)
            #doc_sent_emb = feature_bank[:sent_num]
            else:
                # qy: git中的sentence node embedding
                #node_feature += self.mention_embedding
                
                doc_mention_emb += self.mention_embedding # qy: 加上一层bias?
                node_feature = doc_mention_emb 
                sent_num = node_feature.size(0) # 句子数量
                # qy: node_feature其实就是doc_mention_emb
                #print("sent2mentionid")
                #print(sent2mention_id)
                # qy: 合并sent和 mention 的embedding
                # node_feature = torch.cat((node_feature, doc_mention_emb), dim=0)
                for mention_id, (sent_idx, char_s, char_e) in enumerate( # qy: 遍历所有mention 得到第几个句子
                        doc_arg_rel_info.mention_drange_list
                    ):
                    sent2mention_id[sent_idx].append(mention_id)
                # 3. intra
                for _, mention_id_list in sent2mention_id.items(): # qy: 同一个sent中的mentions
                    for i in mention_id_list: #range(len(mention_id_list)):
                        for j in mention_id_list: #range(len(mention_id_list)):
                            if i != j:
                                d[("node", "m-m", "node")].append((i, j))
                ##print(doc_arg_rel_info.span_mention_range_list)
                # 4. inter
                for mention_id_b, mention_id_e in doc_arg_rel_info.span_mention_range_list:
                    if mention_id_b+1 == mention_id_e:
                        d[("node", "m-m", "node")].append((mention_id_b, mention_id_b))
                    for i in range(mention_id_b, mention_id_e):
                        for j in range(mention_id_b, mention_id_e):
                            if i != j:# or i==j:
                                d[("node", "m-m", "node")].append((i, j))
                # 5. default, when lacking of one of the above four kinds edges
                '''
                for rel in self.rel_name_lists:
                    if ("node", rel, "node") not in d:
                        d[("node", rel, "node")].append((0, 0)) # qy:保证每种edge都存在 default 0-0
                        logger.info("add edge: {}".format(rel))
                '''
                graph = dgl.heterograph(d) # qy: graph需要debug 看sent和mention是否是同样的id?
                graph = graph.to(node_feature.device)
                #print("0000000")
                #print(d[("node", "m-m", "node")])
                #print(node_feature.shape)
                feature_bank = [node_feature]
                for GCN_layer in self.GCN_layers:
                    node_feature = GCN_layer(graph , {"node": node_feature})[
                        "node"
                    ]
                    feature_bank.append(node_feature)
                    
                feature_bank = torch.cat(feature_bank, dim=-1)
                #doc_sent_emb = self.middle_layer_sent(feature_bank_sent)
                doc_mention_emb = self.middle_layer(feature_bank)

            #doc_mention_emb = feature_bank[sent_num:] # qy: to be debug
            ################### end of GIT ##########



        if self.config.use_mention_lstm and doc_mention_emb is not None: # qy: 再过一层mention lstm
            # mention further encoding
            doc_mention_emb = self.mention_lstm(doc_mention_emb.unsqueeze(0))[
                0
            ].squeeze(0)

        # only consider actual sentences
        if doc_sent_emb.size(0) > doc_fea.valid_sent_num:
            doc_sent_emb = doc_sent_emb[: doc_fea.valid_sent_num, :]

        span_context_list = []

        if doc_mention_emb is None:
            # qy: 新加transformer 但是sentence和mention目前的dim不同 只加在mention上？
            '''
            if self.config.use_doc_enc:
                doc_sent_context = self.doc_context_encoder(
                    doc_sent_emb.unsqueeze(0), None
                ).squeeze(0)
            else:
            '''
            doc_sent_context = doc_sent_emb
        else:
            num_mentions = doc_mention_emb.size(0)
            if self.config.use_doc_enc: # qy: 使用transformer
                # Size([1, num_mentions + num_valid_sents, hidden_size])
                '''
                total_ment_sent_emb = torch.cat(
                    [doc_mention_emb, doc_sent_emb], dim=0
                ).unsqueeze(0) # qy: mention和sentence的一起加入transformer
                '''
                # size = [num_mentions+num_valid_sents, hidden_size]
                # here we do not need mask
                total_ment_sent_emb = doc_mention_emb.unsqueeze(0) # ?? tbd
                total_ment_sent_context = self.doc_context_encoder(
                    total_ment_sent_emb, None
                ).squeeze(0)
                #print(total_ment_sent_context.size())# [23,23,800]
                # collect span context
                for mid_s, mid_e in doc_arg_rel_info.span_mention_range_list:
                    assert mid_e <= num_mentions
                    multi_ment_context = total_ment_sent_context[
                        mid_s:mid_e
                    ]  # [num_mentions, hidden_size]

                    # span_context.size [1, hidden_size]
                    if self.config.seq_reduce_type == "AWA":
                        span_context = self.span_mention_reducer(
                            multi_ment_context, keepdim=True
                        )
                    elif self.config.seq_reduce_type == "MaxPooling":
                        span_context = multi_ment_context.max(dim=0, keepdim=True)[0]
                    elif self.config.seq_reduce_type == "MeanPooling":
                        span_context = multi_ment_context.mean(dim=0, keepdim=True)
                    else:
                        raise Exception(
                            "Unknown seq_reduce_type {}".format(
                                self.config.seq_reduce_type
                            )
                        )

                    span_context_list.append(span_context)

                # collect sent context
                doc_sent_context = doc_sent_emb #原来edag为total_ment_sent_context[num_mentions:, :]
            
            else:
                # collect span context
                for mid_s, mid_e in doc_arg_rel_info.span_mention_range_list:
                    assert mid_e <= num_mentions
                    multi_ment_emb = doc_mention_emb[
                        mid_s:mid_e
                    ]  # [num_mentions, hidden_size]

                    if self.config.span_mention_sum: # qy: false
                        span_context = multi_ment_emb.sum(0, keepdim=True)
                    else:
                        # span_context.size is [1, hidden_size]
                        if self.config.seq_reduce_type == "AWA":
                            span_context = self.span_mention_reducer(
                                multi_ment_emb, keepdim=True
                            )
                        elif self.config.seq_reduce_type == "MaxPooling":
                            span_context = multi_ment_emb.max(dim=0, keepdim=True)[0]
                        elif self.config.seq_reduce_type == "MeanPooling":
                            span_context = multi_ment_emb.mean(dim=0, keepdim=True)
                        else:
                            raise Exception(
                                "Unknown seq_reduce_type {}".format(
                                    self.config.seq_reduce_type
                                )
                            )
                    span_context_list.append(span_context)

                # collect sent context
                doc_sent_context = doc_sent_emb

        return span_context_list, doc_sent_context

    def get_arg_combination_loss(
        self, scores, doc_arg_rel_info, event_idx=None, margin=0.1
    ):
        # rel_adj_mat = doc_arg_rel_info.whole_arg_rel_mat.reveal_adj_mat(masked_diagonal=1, tolist=False).to(scores.device).float()
        if self.config.self_loop:
            rel_adj_mat = (
                doc_arg_rel_info.whole_arg_rel_mat.reveal_adj_mat(
                    masked_diagonal=None, tolist=False
                )
                .to(scores.device)
                .float()
            )
        else:
            rel_adj_mat = (
                doc_arg_rel_info.whole_arg_rel_mat.reveal_adj_mat(
                    masked_diagonal=1, tolist=False
                )
                .to(scores.device)
                .float()
            )

        combination_loss = F.binary_cross_entropy_with_logits(scores, rel_adj_mat)
        # combination_loss = F.binary_cross_entropy(torch.clamp(scores, min=1e-6, max=1.0), rel_adj_mat)
        # combination_loss = F.mse_loss(torch.sigmoid(scores), rel_adj_mat, reduction='sum')
        # combination_loss = F.mse_loss(scores, rel_adj_mat)
        # combination_loss = F.mse_loss(torch.sigmoid(scores.view(-1)), rel_adj_mat.view(-1))
        # combination_loss = F.mse_loss(torch.sigmoid(scores), rel_adj_mat)
        # combination_loss = F.mse_loss(torch.sigmoid(torch.clamp(scores, min=-5.0, max=5.0)), rel_adj_mat)
        # combination_loss = F.mse_loss(scores, rel_adj_mat.masked_fill(rel_adj_mat == 0, -1))
        # combination_loss = F.mse_loss(torch.tanh(scores), rel_adj_mat.masked_fill(rel_adj_mat == 0, -1))

        # # Su Jianlin's multilabel CE
        # # reference: https://spaces.ac.cn/archives/7359/comment-page-2
        # scores = scores.view(-1)
        # rel_adj_mat = rel_adj_mat.view(-1)
        # scores = (1 - 2 * rel_adj_mat) * scores
        # pred_neg = scores - rel_adj_mat * 1e12
        # pred_pos = scores - (1 - rel_adj_mat) * 1e12
        # zeros = torch.zeros_like(scores)
        # pred_neg = torch.stack([pred_neg, zeros], dim=-1)
        # pred_pos = torch.stack([pred_pos, zeros], dim=-1)
        # neg_loss = torch.logsumexp(pred_neg, dim=-1)
        # pos_loss = torch.logsumexp(pred_pos, dim=-1)
        # combination_loss = neg_loss + pos_loss
        # combination_loss = combination_loss.mean()

        # contrastive learning
        # cl = F.log_softmax(scores / 0.05, dim=-1)
        # cl = cl * rel_adj_mat.masked_fill(rel_adj_mat == 0, -1)
        # c_score = F.mse_loss(scores, rel_adj_mat.masked_fill(rel_adj_mat == 0, -1), reduction='none')
        # contrastive_loss = -F.log_softmax(c_score / 0.05, dim=-1).mean()
        # return max(-cl.mean(), 0.0)

        # # cos emb loss
        # target = rel_adj_mat.masked_fill(rel_adj_mat == 0, -1)
        # pos = (1.0 - scores).masked_fill(target == -1, 0.0).sum() / torch.sum(target == 1.0)
        # neg_scores = scores.masked_fill(target == 1, margin) - margin
        # neg = neg_scores.masked_fill(neg_scores < 0.0, 0.0).sum() / torch.sum(target == -1.0)
        # combination_loss = pos + neg
        return combination_loss

    def get_adj_mat_logits(self, hidden):
        # dot scaled similarity
        query = self.q_w(hidden)
        key = self.k_w(hidden)
        d_k = query.size(-1)
        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(d_k)

        # # cos similarity
        # num_ents = hidden.shape[0]
        # query = self.q_w(hidden).unsqueeze(1).repeat((1, num_ents, 1))
        # key = self.k_w(hidden).unsqueeze(0).repeat((num_ents, 1, 1))
        # scores = F.cosine_similarity(query, key, dim=-1)
        return scores

    def get_loss_on_doc(
        self,
        doc_token_emb,
        doc_sent_emb,
        doc_fea,
        doc_arg_rel_info,
        use_gold_adj_mat=False,
    ):
        if self.config.stop_gradient:
            doc_token_emb = doc_token_emb.detach()
            doc_sent_emb = doc_sent_emb.detach()
        span_context_list, doc_sent_context = self.get_doc_span_sent_context( # qy: get all the span representations by aggregating mention representations, and sentence representations        
            doc_token_emb,
            doc_sent_emb,
            doc_fea,
            doc_arg_rel_info,
        )
        if len(span_context_list) == 0:
            raise Exception(
                "Error: doc_fea.ex_idx {} does not have valid span".format(
                    doc_fea.ex_idx
                )
            )
        # 0. get span representations
        batch_span_context = torch.cat(span_context_list, dim=0)
        lstm_batch_span_context = None
        if self.config.use_span_lstm: # qy: 当前true
            # there's no padding in spans, no need to pack rnn sequence
            #print(batch_span_context.size()) # [14,23,800]
            lstm_batch_span_context = batch_span_context.unsqueeze(0) # [1,14,23,800]
            #print("11111111111")
            #print(lstm_batch_span_context.size())# qy: debug
            lstm_batch_span_context, (_, _) = self.span_lstm(lstm_batch_span_context)
            lstm_batch_span_context = lstm_batch_span_context.squeeze(0)

        if lstm_batch_span_context is not None:
            batch_span_context = lstm_batch_span_context

        # if self.config.use_span_att:
        # batch_span_context = batch_span_context.unsqueeze(0)
        # batch_span_context, p_attn, scores = self.span_att(batch_span_context, return_scores=True)
        # batch_span_context = batch_span_context.squeeze(1)

        scores = self.get_adj_mat_logits(batch_span_context)

        # for each event type, get argument combination loss
        # argument combination loss, calculated by comparing
        # the biaffine output and the gold event SpanArgRelAdjMat
        arg_combination_loss = []
        arg_role_loss = []

        # event-relevant combination, attention between event representation and batch_span_context output
        if self.config.event_relevant_combination:
            raise RuntimeError("event_relevant_combination is not supported yet")

        # combination loss via biaffine
        # biaffine_out = self.get_adj_mat_logits(batch_span_context)
        assert scores.shape[-1] == doc_arg_rel_info.whole_arg_rel_mat.len_spans
        comb_loss = self.get_arg_combination_loss(
            scores, doc_arg_rel_info, event_idx=None
        )
        arg_combination_loss.append(comb_loss)

        if use_gold_adj_mat:
            pred_adj_mat = doc_fea.whole_arg_rel_mat.reveal_adj_mat()
            event_pred_list = doc_fea.event_type_labels
        else:
            pred_adj_mat = (
                torch.sigmoid(scores).ge(self.config.biaffine_hard_threshold).long() # qy: 超过threshold的话
            )
            # pred_adj_mat = self.pred_adj_mat_reorgnise(pred_adj_mat)
            pred_adj_mat = pred_adj_mat.detach().cpu().tolist()
            event_pred_list = self.get_event_cls_info( # return [1,0,0,1]
                doc_sent_context, doc_fea, train_flag=False
            )
        ### dynamic R
        if not self.config.dynamic_num_triggers:
            if self.config.guessing_decode:
                num_triggers = 0
            else:
                num_triggers = self.config.eval_num_triggers
        else:
            num_triggers = 1
            if self.config.dataset == "Duee":
                # no企业收购 股东增持 股东减持
                if event_pred_list[11] == 1 or event_pred_list[5] == 1: #or event_pred_list[4] == 1:
                    num_triggers = 2
                if self.config.strict_dynamic_num_triggers:  
                    x = [v for i,v in enumerate(event_pred_list) if i not in frozenset((4,5,11))] 
                    if sum(x) > 1:
                        num_triggers = 1
            else:
                # 资产冻结
                if event_pred_list[0] == 1:
                    num_triggers = 2
                if self.config.strict_dynamic_num_triggers:  
                    x =  event_pred_list[1:]
                    if sum(x) > 1:
                        num_triggers = 1


        if self.config.incremental_min_conn > -1:
            combs = directed_trigger_graph_incremental_decode(
                pred_adj_mat, num_triggers, self.config.incremental_min_conn
            )
        else:
            # combs = directed_trigger_graph_decode(pred_adj_mat, num_triggers, self.config.max_clique_decode, self.config.with_left_trigger, self.config.with_all_one_trigger_comb)
            combs = directed_trigger_graph_decode(
                pred_adj_mat,
                num_triggers,
                self_loop=self.config.self_loop, # qy: =false目前
                max_clique=self.config.max_clique_decode, # qy: =true目前
                with_left_trigger=self.config.with_left_trigger, # qy: =true目前
            )

        if self.config.at_least_one_comb:
            if len(combs) < 1:
                combs = [set(range(len(pred_adj_mat)))]

        event_cls_loss = self.get_event_cls_info(
            doc_sent_context, doc_fea, train_flag=True
        )
        for event_idx, event_label in enumerate(event_pred_list): # qy: 所有预测出来的eventtypes
            if not event_label:
                continue
            events = doc_arg_rel_info.pred_event_arg_idxs_objs_list[event_idx] # qy: ground truth 中相同type下所有的events
            if events is None:
                continue
            gold_combinations = events
            for comb in combs: # qy: 叉乘上所有抽取出来的combinations
                event_table = self.event_tables[event_idx] # qy: 属于这个event type的role prediction
                gold_comb, _ = closest_match(comb, gold_combinations) # qy: 找到最接近的gold combi 通过arguments
                instance = assign_role_from_gold_to_comb(comb, gold_comb)# qy: 将gold combi的roles赋给当前的combi，允许出现一个entity多个role的，返回的是roles的set
                span_idxs = []
                role_types = []
                span_rep_list_for_event_instance = []
                for span_idx, role_type in instance:
                    span_idxs.append(span_idx)
                    role_types.append(role_type)
                    if self.config.role_by_encoding:
                        span_rep_list_for_event_instance.append(
                            batch_span_context[span_idx]
                        )
                    else:
                        span_rep_list_for_event_instance.append(
                            span_context_list[span_idx].squeeze(0)
                        )
                span_rep_for_event_instance = torch.stack(
                    span_rep_list_for_event_instance, dim=0
                )
                role_cls_logits = event_table( 
                    batch_span_emb=span_rep_for_event_instance
                )
                role_loss = self.get_arg_role_loss(role_cls_logits, role_types) # qy: 角色预测的loss
                arg_role_loss.append(role_loss)

        self.losses.update(
            {
                "event_cls": event_cls_loss,
                "arg_combination_loss": sum(arg_combination_loss),
                "arg_role_loss": sum(arg_role_loss),
            }
        )
        return (
            self.config.event_cls_loss_weight * event_cls_loss # qy：1.0
            + self.config.combination_loss_weight * sum(arg_combination_loss) # qy: 1.0
            + self.config.role_loss_weight * sum(arg_role_loss) # qy: 1.0
        )

    def get_eval_on_doc(self, doc_token_emb, doc_sent_emb, doc_fea, doc_arg_rel_info):
        """
        Get the final evaluation results (prediction process).
        To unify the evaluation process, the format of output
        event_arg_idxs_objs will stay the same with EDAG.
        Since the `event_idx2event_decode_paths` is not used
        in evaluation, we'll change it to predicted adj_mat
        and adj_decoding combinations.
        """
        final_pred_adj_mat = []
        event_idx2combinations = []

        span_context_list, doc_sent_context = self.get_doc_span_sent_context(
            doc_token_emb, doc_sent_emb, doc_fea, doc_arg_rel_info
        )
        if len(span_context_list) == 0:
            event_pred_list = []
            event_idx2obj_idx2field_idx2token_tup = []
            for event_idx in range(len(self.event_type_fields_pairs)):
                event_pred_list.append(0)
                event_idx2obj_idx2field_idx2token_tup.append(None)

            return (
                doc_fea.ex_idx,
                event_pred_list,
                event_idx2obj_idx2field_idx2token_tup,
                doc_arg_rel_info,
                final_pred_adj_mat,
                event_idx2combinations,
            )

        # 1. get event type prediction
        event_pred_list = self.get_event_cls_info(
            doc_sent_context, doc_fea, train_flag=False
        )

        # 2. for each event type, get argument relation adjacent matrix
        batch_span_context = torch.cat(span_context_list, dim=0)
        lstm_batch_span_context = None
        if self.config.use_span_lstm:
            lstm_batch_span_context = batch_span_context.unsqueeze(0)
            lstm_batch_span_context, (_, _) = self.span_lstm(lstm_batch_span_context)
            lstm_batch_span_context = lstm_batch_span_context.squeeze(0)

        if lstm_batch_span_context is not None:
            batch_span_context = lstm_batch_span_context

        # if self.config.use_span_att:
        # batch_span_context = batch_span_context.unsqueeze(0)
        # batch_span_context, p_attn, scores = self.span_att(batch_span_context, return_scores=True)
        # batch_span_context = batch_span_context.squeeze(1)

        scores = self.get_adj_mat_logits(batch_span_context)

        if (
            self.config.event_relevant_combination
        ):  # event-relevant combination, attention between event representation and batch_span_context output
            raise RuntimeError("event_relevant_combination is not supported yet")

        pred_adj_mat = (
            torch.sigmoid(scores).ge(self.config.biaffine_hard_threshold).long()
        )
        # pred_adj_mat = self.pred_adj_mat_reorgnise(torch.sigmoid(scores).ge(self.config.biaffine_hard_threshold).long())
        assert pred_adj_mat.shape[-1] == doc_arg_rel_info.whole_arg_rel_mat.len_spans
        # debug mode statement only for time saving
        if self.config.run_mode == "debug":
            pred_adj_mat = pred_adj_mat[:10, :10]

        """only for 100% filled graph testing"""
        # pred_adj_mat = torch.ones((batch_span_context.shape[0], batch_span_context.shape[0]))
        """end of testing"""

        pred_adj_mat = pred_adj_mat.detach().cpu().tolist()
        final_pred_adj_mat.append(pred_adj_mat)
        if not self.config.dynamic_num_triggers:
            if self.config.guessing_decode:
                num_triggers = 0
            else:
                num_triggers = self.config.eval_num_triggers
        else:
            num_triggers = 1
            if self.config.dataset == "Duee":
                # 企业收购 股东增持 股东减持
                if event_pred_list[4] == 1 or event_pred_list[5] == 1 or event_pred_list[11] == 1:
                    num_triggers = 2
            else:
                # 资产冻结
                if event_pred_list[0] == 1:
                    num_triggers = 2

        if self.config.incremental_min_conn > -1:
            raw_combinations = directed_trigger_graph_incremental_decode( 
                pred_adj_mat, num_triggers, self.config.incremental_min_conn
            )
        else: # qy: 目前是这个
            # raw_combinations = directed_trigger_graph_decode(pred_adj_mat, num_triggers, self.config.max_clique_decode, self.config.with_left_trigger, self.config.with_all_one_trigger_comb)
            raw_combinations = directed_trigger_graph_decode( # qy: combination decoding 解码图得到组合
                pred_adj_mat,
                num_triggers,
                self_loop=self.config.self_loop,
                max_clique=self.config.max_clique_decode,
                with_left_trigger=self.config.with_left_trigger,
            )

        if self.config.at_least_one_comb:
            if len(raw_combinations) < 1:
                raw_combinations = [set(range(len(pred_adj_mat)))]

        event_idx2obj_idx2field_idx2token_tup = []
        for event_idx, event_pred in enumerate(event_pred_list):
            if event_pred == 0:
                event_idx2obj_idx2field_idx2token_tup.append(None)
                continue
            event_table = self.event_tables[event_idx]
            # TODO(tzhu): m2m support from all the combinations
            """combinations filtering based on minimised number of argument"""
            #combinations = list(filter(lambda x: len(x) >= event_table.min_field_num, raw_combinations)) # qy: qy加上的
            """end of combination filtering"""
            combinations = copy.deepcopy(raw_combinations) # qy 去掉的
            event_idx2combinations.append(combinations)
            if len(combinations) <= 0:
                event_idx2obj_idx2field_idx2token_tup.append(None)
                continue
            obj_idx2field_idx2token_tup = []
            for combination in combinations:
                span_rep_list_for_event_instance = []
                for span_idx in combination:
                    if self.config.role_by_encoding:
                        span_rep_list_for_event_instance.append(
                            batch_span_context[span_idx]
                        )
                    else:
                        span_rep_list_for_event_instance.append(
                            span_context_list[span_idx].squeeze(0)
                        )
                span_rep_for_event_instance = torch.stack(
                    span_rep_list_for_event_instance, dim=0
                )
                role_preds = event_table.predict_span_role(span_rep_for_event_instance, unique_role=self.config.unique_role) # qy: 返回长度为#entities的列表 每个元素是一个list包含这个entity对应的roles
                """roles random generation (only for debugging)"""
                # role_preds = [random.randint(0, event_table.num_fields - 1) for _ in range(len(combination))]
                """end of random roles generation"""
                event_arg_obj = self.reveal_event_arg_obj(
                    combination, role_preds, event_table.num_fields
                )
                field_idx2token_tup = self.convert_span_idx_to_token_tup(
                    event_arg_obj, doc_arg_rel_info
                )
                obj_idx2field_idx2token_tup.append(field_idx2token_tup)
            # obj_idx2field_idx2token_tup = merge_non_conflicting_ins_objs(obj_idx2field_idx2token_tup)
            event_idx2obj_idx2field_idx2token_tup.append(obj_idx2field_idx2token_tup)
        # the first three terms are for metric calculation, the last three are for case studies
        return (
            doc_fea.ex_idx,
            event_pred_list,
            event_idx2obj_idx2field_idx2token_tup,
            doc_arg_rel_info,
            final_pred_adj_mat,
            event_idx2combinations,
            #scores, # qy: return predicted adj. mat before sigmoid
        )
