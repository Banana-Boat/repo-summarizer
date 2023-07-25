import json
import time

from openprompt.data_utils import InputExample


def get_elapse_time(t0):
    elapse_time = time.time() - t0
    if elapse_time > 3600:
        hour = int(elapse_time // 3600)
        minute = int((elapse_time % 3600) // 60)
        return "{}h{}m".format(hour, minute)
    else:
        minute = int((elapse_time % 3600) // 60)
        return "{}m".format(minute)


class Example(object):
    """A single training/test example."""

    def __init__(self,
                 idx,
                 source,
                 target,
                 ):
        self.idx = idx
        self.source = source
        self.target = target


def read_examples(filename, args):
    """Read examples from filename."""
    if args.add_task_prefix:
        task_prefix = f"Generating comments for the code below: "
    else:
        task_prefix = ""

    examples = []
    with open(filename, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            js = json.loads(line)

            examples.append(
                Example(
                    idx=js['index'],
                    source=task_prefix + js['code'],
                    target=js['des'],
                )
            )

    return examples


class InputFeatures(object):
    """A single training/test features for an example."""

    def __init__(self,
                 example_id,
                 source_ids,
                 target_ids,
                 source_mask,
                 target_mask,

                 ):
        self.example_id = example_id
        self.source_ids = source_ids
        self.target_ids = target_ids
        self.source_mask = source_mask
        self.target_mask = target_mask


def convert_examples_to_features(examples, tokenizer, args, stage=None):
    # collect texts
    codes = []
    target_nl = []
    for example in examples:
        codes.append(example.source)

        if stage == "test":
            target_nl.append("None")
        else:
            target_nl.append(example.target)

    # begin tokenizing
    encoded_codes = tokenizer(
        codes, padding=True, verbose=False, add_special_tokens=True,
        truncation=True, max_length=args.max_source_length, return_tensors='pt')

    encoded_targets = tokenizer(
        target_nl, padding=True, verbose=False, add_special_tokens=True,
        truncation=True, max_length=args.max_source_length, return_tensors='pt')

    return {'source_ids':encoded_codes['input_ids'], 'target_ids':encoded_targets['input_ids'],
            'source_mask':encoded_codes['attention_mask'], 'target_mask':encoded_targets['attention_mask']}


def read_prompt_examples(filename):
    """Read examples from filename."""
    examples = []
    with open(filename, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            js = json.loads(line)
            if 'idx' not in js:
                js['idx'] = idx
            code = ' '.join(js['code_tokens']).replace('\n', ' ')
            code = ' '.join(code.strip().split())
            nl = ' '.join(js['docstring_tokens']).replace('\n', '')
            nl = ' '.join(nl.strip().split())
            # code = js['code'].replace('\n', ' ').strip()
            # nl = js['docstring'].replace('\n', ' ').strip()
            examples.append(
                InputExample(
                    guid=idx,
                    text_a= code,
                    tgt_text= nl,
                )
            )

    return examples