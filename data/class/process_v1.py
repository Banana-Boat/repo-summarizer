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
    root_path = os.path.abspath('../javadocs/v1')

    classes_and_interfaces = []

    for dirname in tqdm(os.listdir(root_path)):
        if not dirname.endswith('-javadoc'):
            continue

        repo_name = dirname[:-8]

        allclasses_soup = BeautifulSoup(
            open(os.path.join(root_path, dirname, 'allclasses-noframe.html'), "r", encoding='utf-8'), 'html.parser')

        # 获取包含summary-table样式类的div
        index_container_div = allclasses_soup.find(
            'div', class_='indexContainer')

        for li in index_container_div.find_all('li'):
            class_name = li.find('a').get_text()
            class_a = os.path.join(
                root_path, dirname, li.find('a').get('href'))

            # 读取class_a所指文件，若无法打开文件，则跳过
            try:
                class_soup = BeautifulSoup(
                    open(class_a, "r", encoding='utf-8'), 'html.parser')
            except:
                continue

            # 获取class的签名
            class_signature = formatText(class_soup.find(
                'div', class_='header').find('h2', class_='title').get_text())
            class_signature = class_signature.replace('类', 'class').replace(
                '接口', 'interface').replace('枚举', 'enum')

            # 获取class的概要说明（详细）
            class_description_div = class_soup.find(
                'div', class_='description')
            # 忽略已弃用的类
            class_derecated_div = class_description_div.find(
                'span', class_='deprecatedLabel')
            if class_derecated_div is not None:
                continue
            class_description_block_div = class_description_div.find(
                'div', class_='block')
            # 忽略没有描述的类
            if class_description_block_div is None:
                continue

            # 若存在pre标签或p标签，则删除第一个p或pre标签之后的内容
            p_index = class_description_block_div.decode().find('<p>')
            pre_index = class_description_block_div.decode().find('<pre>')

            if p_index == -1 and pre_index != -1:
                class_des = class_description_block_div.decode()[:pre_index]
            elif p_index != -1 and pre_index == -1:
                class_des = class_description_block_div.decode()[:p_index]
            elif p_index != -1 and pre_index != -1:
                class_des = class_description_block_div.decode()[
                    :min(p_index, pre_index)]
            else:
                class_des = class_description_block_div.get_text()

            class_des = formatText(BeautifulSoup(
                class_des, 'html.parser').get_text())

            # 获取class中的方法以及对应的描述
            methods = []
            table_a = class_soup.find('a', {'name': 'method.summary'})
            if table_a is None:
                continue

            method_summary_table = table_a.find_next_sibling('table')
            if method_summary_table is None:
                continue

            for method_tr in method_summary_table.find_all('tr')[1:]:
                return_div = method_tr.find('td', class_='colFirst')
                method_div = method_tr.find('td', class_='colLast')

                # 忽略已弃用的方法
                method_deprecated_div = method_div.find(
                    'span', class_='deprecatedLabel')
                if method_deprecated_div is not None:
                    continue

                method_des_div = method_div.find('div', class_='block')
                if method_des_div is None:
                    method_des = ''
                else:
                    method_des = formatText(method_des_div.get_text())
                    method_des_div.decompose()

                method_name = formatText(
                    return_div.get_text() + ' ' + method_div.get_text())

                # 忽略通用方法的重写
                temp_str = formatText(method_div.get_text())
                if temp_str == 'toString()' or temp_str == 'equals()' or temp_str == 'hashCode()':
                    continue

                methods.append({
                    'name': method_name,
                    'des': method_des,
                })

            if len(methods) == 0:
                continue

            classes_and_interfaces.append({
                'name': class_name,
                'signature': class_signature,
                'des': class_des,
                'methods': methods,
                'repo': repo_name,
            })

    # 将classes_des写入jsonl文件
    with open('./classes_v1.jsonl', 'w', encoding='utf-8') as f:
        for item in classes_and_interfaces:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
