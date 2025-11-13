# Cluster 9

def process_alpaca(filename, tokenizer):
    """alpaca_gpt4_data_zh.json"""

    def process_one(per):
        q = tokenizer.encode(HUMAN + per['instruction'] + per['input'] + ROBOT, add_special_tokens=False)
        a = tokenizer.encode(per['output'], add_special_tokens=False)
        if len(q) + len(a) >= args.MAX_LENGTH:
            return (None, None)
        input_ids = q + a
        labels = [args.pad_token_id] * (len(q) - 1) + input_ids[len(q):] + [args.eos_token_id]
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='json')

def process_self_cognition(filename, tokenizer):
    """Tongjilibo/self_cognition"""

    def replace_placeholder(query):
        mapping_ = {'<NAME>': args.name, '<AUTHOR>': args.author, '<DATE>': args.date}
        for key, value in mapping_.items():
            query = query.replace(key, value)
        return query

    def process_one(per):
        input = replace_placeholder(HUMAN + per['instruction'] + per['input'] + ROBOT)
        output = replace_placeholder(per['output'])
        q = tokenizer.encode(input, add_special_tokens=False)
        a = tokenizer.encode(output, add_special_tokens=False)
        if len(q) + len(a) >= args.MAX_LENGTH:
            return (None, None)
        input_ids = q + a
        labels = [args.pad_token_id] * (len(q) - 1) + input_ids[len(q):] + [args.eos_token_id]
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='json')

def process_belle(filename, tokenizer):
    """Belle_open_source_1M.json"""

    def process_one(line):
        if not line:
            return (None, None)
        per = json.loads(line)
        q = tokenizer.encode(HUMAN + per['instruction'] + per['input'] + ROBOT, add_special_tokens=False)
        a = tokenizer.encode(per['output'], add_special_tokens=False)
        if len(q) + len(a) >= args.MAX_LENGTH:
            return (None, None)
        input_ids = q + a
        labels = [args.pad_token_id] * (len(q) - 1) + input_ids[len(q):] + [args.eos_token_id]
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='jsonl')

def process_deepctrl(filename, tokenizer):
    """deepctrl-sft-data"""

    def process_one(line):
        if not line:
            return (None, None)
        try:
            per = json.loads(line)
        except:
            return (None, None)
        input_ids, labels = ([], [])
        for human, robot in per['history']:
            q = tokenizer.encode(HUMAN + human + ROBOT, add_special_tokens=False)
            a = tokenizer.encode(robot, add_special_tokens=False)
            if len(input_ids + q + a) >= args.MAX_LENGTH:
                return (None, None)
            input_ids.extend(q + a)
            labels.extend([args.pad_token_id] * (len(q) - 1) + a + [args.eos_token_id])
        q = tokenizer.encode(HUMAN + per['instruction'] + per['input'] + ROBOT, add_special_tokens=False)
        a = tokenizer.encode(per['output'], add_special_tokens=False)
        input_ids.extend(q + a)
        labels.extend([args.pad_token_id] * (len(q) - 1) + a + [args.eos_token_id])
        if len(input_ids) >= args.MAX_LENGTH:
            return (None, None)
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='jsonl')

def process_moss002(filename, tokenizer):
    """fnlp@moss-002-sft-data"""

    def process_one(per):
        history = re.split('<eoh> \\[MOSS\\]: |<eoa> \\[Human\\]: |\\[Human\\]: |<eoa>', per['plain_text'])
        history = [i.strip() for i in history if i]
        input_ids, labels = ([], [])
        for human, robot in zip(history[0::2], history[1::2]):
            human = tokenizer.encode(HUMAN + human + ROBOT, add_special_tokens=False)
            robot = tokenizer.encode(robot, add_special_tokens=False)
            if len(input_ids + human + robot) >= args.MAX_LENGTH:
                break
            input_ids.extend(human + robot)
            labels.extend([args.pad_token_id] * (len(human) - 1) + robot + [args.eos_token_id])
        if len(input_ids) >= args.MAX_LENGTH:
            return (None, None)
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='json')

def process_moss003(filename, tokenizer):
    """fnlp@moss-003-sft-data"""

    def process_one(line):
        if not line:
            return (None, None)
        per = json.loads(line)
        input_ids, labels = ([], [])
        for turn in per['chat'].values():
            if not re.search('[\\u4e00-\\u9fff]', turn['MOSS']):
                continue
            human = turn['Human'].replace('<|Human|>: ', '').replace('<eoh>\n', '')
            robot = turn['MOSS'].replace('<|MOSS|>: ', '').replace('<eom>\n', '')
            robot = re.sub('<sup><\\|[0-9]+\\|></sup>', '', robot).strip()
            human = tokenizer.encode(HUMAN + human + ROBOT, add_special_tokens=False)
            robot = tokenizer.encode(robot, add_special_tokens=False)
            if len(input_ids + human + robot) >= args.MAX_LENGTH:
                break
            input_ids.extend(human + robot)
            labels.extend([args.pad_token_id] * (len(human) - 1) + robot + [args.eos_token_id])
        if len(input_ids) >= args.MAX_LENGTH:
            return (None, None)
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='jsonl')

def process_shareai(filename, tokenizer):
    """shareAI"""

    def process_one(line):
        if not line:
            return (None, None)
        per = json.loads(line)
        input_ids, labels = ([], [])
        for turn in per['conversation']:
            human = turn['human']
            robot = turn['assistant']
            human = tokenizer.encode(HUMAN + human + ROBOT, add_special_tokens=False)
            robot = tokenizer.encode(robot, add_special_tokens=False)
            if len(input_ids + human + robot) >= args.MAX_LENGTH:
                break
            input_ids.extend(human + robot)
            labels.extend([args.pad_token_id] * (len(human) - 1) + robot + [args.eos_token_id])
        if len(input_ids) >= args.MAX_LENGTH:
            return (None, None)
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='jsonl')

def process_firefly(filename, tokenizer):
    """YeungNLP@firefly-train-1.1M"""

    def process_one(line):
        if not line:
            return (None, None)
        per = json.loads(line)
        q = tokenizer.encode(HUMAN + per['input'] + ROBOT, add_special_tokens=False)
        a = tokenizer.encode(per['target'], add_special_tokens=False)
        if len(q) + len(a) >= args.MAX_LENGTH:
            return (None, None)
        input_ids = q + a
        labels = [args.pad_token_id] * (len(q) - 1) + input_ids[len(q):] + [args.eos_token_id]
        assert len(input_ids) == len(labels)
        return (input_ids, labels)
    return collect_tokens(process_one, filename, data_format='jsonl')

def process_DPO_En_Zh_20k(filename, tokenizer):
    """hiyouga/DPO-En-Zh-20k"""

    def process_one(per):
        prompt_ids = tokenizer.encode(HUMAN + per['system'] + per['prompt'] + ROBOT, add_special_tokens=False)
        chosen_ids = tokenizer.encode(per['answer'][0], add_special_tokens=False)
        rejected_ids = tokenizer.encode(per['answer'][1], add_special_tokens=False)
        if len(prompt_ids) + len(chosen_ids) >= args.MAX_LENGTH or len(prompt_ids) + len(rejected_ids) >= args.MAX_LENGTH:
            return (None, None)
        return (prompt_ids, chosen_ids, rejected_ids)
    return collect_tokens(process_one, filename, data_format='json')

def hh_rlhf_cn(filename, tokenizer):
    """dikw/hh_rlhf_cn"""

    def process_one(line):
        per = json.loads(line)
        prompt_ids = []
        for context in per['context']:
            if context['role'] == 'human':
                q = tokenizer.encode(HUMAN + context['text'] + ROBOT, add_special_tokens=False)
                prompt_ids.extend(q)
            elif context['role'] == 'assistant':
                a = tokenizer.encode(context['text'], add_special_tokens=False)
                prompt_ids.extend(a)
            if len(prompt_ids) >= args.MAX_LENGTH:
                break
        chosen_ids = tokenizer.encode(per['chosen']['text'], add_special_tokens=False)
        rejected_ids = tokenizer.encode(per['rejected']['text'], add_special_tokens=False)
        if len(prompt_ids) + len(chosen_ids) >= args.MAX_LENGTH or len(prompt_ids) + len(rejected_ids) >= args.MAX_LENGTH:
            return (None, None)
        return (prompt_ids, chosen_ids, rejected_ids)
    return collect_tokens(process_one, filename)

def CValues_Comparison(filename, tokenizer):
    """diic/CValues-Comparison"""

    def process_one(per):
        prompt_ids = tokenizer.encode(HUMAN + per['prompt'] + ROBOT, add_special_tokens=False)
        chosen_ids = tokenizer.encode(per['pos_resp'], add_special_tokens=False)
        rejected_ids = tokenizer.encode(per['neg_resp'], add_special_tokens=False)
        if len(prompt_ids) + len(chosen_ids) >= args.MAX_LENGTH or len(prompt_ids) + len(rejected_ids) >= args.MAX_LENGTH:
            return (None, None)
        return (prompt_ids, chosen_ids, rejected_ids)
    return collect_tokens(process_one, filename, data_format='jsonl')

def zhihu_rlhf_3k(filename, tokenizer):
    """liyucheng/zhihu_rlhf_3k"""

    def process_one(per):
        prompt_ids = tokenizer.encode(HUMAN + per['prompt'] + ROBOT, add_special_tokens=False)
        chosen_ids = tokenizer.encode(per['chosen'], add_special_tokens=False)
        rejected_ids = tokenizer.encode(per['rejected'], add_special_tokens=False)
        if len(prompt_ids) + len(chosen_ids) >= args.MAX_LENGTH or len(prompt_ids) + len(rejected_ids) >= args.MAX_LENGTH:
            return (None, None)
        return (prompt_ids, chosen_ids, rejected_ids)
    return collect_tokens(process_one, filename, data_format='table')

def rlhf_reward_single_round_trans_chinese(filename, tokenizer):

    def process_one(per):
        prompt_ids = tokenizer.encode(HUMAN + per['prompt'] + ROBOT, add_special_tokens=False)
        chosen_ids = tokenizer.encode(per['chosen'], add_special_tokens=False)
        rejected_ids = tokenizer.encode(per['rejected'], add_special_tokens=False)
        if len(prompt_ids) + len(chosen_ids) >= args.MAX_LENGTH or len(prompt_ids) + len(rejected_ids) >= args.MAX_LENGTH:
            return (None, None)
        return (prompt_ids, chosen_ids, rejected_ids)
    return collect_tokens(process_one, filename, data_format='parquet')

