# Cluster 47

class Table(Sequence[T]):
    """
    Table wrapper. Provide some convenient APIs, for example:
        table = Table(Sample, session)

        first_row = table[0]
        last_row = table[-1]
        some_random_rows = table[50:100]
        my_row = table['row_token_here']

        total_num = len(table)
    """

    def __init__(self, table: Any, db: DB) -> None:
        """
        Init table.
        :param table: Class type in models.py.
        :param db: DB instance.
        """
        self._table = table
        self._db = db
        event.listen(table, 'load', self._decorate_record)

    def _decorate_record(self, record: T, context: Any) -> None:
        """
        Sqlalchemy hook function. This will be called each time sqlalchemy loads a object from db.
        We save table reference as "_table" in the record here.
        :param record: The record loaded from database.
        :param context: Some context we don't use.
        """
        record._table = self

    def __repr__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        count = self.count()
        _repr = str(self._table.__name__) + '({} entries):\n{}\n'.format(count, '-' * 50)
        for ind in range(count)[:3]:
            _repr += repr(self._session.query(self._table)[ind])
        if count > 3:
            _repr += '(...) \n'
            _repr += repr(self._session.query(self._table)[count - 1])
        return _repr

    @property
    def _session(self) -> Session:
        """
        Get the underlying db session.
        :return: The underlying db session.
        """
        return self.db.session

    @property
    def db(self) -> DB:
        """
        Get the underlying db.
        :return: The underlying db.
        """
        return self._db

    def get(self, token: str) -> T:
        """
        Returns a record from table.
        :param token: Token of the record.
        :return: Record object.
        """
        return self._session.query(self._table).get(token)

    def select_one(self, **filters: Any) -> Optional[T]:
        """
        Query table using filters. There should be at most one record matching
        given filters, use select_many for searching multiple records.
            cat = nuplandb.category.select_one(name='vehicle')
        :param filters: Query using keyword expression. For example, query log by log file name:
            log = nuplandb.log.select_one(logfile='2021.07.16.20.45.29_veh-35_01095_01486')
        :return: Record object matching the given filters.
        """
        record: Optional[T] = self._session.query(self._table).filter_by(**filters).one_or_none()
        return record

    def select_many(self, **filters: Any) -> List[T]:
        """
        Query table using filters.
            boston_logs = nuplandb.log.select_many(location='boston').
        :param filters: Query using keyword expression. For example, query log by vehicle:
            logs = nuplandb.log.select_many(vehicle_name='35')
        :return: A list of records mathing the given filters.
        """
        return self._session.query(self._table).filter_by(**filters).all()

    def count(self, **kwargs: Any) -> int:
        """
        Count records for the given queries. For example:
            nuplandb.log.count(location='las_vegas').
        :param kwargs: Filters to count records.
        :return: The number of counted records.
        """
        return self._session.query(self._table).filter_by(**kwargs).count()

    def all(self) -> List[T]:
        """
        Return all the items for the given queries. For example:
            nuplandb.log.all().
        :return: List of records.
        """
        return self._session.query(self._table).all()

    def detach(self) -> None:
        """
        Performs any necessary cleanup of the table for destruction.
        This function must be called once the table is ready to be destroyed to properly free resources.
        Once this function is called, the table should no longer be queried.
        """
        event.remove(self._table, 'load', self._decorate_record)

    def __len__(self) -> int:
        """
        Return length of the records for the given queries. For example:
            nuplandb.log.__len()
        :return: Number of records.
        """
        return self._session.query(self._table.token).count()

    @overload
    def __getitem__(self, index: int) -> T:
        """Inherited, see superclass."""
        ...

    @overload
    def __getitem__(self, token: str) -> T:
        """Inherited, see superclass."""
        ...

    @overload
    def __getitem__(self, indexes: slice) -> List[T]:
        """Inherited, see superclass."""
        ...

    def __getitem__(self, key: Union[int, str, slice]) -> T:
        """Inherited, see superclass."""
        if isinstance(key, str):
            return self._session.query(self._table).get(key)
        else:
            return self._session.query(self._table)[key]

    def __iter__(self) -> Iterator[T]:
        """
        Inherited, see superclass.
        The implementation in Sequence is not good, it uses self[i] to loop over all elements
        which makes it much slower.
        Detail of yield_per can be found:
            https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per
        """
        query = self._session.query(self._table).yield_per(2000).enable_eagerloads(False)
        for row in query:
            yield row

def __init__(self, table: Any, db: DB) -> None:
    """
        Init table.
        :param table: Class type in models.py.
        :param db: DB instance.
        """
    self._table = table
    self._db = db
    event.listen(table, 'load', self._decorate_record)

