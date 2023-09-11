import json
import logging
import os

from summarizer import Summarizer


def parse_repo(logger: logging.Logger, repo_path, output_path, log_path) -> int:
    # 处理相关路径
    if not os.path.exists(repo_path):
        logger.error("Repo's path does not exist")
        exit(1)
    output_dir_path = os.path.dirname(output_path)
    if os.path.exists(output_dir_path) is False:
        os.mkdir(output_dir_path)
    log_dir_path = os.path.dirname(log_path)
    if os.path.exists(log_dir_path) is False:
        os.mkdir(log_dir_path)

    return os.system(
        "java -jar ./java-repo-parser.jar -r={} -o={} -l={}".format(repo_path, output_path, log_path))


if __name__ == "__main__":
    # 创建 Logger
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 处理相关路径
    repo_name = "time"
    repo_path = "./repo/{}".format(repo_name)
    parse_output_path = "./tmp/{}_out.json".format(repo_name)
    parse_log_path = "./tmp/{}_log.txt".format(repo_name)
    summarize_output_path = "./{}_sum.json".format(repo_name)

    # 创建 Summarizer
    summarizer = Summarizer(logger)

    # 解析 repo
    if (0 != parse_repo()):
        logging.error("Failed to parse repo")
        exit(1)

    # 生成摘要并写入文件
    with open(parse_output_path, "r") as parse_output_f, open(summarize_output_path, "w") as summarize_output_f:
        parsed_json = json.loads(parse_output_f.read())
        result = summarizer.summarize_pkg(parsed_json)
        summarize_output_f.write(json.dumps(result))

    logger.info("Result file was written to {}".format(
        summarize_output_path))
    logger.info("RepoSummarizer: Done!")
