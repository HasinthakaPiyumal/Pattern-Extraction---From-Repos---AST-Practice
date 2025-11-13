# Cluster 46

class SessionManager:
    """
    We use this to support multi-processes/threads. The idea is to have one
    db connection for each process, and have one session for each thread.
    """

    def __init__(self, engine_creator: Callable[[], Any]) -> None:
        """
        :param engine_creator: A callable which returns a DBAPI connection.
        """
        self._creator = engine_creator
        self._engine_pool = defaultdict(dict)
        self._session_pool = defaultdict(dict)

    @property
    def engine(self) -> sqlalchemy.engine.Engine:
        """
        Get the engine for the current thread. A new one will be created if not already exist.
        :return: The underlying engine.
        """
        pid = os.getpid()
        t = threading.current_thread()
        if t not in self._engine_pool[pid]:
            self._engine_pool[pid][t] = sqlalchemy.create_engine('sqlite:///', creator=self._creator)
        return self._engine_pool[pid][t]

    @property
    def session(self) -> Session:
        """
        Get the session for the current thread. A new one will be created if not already exist.
        :return: The underlying session.
        """
        pid = os.getpid()
        t = threading.current_thread()
        if t not in self._session_pool[pid]:
            self._session_pool[pid][t] = Session(bind=self.engine, autocommit=True, autoflush=True)
        return self._session_pool[pid][t]

@property
def engine(self) -> sqlalchemy.engine.Engine:
    """
        Get the engine for the current thread. A new one will be created if not already exist.
        :return: The underlying engine.
        """
    pid = os.getpid()
    t = threading.current_thread()
    if t not in self._engine_pool[pid]:
        self._engine_pool[pid][t] = sqlalchemy.create_engine('sqlite:///', creator=self._creator)
    return self._engine_pool[pid][t]

@property
def session(self) -> Session:
    """
        Get the session for the current thread. A new one will be created if not already exist.
        :return: The underlying session.
        """
    pid = os.getpid()
    t = threading.current_thread()
    if t not in self._session_pool[pid]:
        self._session_pool[pid][t] = Session(bind=self.engine, autocommit=True, autoflush=True)
    return self._session_pool[pid][t]

