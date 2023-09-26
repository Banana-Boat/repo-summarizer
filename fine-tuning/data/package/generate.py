import json
import random
from tqdm import tqdm
from transformers import AutoTokenizer


class MyTokenizer:
    MAX_SOURCE_LEN = 512

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            "Salesforce/codet5-base-multi-sum")

    def isLegalSource(self, source):
        encoded = self.tokenizer.encode(source, add_special_tokens=True)
        return len(encoded) <= self.MAX_SOURCE_LEN


def get_processed_data(tokenizer: MyTokenizer, filename, start_idx):
    res = []
    ignore_pkg_num = 0
    ignore_cls_num = 0
    sub_pkg_num = 0

    with open(filename, "r", encoding='utf-8') as f:
        index = start_idx

        for line in tqdm(f.readlines(), desc="Processing {}...".format(filename)):
            jsonl = json.loads(line)
            obj = {}

            code = 'Package: ' + jsonl['name'] + '\n'

            if len(jsonl['subPackages']) > 0:
                code += '\nSub Packages: \n'
                sub_pkg_num += 1

            for sub_pkg in jsonl['subPackages']:
                tmp_str = 'package ' + jsonl['name'] + '.' + sub_pkg['name'] + \
                    '; // ' + sub_pkg['des'] + '\n'

                # 忽略超出字符限制的子包
                if not tokenizer.isLegalSource(code + tmp_str):
                    break

                code += tmp_str

            if len(jsonl['classes']) > 0:
                code += '\nClasses and Interfaces: \n'

            for idx, cls in enumerate(jsonl['classes']):
                tmp_str = cls['signature'] + ';'
                if cls['des'] != '':
                    tmp_str += ' // ' + cls['des']
                tmp_str += '\n'

                # 忽略超出字符限制的类
                if not tokenizer.isLegalSource(code + tmp_str):
                    ignore_cls_num += len(jsonl['classes']) - idx
                    ignore_pkg_num += 1
                    break

                code += tmp_str

            # 忽略总token数大于上限的包
            if not tokenizer.isLegalSource(code):
                if len(jsonl['subPackages']) > 0:
                    sub_pkg_num -= 1
                continue

            obj['index'] = index
            obj['repo'] = jsonl['repo']
            obj['code'] = code
            obj['des'] = jsonl['des']

            res.append(obj)
            index += 1

    return res, ignore_pkg_num, ignore_cls_num, sub_pkg_num


if __name__ == '__main__':
    res = []
    total_ignore_pkg_num = 0  # 存在省略class的pkg总数
    total_ignore_cls_num = 0  # 被省略的class总数
    total_sub_pkg_num = 0  # 有子包作为上下文的包总数

    tokenizer = MyTokenizer()

    for i in range(1, 5):
        filename = './packages_v{}.jsonl'.format(i)

        temp_res, ignore_pkg_num, ignore_cls_num, sub_pkg_num = get_processed_data(
            tokenizer, filename, len(res))

        res.extend(temp_res)
        total_ignore_pkg_num += ignore_pkg_num
        total_ignore_cls_num += ignore_cls_num
        total_sub_pkg_num += sub_pkg_num

    print('\nTotal valid package num: ' + str(len(res)))
    print('Package has ignored class: ' + str(total_ignore_pkg_num))
    print('Ignore class num per ignored package: ' +
          str(total_ignore_cls_num / total_ignore_pkg_num))
    print('Package has sub package: ' + str(total_sub_pkg_num))

    # 打乱顺序
    # random.shuffle(res)

    # 将res拆分为train, valid, test，比例为6:2:2
    train_num = int(len(res) * 0.6)
    valid_num = int(len(res) * 0.2)
    test_num = len(res) - train_num - valid_num

    with open('../train_pkg.jsonl', 'w', encoding='utf-8') as f:
        for item in res[:train_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('../valid_pkg.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num:train_num+valid_num]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    with open('../test_pkg.jsonl', 'w', encoding='utf-8') as f:
        for item in res[train_num+valid_num:]:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
