# Cluster 1

class SPTokenizer:

    def __init__(self, model_path: str):
        assert os.path.isfile(model_path), model_path
        self.sp_model = SentencePieceProcessor(model_file=model_path)
        self.n_words: int = self.sp_model.vocab_size()
        self.bos_id: int = self.sp_model.bos_id()
        self.eos_id: int = self.sp_model.eos_id()
        self.pad_id: int = self.sp_model.unk_id()
        assert self.sp_model.vocab_size() == self.sp_model.get_piece_size()
        special_tokens = ['[MASK]', '[gMASK]', '[sMASK]', 'sop', 'eop']
        self.special_tokens = {}
        self.index_special_tokens = {}
        for token in special_tokens:
            self.special_tokens[token] = self.n_words
            self.index_special_tokens[self.n_words] = token
            self.n_words += 1

    def tokenize(self, s: str):
        return self.sp_model.EncodeAsPieces(s)

    def encode(self, s: str, bos: bool=False, eos: bool=False) -> List[int]:
        assert type(s) is str
        t = self.sp_model.encode(s)
        if bos:
            t = [self.bos_id] + t
        if eos:
            t = t + [self.eos_id]
        return t

    def decode(self, t: List[int]) -> str:
        return self.sp_model.decode(t)

    def decode_tokens(self, tokens: List[str]) -> str:
        text = self.sp_model.DecodePieces(tokens)
        return text

    def convert_token_to_id(self, token):
        """ Converts a token (str) in an id using the vocab. """
        if token in self.special_tokens:
            return self.special_tokens[token]
        return self.sp_model.PieceToId(token)

    def convert_id_to_token(self, index):
        """Converts an index (integer) in a token (str) using the vocab."""
        if index in self.index_special_tokens or index in [self.eos_id, self.bos_id, self.pad_id] or index < 0:
            return ''
        return self.sp_model.IdToPiece(index)

def encode(self, s: str, bos: bool=False, eos: bool=False) -> List[int]:
    assert type(s) is str
    t = self.sp_model.encode(s)
    if bos:
        t = [self.bos_id] + t
    if eos:
        t = t + [self.eos_id]
    return t

def process_wiki_clean():
    with open('./data/wikipedia_cn_20230720/wikipedia-cn-20230720-filtered.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    doc_ids = []
    for line in tqdm(data):
        text = line['completion']
        text_id = tokenizer.encode(text, add_special_tokens=False)
        text_id.append(tokenizer.special_tokens['<eos>'])
        if len(text_id) > 5:
            doc_ids += text_id
    arr = np.array(doc_ids, dtype=np.uint16)
    with open('./data/wiki.bin', 'wb') as f:
        f.write(arr.tobytes())

def process_medical(data_path, name):
    f = open(data_path, 'r', encoding='utf-8')
    doc_ids = []
    while True:
        line = f.readline()
        if not line:
            break
        line = json.loads(line)
        text = line['text']
        text_id = tokenizer.encode(text, add_special_tokens=False)
        text_id.append(tokenizer.special_tokens['<eos>'])
        if len(text_id) > 5:
            doc_ids += text_id
    arr = np.array(doc_ids, dtype=np.uint16)
    with open('./data/medical_{}.bin'.format(name), 'wb') as f:
        f.write(arr.tobytes())

def sft_to_pretrain():
    doc_ids = []
    "\n    df=pd.read_csv('./data/medical_qa_144w.csv')\n    for _,q,a in tqdm(df.itertuples()):\n        q_id = tokenizer.encode(q,add_special_tokens=False)\n        a_id = tokenizer.encode(a,add_special_tokens=False)\n        #\n        print(q)\n        print(a)\n        print('-----')\n        text_id=q_id+a_id+[tokenizer.special_tokens['<eos>']]\n        if len(text_id)>5:\n            doc_ids+=text_id\n    "
    with open('./data/shibing624_medical/finetune/train_en_1.json', 'r', encoding='utf-8') as f:
        for row in f:
            line = json.loads(row)
            q = line['input']
            a = line['output']
            q_id = tokenizer.encode(q, add_special_tokens=False)
            a_id = tokenizer.encode(a, add_special_tokens=False)
            text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
            if len(text_id) > 5:
                doc_ids += text_id
    with open('./data/shibing624_medical/finetune/test_en_1.json', 'r', encoding='utf-8') as f:
        for row in f:
            line = json.loads(row)
            q = line['input']
            a = line['output']
            q_id = tokenizer.encode(q, add_special_tokens=False)
            a_id = tokenizer.encode(a, add_special_tokens=False)
            text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
            if len(text_id) > 5:
                doc_ids += text_id
    with open('./data/shibing624_medical/finetune/valid_en_1.json', 'r', encoding='utf-8') as f:
        for row in f:
            line = json.loads(row)
            q = line['input']
            a = line['output']
            q_id = tokenizer.encode(q, add_special_tokens=False)
            a_id = tokenizer.encode(a, add_special_tokens=False)
            text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
            if len(text_id) > 5:
                doc_ids += text_id
    with open('./data/shibing624_medical/finetune/train_zh_0.json', 'r', encoding='utf-8') as f:
        for row in f:
            line = json.loads(row)
            q = line['instruction'] + line['input']
            a = line['output']
            q_id = tokenizer.encode(q, add_special_tokens=False)
            a_id = tokenizer.encode(a, add_special_tokens=False)
            text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
            if len(text_id) > 5:
                doc_ids += text_id
    with open('./data/shibing624_medical/finetune/test_zh_0.json', 'r', encoding='utf-8') as f:
        for row in f:
            line = json.loads(row)
            q = line['instruction'] + line['input']
            a = line['output']
            q_id = tokenizer.encode(q, add_special_tokens=False)
            a_id = tokenizer.encode(a, add_special_tokens=False)
            text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
            if len(text_id) > 5:
                doc_ids += text_id
    with open('./data/shibing624_medical/finetune/valid_zh_0.json', 'r', encoding='utf-8') as f:
        for row in f:
            line = json.loads(row)
            q = line['instruction'] + line['input']
            a = line['output']
            q_id = tokenizer.encode(q, add_special_tokens=False)
            a_id = tokenizer.encode(a, add_special_tokens=False)
            text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
            if len(text_id) > 5:
                doc_ids += text_id
    arr = np.array(doc_ids, dtype=np.uint16)
    print(arr.shape)
    with open('./data/medical_qa.bin', 'wb') as f:
        f.write(arr.tobytes())

def process_baidu():
    BATCH_SIZE = 1000000
    cnt = 0
    batch_cnt = 0
    token = 0
    doc_ids = []
    f1 = open('./data/563w_baidubaike/563w_baidubaike.json', 'r', encoding='utf-8')
    while True:
        line = f1.readline()
        if not line:
            break
        line = json.loads(line)
        text = ''
        try:
            text += line['title'] + '：' + line['summary']
        except:
            pass
        for per in line['sections']:
            text += per['title'] + '：' + per['content'] + '。'
        text_id = tokenizer.encode(text, add_special_tokens=False)
        text_id.append(tokenizer.special_tokens['<eos>'])
        if len(text_id) > 5:
            doc_ids += text_id
        cnt += 1
        if cnt % BATCH_SIZE == 0:
            batch_cnt += 1
            arr = np.array(doc_ids, dtype=np.uint16)
            doc_ids = []
            print('cnt:', cnt, 'arr_shape:', arr.shape)
            with open('./data/baidubaike_563w_{}.bin'.format(batch_cnt), 'wb') as f2:
                f2.write(arr.tobytes())
            del arr
    if not doc_ids:
        batch_cnt += 1
        arr = np.array(doc_ids, dtype=np.uint16)
        print('cnt:', cnt, 'arr_shape:', arr.shape)
        with open('./data/baidubaike_563w_{}.bin'.format(batch_cnt), 'wb') as f:
            f.write(arr.tobytes())

def process_c4():
    c4_zh_paths = glob.glob('./data/c4_zh/*')
    c4_zh_paths = sorted(c4_zh_paths)
    print(len(c4_zh_paths))
    cnt = 0
    token = 0
    doc_ids = []
    for per in tqdm(c4_zh_paths):
        with open(per, 'r') as f:
            for line in f:
                text = json.loads(line)
                text = text['text']
                text_id = tokenizer.encode(text, add_special_tokens=False)
                text_id.append(tokenizer.special_tokens['<eos>'])
                if len(text_id) > 5:
                    doc_ids += text_id
                cnt += 1
    arr = np.array(doc_ids, dtype=np.uint16)
    with open('./data/c4_zh.bin', 'wb') as f:
        f.write(arr.tobytes())
    print(arr.shape)

def process_wudao():
    wudao_zh_paths = glob.glob('./data/WuDaoCorpus2.0_base_200G/*')
    wudao_zh_paths = sorted(wudao_zh_paths)
    print(len(wudao_zh_paths))
    cnt = 0
    token = 0
    doc_ids = []
    for per in tqdm(wudao_zh_paths[320:]):
        with open(per, 'r') as f:
            data = json.load(f)
            for text in data:
                text = text['title'] + text['content']
                text_id = tokenizer.encode(text, add_special_tokens=False)
                text_id.append(tokenizer.special_tokens['<eos>'])
                if len(text_id) > 5:
                    doc_ids += text_id
                cnt += 1
    arr = np.array(doc_ids, dtype=np.uint16)
    with open('./data/wudaocorpus_zh_16.bin', 'wb') as f:
        f.write(arr.tobytes())
    print(arr.shape)

def process_one(per):
    prompt_ids = tokenizer.encode(HUMAN + per['prompt'] + ROBOT, add_special_tokens=False)
    chosen_ids = tokenizer.encode(per['chosen'], add_special_tokens=False)
    rejected_ids = tokenizer.encode(per['rejected'], add_special_tokens=False)
    if len(prompt_ids) + len(chosen_ids) >= args.MAX_LENGTH or len(prompt_ids) + len(rejected_ids) >= args.MAX_LENGTH:
        return (None, None)
    return (prompt_ids, chosen_ids, rejected_ids)

