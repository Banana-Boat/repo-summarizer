import json
import logging
import os

from summarizer import Summarizer


def parse_repo(repo_path, tokenizer_path, output_path, log_path) -> int:
    return os.system(
        "java -jar ./java-repo-parser.jar -r={} -t={} -o={} -l={}".format(
            repo_path, tokenizer_path, output_path, log_path)
    )


# 检查路径列表中各路径包含的目录路径，若不存在则创建
def exam_dir_paths(paths):
    for path in paths:
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)


def create_logger():
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    return logger


if __name__ == "__main__":
    # 创建 Logger
    logger = create_logger()

    # 处理相关路径
    repo_name = "time"
    repo_path = "./repo/{}".format(repo_name)
    tokenizer_path = "./tokenizer.json"
    parse_log_path = "./result/parse_log_{}.txt".format(repo_name)
    parse_output_path = "./result/parse_out_{}.json".format(repo_name)
    summarize_log_path = "./result/sum_log_{}.txt".format(repo_name)
    summarize_output_path = "./result/sum_out_{}.json".format(repo_name)

    if not os.path.exists(repo_path):
        logger.error("Repo's path does not exist")
        exit(1)

    if not os.path.exists(tokenizer_path):
        logger.error("Tokenizer.json file does not exist")
        exit(1)

    exam_dir_paths([
        parse_log_path, parse_output_path, summarize_log_path, summarize_output_path
    ])

    # 利用java-repo-parser解析repo
    if (0 != parse_repo(repo_path, tokenizer_path, parse_output_path, parse_log_path)):
        logging.error("Failed to parse repo")
        exit(1)

    # 创建 Summarizer
    summarizer = Summarizer(logger)
    result = {}
    sum_logs = []

    # 生成摘要
    with open(parse_output_path, "r") as f:
        parsed_json = json.loads(f.read())
        sum_logs, result = summarizer.summarize_repo(parsed_json)

    # 写入文件
    with open(summarize_output_path, "w") as f_out, open(summarize_log_path, "w") as f_log:
        # 写入日志
        for log in sum_logs:
            f_log.write(log + "\n")
        logger.info("Log file of summarization was written to {}".format(
            summarize_log_path))

        # 写入结果
        f_out.write(json.dumps(result))
        logger.info("Result file of summarization was written to {}".format(
            summarize_output_path))

    logger.info("RepoSummarizer: Done!")
