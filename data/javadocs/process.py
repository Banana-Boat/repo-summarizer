import json
import os
import re
from tqdm import tqdm
from bs4 import BeautifulSoup


def convertToPureText(text):
    res = re.sub(
        r'\s+', ' ', text.strip())  # 替换空格和换行符
    res = re.sub(r'<.*?>', '', res)  # 替换a标签
    res = re.sub(r'\s+', ' ', res)  # 替换空格和换行符

    return res


if __name__ == '__main__':
    cur_path = os.path.abspath('.')

    classes = []

    for dirname in tqdm(os.listdir(cur_path)):
        if not dirname.endswith('-javadoc'):
            continue

        project_name = dirname[:-8]

        allclasses_soup = BeautifulSoup(
            open(dirname + '/allclasses-index.html', encoding='utf-8'), 'html.parser')

        # 获取包含summary-table样式类的div
        summary_table_div = allclasses_soup.find('div', class_='summary-table')

        # 删除summary-table_div中包含table-header样式类的子div
        for div in summary_table_div.find_all('div', class_='table-header'):
            div.decompose()

        # 两个两个的遍历summary-table_div中的子div
        for class_div, class_des_div in zip(summary_table_div.find_all('div', class_='col-first'),
                                            summary_table_div.find_all('div', class_='col-last')):
            # 无描述或弃用的类class_des_div中没有block样式类
            des = class_des_div.find('div', class_='block')
            if des is None:
                continue

            class_name = class_div.find('a').text
            class_a = os.path.join(
                cur_path, dirname, class_div.find('a').get('href'))

            # 读取class_a所指文件
            class_soup = BeautifulSoup(
                open(class_a, encoding='utf-8'), 'html.parser')

            # 获取class的概要说明
            class_description_section = class_soup.find(
                'section', class_='class-description')
            class_description_block_div = class_description_section.find(
                'div', class_='block')
            class_des = convertToPureText(class_description_block_div.text)

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
                method_name = convertToPureText(
                    return_div.text) + ' ' + convertToPureText(method_div.text)
                method_des = convertToPureText(method_des_div.text)

                methods_des.append({
                    'method_name': method_name,
                    'method_des': method_des,
                })

            classes.append({
                'class_name': class_name,
                'class_des': class_des,
                'methods_des': methods_des,
                'project_name': project_name,
            })

    # 将classes_des写入jsonl文件
    with open('../classes.jsonl', 'w', encoding='utf-8') as f:
        for item in classes:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print('total_num:', len(classes))
