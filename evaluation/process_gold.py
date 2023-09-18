import json
import os
import re
from bs4 import BeautifulSoup


def formatText(text):
    res = text.strip().replace('\n', ' ').replace('\t', ' ')
    res = re.sub(r'\s+', ' ', res)
    return res


if __name__ == '__main__':
    file_path = os.path.abspath(
        './javadocs/jdk-17.0.8/api/allpackages-index.html')

    packages = []

    allclasses_soup = BeautifulSoup(
        open(os.path.join(file_path), "r", encoding='utf-8'), 'html.parser')

    pkg_summary_tables = allclasses_soup.find('div', class_='summary-table')

    for div in pkg_summary_tables.find_all('div', class_='table-header'):
        div.decompose()

    for pkg_div, pkg_des_div in zip(pkg_summary_tables.find_all('div', class_='col-first'),
                                    pkg_summary_tables.find_all('div', class_='col-last')):
        # 无描述或弃用的类class_des_div中没有block样式类
        des = pkg_des_div.find('div', class_='block')
        if des is None:
            continue

        # 获取class的概要说明（简短）
        pkg_name = pkg_div.get_text()
        pkg_des = formatText(des.get_text())

        packages.append({
            'name': pkg_name,
            'des': pkg_des
        })

    with open('./gold_jdk17.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(packages, ensure_ascii=False))
