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
    root_path = os.path.abspath('./v2')

    classes_and_interfaces = []

    for dirname in tqdm(os.listdir(root_path)):
        if not dirname.endswith('-javadoc'):
            continue

        repo_name = dirname[:-8]

        allclasses_soup = BeautifulSoup(
            open(os.path.join(root_path, dirname, 'allclasses-index.html'), "r", encoding='utf-8'), 'html.parser')

        # 获取包含summary-table样式类的div
        summary_table_div = allclasses_soup.find('div', class_='summary-table')

        # 删除summary-table_div中包含table-header样式类的子div
        for div in summary_table_div.find_all('div', class_='table-header'):
            div.decompose()

        # 遍历summary-table_div中的子div
        for class_div, class_des_div in zip(summary_table_div.find_all('div', class_='col-first'),
                                            summary_table_div.find_all('div', class_='col-last')):
            # 无描述或弃用的类class_des_div中没有block样式类
            des = class_des_div.find('div', class_='block')
            if des is None:
                continue

            # 获取class的概要说明（简短）
            class_des = formatText(des.get_text())

            class_name = class_div.get_text()
            class_a = os.path.join(
                root_path, dirname, class_div.find('a').get('href'))

            # 读取class_a所指文件
            class_soup = BeautifulSoup(
                open(class_a, "r", encoding='utf-8'), 'html.parser')

            # 获取class的签名
            class_signature = formatText(class_soup.find(
                'div', class_='type-signature').get_text())

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
            method_summary_section = class_soup.find(
                'section', class_='method-summary')
            if method_summary_section is None:
                continue
            method_summary_table_div = method_summary_section.find(
                'div', class_='summary-table')
            if method_summary_table_div is None:
                continue

            # 删除summary-table_div中包含table-header样式类的子div
            for div in method_summary_table_div.find_all('div', class_='table-header'):
                div.decompose()

            for return_div, method_div, method_des_div in zip(
                    method_summary_table_div.find_all(
                        'div', class_='col-first'),
                    method_summary_table_div.find_all(
                        'div', class_='col-second'),
                    method_summary_table_div.find_all('div', class_='col-last')):

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
    with open('../classes_and_interfaces_v2.jsonl', 'w', encoding='utf-8') as f:
        for item in classes_and_interfaces:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
