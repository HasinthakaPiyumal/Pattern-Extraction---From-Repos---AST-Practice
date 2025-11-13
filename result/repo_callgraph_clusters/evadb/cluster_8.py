# Cluster 8

class PluralDirective(AdmonitionDirective):

    def run(self):
        ad = super(PluralDirective, self).run()
        refs = sum((1 for node in ad[0][0] if isinstance(node, (addnodes.pending_xref, nodes.Referential))))
        if refs > 1:
            ad[0].plural = True
        return ad

def run(self):
    ad = super(PluralDirective, self).run()
    refs = sum((1 for node in ad[0][0] if isinstance(node, (addnodes.pending_xref, nodes.Referential))))
    if refs > 1:
        ad[0].plural = True
    return ad

class NoteDirective(AdmonitionDirective):
    node_class = note

    def run(self):
        ad = super(NoteDirective, self).run()
        if isinstance(ad[0][0], nodes.enumerated_list) and sum((1 for _ in ad[0][0].traverse(nodes.list_item))) > 1 or (isinstance(ad[0][0], nodes.footnote) and sum((1 for _ in ad[0].traverse(nodes.footnote))) > 1):
            ad[0].plural = True
        return ad

def run(self):
    ad = super(NoteDirective, self).run()
    if isinstance(ad[0][0], nodes.enumerated_list) and sum((1 for _ in ad[0][0].traverse(nodes.list_item))) > 1 or (isinstance(ad[0][0], nodes.footnote) and sum((1 for _ in ad[0].traverse(nodes.footnote))) > 1):
        ad[0].plural = True
    return ad

class CMDClientTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_mock_stdin_reader(self) -> asyncio.StreamReader:
        stdin_reader = asyncio.StreamReader()
        stdin_reader.feed_data(b'EXIT;\n')
        stdin_reader.feed_eof()
        return stdin_reader

    @patch('evadb.evadb_cmd_client.start_cmd_client')
    @patch('evadb.server.interpreter.create_stdin_reader')
    def test_evadb_client(self, mock_stdin_reader, mock_client):
        mock_stdin_reader.return_value = self.get_mock_stdin_reader()
        mock_client.side_effect = Exception('Test')

        async def test():
            with self.assertRaises(Exception):
                await evadb_client('0.0.0.0', 8803)
        asyncio.run(test())
        mock_client.reset_mock()
        mock_client.side_effect = KeyboardInterrupt

        async def test2():
            await evadb_client('0.0.0.0', 8803)
        asyncio.run(test2())

    @patch('argparse.ArgumentParser.parse_known_args')
    @patch('evadb.evadb_cmd_client.start_cmd_client')
    def test_evadb_client_with_cmd_arguments(self, mock_start_cmd_client, mock_parse_known_args):
        mock_parse_known_args.return_value = (argparse.Namespace(host='127.0.0.1', port='8800'), [])
        main()
        mock_start_cmd_client.assert_called_once_with('127.0.0.1', '8800')

    @patch('argparse.ArgumentParser.parse_known_args')
    @patch('evadb.evadb_cmd_client.start_cmd_client')
    def test_main_without_cmd_arguments(self, mock_start_cmd_client, mock_parse_known_args):
        mock_parse_known_args.return_value = (argparse.Namespace(host=None, port=None), [])
        main()
        mock_start_cmd_client.assert_called_once_with(BASE_EVADB_CONFIG['host'], BASE_EVADB_CONFIG['port'])

@patch('evadb.evadb_cmd_client.start_cmd_client')
@patch('evadb.server.interpreter.create_stdin_reader')
def test_evadb_client(self, mock_stdin_reader, mock_client):
    mock_stdin_reader.return_value = self.get_mock_stdin_reader()
    mock_client.side_effect = Exception('Test')

    async def test():
        with self.assertRaises(Exception):
            await evadb_client('0.0.0.0', 8803)
    asyncio.run(test())
    mock_client.reset_mock()
    mock_client.side_effect = KeyboardInterrupt

    async def test2():
        await evadb_client('0.0.0.0', 8803)
    asyncio.run(test2())

class CommandHandlerTests(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.stop_server_future = self.loop.create_future()
        asyncio.set_event_loop(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_command_handler(self):
        transport = mock.Mock()
        transport.write = MagicMock(return_value='response_message')
        request_message = 'SELECT id FROM foo;'
        asyncio.run(handle_request(None, transport, request_message))

def setUp(self):
    self.loop = asyncio.new_event_loop()
    self.stop_server_future = self.loop.create_future()
    asyncio.set_event_loop(None)

def test_command_handler(self):
    transport = mock.Mock()
    transport.write = MagicMock(return_value='response_message')
    request_message = 'SELECT id FROM foo;'
    asyncio.run(handle_request(None, transport, request_message))

class DBAPITests(unittest.IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self) -> None:
        f = open(suffix_pytest_xdist_worker_id_to_dir('upload.txt'), 'w')
        f.write('dummy data')
        f.close()
        return super().setUp()

    def tearDown(self) -> None:
        os.remove(suffix_pytest_xdist_worker_id_to_dir('upload.txt'))
        return super().tearDown()

    def test_evadb_cursor_execute_async(self):
        connection = AsyncMock()
        evadb_cursor = EvaDBCursor(connection)
        query = 'test_query'
        asyncio.run(evadb_cursor.execute_async(query))
        self.assertEqual(evadb_cursor._pending_query, True)
        with self.assertRaises(SystemError):
            asyncio.run(evadb_cursor.execute_async(query))

    def test_evadb_cursor_fetch_all_async(self):
        connection = AsyncMock()
        evadb_cursor = EvaDBCursor(connection)
        message = 'test_response'
        serialized_message = Response.serialize('test_response')
        serialized_message_length = b'%d' % len(serialized_message)
        connection._reader.readline.side_effect = [serialized_message_length]
        connection._reader.readexactly.side_effect = [serialized_message]
        response = asyncio.run(evadb_cursor.fetch_all_async())
        self.assertEqual(evadb_cursor._pending_query, False)
        self.assertEqual(message, response)

    def test_evadb_cursor_fetch_one_sync(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connection = AsyncMock()
        evadb_cursor = EvaDBCursor(connection)
        message = 'test_response'
        serialized_message = Response.serialize('test_response')
        serialized_message_length = b'%d' % len(serialized_message)
        connection._reader.readline.side_effect = [serialized_message_length]
        connection._reader.readexactly.side_effect = [serialized_message]
        response = evadb_cursor.fetch_one()
        self.assertEqual(evadb_cursor._pending_query, False)
        self.assertEqual(message, response)

    def test_evadb_connection(self):
        hostname = 'localhost'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connection = AsyncMock()
        evadb_cursor = EvaDBCursor(connection)
        with self.assertRaises(AttributeError):
            evadb_cursor.__getattr__('foo')
        with self.assertRaises(OSError):
            connect_remote(hostname, port=1)

    async def test_evadb_signal(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connection = AsyncMock()
        evadb_cursor = EvaDBCursor(connection)
        query = 'test_query'
        await evadb_cursor.execute_async(query)

    def test_client_stop_query(self):
        connection = AsyncMock()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        connection.protocol.loop = loop
        evadb_cursor = EvaDBCursor(connection)
        evadb_cursor.execute('test_query')
        evadb_cursor.stop_query()
        self.assertEqual(evadb_cursor._pending_query, False)

    def test_get_attr(self):
        connection = AsyncMock()
        evadb_cursor = EvaDBCursor(connection)
        with self.assertRaises(AttributeError):
            evadb_cursor.missing_function()

    @patch('asyncio.open_connection')
    def test_get_connection(self, mock_open):
        server_reader = asyncio.StreamReader()
        server_writer = MagicMock()
        mock_open.return_value = (server_reader, server_writer)
        connection = connect_remote('localhost', port=1)
        self.assertNotEqual(connection, None)

def test_evadb_cursor_execute_async(self):
    connection = AsyncMock()
    evadb_cursor = EvaDBCursor(connection)
    query = 'test_query'
    asyncio.run(evadb_cursor.execute_async(query))
    self.assertEqual(evadb_cursor._pending_query, True)
    with self.assertRaises(SystemError):
        asyncio.run(evadb_cursor.execute_async(query))

def test_evadb_cursor_fetch_all_async(self):
    connection = AsyncMock()
    evadb_cursor = EvaDBCursor(connection)
    message = 'test_response'
    serialized_message = Response.serialize('test_response')
    serialized_message_length = b'%d' % len(serialized_message)
    connection._reader.readline.side_effect = [serialized_message_length]
    connection._reader.readexactly.side_effect = [serialized_message]
    response = asyncio.run(evadb_cursor.fetch_all_async())
    self.assertEqual(evadb_cursor._pending_query, False)
    self.assertEqual(message, response)

def test_evadb_cursor_fetch_one_sync(self):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    connection = AsyncMock()
    evadb_cursor = EvaDBCursor(connection)
    message = 'test_response'
    serialized_message = Response.serialize('test_response')
    serialized_message_length = b'%d' % len(serialized_message)
    connection._reader.readline.side_effect = [serialized_message_length]
    connection._reader.readexactly.side_effect = [serialized_message]
    response = evadb_cursor.fetch_one()
    self.assertEqual(evadb_cursor._pending_query, False)
    self.assertEqual(message, response)

def test_evadb_connection(self):
    hostname = 'localhost'
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    connection = AsyncMock()
    evadb_cursor = EvaDBCursor(connection)
    with self.assertRaises(AttributeError):
        evadb_cursor.__getattr__('foo')
    with self.assertRaises(OSError):
        connect_remote(hostname, port=1)

def test_client_stop_query(self):
    connection = AsyncMock()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    connection.protocol.loop = loop
    evadb_cursor = EvaDBCursor(connection)
    evadb_cursor.execute('test_query')
    evadb_cursor.stop_query()
    self.assertEqual(evadb_cursor._pending_query, False)

def test_get_attr(self):
    connection = AsyncMock()
    evadb_cursor = EvaDBCursor(connection)
    with self.assertRaises(AttributeError):
        evadb_cursor.missing_function()

def main():
    parser = argparse.ArgumentParser(description='EvaDB Client')
    parser.add_argument('--host', help='Specify the host address of the server you want to connect to.')
    parser.add_argument('--port', help='Specify the port number of the server you want to connect to.')
    args, unknown = parser.parse_known_args()
    host = args.host if args.host else BASE_EVADB_CONFIG['host']
    port = args.port if args.port else BASE_EVADB_CONFIG['port']
    asyncio.run(evadb_client(host, port))

def main():
    parser = argparse.ArgumentParser(description='EvaDB Server')
    parser.add_argument('--host', help='Specify the host address on which the server will start.')
    parser.add_argument('--port', help='Specify the port number on which the server will start.')
    parser.add_argument('--db_dir', help='Specify the evadb directory which the server should access.')
    parser.add_argument('--sql_backend', help='Specify the custom sql database to use for structured data.')
    parser.add_argument('--start', help='start server', action='store_true', default=True)
    parser.add_argument('--stop', help='stop server', action='store_true', default=False)
    args, unknown = parser.parse_known_args()
    args.host = args.host or '0.0.0.0'
    args.port = args.port or '8803'
    if args.stop:
        return stop_server()
    if args.start:
        asyncio.run(start_evadb_server(args.db_dir, args.host, args.port, args.sql_backend))

class EvaDBConnection:

    def __init__(self, evadb: EvaDBDatabase, reader, writer):
        self._reader = reader
        self._writer = writer
        self._cursor = None
        self._result: Batch = None
        self._evadb = evadb
        self._jobs_process = None

    def cursor(self):
        """Retrieves a cursor associated with the connection.

        Returns:
            EvaDBCursor: The cursor object used to execute queries.


        Examples:
            >>> import evadb
            >>> connection = evadb.connection()
            >>> cursor = connection.cursor()

        The cursor can be used to execute queries.

            >>> cursor.query('SELECT * FROM sample_table;').df()
               col1  col2
            0     1     2
            1     3     4
            2     5     6

        """
        if self._cursor is None:
            self._cursor = EvaDBCursor(self)
        return self._cursor

    def start_jobs(self):
        if self._jobs_process and self._jobs_process.is_alive():
            logger.debug('The job scheduler is already running')
            return
        job_scheduler = JobScheduler(self._evadb)
        self._jobs_process = multiprocessing.Process(target=job_scheduler.execute)
        self._jobs_process.daemon = True
        self._jobs_process.start()
        logger.debug('Job scheduler process started')

    def stop_jobs(self):
        if self._jobs_process is not None and self._jobs_process.is_alive():
            self._jobs_process.terminate()
            self._jobs_process.join()
            logger.debug('Job scheduler process stopped')

def cursor(self):
    """Retrieves a cursor associated with the connection.

        Returns:
            EvaDBCursor: The cursor object used to execute queries.


        Examples:
            >>> import evadb
            >>> connection = evadb.connection()
            >>> cursor = connection.cursor()

        The cursor can be used to execute queries.

            >>> cursor.query('SELECT * FROM sample_table;').df()
               col1  col2
            0     1     2
            1     3     4
            2     5     6

        """
    if self._cursor is None:
        self._cursor = EvaDBCursor(self)
    return self._cursor

def connect_remote(host: str, port: int) -> EvaDBConnection:
    connection = asyncio.run(get_connection(host, port))
    return connection

@dataclass(frozen=True)
class Response:
    """
    Data model for EvaDB server response
    """
    status: ResponseStatus = ResponseStatus.FAIL
    batch: Batch = None
    error: Optional[str] = None
    query_time: Optional[float] = None

    def serialize(self):
        return PickleSerializer.serialize(self)

    @classmethod
    def deserialize(cls, data):
        obj = PickleSerializer.deserialize(data)
        return obj

    def as_df(self):
        if self.error is not None:
            raise ExecutorError(self.error)
        if self.batch is None:
            raise ExecutorError('Empty batch')
        return self.batch.frames

    def __str__(self):
        if self.query_time is not None:
            return '@status: %s\n@batch: \n %s\n@query_time: %s' % (self.status, self.batch, self.query_time)
        else:
            return '@status: %s\n@batch: \n %s\n@error: %s' % (self.status, self.batch, self.error)

def serialize(self):
    return PickleSerializer.serialize(self)

class Batch:
    """
    Data model used for storing a batch of frames.
    Internally stored as a pandas DataFrame with columns
    "id" and "data".
    id: integer index of frame
    data: frame as np.array

    Arguments:
        frames (DataFrame): pandas Dataframe holding frames data
    """

    def __init__(self, frames=None):
        self._frames = pd.DataFrame() if frames is None else frames
        if not isinstance(self._frames, pd.DataFrame):
            raise ValueError(f'Batch constructor not properly called.\nExpected pandas.DataFrame, got {type(self._frames)}')

    @property
    def frames(self) -> pd.DataFrame:
        return self._frames

    def __len__(self):
        return len(self._frames)

    @property
    def columns(self):
        return list(self._frames.columns)

    def column_as_numpy_array(self, column_name: str) -> np.ndarray:
        """Return a column as numpy array

        Args:
            column_name (str): the name of the required column

        Returns:
            numpy.ndarray: the column data as a numpy array
        """
        return self._frames[column_name].to_numpy()

    def serialize(self):
        obj = {'frames': self._frames, 'batch_size': len(self)}
        return PickleSerializer.serialize(obj)

    @classmethod
    def deserialize(cls, data):
        obj = PickleSerializer.deserialize(data)
        return cls(frames=obj['frames'])

    @classmethod
    def from_eq(cls, batch1: Batch, batch2: Batch) -> Batch:
        return Batch(pd.DataFrame(batch1.to_numpy() == batch2.to_numpy()))

    @classmethod
    def from_greater(cls, batch1: Batch, batch2: Batch) -> Batch:
        return Batch(pd.DataFrame(batch1.to_numpy() > batch2.to_numpy()))

    @classmethod
    def from_lesser(cls, batch1: Batch, batch2: Batch) -> Batch:
        return Batch(pd.DataFrame(batch1.to_numpy() < batch2.to_numpy()))

    @classmethod
    def from_greater_eq(cls, batch1: Batch, batch2: Batch) -> Batch:
        return Batch(pd.DataFrame(batch1.to_numpy() >= batch2.to_numpy()))

    @classmethod
    def from_lesser_eq(cls, batch1: Batch, batch2: Batch) -> Batch:
        return Batch(pd.DataFrame(batch1.to_numpy() <= batch2.to_numpy()))

    @classmethod
    def from_not_eq(cls, batch1: Batch, batch2: Batch) -> Batch:
        return Batch(pd.DataFrame(batch1.to_numpy() != batch2.to_numpy()))

    @classmethod
    def compare_contains(cls, batch1: Batch, batch2: Batch) -> None:
        return cls(pd.DataFrame(([all((x in p for x in q)) for p, q in zip(left, right)] for left, right in zip(batch1.to_numpy(), batch2.to_numpy()))))

    @classmethod
    def compare_is_contained(cls, batch1: Batch, batch2: Batch) -> None:
        return cls(pd.DataFrame(([all((x in q for x in p)) for p, q in zip(left, right)] for left, right in zip(batch1.to_numpy(), batch2.to_numpy()))))

    @classmethod
    def compare_like(cls, batch1: Batch, batch2: Batch) -> None:
        col = batch1._frames.iloc[:, 0]
        regex = batch2._frames.iloc[:, 0][0]
        return cls(pd.DataFrame(col.astype('str').str.match(pat=regex)))

    def __str__(self) -> str:
        with pd.option_context('display.pprint_nest_depth', 1, 'display.max_colwidth', 100):
            return f'{self._frames}'

    def __eq__(self, other: Batch):
        return self._frames[sorted(self.columns)].equals(other.frames[sorted(other.columns)])

    def __getitem__(self, indices) -> Batch:
        """
        Returns a batch with the desired frames

        Arguments:
            indices (list, slice or mask): list must be
            a list of indices; mask is boolean array-like
            (i.e. list, NumPy array, DataFrame, etc.)
            of appropriate size with True for desired frames.
        """
        if isinstance(indices, list):
            return self._get_frames_from_indices(indices)
        elif isinstance(indices, slice):
            start = indices.start if indices.start else 0
            end = indices.stop if indices.stop else len(self.frames)
            if end < 0:
                end = len(self._frames) + end
            step = indices.step if indices.step else 1
            return self._get_frames_from_indices(range(start, end, step))
        elif isinstance(indices, int):
            return self._get_frames_from_indices([indices])
        else:
            raise TypeError('Invalid argument type: {}'.format(type(indices)))

    def _get_frames_from_indices(self, required_frame_ids):
        new_frames = self._frames.iloc[required_frame_ids, :]
        new_batch = Batch(new_frames)
        return new_batch

    def apply_function_expression(self, expr: Callable) -> Batch:
        """
        Execute function expression on frames.
        """
        self.drop_column_alias()
        return Batch(expr(self._frames))

    def iterrows(self):
        return self._frames.iterrows()

    def sort(self, by=None) -> None:
        """
        in_place sort
        """
        if self.empty():
            return
        if by is None:
            by = self.columns[0]
        self._frames.sort_values(by=by, ignore_index=True, inplace=True)

    def sort_orderby(self, by, sort_type=None) -> None:
        """
        in_place sort for order_by

        Args:
            by: list of column names
            sort_type: list of True/False if ASC for each column name in 'by'
                i.e [True, False] means [ASC, DESC]
        """
        if sort_type is None:
            sort_type = [True]
        assert by is not None
        for column in by:
            assert column in self._frames.columns, 'Can not orderby non-projected column: {}'.format(column)
        self._frames.sort_values(by, ascending=sort_type, ignore_index=True, inplace=True)

    def invert(self) -> None:
        self._frames = ~self._frames

    def all_true(self) -> bool:
        return self._frames.all().bool()

    def all_false(self) -> bool:
        inverted = ~self._frames
        return inverted.all().bool()

    def create_mask(self) -> List:
        """
        Return list of indices of first row.
        """
        return self._frames[self._frames[0]].index.tolist()

    def create_inverted_mask(self) -> List:
        return self._frames[~self._frames[0]].index.tolist()

    def update_indices(self, indices: List, other: Batch):
        self._frames.iloc[indices] = other._frames
        self._frames = pd.DataFrame(self._frames)

    def file_paths(self) -> Iterable:
        yield from self._frames['file_path']

    def project(self, cols: None) -> Batch:
        """
        Takes as input the column list, returns the projection.
        We do a copy for now.
        """
        cols = cols or []
        verified_cols = [c for c in cols if c in self._frames]
        unknown_cols = list(set(cols) - set(verified_cols))
        assert len(unknown_cols) == 0, unknown_cols
        return Batch(self._frames[verified_cols])

    @classmethod
    def merge_column_wise(cls, batches: List[Batch], auto_renaming=False) -> Batch:
        """
        Merge list of batch frames column_wise and return a new batch frame
        Arguments:
            batches: List[Batch]: list of batch objects to be merged
            auto_renaming: if true rename column names if required

        Returns:
            Batch: Merged batch object
        """
        if not len(batches):
            return Batch()
        frames = [batch.frames for batch in batches]
        frames_index = [list(frame.index) for frame in frames]
        for i, frame_index in enumerate(frames_index):
            assert frame_index == frames_index[i - 1], 'Merging of DataFrames with unmatched indices can cause undefined behavior'
        new_frames = pd.concat(frames, axis=1, copy=False, ignore_index=False)
        if new_frames.columns.duplicated().any():
            logger.debug('Duplicated column name detected {}'.format(new_frames))
        return Batch(new_frames)

    def __add__(self, other: Batch) -> Batch:
        """
        Adds two batch frames and return a new batch frame
        Arguments:
            other (Batch): other framebatch to add

        Returns:
            Batch
        """
        if not isinstance(other, Batch):
            raise TypeError('Input should be of type Batch')
        if self.empty():
            return other
        if other.empty():
            return self
        return Batch.concat([self, other], copy=False)

    @classmethod
    def concat(cls, batch_list: Iterable[Batch], copy=True) -> Batch:
        """Concat a list of batches.
        Notice: only frames are considered.
        """
        frame_list = list([batch.frames for batch in batch_list])
        if len(frame_list) == 0:
            return Batch()
        frame = pd.concat(frame_list, ignore_index=True, copy=copy)
        return Batch(frame)

    @classmethod
    def stack(cls, batch: Batch, copy=True) -> Batch:
        """Stack a given batch along the 0th dimension.
        Notice: input assumed to contain only one column with video frames

        Returns:
            Batch (always of length 1)
        """
        if len(batch.columns) > 1:
            raise ValueError('Stack can only be called on single-column batches')
        frame_data_col = batch.columns[0]
        data_to_stack = batch.frames[frame_data_col].values.tolist()
        if isinstance(data_to_stack[0], np.ndarray) and len(data_to_stack[0].shape) > 1:
            stacked_array = np.array(batch.frames[frame_data_col].values.tolist())
        else:
            stacked_array = np.hstack(batch.frames[frame_data_col].values)
        stacked_frame = pd.DataFrame([{frame_data_col: stacked_array}])
        return Batch(stacked_frame)

    @classmethod
    def join(cls, first: Batch, second: Batch, how='inner') -> Batch:
        return cls(first._frames.merge(second._frames, left_index=True, right_index=True, how=how))

    @classmethod
    def combine_batches(cls, first: Batch, second: Batch, expression: ExpressionType) -> Batch:
        """
        Creates Batch by combining two batches using some arithmetic expression.
        """
        if expression == ExpressionType.ARITHMETIC_ADD:
            return Batch(pd.DataFrame(first._frames + second._frames))
        elif expression == ExpressionType.ARITHMETIC_SUBTRACT:
            return Batch(pd.DataFrame(first._frames - second._frames))
        elif expression == ExpressionType.ARITHMETIC_MULTIPLY:
            return Batch(pd.DataFrame(first._frames * second._frames))
        elif expression == ExpressionType.ARITHMETIC_DIVIDE:
            return Batch(pd.DataFrame(first._frames / second._frames))

    def reassign_indices_to_hash(self, indices) -> None:
        """
        Hash indices and replace the indices with those hash values.
        """
        self._frames.index = self._frames[indices].apply(lambda x: hash(tuple(x)), axis=1)

    def aggregate(self, method: str) -> None:
        """
        Aggregate batch based on method.
        Methods can be sum, count, min, max, mean

        Arguments:
            method: string with one of the five above options
        """
        self._frames = self._frames.agg([method])

    def empty(self):
        """Checks if the batch is empty
        Returns:
            True if the batch_size == 0
        """
        return len(self) == 0

    def unnest(self, cols: List[str]=None) -> None:
        """
        Unnest columns and drop columns with no data
        """
        if cols is None:
            cols = list(self.columns)
        self._frames = self._frames.explode(cols)
        self._frames.dropna(inplace=True)

    def reverse(self) -> None:
        """Reverses dataframe"""
        self._frames = self._frames[::-1]
        self._frames.reset_index(drop=True, inplace=True)

    def drop_zero(self, outcomes: Batch) -> None:
        """Drop all columns with corresponding outcomes containing zero."""
        self._frames = self._frames[(outcomes._frames > 0).to_numpy()]

    def reset_index(self):
        """Resets the index of the data frame in the batch"""
        self._frames.reset_index(drop=True, inplace=True)

    def modify_column_alias(self, alias: Union[Alias, str]) -> None:
        if isinstance(alias, str):
            alias = Alias(alias)
        new_col_names = []
        if len(alias.col_names):
            if len(self.columns) != len(alias.col_names):
                err_msg = f'Expected {len(alias.col_names)} columns {alias.col_names},got {len(self.columns)} columns {self.columns}.'
                raise RuntimeError(err_msg)
            new_col_names = ['{}.{}'.format(alias.alias_name, col_name) for col_name in alias.col_names]
        else:
            for col_name in self.columns:
                if '.' in str(col_name):
                    new_col_names.append('{}.{}'.format(alias.alias_name, str(col_name).split('.')[1]))
                else:
                    new_col_names.append('{}.{}'.format(alias.alias_name, col_name))
        self._frames.columns = new_col_names

    def drop_column_alias(self) -> None:
        new_col_names = []
        for col_name in self.columns:
            if isinstance(col_name, str) and '.' in col_name:
                new_col_names.append(col_name.split('.')[1])
            else:
                new_col_names.append(col_name)
        self._frames.columns = new_col_names

    def to_numpy(self):
        return self._frames.to_numpy()

    def rename(self, columns) -> None:
        """Rename column names"""
        self._frames.rename(columns=columns, inplace=True)

def serialize(self):
    obj = {'frames': self._frames, 'batch_size': len(self)}
    return PickleSerializer.serialize(obj)

class SQLStorageEngine(AbstractStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        """
        Grab the existing sql session
        """
        super().__init__(db)
        self._sql_session = db.catalog().sql_config.session
        self._sql_engine = db.catalog().sql_config.engine
        self._serializer = PickleSerializer

    def _dict_to_sql_row(self, dict_row: dict, columns: List[ColumnCatalogEntry]):
        for col in columns:
            if col.type == ColumnType.NDARRAY:
                dict_row[col.name] = self._serializer.serialize(dict_row[col.name])
            elif isinstance(dict_row[col.name], (np.generic,)):
                dict_row[col.name] = dict_row[col.name].tolist()
        return dict_row

    def _deserialize_sql_row(self, sql_row: dict, columns: List[ColumnCatalogEntry]):
        dict_row = {}
        for idx, col in enumerate(columns):
            if col.type == ColumnType.NDARRAY:
                dict_row[col.name] = self._serializer.deserialize(sql_row[col.name])
            else:
                dict_row[col.name] = sql_row[col.name]
        dict_row[ROW_NUM_COLUMN] = dict_row[IDENTIFIER_COLUMN]
        return dict_row

    def _try_loading_table_via_reflection(self, table_name: str):
        metadata_obj = BaseModel.metadata
        if table_name in metadata_obj.tables:
            return metadata_obj.tables[table_name]
        insp = inspect(self._sql_engine)
        if insp.has_table(table_name):
            table = Table(table_name, metadata_obj)
            insp.reflect_table(table, None)
            return table
        else:
            err_msg = f'No table found with name {table_name}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def create(self, table: TableCatalogEntry, **kwargs):
        """
        Create an empty table in sql.
        It dynamically constructs schema in sqlaclchemy
        to create the table
        """
        attr_dict = {'__tablename__': table.name}
        table_columns = [col for col in table.columns if col.name != IDENTIFIER_COLUMN and col.name != ROW_NUM_COLUMN]
        sqlalchemy_schema = SchemaUtils.xform_to_sqlalchemy_schema(table_columns)
        attr_dict.update(sqlalchemy_schema)
        insp = inspect(self._sql_engine)
        if insp.has_table(table.name):
            logger.warning('Table {table.name} already exists')
            return BaseModel.metadata.tables[table.name]
        new_table = type(f'__placeholder_class_name__{table.name}', (BaseModel,), attr_dict)()
        table = BaseModel.metadata.tables[table.name]
        if not insp.has_table(table.name):
            BaseModel.metadata.tables[table.name].create(self._sql_engine)
        self._sql_session.commit()
        return new_table

    def drop(self, table: TableCatalogEntry):
        try:
            table_to_remove = self._try_loading_table_via_reflection(table.name)
            insp = inspect(self._sql_engine)
            if insp.has_table(table_to_remove.name):
                table_to_remove.drop(self._sql_engine)
                BaseModel.metadata.remove(table_to_remove)
            self._sql_session.commit()
        except Exception as e:
            err_msg = f'Failed to drop the table {table.name} with Exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def write(self, table: TableCatalogEntry, rows: Batch):
        """
        Write rows into the sql table.

        Arguments:
            table: table metadata object to write into
            rows : batch to be persisted in the storage.
        """
        try:
            table_to_update = self._try_loading_table_via_reflection(table.name)
            columns = rows.frames.keys()
            data = []
            table_columns = [col for col in table.columns if col.name != IDENTIFIER_COLUMN and col.name != ROW_NUM_COLUMN]
            for record in rows.frames.values:
                row_data = {col: record[idx] for idx, col in enumerate(columns) if col != ROW_NUM_COLUMN}
                data.append(self._dict_to_sql_row(row_data, table_columns))
            self._sql_session.execute(table_to_update.insert(), data)
            self._sql_session.commit()
        except Exception as e:
            err_msg = f'Failed to update the table {table.name} with exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def read(self, table: TableCatalogEntry, batch_mem_size: int=30000000) -> Iterator[Batch]:
        """
        Reads the table and return a batch iterator for the
        tuples.

        Argument:
            table: table metadata object of the table to read
            batch_mem_size (int): memory size of the batch read from storage
        Return:
            Iterator of Batch read.
        """
        try:
            table_to_read = self._try_loading_table_via_reflection(table.name)
            result = self._sql_session.execute(table_to_read.select()).fetchall()
            result_iter = (self._deserialize_sql_row(row._asdict(), table.columns) for row in result)
            for df in rebatch(result_iter, batch_mem_size):
                yield Batch(pd.DataFrame(df))
        except Exception as e:
            err_msg = f'Failed to read the table {table.name} with exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def delete(self, table: TableCatalogEntry, sqlalchemy_filter_clause: 'ColumnElement[bool]'):
        """Delete tuples from the table where rows satisfy the where_clause.
        The current implementation only handles equality predicates.

        Argument:
            table: table metadata object of the table
            where_clause: clause used to find the tuples to remove.
        """
        try:
            table_to_delete_from = self._try_loading_table_via_reflection(table.name)
            d = table_to_delete_from.delete().where(sqlalchemy_filter_clause)
            self._sql_session.execute(d)
            self._sql_session.commit()
        except Exception as e:
            err_msg = f'Failed to delete from the table {table.name} with exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def rename(self, old_table: TableCatalogEntry, new_name: TableInfo):
        raise Exception('Rename not supported for structured data table')

def _dict_to_sql_row(self, dict_row: dict, columns: List[ColumnCatalogEntry]):
    for col in columns:
        if col.type == ColumnType.NDARRAY:
            dict_row[col.name] = self._serializer.serialize(dict_row[col.name])
        elif isinstance(dict_row[col.name], (np.generic,)):
            dict_row[col.name] = dict_row[col.name].tolist()
    return dict_row

def _dict_to_sql_row(dict_row: dict, columns: List[ColumnCatalogEntry]):
    for col in columns:
        if col.type == ColumnType.NDARRAY:
            dict_row[col.name] = PickleSerializer.serialize(dict_row[col.name])
        elif isinstance(dict_row[col.name], (np.generic,)):
            dict_row[col.name] = dict_row[col.name].tolist()
    return dict_row

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str, help='Path to the directory with documents', default='source_documents')
    args = parser.parse_args()
    directory_path = args.directory
    print(f'🔮 Welcome to EvaDB! Ingesting data in `{directory_path}`')
    load_data(source_folder_path=directory_path)
    print('🔥 Data ingestion complete! You can now run `privateGPT.py` to query your loaded data.')

def run_script(script_body: str, user_input: Dict):
    """Runs script generated by llm.

    Args:
        script_body (str): script generated by llm.
        user_input (Dict): user input.
    """
    absolute_csv_path = os.path.abspath(user_input['csv_path'])
    absolute_script_path = os.path.abspath(SCRIPT_PATH)
    print(absolute_csv_path)
    load_df = f"import pandas as pd\ndf = pd.read_csv('{absolute_csv_path}')\n"
    script_body = load_df + script_body
    with open(absolute_script_path, 'w+') as script_file:
        script_file.write(script_body)
    subprocess.run(['python', absolute_script_path])

