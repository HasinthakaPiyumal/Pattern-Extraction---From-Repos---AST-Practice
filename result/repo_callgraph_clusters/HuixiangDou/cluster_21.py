# Cluster 21

class LoginService:

    def __init__(self, login: LoginBody, request: Request, response: Response):
        self.name = login.name
        self.password = login.password
        self.response = response
        self.request = request

    def _set_cookie(self, cookie_key, *jwt_payloads):
        self.response.set_cookie(key=cookie_key, value=str.gen_jwt(jwt_payloads[0][0], jwt_payloads[0][1], int(round(time.time() * 1000) + 604800000)), max_age=604800, expires=604800, secure=HuixiangDouEnv.get_cookie_secure(), samesite=HuixiangDouEnv.get_cookie_samesite())

    async def login(self):
        if not self.name or len(self.name) < 8:
            logger.error(f'login name={self.name} not valid.')
            return BaseBody(msg=biz_const.ERR_ACCESS_LOGIN.get('msg'), msgCode=biz_const.ERR_ACCESS_LOGIN.get('code'))
        o = r.hget(name=biz_const.RDS_KEY_LOGIN, key=self.name)
        gen_hashed_pass = bcrypt.hash(self.password)
        if not o:
            feature_store_id = str.gen_random_string()
            if not _create_qa_lib(self.name, gen_hashed_pass, feature_store_id):
                self.response.delete_cookie(key=biz_const.HXD_COOKIE_KEY)
                return BaseBody(msg=biz_const.ERR_ACCESS_CREATE.get('msg'), msgCode=biz_const.ERR_ACCESS_CREATE.get('code'))
            self._set_cookie(biz_const.HXD_COOKIE_KEY, [feature_store_id, self.name])
            return BaseBody(data={'exist': False, 'featureStoreId': feature_store_id})
        else:
            access_info = AccessInfo(**json.loads(bytes.decode(o)))
            if bcrypt.verify(self.password, access_info.hashpass):
                feature_store_id = access_info.featureStoreId
            else:
                return BaseBody(msg=biz_const.ERR_ACCESS_LOGIN.get('msg'), msgCode=biz_const.ERR_ACCESS_LOGIN.get('code'))
        self._set_cookie(biz_const.HXD_COOKIE_KEY, [feature_store_id, self.name])
        return BaseBody(data={'exist': True, 'featureStoreId': feature_store_id})

def _set_cookie(self, cookie_key, *jwt_payloads):
    self.response.set_cookie(key=cookie_key, value=str.gen_jwt(jwt_payloads[0][0], jwt_payloads[0][1], int(round(time.time() * 1000) + 604800000)), max_age=604800, expires=604800, secure=HuixiangDouEnv.get_cookie_secure(), samesite=HuixiangDouEnv.get_cookie_samesite())

class QaLibCache:

    def __init__(self):
        pass

    @classmethod
    def get_qalib_info(cls, feature_store_id: str) -> Union[QalibInfo, None]:
        name = biz_const.RDS_KEY_QALIB_INFO
        key = feature_store_id
        o = r.hget(name, key)
        if not o:
            logger.error(f'[qalib] feature_store_id: {feature_store_id}, get info empty')
            return None
        return QalibInfo(**json.loads(o))

    @classmethod
    def set_qalib_info(cls, feature_store_id: str, info: QalibInfo):
        name = biz_const.RDS_KEY_QALIB_INFO
        key = feature_store_id
        return r.hset(name, key, info.model_dump_json()) == 1

    @classmethod
    def init_qalib_info(cls, feature_store_id: str, status: int, name: str, suffix: str) -> bool:
        """add qalib info to qalib:info db.

        :param name:
        :param feature_store_id:
        :param status:
        :return:
        """
        wechat = Wechat(onMessageUrl=get_wechat_on_message_url(suffix))
        lark = Lark(encryptKey=HuixiangDouEnv.get_lark_encrypt_key(), verificationToken=HuixiangDouEnv.get_lark_verification_token(), eventUrl=get_lark_on_message_url())
        qalib_info = QalibInfo(featureStoreId=feature_store_id, status=status, name=name, wechat=wechat, lark=lark, suffix=suffix)
        if not cls.set_qalib_info(feature_store_id, qalib_info):
            logger.error(f'[qalib] feature_store_id: {feature_store_id}, init qalib info failed')
            r.hdel(biz_const.RDS_KEY_QALIB_INFO, feature_store_id)
            return False
        return True

    @classmethod
    def del_qalib_info(cls, feature_store_id: str) -> bool:
        """del qalib info to qalib:info db.

        :param feature_store_id:
        :return:
        """
        return True if r.hdel(biz_const.RDS_KEY_QALIB_INFO, feature_store_id) == 1 else False

    @classmethod
    def rewrite_qalib_docs(cls, feature_store_id: str, added_docs: List[str], file_base: str) -> bool:
        """update qalib's docs.

        :param feature_store_id:
        :param added_docs:
        :param file_base:
        :return:
        """
        try:
            info = cls.get_qalib_info(feature_store_id)
            if not info:
                return False
            info.docs = list(set(added_docs))
            info.docBase = file_base
            cls.set_qalib_info(feature_store_id, info)
            return True
        except Exception as e:
            logger.error(f'[qalib] feature_store_id: {feature_store_id}, update docs failed: {e}')
            return False

    @classmethod
    def update_qalib_docs(cls, feature_store_id: str, added_docs: List[str], file_base: str) -> bool:
        """update qalib's docs.

        :param feature_store_id:
        :param added_docs:
        :param file_base:
        :return:
        """
        try:
            info = cls.get_qalib_info(feature_store_id)
            if not info:
                return False
            raw_docs = info.docs
            if not raw_docs:
                raw_docs = []
            raw_docs.extend(added_docs)
            info.docs = list(set(raw_docs))
            info.docBase = file_base
            cls.set_qalib_info(feature_store_id, info)
            return True
        except Exception as e:
            logger.error(f'[qalib] feature_store_id: {feature_store_id}, update docs failed: {e}')
            return False

    @classmethod
    def get_sample_info(cls, feature_store_id: str) -> Union[QalibSample, None]:
        o = r.hget(name=biz_const.RDS_KEY_SAMPLE_INFO, key=feature_store_id)
        if not o:
            logger.info(f'[qalib] feature_store_id: {feature_store_id}, get empty sample')
            return None
        return QalibSample(**json.loads(o))

    @classmethod
    def set_sample_info(cls, feature_store_id: str, sample_info: QalibSample):
        r.hset(name=biz_const.RDS_KEY_SAMPLE_INFO, key=feature_store_id, value=sample_info.model_dump_json())

    @classmethod
    def set_suffix_to_qalib(cls, suffix: str, feature_store_id: str):
        r.hset(name=biz_const.RDS_KEY_SUFFIX_TO_QALIB, key=suffix, value=feature_store_id)

    @classmethod
    def get_qalib_feature_store_id_by_suffix(cls, suffix: str) -> Union[str, None]:
        o = r.hget(name=biz_const.RDS_KEY_SUFFIX_TO_QALIB, key=suffix)
        if not o:
            logger.error(f'[qalib] suffix: {suffix} has no qalib')
            return None
        return o.decode('utf-8')

    @classmethod
    def get_lark_info_by_app_id(cls, app_id: str) -> Union[str, None]:
        key = biz_const.RDS_KEY_LARK_CONFIG + ':' + app_id
        o = r.get(key)
        if not o:
            logger.error(f'f[lark] app_id: {app_id} has no record')
            return None
        return o.decode('utf-8')

    @classmethod
    def set_lark_info(cls, app_id: str, app_secret: str):
        key = biz_const.RDS_KEY_LARK_CONFIG + ':' + app_id
        r.set(key, app_secret)

@classmethod
def get_qalib_feature_store_id_by_suffix(cls, suffix: str) -> Union[str, None]:
    o = r.hget(name=biz_const.RDS_KEY_SUFFIX_TO_QALIB, key=suffix)
    if not o:
        logger.error(f'[qalib] suffix: {suffix} has no qalib')
        return None
    return o.decode('utf-8')

@classmethod
def get_lark_info_by_app_id(cls, app_id: str) -> Union[str, None]:
    key = biz_const.RDS_KEY_LARK_CONFIG + ':' + app_id
    o = r.get(key)
    if not o:
        logger.error(f'f[lark] app_id: {app_id} has no record')
        return None
    return o.decode('utf-8')

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

def generate_query_id(self, content):
    feature_store_id = self.hxd_info.featureStoreId
    raw = feature_store_id + content[-8:] + str(time.time())
    h = hashlib.sha3_512()
    h.update(raw.encode('utf-8'))
    q = h.hexdigest()
    return q[0:8]

def gen_jwt(feature_store_id: str, qa_name: str, expire: int) -> str:
    """
    :param feature_store_id:
    :param qa_name: 知识库名称
    :param expire: 过期时间 unix 时间戳
    :return: jwt
    """
    payload = {'iat': time.time(), 'jti': feature_store_id, 'qa_name': qa_name, 'exp': expire}
    token = jwt.encode(payload, HuixiangDouEnv.get_jwt_secret(), algorithm='HS256')
    return token

def parse_jwt(token: str) -> dict:
    hxd_token = jwt.decode(token, HuixiangDouEnv.get_jwt_secret(), algorithms='HS256')
    return hxd_token

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
def get_cookie_samesite(cls) -> str:
    return 'none' if HuixiangDouEnv.get_cookie_secure() else 'lax'

class RPM:

    def __init__(self, rpm: int=1000):
        self.rpm = rpm
        self.record = {'slot': self.get_minute_slot(), 'counter': 0}

    def get_minute_slot(self):
        current_time = time.time()
        dt_object = datetime.fromtimestamp(current_time)
        total_minutes_since_midnight = dt_object.hour * 60 + dt_object.minute
        return total_minutes_since_midnight

    def wait_sync(self, silent=False):
        current = time.time()
        dt_object = datetime.fromtimestamp(current)
        minute_slot = self.get_minute_slot()
        if self.record['slot'] == minute_slot:
            if self.record['counter'] >= self.rpm:
                next_minute = dt_object.replace(second=0, microsecond=0) + timedelta(minutes=1)
                _next = next_minute.timestamp()
                sleep_time = abs(_next - current)
                time.sleep(sleep_time)
                self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        else:
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        self.record['counter'] += 1
        if not silent:
            logger.debug(self.record)

    async def wait(self, silent=False):
        current = time.time()
        dt_object = datetime.fromtimestamp(current)
        minute_slot = self.get_minute_slot()
        if self.record['slot'] == minute_slot:
            if self.record['counter'] >= self.rpm:
                next_minute = dt_object.replace(second=0, microsecond=0) + timedelta(minutes=1)
                _next = next_minute.timestamp()
                sleep_time = abs(_next - current)
                asyncio.sleep(sleep_time)
                self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        else:
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        self.record['counter'] += 1
        if not silent:
            logger.debug(self.record)

def __init__(self, rpm: int=1000):
    self.rpm = rpm
    self.record = {'slot': self.get_minute_slot(), 'counter': 0}

def get_minute_slot(self):
    current_time = time.time()
    dt_object = datetime.fromtimestamp(current_time)
    total_minutes_since_midnight = dt_object.hour * 60 + dt_object.minute
    return total_minutes_since_midnight

def wait_sync(self, silent=False):
    current = time.time()
    dt_object = datetime.fromtimestamp(current)
    minute_slot = self.get_minute_slot()
    if self.record['slot'] == minute_slot:
        if self.record['counter'] >= self.rpm:
            next_minute = dt_object.replace(second=0, microsecond=0) + timedelta(minutes=1)
            _next = next_minute.timestamp()
            sleep_time = abs(_next - current)
            time.sleep(sleep_time)
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
    else:
        self.record = {'slot': self.get_minute_slot(), 'counter': 0}
    self.record['counter'] += 1
    if not silent:
        logger.debug(self.record)

class TPM:

    def __init__(self, tpm: int=20000):
        self.tpm = tpm
        self.record = {'slot': self.get_minute_slot(), 'counter': 0}

    def get_minute_slot(self):
        current_time = time.time()
        dt_object = datetime.fromtimestamp(current_time)
        total_minutes_since_midnight = dt_object.hour * 60 + dt_object.minute
        return total_minutes_since_midnight

    def wait_sync(self, token_count, silent=False):
        current = time.time()
        dt_object = datetime.fromtimestamp(current)
        minute_slot = self.get_minute_slot()
        self.record['counter'] += token_count
        if self.record['slot'] == minute_slot:
            if self.record['counter'] >= self.tpm:
                next_minute = dt_object.replace(second=0, microsecond=0) + timedelta(minutes=1)
                _next = next_minute.timestamp()
                sleep_time = abs(_next - current)
                time.sleep(sleep_time)
                self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        else:
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        if not silent:
            logger.debug(self.record)

    async def wait(self, token_count, silent=False):
        current = time.time()
        dt_object = datetime.fromtimestamp(current)
        minute_slot = self.get_minute_slot()
        self.record['counter'] += token_count
        if self.record['slot'] == minute_slot:
            if self.record['counter'] >= self.tpm:
                next_minute = dt_object.replace(second=0, microsecond=0) + timedelta(minutes=1)
                _next = next_minute.timestamp()
                sleep_time = abs(_next - current)
                asyncio.sleep(sleep_time)
                self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        else:
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
        if not silent:
            logger.debug(self.record)

def __init__(self, tpm: int=20000):
    self.tpm = tpm
    self.record = {'slot': self.get_minute_slot(), 'counter': 0}

def get_minute_slot(self):
    current_time = time.time()
    dt_object = datetime.fromtimestamp(current_time)
    total_minutes_since_midnight = dt_object.hour * 60 + dt_object.minute
    return total_minutes_since_midnight

def wait_sync(self, token_count, silent=False):
    current = time.time()
    dt_object = datetime.fromtimestamp(current)
    minute_slot = self.get_minute_slot()
    self.record['counter'] += token_count
    if self.record['slot'] == minute_slot:
        if self.record['counter'] >= self.tpm:
            next_minute = dt_object.replace(second=0, microsecond=0) + timedelta(minutes=1)
            _next = next_minute.timestamp()
            sleep_time = abs(_next - current)
            time.sleep(sleep_time)
            self.record = {'slot': self.get_minute_slot(), 'counter': 0}
    else:
        self.record = {'slot': self.get_minute_slot(), 'counter': 0}
    if not silent:
        logger.debug(self.record)

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

def md5(self, filepath: str):
    hash_object = hashlib.sha256()
    with open(filepath, 'rb') as file:
        chunk_size = 8192
        while (chunk := file.read(chunk_size)):
            hash_object.update(chunk)
    return hash_object.hexdigest()[0:8]

def encode_string(content: str, model_name: str='gpt-4o'):
    global ENCODER
    if ENCODER is None:
        tiktoken.get_encoding('cl100k_base')
        ENCODER = tiktoken.encoding_for_model(model_name)
    tokens = ENCODER.encode(content)
    return tokens

def decode_tokens(tokens: list[int], model_name: str='gpt-4o'):
    global ENCODER
    if ENCODER is None:
        ENCODER = tiktoken.encoding_for_model(model_name)
    content = ENCODER.decode(tokens)
    return content

def is_revert_command(wx_msg: dict):
    """Is wx_msg a revert command."""
    data = wx_msg['data']
    if 'content' not in data:
        return False
    content = data['content']
    if content is not None and len(content) > 0:
        content = content.encode('UTF-8', 'ignore').decode('UTF-8')
    messageType = wx_msg['messageType']
    revert_cmd = 'xrevert'
    if revert_cmd in content:
        return True
    if messageType == 5 or messageType == 9 or messageType == '80001':
        if revert_cmd in content:
            return True
    elif messageType == 14 or messageType == '80014':
        if 'title' in data:
            if revert_cmd in data['title']:
                return True
        elif revert_cmd in content:
            return True
    return False

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

def __init__(self):
    self.history = []
    self.last_msg_time = time.time()
    self.last_msg_id = -1
    self.last_process_time = -1
    self._id = ''
    self.group_id = ''

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

def generate_hash_filename(data: dict):
    xstr = json.dumps(data)
    md5 = hashlib.md5()
    md5.update(xstr.encode('utf8'))
    return md5.hexdigest()[0:6] + '.jpg'

def final_decro(func):
    """Not using async.Semaphore to aovid use nest-asyncio"""
    __current_size = 0

    @wraps(func)
    async def wait_func(*args, **kwargs):
        nonlocal __current_size
        while __current_size >= max_size:
            await asyncio.sleep(waitting_time)
        __current_size += 1
        result = await func(*args, **kwargs)
        __current_size -= 1
        return result
    return wait_func

def text_completion(input_text: str, stop_words) -> str:
    im_end = '<|im_end|>'
    if im_end not in stop_words:
        stop_words = stop_words + [im_end]
    stop_words_ids = [tokenizer.encode(w) for w in stop_words]
    input_ids = torch.tensor([tokenizer.encode(input_text)]).to(model.device)
    output = model.generate(input_ids, stop_words_ids=stop_words_ids)
    output = output.tolist()[0]
    output = tokenizer.decode(output, errors='ignore')
    assert output.startswith(input_text)
    output = output[len(input_text):].replace('<|endoftext|>', '').replace(im_end, '')
    for stop_str in stop_words:
        idx = output.find(stop_str)
        if idx != -1:
            output = output[:idx + len(stop_str)]
    return output

def content_hash(input_str: str):
    hash_object = hashlib.sha256()
    hash_object.update(input_str.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig[:6]

