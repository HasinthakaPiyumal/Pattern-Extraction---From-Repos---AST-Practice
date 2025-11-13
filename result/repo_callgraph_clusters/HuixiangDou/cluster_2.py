# Cluster 2

def read_requirements():
    lines = []
    with open('requirements.txt', 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            if 'textract' in line:
                continue
            if len(line) > 0:
                lines.append(line)
    return lines

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

def analyze_doc(home, path):
    print('analyze {}'.format(path))
    problem_list = []
    code_block = 0
    with open(path, encoding='utf8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith('```'):
                code_block = 1 - code_block
            if code_block > 0:
                continue
            if '[' in line and ']' in line and ('(' in line) and (')' in line):
                all = pattern.findall(line)
                for item in all:
                    if item.find('[') == item.find(']') - 1:
                        continue
                    offset = item.find('](')
                    if offset == -1:
                        continue
                    item = item[offset:]
                    start = item.find('(')
                    end = item.find(')')
                    ref = item[start + 1:end]
                    if ref.startswith('http') or ref.startswith('#'):
                        continue
                    if '.md#' in ref:
                        ref = ref[ref.find('#'):]
                    fullpath = os.path.join(home, ref)
                    if not os.path.exists(fullpath):
                        problem_list.append(ref)
            else:
                continue
    if len(problem_list) > 0:
        print(f'{path}:')
        for item in problem_list:
            print(f'\t {item}')
        print('\n')
        raise Exception('found link error')

def test_reranker():
    model = LLMReranker({'reranker_model_path': '/data2/khj/bce-reranker-base_v1'})
    query = 'apple'
    texts = ['roast banana', 'ice juice', 'red orange', 'apple pie']
    scores = model._sort(texts=texts, query=query)
    assert scores[0] == len(texts) - 1

def command(txt: str):
    """Executes a shell command and returns its output.

    Args:
        txt (str): Command to be executed in the shell.

    Returns:
        str: Output of the shell command execution.
    """
    logger.debug('cmd: {}'.format(txt))
    cmd = os.popen(txt)
    return cmd.read().rstrip().lstrip()

def test_ddgs():
    config_path = 'config-2G.ini'
    engine = WebSearch(config_path=config_path)
    articles, error = engine.get(query='mmpose installation')
    assert error is None
    assert len(articles[0]) > 100

def test_parse_zhihu():
    config_path = 'config-2G.ini'
    engine = WebSearch(config_path=config_path)
    article = engine.fetch_url(query='', target_link='https://zhuanlan.zhihu.com/p/699164101')
    if article is not None:
        assert check_str_useful(article.content)

def test_parse_hljnews():
    config_path = 'config-2G.ini'
    engine = WebSearch(config_path=config_path)
    article = engine.fetch_url(query='', target_link='http://www.hljnews.cn/ljxw/content/2023-10/17/content_729976.html?vp-fm')
    if article is not None:
        assert check_str_useful(article.content)

def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host

def redis_port():
    port = os.getenv('REDIS_PORT')
    if not port:
        logger.debug('REDIS_PORT not set, try 6379')
        port = 6379
    return port

def redis_passwd():
    passwd = os.getenv('REDIS_PASSWORD')
    if passwd is None or len(passwd) < 1:
        raise Exception('REDIS_PASSWORD not config')
    return passwd

def gen_suffix(feature_store_id: str) -> str:
    length = biz_const.HXD_FEATURE_STORE_SUFFIX_LENGTH
    if len(feature_store_id) <= length:
        return feature_store_id
    return feature_store_id[-length:]

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
def _get_content_type_when_at_user_exists(cls, mentions: List[MentionEvent]) -> LarkContentType:
    if not mentions or len(mentions) == 0:
        return LarkContentType.AT_OTHER_PERSON_TEXT
    for item in mentions:
        if not item.id.user_id or len(item.id.user_id) == 0:
            return LarkContentType.AT_BOT_TEXT
    return LarkContentType.AT_OTHER_PERSON_TEXT

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

class ChatCache:

    def __init__(self):
        pass

    @classmethod
    def set_query_request(cls, query_id: str, feature_store_id: str, info: ChatQueryInfo):
        cls._set_query_info(query_id, feature_store_id, info)

    @classmethod
    def set_query_response(cls, query_id: str, feature_store_id: str, response: ChatResponse) -> Union[ChatQueryInfo, None]:
        q = cls.get_query_info(query_id, feature_store_id)
        if not q:
            return None
        q.response = response
        cls._set_query_info(query_id, feature_store_id, q)
        return q

    @classmethod
    def get_query_info(cls, query_id: str, feature_store_id: str) -> Union[ChatQueryInfo, None]:
        key = biz_constant.RDS_KEY_QUERY_INFO + ':' + feature_store_id
        field = query_id
        o = r.hget(key, field)
        if not o or len(o) == 0:
            logger.error(f'feature_store_id: {feature_store_id} get query: {query_id} empty, omit')
            return None
        return ChatQueryInfo(**json.loads(o))

    @classmethod
    def mget_query_info(cls, query_id_list: List[str], feature_store_id: str) -> Union[List[ChatQueryInfo], None]:
        key = biz_constant.RDS_KEY_QUERY_INFO + ':' + feature_store_id
        o = r.hmget(key, query_id_list)
        if not o or len(o) == 0:
            logger.error(f'feature_store_id: {feature_store_id} mget: {query_id_list} empty, omit')
            return None
        ret = []
        for item in o:
            ret.append(ChatQueryInfo(**json.loads(item)))
        return ret

    @classmethod
    def _set_query_info(cls, query_id: str, feature_store_id: str, info: ChatQueryInfo):
        key = biz_constant.RDS_KEY_QUERY_INFO + ':' + feature_store_id
        field = query_id
        r.hset(key, field, info.model_dump_json())

    @classmethod
    def update_case_feedback(cls, feature_store_id: str, case_type: ChatCaseType, feedback: str) -> bool:
        try:
            name = f'{biz_constant.RDS_KEY_FEEDBACK_CASE}:{case_type}:{feature_store_id}'
            r.rpush(name, feedback)
            return True
        except Exception as e:
            logger.error(f'{e}')
            return False

    @classmethod
    def record_query_id_to_fetch(cls, feature_store_id: str, query_id: str):
        key = biz_constant.RDS_KEY_QUERY_ID_TO_FETCH + ':' + feature_store_id
        r.hset(key, query_id, 1)
        r.expire(key, biz_constant.HXD_CHAT_TTL)

    @classmethod
    def mget_query_id_to_fetch(cls, feature_store_id: str) -> List[str]:
        key = biz_constant.RDS_KEY_QUERY_ID_TO_FETCH + ':' + feature_store_id
        o = r.hgetall(key)
        if not o or len(o) == 0:
            return []
        ret = []
        for i in o.keys():
            ret.append(i)
        return ret

    @classmethod
    def mark_query_id_complete(cls, feature_store_id: str, query_id_list: List[str]):
        if len(query_id_list) == 0:
            return
        key = biz_constant.RDS_KEY_QUERY_ID_TO_FETCH + ':' + feature_store_id
        for item in query_id_list:
            r.hdel(key, item)

    @classmethod
    def mark_agent_used(cls, agent_identifier: str, agent: ChatType):
        field = agent_identifier
        if agent == ChatType.LARK:
            key = biz_constant.RDS_KEY_AGENT_LARK_USED
        else:
            key = biz_constant.RDS_KEY_AGENT_WECHAT_USED
        r.hset(key, field, 1)

    @classmethod
    def hlen_agent_used(cls, agent: ChatType) -> int:
        if agent == ChatType.LARK:
            key = biz_constant.RDS_KEY_AGENT_LARK_USED
        else:
            key = biz_constant.RDS_KEY_AGENT_WECHAT_USED
        o = r.hlen(key)
        return o

    @classmethod
    def mark_monthly_active(cls, feature_store_id: str):
        today_month = time_util.get_month_time_str(datetime.now())
        key = biz_constant.RDS_KEY_QALIB_ACTIVE + ':' + today_month
        r.hset(key, feature_store_id, 1)

    @classmethod
    def get_monthly_active(cls) -> int:
        today_month = time_util.get_month_time_str(datetime.now())
        key = biz_constant.RDS_KEY_QALIB_ACTIVE + ':' + today_month
        o = r.hlen(key)
        return o

    @classmethod
    def add_inference_number(cls):
        key = biz_constant.RDS_KEY_TOTAL_INFERENCE_NUMBER
        r.incr(key)

    @classmethod
    def get_inference_number(cls) -> int:
        key = biz_constant.RDS_KEY_TOTAL_INFERENCE_NUMBER
        o = r.get(key)
        return o

    @classmethod
    def mark_unique_inference_user(cls, user_identifier: str, agent: ChatType):
        key = biz_constant.RDS_KEY_USER_INFERENCE
        field = user_identifier + '@' + agent.name
        r.sadd(key, field)

    @classmethod
    def get_unique_inference_user_number(cls) -> int:
        key = biz_constant.RDS_KEY_USER_INFERENCE
        o = r.scard(key)
        return o

@classmethod
def mget_query_id_to_fetch(cls, feature_store_id: str) -> List[str]:
    key = biz_constant.RDS_KEY_QUERY_ID_TO_FETCH + ':' + feature_store_id
    o = r.hgetall(key)
    if not o or len(o) == 0:
        return []
    ret = []
    for i in o.keys():
        ret.append(i)
    return ret

def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host

def redis_port():
    port = os.getenv('REDIS_PORT')
    if port is None:
        logger.debug('REDIS_PORT not set, try 6379')
        port = 6379
    return port

def redis_passwd():
    passwd = os.getenv('REDIS_PASSWORD')
    if passwd is None or len(passwd) < 1:
        raise Exception('REDIS_PASSWORD not config')
    return passwd

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
def get_lark_encrypt_key(cls) -> str:
    return os.getenv('HUIXIANGDOU_LARK_ENCRYPT_KEY') if os.getenv('HUIXIANGDOU_LARK_ENCRYPT_KEY') else 'thisiskey'

@classmethod
def get_lark_verification_token(cls) -> str:
    return os.getenv('HUIXIANGDOU_LARK_VERIFY_TOKEN') if os.getenv('HUIXIANGDOU_LARK_VERIFY_TOKEN') else 'sMzyjKi9vMlEhKCZOVtBMhhl8x23z0AG'

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

def rerank(self, query: str, chunks: List[Chunk]):
    """Rerank faiss search results."""
    if not chunks:
        return []
    texts = []
    for chunk in chunks:
        texts.append(chunk.content_or_path)
    indexes = self._sort(texts=texts, query=query)
    return [chunks[i] for i in indexes]

def judge_language(text):
    global ZH_CN_CHAR_PATTERN
    if ZH_CN_CHAR_PATTERN is None:
        ZH_CN_CHAR_PATTERN = re.compile('[\\u4e00-\\u9fff]')
    global EN_CHAR_PATTERN
    if EN_CHAR_PATTERN is None:
        EN_CHAR_PATTERN = re.compile('[a-zA-Z]')
    chinese_count = len(ZH_CN_CHAR_PATTERN.findall(text))
    english_count = len(EN_CHAR_PATTERN.findall(text))
    if chinese_count > english_count:
        return 'zh_cn'
    else:
        return 'en'

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

def __init__(self, webhook, secret=None, pc_slide=False, fail_notice=False):
    """Init with hook url."""
    self.headers = {'Content-Type': 'application/json; charset=utf-8'}
    logger.debug(f'webhook {webhook}')
    logger.error('This class would be deprecated in 2024.10.10')
    self.webhook = webhook
    self.secret = secret
    self.pc_slide = pc_slide
    self.fail_notice = fail_notice

def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host

def redis_port():
    port = os.getenv('REDIS_PORT')
    if not port:
        logger.debug('REDIS_PORT not set, try 6379')
        port = 6379
    return port

def redis_passwd():
    passwd = os.getenv('REDIS_PASSWORD')
    if passwd is None or len(passwd) < 1:
        raise Exception('REDIS_PASSWORD not config')
    return passwd

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

def search_key(xml_key: str):
    elements = root.findall('.//{}'.format(xml_key))
    content = ''
    if len(elements) > 0:
        content = elements[0].text
    return content

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

@DeprecationWarning
def os_run(cmd: str):
    ret = os.popen(cmd)
    ret = ret.read().rstrip().lstrip()
    return ret

def check_str_useful(content: str):
    useful_char_cnt = 0
    scopes = [['a', 'z'], ['一', '鿿'], ['A', 'Z'], ['0', '9']]
    for char in content:
        for scope in scopes:
            if char >= scope[0] and char <= scope[1]:
                useful_char_cnt += 1
                break
    if useful_char_cnt / len(content) <= 0.5:
        return False
    return True

class Text2vecNode(Node):
    """Text2vecNode is for retrieve from knowledge base."""

    def __init__(self, config: dict, llm: LLM, retriever: Retriever, language: str):
        self.llm = llm
        self.retriever = retriever
        llm_config = config['llm']
        self.context_max_length = llm_config['server']['remote_llm_max_text_length']
        if language == 'zh':
            self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_CN
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_CN
        else:
            self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_EN
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_EN
        self.max_length = self.context_max_length - 2 * len(self.GENERATE_TEMPLATE)
        self.language = language

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        """Try get reply with text2vec & rerank model."""
        sess.chunk, sess.knowledge, sess.references, context_texts = self.retriever.query(sess.query, context_max_length=self.max_length)
        sess.debug['Text2vecNode_chunk'] = sess.chunk
        if not sess.knowledge:
            sess.code = ErrorCode.UNRELATED
            yield sess
            return
        yield sess
        prompt = self.SCORING_RELAVANCE_TEMPLATE.format(sess.query.text, sess.chunk)
        truth, logs = await is_truth(llm=self.llm, prompt=prompt, throttle=5, default=10)
        sess.debug['Text2vecNode_chunk_relavance'] = logs
        if not truth:
            yield sess
            return
        citation = CitationGeneratePrompt(self.language)
        prompt = citation.build(texts=context_texts, question=sess.query.text)
        response = await self.llm.chat(prompt=prompt, history=sess.history)
        sess.code = ErrorCode.SUCCESS
        sess.response = response
        yield sess

def __init__(self, config: dict, llm: LLM, retriever: Retriever, language: str):
    self.llm = llm
    self.retriever = retriever
    llm_config = config['llm']
    self.context_max_length = llm_config['server']['remote_llm_max_text_length']
    if language == 'zh':
        self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_CN
        self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
        self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_CN
    else:
        self.TOPIC_TEMPLATE = TOPIC_TEMPLATE_EN
        self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
        self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_EN
    self.max_length = self.context_max_length - 2 * len(self.GENERATE_TEMPLATE)
    self.language = language

class WebSearchNode(Node):
    """WebSearchNode is for web search, use `ddgs` or `serper`"""

    def __init__(self, config: dict, config_path: str, llm: LLM, language: str):
        self.llm = llm
        self.config_path = config_path
        self.enable = config['worker']['enable_web_search']
        llm_config = config['llm']
        self.context_max_length = llm_config['server']['remote_llm_max_text_length']
        if language == 'zh':
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
            self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_CN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_CN
        else:
            self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
            self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_EN
            self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_EN
        self.max_length = self.context_max_length - 2 * len(self.GENERATE_TEMPLATE)
        self.language = language

    async def process(self, sess: Session) -> AsyncGenerator[Session, None]:
        """Try web search."""
        if not self.enable:
            logger.debug('disable web_search')
            yield sess
            return
        engine = WebSearch(config_path=self.config_path)
        prompt = self.KEYWORDS_TEMPLATE.format(sess.groupname, sess.query.text)
        search_keywords = await self.llm.chat(prompt)
        sess.debug['WebSearchNode_keywords'] = prompt
        articles, error = engine.get(query=search_keywords, max_article=2)
        if error is not None:
            sess.code = ErrorCode.WEB_SEARCH_FAIL
            yield sess
            return
        texts = []
        for article_id, article in enumerate(articles):
            article.cut(0, self.max_length)
            sess.web_knowledge += '\n'
            sess.web_knowledge += article.content
            sess.references.append(article.source)
            texts.append(article.content)
        sess.web_knowledge = sess.web_knowledge[0:self.max_length].strip()
        if len(sess.web_knowledge) < 1:
            sess.code = ErrorCode.NO_SEARCH_RESULT
            yield sess
            return
        citation = CitationGeneratePrompt(self.language)
        prompt = citation.build(texts=texts, question=sess.query.text)
        sess.response = await self.llm.chat(prompt=prompt, history=sess.history)
        sess.code = ErrorCode.SUCCESS
        yield sess

def __init__(self, config: dict, config_path: str, llm: LLM, language: str):
    self.llm = llm
    self.config_path = config_path
    self.enable = config['worker']['enable_web_search']
    llm_config = config['llm']
    self.context_max_length = llm_config['server']['remote_llm_max_text_length']
    if language == 'zh':
        self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_CN
        self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_CN
        self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_CN
    else:
        self.SCORING_RELAVANCE_TEMPLATE = SCORING_RELAVANCE_TEMPLATE_EN
        self.KEYWORDS_TEMPLATE = KEYWORDS_TEMPLATE_EN
        self.GENERATE_TEMPLATE = GENERATE_TEMPLATE_CITATION_HEAD_EN
    self.max_length = self.context_max_length - 2 * len(self.GENERATE_TEMPLATE)
    self.language = language

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

def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host

def redis_port():
    port = os.getenv('REDIS_PORT')
    if port is None:
        logger.debug('REDIS_PORT not set, try 6379')
        port = 6379
    return port

def redis_passwd():
    passwd = os.getenv('REDIS_PASSWORD')
    if passwd is None or len(passwd) < 1:
        raise Exception('REDIS_PASSWORD not config')
    return passwd

class Article:

    def __init__(self, content: str='', source='', brief=''):
        self.content = content
        self.source = source
        if len(brief) < 1:
            self.brief = content
        else:
            self.brief = brief

    def __str__(self):
        return self.content

    def __len__(self):
        return len(self.content)

    def cut(self, start_index, end_index):
        self.source = self.source[start_index:end_index]

def __init__(self, content: str='', source='', brief=''):
    self.content = content
    self.source = source
    if len(brief) < 1:
        self.brief = content
    else:
        self.brief = brief

def __len__(self):
    return len(self.content)

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

def default_model_info(self):
    backend = list(self.backends.keys())[0]
    instance = self.backends[backend]
    return instance.jsonify()

def build_input_text(chat_history, list_of_plugin_info) -> str:
    tools_text = []
    for plugin_info in list_of_plugin_info:
        tool = TOOL_DESC.format(name_for_model=plugin_info['name_for_model'], name_for_human=plugin_info['name_for_human'], description_for_model=plugin_info['description_for_model'], parameters=json.dumps(plugin_info['parameters'], ensure_ascii=False))
        if plugin_info.get('args_format', 'json') == 'json':
            tool += ' Format the arguments as a JSON object.'
        elif plugin_info['args_format'] == 'code':
            tool += ' Enclose the code within triple backticks (`) at the beginning and end of the code.'
        else:
            raise NotImplementedError
        tools_text.append(tool)
    tools_text = '\n\n'.join(tools_text)
    tools_name_text = ', '.join([plugin_info['name_for_model'] for plugin_info in list_of_plugin_info])
    im_start = '<|im_start|>'
    im_end = '<|im_end|>'
    prompt = f'{im_start}system\nYou are a helpful assistant.{im_end}'
    for i, (query, response) in enumerate(chat_history):
        if list_of_plugin_info:
            if len(chat_history) == 1 or i == len(chat_history) - 2:
                query = PROMPT_REACT.format(tools_text=tools_text, tools_name_text=tools_name_text, query=query)
        query = query.lstrip('\n').rstrip()
        response = response.lstrip('\n').rstrip()
        prompt += f'\n{im_start}user\n{query}{im_end}'
        prompt += f'\n{im_start}assistant\n{response}{im_end}'
    assert prompt.endswith(f'\n{im_start}assistant\n{im_end}')
    prompt = prompt[:-len(f'{im_end}')]
    return prompt

