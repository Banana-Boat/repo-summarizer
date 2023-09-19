import json
import logging
import os

from tqdm import tqdm

from summarizer import Summarizer


def parse_repo(repo_path, tokenizer_path, output_path, log_path) -> int:
    return os.system(
        "java -jar ./java-repo-parser.jar -r={} -t={} -o={} -l={}".format(
            repo_path, tokenizer_path, output_path, log_path)
    )


def create_logger():
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    return logger


if __name__ == "__main__":
    repo_root_path = "./repo/jdk-17-35-source-code"
    result_root_path = "./result"
    tokenizer_path = "./tokenizer.json"

    # 清空result目录中的内容
    os.system("rm -rf {}/*".format(result_root_path))

    # 创建 Logger
    logger = create_logger()

    # 创建 Summarizer
    summarizer = Summarizer(logger)

    dirs = os.listdir(repo_root_path)

    for dir in tqdm(dirs, desc="Processing modules..."):
        os.mkdir(os.path.join(result_root_path, dir))

        for sub_dir in os.listdir(os.path.join(repo_root_path, dir)):
            repo_path = os.path.join(repo_root_path, dir, sub_dir)
            if not os.path.isdir(repo_path):
                continue

            # 处理相关路径
            parse_log_path = os.path.join(
                result_root_path, dir, "parse_log_{}.txt".format(sub_dir))
            parse_output_path = os.path.join(
                result_root_path, dir, "parse_out_{}.json".format(sub_dir))
            summarize_log_path = os.path.join(
                result_root_path, dir, "sum_log_{}.txt".format(sub_dir))
            summarize_output_path = os.path.join(
                result_root_path, dir, "sum_out_{}.json".format(sub_dir))

            # 利用java-repo-parser解析repo
            if (0 != parse_repo(repo_path, tokenizer_path, parse_output_path, parse_log_path)):
                logging.error("Failed to parse repo: {}".format(repo_path))
                continue

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

                # 写入结果
                f_out.write(json.dumps(result))

    logger.info("RepoSummarizer: Done!")
