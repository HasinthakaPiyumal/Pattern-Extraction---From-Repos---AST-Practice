# Cluster 48

class DB:
    """
    Base class for DB loaders. Inherited classes should implement property method for each table with type
    annotation, for example:
        class NuPlanDB(DB):
            @property
            def category(self) -> Table[nuplandb_model.Category]:
                return self.tables['category']

    It is not recommended to use db.get('category', some_token), use db.category.get(some_token) or
    db.category[some_token] instead, because we can't get any type hint from the former one.
    """

    def __init__(self, table_names: List[str], models: Any, data_root: str, db_path: str, verbose: bool, model_source_dict: Dict[str, str]={}):
        """
        Initialize database by loading from filesystem or downloading from S3, load json table and build token index.
        :param table_names: List of table names.
        :param models: Auto-generated model template.
        :param data_root: Path to load the database from; if the database is downloaded from S3
                          this is the path to store the downloaded database.
        :param db_path: Local or S3 path to the database file.
        :param verbose: Whether to print status messages when loading the database.
        """
        self._table_names = list(table_names)
        self._data_root = data_root
        self._blob_store = BlobStoreCreator.create_nuplandb(data_root)
        self._tables = {}
        self._tables_detached = False
        self._refcount = 1
        self._refcount_lock = threading.Lock()
        db_path = db_path if db_path.endswith('.db') else f'{db_path}.db'
        self._db_path = Path(db_path)
        self._filename = self._db_path if self._db_path.exists() else Path(self._data_root) / self._db_path.name
        if not self._filename.exists():
            logger.debug(f'DB path not found, downloading db file to {self._filename}...')
            start_time = time.time()
            cache_store = CacheStore(self._data_root, self._blob_store)
            cache_store.save_to_disk(self._db_path.name)
            logger.debug('Downloading db file took {:.1f} seconds'.format(time.time() - start_time))
        if verbose:
            logger.debug('\nLoading tables for database {}...'.format(self.name))
            start_time = time.time()
        self._session_manager = SessionManager(self._create_db_instance)
        for table_name in self._table_names:
            model_name = ''.join([s.capitalize() for s in table_name.split('_')])
            if len(model_source_dict) != 0:
                if model_name in model_source_dict:
                    model_pcls = getattr(models, model_source_dict[model_name])
                else:
                    model_pcls = getattr(models, model_source_dict['default'])
                model_cls = getattr(model_pcls, model_name)
            else:
                model_cls = getattr(models, model_name)
            self._tables[table_name] = Table[model_cls](model_cls, self)
        if verbose:
            for table_name in self._table_names:
                logger.debug('{} {},'.format(len(self._tables[table_name]), table_name))
            logger.debug('Done loading in {:.1f} seconds.\n'.format(time.time() - start_time))

    def __repr__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        return "{}('{}', data_root='{}')".format(self.__class__.__name__, self.name, self.data_root)

    def __str__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        _str = '{} {} with tables:\n{}'.format(self.__class__.__name__, self.name, '=' * 30)
        for table_name in self.table_names:
            if 'log' == table_name:
                continue
            _str += '\n{:20}: {}'.format(table_name, getattr(self, table_name).count())
        return _str

    @property
    def session(self) -> Session:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return self._session_manager.session

    @property
    def name(self) -> str:
        """
        Get the db name.
        :return: The db name.
        """
        return self._db_path.stem

    @property
    def data_root(self) -> str:
        """
        Get the data root.
        :return: The data root.
        """
        return self._data_root

    @property
    def table_root(self) -> str:
        """
        Get the table root.
        :return: The table root.
        """
        return str(self._filename)

    @property
    def table_names(self) -> List[str]:
        """
        Get the list of table names.
        :return: The list of table names.
        """
        self._assert_tables_attached()
        return self._table_names

    @property
    def tables(self) -> Dict[str, Table[Any]]:
        """
        Get the list of tables.
        :return: The list of tables.
        """
        self._assert_tables_attached()
        return self._tables

    def load_blob(self, path: str) -> BinaryIO:
        """
        Loads a blob.
        :param path: Path to the blob.
        :return: A binary stream to read the blob.
        """
        return self._blob_store.get(path)

    def get(self, table: str, token: str) -> Any:
        """
        Returns a record from table.
        :param table: Table name.
        :param token: Token of the record.
        :return: The record. See "templates.py" for details.
        """
        warnings.warn('deprecated', DeprecationWarning)
        self._assert_tables_attached()
        return getattr(self, table).get(token)

    def field2token(self, table: str, field: str, query: str) -> List[str]:
        """
        Function returns a list of tokens given a table and field of that table.
        :param table: Table name.
        :param field: Field name, see "template.py" for details.
        :param query: The same type as the field.
        :return: Return a list of record tokens.
        """
        warnings.warn('deprecated', DeprecationWarning)
        self._assert_tables_attached()
        return [rec.token for rec in getattr(self, table).search(**{field: query})]

    def are_tables_detached(self) -> bool:
        """
        Returns true if the tables have been detached, false otherwise.
        :returns: True if the tables have been detached, false otherwise.
        """
        return self._tables_detached

    def detach_tables(self) -> None:
        """
        Prepares all tables for destruction.
        This must be called when DB is ready to be released to reclaim used memory.
        After calling this method, no further queries should be run from the db.

        Placing this in __del__ is not sufficient, because without detaching tables,
          SQLAlchemy will keep references to the tables alive.
          Which contain references to the DB.
          Which means that __del__ will never be called.
        """
        if not self._tables_detached:
            for table_name in self.table_names:
                self.tables[table_name].detach()
            self._tables_detached = True

    def _assert_tables_attached(self) -> None:
        """
        Checks to ensure that the tables are attached. If not, raises an error.
        """
        if self.are_tables_detached():
            raise RuntimeError('Attempting to query from detached tables.')

    def add_ref(self) -> None:
        """
        Add an external reference to this class to prevent it from being reclaimed by the GC.
        This method should be called when any non-SqlAlchemy class takes a reference to the class.

        See the comments in __init__ for explanation
        """
        with self._refcount_lock:
            if self._refcount == 0:
                raise ValueError('Attempting to revive a database that has had its tables detached. This is likely due to a reference counting error.')
            self._refcount += 1

    def remove_ref(self) -> None:
        """
        Removes an external reference to this class.
        This should be called when any non-SqlAlchemy class is finished using the database (e.g. in their __del__ method).
        If the reference count gets to zero, it will be prepared for collection by the GC.
        """
        with self._refcount_lock:
            self._refcount -= 1
            if self._refcount == 0:
                self.detach_tables()

    def _create_db_instance(self) -> sqlite3.Connection:
        """
        Internal method, return sqlite3 connection for sqlalchemy.
        :return: Sqlite3 connection.
        """
        assert Path(self.table_root).exists(), 'DB file not found: {}'.format(self.table_root)
        db = sqlite3.connect('file:{}?mode=ro'.format(self.table_root), uri=True, check_same_thread=False)
        db.execute('PRAGMA main.journal_mode = OFF;')
        db.execute('PRAGMA main.cache_size=10240;')
        db.execute('PRAGMA main.page_size = 4096;')
        db.execute('PRAGMA main.journal_mode = OFF;')
        db.execute('PRAGMA query_only = 1;')
        return db

def remove_ref(self) -> None:
    """
        Removes an external reference to this class.
        This should be called when any non-SqlAlchemy class is finished using the database (e.g. in their __del__ method).
        If the reference count gets to zero, it will be prepared for collection by the GC.
        """
    with self._refcount_lock:
        self._refcount -= 1
        if self._refcount == 0:
            self.detach_tables()

