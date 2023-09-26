
import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration, T5Config
from openprompt import PromptDataLoader, PromptForGeneration
from openprompt.plms import T5TokenizerWrapper
from openprompt.prompts import SoftTemplate
from openprompt.data_utils import InputExample


def test_prompt_model():
    model_name = 'Salesforce/codet5-base'

    model_config = T5Config.from_pretrained(model_name)
    plm = T5ForConditionalGeneration.from_pretrained(
        model_name, config=model_config)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    template_text = '{"placeholder":"text_a"}\n' + 'Summarization: {"mask"}'
    promptTemplate = SoftTemplate(
        model=plm, tokenizer=tokenizer, text=template_text, num_tokens=50)

    model = PromptForGeneration(
        plm=plm, template=promptTemplate, tokenizer=tokenizer)
    model.eval()

    load_state_path = "../model/pkg_0925_1631/checkpoint-best-bleu/pytorch_model.bin"
    model.load_state_dict(torch.load(load_state_path, map_location="cpu"))

    source = "Package: support\n\nSub Packages: \npackage support.state; // States used in defining the underlying Spring Batch state machine\n\nClasses and Interfaces: \npublic class DefaultStateTransitionComparator extends Object implements Comparator<StateTransition>; // Sorts by decreasing specificity of pattern, based on just counting wildcards (with * taking precedence over ?).\npublic class SimpleFlow extends Object implements Flow, org.springframework.beans.factory.InitializingBean; // A Flow that branches conditionally depending on the exit status of the last State.\npublic final class StateTransition extends Object; // Value object representing a potential transition from one State to another.\n"

    dataloader = PromptDataLoader(
        dataset=[
            InputExample(
                guid=0,
                text_a=source,
            )
        ],
        tokenizer=tokenizer,
        template=promptTemplate,
        tokenizer_wrapper_class=T5TokenizerWrapper,
        max_seq_length=512,
        decoder_max_length=30,
        predict_eos_token=True,
    )

    with torch.no_grad():
        data = next(iter(dataloader))
        _, output_sentence = model.generate(data)

        print(output_sentence[0])


if __name__ == '__main__':
    test_prompt_model()

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
