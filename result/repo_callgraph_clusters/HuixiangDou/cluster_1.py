# Cluster 1

def randomize_labels(true_label):
    options = ['A', 'B', 'C']
    answers = ['不需要提取，信息完整', '需要提取', '不知道']
    random.shuffle(answers)
    correct_answer_index = answers.index('需要提取') if true_label == True else answers.index('不需要提取，信息完整')
    option_str = ''
    for index in range(len(options)):
        option_str += '{}:{}  '.format(options[index], answers[index])
    option_str = option_str.strip()
    gt_str = '{}:{}'.format(options[correct_answer_index], answers[correct_answer_index])
    return (option_str, gt_str)

def metric(llm_type: str, gt_filepath: str='groups/input.jsonl', dt_filepath: str='groups/output.jsonl'):
    gts = []
    dts = []
    unknow_count = 0
    with open(gt_filepath) as gt:
        for line in gt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue
            cr_need_gt = json_obj['cr_need_gt']
            gts.append(cr_need_gt)
    with open(dt_filepath) as dt:
        for line in dt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue
            dt = json_obj['{}_cr_need'.format(llm_type)]
            if 'yes' == dt:
                dts.append(True)
            elif 'no' == dt:
                dts.append(False)
            else:
                dt = dt.replace(' ', '')
                dt = dt.replace('\n', '')
                if 'ab' in dt or 'abc' in dt:
                    unknow_count += 1
                    dts.append(bool(1 - cr_need_gt))
                elif '答案：b' in dt or '选：b' in dt or '答案是：b' in dt:
                    dts.append(True)
                elif '答案是：a' in dt or '答案是"不需要"' in dt or '答案是：不需要' in dt or ('答案：不需要' in dt) or ('选项结果：不需要' in dt) or '结果选项：不需要':
                    dts.append(False)
                else:
                    unknow_count += 1
                    print(dt)
                    dts.append(bool(1 - cr_need_gt))
    assert len(gts) == len(dts)
    precision = precision_score(gts, dts)
    recall = recall_score(gts, dts)
    f1 = f1_score(gts, dts)
    logger.info('{}: {} {} {} {}'.format(llm_type, precision, recall, f1, unknow_count))

def traverse(target):
    if os.path.isfile(target):
        analyze_doc(os.path.dirname(target), target)
        return
    for home, dirs, files in os.walk(target):
        for filename in files:
            if filename.endswith('.md'):
                path = os.path.join(home, filename)
                if os.path.islink(path) is False:
                    if 'copy_' in path:
                        continue
                    analyze_doc(home, path)

def test_bm25_dump():
    corpus = ['Hello there good man!', 'It is quite windy in London', 'How is the weather today?']
    chunks = []
    for content in corpus:
        c = Chunk(content_or_path=content)
        chunks.append(c)
    bm25 = BM25Okapi()
    bm25.save(chunks, './')

def build_feature_store(cache: CacheRetriever, payload: types.SimpleNamespace):
    abs_base = payload.file_abs_base
    fs_id = payload.feature_store_id
    path_list = []
    files = []
    file_opr = FileOperation()
    for filename in payload.file_list:
        abs_path = os.path.join(abs_base, filename)
        _type = file_opr.get_type(abs_path)
        files.append(FileName(root=abs_base, filename=filename, _type=_type))
    BASE = feature_store_base_dir()
    workdir = os.path.join(BASE, fs_id, 'workdir')
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    configpath = os.path.join(BASE, fs_id, 'config.ini')
    if not os.path.exists(configpath):
        template_file = 'config.ini'
        if not os.path.exists(template_file):
            raise Exception(f'{template_file} not exist')
        shutil.copy(template_file, configpath)
    with open(os.path.join(BASE, fs_id, 'desc'), 'w', encoding='utf8') as f:
        f.write(payload.name)
    fs = FeatureStore(config_path=configpath, embedder=cache.embedder)
    task_state = partial(callback_task_state, feature_store_id=fs_id, _type=TaskCode.FS_ADD_DOC.value)
    fs.initialize(files=files, work_dir=workdir, ner_file=None)
    files_state = []
    success_cnt = 0
    fail_cnt = 0
    skip_cnt = 0
    for file in files:
        files_state.append({'file': str(file.basename), 'status': bool(file.state), 'desc': str(file.reason)})
        if file.state:
            success_cnt += 1
        elif file.reason == 'skip':
            skip_cnt += 1
        else:
            fail_cnt += 1
    if success_cnt == len(files):
        task_state(code=ErrorCode.SUCCESS.value, state=ErrorCode.SUCCESS.describe(), files_state=files_state)
    elif success_cnt == 0:
        task_state(code=ErrorCode.FAILED.value, state='无文件被处理', files_state=files_state)
    else:
        state = f'完成{success_cnt}个文件，跳过{skip_cnt}个，{fail_cnt}个处理异常。请确认文件格式。'
        task_state(code=ErrorCode.SUCCESS.value, state=state, files_state=files_state)

def update_sample(cache: CacheRetriever, payload: types.SimpleNamespace):
    positive = payload.positive
    negative = payload.negative
    fs_id = payload.feature_store_id
    task_state = partial(callback_task_state, feature_store_id=fs_id, _type=TaskCode.FS_UPDATE_SAMPLE.value)
    if len(positive) < 1 or len(negative) < 1:
        task_state(code=ErrorCode.BAD_PARAMETER.value, state='正例为空。请根据真实用户问题，填写正例；同时填写几句场景无关闲聊作负例')
        return
    for idx in range(len(positive)):
        if len(positive[idx]) < 1:
            positive[idx] += '.'
    for idx in range(len(negative)):
        if len(negative[idx]) < 1:
            negative[idx] += '.'
    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')
    db_dense = os.path.join(workdir, 'db_dense')
    if not os.path.exists(workdir) or not os.path.exists(configpath) or (not os.path.exists(db_dense)):
        task_state(code=ErrorCode.INTERNAL_ERROR.value, state='知识库未建立或中途异常，已自动反馈研发。请重新建立知识库。')
        return
    retriever = cache.get(fs_id=fs_id, config_path=configpath, work_dir=workdir)
    retriever.update_throttle(config_path=configpath, good_questions=positive, bad_questions=negative)
    del retriever
    task_state(code=ErrorCode.SUCCESS.value, state=ErrorCode.SUCCESS.describe())

def update_pipeline(payload: types.SimpleNamespace):
    fs_id = payload.feature_store_id
    token = payload.web_search_token
    task_state = partial(callback_task_state, feature_store_id=fs_id, _type=TaskCode.FS_UPDATE_PIPELINE.value)
    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')
    if not os.path.exists(workdir) or not os.path.exists(configpath):
        task_state(code=ErrorCode.INTERNAL_ERROR.value, state='知识库未建立或中途异常，已自动反馈研发。请重新建立知识库。')
        return
    with open(configpath, encoding='utf8') as f:
        config = pytoml.load(f)
    config['web_search']['x_api_key'] = token
    with open(configpath, 'w', encoding='utf8') as f:
        pytoml.dump(config, f)
    task_state(code=ErrorCode.SUCCESS.value, state=ErrorCode.SUCCESS.describe())

def get_store_dir(feature_store_id: str) -> Union[str, None]:
    if not feature_store_id:
        return None
    try:
        crt_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(os.path.dirname(crt_path))
        qa_path = os.path.join(parent_path, f'qa/{feature_store_id}')
        os.makedirs(qa_path, exist_ok=True)
        return qa_path
    except Exception as e:
        logger.error(f'{e}')
        return None

class ChatService:

    def __init__(self, request: Request, response: Response, hxd_info: QalibInfo):
        self.hxd_info = hxd_info
        self.request = request
        self.response = response

    async def chat_online(self, body: ChatRequestBody):
        feature_store_id = self.hxd_info.featureStoreId
        query_id = self.generate_query_id(body.content)
        logger.info(f'[chat-request]/online feature_store_id: {feature_store_id}, content: {body.content}, query_id: {query_id}')
        images_path = []
        if len(body.images) > 0:
            images_path = self._store_images(body.images, query_id)
            if len(images_path) == 0:
                return standard_error_response(biz_constant.ERR_CHAT)
        task = HxdTask(type=HxdTaskType.CHAT, payload=HxdTaskPayload(feature_store_id=feature_store_id, query_id=query_id, content=body.content, history=body.history, images=images_path))
        if HuixiangDouTask().updateTask(task):
            chat_query_info = ChatQueryInfo(featureStoreId=feature_store_id, queryId=query_id, request=ChatRequestBody(content=body.content, images=images_path, history=body.history, type=ChatType.ONLINE))
            ChatCache.set_query_request(query_id, feature_store_id, chat_query_info)
            ChatCache.mark_unique_inference_user(feature_store_id, ChatType.ONLINE)
            return BaseBody(data=ChatOnlineResponseBody(queryId=query_id))
        return standard_error_response(biz_constant.ERR_CHAT)

    async def fetch_response(self, body: ChatOnlineResponseBody):
        feature_store_id = self.hxd_info.featureStoreId
        info = ChatCache().get_query_info(body.queryId, feature_store_id)
        if not info:
            return standard_error_response(biz_constant.ERR_NOT_EXIST_CHAT)
        if not info.response:
            return standard_error_response(biz_constant.CHAT_STILL_IN_QUEUE)
        return BaseBody(data=info.response)

    def chat_by_agent(self, body: ChatRequestBody, t: ChatType, chat_detail: object, user_unique_id: str, query_id: str=None) -> bool:
        feature_store_id = self.hxd_info.featureStoreId
        if not query_id:
            query_id = self.generate_query_id(body.content)
        logger.info(f'[chat-request]/agent feature_store_id: {feature_store_id}, content: {body.content}, query_id: {query_id}, type:{t}')
        task = HxdTask(type=HxdTaskType.CHAT, payload=HxdTaskPayload(feature_store_id=feature_store_id, query_id=query_id, content=body.content, history=body.history, images=body.images))
        if HuixiangDouTask().updateTask(task):
            chat_query_info = ChatQueryInfo(featureStoreId=feature_store_id, queryId=query_id, request=ChatRequestBody(content=body.content, images=body.images, history=body.history), type=t, detail=chat_detail)
            ChatCache.set_query_request(query_id, feature_store_id, chat_query_info)
            ChatCache.mark_unique_inference_user(user_unique_id, t)
            return True
        return False

    def generate_query_id(self, content):
        feature_store_id = self.hxd_info.featureStoreId
        raw = feature_store_id + content[-8:] + str(time.time())
        h = hashlib.sha3_512()
        h.update(raw.encode('utf-8'))
        q = h.hexdigest()
        return q[0:8]

    def _store_images(self, images, query_id) -> List[str]:
        feature_store_id = self.hxd_info.featureStoreId
        image_store_dir = get_store_dir(feature_store_id)
        if not image_store_dir:
            logger.error(f'get store dir failed for: {feature_store_id}')
            return []
        image_store_dir += '/images/'
        os.makedirs(image_store_dir, exist_ok=True)
        ret = []
        index = 0
        for image in images:
            try:
                while len(image) % 4 != 0:
                    image += '='
                [image_format, image] = detect_base64_image_suffix(image)
                if image_format == Image.INVALID:
                    logger.error(f'invalid image format, query_id: {query_id}')
                    return []
                decoded_image = base64.b64decode(image)
            except binascii.Error:
                logger.error(f'invalid base64 encoded image, query_id: {query_id}')
                return []
            store_path = image_store_dir + query_id[-8:] + '_' + str(index) + '.' + image_format.value
            with open(store_path, 'wb') as f:
                f.write(decoded_image)
            ret.append(store_path)
        return ret

    def gen_image_store_path(self, query_id, name: str, agent: ChatType) -> Union[str, None]:
        feature_store_id = self.hxd_info.featureStoreId
        image_store_dir = get_store_dir(feature_store_id)
        if not image_store_dir:
            logger.error(f'get store dir failed for: {feature_store_id}')
            return None
        image_store_dir += '/images/'
        os.makedirs(name=image_store_dir, exist_ok=True)
        return image_store_dir + agent.name + query_id[-8:] + '_' + name

    async def case_feedback(self, body: ChatCaseFeedbackBody):
        feature_store_id = self.hxd_info.featureStoreId
        query_id = body.queryId
        query_info = ChatCache.get_query_info(query_id, feature_store_id)
        if not query_info:
            return standard_error_response(biz_constant.ERR_CHAT_CASE_FEEDBACK)
        return BaseBody() if ChatCache.update_case_feedback(feature_store_id, body.type, query_info.model_dump_json()) else standard_error_response(biz_constant.ERR_CHAT_CASE_FEEDBACK)

def _store_images(self, images, query_id) -> List[str]:
    feature_store_id = self.hxd_info.featureStoreId
    image_store_dir = get_store_dir(feature_store_id)
    if not image_store_dir:
        logger.error(f'get store dir failed for: {feature_store_id}')
        return []
    image_store_dir += '/images/'
    os.makedirs(image_store_dir, exist_ok=True)
    ret = []
    index = 0
    for image in images:
        try:
            while len(image) % 4 != 0:
                image += '='
            [image_format, image] = detect_base64_image_suffix(image)
            if image_format == Image.INVALID:
                logger.error(f'invalid image format, query_id: {query_id}')
                return []
            decoded_image = base64.b64decode(image)
        except binascii.Error:
            logger.error(f'invalid base64 encoded image, query_id: {query_id}')
            return []
        store_path = image_store_dir + query_id[-8:] + '_' + str(index) + '.' + image_format.value
        with open(store_path, 'wb') as f:
            f.write(decoded_image)
        ret.append(store_path)
    return ret

def gen_image_store_path(self, query_id, name: str, agent: ChatType) -> Union[str, None]:
    feature_store_id = self.hxd_info.featureStoreId
    image_store_dir = get_store_dir(feature_store_id)
    if not image_store_dir:
        logger.error(f'get store dir failed for: {feature_store_id}')
        return None
    image_store_dir += '/images/'
    os.makedirs(name=image_store_dir, exist_ok=True)
    return image_store_dir + agent.name + query_id[-8:] + '_' + name

def gen_random_string(length=4) -> str:
    """
    :param length: random string's length
    :return: a string with the given length, includes only A-Za-z0-9
    """
    chars = string.ascii_letters + string.digits
    return ''.join((random.choice(chars) for _ in range(length)))

def safe_join(directory: str, path: str) -> str:
    """Safely path to a base directory to avoid escaping the base directory.
    Borrowed from: werkzeug.security.safe_join.

    @param directory:
    @param path:
    """
    _os_alt_seps: List[str] = [sep for sep in [os.path.sep, os.path.altsep] if sep is not None and sep != '/']
    if path == '':
        raise HTTPException(status_code=400, detail='path is empty')
    filename = os.path.normpath(path)
    full_path = os.path.join(directory, filename)
    if any((sep in filename for sep in _os_alt_seps)) or os.path.isabs(filename) or filename == '..' or filename.startswith('../') or os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail='path is illegal')
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail='path is not existed')
    return full_path

def _split_text_with_regex(text: str, separator: str, keep_separator: Union[bool, Literal['start', 'end']]) -> List[str]:
    if separator:
        if keep_separator:
            _splits = re.split(f'({separator})', text)
            splits = [_splits[i] + _splits[i + 1] for i in range(0, len(_splits) - 1, 2)] if keep_separator == 'end' else [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]
            if len(_splits) % 2 == 0:
                splits += _splits[-1:]
            splits = splits + [_splits[-1]] if keep_separator == 'end' else [_splits[0]] + splits
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s != '']

def nested_split_markdown(filepath: str, text: str, chunksize: int=832, metadata: dict={}):
    """First split by header, then by length.

    `header` should be part of content.
    """
    head_splitter = MarkdownHeaderTextSplitter()
    chunks = head_splitter.create_chunks(text, metadata=metadata)
    text_chunks = []
    image_chunks = []
    text_ref_splitter = MarkdownTextRefSplitter(chunk_size=chunksize)
    md_image_pattern = re.compile('\\[([^\\]]+)\\]\\(([a-zA-Z0-9:/._~#-]+)?\\)')
    html_image_pattern = re.compile('<img\\s+[^>]*?src=["\\\']([^"\\\']*)["\\\'][^>]*>')
    file_opr = FileOperation()
    for chunk in chunks:
        header = ''
        if 'Header 1' in chunk.metadata:
            header += chunk.metadata['Header 1']
        if 'Header 2' in chunk.metadata:
            header += ' '
            header += chunk.metadata['Header 2']
        if 'Header 3' in chunk.metadata:
            header += ' '
            header += chunk.metadata['Header 3']
        if len(chunk.content_or_path) > chunksize:
            subchunks = text_ref_splitter.create_chunks([chunk.content_or_path], [chunk.metadata])
            for subchunk in subchunks:
                if len(subchunk.content_or_path) >= 10:
                    subchunk.content_or_path = '{} {}'.format(header, subchunk.content_or_path.lower())
                    text_chunks.append(subchunk)
        elif len(chunk.content_or_path) >= 10:
            content = '{} {}'.format(header, chunk.content_or_path.lower())
            text_chunks.append(Chunk(content, metadata))
        dirname = os.path.dirname(filepath)
        image_paths = []
        for match in md_image_pattern.findall(chunk.content_or_path):
            image_paths.append(match[1])
        for match in html_image_pattern.findall(chunk.content_or_path):
            image_paths.append(match)
        for image_path in image_paths:
            if file_opr.get_type(image_path) != 'image':
                continue
            if image_path.startswith('http'):
                continue
            if not os.path.isabs(image_path):
                image_path = os.path.join(dirname, image_path)
            if os.path.exists(image_path):
                c = Chunk(content_or_path=image_path, metadata=metadata.copy(), modal='image')
                image_chunks.append(c)
            else:
                pass
    return text_chunks + image_chunks

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

def scan_dir(self, repo_dir: str):
    files = []
    for root, _, filenames in os.walk(repo_dir):
        for filename in filenames:
            _type = self.get_type(filename)
            if _type is not None:
                files.append(FileName(root=root, filename=filename, _type=_type))
    return files

def get_pdf_files(directory):
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.abspath(os.path.join(root, file)))
    return pdf_files

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

def __del__(self):
    self.cursor.close()
    self.conn.close()

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

class KnowledgeGraph:

    def __init__(self, config_path: str, override: bool=False, retry: int=1):
        self.llm = LLM(config_path=config_path)
        self.retry = retry
        self.nodes = []
        self.relations = []
        self.chunksize = 2048
        self.prompt_template = '\n你是一位语言专家，现在要做实体识别任务（NER），请阅读以下内容，以 json 形式输出实体。直接给出结果不要解释。\n输出示例：\n[{"entity":"实体","type":"类型"}]\n\n以下是阅读内容：\n'
        self.md_pattern = re.compile('\\[([^\\]]+)\\]\\(([a-zA-Z0-9:/._~#-]+)?\\)')
        self.file_opr = FileOperation()
        self.override = override
        with open(config_path) as f:
            config = pytoml.load(f)
            self.kg_work_dir = os.path.join(config['feature_store']['work_dir'], 'kg')
            if not os.path.exists(self.kg_work_dir):
                os.makedirs(self.kg_work_dir)
        self.nodes_path = os.path.join(self.kg_work_dir, 'kg_nodes.jsonl')
        self.relations_path = os.path.join(self.kg_work_dir, 'kg_relations.jsonl')
        self.gpickle_path = os.path.join(self.kg_work_dir, 'kg.gpickle')
        self.graph = None

    def build(self, repodir: str):
        logger.info('multi-modal knowledge graph retrieval is experimental, only support markdown format.')
        proc_files = []
        processed = []
        processed_path = os.path.join(self.kg_work_dir, 'processed.txt')
        if os.path.exists(processed_path):
            with open(processed_path) as f:
                for path in f:
                    processed.append(path.strip())
        for root, dirs, files in os.walk(repodir):
            for file in files:
                if '.github' in root:
                    continue
                file_type = self.file_opr.get_type(file)
                if file_type not in ['md']:
                    continue
                abspath = os.path.join(root, file)
                if abspath in processed:
                    logger.info(f'skip {abspath}')
                    continue
                proc_files.append((abspath, file_type))
        if self.override:
            if os.path.exists(self.nodes_path):
                os.remove(self.nodes_path)
            if os.path.exists(self.relations_path):
                os.remove(self.relations_path)
        for abspath, file_type in tqdm(proc_files):
            if file_type == 'md':
                self.build_md(abspath)
            with open(processed_path, 'a') as f:
                f.write(abspath)
                f.write('\n')
            with open(self.nodes_path, 'a') as f:
                for node in self.nodes:
                    f.write(node_to_jsonstr(node))
                    f.write('\n')
            self.nodes = []
            with open(self.relations_path, 'a') as f:
                for relation in self.relations:
                    f.write(relation_to_jsonstr(relation))
                    f.write('\n')
            self.relations = []

    async def build_md_chunk(self, md_node: Node, abspath: str):
        """Parse markdown chunk to nodes and relations.

        LLM NER with retry policy.
        """
        items = []
        for _ in range(self.retry):
            llm_raw_text = await self.llm.chat(prompt=self.prompt_template + md_node.data)
            items += extract_json_from_str(raw=llm_raw_text)
        if len(items) < 1:
            logger.warning('parse llm_raw_text failed. {}'.format(llm_raw_text))
            return
        for item in items:
            try:
                entity = item['entity']
                _type = item['type']
            except Exception as e:
                logger.error(e)
                logger.error(item)
                continue
            self.nodes.append(Node(uuid=entity, _type=KGType.KEYWORD))
            self.relations.append(Relation(entity, md_node.uuid, _type))
        matches = self.md_pattern.findall(md_node.data)
        for match in matches:
            uri = match[1]
            if self.file_opr.get_type(uri) != 'image':
                continue
            if not uri.startswith('http'):
                uri = os.path.join(os.path.dirname(abspath), uri)
            uuid, image_path = self.file_opr.save_image(uri=uri, outdir=self.kg_work_dir)
            if image_path is not None:
                self.nodes.append(Node(uuid=uuid, _type=KGType.IMAGE, data=image_path))
                self.relations.append(Relation(uuid, md_node.uuid, 'file'))

    def build_md(self, abspath: str):
        """Load markdown and split, build nodes and relationship."""
        content = ''
        with open(abspath) as f:
            content = f.read()
        splits = content.split('\n')
        chunk = ''
        pageid = 0
        md_node = Node(_type=KGType.MARKDOWN, data=abspath)
        self.nodes.append(md_node)

        def add_chunk(md_node: Node, pageid: int, text: str):
            chunk_node = Node(_type=KGType.CHUNK, data=text)
            self.nodes.append(chunk_node)
            self.build_md_chunk(md_node=chunk_node, abspath=abspath)
            self.relations.append(Relation(md_node.uuid, chunk_node.uuid, 'page{}'.format(pageid)))
        for split in splits:
            if len(split) >= self.chunksize:
                if len(chunk) > 0:
                    add_chunk(md_node=md_node, pageid=pageid, text=chunk)
                    pageid += 1
                    chunk = ''
                add_chunk(md_node=md_node, pageid=pageid, text=split)
                pageid += 1
                continue
            if len(chunk) + len(split) < self.chunksize:
                chunk = chunk + '\n' + split
                continue
            add_chunk(md_node=md_node, pageid=pageid, text=chunk)
            pageid += 1
            chunk = split
        if len(chunk) > 0:
            add_chunk(md_node=md_node, pageid=pageid, text=chunk)

    def dump_neo4j(self, uri: str, user: str, passwd: str):
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, passwd))
        with driver.session() as session:
            session.run('MATCH (n) DETACH DELETE n')
        nodes = dict()
        with open(self.nodes_path) as f:
            for json_str in f:
                node = json.loads(json_str)
                nodes[node['uuid']] = node
        add_node_query_with_props = '        MERGE (n:`%s` {`id`: $value })\n        ON CREATE SET n+=$props\n        '
        with driver.session() as session:
            for node in tqdm(nodes.values()):
                nodel_label = node['_type']
                query = add_node_query_with_props % nodel_label
                session.run(query, {'value': node['uuid']}, props={'type': node['_type'], 'data': node['data']})
        relations = []
        with open(self.relations_path) as f:
            for json_str in f:
                rel = json.loads(json_str)
                relations.append(rel)
        add_edge_query = '        MERGE (node1:`%s` {`id`: $node1 })\n        MERGE (node2:`%s` {`id`: $node2 })\n        MERGE (node1)-[r:`%s`]->(node2)\n        ON CREATE SET r=$props\n        '
        with driver.session() as session:
            for rel in tqdm(relations):
                _from = rel['_from']
                to = rel['to']
                label1 = nodes[_from]['_type']
                label2 = nodes[to]['_type']
                desc = rel['desc']
                if desc in ['file']:
                    relationship_type = desc
                elif desc.startswith('page'):
                    relationship_type = 'page'
                else:
                    relationship_type = 'attr'
                query = add_edge_query % (label1, label2, relationship_type)
                session.run(query, {'node1': _from, 'node2': to}, props={'desc': desc})

    def dump_networkx(self):
        """Convert to networkx and dump GraphML format."""
        if not os.path.exists(self.nodes_path):
            logger.error('nodes path not exist')
            return
        if not os.path.exists(self.relations_path):
            logger.error('relations path not exist')
            return
        with open(self.nodes_path) as f:
            for json_str in f:
                self.nodes.append(json.loads(json_str))
        with open(self.relations_path) as f:
            for json_str in f:
                self.relations.append(json.loads(json_str))
        G = nx.Graph()
        for node in self.nodes:
            G.add_nodes_from([(node['uuid'], {'type': node['_type'], 'data': node['data']})])
        for rel in self.relations:
            G.add_edge(rel['_from'], rel['to'], desc=rel['desc'])
        logger.debug('Loaded knowledge graph, number of nodes {}, number of edges {}'.format(G.number_of_nodes(), G.number_of_edges()))
        with open(self.gpickle_path, 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

    def is_available(self):
        """Check knowledge graph exist or not."""
        if os.path.exists(self.gpickle_path):
            return True
        return False

    def load(self):
        """Load knowledge graph."""
        if not os.path.exists(self.gpickle_path):
            logger.error('gpickle {} not exist.'.format(self.gpickle_path))
            return None
        with open(self.gpickle_path, 'rb') as f:
            self.graph = pickle.load(f)
        logger.debug('number of nodes {}, number of edges {}'.format(self.graph.number_of_nodes(), self.graph.number_of_edges()))

    def query_file_chunk_map(self, attr: str):
        ret = dict()
        G = self.graph
        for chunk in G.neighbors(attr):
            files = [nbr for nbr in G.neighbors(chunk) if 'page' in G.edges[chunk, nbr].get('desc')]
            for file in files:
                chunk_data = G.nodes[chunk].get('data')
                file_data = G.nodes[file].get('data')
                if file_data in ret:
                    ret[file_data].append(chunk_data)
                else:
                    ret[file_data] = [chunk_data]
        return ret

    async def retrieve(self, query: str):
        if self.graph is None:
            self.load()
        llm_raw_text = await self.llm.chat(prompt=self.prompt_template + query)
        items = extract_json_from_str(raw=llm_raw_text)
        if len(items) < 1:
            return []
        file_chunks = dict()
        for item in items:
            try:
                entity = item['entity']
                if not self.graph.has_node(entity):
                    continue
                file_chunks_on_entity = self.query_file_chunk_map(attr=entity)
                for k, v in file_chunks_on_entity.items():
                    if k in file_chunks:
                        file_chunks[k] += v
                    else:
                        file_chunks[k] = v
            except Exception as e:
                logger.error(e)
                logger.error(item)
                continue
        candidates = []
        for k, v in file_chunks.items():
            candidates.append({'path': k, 'chunks': v})
        candidates.sort(key=lambda x: len(x['chunks']))
        return candidates

def build(self, repodir: str):
    logger.info('multi-modal knowledge graph retrieval is experimental, only support markdown format.')
    proc_files = []
    processed = []
    processed_path = os.path.join(self.kg_work_dir, 'processed.txt')
    if os.path.exists(processed_path):
        with open(processed_path) as f:
            for path in f:
                processed.append(path.strip())
    for root, dirs, files in os.walk(repodir):
        for file in files:
            if '.github' in root:
                continue
            file_type = self.file_opr.get_type(file)
            if file_type not in ['md']:
                continue
            abspath = os.path.join(root, file)
            if abspath in processed:
                logger.info(f'skip {abspath}')
                continue
            proc_files.append((abspath, file_type))
    if self.override:
        if os.path.exists(self.nodes_path):
            os.remove(self.nodes_path)
        if os.path.exists(self.relations_path):
            os.remove(self.relations_path)
    for abspath, file_type in tqdm(proc_files):
        if file_type == 'md':
            self.build_md(abspath)
        with open(processed_path, 'a') as f:
            f.write(abspath)
            f.write('\n')
        with open(self.nodes_path, 'a') as f:
            for node in self.nodes:
                f.write(node_to_jsonstr(node))
                f.write('\n')
        self.nodes = []
        with open(self.relations_path, 'a') as f:
            for relation in self.relations:
                f.write(relation_to_jsonstr(relation))
                f.write('\n')
        self.relations = []

def is_available(self):
    """Check knowledge graph exist or not."""
    if os.path.exists(self.gpickle_path):
        return True
    return False

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

def load_queries(fsid: str):
    pwd = os.path.dirname(__file__)
    base = os.path.join(pwd, '..', 'queries')
    query_path = os.path.join(base, fsid + '.txt')
    if not os.path.exists(query_path):
        return []
    queries = []
    print(query_path)
    if fsid == '0000':
        with open(query_path) as f:
            for line in f:
                queries.append(line)
        return queries
    with open(query_path) as f:
        for line in f:
            queries = json.loads(line)
            break
    return queries

def process(param: tuple):
    fsid, filedir = param
    queries = load_queries(fsid=fsid)
    if len(queries) < 1:
        return
    r = Record(fsid=fsid)
    if r.is_processed():
        logger.info('skip {}'.format(fsid))
        return
    config_path = 'config.ini'
    cache = CacheRetriever(config_path=config_path)
    fs_init = FeatureStore(embedder=cache.embedder, config_path=config_path)
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=filedir)
    work_dir = os.path.join('workdir', fsid)
    fs_init.initialize(files=files, work_dir=work_dir)
    file_opr.summarize(files)
    del fs_init
    retriever = cache.get(config_path=config_path, work_dir=work_dir)
    if not os.path.exists('candidates'):
        os.makedirs('candidates')
    for query in queries:
        try:
            query = query[0:400]
            docs = retriever.compression_retriever.get_relevant_documents(query)
            candidates = []
            logger.info('{} docs count {}'.format(fsid, len(docs)))
            for doc in docs:
                data = {'content': doc.page_content, 'source': doc.metadata['read'], 'score': doc.metadata['relevance_score']}
                candidates.append(data)
            json_str = json.dumps({'query': query, 'candidates': candidates}, ensure_ascii=False)
            with open(os.path.join('candidates', fsid + '.jsonl'), 'a') as f:
                f.write(json_str)
                f.write('\n')
        except Exception as e:
            pdb.set_trace()
            print(e)
    r.mark_as_processed()

def load_dataset():
    text_labels = []
    with open(osp.join(osp.dirname(__file__), 'gt_good.txt')) as f:
        for line in f:
            text_labels.append((line, True))
    with open(osp.join(osp.dirname(__file__), 'gt_bad.txt')) as f:
        for line in f:
            text_labels.append((line, False))
    return text_labels

def calculate(config_path: str='config.ini'):
    kg = KnowledgeGraph(config_path=config_path, override=False)
    G = kg.load_networkx()
    if not G:
        logger.error('Knowledge graph not build, quit.')
        return
    text_labels = load_dataset()
    outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
    for text, label in tqdm(text_labels):
        result = kg.retrieve(G=G, query=text)
        json_str = json.dumps({'query': text, 'result': result, 'gt': label}, ensure_ascii=False)
        with open(outpath, 'a') as f:
            f.write(json_str)
            f.write('\n')

def summarize():
    outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
    for throttle in range(0, 40, 5):
        dts = []
        gts = []
        max_ref_cnts = []
        with open(outpath) as f:
            for line in f:
                json_obj = json.loads(line)
                gts.append(json_obj['gt'])
                if not json_obj['result']:
                    dts.append(False)
                elif len(json_obj['result']) <= throttle:
                    dts.append(False)
                else:
                    dts.append(True)
                    max_ref_cnts.append(len(json_obj['result']))
        f1 = f1_score(gts, dts)
        f1 = round(f1, 2)
        precision = precision_score(gts, dts)
        precision = round(precision, 2)
        recall = recall_score(gts, dts)
        recall = round(recall, 2)
        logger.info(('throttle, precision, recall, F1', throttle, precision, recall, f1))

class KnowledgeGraphScore:

    def __init__(self, level: int):
        outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
        self.scores = dict()
        with open(outpath) as f:
            for line in f:
                json_obj = json.loads(line)
                query = json_obj['query']
                score = 0.0
                result = json_obj['result']
                if result is not None and len(result) > level:
                    score = min(100, len(result) - level) / 100
                    print('query cnt score {} {} {}'.format(query, len(result), score))
                self.scores[query] = score

    def evaluate(self, query: str):
        return self.scores[query]

def __init__(self, level: int):
    outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
    self.scores = dict()
    with open(outpath) as f:
        for line in f:
            json_obj = json.loads(line)
            query = json_obj['query']
            score = 0.0
            result = json_obj['result']
            if result is not None and len(result) > level:
                score = min(100, len(result) - level) / 100
                print('query cnt score {} {} {}'.format(query, len(result), score))
            self.scores[query] = score

def load_dataset():
    text_labels = []
    with open(osp.join(osp.dirname(__file__), 'gt_good.txt')) as f:
        for line in f:
            text_labels.append((line, True))
    with open(osp.join(osp.dirname(__file__), 'gt_bad.txt')) as f:
        for line in f:
            text_labels.append((line, False))
    return text_labels

def calculate(chunk_size: int):
    config_path = 'config.ini'
    repo_dir = 'repodir'
    work_dir_base = 'workdir'
    work_dir = work_dir_base + str(chunk_size)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    text_labels = load_dataset()
    cache = CacheRetriever(config_path=config_path)
    fs_init = FeatureStore(embedder=cache.embedder, config_path=config_path, chunk_size=chunk_size)
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=repo_dir)
    fs_init.preprocess(files=files, work_dir=work_dir)
    fs_init.build_dense(files=files, work_dir=work_dir, markdown_as_txt=True)
    del fs_init
    retriever = CacheRetriever(config_path=config_path).get(fs_id=str(chunk_size), work_dir=work_dir)
    start = 0.41
    stop = 0.5
    step = 0.01
    throttles = [round(start + step * i, 4) for i in range(int((stop - start) / step) + 1)]
    best_chunk_f1 = 0.0
    for throttle in tqdm(throttles):
        retriever.reject_throttle = throttle
        dts = []
        gts = []
        for text_label in text_labels:
            question = text_label[0]
            retriever.reject_throttle = throttle
            _, score = retriever.is_relative(query=question, enable_kg=False, enable_threshold=False)
            if score >= throttle:
                dts.append(True)
            else:
                dts.append(False)
            gts.append(text_label[1])
        f1 = f1_score(gts, dts)
        f1 = round(f1, 4)
        precision = precision_score(gts, dts)
        precision = round(precision, 4)
        recall = recall_score(gts, dts)
        recall = round(recall, 4)
        logger.info((throttle, precision, recall, f1))
        data = {'chunk_size': chunk_size, 'throttle': throttle, 'precision': precision, 'recall': recall, 'f1': f1}
        json_str = json.dumps(data)
        with open(osp.join(osp.dirname(__file__), 'chunk{}.jsonl'.format(chunk_size)), 'a') as f:
            f.write(json_str)
            f.write('\n')
        if f1 > best_chunk_f1:
            best_chunk_f1 = f1
    print(best_chunk_f1)
    return best_chunk_f1

def copy_files(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            shutil.copy(src_file, dest_file)
            print(f"Copied '{src_file}' to '{dest_file}'")

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

def load_dataset():
    text_labels = []
    with open(osp.join(osp.dirname(__file__), 'gt_good.txt')) as f:
        for line in f:
            text_labels.append((line, True))
    with open(osp.join(osp.dirname(__file__), 'gt_bad.txt')) as f:
        for line in f:
            text_labels.append((line, False))
    return text_labels

def split_by_group(inputs: list, groupsize: int=1024):
    num_sublists = len(inputs) // groupsize
    remaining_items = len(inputs) % groupsize
    sublists = []
    for i in range(num_sublists):
        start_index = i * groupsize
        end_index = start_index + groupsize
        sublists.append(inputs[start_index:end_index])
    if remaining_items > 0:
        sublists.append(inputs[num_sublists * groupsize:])
    gt = len(inputs)
    dt = 0
    for lis in sublists:
        dt += len(lis)
    assert gt == dt
    return sublists

def calculate(chunk_size: int):
    config_path = 'config.ini'
    repo_dir = 'repodir'
    work_dir_base = 'workdir'
    work_dir = work_dir_base + str(chunk_size)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    text_labels = load_dataset()
    fs_init = FeatureStore(embeddings=None, config_path=config_path, chunk_size=chunk_size, analyze_reject=True, rejecter_naive_splitter=True)
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=repo_dir)
    fs_init.preprocess(files=files, work_dir=work_dir)
    docs = fs_init.build_dense(files=files, work_dir=work_dir)
    del fs_init
    col = init_milvus(col_name='test2', max_length_bytes=3 * chunk_size)
    subdocs = split_by_group(docs)
    for idx, docs in enumerate(subdocs):
        print('build step {}'.format(idx))
        texts = []
        sources = []
        reads = []
        for doc in docs:
            texts.append(doc.page_content[0:chunk_size])
            sources.append(doc.metadata['source'])
            reads.append(doc.metadata['read'])
        max_length = len(max(texts, key=lambda x: len(x)))
        docs_emb = ef(texts)
        entities = [texts, docs_emb['sparse'], docs_emb['dense']]
        try:
            col.insert(entities)
            col.flush()
        except Exception as e:
            print(e)
    print('insert finished')
    start = 0.05
    stop = 0.5
    step = 0.05
    sparse_ratios = []
    sparse_ratios = [round(start + step * i, 4) for i in range(int((stop - start) / step) + 1)]
    best_chunk_f1 = 0.0
    dts = []
    gts = []
    predictions = []
    labels = []
    for sparse_ratio in sparse_ratios:
        for text_label in tqdm(text_labels):
            query_embeddings = ef([text_label[0]])
            k = 1
            sparse_req = AnnSearchRequest(query_embeddings['sparse'], 'sparse_vector', {'metric_type': 'IP'}, limit=k)
            dense_req = AnnSearchRequest(query_embeddings['dense'], 'dense_vector', {'metric_type': 'IP'}, limit=k)
            res = col.hybrid_search([sparse_req, dense_req], rerank=WeightedRanker(sparse_ratio, 1.0 - sparse_ratio), limit=k, output_fields=['text'])
            res = res[0]
            if len(res) > 0:
                predictions.append(max(0.0, min(1.0, res[0].score)))
            else:
                predictions.append(0)
            if text_label[1]:
                labels.append(1)
            else:
                labels.append(0)
        precision, recall, thresholds = precision_recall_curve(labels, predictions)
        f1 = 2 * precision * recall / (precision + recall)
        logger.debug('sparse_ratio {} max f1 {} at {}, threshold {}'.format(sparse_ratio, np.max(f1), np.argmax(f1), thresholds[np.argmax(f1)]))

def files():
    basedir = '/home/data/khj/workspace/huixiangdou/lda/preprocess'
    docs = []
    for root, _, files in os.walk(basedir):
        for file in files:
            if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg'):
                pdb.set_trace()
            else:
                docs.append((file, os.path.join(root, file)))
    return docs

def build_topic(dirname: str='preprocess'):
    namemap = load_namemap()
    pdb.set_trace()
    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=n_features, stop_words='english')
    t0 = time()
    tf = tf_vectorizer.fit_transform(filecontents(dirname))
    print('BoW in %0.3fs.' % (time() - t0))
    lda = LatentDirichletAllocation(n_components=n_components, max_iter=5, learning_method='online', learning_offset=50.0, random_state=0)
    t0 = time()
    doc_types = lda.fit_transform(tf)
    pdb.set_trace()
    print('lda train in %0.3fs.' % (time() - t0))
    feature_names = tf_vectorizer.get_feature_names_out()
    models = {'CountVectorizer': tf_vectorizer, 'LatentDirichletAllocation': lda}
    with open('lda_models.pkl', 'wb') as model_file:
        pkl.dump(models, model_file)
    top_features_list = []
    for _, topic in enumerate(lda.components_):
        top_features_ind = topic.argsort()[-n_top_words:]
        top_features = feature_names[top_features_ind]
        weights = topic[top_features_ind]
        top_features_list.append(top_features.tolist())
    with open(os.path.join('cluster', 'desc.json'), 'w') as f:
        json_str = json.dumps(top_features_list, ensure_ascii=False)
        f.write(json_str)
    filepaths = files()
    pdb.set_trace()
    for file_id, doc_score in enumerate(doc_types):
        basename, input_filepath = filepaths[file_id]
        hashname = basename.split('.')[0]
        source_filepath = namemap[hashname]
        indices_np = np.where(doc_score > 0.1)[0]
        for topic_id in indices_np:
            target_dir = os.path.join('cluster', str(topic_id))
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            shutil.copy(source_filepath, target_dir)

def load_documents(n: int=1):
    basedir = '/home/data/khj/workspace/huixiangdou/repodir.lda'
    docs = []
    for root, _, files in os.walk(basedir):
        for file in files:
            if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg'):
                pdb.set_trace()
            else:
                docs.append((file, os.path.join(root, file)))
    length = len(docs)
    step = length // n
    remainder = length % n
    result = []
    start = 0
    for i in range(n):
        end = start + step + (1 if i < remainder else 0)
        result.append(docs[start:end])
        start = end
    return result

