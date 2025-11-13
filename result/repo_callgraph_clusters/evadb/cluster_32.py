# Cluster 32

class GenericUtilsTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_string_matching_case_insensitive(self):
        """
        A simple test for string_matching_case_insensitive in generic_utils
        used by statement_binder
        """
        test_string_exact_match = string_comparison_case_insensitive('HuggingFace', 'HuggingFace')
        test_string_case_insensitive_match = string_comparison_case_insensitive('HuggingFace', 'hugGingFaCe')
        test_string_no_match = string_comparison_case_insensitive('HuggingFace', 'HuggingFae')
        test_one_string_null = string_comparison_case_insensitive(None, 'HuggingFace')
        test_both_strings_null = string_comparison_case_insensitive(None, None)
        self.assertTrue(test_string_exact_match)
        self.assertTrue(test_string_case_insensitive_match)
        self.assertFalse(test_string_no_match)
        self.assertFalse(test_one_string_null)
        self.assertFalse(test_both_strings_null)

def test_string_matching_case_insensitive(self):
    """
        A simple test for string_matching_case_insensitive in generic_utils
        used by statement_binder
        """
    test_string_exact_match = string_comparison_case_insensitive('HuggingFace', 'HuggingFace')
    test_string_case_insensitive_match = string_comparison_case_insensitive('HuggingFace', 'hugGingFaCe')
    test_string_no_match = string_comparison_case_insensitive('HuggingFace', 'HuggingFae')
    test_one_string_null = string_comparison_case_insensitive(None, 'HuggingFace')
    test_both_strings_null = string_comparison_case_insensitive(None, None)
    self.assertTrue(test_string_exact_match)
    self.assertTrue(test_string_case_insensitive_match)
    self.assertFalse(test_string_no_match)
    self.assertFalse(test_one_string_null)
    self.assertFalse(test_both_strings_null)

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

class CreateFunctionExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: CreateFunctionPlan):
        super().__init__(db, node)
        self.function_dir = Path(EvaDB_INSTALLATION_DIR) / 'functions'

    def handle_huggingface_function(self):
        """Handle HuggingFace functions

        HuggingFace functions are special functions that are not loaded from a file.
        So we do not need to call the setup method on them like we do for other functions.
        """
        try_to_import_torch()
        impl_path = f'{self.function_dir}/abstract/hf_abstract_function.py'
        io_list = gen_hf_io_catalog_entries(self.node.name, self.node.metadata)
        return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata)

    def handle_ludwig_function(self):
        """Handle ludwig functions

        Use Ludwig's auto_train engine to train/tune models.
        """
        try_to_import_ludwig()
        from ludwig.automl import auto_train
        assert len(self.children) == 1, 'Create ludwig function expects 1 child, finds {}.'.format(len(self.children))
        aggregated_batch_list = []
        child = self.children[0]
        for batch in child.exec():
            aggregated_batch_list.append(batch)
        aggregated_batch = Batch.concat(aggregated_batch_list, copy=False)
        aggregated_batch.drop_column_alias()
        arg_map = {arg.key: arg.value for arg in self.node.metadata}
        start_time = int(time.time())
        auto_train_results = auto_train(dataset=aggregated_batch.frames, target=arg_map['predict'], tune_for_memory=arg_map.get('tune_for_memory', False), time_limit_s=arg_map.get('time_limit', DEFAULT_TRAIN_TIME_LIMIT), output_directory=self.db.catalog().get_configuration_catalog_value('tmp_dir'))
        train_time = int(time.time()) - start_time
        model_path = os.path.join(self.db.catalog().get_configuration_catalog_value('model_dir'), self.node.name)
        auto_train_results.best_model.save(model_path)
        best_score = auto_train_results.experiment_analysis.best_result['metric_score']
        self.node.metadata.append(FunctionMetadataCatalogEntry('model_path', model_path))
        impl_path = Path(f'{self.function_dir}/ludwig.py').absolute().as_posix()
        io_list = self._resolve_function_io(None)
        return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata, best_score, train_time)

    def handle_sklearn_function(self):
        """Handle sklearn functions

        Use Sklearn's regression to train models.
        """
        try_to_import_flaml_automl()
        assert len(self.children) == 1, 'Create sklearn function expects 1 child, finds {}.'.format(len(self.children))
        aggregated_batch_list = []
        child = self.children[0]
        for batch in child.exec():
            aggregated_batch_list.append(batch)
        aggregated_batch = Batch.concat(aggregated_batch_list, copy=False)
        aggregated_batch.drop_column_alias()
        arg_map = {arg.key: arg.value for arg in self.node.metadata}
        from flaml import AutoML
        model = AutoML()
        sklearn_model = arg_map.get('model', DEFAULT_SKLEARN_TRAIN_MODEL)
        if sklearn_model not in SKLEARN_SUPPORTED_MODELS:
            raise ValueError(f'Sklearn Model {sklearn_model} provided as input is not supported.')
        settings = {'time_budget': arg_map.get('time_limit', DEFAULT_TRAIN_TIME_LIMIT), 'metric': arg_map.get('metric', DEFAULT_TRAIN_REGRESSION_METRIC), 'estimator_list': [sklearn_model], 'task': arg_map.get('task', DEFAULT_XGBOOST_TASK)}
        start_time = int(time.time())
        model.fit(dataframe=aggregated_batch.frames, label=arg_map['predict'], **settings)
        train_time = int(time.time()) - start_time
        score = model.best_loss
        model_path = os.path.join(self.db.catalog().get_configuration_catalog_value('model_dir'), self.node.name)
        pickle.dump(model, open(model_path, 'wb'))
        self.node.metadata.append(FunctionMetadataCatalogEntry('model_path', model_path))
        self.node.metadata.append(FunctionMetadataCatalogEntry('predict_col', arg_map['predict']))
        impl_path = Path(f'{self.function_dir}/sklearn.py').absolute().as_posix()
        io_list = self._resolve_function_io(None)
        return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata, score, train_time)

    def convert_to_numeric(self, x):
        x = re.sub('[^0-9.,]', '', str(x))
        locale.setlocale(locale.LC_ALL, '')
        x = float(locale.atof(x))
        if x.is_integer():
            return int(x)
        else:
            return x

    def handle_xgboost_function(self):
        """Handle xgboost functions

        We use the Flaml AutoML model for training xgboost models.
        """
        try_to_import_flaml_automl()
        assert len(self.children) == 1, 'Create sklearn function expects 1 child, finds {}.'.format(len(self.children))
        aggregated_batch_list = []
        child = self.children[0]
        for batch in child.exec():
            aggregated_batch_list.append(batch)
        aggregated_batch = Batch.concat(aggregated_batch_list, copy=False)
        aggregated_batch.drop_column_alias()
        arg_map = {arg.key: arg.value for arg in self.node.metadata}
        from flaml import AutoML
        model = AutoML()
        settings = {'time_budget': arg_map.get('time_limit', DEFAULT_TRAIN_TIME_LIMIT), 'metric': arg_map.get('metric', DEFAULT_TRAIN_REGRESSION_METRIC), 'estimator_list': ['xgboost'], 'task': arg_map.get('task', DEFAULT_XGBOOST_TASK)}
        start_time = int(time.time())
        model.fit(dataframe=aggregated_batch.frames, label=arg_map['predict'], **settings)
        train_time = int(time.time()) - start_time
        model_path = os.path.join(self.db.catalog().get_configuration_catalog_value('model_dir'), self.node.name)
        pickle.dump(model, open(model_path, 'wb'))
        self.node.metadata.append(FunctionMetadataCatalogEntry('model_path', model_path))
        self.node.metadata.append(FunctionMetadataCatalogEntry('predict_col', arg_map['predict']))
        impl_path = Path(f'{self.function_dir}/xgboost.py').absolute().as_posix()
        io_list = self._resolve_function_io(None)
        best_score = model.best_loss
        return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata, best_score, train_time)

    def handle_ultralytics_function(self):
        """Handle Ultralytics functions"""
        try_to_import_ultralytics()
        impl_path = Path(f'{self.function_dir}/yolo_object_detector.py').absolute().as_posix()
        function = self._try_initializing_function(impl_path, function_args=get_metadata_properties(self.node))
        io_list = self._resolve_function_io(function)
        return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata)

    def handle_forecasting_function(self):
        """Handle forecasting functions"""
        aggregated_batch_list = []
        child = self.children[0]
        for batch in child.exec():
            aggregated_batch_list.append(batch)
        aggregated_batch = Batch.concat(aggregated_batch_list, copy=False)
        aggregated_batch.drop_column_alias()
        arg_map = {arg.key: arg.value for arg in self.node.metadata}
        if not self.node.impl_path:
            impl_path = Path(f'{self.function_dir}/forecast.py').absolute().as_posix()
        else:
            impl_path = self.node.impl_path.absolute().as_posix()
        library = 'statsforecast'
        supported_libraries = ['statsforecast', 'neuralforecast']
        if 'horizon' not in arg_map.keys():
            raise ValueError('Horizon must be provided while creating function of type FORECASTING')
        try:
            horizon = int(arg_map['horizon'])
        except Exception as e:
            err_msg = f'{str(e)}. HORIZON must be integral.'
            logger.error(err_msg)
            raise FunctionIODefinitionError(err_msg)
        if 'library' in arg_map.keys():
            try:
                assert arg_map['library'].lower() in supported_libraries
            except Exception:
                err_msg = 'EvaDB currently supports ' + str(supported_libraries) + ' only.'
                logger.error(err_msg)
                raise FunctionIODefinitionError(err_msg)
            library = arg_map['library'].lower()
        '\n        The following rename is needed for statsforecast/neuralforecast, which requires the column name to be the following:\n        - The unique_id (string, int or category) represents an identifier for the series.\n        - The ds (datestamp) column should be of a format expected by Pandas, ideally YYYY-MM-DD for a date or YYYY-MM-DD HH:MM:SS for a timestamp.\n        - The y (numeric) represents the measurement we wish to forecast.\n        For reference: https://nixtla.github.io/statsforecast/docs/getting-started/getting_started_short.html\n        '
        aggregated_batch.rename(columns={arg_map['predict']: 'y'})
        if 'time' in arg_map.keys():
            aggregated_batch.rename(columns={arg_map['time']: 'ds'})
        if 'id' in arg_map.keys():
            aggregated_batch.rename(columns={arg_map['id']: 'unique_id'})
        if 'conf' in arg_map.keys():
            try:
                conf = round(arg_map['conf'])
            except Exception:
                err_msg = 'Confidence must be a number.'
                logger.error(err_msg)
                raise FunctionIODefinitionError(err_msg)
        else:
            conf = 90
        if conf > 100:
            err_msg = 'Confidence must <= 100.'
            logger.error(err_msg)
            raise FunctionIODefinitionError(err_msg)
        data = aggregated_batch.frames
        if 'unique_id' not in list(data.columns):
            data['unique_id'] = [1 for x in range(len(data))]
        if 'ds' not in list(data.columns):
            data['ds'] = [x + 1 for x in range(len(data))]
        '\n            Set or infer data frequency\n        '
        if 'frequency' not in arg_map.keys() or arg_map['frequency'] == 'auto':
            arg_map['frequency'] = pd.infer_freq(data['ds'])
        frequency = arg_map['frequency']
        if frequency is None:
            raise RuntimeError(f'Can not infer the frequency for {self.node.name}. Please explicitly set it.')
        season_dict = {'H': 24, 'M': 12, 'Q': 4, 'SM': 24, 'BM': 12, 'BMS': 12, 'BQ': 4, 'BH': 24}
        new_freq = frequency.split('-')[0] if '-' in frequency else frequency
        season_length = season_dict[new_freq] if new_freq in season_dict else 1
        '\n            Neuralforecast implementation\n        '
        if library == 'neuralforecast':
            try_to_import_neuralforecast()
            from neuralforecast import NeuralForecast
            from neuralforecast.auto import AutoDeepAR, AutoFEDformer, AutoInformer, AutoNBEATS, AutoNHITS, AutoPatchTST, AutoTFT
            from neuralforecast.losses.pytorch import MQLoss
            from neuralforecast.models import NBEATS, NHITS, TFT, DeepAR, FEDformer, Informer, PatchTST
            model_dict = {'AutoNBEATS': AutoNBEATS, 'AutoNHITS': AutoNHITS, 'NBEATS': NBEATS, 'NHITS': NHITS, 'PatchTST': PatchTST, 'AutoPatchTST': AutoPatchTST, 'DeepAR': DeepAR, 'AutoDeepAR': AutoDeepAR, 'FEDformer': FEDformer, 'AutoFEDformer': AutoFEDformer, 'Informer': Informer, 'AutoInformer': AutoInformer, 'TFT': TFT, 'AutoTFT': AutoTFT}
            if 'model' not in arg_map.keys():
                arg_map['model'] = 'TFT'
            if 'auto' not in arg_map.keys() or (arg_map['auto'].lower()[0] == 't' and 'auto' not in arg_map['model'].lower()):
                arg_map['model'] = 'Auto' + arg_map['model']
            try:
                model_here = model_dict[arg_map['model']]
            except Exception:
                err_msg = 'Supported models: ' + str(model_dict.keys())
                logger.error(err_msg)
                raise FunctionIODefinitionError(err_msg)
            model_args = {}
            if 'auto' not in arg_map['model'].lower():
                model_args['input_size'] = 2 * horizon
                model_args['early_stop_patience_steps'] = 20
            else:
                model_args_config = {'input_size': 2 * horizon, 'early_stop_patience_steps': 20}
            if len(data.columns) >= 4:
                exogenous_columns = [x for x in list(data.columns) if x not in ['ds', 'y', 'unique_id']]
                if 'auto' not in arg_map['model'].lower():
                    model_args['hist_exog_list'] = exogenous_columns
                else:
                    model_args_config['hist_exog_list'] = exogenous_columns
            if 'auto' in arg_map['model'].lower():

                def get_optuna_config(trial):
                    return model_args_config
                model_args['config'] = get_optuna_config
                model_args['backend'] = 'optuna'
            model_args['h'] = horizon
            model_args['loss'] = MQLoss(level=[conf])
            model = NeuralForecast([model_here(**model_args)], freq=new_freq)
        else:
            if 'auto' in arg_map.keys() and arg_map['auto'].lower()[0] != 't':
                raise RuntimeError('Statsforecast implementation only supports automatic hyperparameter optimization. Please set AUTO to true.')
            try_to_import_statsforecast()
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA, AutoCES, AutoETS, AutoTheta
            model_dict = {'AutoARIMA': AutoARIMA, 'AutoCES': AutoCES, 'AutoETS': AutoETS, 'AutoTheta': AutoTheta}
            if 'model' not in arg_map.keys():
                arg_map['model'] = 'ARIMA'
            if 'auto' not in arg_map['model'].lower():
                arg_map['model'] = 'Auto' + arg_map['model']
            try:
                model_here = model_dict[arg_map['model']]
            except Exception:
                err_msg = 'Supported models: ' + str(model_dict.keys())
                logger.error(err_msg)
                raise FunctionIODefinitionError(err_msg)
            model = StatsForecast([model_here(season_length=season_length)], freq=new_freq)
        data['ds'] = pd.to_datetime(data['ds'])
        model_save_dir_name = library + '_' + arg_map['model'] + '_' + new_freq if 'statsforecast' in library else library + '_' + str(conf) + '_' + arg_map['model'] + '_' + new_freq
        if len(data.columns) >= 4 and library == 'neuralforecast':
            model_save_dir_name += '_exogenous_' + str(sorted(exogenous_columns))
        model_dir = os.path.join(self.db.catalog().get_configuration_catalog_value('model_dir'), 'tsforecasting', model_save_dir_name, str(hashlib.sha256(data.to_string().encode()).hexdigest()))
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        model_save_name = 'horizon' + str(horizon) + '.pkl'
        model_path = os.path.join(model_dir, model_save_name)
        existing_model_files = sorted(os.listdir(model_dir), key=lambda x: int(x.split('horizon')[1].split('.pkl')[0]))
        existing_model_files = [x for x in existing_model_files if int(x.split('horizon')[1].split('.pkl')[0]) >= horizon]
        if len(existing_model_files) == 0:
            logger.info('Training, please wait...')
            for column in data.columns:
                if column != 'ds' and column != 'unique_id':
                    data[column] = data.apply(lambda x: self.convert_to_numeric(x[column]), axis=1)
            rmses = []
            if library == 'neuralforecast':
                cuda_devices_here = '0'
                if 'CUDA_VISIBLE_DEVICES' in os.environ:
                    cuda_devices_here = os.environ['CUDA_VISIBLE_DEVICES'].split(',')[0]
                with set_env(CUDA_VISIBLE_DEVICES=cuda_devices_here):
                    model.fit(df=data, val_size=horizon)
                    model.save(model_path, overwrite=True)
                    if 'metrics' in arg_map and arg_map['metrics'].lower()[0] == 't':
                        crossvalidation_df = model.cross_validation(df=data, val_size=horizon)
                        for uid in crossvalidation_df.unique_id.unique():
                            crossvalidation_df_here = crossvalidation_df[crossvalidation_df.unique_id == uid]
                            rmses.append(root_mean_squared_error(crossvalidation_df_here.y, crossvalidation_df_here[arg_map['model'] + '-median']) / np.mean(crossvalidation_df_here.y))
                            mean_rmse = np.mean(rmses)
                            with open(model_path + '_rmse', 'w') as f:
                                f.write(str(mean_rmse) + '\n')
            else:
                for col in data['unique_id'].unique():
                    if len(data[data['unique_id'] == col]) == 1:
                        data = data._append([data[data['unique_id'] == col]], ignore_index=True)
                model.fit(df=data[['ds', 'y', 'unique_id']])
                hypers = ''
                if 'arima' in arg_map['model'].lower():
                    from statsforecast.arima import arima_string
                    hypers += arima_string(model.fitted_[0, 0].model_)
                f = open(model_path, 'wb')
                pickle.dump(model, f)
                f.close()
                if 'metrics' not in arg_map or arg_map['metrics'].lower()[0] == 't':
                    crossvalidation_df = model.cross_validation(df=data[['ds', 'y', 'unique_id']], h=horizon, step_size=24, n_windows=1).reset_index()
                    for uid in crossvalidation_df.unique_id.unique():
                        crossvalidation_df_here = crossvalidation_df[crossvalidation_df.unique_id == uid]
                        rmses.append(root_mean_squared_error(crossvalidation_df_here.y, crossvalidation_df_here[arg_map['model']]) / np.mean(crossvalidation_df_here.y))
                    mean_rmse = np.mean(rmses)
                    with open(model_path + '_rmse', 'w') as f:
                        f.write(str(mean_rmse) + '\n')
                        f.write(hypers + '\n')
        elif not Path(model_path).exists():
            model_path = os.path.join(model_dir, existing_model_files[-1])
        io_list = self._resolve_function_io(None)
        data['ds'] = data.ds.astype(str)
        metadata_here = [FunctionMetadataCatalogEntry('model_name', arg_map['model']), FunctionMetadataCatalogEntry('model_path', model_path), FunctionMetadataCatalogEntry('predict_column_rename', arg_map.get('predict', 'y')), FunctionMetadataCatalogEntry('time_column_rename', arg_map.get('time', 'ds')), FunctionMetadataCatalogEntry('id_column_rename', arg_map.get('id', 'unique_id')), FunctionMetadataCatalogEntry('horizon', horizon), FunctionMetadataCatalogEntry('library', library), FunctionMetadataCatalogEntry('conf', conf)]
        return (self.node.name, impl_path, self.node.function_type, io_list, metadata_here)

    def handle_generic_function(self):
        """Handle generic functions

        Generic functions are loaded from a file. We check for inputs passed by the user during CREATE or try to load io from decorators.
        """
        impl_path = self.node.impl_path.absolute().as_posix()
        function = self._try_initializing_function(impl_path)
        io_list = self._resolve_function_io(function)
        return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata)

    def exec(self, *args, **kwargs):
        """Create function executor

        Calls the catalog to insert a function catalog entry.
        """
        assert (self.node.if_not_exists and self.node.or_replace) is False, 'OR REPLACE and IF NOT EXISTS can not be both set for CREATE FUNCTION.'
        overwrite = False
        best_score = False
        train_time = False
        if self.catalog().get_function_catalog_entry_by_name(self.node.name):
            if self.node.if_not_exists:
                msg = f'Function {self.node.name} already exists, nothing added.'
                yield Batch(pd.DataFrame([msg]))
                return
            elif self.node.or_replace:
                from evadb.executor.drop_object_executor import DropObjectExecutor
                drop_executor = DropObjectExecutor(self.db, None)
                try:
                    drop_executor._handle_drop_function(self.node.name, if_exists=False)
                except RuntimeError:
                    pass
                else:
                    overwrite = True
            else:
                msg = f'Function {self.node.name} already exists.'
                logger.error(msg)
                raise RuntimeError(msg)
        if string_comparison_case_insensitive(self.node.function_type, 'HuggingFace'):
            name, impl_path, function_type, io_list, metadata = self.handle_huggingface_function()
        elif string_comparison_case_insensitive(self.node.function_type, 'ultralytics'):
            name, impl_path, function_type, io_list, metadata = self.handle_ultralytics_function()
        elif string_comparison_case_insensitive(self.node.function_type, 'Ludwig'):
            name, impl_path, function_type, io_list, metadata, best_score, train_time = self.handle_ludwig_function()
        elif string_comparison_case_insensitive(self.node.function_type, 'Sklearn'):
            name, impl_path, function_type, io_list, metadata, best_score, train_time = self.handle_sklearn_function()
        elif string_comparison_case_insensitive(self.node.function_type, 'XGBoost'):
            name, impl_path, function_type, io_list, metadata, best_score, train_time = self.handle_xgboost_function()
        elif string_comparison_case_insensitive(self.node.function_type, 'Forecasting'):
            name, impl_path, function_type, io_list, metadata = self.handle_forecasting_function()
        else:
            name, impl_path, function_type, io_list, metadata = self.handle_generic_function()
        self.catalog().insert_function_catalog_entry(name, impl_path, function_type, io_list, metadata)
        if overwrite:
            msg = f'Function {self.node.name} overwritten.'
        else:
            msg = f'Function {self.node.name} added to the database.'
        if best_score and train_time:
            yield Batch(pd.DataFrame([msg, 'Validation Score: ' + str(best_score), 'Training time: ' + str(train_time) + ' secs.']))
        else:
            yield Batch(pd.DataFrame([msg]))

    def _try_initializing_function(self, impl_path: str, function_args: Dict={}) -> FunctionCatalogEntry:
        """Attempts to initialize function given the implementation file path and arguments.

        Args:
            impl_path (str): The file path of the function implementation file.
            function_args (Dict, optional): Dictionary of arguments to pass to the function. Defaults to {}.

        Returns:
            FunctionCatalogEntry: A FunctionCatalogEntry object that represents the initialized function.

        Raises:
            RuntimeError: If an error occurs while initializing the function.
        """
        try:
            function = load_function_class_from_file(impl_path, self.node.name)
            function(**function_args)
        except Exception as e:
            err_msg = f'Error creating function {self.node.name}: {str(e)}'
            raise RuntimeError(err_msg)
        return function

    def _resolve_function_io(self, function: FunctionCatalogEntry) -> List[FunctionIOCatalogEntry]:
        """Private method that resolves the input/output definitions for a given function.
        It first searches for the input/outputs in the CREATE statement. If not found, it resolves them using decorators. If not found there as well, it raises an error.

        Args:
            function (FunctionCatalogEntry): The function for which to resolve input and output definitions.

        Returns:
            A List of FunctionIOCatalogEntry objects that represent the resolved input and
            output definitions for the function.

        Raises:
            RuntimeError: If an error occurs while resolving the function input/output
            definitions.
        """
        io_list = []
        try:
            if self.node.inputs:
                io_list.extend(self.node.inputs)
            else:
                io_list.extend(load_io_from_function_decorators(function, is_input=True))
            if self.node.outputs:
                io_list.extend(self.node.outputs)
            else:
                io_list.extend(load_io_from_function_decorators(function, is_input=False))
        except FunctionIODefinitionError as e:
            err_msg = f'Error creating function, input/output definition incorrect: {str(e)}'
            logger.error(err_msg)
            raise RuntimeError(err_msg)
        return io_list

def exec(self, *args, **kwargs):
    """Create function executor

        Calls the catalog to insert a function catalog entry.
        """
    assert (self.node.if_not_exists and self.node.or_replace) is False, 'OR REPLACE and IF NOT EXISTS can not be both set for CREATE FUNCTION.'
    overwrite = False
    best_score = False
    train_time = False
    if self.catalog().get_function_catalog_entry_by_name(self.node.name):
        if self.node.if_not_exists:
            msg = f'Function {self.node.name} already exists, nothing added.'
            yield Batch(pd.DataFrame([msg]))
            return
        elif self.node.or_replace:
            from evadb.executor.drop_object_executor import DropObjectExecutor
            drop_executor = DropObjectExecutor(self.db, None)
            try:
                drop_executor._handle_drop_function(self.node.name, if_exists=False)
            except RuntimeError:
                pass
            else:
                overwrite = True
        else:
            msg = f'Function {self.node.name} already exists.'
            logger.error(msg)
            raise RuntimeError(msg)
    if string_comparison_case_insensitive(self.node.function_type, 'HuggingFace'):
        name, impl_path, function_type, io_list, metadata = self.handle_huggingface_function()
    elif string_comparison_case_insensitive(self.node.function_type, 'ultralytics'):
        name, impl_path, function_type, io_list, metadata = self.handle_ultralytics_function()
    elif string_comparison_case_insensitive(self.node.function_type, 'Ludwig'):
        name, impl_path, function_type, io_list, metadata, best_score, train_time = self.handle_ludwig_function()
    elif string_comparison_case_insensitive(self.node.function_type, 'Sklearn'):
        name, impl_path, function_type, io_list, metadata, best_score, train_time = self.handle_sklearn_function()
    elif string_comparison_case_insensitive(self.node.function_type, 'XGBoost'):
        name, impl_path, function_type, io_list, metadata, best_score, train_time = self.handle_xgboost_function()
    elif string_comparison_case_insensitive(self.node.function_type, 'Forecasting'):
        name, impl_path, function_type, io_list, metadata = self.handle_forecasting_function()
    else:
        name, impl_path, function_type, io_list, metadata = self.handle_generic_function()
    self.catalog().insert_function_catalog_entry(name, impl_path, function_type, io_list, metadata)
    if overwrite:
        msg = f'Function {self.node.name} overwritten.'
    else:
        msg = f'Function {self.node.name} added to the database.'
    if best_score and train_time:
        yield Batch(pd.DataFrame([msg, 'Validation Score: ' + str(best_score), 'Training time: ' + str(train_time) + ' secs.']))
    else:
        yield Batch(pd.DataFrame([msg]))

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

@singledispatchmethod
def bind(self, node):
    raise NotImplementedError(f'Cannot bind {type(node)}')

class Expressions:

    def string_literal(self, tree):
        text = tree.children[0]
        assert text is not None
        return ConstantValueExpression(text[1:-1], ColumnType.TEXT)

    def array_literal(self, tree):
        array_elements = []
        for child in tree.children:
            if isinstance(child, Tree):
                array_element = self.visit(child).value
                array_elements.append(array_element)
        res = ConstantValueExpression(np.array(array_elements), ColumnType.NDARRAY)
        return res

    def boolean_literal(self, tree):
        text = tree.children[0]
        if text == 'TRUE':
            return ConstantValueExpression(True, ColumnType.BOOLEAN)
        return ConstantValueExpression(False, ColumnType.BOOLEAN)

    def constant(self, tree):
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'real_literal':
                    real_literal = self.visit(child)
                    return ConstantValueExpression(real_literal, ColumnType.FLOAT)
                elif child.data == 'decimal_literal':
                    decimal_literal = self.visit(child)
                    return ConstantValueExpression(decimal_literal, ColumnType.INTEGER)
        return self.visit_children(tree)

    def logical_expression(self, tree):
        left = self.visit(tree.children[0])
        op = self.visit(tree.children[1])
        right = self.visit(tree.children[2])
        return LogicalExpression(op, left, right)

    def binary_comparison_predicate(self, tree):
        left = self.visit(tree.children[0])
        op = self.visit(tree.children[1])
        right = self.visit(tree.children[2])
        return ComparisonExpression(op, left, right)

    def nested_expression_atom(self, tree):
        expr = tree.children[0]
        return self.visit(expr)

    def comparison_operator(self, tree):
        op = str(tree.children[0])
        if op == '=':
            return ExpressionType.COMPARE_EQUAL
        elif op == '<':
            return ExpressionType.COMPARE_LESSER
        elif op == '>':
            return ExpressionType.COMPARE_GREATER
        elif op == '>=':
            return ExpressionType.COMPARE_GEQ
        elif op == '<=':
            return ExpressionType.COMPARE_LEQ
        elif op == '!=':
            return ExpressionType.COMPARE_NEQ
        elif op == '@>':
            return ExpressionType.COMPARE_CONTAINS
        elif op == '<@':
            return ExpressionType.COMPARE_IS_CONTAINED
        elif op == 'LIKE':
            return ExpressionType.COMPARE_LIKE

    def logical_operator(self, tree):
        op = str(tree.children[0])
        if string_comparison_case_insensitive(op, 'OR'):
            return ExpressionType.LOGICAL_OR
        elif string_comparison_case_insensitive(op, 'AND'):
            return ExpressionType.LOGICAL_AND
        else:
            raise NotImplementedError('Unsupported logical operator: {}'.format(op))

    def expressions_with_defaults(self, tree):
        expr_list = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'expression_or_default':
                    expression = self.visit(child)
                    expr_list.append(expression)
        return expr_list

    def sample_params(self, tree):
        sample_type = None
        sample_freq = None
        for child in tree.children:
            if child.data == 'sample_clause':
                sample_freq = self.visit(child)
            elif child.data == 'sample_clause_with_type':
                sample_type, sample_freq = self.visit(child)
        return (sample_type, sample_freq)

    def sample_clause(self, tree):
        sample_list = self.visit_children(tree)
        assert len(sample_list) == 2
        return ConstantValueExpression(sample_list[1])

    def sample_clause_with_type(self, tree):
        sample_list = self.visit_children(tree)
        assert len(sample_list) == 3 or len(sample_list) == 2
        if len(sample_list) == 3:
            return (ConstantValueExpression(sample_list[1]), ConstantValueExpression(sample_list[2]))
        else:
            return (ConstantValueExpression(sample_list[1]), ConstantValueExpression(1))

    def chunk_params(self, tree):
        chunk_params = self.visit_children(tree)
        assert len(chunk_params) == 2 or len(chunk_params) == 4
        if len(chunk_params) == 4:
            return {'chunk_size': chunk_params[1], 'chunk_overlap': chunk_params[3]}
        elif len(chunk_params) == 2:
            if chunk_params[0] == 'CHUNK_SIZE':
                return {'chunk_size': chunk_params[1]}
            elif chunk_params[0] == 'CHUNK_OVERLAP':
                return {'chunk_overlap': chunk_params[1]}
            else:
                assert f'incorrect keyword found {chunk_params[0]}'

    def colon_param_dict(self, tree):
        param_dict = {}
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'colon_param':
                    param = self.visit(child)
                    key = param[0].value
                    value = param[1].value
                    param_dict[key] = value
        return param_dict

def logical_operator(self, tree):
    op = str(tree.children[0])
    if string_comparison_case_insensitive(op, 'OR'):
        return ExpressionType.LOGICAL_OR
    elif string_comparison_case_insensitive(op, 'AND'):
        return ExpressionType.LOGICAL_AND
    else:
        raise NotImplementedError('Unsupported logical operator: {}'.format(op))

class DBHandler:
    """
    Base class for handling database operations.

    Args:
        name (str): The name associated with the database handler instance.
    """

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.connection = None

    def connect(self):
        """
        Establishes a connection to the database.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError()

    def disconnect(self):
        """
        Disconnects from the database.

        This method can be overridden in derived classes to perform specific disconnect actions.
        """
        raise NotImplementedError()

    def get_sqlalchmey_uri(self) -> str:
        """
        Return the valid sqlalchemy uri to connect to the database.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError()

    def is_sqlalchmey_compatible(self) -> bool:
        """
        Return  whether the data source is sqlaclchemy compatible

        Returns:
            A True / False boolean value..
        """
        try:
            self.get_sqlalchmey_uri()
        except NotImplementedError:
            return False
        else:
            return True

    def check_connection(self) -> DBHandlerStatus:
        """
        Checks the status of the database connection.

        Returns:
            DBHandlerStatus: An instance of DBHandlerStatus indicating the connection status.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError()

    def get_tables(self) -> DBHandlerResponse:
        """
        Retrieves the list of tables from the database.

        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the list of tables or an error message. Data is in a pandas DataFrame.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError()

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        """
        Retrieves the columns of a specified table from the database.

        Args:
            table_name (str): The name of the table for which to retrieve columns.

        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the columns or an error message. Data is in a pandas DataFrame. It should have the following two columns: name and dtype. The dtype should be a Python dtype and will default to `str`.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError()

    def execute_native_query(self, query_string: str) -> DBHandlerResponse:
        """
        Executes the query through the handler's database engine.

        Args:
            query_string (str): The string representation of the native query.

        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the columns or an error message. Data is in a pandas DataFrame.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
        raise NotImplementedError()

    def select(self, table_name: str) -> DBHandlerResponse:
        """
        Returns a generator that yields the data from the given table, or the data.
        Args:
            table_name (str): name of the table whose data is to be retrieved.
        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the data, data generator, or an error message. Data is in a pandas DataFrame.

        Raises:
            NotImplementedError: The default implementation of this method is for sqlalchemy-supported data source. The data source that does not support sqlalchemy should overwrite this function.
        """
        try:
            uri = self.get_sqlalchmey_uri()
            engine = create_engine(uri)
            metadata = MetaData()
            Session = sessionmaker(bind=engine)
            session = Session()
            table_to_read = Table(table_name, metadata, autoload_with=engine)
            result = session.execute(table_to_read.select()).fetchall()
            session.close()
            return DBHandlerResponse(data=result)
        except Exception as e:
            return DBHandlerResponse(data=None, error=str(e))

def connect(self):
    """
        Establishes a connection to the database.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
    raise NotImplementedError()

def disconnect(self):
    """
        Disconnects from the database.

        This method can be overridden in derived classes to perform specific disconnect actions.
        """
    raise NotImplementedError()

def get_sqlalchmey_uri(self) -> str:
    """
        Return the valid sqlalchemy uri to connect to the database.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
    raise NotImplementedError()

def check_connection(self) -> DBHandlerStatus:
    """
        Checks the status of the database connection.

        Returns:
            DBHandlerStatus: An instance of DBHandlerStatus indicating the connection status.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
    raise NotImplementedError()

def get_tables(self) -> DBHandlerResponse:
    """
        Retrieves the list of tables from the database.

        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the list of tables or an error message. Data is in a pandas DataFrame.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
    raise NotImplementedError()

def get_columns(self, table_name: str) -> DBHandlerResponse:
    """
        Retrieves the columns of a specified table from the database.

        Args:
            table_name (str): The name of the table for which to retrieve columns.

        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the columns or an error message. Data is in a pandas DataFrame. It should have the following two columns: name and dtype. The dtype should be a Python dtype and will default to `str`.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
    raise NotImplementedError()

def execute_native_query(self, query_string: str) -> DBHandlerResponse:
    """
        Executes the query through the handler's database engine.

        Args:
            query_string (str): The string representation of the native query.

        Returns:
            DBHandlerResponse: An instance of DBHandlerResponse containing the columns or an error message. Data is in a pandas DataFrame.

        Raises:
            NotImplementedError: This method should be implemented in derived classes.
        """
    raise NotImplementedError()

class SlackHandler(DBHandler):

    def __init__(self, name: str, **kwargs):
        super().__init__(name)
        self.token = kwargs.get('token')
        self.channel_name = kwargs.get('channel')

    def connect(self):
        try:
            self.client = WebClient(token=self.token)
            return DBHandlerStatus(status=True)
        except Exception as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        TODO: integrate code for disconnecting from slack
        """
        raise NotImplementedError()

    def check_connection(self) -> DBHandlerStatus:
        try:
            self.client.api_test()
        except SlackApiError as e:
            assert e.response['ok'] is False
            return False
        return True

    def get_tables(self) -> DBHandlerResponse:
        if self.client:
            channels = self.client.conversations_list(types='public_channel,private_channel')['channels']
            self.channel_names = [c['name'] for c in channels]
            tables_df = pd.DataFrame(self.channel_names, columns=['table_name'])
            return DBHandlerResponse(data=tables_df)

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        columns = ['ts', 'text', 'message_created_at', 'user', 'channel', 'reactions', 'attachments', 'thread_ts', 'reply_count', 'reply_users_count', 'latest_reply', 'subtype', 'hidden']
        columns_df = pd.DataFrame(columns, columns=['column_name'])
        return DBHandlerResponse(data=columns_df)

    def post_message(self, message) -> DBHandlerResponse:
        try:
            response = self.client.chat_postMessage(channel=self.channel, text=message)
            return DBHandlerResponse(data=response['message']['text'])
        except SlackApiError as e:
            assert e.response['ok'] is False
            assert e.response['error']
            return DBHandlerResponse(data=None, error=e.response['error'])

    def _convert_json_response_to_DataFrame(self, json_response):
        messages = json_response['messages']
        columns = ['text', 'ts', 'user']
        data_df = pd.DataFrame(columns=columns)
        for message in messages:
            if message['text'] and message['ts'] and message['user']:
                data_df.loc[len(data_df.index)] = [message['text'], message['ts'], message['user']]
        return data_df

    def get_messages(self) -> DBHandlerResponse:
        try:
            channels = self.client.conversations_list(types='public_channel,private_channel')['channels']
            channel_ids = {c['name']: c['id'] for c in channels}
            response = self.client.conversations_history(channel=channel_ids[self.channel_name])
            data_df = self._convert_json_response_to_DataFrame(response)
            return data_df
        except SlackApiError as e:
            assert e.response['ok'] is False
            assert e.response['error']
            return DBHandlerResponse(data=None, error=e.response['error'])

    def del_message(self, timestamp) -> DBHandlerResponse:
        try:
            self.client.chat_delete(channel=self.channel, ts=timestamp)
        except SlackApiError as e:
            assert e.response['ok'] is False
            assert e.response['error']
            return DBHandlerResponse(data=None, error=e.response['error'])

    def execute_native_query(self, query_string: str) -> DBHandlerResponse:
        """
        TODO: integrate code for executing query on slack
        """
        raise NotImplementedError()

def disconnect(self):
    """
        TODO: integrate code for disconnecting from slack
        """
    raise NotImplementedError()

def execute_native_query(self, query_string: str) -> DBHandlerResponse:
    """
        TODO: integrate code for executing query on slack
        """
    raise NotImplementedError()

