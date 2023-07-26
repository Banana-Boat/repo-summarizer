import json
import random
from tqdm import tqdm


def get_processed_data(filename, start_idx):
    res = []

    with open(filename, "r", encoding='utf-8') as f:
        index = start_idx

        for line in tqdm(f):
            jsonl = json.loads(line)

            obj = {}

            valid_num = 0
            code = jsonl['signature'] + ' {\n'
            for method in jsonl['methods']:
                tmp_str = ''
                if method['des'] != '':
                    tmp_str += '\t// ' + method['des'] + '\n'
                    valid_num += 1
                tmp_str += '\t' + method['name'] + ';\n'

                if len(code + tmp_str) > 511:
                    break

                code += tmp_str

            code += '}'
            if valid_num < 2:
                continue

            obj['index'] = index
            obj['repo'] = jsonl['repo']
            obj['code'] = code
            obj['des'] = jsonl['des']

            res.append(obj)
            index += 1

    return res


if __name__ == '__main__':
    res = []
    for i in range(1, 4):
        filename = './classes_v{}.jsonl'.format(i)
        print('Processing ' + filename)
        res.extend(get_processed_data(filename, len(res)))

    print('Total num: ' + str(len(res)))

    # 将res拆分为train, valid, test，比例为6:2:2
    train_num = int(len(res) * 0.6)
    valid_num = int(len(res) * 0.2)
    test_num = len(res) - train_num - valid_num

    with open('../../train_classes.jsonl', 'w', encoding='utf-8') as f:
        for item in res[:train_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('../../valid_classes.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num:train_num+valid_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('../../test_classes.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num+valid_num:]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
