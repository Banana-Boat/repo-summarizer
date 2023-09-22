import json
import os


def flatten_pkgs(packages, prefix, result):
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

    result = []
    result_root_path = "../result"

    for dir in os.listdir(result_root_path):
        if not os.path.isdir(os.path.join(result_root_path, dir)):
            continue

        for file in os.listdir(os.path.join(result_root_path, dir)):
            if file.startswith("sum_out_"):
                file_path = os.path.join(result_root_path, dir, file)
                with open(file_path, mode="r") as f_input:
                    pkgs = [json.load(f_input)]

                    flatten_pkgs(pkgs, "", result)

    with open('./out_jdk17.json', mode='w') as f_output:
        json.dump(result, f_output)
