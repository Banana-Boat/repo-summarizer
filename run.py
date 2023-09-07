import json
import os


def parse_repo(repo_path, output_path, log_path):
    # 处理输入输出路径
    if os.path.exists(repo_path) is False:
        raise Exception("repo_dir_path does not exist")
    output_dir_path = os.path.dirname(output_path)
    if os.path.exists(output_dir_path) is False:
        os.mkdir(output_dir_path)
    log_dir_path = os.path.dirname(log_path)
    if os.path.exists(log_dir_path) is False:
        os.mkdir(log_dir_path)

    return os.system(
        "java -jar ./java-repo-parser.jar -r={} -o={} -l={}".format(repo_path, output_path, log_path))


def summarize_by_llm(source, llm_tag):
    return ""


# 生成当前代码片段的摘要。若存在占位符<BLOCK>，则替换为对应位置代码片段的摘要
def summarize_code_snippet(code_snippet_json):
    # TODO:
    #   设计替换<BLOCK>的内容

    source = code_snippet_json["content"]
    summarization = ""

    # 按顺序对code_snippet进行摘要，替换source中的<BLOCK>
    for code_snippet in code_snippet_json["codeSnippets"]:
        code_snippet_sum = summarize_code_snippet(code_snippet)
        source = source.replace("<BLOCK>", "// " + code_snippet_sum, 1)

    summarization = summarize_by_llm(source, "MTH")

    return summarization


# 生成当前方法的摘要。若存在占位符<BLOCK>，则替换为对应位置代码片段的摘要
def summarize_method(method_json):
    # TODO:
    #   设计替换<BLOCK>的内容

    source = method_json["signature"] + method_json["body"]
    summarization = ""

    # 按顺序对code_snippet进行摘要，替换source中的<BLOCK>
    for code_snippet in method_json["codeSnippets"]:
        code_snippet_sum = summarize_code_snippet(code_snippet)
        source = source.replace("<BLOCK>", "// " + code_snippet_sum, 1)

    summarization = summarize_by_llm(source, "MTH")

    return summarization


# 根据类内方法生成当前类的摘要，如果没有方法则摘要为空
def summarize_cls(cls_json):
    source = ""
    summarization = ""

    if len(cls_json["methods"]) > 0:
        source += cls_json["signature"] + " {\n"

        for method in cls_json["methods"]:
            method_sum = summarize_method(method)
            if method_sum != "":
                source += "\t// " + summarize_method(method) + "\n"
            source += "\t" + method["signature"] + ";\n"

        source += "}"

        summarization = summarize_by_llm(source, "CLS")

    return summarization


def summarize_pkg(pkg_json):
    # TODO:
    #   将子包也作为摘要生成的上下文；
    #   是否需要设计prompt

    # 递归处理子包
    sub_pkg_summaries = []
    for sub_pkg in pkg_json["subPackages"]:
        sub_pkg_summaries.append(summarize_pkg(sub_pkg))

    # 根据包内类生成当前包的摘要
    source = ""
    summarization = ""
    if len(pkg_json["classes"]) > 0:
        for cls in pkg_json["classes"]:
            source += cls["signature"] + " "
            cls_sum = summarize_cls(cls)
            if cls_sum != "":
                source += "// " + summarize_cls(cls) + "\n"

        summarization = summarize_by_llm(source, "CLS")
    else:
        summarization = "*** No enough context for summarization ***"

    return {
        "name": pkg_json["name"],
        "summarization": summarization,
        "subPackages": sub_pkg_summaries
    }


if __name__ == "__main__":
    repo_name = "time"
    repo_path = "./repo/{}".format(repo_name)
    parse_output_path = "./tmp/{}_out.json".format(repo_name)
    parse_log_path = "./tmp/{}_log.txt".format(repo_name)
    summarize_output_path = "./{}_sum.json".format(repo_name)

    if (0 != parse_repo(repo_path, parse_output_path, parse_log_path)):
        raise Exception("RepoSummarizer: Parse code failed")

    with open(parse_output_path, "r") as parse_output_f, open(summarize_output_path, "w") as summarize_output_f:
        parsed_json = json.loads(parse_output_f.read())
        result = summarize_pkg(parsed_json)
        summarize_output_f.write(json.dumps(result))

    print("RepoSummarizer: Result file was written to {}".format(
        summarize_output_path))
    print("RepoSummarizer: Done!")
