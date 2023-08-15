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

    packages = []

    for dirname in tqdm(os.listdir(root_path)):
        if not dirname.endswith('-javadoc'):
            continue

        repo_name = dirname[:-8]

        allclasses_soup = BeautifulSoup(
            open(os.path.join(root_path, dirname, 'overview-summary.html'), "r", encoding='utf-8'), 'html.parser')

        overview_summary_tables = allclasses_soup.find_all(
            'table', class_='overviewSummary')
        if len(overview_summary_tables) == 0:
            continue

        for table in overview_summary_tables:
            overview_summary_tbody = table.find('tbody')

            for tr in overview_summary_tbody.find_all('tr'):
                pkg_name_div = tr.find('td', class_='colFirst')
                pkg_des_div = tr.find('td', class_='colLast')
                if pkg_des_div is None:
                    continue
                pkg_des_div = pkg_des_div.find('div', class_='block')
                # 忽略没有描述的包
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
                summary_lis = class_soup.find_all('li', class_='blockList')
                if len(summary_lis) == 0:
                    continue
                for li in summary_lis:
                    summary_tbody = li.find('tbody')
                    if summary_tbody is None:
                        continue
                    for summary_tr in summary_tbody.find_all('tr'):
                        class_name_div = summary_tr.find('td', class_='colFirst')
                        class_des_div = summary_tr.find('td', class_='colLast')
                        if class_des_div is None:
                            continue
                        class_des_div = class_des_div.find('div', class_='block')
                        if class_des_div is None:
                            class_des = ""
                        else:
                            class_des = formatText(class_des_div.get_text())

                        class_name = class_name_div.get_text()
                        class_a = os.path.join(
                            root_path, dirname, class_name_div.find('a').get('href').replace('../', '').replace('./', ''))

                        # 读取class_a所指文件，若无法打开文件，则跳过
                        try:
                            class_soup = BeautifulSoup(
                                open(class_a, "r", encoding='utf-8'), 'html.parser')
                        except:
                            print('Error: ' + class_a)
                            continue

                        # 获取class的签名
                        class_signature = formatText(class_soup.find(
                            'div', class_='header').find('h2', class_='title').get_text())
                        class_signature = class_signature.replace('类', 'class').replace(
                            '接口', 'interface').replace('枚举', 'enum')

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

    with open('./packages_v1.jsonl', 'w', encoding='utf-8') as f:
        for item in packages:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
