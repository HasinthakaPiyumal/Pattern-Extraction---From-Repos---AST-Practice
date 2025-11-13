# Cluster 34

class GlossaryTransform(transforms.Transform):
    """
    Make transformations to a document that affect the way it refers
    to glossary entries:

    1. Change parenthesized sense numbers (1), (2) etc. to
       superscripts in glossary entries and cross-references to
       glossary entries.

    2. Record glossary entries that consist only of "See: XREF" so
       that cross-references to them can be reported by
       `warn_indirect_terms` once the build is completed.

    3. Add "term" cross-reference targets for plurals.
    """
    see_only_ids = set()
    xref_ids = defaultdict(list)
    default_priority = 999
    sense_re = re.compile('(.*)\\s+(\\([0-9]+\\))$', re.S)

    def superscript_children(self, target):
        """
        Yield the children of `target` in order, removing
        parenthesized sense numbers like "(1)" and "(2)" from text
        nodes, and adding new superscript nodes as necessary.
        """
        for e in target:
            if not isinstance(e, nodes.Text):
                yield e
                continue
            m = self.sense_re.match(e)
            if not m:
                yield e
                continue
            yield nodes.Text(m.group(1))
            yield nodes.superscript(text=m.group(2))

    def apply(self):
        for target in self.document.traverse(nodes.term):
            target[:] = list(self.superscript_children(target))
        for target in self.document.traverse(addnodes.pending_xref):
            if target['reftype'] == 'term':
                ids = self.xref_ids['term-{}'.format(target['reftarget'])]
                ids.append((target.source, target.line))
                if len(target) == 1 and isinstance(target[0], nodes.emphasis):
                    target[0][:] = list(self.superscript_children(target[0]))
        for target in self.document.traverse(nodes.definition_list_item):
            ids = set()
            for c in target:
                if isinstance(c, nodes.term):
                    ids = set(c['ids'])
                if isinstance(c, nodes.definition) and len(c) == 1 and isinstance(c[0], see):
                    self.see_only_ids |= ids
        objects = self.document.settings.env.domaindata['std']['objects']
        endings = [(l, l + 's') for l in 'abcedfghijklmnopqrtuvwxz']
        endings.extend([('ss', 'sses'), ('ing', 'ed'), ('y', 'ies'), ('e', 'ed'), ('', 'ed')])
        for (name, fullname), value in list(objects.items()):
            if name != 'term':
                continue
            m = self.sense_re.match(fullname)
            if m:
                old_fullname = m.group(1)
                sense = ' ' + m.group(2)
            else:
                old_fullname = fullname
                sense = ''
            if any((old_fullname.endswith(e) for _, e in endings)):
                continue
            for old_ending, new_ending in endings:
                if not old_fullname.endswith(old_ending):
                    continue
                new_fullname = '{}{}{}'.format(old_fullname[:len(old_fullname) - len(old_ending)], new_ending, sense)
                new_key = (name, new_fullname)
                if new_key not in objects:
                    objects[new_key] = value

    @classmethod
    def warn_indirect_terms(cls, app, exception):
        """
        Output a warning for each cross-reference to a term that
        consists only of a "see:" paragraph. These cross-references
        should be changed in the source text to refer to the target of
        the "see:".
        """
        if not exception:
            for i in cls.see_only_ids:
                for doc, line in cls.xref_ids[i]:
                    print('{}:{}: WARNING: cross-reference to {}.'.format(doc, line, i))

def apply(self):
    for target in self.document.traverse(nodes.term):
        target[:] = list(self.superscript_children(target))
    for target in self.document.traverse(addnodes.pending_xref):
        if target['reftype'] == 'term':
            ids = self.xref_ids['term-{}'.format(target['reftarget'])]
            ids.append((target.source, target.line))
            if len(target) == 1 and isinstance(target[0], nodes.emphasis):
                target[0][:] = list(self.superscript_children(target[0]))
    for target in self.document.traverse(nodes.definition_list_item):
        ids = set()
        for c in target:
            if isinstance(c, nodes.term):
                ids = set(c['ids'])
            if isinstance(c, nodes.definition) and len(c) == 1 and isinstance(c[0], see):
                self.see_only_ids |= ids
    objects = self.document.settings.env.domaindata['std']['objects']
    endings = [(l, l + 's') for l in 'abcedfghijklmnopqrtuvwxz']
    endings.extend([('ss', 'sses'), ('ing', 'ed'), ('y', 'ies'), ('e', 'ed'), ('', 'ed')])
    for (name, fullname), value in list(objects.items()):
        if name != 'term':
            continue
        m = self.sense_re.match(fullname)
        if m:
            old_fullname = m.group(1)
            sense = ' ' + m.group(2)
        else:
            old_fullname = fullname
            sense = ''
        if any((old_fullname.endswith(e) for _, e in endings)):
            continue
        for old_ending, new_ending in endings:
            if not old_fullname.endswith(old_ending):
                continue
            new_fullname = '{}{}{}'.format(old_fullname[:len(old_fullname) - len(old_ending)], new_ending, sense)
            new_key = (name, new_fullname)
            if new_key not in objects:
                objects[new_key] = value

class DummyObjectDetector(AbstractClassifierFunction):

    def setup(self, *args, **kwargs):
        pass

    @property
    def name(self) -> str:
        return 'DummyObjectDetector'

    @property
    def labels(self):
        return ['__background__', 'person', 'bicycle']

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        ret = pd.DataFrame()
        ret['label'] = df.apply(self.classify_one, axis=1)
        return ret

    def classify_one(self, frames: np.ndarray):
        i = int(frames[0][0][0][0])
        label = self.labels[i % 2 + 1]
        return np.array([label])

def classify_one(self, frames: np.ndarray):
    i = int(frames[0][0][0][0])
    label = self.labels[i % 2 + 1]
    return np.array([label])

class DummyMultiObjectDetector(AbstractClassifierFunction):
    """
    Returns multiple objects for each frame
    """

    def setup(self, *args, **kwargs):
        pass

    @property
    def name(self) -> str:
        return 'DummyMultiObjectDetector'

    @property
    def labels(self):
        return ['__background__', 'person', 'bicycle', 'car']

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        ret = pd.DataFrame()
        ret['labels'] = df.apply(self.classify_one, axis=1)
        return ret

    def classify_one(self, frames: np.ndarray):
        i = int(frames[0][0][0][0])
        label = self.labels[i % 3 + 1]
        return np.array([label, label])

def classify_one(self, frames: np.ndarray):
    i = int(frames[0][0][0][0])
    label = self.labels[i % 3 + 1]
    return np.array([label, label])

class DummyFeatureExtractor(AbstractClassifierFunction):
    """
    Returns a feature for a frame.
    """

    def setup(self, *args, **kwargs):
        pass

    @property
    def name(self) -> str:
        return 'DummyFeatureExtractor'

    @property
    def labels(self):
        return []

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:

        def _extract_feature(row: pd.Series):
            feat_input = row[0]
            feat_input = feat_input.reshape(1, -1)
            feat_input = feat_input.astype(np.float32)
            return feat_input
        ret = pd.DataFrame()
        ret['features'] = df.apply(_extract_feature, axis=1)
        return ret

def _extract_feature(row: pd.Series):
    feat_input = row[0]
    feat_input = feat_input.reshape(1, -1)
    feat_input = feat_input.astype(np.float32)
    return feat_input

class DummyObjectDetectorDecorators(AbstractClassifierFunction):

    @decorators.setup(cacheable=True, function_type='object_detection', batchable=True)
    def setup(self, *args, **kwargs):
        pass

    @property
    def name(self) -> str:
        return 'DummyObjectDetectorDecorators'

    @property
    def labels(self):
        return ['__background__', 'person', 'bicycle']

    @decorators.forward(input_signatures=[PandasDataframe(columns=['Frame_Array'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256)])], output_signatures=[NumpyArray(name='label', type=NdArrayType.STR)])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        ret = pd.DataFrame()
        ret['label'] = df.apply(self.classify_one, axis=1)
        return ret

    def classify_one(self, frames: np.ndarray):
        i = int(frames[0][0][0][0]) - 1
        label = self.labels[i % 2 + 1]
        return np.array([label])

def classify_one(self, frames: np.ndarray):
    i = int(frames[0][0][0][0]) - 1
    label = self.labels[i % 2 + 1]
    return np.array([label])

@pytest.mark.notparallel
class S3LoadExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()
        self.multiple_video_file_path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1'
        self.s3_download_dir = self.evadb.catalog().get_configuration_catalog_value('s3_download_dir')
        'Mocked AWS Credentials for moto.'
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        try_to_import_moto()
        from moto import mock_s3
        self.mock_s3 = mock_s3()
        self.mock_s3.start()
        import boto3
        self.s3_client = boto3.client('s3')

    def upload_single_file(self, bucket_name='test-bucket'):
        self.s3_client.create_bucket(Bucket=bucket_name)
        self.s3_client.upload_file(self.video_file_path, bucket_name, 'dummy.avi')

    def upload_multiple_files(self, bucket_name='test-bucket'):
        self.s3_client.create_bucket(Bucket=bucket_name)
        video_path = self.multiple_video_file_path
        for file in os.listdir(video_path):
            self.s3_client.upload_file(f'{video_path}/{file}', bucket_name, file)

    def tearDown(self):
        shutdown_ray()
        file_remove('MyVideo/dummy.avi', parent_dir=self.s3_download_dir)
        for file in os.listdir(self.multiple_video_file_path):
            file_remove(f'MyVideos/{file}', parent_dir=self.s3_download_dir)
        self.mock_s3.stop()

    def test_s3_single_file_load_executor(self):
        bucket_name = 'single-file-bucket'
        self.upload_single_file(bucket_name)
        query = f"LOAD VIDEO 's3://{bucket_name}/dummy.avi' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        select_query = 'SELECT * FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(video_dir=os.path.join(self.s3_download_dir, 'MyVideo')))[0]
        self.assertEqual(actual_batch, expected_batch)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_s3_multiple_file_load_executor(self):
        bucket_name = 'multiple-file-bucket'
        self.upload_multiple_files(bucket_name)
        query = f'LOAD VIDEO "s3://{bucket_name}/*.mp4" INTO MyVideos;'
        result = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 2']))
        self.assertEqual(result, expected)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

    def test_s3_multiple_file_multiple_load_executor(self):
        bucket_name = 'multiple-file-multiple-load-bucket'
        self.upload_single_file(bucket_name)
        self.upload_multiple_files(bucket_name)
        insert_query_one = f'LOAD VIDEO "s3://{bucket_name}/1.mp4" INTO MyVideos;'
        execute_query_fetch_all(self.evadb, insert_query_one)
        insert_query_two = f'LOAD VIDEO "s3://{bucket_name}/2.mp4" INTO MyVideos;'
        execute_query_fetch_all(self.evadb, insert_query_two)
        insert_query_three = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideos;"
        execute_query_fetch_all(self.evadb, insert_query_three)
        select_query = 'SELECT * FROM MyVideos;'
        result = execute_query_fetch_all(self.evadb, select_query)
        result_videos = [Path(video).as_posix() for video in result.frames['myvideos.name'].unique()]
        s3_dir_path = Path(self.s3_download_dir)
        expected_videos = [(s3_dir_path / 'MyVideos/1.mp4').as_posix(), (s3_dir_path / 'MyVideos/2.mp4').as_posix(), Path(self.video_file_path).as_posix()]
        self.assertEqual(result_videos, expected_videos)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

def test_s3_multiple_file_multiple_load_executor(self):
    bucket_name = 'multiple-file-multiple-load-bucket'
    self.upload_single_file(bucket_name)
    self.upload_multiple_files(bucket_name)
    insert_query_one = f'LOAD VIDEO "s3://{bucket_name}/1.mp4" INTO MyVideos;'
    execute_query_fetch_all(self.evadb, insert_query_one)
    insert_query_two = f'LOAD VIDEO "s3://{bucket_name}/2.mp4" INTO MyVideos;'
    execute_query_fetch_all(self.evadb, insert_query_two)
    insert_query_three = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideos;"
    execute_query_fetch_all(self.evadb, insert_query_three)
    select_query = 'SELECT * FROM MyVideos;'
    result = execute_query_fetch_all(self.evadb, select_query)
    result_videos = [Path(video).as_posix() for video in result.frames['myvideos.name'].unique()]
    s3_dir_path = Path(self.s3_download_dir)
    expected_videos = [(s3_dir_path / 'MyVideos/1.mp4').as_posix(), (s3_dir_path / 'MyVideos/2.mp4').as_posix(), Path(self.video_file_path).as_posix()]
    self.assertEqual(result_videos, expected_videos)
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

class CostModel(unittest.TestCase):

    def execute_task_stack(self, task_stack):
        while not task_stack.empty():
            task = task_stack.pop()
            task.execute()

    def test_should_select_cheap_plan(self):

        def side_effect_func(value):
            if value is grp_expr1:
                return 1
            elif value is grp_expr2:
                return 2
        cm = CostModel()
        cm.calculate_cost = MagicMock(side_effect=side_effect_func)
        opt_cxt = OptimizerContext(MagicMock(), cm)
        grp_expr1 = GroupExpression(MagicMock())
        grp_expr1.opr.is_logical = lambda: False
        grp_expr2 = GroupExpression(MagicMock())
        grp_expr2.opr.is_logical = lambda: False
        opt_cxt.memo.add_group_expr(grp_expr1)
        opt_cxt.memo.add_group_expr(grp_expr2, grp_expr1.group_id)
        grp = opt_cxt.memo.get_group_by_id(grp_expr1.group_id)
        opt_cxt.task_stack.push(OptimizeGroup(grp, opt_cxt))
        self.execute_task_stack(opt_cxt.task_stack)
        plan = PlanGenerator(MagicMock()).build_optimal_physical_plan(grp_expr1.group_id, opt_cxt)
        self.assertEqual(plan, grp_expr1.opr)
        self.assertEqual(grp.get_best_expr_cost(PropertyType.DEFAULT), 1)

    def test_should_select_cheap_plan_with_tree(self):

        def side_effect_func(value):
            cost = dict({grp_expr00: 1, grp_expr01: 2, grp_expr10: 4, grp_expr11: 3, grp_expr20: 5})
            return cost[value]
        cm = CostModel()
        cm.calculate_cost = MagicMock(side_effect=side_effect_func)
        opt_cxt = OptimizerContext(MagicMock(), cm)
        grp_expr00 = GroupExpression(Operator(MagicMock()))
        grp_expr00.opr.is_logical = lambda: False
        grp_expr01 = GroupExpression(Operator(MagicMock()))
        grp_expr01.opr.is_logical = lambda: False
        opt_cxt.memo.add_group_expr(grp_expr00)
        opt_cxt.memo.add_group_expr(grp_expr01, grp_expr00.group_id)
        grp_expr10 = GroupExpression(Operator(MagicMock()))
        grp_expr10.opr.is_logical = lambda: False
        opt_cxt.memo.add_group_expr(grp_expr10)
        grp_expr11 = GroupExpression(Operator(MagicMock()))
        grp_expr11.opr.is_logical = lambda: False
        opt_cxt.memo.add_group_expr(grp_expr11, grp_expr10.group_id)
        grp_expr20 = GroupExpression(Operator(MagicMock()))
        grp_expr20.opr.is_logical = lambda: False
        opt_cxt.memo.add_group_expr(grp_expr20)
        grp = opt_cxt.memo.get_group_by_id(grp_expr20.group_id)
        grp_expr10.children = [grp_expr01.group_id]
        grp_expr11.children = [grp_expr01.group_id]
        grp_expr20.children = [grp_expr10.group_id]
        opt_cxt.task_stack.push(OptimizeGroup(grp, opt_cxt))
        self.execute_task_stack(opt_cxt.task_stack)
        plan = PlanGenerator(MagicMock()).build_optimal_physical_plan(grp_expr20.group_id, opt_cxt)
        subplan = copy(grp_expr11.opr)
        subplan.children = [copy(grp_expr01.opr)]
        expected_plan = copy(grp_expr20.opr)
        expected_plan.children = [subplan]
        self.assertEqual(plan, expected_plan)
        self.assertEqual(grp.get_best_expr_cost(PropertyType.DEFAULT), 9)

def execute_task_stack(self, task_stack):
    while not task_stack.empty():
        task = task_stack.pop()
        task.execute()

class TestOptimizerTask(unittest.TestCase):

    def execute_task_stack(self, task_stack):
        while not task_stack.empty():
            task = task_stack.pop()
            task.execute()

    def test_abstract_optimizer_task(self):
        task = OptimizerTask(MagicMock(), MagicMock())
        with self.assertRaises(NotImplementedError):
            task.execute()

    def top_down_rewrite(self, opr):
        opt_cxt = OptimizerContext(MagicMock(), CostModel(), RulesManager())
        grp_expr = opt_cxt.add_opr_to_group(opr)
        root_grp_id = grp_expr.group_id
        opt_cxt.task_stack.push(TopDownRewrite(grp_expr, RulesManager().stage_one_rewrite_rules, opt_cxt))
        self.execute_task_stack(opt_cxt.task_stack)
        return (opt_cxt, root_grp_id)

    def bottom_up_rewrite(self, root_grp_id, opt_cxt):
        grp_expr = opt_cxt.memo.groups[root_grp_id].logical_exprs[0]
        opt_cxt.task_stack.push(BottomUpRewrite(grp_expr, RulesManager().stage_two_rewrite_rules, opt_cxt))
        self.execute_task_stack(opt_cxt.task_stack)
        return (opt_cxt, root_grp_id)

    def implement_group(self, root_grp_id, opt_cxt):
        grp = opt_cxt.memo.groups[root_grp_id]
        opt_cxt.task_stack.push(OptimizeGroup(grp, opt_cxt))
        self.execute_task_stack(opt_cxt.task_stack)
        return (opt_cxt, root_grp_id)

    def test_simple_implementation(self):
        predicate = MagicMock()
        child_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        root_opr = LogicalFilter(predicate, [child_opr])
        opt_cxt, root_grp_id = self.top_down_rewrite(root_opr)
        opt_cxt, root_grp_id = self.bottom_up_rewrite(root_grp_id, opt_cxt)
        opt_cxt, root_grp_id = self.implement_group(root_grp_id, opt_cxt)
        root_grp = opt_cxt.memo.groups[root_grp_id]
        best_root_grp_expr = root_grp.get_best_expr(PropertyType.DEFAULT)
        self.assertEqual(type(best_root_grp_expr.opr), PredicatePlan)

    def test_nested_implementation(self):
        child_predicate = MagicMock()
        root_predicate = MagicMock()
        with patch('evadb.optimizer.rules.rules.extract_pushdown_predicate') as mock:
            with patch('evadb.optimizer.rules.rules.is_video_table') as mock_vid:
                mock_vid.return_value = True
                mock.side_effect = [(child_predicate, None), (root_predicate, None)]
                child_get_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
                child_filter_opr = LogicalFilter(child_predicate, children=[child_get_opr])
                child_project_opr = LogicalProject([MagicMock()], children=[child_filter_opr])
                root_derived_get_opr = LogicalQueryDerivedGet(MagicMock(), children=[child_project_opr])
                root_filter_opr = LogicalFilter(root_predicate, children=[root_derived_get_opr])
                root_project_opr = LogicalProject([MagicMock()], children=[root_filter_opr])
                opt_cxt, root_grp_id = self.top_down_rewrite(root_project_opr)
                opt_cxt, root_grp_id = self.bottom_up_rewrite(root_grp_id, opt_cxt)
                opt_cxt, root_grp_id = self.implement_group(root_grp_id, opt_cxt)
                expected_expr_order = [ProjectPlan, PredicatePlan, SeqScanPlan, ProjectPlan, SeqScanPlan]
                curr_grp_id = root_grp_id
                idx = 0
                while True:
                    root_grp = opt_cxt.memo.groups[curr_grp_id]
                    best_root_grp_expr = root_grp.get_best_expr(PropertyType.DEFAULT)
                    self.assertEqual(type(best_root_grp_expr.opr), expected_expr_order[idx])
                    idx += 1
                    if idx == len(expected_expr_order):
                        break
                    curr_grp_id = best_root_grp_expr.children[0]

def execute_task_stack(self, task_stack):
    while not task_stack.empty():
        task = task_stack.pop()
        task.execute()

class ColumnTypeTests(unittest.TestCase):

    def test_ndarray_type_to_numpy_type(self):
        expected_type = [np.int8, np.uint8, np.int16, np.int32, np.int64, np.unicode_, np.bool_, np.float32, np.float64, Decimal, np.str_, np.datetime64]
        for ndarray_type, np_type in zip(NdArrayType, expected_type):
            self.assertEqual(NdArrayType.to_numpy_type(ndarray_type), np_type)

    def test_raise_exception_uknown_ndarray_type(self):
        self.assertRaises(ValueError, NdArrayType.to_numpy_type, ColumnType.TEXT)

def test_ndarray_type_to_numpy_type(self):
    expected_type = [np.int8, np.uint8, np.int16, np.int32, np.int64, np.unicode_, np.bool_, np.float32, np.float64, Decimal, np.str_, np.datetime64]
    for ndarray_type, np_type in zip(NdArrayType, expected_type):
        self.assertEqual(NdArrayType.to_numpy_type(ndarray_type), np_type)

class CatalogModelsTest(unittest.TestCase):

    def test_df_column(self):
        df_col = ColumnCatalogEntry('name', ColumnType.TEXT, is_nullable=False)
        df_col.array_dimensions = [1, 2]
        df_col.table_id = 1
        self.assertEqual(df_col.array_type, None)
        self.assertEqual(df_col.array_dimensions, [1, 2])
        self.assertEqual(df_col.is_nullable, False)
        self.assertEqual(df_col.name, 'name')
        self.assertEqual(df_col.type, ColumnType.TEXT)
        self.assertEqual(df_col.table_id, 1)
        self.assertEqual(df_col.row_id, None)

    def test_df_equality(self):
        df_col = ColumnCatalogEntry('name', ColumnType.TEXT, is_nullable=False)
        self.assertEqual(df_col, df_col)
        df_col1 = ColumnCatalogEntry('name2', ColumnType.TEXT, is_nullable=False)
        self.assertNotEqual(df_col, df_col1)
        df_col1 = ColumnCatalogEntry('name', ColumnType.INTEGER, is_nullable=False)
        self.assertNotEqual(df_col, df_col1)
        df_col1 = ColumnCatalogEntry('name', ColumnType.INTEGER, is_nullable=True)
        self.assertNotEqual(df_col, df_col1)
        df_col1 = ColumnCatalogEntry('name', ColumnType.INTEGER, is_nullable=False)
        self.assertNotEqual(df_col, df_col1)
        df_col._array_dimensions = [2, 4]
        df_col1 = ColumnCatalogEntry('name', ColumnType.INTEGER, is_nullable=False, array_dimensions=[1, 2])
        self.assertNotEqual(df_col, df_col1)
        df_col._table_id = 1
        df_col1 = ColumnCatalogEntry('name', ColumnType.INTEGER, is_nullable=False, array_dimensions=[2, 4], table_id=2)
        self.assertNotEqual(df_col, df_col1)

    def test_table_catalog_entry_equality(self):
        column_1 = ColumnCatalogEntry('frame_id', ColumnType.INTEGER, False)
        column_2 = ColumnCatalogEntry('frame_label', ColumnType.INTEGER, False)
        col_list = [column_1, column_2]
        table_catalog_entry = TableCatalogEntry('name', 'evadb_dataset', table_type=TableType.VIDEO_DATA, columns=col_list)
        self.assertEqual(table_catalog_entry, table_catalog_entry)
        table_catalog_entry1 = TableCatalogEntry('name2', 'evadb_dataset', table_type=TableType.VIDEO_DATA, columns=col_list)
        self.assertNotEqual(table_catalog_entry, table_catalog_entry1)

    def test_function(self):
        function = FunctionCatalogEntry('function', 'fasterRCNN', 'ObjectDetection', 'checksum')
        self.assertEqual(function.row_id, None)
        self.assertEqual(function.impl_file_path, 'fasterRCNN')
        self.assertEqual(function.name, 'function')
        self.assertEqual(function.type, 'ObjectDetection')
        self.assertEqual(function.checksum, 'checksum')

    def test_function_hash(self):
        function1 = FunctionCatalogEntry('function', 'fasterRCNN', 'ObjectDetection', 'checksum')
        function2 = FunctionCatalogEntry('function', 'fasterRCNN', 'ObjectDetection', 'checksum')
        self.assertEqual(hash(function1), hash(function2))

    def test_function_equality(self):
        function = FunctionCatalogEntry('function', 'fasterRCNN', 'ObjectDetection', 'checksum')
        self.assertEqual(function, function)
        function2 = FunctionCatalogEntry('function2', 'fasterRCNN', 'ObjectDetection', 'checksum')
        self.assertNotEqual(function, function2)
        function3 = FunctionCatalogEntry('function', 'fasterRCNN2', 'ObjectDetection', 'checksum')
        self.assertNotEqual(function, function3)
        function4 = FunctionCatalogEntry('function2', 'fasterRCNN', 'ObjectDetection3', 'checksum')
        self.assertNotEqual(function, function4)

    def test_function_io(self):
        function_io = FunctionIOCatalogEntry('name', ColumnType.NDARRAY, True, NdArrayType.UINT8, [2, 3], True, 1)
        self.assertEqual(function_io.row_id, None)
        self.assertEqual(function_io.function_id, 1)
        self.assertEqual(function_io.is_input, True)
        self.assertEqual(function_io.is_nullable, True)
        self.assertEqual(function_io.array_type, NdArrayType.UINT8)
        self.assertEqual(function_io.array_dimensions, [2, 3])
        self.assertEqual(function_io.name, 'name')
        self.assertEqual(function_io.type, ColumnType.NDARRAY)

    def test_function_io_equality(self):
        function_io = FunctionIOCatalogEntry('name', ColumnType.FLOAT, True, None, [2, 3], True, 1)
        self.assertEqual(function_io, function_io)
        function_io2 = FunctionIOCatalogEntry('name2', ColumnType.FLOAT, True, None, [2, 3], True, 1)
        self.assertNotEqual(function_io, function_io2)
        function_io2 = FunctionIOCatalogEntry('name', ColumnType.INTEGER, True, None, [2, 3], True, 1)
        self.assertNotEqual(function_io, function_io2)
        function_io2 = FunctionIOCatalogEntry('name', ColumnType.FLOAT, False, None, [2, 3], True, 1)
        self.assertNotEqual(function_io, function_io2)
        function_io2 = FunctionIOCatalogEntry('name', ColumnType.FLOAT, True, None, [2, 3, 4], True, 1)
        self.assertNotEqual(function_io, function_io2)
        function_io2 = FunctionIOCatalogEntry('name', ColumnType.FLOAT, True, None, [2, 3], False, 1)
        self.assertNotEqual(function_io, function_io2)
        function_io2 = FunctionIOCatalogEntry('name', ColumnType.FLOAT, True, None, [2, 3], True, 2)
        self.assertNotEqual(function_io, function_io2)

    def test_index(self):
        index = IndexCatalogEntry('index', 'FaissSavePath', 'HNSW')
        self.assertEqual(index.row_id, None)
        self.assertEqual(index.name, 'index')
        self.assertEqual(index.save_file_path, 'FaissSavePath')
        self.assertEqual(index.type, 'HNSW')

    def test_index_hash(self):
        index1 = IndexCatalogEntry('index', 'FaissSavePath', 'HNSW')
        index2 = IndexCatalogEntry('index', 'FaissSavePath', 'HNSW')
        self.assertEqual(hash(index1), hash(index2))

    def test_index_equality(self):
        index = IndexCatalogEntry('index', 'FaissSavePath', 'HNSW')
        self.assertEqual(index, index)
        index2 = IndexCatalogEntry('index2', 'FaissSavePath', 'HNSW')
        self.assertNotEqual(index, index2)
        index3 = IndexCatalogEntry('index', 'FaissSavePath3', 'HNSW')
        self.assertNotEqual(index, index3)
        index4 = IndexCatalogEntry('index', 'FaissSavePath', 'HNSW4')
        self.assertNotEqual(index, index4)

def test_function_io(self):
    function_io = FunctionIOCatalogEntry('name', ColumnType.NDARRAY, True, NdArrayType.UINT8, [2, 3], True, 1)
    self.assertEqual(function_io.row_id, None)
    self.assertEqual(function_io.function_id, 1)
    self.assertEqual(function_io.is_input, True)
    self.assertEqual(function_io.is_nullable, True)
    self.assertEqual(function_io.array_type, NdArrayType.UINT8)
    self.assertEqual(function_io.array_dimensions, [2, 3])
    self.assertEqual(function_io.name, 'name')
    self.assertEqual(function_io.type, ColumnType.NDARRAY)

@pytest.mark.notparallel
class DecordLoaderTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        try_to_import_decord()
        self.video_file_url = create_sample_video()
        self.video_with_audio_file_url = f'{EvaDB_ROOT_DIR}/data/sample_videos/touchdown.mp4'
        self.frame_size = FRAME_SIZE[0] * FRAME_SIZE[1] * 3
        self.audio_frames = []
        for line in open(f'{EvaDB_ROOT_DIR}/test/data/touchdown_audio_frames.csv').readlines():
            self.audio_frames.append(np.fromstring(line, sep=','))

    @classmethod
    def tearDownClass(self):
        file_remove('dummy.avi')

    def _batches_to_reader_convertor(self, batches):
        new_batches = []
        for batch in batches:
            batch.drop_column_alias()
            new_batches.append(batch.project(['id', 'data', 'seconds', '_row_number']))
        return new_batches

    def test_should_sample_only_iframe(self):
        for k in range(1, 10):
            video_loader = DecordReader(file_url=self.video_file_url, sampling_type=IFRAMES, sampling_rate=k)
            batches = list(video_loader.read())
            expected = self._batches_to_reader_convertor(create_dummy_batches(filters=[i for i in range(0, NUM_FRAMES, k)], is_from_storage=True))
            self.assertEqual(batches, expected)

    def test_should_sample_every_k_frame_with_predicate(self):
        col = TupleValueExpression('id')
        val = ConstantValueExpression(NUM_FRAMES // 2)
        predicate = ComparisonExpression(ExpressionType.COMPARE_GEQ, left=col, right=val)
        for k in range(2, 4):
            video_loader = DecordReader(file_url=self.video_file_url, sampling_rate=k, predicate=predicate)
            batches = list(video_loader.read())
            value = NUM_FRAMES // 2
            start = value + k - value % k if value % k else value
            expected = self._batches_to_reader_convertor(create_dummy_batches(filters=[i for i in range(start, NUM_FRAMES, k)], is_from_storage=True))
        self.assertEqual(batches, expected)
        value = 2
        predicate_1 = ComparisonExpression(ExpressionType.COMPARE_GEQ, left=TupleValueExpression('id'), right=ConstantValueExpression(value))
        predicate_2 = ComparisonExpression(ExpressionType.COMPARE_LEQ, left=TupleValueExpression('id'), right=ConstantValueExpression(8))
        predicate = LogicalExpression(ExpressionType.LOGICAL_AND, predicate_1, predicate_2)
        for k in range(2, 4):
            video_loader = DecordReader(file_url=self.video_file_url, sampling_rate=k, predicate=predicate)
            batches = list(video_loader.read())
            start = value + k - value % k if value % k else value
            expected = self._batches_to_reader_convertor(create_dummy_batches(filters=[i for i in range(start, 8, k)], is_from_storage=True))
        self.assertEqual(batches, expected)

    def test_should_return_one_batch(self):
        video_loader = DecordReader(file_url=self.video_file_url)
        batches = list(video_loader.read())
        expected = self._batches_to_reader_convertor(create_dummy_batches(is_from_storage=True))
        self.assertEqual(batches, expected)

    def test_should_return_batches_equivalent_to_number_of_frames(self):
        video_loader = DecordReader(file_url=self.video_file_url, batch_mem_size=self.frame_size)
        batches = list(video_loader.read())
        expected = self._batches_to_reader_convertor(create_dummy_batches(batch_size=1, is_from_storage=True))
        self.assertEqual(batches, expected)

    def test_should_sample_every_k_frame(self):
        for k in range(1, 10):
            video_loader = DecordReader(file_url=self.video_file_url, sampling_rate=k)
            batches = list(video_loader.read())
            expected = self._batches_to_reader_convertor(create_dummy_batches(filters=[i for i in range(0, NUM_FRAMES, k)], is_from_storage=True))
            self.assertEqual(batches, expected)

    def test_should_throw_error_for_audioless_video(self):
        with self.assertRaises(AssertionError) as error_context:
            video_loader = DecordReader(file_url=self.video_file_url, read_audio=True, read_video=True)
            list(video_loader.read())
        self.assertIn("Can't find audio stream", error_context.exception.args[0].args[0])

    def test_should_throw_error_when_sampling_iframes_for_audio(self):
        with self.assertRaises(AssertionError) as error_context:
            video_loader = DecordReader(file_url=self.video_with_audio_file_url, sampling_type=IFRAMES, read_audio=True, read_video=False)
            list(video_loader.read())
        self.assertEquals('Cannot use IFRAMES with audio streams', error_context.exception.args[0])

    def test_should_throw_error_when_sampling_audio_for_video(self):
        with self.assertRaises(AssertionError) as error_context:
            video_loader = DecordReader(file_url=self.video_file_url, sampling_type=AUDIORATE, read_audio=False, read_video=True)
            list(video_loader.read())
        self.assertEquals('Cannot use AUDIORATE with video streams', error_context.exception.args[0])

    def test_should_return_audio_frames(self):
        video_loader = DecordReader(file_url=self.video_with_audio_file_url, sampling_type=AUDIORATE, sampling_rate=16000, read_audio=True, read_video=False)
        batches = list(video_loader.read())
        batches = batches[0].frames[batches[0].frames.index.isin([0, 100, 200, 300, 400, 500, 600, 700, 800, 900])].reset_index()
        for i, frame in enumerate(self.audio_frames):
            self.assertTrue(np.array_equiv(self.audio_frames[i], batches.iloc[i]['audio']))
        self.assertEqual(batches.iloc[0]['data'].shape, (0,))

def _batches_to_reader_convertor(self, batches):
    new_batches = []
    for batch in batches:
        batch.drop_column_alias()
        new_batches.append(batch.project(['id', 'data', 'seconds', '_row_number']))
    return new_batches

class AbstractPlan(ABC):

    def __init__(self, opr_type):
        self._children = []
        self._parent = None
        self._opr_type = opr_type

    def append_child(self, child):
        """append node to children list

        Arguments:
            child {AbstractPlan} -- input child node
        """
        self._children.append(child)

    @property
    def parent(self):
        """Returns the parent of current node

        Returns:
            AbstractPlan -- parent node
        """
        return self._parent

    @parent.setter
    def parent(self, node: 'AbstractPlan'):
        """sets parent of current node

        Arguments:
            node {AbstractPlan} -- parent node
        """
        self._parent = node

    @property
    def children(self) -> List['AbstractPlan']:
        return self._children

    @property
    def opr_type(self) -> PlanOprType:
        """
        Property used for returning the node type of Plan.

        Returns:
            PlanOprType: The node type corresponding to the plan
        """
        return self._opr_type

    def clear_children(self):
        self.children.clear()

    def is_logical(self):
        return False

    @abstractmethod
    def __hash__(self) -> int:
        return hash(self.opr_type)

    @abstractmethod
    def __str__(self) -> str:
        return 'AbstractPlan'

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        for k, v in self.__dict__.items():
            if k == '_children':
                setattr(result, k, [])
            else:
                setattr(result, k, v)
        return result

    def walk(self, bfs=True):
        """
        Returns a generator which visits all nodes in physical plan tree.
        """
        if bfs:
            yield from self.bfs()
        else:
            yield from self.dfs()

    def bfs(self):
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            for child in node.children:
                queue.append(child)

    def dfs(self):
        yield self
        for child in self.children:
            yield from child.dfs()

    def find_all(self, plan_type: Any):
        """Returns a generator which visits all the nodes in plan tree and yields one
        that matches the passed `expression_type`.

        Args:
            plan_type (Any): plan type to match with

        Returns:
            the generator object.
        """
        for node in self.bfs():
            if isinstance(node, plan_type) or self.opr_type == plan_type:
                yield node

def append_child(self, child):
    """append node to children list

        Arguments:
            child {AbstractPlan} -- input child node
        """
    self._children.append(child)

def bfs(self):
    queue = deque([self])
    while queue:
        node = queue.popleft()
        yield node
        for child in node.children:
            queue.append(child)

class Operator:
    """Base class for logical plan of operators
    Arguments:
        op_type: {OperatorType} -- {the opr type held by this node}
        children: {List} -- {the list of operator children for this node}
    """

    def __init__(self, op_type: OperatorType, children=None):
        self._opr_type = op_type
        self._children = children or []

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        self._children = children

    @property
    def opr_type(self):
        return self._opr_type

    def append_child(self, child: 'Operator'):
        self.children.append(child)

    def clear_children(self):
        self.children = []

    def __str__(self) -> str:
        return '%s[%s](%s)' % (type(self).__name__, hex(id(self)), ', '.join(('%s=%s' % item for item in vars(self).items())))

    def __eq__(self, other):
        is_subtree_equal = True
        if not isinstance(other, Operator):
            return False
        if len(self.children) != len(other.children):
            return False
        for child1, child2 in zip(self.children, other.children):
            is_subtree_equal = is_subtree_equal and child1 == child2
        return is_subtree_equal

    def is_logical(self):
        return self._opr_type < OperatorType.LOGICALDELIMITER

    def __hash__(self) -> int:
        return hash((self.opr_type, tuple(self.children)))

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        for k, v in self.__dict__.items():
            if k == '_children':
                setattr(result, k, [])
            else:
                setattr(result, k, v)
        return result

    def bfs(self):
        """Returns a generator which visits all nodes in operator tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            for child in node.children:
                queue.append(child)

    def find_all(self, operator_type: Any):
        """Returns a generator which visits all the nodes in operator tree and yields one that matches the passed `operator_type`.

        Args:
            operator_type (Any): operator type to match with

        Returns:
            the generator object.
        """
        for node in self.bfs():
            if isinstance(node, operator_type) or self.opr_type == operator_type:
                yield node

def append_child(self, child: 'Operator'):
    self.children.append(child)

def __eq__(self, other):
    is_subtree_equal = True
    if not isinstance(other, Operator):
        return False
    if len(self.children) != len(other.children):
        return False
    for child1, child2 in zip(self.children, other.children):
        is_subtree_equal = is_subtree_equal and child1 == child2
    return is_subtree_equal

def bfs(self):
    """Returns a generator which visits all nodes in operator tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
    queue = deque([self])
    while queue:
        node = queue.popleft()
        yield node
        for child in node.children:
            queue.append(child)

class GroupExpression:

    def __init__(self, opr: Operator, group_id: int=UNDEFINED_GROUP_ID, children: List[int]=[]):
        assert len(opr.children) == 0, 'Cannot create a group expression\n                                from operator with children'
        self._opr = opr
        self._group_id = group_id
        self._children = children
        self._rules_explored = RuleType.INVALID_RULE

    @property
    def opr(self):
        return self._opr

    @property
    def group_id(self):
        return self._group_id

    @group_id.setter
    def group_id(self, new_id):
        self._group_id = new_id

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, new_children):
        self._children = new_children

    def append_child(self, child_id: int):
        self._children.append(child_id)

    @property
    def rules_explored(self):
        return self._rules_explored

    def is_logical(self):
        return self.opr.is_logical()

    def mark_rule_explored(self, rule_id: RuleType):
        self._rules_explored |= rule_id

    def is_rule_explored(self, rule_id: RuleType):
        return self._rules_explored & rule_id == rule_id

    def __eq__(self, other: 'GroupExpression'):
        if not isinstance(other, GroupExpression):
            return False
        return self.group_id == other.group_id and self.opr == other.opr and (self.children == other.children)

    def __str__(self) -> str:
        return '%s(%s)' % (type(self).__name__, ', '.join(('%s=%s' % item for item in vars(self).items())))

    def __hash__(self):
        return hash((self.opr, tuple(self.children)))

def append_child(self, child_id: int):
    self._children.append(child_id)

class PlanGenerator:
    """
    Used for building Physical Plan from Logical Plan.
    """

    def __init__(self, db: EvaDBDatabase, rules_manager: RulesManager=None, cost_model: CostModel=None) -> None:
        self.db = db
        is_ray_enabled = self.db.catalog().get_configuration_catalog_value('ray')
        self.rules_manager = rules_manager or RulesManager({'ray': is_ray_enabled})
        self.cost_model = cost_model or CostModel()

    def execute_task_stack(self, task_stack: OptimizerTaskStack):
        while not task_stack.empty():
            task = task_stack.pop()
            task.execute()

    def build_optimal_physical_plan(self, root_grp_id: int, optimizer_context: OptimizerContext):
        physical_plan = None
        root_grp = optimizer_context.memo.groups[root_grp_id]
        best_grp_expr = root_grp.get_best_expr(PropertyType.DEFAULT)
        physical_plan = best_grp_expr.opr
        for child_grp_id in best_grp_expr.children:
            child_plan = self.build_optimal_physical_plan(child_grp_id, optimizer_context)
            physical_plan.append_child(child_plan)
        return physical_plan

    def optimize(self, logical_plan: Operator):
        optimizer_context = OptimizerContext(self.db, self.cost_model, self.rules_manager)
        memo = optimizer_context.memo
        grp_expr = optimizer_context.add_opr_to_group(opr=logical_plan)
        root_grp_id = grp_expr.group_id
        root_expr = memo.groups[root_grp_id].logical_exprs[0]
        optimizer_context.task_stack.push(TopDownRewrite(root_expr, self.rules_manager.stage_one_rewrite_rules, optimizer_context))
        self.execute_task_stack(optimizer_context.task_stack)
        root_expr = memo.groups[root_grp_id].logical_exprs[0]
        optimizer_context.task_stack.push(BottomUpRewrite(root_expr, self.rules_manager.stage_two_rewrite_rules, optimizer_context))
        self.execute_task_stack(optimizer_context.task_stack)
        root_group = memo.get_group_by_id(root_grp_id)
        optimizer_context.task_stack.push(OptimizeGroup(root_group, optimizer_context))
        self.execute_task_stack(optimizer_context.task_stack)
        optimal_plan = self.build_optimal_physical_plan(root_grp_id, optimizer_context)
        return optimal_plan

    def build(self, logical_plan: Operator):
        try:
            plan = self.optimize(logical_plan)
        except TimeoutError:
            raise ValueError('Optimizer timed out!')
        return plan

def execute_task_stack(self, task_stack: OptimizerTaskStack):
    while not task_stack.empty():
        task = task_stack.pop()
        task.execute()

class Memo:
    """
    For now, we assume every group has only one logic expression.
    """

    def __init__(self):
        self._group_exprs: Dict[int, GroupExpression] = dict()
        self._groups = dict()

    @property
    def groups(self):
        return self._groups

    @property
    def group_exprs(self):
        return self._group_exprs

    def find_duplicate_expr(self, expr: GroupExpression) -> GroupExpression:
        if hash(expr) in self.group_exprs:
            return self.group_exprs[hash(expr)]
        else:
            return None

    def get_group_by_id(self, group_id: int) -> GroupExpression:
        if group_id in self._groups.keys():
            return self._groups[group_id]
        else:
            logger.error('Missing group id')
    '\n    For the consistency of the memo, all modification should use the\n    following functions.\n    '

    def _get_table_aliases(self, expr: GroupExpression) -> List[str]:
        """
        Collects table aliases of all the children
        """
        aliases = []
        for child_grp_id in expr.children:
            child_grp = self._groups[child_grp_id]
            aliases.extend(child_grp.aliases)
        if expr.opr.opr_type == OperatorType.LOGICALGET or expr.opr.opr_type == OperatorType.LOGICALQUERYDERIVEDGET:
            aliases.append(expr.opr.alias)
        elif expr.opr.opr_type == OperatorType.LOGICALFUNCTIONSCAN:
            aliases.append(expr.opr.alias)
        return aliases

    def _create_new_group(self, expr: GroupExpression):
        """
        Create new group for the expr
        """
        new_group_id = len(self._groups)
        aliases = self._get_table_aliases(expr)
        self._groups[new_group_id] = Group(new_group_id, aliases)
        self._insert_expr(expr, new_group_id)

    def _insert_expr(self, expr: GroupExpression, group_id: int):
        """
        Insert a group expression into a particular group
        """
        assert group_id < len(self.groups), 'Group Id out of the bound'
        group = self.groups[group_id]
        group.add_expr(expr)
        self._group_exprs[hash(expr)] = expr

    def erase_group(self, group_id: int):
        """
        Remove all the expr from the group_id
        """
        group = self.groups[group_id]
        for expr in group.logical_exprs:
            del self._group_exprs[hash(expr)]
        for expr in group.physical_exprs:
            del self._group_exprs[hash(expr)]
        group.clear_grp_exprs()

    def add_group_expr(self, expr: GroupExpression, group_id: int=UNDEFINED_GROUP_ID) -> GroupExpression:
        """
        Add an expression into the memo.
        If expr exists, we return it.
        If group_id is not specified, creates a new group
        Otherwise, inserts the expr into specified group.
        """
        duplicate_expr = self.find_duplicate_expr(expr)
        if duplicate_expr is not None:
            return duplicate_expr
        expr.group_id = group_id
        if expr.group_id == UNDEFINED_GROUP_ID:
            self._create_new_group(expr)
        else:
            self._insert_expr(expr, group_id)
        assert expr.group_id is not UNDEFINED_GROUP_ID, 'Expr should have a valid group id'
        return expr

def _get_table_aliases(self, expr: GroupExpression) -> List[str]:
    """
        Collects table aliases of all the children
        """
    aliases = []
    for child_grp_id in expr.children:
        child_grp = self._groups[child_grp_id]
        aliases.extend(child_grp.aliases)
    if expr.opr.opr_type == OperatorType.LOGICALGET or expr.opr.opr_type == OperatorType.LOGICALQUERYDERIVEDGET:
        aliases.append(expr.opr.alias)
    elif expr.opr.opr_type == OperatorType.LOGICALFUNCTIONSCAN:
        aliases.append(expr.opr.alias)
    return aliases

class OptimizerTaskStack:

    def __init__(self):
        self._task_stack = deque()

    def push(self, task: OptimizerTask):
        self._task_stack.append(task)

    def pop(self) -> OptimizerTask:
        return self._task_stack.pop()

    def empty(self) -> bool:
        return not self._task_stack

def __init__(self):
    self._task_stack = deque()

def push(self, task: OptimizerTask):
    self._task_stack.append(task)

def pop(self) -> OptimizerTask:
    return self._task_stack.pop()

class Group:

    def __init__(self, group_id: int, aliases: List[str]=None):
        self._group_id = group_id
        self._aliases = aliases
        self._logical_exprs = []
        self._physical_exprs = []
        self._winner_exprs: Dict[Property, Winner] = {}
        self._is_explored = False

    @property
    def group_id(self):
        return self._group_id

    @property
    def aliases(self):
        return self._aliases

    @property
    def logical_exprs(self):
        return self._logical_exprs

    @property
    def physical_exprs(self):
        return self._physical_exprs

    def is_explored(self):
        return self._is_explored

    def mark_explored(self):
        self._is_explored = True

    def __str__(self) -> str:
        return '%s(%s)' % (type(self).__name__, ', '.join(('%s=%s' % item for item in vars(self).items())))

    def add_expr(self, expr: GroupExpression):
        if expr.group_id == UNDEFINED_GROUP_ID:
            expr.group_id = self.group_id
        if expr.group_id != self.group_id:
            logger.error('Expected group id {}, found {}'.format(self.group_id, expr.group_id))
            return
        if expr.opr.is_logical():
            self._add_logical_expr(expr)
        else:
            self._add_physical_expr(expr)

    def get_best_expr(self, property: Property) -> GroupExpression:
        winner = self._winner_exprs.get(property, None)
        if winner:
            return winner.grp_expr
        else:
            return None

    def get_best_expr_cost(self, property: Property):
        winner = self._winner_exprs.get(property, None)
        if winner:
            return winner.cost
        else:
            return None

    def add_expr_cost(self, expr: GroupExpression, property, cost):
        existing_winner = self._winner_exprs.get(property, None)
        if not existing_winner or existing_winner.cost > cost:
            self._winner_exprs[property] = Winner(expr, cost)

    def clear_grp_exprs(self):
        self._logical_exprs.clear()
        self._physical_exprs.clear()

    def _add_logical_expr(self, expr: GroupExpression):
        self._logical_exprs.append(expr)

    def _add_physical_expr(self, expr: GroupExpression):
        self._physical_exprs.append(expr)

def _add_logical_expr(self, expr: GroupExpression):
    self._logical_exprs.append(expr)

def _add_physical_expr(self, expr: GroupExpression):
    self._physical_exprs.append(expr)

class Binder:

    def __init__(self, grp_expr: GroupExpression, pattern: Pattern, memo: Memo):
        self._grp_expr = grp_expr
        self._pattern = pattern
        self._memo = memo

    @staticmethod
    def _grp_binder(idx: int, pattern: Pattern, memo: Memo):
        grp = memo.groups[idx]
        for expr in grp.logical_exprs:
            yield from Binder._binder(expr, pattern, memo)

    @staticmethod
    def _binder(expr: GroupExpression, pattern: Pattern, memo: Memo):
        assert isinstance(expr, GroupExpression)
        curr_iterator = iter(())
        child_binders = []
        if pattern.opr_type is not OperatorType.DUMMY:
            curr_iterator = iter([expr.opr])
            if expr.opr.opr_type != pattern.opr_type:
                return
            if len(pattern.children) != len(expr.children):
                return
            for child_grp, pattern_child in zip(expr.children, pattern.children):
                child_binders.append(Binder._grp_binder(child_grp, pattern_child, memo))
        else:
            curr_iterator = iter([Dummy(expr.group_id, expr.opr)])
        yield from itertools.product(curr_iterator, *child_binders)

    @staticmethod
    def build_opr_tree_from_pre_order_repr(pre_order_repr: tuple) -> Operator:
        opr_tree = pre_order_repr[0]
        assert isinstance(opr_tree, Operator), f'Unknown operator encountered, expected Operator found {type(opr_tree)}'
        opr_tree = copy.copy(opr_tree)
        opr_tree.children.clear()
        if len(pre_order_repr) > 1:
            for child in pre_order_repr[1:]:
                opr_tree.append_child(Binder.build_opr_tree_from_pre_order_repr(child))
        return opr_tree

    def __iter__(self):
        for match in Binder._binder(self._grp_expr, self._pattern, self._memo):
            x = Binder.build_opr_tree_from_pre_order_repr(match)
            yield x

@staticmethod
def _binder(expr: GroupExpression, pattern: Pattern, memo: Memo):
    assert isinstance(expr, GroupExpression)
    curr_iterator = iter(())
    child_binders = []
    if pattern.opr_type is not OperatorType.DUMMY:
        curr_iterator = iter([expr.opr])
        if expr.opr.opr_type != pattern.opr_type:
            return
        if len(pattern.children) != len(expr.children):
            return
        for child_grp, pattern_child in zip(expr.children, pattern.children):
            child_binders.append(Binder._grp_binder(child_grp, pattern_child, memo))
    else:
        curr_iterator = iter([Dummy(expr.group_id, expr.opr)])
    yield from itertools.product(curr_iterator, *child_binders)

def column_definition_to_function_io(col_list: List[ColumnDefinition], is_input: bool):
    """Create the FunctionIOCatalogEntry object for each column definition provided

    Arguments:
        col_list(List[ColumnDefinition]): parsed input/output definitions
        is_input(bool): true if input else false
    """
    if isinstance(col_list, ColumnDefinition):
        col_list = [col_list]
    result_list = []
    for col in col_list:
        assert col is not None, 'Empty column definition while creating function io'
        result_list.append(FunctionIOCatalogEntry(col.name, col.type, col.cci.nullable, array_type=col.array_type, array_dimensions=col.dimension, is_input=is_input))
    return result_list

def metadata_definition_to_function_metadata(metadata_list: List[Tuple[str, str]]):
    """Create the FunctionMetadataCatalogEntry object for each metadata definition provided

    Arguments:
        col_list(List[Tuple[str, str]]): parsed metadata definitions
    """
    result_list = []
    for metadata in metadata_list:
        result_list.append(FunctionMetadataCatalogEntry(metadata[0], metadata[1]))
    return result_list

def extract_equi_join_keys(join_predicate: AbstractExpression, left_table_aliases: List[Alias], right_table_aliases: List[Alias]) -> Tuple[List[AbstractExpression], List[AbstractExpression]]:
    pred_list = to_conjunction_list(join_predicate)
    left_join_keys = []
    right_join_keys = []
    left_table_alias_strs = [left_table_alias.alias_name for left_table_alias in left_table_aliases]
    right_table_alias_strs = [right_table_alias.alias_name for right_table_alias in right_table_aliases]
    for pred in pred_list:
        if pred.etype == ExpressionType.COMPARE_EQUAL:
            left_child = pred.children[0]
            right_child = pred.children[1]
            if left_child.etype == ExpressionType.TUPLE_VALUE and right_child.etype == ExpressionType.TUPLE_VALUE:
                if left_child.table_alias in left_table_alias_strs and right_child.table_alias in right_table_alias_strs:
                    left_join_keys.append(left_child)
                    right_join_keys.append(right_child)
                elif left_child.table_alias in right_table_alias_strs and right_child.table_alias in left_table_alias_strs:
                    left_join_keys.append(right_child)
                    right_join_keys.append(left_child)
    return (left_join_keys, right_join_keys)

def extract_pushdown_predicate(predicate: AbstractExpression, column_alias: str) -> Tuple[AbstractExpression, AbstractExpression]:
    """Decompose the predicate into pushdown predicate and remaining predicate

    Args:
        predicate (AbstractExpression): predicate that needs to be decomposed
        column (str): column_alias to extract predicate
    Returns:
        Tuple[AbstractExpression, AbstractExpression]: (pushdown predicate,
        remaining predicate)
    """
    if predicate is None:
        return (None, None)
    if contains_single_column(predicate, column_alias):
        if is_simple_predicate(predicate):
            return (predicate, None)
    pushdown_preds = []
    rem_pred = []
    pred_list = to_conjunction_list(predicate)
    for pred in pred_list:
        if contains_single_column(pred, column_alias) and is_simple_predicate(pred):
            pushdown_preds.append(pred)
        else:
            rem_pred.append(pred)
    return (conjunction_list_to_expression_tree(pushdown_preds), conjunction_list_to_expression_tree(rem_pred))

def extract_pushdown_predicate_for_alias(predicate: AbstractExpression, aliases: List[Alias]):
    """Extract predicate that can be pushed down based on the input aliases.

    Atomic predicates on the table columns that are the subset of the input aliases are
    considered as candidates for pushdown.

    Args:
        predicate (AbstractExpression): input predicate
        aliases (List[str]): aliases for which predicate can be pushed
    """
    if predicate is None:
        return (None, None)
    pred_list = to_conjunction_list(predicate)
    pushdown_preds = []
    rem_pred = []
    aliases = [alias.alias_name for alias in aliases]
    for pred in pred_list:
        column_aliases = get_columns_in_predicate(pred)
        table_aliases = set([col.split('.')[0] for col in column_aliases])
        if table_aliases.issubset(set(aliases)):
            pushdown_preds.append(pred)
        else:
            rem_pred.append(pred)
    return (conjunction_list_to_expression_tree(pushdown_preds), conjunction_list_to_expression_tree(rem_pred))

class Pattern:

    def __init__(self, opr_type: OperatorType):
        self._opr_type = opr_type
        self._children = []

    def append_child(self, child: Pattern):
        self._children.append(child)

    @property
    def children(self):
        return self._children

    @property
    def opr_type(self):
        return self._opr_type

def append_child(self, child: Pattern):
    self._children.append(child)

class AbstractExecutor(ABC):
    """
    An abstract class for the executor engine
    Arguments:
        node (AbstractPlan): Plan node corresponding to this executor
    """

    def __init__(self, db: EvaDBDatabase, node: AbstractPlan):
        self._db = db
        self._node = node
        self._children = []

    def catalog(self) -> 'CatalogManager':
        """The object is intentionally generated on demand to prevent serialization issues. Having a SQLAlchemy object as a member variable can cause problems with multiprocessing. See get_catalog_instance()"""
        return self._db.catalog() if self._db else None

    def append_child(self, child: AbstractExecutor):
        """
        appends a child executor node

        Arguments:
            child {AbstractExecutor} -- child node
        """
        self._children.append(child)

    @property
    def children(self) -> List[AbstractExecutor]:
        """
        Returns the list of child executor
        Returns:
            [] -- list of children
        """
        return self._children

    @children.setter
    def children(self, children):
        self._children = children

    @property
    def node(self) -> AbstractPlan:
        return self._node

    @property
    def db(self) -> EvaDBDatabase:
        return self._db

    @abstractmethod
    def exec(self, *args, **kwargs) -> Iterable[Batch]:
        """
        This method is implemented by every executor.
        Contains logic for that executor;
        For retrieval based executor : It fetches frame batches from
        child nodes and emits it to parent node.
        """

    def __call__(self, *args, **kwargs) -> Generator[Batch, None, None]:
        yield from self.exec(*args, **kwargs)

    def bfs(self):
        """Returns a generator which visits all nodes in execution tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            for child in node.children:
                queue.append(child)

    def find_all(self, execution_type: Any):
        """Returns a generator which visits all the nodes in execution tree and yields one that matches the passed `execution_type`.

        Args:
            execution_type (Any): execution type to match with

        Returns:
            the generator object.
        """
        for node in self.bfs():
            if isinstance(node, execution_type):
                yield node

def append_child(self, child: AbstractExecutor):
    """
        appends a child executor node

        Arguments:
            child {AbstractExecutor} -- child node
        """
    self._children.append(child)

def bfs(self):
    """Returns a generator which visits all nodes in execution tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
    queue = deque([self])
    while queue:
        node = queue.popleft()
        yield node
        for child in node.children:
            queue.append(child)

def get_row_num_column_alias(column_list):
    for column in column_list:
        alias, col_name = column.split('.')
        if col_name == ROW_NUM_COLUMN:
            return alias

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

def extract_sort_types(self):
    """extracts the sort type for the column"""
    sort_type_bools = []
    for st in self._sort_types:
        if st is ParserOrderBySortType.ASC:
            sort_type_bools.append(True)
        else:
            sort_type_bools.append(False)
    return sort_type_bools

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

def is_ludwig_available() -> bool:
    try:
        try_to_import_ludwig()
        return True
    except ValueError:
        return False

def is_forecast_available() -> bool:
    try:
        try_to_import_statsforecast()
        try_to_import_neuralforecast()
        return True
    except ValueError:
        return False

def is_flaml_automl_available() -> bool:
    try:
        try_to_import_flaml_automl()
        return True
    except ValueError:
        return False

def create_table_catalog_entry_for_data_source(table_name: str, database_name: str, column_info: pd.DataFrame):
    column_name_list = list(column_info['name'])
    column_type_list = [ColumnType.python_type_to_evadb_type(dtype) for dtype in list(column_info['dtype'])]
    column_list = []
    for name, dtype in zip(column_name_list, column_type_list):
        column_list.append(ColumnCatalogEntry(name.lower(), dtype))
    table_catalog_entry = TableCatalogEntry(name=table_name, file_url=None, table_type=TableType.NATIVE_DATA, columns=column_list, database_name=database_name)
    return table_catalog_entry

def get_column_definition_from_select_target_list(target_list: List[AbstractExpression]) -> List[ColumnDefinition]:
    """
    This function is used by CREATE TABLE AS (SELECT...) and
    CREATE FUNCTION FROM (SELECT ...) to get the output objs from the
    child SELECT statement.
    """
    binded_col_list = []
    for expr in target_list:
        output_objs = [(expr.name, expr.col_object)] if expr.etype == ExpressionType.TUPLE_VALUE else zip(expr.projection_columns, expr.output_objs)
        for col_name, output_obj in output_objs:
            binded_col_list.append(ColumnDefinition(col_name.lower(), output_obj.type, output_obj.array_type, output_obj.array_dimensions))
    return binded_col_list

def drop_row_id_from_target_list(target_list: List[AbstractExpression]) -> List[AbstractExpression]:
    """
    This function is intended to be used by CREATE FUNCTION FROM (SELECT * FROM ...) and CREATE TABLE AS SELECT * FROM ... to exclude the row_id column.
    """
    filtered_list = []
    for expr in target_list:
        if isinstance(expr, TupleValueExpression):
            if expr.name == IDENTIFIER_COLUMN:
                continue
        filtered_list.append(expr)
    return filtered_list

def get_bound_func_expr_outputs_as_tuple_value_expr(func_expr: FunctionExpression):
    output_cols = []
    for obj, alias in zip(func_expr.output_objs, func_expr.alias.col_names):
        col_alias = '{}.{}'.format(func_expr.alias.alias_name, alias)
        alias_obj = TupleValueExpression(name=alias, table_alias=func_expr.alias.alias_name, col_object=obj, col_alias=col_alias)
        output_cols.append(alias_obj)
    return output_cols

def bind_func_expr(binder: StatementBinder, node: FunctionExpression):
    gpus_ids = binder._catalog().get_configuration_catalog_value('gpu_ids')
    node._context = Context(gpus_ids)
    if node.name.upper() == str(FunctionType.EXTRACT_OBJECT):
        handle_bind_extract_object_function(node, binder)
        return
    if len(node.children) == 1 and isinstance(node.children[0], TupleValueExpression) and (node.children[0].name == '*'):
        node.children = extend_star(binder._binder_context)
    for child in node.children:
        binder.bind(child)
    function_obj = binder._catalog().get_function_catalog_entry_by_name(node.name)
    if function_obj is None:
        err_msg = f"Function '{node.name}' does not exist in the catalog. Please create the function using CREATE FUNCTION command."
        logger.error(err_msg)
        raise BinderError(err_msg)
    if string_comparison_case_insensitive(function_obj.type, 'HuggingFace'):
        node.function = assign_hf_function(function_obj)
    elif string_comparison_case_insensitive(function_obj.type, 'Ludwig'):
        function_class = load_function_class_from_file(function_obj.impl_file_path, 'GenericLudwigModel')
        function_metadata = get_metadata_properties(function_obj)
        assert 'model_path' in function_metadata, "Ludwig models expect 'model_path'."
        node.function = lambda: function_class(model_path=function_metadata['model_path'])
    else:
        if function_obj.type == 'ultralytics':
            function_dir = Path(EvaDB_INSTALLATION_DIR) / 'functions'
            function_obj.impl_file_path = Path(f'{function_dir}/yolo_object_detector.py').absolute().as_posix()
        try:
            function_class = load_function_class_from_file(function_obj.impl_file_path, function_obj.name)
            properties = get_metadata_properties(function_obj)
            if string_comparison_case_insensitive(node.name, 'CHATGPT'):
                if 'OPENAI_API_KEY' not in properties.keys():
                    openai_key = binder._catalog().get_configuration_catalog_value('OPENAI_API_KEY')
                    properties['openai_api_key'] = openai_key
            node.function = lambda: function_class(**properties)
        except Exception as e:
            err_msg = f'{str(e)}. Please verify that the function class name in the implementation file matches the function name.'
            logger.error(err_msg)
            raise BinderError(err_msg)
    node.function_obj = function_obj
    output_objs = binder._catalog().get_function_io_catalog_output_entries(function_obj)
    if node.output:
        for obj in output_objs:
            if obj.name.lower() == node.output:
                node.output_objs = [obj]
        if not node.output_objs:
            err_msg = f'Output {node.output} does not exist for {function_obj.name}.'
            logger.error(err_msg)
            raise BinderError(err_msg)
        node.projection_columns = [node.output]
    else:
        node.output_objs = output_objs
        node.projection_columns = [obj.name.lower() for obj in output_objs]
    resolve_alias_table_value_expression(node)

def to_conjunction_list(expression_tree: AbstractExpression) -> List[AbstractExpression]:
    """Convert expression tree to list of conjunctives

    Note: It does not normalize the expression tree before extracting the conjunctives.

    Args:
        expression_tree (AbstractExpression): expression tree to transform

    Returns:
        List[AbstractExpression]: list of conjunctives

    Example:
        to_conjunction_list(AND(AND(a,b), OR(c,d))): [a, b, OR(c,d)]
        to_conjunction_list(OR(AND(a,b), c)): [OR(AND(a,b), c)]
            returns the original expression, does not normalize
    """
    expression_list = []
    if expression_tree.etype == ExpressionType.LOGICAL_AND:
        expression_list.extend(to_conjunction_list(expression_tree.children[0]))
        expression_list.extend(to_conjunction_list(expression_tree.children[1]))
    else:
        expression_list.append(expression_tree)
    return expression_list

def _has_simple_expressions(expr):
    simple = type(expr) in simple_expressions
    for child in expr.children:
        simple = simple and _has_simple_expressions(child)
    return simple

def is_simple_predicate(predicate: AbstractExpression) -> bool:
    """Checks if conditions in the predicate are on a single column and
        only contains LogicalExpression, ComparisonExpression,
        TupleValueExpression or ConstantValueExpression

    Args:
        predicate (AbstractExpression): predicate expression to check

    Returns:
        bool: True, if it is a simple predicate, else False
    """

    def _has_simple_expressions(expr):
        simple = type(expr) in simple_expressions
        for child in expr.children:
            simple = simple and _has_simple_expressions(child)
        return simple
    simple_expressions = [LogicalExpression, ComparisonExpression, TupleValueExpression, ConstantValueExpression]
    return _has_simple_expressions(predicate) and contains_single_column(predicate)

class AbstractExpression(ABC):

    def __init__(self, exp_type: ExpressionType, rtype: ExpressionReturnType=ExpressionReturnType.INVALID, children=None):
        self._etype = exp_type
        self._rtype = rtype
        self._children = children or []

    def get_child(self, index: int):
        assert self._children is not None
        assert index >= 0 and index < len(self._children)
        return self._children[index]

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        self._children = children

    def append_child(self, child):
        self._children.append(child)

    def get_children_count(self) -> int:
        return len(self._children)

    @property
    def etype(self) -> ExpressionType:
        return self._etype

    @property
    def rtype(self) -> ExpressionReturnType:
        return self._rtype

    @abstractmethod
    def evaluate(self, *args, **kwargs):
        pass

    def __eq__(self, other):
        is_subtree_equal = True
        if not isinstance(other, AbstractExpression):
            return False
        if self.get_children_count() != other.get_children_count():
            return False
        for child1, child2 in zip(self.children, other.children):
            is_subtree_equal = is_subtree_equal and child1 == child2
        return is_subtree_equal

    def __hash__(self) -> int:
        return hash((self.etype, self.rtype, tuple(self.children)))

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def copy(self):
        """Returns a deepcopy of the expression tree."""
        return deepcopy(self)

    def walk(self, bfs=True):
        """
        Returns a generator which visits all nodes in expression tree.

        Args:
            bfs (bool): if True, use breadth-first search (BFS) traversal order;
                if False, use the depth-first search (DFS) traversal order

        Returns:
            the generator object.
        """
        if bfs:
            yield from self.bfs()
        else:
            yield from self.dfs()

    def bfs(self):
        """Returns a generator which visits all nodes in expression tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            for child in node.children:
                queue.append(child)

    def dfs(self):
        """Returns a generator which visits all nodes in expression tree in depth-first
        search (DFS) traversal order.

        Returns:
            the generator object.
        """
        yield self
        for child in self.children:
            yield from child.dfs()

    def find_all(self, expression_type: Any):
        """Returns a generator which visits all the nodes in expression tree and yields one that matches the passed `expression_type`.

        Args:
            expression_type (Any): expression type to match with

        Returns:
            the generator object.
        """
        for node in self.bfs():
            if isinstance(node, expression_type):
                yield node

def append_child(self, child):
    self._children.append(child)

def bfs(self):
    """Returns a generator which visits all nodes in expression tree in
        breadth-first search (BFS) traversal order.

        Returns:
            the generator object.
        """
    queue = deque([self])
    while queue:
        node = queue.popleft()
        yield node
        for child in node.children:
            queue.append(child)

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

@property
def col_alias(self):
    col_alias_list = []
    if self.alias is not None:
        for col in self.alias.col_names:
            col_alias_list.append('{}.{}'.format(self.alias.alias_name, col))
    return col_alias_list

def get_table_primary_columns(table_catalog_obj: TableCatalogEntry) -> List[ColumnDefinition]:
    """
    Get the primary columns for a table based on its table type.

    Args:
        table_catalog_obj (TableCatalogEntry): The table catalog object.

    Returns:
        List[ColumnDefinition]: The list of primary columns for the table.
    """
    primary_columns = [ColumnDefinition(IDENTIFIER_COLUMN, ColumnType.INTEGER, None, None)]
    if table_catalog_obj.table_type == TableType.VIDEO_DATA:
        primary_columns.append(ColumnDefinition(VideoColumnName.id.name, ColumnType.INTEGER, None, None))
    elif table_catalog_obj.table_type == TableType.PDF_DATA:
        primary_columns.append(ColumnDefinition(PDFColumnName.paragraph.name, ColumnType.INTEGER, None, None))
    elif table_catalog_obj.table_type == TableType.DOCUMENT_DATA:
        primary_columns.append(ColumnDefinition(DocumentColumnName.chunk_id.name, ColumnType.INTEGER, None, None))
    return primary_columns

def xform_column_definitions_to_catalog_entries(col_list: List[ColumnDefinition]) -> List[ColumnCatalogEntry]:
    """Create column catalog entries for the input parsed column list.

    Arguments:
        col_list {List[ColumnDefinition]} -- parsed col list to be created
    """
    result_list = []
    for col in col_list:
        column_entry = ColumnCatalogEntry(name=col.name, type=col.type, array_type=col.array_type, array_dimensions=col.dimension, is_nullable=col.cci.nullable)
        result_list.append(column_entry)
    return result_list

def construct_function_cache_catalog_entry(func_expr: FunctionExpression, cache_dir: str) -> FunctionCacheCatalogEntry:
    """Constructs a function cache catalog entry from a given function expression.
    It is assumed that the function expression has already been bound using the binder.
    The catalog entry is populated with dependent functions and columns by traversing the
    expression tree. The cache name is represented by the signature of the function
    expression.
    Args:
        func_expr (FunctionExpression): the function expression with which the cache is associated
        cache_dir (str): path to store the cache
    Returns:
        FunctionCacheCatalogEntry: the function cache catalog entry
    """
    function_depends = []
    col_depends = []
    for expr in func_expr.find_all(FunctionExpression):
        function_depends.append(expr.function_obj.row_id)
    for expr in func_expr.find_all(TupleValueExpression):
        col_depends.append(expr.col_object.row_id)
    cache_name = func_expr.signature()
    path = str(get_str_hash(cache_name + uuid.uuid4().hex))
    cache_path = str(Path(cache_dir) / Path(f'{path}_{func_expr.name}'))
    args = tuple([arg.signature() for arg in func_expr.children])
    entry = FunctionCacheCatalogEntry(name=func_expr.signature(), function_id=func_expr.function_obj.row_id, cache_path=cache_path, args=args, function_depends=function_depends, col_depends=col_depends)
    return entry

class FunctionIOCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(FunctionIOCatalog, db_session)

    def get_input_entries_by_function_id(self, function_id: int) -> List[FunctionIOCatalogEntry]:
        try:
            result = self.session.execute(select(self.model).filter(self.model._function_id == function_id, self.model._is_input == True)).scalars().all()
            return [obj.as_dataclass() for obj in result]
        except Exception as e:
            error = f'Getting inputs for function id {function_id} raised {e}'
            logger.error(error)
            raise RuntimeError(error)

    def get_output_entries_by_function_id(self, function_id: int) -> List[FunctionIOCatalogEntry]:
        try:
            result = self.session.execute(select(self.model).filter(self.model._function_id == function_id, self.model._is_input == False)).scalars().all()
            return [obj.as_dataclass() for obj in result]
        except Exception as e:
            error = f'Getting outputs for function id {function_id} raised {e}'
            logger.error(error)
            raise RuntimeError(error)

    def create_entries(self, io_list: List[FunctionIOCatalogEntry]):
        io_objs = []
        for io in io_list:
            io_obj = FunctionIOCatalog(name=io.name, type=io.type, is_nullable=io.is_nullable, array_type=io.array_type, array_dimensions=io.array_dimensions, is_input=io.is_input, function_id=io.function_id)
            io_objs.append(io_obj)
        return io_objs

def create_entries(self, io_list: List[FunctionIOCatalogEntry]):
    io_objs = []
    for io in io_list:
        io_obj = FunctionIOCatalog(name=io.name, type=io.type, is_nullable=io.is_nullable, array_type=io.array_type, array_dimensions=io.array_dimensions, is_input=io.is_input, function_id=io.function_id)
        io_objs.append(io_obj)
    return io_objs

class FunctionMetadataCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(FunctionMetadataCatalog, db_session)

    def create_entries(self, entries: List[FunctionMetadataCatalogEntry]):
        metadata_objs = []
        try:
            for entry in entries:
                metadata_obj = FunctionMetadataCatalog(key=entry.key, value=entry.value, function_id=entry.function_id)
                metadata_objs.append(metadata_obj)
            return metadata_objs
        except Exception as e:
            raise CatalogError(e)

    def get_entries_by_function_id(self, function_id: int) -> List[FunctionMetadataCatalogEntry]:
        try:
            result = self.session.execute(select(self.model).filter(self.model._function_id == function_id)).scalars().all()
            return [obj.as_dataclass() for obj in result]
        except Exception as e:
            error = f'Getting metadata entries for function id {function_id} raised {e}'
            logger.error(error)
            raise CatalogError(error)

def create_entries(self, entries: List[FunctionMetadataCatalogEntry]):
    metadata_objs = []
    try:
        for entry in entries:
            metadata_obj = FunctionMetadataCatalog(key=entry.key, value=entry.value, function_id=entry.function_id)
            metadata_objs.append(metadata_obj)
        return metadata_objs
    except Exception as e:
        raise CatalogError(e)

class FunctionMetadataCatalog(BaseModel):
    """
    The `FunctionMetadataCatalog` catalog stores information about the metadata of user-defined functions (Functions).
    Metadata is implemented a key-value pair that can be used to store additional information about the Function.
    It maintains the following information for each attribute:
        `_row_id:` an autogenerated identifier
        `_key: ` key/identifier of the metadata (as a string)
        `_value:` value of the metadata (as a string)
        `_function_id:` the `_row_id` of the `FunctionCatalog` entry to which the attribute belongs
    """
    __tablename__ = 'function_metadata_catalog'
    _key = Column('key', String(100))
    _value = Column('value', TextPickleType())
    _function_id = Column('function_id', Integer, ForeignKey('function_catalog._row_id'))
    __table_args__ = (UniqueConstraint('key', 'function_id'), {})
    _function = relationship('FunctionCatalog', back_populates='_metadata')

    def __init__(self, key: str, value: str, function_id: int):
        self._key = key
        self._value = value
        self._function_id = function_id

    def as_dataclass(self) -> 'FunctionMetadataCatalogEntry':
        return FunctionMetadataCatalogEntry(row_id=self._row_id, key=self._key, value=self._value, function_id=self._function_id, function_name=self._function._name)

def as_dataclass(self) -> 'FunctionMetadataCatalogEntry':
    return FunctionMetadataCatalogEntry(row_id=self._row_id, key=self._key, value=self._value, function_id=self._function_id, function_name=self._function._name)

class ColumnCatalog(BaseModel):
    """The `ColumnCatalog` catalog stores information about the columns of the table.
    It maintains the following information for each column
    `_row_id:` an autogenerated identifier
    `_name: ` name of the column
    `_type:` the type of the column, refer `ColumnType`
    `_is_nullable:` which indicates whether the column is nullable
    `_array_type:` the type of array, as specified in `NdArrayType` (or `None` if the column is a primitive type)
    `_array_dimensions:` the dimensions of the array (if `_array_type` is not `None`)
    `_table_id:` the `_row_id` of the `TableCatalog` entry to which the column belongs
    `_dep_caches`: list of function caches associated with the column
    """
    __tablename__ = 'column_catalog'
    _name = Column('name', String(100))
    _type = Column('type', Enum(ColumnType), default=Enum)
    _is_nullable = Column('is_nullable', Boolean, default=False)
    _array_type = Column('array_type', Enum(NdArrayType), nullable=True)
    _array_dimensions = Column('array_dimensions', String(100))
    _table_id = Column('table_id', Integer, ForeignKey('table_catalog._row_id'))
    __table_args__ = (UniqueConstraint('name', 'table_id'), {})
    _table_catalog = relationship('TableCatalog', back_populates='_columns')
    _dep_caches = relationship('FunctionCacheCatalog', secondary=depend_column_and_function_cache, back_populates='_col_depends', cascade='all, delete')
    _index_column = relationship('IndexCatalog', back_populates='_feat_column', cascade='all, delete')

    def __init__(self, name: str, type: ColumnType, is_nullable: bool=False, array_type: NdArrayType=None, array_dimensions: Tuple[int]=(), table_id: int=None):
        self._name = name
        self._type = type
        self._is_nullable = is_nullable
        self._array_type = array_type
        self.array_dimensions = array_dimensions
        self._table_id = table_id

    @property
    def array_dimensions(self):
        return literal_eval(self._array_dimensions)

    @array_dimensions.setter
    def array_dimensions(self, value: Tuple[int]):
        dimensions = []
        for dim in value:
            if dim == Dimension.ANYDIM:
                dimensions.append(None)
            else:
                dimensions.append(dim)
        self._array_dimensions = str(tuple(dimensions))

    def as_dataclass(self) -> 'ColumnCatalogEntry':
        return ColumnCatalogEntry(row_id=self._row_id, name=self._name, type=self._type, is_nullable=self._is_nullable, array_type=self._array_type, array_dimensions=self.array_dimensions, table_id=self._table_id, table_name=self._table_catalog._name, dep_caches=[cache.as_dataclass() for cache in self._dep_caches])

@array_dimensions.setter
def array_dimensions(self, value: Tuple[int]):
    dimensions = []
    for dim in value:
        if dim == Dimension.ANYDIM:
            dimensions.append(None)
        else:
            dimensions.append(dim)
    self._array_dimensions = str(tuple(dimensions))

class FunctionCacheCatalog(BaseModel):
    """The `FunctionCacheCatalog` catalog stores information about the function cache.

    It maintains the following information for each cache entry:
    `_row_id:` An autogenerated identifier for the cache entry.
    `_name:` The name of the cache, also referred to as the unique function signature.
    `_function_id:` `_row_id` of the function in the `FunctionCatalog` for which the cache is built.
    `_args:` A serialized list of `ColumnCatalog` `_row_id`s for each argument of the
    Function. If the argument is a function expression, it stores the string representation
    of the expression tree.
    """
    __tablename__ = 'function_cache'
    _name = Column('name', String(128))
    _function_id = Column('function_id', Integer, ForeignKey('function_catalog._row_id', ondelete='CASCADE'))
    _cache_path = Column('cache_path', String(256))
    _args = Column('args', String(1024))
    __table_args__ = (UniqueConstraint('name', 'function_id'), {})
    _col_depends = relationship('ColumnCatalog', secondary=depend_column_and_function_cache, back_populates='_dep_caches')
    _function_depends = relationship('FunctionCatalog', secondary=depend_function_and_function_cache, back_populates='_dep_caches')

    def __init__(self, name: str, function_id: int, cache_path: str, args: Tuple[str]):
        self._name = name
        self._function_id = function_id
        self._cache_path = cache_path
        self._args = str(args)

    def as_dataclass(self) -> 'FunctionCacheCatalogEntry':
        function_depends = [obj._row_id for obj in self._function_depends]
        col_depends = [obj._row_id for obj in self._col_depends]
        return FunctionCacheCatalogEntry(row_id=self._row_id, name=self._name, function_id=self._function_id, cache_path=self._cache_path, args=literal_eval(self._args), function_depends=function_depends, col_depends=col_depends)

def as_dataclass(self) -> 'FunctionCacheCatalogEntry':
    function_depends = [obj._row_id for obj in self._function_depends]
    col_depends = [obj._row_id for obj in self._col_depends]
    return FunctionCacheCatalogEntry(row_id=self._row_id, name=self._name, function_id=self._function_id, cache_path=self._cache_path, args=literal_eval(self._args), function_depends=function_depends, col_depends=col_depends)

class FunctionIOCatalog(BaseModel):
    """The `FunctionIOCatalog` catalog stores information about the input and output
    attributes of user-defined functions (Functions). It maintains the following information
    for each attribute:
    `_row_id:` an autogenerated identifier
    `_name: ` name of the input/output argument
    `_type:` the type of the argument, refer `ColumnType`
    `_is_nullable:` which indicates whether it is nullable
    `_array_type:` the type of array, as specified in `NdArrayType` (or `None` if the attribute is a primitive type)
    `_array_dimensions:` the dimensions of the array (if `_array_type` is not `None`)
    `_function_id:` the `_row_id` of the `FunctionCatalog` entry to which the attribute belongs
    """
    __tablename__ = 'functionio_catalog'
    _name = Column('name', String(100))
    _type = Column('type', Enum(ColumnType), default=Enum)
    _is_nullable = Column('is_nullable', Boolean, default=False)
    _array_type = Column('array_type', Enum(NdArrayType), nullable=True)
    _array_dimensions = Column('array_dimensions', String(100))
    _is_input = Column('is_input', Boolean, default=True)
    _function_id = Column('function_id', Integer, ForeignKey('function_catalog._row_id'))
    __table_args__ = (UniqueConstraint('name', 'function_id'), {})
    _function = relationship('FunctionCatalog', back_populates='_attributes')

    def __init__(self, name: str, type: ColumnType, is_nullable: bool=False, array_type: NdArrayType=None, array_dimensions: Tuple[int]=None, is_input: bool=True, function_id: int=None):
        self._name = name
        self._type = type
        self._is_nullable = is_nullable
        self._array_type = array_type
        self.array_dimensions = array_dimensions or str(())
        self._is_input = is_input
        self._function_id = function_id

    @property
    def array_dimensions(self):
        return literal_eval(self._array_dimensions)

    @array_dimensions.setter
    def array_dimensions(self, value: Tuple[int]):
        if not isinstance(value, tuple):
            self._array_dimensions = str(value)
        else:
            dimensions = []
            for dim in value:
                if dim == Dimension.ANYDIM:
                    dimensions.append(None)
                else:
                    dimensions.append(dim)
            self._array_dimensions = str(tuple(dimensions))

    def as_dataclass(self) -> 'FunctionIOCatalogEntry':
        return FunctionIOCatalogEntry(row_id=self._row_id, name=self._name, type=self._type, is_nullable=self._is_nullable, array_type=self._array_type, array_dimensions=self.array_dimensions, is_input=self._is_input, function_id=self._function_id, function_name=self._function._name)

@array_dimensions.setter
def array_dimensions(self, value: Tuple[int]):
    if not isinstance(value, tuple):
        self._array_dimensions = str(value)
    else:
        dimensions = []
        for dim in value:
            if dim == Dimension.ANYDIM:
                dimensions.append(None)
            else:
                dimensions.append(dim)
        self._array_dimensions = str(tuple(dimensions))

def as_dataclass(self) -> 'FunctionIOCatalogEntry':
    return FunctionIOCatalogEntry(row_id=self._row_id, name=self._name, type=self._type, is_nullable=self._is_nullable, array_type=self._array_type, array_dimensions=self.array_dimensions, is_input=self._is_input, function_id=self._function_id, function_name=self._function._name)

class Functions:

    def function(self, tree):
        function_name = None
        function_output = None
        function_args = []
        for child in tree.children:
            if isinstance(child, Token):
                if child.value == '*':
                    function_args = [TupleValueExpression(name='*')]
            if isinstance(child, Tree):
                if child.data == 'simple_id':
                    function_name = self.visit(child)
                elif child.data == 'dotted_id':
                    function_output = self.visit(child)
                elif child.data == 'function_args':
                    function_args = self.visit(child)
        func_expr = FunctionExpression(None, name=function_name, output=function_output)
        for arg in function_args:
            func_expr.append_child(arg)
        return func_expr

    def function_args(self, tree):
        args = []
        for child in tree.children:
            if isinstance(child, Tree):
                args.append(self.visit(child))
        return args

    def create_function(self, tree):
        function_name = None
        or_replace = False
        if_not_exists = False
        input_definitions = []
        output_definitions = []
        impl_path = None
        function_type = None
        query = None
        metadata = []
        create_definitions_index = 0
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'function_name':
                    function_name = self.visit(child)
                elif child.data == 'or_replace':
                    or_replace = True
                elif child.data == 'if_not_exists':
                    if_not_exists = True
                elif child.data == 'create_definitions':
                    if create_definitions_index == 0:
                        input_definitions = self.visit(child)
                        create_definitions_index += 1
                    elif create_definitions_index == 1:
                        output_definitions = self.visit(child)
                elif child.data == 'function_type':
                    function_type = self.visit(child)
                elif child.data == 'function_impl':
                    impl_path = self.visit(child).value
                elif child.data == 'simple_select':
                    query = self.visit(child)
                elif child.data == 'function_metadata':
                    key_value_pair = self.visit(child)
                    value = key_value_pair[1]
                    if isinstance(value, ConstantValueExpression):
                        value = value.value
                    (metadata.append((key_value_pair[0].lower(), value)),)
        return CreateFunctionStatement(function_name, or_replace, if_not_exists, impl_path, input_definitions, output_definitions, function_type, query, metadata)

    def get_aggregate_function_type(self, agg_func_name):
        agg_func_type = None
        if agg_func_name == 'COUNT':
            agg_func_type = ExpressionType.AGGREGATION_COUNT
        elif agg_func_name == 'MIN':
            agg_func_type = ExpressionType.AGGREGATION_MIN
        elif agg_func_name == 'MAX':
            agg_func_type = ExpressionType.AGGREGATION_MAX
        elif agg_func_name == 'SUM':
            agg_func_type = ExpressionType.AGGREGATION_SUM
        elif agg_func_name == 'AVG':
            agg_func_type = ExpressionType.AGGREGATION_AVG
        elif agg_func_name == 'FIRST':
            agg_func_type = ExpressionType.AGGREGATION_FIRST
        elif agg_func_name == 'LAST':
            agg_func_type = ExpressionType.AGGREGATION_LAST
        elif agg_func_name == 'SEGMENT':
            agg_func_type = ExpressionType.AGGREGATION_SEGMENT
        return agg_func_type

    def aggregate_windowed_function(self, tree):
        agg_func_arg = None
        agg_func_name = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'function_arg':
                    agg_func_arg = self.visit(child)
                elif child.data == 'aggregate_function_name':
                    agg_func_name = self.visit(child).value
            elif isinstance(child, Token):
                token = child.value
                if token != '*':
                    agg_func_name = token
                elif token == '*':
                    agg_func_arg = TupleValueExpression(name='_row_id')
                else:
                    agg_func_arg = TupleValueExpression(name='id')
        agg_func_type = self.get_aggregate_function_type(agg_func_name)
        agg_expr = AggregationExpression(agg_func_type, None, agg_func_arg)
        return agg_expr

def function_args(self, tree):
    args = []
    for child in tree.children:
        if isinstance(child, Tree):
            args.append(self.visit(child))
    return args

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

def expressions_with_defaults(self, tree):
    expr_list = []
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'expression_or_default':
                expression = self.visit(child)
                expr_list.append(expression)
    return expr_list

class TableSources:

    def select_elements(self, tree):
        kind = tree.children[0]
        if kind == '*':
            select_list = [TupleValueExpression(name='*')]
        else:
            select_list = []
            for child in tree.children:
                element = self.visit(child)
                select_list.append(element)
        return select_list

    def table_sources(self, tree):
        return self.visit(tree.children[0])

    def table_source(self, tree):
        left_node = None
        join_nodes = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_source_item_with_param':
                    left_node = self.visit(child)
                    join_nodes = [left_node]
                elif child.data.endswith('join'):
                    table = self.visit(child)
                    join_nodes.append(table)
        num_table_joins = len(join_nodes)
        if num_table_joins > 1:
            for i in range(num_table_joins - 1):
                join_nodes[i + 1].join_node.left = join_nodes[i]
            return join_nodes[-1]
        else:
            return join_nodes[0]

    def table_source_item_with_param(self, tree):
        sample_freq = None
        sample_type = None
        alias = None
        table = None
        chunk_params = {}
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_source_item':
                    table = self.visit(child)
                elif child.data == 'sample_params':
                    sample_type, sample_freq = self.visit(child)
                elif child.data == 'chunk_params':
                    chunk_params = self.visit(child)
                elif child.data == 'alias_clause':
                    alias = self.visit(child)
        return TableRef(table=table, alias=alias, sample_freq=sample_freq, sample_type=sample_type, chunk_params=chunk_params)

    def table_source_item(self, tree):
        return self.visit(tree.children[0])

    def query_specification(self, tree):
        target_list = None
        from_clause = None
        where_clause = None
        groupby_clause = None
        orderby_clause = None
        limit_count = None
        for child in tree.children[1:]:
            try:
                if child.data == 'select_elements':
                    target_list = self.visit(child)
                elif child.data == 'from_clause':
                    clause = self.visit(child)
                    from_clause = clause.get('from', None)
                    where_clause = clause.get('where', None)
                    groupby_clause = clause.get('groupby', None)
                elif child.data == 'order_by_clause':
                    orderby_clause = self.visit(child)
                elif child.data == 'limit_clause':
                    limit_count = self.visit(child)
            except BaseException as e:
                logger.error('Error while parsing                                 QuerySpecification')
                raise e
        select_stmt = SelectStatement(target_list, from_clause, where_clause, groupby_clause=groupby_clause, orderby_list=orderby_clause, limit_count=limit_count)
        return select_stmt

    def from_clause(self, tree):
        from_table = None
        where_clause = None
        groupby_clause = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_sources':
                    from_table = self.visit(child)
                elif child.data == 'where_expr':
                    where_clause = self.visit(child)
                elif child.data == 'group_by_item':
                    groupby_item = self.visit(child)
                    groupby_clause = groupby_item
        return {'from': from_table, 'where': where_clause, 'groupby': groupby_clause}

    def inner_join(self, tree):
        table = None
        join_predicate = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_source_item_with_param':
                    table = self.visit(child)
                elif child.data.endswith('expression'):
                    join_predicate = self.visit(child)
        return TableRef(JoinNode(None, table, predicate=join_predicate, join_type=JoinType.INNER_JOIN))

    def lateral_join(self, tree):
        tve = None
        alias = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_valued_function':
                    tve = self.visit(child)
                elif child.data == 'alias_clause':
                    alias = self.visit(child)
        if alias is None:
            err_msg = f'TableValuedFunction {tve.func_expr.name} should have alias.'
            logger.error(err_msg)
            raise SyntaxError(err_msg)
        join_type = JoinType.LATERAL_JOIN
        return TableRef(JoinNode(None, TableRef(tve, alias=alias), join_type=join_type))

    def table_valued_function(self, tree):
        func_expr = None
        has_unnest = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('function_call'):
                    func_expr = self.visit(child)
            elif child.lower() == 'unnest':
                has_unnest = True
        return TableValuedExpression(func_expr, do_unnest=has_unnest)

    def subquery_table_source_item(self, tree):
        subquery_table_source_item = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'simple_select':
                    subquery_table_source_item = self.visit(child)
        return subquery_table_source_item

    def union_select(self, tree):
        right_select_statement = None
        union_all = False
        statement_id = 0
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('select'):
                    if statement_id == 0:
                        left_select_statement = self.visit(child)
                    elif statement_id == 1:
                        right_select_statement = self.visit(child)
                    statement_id += 1
            elif isinstance(child, Token):
                if child.value == 'ALL':
                    union_all = True
        if left_select_statement is not None:
            assert left_select_statement.union_link is None, 'Checking for the correctness of the operator'
            left_select_statement.union_link = right_select_statement
            if union_all is False:
                left_select_statement.union_all = False
            else:
                left_select_statement.union_all = True
        return left_select_statement

    def group_by_item(self, tree):
        expr = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('expression'):
                    expr = self.visit(child)
        return expr

    def alias_clause(self, tree):
        alias_name = None
        column_list = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid':
                    alias_name = self.visit(child)
                elif child.data == 'uid_list':
                    column_list = self.visit(child)
                    column_list = [col.name for col in column_list]
        return Alias(alias_name, column_list)

def select_elements(self, tree):
    kind = tree.children[0]
    if kind == '*':
        select_list = [TupleValueExpression(name='*')]
    else:
        select_list = []
        for child in tree.children:
            element = self.visit(child)
            select_list.append(element)
    return select_list

class LarkInterpreter(LarkBaseInterpreter, CommonClauses, CreateTable, CreateIndex, CreateDatabase, CreateJob, Expressions, Functions, Insert, Select, TableSources, Load, RenameTable, DropObject, Show, Explain, Delete, Use, Set):

    def __init__(self, query):
        super().__init__()
        self.query = query

    def start(self, tree):
        return self.visit_children(tree)

    def sql_statement(self, tree):
        return self.visit(tree.children[0])

    def job_sql_statements(self, tree):
        sql_statements = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'query_string':
                    sql_statements.append(self.visit(child))
        return sql_statements

def job_sql_statements(self, tree):
    sql_statements = []
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'query_string':
                sql_statements.append(self.visit(child))
    return sql_statements

class CreateTable:

    def create_table(self, tree):
        table_info = None
        if_not_exists = False
        create_definitions = []
        query = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_not_exists':
                    if_not_exists = True
                elif child.data == 'table_name':
                    table_info = self.visit(child)
                elif child.data == 'create_definitions':
                    create_definitions = self.visit(child)
                elif child.data == 'simple_select':
                    query = self.visit(child)
        create_stmt = CreateTableStatement(table_info, if_not_exists, create_definitions, query=query)
        return create_stmt

    def create_definitions(self, tree):
        column_definitions = []
        for child in tree.children:
            if isinstance(child, Tree):
                create_definition = None
                if child.data == 'column_declaration':
                    create_definition = self.visit(child)
                column_definitions.append(create_definition)
        return column_definitions

    def column_declaration(self, tree):
        column_name = None
        data_type = None
        array_type = None
        dimensions = None
        column_constraint_information = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid':
                    column_name = self.visit(child)
                elif child.data == 'column_definition':
                    data_type, array_type, dimensions, column_constraint_information = self.visit(child)
        if column_name is not None:
            return ColumnDefinition(column_name, data_type, array_type, dimensions, column_constraint_information)

    def column_definition(self, tree):
        data_type = None
        array_type = None
        dimensions = None
        column_constraint_information = ColConstraintInfo()
        not_null_set = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('data_type'):
                    data_type, array_type, dimensions = self.visit(child)
                elif child.data.endswith('column_constraint'):
                    return_type = self.visit(child)
                    if return_type == ColumnConstraintEnum.UNIQUE:
                        column_constraint_information.unique = True
                        column_constraint_information.nullable = False
                        not_null_set = True
                    elif return_type == ColumnConstraintEnum.NOTNULL:
                        column_constraint_information.nullable = False
                        not_null_set = True
        if not not_null_set:
            column_constraint_information.nullable = True
        return (data_type, array_type, dimensions, column_constraint_information)

    def unique_key_column_constraint(self, tree):
        return ColumnConstraintEnum.UNIQUE

    def null_column_constraint(self, tree):
        return ColumnConstraintEnum.NOTNULL

    def simple_data_type(self, tree):
        data_type = None
        array_type = None
        dimensions = []
        token = tree.children[0]
        if str.upper(token) == 'BOOLEAN':
            data_type = ColumnType.BOOLEAN
        return (data_type, array_type, dimensions)

    def integer_data_type(self, tree):
        data_type = None
        array_type = None
        dimensions = []
        token = tree.children[0]
        if str.upper(token) == 'INTEGER':
            data_type = ColumnType.INTEGER
        return (data_type, array_type, dimensions)

    def dimension_data_type(self, tree):
        data_type = None
        array_type = None
        dimensions = []
        token = tree.children[0]
        if str.upper(token) == 'FLOAT':
            data_type = ColumnType.FLOAT
        elif str.upper(token) == 'TEXT':
            data_type = ColumnType.TEXT
        if len(tree.children) > 1:
            dimensions = self.visit(tree.children[1])
        return (data_type, array_type, dimensions)

    def array_data_type(self, tree):
        data_type = ColumnType.NDARRAY
        array_type = NdArrayType.ANYTYPE
        dimensions = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'array_type':
                    array_type = self.visit(child)
                elif child.data == 'length_dimension_list':
                    dimensions = self.visit(child)
        return (data_type, array_type, dimensions)

    def any_data_type(self, tree):
        return (ColumnType.ANY, None, [])

    def array_type(self, tree):
        array_type = None
        token = tree.children[0]
        if str.upper(token) == 'INT8':
            array_type = NdArrayType.INT8
        elif str.upper(token) == 'UINT8':
            array_type = NdArrayType.UINT8
        elif str.upper(token) == 'INT16':
            array_type = NdArrayType.INT16
        elif str.upper(token) == 'INT32':
            array_type = NdArrayType.INT32
        elif str.upper(token) == 'INT64':
            array_type = NdArrayType.INT64
        elif str.upper(token) == 'UNICODE':
            array_type = NdArrayType.UNICODE
        elif str.upper(token) == 'BOOLEAN':
            array_type = NdArrayType.BOOL
        elif str.upper(token) == 'FLOAT32':
            array_type = NdArrayType.FLOAT32
        elif str.upper(token) == 'FLOAT64':
            array_type = NdArrayType.FLOAT64
        elif str.upper(token) == 'DECIMAL':
            array_type = NdArrayType.DECIMAL
        elif str.upper(token) == 'STR':
            array_type = NdArrayType.STR
        elif str.upper(token) == 'DATETIME':
            array_type = NdArrayType.DATETIME
        elif str.upper(token) == 'ANYTYPE':
            array_type = NdArrayType.ANYTYPE
        return array_type

    def dimension_helper(self, tree):
        dimensions = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'decimal_literal':
                    decimal = self.visit(child)
                    dimensions.append(decimal)
        return tuple(dimensions)

    def length_one_dimension(self, tree):
        dimensions = self.dimension_helper(tree)
        return dimensions

    def length_two_dimension(self, tree):
        dimensions = self.dimension_helper(tree)
        return dimensions

    def length_dimension_list(self, tree):
        dimensions = self.dimension_helper(tree)
        return dimensions

def create_definitions(self, tree):
    column_definitions = []
    for child in tree.children:
        if isinstance(child, Tree):
            create_definition = None
            if child.data == 'column_declaration':
                create_definition = self.visit(child)
            column_definitions.append(create_definition)
    return column_definitions

def sample_audio():
    duration_ms, sample_rate = (1000, 16000)
    num_samples = int(duration_ms * sample_rate / 1000)
    audio_data = np.random.rand(num_samples)
    return audio_data

def io_entry_for_inputs(function_name: str, function_input: Union[str, List]):
    """
    Generates the IO Catalog Entry for the inputs to HF Functions
    Input is one of ["text", "image", "audio", "video", "multimodal"]
    """
    if isinstance(function_input, HFInputTypes):
        function_input = [function_input]
    inputs = []
    for input_type in function_input:
        array_type = NdArrayType.ANYTYPE
        if input_type == HFInputTypes.TEXT:
            array_type = NdArrayType.STR
        elif input_type == HFInputTypes.IMAGE or function_input == HFInputTypes.AUDIO:
            array_type = NdArrayType.FLOAT32
        inputs.append(FunctionIOCatalogEntry(name=f'{function_name}_{input_type}', type=ColumnType.NDARRAY, is_nullable=False, array_type=array_type, is_input=True))
    return inputs

def io_entry_for_outputs(function_outputs: Dict[str, Type]):
    """
    Generates the IO Catalog Entry for the output
    """
    outputs = []
    for col_name, col_type in function_outputs.items():
        outputs.append(FunctionIOCatalogEntry(name=col_name, type=ColumnType.NDARRAY, array_type=ptype_to_ndarray_type(col_type), is_input=False))
    return outputs

class AudioHFModel(AbstractHFFunction):
    """
    Base Model for all HF Models that take in audio as input
    """

    def input_formatter(self, inputs: Any):
        if inputs.columns.str.contains('audio').any():
            return np.concatenate(inputs.iloc[:, 0].values)
        audio = []
        files = inputs.iloc[:, 0].tolist()
        try_to_import_decord()
        import decord
        for file in files:
            reader = decord.AudioReader(file, mono=True, sample_rate=16000)
            audio.append(reader[0:].asnumpy()[0])
        return audio

def input_formatter(self, inputs: Any):
    if inputs.columns.str.contains('audio').any():
        return np.concatenate(inputs.iloc[:, 0].values)
    audio = []
    files = inputs.iloc[:, 0].tolist()
    try_to_import_decord()
    import decord
    for file in files:
        reader = decord.AudioReader(file, mono=True, sample_rate=16000)
        audio.append(reader[0:].asnumpy()[0])
    return audio

class MilvusVectorStore(VectorStore):

    def __init__(self, index_name: str, **kwargs) -> None:
        self._milvus_uri = kwargs.get('MILVUS_URI')
        if not self._milvus_uri:
            self._milvus_uri = os.environ.get('MILVUS_URI')
        assert self._milvus_uri, 'Please set your Milvus URI in evadb.yml file (third_party, MILVUS_URI) or environment variable (MILVUS_URI).'
        self._milvus_user = kwargs.get('MILVUS_USER')
        if not self._milvus_user:
            self._milvus_user = os.environ.get('MILVUS_USER', '')
        self._milvus_password = kwargs.get('MILVUS_PASSWORD')
        if not self._milvus_password:
            self._milvus_password = os.environ.get('MILVUS_PASSWORD', '')
        self._milvus_db_name = kwargs.get('MILVUS_DB_NAME')
        if not self._milvus_db_name:
            self._milvus_db_name = os.environ.get('MILVUS_DB_NAME', '')
        self._milvus_token = kwargs.get('MILVUS_TOKEN')
        if not self._milvus_token:
            self._milvus_token = os.environ.get('MILVUS_TOKEN', '')
        self._client = get_milvus_client(milvus_uri=self._milvus_uri, milvus_user=self._milvus_user, milvus_password=self._milvus_password, milvus_db_name=self._milvus_db_name, milvus_token=self._milvus_token)
        self._collection_name = index_name

    def create(self, vector_dim: int):
        if self._collection_name in self._client.list_collections():
            self._client.drop_collection(self._collection_name)
        self._client.create_collection(collection_name=self._collection_name, dimension=vector_dim, metric_type='COSINE')

    def add(self, payload: List[FeaturePayload]):
        milvus_data = [{'id': feature_payload.id, 'vector': feature_payload.embedding.reshape(-1).tolist()} for feature_payload in payload]
        ids = [feature_payload.id for feature_payload in payload]
        self._client.delete(collection_name=self._collection_name, pks=ids)
        self._client.insert(collection_name=self._collection_name, data=milvus_data)

    def persist(self):
        self._client.flush(self._collection_name)

    def delete(self) -> None:
        self._client.drop_collection(collection_name=self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.search(collection_name=self._collection_name, data=[query.embedding.reshape(-1).tolist()], limit=query.top_k)[0]
        distances, ids = ([], [])
        for result in response:
            distances.append(result['distance'])
            ids.append(result['id'])
        return VectorIndexQueryResult(distances, ids)

def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
    response = self._client.search(collection_name=self._collection_name, data=[query.embedding.reshape(-1).tolist()], limit=query.top_k)[0]
    distances, ids = ([], [])
    for result in response:
        distances.append(result['distance'])
        ids.append(result['id'])
    return VectorIndexQueryResult(distances, ids)

class PineconeVectorStore(VectorStore):

    def __init__(self, index_name: str, **kwargs) -> None:
        try_to_import_pinecone_client()
        global _pinecone_init_done
        self._index_name = index_name.strip().lower()
        self._api_key = kwargs.get('PINECONE_API_KEY')
        if not self._api_key:
            self._api_key = os.environ.get('PINECONE_API_KEY')
        assert self._api_key, 'Please set your `PINECONE_API_KEY` using set command or environment variable (PINECONE_KEY). It can be found at Pinecone Dashboard > API Keys > Value'
        self._environment = kwargs.get('PINECONE_ENV')
        if not self._environment:
            self._environment = os.environ.get('PINECONE_ENV')
        assert self._environment, 'Please set your `PINECONE_ENV` or environment variable (PINECONE_ENV). It can be found Pinecone Dashboard > API Keys > Environment.'
        if not _pinecone_init_done:
            import pinecone
            pinecone.init(api_key=self._api_key, environment=self._environment)
            _pinecone_init_done = True
        self._client = None

    def create(self, vector_dim: int):
        import pinecone
        pinecone.create_index(self._index_name, dimension=vector_dim, metric='cosine')
        logger.warning(f'Created index {self._index_name}. Please note that Pinecone is eventually consistent, hence any additions to the Vector Index may not get immediately reflected in queries.')
        self._client = pinecone.Index(self._index_name)

    def add(self, payload: List[FeaturePayload]):
        self._client.upsert(vectors=[{'id': str(row.id), 'values': row.embedding.reshape(-1).tolist()} for row in payload])

    def delete(self) -> None:
        import pinecone
        pinecone.delete_index(self._index_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        import pinecone
        if not self._client:
            self._client = pinecone.Index(self._index_name)
        response = self._client.query(top_k=query.top_k, vector=query.embedding.reshape(-1).tolist())
        distances, ids = ([], [])
        for row in response['matches']:
            distances.append(row['score'])
            ids.append(int(row['id']))
        return VectorIndexQueryResult(distances, ids)

def create(self, vector_dim: int):
    import pinecone
    pinecone.create_index(self._index_name, dimension=vector_dim, metric='cosine')
    logger.warning(f'Created index {self._index_name}. Please note that Pinecone is eventually consistent, hence any additions to the Vector Index may not get immediately reflected in queries.')
    self._client = pinecone.Index(self._index_name)

def add(self, payload: List[FeaturePayload]):
    self._client.upsert(vectors=[{'id': str(row.id), 'values': row.embedding.reshape(-1).tolist()} for row in payload])

def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
    import pinecone
    if not self._client:
        self._client = pinecone.Index(self._index_name)
    response = self._client.query(top_k=query.top_k, vector=query.embedding.reshape(-1).tolist())
    distances, ids = ([], [])
    for row in response['matches']:
        distances.append(row['score'])
        ids.append(int(row['id']))
    return VectorIndexQueryResult(distances, ids)

class ChromaDBVectorStore(VectorStore):

    def __init__(self, index_name: str, index_path: str) -> None:
        self._client = get_chromadb_client(index_path)
        self._collection_name = index_name

    def create(self, vector_dim: int):
        self._client.create_collection(name=self._collection_name, metadata={'hnsw:construction_ef': vector_dim, 'hnsw:space': 'cosine'})

    def add(self, payload: List[FeaturePayload]):
        ids = [str(row.id) for row in payload]
        embeddings = [row.embedding.reshape(-1).tolist() for row in payload]
        self._client.get_collection(self._collection_name).add(ids=ids, embeddings=embeddings)

    def delete(self) -> None:
        self._client.delete_collection(name=self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.get_collection(self._collection_name).query(query_embeddings=query.embedding.reshape(-1).tolist(), n_results=query.top_k)
        distances, ids = ([], [])
        if 'ids' in response:
            for id in response['ids'][0]:
                ids.append(int(id))
            for distance in response['distances'][0]:
                distances.append(distance)
        return VectorIndexQueryResult(distances, ids)

def add(self, payload: List[FeaturePayload]):
    ids = [str(row.id) for row in payload]
    embeddings = [row.embedding.reshape(-1).tolist() for row in payload]
    self._client.get_collection(self._collection_name).add(ids=ids, embeddings=embeddings)

def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
    response = self._client.get_collection(self._collection_name).query(query_embeddings=query.embedding.reshape(-1).tolist(), n_results=query.top_k)
    distances, ids = ([], [])
    if 'ids' in response:
        for id in response['ids'][0]:
            ids.append(int(id))
        for distance in response['distances'][0]:
            distances.append(distance)
    return VectorIndexQueryResult(distances, ids)

class QdrantVectorStore(VectorStore):

    def __init__(self, index_name: str, index_db: str) -> None:
        self._client = get_qdrant_client(index_db)
        self._collection_name = index_name

    def create(self, vector_dim: int):
        from qdrant_client.models import Distance, VectorParams
        self._client.recreate_collection(collection_name=self._collection_name, vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE))

    def add(self, payload: List[FeaturePayload]):
        from qdrant_client.models import Batch
        ids = [int(row.id) for row in payload]
        embeddings = [row.embedding.reshape(-1).tolist() for row in payload]
        self._client.upsert(collection_name=self._collection_name, points=Batch.construct(ids=ids, vectors=embeddings))

    def delete(self) -> None:
        self._client.delete_collection(collection_name=self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.search(collection_name=self._collection_name, query_vector=query.embedding.reshape(-1).tolist(), limit=query.top_k)
        distances, ids = ([], [])
        for point in response:
            distances.append(point.score)
            ids.append(int(point.id))
        return VectorIndexQueryResult(distances, ids)

def add(self, payload: List[FeaturePayload]):
    from qdrant_client.models import Batch
    ids = [int(row.id) for row in payload]
    embeddings = [row.embedding.reshape(-1).tolist() for row in payload]
    self._client.upsert(collection_name=self._collection_name, points=Batch.construct(ids=ids, vectors=embeddings))

def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
    response = self._client.search(collection_name=self._collection_name, query_vector=query.embedding.reshape(-1).tolist(), limit=query.top_k)
    distances, ids = ([], [])
    for point in response:
        distances.append(point.score)
        ids.append(int(point.id))
    return VectorIndexQueryResult(distances, ids)

class WeaviateVectorStore(VectorStore):

    def __init__(self, collection_name: str, **kwargs) -> None:
        try_to_import_weaviate_client()
        global _weaviate_init_done
        self._collection_name = collection_name
        self._api_key = kwargs.get('WEAVIATE_API_KEY')
        if not self._api_key:
            self._api_key = os.environ.get('WEAVIATE_API_KEY')
        assert self._api_key, 'Please set your `WEAVIATE_API_KEY` using set command or environment variable (WEAVIATE_API_KEY). It can be found at the Details tab in WCS Dashboard.'
        self._api_url = kwargs.get('WEAVIATE_API_URL')
        if not self._api_url:
            self._api_url = os.environ.get('WEAVIATE_API_URL')
        assert self._api_url, 'Please set your `WEAVIATE_API_URL` using set command or environment variable (WEAVIATE_API_URL). It can be found at the Details tab in WCS Dashboard.'
        if not _weaviate_init_done:
            import weaviate
            client = weaviate.Client(url=self._api_url, auth_client_secret=weaviate.AuthApiKey(api_key=self._api_key))
            client.schema.get()
            _weaviate_init_done = True
        self._client = client

    def create(self, vectorizer: str='text2vec-openai', properties: list=None, module_config: dict=None):
        properties = properties or []
        module_config = module_config or {}
        collection_obj = {'class': self._collection_name, 'properties': properties, 'vectorizer': vectorizer, 'moduleConfig': module_config}
        if self._client.schema.exists(self._collection_name):
            self._client.schema.delete_class(self._collection_name)
        self._client.schema.create_class(collection_obj)

    def add(self, payload: List[FeaturePayload]) -> None:
        with self._client.batch as batch:
            for item in payload:
                data_object = {'id': item.id, 'vector': item.embedding}
                batch.add_data_object(data_object, self._collection_name)

    def delete(self) -> None:
        self._client.schema.delete_class(self._collection_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        response = self._client.query.get(self._collection_name, ['*']).with_near_vector({'vector': query.embedding}).with_limit(query.top_k).do()
        data = response.get('data', {})
        results = data.get('Get', {}).get(self._collection_name, [])
        similarities = [item['_additional']['distance'] for item in results]
        ids = [item['id'] for item in results]
        return VectorIndexQueryResult(similarities, ids)

def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
    response = self._client.query.get(self._collection_name, ['*']).with_near_vector({'vector': query.embedding}).with_limit(query.top_k).do()
    data = response.get('data', {})
    results = data.get('Get', {}).get(self._collection_name, [])
    similarities = [item['_additional']['distance'] for item in results]
    ids = [item['id'] for item in results]
    return VectorIndexQueryResult(similarities, ids)

class FaissVectorStore(VectorStore):

    def __init__(self, index_name: str, index_path: str) -> None:
        try_to_import_faiss()
        self._index_name = index_name
        self._index_path = index_path
        self._index = None
        import faiss
        self._existing_id_set = set([])
        if self._index is None and os.path.exists(self._index_path):
            self._index = faiss.read_index(self._index_path)
            for i in range(self._index.ntotal):
                self._existing_id_set.add(self._index.id_map.at(i))

    def create(self, vector_dim: int):
        import faiss
        self._index = faiss.IndexIDMap2(faiss.IndexHNSWFlat(vector_dim, 32))

    def add(self, payload: List[FeaturePayload]):
        assert self._index is not None, 'Please create an index before adding features.'
        for row in payload:
            embedding = np.array(row.embedding, dtype='float32')
            if len(embedding.shape) != 2:
                embedding = embedding.reshape(1, -1)
            if row.id not in self._existing_id_set:
                self._index.add_with_ids(embedding, np.array([row.id]))

    def persist(self):
        assert self._index is not None, 'Please create an index before calling persist.'
        import faiss
        faiss.write_index(self._index, self._index_path)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        assert self._index is not None, 'Cannot query as index does not exists.'
        embedding = np.array(query.embedding, dtype='float32')
        if len(embedding.shape) != 2:
            embedding = embedding.reshape(1, -1)
        dists, indices = self._index.search(embedding, query.top_k)
        distances, ids = ([], [])
        for dis, idx in zip(dists[0], indices[0]):
            distances.append(dis)
            ids.append(idx)
        return VectorIndexQueryResult(distances, ids)

    def delete(self):
        index_path = Path(self._index_path)
        if index_path.exists():
            index_path.unlink()

def add(self, payload: List[FeaturePayload]):
    assert self._index is not None, 'Please create an index before adding features.'
    for row in payload:
        embedding = np.array(row.embedding, dtype='float32')
        if len(embedding.shape) != 2:
            embedding = embedding.reshape(1, -1)
        if row.id not in self._existing_id_set:
            self._index.add_with_ids(embedding, np.array([row.id]))

def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
    assert self._index is not None, 'Cannot query as index does not exists.'
    embedding = np.array(query.embedding, dtype='float32')
    if len(embedding.shape) != 2:
        embedding = embedding.reshape(1, -1)
    dists, indices = self._index.search(embedding, query.top_k)
    distances, ids = ([], [])
    for dis, idx in zip(dists[0], indices[0]):
        distances.append(dis)
        ids.append(idx)
    return VectorIndexQueryResult(distances, ids)

class DecordReader(AbstractReader):

    def __init__(self, *args, predicate: AbstractExpression=None, sampling_rate: int=None, sampling_type: str=None, read_audio: bool=False, read_video: bool=True, **kwargs):
        """Read frames from the disk

        Args:
            predicate (AbstractExpression, optional): If only subset of frames
            need to be read. The predicate should be only on single column and
            can be converted to ranges. Defaults to None.
            sampling_rate (int, optional): Set if the caller wants one frame
            every `sampling_rate` number of frames. For example, if `sampling_rate = 10`, it returns every 10th frame. If both `predicate` and `sampling_rate` are specified, `sampling_rate` is given precedence.
            sampling_type (str, optional): Set as IFRAMES if caller want to sample on top on iframes only. e.g if the IFRAME frame numbers are [10,20,30,40,50] then 'SAMPLE IFRAMES 2' will return [10,30,50]
            read_audio (bool, optional): Whether to read audio stream from the video. Defaults to False
            read_video (bool, optional): Whether to read video stream from the video. Defaults to True
        """
        self._predicate = predicate
        self._sampling_rate = sampling_rate or 1
        self._sampling_type = sampling_type
        self._read_audio = read_audio
        self._read_video = read_video
        self._reader = None
        self._get_frame = None
        super().__init__(*args, **kwargs)
        self.initialize_reader()

    def _read(self) -> Iterator[Dict]:
        num_frames = int(len(self._reader))
        if self._predicate:
            range_list = extract_range_list_from_predicate(self._predicate, 0, num_frames - 1)
        else:
            range_list = [(0, num_frames - 1)]
        logger.debug('Reading frames')
        if self._sampling_type == IFRAMES:
            iframes = self._reader.get_key_indices()
            idx = 0
            for begin, end in range_list:
                while idx < len(iframes) and iframes[idx] < begin:
                    idx += self._sampling_rate
                while idx < len(iframes) and iframes[idx] <= end:
                    frame_id = iframes[idx]
                    idx += self._sampling_rate
                    yield self._get_frame(frame_id)
        elif self._sampling_rate == 1 or self._read_audio:
            for begin, end in range_list:
                frame_id = begin
                while frame_id <= end:
                    yield self._get_frame(frame_id)
                    frame_id += 1
        else:
            for begin, end in range_list:
                if begin % self._sampling_rate:
                    begin += self._sampling_rate - begin % self._sampling_rate
                for frame_id in range(begin, end + 1, self._sampling_rate):
                    yield self._get_frame(frame_id)

    def initialize_reader(self):
        try_to_import_decord()
        import decord
        if self._read_audio:
            assert self._sampling_type != IFRAMES, 'Cannot use IFRAMES with audio streams'
            sample_rate = 16000
            if self._sampling_type == AUDIORATE and self._sampling_rate != 1:
                sample_rate = self._sampling_rate
            try:
                self._reader = decord.AVReader(self.file_url, mono=True, sample_rate=sample_rate)
                self._get_frame = self.__get_audio_frame
            except decord._ffi.base.DECORDError as error_msg:
                assert "Can't find audio stream" not in str(error_msg), error_msg
        else:
            assert self._sampling_type != AUDIORATE, 'Cannot use AUDIORATE with video streams'
            self._reader = decord.VideoReader(self.file_url)
            self._get_frame = self.__get_video_frame

    def __get_video_frame(self, frame_id):
        frame_video = self._reader[frame_id]
        frame_video = frame_video.asnumpy()
        timestamp = self._reader.get_frame_timestamp(frame_id)[0]
        return {VideoColumnName.id.name: frame_id, ROW_NUM_COLUMN: frame_id, VideoColumnName.data.name: frame_video, VideoColumnName.seconds.name: round(timestamp, 2)}

    def __get_audio_frame(self, frame_id):
        frame_audio, _ = self._reader[frame_id]
        frame_audio = frame_audio.asnumpy()[0]
        return {VideoColumnName.id.name: frame_id, ROW_NUM_COLUMN: frame_id, VideoColumnName.data.name: np.empty(0), VideoColumnName.seconds.name: 0.0, VideoColumnName.audio.name: frame_audio}

def _read(self) -> Iterator[Dict]:
    num_frames = int(len(self._reader))
    if self._predicate:
        range_list = extract_range_list_from_predicate(self._predicate, 0, num_frames - 1)
    else:
        range_list = [(0, num_frames - 1)]
    logger.debug('Reading frames')
    if self._sampling_type == IFRAMES:
        iframes = self._reader.get_key_indices()
        idx = 0
        for begin, end in range_list:
            while idx < len(iframes) and iframes[idx] < begin:
                idx += self._sampling_rate
            while idx < len(iframes) and iframes[idx] <= end:
                frame_id = iframes[idx]
                idx += self._sampling_rate
                yield self._get_frame(frame_id)
    elif self._sampling_rate == 1 or self._read_audio:
        for begin, end in range_list:
            frame_id = begin
            while frame_id <= end:
                yield self._get_frame(frame_id)
                frame_id += 1
    else:
        for begin, end in range_list:
            if begin % self._sampling_rate:
                begin += self._sampling_rate - begin % self._sampling_rate
            for frame_id in range(begin, end + 1, self._sampling_rate):
                yield self._get_frame(frame_id)

def initialize_reader(self):
    try_to_import_decord()
    import decord
    if self._read_audio:
        assert self._sampling_type != IFRAMES, 'Cannot use IFRAMES with audio streams'
        sample_rate = 16000
        if self._sampling_type == AUDIORATE and self._sampling_rate != 1:
            sample_rate = self._sampling_rate
        try:
            self._reader = decord.AVReader(self.file_url, mono=True, sample_rate=sample_rate)
            self._get_frame = self.__get_audio_frame
        except decord._ffi.base.DECORDError as error_msg:
            assert "Can't find audio stream" not in str(error_msg), error_msg
    else:
        assert self._sampling_type != AUDIORATE, 'Cannot use AUDIORATE with video streams'
        self._reader = decord.VideoReader(self.file_url)
        self._get_frame = self.__get_video_frame

def __get_video_frame(self, frame_id):
    frame_video = self._reader[frame_id]
    frame_video = frame_video.asnumpy()
    timestamp = self._reader.get_frame_timestamp(frame_id)[0]
    return {VideoColumnName.id.name: frame_id, ROW_NUM_COLUMN: frame_id, VideoColumnName.data.name: frame_video, VideoColumnName.seconds.name: round(timestamp, 2)}

def __get_audio_frame(self, frame_id):
    frame_audio, _ = self._reader[frame_id]
    frame_audio = frame_audio.asnumpy()[0]
    return {VideoColumnName.id.name: frame_id, ROW_NUM_COLUMN: frame_id, VideoColumnName.data.name: np.empty(0), VideoColumnName.seconds.name: 0.0, VideoColumnName.audio.name: frame_audio}

class GenericSklearnModel(AbstractFunction):

    @property
    def name(self) -> str:
        return 'GenericSklearnModel'

    def setup(self, model_path: str, predict_col: str, **kwargs):
        try_to_import_flaml_automl()
        self.model = pickle.load(open(model_path, 'rb'))
        self.predict_col = predict_col

    def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
        frames.drop([self.predict_col], axis=1, inplace=True)
        predictions = self.model.predict(frames)
        predict_df = pd.DataFrame(predictions)
        predict_df.rename(columns={0: self.predict_col}, inplace=True)
        return predict_df

    def to_device(self, device: str):
        return self

def setup(self, model_path: str, predict_col: str, **kwargs):
    try_to_import_flaml_automl()
    self.model = pickle.load(open(model_path, 'rb'))
    self.predict_col = predict_col

class GenericLudwigModel(AbstractFunction):

    @property
    def name(self) -> str:
        return 'GenericLudwigModel'

    def setup(self, model_path: str, **kwargs):
        try_to_import_ludwig()
        from ludwig.api import LudwigModel
        self.model = LudwigModel.load(model_path)

    def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
        predictions, _ = self.model.predict(frames, return_type=pd.DataFrame)
        try:
            import dask
            if isinstance(predictions, dask.dataframe.core.DataFrame):
                predictions = predictions.compute()
        except ImportError:
            pass
        return predictions

    def to_device(self, device: str):
        return self

def setup(self, model_path: str, **kwargs):
    try_to_import_ludwig()
    from ludwig.api import LudwigModel
    self.model = LudwigModel.load(model_path)

class GenericXGBoostModel(AbstractFunction):

    @property
    def name(self) -> str:
        return 'GenericXGBoostModel'

    def setup(self, model_path: str, predict_col: str, **kwargs):
        try_to_import_flaml_automl()
        self.model = pickle.load(open(model_path, 'rb'))
        self.predict_col = predict_col

    def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
        frames.drop([self.predict_col], axis=1, inplace=True)
        predictions = self.model.predict(frames)
        predict_df = pd.DataFrame(predictions)
        predict_df.rename(columns={0: self.predict_col}, inplace=True)
        return predict_df

    def to_device(self, device: str):
        return self

def setup(self, model_path: str, predict_col: str, **kwargs):
    try_to_import_flaml_automl()
    self.model = pickle.load(open(model_path, 'rb'))
    self.predict_col = predict_col

class StableDiffusion(AbstractFunction):

    @property
    def name(self) -> str:
        return 'StableDiffusion'

    def setup(self, replicate_api_token='') -> None:
        self.replicate_api_token = replicate_api_token

    @forward(input_signatures=[PandasDataframe(columns=['prompt'], column_types=[NdArrayType.STR], column_shapes=[(None,)])], output_signatures=[PandasDataframe(columns=['response'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, text_df):
        try_to_import_replicate()
        import replicate
        replicate_api_key = self.replicate_api_token
        if replicate_api_key is None:
            replicate_api_key = os.environ.get('REPLICATE_API_TOKEN', '')
        assert len(replicate_api_key) != 0, "Please set your Replicate API key using SET REPLICATE_API_TOKEN = '' or set the environment variable (REPLICATE_API_TOKEN)"
        os.environ['REPLICATE_API_TOKEN'] = replicate_api_key
        model_id = replicate.models.get('stability-ai/stable-diffusion').versions.list()[0].id

        def generate_image(text_df: PandasDataframe):
            results = []
            queries = text_df[text_df.columns[0]]
            for query in queries:
                output = replicate.run('stability-ai/stable-diffusion:' + model_id, input={'prompt': query})
                response = requests.get(output[0])
                image = Image.open(BytesIO(response.content))
                frame = np.array(image)
                results.append(frame)
            return results
        df = pd.DataFrame({'response': generate_image(text_df=text_df)})
        return df

def generate_image(text_df: PandasDataframe):
    results = []
    queries = text_df[text_df.columns[0]]
    for query in queries:
        output = replicate.run('stability-ai/stable-diffusion:' + model_id, input={'prompt': query})
        response = requests.get(output[0])
        image = Image.open(BytesIO(response.content))
        frame = np.array(image)
        results.append(frame)
    return results

class TextFilterKeyword(AbstractFunction):

    @setup(cacheable=False, function_type='TextProcessing', batchable=False)
    def setup(self):
        pass

    @property
    def name(self) -> str:
        return 'TextFilterKeyword'

    @forward(input_signatures=[PandasDataframe(columns=['data', 'keyword'], column_types=[NdArrayType.STR, NdArrayType.STR], column_shapes=[1, 1])], output_signatures=[PandasDataframe(columns=['filtered'], column_types=[NdArrayType.STR], column_shapes=[1])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:

        def _forward(row: pd.Series) -> np.ndarray:
            import re
            data = row.iloc[0]
            keywords = row.iloc[1]
            flag = False
            for i in keywords:
                pattern = f'^(.*?({i})[^$]*)$'
                match_check = re.search(pattern, data, re.IGNORECASE)
                if match_check:
                    flag = True
            if flag is False:
                return data
            flag = False
        ret = pd.DataFrame()
        ret['filtered'] = df.apply(_forward, axis=1)
        return ret

def _forward(row: pd.Series) -> np.ndarray:
    import re
    data = row.iloc[0]
    keywords = row.iloc[1]
    flag = False
    for i in keywords:
        pattern = f'^(.*?({i})[^$]*)$'
        match_check = re.search(pattern, data, re.IGNORECASE)
        if match_check:
            flag = True
    if flag is False:
        return data
    flag = False

class DallEFunction(AbstractFunction):

    @property
    def name(self) -> str:
        return 'DallE'

    def setup(self, openai_api_key='') -> None:
        self.openai_api_key = openai_api_key

    @forward(input_signatures=[PandasDataframe(columns=['prompt'], column_types=[NdArrayType.STR], column_shapes=[(None,)])], output_signatures=[PandasDataframe(columns=['response'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, text_df):
        try_to_import_openai()
        from openai import OpenAI
        api_key = self.openai_api_key
        if len(self.openai_api_key) == 0:
            api_key = os.environ.get('OPENAI_API_KEY', '')
        assert len(api_key) != 0, "Please set your OpenAI API key using SET OPENAI_API_KEY = 'sk-' or environment variable (OPENAI_API_KEY)"
        client = OpenAI(api_key=api_key)

        def generate_image(text_df: PandasDataframe):
            results = []
            queries = text_df[text_df.columns[0]]
            for query in queries:
                response = client.images.generate(prompt=query, n=1, size='1024x1024')
                image_response = requests.get(response.data[0].url)
                image = Image.open(BytesIO(image_response.content))
                frame = np.array(image)
                results.append(frame)
            return results
        df = pd.DataFrame({'response': generate_image(text_df=text_df)})
        return df

def generate_image(text_df: PandasDataframe):
    results = []
    queries = text_df[text_df.columns[0]]
    for query in queries:
        response = client.images.generate(prompt=query, n=1, size='1024x1024')
        image_response = requests.get(response.data[0].url)
        image = Image.open(BytesIO(image_response.content))
        frame = np.array(image)
        results.append(frame)
    return results

def init_builtin_functions(db: EvaDBDatabase, mode: str='debug') -> None:
    """Load the built-in functions into the system during system bootstrapping.

    The function loads a set of pre-defined function queries based on the `mode` argument.
    In 'debug' mode, the function loads debug functions along with release functions.
    In 'release' mode, only release functions are loaded. In addition, in 'debug' mode,
    the function loads a smaller model to accelerate the test suite time.

    Args:G
        mode (str, optional): The mode for loading functions, either 'debug' or 'release'.
        Defaults to 'debug'.

    """
    try:
        import torch
    except ImportError:
        pass
    import os
    os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    queries = [mnistcnn_function_query, Fastrcnn_function_query, ArrayCount_function_query, Crop_function_query, Open_function_query, Similarity_function_query, norfair_obj_tracker_query, chatgpt_function_query, face_detection_function_query, Sift_function_query, Yolo_function_query, stablediffusion_function_query, dalle_function_query, Upper_function_query, Lower_function_query, Concat_function_query]
    if mode == 'debug':
        queries.extend([DummyObjectDetector_function_query, DummyMultiObjectDetector_function_query, DummyFeatureExtractor_function_query, DummyNoInputFunction_function_query, DummyLLM_function_query])
    for query in queries:
        try:
            execute_query_fetch_all(db, query, do_not_print_exceptions=False, do_not_raise_exceptions=True)
        except Exception:
            pass

class FaceDetector(AbstractClassifierFunction, GPUCompatible):
    """
    Arguments:
        threshold (float): Threshold for classifier confidence score
    """

    def setup(self, threshold=0.85):
        self.threshold = threshold
        try_to_import_torch()
        try_to_import_torchvision()
        try_to_import_facenet_pytorch()
        from facenet_pytorch import MTCNN
        self.model = MTCNN()

    @property
    def name(self) -> str:
        return 'FaceDetector'

    def to_device(self, device: str):
        try_to_import_facenet_pytorch()
        import torch
        from facenet_pytorch import MTCNN
        gpu = 'cuda:{}'.format(device)
        self.model = MTCNN(device=torch.device(gpu))
        return self

    @property
    def labels(self) -> List[str]:
        return []

    def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
        """
        Performs predictions on input frames
        Arguments:
            frames (np.ndarray): Frames on which predictions need
            to be performed
        Returns:
            face boxes (List[List[BoundingBox]])
        """
        frames_list = frames.transpose().values.tolist()[0]
        frames = np.asarray(frames_list)
        detections = self.model.detect(frames)
        boxes, scores = detections
        outcome = []
        for frame_boxes, frame_scores in zip(boxes, scores):
            pred_boxes = []
            pred_scores = []
            if frame_boxes is not None and frame_scores is not None:
                if not np.isnan(pred_boxes):
                    pred_boxes = np.asarray(frame_boxes, dtype='int')
                    pred_scores = frame_scores
                else:
                    logger.warn(f'Nan entry in box {frame_boxes}')
            outcome.append({'bboxes': pred_boxes, 'scores': pred_scores})
        return pd.DataFrame(outcome, columns=['bboxes', 'scores'])

def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
    """
        Performs predictions on input frames
        Arguments:
            frames (np.ndarray): Frames on which predictions need
            to be performed
        Returns:
            face boxes (List[List[BoundingBox]])
        """
    frames_list = frames.transpose().values.tolist()[0]
    frames = np.asarray(frames_list)
    detections = self.model.detect(frames)
    boxes, scores = detections
    outcome = []
    for frame_boxes, frame_scores in zip(boxes, scores):
        pred_boxes = []
        pred_scores = []
        if frame_boxes is not None and frame_scores is not None:
            if not np.isnan(pred_boxes):
                pred_boxes = np.asarray(frame_boxes, dtype='int')
                pred_scores = frame_scores
            else:
                logger.warn(f'Nan entry in box {frame_boxes}')
        outcome.append({'bboxes': pred_boxes, 'scores': pred_scores})
    return pd.DataFrame(outcome, columns=['bboxes', 'scores'])

class Similarity(AbstractFunction):

    def _get_distance(self, numpy_distance):
        return numpy_distance[0][0]

    def setup(self):
        try_to_import_faiss()
        pass

    @property
    def name(self):
        return 'Similarity'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get similarity score between two feature vectors: 1. feature vector of an opened image;
        and 2. feature vector from base table.
        """

        def _similarity(row: pd.Series) -> float:
            open_feat_np, base_feat_np = (row.iloc[0], row.iloc[1])
            open_feat_np = open_feat_np.reshape(1, -1)
            base_feat_np = base_feat_np.reshape(1, -1)
            import faiss
            distance_np = faiss.pairwise_distances(open_feat_np, base_feat_np)
            return self._get_distance(distance_np)
        ret = pd.DataFrame()
        ret['distance'] = df.apply(_similarity, axis=1)
        return ret

def _similarity(row: pd.Series) -> float:
    open_feat_np, base_feat_np = (row.iloc[0], row.iloc[1])
    open_feat_np = open_feat_np.reshape(1, -1)
    base_feat_np = base_feat_np.reshape(1, -1)
    import faiss
    distance_np = faiss.pairwise_distances(open_feat_np, base_feat_np)
    return self._get_distance(distance_np)

class IOColumnArgument(IOArgument):
    """
    Base class for IO arguments that are represented individually as columns in the catalog.
    """

    @abstractmethod
    def __init__(self, name: str=None, type: ColumnType=None, is_nullable: bool=None, array_type: NdArrayType=None, array_dimensions: Tuple[int]=None) -> None:
        """The parameters like shape, data type are passed as parameters to be initialized

        Args:
            shape (tuple[int]): a tuple of integers of the required shape.
            dtype (str): datatype of the elements. Types are int32, float16 and float32.

        """
        self.name = name
        self.type = type
        self.is_nullable = is_nullable
        self.array_type = array_type
        self.array_dimensions = array_dimensions

    def generate_catalog_entries(self, is_input=False) -> List[Type[FunctionIOCatalogEntry]]:
        """Generates the catalog IO entries from the Argument.

        Returns:
            list: list of catalog entries for the EvaArgument.

        """
        return [FunctionIOCatalogEntry(name=self.name, type=self.type, is_nullable=self.is_nullable, array_type=self.array_type, array_dimensions=self.array_dimensions, is_input=is_input)]

def generate_catalog_entries(self, is_input=False) -> List[Type[FunctionIOCatalogEntry]]:
    """Generates the catalog IO entries from the Argument.

        Returns:
            list: list of catalog entries for the EvaArgument.

        """
    return [FunctionIOCatalogEntry(name=self.name, type=self.type, is_nullable=self.is_nullable, array_type=self.array_type, array_dimensions=self.array_dimensions, is_input=is_input)]

class PandasDataframe(IOArgument):
    """Descriptor data type for Pandas Dataframe"""

    def __init__(self, columns, column_types=[], column_shapes=[]) -> None:
        super().__init__()
        self.columns = columns
        self.column_types = column_types
        self.column_shapes = column_shapes

    def generate_catalog_entries(self, is_input=False) -> List[Type[FunctionIOCatalogEntry]]:
        catalog_entries = []
        if not self.column_types:
            self.column_types = [NdArrayType.ANYTYPE] * len(self.columns)
        if not self.column_shapes:
            self.column_shapes = [Dimension.ANYDIM] * len(self.columns)
        if len(self.columns) != len(self.column_types) or len(self.columns) != len(self.column_shapes):
            raise FunctionIODefinitionError('columns, column_types and column_shapes should be of same length if specified. ')
        for column_name, column_type, column_shape in zip(self.columns, self.column_types, self.column_shapes):
            catalog_entries.append(FunctionIOCatalogEntry(name=column_name, type=ColumnType.NDARRAY, is_nullable=False, array_type=column_type, array_dimensions=column_shape, is_input=is_input))
        return catalog_entries

def generate_catalog_entries(self, is_input=False) -> List[Type[FunctionIOCatalogEntry]]:
    catalog_entries = []
    if not self.column_types:
        self.column_types = [NdArrayType.ANYTYPE] * len(self.columns)
    if not self.column_shapes:
        self.column_shapes = [Dimension.ANYDIM] * len(self.columns)
    if len(self.columns) != len(self.column_types) or len(self.columns) != len(self.column_shapes):
        raise FunctionIODefinitionError('columns, column_types and column_shapes should be of same length if specified. ')
    for column_name, column_type, column_shape in zip(self.columns, self.column_types, self.column_shapes):
        catalog_entries.append(FunctionIOCatalogEntry(name=column_name, type=ColumnType.NDARRAY, is_nullable=False, array_type=column_type, array_dimensions=column_shape, is_input=is_input))
    return catalog_entries

class AbstractHFFunction(AbstractFunction, GPUCompatible):
    """
    An abstract class for all HuggingFace models.

    This is implemented using the pipeline API from HuggingFace. pipeline is an
    easy way to use a huggingface model for inference. In EvaDB, we require users
    to mention the task they want to perform for simplicity. A HuggingFace task
    is different from a model(pytorch). There are a large number of models on HuggingFace
    hub that can be used for a particular task. The user can specify the model or a default
    model will be used.

    Refer to https://huggingface.co/transformers/main_classes/pipelines.html for more details
    on pipelines.
    """

    @property
    def name(self) -> str:
        return 'GenericHuggingfaceModel'

    def __init__(self, function_obj: FunctionCatalogEntry, device: int=-1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pipeline_args = self.default_pipeline_args
        for entry in function_obj.metadata:
            if entry.value.isnumeric():
                pipeline_args[entry.key] = int(entry.value)
            else:
                pipeline_args[entry.key] = entry.value
        self.pipeline_args = pipeline_args
        try_to_import_transformers()
        from transformers import pipeline
        self.hf_function_obj = pipeline(**pipeline_args, device=device)

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)

    @property
    def default_pipeline_args(self) -> dict:
        """
        Arguments that will be passed to the pipeline by default.
        User provided arguments override the default arguments
        """
        return {}

    def input_formatter(self, inputs: Any):
        """
        Function that formats input from EvaDB format to HuggingFace format for that particular HF model
        """
        return inputs

    def output_formatter(self, outputs: Any):
        """
        Function that formats output from HuggingFace format to EvaDB format (pandas dataframe)
        The output can be in various formats, depending on the model. For example:
            {'text' : 'transcript from video'}
            [[{'score': 0.25, 'label': 'bridge'}, {'score': 0.50, 'label': 'car'}]]
        """
        if isinstance(outputs, dict):
            return pd.DataFrame(outputs, index=[0])
        result_list = []
        if outputs != [[]]:
            for row_output in outputs:
                if isinstance(row_output, list):
                    row_output = {k: [dic[k] for dic in row_output] for k in row_output[0]}
                result_list.append(row_output)
        result_df = pd.DataFrame(result_list)
        return result_df

    def forward(self, inputs, *args, **kwargs) -> pd.DataFrame:
        hf_input = self.input_formatter(inputs)
        hf_output = self.hf_function_obj(hf_input, *args, **kwargs)
        evadb_output = self.output_formatter(hf_output)
        return evadb_output

    def to_device(self, device: str) -> GPUCompatible:
        try_to_import_transformers()
        from transformers import pipeline
        self.hf_function_obj = pipeline(**self.pipeline_args, device=device)
        return self

def output_formatter(self, outputs: Any):
    """
        Function that formats output from HuggingFace format to EvaDB format (pandas dataframe)
        The output can be in various formats, depending on the model. For example:
            {'text' : 'transcript from video'}
            [[{'score': 0.25, 'label': 'bridge'}, {'score': 0.50, 'label': 'car'}]]
        """
    if isinstance(outputs, dict):
        return pd.DataFrame(outputs, index=[0])
    result_list = []
    if outputs != [[]]:
        for row_output in outputs:
            if isinstance(row_output, list):
                row_output = {k: [dic[k] for dic in row_output] for k in row_output[0]}
            result_list.append(row_output)
    result_df = pd.DataFrame(result_list)
    return result_df

class NorFairTracker(EvaDBTrackerAbstractFunction):

    @property
    def name(self) -> str:
        return 'NorFairTracker'

    def setup(self, distance_threshold=DISTANCE_THRESHOLD_CENTROID) -> None:
        try_to_import_norfair()
        from norfair import Tracker
        self.tracker = Tracker(distance_function='euclidean', distance_threshold=distance_threshold)
        self.prev_frame_id = None

    def forward(self, frame_id, frame, labels, bboxes, scores):
        from norfair import Detection
        norfair_detections = [Detection(points=get_centroid(bbox), scores=np.array([score]), label=hash(label) % 10 ** 8, data=(label, bbox, score)) for bbox, score, label in zip(bboxes, scores, labels)]
        period = frame_id - self.prev_frame_id if self.prev_frame_id else 1
        self.prev_frame_id = frame_id
        tracked_objects = self.tracker.update(detections=norfair_detections, period=period)
        bboxes_xyxy = []
        labels = []
        scores = []
        ids = []
        for obj in tracked_objects:
            det = obj.last_detection.data
            labels.append(det[0])
            bboxes_xyxy.append(det[1])
            scores.append(det[2])
            ids.append(obj.id)
        return (np.array(ids), np.array(labels), np.array(bboxes_xyxy), np.array(scores))

def forward(self, frame_id, frame, labels, bboxes, scores):
    from norfair import Detection
    norfair_detections = [Detection(points=get_centroid(bbox), scores=np.array([score]), label=hash(label) % 10 ** 8, data=(label, bbox, score)) for bbox, score, label in zip(bboxes, scores, labels)]
    period = frame_id - self.prev_frame_id if self.prev_frame_id else 1
    self.prev_frame_id = frame_id
    tracked_objects = self.tracker.update(detections=norfair_detections, period=period)
    bboxes_xyxy = []
    labels = []
    scores = []
    ids = []
    for obj in tracked_objects:
        det = obj.last_detection.data
        labels.append(det[0])
        bboxes_xyxy.append(det[1])
        scores.append(det[2])
        ids.append(obj.id)
    return (np.array(ids), np.array(labels), np.array(bboxes_xyxy), np.array(scores))

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

def apply_function_expression(self, expr: Callable) -> Batch:
    """
        Execute function expression on frames.
        """
    self.drop_column_alias()
    return Batch(expr(self._frames))

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

def _mk_label(mapper, show_operations, show_attributes, show_datatypes, show_inherited, bordersize):
    html = '<<TABLE CELLSPACING="0" CELLPADDING="1" BORDER="0" CELLBORDER="%d" ALIGN="LEFT"><TR><TD><FONT POINT-SIZE="10">%s</FONT></TD></TR>' % (bordersize, mapper.class_.__name__)

    def format_col(col):
        colstr = '+%s' % col.name
        if show_datatypes:
            colstr += ' : %s' % col.type.__class__.__name__
        return colstr
    if show_attributes:
        if not show_inherited:
            cols = [c for c in mapper.columns if c.table == mapper.tables[0]]
        else:
            cols = mapper.columns
        html += '<TR><TD ALIGN="LEFT">%s</TD></TR>' % '<BR ALIGN="LEFT"/>'.join((format_col(col) for col in cols))
    else:
        [format_col(col) for col in sorted(mapper.columns, key=lambda col: not col.primary_key)]
    if show_operations:
        html += '<TR><TD ALIGN="LEFT">%s</TD></TR>' % '<BR ALIGN="LEFT"/>'.join(('%s(%s)' % (name, ', '.join((default is _mk_label and '%s' % arg or '%s=%s' % (arg, repr(default)) for default, arg in zip((func.func_defaults and len(func.func_code.co_varnames) - 1 - (len(func.func_defaults) or 0) or func.func_code.co_argcount - 1) * [_mk_label] + list(func.func_defaults or []), func.func_code.co_varnames[1:])))) for name, func in mapper.class_.__dict__.items() if isinstance(func, types.FunctionType) and func.__module__ == mapper.class_.__module__))
    html += '</TABLE>>'
    return html

def append_changelog(insert_changelog: str, version: str):
    with open(EvaDB_CHANGELOG_PATH, 'r') as file:
        file_contents = file.read()
    position = 327
    version = version.split('+')[0]
    today_date = date.today()
    header = f'##  [{version}] - {today_date}\n\n'
    modified_content = file_contents[:position] + header + insert_changelog + '\n' + file_contents[position:]
    with open(EvaDB_CHANGELOG_PATH, 'w') as file:
        file.write(modified_content)

def partition_transcript(raw_transcript: str):
    """Group video transcript elements when they are too large.

    Args:
        transcript (str): downloaded video transcript as a raw string.

    Returns:
        List: a list of partitioned transcript
    """
    if len(raw_transcript) <= MAX_CHUNK_SIZE:
        return [{'text': raw_transcript}]
    k = 2
    while True:
        if len(raw_transcript) / k <= MAX_CHUNK_SIZE:
            break
        else:
            k += 1
    chunk_size = int(len(raw_transcript) / k)
    partitioned_transcript = [{'text': raw_transcript[i:i + chunk_size]} for i in range(0, len(raw_transcript), chunk_size)]
    if len(partitioned_transcript[-1]['text']) < 30:
        partitioned_transcript.pop()
    return partitioned_transcript

def partition_summary(prev_summary: str):
    """Summarize a summary if a summary is too large.

    Args:
        prev_summary (str): previous summary that is too large.

    Returns:
        List: a list of partitioned summary
    """
    k = 2
    while True:
        if len(prev_summary) / k <= MAX_CHUNK_SIZE:
            break
        else:
            k += 1
    chunk_size = int(len(prev_summary) / k)
    new_summary = [{'summary': prev_summary[i:i + chunk_size]} for i in range(0, len(prev_summary), chunk_size)]
    if len(new_summary[-1]['summary']) < 30:
        new_summary.pop()
    return new_summary

