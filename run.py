import json
import logging
import os

from summarizer import Summarizer


def parse_repo(repo_path, output_path, log_path) -> int:
    return os.system(
        "java -jar ./java-repo-parser.jar -r={} -o={} -l={}".format(repo_path, output_path, log_path))


# 检查路径列表中各路径包含的目录路径，若不存在则创建
def exam_dir_paths(paths):
    for path in paths:
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)


def create_logger(log_path):
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 写入文件
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    # 写入控制台
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    return logger


if __name__ == "__main__":
    # 处理相关路径
    repo_name = "time"
    repo_path = "./repo/{}".format(repo_name)
    parse_log_path = "./tmp/parse_log_{}.txt".format(repo_name)
    parse_output_path = "./tmp/parse_out_{}.json".format(repo_name)
    summarize_log_path = "./tmp/sum_log_{}.txt".format(repo_name)
    summarize_output_path = "./sum_out_{}.json".format(repo_name)

    if not os.path.exists(repo_path):
        print("Repo's path does not exist")
        exit(1)
    exam_dir_paths([
        parse_log_path, parse_output_path, summarize_log_path, summarize_output_path
    ])

    # 创建 Logger
    logger = create_logger(summarize_log_path)

    # 利用java-repo-parser解析repo
    if (0 != parse_repo(repo_path, parse_output_path, parse_log_path)):
        logging.error("Failed to parse repo")
        exit(1)

    # 创建 Summarizer
    summarizer = Summarizer(logger)

    # 生成摘要并写入文件
    with open(parse_output_path, "r") as parse_output_f, open(summarize_output_path, "w") as summarize_output_f:
        parsed_json = json.loads(parse_output_f.read())
        result = summarizer.summarize_pkg(parsed_json)
        summarize_output_f.write(json.dumps(result))

    logger.info("Summarization result file was written to {}".format(
        summarize_output_path))
    logger.info("Summarization log file was written to {}".format(
        summarize_log_path))
    logger.info("RepoSummarizer: Done!")
