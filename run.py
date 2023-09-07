import os


def parse_code(repo_path, output_path, log_path):
    # 处理输入输出路径
    if os.path.exists(repo_path) is False:
        raise Exception("repo_dir_path does not exist")
    output_dir_path = os.path.dirname(output_path)
    if os.path.exists(output_dir_path) is False:
        os.mkdir(output_dir_path)

    os.system(
        "java -jar ./java-code-parser.jar -r={} -o={} -l={}".format(repo_path, output_path, log_path))


if __name__ == "__main__":
    repo_name = "time"
    parse_code("./repo/{}".format(repo_name),
               "./tmp/{}_out.json".format(repo_name), "./tmp/{}_log.txt".format(repo_name))
