import json

# convert into luge submit format
with open(r'./luge_p1_submit_new_mlp_ner0.001_short256_0417.json', "r", encoding="utf-8") as f:
    json_data = []
    for line in f.readlines():
        json_data.append(json.loads(line))
    list1= []
    for i in json_data:
        i.pop("mspans",0)
        i.pop("comments",0)
        i.pop("sentences",0)
        list1.append(i)

with open(r'./luge_p1_submit_new_mlp_ner0.001_short256_truncated.json', "w", encoding="UTF-8") as e:
    
    # json_new_data = json.dumps(list1, ensure_ascii=False, indent=4)
    for line in list1:
        e.write(json.dumps(line,ensure_ascii=False))
        e.write('\n')
'''
with open(r'./guosou_p2_submit_new_0804.json', "r", encoding="utf-8") as f:
    json_data = []
    for line in f.readlines():
        json_data.append(json.loads(line))
    list1= []
    for i in json_data:
        i.pop("mspans",0)
        i.pop("comments",0)
        i.pop("sentences",0)
        list1.append(i)

with open(r'./guosou2_truncated_0408.json', "w", encoding="UTF-8") as e:

    # json_new_data = json.dumps(list1, ensure_ascii=False, indent=4)
    for line in list1:
        e.write(json.dumps(line,ensure_ascii=False))
        e.write('\n')
'''
