import json
import random

with open('./classes_and_interfaces.jsonl', encoding='utf-8') as f:
    f.readline()
    lines = f.readlines()
    random.shuffle(lines)
    jsonl = json.loads(lines[0])

    with open('test.java', 'w', encoding='utf-8') as f:
        f.write('/**\n')
        f.write(' * ' + jsonl['des'] + '\n')
        f.write(' * ' + jsonl['repo'] + '\n')
        f.write(' */\n')
        f.write(jsonl['signature'] + ' {\n')
        for method in jsonl['methods_des']:
            if method['method_des'] != '':
                f.write('\t// ' + method['method_des'] + '\n')
            f.write('\t' + method['method_name'] + ';\n')
        f.write('}')
