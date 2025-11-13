# Cluster 30

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

class CacheRetriever:

    def __init__(self, config_path: str, cache_size: int=4, rerank_topn: int=4):
        self.cache = dict()
        self.cache_size = cache_size
        with open(config_path, encoding='utf8') as f:
            fs_config = pytoml.load(f)['feature_store']
        logger.info('loading test2vec and rerank models')
        self.embedder = Embedder(model_config=fs_config)
        self.reranker = LLMReranker(model_config=fs_config, topn=rerank_topn)

    def get(self, fs_id: str='default', config_path='config.ini', work_dir='workdir'):
        """Get database by id."""
        if fs_id in self.cache:
            self.cache[fs_id]['time'] = time.time()
            return self.cache[fs_id]['retriever']
        with open(config_path, encoding='utf8') as f:
            reject_throttle = pytoml.load(f)['feature_store']['reject_throttle']
        if len(self.cache) >= self.cache_size:
            del_key = None
            min_time = time.time()
            for key, value in self.cache.items():
                cur_time = value['time']
                if cur_time < min_time:
                    min_time = cur_time
                    del_key = key
            if del_key is not None:
                del_value = self.cache[del_key]
                self.cache.pop(del_key)
                del del_value['retriever']
        retriever = Retriever(config_path=config_path, embedder=self.embedder, reranker=self.reranker, work_dir=work_dir, reject_throttle=reject_throttle)
        self.cache[fs_id] = {'retriever': retriever, 'time': time.time()}
        return retriever

    def pop(self, fs_id: str):
        """Drop database by id."""
        if fs_id not in self.cache:
            return
        del_value = self.cache[fs_id]
        self.cache.pop(fs_id)
        del del_value

def pop(self, fs_id: str):
    """Drop database by id."""
    if fs_id not in self.cache:
        return
    del_value = self.cache[fs_id]
    self.cache.pop(fs_id)
    del del_value

