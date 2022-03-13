import json

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

with open(r'./luge_submit_mlp_mention_lstm_truncated_0313.json', "w", encoding="UTF-8") as e:
    
    # json_new_data = json.dumps(list1, ensure_ascii=False, indent=4)
    for line in list1:
        e.write(json.dumps(line,ensure_ascii=False))
        e.write('\n')
