# Cluster 16

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

def __init__(self, separator: str='\n\n', is_separator_regex: bool=False, **kwargs: Any) -> None:
    """Create a new TextSplitter."""
    super().__init__(**kwargs)
    self._separator = separator
    self._is_separator_regex = is_separator_regex

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

def __init__(self, separators: Optional[List[str]]=None, keep_separator: bool=True, is_separator_regex: bool=False, **kwargs: Any) -> None:
    """Create a new TextSplitter."""
    super().__init__(keep_separator=keep_separator, **kwargs)
    self._separators = separators or ['\n\n', '\n', ' ', '']
    self._is_separator_regex = is_separator_regex

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

def __init__(self, separators: Optional[List[str]]=None, keep_separator: bool=True, is_separator_regex: bool=True, **kwargs: Any) -> None:
    """Create a new TextSplitter."""
    super().__init__(keep_separator=keep_separator, **kwargs)
    self._separators = separators or ['\n\n', '\n', '。|！|？', '\\.\\s|\\!\\s|\\?\\s', '；|;\\s', '，|,\\s']
    self._is_separator_regex = is_separator_regex

class MarkdownTextRefSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along Markdown-formatted headings."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a MarkdownTextRefSplitter."""
        separators = ['\n#{1,6} ', '```\n', '\n\\*\\*\\*+\n', '\n---+\n', '\n___+\n', '\n\n', '\n', ' ', '']
        super().__init__(separators=separators, **kwargs)

def __init__(self, **kwargs: Any) -> None:
    """Initialize a MarkdownTextRefSplitter."""
    separators = ['\n#{1,6} ', '```\n', '\n\\*\\*\\*+\n', '\n---+\n', '\n___+\n', '\n\n', '\n', ' ', '']
    super().__init__(separators=separators, **kwargs)

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

def __init__(self, headers_to_split_on: List[Tuple[str, str]]=[('#', 'Header 1'), ('##', 'Header 2'), ('###', 'Header 3')], strip_headers: bool=True):
    """Create a new MarkdownHeaderTextSplitter.

        Args:
            headers_to_split_on: Headers we want to track
            strip_headers: Strip split headers from the content of the chunk
        """
    self.headers_to_split_on = sorted(headers_to_split_on, key=lambda split: len(split[0]), reverse=True)
    self.strip_headers = strip_headers
    super().__init__()

class NestablePool(multiprocessing.pool.Pool):

    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(NestablePool, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs['context'] = NoDaemonContext()
    super(NestablePool, self).__init__(*args, **kwargs)

class NestablePool(multiprocessing.pool.Pool):

    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(NestablePool, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs['context'] = NoDaemonContext()
    super(NestablePool, self).__init__(*args, **kwargs)

class NestablePool(multiprocessing.pool.Pool):

    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(NestablePool, self).__init__(*args, **kwargs)

def __init__(self, *args, **kwargs):
    kwargs['context'] = NoDaemonContext()
    super(NestablePool, self).__init__(*args, **kwargs)

