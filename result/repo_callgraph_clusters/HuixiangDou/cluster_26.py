# Cluster 26

def readme():
    with open(os.path.join(pwd, 'README.md'), encoding='utf-8') as f:
        content = f.read()
    return content

def get_version():
    with open(os.path.join(pwd, version_file), 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']

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
        self.config_path = config_path
        self.llm_config = None
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']

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

def __init__(self, config_path: str) -> None:
    """Initialize the ChatClient with the path of the configuration
        file."""
    self.config_path = config_path
    self.llm_config = None
    with open(self.config_path, encoding='utf8') as f:
        config = pytoml.load(f)
        self.llm_config = config['llm']

def kimi_annotate(puyu_file_path: str, kimi_file_path: str):
    with open(puyu_file_path, 'r', encoding='utf-8') as input_file, open(kimi_file_path, 'w', encoding='utf-8') as output_file:
        datas = []
        for line in input_file:
            data = json.loads(line)
            if not data['is_question']:
                continue
            text = data['text']
            kimi_gt = kimi_is_question(query=text)
            logger.debug('{} --- {}'.format(text, kimi_gt))
            data['kimi_is_question'] = kimi_gt
            datas.append(data)
            output_file.write(json.dumps(data, ensure_ascii=False) + '\n')

def human_annotate(kimi_file_path: str, gt_file_path):
    datas = []
    miss_key = 0
    kimi_is_not_question = 0
    line_idx = 0
    too_short = 0
    with open(kimi_file_path) as input_file:
        while True:
            line = input_file.readline()
            line_idx += 1
            if not line:
                break
            data = json.loads(line)
            if 'kimi_is_question' not in data:
                miss_key += 1
                continue
            if data['kimi_is_question'] == False:
                kimi_is_not_question += 1
                continue
            if len(data['text']) < 7:
                too_short += 1
                continue
            datas.append(data)
    logger.debug('sum: {}, kimi_is_question: {}, kimi_is_not_question {}, miss_key {} too_short {}'.format(line_idx, len(datas), kimi_is_not_question, miss_key, too_short))
    START_INDEX = 0
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(sys.stdin)
    with open(gt_file_path, 'a', encoding='utf-8') as output_file:
        max_len = len(datas)
        datas = datas[START_INDEX:]
        for idx, data in enumerate(datas):
            cr_window = data.get('cr_window', {})
            text = data.get('text', '')
            sender = data.get('sender', '')
            context = build_context(sender=sender, query=text, window=cr_window)
            print('{} / {}'.format(idx, max_len))
            print(context)
            while True:
                user_input = sys.stdin.read(1)
                if user_input not in ['j', 'k', 'i']:
                    print("Invalid input. Please enter 'j' or 'k' (yes, no or none). ")
                    continue
                print(user_input)
                break
            if user_input == 'j':
                data['cr_need_gt'] = True
            elif user_input == 'k':
                data['cr_need_gt'] = False
            elif user_input == 'i':
                data['cr_need_gt'] = 'not a question'
            output_file.write(json.dumps(data, ensure_ascii=False) + '\n')
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    print('Annotation completed. Check the output file for the results.')

def human_check(gt_file_path):
    bad = []
    bad_text_sum = 0
    good = []
    good_text_sum = 0
    with open(gt_file_path) as f:
        for idx, line in enumerate(f):
            data = json.loads(line)
            if data['cr_need_gt']:
                bad.append(repr(data['text']))
                bad_text_sum += len(data['text'])
            else:
                good.append(repr(data['text']))
                good_text_sum += len(data['text'])
    print(json.dumps(bad, indent=2, ensure_ascii=False))
    print(json.dumps(good, indent=2, ensure_ascii=False))
    print('bad count {}, avg text len {}; good count {}, avg text len {}'.format(len(bad), bad_text_sum / len(bad), len(good), good_text_sum / len(good)))
    with open('groups/good.json', 'w') as f:
        f.write(json.dumps(good, ensure_ascii=False, indent=2))
    with open('groups/bad.json', 'w') as f:
        f.write(json.dumps(bad, ensure_ascii=False, indent=2))

def llm_annotate(llm_type: str, input_filepath: str='groups/input.jsonl', output_filepath: str='groups/output.jsonl'):
    idx = 0
    with open(input_filepath) as fin, open(output_filepath, 'a') as fout:
        for line in fin:
            json_obj = json.loads(line)
            if not json_obj['is_question']:
                continue
            if not json_obj['kimi_is_question']:
                continue
            idx += 1
            if 'qwen' in llm_type.lower():
                cr_text, state = qwen_coref_res(llm_type=llm_type, target=json_obj)
            json_obj['{}_cr_text'.format(llm_type)] = cr_text
            json_obj['{}_cr_need'.format(llm_type)] = state
            json_text = json.dumps(json_obj, ensure_ascii=False)
            fout.write(json_text)
            fout.write('\n')

def test_character_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = CharacterTextSplitter()
    print(type(s))
    splits = s.split_text(text)
    assert len(splits) > 10
    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/character_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('-----------\n')
    return chunks

def test_recursive_character_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = RecursiveCharacterTextSplitter()
    print(type(s))
    splits = s.split_text(text)
    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/recursive_character_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks

def test_chinese_recursive_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = ChineseRecursiveTextSplitter()
    print(type(s))
    splits = s.split_text(text)
    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/chinese_recursive_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks

def test_markdown_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = MarkdownTextRefSplitter()
    print(type(s))
    splits = s.split_text(text)
    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/markdown_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks

def test_markdown_header_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = MarkdownHeaderTextSplitter()
    print(type(s))
    chunks = s.create_chunks(text, metadata={'path': path})
    with open('/tmp/markdown_header_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks

def test_nested_markdown_split():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    print(type('nested'))
    chunks = nested_split_markdown(filepath=path, text=text, chunksize=768)
    with open('/tmp/markdown_nested_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks

def test_split_python_code():
    path = 'huixiangdou/main.py'
    with open(path) as f:
        content = f.read()
    chunks = split_python_code(filepath=path, text=content, metadata={'test': 'meta'})
    for chunk in chunks:
        print(chunk)

def test_bm25_load():
    bm25 = BM25Okapi()
    bm25.load('./')
    query_text = 'what is the weather'
    res = bm25.get_top_n(query=query_text.split(' '))
    print(res)
    res = bm25.get_top_n(query=query_text)
    print(res)

def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
    return (kimi_token, serper_token)

def build_config_path():
    config_path = 'config-2G.ini'
    kimi_token, _ = load_secret()
    config = None
    with open(config_path) as f:
        config = pytoml.load(f)
        config['feature_store']['embedding_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['feature_store']['reranker_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['llm']['server']['remote_api_key'] = kimi_token
    config_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp_file:
        tomlstr = pytoml.dumps(config)
        temp_file.write(tomlstr.encode('utf8'))
        config_path = temp_file.name
    return config_path

def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
    return (kimi_token, serper_token)

def test_serper():
    config_path = 'config-2G.ini'
    _, serper_token = load_secret()
    config = None
    with open(config_path) as f:
        config = pytoml.load(f)
        config['web_search']['engine'] = 'serper'
        config['web_search']['serper_x_api_key'] = serper_token
    config_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp_file:
        tomlstr = pytoml.dumps(config)
        temp_file.write(tomlstr.encode('utf8'))
        config_path = temp_file.name
    engine = WebSearch(config_path=config_path)
    articles, error = engine.get(query='mmpose installation')
    assert error is None
    assert len(articles[0]) > 100
    assert articles[0].brief == articles[0].content
    os.remove(temp_file.name)

def load_secret():
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        return json_obj

def test_llm_backend_fail():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    server = HybridLLMServer(llm_config=llm_config)
    _, error = server.chat(prompt='hello', history=[], backend='kimi')
    logger.error(error)
    assert error is not None
    _, error = server.chat(prompt='hello', history=[], backend='deepseek')
    logger.error(error)
    assert error is not None
    _, error = server.chat(prompt='hello', history=[], backend='zhipuai')
    logger.error(error)
    assert error is not None
    _, error = server.chat(prompt='hello', history=[], backend='xi-api')
    logger.error(error)
    assert error is not None

def test_kimi_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    secrets = load_secret()
    llm_config['server']['remote_type'] = 'kimi'
    llm_config['server']['remote_api_key'] = secrets['kimi']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)
    response, error = server.chat(prompt=PROMPT, history=[], backend='kimi')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0

def test_zhipu_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    secrets = load_secret()
    llm_config['server']['remote_type'] = 'zhipuai'
    llm_config['server']['remote_api_key'] = secrets['zhipuai']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)
    response, error = server.chat(prompt=PROMPT, history=[], backend='zhipuai')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0

def test_deepseek_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    secrets = load_secret()
    llm_config['server']['remote_type'] = 'deepseek'
    llm_config['server']['remote_api_key'] = secrets['deepseek']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)
    response, error = server.chat(prompt=PROMPT, history=[], backend='deepseek')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0

def test_step_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    secrets = load_secret()
    llm_config['server']['remote_type'] = 'step'
    llm_config['server']['remote_api_key'] = secrets['step']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)
    response, error = server.chat(prompt=PROMPT, history=[], backend='step')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0

def test_puyu_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    secrets = load_secret()
    llm_config['server']['remote_type'] = 'puyu'
    llm_config['server']['remote_api_key'] = secrets['puyu']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)
    response, error = server.chat(prompt=PROMPT, history=[], backend='puyu')
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None

def test_siliconcloud_pass():
    remote_only_config = 'config-2G.ini'
    llm_config = None
    with open(remote_only_config, encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    secrets = load_secret()
    llm_config['server']['remote_type'] = 'siliconcloud'
    llm_config['server']['remote_api_key'] = secrets['siliconcloud']
    print('testing {}'.format(llm_config['server']))
    server = HybridLLMServer(llm_config=llm_config)
    response, error = server.chat(prompt=PROMPT, history=[], backend='siliconcloud')
    logger.info('siliconcloud response {}'.format(response))
    score = get_score(relation=response, default=0)
    assert score >= 5
    assert error is None
    assert len(response) > 0

def test_internlm_local():
    wrapper = InferenceWrapper(llm_local_path)
    repeat = 1
    for i in range(repeat):
        resp = wrapper.chat(prompt=PROMPT)
        logger.info(resp)
        logger.info(get_score(relation=resp))
    del wrapper

def test_internlm_local_():
    with open('config.ini', encoding='utf8') as f:
        llm_config = pytoml.load(f)['llm']
    llm_config['server']['local_llm_path'] = llm_local_path
    server = HybridLLMServer(llm_config)
    resp, error = server.chat(prompt=PROMPT)
    print(resp)
    del server

def load_secret():
    kimi_token = ''
    serper_token = ''
    with open('unittest/token.json') as f:
        json_obj = json.load(f)
        kimi_token = json_obj['kimi']
        serper_token = json_obj['serper']
        sg_token = json_obj['sg']
    return (kimi_token, serper_token, sg_token)

def build_config_path():
    config_path = 'config-2G.ini'
    kimi_token, serper_token, sg_token = load_secret()
    config = None
    with open(config_path) as f:
        config = pytoml.load(f)
        config['web_search']['engine'] = 'serper'
        config['web_search']['serper_x_api_key'] = serper_token
        config['feature_store']['embedding_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['feature_store']['reranker_model_path'] = '/data2/khj/bce-embedding-base_v1/'
        config['llm']['server']['remote_api_key'] = kimi_token
        config['worker']['enable_sg_search'] = 1
        config['sg_search']['src_access_token'] = sg_token
    config_path = None
    with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp_file:
        tomlstr = pytoml.dumps(config)
        temp_file.write(tomlstr.encode('utf8'))
        config_path = temp_file.name
    return config_path

class OpenXLabWorker:
    """The OpenXLab Worker class orchestrates the logic of handling user queries,
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
        self.config_path = config_path
        self.config = None
        self.language = language
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')
        self.context_max_length = -1
        llm_config = self.config['llm']
        self.context_max_length = llm_config['server']['remote_llm_max_text_length']
        if self.language == 'zh':
            self.TOPIC_TEMPLATE = '告诉我这句话的主题，直接说主题不要解释：“{}”'
            self.SCORING_QUESTION_TEMPLATE = '“{}”\n请仔细阅读以上内容，判断句子是否是个疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
            self.SCORING_RELAVANCE_TEMPLATE = '问题：“{}”\n材料：“{}”\n请仔细阅读以上内容，判断问题和材料的关联度，用0～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n'
            self.KEYWORDS_TEMPLATE = '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。搜索参数类型 string， 内容是短语或关键字，以空格分隔。\n你现在是{}交流群里的技术助手，用户问“{}”，你打算通过谷歌搜索查询相关资料，请提供用于搜索的关键字或短语，不要解释直接给出关键字或短语。'
            self.SECURITY_TEMAPLTE = '判断以下句子是否涉及政治、辱骂、色情、恐暴、宗教、网络暴力、种族歧视等违禁内容，结果用 0～10 表示，不要解释直接给出得分。判断标准：涉其中任一问题直接得 10 分；完全不涉及得 0 分。直接给得分不要解释：“{}”'
            self.PERPLESITY_TEMPLATE = '“question:{} answer:{}”\n阅读以上对话，answer 是否在表达自己不知道，回答越全面得分越少，用0～10表示，不要解释直接给出得分。\n判断标准：准确回答问题得 0 分；答案详尽得 1 分；知道部分答案但有不确定信息得 8 分；知道小部分答案但推荐求助其他人得 9 分；不知道任何答案直接推荐求助别人得 10 分。直接打分不要解释。'
            self.SUMMARIZE_TEMPLATE = '{} \n 仔细阅读以上内容，总结得简短有力点'
            self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'
        else:
            self.TOPIC_TEMPLATE = 'Tell me the theme of this sentence, just state the theme without explanation: "{}"'
            self.SCORING_QUESTION_TEMPLATE = '"{}"\nPlease read the content above carefully and judge whether the sentence is a thematic question. Rate it on a scale of 0-10. Only provide the score, no explanation.\nThe criteria are as follows: a sentence gets 10 points if it has a subject, predicate, object and is a question; points are deducted for missing subject, predicate or object; declarative sentences get 0 points; sentences that are not questions also get 0 points. Just give the score, no explanation.'
            self.SCORING_RELAVANCE_TEMPLATE = 'Question: "{}", Background Information: "{}"\nPlease read the content above carefully and assess the relevance between the question and the material on a scale of 0-10. The scoring standard is as follows: extremely relevant gets 10 points; completely irrelevant gets 0 points. Only provide the score, no explanation needed.'
            self.KEYWORDS_TEMPLATE = 'Google search is a general-purpose search engine that can be used to access the internet, look up encyclopedic knowledge, keep abreast of current affairs and more. Search parameters type: string, content consists of phrases or keywords separated by spaces.\nYou are now the assistant in the "{}" communication group. A user asked "{}", you plan to use Google search to find related information, please provide the keywords or phrases for the search, no explanation, just give the keywords or phrases.'
            self.SECURITY_TEMAPLTE = 'Evaluate whether the following sentence involves prohibited content such as politics, insult, pornography, terror, religion, cyber violence, racial discrimination, etc., rate it on a scale of 0-10, do not explain, just give the score. The scoring standard is as follows: any violation directly gets 10 points; completely unrelated gets 0 points. Give the score, no explanation: "{}"'
            self.PERPLESITY_TEMPLATE = "Question: {} Answer: {}\nRead the dialogue above, does the answer express that they don't know? The more comprehensive the answer, the lower the score. Rate it on a scale of 0-10, no explanation, just give the score.\nThe scoring standard is as follows: an accurate answer to the question gets 0 points; a detailed answer gets 1 point; knowing some answers but having uncertain information gets 8 points; knowing a small part of the answer but recommends seeking help from others gets 9 points; not knowing any of the answers and directly recommending asking others for help gets 10 points. Just give the score, no explanation."
            self.SUMMARIZE_TEMPLATE = '"{}" \n Read the content above carefully, summarize it in a short and powerful way.'
            self.GENERATE_TEMPLATE = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'

    def security_content(self, tracker, response: str):
        return True

    async def single_judge(self, prompt, tracker, throttle: int, default: int, **kwargs):
        """Generates a score based on the prompt, and then compares it to
        threshold.

        Args:
            prompt (str): The prompt for the language model.
            tracker (obj): An instance of QueryTracker logs the operations.
            throttle (int): Threshold value to compare the score against.
            default (int): Default score to be assigned in case of failure in score calculation.  # noqa E501

        Returns:
            bool: True if the score surpasses the throttle, otherwise False.
        """
        if prompt is None or len(prompt) == 0:
            return False
        score = default
        relation = await self.llm.chat(prompt=prompt)
        tracker.log('score' + prompt[0:20], [relation, throttle, default])
        filtered_relation = ''.join([c for c in relation if c.isdigit()])
        try:
            score_str = re.sub('[^\\d]', ' ', filtered_relation).strip()
            score = int(score_str.split(' ')[0])
        except Exception as e:
            logger.error(str(e))
        if score >= throttle:
            return True
        return False

    async def generate(self, query, history, retriever, groupname):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (str): User's query.
            history (list): Chat history.
            groupname (str): The group name in which user asked the query.

        Returns:
            ErrorCode: An error code indicating the status of response generation.  # noqa E501
            str: Generated response to the user query.
        """
        response = ''
        reborn_code = ErrorCode.SUCCESS
        tracker = QueryTracker(self.config['worker']['save_path'])
        tracker.log('input', [query, history, groupname])
        if not await self.single_judge(prompt=self.SCORING_QUESTION_TEMPLATE.format(query), tracker=tracker, throttle=6, default=2):
            response = await self.llm.chat(prompt=query, history=history)
            return (ErrorCode.NOT_A_QUESTION, response, [])
        topic = await self.llm.chat(self.TOPIC_TEMPLATE.format(query))
        tracker.log('topic', topic)
        if len(topic) < 2:
            return (ErrorCode.NO_TOPIC, response, [])
        chunk, db_context, retrieve_ref, context_texts = retriever.query(topic, context_max_length=self.context_max_length - 2 * len(self.GENERATE_TEMPLATE))
        if db_context is None or len(db_context) < 1:
            tracker.log('topic feature store reject')
            chunk, db_context, retrieve_ref, context_texts = retriever.query(query, context_max_length=self.context_max_length - 2 * len(self.GENERATE_TEMPLATE))
            if db_context is None or len(db_context) < 1:
                return (ErrorCode.UNRELATED, response, retrieve_ref)
        logger.info('fetch context length {}'.format(len(db_context)))
        prompt, history = self.llm.build_prompt(instruction=query, context=db_context, history_pair=history, template=self.GENERATE_TEMPLATE)
        response = await self.llm.chat(prompt=prompt, history=history)
        tracker.log('feature store doc', [chunk, response])
        if response is not None and len(response) < 1:
            return (ErrorCode.INTERNAL_ERROR, 'LLM API 没给回复，见 https://github.com/InternLM/HuixiangDou/issues/214 ', retrieve_ref)
        if response is not None and len(response) > 0:
            prompt = self.PERPLESITY_TEMPLATE.format(query, response)
            if not await self.single_judge(prompt=prompt, tracker=tracker, throttle=9, default=0):
                if not self.security_content(tracker, response):
                    return (ErrorCode.SECURITY, '检测到敏感内容，无法显示', retrieve_ref)
                return (ErrorCode.SUCCESS, response, retrieve_ref)
        web = WebSearch(config_path=self.config_path)
        if len(web.load_key()) < 1:
            return (ErrorCode.BAD_ANSWER, response, [])
        use_ref = []
        try:
            web_context = ''
            articles, error = web.get(query=topic, max_article=2)
            if error is not None:
                return (ErrorCode.WEB_SEARCH_FAIL, response, [])
            tracker.log('search returned')
            for article in articles:
                if len(article) > 0 and len(web_context) < self.context_max_length:
                    if len(article) > self.context_max_length:
                        article.cut(0, self.context_max_length - 2 * len(self.SCORING_RELAVANCE_TEMPLATE))
                    if await self.single_judge(self.SCORING_RELAVANCE_TEMPLATE.format(query, str(article)), tracker=tracker, throttle=5, default=10):
                        web_context += '\n'
                        web_context += str(article)
                        use_ref.append(article.source)
            web_context = web_context[0:self.context_max_length]
            web_context = web_context.strip()
            if len(web_context) > 0:
                prompt, history = self.llm.build_prompt(instruction=query, context=web_context, history_pair=history, template=self.GENERATE_TEMPLATE)
                response = self.llm.chat(prompt=prompt, history=history)
            else:
                reborn_code = ErrorCode.NO_SEARCH_RESULT
            tracker.log('web response', [web_context, response, reborn_code])
        except Exception as e:
            logger.error(e)
        if response is not None and len(response) > 0:
            prompt = self.PERPLESITY_TEMPLATE.format(query, response)
            if await self.single_judge(prompt=prompt, tracker=tracker, throttle=9, default=0):
                reborn_code = ErrorCode.BAD_ANSWER
        if not self.security_content(tracker, response):
            return (ErrorCode.SECURITY, '回复可能包含不安全内容，无法显示', use_ref)
        if reborn_code != ErrorCode.SUCCESS:
            return (reborn_code, response, use_ref)
        return (ErrorCode.SUCCESS, response, use_ref)

def __init__(self, work_dir: str, config_path: str, language: str='zh'):
    """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
            language (str, optional): Specifies the language to be used. Defaults to 'zh' (Chinese).  # noqa E501
        """
    self.llm = LLM(config_path=config_path)
    self.config_path = config_path
    self.config = None
    self.language = language
    with open(config_path, encoding='utf8') as f:
        self.config = pytoml.load(f)
    if self.config is None:
        raise Exception('worker config can not be None')
    self.context_max_length = -1
    llm_config = self.config['llm']
    self.context_max_length = llm_config['server']['remote_llm_max_text_length']
    if self.language == 'zh':
        self.TOPIC_TEMPLATE = '告诉我这句话的主题，直接说主题不要解释：“{}”'
        self.SCORING_QUESTION_TEMPLATE = '“{}”\n请仔细阅读以上内容，判断句子是否是个疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
        self.SCORING_RELAVANCE_TEMPLATE = '问题：“{}”\n材料：“{}”\n请仔细阅读以上内容，判断问题和材料的关联度，用0～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n'
        self.KEYWORDS_TEMPLATE = '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。搜索参数类型 string， 内容是短语或关键字，以空格分隔。\n你现在是{}交流群里的技术助手，用户问“{}”，你打算通过谷歌搜索查询相关资料，请提供用于搜索的关键字或短语，不要解释直接给出关键字或短语。'
        self.SECURITY_TEMAPLTE = '判断以下句子是否涉及政治、辱骂、色情、恐暴、宗教、网络暴力、种族歧视等违禁内容，结果用 0～10 表示，不要解释直接给出得分。判断标准：涉其中任一问题直接得 10 分；完全不涉及得 0 分。直接给得分不要解释：“{}”'
        self.PERPLESITY_TEMPLATE = '“question:{} answer:{}”\n阅读以上对话，answer 是否在表达自己不知道，回答越全面得分越少，用0～10表示，不要解释直接给出得分。\n判断标准：准确回答问题得 0 分；答案详尽得 1 分；知道部分答案但有不确定信息得 8 分；知道小部分答案但推荐求助其他人得 9 分；不知道任何答案直接推荐求助别人得 10 分。直接打分不要解释。'
        self.SUMMARIZE_TEMPLATE = '{} \n 仔细阅读以上内容，总结得简短有力点'
        self.GENERATE_TEMPLATE = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'
    else:
        self.TOPIC_TEMPLATE = 'Tell me the theme of this sentence, just state the theme without explanation: "{}"'
        self.SCORING_QUESTION_TEMPLATE = '"{}"\nPlease read the content above carefully and judge whether the sentence is a thematic question. Rate it on a scale of 0-10. Only provide the score, no explanation.\nThe criteria are as follows: a sentence gets 10 points if it has a subject, predicate, object and is a question; points are deducted for missing subject, predicate or object; declarative sentences get 0 points; sentences that are not questions also get 0 points. Just give the score, no explanation.'
        self.SCORING_RELAVANCE_TEMPLATE = 'Question: "{}", Background Information: "{}"\nPlease read the content above carefully and assess the relevance between the question and the material on a scale of 0-10. The scoring standard is as follows: extremely relevant gets 10 points; completely irrelevant gets 0 points. Only provide the score, no explanation needed.'
        self.KEYWORDS_TEMPLATE = 'Google search is a general-purpose search engine that can be used to access the internet, look up encyclopedic knowledge, keep abreast of current affairs and more. Search parameters type: string, content consists of phrases or keywords separated by spaces.\nYou are now the assistant in the "{}" communication group. A user asked "{}", you plan to use Google search to find related information, please provide the keywords or phrases for the search, no explanation, just give the keywords or phrases.'
        self.SECURITY_TEMAPLTE = 'Evaluate whether the following sentence involves prohibited content such as politics, insult, pornography, terror, religion, cyber violence, racial discrimination, etc., rate it on a scale of 0-10, do not explain, just give the score. The scoring standard is as follows: any violation directly gets 10 points; completely unrelated gets 0 points. Give the score, no explanation: "{}"'
        self.PERPLESITY_TEMPLATE = "Question: {} Answer: {}\nRead the dialogue above, does the answer express that they don't know? The more comprehensive the answer, the lower the score. Rate it on a scale of 0-10, no explanation, just give the score.\nThe scoring standard is as follows: an accurate answer to the question gets 0 points; a detailed answer gets 1 point; knowing some answers but having uncertain information gets 8 points; knowing a small part of the answer but recommends seeking help from others gets 9 points; not knowing any of the answers and directly recommending asking others for help gets 10 points. Just give the score, no explanation."
        self.SUMMARIZE_TEMPLATE = '"{}" \n Read the content above carefully, summarize it in a short and powerful way.'
        self.GENERATE_TEMPLATE = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'

class WechatAgent:

    @classmethod
    def action(cls, body: WechatRequest, suffix: str) -> Union[BaseBody, WechatResponse]:
        feature_store_id = QaLibCache.get_qalib_feature_store_id_by_suffix(suffix)
        hxd_info = QaLibCache.get_qalib_info(feature_store_id)
        if not hxd_info:
            logger.error(f'[wechat] suffix:{suffix} get feature store failed, omit wechat message callback')
            return standard_error_response(biz_constant.ERR_QALIB_INFO_NOT_FOUND)
        ChatCache.mark_agent_used(body.groupname, ChatType.WECHAT)
        chat_svc = ChatService(None, None, hxd_info)
        query_id = ''
        if body.query.type != WechatType.Poll:
            query_id = chat_svc.generate_query_id(body.query.content)
        chat_request_body = None
        if body.query.type == WechatType.Image:
            path = chat_svc.gen_image_store_path(query_id, 'i', ChatType.WECHAT)
            cls._store_image(path, body.query.content)
            chat_request_body = ChatRequestBody(images=[path])
        elif body.query.type == WechatType.Poll:
            return cls._fetch_response(feature_store_id)
        else:
            chat_request_body = ChatRequestBody(content=body.query.content)
        unique_id = body.username + '@' + body.groupname
        chat_svc.chat_by_agent(chat_request_body, ChatType.WECHAT, body, unique_id, query_id)
        ChatCache.record_query_id_to_fetch(feature_store_id, query_id)
        return WechatResponse()

    @classmethod
    def _store_image(cls, path: str, url: str) -> bool:
        response = requests.get(url)
        if not response or response.status_code != 200:
            logger.error(f'[wechat] get image: {url} binary failed, code: {response.status_code}, msg: {response.content}')
            return False
        with open(path, mode='wb') as fout:
            fout.write(response.content)
        return True

    @classmethod
    def _fetch_response(cls, feature_store_id: str) -> WechatResponse:
        ret = WechatResponse()
        query_id_list = ChatCache.mget_query_id_to_fetch(feature_store_id)
        if len(query_id_list) == 0:
            logger.debug(f'[wechat] feature_store_id: {feature_store_id} has no response yet')
            return ret
        complete_query_id_list = []
        l = []
        query_infos = ChatCache.mget_query_info(query_id_list, feature_store_id)
        for item in query_infos:
            if item.response:
                l.append(WechatPollItem(req=WechatRequest.model_validate_json(json.dumps(item.detail)), rsp=item.response))
                complete_query_id_list.append(item.queryId)
        ret.root = l
        ChatCache.mark_query_id_complete(feature_store_id, complete_query_id_list)
        return ret

@classmethod
def _store_image(cls, path: str, url: str) -> bool:
    response = requests.get(url)
    if not response or response.status_code != 200:
        logger.error(f'[wechat] get image: {url} binary failed, code: {response.status_code}, msg: {response.content}')
        return False
    with open(path, mode='wb') as fout:
        fout.write(response.content)
    return True

def read_config_ini_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == 'config.ini':
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = pytoml.load(f)
                    print((file_path, config['llm']['server']['remote_llm_max_text_length']))
                    config['llm']['server']['remote_llm_max_text_length'] = 40000
                    with open(file_path, 'w', encoding='utf8') as f:
                        pytoml.dump(config, f)
                except Exception as e:
                    print(f'An error occurred while reading {file_path}: {e}')

def on_language_changed(value: str):
    global language
    print(value)
    language = value

def on_pipeline_changed(value: str):
    global pipeline
    print(value)
    pipeline = value

def on_web_search_changed(value: str):
    global enable_web_search
    print(value)
    if 'no' in value:
        enable_web_search = False
    else:
        enable_web_search = True

def on_code_search_changed(value: str):
    global enable_code_search
    print(value)
    if 'no' in value:
        enable_code_search = False
    else:
        enable_code_search = True

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

def set_entity(self, entities: List[str]):
    json_str = json.dumps(entities, ensure_ascii=False)
    with open(self.entity_path, 'w') as f:
        f.write(json_str)
    self.entities = entities
    if self.ignore_case:
        for id, value in enumerate(self.entities):
            self.entities[id] = value.lower()

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

def read_and_save(file: FileName):
    if os.path.exists(file.copypath):
        logger.info('already exist, skip load')
        return
    file_opr = FileOperation()
    logger.info('reading {}, would save to {}'.format(file.origin, file.copypath))
    content, error = file_opr.read(file.origin)
    if error is not None:
        logger.error('{} load error: {}'.format(file.origin, str(error)))
        return
    if content is None or len(content) < 1:
        logger.warning('{} empty, skip save'.format(file.origin))
        return
    with open(file.copypath, 'w') as f:
        f.write(content)

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

def test_reject(retriever: Retriever, sample: str=None):
    """Simple test reject pipeline."""
    if sample is None:
        real_questions = ['SAM 10个T 的训练集，怎么比比较公平呢~？速度上还有缺陷吧？', '想问下，如果只是推理的话，amp的fp16是不会省显存么，我看parameter仍然是float32，开和不开推理的显存占用都是一样的。能不能直接用把数据和model都 .half() 代替呢，相比之下amp好在哪里', 'mmdeploy支持ncnn vulkan部署么，我只找到了ncnn cpu 版本', '大佬们，如果我想在高空检测安全帽，我应该用 mmdetection 还是 mmrotate', '请问 ncnn 全称是什么', '有啥中文的 text to speech 模型吗?', '今天中午吃什么？', 'huixiangdou 是什么？', 'mmpose 如何安装？', '使用科研仪器需要注意什么？']
    else:
        with open(sample) as f:
            real_questions = json.load(f)
    for example in real_questions:
        relative, score = retriever.is_relative(example)
        if relative:
            logger.warning(f'process query: {example}')
        else:
            logger.error(f'reject query: {example}')
        if sample is not None:
            if relative:
                with open('workdir/positive.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
            else:
                with open('workdir/negative.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
    empty_cache()

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

def __init__(self, config_path: str) -> None:
    """Initialize the ChatClient with the path of the configuration
        file."""
    logger.warning('The `class ChatClient` will be removed on 20250935, use `class LLM` instead.')
    self.config_path = config_path
    self.llm_config = None
    with open(self.config_path, encoding='utf8') as f:
        config = pytoml.load(f)
        self.llm_config = config['llm']

class ParallelPipeline:
    """The ParallelPipeline class orchestrates the logic of handling user queries,
    generating responses and managing several aspects of a chat assistant. It
    enables feature storage, language model client setup, time scheduling and
    much more.

    Attributes:
        llm: A LLM instance that communicates with the language model.
        fs: An instance of FeatureStore for loading and querying features.
        config_path: A string indicating the path of the configuration file.
        config: A dictionary holding the configuration settings.
        context_max_length: An integer representing the maximum length of the context used by the language model.  # noqa E501

        Several template strings for various prompts are also defined.
    """

    def __init__(self, work_dir: str, config_path: str):
        """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
        """
        self.llm = LLM(config_path=config_path)
        self.retriever = CacheRetriever(config_path=config_path).get(work_dir=work_dir)
        self.config_path = config_path
        self.config = None
        with open(config_path, encoding='utf8') as f:
            self.config = pytoml.load(f)
        if self.config is None:
            raise Exception('worker config can not be None')

    async def generate(self, query: Union[Query, str], history: List[Tuple[str]]=[], language: str='zh', enable_web_search: bool=True, enable_code_search: bool=True):
        """Processes user queries and generates appropriate responses. It
        involves several steps including checking for valid questions,
        extracting topics, querying the feature store, searching the web, and
        generating responses from the language model.

        Args:
            query (Union[Query,str]): User's multimodal query.
            history (str): Chat history.
            language (str): zh or en.
            enable_web_search (bool): enable web search or not, default value is True.
            enable_code_search (bool): enable code search or not, default value is True.

        Returns:
            Session: Sync generator, this function would yield session which contains:
                ErrorCode: An error code indicating the status of response generation.  # noqa E501
                str: Generated response to the user query.
                references: List for referenced filename or web url
        """
        if type(query) is str:
            query = Query(text=query)
        sess = Session(query=query, history=history, log_path=self.config['worker']['save_path'])
        preproc = PreprocNode(self.config, self.llm, language)
        text2vec = Text2vecRetrieval(self.retriever)
        inverted_index = InvertedIndexRetrieval(self.retriever)
        coderetrieval = CodeRetrieval(self.retriever)
        websearch = WebSearchRetrieval(self.config, self.config_path, self.llm, language)
        reduce = ReduceGenerate(self.config, self.llm, self.retriever, language)
        direct_chat_states = [ErrorCode.QUESTION_TOO_SHORT, ErrorCode.NOT_A_QUESTION, ErrorCode.NO_TOPIC, ErrorCode.UNRELATED]
        async for sess in preproc.process(sess):
            if sess.code in direct_chat_states:
                async for resp in reduce.process(sess):
                    yield resp
                return
        tasks = [text2vec.process_coroutine(copy.deepcopy(sess)), inverted_index.process_coroutine(copy.deepcopy(sess))]
        if enable_web_search:
            tasks.append(websearch.process_coroutine(copy.deepcopy(sess)))
        if enable_code_search:
            tasks.append(coderetrieval.process_coroutine(copy.deepcopy(sess)))
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in task_results:
            if type(result) is Session:
                sess.parallel_chunks += result.parallel_chunks
                continue
            logger.error(result)
        async for sess in reduce.process(sess):
            yield sess
        return

def __init__(self, work_dir: str, config_path: str):
    """Constructs all the necessary attributes for the worker object.

        Args:
            work_dir (str): The working directory where feature files are located.
            config_path (str): The location of the configuration file.
        """
    self.llm = LLM(config_path=config_path)
    self.retriever = CacheRetriever(config_path=config_path).get(work_dir=work_dir)
    self.config_path = config_path
    self.config = None
    with open(config_path, encoding='utf8') as f:
        self.config = pytoml.load(f)
    if self.config is None:
        raise Exception('worker config can not be None')

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

def __init__(self, config_path: str, retry: int=1, language: str='zh') -> None:
    """Initializes the WebSearch object with the given config path and
        retry count."""
    self.search_config = None
    with open(config_path, encoding='utf8') as f:
        config = pytoml.load(f)
        self.search_config = types.SimpleNamespace(**config['web_search'])
    self.retry = retry
    self.language = language

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

def mark_as_processed(self):
    with open('record.txt', 'a') as f:
        f.write(self.fsid)
        f.write('\n')

def write_all_issues(owener, name, issues_list, max_issue_number):
    for j in range(len(issues_list)):
        issue_number = issues_list[j]['number']
        if issue_number >= max_issue_number:
            continue
        issue_body = issues_list[j]['body']
        issue_comments = get_all_comments(owener, name, issue_number)
        issue_title = issues_list[j]['title']
        forbidden_chars_pattern = '[<>:"/\\\\|?*]'
        issue_title = re.sub(forbidden_chars_pattern, ' ', issue_title)
        md_basename = f'{issue_number}_{issue_title}.md'
        md_question = issue_body
        md_answer = ''.join([f'#### 第{i['id']}条回复来自{i['user']} \n {i['body']} \n' for i in issue_comments])
        md_contents = f'## quesion\n\n    =========== question ===========\n    {issue_title}\n\n    {md_question}\n    =========== question ===========\n\n    ## answer\n\n    =========== answer ===========\n    {md_answer}\n    =========== answer ===========\n\n        '
        with open(os.path.join(EXPORT_DIR, md_basename), mode='w', encoding='utf-8') as file:
            file.write(md_contents)

def test_reject(retriever: Retriever, sample: str=None):
    """Simple test reject pipeline."""
    if sample is None:
        real_questions = ['SAM 10个T 的训练集，怎么比比较公平呢~？速度上还有缺陷吧？', '想问下，如果只是推理的话，amp的fp16是不会省显存么，我看parameter仍然是float32，开和不开推理的显存占用都是一样的。能不能直接用把数据和model都 .half() 代替呢，相比之下amp好在哪里', 'mmdeploy支持ncnn vulkan部署么，我只找到了ncnn cpu 版本', '大佬们，如果我想在高空检测安全帽，我应该用 mmdetection 还是 mmrotate', '请问 ncnn 全称是什么', '有啥中文的 text to speech 模型吗?', '今天中午吃什么？', 'huixiangdou 是什么？', 'mmpose 如何安装？', '使用科研仪器需要注意什么？']
    else:
        with open(sample) as f:
            real_questions = json.load(f)
    for example in real_questions:
        relative, _ = retriever.is_relative(example)
        if relative:
            logger.warning(f'process query: {example}')
        else:
            logger.error(f'reject query: {example}')
        if sample is not None:
            if relative:
                with open('workdir/positive.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
            else:
                with open('workdir/negative.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
    empty_cache()

def task1_intention():
    """Test prompt."""
    ret = []
    with open('data.json', encoding='utf8') as f:
        items = json.load(f)
    for idx, item in enumerate(items):
        question = item['question']
        prompt = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 1～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'.format(question)
        answer, _ = model.chat(tokenizer, prompt, history=[], top_k=1)
        print((answer, prompt))
        ret.append({'question': prompt, 'answer': answer})
        with open('task1_intention_internlm_prompt.json', 'w', encoding='utf8') as f:
            json.dump(list(ret), f, ensure_ascii=False, indent=2)
        print('{}/{}'.format(idx, len(items)))

def test():
    tools = [{'name_for_human': '谷歌搜索', 'name_for_model': 'google_search', 'description_for_model': '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。', 'parameters': [{'name': 'search_query', 'description': '搜索关键词或短语', 'required': True, 'schema': {'type': 'string'}}]}]
    history = []
    for query in ['请问mmdet3.0依赖mmcv哪个版本', 'openmmlab和上海 AI Lab 是什么关系', '如何安装 mmdeploy', 'ncnn 全称是啥', '如果我要从高空检测安全帽，我应该用 mmdet 还是 mmrotate ']:
        print(f"User's Query:\n{query}\n")
        response, history = llm_with_plugin(prompt=query, history=history, list_of_plugin_info=tools)
        print(f"Qwen's Response:\n{response}\n")

def filecontents(dirname: str):
    filepaths = files()
    for _, filepath in filepaths:
        with open(filepath) as f:
            content = f.read()
            if len(content) > 0:
                yield content

def load_newwords():
    words = []
    basename = './newwords'
    files = os.listdir(basename)
    for filename in files:
        filepath = os.path.join(basename, filename)
        with open(filepath, encoding='utf8') as f:
            words += json.load(f)
        print('load {}'.format(filepath))
    return words

