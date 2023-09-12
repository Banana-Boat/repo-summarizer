import json
import random
from tqdm import tqdm

MAX_TARGET_LEN = 512


def get_processed_data(filename, start_idx):
    res = []

    with open(filename, "r", encoding='utf-8') as f:
        index = start_idx

        for line in tqdm(f):
            jsonl = json.loads(line)

            obj = {}

            valid_num = 0  # 带摘要的方法数

            code = jsonl['signature'] + ' {\n'
            for method in jsonl['methods']:
                tmp_str = ''
                if method['des'] != '':
                    tmp_str += '\t// ' + method['des'] + '\n'
                    valid_num += 1
                tmp_str += '\t' + method['name'] + ';\n'

                # 忽略超出字符限制的方法
                # if len(code + tmp_str) > MAX_TARGET_LEN - 1:
                #     break

                code += tmp_str

            code += '}'

            # 若带摘要的方法数少于2，则忽略该类
            if valid_num < 2:
                continue

            # 忽略总字符数大于上限的类
            if len(code) > MAX_TARGET_LEN:
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
    for i in range(1, 5):
        filename = './classes_v{}.jsonl'.format(i)
        print('Processing ' + filename)
        res.extend(get_processed_data(filename, len(res)))

    print('Total num: ' + str(len(res)))

    # 打乱顺序
    # random.shuffle(res)

    # 将res拆分为train, valid, test，比例为6:2:2
    train_num = int(len(res) * 0.6)
    valid_num = int(len(res) * 0.2)
    test_num = len(res) - train_num - valid_num

    with open('../train_cls.jsonl', 'w', encoding='utf-8') as f:
        for item in res[:train_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('../valid_cls.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num:train_num+valid_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('../test_cls.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num+valid_num:]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
