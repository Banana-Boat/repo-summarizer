import logging
from typing import Tuple
import torch
from enum import Enum
from tqdm import tqdm
from transformers import (AutoTokenizer, T5Config,
                          T5ForConditionalGeneration)


class MODEL_TAG(Enum):
    CODE = "CODE"
    CLS = "CLS"
    PKG = "PKG"


class Summarizer:
    sum_logs = []

    model_dict = {
        MODEL_TAG.CODE: {
            "name": "Salesforce/codet5-base-multi-sum",
            "max_source_length": 512,
            "max_target_length": 30,
        },
        MODEL_TAG.CLS: {
            "name": "Salesforce/codet5-base-multi-sum",
            "max_source_length": 512,
            "max_target_length": 30,
            "load_state_path": "model/cls_0914_0930/checkpoint-best-bleu/pytorch_model.bin"
        },
        MODEL_TAG.PKG: {
            "name": "Salesforce/codet5-base-multi-sum",
            "max_source_length": 512,
            "max_target_length": 30,
            "load_state_path": "model/pkg_0917_1057/checkpoint-best-bleu/pytorch_model.bin"
        }
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger

        # 加载模型

        # device = torch.device(
        #     "cuda" if torch.cuda.is_available() else "cpu")
        # os.environ["CUDA_VISIBLE_DEVICES"] = "0"

        for tag, val in self.model_dict.items():
            model_config = T5Config.from_pretrained(val["name"])
            model = T5ForConditionalGeneration.from_pretrained(
                val["name"], config=model_config)
            tokenizer = AutoTokenizer.from_pretrained(val["name"])

            # 加载模型参数
            if 'load_state_path' in val:
                logger.info("Load model state from {}".format(
                    val["load_state_path"]))
                model.load_state_dict(torch.load(
                    val["load_state_path"], map_location="cpu"))  # 将GPU上训练的模型权重加载到CPU上

            # model = model.to(device)

            self.model_dict[tag]["model"] = model
            self.model_dict[tag]["tokenizer"] = tokenizer

            self.logger.info("Model for {} loaded successfully".format(tag))

    # 判断输入token数是否合法
    def isLegalSource(self, source, model_tag: MODEL_TAG):
        model_obj = self.model_dict[model_tag]

        encoded = model_obj['tokenizer'].encode(
            source, add_special_tokens=True)
        return len(encoded) <= model_obj['max_source_length']

    def summarize_by_llm(self, source: str, model_tag: MODEL_TAG) -> str:
        model_obj = self.model_dict[model_tag]

        encoded_code = model_obj['tokenizer'](source, return_tensors='pt',
                                              max_length=model_obj['max_source_length'],
                                              padding=True, verbose=False,
                                              add_special_tokens=True, truncation=True)

        generated_texts_ids = model_obj['model'].generate(input_ids=encoded_code['input_ids'],
                                                          attention_mask=encoded_code['attention_mask'],
                                                          max_length=model_obj['max_target_length'])

        generated_text = model_obj['tokenizer'].decode(generated_texts_ids[0],
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

        summarization = self.summarize_by_llm(source, MODEL_TAG.CODE)

        self.sum_logs.append(
            "{}\n{}\n<=\n{}".format("CODE======================================================",
                                    summarization, source))
        self.pbar.update(1)

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

        summarization = self.summarize_by_llm(source, MODEL_TAG.CODE)

        self.sum_logs.append(
            "{}\n{}\n<=\n{}".format("METHOD======================================================",
                                    summarization, source))
        self.pbar.update(1)

        return summarization

    # 根据类内方法生成当前类的摘要，如果没有方法则摘要为空
    def summarize_cls(self, cls_json) -> str:
        source = cls_json["signature"]
        summarization = ""

        if len(cls_json["methods"]) > 0:
            source += " {\n"

            for method in cls_json["methods"]:
                method_sum = self.summarize_method(method)
                tmp_str = "\t" + method["signature"] + \
                    "; // " + method_sum + "\n"

                # 忽略超出token限制的方法
                if not self.isLegalSource(source + tmp_str, MODEL_TAG.CLS):
                    break

                source += tmp_str

            source += "}"

            summarization = self.summarize_by_llm(source, MODEL_TAG.CLS)
            self.sum_logs.append(
                "{}\n{}\n<=\n{}".format("CLASS======================================================",
                                        summarization, source))
        else:
            self.sum_logs.append(
                "{}\n{}\n<=\n{}".format("CLASS======================================================",
                                        "*** No enough context for summarization ***", source))

        self.pbar.update(1)

        return summarization

    def summarize_pkg(self, pkg_json) -> dict:
        # TODO:
        #   是否需要设计prompt

        # 递归处理子包
        sub_pkg_summaries = []
        for sub_pkg in pkg_json["subPackages"]:
            sub_pkg_summaries.append(self.summarize_pkg(sub_pkg))

        # 根据子包与包内类的摘要生成当前包的摘要
        summarization = ""
        source = 'package ' + pkg_json['name'] + ';\n\n'

        for sub_pkg in sub_pkg_summaries:
            tmp_str = 'package ' + \
                pkg_json['name'] + '.' + sub_pkg['name'] + \
                '; // ' + sub_pkg['summarization'] + '\n'

            # 忽略超出字符限制的子包
            if not self.isLegalSource(source + tmp_str, MODEL_TAG.PKG):
                break

            source += tmp_str

        for cls in pkg_json["classes"]:
            tmp_str = ""
            cls_sum = self.summarize_cls(cls)
            tmp_str += cls["signature"] + ";"
            if cls_sum != "":
                tmp_str += " // " + cls_sum
            tmp_str += "\n"

            if not self.isLegalSource(source + tmp_str, MODEL_TAG.PKG):
                break

            source += tmp_str

        summarization = self.summarize_by_llm(source, MODEL_TAG.PKG)

        self.sum_logs.append(
            "{}\n{}\n<=\n{}".format("PACKAGE======================================================",
                                    summarization, source))
        self.pbar.update(1)

        return {
            "name": pkg_json["name"],
            "summarization": summarization,
            "subPackages": sub_pkg_summaries
        }

    def summarize_repo(self, repo_json) -> Tuple[list, dict]:
        with tqdm(total=repo_json['nodeCount']) as pbar:
            pbar.set_description("Summarizing repo...")
            self.pbar = pbar

            return self.sum_logs, self.summarize_pkg(repo_json['mainPackage'])
