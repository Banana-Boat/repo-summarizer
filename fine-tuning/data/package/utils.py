import re


def formatText(text):
    res = text.strip().replace('\n', ' ').replace('\t', ' ')
    res = re.sub(r'\s+', ' ', res)
    return res


def add_sub_packages(pkgs: list):
    for pkg in pkgs:
        sub_pkgs = []

        # 遍历所有包，找到一级子包
        for pgk_tmp in pkgs:
            parent_pkg_name = ".".join(pgk_tmp['name'].split('.')[:-1])
            if parent_pkg_name == pkg['name']:
                sub_pkgs.append({
                    'name': pgk_tmp['name'].split('.')[-1],
                    'des': pgk_tmp['des'],
                })

        pkg['subPackages'] = sub_pkgs
        pkg['name'] = pkg['name'].split('.')[-1]
