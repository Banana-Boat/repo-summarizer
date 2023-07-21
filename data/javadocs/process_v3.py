import json
import os
import re
from tqdm import tqdm
from bs4 import BeautifulSoup


def formatText(text):
    res = text.strip().replace('\n', ' ').replace('\t', ' ')
    res = re.sub(r'\s+', ' ', res)
    return res


if __name__ == '__main__':
    root_path = os.path.abspath('./v3')

    classes_and_interfaces = []

    for dirname in tqdm(os.listdir(root_path)):
        if not dirname.endswith('-javadoc'):
            continue

        repo_name = dirname[:-8]

        allclasses_soup = BeautifulSoup(
            open(os.path.join(root_path, dirname, 'allclasses-index.html'), "r", encoding='utf-8'), 'html.parser')

        # 遍历table
        all_class_table = allclasses_soup.find('table', class_='typeSummary')
        if all_class_table is None:
            continue
        for tr in all_class_table.find_all('tr')[1:]:
            class_div = tr.find('td', class_='colFirst')
            class_des_div = tr.find('th', class_='colLast')

            # 无描述或弃用的类class_des_div中没有block样式类
            des = class_des_div.find('div', class_='block')
            if des is None:
                continue

            # 获取class的概要说明（简短）
            class_des = formatText(des.get_text())

            class_name = formatText(class_div.get_text())
            # 忽略opencms-core中重复的Messages类
            if class_name == 'Messages':
                continue
            class_a = os.path.join(
                root_path, dirname, class_div.find('a').get('href'))

            # 读取class_a所指文件
            class_soup = BeautifulSoup(
                open(class_a, "r", encoding='utf-8'), 'html.parser')

            # 获取class的签名
            class_signature = formatText(class_soup.find(
                'div', class_='header').find('h2', class_='title').get_text())

            # 获取class的概要说明（详细）
            # class_description_section = class_soup.find(
            #     'section', class_='class-description')
            # class_description_block_div = class_description_section.find(
            #     'div', class_='block')

            # # 若存在pre标签或p标签，则删除第一个p或pre标签之后的内容
            # p_index = class_description_block_div.decode().find('<p>')
            # pre_index = class_description_block_div.decode().find('<pre>')

            # if p_index == -1 and pre_index != -1:
            #     class_des = class_description_block_div.decode()[:pre_index]
            # elif p_index != -1 and pre_index == -1:
            #     class_des = class_description_block_div.decode()[:p_index]
            # elif p_index != -1 and pre_index != -1:
            #     class_des = class_description_block_div.decode()[
            #         :min(p_index, pre_index)]
            # else:
            #     class_des = class_description_block_div.get_text()

            # class_des = formatText(BeautifulSoup(
            #     class_des, 'html.parser').get_text())

            # 获取class中的方法以及对应的描述
            methods_des = []
            table_a = class_soup.find('a', id='method.summary')
            if table_a is None:
                continue
            method_summary_table = table_a.find_next_sibling('table')
            if method_summary_table is None:
                continue
            for method_tr in method_summary_table.find_all('tr')[1:]:
                return_div = method_tr.find('td', class_='colFirst')
                method_div = method_tr.find('th', class_='colSecond')
                method_des_div = method_tr.find('td', class_='colLast')

                if return_div is None or method_div is None or method_des_div is None:
                    continue

                # 忽略通用方法的重写
                temp_str = formatText(method_div.get_text())
                if temp_str == 'toString()' or temp_str == 'equals()' or temp_str == 'hashCode()':
                    continue

                method_name = formatText(
                    return_div.get_text() + ' ' + method_div.get_text())
                method_des = formatText(method_des_div.get_text())

                methods_des.append({
                    'method_name': method_name,
                    'method_des': method_des,
                })

            if len(methods_des) == 0:
                continue

            classes_and_interfaces.append({
                'name': class_name,
                'signature': class_signature,
                'des': class_des,
                'methods_des': methods_des,
                'repo': repo_name,
            })

    # 将classes_des写入jsonl文件
    with open('../classes_and_interfaces_v3.jsonl', 'w', encoding='utf-8') as f:
        for item in classes_and_interfaces:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
