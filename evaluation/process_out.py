import json


def flatten_pkgs(packages, prefix="", result=[]):
    for package in packages:
        full_name = f"{prefix}.{package['name']}" if prefix else package['name']
        result.append({
            "name": full_name,
            "des": package['summarization']
        })
        if package['subPackages']:
            flatten_pkgs(package['subPackages'], full_name, result)

    return result


if __name__ == '__main__':
    repo_name = "time"

    pkgs = []
    flattened_pkgs = []

    with open("../result/sum_out_{}.json".format(repo_name), mode="r") as f_input:
        pkgs = json.load(f_input)

    flattened_pkgs = flatten_pkgs([pkgs])

    with open('./out/out_{}.json'.format(repo_name), mode='w') as f_output:
        json.dump(flattened_pkgs, f_output, indent=4)
