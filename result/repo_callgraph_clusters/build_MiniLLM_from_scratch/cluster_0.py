# Cluster 0

class Chat(ChatWebGradio, LLaMA2):

    def build_prompt(self, query, history, functions) -> str:
        texts = ''
        for query_or_response in history:
            role, content = (query_or_response['role'], query_or_response['content'].strip())
            if role == 'user':
                texts += f'{HUMAN}{content}'
            elif role == 'assistant':
                texts += f'{ROBOT}{content}'
        texts += f'{HUMAN}{query}{ROBOT}'
        history.append({'role': 'user', 'content': query})
        return texts

    def build_model(self):
        model = build_transformer_model(config_path=args.config_path, checkpoint_path=None, add_trainer=True)
        model.to(args.device)
        model.load_weights(args.model_path, mapping=lambda x: x.replace('module.', ''))
        return model

    def build_tokenizer(self, **kwargs):
        return tokenizer

def build_prompt(self, query, history, functions) -> str:
    texts = ''
    for query_or_response in history:
        role, content = (query_or_response['role'], query_or_response['content'].strip())
        if role == 'user':
            texts += f'{HUMAN}{content}'
        elif role == 'assistant':
            texts += f'{ROBOT}{content}'
    texts += f'{HUMAN}{query}{ROBOT}'
    history.append({'role': 'user', 'content': query})
    return texts

class Chat(ChatCli, LLaMA2):

    def build_prompt(self, query, history, functions) -> str:
        texts = ''
        for query_or_response in history:
            role, content = (query_or_response['role'], query_or_response['content'].strip())
            if role == 'user':
                texts += f'{HUMAN}{content}'
            elif role == 'assistant':
                texts += f'{ROBOT}{content}'
        texts += f'{HUMAN}{query}{ROBOT}'
        history.append({'role': 'user', 'content': query})
        return texts

    def build_model(self):
        model = build_transformer_model(config_path=args.config_path, checkpoint_path=None, add_trainer=True)
        model.to(args.device)
        model.load_weights(args.model_path, mapping=lambda x: x.replace('module.', ''))
        return model

    def build_tokenizer(self, **kwargs):
        return tokenizer

def build_prompt(self, query, history, functions) -> str:
    texts = ''
    for query_or_response in history:
        role, content = (query_or_response['role'], query_or_response['content'].strip())
        if role == 'user':
            texts += f'{HUMAN}{content}'
        elif role == 'assistant':
            texts += f'{ROBOT}{content}'
    texts += f'{HUMAN}{query}{ROBOT}'
    history.append({'role': 'user', 'content': query})
    return texts

def build_cli_history(history):
    prompt = ''
    for query, response in history:
        prompt += f'\n\nUser：{query.strip()}'
        prompt += f'\n\nRobot：{response.strip()}'
    return prompt

def chat():
    """非流式"""
    history = []
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    while True:
        query = input('\n输入:')
        if query.strip() == 'stop':
            break
        if query.strip() == 'clear':
            history = []
            os.system(clear_command)
            continue
        inputs = tokenizer.encode(build_prompt(query, history), return_tensors='pt', add_special_tokens=False).to(device)
        response = model.generate(inputs)
        response = tokenizer.decode(response[0].cpu(), skip_special_tokens=True)
        os.system(clear_command)
        print(build_cli_history(history + [(query, response)]), flush=True)

def stream_chat():
    """流式"""
    streamer = TextIteratorStreamer(tokenizer)
    history = []
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    while True:
        query = input('\nUser:')
        if query.strip() == 'stop':
            break
        if query.strip() == 'clear':
            history = []
            os.system(clear_command)
            continue
        query_new = build_prompt(query, history)
        inputs = tokenizer.encode(query_new, return_tensors='pt', add_special_tokens=False).to(device)
        generation_kwargs = dict({'input_ids': inputs}, streamer=streamer, max_new_tokens=512)
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        response = ''
        for new_text in streamer:
            os.system(clear_command)
            response += new_text
            print(build_cli_history(history + [(query, response[len(query_new):])]), flush=True)
        os.system(clear_command)
        print(build_cli_history(history + [(query, response[len(query_new):])]), flush=True)

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

def decode(self, t: List[int]) -> str:
    return self.sp_model.decode(t)

def chat():
    """
    非流式输出
    """
    history = []
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    while True:
        query = input('\n输入:')
        if query.strip() == 'stop':
            break
        if query.strip() == 'clear':
            history = []
            os.system(clear_command)
            continue
        inputs = tokenizer.encode(query, return_tensors='pt', add_special_tokens=False).to(device)
        response = model.generate(inputs)
        response = tokenizer.decode(response[0].cpu(), skip_special_tokens=True)
        os.system(clear_command)
        print(build_cli_history(history + [(query, response)]), flush=True)

def stream_chat():
    """
    流式输出
    """
    streamer = TextIteratorStreamer(tokenizer)
    history = []
    clear_command = 'cls' if os.name == 'nt' else 'clear'
    while True:
        query = input('\n输入:')
        if query.strip() == 'stop':
            break
        if query.strip() == 'clear':
            history = []
            os.system(clear_command)
            continue
        inputs = tokenizer.encode(query, return_tensors='pt', add_special_tokens=False).to(device)
        generation_kwargs = dict({'input_ids': inputs}, streamer=streamer, max_new_tokens=512)
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        response = ''
        for new_text in streamer:
            os.system(clear_command)
            response += new_text
            print(build_cli_history(history + [(query, response)]), flush=True)
        os.system(clear_command)
        print(build_cli_history(history + [(query, response)]), flush=True)

class Chat(ChatCli, LLaMA2):

    def build_prompt(self, query, history, functions) -> str:
        texts = ''
        for query_or_response in history:
            role, content = (query_or_response['role'], query_or_response['content'].strip())
            if role == 'user':
                texts += f'{HUMAN}{content}'
            elif role == 'assistant':
                texts += f'{ROBOT}{content}'
        texts += f'{HUMAN}{query}{ROBOT}'
        history.append({'role': 'user', 'content': query})
        return texts

    def build_model(self):
        model = build_transformer_model(config_path=args.config_path, checkpoint_path=None, add_trainer=True)
        model.to(args.device)
        if args.use_peft:
            from peft import LoraConfig, get_peft_model
            peft_config = LoraConfig(inference_mode=False, r=8, lora_alpha=16, lora_dropout=0.05, target_modules=find_all_linear_names(model, int4=getattr(args, 'load_in_4bit', False), int8=getattr(args, 'load_in_8bit', False)))
            model = get_peft_model(model, peft_config)
        model.load_weights(args.model_path, mapping=lambda x: x.replace('model.base_model.model.', ''))
        return model

    def build_tokenizer(self, **kwargs):
        return tokenizer

def build_prompt(self, query, history, functions) -> str:
    texts = ''
    for query_or_response in history:
        role, content = (query_or_response['role'], query_or_response['content'].strip())
        if role == 'user':
            texts += f'{HUMAN}{content}'
        elif role == 'assistant':
            texts += f'{ROBOT}{content}'
    texts += f'{HUMAN}{query}{ROBOT}'
    history.append({'role': 'user', 'content': query})
    return texts

