import json
triggers = {"质押": "质押股票/股份数量",
           "股份回购": "回购股份数量",
            "解除质押": "质押股票/股份数量",
           "被约谈": "公司名称",
            "股东增持": "增持方",
            "高管变动": "高管姓名",
            "中标": "中标标的",
            "公司上市": "上市公司",
            "企业融资": "融资金额",
            "亏损": "净亏损",
            "股东减持": "减持方",
            "企业破产": "破产公司",
           "企业收购": "被收购方"}
# convert into luge submit format
with open(r'./luge_p1_submit_new_mlp_mention_lstm_0312.json', "r", encoding="utf-8") as f:
    json_data = []
    for line in f.readlines():
        json_data.append(json.loads(line))
    list1= []
    for i in json_data:
        i.pop("mspans",0)
        i.pop("comments",0)
        i.pop("sentences",0)
        list1.append(i)
list2 = []
for i in list1:
    new_ent = {}
    new_ent['id'] = i['id']
    event_list = []
    for eve in i['event_list']:
        if (triggers[eve['event_type']] in [j['role'] for j in eve['arguments']]):
            event_list.append(eve)
    new_ent['event_list'] = event_list
    list2.append(new_ent)
        
with open(r'./luge_submit_mlp_mention_lstm_truncated_0313.json', "w", encoding="UTF-8") as e:
    
    # json_new_data = json.dumps(list1, ensure_ascii=False, indent=4)
    for line in list2:
        e.write(json.dumps(line,ensure_ascii=False))
        e.write('\n')
