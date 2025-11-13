# Cluster 22

def coref_res(target: object, window: list, group_intro: str):
    llm = ChatClient('config.ini')
    name_map = dict()
    name_int = ord('A')
    format_history = []
    for item in window:
        sender = item['sender']
        if sender not in name_map:
            name_map[sender] = chr(name_int)
            name_int += 1
        format_history.append({'username': name_map[sender], 'content': item['text']})
    target_sender = target['sender']
    if target_sender not in name_map:
        name_map[target_sender] = chr(name_int)
        name_int += 1
    target_str = json.dumps({'username': name_map[target_sender], 'content': target['text']}, indent=2, ensure_ascii=False)
    BASE_PROMPT_TEMPLATE = '请完成群聊场景中的指代消解任务。\n"{}"\n以下是历史对话，可能有多个人的发言：\n{}\n\n输入内容：\n"{}"'
    prompt_base = BASE_PROMPT_TEMPLATE.format(group_intro, json.dumps(format_history, ensure_ascii=False), target['text'])
    prompt = '{}\n输入是否需要指代消解？ A：需要  B不需要 C不知道'.format(prompt_base)
    need_cr = llm.generate_response(prompt=prompt, backend='puyu').lower()
    logger.debug('{} {}'.format(prompt, need_cr))
    response = ''
    if 'a' in need_cr:
        prompt = '{}\n指代消解输入后的结果是？直接返回消解后的完整文本不要解释原因；直接返回最终结果不要解释过程。'.format(prompt_base)
        response = llm.generate_response(prompt=prompt, backend='puyu').lower()
    else:
        return ('', False)
    keywords = ['指代消解后的文本是：', '指代消解后是：', '指代消解后：', '指代消解后的文本为：']
    for keyword in keywords:
        if keyword in response:
            response = response.split(keyword)[-1]
    response = response.strip()
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    logger.debug('return response {}'.format(response))
    return (response, True)

def convert_alpaca(input_filepath: str, output_filepath: str):
    gts = []
    with open(input_filepath) as gt:
        for line in gt:
            target = json.loads(line)
            if 'cr_need_gt' not in target:
                continue
            gt_bool = target['cr_need_gt']
            text = target['text']
            window = target['cr_window']
            name_map = dict()
            name_int = ord('A')
            format_history = []
            for item in window:
                sender = item['sender']
                if sender not in name_map:
                    name_map[sender] = chr(name_int)
                    name_int += 1
                format_history.append({'username': name_map[sender], 'content': item['text']})
            target_sender = target['sender']
            if target_sender not in name_map:
                name_map[target_sender] = chr(name_int)
                name_int += 1
            target_str = json.dumps({'username': name_map[target_sender], 'content': target['text']}, indent=2, ensure_ascii=False)
            BASE_PROMPT_TEMPLATE = '群聊场景中“这”、“它”、“哪”等代词需要查看上下文和其他用户的回复才能确定具体指什么，请完成群聊场景代词替换任务。\n以下是历史对话，可能有多个人的发言：\n{}\n输入内容：\n"{}"\n'
            prompt_base = BASE_PROMPT_TEMPLATE.format(json.dumps(format_history, ensure_ascii=False), target_str)
            option_str, output = randomize_labels(gt_bool)
            instruction = '{} 输入内容中的 content 信息是否完整，是否需要从历史对话中提取代词或宾语来替代 content 中的一部分词汇？ {} \n一步步分析，首先历史消息包含哪些话题；其次哪个话题与问题最相关；如果都不相关就不提取。 '.format(prompt_base, option_str)
            gts.append({'instruction': instruction, 'input': '', 'output': output})
    alpaca_str = json.dumps(gts, ensure_ascii=False, indent=2)
    with open(output_filepath, 'w') as fout:
        fout.write(alpaca_str)

def qwen_coref_res(llm_type: str, target: object):
    model = '/workspace/models/{}'.format(llm_type)
    client = OpenAI(base_url='http://10.140.24.142:29999/v1', api_key='token-abc123')
    group_intro = '\n名词解释：\nopen-compass/opencompass : 用于评测大型语言模型（LLM）. 它提供了完整的开源可复现的评测框架，支持大语言模型、多模态模型的一站式评测，基于分布式技术，对大参数量模型亦能实现高效评测。评测方向汇总为知识、语言、理解、推理、考试五大能力维度，整合集纳了超过70个评测数据集，合计提供了超过40万个模型评测问题，并提供长文本、安全、代码3类大模型特色技术能力评测。\nopenmmlab/mmpose is an open-source toolbox for pose estimation based on PyTorch\nopenmmlab/mmdeploy is an open-source deep learning model deployment toolset\nopenmmlab/mmdetection is an open source object detection toolbox based on PyTorch.\nlmdeploy 是一个用于压缩、部署和服务 LLM（Large Language Model）的工具包。是一个服务端场景下，transformer 结构 LLM 部署工具，支持 GPU 服务端部署，速度有保障，支持 Tensor Parallel，多并发优化，功能全面，包括模型转换、缓存历史会话的 cache feature 等. 它还提供了 WebUI、命令行和 gRPC 客户端接入。\n茴香豆（HuixiangDou）是一个基于 LLM 的群聊知识助手。设计拒答、响应两阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。\nxtuner is an efficient, flexible and full-featured toolkit for fine-tuning large models.\nmmyolo : YOLO series toolbox and benchmark. Implemented RTMDet, RTMDet-Rotated,YOLOv5, YOLOv6, YOLOv7, YOLOv8,YOLOX, PPYOLOE, etc.\nncnn is a high-performance neural network inference framework optimized for the mobile platform\n'
    window = target['cr_window']
    name_map = dict()
    name_int = ord('A')
    format_history = []
    for item in window:
        sender = item['sender']
        if sender not in name_map:
            name_map[sender] = chr(name_int)
            name_int += 1
        format_history.append({'username': name_map[sender], 'content': item['text']})
    target_sender = target['sender']
    if target_sender not in name_map:
        name_map[target_sender] = chr(name_int)
        name_int += 1
    target_str = json.dumps({'username': name_map[target_sender], 'content': target['text']}, indent=2, ensure_ascii=False)
    BASE_PROMPT_TEMPLATE = '群聊场景中“这”、“它”、“哪”等代词需要查看上下文和其他用户的回复才能确定具体指什么，请完成群聊场景代词替换任务。\n\n以下是历史对话，可能有多个人的发言：\n{}\n\n输入内容：\n"{}"'
    prompt_base = BASE_PROMPT_TEMPLATE.format(json.dumps(format_history, ensure_ascii=False), target_str)
    prompt = '{}\n输入内容中的 content 信息是否完整，是否需要从历史对话中提取代词或宾语来替代 content 中的一部分词汇？ A：不需要提取，信息完整  B：需要  C：不知道 \n一步步分析，首先历史消息包含哪些话题；其次哪个话题与问题最相关；如果都不相关就不提取。 '.format(prompt_base)
    completion = client.chat.completions.create(model=model, messages=[{'role': 'user', 'content': prompt}])
    need_cr = completion.choices[0].message.content.lower()
    need_cr = need_cr.strip()
    logger.debug('{} {}'.format(prompt, need_cr))
    response = ''
    prompt = '请判断用户意图，这位用户在做单选题，单选题答案有 3 个， A：不需要提取，信息完整  B：需要  C：不知道。\n用户输入：\n{}\n\n用户的答案是？不要解释，直接给 ABC 选项结果。\n'.format(need_cr)
    completion = client.chat.completions.create(model=model, messages=[{'role': 'user', 'content': prompt}])
    need_cr = completion.choices[0].message.content.lower()
    need_cr = need_cr.strip()
    logger.warning('final choose {}'.format(need_cr))
    if need_cr.startswith('a') or need_cr == '不需要' or '因此不需要' in need_cr or ('a：不需要' in need_cr) or ('不需要进行指代消解' in need_cr) or ('选项 a' in need_cr):
        return ('', 'no')
    elif need_cr.startswith('b') or need_cr == '需要' or '因此需要' in need_cr or ('因此选择b' in need_cr) or ('需要进行指代消解' in need_cr) or ('需要指代消解' in need_cr) or ('b：需要' in need_cr):
        prompt = '{}\n指代消解输入内容中 content 后的文本是？直接返回消解后的完整文本不要解释原因；直接返回最终结果不要解释过程。'.format(prompt_base)
        completion = client.chat.completions.create(model=model, messages=[{'role': 'user', 'content': prompt}])
        response = completion.choices[0].message.content.lower()
    elif need_cr.startswith('c') or '不知道' in need_cr:
        return ('', 'unknown')
    else:
        return ('', 'exception {}'.format(need_cr))
    keywords = ['指代消解后的文本是：', '指代消解后是：', '指代消解后：', '指代消解后的文本为：']
    for keyword in keywords:
        if keyword in response:
            response = response.split(keyword)[-1]
    response = response.strip()
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    logger.warning('coref response {}'.format(response))
    return (response, 'yes')

@DeprecationWarning
def test_auto_fix():
    """test auto choose backend based on config."""
    remote_only_config = 'config-2G.ini'
    local_only_config = 'config.ini'
    full_config = 'config-advanced.ini'
    client = ChatClient(config_path=remote_only_config)
    real_backend, max_len = client.auto_fix(backend='local')
    assert real_backend != 'local'
    assert max_len >= 32000
    client = ChatClient(config_path=local_only_config)
    real_backend, max_len = client.auto_fix(backend='kimi')
    assert real_backend == 'local'
    client = ChatClient(config_path=full_config)
    real_backend, max_len = client.auto_fix(backend='local')
    assert real_backend == 'local'
    real_backend, max_len = client.auto_fix(backend='kimi')
    assert real_backend != 'local'

def format_history(history):
    """format [{sender, content}] to [[user1, bot1],[user2,bot2]..] style."""
    ret = []
    last_id = -1
    user = ''
    concat_text = ''
    for item in history:
        if last_id == -1:
            last_id = item.sender
            concat_text = item.content
            continue
        if last_id == item.sender:
            concat_text += '\n'
            concat_text += item.content
            continue
        if last_id == 0:
            user = concat_text
        elif last_id == 1:
            ret.append([user, concat_text])
            user = ''
        last_id = item.sender
        concat_text = item.content
    if last_id == 0:
        ret.append([concat_text, ''])
        logger.warning('chat history should not ends with user')
    elif last_id == 1:
        ret.append([user, concat_text])
    return ret

def detect_base64_image_suffix(base64: str) -> [Image, str]:
    if not base64 or len(base64) == 0:
        return [Image.INVALID, '']
    s = base64.split('base64,')
    if len(s) < 2:
        return [Image.INVALID, '']
    base64_prefix = s[0].lower()
    if 'data:image/jpeg;' == base64_prefix:
        return [Image.JPG, s[1]]
    if 'data:image/png;' == base64_prefix:
        return [Image.PNG, s[1]]
    if 'data:image/bmp;' == base64_prefix:
        return [Image.BMP, s[1]]
    return [Image.INVALID, '']

class HuixiangDouEnv:

    @classmethod
    def print_env(cls):
        methods = [method for method in cls.__dict__ if callable(getattr(HuixiangDouEnv, method)) and method != 'print_env']
        for method in methods:
            f = getattr(HuixiangDouEnv, method)
            value = f()
            logger.info(f'[config] {method}: {value}')

    @classmethod
    def get_cookie_secure(cls) -> bool:
        return True if os.getenv('COOKIE_SECURE') else False

    @classmethod
    def get_server_port(cls) -> str:
        return os.getenv('SERVER_PORT') if os.getenv('SERVER_PORT') else '23333'

    @classmethod
    def get_jwt_secret(cls) -> str:
        return os.getenv('JWT_SECRET') if os.getenv('JWT_SECRET') else 'HuixiangDou_is_awesome'

    @classmethod
    def get_redis_host(cls) -> str:
        return 'localhost' if os.getenv('REDIS_HOST') is None else os.getenv('REDIS_HOST')

    @classmethod
    def get_redis_password(cls) -> str:
        return 'default_password' if os.getenv('REDIS_PASSWORD') is None else os.getenv('REDIS_PASSWORD')

    @classmethod
    def get_redis_port(cls) -> int:
        return 6379 if os.getenv('REDIS_PORT') is None else os.getenv('REDIS_PORT')

    @classmethod
    def get_redis_db(cls) -> int:
        return 0 if os.getenv('REDIS_DB') is None else os.getenv('REDIS_DB')

    @classmethod
    def _get_default_endpoint(cls) -> str:
        return f'http://0.0.0.0:{cls.get_server_port()}/'

    @classmethod
    def get_lark_encrypt_key(cls) -> str:
        return os.getenv('HUIXIANGDOU_LARK_ENCRYPT_KEY') if os.getenv('HUIXIANGDOU_LARK_ENCRYPT_KEY') else 'thisiskey'

    @classmethod
    def get_lark_verification_token(cls) -> str:
        return os.getenv('HUIXIANGDOU_LARK_VERIFY_TOKEN') if os.getenv('HUIXIANGDOU_LARK_VERIFY_TOKEN') else 'sMzyjKi9vMlEhKCZOVtBMhhl8x23z0AG'

    @classmethod
    def get_message_endpoint(cls) -> str:
        endpoint = os.getenv('HUIXIANGDOU_MESSAGE_ENDPOINT')
        if not endpoint:
            endpoint = cls._get_default_endpoint()
        if not endpoint.endswith('/'):
            endpoint += '/'
        return endpoint

    @classmethod
    def get_lark_log_level(cls) -> lark.LogLevel:
        return lark.LogLevel.DEBUG

    @classmethod
    def get_cookie_samesite(cls) -> str:
        return 'none' if HuixiangDouEnv.get_cookie_secure() else 'lax'

@classmethod
def get_message_endpoint(cls) -> str:
    endpoint = os.getenv('HUIXIANGDOU_MESSAGE_ENDPOINT')
    if not endpoint:
        endpoint = cls._get_default_endpoint()
    if not endpoint.endswith('/'):
        endpoint += '/'
    return endpoint

class Embedder:
    """Wrap text2vec (multimodal) model."""
    client: Any
    _type: str

    def __init__(self, model_config: dict):
        self.support_image = False
        self.distance_strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
        model_path = model_config['embedding_model_path']
        self._type = self.model_type(model_path=model_path)
        if 'bce' in self._type:
            from sentence_transformers import SentenceTransformer
            self.client = SentenceTransformer(model_name_or_path=model_path).half()
        elif 'bge' in self._type:
            from FlagEmbedding.visual.modeling import Visualized_BGE
            self.support_image = True
            vision_weight_path = os.path.join(model_path, 'Visualized_m3.pth')
            self.client = Visualized_BGE(model_name_bge=model_path, model_weight=vision_weight_path).eval()
        elif 'siliconcloud' in self._type:
            api_token = model_config['api_token'].strip()
            if len(api_token) < 1:
                api_token = os.getenv('SILICONCLOUD_TOKEN')
                if api_token is None or len(api_token) < 1:
                    raise ValueError('siliconclud remote embedder api token is None')
            if 'Bearer' not in api_token:
                api_token = 'Bearer ' + api_token
            api_rpm = max(1000, int(model_config['api_rpm']))
            api_tpm = max(40000, int(model_config['api_tpm']))
            self.client = {'api_token': api_token, 'api_rpm': RPM(api_rpm), 'api_tpm': TPM(api_tpm)}
        else:
            raise ValueError('Unknown type {}'.format(self._type))

    @classmethod
    def model_type(self, model_path):
        """Check text2vec model using multimodal or not."""
        if model_path.startswith('https'):
            return 'siliconcloud'
        if 'bge-m3' not in model_path.lower():
            return 'bce'
        vision_weight = os.path.join(model_path, 'Visualized_m3.pth')
        if not os.path.exists(vision_weight):
            logger.warning('`Visualized_m3.pth` (vision model weight) not exist')
            return 'bce'
        return 'bge'

    def token_length(self, text: str) -> int:
        if 'bge' in self._type or 'bce' in self._type:
            return len(self.client.tokenizer(text, padding=False, truncation=False)['input_ids'])
        else:
            return len(text) // 2

    def distance(self, text1: str, text2: str) -> float:
        emb1 = self.embed_query(text=text1)
        emb2 = self.embed_query(text=text2)
        if self.distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
            distance = np.linalg.norm(emb1 - emb2)
            return distance
        raise ValueError('Unsupported distance strategy')

    def embed_query(self, text: str=None, path: str=None) -> np.ndarray:
        """Embed input text or image as feature, output np.ndarray with np.float32"""
        if 'bge' in self._type:
            import torch
            with torch.no_grad():
                feature = self.client.encode(text=text, image=path)
                return feature.cpu().numpy().astype(np.float32)
        elif 'bce' in self._type:
            if not text:
                raise ValueError('This model only support text')
            emb = self.client.encode([text], show_progress_bar=False, normalize_embeddings=True)
            emb = emb.astype(np.float32)
            return emb
        else:
            self.client['api_rpm'].wait_sync(silent=True)
            self.client['api_tpm'].wait_sync(silent=True, token_count=len(text))
            if not text:
                raise ValueError('This api only support text')
            url = 'https://api.siliconflow.cn/v1/embeddings'
            payload = {'model': 'netease-youdao/bce-embedding-base_v1', 'input': text, 'encoding_format': 'float'}
            headers = {'accept': 'application/json', 'content-type': 'application/json', 'authorization': self.client['api_token']}
            response = requests.post(url, json=payload, headers=headers)
            json_obj = json.loads(response.text)
            emb_list = json_obj['data'][0]['embedding']
            emb = np.array(emb_list).astype(np.float32).reshape(1, -1)
            return emb

    def embed_query_batch_text(self, chunks: List[Chunk]=[]) -> np.ndarray:
        """Embed input text or image as feature, output np.ndarray with np.float32"""
        if 'bge' in self._type:
            import torch
            with torch.no_grad():
                features = []
                for c in chunks:
                    feature = self.client.encode(text=c.content_or_path)
                    features.append(feature.cpu().numpy())
                return np.concatenate(features).reshape(len(chunks), -1).astype(np.float32)
        elif 'bce' in self._type:
            texts = []
            for c in chunks:
                texts.append(c.content_or_path)
            emb = self.client.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            return emb.astype(np.float32)
        else:
            features = []
            for c in chunks:
                feature = self.embed_query(text=c.content_or_path)
                features.append(feature)
            return np.concatenate(features).reshape(len(chunks), -1).astype(np.float32)

@classmethod
def model_type(self, model_path):
    """Check text2vec model using multimodal or not."""
    if model_path.startswith('https'):
        return 'siliconcloud'
    if 'bge-m3' not in model_path.lower():
        return 'bce'
    vision_weight = os.path.join(model_path, 'Visualized_m3.pth')
    if not os.path.exists(vision_weight):
        logger.warning('`Visualized_m3.pth` (vision model weight) not exist')
        return 'bce'
    return 'bge'

def clean_md(text: str):
    """Remove parts of the markdown document that do not contain the key
    question words, such as code blocks, URL links, etc."""
    pattern_ref = '\\[(.*?)\\]\\(.*?\\)'
    new_text = re.sub(pattern_ref, '\\1', text)
    pattern_code = '```.*?```'
    new_text = re.sub(pattern_code, '', new_text, flags=re.DOTALL)
    new_text = re.sub('_{5,}', '', new_text)
    new_text = new_text.lower()
    return new_text

class LLMReranker:
    _type: str
    topn: int

    def __init__(self, model_config: dict, topn: int=10):
        model_name_or_path = model_config['reranker_model_path']
        self._type = self.model_type(model_path=model_name_or_path)
        self.topn = topn
        if 'bge' in self._type:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(model_name_or_path, trust_remote_code=True, torch_dtype=torch.bfloat16).eval().to('cuda')
        elif 'bce' in self._type:
            from BCEmbedding import RerankerModel
            self.bce_client = RerankerModel(model_name_or_path=model_name_or_path, use_fp16=True)
        elif 'siliconcloud' in self._type:
            api_token = model_config['api_token'].strip()
            if len(api_token) < 1:
                api_token = os.getenv('SILICONCLOUD_TOKEN')
                if api_token is None or len(api_token) < 1:
                    raise ValueError('siliconclud remote reranker api token is None')
            if 'Bearer' not in api_token:
                api_token = 'Bearer ' + api_token
            api_rpm = max(1, int(model_config['api_rpm']))
            self.client = {'api_token': api_token, 'api_rpm': RPM(api_rpm)}
        else:
            raise ValueError('Unknown type {}'.format(self._type))

    @classmethod
    def model_type(self, model_path):
        """Check reranker model is LLM reranker or not."""
        if model_path.startswith('https'):
            return 'siliconcloud'
        config_path = os.path.join(model_path, 'config.json')
        if not os.path.exists(config_path):
            if 'bge-reranker-v2-minicpm-layerwise' in config_path.lower():
                return 'bge'
            return 'bce'
        try:
            with open(config_path) as f:
                if 'bge-reranker-v2-minicpm-layerwise' in json.loads(f.read())['_name_or_path']:
                    return 'bge'
        except Exception as e:
            logger.warning(e)
        return 'bce'

    def _get_inputs(self, pairs, prompt=None, max_length=1024):
        """Build input tokens with query and chunks."""
        if prompt is None:
            prompt = "Given a query A and a passage B, determine whether the passage contains an answer to the query by providing a prediction of either 'Yes' or 'No'."
        sep = '\n'
        prompt_inputs = self.tokenizer(prompt, return_tensors=None, add_special_tokens=False)['input_ids']
        sep_inputs = self.tokenizer(sep, return_tensors=None, add_special_tokens=False)['input_ids']
        inputs = []
        for query, passage in pairs:
            query_inputs = self.tokenizer(f'A: {query}', return_tensors=None, add_special_tokens=False, max_length=max_length * 3 // 4, truncation=True)
            passage_inputs = self.tokenizer(f'B: {passage}', return_tensors=None, add_special_tokens=False, max_length=max_length, truncation=True)
            item = self.tokenizer.prepare_for_model([self.tokenizer.bos_token_id] + query_inputs['input_ids'], sep_inputs + passage_inputs['input_ids'], truncation='only_second', max_length=max_length, padding=False, return_attention_mask=False, return_token_type_ids=False, add_special_tokens=False)
            item['input_ids'] = item['input_ids'] + sep_inputs + prompt_inputs
            item['attention_mask'] = [1] * len(item['input_ids'])
            inputs.append(item)
        return self.tokenizer.pad(inputs, padding=True, max_length=max_length + len(sep_inputs) + len(prompt_inputs), pad_to_multiple_of=8, return_tensors='pt')

    def _sort(self, texts: List[str], query: str):
        """Rerank input texts, return descending indexes, indexes[0] is the
        nearest chunk."""
        pairs = []
        for text in texts:
            pairs.append([query, text])
        if 'bge' in self._type:
            import torch
            with torch.no_grad():
                inputs = self._get_inputs(pairs).to(self.model.device)
                all_scores = self.model(**inputs, return_dict=True, cutoff_layers=[28])
                scores = [scores[:, -1].view(-1).float() for scores in all_scores[0]]
                scores = scores[0].cpu().numpy()
        elif 'bce' in self._type:
            scores_list = self.bce_client.compute_score(pairs)
            scores = np.array(scores_list)
        else:
            self.client['api_rpm'].wait_sync(silent=True)
            url = 'https://api.siliconflow.cn/v1/rerank'
            payload = {'model': 'netease-youdao/bce-reranker-base_v1', 'query': query, 'documents': texts, 'return_documents': False, 'max_chunks_per_doc': 832, 'overlap_tokens': 32}
            headers = {'accept': 'application/json', 'content-type': 'application/json', 'authorization': self.client['api_token']}
            try:
                response = requests.post(url, json=payload, headers=headers)
                json_obj = json.loads(response.text)
                results = json_obj['results']
                indexes_list = [round(item['index']) for item in results]
                indexes = np.array(indexes_list).astype(np.int32)
                return indexes[0:self.topn]
            except Exception as e:
                logger.error(f'reranker API fail {e}, use default order')
                return [i for i in range(min(len(texts), self.topn))]
        return scores.argsort()[::-1][0:self.topn]

    def rerank(self, query: str, chunks: List[Chunk]):
        """Rerank faiss search results."""
        if not chunks:
            return []
        texts = []
        for chunk in chunks:
            texts.append(chunk.content_or_path)
        indexes = self._sort(texts=texts, query=query)
        return [chunks[i] for i in indexes]

@classmethod
def model_type(self, model_path):
    """Check reranker model is LLM reranker or not."""
    if model_path.startswith('https'):
        return 'siliconcloud'
    config_path = os.path.join(model_path, 'config.json')
    if not os.path.exists(config_path):
        if 'bge-reranker-v2-minicpm-layerwise' in config_path.lower():
            return 'bge'
        return 'bce'
    try:
        with open(config_path) as f:
            if 'bge-reranker-v2-minicpm-layerwise' in json.loads(f.read())['_name_or_path']:
                return 'bge'
    except Exception as e:
        logger.warning(e)
    return 'bce'

class FileOperation:
    """Encapsulate all file reading operations."""

    def __init__(self):
        self.image_suffix = ['.jpg', '.jpeg', '.png', '.bmp']
        self.md_suffix = '.md'
        self.text_suffix = ['.txt', '.text']
        self.excel_suffix = ['.xlsx', '.xls', '.csv']
        self.pdf_suffix = '.pdf'
        self.ppt_suffix = '.pptx'
        self.html_suffix = ['.html', '.htm', '.shtml', '.xhtml']
        self.word_suffix = ['.docx', '.doc']
        self.code_suffix = ['.py']
        self.normal_suffix = [self.md_suffix] + self.text_suffix + self.excel_suffix + [self.pdf_suffix] + self.word_suffix + [self.ppt_suffix] + self.html_suffix

    def save_image(self, uri: str, outdir: str):
        """Save image URI to local dir.

        Return None if failed.
        """
        images_dir = os.path.join(outdir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        md5 = hashlib.md5()
        md5.update(uri.encode('utf8'))
        uuid = md5.hexdigest()[0:6]
        filename = uuid + uri[uri.rfind('.'):]
        image_path = os.path.join(images_dir, filename)
        logger.info('download {}'.format(uri))
        try:
            if uri.startswith('http'):
                resp = requests.get(uri, stream=True)
                if resp.status_code == 200:
                    with open(image_path, 'wb') as image_file:
                        for chunk in resp.iter_content(1024):
                            image_file.write(chunk)
            else:
                shutil.copy(uri, image_path)
        except Exception as e:
            logger.debug(e)
            return (None, None)
        return (uuid, image_path)

    def get_type(self, filepath: str):
        """Get filetype depends on URI suffix."""
        filepath = filepath.lower()
        if filepath.endswith(self.pdf_suffix):
            return 'pdf'
        if filepath.endswith(self.md_suffix):
            return 'md'
        if filepath.endswith(self.ppt_suffix):
            return 'ppt'
        for suffix in self.image_suffix:
            if filepath.endswith(suffix):
                return 'image'
        for suffix in self.text_suffix:
            if filepath.endswith(suffix):
                return 'text'
        for suffix in self.word_suffix:
            if filepath.endswith(suffix):
                return 'word'
        for suffix in self.excel_suffix:
            if filepath.endswith(suffix):
                return 'excel'
        for suffix in self.html_suffix:
            if filepath.endswith(suffix):
                return 'html'
        for suffix in self.code_suffix:
            if filepath.endswith(suffix):
                return 'code'
        return None

    def md5(self, filepath: str):
        hash_object = hashlib.sha256()
        with open(filepath, 'rb') as file:
            chunk_size = 8192
            while (chunk := file.read(chunk_size)):
                hash_object.update(chunk)
        return hash_object.hexdigest()[0:8]

    def summarize(self, files: list):
        success = 0
        skip = 0
        failed = 0
        for file in files:
            if file.state:
                success += 1
            elif file.reason == 'skip':
                skip += 1
            else:
                failed += 1
        logger.info('累计{}文件，成功{}个，跳过{}个，异常{}个'.format(len(files), success, skip, failed))

    def scan_dir(self, repo_dir: str):
        files = []
        for root, _, filenames in os.walk(repo_dir):
            for filename in filenames:
                _type = self.get_type(filename)
                if _type is not None:
                    files.append(FileName(root=root, filename=filename, _type=_type))
        return files

    def read_pdf(self, filepath: str):
        text = ''
        with fitz.open(filepath) as pages:
            for page in pages:
                text += page.get_text()
                tables = page.find_tables()
                for table in tables:
                    tablename = '_'.join(filter(lambda x: x is not None and 'Col' not in x, table.header.names))
                    pan = table.to_pandas()
                    json_text = pan.dropna(axis=1).to_json(force_ascii=False)
                    text += tablename
                    text += '\n'
                    text += json_text
                    text += '\n'
        return text

    def read_excel(self, filepath: str):
        table = None
        if filepath.endswith('.csv'):
            table = pd.read_csv(filepath)
        else:
            table = pd.read_excel(filepath)
        if table is None:
            return ''
        json_text = table.dropna(axis=1).to_json(force_ascii=False)
        return json_text

    def read(self, filepath: str):
        file_type = self.get_type(filepath)
        text = ''
        if not os.path.exists(filepath):
            return (text, None)
        try:
            if file_type == 'md' or file_type == 'text':
                with open(filepath, encoding='utf-8') as f:
                    text = f.read()
            elif file_type == 'pdf':
                text += self.read_pdf(filepath)
            elif file_type == 'excel':
                text += self.read_excel(filepath)
            elif file_type == 'word' or file_type == 'ppt':
                import textract
                text = textract.process(filepath).decode('utf8')
                if file_type == 'ppt':
                    text = text.replace('\n', ' ')
            elif file_type == 'html':
                with open(filepath) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    text += soup.text
            elif file_type == 'code':
                with open(filepath, errors='ignore') as f:
                    text += f.read()
        except Exception as e:
            logger.error((filepath, str(e)))
            return ('', e)
        if file_type != 'code':
            text = text.replace('\n\n', '\n')
            text = text.replace('\n\n', '\n')
            text = text.replace('\n\n', '\n')
            text = text.replace('  ', ' ')
            text = text.replace('  ', ' ')
            text = text.replace('  ', ' ')
        return (text, None)

def get_type(self, filepath: str):
    """Get filetype depends on URI suffix."""
    filepath = filepath.lower()
    if filepath.endswith(self.pdf_suffix):
        return 'pdf'
    if filepath.endswith(self.md_suffix):
        return 'md'
    if filepath.endswith(self.ppt_suffix):
        return 'ppt'
    for suffix in self.image_suffix:
        if filepath.endswith(suffix):
            return 'image'
    for suffix in self.text_suffix:
        if filepath.endswith(suffix):
            return 'text'
    for suffix in self.word_suffix:
        if filepath.endswith(suffix):
            return 'word'
    for suffix in self.excel_suffix:
        if filepath.endswith(suffix):
            return 'excel'
    for suffix in self.html_suffix:
        if filepath.endswith(suffix):
            return 'html'
    for suffix in self.code_suffix:
        if filepath.endswith(suffix):
            return 'code'
    return None

def main():
    """Function to start the server without running a separate process."""
    args = parse_args()
    server_ready = Value('i', 0)
    if not args.unittest:
        llm_serve(args.config_path, server_ready)
    else:
        queries = ['今天天气如何？']
        start_llm_server(config_path=args.config_path)
        from .llm_client import ChatClient
        client = ChatClient(config_path=args.config_path)
        for query in queries:
            print(client.generate_response(prompt=query, history=[], backend='local'))

@DeprecationWarning
class SourceGraphProxy:
    """A class to serve as a proxy for interacting with the Source Graph.

    Args:
        config_path (str): Path to the configuration file.
        topk (int, optional): Top K results to consider from the search. Defaults to 1.  # noqa E501
        language (str, optional): Language for the system prompts - 'zh' for Chinese and 'en' for English. Defaults to 'zh'.  # noqa E501

    Attributes:
        config_path (str): The path of the configuration file.
        sg_config (dict): Configuration settings for sourcegraph search.
        topk (int): Top K results to consider from the search.
        language (str): Language for the system prompts.
        CHOICE_TEMPLATE (str): Template string for generating choice based on selected language.  # noqa E501
        KEYWORDS_TEMPLATE (str): Template string for generating keywords based on selected language.  # noqa E501
    """

    def __init__(self, config_path: str, topk=1, language: str='zh') -> None:
        """Init searcher with config."""
        self.config_path = config_path
        self.sg_config = None
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.sg_config = config['sg_search']
        self.topk = topk
        self.language = language
        if self.language == 'zh':
            self.CHOICE_TEMPLATE = '“{}”\n请仔细阅读以上问题，请问应该查询以下哪个开源项目：\n'
            self.KEYWORDS_TEMPLATE = '“{}”\n请仔细阅读以上问题，提取其中可用作搜索引擎的关键字，关键字之间,分隔，不要解释。'
        else:
            self.CHOICE_TEMPLATE = '"{}"\nPlease read the above question carefully, which of the following open-source projects should this question refer to: \n'
            self.KEYWORDS_TEMPLATE = '"{}"\nPlease read the above questions carefully, extract the keywords which can be used as search engines, between keywords, separate, do not explain.'

    def command(self, txt: str):
        """Executes a shell command and returns its output.

        Args:
            txt (str): Command to be executed in the shell.

        Returns:
            str: Output of the shell command execution.
        """
        logger.debug('cmd: {}'.format(txt))
        cmd = os.popen(txt)
        return cmd.read().rstrip().lstrip()

    def extract_sg_result(self, jsonstr):
        """Extracts the desired data from the source graph result.

        Args:
            jsonstr (str): JSON string containing source graph search result.

        Returns:
            list: List of dictionaries each contains 'filepath' and 'content' of the files returned by source graph.  # noqa E501
        """
        ret = []
        try:
            root = json.loads(jsonstr)
            results = root['Results']
            for result in results:
                if 'FileMatch' != result['__typename']:
                    continue
                content = result['file']['content']
                path = result['file']['path']
                ret.append({'filepath': path, 'content': content})
                if len(ret) >= self.topk:
                    break
        except Exception as e:
            logger.warning('{} when source graph parse {}'.format(str(e), jsonstr))
        return ret

    async def choose_repo(self, llm_client, question, groupname):
        """Interactively assists user to select a repository for search based
        on user's question.

        Args:
            llm_client: Client instance for LLM.
            question (str): User's question.
            groupname (str): Name of the user's group.

        Returns:
            str: The ID of selected repository.
        """
        prompt = self.CHOICE_TEMPLATE.format(question)
        keys = self.sg_config.keys()
        skip = ['binary_src_path', 'src_access_token']
        repos = {}
        for key in keys:
            if key in skip:
                continue
            introduction = self.sg_config[key]['introduction']
            prompt += f'* {key} {introduction}\n'
            repos[key] = self.sg_config[key]
        prompt += '* none '
        choice = await llm_client.chat(prompt=prompt).strip()
        target_repo_id = None
        for key in repos.keys():
            if key in choice:
                target_repo_id = repos[key]['github_repo_id']
                break
        return target_repo_id

    async def search(self, llm_client, question, groupname) -> List[str]:
        """Performs a search operation in the selected repository based on the
        user's question.

        Args:
            llm_client: Client instance for LLM.
            question (str): User's question.
            groupname (str): Name of the user's group.

        Returns:
            str: Search result from source graph in JSON format.
        """
        repo_id = await self.choose_repo(llm_client, question, groupname)
        if repo_id is None:
            logger.warning('cannot choose repo_id')
            return ''
        ENV = 'export SRC_ACCESS_TOKEN="{}" && '.format(self.sg_config['src_access_token'])
        BINARY = self.sg_config['binary_src_path']
        if not os.path.exists(BINARY):
            raise Exception('{} not exist'.format(BINARY))
        prompt = self.KEYWORDS_TEMPLATE.format(question)
        entities = []
        entity_str = ''
        try:
            entity_str = await llm_client.chat(prompt=prompt)
            separator = ','
            if '，' in entity_str:
                separator = '，'
            entities = [item for item in entity_str.split(separator) if item.strip()]
        except Exception as e:
            logger.error('parse {} failed {}.'.format(entity_str, str(e)))
            entities = []
        search_items = []
        for entity in entities:
            cmd_doc = "{} search -json 'repo:{} lang:MarkDown {}' ".format(BINARY, repo_id, entity)
            cmd_return = self.command(ENV + cmd_doc)
            search_items += self.extract_sg_result(cmd_return)
            cmd_python = "{} search -json 'repo:{} lang:Python {}' ".format(BINARY, repo_id, entity)
            cmd_return = self.command(ENV + cmd_python)
            search_items += self.extract_sg_result(cmd_return)
        if len(search_items) < 1:
            return None
        return search_items

def extract_sg_result(self, jsonstr):
    """Extracts the desired data from the source graph result.

        Args:
            jsonstr (str): JSON string containing source graph search result.

        Returns:
            list: List of dictionaries each contains 'filepath' and 'content' of the files returned by source graph.  # noqa E501
        """
    ret = []
    try:
        root = json.loads(jsonstr)
        results = root['Results']
        for result in results:
            if 'FileMatch' != result['__typename']:
                continue
            content = result['file']['content']
            path = result['file']['path']
            ret.append({'filepath': path, 'content': content})
            if len(ret) >= self.topk:
                break
    except Exception as e:
        logger.warning('{} when source graph parse {}'.format(str(e), jsonstr))
    return ret

class WebSearch:
    """This class provides functionality to perform web search operations.

    Attributes:
        config_path (str): Path to the configuration file.
        retry (int): Number of times to retry a request before giving up.

    Methods:
        load_key(): Retrieves API key from the config file.
        load_save_dir(): Gets the directory path for saving results.
        google(query: str, max_article:int): Performs Google search for the given query and returns top max_article results.  # noqa E501
        save_search_result(query:str, articles: list): Saves the search result into a text file.  # noqa E501
        get(query: str, max_article=1): Searches with cache. If the query already exists in the cache, return the cached result.  # noqa E501
    """

    def __init__(self, config_path: str, retry: int=1, language: str='zh') -> None:
        """Initializes the WebSearch object with the given config path and
        retry count."""
        self.search_config = None
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.search_config = types.SimpleNamespace(**config['web_search'])
        self.retry = retry
        self.language = language

    def load_key():
        try:
            return self.search_config.serper_x_api_key
        except Exception as e:
            return ''

    def fetch_url(self, query: str, target_link: str, brief: str=''):
        if not target_link.startswith('http'):
            return None
        logger.info(f'extract: {target_link}')
        try:
            content = ''
            if target_link.lower().endswith('.pdf') or target_link.lower().endswith('.docx'):
                logger.info(f'download and parse: {target_link}')
                response = requests.get(target_link, stream=True, allow_redirects=True)
                save_dir = self.search_config.save_dir
                basename = os.path.basename(target_link)
                save_path = os.path.join(save_dir, basename)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                file_opr = FileOperation()
                content, error = file_opr.read(filepath=save_path)
                if error is not None:
                    return error
                return Article(content=content, source=target_link, brief=brief)
            response = requests.get(target_link, timeout=30)
            doc = Document(response.text)
            content_html = doc.summary()
            title = doc.short_title()
            soup = BS(content_html, 'html.parser')
            if len(soup.text) < 4 * len(query):
                return None
            content = '{} {}'.format(title, soup.text)
            content = content.replace('\n\n', '\n')
            content = content.replace('\n\n', '\n')
            content = content.replace('  ', ' ')
            if not check_str_useful(content=content):
                return None
            return Article(content=content, source=target_link, brief=brief)
        except Exception as e:
            logger.error('fetch_url {}'.format(str(e)))
        return None

    def ddgs(self, query: str, max_article: int):
        """Run DDGS search based on query."""
        results = DDGS().text(query, max_results=20)
        filter_results = []
        for domain in self.search_config.domain_partial_order:
            for result in results:
                if domain in result['href']:
                    filter_results.append(result)
                    break
        logger.debug('filter results: {}'.format(filter_results))
        articles = []
        for result in filter_results:
            a = self.fetch_url(query=query, target_link=result['href'], brief=result['body'])
            if a is not None and len(a) > 0:
                articles.append(a)
            if len(articles) > max_article:
                break
        return articles

    def google(self, query: str, max_article: int):
        """Executes a google search based on the provided query.

        Parses the response and extracts the relevant URLs based on the
        priority defined in the configuration file. Performs a GET request on
        these URLs and extracts the title and content of the page. The content
        is cleaned and added to the articles list. Returns a list of articles.
        """
        url = 'https://google.serper.dev/search'
        if 'zh' in self.language:
            lang = 'zh-cn'
        else:
            lang = 'en'
        payload = json.dumps({'q': f'{query}', 'hl': lang})
        headers = {'X-API-KEY': self.search_config.serper_x_api_key, 'Content-Type': 'application/json'}
        response = requests.request('POST', url, headers=headers, data=payload, timeout=5)
        jsonobj = json.loads(response.text)
        logger.debug(jsonobj)
        keys = self.search_config.domain_partial_order
        urls = {}
        normal_urls = []
        for organic in jsonobj['organic']:
            link = ''
            logger.debug(organic)
            if 'link' in organic:
                link = organic['link']
            else:
                link = organic['sitelinks'][0]['link']
            for key in keys:
                if key in link:
                    if key not in urls:
                        urls[key] = [link]
                    else:
                        urls[key].append(link)
                    break
                else:
                    normal_urls.append(link)
        logger.debug(f'gather urls: {urls}')
        links = []
        for key in keys:
            if key in urls:
                links += urls[key]
        target_links = links[0:max_article]
        logger.debug(f'target_links:{target_links}')
        articles = []
        for target_link in target_links:
            a = self.fetch_url(query=query, target_link=target_link)
            if a is not None:
                articles.append(a)
        return articles

    def save_search_result(self, query: str, articles: list):
        """Writes the search results (articles) for the provided query into a
        text file.

        If the directory does not exist, it creates one. In case of an error,
        logs a warning message.
        """
        try:
            save_dir = self.search_config.save_dir
            if save_dir is None:
                return
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            filepath = os.path.join(save_dir, query)
            text = ''
            if len(articles) > 0:
                texts = [str(a) for a in articles]
                text = '\n\n'.join(texts)
            with open(filepath, 'w', encoding='utf8') as f:
                f.write(text)
        except Exception as e:
            logger.warning(f'error while saving search result {str(e)}')

    def logging_search_query(self, query: str):
        """Logging search query to txt file."""
        save_dir = self.search_config.save_dir
        if save_dir is None:
            return
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        filepath = os.path.join(save_dir, 'search_query.txt')
        with open(filepath, 'a') as f:
            f.write(query)
            f.write('\n')

    def get(self, query: str, max_article=1):
        """Executes a google search with cache.

        If the query already exists in the cache, returns the cached result. If
        an exception occurs during the process, retries the request based on
        the retry count. Sleeps for a random time interval between retries.
        """
        query = query.strip()
        query = query[0:32]
        try:
            self.logging_search_query(query=query)
            articles = []
            engine = self.search_config.engine.lower()
            if engine == 'ddgs':
                articles = self.ddgs(query=query, max_article=max_article)
            elif engine == 'serper':
                articles = self.google(query=query, max_article=max_article)
            self.save_search_result(query=query, articles=articles)
            return (articles, None)
        except Exception as e:
            logger.error(('web_search exception', query, str(e)))
            return ([], Exception('search fail, please check TOKEN'))
        return ([], None)

def fetch_url(self, query: str, target_link: str, brief: str=''):
    if not target_link.startswith('http'):
        return None
    logger.info(f'extract: {target_link}')
    try:
        content = ''
        if target_link.lower().endswith('.pdf') or target_link.lower().endswith('.docx'):
            logger.info(f'download and parse: {target_link}')
            response = requests.get(target_link, stream=True, allow_redirects=True)
            save_dir = self.search_config.save_dir
            basename = os.path.basename(target_link)
            save_path = os.path.join(save_dir, basename)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            file_opr = FileOperation()
            content, error = file_opr.read(filepath=save_path)
            if error is not None:
                return error
            return Article(content=content, source=target_link, brief=brief)
        response = requests.get(target_link, timeout=30)
        doc = Document(response.text)
        content_html = doc.summary()
        title = doc.short_title()
        soup = BS(content_html, 'html.parser')
        if len(soup.text) < 4 * len(query):
            return None
        content = '{} {}'.format(title, soup.text)
        content = content.replace('\n\n', '\n')
        content = content.replace('\n\n', '\n')
        content = content.replace('  ', ' ')
        if not check_str_useful(content=content):
            return None
        return Article(content=content, source=target_link, brief=brief)
    except Exception as e:
        logger.error('fetch_url {}'.format(str(e)))
    return None

def fetch_web_content(target_link: str):
    """Fetches and parses the content of the target URL.

    Extracts the main content and title from the HTML of the page. Returns the
    title and content as a single string.
    """
    response = requests.get(target_link, timeout=60)
    doc = Document(response.text)
    content_html = doc.summary()
    title = doc.short_title()
    soup = BS(content_html, 'html.parser')
    ret = '{} {}'.format(title, soup.text)
    return ret

