import datetime
from bleu import computeMaps, bleuFromMaps
from tqdm import tqdm
from transformers import RobertaTokenizer, T5ForConditionalGeneration
import json

if __name__ == '__main__':
    model_name = 'codet5-base-multi-sum'

    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/' + model_name)
    model = T5ForConditionalGeneration.from_pretrained('Salesforce/' + model_name)

    predictions = []

    with open('./data/valid.jsonl', "r") as valid_file, open('./log/valid.out', "w", encoding="utf-8") as out_file, open('./log/valid.gold', "w", encoding="utf-8") as gold_file:
        for line in tqdm(valid_file):
            obj = json.loads(line)

            if obj['index'] == 1000:
                break

            input_ids = tokenizer(obj['code'], max_length=510, truncation=True, return_tensors="pt").input_ids
            generated_ids = model.generate(input_ids, max_length=20)
            res = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

            predictions.append(str(obj['index']) + '\t' + res)
            out_file.write(str(obj['index']) + '\t' + res + '\n')
            gold_file.write(str(obj['index']) + '\t' + obj['des'] + '\n')


    (goldMap, predictionMap) = computeMaps(predictions, "./log/valid.gold")
    this_bleu = round(bleuFromMaps(goldMap, predictionMap)[0], 2)

    print(this_bleu)


    # log_filename = '{}_{}_{}.txt'.format(class_name, model_name, datetime.datetime.now().strftime("%m%d_%H%M"))
    # with open('./log/' + log_filename, mode="w", encoding='utf-8') as f:
    #     f.write('result: {}\n'.format(res))
    #     f.write('ground truth: {}\n'.format(class_des))

