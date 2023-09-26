import datetime
import random
from time import sleep

import torch
from bleu import computeMaps, bleuFromMaps
from tqdm import tqdm
from transformers import RobertaTokenizer, T5ForConditionalGeneration, T5Config, AutoTokenizer
import json

if __name__ == '__main__':
    model_name = 'Salesforce/codet5-base'

    model_config = T5Config.from_pretrained(model_name, mirror='tuna')
    model = T5ForConditionalGeneration.from_pretrained(
        model_name, config=model_config, mirror='tuna')
    tokenizer = AutoTokenizer.from_pretrained(model_name, mirror='tuna')

    # 加载模型参数
    load_state_path = "../model/pkg_0925_1631/checkpoint-best-bleu/pytorch_model.bin"
    model.load_state_dict(torch.load(load_state_path, map_location="cpu"))

    source = "Package: support\n\nSub Packages: \npackage support.state; // States used in defining the underlying Spring Batch state machine\n\nClasses and Interfaces: \npublic class DefaultStateTransitionComparator extends Object implements Comparator<StateTransition>; // Sorts by decreasing specificity of pattern, based on just counting wildcards (with * taking precedence over ?).\npublic class SimpleFlow extends Object implements Flow, org.springframework.beans.factory.InitializingBean; // A Flow that branches conditionally depending on the exit status of the last State.\npublic final class StateTransition extends Object; // Value object representing a potential transition from one State to another.\n"
    source += "Summarization: "

    encoded_code = tokenizer(source, return_tensors='pt',
                             max_length=512,
                             padding=True, verbose=False,
                             add_special_tokens=True, truncation=True)

    generated_texts_ids = model.generate(input_ids=encoded_code['input_ids'],
                                         attention_mask=encoded_code['attention_mask'],
                                         max_length=30)

    generated_text = tokenizer.decode(generated_texts_ids[0],
                                      skip_special_tokens=True, clean_up_tokenization_spaces=False)

    print(generated_text)

    # predictions = []

    # with open('./data/valid.jsonl', "r") as valid_file, open('./log/valid.out', "w", encoding="utf-8") as out_file, open('./log/valid.gold', "w", encoding="utf-8") as gold_file:
    #     lines = valid_file.readlines()
    #     random.shuffle(lines)
    #     for line in tqdm(lines):
    #         obj = json.loads(line)

    #         input_ids = tokenizer(
    #             obj['code'], max_length=512, truncation=True, return_tensors="pt").input_ids
    #         generated_ids = model.generate(input_ids, max_length=30)
    #         res = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

    #         predictions.append(str(obj['index']) + '\t' + res)
    #         out_file.write(str(obj['index']) + '\t' + res + '\n')
    #         gold_file.write(str(obj['index']) + '\t' + obj['des'] + '\n')

    # (goldMap, predictionMap) = computeMaps(predictions, "./log/valid.gold")
    # this_bleu = round(bleuFromMaps(goldMap, predictionMap)[0], 2)

    # print(this_bleu)
