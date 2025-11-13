# Cluster 14

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

def main():
    pwd = os.path.dirname(__file__)
    base = os.path.join(pwd, '..', 'feature_stores')
    dirs = os.listdir(base)
    params = []
    import pdb
    pdb.set_trace()
    for fsid in dirs:
        filedir = os.path.join(base, fsid, 'workdir/preprocess')
        process((fsid, filedir))
        params.append((fsid, filedir))

def plot_3d():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for jsonl_file in os.listdir('./'):
        if not jsonl_file.endswith('.jsonl'):
            continue
        if not 'chunk_size' in jsonl_file:
            continue
        x = []
        y = []
        z = []
        print(jsonl_file)
        datas = []
        with open(jsonl_file) as f:
            for json_str in f:
                json_obj = json.loads(json_str)
                datas.append(json_obj)
        datas.sort(key=lambda x: x['throttle'])
        for data in datas:
            chunk_size = data['chunk_size']
            throttle = data['throttle']
            f1 = data['f1']
            x.append(chunk_size)
            y.append(throttle)
            z.append(f1)
        ax.plot(x, y, z)
    ax.set_title('3D Line Plot')
    ax.set_xlabel('chunk_size')
    ax.set_ylabel('throttle')
    ax.set_zlabel('f1')
    plt.show()

def plot_cross_splitter():
    fig = plt.figure()
    for splitter in os.listdir('./'):
        if not splitter.startswith('chunk_size'):
            continue
        if not os.path.isdir(splitter):
            continue
        items = []
        for jsonl_file in os.listdir(splitter):
            if not 'chunk_size' in jsonl_file:
                continue
            print(splitter, jsonl_file)
            datas = []
            with open(os.path.join(splitter, jsonl_file)) as f:
                for json_str in f:
                    json_obj = json.loads(json_str)
                    datas.append(json_obj)
            datas.sort(key=lambda x: x['f1'])
            items.append({'chunk_size': datas[-1]['chunk_size'], 'f1': datas[-1]['f1']})
        items.sort(key=lambda x: x['chunk_size'])
        x = []
        y = []
        for item in items:
            if item['chunk_size'] > 1000:
                continue
            x.append(item['chunk_size'])
            y.append(item['f1'])
        print(x, y)
        label_name = splitter.split('chunk_size_')[-1]
        plt.plot(x, y, label=label_name)
    plt.xlabel('chunk_size')
    plt.ylabel('best_f1')
    plt.legend()
    plt.show()

def test_llm_reranker():
    model_path = '/data2/khj/bge-reranker-v2-minicpm-layerwise'
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True, torch_dtype=torch.bfloat16)
    model = model.to('cuda')
    model.eval()
    outdir = '/home/khj/hxd-ci/odir'
    with torch.no_grad():
        dirpath = '/home/khj/hxd-ci/candidates'
        for name in os.listdir(dirpath):
            fullpath = os.path.join(dirpath, name)
            outfullpath = os.path.join(outdir, name)
            with open(fullpath) as fin:
                for jsonstr in fin:
                    jsonobj = json.loads(jsonstr)
                    pairs = []
                    query = jsonobj['query']
                    candidates = jsonobj['candidates']
                    output = {'query': query, 'rank': []}
                    for can in candidates:
                        content = can['content']
                        pairs.append([query, content])
                    inputs = get_inputs(pairs, tokenizer).to(model.device)
                    all_scores = model(**inputs, return_dict=True, cutoff_layers=[28])
                    all_scores = [scores[:, -1].view(-1).float() for scores in all_scores[0]]
                    all_scores = all_scores[0].cpu().numpy()
                    indexes = all_scores.argsort()[::-1]
                    for index in indexes:
                        output['rank'].append(candidates[index]['content'])
                    outstr = json.dumps(output, ensure_ascii=False, indent=2)
                    with open(outfullpath, 'a') as fout:
                        fout.write(outstr)
                        fout.write('\n')

def test_bce_reranker():
    whitelist = ['0JOL.jsonl', '0ki5.jsonl', '0oDm.jsonl', '1lA9.jsonl', '2P8j.jsonl']
    model_path = '/data2/khj/bce-embedding-base_v1'
    model = RerankerModel(model_name_or_path=model_path)
    outdir = '/home/khj/hxd-ci/bceodir'
    with torch.no_grad():
        dirpath = '/home/khj/hxd-ci/candidates'
        for name in os.listdir(dirpath):
            if name not in whitelist:
                continue
            fullpath = os.path.join(dirpath, name)
            outfullpath = os.path.join(outdir, name)
            with open(fullpath) as fin:
                for jsonstr in fin:
                    jsonobj = json.loads(jsonstr)
                    query = jsonobj['query']
                    passages = []
                    candidates = jsonobj['candidates']
                    output = {'query': query, 'rank': []}
                    for can in candidates:
                        content = can['content']
                        passages.append(content)
                    rerank_results = model.rerank(query, passages)
                    output['rank'] = rerank_results['rerank_passages']
                    outstr = json.dumps(output, ensure_ascii=False, indent=2)
                    with open(outfullpath, 'a') as fout:
                        fout.write(outstr)
                        fout.write('\n')

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-09)

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

def _forward(self, model_inputs):
    outputs = self.model(**model_inputs)
    return {'outputs': outputs, 'attention_mask': model_inputs['attention_mask']}

def plot_top_words(model, feature_names, n_top_words, title):
    fig, axes = plt.subplots(2, 5, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[-n_top_words:]
        top_features = feature_names[top_features_ind]
        weights = topic[top_features_ind]
        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f'Topic {topic_idx + 1}', fontdict={'fontsize': 30})
        ax.tick_params(axis='both', which='major', labelsize=20)
        for i in 'top right left'.split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)
    plt.subplots_adjust(top=0.9, bottom=0.05, wspace=0.9, hspace=0.3)
    plt.savefig('topic_centers.jpg')

