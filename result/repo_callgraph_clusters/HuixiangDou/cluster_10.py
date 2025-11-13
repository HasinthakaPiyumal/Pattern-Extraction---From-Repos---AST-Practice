# Cluster 10

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

def put(self, item):
    """Put item into the queue."""
    self.__db.rpush(self.key, item)

def handle_task_add_doc_response(response: HxdTaskResponse):
    """update qalib's status from huixiangdou response's code.

    :param response:
    :return:
    """
    logger.info('do task: add doc')
    fid = response.feature_store_id
    name = biz_const.RDS_KEY_QALIB_INFO
    files_state = response.files_state
    o = r.hget(name=name, key=fid)
    if not o:
        logger.error(f"can't find {name}:{fid} in redis.")
        return
    qalib_info = QalibInfo(**json.loads(o))
    qalib_info.status = biz_const.HXD_PIPELINE_QALIB_CREATE_SUCCESS if response.code == 0 else response.code
    qalib_info.status_desc = response.status
    qalib_info.filesState = files_state
    r.hset(name=name, key=fid, value=qalib_info.model_dump_json())
    logger.info(f"do task={response.type} with fid={response.feature_store_id}'s result: {response.code}-{response.status}")

def handle_task_update_sample_response(response: HxdTaskResponse):
    """update sample's confirm status from response's code.

    :param response:
    :return:
    """
    logger.info('do task: update sample')
    name = biz_const.RDS_KEY_SAMPLE_INFO
    fid = response.feature_store_id
    o = r.hget(name=name, key=fid)
    if not o:
        logger.error(f"can't find {name}:{fid} in redis")
        return
    sample = QalibSample(**json.loads(o))
    sample.confirmed = True if response.code == 0 else False
    r.hset(name=name, key=fid, value=sample.model_dump_json())

def handle_task_update_pipeline_response(response: HxdTaskResponse):
    logger.info('do task: update pipeline')
    name = biz_const.RDS_KEY_PIPELINE
    o = r.hget(name=name, key=response.feature_store_id)
    if not o:
        logger.error(f"can't find {name}:{response.feature_store_id} in redis")
        return
    pipeline = Pipeline(**json.loads(o))
    pipeline.status = response.status
    pipeline.code = response.code
    pipeline.confirmed = True
    pipeline.success = True if response.code == 0 else False
    r.hset(name=name, key=response.feature_store_id, value=pipeline.model_dump_json())

def release_scheduler_lock(task) -> bool:
    key = f'{biz_const.RDS_KEY_SCHEDULER}-{task}'
    r.delete(key)
    return False if r.exists(key) else True

def stop_scheduler():
    task_1 = 'sync_hxd_task_response'
    if release_scheduler_lock(task_1):
        logger.info(f'release scheduler lock of {task_1} successfully.')
    else:
        logger.error(f'release scheduler lock of {task_1} failed. you should delete this key from redis manually.')

class HuixiangDouTask:

    def __init__(self):
        pass

    def updateTask(self, task: HxdTask) -> bool:
        """update task into redis.

        :param task: HxdTask
        :return: bool: True or False
        """
        if not task:
            logger.error("HuixiangDou's task is empty, update task aborted.")
            return False
        ChatCache.mark_monthly_active(task.payload.feature_store_id)
        if task.type == HxdTaskType.CHAT:
            ChatCache.add_inference_number()
        try:
            r.rpush(biz_const.RDS_KEY_HXD_TASK, task.model_dump_json())
        except Exception as e:
            logger.error(f'{e}')
            return False
        return True

def updateTask(self, task: HxdTask) -> bool:
    """update task into redis.

        :param task: HxdTask
        :return: bool: True or False
        """
    if not task:
        logger.error("HuixiangDou's task is empty, update task aborted.")
        return False
    ChatCache.mark_monthly_active(task.payload.feature_store_id)
    if task.type == HxdTaskType.CHAT:
        ChatCache.add_inference_number()
    try:
        r.rpush(biz_const.RDS_KEY_HXD_TASK, task.model_dump_json())
    except Exception as e:
        logger.error(f'{e}')
        return False
    return True

def add_access_info(name, value) -> bool:
    """add new access info to access:info db.

    :param name:
    :param value:
    :return:
    """
    return False if 1 != r.hset(name=biz_const.RDS_KEY_LOGIN, key=name, value=value) else True

def del_access_info(name) -> bool:
    """del new access info from access:info db.

    :param name:
    :return:
    """
    return True if 1 == r.hdel(biz_const.RDS_KEY_LOGIN, name) else False

def _create_qa_lib(name, hashed_pass, feature_store_id) -> bool:
    """
    1. init access info
    2. init qalib info
    :param name:
    :param hashed_pass:
    :param feature_store_id:
    :return:
    """
    try:
        if not add_access_info(name, AccessInfo(hashpass=hashed_pass, featureStoreId=feature_store_id).model_dump_json()):
            return False
        suffix = gen_suffix(feature_store_id)
        if not QaLibCache().init_qalib_info(feature_store_id, biz_const.HXD_QALIB_STATUS_INIT, name, suffix):
            if not del_access_info(name):
                logger.error(f'del access info by {name} failed')
            return False
        QaLibCache().set_suffix_to_qalib(suffix, feature_store_id)
        return True
    except Exception as e:
        logger.error(f'[create] create name: {name} failed: {e}')
        if not del_access_info(name):
            logger.error(f'del access info by {name} failed')
        if not QaLibCache().del_qalib_info(feature_store_id):
            logger.error(f'del qalib info by {name} failed')
        return False

def get_suffix_by_name(name: str) -> Union[str, None]:
    length = biz_const.HXD_FEATURE_STORE_SUFFIX_LENGTH
    if len(name) < length:
        logger.error(f'group name: {name} shorter than suffix length, remind check group name')
        return None
    return name[-length:]

class QaLibService:

    def __init__(self, request: Request, response: Response, hxd_info: QalibInfo):
        self.request = request
        self.response = response
        self.hxd_info = hxd_info

    @classmethod
    def get_existed_docs(cls, feature_store_id) -> List:
        o = r.hget(name=biz_const.RDS_KEY_QALIB_INFO, key=feature_store_id)
        if not o:
            return []
        qalib_info = QalibInfo(**json.loads(o))
        return qalib_info.docs

    async def info(self) -> BaseBody:
        return BaseBody(data=self.hxd_info)

    async def add_docs(self, files: List[UploadFile]=File(...)):
        feature_store_id = self.hxd_info.featureStoreId
        name = self.hxd_info.name
        logger.info(f'start to add docs for qalib: {name}')
        store_dir = get_store_dir(feature_store_id)
        if not files or not store_dir:
            return BaseBody()
        ret = AddDocsRes(errors=[])
        docs = self.get_existed_docs(feature_store_id)
        total_bytes = int(self.request.headers.get('content-length'))
        if total_bytes > biz_const.HXD_ADD_DOCS_ONCE_MAX:
            return standard_error_response(biz_const.ERR_QALIB_ADD_DOCS_ONCE_MAX)
        write_size = 0
        for file in files:
            if file.filename and len(file.filename.encode('utf-8')) > 255:
                logger.error(f'filename: {file.filename} too long, maximum 255 bytes, omit current filename')
                ret.errors.append(AddDocError(fileName=file.filename, reason='filename is too long'))
                continue
            with open(os.path.join(store_dir, file.filename), 'wb') as f:
                while True:
                    chunk = await file.read(32768)
                    if not chunk:
                        break
                    f.write(chunk)
                    write_size += len(chunk)
                    progress = write_size / total_bytes * 100
                    print(f'\rQalib({name}) total process: {progress:.2f}%', end='')
            docs.append(file.filename)
            await file.close()
        if not QaLibCache().update_qalib_docs(feature_store_id, docs, store_dir):
            return BaseBody()
        if not HuixiangDouTask().updateTask(HxdTask(type=HxdTaskType.ADD_DOC, payload=HxdTaskPayload(name=name, feature_store_id=feature_store_id, file_list=docs, file_abs_base=store_dir))):
            return BaseBody()
        ret.docBase = store_dir
        ret.docs = docs
        return BaseBody(data=ret)

    async def delete_docs(self, body: QalibDeleteDoc):
        feature_store_id = self.hxd_info.featureStoreId
        name = self.hxd_info.name
        logger.info(f'start to delete docs for qalib: {name}')
        store_dir = get_store_dir(feature_store_id)
        for filename in body.filenames:
            path = os.path.join(store_dir, filename)
            if not os.path.exists(path):
                logger.warn(f'qalib: {name} has no file named {filename} to delete.')
                continue
            if path.startswith('.'):
                continue
            try:
                os.remove(path)
            except OSError as e:
                logger.error(f'qalib: error: {e} when removing {path}')
        filenames = set(os.listdir(store_dir))
        left_filenames = list(filenames - set(body.filenames))
        if not QaLibCache().rewrite_qalib_docs(feature_store_id, left_filenames, store_dir):
            return BaseBody()
        if not HuixiangDouTask().updateTask(HxdTask(type=HxdTaskType.ADD_DOC, payload=HxdTaskPayload(name=name, feature_store_id=feature_store_id, file_list=left_filenames, file_abs_base=store_dir))):
            return BaseBody()
        ret = AddDocsRes(errors=[])
        ret.docBase = store_dir
        ret.docs = left_filenames
        return BaseBody(data=ret)

    async def get_sample_info(self):
        sample_info = QaLibCache.get_sample_info(self.hxd_info.featureStoreId)
        return BaseBody(data=sample_info)

    async def update_sample_info(self, body: QalibPositiveNegative):
        name = self.hxd_info.name
        feature_store_id = self.hxd_info.featureStoreId
        positives = body.positives
        negatives = body.negatives
        qalib_sample = QalibSample(name=name, featureStoreId=feature_store_id, positives=positives, negatives=negatives, confirmed=False)
        QaLibCache.set_sample_info(feature_store_id, qalib_sample)
        if not HuixiangDouTask().updateTask(HxdTask(type=HxdTaskType.UPDATE_SAMPLE, payload=HxdTaskPayload(name=name, feature_store_id=feature_store_id, positive=positives, negative=negatives))):
            return BaseBody()
        return await self.get_sample_info()

    async def integrate_lark(self, body: IntegrateLarkBody):
        feature_store_id = self.hxd_info.featureStoreId
        info = QaLibCache.get_qalib_info(feature_store_id)
        if not info:
            return standard_error_response(biz_const.ERR_QALIB_INFO_NOT_FOUND)
        if info.lark:
            info.lark.appId = body.appId
            info.lark.appSecret = body.appSecret
        else:
            info.lark = Lark(appId=body.appId, appSecret=body.appSecret, encryptKey=HuixiangDouEnv.get_lark_encrypt_key(), verificationToken=HuixiangDouEnv.get_lark_verification_token(), eventUrl=get_lark_on_message_url())
        QaLibCache.set_qalib_info(feature_store_id, info)
        QaLibCache.set_lark_info(body.appId, body.appSecret)
        return BaseBody(data=info.lark)

    async def integrate_web_search(self, body: IntegrateWebSearchBody):
        feature_store_id = self.hxd_info.featureStoreId
        info = QaLibCache.get_qalib_info(feature_store_id)
        if not info:
            return standard_error_response(biz_const.ERR_QALIB_INFO_NOT_FOUND)
        info.webSearch = WebSearch(token=body.webSearchToken)
        task = HxdTask(type=HxdTaskType.UPDATE_PIPELINE, payload=HxdTaskPayload(feature_store_id=feature_store_id, name=self.hxd_info.name, web_search_token=body.webSearchToken))
        if HuixiangDouTask().updateTask(task):
            QaLibCache.set_qalib_info(feature_store_id, info)
            return BaseBody()
        return standard_error_response(biz_const.ERR_INFO_UPDATE_FAILED)

@classmethod
def get_existed_docs(cls, feature_store_id) -> List:
    o = r.hget(name=biz_const.RDS_KEY_QALIB_INFO, key=feature_store_id)
    if not o:
        return []
    qalib_info = QalibInfo(**json.loads(o))
    return qalib_info.docs

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
def get_event_handler(cls):
    return lark.EventDispatcherHandler.builder(HuixiangDouEnv.get_lark_encrypt_key(), HuixiangDouEnv.get_lark_verification_token(), lark.LogLevel.DEBUG).register_p2_im_message_receive_v1(cls._on_im_message_received).build()

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

def check_endpoint_update(info: QalibInfo):
    update = False
    if not info.wechat or info.wechat.onMessageUrl.endswith('wechat'):
        info.wechat = Wechat(onMessageUrl=get_wechat_on_message_url(info.suffix))
        update = True
    else:
        wechat_message_url = get_wechat_on_message_url(info.suffix)
        if info.wechat.onMessageUrl != wechat_message_url:
            info.wechat.onMessageUrl = wechat_message_url
            update = True
    if info.lark:
        lark_event_url = get_lark_on_message_url()
        if info.lark.eventUrl != lark_event_url:
            info.lark.eventUrl = lark_event_url
            update = True
    if update:
        QaLibCache.set_qalib_info(info.featureStoreId, info)

@app.route('/event', methods=['POST'])
def event():
    jsonstr = request.get_json()
    if type(jsonstr) is dict:
        param = jsonstr
    else:
        param = json.loads(jsonstr)
    logger.debug(param)
    resp = handler.do(parse_req())
    return parse_resp(resp)

def revert_from_lark_group(msg_id: str, app_id: str, app_secret: str):
    client = lark.Client.builder().app_id(app_id).app_secret(app_secret).log_level(lark.LogLevel.DEBUG).build()
    request: DeleteMessageRequest = DeleteMessageRequest.builder().message_id(msg_id).build()
    response: DeleteMessageResponse = client.im.v1.message.delete(request)
    if not response.success():
        lark.logger.error(f'client.im.v1.message.delete failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}')
        return Exception(response.msg)
    return None

def send_to_lark_group(json_obj: dict, app_id: str, app_secret: str):
    msg_id = ''
    try:
        source = json_obj['source']
        if source != 'lark':
            return Exception(f'unsupported source {source}')
        client = lark.Client.builder().app_id(app_id).app_secret(app_secret).log_level(lark.LogLevel.DEBUG).build()
        text_str = json.dumps({'text': json_obj['reply']}, ensure_ascii=False)
        request: ReplyMessageRequest = ReplyMessageRequest.builder().message_id(json_obj['msg_id']).request_body(ReplyMessageRequestBody.builder().content(text_str).msg_type('text').reply_in_thread(True).build()).build()
        response: ReplyMessageResponse = client.im.v1.message.reply(request)
        msg_id = response.data.message_id
        if not response.success():
            lark.logger.error(f'client.im.v1.message.reply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}')
            return (None, '')
        lark.logger.info(lark.JSON.marshal(response.data, indent=2))
    except Exception as e:
        return (e, '')
    return (None, msg_id)

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

def put(self, item):
    """Put item into the queue."""
    self.__db.rpush(self.key, item)

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

def load(self):
    """Load knowledge graph."""
    if not os.path.exists(self.gpickle_path):
        logger.error('gpickle {} not exist.'.format(self.gpickle_path))
        return None
    with open(self.gpickle_path, 'rb') as f:
        self.graph = pickle.load(f)
    logger.debug('number of nodes {}, number of edges {}'.format(self.graph.number_of_nodes(), self.graph.number_of_edges()))

@DeprecationWarning
def check_gpu_max_memory_gb():
    try:
        import torch
        device = torch.device('cuda')
        return torch.cuda.get_device_properties(device).total_memory / (1 << 30)
    except Exception as e:
        logger.error(str(e))
    return -1

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

def put(self, item):
    """Put item into the queue."""
    self.__db.rpush(self.key, item)

def parse_json_str(json_str: str):
    try:
        logger.info(json_str)
        return (json.loads(json_str, object_hook=lambda d: SimpleNamespace(**d)), None)
    except Exception as e:
        logger.error(str(e))
        return (None, e)

def empty_cache():
    try:
        from torch.cuda import empty_cache as cuda_empty_cache
        cuda_empty_cache()
    except Exception as e:
        logger.error(e)

