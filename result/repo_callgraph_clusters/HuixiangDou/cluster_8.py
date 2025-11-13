# Cluster 8

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

def get_nowait(self):
    """Equivalent to get(False)."""
    return self.get(False)

def test_create_fs():
    target = {'type': TaskCode.FS_ADD_DOC.value, 'payload': {'name': 'ailab 行政说明', 'feature_store_id': '9527', 'file_abs_base': '/root/huixiangdou-res/test-data', 'file_list': ['huixiangdou.md', '']}}
    base_dir = target['payload']['file_abs_base']
    file_list = [str(x) for x in list(Path(base_dir).glob('*'))]
    target['payload']['file_list'] = file_list
    print(target)
    task_in.put(json.dumps(target, ensure_ascii=False))
    out = task_out.get()
    print(out)

def test_update_sample():
    target = {'type': TaskCode.FS_UPDATE_SAMPLE.value, 'payload': {'name': 'ailab 行政说明', 'feature_store_id': '9527', 'positive': ['请问如何申请公寓？我是实习生但名下有房还行么？', '几十万的科研仪器不小心打碎了，我得自己付钱赔偿么'], 'negative': ['今天中午吃什么', 'ncnn 的作者是谁']}}
    print(target)
    task_in.put(json.dumps(target, ensure_ascii=False))
    out = task_out.get()
    print(out)

def test_update_pipeline():
    target = {'type': TaskCode.FS_UPDATE_PIPELINE.value, 'payload': {'name': 'ailab 行政说明', 'feature_store_id': '9527', 'web_search_token': ''}}
    print(target)
    task_in.put(json.dumps(target, ensure_ascii=False))
    out = task_out.get()
    print(out)

def test_chat():
    queries = ['请问公寓退房需要注意哪些事情？']
    for query in queries:
        target = {'type': TaskCode.CHAT.value, 'payload': {'query_id': 'ae86', 'feature_store_id': '9527', 'content': query, 'images': [], 'history': [{'sender': 0, 'content': '你好'}, {'sender': 0, 'content': '你是谁'}, {'sender': 1, 'content': '我是行政助手茴香豆'}]}}
        task_in.put(json.dumps(target, ensure_ascii=False))
        print(chat_out.get())

def callback_task_state(feature_store_id: str, code: int, _type: str, state: str, files_state: list=[]):
    resp = Queue(name='TaskResponse')
    target = {'feature_store_id': feature_store_id, 'code': code, 'type': _type, 'state': state, 'status': state, 'files_state': files_state}
    logger.debug(target)
    resp.put(json.dumps(target, ensure_ascii=False))

def callback_chat_state(feature_store_id: str, query_id: str, code: int, state: str, text: str, ref: list):
    que = Queue(name='ChatResponse')
    target = {'feature_store_id': feature_store_id, 'query_id': query_id, 'response': {'code': code, 'state': state, 'text': text, 'references': ref}}
    logger.debug(target)
    que.put(json.dumps(target, ensure_ascii=False))

def process():
    que = Queue(name='Task')
    fs_cache = CacheRetriever('config.ini')
    logger.info('start wait task queue..')
    while True:
        msg_pop = que.get(timeout=16)
        if msg_pop is None:
            continue
        msg, error = parse_json_str(msg_pop)
        logger.info(msg)
        if error is not None:
            raise error
        logger.debug(f'process {msg}')
        if msg.type == TaskCode.FS_ADD_DOC.value:
            fs_cache.pop(msg.payload.feature_store_id)
            build_feature_store(fs_cache, msg.payload)
        elif msg.type == TaskCode.FS_UPDATE_SAMPLE.value:
            fs_cache.pop(msg.payload.feature_store_id)
            update_sample(fs_cache, msg.payload)
        elif msg.type == TaskCode.FS_UPDATE_PIPELINE.value:
            update_pipeline(msg.payload)
        elif msg.type == TaskCode.CHAT.value:
            loop = always_get_an_event_loop()
            loop.run_until_complete(chat_with_featue_store(fs_cache, msg.payload))
        else:
            logger.warning(f'unknown type {msg}')

def get_hxd_token_by_cookie(cookies) -> Union[HxdToken, None]:
    return HxdToken(**str_util.parse_jwt(cookies.get(biz_const.HXD_COOKIE_KEY))) if cookies and cookies.get(biz_const.HXD_COOKIE_KEY) else None

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
def get_inference_number(cls) -> int:
    key = biz_constant.RDS_KEY_TOTAL_INFERENCE_NUMBER
    o = r.get(key)
    return o

def standard_error_response(error: dict, data=None) -> BaseBody:
    if not data:
        data = {}
    return BaseBody(msg=error.get('msg'), msgCode=error.get('code'), data=data)

def _get_hxd_token_by_cookie(cookies) -> Union[HxdToken, None]:
    return HxdToken(**str_util.parse_jwt(cookies.get(biz_const.HXD_COOKIE_KEY))) if cookies and cookies.get(biz_const.HXD_COOKIE_KEY) else None

def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    logger.info(lark.JSON.marshal(data))
    if data.header.event_type != 'im.message.receive_v1':
        return None
    msg = data.event.message
    if msg.chat_type != 'group':
        return None
    if msg.message_type != 'text':
        return None
    msg_id = msg.message_id
    group_id = msg.chat_id
    user_id = data.event.sender.sender_id.user_id
    content = json.loads(msg.content)['text']
    msg_time = msg.create_time
    json_str = json.dumps({'source': 'lark', 'msg_id': msg_id, 'user_id': user_id, 'content': content, 'group_id': group_id, 'msg_time': msg_time}, ensure_ascii=False) + '\n'
    que = None
    if is_revert_command(content):
        que = Queue(name='huixiangdou-high-priority')
    else:
        que = Queue(name='huixiangdou')
    que.put(json_str)
    logger.debug(f'save {json_str} to {que.key}')
    return None

@app.route('/fetch', methods=['POST'])
def fetch():
    revert_que = Queue(name='huixiangdou-high-priority')
    json_str = revert_que.get(timeout=1)
    if json_str is not None and len(json_str) > 0:
        json_obj = json.loads(json_str)
        return jsonify(json_obj)
    msg_que = Queue(name='huixiangdou')
    json_str = msg_que.get(timeout=3)
    if json_str is not None and len(json_str) > 0:
        json_obj = json.loads(json_str)
        return jsonify(json_obj)
    return jsonify({})

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

def get_nowait(self):
    """Equivalent to get(False)."""
    return self.get(False)

class User:

    def __init__(self):
        self.history = []
        self.last_msg_time = time.time()
        self.last_msg_id = -1
        self.last_process_time = -1
        self._id = ''
        self.group_id = ''

    def __str__(self):
        obj = {'history': [], 'last_msg_time': self.last_msg_time, 'last_process_time': self.last_process_time, '_id': self._id}
        for item in self.history:
            obj['history'].append(convert_talk_to_dict(item))
        return json.dumps(obj, indent=2, ensure_ascii=False)

    def feed(self, msg: Message):
        if msg.type in ['url', 'image']:
            talk = Talk(query=msg.query, refs=msg.url)
            self.history.append(talk)
        else:
            talk = Talk(query=msg.query)
            self.history.append(talk)
        self.last_msg_time = time.time()
        self.last_msg_type = msg.type
        self.last_msg_id = msg._id
        self._id = msg.global_user_id
        self.group_id = msg.group_id

    def concat(self):
        if len(self.history) < 2:
            return
        ret = []
        merge_list = []
        now = time.time()
        for item in self.history:
            if abs(now - item.now) > 7200:
                continue
            answer = item.reply
            if answer is not None and len(answer) > 0:
                ret.append(item)
            else:
                merge_list.append(item.query)
        concat_query = '\n'.join(merge_list)
        concat_talk = Talk(query=concat_query)
        ret.append(concat_talk)
        self.history = ret

    def update_history(self, query, reply, refs):
        if type(refs) is list:
            talk = Talk(query=query, reply=reply, refs=tuple(refs))
        else:
            talk = Talk(query=query, reply=reply, refs=refs)
        self.history[-1] = talk
        self.last_process_time = time.time()

def __str__(self):
    obj = {'history': [], 'last_msg_time': self.last_msg_time, 'last_process_time': self.last_process_time, '_id': self._id}
    for item in self.history:
        obj['history'].append(convert_talk_to_dict(item))
    return json.dumps(obj, indent=2, ensure_ascii=False)

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

def node_to_jsonstr(instance):
    dict_instance = asdict(instance)
    dict_instance['_type'] = instance._type.value
    return json.dumps(dict_instance, ensure_ascii=False)

def relation_to_jsonstr(instance):
    dict_instance = asdict(instance)
    return json.dumps(dict_instance, ensure_ascii=False)

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

def get_nowait(self):
    """Equivalent to get(False)."""
    return self.get(False)

def multimodal(filepath: str, timeout=5):
    header = {'Content-Type': 'application/json'}
    data = {'image_path': filepath}
    try:
        resp = requests.post('http://127.0.0.1:9999/api', headers=header, data=json.dumps(data), timeout=timeout)
        resp_json = resp.json()
        content = resp_json['content']
        useful_char_cnt = 0
        scopes = [['a', 'z'], ['一', '鿿'], ['A', 'Z'], ['0', '9']]
        for char in content:
            for scope in scopes:
                if char >= scope[0] and char <= scope[1]:
                    useful_char_cnt += 1
                    break
        if useful_char_cnt / len(content) <= 0.5:
            return None
        if len(content) <= 100:
            return None
        return content
    except Exception as e:
        logger.error(str(e))
    return None

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

def __str__(self):
    return json.dumps(self.jsonify())

def get_issue_count(owner, name):
    headers = {'Authorization': TOKEN}
    url = f'https://api.github.com/repos/{owner}/{name}/issues'
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        issues = response.json()
        count = issues[0]['number']
    else:
        loguru.logger.error(f'Error fetching issues: {response.status_code}')
        loguru.logger.error(response.text)
        if 'limit' in response.text:
            loguru.logger.error('受到 github 限制，自动结束')
            exit()
        count = 0
    return count

def get_issues_list(owner, name, issue_count):
    headers = {'Authorization': TOKEN}
    GITHUB_API_URL = f'https://api.github.com/repos/{owner}/{name}/issues'
    pages = math.ceil(issue_count / 100) + 1
    loguru.logger.info(f'all_pages:{pages}')
    issues_list = []
    for page in range(pages):
        response = requests.get(GITHUB_API_URL, headers=headers, params={'state': 'all', 'per_page': 100, 'page': {page}})
        if response.status_code == 200:
            issues = response.json()
            for issue in issues:
                if 'issues' in issue['html_url'] and issue['state'] == 'closed':
                    issues_list.append({'number': issue['number'], 'title': issue['title'], 'html_url': issue['html_url'], 'body': issue['body'], 'closed_at': issue['closed_at']})
        else:
            loguru.logger.error(f'Error fetching issues: {response.status_code}')
            loguru.logger.error(response.text)
    return issues_list

def send():
    data_send = {'query_id': 'abb', 'groupname': '茴香豆测试群', 'username': '豆哥 123', 'query': {'type': 'text', 'content': '请问如何申请公寓？'}}
    resp = requests.post(base_url, headers=headers, data=json.dumps(data_send), timeout=10)
    resp_json = resp.json()
    print(resp_json)

def get():
    data_wait = {'query_id': 'abb', 'groupname': '茴香豆测试群', 'username': '豆哥 123', 'query': {'type': 'poll'}}
    resp = requests.post(base_url, headers=headers, data=json.dumps(data_wait), timeout=20)
    print(resp.text)

