import json
from tqdm import tqdm

with open('./classes_and_interfaces.jsonl', encoding='utf-8') as f:
    res = []
    for line in tqdm(f):
        jsonl = json.loads(line)

        obj = {}

        code = jsonl['signature'] + ' {\n'
        for method in jsonl['methods_des']:
            if method['method_des'] != '':
                code += '\t// ' + method['method_des'] + '\n'
            code += '\t' + method['method_name'] + ';\n'
        code += '}'

        obj['index'] = jsonl['index']
        obj['code'] = code
        obj['des'] = jsonl['des']

        res.append(obj)

    with open('valid.jsonl', 'w', encoding='utf-8') as f:
        for item in res:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')