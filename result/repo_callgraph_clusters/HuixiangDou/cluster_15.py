# Cluster 15

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

def get_month_time_str(t: datetime) -> str:
    return t.strftime('%y-%m')

def ymd():
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    if not os.path.exists(date_string):
        os.makedirs(date_string)
    return date_string

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

