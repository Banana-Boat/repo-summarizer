import json
from tqdm import tqdm


def get_processed_data(filename, start_idx):
    with open(filename, "r", encoding='utf-8') as f:
        res = []
        index = start_idx

        for line in tqdm(f):
            jsonl = json.loads(line)

            obj = {}

            valid_num = 0
            code = jsonl['signature'] + ' {\n'
            for method in jsonl['methods_des']:
                if method['method_des'] != '':
                    code += '\t// ' + method['method_des'] + '\n'
                    valid_num += 1
                code += '\t' + method['method_name'] + ';\n'
            code += '}'
            if valid_num < 2:
                continue

            # 根据模型输入token个数上限而定
            if len(code) > 512:
                continue

            obj['index'] = index
            obj['code'] = code
            obj['des'] = jsonl['des']

            res.append(obj)
            index += 1

        return res


if __name__ == '__main__':
    res = []
    for i in range(1, 4):
        filename = './classes_and_interfaces_v{}.jsonl'.format(i)
        print('Processing ' + filename)
        res.extend(get_processed_data(filename, len(res)))

    # 将res拆分为train, valid, test，比例为6:2:2
    train_num = int(len(res) * 0.6)
    valid_num = int(len(res) * 0.2)
    test_num = len(res) - train_num - valid_num

    with open('train.jsonl', 'w', encoding='utf-8') as f:
        for item in res[:train_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('valid.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num:train_num+valid_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('test.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num+valid_num:]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
