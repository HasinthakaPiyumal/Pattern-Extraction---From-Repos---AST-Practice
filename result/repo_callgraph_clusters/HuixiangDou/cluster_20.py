# Cluster 20

def split(_input, output_dir):
    """把一个完整的聊天日志，简化、划成不同群的群聊记录。"""
    if not os.path.exists(_input):
        logger.error('{} not exist'.format(_input))
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    groups = {}
    json_str = ''
    with open(_input) as f:
        while True:
            line = f.readline()
            if not line:
                break
            json_str += line
            if line == '}\n':
                try:
                    json_obj = json.loads(json_str)
                    if 'data' in json_obj:
                        data = json_obj['data']
                        data['messageType'] = json_obj['messageType']
                        if 'fromGroup' in data:
                            group_id = data['fromGroup']
                            if group_id in groups:
                                groups[group_id].append(data)
                            else:
                                groups[group_id] = [data]
                            json_str = ''
                            continue
                        logger.error((json_str, 'no fromGroup'))
                    if 'answer' in json_obj:
                        if 'groupId' in json_obj:
                            group_id = json_obj['groupId']
                            if group_id in groups:
                                groups[group_id].append(data)
                            else:
                                groups[group_id] = [data]
                            json_str = ''
                            continue
                        logger.error((json_str, 'has answer but no groupId'))
                except Exception as e:
                    logger.error((e, json_str))
                json_str = ''
    msg_sum = 0
    for group_id, message_list in groups.items():
        msg_sum += len(message_list)
        logger.info('{} {}'.format(group_id, len(message_list)))
        if len(message_list) < 1000:
            logger.debug('msg count number too small, skip dump')
            continue
        filepath = os.path.join(output_dir, '{}@reconstruct.txt'.format(group_id))
        with open(filepath, 'w') as fout:
            idx = 0
            for json_obj in message_list:
                obj = simplify_wx_object(json_obj)
                obj['id'] = idx
                idx += 1
                fout.write(json.dumps(obj, ensure_ascii=False))
                fout.write('\n')
    logger.info('sum message {}'.format(msg_sum))

def intention(output_dir):
    """扫描一个群的流式聊天记录，把同一个人 18 秒内发的连续内容合并."""
    if not os.path.exists(output_dir):
        logger.error('{} not exist'.format(output_dir))
        return
    sender_cnt = {}
    group_intros = {'20814553575': '\n名词解释：\nopen-compass/opencompass : 用于评测大型语言模型（LLM）. 它提供了完整的开源可复现的评测框架，支持大语言模型、多模态模型的一站式评测，基于分布式技术，对大参数量模型亦能实现高效评测。评测方向汇总为知识、语言、理解、推理、考试五大能力维度，整合集纳了超过70个评测数据集，合计提供了超过40万个模型评测问题，并提供长文本、安全、代码3类大模型特色技术能力评测。\nopenmmlab/mmpose is an open-source toolbox for pose estimation based on PyTorch\nopenmmlab/mmdeploy is an open-source deep learning model deployment toolset\nopenmmlab/mmdetection is an open source object detection toolbox based on PyTorch.\nlmdeploy 是一个用于压缩、部署和服务 LLM（Large Language Model）的工具包。是一个服务端场景下，transformer 结构 LLM 部署工具，支持 GPU 服务端部署，速度有保障，支持 Tensor Parallel，多并发优化，功能全面，包括模型转换、缓存历史会话的 cache feature 等. 它还提供了 WebUI、命令行和 gRPC 客户端接入。\n茴香豆（HuixiangDou）是一个基于 LLM 的群聊知识助手。设计拒答、响应两阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。\nxtuner is an efficient, flexible and full-featured toolkit for fine-tuning large models.\nmmyolo : YOLO series toolbox and benchmark. Implemented RTMDet, RTMDet-Rotated,YOLOv5, YOLOv6, YOLOv7, YOLOv8,YOLOX, PPYOLOE, etc.\n\n群描述：\n这是 openmmlab 贡献者和用户群。用户会发一些相关技术疑问。'}
    files = os.listdir(output_dir)
    for file in files:
        filepath = os.path.join(output_dir, file)
        if not filepath.endswith('@chatroom@reconstruct.txt'):
            continue
        introduction = ''
        group_id = os.path.basename(filepath)
        group_id = group_id.split('@')[0]
        if group_id in group_intros:
            introduction = group_intros[group_id]
        if len(introduction) < 1:
            continue
        window_history = []
        MAX_WINDOW_SIZE = 12
        STME_SPAN = 18
        raw_chats = []
        with open(filepath) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if len(line) < 2:
                    continue
                json_obj = json.loads(line)
                if json_obj['show'] == 'ref':
                    continue
                raw_chats.append(json_obj)
        idx = 0
        concat_chats = []
        target = None
        target_timestamp = 0
        while idx < len(raw_chats):
            chat = raw_chats[idx]
            idx += 1
            if chat['timestamp'] == target_timestamp:
                continue
            if target is None:
                target = chat
                target_timestamp = target['timestamp']
            elif target['sender'] == chat['sender'] and abs(chat['timestamp'] - target_timestamp) < STME_SPAN:
                target_timestamp = chat['timestamp']
                target['text'] += '\n'
                target['text'] += chat['text']
            else:
                concat_chats.append(target)
                target = None
        if target is not None:
            concat_chats.append(target)
        outfilepath = filepath + '.concat'
        with open(outfilepath, 'w') as f:
            f.write(json.dumps(concat_chats, indent=2, ensure_ascii=False))
        logger.info('concat {} to {} msg'.format(len(raw_chats), len(concat_chats)))
        for json_obj in concat_chats:
            text = json_obj['text']
            if len(text) < 1:
                continue
            window_history.append(json_obj)
            if is_question(text):
                json_obj['is_question'] = True
                window_history = window_history[-MAX_WINDOW_SIZE:-1]
                cr_text, success = coref_res(json_obj, window=window_history, group_intro=introduction)
                json_obj['cr_window'] = window_history
                if success:
                    json_obj['cr_text'] = cr_text
                    json_obj['cr_need'] = True
                else:
                    json_obj['cr_need'] = False
            else:
                json_obj['is_question'] = False
            outfilepath = filepath + '.llm'
            with open(outfilepath, 'a') as fout:
                json_text = json.dumps(json_obj, ensure_ascii=False)
                fout.write(json_text)
                fout.write('\n')

def build_context(sender: str, query: str, window: list):
    context = ''
    for item in window:
        context += '{}: {}\n'.format(item['sender'], item['text'])
    context += '标注问题：\n'
    context += '{}: {}\n'.format(sender, query)
    return context

def test_rpm():
    rpm = RPM(30)
    for i in range(40):
        rpm.wait()
        print(i)
    time.sleep(5)
    for i in range(40):
        rpm.wait()
        print(i)

def test_tpm():
    tpm = TPM(2000)
    for i in range(20):
        tpm.wait(silent=False, token_count=150)
        print(i)

def test_faiss():
    a = Chunk('hello world', {'source': 'unittest'})
    b = Chunk('resource/figures/inside-mmpose.jpg', {'source': 'unittest'}, 'image')
    c = Chunk('resource/figures/wechat.jpg', {'source': 'test image'}, 'image')
    chunks = [a, b, c]
    save_path = '/tmp/faiss'
    model_config = {'embedding_model_path': '/data2/khj/bge-m3'}
    embedder = Embedder(model_config)
    Faiss.save_local(folder_path=save_path, chunks=chunks, embedder=embedder)
    assert os.path.exists(os.path.join(save_path, 'embedding.faiss'))
    g = Faiss.load_local(save_path)
    for idx, c in enumerate(g.chunks):
        assert str(chunks[idx]) == str(c)
    target = 'resource/figures/inside-mmpose.jpg'
    query = Query(image=target)
    pairs = g.similarity_search_with_query(query=query, embedder=embedder)
    chunk, score = pairs[0]
    assert chunk.content_or_path == target
    assert score >= 0.9999

def test_embedder():
    emb = Embedder({'embedding_model_path': '/data2/khj/bge-m3'})
    sentence = 'hello world '
    sentence_16k = sentence * (16384 // len(sentence))
    image_path = 'resource/figures/wechat.jpg'
    text_feature = emb.embed_query(text=sentence_16k)
    image_feature = emb.embed_query(path=image_path)
    query_feature = emb.embed_query(text=sentence_16k, path=image_path)
    sim1 = query_feature @ text_feature.T
    sim2 = query_feature @ image_feature.T
    assert sim1.item() >= 0.4
    assert sim2.item() >= 0.4

def test_query():
    q = Query(text='hello', image='test.jpg')
    q_str = '{}'.format(q)
    assert 'hello' in q_str
    assert 'image=' in q_str
    p = Query('hello')
    p_str = '{}'.format(p)
    assert 'text=' in p_str

def run():
    config_path = build_config_path()
    actions = {'feature_store': 'python3 -m huixiangdou.services.store --config_path {}', 'main': 'python3 -m huixiangdou.main --config_path {}'}
    reports = ['HuixiangDou daily smoke:']
    for action, cmd in actions.items():
        cmd = cmd.format(config_path)
        log = command(cmd)
        if 'ConnectionResetError' in log:
            logger.info(f'*{action}, {cmd}')
            assert 0
        else:
            logger.info(f'*{action}, passed')

def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.info('Creating a new event loop in a sub-thread.')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def allow_scheduler(task):
    lock = Lock(r, f'{biz_const.RDS_KEY_SCHEDULER}-{task}')
    if lock.acquire(blocking=False):
        logger.info(f'{biz_const.RDS_KEY_SCHEDULER}-{task} is locked')
        return True
    return False

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
def print_env(cls):
    methods = [method for method in cls.__dict__ if callable(getattr(HuixiangDouEnv, method)) and method != 'print_env']
    for method in methods:
        f = getattr(HuixiangDouEnv, method)
        value = f()
        logger.info(f'[config] {method}: {value}')

def download_and_unzip(main_args):
    zip_filepath = os.path.join(main_args.feature_local, 'workdir.zip')
    main_args.work_dir = os.path.join(main_args.feature_local, 'workdir')
    logger.info(f'assign {main_args.work_dir} to args.work_dir')
    download_cmd = f'wget -O {zip_filepath} {main_args.feature_url}'
    os.system(download_cmd)
    if not os.path.exists(zip_filepath):
        raise Exception(f'zip filepath {zip_filepath} not exist.')
    unzip_cmd = f'unzip -o {zip_filepath} -d {main_args.feature_local}'
    os.system(unzip_cmd)
    if not os.path.exists(main_args.work_dir):
        raise Exception(f'feature dir {zip_dir} not exist.')

def build_feature_store(main_args):
    if os.path.exists('workdir'):
        logger.warning('feature_store `workdir` already exist, skip')
        return
    logger.info('start build feature_store..')
    os.system('python3 -m huixiangdou.services.store --config_path {}'.format(main_args.config_path))

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

def distance(self, text1: str, text2: str) -> float:
    emb1 = self.embed_query(text=text1)
    emb2 = self.embed_query(text=text2)
    if self.distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
        distance = np.linalg.norm(emb1 - emb2)
        return distance
    raise ValueError('Unsupported distance strategy')

def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.info('Creating a new event loop in a sub-thread.')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

class TextSplitter(ABC):
    """Interface for splitting text into chunks."""

    def __init__(self, chunk_size: int=832, chunk_overlap: int=32, length_function: Callable[[str], int]=len, keep_separator: Union[bool, Literal['start', 'end']]=False, add_start_index: bool=False, strip_whitespace: bool=True) -> None:
        """Create a new TextSplitter.

        Args:
            chunk_size: Maximum size of chunks to return
            chunk_overlap: Overlap in characters between chunks
            length_function: Function that measures the length of given chunks
            keep_separator: Whether to keep the separator and where to place it
                            in each corresponding chunk (True='start')
            add_start_index: If `True`, includes chunk's start index in metadata
            strip_whitespace: If `True`, strips whitespace from the start and end of
                              every chunk
        """
        if chunk_overlap > chunk_size:
            raise ValueError(f'Got a larger chunk overlap ({chunk_overlap}) than chunk size ({chunk_size}), should be smaller.')
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        self._keep_separator = keep_separator
        self._add_start_index = add_start_index
        self._strip_whitespace = strip_whitespace

    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """Split text into multiple components."""

    def create_chunks(self, texts: List[str], metadatas: Optional[List[dict]]=None) -> List[Chunk]:
        """Create chunks from a list of texts."""
        _metadatas = metadatas or [{}] * len(texts)
        chunks = []
        for i, text in enumerate(texts):
            index = 0
            previous_chunk_len = 0
            for chunk in self.split_text(text):
                metadata = copy.deepcopy(_metadatas[i])
                if self._add_start_index:
                    offset = index + previous_chunk_len - self._chunk_overlap
                    index = text.find(chunk, max(0, offset))
                    metadata['start_index'] = index
                    previous_chunk_len = len(chunk)
                new_chunk = Chunk(content_or_path=chunk, metadata=metadata)
                chunks.append(new_chunk)
        return chunks

    def _join_chunks(self, chunks: List[str], separator: str) -> Optional[str]:
        text = separator.join(chunks)
        if self._strip_whitespace:
            text = text.strip()
        if text == '':
            return None
        else:
            return text

    def _merge_splits(self, splits: Iterable[str], separator: str) -> List[str]:
        separator_len = self._length_function(separator)
        chunks = []
        current_chunk: List[str] = []
        total = 0
        for d in splits:
            _len = self._length_function(d)
            if total + _len + (separator_len if len(current_chunk) > 0 else 0) > self._chunk_size:
                if total > self._chunk_size:
                    logger.warning(f'Created a chunk of size {total}, which is longer than the specified {self._chunk_size}')
                if len(current_chunk) > 0:
                    chunk = self._join_chunks(current_chunk, separator)
                    if chunk is not None:
                        chunks.append(chunk)
                    while total > self._chunk_overlap or (total + _len + (separator_len if len(current_chunk) > 0 else 0) > self._chunk_size and total > 0):
                        total -= self._length_function(current_chunk[0]) + (separator_len if len(current_chunk) > 1 else 0)
                        current_chunk = current_chunk[1:]
            current_chunk.append(d)
            total += _len + (separator_len if len(current_chunk) > 1 else 0)
        chunk = self._join_chunks(current_chunk, separator)
        if chunk is not None:
            chunks.append(chunk)
        return chunks

def __init__(self, chunk_size: int=832, chunk_overlap: int=32, length_function: Callable[[str], int]=len, keep_separator: Union[bool, Literal['start', 'end']]=False, add_start_index: bool=False, strip_whitespace: bool=True) -> None:
    """Create a new TextSplitter.

        Args:
            chunk_size: Maximum size of chunks to return
            chunk_overlap: Overlap in characters between chunks
            length_function: Function that measures the length of given chunks
            keep_separator: Whether to keep the separator and where to place it
                            in each corresponding chunk (True='start')
            add_start_index: If `True`, includes chunk's start index in metadata
            strip_whitespace: If `True`, strips whitespace from the start and end of
                              every chunk
        """
    if chunk_overlap > chunk_size:
        raise ValueError(f'Got a larger chunk overlap ({chunk_overlap}) than chunk size ({chunk_size}), should be smaller.')
    self._chunk_size = chunk_size
    self._chunk_overlap = chunk_overlap
    self._length_function = length_function
    self._keep_separator = keep_separator
    self._add_start_index = add_start_index
    self._strip_whitespace = strip_whitespace

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

class BM25Okapi:

    def __init__(self, k1=1.5, b=0.75, epsilon=0.25):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus_size = 0
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.average_idf = 0.0
        self.chunks = []
        self.tokenizer = jieba.analyse.extract_tags

    def _initialize(self, corpus):
        nd = {}
        num_doc = 0
        for document in corpus:
            self.doc_len.append(len(document))
            num_doc += len(document)
            frequencies = {}
            for word in document:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
            self.doc_freqs.append(frequencies)
            for word, freq in frequencies.items():
                try:
                    nd[word] += 1
                except KeyError:
                    nd[word] = 1
            self.corpus_size += 1
        self.avgdl = num_doc / self.corpus_size
        return nd

    def _tokenize_corpus(self, corpus):
        tokenized_corpus = self.tokenizer(corpus)
        return tokenized_corpus

    def save(self, chunks: List[Chunk], filedir: str):
        if len(chunks) < 1:
            return
        self.chunks = chunks
        filtered_corpus = []
        for c in chunks:
            content = c.content_or_path
            if self.tokenizer is not None:
                corpus = self.tokenizer(content)
                if content not in corpus:
                    corpus.append(content)
            else:
                logger.warning('No tokenizer, use naive split')
                corpus = content.split(' ')
            filtered_corpus.append(corpus)
        nd = self._initialize(filtered_corpus)
        self._calc_idf(nd)
        data = {'corpus_size': self.corpus_size, 'avgdl': self.avgdl, 'doc_freqs': self.doc_freqs, 'idf': self.idf, 'doc_len': self.doc_len, 'average_idf': self.average_idf, 'chunks': chunks}
        logger.info('bm250kpi dump..')
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        filepath = os.path.join(filedir, 'bm25.pkl')
        with open(filepath, 'wb') as f:
            pkl.dump(data, f)

    def load(self, filedir: str, tokenizer=None):
        self.tokenizer = tokenizer
        filepath = os.path.join(filedir, 'bm25.pkl')
        with open(filepath, 'rb') as f:
            data = pkl.load(f)
        self.corpus_size = data['corpus_size']
        self.avgdl = data['avgdl']
        self.doc_freqs = data['doc_freqs']
        self.idf = data['idf']
        self.doc_len = data['doc_len']
        self.average_idf = data['average_idf']
        self.chunks = data['chunks']

    def _calc_idf(self, nd):
        """
        Calculates frequencies of terms in documents and in corpus.
        This algorithm sets a floor on the idf values to eps * average_idf
        """
        idf_sum = 0
        negative_idfs = []
        for word, freq in nd.items():
            idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)
        self.average_idf = idf_sum / len(self.idf)
        eps = self.epsilon * self.average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_scores(self, query: List):
        """
        The ATIRE BM25 variant uses an idf function which uses a log(idf) score. To prevent negative idf scores,
        this algorithm also adds a floor to the idf value of epsilon.
        See [Trotman, A., X. Jia, M. Crane, Towards an Efficient and Effective Search Engine] for more info
        :param query:
        :return:
        """
        if type(query) is not list:
            raise ValueError('query must be list, tokenize it byself.')
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)
        for q in query:
            q_freq = np.array([doc.get(q) or 0 for doc in self.doc_freqs])
            score += (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) / (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score

    def get_batch_scores(self, query, doc_ids):
        """
        Calculate bm25 scores between query and subset of all docs
        """
        assert all((di < len(self.doc_freqs) for di in doc_ids))
        score = np.zeros(len(doc_ids))
        doc_len = np.array(self.doc_len)[doc_ids]
        for q in query:
            q_freq = np.array([self.doc_freqs[di].get(q) or 0 for di in doc_ids])
            score += (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) / (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score.tolist()

    def get_top_n(self, query: Union[List, str], n=5):
        if type(query) is str:
            if self.tokenizer is not None:
                queries = self.tokenizer(query)
            else:
                queries = query.split(' ')
        else:
            queries = query
        scores = self.get_scores(queries)
        top_n = np.argsort(scores)[::-1][:n]
        logger.info('{} {}'.format(scores, top_n))
        if abs(scores[top_n[0]]) < 1e-05:
            return []
        return [self.chunks[i] for i in top_n]

def get_top_n(self, query: Union[List, str], n=5):
    if type(query) is str:
        if self.tokenizer is not None:
            queries = self.tokenizer(query)
        else:
            queries = query.split(' ')
    else:
        queries = query
    scores = self.get_scores(queries)
    top_n = np.argsort(scores)[::-1][:n]
    logger.info('{} {}'.format(scores, top_n))
    if abs(scores[top_n[0]]) < 1e-05:
        return []
    return [self.chunks[i] for i in top_n]

@dataclass
class Chunk:
    """Class for storing a piece of text and associated metadata.

    Example:

        .. code-block:: python

            from huixiangdou.primitive import Chunk

            chunk = Chunk(
                content_or_path="Hello, world!",
                metadata={"source": "https://example.com"}
            )
    """
    content_or_path: str = ''
    metadata: dict = field(default_factory=dict)
    modal: str = 'text'

    def __post_init__(self):
        if self.modal not in ['text', 'image', 'audio', 'qa']:
            raise ValueError(f'Invalid modal: {self.modal}. Allowed values are: `text`, `image`, `audio`, `qa`')

    def __str__(self) -> str:
        """Override __str__ to restrict it to content_or_path and metadata."""
        if self.metadata:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}' metadata={self.metadata}"
        else:
            return f"modal='{self.modal}' content_or_path='{self.content_or_path}'"

    def __repr__(self) -> str:
        return self.__str__()

def __post_init__(self):
    if self.modal not in ['text', 'image', 'audio', 'qa']:
        raise ValueError(f'Invalid modal: {self.modal}. Allowed values are: `text`, `image`, `audio`, `qa`')

class FileName:
    """Record file original name, state and copied filepath with text
    format."""

    def __init__(self, root: str, filename: str, _type: str):
        self.root = root
        self.prefix = filename.replace('/', '_')
        self.basename = os.path.basename(filename)
        self.origin = os.path.join(root, filename)
        self.copypath = self.origin
        self._type = _type
        self.state = True
        self.reason = ''

    def __str__(self):
        return '{},{},{},{}\n'.format(self.basename, self.copypath, self.state, self.reason)

def __str__(self):
    return '{},{},{},{}\n'.format(self.basename, self.copypath, self.state, self.reason)

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

class NamedEntity2Chunk:
    """Save the relationship between Named Entity and Chunk to sqlite"""

    def __init__(self, file_dir: str, ignore_case=True):
        self.file_dir = file_dir
        self.ignore_case = ignore_case
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        self.conn = sqlite3.connect(os.path.join(file_dir, 'entity2chunk.sql'))
        self.cursor = self.conn.cursor()
        self.cursor.execute('\n        CREATE TABLE IF NOT EXISTS entities (\n            eid INTEGER PRIMARY KEY,\n            chunk_ids TEXT\n        )\n        ')
        self.conn.commit()
        self.entities = []
        self.entity_path = os.path.join(self.file_dir, 'entities.json')
        if os.path.exists(self.entity_path):
            with open(self.entity_path) as f:
                self.entities = json.load(f)
                if self.ignore_case:
                    for id, value in enumerate(self.entities):
                        self.entities[id] = value.lower()

    def clean(self):
        self.cursor.execute('DROP TABLE entities;')
        self.cursor.execute('\n        CREATE TABLE IF NOT EXISTS entities (\n            eid INTEGER PRIMARY KEY,\n            chunk_ids TEXT\n        )\n        ')
        self.conn.commit()

    def insert_relation(self, eid: int, chunk_ids: List[int]):
        """Insert the relationship between keywords id and List of chunk_id"""
        chunk_ids_str = ','.join(map(str, chunk_ids))
        self.cursor.execute('INSERT INTO entities (eid, chunk_ids) VALUES (?, ?)', (eid, chunk_ids_str))
        self.conn.commit()

    def parse(self, text: str) -> List[int]:
        if self.ignore_case:
            text = text.lower()
        if len(self.entities) < 1:
            raise ValueError('entity list empty, please check feature_store init')
        ret = []
        for index, entity in enumerate(self.entities):
            if entity in text:
                ret.append(index)
        return ret

    def set_entity(self, entities: List[str]):
        json_str = json.dumps(entities, ensure_ascii=False)
        with open(self.entity_path, 'w') as f:
            f.write(json_str)
        self.entities = entities
        if self.ignore_case:
            for id, value in enumerate(self.entities):
                self.entities[id] = value.lower()

    def get_chunk_ids(self, entity_ids: Union[List, int]) -> Set:
        """Query by keywords ids"""
        if type(entity_ids) is int:
            entity_ids = [entity_ids]
        counter = dict()
        for eid in entity_ids:
            self.cursor.execute('SELECT chunk_ids FROM entities WHERE eid = ?', (eid,))
            result = self.cursor.fetchone()
            if result:
                chunk_ids = result[0].split(',')
                for chunk_id_str in chunk_ids:
                    chunk_id = int(chunk_id_str)
                    if chunk_id not in counter:
                        counter[chunk_id] = 1
                    else:
                        counter[chunk_id] += 1
        counter_list = []
        for k, v in counter.items():
            counter_list.append((k, v))
        counter_list.sort(key=lambda item: item[1], reverse=True)
        return counter_list

    def __del__(self):
        self.cursor.close()
        self.conn.close()

def parse(self, text: str) -> List[int]:
    if self.ignore_case:
        text = text.lower()
    if len(self.entities) < 1:
        raise ValueError('entity list empty, please check feature_store init')
    ret = []
    for index, entity in enumerate(self.entities):
        if entity in text:
            ret.append(index)
    return ret

class Faiss:

    def __init__(self, index: Any, chunks: List[Chunk], strategy: DistanceStrategy, k: int=30):
        """Initialize with necessary components."""
        self.index = index
        self.chunks = chunks
        self.strategy = strategy
        self.k = k

    def similarity_search(self, embedding: np.ndarray) -> List[Tuple[Chunk, float]]:
        """Return chunks most similar to query.

        Args:
            embedding: Embedding vector to look up chunk similar to.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. High score represents more similarity.
        """
        embedding = embedding.astype(np.float32)
        scores, indices = self.index.search(embedding, self.k)
        pairs = []
        for j, i in enumerate(indices[0]):
            if i == -1:
                continue
            chunk = self.chunks[i]
            score = scores[0][j]
            if self.strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
                rel_score = DistanceStrategy.euclidean_relevance_score_fn(score)
            elif self.strategy == DistanceStrategy.MAX_INNER_PRODUCT:
                rel_score = DistanceStrategy.max_inner_product_relevance_score_fn(score)
            else:
                raise ValueError('self.strategy unset')
            pairs.append((chunk, rel_score))
        if len(pairs) >= 2:
            assert pairs[0][1] >= pairs[1][1]
        return pairs

    def similarity_search_with_query(self, embedder: Embedder, query: Query, threshold: float=-1):
        """Return chunks most similar to query.

        Args:
            query: Multimodal query.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. Lower score represents more similarity.
        """
        if query.text is None and query.image is None:
            raise ValueError(f'Input query is None')
        if query.text is None and query.image is not None:
            if not embedder.support_image:
                logger.info('Embedder not support image')
                return []
        np_feature = embedder.embed_query(text=query.text, path=query.image)
        pairs = self.similarity_search(embedding=np_feature)
        highest_score = -1.0
        ret = []
        for pair in pairs:
            if pair[1] >= threshold:
                ret.append(pair)
            if highest_score < pair[1]:
                highest_score = pair[1]
        if len(ret) < 1:
            logger.info('highest score {}, threshold {}'.format(highest_score, threshold))
        return ret

    @classmethod
    def split_by_batchsize(self, chunks: List[Chunk]=[], batchsize: int=4):
        texts = [c for c in chunks if c.modal == 'text']
        images = [c for c in chunks if c.modal == 'image']
        block_text = []
        for i in range(0, len(texts), batchsize):
            block_text.append(texts[i:i + batchsize])
        block_image = []
        for i in range(0, len(images), batchsize):
            block_image.append(images[i:i + batchsize])
        return (block_text, block_image)

    @classmethod
    def build_index(self, np_feature: np.ndarray, distance_strategy: DistanceStrategy):
        dimension = np_feature.shape[-1]
        M = 16
        if distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
            index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_L2)
        elif distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
            index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_IP)
        else:
            raise ValueError('Unknown distance {}'.format(distance_strategy))
        index.hnsw.efSearch = 128
        return index

    @classmethod
    def save_local(self, folder_path: str, chunks: List[Chunk], embedder: Embedder) -> None:
        """Save FAISS index and store to disk.

        Args:
            folder_path: folder path to save.
            chunks: chunks to save.
            embedder: embedding function.
        """
        index = None
        batchsize = 1
        try:
            batchsize_str = os.getenv('HUIXIANGDOU_BATCHSIZE')
            if batchsize_str is None:
                logger.info('`export HUIXIANGDOU_BATCHSIZE=64` for faster feature building.')
            else:
                batchsize = int(batchsize_str)
        except Exception as e:
            logger.error(str(e))
            batchsize = 1
        if batchsize == 1:
            for chunk in tqdm(chunks, 'chunks'):
                np_feature = None
                try:
                    if chunk.modal == 'text' or chunk.modal == 'qa':
                        np_feature = embedder.embed_query(text=chunk.content_or_path)
                    elif chunk.modal == 'image':
                        np_feature = embedder.embed_query(path=chunk.content_or_path)
                    else:
                        raise ValueError(f'Unimplement chunk type: {chunk.modal}')
                except Exception as e:
                    logger.error('{}'.format(e))
                if np_feature is None:
                    logger.error('np_feature is None')
                    continue
                if index is None:
                    index = self.build_index(np_feature=np_feature, distance_strategy=embedder.distance_strategy)
                index.add(np_feature)
        else:
            block_text, block_image = self.split_by_batchsize(chunks=chunks, batchsize=batchsize)
            for subchunks in tqdm(block_text, 'build_text'):
                np_features = embedder.embed_query_batch_text(chunks=subchunks)
                if index is None:
                    index = self.build_index(np_feature=np_features, distance_strategy=embedder.distance_strategy)
                index.add(np_features)
            for subchunks in tqdm(block_image, 'build_image'):
                for chunk in subchunks:
                    np_feature = embedder.embed_query(path=chunk.content_or_path)
                    if np_feature is None:
                        logger.error('np_feature is None')
                        continue
                    if index is None:
                        index = self.build_index(np_feature=np_feature, distance_strategy=embedder.distance_strategy)
                    index.add(np_feature)
        path = Path(folder_path)
        path.mkdir(exist_ok=True, parents=True)
        faiss.write_index(index, str(path / 'embedding.faiss'))
        data = {'chunks': chunks, 'strategy': str(embedder.distance_strategy)}
        with open(path / 'chunks_and_strategy.pkl', 'wb') as f:
            pickle.dump(data, f)

    @classmethod
    def load_local(cls, folder_path: str) -> FAISS:
        """Load FAISS index and chunks from disk.

        Args:
            folder_path: folder path to load index and chunks from index.faiss
            index_name: for saving with a specific index file name
        """
        path = Path(folder_path)
        t1 = time.time()
        index = faiss.read_index(str(path / f'embedding.faiss'))
        strategy = DistanceStrategy.UNKNOWN
        t2 = time.time()
        with open(path / f'chunks_and_strategy.pkl', 'rb') as f:
            data = pickle.load(f)
            chunks = data['chunks']
            strategy_str = data['strategy']
            if 'EUCLIDEAN_DISTANCE' in strategy_str:
                strategy = DistanceStrategy.EUCLIDEAN_DISTANCE
            elif 'MAX_INNER_PRODUCT' in strategy_str:
                strategy = DistanceStrategy.MAX_INNER_PRODUCT
            else:
                raise ValueError('Unknown strategy type {}'.format(strategy_str))
        t3 = time.time()
        logger.info('Timecost for load dense, load faiss {} seconds, load chunk {} seconds'.format(int(t2 - t1), int(t3 - t2)))
        return cls(index, chunks, strategy)

def similarity_search_with_query(self, embedder: Embedder, query: Query, threshold: float=-1):
    """Return chunks most similar to query.

        Args:
            query: Multimodal query.
            k: Number of Documents to return. Defaults to 30.

        Returns:
            List of chunks most similar to the query text and L2 distance
            in float for each. Lower score represents more similarity.
        """
    if query.text is None and query.image is None:
        raise ValueError(f'Input query is None')
    if query.text is None and query.image is not None:
        if not embedder.support_image:
            logger.info('Embedder not support image')
            return []
    np_feature = embedder.embed_query(text=query.text, path=query.image)
    pairs = self.similarity_search(embedding=np_feature)
    highest_score = -1.0
    ret = []
    for pair in pairs:
        if pair[1] >= threshold:
            ret.append(pair)
        if highest_score < pair[1]:
            highest_score = pair[1]
    if len(ret) < 1:
        logger.info('highest score {}, threshold {}'.format(highest_score, threshold))
    return ret

@classmethod
def build_index(self, np_feature: np.ndarray, distance_strategy: DistanceStrategy):
    dimension = np_feature.shape[-1]
    M = 16
    if distance_strategy == DistanceStrategy.EUCLIDEAN_DISTANCE:
        index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_L2)
    elif distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
        index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_IP)
    else:
        raise ValueError('Unknown distance {}'.format(distance_strategy))
    index.hnsw.efSearch = 128
    return index

class Lark:
    """Lark bot http proxy."""

    def __init__(self, webhook, secret=None, pc_slide=False, fail_notice=False):
        """Init with hook url."""
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        logger.debug(f'webhook {webhook}')
        logger.error('This class would be deprecated in 2024.10.10')
        self.webhook = webhook
        self.secret = secret
        self.pc_slide = pc_slide
        self.fail_notice = fail_notice

    def is_not_null_and_blank_str(self, content: str):
        """Is content empty."""
        if content is not None and content.strip():
            return True
        return False

    def send_text(self, msg):
        """Send text to hook url."""
        data = {'msg_type': 'text', 'at': {}}
        if self.is_not_null_and_blank_str(msg):
            data['content'] = {'text': msg}
        else:
            logging.error('text类型，消息内容不能为空！')
            raise ValueError('text类型，消息内容不能为空！')
        logging.debug(f'text类型：{data}')
        return self.post(data)

    def post(self, data):
        """Post data to hook url."""
        try:
            post_data = json.dumps(data)
            response = requests.post(self.webhook, headers=self.headers, data=post_data, verify=False, timeout=60)
        except requests.exceptions.HTTPError as exc:
            code = exc.response.status_code
            reason = exc.response.reason
            logging.error(f'消息发送失败， HTTP error: {code}, reason: {reason}')
            raise
        except requests.exceptions.ConnectionError:
            logging.error('消息发送失败，HTTP connection error!')
            raise
        except requests.exceptions.Timeout:
            logging.error('消息发送失败，Timeout error!')
            raise
        except requests.exceptions.RequestException:
            logging.error('消息发送失败, Request Exception!')
            raise
        try:
            result = response.json()
        except json.JSONDecodeError:
            code = response.status_code
            text = response.text
            logging.error(f'服务器响应异常，状态码：{code}，响应内容：{text}')
            return {'errcode': 500, 'errmsg': '服务器响应异常'}
        logging.debug('发送结果：%s' % result)
        if self.fail_notice and result.get('errcode', True):
            time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            reason_text = result['errmsg'] if result.get('errmsg', False) else '未知异常'
            error_data = {'msgtype': 'text', 'text': {'content': f'[注意-自动通知]飞书机器人消息发送失败，时间：{time_now}，原因：{reason_text}，请及时跟进，谢谢!'}, 'at': {'isAtAll': False}}
            logging.error('消息发送失败，自动通知：%s' % error_data)
            requests.post(self.webhook, headers=self.headers, data=json.dumps(error_data), timeout=60)
        return result

def send_text(self, msg):
    """Send text to hook url."""
    data = {'msg_type': 'text', 'at': {}}
    if self.is_not_null_and_blank_str(msg):
        data['content'] = {'text': msg}
    else:
        logging.error('text类型，消息内容不能为空！')
        raise ValueError('text类型，消息内容不能为空！')
    logging.debug(f'text类型：{data}')
    return self.post(data)

class Message:

    def __init__(self):
        self.data = dict()
        self.type = None
        self.query = ''
        self.group_id = ''
        self.global_user_id = ''
        self._id = -1
        self.status = ''
        self.sender = ''
        self.url = ''
        self.push_content = ''
        self.content = ''
        self.title = ''
        self.desc = ''
        self.thumburl = ''
        self.md5 = ''
        self.length = 0
        self.new_msg_id = ''

    def parse(self, wx_msg: dict, bot_wxid: str, auth: str='', wkteam_ip_port: str=''):
        msg_type = wx_msg['messageType']
        parse_type = 'unknown'
        if 'data' not in wx_msg:
            self.status = 'skip'
            return Exception('data not in wx_msg')
        data = wx_msg['data']
        if not data:
            return Exception('data is None')
        if 'self' in data:
            if data['self']:
                return Exception('self msg, return')
        if 'msgId' in data:
            self._id = data['msgId']
        query = ''
        if 'atlist' in data:
            atlist = data['atlist']
            if bot_wxid not in atlist:
                self.status = 'skip'
                return Exception('atlist not contains bot')
        content = data['content'] if 'content' in data else ''
        if msg_type in ['80014', '60014']:
            query = data['title']
            root = ET.fromstring(data['content'])

            def search_key(xml_key: str):
                elements = root.findall('.//{}'.format(xml_key))
                value = ''
                if len(elements) > 0:
                    value = elements[0].text
                return value
            displayname = search_key(xml_key='displayname')
            if displayname == '茴香豆':
                displayname = ''
            displaycontent = search_key(xml_key='content')
            content = '{}:{}'.format(displayname, displaycontent)
            to_user = search_key(xml_key='chatusr')
            if to_user != bot_wxid:
                parse_type = 'ref_for_others'
                self.status = 'skip'
            else:
                parse_type = 'ref_for_bot'
        elif msg_type in ['80007', '60007', '90001']:
            parse_type = 'link'
            root = ET.fromstring(data['content'])

            def search_key(xml_key: str):
                elements = root.findall('.//{}'.format(xml_key))
                content = ''
                if len(elements) > 0:
                    content = elements[0].text
                return content
            self.url = search_key(xml_key='url')
            title = search_key(xml_key='title')
            self.title = title
            desc = search_key(xml_key='des')
            self.desc = desc
            self.thumb_url = search_key(xml_key='thumburl')
            query = data['pushContent']
        elif msg_type in ['80006']:
            parse_type = 'emoji'
            self.md5 = data['md5']
            self.length = data['length']
        elif msg_type in ['80002', '60002']:
            parse_type = 'image'
            getMsgData = {'wId': bot_wxid, 'content': data['content'], 'msgId': data['msgId'], 'type': 0}
            headers = {'Content-Type': 'application/json', 'Authorization': auth}
            resp = requests.post('http://{}/getMsgImg'.format(wkteam_ip_port), data=json.dumps(getMsgData), headers=headers)
            json_str = resp.content.decode('utf8')
            if resp.status_code == 200:
                jsonobj = json.loads(json_str)
                if jsonobj['code'] != '1000':
                    logger.error('download {} {}'.format(data, json_str))
                jsondata = jsonobj['data']
                if not jsondata:
                    return Exception('download image failed, skip')
                self.url = jsonobj['data']['url']
        elif msg_type in ['80001', '60001']:
            query = data['content']
            parse_type = 'text'
        elif type(msg_type) is int:
            logger.warning(wx_msg)
        else:
            return Exception('Skip msg type {}'.format(msg_type))
        query = query.encode('UTF-8', 'ignore').decode('UTF-8')
        if query.startswith('@茴香豆'):
            query = query.replace('@茴香豆', '')
        self.query = query.strip()
        if 'fromUser' not in data:
            self.status = 'skip'
            return Exception('msg no sender id, skip')
        self.sender = data['fromUser']
        self.data = data
        if 'newMsgId' in data:
            self.new_msg_id = data['newMsgId']
        self.type = parse_type
        if 'fromGroup' not in data:
            return Exception('GroupID not found in message')
        self.group_id = data['fromGroup']
        self.global_user_id = '{}|{}'.format(self.group_id, data['fromUser'])
        self.push_content = data['pushContent'] if 'pushContent' in data else ''
        self.content = content
        return None

def parse(self, wx_msg: dict, bot_wxid: str, auth: str='', wkteam_ip_port: str=''):
    msg_type = wx_msg['messageType']
    parse_type = 'unknown'
    if 'data' not in wx_msg:
        self.status = 'skip'
        return Exception('data not in wx_msg')
    data = wx_msg['data']
    if not data:
        return Exception('data is None')
    if 'self' in data:
        if data['self']:
            return Exception('self msg, return')
    if 'msgId' in data:
        self._id = data['msgId']
    query = ''
    if 'atlist' in data:
        atlist = data['atlist']
        if bot_wxid not in atlist:
            self.status = 'skip'
            return Exception('atlist not contains bot')
    content = data['content'] if 'content' in data else ''
    if msg_type in ['80014', '60014']:
        query = data['title']
        root = ET.fromstring(data['content'])

        def search_key(xml_key: str):
            elements = root.findall('.//{}'.format(xml_key))
            value = ''
            if len(elements) > 0:
                value = elements[0].text
            return value
        displayname = search_key(xml_key='displayname')
        if displayname == '茴香豆':
            displayname = ''
        displaycontent = search_key(xml_key='content')
        content = '{}:{}'.format(displayname, displaycontent)
        to_user = search_key(xml_key='chatusr')
        if to_user != bot_wxid:
            parse_type = 'ref_for_others'
            self.status = 'skip'
        else:
            parse_type = 'ref_for_bot'
    elif msg_type in ['80007', '60007', '90001']:
        parse_type = 'link'
        root = ET.fromstring(data['content'])

        def search_key(xml_key: str):
            elements = root.findall('.//{}'.format(xml_key))
            content = ''
            if len(elements) > 0:
                content = elements[0].text
            return content
        self.url = search_key(xml_key='url')
        title = search_key(xml_key='title')
        self.title = title
        desc = search_key(xml_key='des')
        self.desc = desc
        self.thumb_url = search_key(xml_key='thumburl')
        query = data['pushContent']
    elif msg_type in ['80006']:
        parse_type = 'emoji'
        self.md5 = data['md5']
        self.length = data['length']
    elif msg_type in ['80002', '60002']:
        parse_type = 'image'
        getMsgData = {'wId': bot_wxid, 'content': data['content'], 'msgId': data['msgId'], 'type': 0}
        headers = {'Content-Type': 'application/json', 'Authorization': auth}
        resp = requests.post('http://{}/getMsgImg'.format(wkteam_ip_port), data=json.dumps(getMsgData), headers=headers)
        json_str = resp.content.decode('utf8')
        if resp.status_code == 200:
            jsonobj = json.loads(json_str)
            if jsonobj['code'] != '1000':
                logger.error('download {} {}'.format(data, json_str))
            jsondata = jsonobj['data']
            if not jsondata:
                return Exception('download image failed, skip')
            self.url = jsonobj['data']['url']
    elif msg_type in ['80001', '60001']:
        query = data['content']
        parse_type = 'text'
    elif type(msg_type) is int:
        logger.warning(wx_msg)
    else:
        return Exception('Skip msg type {}'.format(msg_type))
    query = query.encode('UTF-8', 'ignore').decode('UTF-8')
    if query.startswith('@茴香豆'):
        query = query.replace('@茴香豆', '')
    self.query = query.strip()
    if 'fromUser' not in data:
        self.status = 'skip'
        return Exception('msg no sender id, skip')
    self.sender = data['fromUser']
    self.data = data
    if 'newMsgId' in data:
        self.new_msg_id = data['newMsgId']
    self.type = parse_type
    if 'fromGroup' not in data:
        return Exception('GroupID not found in message')
    self.group_id = data['fromGroup']
    self.global_user_id = '{}|{}'.format(self.group_id, data['fromUser'])
    self.push_content = data['pushContent'] if 'pushContent' in data else ''
    self.content = content
    return None

class WkteamManager:
    """
    1. wkteam Login, see https://wkteam.cn/
    2. Handle wkteam wechat message call back
    """

    def __init__(self, config_path: str):
        """init with config."""
        self.WKTEAM_IP_PORT = '121.229.29.88:9899'
        self.auth = ''
        self.wId = ''
        self.wcId = ''
        self.qrCodeUrl = ''
        self.wkteam_config = dict()
        self.users = dict()
        self.preprocessed = set()
        self.messages = []
        self.group_whitelist = dict()
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
            assert len(self.config) > 1
            wkconf = self.config['frontend']['wechat_wkteam']
            for key in wkconf.keys():
                key = key.strip()
                if re.match('\\d+', key) is None:
                    continue
                group = wkconf[key]
                self.group_whitelist['{}@chatroom'.format(key)] = group['name']
            self.wkteam_config = types.SimpleNamespace(**wkconf)
        if os.getenv('REDIS_HOST') is None:
            os.environ['REDIS_HOST'] = str(self.wkteam_config.redis_host)
        if os.getenv('REDIS_PORT') is None:
            os.environ['REDIS_PORT'] = str(self.wkteam_config.redis_port)
        if os.getenv('REDIS_PASSWORD') is None:
            os.environ['REDIS_PASSWORD'] = str(self.wkteam_config.redis_passwd)
        if not os.path.exists(self.wkteam_config.dir):
            os.makedirs(self.wkteam_config.dir)
        self.license_path = os.path.join(self.wkteam_config.dir, 'license.json')
        self.record_path = os.path.join(self.wkteam_config.dir, 'record.jsonl')
        if os.path.exists(self.license_path):
            with open(self.license_path) as f:
                jsonobj = json.load(f)
                self.auth = jsonobj['auth']
                self.wId = jsonobj['wId']
                self.wcId = jsonobj['wcId']
                self.qrCodeUrl = jsonobj['qrCodeUrl']
                logger.debug(jsonobj)
        self.sent_msg = dict()
        self.debug()

    def debug(self):
        logger.debug('auth {}'.format(self.auth))
        logger.debug('wId {}'.format(self.wId))
        logger.debug('wcId {}'.format(self.wcId))
        logger.debug('REDIS_HOST {}'.format(os.getenv('REDIS_HOST')))
        logger.debug('REDIS_PORT {}'.format(os.getenv('REDIS_PORT')))
        logger.debug(self.group_whitelist)

    def post(self, url, data, headers):
        """Wrap http post and error handling."""
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        json_str = resp.content.decode('utf8')
        logger.debug(json_str)
        if resp.status_code != 200:
            return (None, Exception('wkteam auth fail {}'.format(json_str)))
        json_obj = json.loads(json_str)
        if json_obj['code'] != '1000':
            return (json_obj, Exception(json_str))
        return (json_obj, None)

    def revert_all(self):
        for groupId in self.group_whitelist:
            self.revert(groupId=groupId)

    def revert(self, groupId: str):
        """Revert all msgs in this group."""
        if groupId in self.group_whitelist:
            groupname = self.group_whitelist[groupId]
            logger.debug('revert message in group {} {}'.format(groupname, groupId))
        else:
            logger.debug('revert message in group {} '.format(groupId))
        if groupId not in self.sent_msg:
            return
        group_sent_list = self.sent_msg[groupId]
        for sent in group_sent_list:
            logger.info(sent)
            time_diff = abs(time.time() - int(sent['createTime']))
            if time_diff <= 120:
                headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
                self.post(url='http://{}/revokeMsg'.format(self.WKTEAM_IP_PORT), data=sent, headers=headers)
        del self.sent_msg[groupId]

    def download_image(self, param: dict):
        """Download group chat image."""
        content = param['content']
        msgId = param['msgId']
        wId = param['wId']
        if len(self.auth) < 1:
            logger.error('Authentication empty')
            return
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'wId': wId, 'content': content, 'msgId': msgId, 'type': 0}

        def generate_hash_filename(data: dict):
            xstr = json.dumps(data)
            md5 = hashlib.md5()
            md5.update(xstr.encode('utf8'))
            return md5.hexdigest()[0:6] + '.jpg'

        def download(data: dict, headers: dict, dir: str):
            resp = requests.post('http://{}/getMsgImg'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
            json_str = resp.content.decode('utf8')
            if resp.status_code == 200:
                jsonobj = json.loads(json_str)
                if jsonobj['code'] != '1000':
                    logger.error('download {} {}'.format(data, json_str))
                    return
                image_url = jsonobj['data']['url']
                logger.info('image url {}'.format(image_url))
                resp = requests.get(image_url, stream=True)
                image_path = None
                if resp.status_code == 200:
                    image_dir = os.path.join(dir, 'images')
                    if not os.path.exists(image_dir):
                        os.makedirs(image_dir)
                    image_path = os.path.join(image_dir, generate_hash_filename(data=data))
                    logger.debug('local path {}'.format(image_path))
                    with open(image_path, 'wb') as image_file:
                        for chunk in resp.iter_content(1024):
                            image_file.write(chunk)
                return (image_url, image_path)
        url = ''
        path = ''
        try:
            url, path = download(data, headers, self.wkteam_config.dir)
        except Exception as e:
            logger.error(str(e))
            return (None, None)
        return (url, path)

    def login(self):
        """user login, need scan qr code on mobile phone."""
        if len(self.wkteam_config.account) < 1 or len(self.wkteam_config.password) < 1:
            return Exception('wkteam account or password not set')
        if len(self.wkteam_config.callback_ip) < 1:
            return Exception('wkteam wechat message public callback ip not set, try FRP or buy cloud service ?')
        if self.wkteam_config.proxy <= 0:
            return Exception('wkteam proxy not set')
        headers = {'Content-Type': 'application/json'}
        data = {'account': self.wkteam_config.account, 'password': self.wkteam_config.password}
        json_obj, err = self.post(url='http://{}/member/login'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        self.auth = json_obj['data']['Authorization']
        headers['Authorization'] = self.auth
        data = {'wcId': '', 'proxy': self.wkteam_config.proxy}
        json_obj, err = self.post(url='http://{}/iPadLogin'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        x = json_obj['data']
        self.wId = x['wId']
        self.qrCodeUrl = x['qrCodeUrl']
        logger.info('浏览器打开这个地址、下载二维码。打开手机，扫描登录微信\n {}\n 请确认 proxy 地区正确，首次使用、24 小时后要再次登录，以后不需要登。'.format(self.qrCodeUrl))
        json_obj, err = self.post(url='http://{}/getIPadLoginInfo'.format(self.WKTEAM_IP_PORT), data={'wId': self.wId}, headers=headers)
        x = json_obj['data']
        self.wcId = x['wcId']
        with open(self.license_path, 'w') as f:
            json_str = json.dumps({'auth': self.auth, 'wId': self.wId, 'wcId': self.wcId, 'qrCodeUrl': self.qrCodeUrl}, indent=2, ensure_ascii=False)
            f.write(json_str)

    def set_callback(self):
        httpUrl = 'http://{}:{}/callback'.format(self.wkteam_config.callback_ip, self.wkteam_config.callback_port)
        logger.debug('set callback url {}'.format(httpUrl))
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'httpUrl': httpUrl, 'type': 2}
        json_obj, err = self.post(url='http://{}/setHttpCallbackUrl'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        logger.info('login success, all license saved to {}'.format(self.license_path))
        return None

    def send_image(self, groupId: str, image_url: str):
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'wId': self.wId, 'wcId': groupId, 'content': image_url}
        json_obj, err = self.post(url='http://{}/sendImage2'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        sent = json_obj['data']
        sent['wId'] = self.wId
        if groupId not in self.sent_msg:
            self.sent_msg[groupId] = [sent]
        else:
            self.sent_msg[groupId].append(sent)
        return None

    def send_emoji(self, groupId: str, md5: str, length: int):
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'wId': self.wId, 'wcId': groupId, 'imageMd5': md5, 'imgSize': length}
        json_obj, err = self.post(url='http://{}/sendEmoji'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        sent = json_obj['data']
        sent['wId'] = self.wId
        if groupId not in self.sent_msg:
            self.sent_msg[groupId] = [sent]
        else:
            self.sent_msg[groupId].append(sent)
        return None

    def send_message(self, groupId: str, text: str):
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'wId': self.wId, 'wcId': groupId, 'content': text}
        json_obj, err = self.post(url='http://{}/sendText'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        sent = json_obj['data']
        sent['wId'] = self.wId
        if groupId not in self.sent_msg:
            self.sent_msg[groupId] = [sent]
        else:
            self.sent_msg[groupId].append(sent)
        return None

    def send_user_message(self, userId: str, text: str):
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'wId': self.wId, 'wcId': userId, 'content': text}
        json_obj, err = self.post(url='http://{}/sendText'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        sent = json_obj['data']
        sent['wId'] = self.wId
        if userId not in self.sent_msg:
            self.sent_msg[userId] = [sent]
        else:
            self.sent_msg[userId].append(sent)
        return None

    def send_url(self, groupId: str, description: str, title: str, thumb_url: str, url: str):
        headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
        data = {'wId': self.wId, 'wcId': groupId, 'description': description, 'title': title, 'thumbUrl': thumb_url, 'url': url}
        json_obj, err = self.post(url='http://{}/sendUrl'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
        if err is not None:
            return err
        sent = json_obj['data']
        sent['wId'] = self.wId
        if groupId not in self.sent_msg:
            self.sent_msg[groupId] = [sent]
        else:
            self.sent_msg[groupId].append(sent)
        return None

    def bind(self, logdir: str, port: int, forward: bool=False):
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logpath = os.path.join(logdir, 'wechat_message.jsonl')

        async def forward_msg(input_json: dict):
            msg = Message()
            print(input_json)
            err = msg.parse(wx_msg=input_json, bot_wxid=self.wId, auth=self.auth, wkteam_ip_port=self.WKTEAM_IP_PORT)
            if err is not None:
                logger.error(str(err))
                return
            if msg.new_msg_id in self.preprocessed:
                print(f'{msg.new_msg_id} repeated, skip')
                return
            self.preprocessed.add(msg.new_msg_id)
            come_from_whitelist = False
            from_group_name = ''
            for groupId, groupname in self.group_whitelist.items():
                if msg.group_id == groupId:
                    come_from_whitelist = True
                    from_group_name = groupname
            if not come_from_whitelist:
                return
            if msg.sender == self.wcId:
                return
            for groupId, _ in self.group_whitelist.items():
                if groupId == msg.group_id:
                    continue
                logger.info(str(msg.__dict__))
                if msg.type == 'text':
                    username = msg.push_content.split(':')[0].strip()
                    formatted_reply = '{}：{}'.format(username, msg.content)
                    self.send_message(groupId=groupId, text=formatted_reply)
                elif msg.type == 'image':
                    self.send_image(groupId=groupId, image_url=msg.url)
                elif msg.type == 'emoji':
                    self.send_emoji(groupId=groupId, md5=msg.md5, length=msg.length)
                elif msg.type == 'ref_for_others' or msg.type == 'ref_for_bot':
                    formatted_reply = '{}\n---\n{}'.format(msg.content, msg.query)
                    self.send_message(groupId=groupId, text=formatted_reply)
                elif msg.type == 'link':
                    thumbnail = msg.thumb_url if msg.thumb_url else 'https://deploee.oss-cn-shanghai.aliyuncs.com/icon.jpg'
                    self.send_url(groupId=groupId, description=msg.desc, title=msg.title, thumb_url=thumbnail, url=msg.url)
                await asyncio.sleep(random.uniform(0.2, 2.0))

        async def msg_callback(request):
            """Save wechat message to redis, for revert command, use high
            priority."""
            input_json = await request.json()
            with open(logpath, 'a') as f:
                json_str = json.dumps(input_json, indent=2, ensure_ascii=False)
                f.write(json_str)
                f.write('\n')
            logger.debug(input_json)
            try:
                msg_que = Queue(name='wechat')
            except Exception as e:
                msg_que = None
                print('redis unavailable')
                pass
            if input_json['messageType'] == '00000':
                return web.json_response(text='done')
            try:
                json_str = json.dumps(input_json)
                if is_revert_command(input_json):
                    self.revert_all()
                    return web.json_response(text='done')
                if msg_que:
                    msg_que.put(json_str)
                if forward and (not is_revert_command(input_json)):
                    await forward_msg(input_json)
            except Exception as e:
                logger.error(str(e))
            return web.json_response(text='done')
        app = web.Application()
        app.add_routes([web.post('/callback', msg_callback)])
        web.run_app(app, host='0.0.0.0', port=port)

    def serve(self, forward: bool=False):
        p = Process(target=self.bind, args=(self.wkteam_config.dir, self.wkteam_config.callback_port, forward))
        p.start()
        self.set_callback()
        p.join()

    def fetch_groupchats(self, user: User, max_length: int=12):
        """Before obtaining user messages, there are a maximum of `max_length`
        historical conversations in the group.

        Fetch them for coreference resolution.
        """
        user_msg_id = user.last_msg_id
        conversations = []
        for index in range(len(self.messages) - 1, -1, -1):
            msg = self.messages[index]
            if len(conversations) >= max_length:
                break
            if msg.type == 'unknown':
                continue
            if msg._id < user_msg_id and msg.group_id == user.group_id:
                conversations.append(msg)
        return conversations

    async def loop(self, assistant):
        """Fetch all messages from redis, split it by groupId; concat by
        timestamp."""
        from huixiangdou.services import ErrorCode, kimi_ocr
        que = Queue(name='wechat')
        while True:
            for wx_msg_str in que.get_all():
                wx_msg = json.loads(wx_msg_str)
                logger.debug(wx_msg)
                msg = Message()
                err = msg.parse(wx_msg=wx_msg, bot_wxid=self.wcId, auth=self.auth, wkteam_ip_port=self.WKTEAM_IP_PORT)
                if err is not None:
                    logger.debug(str(err))
                    continue
                if msg.type == 'image':
                    _, local_image_path = self.download_image(param=msg.data)
                    llm_server_config = self.config['llm']['server']
                    if local_image_path is not None and llm_server_config['remote_type'] == 'kimi':
                        token = llm_server_config['remote_api_key']
                        msg.query = kimi_ocr(local_image_path, token)
                        logger.debug('kimi ocr {} {}'.format(local_image_path, msg.query))
                if len(msg.query) < 1:
                    continue
                self.messages.append(msg)
                if msg.type == 'ref_for_others':
                    continue
                if msg.global_user_id not in self.users:
                    self.users[msg.global_user_id] = User()
                user = self.users[msg.global_user_id]
                user.feed(msg)
            for user in self.users.values():
                if len(user.history) < 1:
                    continue
                now = time.time()
                if now - user.last_msg_time >= 12 and user.last_process_time < user.last_msg_time:
                    if user.last_msg_type in ['link', 'image']:
                        continue
                    logger.debug('before concat {}'.format(user))
                    user.concat()
                    logger.debug('after concat {}'.format(user))
                    assert len(user.history) > 0
                    item = user.history[-1]
                    if item.reply is not None and len(item.reply) > 0:
                        logger.error('item reply not None, {}'.format(item))
                    query = item.query
                    code = ErrorCode.QUESTION_TOO_SHORT
                    resp = ''
                    refs = []
                    groupname = ''
                    groupchats = []
                    if user.group_id in self.group_whitelist:
                        groupname = self.group_whitelist[user.group_id]
                    if len(query) >= 8:
                        groupchats = self.fetch_groupchats(user=user)
                        tuple_history = convert_history_to_tuple(user.history[0:-1])
                        async for sess in assistant.generate(query=query, history=tuple_history, groupname=groupname, groupchats=groupchats):
                            code, resp, refs = (sess.code, sess.response, sess.references)
                    user.last_process_time = time.time()
                    if code in [ErrorCode.NOT_A_QUESTION, ErrorCode.SECURITY, ErrorCode.NO_SEARCH_RESULT, ErrorCode.NO_TOPIC]:
                        del user.history[-1]
                    else:
                        user.update_history(query=query, reply=resp, refs=refs)
                    if code == ErrorCode.SUCCESS:
                        formatted_reply = ''
                        if len(query) > 30:
                            formatted_reply = '{}..\n---\n{}'.format(query[0:30], resp)
                        else:
                            formatted_reply = '{}\n---\n{}'.format(query, resp)
                        if user.group_id in self.group_whitelist:
                            logger.warning('send {} to {}'.format(formatted_reply, user.group_id))
                            self.send_message(groupId=user.group_id, text=formatted_reply)
                        else:
                            logger.warning('prepare respond {} to {}'.format(formatted_reply, user.group_id))

def post(self, url, data, headers):
    """Wrap http post and error handling."""
    resp = requests.post(url, data=json.dumps(data), headers=headers)
    json_str = resp.content.decode('utf8')
    logger.debug(json_str)
    if resp.status_code != 200:
        return (None, Exception('wkteam auth fail {}'.format(json_str)))
    json_obj = json.loads(json_str)
    if json_obj['code'] != '1000':
        return (json_obj, Exception(json_str))
    return (json_obj, None)

def revert(self, groupId: str):
    """Revert all msgs in this group."""
    if groupId in self.group_whitelist:
        groupname = self.group_whitelist[groupId]
        logger.debug('revert message in group {} {}'.format(groupname, groupId))
    else:
        logger.debug('revert message in group {} '.format(groupId))
    if groupId not in self.sent_msg:
        return
    group_sent_list = self.sent_msg[groupId]
    for sent in group_sent_list:
        logger.info(sent)
        time_diff = abs(time.time() - int(sent['createTime']))
        if time_diff <= 120:
            headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
            self.post(url='http://{}/revokeMsg'.format(self.WKTEAM_IP_PORT), data=sent, headers=headers)
    del self.sent_msg[groupId]

def download(data: dict, headers: dict, dir: str):
    resp = requests.post('http://{}/getMsgImg'.format(self.WKTEAM_IP_PORT), data=json.dumps(data), headers=headers)
    json_str = resp.content.decode('utf8')
    if resp.status_code == 200:
        jsonobj = json.loads(json_str)
        if jsonobj['code'] != '1000':
            logger.error('download {} {}'.format(data, json_str))
            return
        image_url = jsonobj['data']['url']
        logger.info('image url {}'.format(image_url))
        resp = requests.get(image_url, stream=True)
        image_path = None
        if resp.status_code == 200:
            image_dir = os.path.join(dir, 'images')
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            image_path = os.path.join(image_dir, generate_hash_filename(data=data))
            logger.debug('local path {}'.format(image_path))
            with open(image_path, 'wb') as image_file:
                for chunk in resp.iter_content(1024):
                    image_file.write(chunk)
        return (image_url, image_path)

def login(self):
    """user login, need scan qr code on mobile phone."""
    if len(self.wkteam_config.account) < 1 or len(self.wkteam_config.password) < 1:
        return Exception('wkteam account or password not set')
    if len(self.wkteam_config.callback_ip) < 1:
        return Exception('wkteam wechat message public callback ip not set, try FRP or buy cloud service ?')
    if self.wkteam_config.proxy <= 0:
        return Exception('wkteam proxy not set')
    headers = {'Content-Type': 'application/json'}
    data = {'account': self.wkteam_config.account, 'password': self.wkteam_config.password}
    json_obj, err = self.post(url='http://{}/member/login'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    self.auth = json_obj['data']['Authorization']
    headers['Authorization'] = self.auth
    data = {'wcId': '', 'proxy': self.wkteam_config.proxy}
    json_obj, err = self.post(url='http://{}/iPadLogin'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    x = json_obj['data']
    self.wId = x['wId']
    self.qrCodeUrl = x['qrCodeUrl']
    logger.info('浏览器打开这个地址、下载二维码。打开手机，扫描登录微信\n {}\n 请确认 proxy 地区正确，首次使用、24 小时后要再次登录，以后不需要登。'.format(self.qrCodeUrl))
    json_obj, err = self.post(url='http://{}/getIPadLoginInfo'.format(self.WKTEAM_IP_PORT), data={'wId': self.wId}, headers=headers)
    x = json_obj['data']
    self.wcId = x['wcId']
    with open(self.license_path, 'w') as f:
        json_str = json.dumps({'auth': self.auth, 'wId': self.wId, 'wcId': self.wcId, 'qrCodeUrl': self.qrCodeUrl}, indent=2, ensure_ascii=False)
        f.write(json_str)

def set_callback(self):
    httpUrl = 'http://{}:{}/callback'.format(self.wkteam_config.callback_ip, self.wkteam_config.callback_port)
    logger.debug('set callback url {}'.format(httpUrl))
    headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
    data = {'httpUrl': httpUrl, 'type': 2}
    json_obj, err = self.post(url='http://{}/setHttpCallbackUrl'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    logger.info('login success, all license saved to {}'.format(self.license_path))
    return None

def send_image(self, groupId: str, image_url: str):
    headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
    data = {'wId': self.wId, 'wcId': groupId, 'content': image_url}
    json_obj, err = self.post(url='http://{}/sendImage2'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    sent = json_obj['data']
    sent['wId'] = self.wId
    if groupId not in self.sent_msg:
        self.sent_msg[groupId] = [sent]
    else:
        self.sent_msg[groupId].append(sent)
    return None

def send_emoji(self, groupId: str, md5: str, length: int):
    headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
    data = {'wId': self.wId, 'wcId': groupId, 'imageMd5': md5, 'imgSize': length}
    json_obj, err = self.post(url='http://{}/sendEmoji'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    sent = json_obj['data']
    sent['wId'] = self.wId
    if groupId not in self.sent_msg:
        self.sent_msg[groupId] = [sent]
    else:
        self.sent_msg[groupId].append(sent)
    return None

def send_message(self, groupId: str, text: str):
    headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
    data = {'wId': self.wId, 'wcId': groupId, 'content': text}
    json_obj, err = self.post(url='http://{}/sendText'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    sent = json_obj['data']
    sent['wId'] = self.wId
    if groupId not in self.sent_msg:
        self.sent_msg[groupId] = [sent]
    else:
        self.sent_msg[groupId].append(sent)
    return None

def send_user_message(self, userId: str, text: str):
    headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
    data = {'wId': self.wId, 'wcId': userId, 'content': text}
    json_obj, err = self.post(url='http://{}/sendText'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    sent = json_obj['data']
    sent['wId'] = self.wId
    if userId not in self.sent_msg:
        self.sent_msg[userId] = [sent]
    else:
        self.sent_msg[userId].append(sent)
    return None

def send_url(self, groupId: str, description: str, title: str, thumb_url: str, url: str):
    headers = {'Content-Type': 'application/json', 'Authorization': self.auth}
    data = {'wId': self.wId, 'wcId': groupId, 'description': description, 'title': title, 'thumbUrl': thumb_url, 'url': url}
    json_obj, err = self.post(url='http://{}/sendUrl'.format(self.WKTEAM_IP_PORT), data=data, headers=headers)
    if err is not None:
        return err
    sent = json_obj['data']
    sent['wId'] = self.wId
    if groupId not in self.sent_msg:
        self.sent_msg[groupId] = [sent]
    else:
        self.sent_msg[groupId].append(sent)
    return None

class Retriever:
    """Tokenize and extract features from the project's chunks, for use in the
    reject pipeline and response pipeline."""

    def __init__(self, config_path: str, embedder: Any, reranker: Any, work_dir: str, reject_throttle: float) -> None:
        """Init with model device type and config."""
        self.config_path = config_path
        self.reject_throttle = reject_throttle
        self.embedder = embedder
        self.reranker = reranker
        self.faiss = None
        self.work_dir = work_dir
        if not os.path.exists(work_dir):
            logger.warning('!!!warning, workdir not exist.!!!')
            return
        self.kg = KnowledgeGraph(config_path=config_path)
        dense_dir = os.path.join(work_dir, 'db_dense')
        if not os.path.exists(dense_dir):
            logger.warning('Dense retriever is None, skip load faiss')
            self.faiss = None
        else:
            self.faiss = Faiss.load_local(dense_dir)
        sparse_dir = os.path.join(work_dir, 'db_sparse')
        if not os.path.exists(sparse_dir):
            logger.warning('Sparse retriever is None, skip load bm25')
            self.bm25 = None
        else:
            self.bm25 = BM25Okapi()
            self.bm25.load(sparse_dir)

    def update_throttle(self, config_path: str='config.ini', good_questions=[], bad_questions=[]):
        """Update reject throttle based on positive and negative examples."""
        if len(good_questions) == 0 or len(bad_questions) == 0:
            raise Exception('good and bad question examples cat not be empty.')
        questions = good_questions + bad_questions
        predictions = []
        self.reject_throttle = -1
        for question in questions:
            _, score = self.is_relative(query=question, enable_kg=True, enable_threshold=False)
            predictions.append(max(0, score))
        labels = [1 for _ in range(len(good_questions))] + [0 for _ in range(len(bad_questions))]
        precision, recall, thresholds = precision_recall_curve(labels, predictions)
        sum_precision_recall = precision[:-1] + recall[:-1]
        index_max = np.argmax(sum_precision_recall)
        optimal_threshold = max(thresholds[index_max], 0.0)
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)
        config['feature_store']['reject_throttle'] = float(optimal_threshold)
        with open(config_path, 'w', encoding='utf8') as f:
            pytoml.dump(config, f)
        logger.info(f'The optimal threshold is: {optimal_threshold}, saved it to {config_path}')

    def inverted_index_retrieve(self, query: Union[Query, str], topk=100) -> List[Chunk]:
        """Retrieve chunks by named entity."""
        reverted_index_dir = os.path.join(self.work_dir, 'db_reverted_index')
        if not os.path.exists(reverted_index_dir):
            return []
        reverted_indexer = NamedEntity2Chunk(reverted_index_dir)
        if type(query) is str:
            query = Query(text=query)
        entity_ids = reverted_indexer.parse(query.text)
        chunk_id_score_list = reverted_indexer.get_chunk_ids(entity_ids=entity_ids)
        chunk_id_score_list = chunk_id_score_list[0:topk]
        del reverted_indexer
        chunks = []
        for chunk_id, ref_count in chunk_id_score_list:
            chunks.append(self.faiss.chunks[chunk_id])
        return chunks

    def text2vec_retrieve(self, query: Union[Query, str]) -> List[Chunk]:
        """Retrieve chunks by text2vec model or knowledge graph. 
        
        Args:
            query (Query): The multimodal question asked by the user.
        
        Returns:
            List[Chunk]: ref chunks.
        """
        if type(query) is str:
            query = Query(text=query)
        graph_delta = 0.0
        if self.kg.is_available():
            try:
                docs = self.kg.retrieve(query=query.text)
                graph_delta = 0.2 * min(100, len(docs)) / 100
            except Exception as e:
                logger.warning(str(e))
                logger.info('KG folder exists, but search failed, skip.')
        threshold = self.reject_throttle - graph_delta
        t1 = time.time()
        pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=threshold)
        t2 = time.time()
        logger.info('Timecost for text2vec_retrieve {} seconds'.format(float(t2 - t1)))
        chunks = [pair[0] for pair in pairs]
        return chunks

    def rerank_fuse(self, query: Union[Query, str], chunks: List[Chunk], context_max_length: int) -> Tuple[str, str, List[str], List[str]]:
        """Rerank chunks and extract content
        
        Args:
            chunks (List[Chunk]): filtered chunks.
        
        Returns:
            str: Joined chunks, or empty string
            str: Matched context from origin file content
            List[str]: References
        """
        if type(query) is str:
            query = Query(text=query)
        rerank_chunks = self.reranker.rerank(query=query.text, chunks=chunks)
        file_opr = FileOperation()
        splits = []
        context = ''
        references = []
        ref_texts = []
        for chunk in rerank_chunks:
            content = chunk.content_or_path
            splits.append(content)
            source = chunk.metadata['source']
            if '://' in source:
                file_text = content
            elif chunk.modal == 'text':
                file_text, error = file_opr.read(chunk.metadata['read'])
                if error is not None:
                    continue
            elif chunk.modal == 'qa':
                file_text = chunk.metadata['qa']
            logger.info('target {} content length {}'.format(source, len(file_text)))
            if len(file_text) + len(context) > context_max_length:
                if source in references:
                    continue
                references.append(source)
                add_len = context_max_length - len(context)
                if add_len <= 0:
                    break
                content_index = file_text.find(content)
                if content_index == -1:
                    delta = '{}\n{}'.format(content, file_text[0:add_len - len(content) - 1])
                    context += delta
                    ref_texts.append(delta)
                else:
                    start_index = max(0, content_index - (add_len - len(content)))
                    delta = file_text[start_index:start_index + add_len]
                    context += delta
                    ref_texts.append(delta)
                break
            if source not in references:
                context += file_text
                context += '\n'
                references.append(source)
                ref_texts.append(file_text)
        context = context[0:context_max_length]
        logger.debug('query:{} files:{}'.format(query, references))
        return ('\n'.join(splits), context, [os.path.basename(r) for r in references], ref_texts)

    def query(self, query: Union[Query, str], context_max_length: int=40000, tracker: QueryTracker=None):
        """Processes a query and returns the best match from the vector store
        database. If the question is rejected, returns None.

        Args:
            query (Query): The multimodal question asked by the user.
            context_max_length (int): Max contenxt length for LLM.
            tracker (QueryTracker): Log tracker.

        Returns:
            str: Matched chunks, or empty string
            str: Matched context from origin file content
            List[str]: References 
        """
        if type(query) is str:
            query = Query(text=query)
        if query.text is None or len(query.text) < 1 or self.faiss is None:
            return (None, None, [])
        if len(query.text) > 512:
            logger.warning('input too long, truncate to 512')
            query.text = query.text[0:512]
        high_score_chunks = self.text2vec_retrieve(query=query)
        if tracker is not None:
            tracker.log('retrieve', [c.metadata['source'] for c in high_score_chunks])
        return self.rerank_fuse(query=query, chunks=high_score_chunks, context_max_length=context_max_length)

    def is_relative(self, query, k=30, enable_kg=True, enable_threshold=True) -> Tuple[bool, float]:
        """Is input query relative with knowledge base. Return true or false, and the maxisum score"""
        if type(query) is str:
            query = Query(text=query)
        if query.text is None or len(query.text) < 1 or self.faiss is None:
            raise ValueError('input query {}, faiss {}'.format(query, self.faiss))
        graph_delta = 0.0
        if not enable_kg and self.kg.is_available():
            try:
                docs = self.kg.retrieve(query=query.text)
                graph_delta = 0.2 * min(100, len(docs)) / 100
            except Exception as e:
                logger.warning(str(e))
                logger.info('KG folder exists, but search failed, skip.')
        threshold = self.reject_throttle - graph_delta
        if enable_threshold:
            pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=threshold)
        else:
            pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=-1)
        if len(pairs) > 0:
            return (True, pairs[0][1])
        return (False, -1)

def text2vec_retrieve(self, query: Union[Query, str]) -> List[Chunk]:
    """Retrieve chunks by text2vec model or knowledge graph. 
        
        Args:
            query (Query): The multimodal question asked by the user.
        
        Returns:
            List[Chunk]: ref chunks.
        """
    if type(query) is str:
        query = Query(text=query)
    graph_delta = 0.0
    if self.kg.is_available():
        try:
            docs = self.kg.retrieve(query=query.text)
            graph_delta = 0.2 * min(100, len(docs)) / 100
        except Exception as e:
            logger.warning(str(e))
            logger.info('KG folder exists, but search failed, skip.')
    threshold = self.reject_throttle - graph_delta
    t1 = time.time()
    pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=threshold)
    t2 = time.time()
    logger.info('Timecost for text2vec_retrieve {} seconds'.format(float(t2 - t1)))
    chunks = [pair[0] for pair in pairs]
    return chunks

def rerank_fuse(self, query: Union[Query, str], chunks: List[Chunk], context_max_length: int) -> Tuple[str, str, List[str], List[str]]:
    """Rerank chunks and extract content
        
        Args:
            chunks (List[Chunk]): filtered chunks.
        
        Returns:
            str: Joined chunks, or empty string
            str: Matched context from origin file content
            List[str]: References
        """
    if type(query) is str:
        query = Query(text=query)
    rerank_chunks = self.reranker.rerank(query=query.text, chunks=chunks)
    file_opr = FileOperation()
    splits = []
    context = ''
    references = []
    ref_texts = []
    for chunk in rerank_chunks:
        content = chunk.content_or_path
        splits.append(content)
        source = chunk.metadata['source']
        if '://' in source:
            file_text = content
        elif chunk.modal == 'text':
            file_text, error = file_opr.read(chunk.metadata['read'])
            if error is not None:
                continue
        elif chunk.modal == 'qa':
            file_text = chunk.metadata['qa']
        logger.info('target {} content length {}'.format(source, len(file_text)))
        if len(file_text) + len(context) > context_max_length:
            if source in references:
                continue
            references.append(source)
            add_len = context_max_length - len(context)
            if add_len <= 0:
                break
            content_index = file_text.find(content)
            if content_index == -1:
                delta = '{}\n{}'.format(content, file_text[0:add_len - len(content) - 1])
                context += delta
                ref_texts.append(delta)
            else:
                start_index = max(0, content_index - (add_len - len(content)))
                delta = file_text[start_index:start_index + add_len]
                context += delta
                ref_texts.append(delta)
            break
        if source not in references:
            context += file_text
            context += '\n'
            references.append(source)
            ref_texts.append(file_text)
    context = context[0:context_max_length]
    logger.debug('query:{} files:{}'.format(query, references))
    return ('\n'.join(splits), context, [os.path.basename(r) for r in references], ref_texts)

def query(self, query: Union[Query, str], context_max_length: int=40000, tracker: QueryTracker=None):
    """Processes a query and returns the best match from the vector store
        database. If the question is rejected, returns None.

        Args:
            query (Query): The multimodal question asked by the user.
            context_max_length (int): Max contenxt length for LLM.
            tracker (QueryTracker): Log tracker.

        Returns:
            str: Matched chunks, or empty string
            str: Matched context from origin file content
            List[str]: References 
        """
    if type(query) is str:
        query = Query(text=query)
    if query.text is None or len(query.text) < 1 or self.faiss is None:
        return (None, None, [])
    if len(query.text) > 512:
        logger.warning('input too long, truncate to 512')
        query.text = query.text[0:512]
    high_score_chunks = self.text2vec_retrieve(query=query)
    if tracker is not None:
        tracker.log('retrieve', [c.metadata['source'] for c in high_score_chunks])
    return self.rerank_fuse(query=query, chunks=high_score_chunks, context_max_length=context_max_length)

def is_relative(self, query, k=30, enable_kg=True, enable_threshold=True) -> Tuple[bool, float]:
    """Is input query relative with knowledge base. Return true or false, and the maxisum score"""
    if type(query) is str:
        query = Query(text=query)
    if query.text is None or len(query.text) < 1 or self.faiss is None:
        raise ValueError('input query {}, faiss {}'.format(query, self.faiss))
    graph_delta = 0.0
    if not enable_kg and self.kg.is_available():
        try:
            docs = self.kg.retrieve(query=query.text)
            graph_delta = 0.2 * min(100, len(docs)) / 100
        except Exception as e:
            logger.warning(str(e))
            logger.info('KG folder exists, but search failed, skip.')
    threshold = self.reject_throttle - graph_delta
    if enable_threshold:
        pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=threshold)
    else:
        pairs = self.faiss.similarity_search_with_query(self.embedder, query=query, threshold=-1)
    if len(pairs) > 0:
        return (True, pairs[0][1])
    return (False, -1)

@DeprecationWarning
class InferenceWrapper:
    """A class to wrapper kinds of inference framework."""

    def __init__(self, model_path: str):
        """Init model handler."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers import TextIteratorStreamer
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        model_path_lower = model_path.lower()
        if 'qwen2' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype='auto', device_map='auto', trust_remote_code=True).eval()
        elif 'qwen1.5' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map='auto', trust_remote_code=True).eval()
        elif 'internlm2_5' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True).cuda().eval()
        elif 'internlm2' in model_path_lower:
            self.model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True, device_map='auto', torch_dtype='auto').eval()
        else:
            raise ValueError('Unknown model path {}'.format(model_path))

    async def chat_stream(self, prompt: str, history=[]):
        """Generate a stream response from local LLM. Wrap transformer API to async generator

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        output_text = ''
        if type(self.model).__name__ == 'Qwen2ForCausalLM':
            messages = build_messages(prompt=prompt, history=history, system='You are a helpful assistant')
            text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            model_inputs = self.tokenizer([text], return_tensors='pt').to('cuda')
            generation_kwargs = dict(model_inputs, streamer=self.streamer, max_new_tokens=512)
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            for new_text in self.streamer:
                yield new_text
            thread.join()
        elif type(self.model).__name__ == 'InternLM2ForCausalLM':
            if '请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。' in prompt:
                prompt = '你是一个语言专家，擅长分析语句并打分。\n' + prompt
            length = 0
            for response, _ in self.model.stream_chat(self.tokenizer, prompt, history, top_k=1, do_sample=False):
                part = response[length:]
                length = len(response)
                yield part
        else:
            raise ValueError('Unknown model type {}'.format(type(self.model).__name__))

    def chat(self, prompt: str, history=[]):
        """Generate a sync response from local LLM. Sync chat.

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        loop = asyncio.get_event_loop()

        async def coroutine_wrapper():
            messages = []
            async for part in self.chat_stream(prompt=prompt, history=history):
                messages.append(part)
            return ''.join(messages)
        content = loop.run_until_complete(coroutine_wrapper())
        return content

def __init__(self, model_path: str):
    """Init model handler."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers import TextIteratorStreamer
    self.model_path = model_path
    self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    self.streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
    model_path_lower = model_path.lower()
    if 'qwen2' in model_path_lower:
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype='auto', device_map='auto', trust_remote_code=True).eval()
    elif 'qwen1.5' in model_path_lower:
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map='auto', trust_remote_code=True).eval()
    elif 'internlm2_5' in model_path_lower:
        self.model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True).cuda().eval()
    elif 'internlm2' in model_path_lower:
        self.model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True, device_map='auto', torch_dtype='auto').eval()
    else:
        raise ValueError('Unknown model path {}'.format(model_path))

@DeprecationWarning
class HybridLLMServer:
    """A class to handle server-side interactions with a hybrid language
    learning model (LLM) service.

    This class is responsible for initializing the local and remote LLMs,
    generating responses from these models as per the provided configuration,
    and handling retries in case of failures.
    """

    def __init__(self, llm_config: dict, device: str='cuda', retry=2) -> None:
        """Initialize the HybridLLMServer with the given configuration, device,
        and number of retries."""
        self.device = device
        self.retry = retry
        self.llm_config = llm_config
        self.server_config = llm_config['server']
        self.enable_remote = llm_config['enable_remote']
        self.enable_local = llm_config['enable_local']
        self.local_max_length = self.server_config['local_llm_max_text_length']
        self.remote_max_length = self.server_config['remote_llm_max_text_length']
        self.remote_type = self.server_config['remote_type']
        model_path = self.server_config['local_llm_path']
        _rpm = 1000
        _tpm = 20000
        if 'rpm' in self.server_config:
            _rpm = self.server_config['rpm']
        if 'tpm' in self.server_config:
            _tpm = self.server_config['tpm']
        self.rpm = RPM(_rpm)
        self.tpm = TPM(_tpm)
        if self.enable_local:
            self.inference = InferenceWrapper(model_path)
        else:
            self.inference = None
            logger.warning('local LLM disabled.')
        self.backend2model = {'kimi': 'auto', 'step': 'auto', 'xi-api': 'gpt-4-0613', 'deepseek': 'deepseek-chat', 'zhipuai': 'glm-4', 'puyu': 'internlm2-latest', 'siliconcloud': 'Qwen/Qwen2.5-14B-Instruct'}

    async def call_kimi(self, prompt: str, history: List[Tuple], remote_api_key: str, model: str):
        """Generate a response from Kimi (a remote LLM).

        Args:
            prompt (str): The prompt to send to Kimi.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from Kimi.
        """
        client = OpenAI(api_key=remote_api_key, base_url='https://api.moonshot.cn/v1')
        SYSTEM = '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力，政治宗教等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'
        if '请仔细阅读以上内容，判断句子是否是个有主题的疑问句' in prompt:
            SYSTEM = '你是一个语文专家，擅长对句子的结构进行分析'
        messages = build_messages(prompt=prompt, history=history, system=SYSTEM)
        logger.debug('remote api sending: {}'.format(messages))
        if model == 'auto':
            prompt_len = len(str(messages))
            if prompt_len <= int(8192 * 1.5) - 1024:
                model = 'moonshot-v1-8k'
            elif prompt_len <= int(32768 * 1.5) - 1024:
                model = 'moonshot-v1-32k'
            else:
                prompt = prompt[0:int(128000 * 1.5) - 1024]
                model = 'moonshot-v1-128k'
        logger.info('choose kimi model {}'.format(model))
        stream = client.chat.completions.create(model=model, messages=messages, temperature=0.0, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def call_step(self, prompt: str, history: List, remote_api_key: str, model: str):
        """Generate a response from step, see
        https://platform.stepfun.com/docs/overview/quickstart.

        Args:
            prompt (str): The prompt to send to LLM.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from LLM.
        """
        client = OpenAI(api_key=self.server_config['remote_api_key'], base_url='https://api.stepfun.com/v1')
        SYSTEM = '你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。在保证用户数据安全的前提下，你能对用户的问题和请求，作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容'
        messages = build_messages(prompt=prompt, history=history, system=SYSTEM)
        logger.debug('remote api sending: {}'.format(messages))
        if model == 'auto':
            prompt_len = len(prompt)
            if prompt_len <= int(8192 * 1.5) - 1024:
                model = 'step-1-8k'
            elif prompt_len <= int(32768 * 1.5) - 1024:
                model = 'step-1-32k'
            elif prompt_len <= int(128000 * 1.5) - 1024:
                model = 'step-1-128k'
            else:
                prompt = prompt[0:int(256000 * 1.5) - 1024]
                model = 'step-1-256k'
        logger.info('choose step model {}'.format(model))
        stream = client.chat.completions.create(model=model, messages=messages, temperature=0.0, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def call_openai(self, prompt: str, history: List, remote_api_key: str, model: str, base_url: str=None, system: str=None):
        """Generate a response from openai API.

        Args:
            prompt (str): The prompt to send to openai API.
            history (list): List of previous interactions.

        Returns:
            str: Generated response from RPC.
        """
        if base_url is not None:
            client = OpenAI(api_key=remote_api_key, base_url=base_url)
        else:
            client = OpenAI(api_key=remote_api_key)
        messages = build_messages(prompt=prompt, history=history, system=system)
        logger.debug('remote api sending: {}'.format(messages))
        stream = client.chat.completions.create(model=model, messages=messages, stream=True)
        for chunk in stream:
            if chunk.choices is None:
                raise Exception(str(chunk))
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def chat_stream(self, prompt, history=[], backend='local'):
        """Generate a response from the appropriate LLM based on the
        configuration. If failed, use exponential backoff. Async generator.

        Args:
            prompt (str): The prompt to send to the LLM.
            history (list, optional): List of previous interactions. Defaults to [].  # noqa E501
            remote (bool, optional): Flag to determine whether to use a remote server. Defaults to False.  # noqa E501
            backend (str): LLM type to call. Support 'local', 'remote' and specified LLM name ('kimi', 'deepseek' and so on)

        Returns:
            str: Generated response from the LLM. If LLM not support stream reply, just reply once.
        """
        if backend == 'local' and self.inference is None:
            logger.error("!!! fatal error.  !!! \n Detect `enable_local=0` in `config.ini` while backend='local', please immediately stop the service and check it. \n For this request, autofix the backend to '{}' and proceed.".format(self.server_config['remote_type']))
            backend = self.server_config['remote_type']
        if backend == 'remote':
            backend = self.server_config['remote_type']
        if backend == 'local':
            prompt = prompt[0:self.local_max_length]
            "# Caution: For the results of this software to be reliable and verifiable,  # noqa E501\n            it's essential to ensure reproducibility. Thus `GenerationMode.GREEDY_SEARCH`  # noqa E501\n            must enabled."
            async for value in self.inference.chat_stream(prompt, history):
                yield value
        else:
            output_text = ''
            prompt = prompt[0:self.remote_max_length]
            map_fn = {'kimi': self.call_kimi, 'step': self.call_step, 'puyu': self.call_openai, 'deepseek': self.call_openai, 'zhipuai': self.call_openai, 'xi-api': self.call_openai, 'gpt': self.call_openai, 'siliconcloud': self.call_openai}
            map_base_url = {'xi-api': 'https://api.xi-ai.cn/v1', 'deepseek': 'https://api.deepseek.com/v1', 'zhipuai': 'https://open.bigmodel.cn/api/paas/v4/', 'puyu': 'https://puyu.openxlab.org.cn/puyu/api/v1/', 'siliconcloud': 'https://api.siliconflow.cn/v1'}
            if backend not in map_fn:
                raise ValueError('unknown backend {}'.format(backend))
            target_fn = map_fn[backend]
            default_model = self.backend2model[backend]
            model = self.server_config['remote_llm_model']
            if model is None or len(model) < 1:
                model = default_model
            args = {'prompt': prompt, 'history': history, 'model': model}
            if backend in map_base_url:
                args['base_url'] = map_base_url[backend]
            if backend in ['xi-api', 'deepseek']:
                args['system'] = 'You are a helpful assistant.'
            remote_api_key = self.server_config['remote_api_key']
            if len(remote_api_key) < 1:
                remote_api_key = os.getenv('LLM_API_TOKEN')
            args['remote_api_key'] = remote_api_key
            life = 0
            while life < self.retry:
                try:
                    self.rpm.wait()
                    self.tpm.wait(token_count=len(prompt))
                    async for value in target_fn(**args):
                        yield value
                    break
                except Exception as e:
                    error = str(e)
                    logger.error(error)
                    if 'Error code: 401' in error or 'invalid api_key' in error or 'Authentication Fails' in error:
                        raise e
                    life += 1
                    randval = random.randint(1, int(pow(2, life)))
                    time.sleep(randval)
            self.tpm.wait(token_count=len(output_text))
            yield output_text

    def chat(self, prompt: str, history=[], backend: str='local'):
        """Generate a sync response from local LLM.

        Args:
            prompt (str): The prompt for inference.
            history (list): List of previous interactions.

        Returns:
            str: Generated response.
        """
        time_tokenizer = time.time()

        async def coroutine_wrapper():
            messages = []
            async for part in self.chat_stream(prompt=prompt, history=history, backend=backend):
                messages.append(part)
                print(part, end='')
            return ''.join(messages)
        loop = asyncio.get_event_loop()
        try:
            output_text = loop.run_until_complete(coroutine_wrapper())
        except Exception as e:
            return ('', e)
        time_finish = time.time()
        logger.debug('Q:{} A:{} \t\t backend {} timecost {} '.format(prompt[-100:-1], output_text, backend, time_finish - time_tokenizer))
        return (output_text, None)

def __init__(self, llm_config: dict, device: str='cuda', retry=2) -> None:
    """Initialize the HybridLLMServer with the given configuration, device,
        and number of retries."""
    self.device = device
    self.retry = retry
    self.llm_config = llm_config
    self.server_config = llm_config['server']
    self.enable_remote = llm_config['enable_remote']
    self.enable_local = llm_config['enable_local']
    self.local_max_length = self.server_config['local_llm_max_text_length']
    self.remote_max_length = self.server_config['remote_llm_max_text_length']
    self.remote_type = self.server_config['remote_type']
    model_path = self.server_config['local_llm_path']
    _rpm = 1000
    _tpm = 20000
    if 'rpm' in self.server_config:
        _rpm = self.server_config['rpm']
    if 'tpm' in self.server_config:
        _tpm = self.server_config['tpm']
    self.rpm = RPM(_rpm)
    self.tpm = TPM(_tpm)
    if self.enable_local:
        self.inference = InferenceWrapper(model_path)
    else:
        self.inference = None
        logger.warning('local LLM disabled.')
    self.backend2model = {'kimi': 'auto', 'step': 'auto', 'xi-api': 'gpt-4-0613', 'deepseek': 'deepseek-chat', 'zhipuai': 'glm-4', 'puyu': 'internlm2-latest', 'siliconcloud': 'Qwen/Qwen2.5-14B-Instruct'}

def histogram(values: list):
    """Print histogram log string for values."""
    values.sort()
    _len = len(values)
    if _len <= 1:
        return ''
    median = values[round((_len - 1) / 2)]
    _sum = 0
    min_val = min(values)
    max_val = max(values)
    range_width = max(1, round(0.1 * (max_val - min_val)))
    ranges = [(i * range_width, (i + 1) * range_width) for i in range(max_val // range_width + 1)]
    total_count = len(values)
    range_counts = [0] * len(ranges)
    for value in values:
        _sum += value
        for i, (start, end) in enumerate(ranges):
            if start <= value < end:
                range_counts[i] += 1
                break
    range_percentages = [count / total_count * 100 for count in range_counts]
    log_str = 'length count {}, avg {}, median {}\n'.format(len(values), round(_sum / len(values), 2), median)
    for i, (start, end) in enumerate(ranges):
        log_str += f'{start}-{end}  {range_percentages[i]:.2f}%'
        log_str += '\n'
    return log_str

class FeatureStore:
    """Tokenize and extract features from the project's documents, for use in
    the reject pipeline and response pipeline."""

    def __init__(self, embedder: Embedder, config_path: str='config.ini', language: str='zh', chunk_size=900, analyze_reject=False, rejecter_naive_splitter=False, override=False) -> None:
        """Init with model device type and config."""
        self.config_path = config_path
        self.reject_throttle = -1
        self.language = language
        self.override = override
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)['feature_store']
            self.reject_throttle = config['reject_throttle']
        logger.debug('loading text2vec model..')
        self.embedder = embedder
        self.retriever = None
        self.chunk_size = chunk_size
        self.analyze_reject = analyze_reject
        if rejecter_naive_splitter:
            raise ValueError('The `rejecter_naive_splitter` option deprecated, please `git checkout v20240722`')
        if analyze_reject:
            raise ValueError('The `analyze_reject` option deprecated, please `git checkout v20240722`')
        logger.info('init dense retrieval database with chunk_size {}'.format(chunk_size))
        if language == 'zh':
            self.text_splitter = ChineseRecursiveTextSplitter(keep_separator=True, is_separator_regex=True, chunk_size=chunk_size, chunk_overlap=32)
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=32)

    def parse_markdown(self, file: FileName, metadata: Dict):
        length = 0
        text = file.basename + '\n'
        with open(file.copypath, encoding='utf8') as f:
            text += f.read()
        if len(text) <= 1:
            return ([], length)
        chunks = nested_split_markdown(file.origin, text=text, chunksize=self.chunk_size, metadata=metadata)
        for c in chunks:
            length += len(c.content_or_path)
        return (chunks, length)

    def build_inverted_index(self, chunks: List[Chunk], ner_file: str, work_dir: str):
        """Build inverted index based on named entity for knowledge base."""
        if ner_file is None:
            return
        index_dir = os.path.join(work_dir, 'db_reverted_index')
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        entities = []
        with open(ner_file) as f:
            entities = json.load(f)
        time0 = time.time()
        map_entity2chunks = dict()
        indexer = NamedEntity2Chunk(file_dir=index_dir)
        indexer.clean()
        indexer.set_entity(entities=entities)
        for chunk_id, chunk in enumerate(chunks):
            if chunk.modal != 'text':
                continue
            entity_ids = indexer.parse(text=chunk.content_or_path)
            for entity_id in entity_ids:
                if entity_id not in map_entity2chunks:
                    map_entity2chunks[entity_id] = [chunk_id]
                else:
                    map_entity2chunks[entity_id].append(chunk_id)
        for entity_id, chunk_indexes in map_entity2chunks.items():
            indexer.insert_relation(eid=entity_id, chunk_ids=chunk_indexes)
        del indexer
        time1 = time.time()
        logger.info('Timecost for build_inverted_index {}s'.format(time1 - time0))

    def build_sparse(self, files: List[FileName], work_dir: str):
        """Use BM25 for building code feature"""
        fileopr = FileOperation()
        chunks = []
        for file in files:
            content, error = fileopr.read(file.origin)
            if error is not None:
                continue
            file_chunks = split_python_code(filepath=file.origin, text=content, metadata={'source': file.origin, 'read': file.copypath})
            chunks += file_chunks
        sparse_dir = os.path.join(work_dir, 'db_sparse')
        bm25 = BM25Okapi()
        bm25.save(chunks, sparse_dir)

    def process_qa_pairs(self, qa_pair_file: str) -> List[Chunk]:
        """Process QA pairs from CSV or JSON file.
        
        Args:
            qa_pair_file: Path to the CSV or JSON file containing QA pairs.
            
        Returns:
            List of Chunk objects where key is the content and value is stored in metadata.
        """
        chunks = []
        file_ext = os.path.splitext(qa_pair_file)[1].lower()
        try:
            if file_ext == '.csv':
                with open(qa_pair_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    for row in csv_reader:
                        if len(row) >= 2:
                            key, value = (row[0], row[1])
                            chunk = Chunk(modal='qa', content_or_path=key, metadata={'read': qa_pair_file, 'source': qa_pair_file, 'qa': f'{key}: {value}'})
                            chunks.append(chunk)
            elif file_ext == '.json':
                with open(qa_pair_file, 'r', encoding='utf-8') as f:
                    qa_data = json.load(f)
                    if isinstance(qa_data, dict):
                        for key, value in qa_data.items():
                            chunk = Chunk(modal='qa', content_or_path=key, metadata={'read': qa_pair_file, 'source': qa_pair_file, 'qa': f'{key}: {value}'})
                            chunks.append(chunk)
                    elif isinstance(qa_data, list):
                        for item in qa_data:
                            if isinstance(item, dict) and 'key' in item and ('value' in item):
                                chunk = Chunk(modal='qa', content_or_path=key, metadata={'read': qa_pair_file, 'source': qa_pair_file, 'qa': f'{key}: {value}'})
                                chunks.append(chunk)
            logger.info(f'Processed {len(chunks)} QA pairs from {qa_pair_file}')
            return chunks
        except Exception as e:
            logger.error(f'Error processing QA pairs from {qa_pair_file}: {str(e)}')
            return []

    def build_dense(self, files: List[FileName], work_dir: str, markdown_as_txt: bool=False, qa_pair_file: str=None):
        """Extract the features required for the response pipeline based on the
        document."""
        feature_dir = os.path.join(work_dir, 'db_dense')
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)
        file_opr = FileOperation()
        chunks = []
        if qa_pair_file is not None:
            qa_chunks = self.process_qa_pairs(qa_pair_file)
            chunks.extend(qa_chunks)
            logger.info(f'Added {len(qa_chunks)} chunks from QA pairs')
        for i, file in tqdm(enumerate(files), 'split'):
            if not file.state:
                continue
            metadata = {'source': file.origin, 'read': file.copypath}
            if not markdown_as_txt and file._type == 'md':
                md_chunks, md_length = self.parse_markdown(file=file, metadata=metadata)
                chunks += md_chunks
                file.reason = str(md_length)
            else:
                text, error = file_opr.read(file.copypath)
                if error is not None:
                    file.state = False
                    file.reason = str(error)
                    continue
                file.reason = str(len(text))
                text = file.prefix + text
                chunks += self.text_splitter.create_chunks(texts=[text], metadatas=[metadata])
        if not self.embedder.support_image:
            filtered_chunks = list(filter(lambda x: x.modal == 'text' or x.modal == 'qa', chunks))
        else:
            filtered_chunks = chunks
        if len(chunks) < 1:
            return chunks
        self.analyze(filtered_chunks)
        Faiss.save_local(folder_path=feature_dir, chunks=filtered_chunks, embedder=self.embedder)
        return chunks

    def analyze(self, chunks: List[Chunk]):
        """Output documents length mean, median and histogram."""
        MAX_COUNT = 10000
        if len(chunks) > MAX_COUNT:
            chunks = random.sample(chunks, MAX_COUNT)
        text_lens = []
        token_lens = []
        text_chunk_count = 0
        image_chunk_count = 0
        if self.embedder is None:
            logger.info('self.embedder is None, skip `anaylze_output`')
            return
        for chunk in tqdm(chunks, 'analyze distribution'):
            if chunk.modal == 'image':
                image_chunk_count += 1
            elif chunk.modal == 'text':
                text_chunk_count += 1
            content = chunk.content_or_path
            text_lens.append(len(content))
            token_lens.append(self.embedder.token_length(content))
        logger.info('text_chunks {}, image_chunks {}'.format(text_chunk_count, image_chunk_count))
        logger.info('text histogram, {}'.format(histogram(text_lens)))
        logger.info('token histogram, {}'.format(histogram(token_lens)))

    def preprocess(self, files: List, work_dir: str):
        """Preprocesses files in a given directory. Copies each file to
        'preprocess' with new name formed by joining all subdirectories with
        '_'.

        Args:
            files (list): original file list.
            work_dir (str): Working directory where preprocessed files will be stored.  # noqa E501

        Returns:
            str: Path to the directory where preprocessed markdown files are saved.

        Raises:
            Exception: Raise an exception if no markdown files are found in the provided repository directory.  # noqa E501
        """
        preproc_dir = os.path.join(work_dir, 'preprocess')
        if not os.path.exists(preproc_dir):
            os.makedirs(preproc_dir)
        pool = Pool(processes=8)
        file_opr = FileOperation()
        for idx, file in tqdm(enumerate(files), 'preprocess'):
            if not os.path.exists(file.origin):
                file.state = False
                file.reason = 'skip not exist'
                continue
            if file._type == 'image':
                file.state = False
                file.reason = 'skip image'
            elif file._type in ['pdf', 'word', 'excel', 'ppt', 'html']:
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir, '{}.text'.format(md5))
                pool.apply_async(read_and_save, (file,))
            elif file._type in ['code']:
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir, '{}.code'.format(md5))
                read_and_save(file)
            elif file._type in ['md', 'text']:
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir, file.origin.replace('/', '_')[-84:])
                try:
                    shutil.copy(file.origin, file.copypath)
                    file.state = True
                    file.reason = 'preprocessed'
                except Exception as e:
                    file.state = False
                    file.reason = str(e)
            else:
                file.state = False
                file.reason = 'skip unknown format'
        pool.close()
        logger.debug('waiting for file preprocess finish..')
        pool.join()
        for file in files:
            if file._type in ['pdf', 'word', 'excel']:
                if os.path.exists(file.copypath):
                    file.state = True
                    file.reason = 'preprocessed'
                else:
                    file.state = False
                    file.reason = 'read error'

    def initialize(self, config: InitializeConfig):
        """Initializes response and reject feature store.

        Only needs to be called once. Also calculates the optimal threshold
        based on provided good and bad question examples, and saves it in the
        configuration file.
        
        Args:
            config: Configuration object containing initialization parameters
        """
        logger.info('initialize response and reject feature store, you only need call this once.')
        self.preprocess(files=config.files, work_dir=config.work_dir)
        documents = list(filter(lambda x: x._type != 'code', config.files))
        chunks = self.build_dense(files=documents, work_dir=config.work_dir, qa_pair_file=config.qa_pair_file)
        codes = list(filter(lambda x: x._type == 'code', config.files))
        self.build_sparse(files=codes, work_dir=config.work_dir)
        self.build_inverted_index(chunks=chunks, ner_file=config.ner_file, work_dir=config.work_dir)

def __init__(self, embedder: Embedder, config_path: str='config.ini', language: str='zh', chunk_size=900, analyze_reject=False, rejecter_naive_splitter=False, override=False) -> None:
    """Init with model device type and config."""
    self.config_path = config_path
    self.reject_throttle = -1
    self.language = language
    self.override = override
    with open(config_path, encoding='utf8') as f:
        config = pytoml.load(f)['feature_store']
        self.reject_throttle = config['reject_throttle']
    logger.debug('loading text2vec model..')
    self.embedder = embedder
    self.retriever = None
    self.chunk_size = chunk_size
    self.analyze_reject = analyze_reject
    if rejecter_naive_splitter:
        raise ValueError('The `rejecter_naive_splitter` option deprecated, please `git checkout v20240722`')
    if analyze_reject:
        raise ValueError('The `analyze_reject` option deprecated, please `git checkout v20240722`')
    logger.info('init dense retrieval database with chunk_size {}'.format(chunk_size))
    if language == 'zh':
        self.text_splitter = ChineseRecursiveTextSplitter(keep_separator=True, is_separator_regex=True, chunk_size=chunk_size, chunk_overlap=32)
    else:
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=32)

class SerialPipeline:
    """The SerialPipeline class orchestrates the logic of handling user queries,
    generating responses and managing several aspects of a chat assistant. It
    enables feature storage, language model client setup, time scheduling and
    much more.

    Attributes:
        llm: A LLM instance that communicates with the language model.
        fs: An instance of FeatureStore for loading and querying features.
        config_path: A string indicating the path of the configuration file.
        config: A dictionary holding the configuration settings.
        language: A string indicating the language of the chat, default is 'zh' (Chinese).  # noqa E501
        context_max_length: An integer representing the maximum length of the context used by the language model.  # noqa E501

        Several template strings for various prompts are also defined.
    """

    def __init__(self, work_dir: str, config_path: str, language: str='zh'):
        """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
            language (str, optional): Specifies the language to be used. Defaults to 'zh' (Chinese).  # noqa E501
        """
        self.llm = LLM(config_path=config_path)
        self.retriever = CacheRetriever(config_path=config_path).get()
        self.config_path = config_path
        self.config = None
        self.language = language
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')

    def notify_badcase(self):
        """Receiving revert command means the current threshold is too low, use
        higher one."""
        delta = max(0, 1 - self.retriever.reject_throttle) * 0.02
        logger.info('received badcase, use bigger reject_throttle. Current {}, delta {}'.format(self.retriever.reject_throttle, delta))
        self.retriever.reject_throttle = min(self.retriever.reject_throttle + delta, 0.5)
        with open('throttle', 'w') as f:
            f.write(str(self.retriever.reject_throttle))

    def work_time(self):
        """If worktime enabled, determines the current time falls within the
        scheduled working hours of the chat assistant.

        Returns:
            bool: True if the current time is within working hours, otherwise False.  # noqa E501
        """
        time_config = self.config['worker']['time']
        if 'enable' in time_config:
            if not time_config['enable']:
                return True
        beginWork = datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + time_config['start']
        endWork = datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + time_config['end']
        beginWorkSeconds = time.time() - time.mktime(time.strptime(beginWork, '%Y-%m-%d %H:%M:%S'))
        endWorkSeconds = time.time() - time.mktime(time.strptime(endWork, '%Y-%m-%d %H:%M:%S'))
        if int(beginWorkSeconds) > 0 and int(endWorkSeconds) < 0:
            if not time_config['has_weekday']:
                return True
            if int(datetime.datetime.now().weekday()) in range(7):
                return True
        return False

    async def generate(self, query: Union[Query, str], history: List[Tuple[str, str]]=[], groupname: str='', groupchats: List[str]=[]):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (Union[Query,str]): User's multimodal query.
            history (str): Chat history.
            groupname (str): The group name in which user asked the query.
            groupchats (List[str]): The history conversation in group before user query.

        Returns:
            Session: Sync generator, this function would yield session which contains:
                ErrorCode: An error code indicating the status of response generation.  # noqa E501
                str: Generated response to the user query.
                references: List for referenced filename or web url
        """
        if type(query) is str:
            query = Query(text=query)
        sess = Session(query=query, history=history, groupname=groupname, log_path=self.config['worker']['save_path'], groupchats=groupchats)
        preproc = PreprocNode(self.config, self.llm, self.language)
        text2vec = Text2vecNode(self.config, self.llm, self.retriever, self.language)
        websearch = WebSearchNode(self.config, self.config_path, self.llm, self.language)
        check = SecurityNode(self.llm, self.language)
        pipeline = [preproc, text2vec, websearch]
        exit_states = [ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION, ErrorCode.NO_TOPIC, ErrorCode.UNRELATED]
        for node in pipeline:
            async for sess in node.process(sess):
                yield sess
            if sess.code in exit_states:
                break
            if sess.code == ErrorCode.SUCCESS:
                async for sess in check.process(sess):
                    yield sess
            if sess.code == ErrorCode.SUCCESS:
                break
        logger.debug(sess.debug)
        yield sess

def notify_badcase(self):
    """Receiving revert command means the current threshold is too low, use
        higher one."""
    delta = max(0, 1 - self.retriever.reject_throttle) * 0.02
    logger.info('received badcase, use bigger reject_throttle. Current {}, delta {}'.format(self.retriever.reject_throttle, delta))
    self.retriever.reject_throttle = min(self.retriever.reject_throttle + delta, 0.5)
    with open('throttle', 'w') as f:
        f.write(str(self.retriever.reject_throttle))

class Backend:

    def __init__(self, name: str, data: Dict):
        self.api_key = data.get('remote_api_key', '')
        self._type = data.get('remote_type', '')
        self.max_token_size = data.get('remote_llm_max_text_length', 32000) - 4096
        if self.max_token_size < 0:
            raise Exception(f'{self.max_token_size} < 4096')
        self.rpm = RPM(int(data.get('rpm', 500)))
        self.tpm = TPM(int(data.get('tpm', 50000)))
        self.name = name
        self.port = int(data.get('port', 23333))
        self.model = data.get('remote_llm_model', '')
        self.base_url = data.get('base_url', '')
        if not self.base_url and name in backend2url:
            self.base_url = backend2url[name]

    def jsonify(self):
        return {'api_key': self.name, 'model': self.model}

    def __str__(self):
        return json.dumps(self.jsonify())

def __init__(self, name: str, data: Dict):
    self.api_key = data.get('remote_api_key', '')
    self._type = data.get('remote_type', '')
    self.max_token_size = data.get('remote_llm_max_text_length', 32000) - 4096
    if self.max_token_size < 0:
        raise Exception(f'{self.max_token_size} < 4096')
    self.rpm = RPM(int(data.get('rpm', 500)))
    self.tpm = TPM(int(data.get('tpm', 50000)))
    self.name = name
    self.port = int(data.get('port', 23333))
    self.model = data.get('remote_llm_model', '')
    self.base_url = data.get('base_url', '')
    if not self.base_url and name in backend2url:
        self.base_url = backend2url[name]

class LLM:

    def __init__(self, config_path: str):
        """Initialize the LLM with the path of the configuration file."""
        self.config_path = config_path
        self.llm_config = None
        self.backends = dict()
        self.sum_input_token_size = 0
        self.sum_output_token_size = 0
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']['server']
            name = self.llm_config['remote_type']
            self.backends[name] = Backend(name=name, data=self.llm_config)

    def choose_model(self, backend: Backend, token_size: int) -> str:
        model = backend.model
        response_reserve_length = 2048
        if backend.name == 'kimi':
            if model == 'auto':
                if token_size <= 8192 - response_reserve_length:
                    model = 'moonshot-v1-8k'
                elif token_size <= 32768 - response_reserve_length:
                    model = 'moonshot-v1-32k'
                elif token_size <= 128000 - response_reserve_length:
                    model = 'moonshot-v1-128k'
                else:
                    raise ValueError('Input token length exceeds 128k')
        elif backend.name == 'step' and model == 'auto':
            if token_size <= 8192 - response_reserve_length:
                model = 'step-1-8k'
            elif token_size <= 32768 - response_reserve_length:
                model = 'step-1-32k'
            elif token_size <= 128000 - response_reserve_length:
                model = 'step-1-128k'
            elif token_size <= 256000 - response_reserve_length:
                model = 'step-1-256k'
            else:
                raise ValueError('Input token length exceeds 256k')
        elif not model and backend.name in backend2model:
            model = backend2model[backend.name]
        return model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60), retry=retry_if_exception_type((RateLimitError, APIConnectionError, Timeout, APITimeoutError)))
    @limit_async_func_call(16)
    async def chat(self, prompt: str, backend: str='default', system_prompt='你是茴香豆，简称豆哥。是一个微信群机器人，用于回答群友的疑问。', history=[], allow_truncate=False, max_tokens=1024, timeout=600, tools=[]) -> str:
        if backend == 'default':
            backend = list(self.backends.keys())[0]
        instance = self.backends[backend]
        input_tokens = encode_string(content=str(prompt) + str(history))
        input_token_size = len(input_tokens)
        if input_token_size > instance.max_token_size:
            if not allow_truncate:
                raise Exception(f'input token size {input_token_size}, max {instance.max_token_size}')
            tokens = input_tokens[0:instance.max_token_size - input_token_size]
            prompt = decode_tokens(tokens=tokens)
            input_token_size = len(tokens)
        await instance.tpm.wait(token_count=input_token_size)
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})
        content = ''
        model = self.choose_model(backend=instance, token_size=input_token_size)
        openai_async_client = AsyncOpenAI(base_url=instance.base_url, api_key=instance.api_key, timeout=timeout)
        kwargs = {'model': model, 'messages': messages, 'temperature': 0.7, 'top_p': 0.7, 'tools': tools}
        if max_tokens:
            kwargs['max_tokens'] = max_tokens
        try:
            response = await openai_async_client.chat.completions.create(**kwargs)
        except Exception as e:
            logger.error(str(e) + ' input len {}'.format(len(str(messages))))
            pass
        logger.info(response.choices[0].message.content)
        content = response.choices[0].message.content
        content_token_size = len(encode_string(content=content))
        self.sum_input_token_size += input_token_size
        self.sum_output_token_size += content_token_size
        await instance.tpm.wait(token_count=content_token_size)
        await instance.rpm.wait()
        return content.strip()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=30, max=60), retry=retry_if_exception_type((RateLimitError, APIConnectionError, Timeout, APITimeoutError)))
    async def chat_stream(self, prompt: str, backend: str='default', system_prompt=None, history=[], allow_truncate=False, max_tokens=1024, timeout=600):
        if backend == 'default':
            backend = list(self.backends.keys())[0]
        instance = self.backends[backend]
        input_tokens = encode_string(content=str(prompt) + str(history))
        input_token_size = len(input_tokens)
        if input_token_size > instance.max_token_size:
            if not allow_truncate:
                raise Exception(f'input token size {input_token_size}, max {instance.max_token_size}')
            tokens = input_tokens[0:instance.max_token_size - input_token_size]
            prompt = decode_tokens(tokens=tokens)
            input_token_size = len(tokens)
        await instance.tpm.wait(token_count=input_token_size)
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.extend(history)
        messages.append({'role': 'user', 'content': prompt})
        content = ''
        try:
            model = self.choose_model(backend=instance, token_size=input_token_size)
            openai_async_client = AsyncOpenAI(base_url=instance.base_url, api_key=instance.api_key, timeout=timeout)
            stream = await openai_async_client.chat.completions.create(model=model, messages=messages, temperature=0.7, top_p=0.7, max_tokens=max_tokens, stream=True)
            content = ''
            async for chunk in stream:
                if chunk.choices is None:
                    raise Exception(str(chunk))
                delta = chunk.choices[0].delta
                if delta.content:
                    content += delta.content
                    yield delta.content
        except Exception as e:
            logger.error(str(e) + ' input len {}'.format(len(str(messages))))
            raise e
        content_token_size = len(encode_string(content=content))
        self.sum_input_token_size += input_token_size
        self.sum_output_token_size += content_token_size
        await instance.tpm.wait(token_count=content_token_size)
        await instance.rpm.wait()
        return

    def default_model_info(self):
        backend = list(self.backends.keys())[0]
        instance = self.backends[backend]
        return instance.jsonify()

    def build_prompt(self, history_pair, instruction: str, template: str, context: str='', reject: str='<reject>'):
        """Build a prompt for interaction.

        Args:
            history_pair (list): List of previous interactions.
            instruction (str): Instruction for the current interaction.
            template (str): Template for constructing the interaction.
            context (str, optional): Context of the interaction. Defaults to ''.  # noqa E501
            reject (str, optional): Text that indicates a rejected interaction. Defaults to '<reject>'.  # noqa E501

        Returns:
            tuple: A tuple containing the constructed instruction and real history.
        """
        if context is not None and len(context) > 0:
            instruction = template.format(context, instruction)
        real_history = []
        for pair in history_pair:
            if pair[1] == reject:
                continue
            if pair[0] is None or pair[1] is None:
                continue
            if len(pair[0]) < 1 or len(pair[1]) < 1:
                continue
            real_history.append(pair)
        return (instruction, real_history)

def choose_model(self, backend: Backend, token_size: int) -> str:
    model = backend.model
    response_reserve_length = 2048
    if backend.name == 'kimi':
        if model == 'auto':
            if token_size <= 8192 - response_reserve_length:
                model = 'moonshot-v1-8k'
            elif token_size <= 32768 - response_reserve_length:
                model = 'moonshot-v1-32k'
            elif token_size <= 128000 - response_reserve_length:
                model = 'moonshot-v1-128k'
            else:
                raise ValueError('Input token length exceeds 128k')
    elif backend.name == 'step' and model == 'auto':
        if token_size <= 8192 - response_reserve_length:
            model = 'step-1-8k'
        elif token_size <= 32768 - response_reserve_length:
            model = 'step-1-32k'
        elif token_size <= 128000 - response_reserve_length:
            model = 'step-1-128k'
        elif token_size <= 256000 - response_reserve_length:
            model = 'step-1-256k'
        else:
            raise ValueError('Input token length exceeds 256k')
    elif not model and backend.name in backend2model:
        model = backend2model[backend.name]
    return model

