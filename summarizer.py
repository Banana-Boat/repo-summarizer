import logging
import os
import torch
from transformers import (RobertaTokenizer, T5Config,
                          T5ForConditionalGeneration)


class Summarizer:
    model_name = "Salesforce/codet5-base-multi-sum"
    max_target_length = 30

    def __init__(self, logger: logging.Logger):
        self.logger = logger

        # 加载模型
        model_config = T5Config.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(
            self.model_name, config=model_config)
        self.tokenizer = RobertaTokenizer.from_pretrained(self.model_name)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(device)

    def summarize_by_llm(self, source: str, llm_tag) -> str:
        encoded_code = self.tokenizer(source, return_tensors='pt',
                                      max_length=self.max_source_length,
                                      padding=True, verbose=False,
                                      add_special_tokens=True, truncation=True)

        generated_texts_ids = self.model.generate(input_ids=encoded_code['input_ids'],
                                                  attention_mask=encoded_code['attention_mask'],
                                                  max_length=self.max_target_length)

        generated_text = self.tokenizer.decode(generated_texts_ids[0],
                                               skip_special_tokens=True, clean_up_tokenization_spaces=False)

        return generated_text

    # 生成当前代码片段的摘要。若存在占位符<BLOCK>，则替换为对应位置代码片段的摘要
    def summarize_code_snippet(self, code_snippet_json) -> str:
        # TODO:
        #   设计替换<BLOCK>的内容

        source = code_snippet_json["content"]
        summarization = ""

        # 按顺序对code_snippet进行摘要，替换source中的<BLOCK>
        for code_snippet in code_snippet_json["codeSnippets"]:
            code_snippet_sum = self.summarize_code_snippet(code_snippet)
            source = source.replace("<BLOCK>", "// " + code_snippet_sum, 1)

        summarization = self.summarize_by_llm(source, "MTH")

        return summarization

    # 生成当前方法的摘要。若存在占位符<BLOCK>，则替换为对应位置代码片段的摘要
    def summarize_method(self, method_json) -> str:
        # TODO:
        #   设计替换<BLOCK>的内容

        source = method_json["signature"] + method_json["body"]
        summarization = ""

        # 按顺序对code_snippet进行摘要，替换source中的<BLOCK>
        for code_snippet in method_json["codeSnippets"]:
            code_snippet_sum = self.summarize_code_snippet(code_snippet)
            source = source.replace("<BLOCK>", "// " + code_snippet_sum, 1)

        summarization = self.summarize_by_llm(source, "MTH")

        return summarization

    # 根据类内方法生成当前类的摘要，如果没有方法则摘要为空
    def summarize_cls(self, cls_json) -> str:
        source = ""
        summarization = ""

        if len(cls_json["methods"]) > 0:
            source += cls_json["signature"] + " {\n"

            for method in cls_json["methods"]:
                method_sum = self.summarize_method(method)
                if method_sum != "":
                    source += "\t// " + self.summarize_method(method) + "\n"
                source += "\t" + method["signature"] + ";\n"

            source += "}"

            summarization = self.summarize_by_llm(source, "CLS")

        return summarization

    def summarize_pkg(self, pkg_json):
        # TODO:
        #   将子包也作为摘要生成的上下文；
        #   是否需要设计prompt

        # 递归处理子包
        sub_pkg_summaries = []
        for sub_pkg in pkg_json["subPackages"]:
            sub_pkg_summaries.append(self.summarize_pkg(sub_pkg))

        # 根据包内类生成当前包的摘要
        source = ""
        summarization = ""
        if len(pkg_json["classes"]) > 0:
            for cls in pkg_json["classes"]:
                source += cls["signature"] + " "
                cls_sum = self.summarize_cls(cls)
                if cls_sum != "":
                    source += "// " + self.summarize_cls(cls) + "\n"

            summarization = self.summarize_by_llm(source, "CLS")
        else:
            summarization = "*** No enough context for summarization ***"

        return {
            "name": pkg_json["name"],
            "summarization": summarization,
            "subPackages": sub_pkg_summaries
        }
