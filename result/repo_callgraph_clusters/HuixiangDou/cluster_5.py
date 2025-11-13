# Cluster 5

def builder_inited_handler(app):
    subprocess.run(['./cp_origin_docs.sh'])

def builder_inited_handler(app):
    subprocess.run(['./cp_origin_docs.sh'])

def main():
    """main function start server use uvicorn default workers: 3 default port:

    23333.
    """
    HuixiangDouEnv.print_env()
    uvicorn.run('web.main:app', host='0.0.0.0', port=int(SERVER_PORT), timeout_keep_alive=600, workers=3, log_config=LOGGING_CONFIG)

def event_stream():
    for sess in assistant.generate(query=query):
        status = {'state': str(sess.code), 'response': sess.response, 'refs': sess.references}
        pipeline['step'].append(status)
        yield json.dumps(pipeline)

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

def token_length(self, text: str) -> int:
    if 'bge' in self._type or 'bce' in self._type:
        return len(self.client.tokenizer(text, padding=False, truncation=False)['input_ids'])
    else:
        return len(text) // 2

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

def _tokenize_corpus(self, corpus):
    tokenized_corpus = self.tokenizer(corpus)
    return tokenized_corpus

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

def llm_serve(config_path: str, server_ready: Value):
    """Start the LLM server.

    Args:
        config_path (str): Path to the configuration file.
        server_ready (multiprocessing.Value): Shared variable to indicate when the server is ready.  # noqa E501
    """
    with open(config_path, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
        bind_port = int(llm_config['server']['local_llm_bind_port'])
    try:
        server = HybridLLMServer(llm_config=llm_config)
        server_ready.value = 1
    except Exception as e:
        server_ready.value = -1
        raise e

    async def inference(talk: Talk):
        """Call local llm inference."""
        logger.info(talk)
        prompt = talk.prompt
        history = talk.history
        backend = talk.backend
        parts = []
        try:
            async for text in server.chat_stream(prompt=prompt, history=history, backend=backend):
                parts.append(text)
            return {'text': ''.join(parts), 'error': ''}
        except Exception as e:
            return {'text': '', 'error': str(e)}

    async def stream(talk: Talk):
        """Call local llm inference."""
        logger.info(talk)
        prompt = talk.prompt
        history = talk.history
        backend = talk.backend

        async def generate():
            async for text in server.chat_stream(prompt=prompt, history=history, backend=backend):
                yield text
        return EventSourceResponse(generate())
    app = FastAPI(docs_url='/')
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
    router = APIRouter()
    router.add_api_route('/inference', inference, methods=['POST'])
    router.add_api_route('/stream', stream, methods=['POST'])
    app.include_router(router)
    uvicorn.run(app, host='0.0.0.0', port=bind_port, log_level='info')

def main(args):
    n_garbage = args.max_tokens - 1000
    passed_tests = 0
    for j in range(args.num_tests):
        prompt, pass_key = generate_prompt_landmark(n_garbage=n_garbage, seed=5120 + j)
        try:
            response = generate(prompt='hello')
            print(response)
            response = generate(prompt=prompt)
        except Exception as e:
            print(e)
        print('result: ', response, pass_key)
        if pass_key in response.content:
            passed_tests += 1
    precision = passed_tests / args.num_tests
    print('precision {} @ {}'.format(precision, args.max_tokens))

def get_inputs(pairs, tokenizer, prompt=None, max_length=1024):
    if prompt is None:
        prompt = "Given a query A and a passage B, determine whether the passage contains an answer to the query by providing a prediction of either 'Yes' or 'No'."
    sep = '\n'
    prompt_inputs = tokenizer(prompt, return_tensors=None, add_special_tokens=False)['input_ids']
    sep_inputs = tokenizer(sep, return_tensors=None, add_special_tokens=False)['input_ids']
    inputs = []
    for query, passage in pairs:
        query_inputs = tokenizer(f'A: {query}', return_tensors=None, add_special_tokens=False, max_length=max_length * 3 // 4, truncation=True)
        passage_inputs = tokenizer(f'B: {passage}', return_tensors=None, add_special_tokens=False, max_length=max_length, truncation=True)
        item = tokenizer.prepare_for_model([tokenizer.bos_token_id] + query_inputs['input_ids'], sep_inputs + passage_inputs['input_ids'], truncation='only_second', max_length=max_length, padding=False, return_attention_mask=False, return_token_type_ids=False, add_special_tokens=False)
        item['input_ids'] = item['input_ids'] + sep_inputs + prompt_inputs
        item['attention_mask'] = [1] * len(item['input_ids'])
        inputs.append(item)
    return tokenizer.pad(inputs, padding=True, max_length=max_length + len(sep_inputs) + len(prompt_inputs), pad_to_multiple_of=8, return_tensors='pt')

class SentenceEmbeddingPipeline(Pipeline):

    def _sanitize_parameters(self, **kwargs):
        preprocess_kwargs = {}
        return (preprocess_kwargs, {}, {})

    def preprocess(self, inputs):
        encoded_inputs = self.tokenizer(inputs, padding=True, truncation=True, return_tensors='pt')
        return encoded_inputs

    def _forward(self, model_inputs):
        outputs = self.model(**model_inputs)
        return {'outputs': outputs, 'attention_mask': model_inputs['attention_mask']}

    def postprocess(self, model_outputs):
        sentence_embeddings = mean_pooling(model_outputs['outputs'], model_outputs['attention_mask'])
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings

def preprocess(self, inputs):
    encoded_inputs = self.tokenizer(inputs, padding=True, truncation=True, return_tensors='pt')
    return encoded_inputs

def profiling():
    onnx_path = 'o4-opt-onnx'
    model = ORTModelForFeatureExtraction.from_pretrained(onnx_path, file_name='model.onnx')
    model.to('cuda')
    tokenizer = AutoTokenizer.from_pretrained(onnx_path)
    vanilla_emb = SentenceEmbeddingPipeline(model=model, tokenizer=tokenizer)
    pred = vanilla_emb('Could you assist me in finding my lost card? vanilla_emb')
    print(pred[0][:5])
    onnx_path = 'onnx'
    model = ORTModelForFeatureExtraction.from_pretrained(onnx_path, file_name='model.onnx')
    model.to('cuda')
    tokenizer = AutoTokenizer.from_pretrained(onnx_path)
    q8_emb = SentenceEmbeddingPipeline(model=model, tokenizer=tokenizer)
    pred = q8_emb('Could you assist me in finding my lost card? q8_emb')
    print(pred[0][:5])
    from time import perf_counter
    import numpy as np
    payload = 'Hello, my name is Philipp and I live in Nuremberg, Germany. Currently I am working as a Technical Lead at Hugging Face to democratize artificial intelligence through open source and open science. In the past I designed and implemented cloud-native machine learning architectures for fin-tech and insurance companies. I found my passion for cloud concepts and machine learning 5 years ago. Since then I never stopped learning. Currently, I am focusing myself in the area NLP and how to leverage models like BERT, Roberta, T5, ViT, and GPT2 to generate business value. I cannot wait to see what is next for me'
    print(f'Payload sequence length: {len(tokenizer(payload)['input_ids'])}')

    def measure_latency(pipe):
        latencies = []
        for _ in range(4):
            _ = pipe(payload)
        for _ in range(20):
            start_time = perf_counter()
            _ = pipe(payload)
            latency = perf_counter() - start_time
            latencies.append(latency)
        time_avg_ms = 1000 * np.mean(latencies)
        time_std_ms = 1000 * np.std(latencies)
        time_p95_ms = 1000 * np.percentile(latencies, 95)
        return (f'P95 latency (ms) - {time_p95_ms}; Average latency (ms) - {time_avg_ms:.2f} +\\- {time_std_ms:.2f};', time_p95_ms)
    vanilla_model = measure_latency(vanilla_emb)
    quantized_model = measure_latency(q8_emb)
    print(f'Vanilla model: {vanilla_model[0]}')
    print(f'Quantized model: {quantized_model[0]}')
    print(f'Improvement through quantization: {round(vanilla_model[1] / quantized_model[1], 2)}x')

def call_plugin(plugin_name: str, plugin_args: str) -> str:
    if plugin_name == 'google_search':
        os.environ['SERPAPI_API_KEY'] = os.getenv('SERPAPI_API_KEY', default='')
        from langchain import SerpAPIWrapper
        return SerpAPIWrapper().run(json5.loads(plugin_args)['search_query'])
    elif plugin_name == 'image_gen':
        import urllib.parse
        prompt = json5.loads(plugin_args)['prompt']
        prompt = urllib.parse.quote(prompt)
        return json.dumps({'image_url': f'https://image.pollinations.ai/prompt/{prompt}'}, ensure_ascii=False)
    else:
        raise NotImplementedError

def run(input_text: str):
    prompt = "The following is a conversation between a human and an AI assistant namely YuLan, developed by GSAI, Renmin University of China. The AI assistant gives helpful, detailed, and polite answers to the user's questions.\n[|Human|]:{}\n[|AI|]:".format(input_text)
    inputs = tokenizer(prompt, return_tensors='pt', padding='longest', max_length=8192, truncation=True, return_attention_mask=True, add_special_tokens=True)
    print(inputs)
    kwargs = {'temperature': 0.8, 'top_p': 0.95, 'top_k': 50, 'repetition_penalty': 1.1, 'no_repeat_ngram_size': 64, 'max_length': 8192, 'pad_token_id': tokenizer.bos_token_id, 'eos_token_id': tokenizer.eos_token_id}
    outputs = model.generate(inputs['input_ids'].to(model.device), attention_mask=inputs['attention_mask'].to(model.device), do_sample=True, **kwargs)
    print(tokenizer.batch_decode(outputs, skip_special_tokens=True))

