# Cluster 9

def remove_at_name(text):
    pattern = '@[\\w\\.-]+\\s+'
    text = re.sub(pattern, '', text)
    pos = text.find('@')
    if pos != -1:
        text = text[0:pos]
    return text

def is_question(query):
    llm = ChatClient('config.ini')
    SCORING_QUESTION_TEMPLATE = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    prompt = SCORING_QUESTION_TEMPLATE.format(query)
    if prompt is None or len(prompt) == 0:
        return False
    score = 0
    relation = llm.generate_response(prompt=prompt, backend='puyu')
    filtered_relation = ''.join([c for c in relation if c.isdigit()])
    try:
        score_str = re.sub('[^\\d]', ' ', filtered_relation).strip()
        score = int(score_str.split(' ')[0])
    except Exception as e:
        logger.error(str(e))
    if score >= 5:
        return True
    return False

def kimi_is_question(query):
    SCORING_QUESTION_TEMPLATE = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句或在向其他人问问题，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    prompt = SCORING_QUESTION_TEMPLATE.format(query)
    if prompt is None or len(prompt) == 0:
        return False
    messages = [{'role': 'system', 'content': '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'}, {'role': 'user', 'content': prompt}]
    API_KEY = os.getenv('MOONSHOT_API_KEY')
    if API_KEY is None or len(API_KEY) < 1:
        assert 'moonshot api key not set'
    client = OpenAI(api_key=API_KEY, base_url='https://api.moonshot.cn/v1')
    try:
        completion = client.chat.completions.create(model='moonshot-v1-8k', messages=messages, temperature=0.0)
        relation = completion.choices[0].message.content
        filtered_relation = ''.join([c for c in relation if c.isdigit()])
        try:
            score_str = re.sub('[^\\d]', ' ', filtered_relation).strip()
            score = int(score_str.split(' ')[0])
            if score >= 5:
                return True
        except Exception as e:
            logger.error(str(e))
    except Exception as e:
        return str(e)
    return False

def get_score(relation: str, default=0):
    score = default
    filtered_relation = ''.join([c for c in relation if c.isdigit()])
    try:
        score_str = re.sub('[^\\d]', ' ', filtered_relation).strip()
        score = int(score_str.split(' ')[0])
    except Exception as e:
        logger.warning('primitive is_truth: {}, use default value {}'.format(str(e), default))
    return score

def get_score(relation: str, default=0):
    score = default
    filtered_relation = ''.join([c for c in relation if c.isdigit()])
    try:
        score_str = re.sub('[^\\d]', ' ', filtered_relation).strip()
        score = int(score_str.split(' ')[0])
    except Exception as e:
        logger.warning('primitive is_truth: {}, use default value {}'.format(str(e), default))
    return score

def openxlab_security(query: str, retry=1):
    life = 0
    while life < retry:
        try:
            headers = {'Content-Type': 'application/json'}
            data = {'bizId': str('antiseed' + str(time.time())), 'contents': [query], 'scopes': [], 'vendor': 1}
            resp = requests.post('https://openxlab.org.cn/gw/checkit/api/v1/audit/text', data=json.dumps(data), headers=headers)
            logger.debug((resp, resp.content))
            json_obj = json.loads(resp.content)
            items = json_obj['data']
            block = False
            for item in items:
                label = item['label']
                if label is not None and label in ['porn', 'politics']:
                    suggestion = item['suggestion']
                    if suggestion == 'block':
                        logger.debug(items)
                        block = True
                        break
            if block:
                return False
            return True
        except Exception as e:
            logger.debug(e)
            life += 1
            randval = random.randint(1, int(pow(2, life)))
            time.sleep(randval)
    return False

class LarkAgent:

    @classmethod
    async def parse_req(cls, request: Request) -> RawRequest:
        headers = dict(request.headers)
        req = RawRequest()
        req.uri = request.url.path
        req.body = await request.body()
        req.headers = {}
        for k, v in headers.items():
            if USER_AGENT.lower() == k.lower():
                req.headers[USER_AGENT] = v
            elif AUTHORIZATION.lower() == k.lower():
                req.headers[AUTHORIZATION] = v
            elif X_TT_LOGID.lower() == k.lower():
                req.headers[X_TT_LOGID] = v
            elif X_REQUEST_ID.lower() == k.lower():
                req.headers[X_REQUEST_ID] = v
            elif CONTENT_TYPE.lower() == k.lower():
                req.headers[CONTENT_TYPE] = v
            elif Content_Disposition.lower() == k.lower():
                req.headers[Content_Disposition] = v
            elif LARK_REQUEST_TIMESTAMP.lower() == k.lower():
                req.headers[LARK_REQUEST_TIMESTAMP] = v
            elif LARK_REQUEST_NONCE.lower() == k.lower():
                req.headers[LARK_REQUEST_NONCE] = v
            elif LARK_REQUEST_SIGNATURE.lower() == k.lower():
                req.headers[LARK_REQUEST_SIGNATURE] = v
        return req

    @classmethod
    def parse_rsp(cls, response: RawResponse) -> Response:
        return Response(status_code=response.status_code, content=str(response.content, UTF_8), headers=response.headers)

    @classmethod
    def get_event_handler(cls):
        return lark.EventDispatcherHandler.builder(HuixiangDouEnv.get_lark_encrypt_key(), HuixiangDouEnv.get_lark_verification_token(), lark.LogLevel.DEBUG).register_p2_im_message_receive_v1(cls._on_im_message_received).build()

    @classmethod
    def _on_im_message_received(cls, data: P2ImMessageReceiveV1):
        msg = data.event.message
        chat_id = msg.chat_id
        message_id = msg.message_id
        app_id = data.header.app_id
        app_secret = QaLibCache.get_lark_info_by_app_id(app_id)
        if not app_secret:
            logger.error(f'[lark] app_id: {app_id} not record, omit lark message callback')
            return
        client = cls._get_lark_client(app_id, app_secret)
        chat_name = cls._get_chat_name(chat_id, client)
        if not chat_name:
            logger.error(f'[lark] app_id: {app_id} get group name failed, omit lark message callback')
            return
        suffix = qalib.get_suffix_by_name(chat_name)
        if not suffix:
            logger.error(f'[lark] app_id: {app_id}, name: {chat_name} get suffix failed, omit lark message callback')
            return
        feature_store_id = QaLibCache.get_qalib_feature_store_id_by_suffix(suffix)
        if not feature_store_id:
            return
        hxd_info = QaLibCache.get_qalib_info(feature_store_id)
        if not hxd_info:
            logger.error(f'[lark] app_id: {app_id}, name: {chat_name} get feature store failed, omit lark message callback')
            return
        ChatCache.mark_agent_used(app_id, ChatType.LARK)
        if msg.root_id or msg.parent_id:
            logger.debug(f'[lark] app_id: {app_id}, name: {chat_name} got reply message, omit')
            return
        content = msg.content
        mentions = msg.mentions
        lark_content = cls._parse_lark_content(content, mentions)
        if not lark_content:
            logger.debug(f'[lark] app_id: {app_id}, name: {chat_name}, content: {content} omit')
            return
        query_id = None
        chat_svc = ChatService(None, None, hxd_info)
        if len(lark_content.images) > 0:
            query_id = chat_svc.generate_query_id(lark_content.content)
            for index in range(len(lark_content.images)):
                image_store_path = chat_svc.gen_image_store_path(query_id, str(index), ChatType.LARK)
                if cls._store_image(client, message_id, lark_content.images[index], image_store_path):
                    lark_content.images[index] = image_store_path
        chat_detail = LarkChatDetail(appId=app_id, appSecret=app_secret, messageId=msg.message_id)
        unique_id = data.event.sender.sender_id.open_id + '@' + chat_id
        chat_svc.chat_by_agent(lark_content, ChatType.LARK, chat_detail, unique_id, query_id)

    @classmethod
    def _get_chat_name(cls, chat_id: str, client: lark.client) -> Union[str, None]:
        request = GetChatRequest.builder().chat_id(chat_id).build()
        response = client.im.v1.chat.get(request)
        if not response.success():
            logger.error(f'[lark] get chat: {chat_id} info failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}')
            return None
        try:
            return response.data.name
        except:
            logger.error(f'[lark] get chat: {chat_id} name failed, data: {response.data}')
            return None

    @classmethod
    def _get_lark_client(cls, app_id: str, app_secret: str) -> lark.client:
        return lark.Client.builder().app_id(app_id).app_secret(app_secret).log_level(HuixiangDouEnv.get_lark_log_level()).build()

    @classmethod
    def _parse_lark_content(cls, content: str, mentions: List[MentionEvent]) -> Union[ChatRequestBody, None]:
        if not content or len(content) == 0:
            return None
        lark_json = json.loads(content)
        content_type = LarkContentType.NORMAL_TEXT
        if 'text' in lark_json:
            text = lark_json.get('text')
            if '@_user' in text:
                content_type = cls._get_content_type_when_at_user_exists(mentions)
            elif '@_all' in text:
                content_type = LarkContentType.AT_ALL_TEXT
        elif len(lark_json) == 1 and 'image_key' in lark_json:
            content_type = LarkContentType.IMAGE
        else:
            content_type = LarkContentType.OTHER
        process_flag = cls._check_should_process(content_type)
        if not process_flag:
            logger.debug(f'[lark] content: {content} has content_type: {content_type}, omit')
            return None
        if content_type == LarkContentType.IMAGE:
            image_key = lark_json.get('image_key')
            return ChatRequestBody(images=[image_key])
        else:
            text = lark_json.get('text')
            if content_type != LarkContentType.NORMAL_TEXT:
                text = re.sub('@_user_\\d+', '', text)
                text = re.sub('@_all\\d', '', text)
            return ChatRequestBody(content=text)

    @classmethod
    def _check_should_process(cls, t: LarkContentType) -> bool:
        return t == LarkContentType.AT_BOT_TEXT or t == LarkContentType.NORMAL_TEXT or t == LarkContentType.AT_ALL_TEXT or (t == LarkContentType.IMAGE)

    @classmethod
    def _get_content_type_when_at_user_exists(cls, mentions: List[MentionEvent]) -> LarkContentType:
        if not mentions or len(mentions) == 0:
            return LarkContentType.AT_OTHER_PERSON_TEXT
        for item in mentions:
            if not item.id.user_id or len(item.id.user_id) == 0:
                return LarkContentType.AT_BOT_TEXT
        return LarkContentType.AT_OTHER_PERSON_TEXT

    @classmethod
    def _store_image(cls, client: lark.client, message_id: str, image_key: str, path: str) -> bool:
        body = GetMessageResourceRequest.builder().message_id(message_id).file_key(image_key).build()
        response = client.im.v1.message_resource.get(body)
        if not response.success():
            logger.error(f'[lark] get image: {image_key} info failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}')
            return False
        if response.file:
            with open(path, mode='wb') as fout:
                fout.write(response.file.read())
            return True
        logger.error(f'[lark] get image: {image_key} stream empty, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}')
        return False

    @classmethod
    async def response_callback(cls, chat_info: ChatQueryInfo) -> bool:
        if not chat_info.detail:
            logger.error(f'[lark] invalid lark detail to send response, chat_info: {chat_info.model_dump()}')
            return False
        if chat_info.response.code != 0:
            logger.info(f'[lark] HuixiangDou inference error, detail: {chat_info.response.model_dump()}')
            return True
        lark_detail = json.dumps(chat_info.detail)
        lark_detail = LarkChatDetail(**json.loads(lark_detail))
        client = cls._get_lark_client(lark_detail.appId, lark_detail.appSecret)
        content_body = ReplyMessageRequestBody.builder().content(json.dumps({'text': chat_info.response.text})).msg_type('text').reply_in_thread(False).build()
        reply_body = ReplyMessageRequest.builder().message_id(lark_detail.messageId).request_body(content_body).build()
        response = await client.im.v1.message.areply(reply_body)
        if not response.success():
            logger.error(f'[lark] response: {chat_info.model_dump()} failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}')
            return False
        return True

@classmethod
def parse_rsp(cls, response: RawResponse) -> Response:
    return Response(status_code=response.status_code, content=str(response.content, UTF_8), headers=response.headers)

def parse_version_info(version_str: str) -> Tuple:
    """Parse version from a string.

    Args:
        version_str (str): A string represents a version info.

    Returns:
        tuple: A sequence of integer and string represents version.
    """
    _version_info = []
    for x in version_str.split('.'):
        if x.isdigit():
            _version_info.append(int(x))
        elif x.find('rc') != -1:
            patch_version = x.split('rc')
            _version_info.append(int(patch_version[0]))
            _version_info.append(f'rc{patch_version[1]}')
    return tuple(_version_info)

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

def _join_chunks(self, chunks: List[str], separator: str) -> Optional[str]:
    text = separator.join(chunks)
    if self._strip_whitespace:
        text = text.strip()
    if text == '':
        return None
    else:
        return text

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

def is_not_null_and_blank_str(self, content: str):
    """Is content empty."""
    if content is not None and content.strip():
        return True
    return False

def simple_uuid():
    return str(uuid4())[0:6]

def kimi_ocr(filepath, token):
    client = OpenAI(api_key=token, base_url='https://api.moonshot.cn/v1')
    try:
        file_object = client.files.create(file=Path(filepath), purpose='file-extract')
        json_str = client.files.content(file_id=file_object.id).text
        json_obj = json.loads(json_str)
        return json_obj['content']
    except Exception as e:
        logger.error(str(e))
    return ''

def extract_json_from_str(raw: str):
    raw = raw.strip()
    raw = raw.replace('”', '"')
    raw = raw.replace('“', '"')
    raw = raw.replace('"""', '"')
    raw = raw.replace('""', '"')
    raw = raw.replace('```json\n', '')
    raw = raw.replace('```', '')
    raw = raw.replace('，', ',')
    json_list = []
    try:
        start = raw.find('[')
        end = raw.rfind(']')
        json_str = raw[start:end + 1]
        json_obj = json.loads(json_str)
        if type(json_obj) is dict:
            for k in json_obj.keys():
                json_list = json_obj[k]
                break
        else:
            json_list = json_obj
    except Exception as e:
        logger.error(e)
        logger.error(raw)
    ret_list = []
    for item in json_list:
        if 'events' in item:
            ret_list += item['events']
        else:
            ret_list.append(item)
    return ret_list

def build_reply_text(code, query: str, reply: str, refs: list, max_len: int=20):
    table = Texttable()
    table.set_cols_valign(['t', 't', 't', 't'])
    table.header(['Query', 'State', 'Reply', 'References'])
    table.add_row([query, str(code), reply[0:max_len] + '..', ','.join(refs)])
    return table.draw()

def test_query(retriever: Retriever, sample: str=None):
    """Simple test response pipeline."""
    from texttable import Texttable
    if sample is not None:
        with open(sample) as f:
            real_questions = json.load(f)
        logger.add('logs/feature_store_query.log', rotation='4MB')
    else:
        real_questions = ['百草园里有啥？', 'how to use std::vector ?']
    table = Texttable()
    table.set_cols_valign(['t', 't', 't', 't'])
    table.header(['Query', 'State', 'Chunks', 'References'])
    for example in real_questions:
        example = example[0:400]
        chunks, context, refs, context_texts = retriever.query(example)
        if chunks:
            table.add_row([example, 'Accepted', chunks[0:100] + '..', ','.join(refs)])
        else:
            table.add_row([example, 'Rejected', 'None', 'None'])
        empty_cache()
    logger.info('\n' + table.draw())
    empty_cache()

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

class Record:

    def __init__(self, fsid: str):
        self.records = []
        self.fsid = fsid
        if os.path.exists('record.txt'):
            with open('record.txt') as f:
                for line in f:
                    self.records.append(line.strip())

    def is_processed(self):
        if self.fsid in self.records:
            return True
        return False

    def mark_as_processed(self):
        with open('record.txt', 'a') as f:
            f.write(self.fsid)
            f.write('\n')

def __init__(self, fsid: str):
    self.records = []
    self.fsid = fsid
    if os.path.exists('record.txt'):
        with open('record.txt') as f:
            for line in f:
                self.records.append(line.strip())

def generate():
    """Test generate."""
    messages = [{'role': 'system', 'content': '你是一个语文专家，擅长对句子的结构进行分析'}, {'role': 'user', 'content': prompt}]
    whole_input = str(messages)
    print(whole_input)
    try:
        completion = client.chat.completions.create(model='kimi-k2-0711-preview', messages=messages, temperature=0.1, n=5)
    except Exception as e:
        return (prompt, str(e))
    results = []
    for choice in completion.choices:
        results.append(choice.message.content)
    return (prompt, results)

def generate(prompt: str):
    """Test generate."""
    messages = [{'role': 'system', 'content': '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'}, {'role': 'user', 'content': prompt}]
    try:
        completion = client.chat.completions.create(model='moonshot-v1-128k', messages=messages, temperature=0.3)
    except Exception as e:
        return (prompt, str(e))
    return (prompt, completion.choices[0].message.content)

def generate_prompt_landmark(n_garbage=60000, seed=666):
    """Generates a text file and inserts an passkey at a random position."""
    from numpy import random
    rnd_state = random.get_state()
    random.seed(seed)
    n_garbage_prefix = random.randint(0, n_garbage)
    n_garbage_suffix = n_garbage - n_garbage_prefix
    task_description = 'There is an important info hidden inside a lot of irrelevant text. Find it and memorize them. I will quiz you about the important information there.'
    garbage = 'The grass is green. The sky is blue. The sun is yellow. Here we go. There and back again.'
    garbage_inf = ' '.join([garbage] * 384000)
    assert len(garbage_inf) >= n_garbage
    garbage_prefix = garbage_inf[:n_garbage_prefix]
    garbage_suffix = garbage_inf[:n_garbage_suffix]
    pass_key = random.randint(1, 192000)
    information_line = f'The pass key is {pass_key}. Remember it. {pass_key} is the pass key.'
    final_question = 'What is the pass key? The pass key is'
    lines = [task_description, garbage_prefix, information_line, garbage_suffix, final_question]
    random.set_state(rnd_state)
    return ('\n'.join(lines), str(pass_key))

def call_openai(model_name, prompt, history):
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
    for item in history:
        messages.append({'role': 'user', 'content': item[0]})
        messages.append({'role': 'system', 'content': item[1]})
    messages.append({'role': 'user', 'content': prompt})
    client = OpenAI(api_key='EMPTY', base_url='https://10.140.24.142:29500/v1')
    completion = client.chat.completions.create(model=model_name, messages=messages)
    return completion.choices[0].message.content

def call2():
    from openai import OpenAI
    openai_api_key = 'EMPTY'
    openai_api_base = 'http://10.140.24.142:29500/v1'
    client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)
    chat_response = client.chat.completions.create(model='../models/Qwen1.5-14B-Chat/', messages=[{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'Tell me a joke.'}])
    print('Chat response:', chat_response)

def export_onnx():
    model_id = '/workspace/models/text2vec-large-chinese'
    onnx_path = Path('onnx')
    model = ORTModelForFeatureExtraction.from_pretrained(model_id, from_transformers=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model.save_pretrained(onnx_path)
    tokenizer.save_pretrained(onnx_path)

def test_intention_scoring():
    client = OpenAI(api_key=api_key, base_url='https://api.stepfun.com/v1')
    question1 = '请用四字成语形容一个人皮肤光滑，就像渲染里开了抗锯齿。'
    question2 = '“不是盲审嘛，这对其他工作不太公平吧”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question3 = '“矩阵乘法有问题，我这段时间跑的模型怕不是都白跑了”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question4 = '“你这次卧还带玄关 真好”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question5 = '“我好气啊，为啥我赚不到这个钱”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question6 = '“要不，还是把豆哥从卷卷群移除吧”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question7 = '检查英文表达是否合适：Web portal is available on [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), you can build your own knowledge assistant, zero coding with WeChat and Feishu group.'
    questions = [question7]
    for question in questions:
        completion = client.chat.completions.create(model='step-1', temperature=0.2, messages=[{'role': 'system', 'content': '你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。在保证用户数据安全的前提下，你能对用户的问题和请求，作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容'}, {'role': 'user', 'content': question}])
        print(question)
        print(completion.choices[0].message)

def test_multimodal():
    question1 = ('这个截图里在说什么？', 'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/inside-mmpose.jpg')
    question2 = ('提取图片里的对话，结果用 json 表示。直接告诉我 json 结果，不要解释', 'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/inside-ncnn-group.jpg')
    question3 = ('回答这个截图里，第一条用户的问题。直接回答问题本身，不要解释，不要告诉我问题是什么。', 'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/inside-mmpose.jpg')
    question4 = ('图片里是什么群的二维码？干什么用的。不要解释，直接告诉我答案。', 'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/wechat.jpg')
    questions = [question4]
    client = OpenAI(api_key=api_key, base_url='https://api.stepfun.com/v1')
    for question in questions:
        completion = client.chat.completions.create(model='step-1v-32k', temperature=0.2, messages=[{'role': 'system', 'content': '你是由阶跃星辰提供的AI聊天助手，你除了擅长中文，英文，以及多种其他语言的对话以外，还能够根据用户提供的图片，对内容进行精准的内容文本描述。在保证用户数据安全的前提下，你能对用户的问题和请求，作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容'}, {'role': 'user', 'content': '你好呀!'}, {'role': 'user', 'content': [{'type': 'text', 'text': question[0]}, {'type': 'image_url', 'image_url': {'url': question[1]}}]}])
        print(completion.choices[0].message)

def parse_latest_plugin_call(text):
    plugin_name, plugin_args = ('', '')
    i = text.rfind('\nAction:')
    j = text.rfind('\nAction Input:')
    k = text.rfind('\nObservation:')
    if 0 <= i < j:
        if k < j:
            text = text.rstrip() + '\nObservation:'
        k = text.rfind('\nObservation:')
        plugin_name = text[i + len('\nAction:'):j].strip()
        plugin_args = text[j + len('\nAction Input:'):k].strip()
        text = text[:k]
    return (plugin_name, plugin_args, text)

def load_stopwords():
    sw = []
    with open('cn_en_stopwords.txt') as f:
        for line in f:
            if len(line.strip()) > 0:
                sw.append(line.strip())
    return sw

def process_data(documents: list, pid: int):
    t0 = time.time()
    new_words = load_newwords()
    for w in new_words:
        jieba.add_word(w, tag='n')
    stop_words = load_stopwords()
    print('{} start..'.format(pid))
    bad_patterns = [image_name, chapter2, chapter3]
    for filename, filepath in documents:
        d = ''
        with open(filepath) as f:
            d = f.read()
            head_length = int(len(d) * 0.8)
            d = d[0:head_length]
        cuts = [w.word for w in jp.cut(d)]
        filtered = []
        for c in cuts:
            c = c.strip()
            if c in stop_words:
                continue
            if 'images' == c:
                continue
            skip = False
            for bad_pattern in bad_patterns:
                if bad_pattern.match(c):
                    skip = True
                    break
            if skip:
                continue
            filtered.append(c)
        if len(filtered) < 1:
            continue
        new_content = ' '.join(filtered)
        if len(new_content) < 300:
            continue
        dirname = os.path.join('preprocess', str(pid))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        hashname = content_hash(new_content)
        outfilepath = os.path.join(dirname, hashname + '.md')
        with open('name_map.txt', 'a') as f:
            f.write('{}\t {}'.format(hashname, filepath))
            f.write('\n')
        with open(outfilepath, 'w') as f:
            f.write(new_content)
            f.flush()
    print('{} finish, timecost {}'.format(pid, time.time() - t0))

