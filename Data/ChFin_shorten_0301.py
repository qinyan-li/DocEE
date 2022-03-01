import json
def read_file(path):
    res = []
    with open(path,'r',encoding='utf-8') as f:
        return json.load(f)
def write_to_file(path,dataset):
    with open(path,"w",encoding="utf-8") as fout:
        for data in dataset:
            fout.write(json.dumps(data,ensure_ascii = False)+"\n")
def convert_data(dataset):
    for data in dataset:
        data[1]['sentences'] = convert_sents(data[1]['sentences'])
def sent_seg(
    text,
    special_seg_indicators=None,
    lang="zh",
    punctuations=None,
    quotation_seg_mode=True,
) -> list:
    """
    cut texts into sentences (in chinese language).
    Args:
        text <str>: texts ready to be cut
        special_seg_indicators <list>: some special segment indicators and
            their replacement ( [indicator, replacement] ), in baike data,
            this argument could be `[('###', '\n'), ('%%%', ' '), ('%%', ' ')]`
        lang <str>: languages that your corpus is, support `zh` for Chinese
            and `en` for English now.
        punctuations <set>: you can split the texts by specified punctuations.
            texts will not be splited by `;`, so you can specify them by your own.
        quotation_seg_mode <bool>: if True, the quotations will be regarded as a
            part of the former sentence.
            e.g. `我说：“翠花，上酸菜。”，她说：“欸，好嘞。”`
            the text will be splited into
            ['我说：“翠花，上酸菜。”，', '她说：“欸，好嘞。”'], other than
            ['我说：“翠花，上酸菜。', '”，她说：“欸，好嘞。”']
    Rrturns:
        <list>: a list of strings, which are splited sentences.
    """
    # if texts are not in string format, raise an error
    if not isinstance(text, str):
        raise ValueError

    # if the text is empty, return a list with an empty string
    if len(text) == 0:
        return []

    text_return = text

    # segment on specified indicators
    # special indicators standard, like [('###', '\n'), ('%%%', '\t'), ('\s', '')]
    if special_seg_indicators:
        for indicator in special_seg_indicators:
            text_return = re.sub(indicator[0], indicator[1], text_return)

    if lang == "zh":
        punkt = {"。", "？", "！", "…"}
    elif lang == "en":
        punkt = {".", "?", "!"}
    if punctuations:
        punkt = punkt | punctuations

    if quotation_seg_mode:
        text_return = re.sub(
            "([%s]+[’”`'\"]*)" % ("".join(punkt)), "\\1\n", text_return
        )
    else:
        text_return = re.sub("([{}])".format("".join(punkt)), "\\1\n", text_return)

    # drop sentences with no length
    return [
        s.strip()
        for s in filter(
            lambda x: len(x.strip()) == 1
            and x.strip() not in punkt
            or len(x.strip()) > 0,
            text_return.split("\n"),
        )
    ]


def stat_sent_len(filepath):
    num_sents = []
    sent_len = []
    for d in load_line_json_iterator(filepath):
        sents = sent_seg(d["text"])
        num_sents.append(len(sents))
        lens = [len(sent) for sent in sents]
        sent_len.extend(lens)
        # if min(lens) < 5:
        #     print("================= raw text =================")
        #     print(d["text"])
        #     print("================= processed text =================")
        #     print("\n".join(filter(lambda x: len(x) < 5, sents)))
        #     breakpoint()
    sent_len_counter = Counter(sent_len)
    print(
        (
            f"num_sents: min: {min(num_sents)}, median: {median(num_sents)}, max: {max(num_sents)}\n"
            f"sent_len: min: {min(sent_len)}, median: {median(sent_len)}, max: {max(sent_len)}"
            f"{sent_len_counter.most_common()}"
        )
    )

# qy:将短句子合并为每句总长不超过128
def reorganise_sents(sents, max_seq_len, concat=False, final_cut=False, concat_str=" "):
    # qy:concat 是否合并句子
    new_sents = []
    group = ""
    for sent in sents:
        if len(sent) + len(group) < max_seq_len:
            if concat:
                if len(group) > 1 and "\u4e00" <= group[-1] <= "\u9fa5":
                    group += concat_str + sent
                else:
                    group += sent
            else:
                new_sents.append(sent)
        else:
            if len(group) > 0:
                new_sents.append(group)
                group = ""
            if len(sent) > max_seq_len:
                if final_cut:
                    group = sent[:max_seq_len]
                else:
                    sent_splits = sent_seg(sent, punctuations={"，", "、"})
                    reorg_sent_splits = reorganise_sents(
                        sent_splits, max_seq_len, concat=True, final_cut=True
                    )
                    new_sents.extend(reorg_sent_splits)
            else:
                group = sent
    if len(group) > 0:
        new_sents.append(group)
    return [s.strip() for s in filter(lambda x: len(x) > 0, new_sents)]

import re
import sys
import json
from collections import Counter, defaultdict
from statistics import median
def convert_sents(text1):
    text = '。'.join(text1[:3])+''.join(text1[3:])
    sents = sent_seg(text, punctuations={"；"}) # qy:sentence segmentation
    sents = reorganise_sents(sents, max_seq_len = 128, concat=True) # qy:合并短句
            # sents = d['map_sentences']
            # sentence length filtering
    sents = list(filter(lambda x: len(x) >= 5, sents)) # qy:去除<5个字的句子
    return sents
    
if __name__ == "__main__":
    train = read_file("./typed_train.json")
    dev = read_file("./typed_dev.json")
    test = read_file("./typed_test.json")
    convert_data(test)
    convert_data(dev)    
    convert_data(train)
    write_to_file("typed_train_short.json",train)
    write_to_file("typed_dev_short.json",dev)
    write_to_file("typed_test_short.json",test)

