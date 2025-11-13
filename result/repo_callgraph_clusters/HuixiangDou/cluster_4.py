# Cluster 4

def simplify_wx_object(json_obj):
    msg_type = json_obj['messageType']
    show_type = ''
    text = json_obj['content']
    sender = json_obj['fromUser']
    recvs = []
    if msg_type in [5, 9, '80001']:
        show_type = 'normal'
        if 'atlist' in json_obj:
            show_type = 'normal_at'
            atlist = json_obj['atlist']
            for at in atlist:
                if len(at) > 0:
                    recvs.append(at)
    if msg_type in [6, '80002']:
        show_type = 'image'
        text = '[图片]'
    elif msg_type == '80009':
        show_type = 'file'
        content = json_obj['pushContent']
    elif msg_type in [14, '80014']:
        show_type = 'ref'
        if 'title' in json_obj:
            content = json_obj['title']
        else:
            content = 'unknown'
        if 'toUser' in json_obj:
            recvs.append(json_obj['toUser'])
    else:
        show_type = 'other'
    if '<?xml version="1.0"?>' in text:
        text = 'xml msg'
    if '<sysmsg' in text:
        text = 'sys msg'
    if '<msg><emoji' in text:
        text = 'emoji'
    if '<msg>' in text and '<op id' in text:
        text = 'app msg'
    text = remove_at_name(text)
    obj = {'show': show_type, 'sender': sender, 'text': text, 'recvs': recvs, 'timestamp': json_obj['timestamp']}
    return obj

def read_badcase(llm_type: str, input_filepath: str):
    gts = []
    dts = []
    unknow_count = 0
    with open('groups/input.jsonl') as gt:
        for line in gt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue
            cr_need_gt = json_obj['cr_need_gt']
            gts.append(cr_need_gt)
    ret = dict()
    idx = 0
    with open(input_filepath) as dt:
        for line in dt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue
            dt = json_obj['{}_cr_need'.format(llm_type)] == 'yes'
            if dt != gts[idx]:
                ret[json_obj['text']] = line
            idx += 1
    return ret

def test_entity_build_and_query():
    entities = ['HuixiangDou', 'WeChat']
    indexer = NamedEntity2Chunk('/tmp')
    indexer.clean()
    indexer.set_entity(entities=entities)
    c0 = Chunk(content_or_path='How to deploy HuixiangDou on wechaty ?')
    c1 = Chunk(content_or_path='do you know what huixiangdou means ?')
    chunks = [c0, c1]
    map_entity2chunks = dict()
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
    query_text = 'how to install wechat ?'
    retriver = NamedEntity2Chunk('/tmp')
    entity_ids = retriver.parse(query_text)
    chunk_id_list = retriver.get_chunk_ids(entity_ids=entity_ids)
    print(chunk_id_list)
    assert chunk_id_list[0][0] == 0

def test_chunk():
    c = Chunk()
    c_str = '{}'.format(c)
    assert 'content_or_path=' in c_str

def test_sg():
    config_path = build_config_path()
    llm = LLM(config_path=config_path)
    proxy = SourceGraphProxy(config_path=config_path)
    content = proxy.search(llm_client=llm, question='mmpose installation', groupname='mmpose dev group')
    assert len(content) > 0

class Queue:

    def __init__(self, name, namespace='HuixiangDou', **redis_kwargs):
        self.__db = redis.Redis(host=redis_host(), port=redis_port(), password=redis_passwd(), charset='utf-8', decode_responses=True)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def peek_tail(self):
        return self.__db.lrange(self.key, -1, -1)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)
        if item:
            item = item[1]
        return item

    def get_all(self):
        """Get add messages in queue without block."""
        ret = []
        while True:
            item = self.__db.lpop(self.key)
            if not item:
                break
            ret.append(item)
        return ret

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

def get(self, block=True, timeout=None):
    """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
    if block:
        item = self.__db.blpop(self.key, timeout=timeout)
    else:
        item = self.__db.lpop(self.key)
    if item:
        item = item[1]
    return item

def get_all(self):
    """Get add messages in queue without block."""
    ret = []
    while True:
        item = self.__db.lpop(self.key)
        if not item:
            break
        ret.append(item)
    return ret

def log(name):
    """
    @param name: python file name
    @return: Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s:     %(asctime)s - %(module)s-%(funcName)s-line:%(lineno)d - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def clear_other_log():
    for name, item in logging.Logger.manager.loggerDict.items():
        if not isinstance(item, logging.Logger):
            continue
        if 'aoe' not in name:
            item.setLevel(logging.CRITICAL)

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

class CharacterTextSplitter(TextSplitter):
    """Splitting text that looks at characters."""

    def __init__(self, separator: str='\n\n', is_separator_regex: bool=False, **kwargs: Any) -> None:
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator
        self._is_separator_regex = is_separator_regex

    def split_text(self, text: str) -> List[str]:
        """Split incoming text and return chunks."""
        separator = self._separator if self._is_separator_regex else re.escape(self._separator)
        splits = _split_text_with_regex(text, separator, self._keep_separator)
        _separator = '' if self._keep_separator else self._separator
        return self._merge_splits(splits, _separator)

def split_text(self, text: str) -> List[str]:
    """Split incoming text and return chunks."""
    separator = self._separator if self._is_separator_regex else re.escape(self._separator)
    splits = _split_text_with_regex(text, separator, self._keep_separator)
    _separator = '' if self._keep_separator else self._separator
    return self._merge_splits(splits, _separator)

class RecursiveCharacterTextSplitter(TextSplitter):
    """Splitting text by recursively look at characters.

    Recursively tries to split by different characters to find one that works.
    """

    def __init__(self, separators: Optional[List[str]]=None, keep_separator: bool=True, is_separator_regex: bool=False, **kwargs: Any) -> None:
        """Create a new TextSplitter."""
        super().__init__(keep_separator=keep_separator, **kwargs)
        self._separators = separators or ['\n\n', '\n', ' ', '']
        self._is_separator_regex = is_separator_regex

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self._is_separator_regex else re.escape(_s)
            if _s == '':
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1:]
                break
        _separator = separator if self._is_separator_regex else re.escape(separator)
        splits = _split_text_with_regex(text, _separator, self._keep_separator)
        _good_splits = []
        _separator = '' if self._keep_separator else separator
        for s in splits:
            if self._length_function(s) < self._chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return final_chunks

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self._separators)

def _split_text(self, text: str, separators: List[str]) -> List[str]:
    """Split incoming text and return chunks."""
    final_chunks = []
    separator = separators[-1]
    new_separators = []
    for i, _s in enumerate(separators):
        _separator = _s if self._is_separator_regex else re.escape(_s)
        if _s == '':
            separator = _s
            break
        if re.search(_separator, text):
            separator = _s
            new_separators = separators[i + 1:]
            break
    _separator = separator if self._is_separator_regex else re.escape(separator)
    splits = _split_text_with_regex(text, _separator, self._keep_separator)
    _good_splits = []
    _separator = '' if self._keep_separator else separator
    for s in splits:
        if self._length_function(s) < self._chunk_size:
            _good_splits.append(s)
        else:
            if _good_splits:
                merged_text = self._merge_splits(_good_splits, _separator)
                final_chunks.extend(merged_text)
                _good_splits = []
            if not new_separators:
                final_chunks.append(s)
            else:
                other_info = self._split_text(s, new_separators)
                final_chunks.extend(other_info)
    if _good_splits:
        merged_text = self._merge_splits(_good_splits, _separator)
        final_chunks.extend(merged_text)
    return final_chunks

def split_text(self, text: str) -> List[str]:
    return self._split_text(text, self._separators)

class ChineseRecursiveTextSplitter(RecursiveCharacterTextSplitter):

    def __init__(self, separators: Optional[List[str]]=None, keep_separator: bool=True, is_separator_regex: bool=True, **kwargs: Any) -> None:
        """Create a new TextSplitter."""
        super().__init__(keep_separator=keep_separator, **kwargs)
        self._separators = separators or ['\n\n', '\n', '。|！|？', '\\.\\s|\\!\\s|\\?\\s', '；|;\\s', '，|,\\s']
        self._is_separator_regex = is_separator_regex

    def _split_text_with_regex_from_end(self, text: str, separator: str, keep_separator: bool) -> List[str]:
        if separator:
            if keep_separator:
                _splits = re.split(f'({separator})', text)
                splits = [''.join(i) for i in zip(_splits[0::2], _splits[1::2])]
                if len(_splits) % 2 == 1:
                    splits += _splits[-1:]
            else:
                splits = re.split(separator, text)
        else:
            splits = list(text)
        return [s for s in splits if s != '']

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self._is_separator_regex else re.escape(_s)
            if _s == '':
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1:]
                break
        _separator = separator if self._is_separator_regex else re.escape(separator)
        splits = self._split_text_with_regex_from_end(text, _separator, self._keep_separator)
        _good_splits = []
        _separator = '' if self._keep_separator else separator
        for s in splits:
            if self._length_function(s) < self._chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return [re.sub('\\n{2,}', '\n', chunk.strip()) for chunk in final_chunks if chunk.strip() != '']

def _split_text(self, text: str, separators: List[str]) -> List[str]:
    """Split incoming text and return chunks."""
    final_chunks = []
    separator = separators[-1]
    new_separators = []
    for i, _s in enumerate(separators):
        _separator = _s if self._is_separator_regex else re.escape(_s)
        if _s == '':
            separator = _s
            break
        if re.search(_separator, text):
            separator = _s
            new_separators = separators[i + 1:]
            break
    _separator = separator if self._is_separator_regex else re.escape(separator)
    splits = self._split_text_with_regex_from_end(text, _separator, self._keep_separator)
    _good_splits = []
    _separator = '' if self._keep_separator else separator
    for s in splits:
        if self._length_function(s) < self._chunk_size:
            _good_splits.append(s)
        else:
            if _good_splits:
                merged_text = self._merge_splits(_good_splits, _separator)
                final_chunks.extend(merged_text)
                _good_splits = []
            if not new_separators:
                final_chunks.append(s)
            else:
                other_info = self._split_text(s, new_separators)
                final_chunks.extend(other_info)
    if _good_splits:
        merged_text = self._merge_splits(_good_splits, _separator)
        final_chunks.extend(merged_text)
    return [re.sub('\\n{2,}', '\n', chunk.strip()) for chunk in final_chunks if chunk.strip() != '']

class MarkdownHeaderTextSplitter:
    """Splitting markdown files based on specified headers."""

    def __init__(self, headers_to_split_on: List[Tuple[str, str]]=[('#', 'Header 1'), ('##', 'Header 2'), ('###', 'Header 3')], strip_headers: bool=True):
        """Create a new MarkdownHeaderTextSplitter.

        Args:
            headers_to_split_on: Headers we want to track
            strip_headers: Strip split headers from the content of the chunk
        """
        self.headers_to_split_on = sorted(headers_to_split_on, key=lambda split: len(split[0]), reverse=True)
        self.strip_headers = strip_headers
        super().__init__()

    def aggregate_lines_to_chunks(self, lines: List[LineType], base_meta: dict) -> List[Chunk]:
        """Combine lines with common metadata into chunks
        Args:
            lines: Line of text / associated header metadata
        """
        aggregated_chunks: List[LineType] = []
        for line in lines:
            if aggregated_chunks and aggregated_chunks[-1]['metadata'] == line['metadata']:
                aggregated_chunks[-1]['content'] += '  \n' + line['content']
            elif aggregated_chunks and aggregated_chunks[-1]['metadata'] != line['metadata'] and (len(aggregated_chunks[-1]['metadata']) < len(line['metadata'])) and (aggregated_chunks[-1]['content'].split('\n')[-1][0] == '#') and (not self.strip_headers):
                aggregated_chunks[-1]['content'] += '  \n' + line['content']
                aggregated_chunks[-1]['metadata'] = line['metadata']
            else:
                aggregated_chunks.append(line)
        return [Chunk(content_or_path=chunk['content'], metadata=dict(chunk['metadata'], **base_meta)) for chunk in aggregated_chunks]

    def create_chunks(self, text: str, metadata: dict={}) -> List[Chunk]:
        """Split markdown file
        Args:
            text: Markdown file"""
        lines = text.split('\n')
        lines_with_metadata: List[LineType] = []
        current_content: List[str] = []
        current_metadata: Dict[str, str] = {}
        header_stack: List[HeaderType] = []
        initial_metadata: Dict[str, str] = {}
        in_code_block = False
        opening_fence = ''
        for line in lines:
            stripped_line = line.strip()
            stripped_line = ''.join(filter(str.isprintable, stripped_line))
            if not in_code_block:
                if stripped_line.startswith('```') and stripped_line.count('```') == 1:
                    in_code_block = True
                    opening_fence = '```'
                elif stripped_line.startswith('~~~'):
                    in_code_block = True
                    opening_fence = '~~~'
            elif stripped_line.startswith(opening_fence):
                in_code_block = False
                opening_fence = ''
            if in_code_block:
                current_content.append(stripped_line)
                continue
            for sep, name in self.headers_to_split_on:
                if stripped_line.startswith(sep) and (len(stripped_line) == len(sep) or stripped_line[len(sep)] == ' '):
                    if name is not None:
                        current_header_level = sep.count('#')
                        while header_stack and header_stack[-1]['level'] >= current_header_level:
                            popped_header = header_stack.pop()
                            if popped_header['name'] in initial_metadata:
                                initial_metadata.pop(popped_header['name'])
                        header: HeaderType = {'level': current_header_level, 'name': name, 'data': stripped_line[len(sep):].strip()}
                        header_stack.append(header)
                        initial_metadata[name] = header['data']
                    if current_content:
                        lines_with_metadata.append({'content': '\n'.join(current_content), 'metadata': current_metadata.copy()})
                        current_content.clear()
                    if not self.strip_headers:
                        current_content.append(stripped_line)
                    break
            else:
                if stripped_line:
                    current_content.append(stripped_line)
                elif current_content:
                    lines_with_metadata.append({'content': '\n'.join(current_content), 'metadata': current_metadata.copy()})
                    current_content.clear()
            current_metadata = initial_metadata.copy()
        if current_content:
            lines_with_metadata.append({'content': '\n'.join(current_content), 'metadata': current_metadata})
        return self.aggregate_lines_to_chunks(lines_with_metadata, base_meta=metadata)

def aggregate_lines_to_chunks(self, lines: List[LineType], base_meta: dict) -> List[Chunk]:
    """Combine lines with common metadata into chunks
        Args:
            lines: Line of text / associated header metadata
        """
    aggregated_chunks: List[LineType] = []
    for line in lines:
        if aggregated_chunks and aggregated_chunks[-1]['metadata'] == line['metadata']:
            aggregated_chunks[-1]['content'] += '  \n' + line['content']
        elif aggregated_chunks and aggregated_chunks[-1]['metadata'] != line['metadata'] and (len(aggregated_chunks[-1]['metadata']) < len(line['metadata'])) and (aggregated_chunks[-1]['content'].split('\n')[-1][0] == '#') and (not self.strip_headers):
            aggregated_chunks[-1]['content'] += '  \n' + line['content']
            aggregated_chunks[-1]['metadata'] = line['metadata']
        else:
            aggregated_chunks.append(line)
    return [Chunk(content_or_path=chunk['content'], metadata=dict(chunk['metadata'], **base_meta)) for chunk in aggregated_chunks]

def split_python_code(filepath: str, text: str, metadata: dict={}):
    """Split python code to class, function and annotation."""
    basename = os.path.basename(filepath)
    texts = []
    texts.append(basename)
    try:
        node = ast.parse(text)
        data = ast.get_docstring(node)
        if data:
            texts.append(data)
        for child_node in ast.walk(node):
            if isinstance(child_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                data = ast.get_docstring(child_node)
                if data:
                    texts.append(f'{child_node.name} {data}')
    except Exception as e:
        logger.error('{} {}, continue'.format(filepath, str(e)))
    chunks = []
    for text in texts:
        chunks.append(Chunk(content_or_path=text, metadata=metadata))
    return chunks

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

def __init__(self, root: str, filename: str, _type: str):
    self.root = root
    self.prefix = filename.replace('/', '_')
    self.basename = os.path.basename(filename)
    self.origin = os.path.join(root, filename)
    self.copypath = self.origin
    self._type = _type
    self.state = True
    self.reason = ''

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

class Queue:

    def __init__(self, name, namespace='HuixiangDou', **redis_kwargs):
        self.__db = redis.Redis(host=redis_host(), port=redis_port(), password=redis_passwd(), charset='utf-8', decode_responses=True)
        self.key = '%s:%s' % (namespace, name)
        print(self.qsize())

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def peek_tail(self):
        return self.__db.lrange(self.key, -1, -1)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)
        if item:
            item = item[1]
        return item

    def get_all(self):
        """Get add messages in queue without block."""
        ret = []
        try:
            while len(ret) < 1:
                item = self.__db.lpop(self.key)
                if not item:
                    break
                ret.append(item)
        except Exception as e:
            logger.error(str(e))
        return ret

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

def get(self, block=True, timeout=None):
    """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
    if block:
        item = self.__db.blpop(self.key, timeout=timeout)
    else:
        item = self.__db.lpop(self.key)
    if item:
        item = item[1]
    return item

def get_all(self):
    """Get add messages in queue without block."""
    ret = []
    try:
        while len(ret) < 1:
            item = self.__db.lpop(self.key)
            if not item:
                break
            ret.append(item)
    except Exception as e:
        logger.error(str(e))
    return ret

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

def convert_history_to_tuple(history: List[Talk]):
    history = []
    for item in history:
        history.append({'role': 'user', 'content': item.query})
        history.append({'role': 'assistant', 'content': item.reply})
    return history

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

def add_chunk(md_node: Node, pageid: int, text: str):
    chunk_node = Node(_type=KGType.CHUNK, data=text)
    self.nodes.append(chunk_node)
    self.build_md_chunk(md_node=chunk_node, abspath=abspath)
    self.relations.append(Relation(md_node.uuid, chunk_node.uuid, 'page{}'.format(pageid)))

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

@DeprecationWarning
def build_messages(prompt, history, system: str=None):
    messages = []
    if system is not None and len(system) > 0:
        messages.append({'role': 'system', 'content': system})
    for item in history:
        messages.append({'role': 'user', 'content': item[0]})
        messages.append({'role': 'assistant', 'content': item[1]})
    messages.append({'role': 'user', 'content': prompt})
    return messages

class ErrorCode(Enum):
    """Define an enumerated type for error codes, each has a numeric value and
    a description.

    Each enum member is associated with a numeric code and a description
    string. The numeric code is used as the return code in function calls, and
    the description provides a human-readable explanation of the error.
    """
    SUCCESS = (0, 'success')
    NOT_A_QUESTION = (1, 'query is not a question')
    NO_TOPIC = (2, 'The question does not have a topic. It might be a meaningless sentence.')
    UNRELATED = (3, 'Topics unrelated to the knowledge base. Updating good_questions and bad_questions can improve accuracy.')
    NO_SEARCH_KEYWORDS = (4, 'Cannot extract keywords.')
    NO_SEARCH_RESULT = (5, 'No search result.')
    BAD_ANSWER = (6, 'Irrelevant answer.')
    SECURITY = (7, 'Reply has a high relevance to prohibited topics.')
    NOT_WORK_TIME = (8, 'Non-working hours. The config.ini file can be modified to adjust this. **In scenarios where speech may pose risks, let the robot operate under human supervision**')
    PARAMETER_ERROR = (9, "HTTP interface parameter error. Query cannot be empty; the format of history is list of lists, like [['question1', 'reply1'], ['question2'], ['reply2']]")
    PARAMETER_MISS = (10, 'Missing key in http json input parameters.')
    WORK_IN_PROGRESS = (11, 'Not finish')
    FAILED = (12, 'Fail')
    BAD_PARAMETER = (13, 'Bad parameter')
    INTERNAL_ERROR = (14, 'Internal error')
    WEB_SEARCH_FAIL = (15, 'Web search fail, please check network, TOKEN and quota')
    SG_SEARCH_FAIL = (16, 'SourceGraph not result, please check token or input query')
    LLM_NOT_RESPONSE_SG = (17, 'LLM not response query with sg search')
    QUESTION_TOO_SHORT = (18, 'Query length too short')
    INIT = (19, 'Init state')

    def __new__(cls, value, description):
        """Create new instance of ErrorCode."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __int__(self):
        """Return the integer representation of the error code."""
        return self.value

    def __str__(self):
        """Return the str representation of the error code."""
        return self.description

    def describe(self):
        """Return the description of the error code."""
        return self.description

    @classmethod
    def format(cls, code):
        """Format the error code into a JSON result.

        Args:
            code (ErrorCode): Error code to be formatted.

        Returns:
            dict: A dictionary that includes the error code and its description.  # noqa E501

        Raises:
            TypeError: If the input is not an instance of ErrorCode.
        """
        if isinstance(code, cls):
            return {'code': int(code), 'message': code.describe()}
        raise TypeError(f'Expected type {cls}, got {type(code)}')

@classmethod
def format(cls, code):
    """Format the error code into a JSON result.

        Args:
            code (ErrorCode): Error code to be formatted.

        Returns:
            dict: A dictionary that includes the error code and its description.  # noqa E501

        Raises:
            TypeError: If the input is not an instance of ErrorCode.
        """
    if isinstance(code, cls):
        return {'code': int(code), 'message': code.describe()}
    raise TypeError(f'Expected type {cls}, got {type(code)}')

class Queue:

    def __init__(self, name, namespace='HuixiangDou', **redis_kwargs):
        self.__db = redis.Redis(host=redis_host(), port=redis_port(), password=redis_passwd(), charset='utf-8', decode_responses=True)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def peek_tail(self):
        return self.__db.lrange(self.key, -1, -1)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)
        if item:
            item = item[1]
        return item

    def get_all(self):
        """Get add messages in queue without block."""
        ret = []
        while True:
            item = self.__db.lpop(self.key)
            if not item:
                break
            ret.append(item)
        return ret

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

def get(self, block=True, timeout=None):
    """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
    if block:
        item = self.__db.blpop(self.key, timeout=timeout)
    else:
        item = self.__db.lpop(self.key)
    if item:
        item = item[1]
    return item

def get_all(self):
    """Get add messages in queue without block."""
    ret = []
    while True:
        item = self.__db.lpop(self.key)
        if not item:
            break
        ret.append(item)
    return ret

class QueryTracker:
    """A class to track queries and log them into a file.

    This class provides functionality to keep track of queries and write them
    into a log file. Whenever a query is made, it can be logged using this
    class, and when the instance of this class is destroyed, all logged queries
    are written to the file.
    """

    def __init__(self, log_file_path):
        """Initialize the QueryTracker with the path of the log file."""
        self.log_file_path = log_file_path
        self.log_list = []

    def log(self, key, value=''):
        """Log a query.

        Args:
            key (str): The key associated with the query.
            value (str): The value or result associated with the query.
        """
        self.log_list.append((key, value))

    def __del__(self):
        """Write all logged queries into the file when the QueryTracker
        instance is destroyed.

        It opens the log file in append mode, writes all logged queries into
        the file, and then closes the file. If any exception occurs during this
        process, it will be caught and printed to standard output.
        """
        try:
            with open(self.log_file_path, 'a', encoding='utf8') as log_file:
                for key, value in self.log_list:
                    log_file.write(f'{key}: {value}\n')
                log_file.write('\n')
        except Exception as e:
            print(e)

def log(self, key, value=''):
    """Log a query.

        Args:
            key (str): The key associated with the query.
            value (str): The value or result associated with the query.
        """
    self.log_list.append((key, value))

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

@DeprecationWarning
class ChatClient:
    """A class to handle client-side interactions with a chat service.

    This class is responsible for loading configurations from a given path,
    building prompts, and generating responses by interacting with the chat
    service.
    """

    def __init__(self, config_path: str) -> None:
        """Initialize the ChatClient with the path of the configuration
        file."""
        logger.warning('The `class ChatClient` will be removed on 20250935, use `class LLM` instead.')
        self.config_path = config_path
        self.llm_config = None
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']

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

    def auto_fix(self, backend):
        """Choose real backend according to config.ini."""
        enable_local, enable_remote = (self.llm_config['enable_local'], self.llm_config['enable_remote'])
        local_len, remote_len = (self.llm_config['server']['local_llm_max_text_length'], self.llm_config['server']['remote_llm_max_text_length'])
        max_length = local_len
        if enable_remote:
            max_length = remote_len
        if backend == 'local' and (not enable_local):
            backend = self.llm_config['server']['remote_type']
            max_length = remote_len
        elif backend != 'local' and (not enable_remote):
            backend = 'local'
            max_length = local_len
        return (backend, max_length)

    def generate_response(self, prompt, history=[], backend='local'):
        """Generate a response from the chat service.

        Args:
            prompt (str): The prompt to send to the chat service.
            history (list, optional): List of previous interactions. Defaults to [].
            backend (str, optional): Determine which LLM should be called. Default to `local`

        Returns:
            str: Generated response from the chat service.
        """
        url = self.llm_config['client_url']
        real_backend, max_length = self.auto_fix(backend=backend)
        if len(prompt) > max_length:
            logger.warning(f'prompt length {len(prompt)}  > max_length {max_length}, truncated')
            prompt = prompt[0:max_length]
        try:
            header = {'Content-Type': 'application/json'}
            data_history = []
            for item in history:
                data_history.append([item[0], item[1]])
            data = {'prompt': prompt, 'history': data_history, 'backend': real_backend}
            resp = requests.post(url, headers=header, data=json.dumps(data), timeout=300)
            if resp.status_code != 200:
                raise Exception(str((resp.status_code, resp.reason)))
            json_obj = resp.json()
            text = json_obj['text']
            if 'error' in json_obj:
                error = json_obj['error']
                if len(error) > 0:
                    logger.error(error)
            return text
        except Exception as e:
            logger.error(str(e))
            return ''

    async def chat_stream(self, prompt, history=[], backend='local'):
        """Generate a stream response from the chat service.

        Args:
            prompt (str): The prompt to send to the chat service.
            history (list, optional): List of previous interactions. Defaults to [].
            backend (str, optional): Determine which LLM should be called. Default to `local`

        Returns:
            str: Generated response from the chat service.
        """
        sync_url = self.llm_config['client_url']
        stream_url = sync_url.replace('/inference', '/stream')
        real_backend, max_length = self.auto_fix(backend=backend)
        if len(prompt) > max_length:
            logger.warning(f'prompt length {len(prompt)}  > max_length {max_length}, truncated')
            prompt = prompt[0:max_length]
        sse_pattern = re.compile('data: (.*?)(?=\\r\\n\\r\\n)', re.DOTALL)
        try:
            headers = {'Content-Type': 'application/json'}
            data_history = []
            for item in history:
                data_history.append([item[0], item[1]])
            data = {'prompt': prompt, 'history': data_history, 'backend': real_backend}
            async with aiohttp.ClientSession() as session:
                async with session.post(stream_url, headers=headers, data=json.dumps(data)) as response:
                    if response.status == 200:
                        async for chunk in response.content.iter_any():
                            chunk_data = chunk.decode()
                            messages = sse_pattern.findall(chunk_data)
                            for message in messages:
                                if '\r\ndata: ' in message:
                                    message = message.replace('\r\ndata: ', '\r\n')
                                yield message
                    else:
                        raise Exception(response.status)
        except Exception as e:
            logger.error(str(e))
            logger.error('See the HuixiangDou FAQ, feel free to `submit an issue` or `ask in the WeChat group`. ')

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

class CitationGeneratePrompt:
    """Build generate prompt with citation format"""
    language = None

    def __init__(self, language: str):
        self.language = language

    def remove_markdown_headers(self, texts: List[str]):
        pure_texts = []
        for text in texts:
            pure_text = re.sub('^#{1,6}\\s*', '', text, flags=re.MULTILINE)
            pure_texts.append(pure_text)
        return pure_texts

    def build(self, texts: List[str], question: str):
        pure_texts = self.remove_markdown_headers(texts)
        if self.language == 'zh':
            head = GENERATE_TEMPLATE_CITATION_HEAD_CN
            question_prompt = '\n## 用户输入\n{}\n'.format(question)
            context_prompt = ''
            for index, text in enumerate(pure_texts):
                context_prompt += '\n## 检索结果{}\n{}\n'.format(index + 1, text)
        elif self.language == 'en':
            head = GENERATE_TEMPLATE_CITATION_HEAD_EN
            question_prompt = '\n## user input\n{}\n'.format(question)
            context_prompt = ''
            for index, text in enumerate(pure_texts):
                context_prompt += '\n## search result{}\n{}\n'.format(index + 1, text)
        prompt = head + context_prompt + question_prompt
        return prompt

def remove_markdown_headers(self, texts: List[str]):
    pure_texts = []
    for text in texts:
        pure_text = re.sub('^#{1,6}\\s*', '', text, flags=re.MULTILINE)
        pure_texts.append(pure_text)
    return pure_texts

def build(self, texts: List[str], question: str):
    pure_texts = self.remove_markdown_headers(texts)
    if self.language == 'zh':
        head = GENERATE_TEMPLATE_CITATION_HEAD_CN
        question_prompt = '\n## 用户输入\n{}\n'.format(question)
        context_prompt = ''
        for index, text in enumerate(pure_texts):
            context_prompt += '\n## 检索结果{}\n{}\n'.format(index + 1, text)
    elif self.language == 'en':
        head = GENERATE_TEMPLATE_CITATION_HEAD_EN
        question_prompt = '\n## user input\n{}\n'.format(question)
        context_prompt = ''
        for index, text in enumerate(pure_texts):
            context_prompt += '\n## search result{}\n{}\n'.format(index + 1, text)
    prompt = head + context_prompt + question_prompt
    return prompt

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

class Session:
    """For compute graph, `session` takes all parameter."""

    def __init__(self, query: Query, history: list, groupname: str='', log_path: str='logs/generate.jsonl', groupchats: list=[]):
        self.query = query
        self.history = history
        self.groupname = groupname
        self.groupchats = groupchats
        self.delta = ''
        self.parallel_chunks = []
        self.response = ''
        self.references = []
        self.topic = ''
        self.code = ErrorCode.INIT
        self.cr = ''
        self.chunk = ''
        self.knowledge = ''
        self.web_knowledge = ''
        self.sg_knowledge = ''
        self.debug = dict()
        self.log_path = log_path

    def __del__(self):
        dirname = os.path.dirname(self.log_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        try:
            with open(self.log_path, 'a') as f:
                json_str = json.dumps(self.debug, indent=2, ensure_ascii=False)
                f.write(json_str)
                f.write('\n')
        except Exception as e:
            pass

def __init__(self, query: Query, history: list, groupname: str='', log_path: str='logs/generate.jsonl', groupchats: list=[]):
    self.query = query
    self.history = history
    self.groupname = groupname
    self.groupchats = groupchats
    self.delta = ''
    self.parallel_chunks = []
    self.response = ''
    self.references = []
    self.topic = ''
    self.code = ErrorCode.INIT
    self.cr = ''
    self.chunk = ''
    self.knowledge = ''
    self.web_knowledge = ''
    self.sg_knowledge = ''
    self.debug = dict()
    self.log_path = log_path

def save(_id, sentence):
    if _id not in queries:
        queries[_id] = [sentence]
    else:
        queries[_id].append(sentence)

def get_all_comments(owner, name, issue_number):
    headers = {'Authorization': TOKEN}
    issue_comments_url = f'https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/comments'
    comments = []
    result_comments = []
    response = requests.get(issue_comments_url, headers=headers)
    if response.status_code != 200:
        loguru.logger.error(f'Failed to retrieve comments: {response.status_code} issue_number {issue_number}')
        loguru.logger.error(f'{response.text}')
        if 'limit' in response.text:
            loguru.logger.error('受到 github 限制，自动结束')
            exit()
        return []
    page_comments = response.json()
    if not page_comments:
        return []
    comments.extend(page_comments)
    for i, sub_comment in enumerate(comments):
        comment = {'id': i, 'user': sub_comment['user']['login'], 'body': sub_comment['body']}
        if '> ' in comment['body']:
            quoted_regex = re.compile('^>.*(?:\\r?\\n|\\r)?', re.MULTILINE)
            comment['body'] = re.sub(quoted_regex, '', comment['body']).strip()
        result_comments.append(comment)
    return result_comments

def langchain_splitter(text: str, chunk_size: int, metadata):
    """This is for debugging"""
    from langchain.text_splitter import MarkdownTextSplitter
    md_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=32)
    docs = md_splitter.create_documents([text])
    chunks = []
    for doc in docs:
        c = Chunk(content_or_path=doc.page_content, metadata=metadata)
        chunks.append(c)
    return chunks

def llm_with_plugin(prompt: str, history, list_of_plugin_info=()):
    chat_history = [(x['user'], x['bot']) for x in history] + [(prompt, '')]
    planning_prompt = build_input_text(chat_history, list_of_plugin_info)
    text = ''
    while True:
        output = text_completion(planning_prompt + text, stop_words=['Observation:', 'Observation:\n'])
        action, action_input, output = parse_latest_plugin_call(output)
        if action:
            observation = call_plugin(action, action_input)
            output += f'\nObservation: {observation}\nThought:'
            text += output
        else:
            text += output
            break
    new_history = []
    new_history.extend(history)
    new_history.append({'user': prompt, 'bot': text})
    return (text, new_history)

def load_namemap():
    namemap = dict()
    with open('name_map.txt') as f:
        for line in f:
            parts = line.split('\t')
            namemap[parts[0].strip()] = parts[1].strip()
    return namemap

