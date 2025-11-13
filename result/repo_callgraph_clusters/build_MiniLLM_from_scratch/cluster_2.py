# Cluster 2

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

def build_model(self):
    model = build_transformer_model(config_path=args.config_path, checkpoint_path=None, add_trainer=True)
    model.to(args.device)
    model.load_weights(args.model_path, mapping=lambda x: x.replace('module.', ''))
    return model

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

def build_model(self):
    model = build_transformer_model(config_path=args.config_path, checkpoint_path=None, add_trainer=True)
    model.to(args.device)
    model.load_weights(args.model_path, mapping=lambda x: x.replace('module.', ''))
    return model

def replace_placeholder(query):
    mapping_ = {'<NAME>': args.name, '<AUTHOR>': args.author, '<DATE>': args.date}
    for key, value in mapping_.items():
        query = query.replace(key, value)
    return query

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

def build_model(self):
    model = build_transformer_model(config_path=args.config_path, checkpoint_path=None, add_trainer=True)
    model.to(args.device)
    if args.use_peft:
        from peft import LoraConfig, get_peft_model
        peft_config = LoraConfig(inference_mode=False, r=8, lora_alpha=16, lora_dropout=0.05, target_modules=find_all_linear_names(model, int4=getattr(args, 'load_in_4bit', False), int8=getattr(args, 'load_in_8bit', False)))
        model = get_peft_model(model, peft_config)
    model.load_weights(args.model_path, mapping=lambda x: x.replace('model.base_model.model.', ''))
    return model

