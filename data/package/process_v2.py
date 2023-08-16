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
    root_path = os.path.abspath('../javadocs/v2')

    packages = []

    for dirname in tqdm(os.listdir(root_path)):
        if not dirname.endswith('-javadoc'):
            continue

        repo_name = dirname[:-8]

        allclasses_soup = BeautifulSoup(
            open(os.path.join(root_path, dirname, 'allpackages-index.html'), "r", encoding='utf-8'), 'html.parser')

        pkg_summary_table = allclasses_soup.find(
            'div', class_='summary-table')
        if pkg_summary_table is None:
            continue

        # 删除table-header样式类的子div
        for div in pkg_summary_table.find_all('div', class_='table-header'):
            div.decompose()

        for pkg_name_div, pkg_des_div in zip(pkg_summary_table.find_all('div', class_='col-first'),
                                            pkg_summary_table.find_all('div', class_='col-last')):

            # 无描述或弃用的类class_des_div中没有block样式类
            pkg_des_div = pkg_des_div.find('div', class_='block')
            if pkg_des_div is None:
                continue

            pkg_des = formatText(pkg_des_div.get_text())
            pkg_name = pkg_name_div.get_text().split('.')[-1]
            pkg_a = os.path.join(
                root_path, dirname, pkg_name_div.find('a').get('href'))

            # 读取pkg_a所指文件，若无法打开文件，则跳过
            try:
                class_soup = BeautifulSoup(
                    open(pkg_a, "r", encoding='utf-8'), 'html.parser')
            except:
                continue

            # 获取interfaces / classes / enums的概要说明
            summaries = []
            summary_div = class_soup.find('div', id='class-summary')
            if summary_div is None:
                continue
            summary_table = summary_div.find('div', class_='summary-table')
            if summary_table is None:
                continue
            # 删除table-header样式类的子div
            for div in summary_table.find_all('div', class_='table-header'):
                div.decompose()

            for class_name_div, class_des_div in zip(summary_table.find_all('div', class_='col-first'),
                                                summary_table.find_all('div', class_='col-last')):
                class_des_div = class_des_div.find('div', class_='block')
                if class_des_div is None:
                    class_des = ""
                else:
                    class_des = formatText(class_des_div.get_text())
                class_name = class_name_div.get_text()

                #删去pkg_a的最后一项
                pkg_root_path = pkg_a.split('/')[0:-1]
                pkg_root_path = '/'.join(pkg_root_path)
                class_a = os.path.join(pkg_root_path, class_name_div.find('a').get('href'))

                # 读取class_a所指文件，若无法打开文件，则跳过
                try:
                    class_soup = BeautifulSoup(
                        open(class_a, "r", encoding='utf-8'), 'html.parser')
                except:
                    print('Error: ' + class_a)
                    continue

                # 获取class的签名
                class_signature = formatText(class_soup.find(
                    'div', class_='type-signature').get_text())

                summaries.append({
                    'name': class_name,
                    'signature': class_signature,
                    'des': class_des,
                })

            if len(summaries) == 0:
                continue

            packages.append({
                'name': pkg_name,
                'des': pkg_des,
                'summaries': summaries,
                'repo': repo_name,
            })

    with open('./packages_v2.jsonl', 'w', encoding='utf-8') as f:
        for item in packages:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
