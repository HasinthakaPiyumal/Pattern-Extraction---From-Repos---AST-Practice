# Cluster 18

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

class CreateDatabaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        cls.db_path = f'{os.path.dirname(os.path.abspath(__file__))}/testing.db'

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, 'DROP DATABASE IF EXISTS test_data_source;')
        execute_query_fetch_all(cls.evadb, 'DROP DATABASE IF EXISTS demo;')
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_create_database_should_add_the_entry(self):
        params = {'user': 'user', 'password': 'password', 'host': '127.0.0.1', 'port': '5432', 'database': 'demo'}
        query = 'CREATE DATABASE demo_db\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {};'.format(params)
        with patch('evadb.executor.create_database_executor.get_database_handler'):
            execute_query_fetch_all(self.evadb, query)
        db_entry = self.evadb.catalog().get_database_catalog_entry('demo_db')
        self.assertEqual(db_entry.name, 'demo_db')
        self.assertEqual(db_entry.engine, 'postgres')
        self.assertEqual(db_entry.params, params)

    def test_should_create_sqlite_database(self):
        import os
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        database_path = f'{current_file_dir}/testing.db'
        if_not_exists = 'IF NOT EXISTS'
        params = {'database': database_path}
        query = 'CREATE DATABASE {} test_data_source\n                    WITH ENGINE = "sqlite",\n                    PARAMETERS = {};'
        execute_query_fetch_all(self.evadb, query.format(if_not_exists, params))
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query.format('', params))
        execute_query_fetch_all(self.evadb, query.format(if_not_exists, params))

def test_create_database_should_add_the_entry(self):
    params = {'user': 'user', 'password': 'password', 'host': '127.0.0.1', 'port': '5432', 'database': 'demo'}
    query = 'CREATE DATABASE demo_db\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {};'.format(params)
    with patch('evadb.executor.create_database_executor.get_database_handler'):
        execute_query_fetch_all(self.evadb, query)
    db_entry = self.evadb.catalog().get_database_catalog_entry('demo_db')
    self.assertEqual(db_entry.name, 'demo_db')
    self.assertEqual(db_entry.engine, 'postgres')
    self.assertEqual(db_entry.params, params)

class CostModel:
    """
    Basic cost model. Change it as we add more cost based rules
    """

    def __init__(self):
        pass

    def calculate_cost(self, gexpr: GroupExpression):
        """
        Return the cost of the group expression.
        """

        @singledispatch
        def cost(opr: AbstractPlan):
            return 1.0

        @cost.register(NestedLoopJoinPlan)
        def cost_nested_loop_join_build_plan(opr: NestedLoopJoinPlan):
            return 1.0

        @cost.register(HashJoinBuildPlan)
        def cost_hash_join_build_plan(opr: HashJoinBuildPlan):
            return 1.0

        @cost.register(HashJoinProbePlan)
        def cost_hash_join_probe_plan(opr: HashJoinProbePlan):
            return 1.0

        @cost.register(SeqScanPlan)
        def cost_seq_scan(opr: SeqScanPlan):
            return 1.0

        @cost.register(ApplyAndMergePlan)
        def cost_apply_and_merge(opr: ApplyAndMergePlan):
            if opr.func_expr.has_cache():
                return 0
            return 1
        return cost(gexpr.opr)

@cost.register(NestedLoopJoinPlan)
def cost_nested_loop_join_build_plan(opr: NestedLoopJoinPlan):
    return 1.0

@cost.register(HashJoinBuildPlan)
def cost_hash_join_build_plan(opr: HashJoinBuildPlan):
    return 1.0

@cost.register(HashJoinProbePlan)
def cost_hash_join_probe_plan(opr: HashJoinProbePlan):
    return 1.0

@cost.register(SeqScanPlan)
def cost_seq_scan(opr: SeqScanPlan):
    return 1.0

class EmbedFilterIntoGet(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALFILTER)
        pattern.append_child(Pattern(OperatorType.LOGICALGET))
        super().__init__(RuleType.EMBED_FILTER_INTO_GET, pattern)

    def promise(self):
        return Promise.EMBED_FILTER_INTO_GET

    def check(self, before: LogicalFilter, context: OptimizerContext):
        predicate = before.predicate
        lget: LogicalGet = before.children[0]
        if predicate and is_video_table(lget.table_obj):
            video_alias = lget.video.alias
            col_alias = f'{video_alias}.id'
            pushdown_pred, _ = extract_pushdown_predicate(predicate, col_alias)
            if pushdown_pred:
                return True
        return False

    def apply(self, before: LogicalFilter, context: OptimizerContext):
        predicate = before.predicate
        lget = before.children[0]
        video_alias = lget.video.alias
        col_alias = f'{video_alias}.id'
        pushdown_pred, unsupported_pred = extract_pushdown_predicate(predicate, col_alias)
        if pushdown_pred:
            new_get_opr = LogicalGet(lget.video, lget.table_obj, alias=lget.alias, predicate=pushdown_pred, target_list=lget.target_list, sampling_rate=lget.sampling_rate, sampling_type=lget.sampling_type, children=lget.children)
            if unsupported_pred:
                unsupported_opr = LogicalFilter(unsupported_pred)
                unsupported_opr.append_child(new_get_opr)
                new_get_opr = unsupported_opr
            yield new_get_opr
        else:
            yield before

def check(self, before: LogicalFilter, context: OptimizerContext):
    predicate = before.predicate
    lget: LogicalGet = before.children[0]
    if predicate and is_video_table(lget.table_obj):
        video_alias = lget.video.alias
        col_alias = f'{video_alias}.id'
        pushdown_pred, _ = extract_pushdown_predicate(predicate, col_alias)
        if pushdown_pred:
            return True
    return False

class DropObjectExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: DropObjectPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        """Drop Object executor"""
        if self.node.object_type == ObjectType.TABLE:
            yield self._handle_drop_table(self.node.name, self.node.if_exists)
        elif self.node.object_type == ObjectType.INDEX:
            yield self._handle_drop_index(self.node.name, self.node.if_exists)
        elif self.node.object_type == ObjectType.FUNCTION:
            yield self._handle_drop_function(self.node.name, self.node.if_exists)
        elif self.node.object_type == ObjectType.DATABASE:
            yield self._handle_drop_database(self.node.name, self.node.if_exists)
        elif self.node.object_type == ObjectType.JOB:
            yield self._handle_drop_job(self.node.name, self.node.if_exists)

    def _handle_drop_table(self, table_name: str, if_exists: bool):
        if not self.catalog().check_table_exists(table_name):
            err_msg = 'Table: {} does not exist'.format(table_name)
            if if_exists:
                return Batch(pd.DataFrame([err_msg]))
            else:
                raise ExecutorError(err_msg)
        table_obj = self.catalog().get_table_catalog_entry(table_name)
        storage_engine = StorageEngine.factory(self.db, table_obj)
        logger.debug(f'Dropping table {table_name}')
        storage_engine.drop(table=table_obj)
        for col_obj in table_obj.columns:
            for cache in col_obj.dep_caches:
                self.catalog().drop_function_cache_catalog_entry(cache)
        assert self.catalog().delete_table_catalog_entry(table_obj), 'Failed to drop {}'.format(table_name)
        return Batch(pd.DataFrame({'Table Successfully dropped: {}'.format(table_name)}, index=[0]))

    def _handle_drop_function(self, function_name: str, if_exists: bool):
        if not self.catalog().get_function_catalog_entry_by_name(function_name):
            err_msg = f'Function {function_name} does not exist, therefore cannot be dropped.'
            if if_exists:
                logger.warning(err_msg)
                return Batch(pd.DataFrame([err_msg]))
            else:
                raise RuntimeError(err_msg)
        else:
            function_entry = self.catalog().get_function_catalog_entry_by_name(function_name)
            for cache in function_entry.dep_caches:
                self.catalog().drop_function_cache_catalog_entry(cache)
            self.catalog().delete_function_catalog_entry_by_name(function_name)
            return Batch(pd.DataFrame({f'Function {function_name} successfully dropped'}, index=[0]))

    def _handle_drop_index(self, index_name: str, if_exists: bool):
        index_obj = self.catalog().get_index_catalog_entry_by_name(index_name)
        if not index_obj:
            err_msg = f'Index {index_name} does not exist, therefore cannot be dropped.'
            if if_exists:
                logger.warning(err_msg)
                return Batch(pd.DataFrame([err_msg]))
            else:
                raise RuntimeError(err_msg)
        else:
            index = VectorStoreFactory.init_vector_store(index_obj.type, index_obj.name, **handle_vector_store_params(index_obj.type, index_obj.save_file_path, self.catalog))
            assert index is not None, f'Failed to initialize the vector store handler for {index_obj.type}'
            if index:
                index.delete()
            self.catalog().drop_index_catalog_entry(index_name)
            return Batch(pd.DataFrame({f'Index {index_name} successfully dropped'}, index=[0]))

    def _handle_drop_database(self, database_name: str, if_exists: bool):
        db_catalog_entry = self.catalog().get_database_catalog_entry(database_name)
        if not db_catalog_entry:
            err_msg = f'Database {database_name} does not exist, therefore cannot be dropped.'
            if if_exists:
                logger.warning(err_msg)
                return Batch(pd.DataFrame([err_msg]))
            else:
                raise RuntimeError(err_msg)
        logger.debug(f'Dropping database {database_name}')
        self.catalog().drop_database_catalog_entry(db_catalog_entry)
        return Batch(pd.DataFrame({f'Database {database_name} successfully dropped'}, index=[0]))

    def _handle_drop_job(self, job_name: str, if_exists: bool):
        job_catalog_entry = self.catalog().get_job_catalog_entry(job_name)
        if not job_catalog_entry:
            err_msg = f'Job {job_name} does not exist, therefore cannot be dropped.'
            if if_exists:
                logger.warning(err_msg)
                return Batch(pd.DataFrame([err_msg]))
            else:
                raise RuntimeError(err_msg)
        logger.debug(f'Dropping Job {job_name}')
        self.catalog().drop_job_catalog_entry(job_catalog_entry)
        return Batch(pd.DataFrame({f'Job {job_name} successfully dropped'}, index=[0]))

def _handle_drop_index(self, index_name: str, if_exists: bool):
    index_obj = self.catalog().get_index_catalog_entry_by_name(index_name)
    if not index_obj:
        err_msg = f'Index {index_name} does not exist, therefore cannot be dropped.'
        if if_exists:
            logger.warning(err_msg)
            return Batch(pd.DataFrame([err_msg]))
        else:
            raise RuntimeError(err_msg)
    else:
        index = VectorStoreFactory.init_vector_store(index_obj.type, index_obj.name, **handle_vector_store_params(index_obj.type, index_obj.save_file_path, self.catalog))
        assert index is not None, f'Failed to initialize the vector store handler for {index_obj.type}'
        if index:
            index.delete()
        self.catalog().drop_index_catalog_entry(index_name)
        return Batch(pd.DataFrame({f'Index {index_name} successfully dropped'}, index=[0]))

class UseExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: UseStatement):
        super().__init__(db, node)
        self._database_name = node.database_name
        self._query_string = node.query_string

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        db_catalog_entry = self.db.catalog().get_database_catalog_entry(self._database_name)
        if db_catalog_entry is None:
            raise ExecutorError(f'{self._database_name} data source does not exist. Use CREATE DATABASE to add a new data source.')
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            resp = handler.execute_native_query(self._query_string)
        if resp and resp.error is None:
            yield Batch(resp.data)
        else:
            raise ExecutorError(resp.error)

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    db_catalog_entry = self.db.catalog().get_database_catalog_entry(self._database_name)
    if db_catalog_entry is None:
        raise ExecutorError(f'{self._database_name} data source does not exist. Use CREATE DATABASE to add a new data source.')
    with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
        resp = handler.execute_native_query(self._query_string)
    if resp and resp.error is None:
        yield Batch(resp.data)
    else:
        raise ExecutorError(resp.error)

class VectorIndexScanExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: VectorIndexScanPlan):
        super().__init__(db, node)
        self.index_name = node.index.name
        self.vector_store_type = node.index.type
        self.feat_column = node.index.feat_column
        self.limit_count = node.limit_count
        self.search_query_expr = node.search_query_expr

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        if self.vector_store_type == VectorStoreType.PGVECTOR:
            return self._native_vector_index_scan()
        else:
            return self._evadb_vector_index_scan(*args, **kwargs)

    def _get_search_query_results(self):
        dummy_batch = Batch(frames=pd.DataFrame({'0': [0]}))
        search_batch = self.search_query_expr.evaluate(dummy_batch)
        feature_col_name = self.search_query_expr.output_objs[0].name
        search_batch.drop_column_alias()
        search_feat = search_batch.column_as_numpy_array(feature_col_name)[0]
        search_feat = search_feat.reshape(1, -1)
        return search_feat

    def _native_vector_index_scan(self):
        search_feat = self._get_search_query_results()
        search_feat = search_feat.reshape(-1).tolist()
        tb_catalog_entry = list(self.node.find_all(StoragePlan))[0].table
        db_catalog_entry = self.db.catalog().get_database_catalog_entry(tb_catalog_entry.database_name)
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            resp = handler.execute_native_query(f"SELECT * FROM {tb_catalog_entry.name}\n                                                ORDER BY {self.feat_column.name} <-> '{search_feat}'\n                                                LIMIT {self.limit_count}")
            if resp.error is not None:
                raise ExecutorError(f'Native index can encounters {resp.error}')
            res = Batch(frames=resp.data)
            res.modify_column_alias(tb_catalog_entry.name)
            yield res

    def _evadb_vector_index_scan(self, *args, **kwargs):
        index_catalog_entry = self.catalog().get_index_catalog_entry_by_name(self.index_name)
        self.index_path = index_catalog_entry.save_file_path
        self.index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.index_name, **handle_vector_store_params(self.vector_store_type, self.index_path, self.db.catalog))
        search_feat = self._get_search_query_results()
        index_result = self.index.query(VectorIndexQuery(search_feat, self.limit_count.value))
        row_num_np = index_result.ids
        row_num_col_name = None
        num_required_results = self.limit_count.value
        if len(index_result.ids) < self.limit_count.value:
            num_required_results = len(index_result.ids)
            logger.warning(f'The index {self.index_name} returned only {num_required_results} results, which is fewer than the required {self.limit_count.value}.')
        final_df = pd.DataFrame()
        res_data_list = []
        row_num_df = pd.DataFrame({'row_num_np': row_num_np})
        for batch in self.children[0].exec(**kwargs):
            if not row_num_col_name:
                column_list = batch.columns
                row_num_alias = get_row_num_column_alias(column_list)
                row_num_col_name = '{}.{}'.format(row_num_alias, ROW_NUM_COLUMN)
            if not batch.frames[row_num_col_name].isin(row_num_df['row_num_np']).any():
                continue
            for index, row in batch.frames.iterrows():
                row_dict = row.to_dict()
                res_data_list.append(row_dict)
        result_df = pd.DataFrame(res_data_list)
        final_df = pd.merge(row_num_df, result_df, left_on='row_num_np', right_on=row_num_col_name, how='inner')
        if 'row_num_np' in final_df:
            del final_df['row_num_np']
        yield Batch(final_df)

def _native_vector_index_scan(self):
    search_feat = self._get_search_query_results()
    search_feat = search_feat.reshape(-1).tolist()
    tb_catalog_entry = list(self.node.find_all(StoragePlan))[0].table
    db_catalog_entry = self.db.catalog().get_database_catalog_entry(tb_catalog_entry.database_name)
    with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
        resp = handler.execute_native_query(f"SELECT * FROM {tb_catalog_entry.name}\n                                                ORDER BY {self.feat_column.name} <-> '{search_feat}'\n                                                LIMIT {self.limit_count}")
        if resp.error is not None:
            raise ExecutorError(f'Native index can encounters {resp.error}')
        res = Batch(frames=resp.data)
        res.modify_column_alias(tb_catalog_entry.name)
        yield res

def _evadb_vector_index_scan(self, *args, **kwargs):
    index_catalog_entry = self.catalog().get_index_catalog_entry_by_name(self.index_name)
    self.index_path = index_catalog_entry.save_file_path
    self.index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.index_name, **handle_vector_store_params(self.vector_store_type, self.index_path, self.db.catalog))
    search_feat = self._get_search_query_results()
    index_result = self.index.query(VectorIndexQuery(search_feat, self.limit_count.value))
    row_num_np = index_result.ids
    row_num_col_name = None
    num_required_results = self.limit_count.value
    if len(index_result.ids) < self.limit_count.value:
        num_required_results = len(index_result.ids)
        logger.warning(f'The index {self.index_name} returned only {num_required_results} results, which is fewer than the required {self.limit_count.value}.')
    final_df = pd.DataFrame()
    res_data_list = []
    row_num_df = pd.DataFrame({'row_num_np': row_num_np})
    for batch in self.children[0].exec(**kwargs):
        if not row_num_col_name:
            column_list = batch.columns
            row_num_alias = get_row_num_column_alias(column_list)
            row_num_col_name = '{}.{}'.format(row_num_alias, ROW_NUM_COLUMN)
        if not batch.frames[row_num_col_name].isin(row_num_df['row_num_np']).any():
            continue
        for index, row in batch.frames.iterrows():
            row_dict = row.to_dict()
            res_data_list.append(row_dict)
    result_df = pd.DataFrame(res_data_list)
    final_df = pd.merge(row_num_df, result_df, left_on='row_num_np', right_on=row_num_col_name, how='inner')
    if 'row_num_np' in final_df:
        del final_df['row_num_np']
    yield Batch(final_df)

class OrderByExecutor(AbstractExecutor):
    """
    Sort the frames which satisfy the condition

    Arguments:
        node (AbstractPlan): The OrderBy Plan

    """

    def __init__(self, db: EvaDBDatabase, node: OrderByPlan):
        super().__init__(db, node)
        self._orderby_list = node.orderby_list
        self._columns = node.columns
        self._sort_types = node.sort_types
        self.batch_sizes = []

    def _extract_column_name(self, col):
        col_name = []
        if isinstance(col, TupleValueExpression):
            col_name += [col.col_alias]
        elif isinstance(col, FunctionExpression):
            col_name += col.col_alias
        else:
            raise ExecutorError('Expression type {} is not supported.'.format(type(col)))
        return col_name

    def extract_column_names(self):
        """extracts the string name of the column"""
        col_name_list = []
        for col in self._columns:
            col_name_list += self._extract_column_name(col)
        return col_name_list

    def extract_sort_types(self):
        """extracts the sort type for the column"""
        sort_type_bools = []
        for st in self._sort_types:
            if st is ParserOrderBySortType.ASC:
                sort_type_bools.append(True)
            else:
                sort_type_bools.append(False)
        return sort_type_bools

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        aggregated_batch_list = []
        for batch in child_executor.exec(**kwargs):
            self.batch_sizes.append(len(batch))
            aggregated_batch_list.append(batch)
        aggregated_batch = Batch.concat(aggregated_batch_list, copy=False)
        if not len(aggregated_batch):
            return
        merge_batch_list = [aggregated_batch]
        for col in self._columns:
            col_name_list = self._extract_column_name(col)
            for col_name in col_name_list:
                if col_name not in aggregated_batch.columns:
                    batch = col.evaluate(aggregated_batch)
                    merge_batch_list.append(batch)
        if len(merge_batch_list) > 1:
            aggregated_batch = Batch.merge_column_wise(merge_batch_list)
        try:
            aggregated_batch.sort_orderby(by=self.extract_column_names(), sort_type=self.extract_sort_types())
        except KeyError:
            pass
        index = 0
        for i in self.batch_sizes:
            batch = aggregated_batch[index:index + i]
            batch.reset_index()
            index += i
            yield batch

def _extract_column_name(self, col):
    col_name = []
    if isinstance(col, TupleValueExpression):
        col_name += [col.col_alias]
    elif isinstance(col, FunctionExpression):
        col_name += col.col_alias
    else:
        raise ExecutorError('Expression type {} is not supported.'.format(type(col)))
    return col_name

class StorageExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: StoragePlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        try:
            storage_engine = StorageEngine.factory(self.db, self.node.table)
            if self.node.table.table_type == TableType.VIDEO_DATA:
                return storage_engine.read(self.node.table, self.node.batch_mem_size, predicate=self.node.predicate, sampling_rate=self.node.sampling_rate, sampling_type=self.node.sampling_type, read_audio=self.node.table_ref.get_audio, read_video=self.node.table_ref.get_video)
            elif self.node.table.table_type == TableType.IMAGE_DATA:
                return storage_engine.read(self.node.table)
            elif self.node.table.table_type == TableType.DOCUMENT_DATA:
                return storage_engine.read(self.node.table, self.node.chunk_params)
            elif self.node.table.table_type == TableType.STRUCTURED_DATA:
                return storage_engine.read(self.node.table, self.node.batch_mem_size)
            elif self.node.table.table_type == TableType.NATIVE_DATA:
                return storage_engine.read(self.node.table)
            elif self.node.table.table_type == TableType.PDF_DATA:
                return storage_engine.read(self.node.table)
            else:
                raise ExecutorError(f'Unsupported TableType {self.node.table.table_type} encountered')
        except Exception as e:
            logger.error(e)
            raise ExecutorError(e)

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    try:
        storage_engine = StorageEngine.factory(self.db, self.node.table)
        if self.node.table.table_type == TableType.VIDEO_DATA:
            return storage_engine.read(self.node.table, self.node.batch_mem_size, predicate=self.node.predicate, sampling_rate=self.node.sampling_rate, sampling_type=self.node.sampling_type, read_audio=self.node.table_ref.get_audio, read_video=self.node.table_ref.get_video)
        elif self.node.table.table_type == TableType.IMAGE_DATA:
            return storage_engine.read(self.node.table)
        elif self.node.table.table_type == TableType.DOCUMENT_DATA:
            return storage_engine.read(self.node.table, self.node.chunk_params)
        elif self.node.table.table_type == TableType.STRUCTURED_DATA:
            return storage_engine.read(self.node.table, self.node.batch_mem_size)
        elif self.node.table.table_type == TableType.NATIVE_DATA:
            return storage_engine.read(self.node.table)
        elif self.node.table.table_type == TableType.PDF_DATA:
            return storage_engine.read(self.node.table)
        else:
            raise ExecutorError(f'Unsupported TableType {self.node.table.table_type} encountered')
    except Exception as e:
        logger.error(e)
        raise ExecutorError(e)

class LoadDataExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: LoadDataPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        """
        Use TYPE to determine the type of data to load.
        """
        if self.node.file_options['file_format'] is None:
            err_msg = 'Invalid file format, please use supported file formats: CSV | VIDEO | IMAGE | DOCUMENT | PDF'
            raise ExecutorError(err_msg)
        if self.node.file_options['file_format'] in [FileFormatType.VIDEO, FileFormatType.IMAGE, FileFormatType.DOCUMENT, FileFormatType.PDF]:
            executor = LoadMultimediaExecutor(self.db, self.node)
        elif self.node.file_options['file_format'] == FileFormatType.CSV:
            executor = LoadCSVExecutor(self.db, self.node)
        for batch in executor.exec():
            yield batch

def exec(self, *args, **kwargs):
    """
        Use TYPE to determine the type of data to load.
        """
    if self.node.file_options['file_format'] is None:
        err_msg = 'Invalid file format, please use supported file formats: CSV | VIDEO | IMAGE | DOCUMENT | PDF'
        raise ExecutorError(err_msg)
    if self.node.file_options['file_format'] in [FileFormatType.VIDEO, FileFormatType.IMAGE, FileFormatType.DOCUMENT, FileFormatType.PDF]:
        executor = LoadMultimediaExecutor(self.db, self.node)
    elif self.node.file_options['file_format'] == FileFormatType.CSV:
        executor = LoadCSVExecutor(self.db, self.node)
    for batch in executor.exec():
        yield batch

class PlanExecutor:
    """
    This is an interface between plan tree and execution tree.
    We traverse the plan tree and build execution tree from it

    Arguments:
        plan (AbstractPlan): Physical plan tree which needs to be executed
        evadb (EvaDBDatabase): database to execute the query on
    """

    def __init__(self, evadb: EvaDBDatabase, plan: AbstractPlan):
        self._db = evadb
        self._plan = plan

    def _build_execution_tree(self, plan: Union[AbstractPlan, AbstractStatement]) -> AbstractExecutor:
        """build the execution tree from plan tree

        Arguments:
            plan {AbstractPlan} -- Input Plan tree

        Returns:
            AbstractExecutor -- Compiled Execution tree
        """
        root = None
        if plan is None:
            return root
        if isinstance(plan, CreateDatabaseStatement):
            return CreateDatabaseExecutor(db=self._db, node=plan)
        elif isinstance(plan, UseStatement):
            return UseExecutor(db=self._db, node=plan)
        elif isinstance(plan, SetStatement):
            return SetExecutor(db=self._db, node=plan)
        elif isinstance(plan, CreateJobStatement):
            return CreateJobExecutor(db=self._db, node=plan)
        plan_opr_type = plan.opr_type
        if plan_opr_type == PlanOprType.SEQUENTIAL_SCAN:
            executor_node = SequentialScanExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.UNION:
            executor_node = UnionExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.STORAGE_PLAN:
            executor_node = StorageExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.PP_FILTER:
            executor_node = PPExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.CREATE:
            executor_node = CreateExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.RENAME:
            executor_node = RenameExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.DROP_OBJECT:
            executor_node = DropObjectExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.INSERT:
            executor_node = InsertExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.CREATE_FUNCTION:
            executor_node = CreateFunctionExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.LOAD_DATA:
            executor_node = LoadDataExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.GROUP_BY:
            executor_node = GroupByExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.ORDER_BY:
            executor_node = OrderByExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.LIMIT:
            executor_node = LimitExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.SAMPLE:
            executor_node = SampleExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.NESTED_LOOP_JOIN:
            executor_node = NestedLoopJoinExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.HASH_JOIN:
            executor_node = HashJoinExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.HASH_BUILD:
            executor_node = BuildJoinExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.FUNCTION_SCAN:
            executor_node = FunctionScanExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.EXCHANGE:
            executor_node = ExchangeExecutor(db=self._db, node=plan)
            inner_executor = self._build_execution_tree(plan.inner_plan)
            executor_node.build_inner_executor(inner_executor)
        elif plan_opr_type == PlanOprType.PROJECT:
            executor_node = ProjectExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.PREDICATE_FILTER:
            executor_node = PredicateExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.SHOW_INFO:
            executor_node = ShowInfoExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.EXPLAIN:
            executor_node = ExplainExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.CREATE_INDEX:
            executor_node = CreateIndexExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.APPLY_AND_MERGE:
            executor_node = ApplyAndMergeExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.VECTOR_INDEX_SCAN:
            executor_node = VectorIndexScanExecutor(db=self._db, node=plan)
        elif plan_opr_type == PlanOprType.DELETE:
            executor_node = DeleteExecutor(db=self._db, node=plan)
        if plan_opr_type != PlanOprType.EXPLAIN:
            for children in plan.children:
                executor_node.append_child(self._build_execution_tree(children))
        return executor_node

    def execute_plan(self, do_not_raise_exceptions: bool=False, do_not_print_exceptions: bool=False) -> Iterator[Batch]:
        """execute the plan tree"""
        try:
            execution_tree = self._build_execution_tree(self._plan)
            output = execution_tree.exec()
            if output is not None:
                yield from output
        except Exception as e:
            if do_not_raise_exceptions is False:
                if do_not_print_exceptions is False:
                    logger.exception(str(e))
                raise ExecutorError(e)

def execute_plan(self, do_not_raise_exceptions: bool=False, do_not_print_exceptions: bool=False) -> Iterator[Batch]:
    """execute the plan tree"""
    try:
        execution_tree = self._build_execution_tree(self._plan)
        output = execution_tree.exec()
        if output is not None:
            yield from output
    except Exception as e:
        if do_not_raise_exceptions is False:
            if do_not_print_exceptions is False:
                logger.exception(str(e))
            raise ExecutorError(e)

def handle_if_not_exists(catalog: 'CatalogManager', table_info: TableInfo, if_not_exist=False):
    if catalog.check_table_exists(table_info.table_name, table_info.database_name):
        err_msg = 'Table: {} already exists'.format(table_info)
        if if_not_exist:
            logger.warn(err_msg)
            return True
        else:
            logger.error(err_msg)
            raise ExecutorError(err_msg)
    else:
        return False

class CreateIndexExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: CreateIndexPlan):
        super().__init__(db, node)
        self.name = self.node.name
        self.if_not_exists = self.node.if_not_exists
        self.table_ref = self.node.table_ref
        self.col_list = self.node.col_list
        self.vector_store_type = self.node.vector_store_type
        self.project_expr_list = self.node.project_expr_list
        self.index_def = self.node.index_def

    def exec(self, *args, **kwargs):
        if self.vector_store_type == VectorStoreType.PGVECTOR:
            self._create_native_index()
        else:
            self._create_evadb_index()
        yield Batch(pd.DataFrame([f'Index {self.name} successfully added to the database.']))

    def _create_native_index(self):
        table = self.table_ref.table
        db_catalog_entry = self.catalog().get_database_catalog_entry(table.database_name)
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            resp = handler.execute_native_query(f'CREATE INDEX {self.name} ON {table.table_name}\n                    USING hnsw ({self.col_list[0].name} vector_l2_ops)')
            if resp.error is not None:
                raise ExecutorError(f'Native engine create index encounters error: {resp.error}')

    def _get_evadb_index_save_path(self) -> Path:
        index_dir = Path(self.db.catalog().get_configuration_catalog_value('index_dir'))
        if not index_dir.exists():
            index_dir.mkdir(parents=True, exist_ok=True)
        return str(index_dir / Path('{}_{}.index'.format(self.vector_store_type, self.name)))

    def _create_evadb_index(self):
        function_expression, function_expression_signature = (None, None)
        for project_expr in self.project_expr_list:
            if isinstance(project_expr, FunctionExpression):
                function_expression = project_expr
                function_expression_signature = project_expr.signature()
        feat_tb_catalog_entry = self.table_ref.table.table_obj
        feat_col_name = self.col_list[0].name
        feat_col_catalog_entry = [col for col in feat_tb_catalog_entry.columns if col.name == feat_col_name][0]
        if function_expression is not None:
            feat_col_name = function_expression.output_objs[0].name
        index_catalog_entry = self.catalog().get_index_catalog_entry_by_name(self.name)
        index_path = self._get_evadb_index_save_path()
        if index_catalog_entry is not None:
            msg = f'Index {self.name} already exists.'
            if self.if_not_exists:
                if index_catalog_entry.feat_column == feat_col_catalog_entry and index_catalog_entry.function_signature == function_expression_signature and (index_catalog_entry.type == self.node.vector_store_type):
                    logger.warn(msg + ' It will be updated on existing table.')
                    index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.name, **handle_vector_store_params(self.vector_store_type, index_path, self.catalog))
                else:
                    logger.warn(msg)
                    return
            else:
                logger.error(msg)
                raise ExecutorError(msg)
        else:
            index = None
        try:
            for input_batch in self.children[0].exec():
                input_batch.drop_column_alias()
                feat = input_batch.column_as_numpy_array(feat_col_name)
                row_num = input_batch.column_as_numpy_array(ROW_NUM_COLUMN)
                for i in range(len(input_batch)):
                    row_feat = feat[i].reshape(1, -1)
                    if index is None:
                        input_dim = row_feat.shape[1]
                        index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.name, **handle_vector_store_params(self.vector_store_type, index_path, self.catalog))
                        index.create(input_dim)
                    index.add([FeaturePayload(row_num[i], row_feat)])
            index.persist()
            if index_catalog_entry is None:
                self.catalog().insert_index_catalog_entry(self.name, index_path, self.vector_store_type, feat_col_catalog_entry, function_expression_signature, self.index_def)
        except Exception as e:
            if index:
                index.delete()
            raise ExecutorError(str(e))

def _create_native_index(self):
    table = self.table_ref.table
    db_catalog_entry = self.catalog().get_database_catalog_entry(table.database_name)
    with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
        resp = handler.execute_native_query(f'CREATE INDEX {self.name} ON {table.table_name}\n                    USING hnsw ({self.col_list[0].name} vector_l2_ops)')
        if resp.error is not None:
            raise ExecutorError(f'Native engine create index encounters error: {resp.error}')

def _create_evadb_index(self):
    function_expression, function_expression_signature = (None, None)
    for project_expr in self.project_expr_list:
        if isinstance(project_expr, FunctionExpression):
            function_expression = project_expr
            function_expression_signature = project_expr.signature()
    feat_tb_catalog_entry = self.table_ref.table.table_obj
    feat_col_name = self.col_list[0].name
    feat_col_catalog_entry = [col for col in feat_tb_catalog_entry.columns if col.name == feat_col_name][0]
    if function_expression is not None:
        feat_col_name = function_expression.output_objs[0].name
    index_catalog_entry = self.catalog().get_index_catalog_entry_by_name(self.name)
    index_path = self._get_evadb_index_save_path()
    if index_catalog_entry is not None:
        msg = f'Index {self.name} already exists.'
        if self.if_not_exists:
            if index_catalog_entry.feat_column == feat_col_catalog_entry and index_catalog_entry.function_signature == function_expression_signature and (index_catalog_entry.type == self.node.vector_store_type):
                logger.warn(msg + ' It will be updated on existing table.')
                index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.name, **handle_vector_store_params(self.vector_store_type, index_path, self.catalog))
            else:
                logger.warn(msg)
                return
        else:
            logger.error(msg)
            raise ExecutorError(msg)
    else:
        index = None
    try:
        for input_batch in self.children[0].exec():
            input_batch.drop_column_alias()
            feat = input_batch.column_as_numpy_array(feat_col_name)
            row_num = input_batch.column_as_numpy_array(ROW_NUM_COLUMN)
            for i in range(len(input_batch)):
                row_feat = feat[i].reshape(1, -1)
                if index is None:
                    input_dim = row_feat.shape[1]
                    index = VectorStoreFactory.init_vector_store(self.vector_store_type, self.name, **handle_vector_store_params(self.vector_store_type, index_path, self.catalog))
                    index.create(input_dim)
                index.add([FeaturePayload(row_num[i], row_feat)])
        index.persist()
        if index_catalog_entry is None:
            self.catalog().insert_index_catalog_entry(self.name, index_path, self.vector_store_type, feat_col_catalog_entry, function_expression_signature, self.index_def)
    except Exception as e:
        if index:
            index.delete()
        raise ExecutorError(str(e))

class StatementBinder:

    def __init__(self, binder_context: StatementBinderContext):
        self._binder_context = binder_context
        self._catalog: Callable = binder_context._catalog

    @singledispatchmethod
    def bind(self, node):
        raise NotImplementedError(f'Cannot bind {type(node)}')

    @bind.register(AbstractStatement)
    def _bind_abstract_statement(self, node: AbstractStatement):
        pass

    @bind.register(AbstractExpression)
    def _bind_abstract_expr(self, node: AbstractExpression):
        for child in node.children:
            self.bind(child)

    @bind.register(ExplainStatement)
    def _bind_explain_statement(self, node: ExplainStatement):
        self.bind(node.explainable_stmt)

    @bind.register(CreateFunctionStatement)
    def _bind_create_function_statement(self, node: CreateFunctionStatement):
        if node.query is not None:
            self.bind(node.query)
            node.query.target_list = drop_row_id_from_target_list(node.query.target_list)
            all_column_list = get_column_definition_from_select_target_list(node.query.target_list)
            arg_map = {key: value for key, value in node.metadata}
            inputs, outputs = ([], [])
            if string_comparison_case_insensitive(node.function_type, 'ludwig'):
                assert 'predict' in arg_map, f"Creating {node.function_type} functions expects 'predict' metadata."
                predict_columns = set([arg_map['predict']])
                for column in all_column_list:
                    if column.name in predict_columns:
                        column.name = column.name + '_predictions'
                        outputs.append(column)
                    else:
                        inputs.append(column)
            elif string_comparison_case_insensitive(node.function_type, 'sklearn') or string_comparison_case_insensitive(node.function_type, 'XGBoost'):
                assert 'predict' in arg_map, f"Creating {node.function_type} functions expects 'predict' metadata."
                predict_columns = set([arg_map['predict']])
                for column in all_column_list:
                    if column.name in predict_columns:
                        outputs.append(column)
                    else:
                        inputs.append(column)
            elif string_comparison_case_insensitive(node.function_type, 'forecasting'):
                inputs = [ColumnDefinition('horizon', ColumnType.INTEGER, None, None)]
                required_columns = set([arg_map.get('predict', 'y')])
                for column in all_column_list:
                    if column.name == arg_map.get('id', 'unique_id'):
                        outputs.append(column)
                    elif column.name == arg_map.get('time', 'ds'):
                        outputs.append(column)
                    elif column.name == arg_map.get('predict', 'y'):
                        outputs.append(column)
                        required_columns.remove(column.name)
                assert len(required_columns) == 0, f'Missing required {required_columns} columns for forecasting function.'
                outputs.extend([ColumnDefinition(arg_map.get('predict', 'y') + '-lo', ColumnType.FLOAT, None, None), ColumnDefinition(arg_map.get('predict', 'y') + '-hi', ColumnType.FLOAT, None, None)])
            else:
                raise BinderError(f'Unsupported type of function: {node.function_type}.')
            assert len(node.inputs) == 0 and len(node.outputs) == 0, f"{node.function_type} functions' input and output are auto assigned"
            node.inputs, node.outputs = (inputs, outputs)

    @bind.register(SelectStatement)
    def _bind_select_statement(self, node: SelectStatement):
        if node.from_table:
            self.bind(node.from_table)
        if node.where_clause:
            self.bind(node.where_clause)
            if node.where_clause.etype == ExpressionType.COMPARE_LIKE:
                check_column_name_is_string(node.where_clause.children[0])
        if node.target_list:
            if len(node.target_list) == 1 and isinstance(node.target_list[0], TupleValueExpression) and (node.target_list[0].name == '*'):
                node.target_list = extend_star(self._binder_context)
            for expr in node.target_list:
                self.bind(expr)
                if isinstance(expr, FunctionExpression):
                    output_cols = get_bound_func_expr_outputs_as_tuple_value_expr(expr)
                    self._binder_context.add_derived_table_alias(expr.alias.alias_name, output_cols)
        if node.groupby_clause:
            self.bind(node.groupby_clause)
            check_table_object_is_groupable(node.from_table)
            check_groupby_pattern(node.from_table, node.groupby_clause.value)
        if node.orderby_list:
            for expr in node.orderby_list:
                self.bind(expr[0])
        if node.union_link:
            current_context = self._binder_context
            self._binder_context = StatementBinderContext(self._catalog)
            self.bind(node.union_link)
            self._binder_context = current_context
        if node.from_table and node.from_table.chunk_params:
            assert is_document_table(node.from_table.table.table_obj), 'CHUNK related parameters only supported for DOCUMENT tables.'
        assert not (self._binder_context.is_retrieve_audio() and self._binder_context.is_retrieve_video()), 'Cannot query over both audio and video streams'
        if self._binder_context.is_retrieve_audio():
            node.from_table.get_audio = True
        if self._binder_context.is_retrieve_video():
            node.from_table.get_video = True

    @bind.register(DeleteTableStatement)
    def _bind_delete_statement(self, node: DeleteTableStatement):
        self.bind(node.table_ref)
        if node.where_clause:
            self.bind(node.where_clause)

    @bind.register(CreateTableStatement)
    def _bind_create_statement(self, node: CreateTableStatement):
        for col in node.column_list:
            assert col.name.lower() not in RESTRICTED_COL_NAMES, f'EvaDB does not allow to create a table with column name {col.name}'
        if node.query is not None:
            self.bind(node.query)
            node.column_list = get_column_definition_from_select_target_list(node.query.target_list)

    @bind.register(CreateIndexStatement)
    def _bind_create_index_statement(self, node: CreateIndexStatement):
        from evadb.binder.create_index_statement_binder import bind_create_index
        bind_create_index(self, node)

    @bind.register(RenameTableStatement)
    def _bind_rename_table_statement(self, node: RenameTableStatement):
        self.bind(node.old_table_ref)
        assert node.old_table_ref.table.table_obj.table_type != TableType.STRUCTURED_DATA, 'Rename not yet supported on structured data'

    @bind.register(TableRef)
    def _bind_tableref(self, node: TableRef):
        if node.is_table_atom():
            self._binder_context.add_table_alias(node.alias.alias_name, node.table.database_name, node.table.table_name)
            bind_table_info(self._catalog(), node.table)
        elif node.is_select():
            current_context = self._binder_context
            self._binder_context = StatementBinderContext(self._catalog)
            self.bind(node.select_statement)
            self._binder_context = current_context
            self._binder_context.add_derived_table_alias(node.alias.alias_name, node.select_statement.target_list)
        elif node.is_join():
            self.bind(node.join_node.left)
            self.bind(node.join_node.right)
            if node.join_node.predicate:
                self.bind(node.join_node.predicate)
        elif node.is_table_valued_expr():
            func_expr = node.table_valued_expr.func_expr
            func_expr.alias = node.alias
            self.bind(func_expr)
            output_cols = get_bound_func_expr_outputs_as_tuple_value_expr(func_expr)
            self._binder_context.add_derived_table_alias(func_expr.alias.alias_name, output_cols)
        else:
            raise BinderError(f'Unsupported node {type(node)}')

    @bind.register(TupleValueExpression)
    def _bind_tuple_expr(self, node: TupleValueExpression):
        from evadb.binder.tuple_value_expression_binder import bind_tuple_expr
        bind_tuple_expr(self, node)

    @bind.register(FunctionExpression)
    def _bind_func_expr(self, node: FunctionExpression):
        from evadb.binder.function_expression_binder import bind_func_expr
        bind_func_expr(self, node)

@bind.register(AbstractStatement)
def _bind_abstract_statement(self, node: AbstractStatement):
    pass

@bind.register(AbstractExpression)
def _bind_abstract_expr(self, node: AbstractExpression):
    for child in node.children:
        self.bind(child)

@bind.register(ExplainStatement)
def _bind_explain_statement(self, node: ExplainStatement):
    self.bind(node.explainable_stmt)

@bind.register(CreateFunctionStatement)
def _bind_create_function_statement(self, node: CreateFunctionStatement):
    if node.query is not None:
        self.bind(node.query)
        node.query.target_list = drop_row_id_from_target_list(node.query.target_list)
        all_column_list = get_column_definition_from_select_target_list(node.query.target_list)
        arg_map = {key: value for key, value in node.metadata}
        inputs, outputs = ([], [])
        if string_comparison_case_insensitive(node.function_type, 'ludwig'):
            assert 'predict' in arg_map, f"Creating {node.function_type} functions expects 'predict' metadata."
            predict_columns = set([arg_map['predict']])
            for column in all_column_list:
                if column.name in predict_columns:
                    column.name = column.name + '_predictions'
                    outputs.append(column)
                else:
                    inputs.append(column)
        elif string_comparison_case_insensitive(node.function_type, 'sklearn') or string_comparison_case_insensitive(node.function_type, 'XGBoost'):
            assert 'predict' in arg_map, f"Creating {node.function_type} functions expects 'predict' metadata."
            predict_columns = set([arg_map['predict']])
            for column in all_column_list:
                if column.name in predict_columns:
                    outputs.append(column)
                else:
                    inputs.append(column)
        elif string_comparison_case_insensitive(node.function_type, 'forecasting'):
            inputs = [ColumnDefinition('horizon', ColumnType.INTEGER, None, None)]
            required_columns = set([arg_map.get('predict', 'y')])
            for column in all_column_list:
                if column.name == arg_map.get('id', 'unique_id'):
                    outputs.append(column)
                elif column.name == arg_map.get('time', 'ds'):
                    outputs.append(column)
                elif column.name == arg_map.get('predict', 'y'):
                    outputs.append(column)
                    required_columns.remove(column.name)
            assert len(required_columns) == 0, f'Missing required {required_columns} columns for forecasting function.'
            outputs.extend([ColumnDefinition(arg_map.get('predict', 'y') + '-lo', ColumnType.FLOAT, None, None), ColumnDefinition(arg_map.get('predict', 'y') + '-hi', ColumnType.FLOAT, None, None)])
        else:
            raise BinderError(f'Unsupported type of function: {node.function_type}.')
        assert len(node.inputs) == 0 and len(node.outputs) == 0, f"{node.function_type} functions' input and output are auto assigned"
        node.inputs, node.outputs = (inputs, outputs)

@bind.register(SelectStatement)
def _bind_select_statement(self, node: SelectStatement):
    if node.from_table:
        self.bind(node.from_table)
    if node.where_clause:
        self.bind(node.where_clause)
        if node.where_clause.etype == ExpressionType.COMPARE_LIKE:
            check_column_name_is_string(node.where_clause.children[0])
    if node.target_list:
        if len(node.target_list) == 1 and isinstance(node.target_list[0], TupleValueExpression) and (node.target_list[0].name == '*'):
            node.target_list = extend_star(self._binder_context)
        for expr in node.target_list:
            self.bind(expr)
            if isinstance(expr, FunctionExpression):
                output_cols = get_bound_func_expr_outputs_as_tuple_value_expr(expr)
                self._binder_context.add_derived_table_alias(expr.alias.alias_name, output_cols)
    if node.groupby_clause:
        self.bind(node.groupby_clause)
        check_table_object_is_groupable(node.from_table)
        check_groupby_pattern(node.from_table, node.groupby_clause.value)
    if node.orderby_list:
        for expr in node.orderby_list:
            self.bind(expr[0])
    if node.union_link:
        current_context = self._binder_context
        self._binder_context = StatementBinderContext(self._catalog)
        self.bind(node.union_link)
        self._binder_context = current_context
    if node.from_table and node.from_table.chunk_params:
        assert is_document_table(node.from_table.table.table_obj), 'CHUNK related parameters only supported for DOCUMENT tables.'
    assert not (self._binder_context.is_retrieve_audio() and self._binder_context.is_retrieve_video()), 'Cannot query over both audio and video streams'
    if self._binder_context.is_retrieve_audio():
        node.from_table.get_audio = True
    if self._binder_context.is_retrieve_video():
        node.from_table.get_video = True

@bind.register(DeleteTableStatement)
def _bind_delete_statement(self, node: DeleteTableStatement):
    self.bind(node.table_ref)
    if node.where_clause:
        self.bind(node.where_clause)

@bind.register(CreateTableStatement)
def _bind_create_statement(self, node: CreateTableStatement):
    for col in node.column_list:
        assert col.name.lower() not in RESTRICTED_COL_NAMES, f'EvaDB does not allow to create a table with column name {col.name}'
    if node.query is not None:
        self.bind(node.query)
        node.column_list = get_column_definition_from_select_target_list(node.query.target_list)

@bind.register(CreateIndexStatement)
def _bind_create_index_statement(self, node: CreateIndexStatement):
    from evadb.binder.create_index_statement_binder import bind_create_index
    bind_create_index(self, node)

@bind.register(RenameTableStatement)
def _bind_rename_table_statement(self, node: RenameTableStatement):
    self.bind(node.old_table_ref)
    assert node.old_table_ref.table.table_obj.table_type != TableType.STRUCTURED_DATA, 'Rename not yet supported on structured data'

@bind.register(TupleValueExpression)
def _bind_tuple_expr(self, node: TupleValueExpression):
    from evadb.binder.tuple_value_expression_binder import bind_tuple_expr
    bind_tuple_expr(self, node)

@bind.register(FunctionExpression)
def _bind_func_expr(self, node: FunctionExpression):
    from evadb.binder.function_expression_binder import bind_func_expr
    bind_func_expr(self, node)

class StatementBinderContext:
    """
    This context is used to store information that is useful during the process of binding a statement (such as a SELECT statement) to the catalog. It stores the following information:

    Args:
        `_table_alias_map`: Maintains a mapping from table_alias to corresponding
        catalog table entry
        `_derived_table_alias_map`: Maintains a mapping from derived table aliases,
        such as subqueries or function expressions, to column alias maps for all the
        corresponding projected columns. For example, in the following queries, the
        `_derived_table_alias_map` attribute would contain:

        `Select * FROM (SELECT id1, id2 FROM table) AS A` :
            `{A: {id1: table.col1, id2: table.col2}}`
        `Select * FROM video LATERAL JOIN func AS T(a, b)` :
            `{T: {a: func.obj1, b:func.obj2}}`
    """

    def __init__(self, catalog: Callable):
        self._catalog = catalog
        self._table_alias_map: Dict[str, TableCatalogEntry] = dict()
        self._derived_table_alias_map: Dict[str, Dict[str, CatalogColumnType]] = dict()
        self._retrieve_audio = False
        self._retrieve_video = False

    def _check_duplicate_alias(self, alias: str):
        """
        Sanity check: no duplicate alias in table and derived_table
        Arguments:
            alias (str): name of the alias

        Exception:
            Raise exception if found duplication
        """
        if alias in self._derived_table_alias_map or alias in self._table_alias_map:
            err_msg = f'Found duplicate alias {alias}'
            logger.error(err_msg)
            raise BinderError(err_msg)

    def add_table_alias(self, alias: str, database_name: str, table_name: str):
        """
        Add a alias -> table_name mapping
        Arguments:
            alias (str): name of alias
            table_name (str): name of the table
        """
        self._check_duplicate_alias(alias)
        if database_name is not None:
            check_data_source_and_table_are_valid(self._catalog(), database_name, table_name)
            db_catalog_entry = self._catalog().get_database_catalog_entry(database_name)
            with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
                response = handler.get_columns(table_name)
                if response.error is not None:
                    raise BinderError(response.error)
                column_df = response.data
                table_obj = create_table_catalog_entry_for_data_source(table_name, database_name, column_df)
        else:
            table_obj = self._catalog().get_table_catalog_entry(table_name)
        self._table_alias_map[alias] = table_obj

    def add_derived_table_alias(self, alias: str, target_list: List[Union[TupleValueExpression, FunctionExpression, FunctionIOCatalogEntry]]):
        """
        Add a alias -> derived table column mapping
        Arguments:
            alias (str): name of alias
            target_list: list of TupleValueExpression or FunctionExpression or FunctionIOCatalogEntry
        """
        self._check_duplicate_alias(alias)
        col_alias_map = {}
        for expr in target_list:
            if isinstance(expr, FunctionExpression):
                for obj in expr.output_objs:
                    col_alias_map[obj.name] = obj
            elif isinstance(expr, TupleValueExpression):
                col_alias_map[expr.name] = expr.col_object
            else:
                continue
        self._derived_table_alias_map[alias] = col_alias_map

    def get_binded_column(self, col_name: str, alias: str=None) -> Tuple[str, CatalogColumnType]:
        """
        Find the binded column object
        Arguments:
            col_name (str): column name
            alias (str): alias name

        Returns:
            A tuple of alias and column object
        """
        col_name = col_name.lower()

        def raise_error():
            all_columns = sorted(list(set([col for _, col in self._get_all_alias_and_col_name()])))
            res = process.extractOne(col_name, all_columns)
            if res is not None:
                guess_column, _ = res
                err_msg = f'Cannot find column {col_name}. Did you mean {guess_column}? The feasible columns are {all_columns}.'
            else:
                err_msg = f'Cannot find column {col_name}. There are no feasible columns.'
            logger.error(err_msg)
            raise BinderError(err_msg)
        if not alias:
            alias, col_obj = self._search_all_alias_maps(col_name)
        else:
            col_obj = self._check_table_alias_map(alias, col_name)
            if not col_obj:
                col_obj = self._check_derived_table_alias_map(alias, col_name)
        if col_obj:
            return (alias, col_obj)
        raise_error()

    def _check_table_alias_map(self, alias, col_name) -> ColumnCatalogEntry:
        """
        Find the column object in table alias map
        Arguments:
            col_name (str): column name
            alias (str): alias name

        Returns:
            column object
        """
        table_obj = self._table_alias_map.get(alias, None)
        if table_obj is not None:
            if table_obj.table_type == TableType.NATIVE_DATA:
                for column_catalog_entry in table_obj.columns:
                    if column_catalog_entry.name == col_name:
                        return column_catalog_entry
            else:
                return self._catalog().get_column_catalog_entry(table_obj, col_name)

    def _check_derived_table_alias_map(self, alias, col_name) -> CatalogColumnType:
        """
        Find the column object in derived table alias map
        Arguments:
            col_name (str): column name
            alias (str): alias name

        Returns:
            column object
        """
        col_objs_map = self._derived_table_alias_map.get(alias, None)
        if col_objs_map is None:
            return None
        for name, obj in col_objs_map.items():
            if name == col_name:
                return obj

    def _get_all_alias_and_col_name(self) -> List[Tuple[str, str]]:
        """
        Return all alias and column objects mapping in the current context
        Returns:
            a list of tuple of alias name, column name
        """
        alias_cols = []
        for alias, table_obj in self._table_alias_map.items():
            alias_cols += list([(alias, col.name) for col in table_obj.columns])
        for alias, col_objs_map in self._derived_table_alias_map.items():
            alias_cols += list([(alias, col_name) for col_name in col_objs_map])
        return alias_cols

    def _search_all_alias_maps(self, col_name: str) -> Tuple[str, CatalogColumnType]:
        """
        Search the alias and column object using column name
        Arguments:
            col_name (str): column name

        Returns:
            A tuple of alias and column object.
        """
        num_alias_matches = 0
        alias_match = None
        match_obj = None
        for alias in self._table_alias_map:
            col_obj = self._check_table_alias_map(alias, col_name)
            if col_obj:
                match_obj = col_obj
                num_alias_matches += 1
                alias_match = alias
        for alias in self._derived_table_alias_map:
            col_obj = self._check_derived_table_alias_map(alias, col_name)
            if col_obj:
                match_obj = col_obj
                num_alias_matches += 1
                alias_match = alias
        if num_alias_matches > 1:
            err_msg = f'Ambiguous Column name {col_name}'
            logger.error(err_msg)
            raise BinderError(err_msg)
        return (alias_match, match_obj)

    def enable_audio_retrieval(self):
        self._retrieve_audio = True

    def is_retrieve_audio(self):
        return self._retrieve_audio

    def enable_video_retrieval(self):
        self._retrieve_video = True

    def is_retrieve_video(self):
        return self._retrieve_video

def _check_duplicate_alias(self, alias: str):
    """
        Sanity check: no duplicate alias in table and derived_table
        Arguments:
            alias (str): name of the alias

        Exception:
            Raise exception if found duplication
        """
    if alias in self._derived_table_alias_map or alias in self._table_alias_map:
        err_msg = f'Found duplicate alias {alias}'
        logger.error(err_msg)
        raise BinderError(err_msg)

def add_table_alias(self, alias: str, database_name: str, table_name: str):
    """
        Add a alias -> table_name mapping
        Arguments:
            alias (str): name of alias
            table_name (str): name of the table
        """
    self._check_duplicate_alias(alias)
    if database_name is not None:
        check_data_source_and_table_are_valid(self._catalog(), database_name, table_name)
        db_catalog_entry = self._catalog().get_database_catalog_entry(database_name)
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            response = handler.get_columns(table_name)
            if response.error is not None:
                raise BinderError(response.error)
            column_df = response.data
            table_obj = create_table_catalog_entry_for_data_source(table_name, database_name, column_df)
    else:
        table_obj = self._catalog().get_table_catalog_entry(table_name)
    self._table_alias_map[alias] = table_obj

def add_derived_table_alias(self, alias: str, target_list: List[Union[TupleValueExpression, FunctionExpression, FunctionIOCatalogEntry]]):
    """
        Add a alias -> derived table column mapping
        Arguments:
            alias (str): name of alias
            target_list: list of TupleValueExpression or FunctionExpression or FunctionIOCatalogEntry
        """
    self._check_duplicate_alias(alias)
    col_alias_map = {}
    for expr in target_list:
        if isinstance(expr, FunctionExpression):
            for obj in expr.output_objs:
                col_alias_map[obj.name] = obj
        elif isinstance(expr, TupleValueExpression):
            col_alias_map[expr.name] = expr.col_object
        else:
            continue
    self._derived_table_alias_map[alias] = col_alias_map

def _check_table_alias_map(self, alias, col_name) -> ColumnCatalogEntry:
    """
        Find the column object in table alias map
        Arguments:
            col_name (str): column name
            alias (str): alias name

        Returns:
            column object
        """
    table_obj = self._table_alias_map.get(alias, None)
    if table_obj is not None:
        if table_obj.table_type == TableType.NATIVE_DATA:
            for column_catalog_entry in table_obj.columns:
                if column_catalog_entry.name == col_name:
                    return column_catalog_entry
        else:
            return self._catalog().get_column_catalog_entry(table_obj, col_name)

def check_data_source_and_table_are_valid(catalog: CatalogManager, database_name: str, table_name: str):
    """
    Validate the database is valid and the requested table in database is
    also valid.
    """
    error = None
    if catalog.get_database_catalog_entry(database_name) is None:
        error = '{} data source does not exist. Create the new database source using CREATE DATABASE.'.format(database_name)
    if not catalog.check_table_exists(table_name, database_name):
        error = 'Table {} does not exist in data source {}. Create the table using native query.'.format(table_name, database_name)
    if error:
        logger.error(error)
        raise BinderError(error)

def bind_native_table_info(catalog: CatalogManager, table_info: TableInfo):
    check_data_source_and_table_are_valid(catalog, table_info.database_name, table_info.table_name)
    db_catalog_entry = catalog.get_database_catalog_entry(table_info.database_name)
    with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
        column_df = handler.get_columns(table_info.table_name).data
        table_info.table_obj = create_table_catalog_entry_for_data_source(table_info.table_name, table_info.database_name, column_df)

def bind_evadb_table_info(catalog: CatalogManager, table_info: TableInfo):
    obj = catalog.get_table_catalog_entry(table_info.table_name, table_info.database_name)
    if obj and obj.table_type == TableType.SYSTEM_STRUCTURED_DATA:
        err_msg = f'The query attempted to access or modify the internal table{table_info.table_name} of the system, but permission was denied.'
        logger.error(err_msg)
        raise BinderError(err_msg)
    if obj:
        table_info.table_obj = obj
    else:
        error = '{} does not exist. Create the table using CREATE TABLE.'.format(table_info.table_name)
        logger.error(error)
        raise BinderError(error)

def check_groupby_pattern(table_ref: TableRef, groupby_string: str) -> None:
    pattern = re.search('^\\d+\\s*(?:frames|samples|paragraphs)$', groupby_string)
    if not pattern:
        err_msg = 'Incorrect GROUP BY pattern: {}'.format(groupby_string)
        raise BinderError(err_msg)
    match_string = pattern.group(0)
    suffix_string = re.sub('^\\d+\\s*', '', match_string)
    if suffix_string not in ['frames', 'samples', 'paragraphs']:
        err_msg = 'Grouping only supported by frames for videos, by samples for audio, and by paragraphs for documents'
        raise BinderError(err_msg)
    if suffix_string == 'frames' and (not is_video_table(table_ref.table.table_obj)):
        err_msg = 'Grouping by frames only supported for videos'
        raise BinderError(err_msg)
    if suffix_string == 'samples' and (not is_video_table(table_ref.table.table_obj)):
        err_msg = 'Grouping by samples only supported for videos'
        raise BinderError(err_msg)
    if suffix_string == 'paragraphs' and (not is_pdf_table(table_ref.table.table_obj)):
        err_msg = 'Grouping by paragraphs only supported for pdf tables'
        raise BinderError(err_msg)

def check_table_object_is_groupable(table_ref: TableRef) -> None:
    table_obj = table_ref.table.table_obj
    if not (is_video_table(table_obj) or is_document_table(table_obj) or is_pdf_table(table_obj)):
        raise BinderError('GROUP BY only supported for video and document tables')

def check_column_name_is_string(col_ref) -> None:
    if not is_string_col(col_ref.col_object):
        err_msg = 'LIKE only supported for string columns'
        raise BinderError(err_msg)

def bind_create_index(binder: StatementBinder, node: CreateIndexStatement):
    binder.bind(node.table_ref)
    func_project_expr = None
    for project_expr in node.project_expr_list:
        binder.bind(project_expr)
        if isinstance(project_expr, FunctionExpression):
            func_project_expr = project_expr
    node.project_expr_list += [create_row_num_tv_expr(node.table_ref.alias)]
    assert len(node.col_list) == 1, 'Index cannot be created on more than 1 column'
    assert node.table_ref.is_table_atom(), 'Index can only be created on an existing table'
    catalog = binder._catalog()
    if node.vector_store_type == VectorStoreType.PGVECTOR:
        db_catalog_entry = catalog.get_database_catalog_entry(node.table_ref.table.database_name)
        if db_catalog_entry.engine != 'postgres':
            raise BinderError('PGVECTOR index works only with Postgres data source.')
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            df = handler.execute_native_query("SELECT * FROM pg_extension WHERE extname = 'vector'").data
            if len(df) == 0:
                raise BinderError('PGVECTOR extension is not enabled.')
        return
    assert len(node.col_list) == 1, f'Index can be only created on one column, but instead {len(node.col_list)} are provided'
    col_def = node.col_list[0]
    if func_project_expr is None:
        table_ref_obj = node.table_ref.table.table_obj
        col_list = [col for col in table_ref_obj.columns if col.name == col_def.name]
        assert len(col_list) == 1, f'Index is created on non-existent column {col_def.name}'
        col = col_list[0]
        assert len(col.array_dimensions) == 2
        if node.vector_store_type == VectorStoreType.FAISS:
            assert col.array_type == NdArrayType.FLOAT32, 'Index input needs to be float32.'
    else:
        function_obj = binder._catalog().get_function_catalog_entry_by_name(func_project_expr.name)
        for output in function_obj.outputs:
            assert len(output.array_dimensions) == 2, 'Index input needs to be 2 dimensional.'
            if node.vector_store_type == VectorStoreType.FAISS:
                assert output.array_type == NdArrayType.FLOAT32, 'Index input needs to be float32.'

class FunctionExpression(AbstractExpression):
    """
    Consider FunctionExpression: ObjDetector -> (labels, boxes)

    `output`: If the user wants only subset of outputs. Eg,
    ObjDetector.labels the parser with set output to 'labels'

    `output_objs`: It is populated by the binder. In case the
    output is None, the binder sets output_objs to list of all
    output columns of the FunctionExpression. Eg, ['labels',
    'boxes']. Otherwise, only the output columns.

    FunctionExpression also needs to prepend its alias to all the
    projected columns. This is important as other parts of the query
    might be assessing the results using alias. Eg,

    `Select Detector.labels
     FROM Video JOIN LATERAL ObjDetector AS Detector;`
    """

    def __init__(self, func: Callable, name: str, output: str=None, alias: Alias=None, **kwargs):
        super().__init__(ExpressionType.FUNCTION_EXPRESSION, **kwargs)
        self._context = Context()
        self._name = name
        self._function = func
        self._function_instance = None
        self._output = output
        self.alias = alias
        self.function_obj: FunctionCatalogEntry = None
        self.output_objs: List[FunctionIOCatalogEntry] = []
        self.projection_columns: List[str] = []
        self._cache: FunctionExpressionCache = None
        self._stats = FunctionStats()

    @property
    def name(self):
        return self._name

    @property
    def output(self):
        return self._output

    @property
    def col_alias(self):
        col_alias_list = []
        if self.alias is not None:
            for col in self.alias.col_names:
                col_alias_list.append('{}.{}'.format(self.alias.alias_name, col))
        return col_alias_list

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, func: Callable):
        self._function = func

    def enable_cache(self, cache: 'FunctionExpressionCache'):
        self._cache = cache
        return self

    def has_cache(self):
        return self._cache is not None

    def consolidate_stats(self):
        if self.function_obj is None:
            return
        if self.has_cache() and self._stats.cache_misses > 0:
            cost_per_func_call = self._stats.timer.total_elapsed_time / self._stats.cache_misses
        else:
            cost_per_func_call = self._stats.timer.total_elapsed_time / self._stats.num_calls
        if abs(self._stats.prev_cost - cost_per_func_call) > cost_per_func_call / 10:
            self._stats.prev_cost = cost_per_func_call

    def evaluate(self, batch: Batch, **kwargs) -> Batch:
        func = self._gpu_enabled_function()
        with self._stats.timer:
            outcomes = self._apply_function_expression(func, batch, **kwargs)
            if outcomes.frames.empty is False:
                outcomes = outcomes.project(self.projection_columns)
                outcomes.modify_column_alias(self.alias)
        self._stats.num_calls += len(batch)
        try:
            self.consolidate_stats()
        except Exception as e:
            logger.warn(f'Persisting FunctionExpression {str(self)} stats failed with {str(e)}')
        return outcomes

    def signature(self) -> str:
        """It constructs the signature of the function expression.
        It traverses the children (function arguments) and compute signature for each
        child. The output is in the form `function_name[row_id](arg1, arg2, ...)`.

        Returns:
            str: signature string
        """
        child_sigs = []
        for child in self.children:
            child_sigs.append(child.signature())
        func_sig = f'{self.name}[{self.function_obj.row_id}]({','.join(child_sigs)})'
        return func_sig

    def _gpu_enabled_function(self):
        if self._function_instance is None:
            self._function_instance = self.function()
            if isinstance(self._function_instance, GPUCompatible):
                device = self._context.gpu_device()
                if device != NO_GPU:
                    self._function_instance = self._function_instance.to_device(device)
        return self._function_instance

    def _apply_function_expression(self, func: Callable, batch: Batch, **kwargs):
        """
        If cache is not enabled, call the func on the batch and return.
        If cache is enabled:
        (1) iterate over the input batch rows and check if we have the value in the
        cache;
        (2) for all cache miss rows, call the func;
        (3) iterate over each cache miss row and store the results in the cache;
        (4) stitch back the partial cache results with the new func calls.
        """
        func_args = Batch.merge_column_wise([child.evaluate(batch, **kwargs) for child in self.children])
        if not self._cache:
            return func_args.apply_function_expression(func)
        output_cols = [obj.name for obj in self.function_obj.outputs]
        results = np.full([len(batch), len(output_cols)], None)
        cache_keys = func_args
        if self._cache.key:
            cache_keys = Batch.merge_column_wise([child.evaluate(batch, **kwargs) for child in self._cache.key])
            assert len(cache_keys) == len(batch), 'Not all rows have the cache key'
        cache_miss = np.full(len(batch), True)
        for idx, (_, key) in enumerate(cache_keys.iterrows()):
            val = self._cache.store.get(key.to_numpy())
            results[idx] = val
            cache_miss[idx] = val is None
        self._stats.cache_misses += sum(cache_miss)
        if cache_miss.any():
            func_args = func_args[list(cache_miss)]
            cache_miss_results = func_args.apply_function_expression(func)
            missing_keys = cache_keys[list(cache_miss)]
            for key, value in zip(missing_keys.iterrows(), cache_miss_results.iterrows()):
                self._cache.store.set(key[1].to_numpy(), value[1].to_numpy())
            results[cache_miss] = cache_miss_results.to_numpy()
        return Batch(pd.DataFrame(results, columns=output_cols))

    def __str__(self) -> str:
        args = [str(child) for child in self.children]
        expr_str = f'{self.name}({','.join(args)})'
        return expr_str

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, FunctionExpression):
            return False
        return is_subtree_equal and self.name == other.name and (self.output == other.output) and (self.alias == other.alias) and (self.function == other.function) and (self.output_objs == other.output_objs) and (self._cache == other._cache)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.name, self.output, self.alias, self.function, tuple(self.output_objs), self._cache))

def evaluate(self, batch: Batch, **kwargs) -> Batch:
    func = self._gpu_enabled_function()
    with self._stats.timer:
        outcomes = self._apply_function_expression(func, batch, **kwargs)
        if outcomes.frames.empty is False:
            outcomes = outcomes.project(self.projection_columns)
            outcomes.modify_column_alias(self.alias)
    self._stats.num_calls += len(batch)
    try:
        self.consolidate_stats()
    except Exception as e:
        logger.warn(f'Persisting FunctionExpression {str(self)} stats failed with {str(e)}')
    return outcomes

class CatalogManager(object):

    def __init__(self, db_uri: str):
        self._db_uri = db_uri
        self._sql_config = SQLConfig(db_uri)
        self._bootstrap_catalog()
        self._db_catalog_service = DatabaseCatalogService(self._sql_config.session)
        self._config_catalog_service = ConfigurationCatalogService(self._sql_config.session)
        self._job_catalog_service = JobCatalogService(self._sql_config.session)
        self._job_history_catalog_service = JobHistoryCatalogService(self._sql_config.session)
        self._table_catalog_service = TableCatalogService(self._sql_config.session)
        self._column_service = ColumnCatalogService(self._sql_config.session)
        self._function_service = FunctionCatalogService(self._sql_config.session)
        self._function_cost_catalog_service = FunctionCostCatalogService(self._sql_config.session)
        self._function_io_service = FunctionIOCatalogService(self._sql_config.session)
        self._function_metadata_service = FunctionMetadataCatalogService(self._sql_config.session)
        self._index_service = IndexCatalogService(self._sql_config.session)
        self._function_cache_service = FunctionCacheCatalogService(self._sql_config.session)

    @property
    def sql_config(self):
        return self._sql_config

    def reset(self):
        """
        This method resets the state of the singleton instance.
        It should clear the contents of the catalog tables and any storage data
        Used by testcases to reset the db state before
        """
        self._clear_catalog_contents()

    def close(self):
        """
        This method closes all the connections
        """
        if self.sql_config is not None:
            sqlalchemy_engine = self.sql_config.engine
            sqlalchemy_engine.dispose()

    def _bootstrap_catalog(self):
        """Bootstraps catalog.
        This method runs all tasks required for using catalog. Currently,
        it includes only one task ie. initializing database. It creates the
        catalog database and tables if they do not exist.
        """
        logger.info('Bootstrapping catalog')
        init_db(self._sql_config.engine)

    def _clear_catalog_contents(self):
        """
        This method is responsible for clearing the contents of the
        catalog. It clears the tuples in the catalog tables, indexes, and cached data.
        """
        logger.info('Clearing catalog')
        drop_all_tables_except_catalog(self._sql_config.engine)
        truncate_catalog_tables(self._sql_config.engine, tables_not_to_truncate=['configuration_catalog'])
        for folder in ['cache_dir', 'index_dir', 'datasets_dir']:
            remove_directory_contents(self.get_configuration_catalog_value(folder))
    'Database catalog services'

    def insert_database_catalog_entry(self, name: str, engine: str, params: dict):
        """A new entry is persisted in the database catalog."

        Args:
            name: database name
            engine: engine name
            params: required params as a dictionary for the database
        """
        self._db_catalog_service.insert_entry(name, engine, params)

    def get_database_catalog_entry(self, database_name: str) -> DatabaseCatalogEntry:
        """
        Returns the database catalog entry for the given database_name
        Arguments:
            database_name (str): name of the database

        Returns:
            DatabaseCatalogEntry
        """
        table_entry = self._db_catalog_service.get_entry_by_name(database_name)
        return table_entry

    def get_all_database_catalog_entries(self):
        return self._db_catalog_service.get_all_entries()

    def drop_database_catalog_entry(self, database_entry: DatabaseCatalogEntry) -> bool:
        """
        This method deletes the database from  catalog.

        Arguments:
           database_entry: database catalog entry to remove

        Returns:
           True if successfully deleted else False
        """
        return self._db_catalog_service.delete_entry(database_entry)

    def check_native_table_exists(self, table_name: str, database_name: str):
        """
        Validate the database is valid and the requested table in database is
        also valid.
        """
        db_catalog_entry = self.get_database_catalog_entry(database_name)
        if db_catalog_entry is None:
            return False
        with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
            resp = handler.get_tables()
            if resp.error is not None:
                raise Exception(resp.error)
            table_df = resp.data
            if table_name not in table_df['table_name'].values:
                return False
        return True
    'Job catalog services'

    def insert_job_catalog_entry(self, name: str, queries: str, start_time: datetime, end_time: datetime, repeat_interval: int, active: bool, next_schedule_run: datetime) -> JobCatalogEntry:
        """A new entry is persisted in the job catalog.

        Args:
            name: job name
            queries: job's queries
            start_time: job start time
            end_time: job end time
            repeat_interval: job repeat interval
            active: job status
            next_schedule_run: next run time as per schedule
        """
        job_entry = self._job_catalog_service.insert_entry(name, queries, start_time, end_time, repeat_interval, active, next_schedule_run)
        return job_entry

    def get_job_catalog_entry(self, job_name: str) -> JobCatalogEntry:
        """
        Returns the job catalog entry for the given database_name
        Arguments:
            job_name (str): name of the job

        Returns:
            JobCatalogEntry
        """
        table_entry = self._job_catalog_service.get_entry_by_name(job_name)
        return table_entry

    def drop_job_catalog_entry(self, job_entry: JobCatalogEntry) -> bool:
        """
        This method deletes the job from  catalog.

        Arguments:
           job_entry: job catalog entry to remove

        Returns:
           True if successfully deleted else False
        """
        return self._job_catalog_service.delete_entry(job_entry)

    def get_next_executable_job(self, only_past_jobs: bool=False) -> JobCatalogEntry:
        """Get the oldest job that is ready to be triggered by trigger time
        Arguments:
            only_past_jobs: boolean flag to denote if only jobs with trigger time in
                past should be considered
        Returns:
            Returns the first job to be triggered
        """
        return self._job_catalog_service.get_next_executable_job(only_past_jobs)

    def update_job_catalog_entry(self, job_name: str, next_scheduled_run: datetime, active: bool):
        """Update the next_scheduled_run and active column as per the provided values
        Arguments:
            job_name (str): job which should be updated

            next_run_time (datetime): the next trigger time for the job

            active (bool): the active status for the job
        """
        self._job_catalog_service.update_next_scheduled_run(job_name, next_scheduled_run, active)
    'Job history catalog services'

    def insert_job_history_catalog_entry(self, job_id: str, job_name: str, execution_start_time: datetime, execution_end_time: datetime) -> JobCatalogEntry:
        """A new entry is persisted in the job history catalog.

        Args:
            job_id: job id for the execution entry
            job_name: job name for the execution entry
            execution_start_time: job execution start time
            execution_end_time: job execution end time
        """
        job_history_entry = self._job_history_catalog_service.insert_entry(job_id, job_name, execution_start_time, execution_end_time)
        return job_history_entry

    def get_job_history_by_job_id(self, job_id: int) -> List[JobHistoryCatalogEntry]:
        """Returns all the entries present for this job_id on in the history.

        Args:
            job_id: the id of job whose history should be fetched
        """
        return self._job_history_catalog_service.get_entry_by_job_id(job_id)

    def update_job_history_end_time(self, job_id: int, execution_start_time: datetime, execution_end_time: datetime) -> List[JobHistoryCatalogEntry]:
        """Updates the execution_end_time for this job history matching job_id and execution_start_time.

        Args:
            job_id: id of the job whose history entry which should be updated
            execution_start_time: the start time for the job history entry
            execution_end_time: the end time for the job history entry
        """
        return self._job_history_catalog_service.update_entry_end_time(job_id, execution_start_time, execution_end_time)
    'Table catalog services'

    def insert_table_catalog_entry(self, name: str, file_url: str, column_list: List[ColumnCatalogEntry], identifier_column='id', table_type=TableType.VIDEO_DATA) -> TableCatalogEntry:
        """A new entry is added to the table catalog and persisted in the database.
        The schema field is set before the object is returned."

        Args:
            name: table name
            file_url: #todo
            column_list: list of columns
            identifier_column (str):  A unique identifier column for each row
            table_type (TableType): type of the table, video, images etc
        Returns:
            The persisted TableCatalogEntry object with the id field populated.
        """
        column_list = [ColumnCatalogEntry(name=IDENTIFIER_COLUMN, type=ColumnType.INTEGER)] + column_list
        table_entry = self._table_catalog_service.insert_entry(name, file_url, identifier_column=identifier_column, table_type=table_type, column_list=column_list)
        return table_entry

    def get_table_catalog_entry(self, table_name: str, database_name: str=None) -> TableCatalogEntry:
        """
        Returns the table catalog entry for the given table name
        Arguments:
            table_name (str): name of the table

        Returns:
            TableCatalogEntry
        """
        table_entry = self._table_catalog_service.get_entry_by_name(database_name, table_name)
        return table_entry

    def delete_table_catalog_entry(self, table_entry: TableCatalogEntry) -> bool:
        """
        This method deletes the table along with its columns from table catalog
        and column catalog respectively

        Arguments:
           table: table catalog entry to remove

        Returns:
           True if successfully deleted else False
        """
        return self._table_catalog_service.delete_entry(table_entry)

    def rename_table_catalog_entry(self, curr_table: TableCatalogEntry, new_name: TableInfo):
        return self._table_catalog_service.rename_entry(curr_table, new_name.table_name)

    def check_table_exists(self, table_name: str, database_name: str=None):
        is_native_table = database_name is not None
        if is_native_table:
            return self.check_native_table_exists(table_name, database_name)
        else:
            table_entry = self._table_catalog_service.get_entry_by_name(database_name, table_name)
            return table_entry is not None

    def get_all_table_catalog_entries(self):
        return self._table_catalog_service.get_all_entries()
    'Column catalog services'

    def get_column_catalog_entry(self, table_obj: TableCatalogEntry, col_name: str) -> ColumnCatalogEntry:
        col_obj = self._column_service.filter_entry_by_table_id_and_name(table_obj.row_id, col_name)
        if col_obj:
            return col_obj
        else:
            if col_name == VideoColumnName.audio:
                return ColumnCatalogEntry(col_name, ColumnType.NDARRAY, table_id=table_obj.row_id, table_name=table_obj.name)
            return None

    def get_column_catalog_entries_by_table(self, table_obj: TableCatalogEntry):
        col_entries = self._column_service.filter_entries_by_table(table_obj)
        return col_entries
    'function catalog services'

    def insert_function_catalog_entry(self, name: str, impl_file_path: str, type: str, function_io_list: List[FunctionIOCatalogEntry], function_metadata_list: List[FunctionMetadataCatalogEntry]) -> FunctionCatalogEntry:
        """Inserts a function catalog entry along with Function_IO entries.
        It persists the entry to the database.

        Arguments:
            name(str): name of the function
            impl_file_path(str): implementation path of the function
            type(str): what kind of function operator like classification,
                                                        detection etc
            function_io_list(List[FunctionIOCatalogEntry]): input/output function info list

        Returns:
            The persisted FunctionCatalogEntry object.
        """
        checksum = get_file_checksum(impl_file_path)
        function_entry = self._function_service.insert_entry(name, impl_file_path, type, checksum, function_io_list, function_metadata_list)
        return function_entry

    def get_function_catalog_entry_by_name(self, name: str) -> FunctionCatalogEntry:
        """
        Get the function information based on name.

        Arguments:
             name (str): name of the function

        Returns:
            FunctionCatalogEntry object
        """
        return self._function_service.get_entry_by_name(name)

    def delete_function_catalog_entry_by_name(self, function_name: str) -> bool:
        return self._function_service.delete_entry_by_name(function_name)

    def get_all_function_catalog_entries(self):
        return self._function_service.get_all_entries()
    'function cost catalog services'

    def upsert_function_cost_catalog_entry(self, function_id: int, name: str, cost: int) -> FunctionCostCatalogEntry:
        """Upserts function cost catalog entry.

        Arguments:
            function_id(int): unique function id
            name(str): the name of the function
            cost(int): cost of this function

        Returns:
            The persisted FunctionCostCatalogEntry object.
        """
        self._function_cost_catalog_service.upsert_entry(function_id, name, cost)

    def get_function_cost_catalog_entry(self, name: str):
        return self._function_cost_catalog_service.get_entry_by_name(name)
    'FunctionIO services'

    def get_function_io_catalog_input_entries(self, function_obj: FunctionCatalogEntry) -> List[FunctionIOCatalogEntry]:
        return self._function_io_service.get_input_entries_by_function_id(function_obj.row_id)

    def get_function_io_catalog_output_entries(self, function_obj: FunctionCatalogEntry) -> List[FunctionIOCatalogEntry]:
        return self._function_io_service.get_output_entries_by_function_id(function_obj.row_id)
    ' Index related services. '

    def insert_index_catalog_entry(self, name: str, save_file_path: str, vector_store_type: VectorStoreType, feat_column: ColumnCatalogEntry, function_signature: str, index_def: str) -> IndexCatalogEntry:
        index_catalog_entry = self._index_service.insert_entry(name, save_file_path, vector_store_type, feat_column, function_signature, index_def)
        return index_catalog_entry

    def get_index_catalog_entry_by_name(self, name: str) -> IndexCatalogEntry:
        return self._index_service.get_entry_by_name(name)

    def get_index_catalog_entry_by_column_and_function_signature(self, column: ColumnCatalogEntry, function_signature: str):
        return self._index_service.get_entry_by_column_and_function_signature(column, function_signature)

    def drop_index_catalog_entry(self, index_name: str) -> bool:
        return self._index_service.delete_entry_by_name(index_name)

    def get_all_index_catalog_entries(self):
        return self._index_service.get_all_entries()
    ' Function Cache related'

    def insert_function_cache_catalog_entry(self, func_expr: FunctionExpression):
        cache_dir = self.get_configuration_catalog_value('cache_dir')
        entry = construct_function_cache_catalog_entry(func_expr, cache_dir=cache_dir)
        return self._function_cache_service.insert_entry(entry)

    def get_function_cache_catalog_entry_by_name(self, name: str) -> FunctionCacheCatalogEntry:
        return self._function_cache_service.get_entry_by_name(name)

    def drop_function_cache_catalog_entry(self, entry: FunctionCacheCatalogEntry) -> bool:
        if entry:
            shutil.rmtree(entry.cache_path)
        return self._function_cache_service.delete_entry(entry)
    ' function Metadata Catalog'

    def get_function_metadata_entries_by_function_name(self, function_name: str) -> List[FunctionMetadataCatalogEntry]:
        """
        Get the function metadata information for the provided function.

        Arguments:
             function_name (str): name of the function

        Returns:
            FunctionMetadataCatalogEntry objects
        """
        function_entry = self.get_function_catalog_entry_by_name(function_name)
        if function_entry:
            entries = self._function_metadata_service.get_entries_by_function_id(function_entry.row_id)
            return entries
        else:
            return []
    ' Utils '

    def create_and_insert_table_catalog_entry(self, table_info: TableInfo, columns: List[ColumnDefinition], identifier_column: str=None, table_type: TableType=TableType.STRUCTURED_DATA) -> TableCatalogEntry:
        """Create a valid table catalog tuple and insert into the table

        Args:
            table_info (TableInfo): table info object
            columns (List[ColumnDefinition]): columns definitions of the table
            identifier_column (str, optional): Specify unique columns. Defaults to None.
            table_type (TableType, optional): table type. Defaults to TableType.STRUCTURED_DATA.

        Returns:
            TableCatalogEntry: entry that has been inserted into the table catalog
        """
        table_name = table_info.table_name
        column_catalog_entries = xform_column_definitions_to_catalog_entries(columns)
        dataset_location = self.get_configuration_catalog_value('datasets_dir')
        file_url = str(generate_file_path(dataset_location, table_name))
        table_catalog_entry = self.insert_table_catalog_entry(table_name, file_url, column_catalog_entries, identifier_column=identifier_column, table_type=table_type)
        return table_catalog_entry

    def create_and_insert_multimedia_table_catalog_entry(self, name: str, format_type: FileFormatType) -> TableCatalogEntry:
        """Create a table catalog entry for the multimedia table.
        Depending on the type of multimedia, the appropriate "create catalog entry" command is called.

        Args:
            name (str):  name of the table catalog entry
            format_type (FileFormatType): media type

        Raises:
            CatalogError: if format_type is not supported

        Returns:
            TableCatalogEntry: newly inserted table catalog entry
        """
        assert format_type in [FileFormatType.VIDEO, FileFormatType.IMAGE, FileFormatType.DOCUMENT, FileFormatType.PDF], f'Format Type {format_type} is not supported'
        if format_type is FileFormatType.VIDEO:
            columns = get_video_table_column_definitions()
            table_type = TableType.VIDEO_DATA
        elif format_type is FileFormatType.IMAGE:
            columns = get_image_table_column_definitions()
            table_type = TableType.IMAGE_DATA
        elif format_type is FileFormatType.DOCUMENT:
            columns = get_document_table_column_definitions()
            table_type = TableType.DOCUMENT_DATA
        elif format_type is FileFormatType.PDF:
            columns = get_pdf_table_column_definitions()
            table_type = TableType.PDF_DATA
        return self.create_and_insert_table_catalog_entry(TableInfo(name), columns, table_type=table_type)

    def get_multimedia_metadata_table_catalog_entry(self, input_table: TableCatalogEntry) -> TableCatalogEntry:
        """Get table catalog entry for multimedia metadata table.
        Raise if it does not exists
        Args:
            input_table (TableCatalogEntryEntryEntryEntry): input media table

        Returns:
            TableCatalogEntry: metainfo table entry which is maintained by the system
        """
        media_metadata_name = Path(input_table.file_url).stem
        obj = self.get_table_catalog_entry(media_metadata_name)
        assert obj is not None, f'Table with name {media_metadata_name} does not exist in catalog'
        return obj

    def create_and_insert_multimedia_metadata_table_catalog_entry(self, input_table: TableCatalogEntry) -> TableCatalogEntry:
        """Create and insert table catalog entry for multimedia metadata table.
         This table is used to store all media filenames and related information. In
         order to prevent direct access or modification by users, it should be
         designated as a SYSTEM_STRUCTURED_DATA type.
         **Note**: this table is managed by the storage engine, so it should not be
         called elsewhere.
        Args:
            input_table (TableCatalogEntry): input video table

        Returns:
            TableCatalogEntry: metainfo table entry which is maintained by the system
        """
        media_metadata_name = Path(input_table.file_url).stem
        obj = self.get_table_catalog_entry(media_metadata_name)
        assert obj is None, 'Table with name {media_metadata_name} already exists'
        columns = [ColumnDefinition('file_url', ColumnType.TEXT, None, None)]
        obj = self.create_and_insert_table_catalog_entry(TableInfo(media_metadata_name), columns, identifier_column=columns[0].name, table_type=TableType.SYSTEM_STRUCTURED_DATA)
        return obj
    'Configuration catalog services'

    def upsert_configuration_catalog_entry(self, key: str, value: any):
        """Upserts configuration catalog entry"

        Args:
            key: key name
            value: value name
        """
        self._config_catalog_service.upsert_entry(key, value)

    def get_configuration_catalog_value(self, key: str, default: Any=None) -> Any:
        """
        Returns the value entry for the given key
        Arguments:
            key (str): key name

        Returns:
            ConfigurationCatalogEntry
        """
        table_entry = self._config_catalog_service.get_entry_by_name(key)
        if table_entry:
            return table_entry.value
        return default

    def get_all_configuration_catalog_entries(self) -> List:
        return self._config_catalog_service.get_all_entries()

def check_native_table_exists(self, table_name: str, database_name: str):
    """
        Validate the database is valid and the requested table in database is
        also valid.
        """
    db_catalog_entry = self.get_database_catalog_entry(database_name)
    if db_catalog_entry is None:
        return False
    with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
        resp = handler.get_tables()
        if resp.error is not None:
            raise Exception(resp.error)
        table_df = resp.data
        if table_name not in table_df['table_name'].values:
            return False
    return True

@contextmanager
def get_database_handler(engine: str, **kwargs):
    handler = _get_database_handler(engine, **kwargs)
    try:
        resp = handler.connect()
        if not resp.status:
            raise ExecutorError(f'Cannot establish connection due to {resp.error}')
        yield handler
    finally:
        handler.disconnect()

class ClickHouseHandler(DBHandler):

    def __init__(self, name: str, **kwargs):
        """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
        super().__init__(name)
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.database = kwargs.get('database')
        self.protocol = kwargs.get('protocol')
        protocols_map = {'native': 'clickhouse+native', 'http': 'clickhouse+http', 'https': 'clickhouse+https'}
        if self.protocol in protocols_map:
            self.protocol = protocols_map[self.protocol]

    def connect(self):
        """
        Set up the connection required by the handler.
        Returns:
            DBHandlerStatus
        """
        try:
            protocol = self.protocol
            host = self.host
            port = self.port
            user = self.user
            password = self.password
            database = self.database
            url = f'{protocol}://{user}:{password}@{host}:{port}/{database}'
            if self.protocol == 'clickhouse+https':
                url = url + '?protocol=https'
            engine = create_engine(url)
            self.connection = engine.raw_connection()
            return DBHandlerStatus(status=True)
        except Exception as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        Close any existing connections.
        """
        if self.connection:
            self.disconnect()

    def check_connection(self) -> DBHandlerStatus:
        """
        Check connection to the handler.
        Returns:
            DBHandlerStatus
        """
        if self.connection:
            return DBHandlerStatus(status=True)
        else:
            return DBHandlerStatus(status=False, error='Not connected to the database.')

    def get_tables(self) -> DBHandlerResponse:
        """
        Return the list of tables in the database.
        Returns:
            DBHandlerResponse
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f'SHOW TABLES FROM {self.connection_data['database']}'
            tables_df = pd.read_sql_query(query, self.connection)
            return DBHandlerResponse(data=tables_df)
        except Exception as e:
            return DBHandlerResponse(data=None, error=str(e))

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        """
        Returns the list of columns for the given table.
        Args:
            table_name (str): name of the table whose columns are to be retrieved.
        Returns:
            DBHandlerResponse
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f'DESCRIBE {table_name}'
            columns_df = pd.read_sql_query(query, self.connection)
            columns_df['dtype'] = columns_df['dtype'].apply(self._clickhouse_to_python_types)
            return DBHandlerResponse(data=columns_df)
        except Exception as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _fetch_results_as_df(self, cursor):
        try:
            res = cursor.fetchall()
            if not res:
                return pd.DataFrame({'status': ['success']})
            res_df = pd.DataFrame(res, columns=[desc[0] for desc in cursor.description])
            return res_df
        except Exception as e:
            if str(e) == 'no results to fetch':
                return pd.DataFrame({'status': ['success']})
            raise e

    def execute_native_query(self, query_string: str) -> DBHandlerResponse:
        """
        Executes the native query on the database.
        Args:
            query_string (str): query in native format
        Returns:
            DBHandlerResponse
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            cursor = self.connection.cursor()
            cursor.execute(query_string)
            return DBHandlerResponse(data=self._fetch_results_as_df(cursor))
        except Exception as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _clickhouse_to_python_types(self, clickhouse_type: str):
        mapping = {'char': str, 'varchar': str, 'text': str, 'boolean': bool, 'integer': int, 'int': int, 'float': float, 'double': float}
        if clickhouse_type in mapping:
            return mapping[clickhouse_type]
        else:
            raise Exception(f'Unsupported column {clickhouse_type} encountered in the clickhouse table. Please raise a feature request!')

def disconnect(self):
    """
        Close any existing connections.
        """
    if self.connection:
        self.disconnect()

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

def as_df(self):
    if self.error is not None:
        raise ExecutorError(self.error)
    if self.batch is None:
        raise ExecutorError('Empty batch')
    return self.batch.frames

