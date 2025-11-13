# Cluster 3

class MpsDirective(Directive):

    @classmethod
    def add_to_app(cls, app):
        if hasattr(cls, 'name'):
            name = cls.name
        elif hasattr(cls, 'node_class') and cls.node_class is not None:
            name = cls.node_class.__name__
        else:
            return
        if hasattr(cls, 'node_class') and hasattr(cls, 'visit'):
            app.add_node(cls.node_class, html=cls.visit, latex=cls.visit, text=cls.visit, man=cls.visit)
        if hasattr(cls, 'domain'):
            app.add_directive_to_domain(cls.domain, name, cls)
        else:
            app.add_directive(name, cls)

@classmethod
def add_to_app(cls, app):
    if hasattr(cls, 'name'):
        name = cls.name
    elif hasattr(cls, 'node_class') and cls.node_class is not None:
        name = cls.node_class.__name__
    else:
        return
    if hasattr(cls, 'node_class') and hasattr(cls, 'visit'):
        app.add_node(cls.node_class, html=cls.visit, latex=cls.visit, text=cls.visit, man=cls.visit)
    if hasattr(cls, 'domain'):
        app.add_directive_to_domain(cls.domain, name, cls)
    else:
        app.add_directive(name, cls)

def setup(app):
    designs.convert_updated(app)
    app.add_domain(MpsDomain)
    app.add_role_to_domain('mps', 'tag', mps_tag_role)
    app.add_role_to_domain('mps', 'ref', mps_ref_role)
    app.add_transform(GlossaryTransform)
    app.connect('build-finished', GlossaryTransform.warn_indirect_terms)
    for g in globals().values():
        if isclass(g) and issubclass(g, MpsDirective):
            g.add_to_app(app)

def is_ray_stage_running():
    import psutil
    return 'ray::ray_stage' in (p.name() for p in psutil.process_iter())

def recurse(klass):
    for subclass in klass.__subclasses__():
        subclass_list.append(subclass)
        recurse(subclass)

def get_all_subclasses(cls):
    subclass_list = []

    def recurse(klass):
        for subclass in klass.__subclasses__():
            subclass_list.append(subclass)
            recurse(subclass)
    recurse(cls)
    return set(subclass_list)

class YoloTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = os.path.dirname(os.path.abspath(__file__))

    def _load_image(self, path):
        try_to_import_cv2()
        import cv2
        img = cv2.imread(path)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def test_should_raise_import_error_with_missing_torch(self):
        with self.assertRaises(ImportError):
            with mock.patch.dict(sys.modules, {'torch': None}):
                from evadb.functions.decorators.yolo_object_detection_decorators import Yolo
                pass

    @unittest.skip('disable test due to model downloading time')
    def test_should_return_batches_equivalent_to_number_of_frames(self):
        from evadb.functions.decorators.yolo_object_detection_decorators import Yolo
        frame_dog = {'id': 1, 'data': self._load_image(os.path.join(self.base_path, 'data', 'dog.jpeg'))}
        frame_dog_cat = {'id': 2, 'data': self._load_image(os.path.join(self.base_path, 'data', 'dog_cat.jpg'))}
        test_df_dog = pd.DataFrame([frame_dog])
        test_df_cat = pd.DataFrame([frame_dog_cat])
        frame_dog = numpy_to_yolo_format(test_df_dog['data'].values[0])
        frame_cat = numpy_to_yolo_format(test_df_cat['data'].values[0])
        detector = Yolo()
        result = []
        result.append(detector.forward(frame_dog))
        result.append(detector.forward(frame_cat))
        self.assertEqual(['dog'], result[0]['labels'].tolist()[0])
        self.assertEqual(['cat', 'dog'], result[1]['labels'].tolist()[0])

def test_should_raise_import_error_with_missing_torch(self):
    with self.assertRaises(ImportError):
        with mock.patch.dict(sys.modules, {'torch': None}):
            from evadb.functions.decorators.yolo_object_detection_decorators import Yolo
            pass

class FlipTests(unittest.TestCase):

    def setUp(self):
        self.horizontal_flip_instance = HorizontalFlip()
        self.vertical_flip_instance = VerticalFlip()

    def test_flip_name_exists(self):
        assert hasattr(self.horizontal_flip_instance, 'name')
        assert hasattr(self.vertical_flip_instance, 'name')

    def test_should_flip_horizontally(self):
        try_to_import_pillow()
        from PIL import Image
        img = Image.open(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/img00001.jpg')
        arr = asarray(img)
        df = pd.DataFrame([[arr]])
        flipped_arr = self.horizontal_flip_instance(df)['horizontally_flipped_frame_array']
        self.assertEqual(np.sum(arr[:, 0] - np.flip(flipped_arr[0][:, -1], 1)), 0)

    def test_should_flip_vertically(self):
        try_to_import_pillow()
        from PIL import Image
        img = Image.open(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/img00001.jpg')
        arr = asarray(img)
        df = pd.DataFrame([[arr]])
        flipped_arr = self.vertical_flip_instance(df)['vertically_flipped_frame_array']
        self.assertEqual(np.sum(arr[0, :] - np.flip(flipped_arr[0][-1, :], 1)), 0)

def test_flip_name_exists(self):
    assert hasattr(self.horizontal_flip_instance, 'name')
    assert hasattr(self.vertical_flip_instance, 'name')

class AnnotateTests(unittest.TestCase):

    def setUp(self):
        try_to_import_pillow()
        self.annotate_instance = Annotate()

    def test_annotate_name_exists(self):
        assert hasattr(self.annotate_instance, 'name')

    def test_should_annotate(self):
        from PIL import Image
        img = Image.open(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/img00001.jpg')
        arr = asarray(img)
        arr_copy = 0 + arr
        object_type = np.array(['object'])
        bbox = np.array([[50, 50, 70, 70]])
        df = pd.DataFrame([[arr, object_type, bbox]])
        modified_arr = self.annotate_instance(df)['annotated_frame_array']
        self.assertNotEqual(np.sum(arr_copy - modified_arr[0]), 0)
        self.assertEqual(np.sum(modified_arr[0][50][50] - np.array([207, 248, 64])), 0)
        self.assertEqual(np.sum(modified_arr[0][70][70] - np.array([207, 248, 64])), 0)
        self.assertEqual(np.sum(modified_arr[0][50][70] - np.array([207, 248, 64])), 0)
        self.assertEqual(np.sum(modified_arr[0][70][50] - np.array([207, 248, 64])), 0)

def test_annotate_name_exists(self):
    assert hasattr(self.annotate_instance, 'name')

@pytest.mark.notparallel
class OpenTests(unittest.TestCase):

    def setUp(self):
        self.open_instance = Open()
        self.image_file_path = create_sample_image()
        try_to_import_cv2()

    def test_open_name_exists(self):
        assert hasattr(self.open_instance, 'name')

    def test_should_open_image(self):
        df = self.open_instance(pd.DataFrame([self.image_file_path]))
        actual_img = df['data'].to_numpy()[0]
        expected_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
        expected_img[0] -= 1
        expected_img[2] += 1
        self.assertEqual(actual_img.shape, expected_img.shape)
        self.assertEqual(np.sum(actual_img[0]), np.sum(expected_img[0]))
        self.assertEqual(np.sum(actual_img[1]), np.sum(expected_img[1]))
        self.assertEqual(np.sum(actual_img[2]), np.sum(expected_img[2]))

    def test_open_same_path_should_use_cache(self):
        import cv2
        with patch('cv2.imread') as mock_cv2_imread:
            self.open_instance(pd.DataFrame([self.image_file_path]))
            mock_cv2_imread.assert_called_once_with(self.image_file_path)
        with patch('cv2.imread') as mock_cv2_imread:
            self.open_instance(pd.DataFrame([self.image_file_path]))
            mock_cv2_imread.assert_not_called()

    def test_open_path_should_raise_error(self):
        with self.assertRaises((AssertionError, FileNotFoundError)):
            self.open_instance(pd.DataFrame(['incorrect_path']))

def test_open_name_exists(self):
    assert hasattr(self.open_instance, 'name')

class GaussianBlurTests(unittest.TestCase):

    def setUp(self):
        self.gb_instance = GaussianBlur()
        self.tmp_file = f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/tmp.jpeg'

    def test_gb_name_exists(self):
        assert hasattr(self.gb_instance, 'name')

    def test_should_blur_image(self):
        try_to_import_cv2()
        import cv2
        arr = cv2.imread(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/dog.jpeg')
        df = pd.DataFrame([[arr]])
        modified_arr = self.gb_instance(df)['blurred_frame_array']
        cv2.imwrite(self.tmp_file, cv2.cvtColor(modified_arr[0], cv2.COLOR_RGB2BGR))
        actual_array = cv2.imread(self.tmp_file)
        expected_array = cv2.imread(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/blurred_dog.jpeg')
        self.assertEqual(np.sum(actual_array - expected_array), 0)
        file_remove(Path(self.tmp_file))

def test_gb_name_exists(self):
    assert hasattr(self.gb_instance, 'name')

class ToGrayscaleTests(unittest.TestCase):

    def setUp(self):
        self.to_grayscale_instance = ToGrayscale()

    def test_gray_scale_name_exists(self):
        assert hasattr(self.to_grayscale_instance, 'name')

    def test_should_convert_to_grayscale(self):
        try_to_import_cv2()
        import cv2
        arr = cv2.imread(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/dog.jpeg')
        df = pd.DataFrame([[arr]])
        modified_arr = self.to_grayscale_instance(df)['grayscale_frame_array']
        cv2.imwrite(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/tmp.jpeg', modified_arr[0])
        actual_array = cv2.imread(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/tmp.jpeg')
        expected_arr = cv2.imread(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/grayscale_dog.jpeg')
        self.assertEqual(np.sum(actual_array - expected_arr), 0)
        file_remove(Path(f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/tmp.jpeg'))

def test_gray_scale_name_exists(self):
    assert hasattr(self.to_grayscale_instance, 'name')

class CropTests(unittest.TestCase):

    def setUp(self):
        self.array_count = ArrayCount()

    def test_array_count_name_exists(self):
        assert hasattr(self.array_count, 'name')

def test_array_count_name_exists(self):
    assert hasattr(self.array_count, 'name')

class CropTests(unittest.TestCase):

    def setUp(self):
        self.crop_instance = Crop()

    def test_crop_name_exists(self):
        assert hasattr(self.crop_instance, 'name')

    def test_should_crop_one_frame(self):
        imarray = np.random.randint(0, 255, size=(100, 100, 3))
        bbox = np.array([0, 0, 30, 60])
        df = pd.DataFrame([[imarray, bbox]])
        cropped_image = self.crop_instance(df)
        expected_image = pd.DataFrame([[imarray[0:60, 0:30]]], columns=['cropped_frame_array'])
        self.assertTrue(expected_image.equals(cropped_image))

    def test_should_crop_multi_frame(self):
        imarray = np.random.randint(0, 255, size=(100, 100, 3))
        bbox1 = np.array([0, 0, 30, 60])
        bbox2 = np.array([50, 50, 70, 70])
        bbox3 = np.array([30, 0, 60, 20])
        df = pd.DataFrame([[imarray, bbox1], [imarray, bbox2], [imarray, bbox3]])
        cropped_image = self.crop_instance(df)
        expected_image = pd.DataFrame([[imarray[0:60, 0:30]], [imarray[50:70, 50:70]], [imarray[0:20, 30:60]]], columns=['cropped_frame_array'])
        self.assertTrue(expected_image.equals(cropped_image))

    def test_should_crop_bad_bbox(self):
        imarray = np.random.randint(0, 255, size=(100, 100, 3))
        bbox1 = np.array([0, 0, 0, 0])
        bbox2 = np.array([-10, -10, 20, 20])
        df = pd.DataFrame([[imarray, bbox1], [imarray, bbox2]])
        cropped_image = self.crop_instance(df)
        expected_image = pd.DataFrame([[imarray[0:1, 0:1]], [imarray[0:20, 0:20]]], columns=['cropped_frame_array'])
        self.assertTrue(expected_image.equals(cropped_image))

def test_crop_name_exists(self):
    assert hasattr(self.crop_instance, 'name')

@pytest.mark.notparallel
class PlanNodeTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_create_plan(self):
        dummy_info = TableInfo('dummy')
        columns = [ColumnCatalogEntry('id', ColumnType.INTEGER), ColumnCatalogEntry('name', ColumnType.TEXT, array_dimensions=[50])]
        dummy_plan_node = CreatePlan(dummy_info, columns, False)
        self.assertEqual(dummy_plan_node.opr_type, PlanOprType.CREATE)
        self.assertEqual(dummy_plan_node.if_not_exists, False)
        self.assertEqual(dummy_plan_node.table_info.table_name, 'dummy')
        self.assertEqual(dummy_plan_node.column_list[0].name, 'id')
        self.assertEqual(dummy_plan_node.column_list[1].name, 'name')

    def test_rename_plan(self):
        dummy_info = TableInfo('old')
        dummy_old = TableRef(dummy_info)
        dummy_new = TableInfo('new')
        dummy_plan_node = RenamePlan(dummy_old, dummy_new)
        self.assertEqual(dummy_plan_node.opr_type, PlanOprType.RENAME)
        self.assertEqual(dummy_plan_node.old_table.table.table_name, 'old')
        self.assertEqual(dummy_plan_node.new_name.table_name, 'new')

    def test_insert_plan(self):
        video_id = 0
        column_ids = [0, 1]
        expression = type('AbstractExpression', (), {'evaluate': lambda: 1})
        values = [expression, expression]
        dummy_plan_node = InsertPlan(video_id, column_ids, values)
        self.assertEqual(dummy_plan_node.opr_type, PlanOprType.INSERT)

    def test_create_function_plan(self):
        function_name = 'function'
        or_replace = False
        if_not_exists = True
        functionIO = 'functionIO'
        inputs = [functionIO, functionIO]
        outputs = [functionIO]
        impl_path = 'test'
        ty = 'classification'
        node = CreateFunctionPlan(function_name, or_replace, if_not_exists, inputs, outputs, impl_path, ty)
        self.assertEqual(node.opr_type, PlanOprType.CREATE_FUNCTION)
        self.assertEqual(node.or_replace, or_replace)
        self.assertEqual(node.if_not_exists, if_not_exists)
        self.assertEqual(node.inputs, [functionIO, functionIO])
        self.assertEqual(node.outputs, [functionIO])
        self.assertEqual(node.impl_path, impl_path)
        self.assertEqual(node.function_type, ty)

    def test_drop_object_plan(self):
        object_type = ObjectType.TABLE
        function_name = 'function'
        if_exists = True
        node = DropObjectPlan(object_type, function_name, if_exists)
        self.assertEqual(node.opr_type, PlanOprType.DROP_OBJECT)
        self.assertEqual(node.if_exists, True)
        self.assertEqual(node.object_type, ObjectType.TABLE)

    def test_load_data_plan(self):
        table_info = 'info'
        file_path = 'test.mp4'
        file_format = FileFormatType.VIDEO
        file_options = {}
        file_options['file_format'] = file_format
        column_list = None
        batch_mem_size = 3000
        plan_str = 'LoadDataPlan(table_id={}, file_path={},             column_list={},             file_options={},             batch_mem_size={})'.format(table_info, file_path, column_list, file_options, batch_mem_size)
        plan = LoadDataPlan(table_info, file_path, column_list, file_options, batch_mem_size)
        self.assertEqual(plan.opr_type, PlanOprType.LOAD_DATA)
        self.assertEqual(plan.table_info, table_info)
        self.assertEqual(plan.file_path, file_path)
        self.assertEqual(plan.batch_mem_size, batch_mem_size)
        self.assertEqual(str(plan), plan_str)

    def test_union_plan(self):
        all = True
        plan = UnionPlan(all)
        self.assertEqual(plan.opr_type, PlanOprType.UNION)
        self.assertEqual(plan.all, all)

    def test_abstract_plan_str(self):
        derived_plan_classes = list(get_all_subclasses(AbstractPlan))
        for derived_plan_class in derived_plan_classes:
            sig = signature(derived_plan_class.__init__)
            params = sig.parameters
            plan_dict = {}
            if isabstract(derived_plan_class) is False:
                obj = get_mock_object(derived_plan_class, len(params))
                plan_dict[obj] = obj

def test_abstract_plan_str(self):
    derived_plan_classes = list(get_all_subclasses(AbstractPlan))
    for derived_plan_class in derived_plan_classes:
        sig = signature(derived_plan_class.__init__)
        params = sig.parameters
        plan_dict = {}
        if isabstract(derived_plan_class) is False:
            obj = get_mock_object(derived_plan_class, len(params))
            plan_dict[obj] = obj

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

def side_effect_func(value):
    cost = dict({grp_expr00: 1, grp_expr01: 2, grp_expr10: 4, grp_expr11: 3, grp_expr20: 5})
    return cost[value]

@pytest.mark.notparallel
class RulesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        video_file_path = create_sample_video()
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(cls.evadb, load_query)

    @classmethod
    def tearDownClass(cls):
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_rules_promises_order(self):
        rewrite_promises = [Promise.LOGICAL_INNER_JOIN_COMMUTATIVITY, Promise.EMBED_FILTER_INTO_GET, Promise.EMBED_SAMPLE_INTO_GET, Promise.XFORM_LATERAL_JOIN_TO_LINEAR_FLOW, Promise.PUSHDOWN_FILTER_THROUGH_JOIN, Promise.PUSHDOWN_FILTER_THROUGH_APPLY_AND_MERGE, Promise.COMBINE_SIMILARITY_ORDERBY_AND_LIMIT_TO_VECTOR_INDEX_SCAN, Promise.REORDER_PREDICATES, Promise.XFORM_EXTRACT_OBJECT_TO_LINEAR_FLOW]
        for promise in rewrite_promises:
            self.assertTrue(promise > Promise.IMPLEMENTATION_DELIMITER)
        implementation_promises = [Promise.LOGICAL_EXCHANGE_TO_PHYSICAL, Promise.LOGICAL_UNION_TO_PHYSICAL, Promise.LOGICAL_GROUPBY_TO_PHYSICAL, Promise.LOGICAL_ORDERBY_TO_PHYSICAL, Promise.LOGICAL_LIMIT_TO_PHYSICAL, Promise.LOGICAL_INSERT_TO_PHYSICAL, Promise.LOGICAL_DELETE_TO_PHYSICAL, Promise.LOGICAL_RENAME_TO_PHYSICAL, Promise.LOGICAL_DROP_OBJECT_TO_PHYSICAL, Promise.LOGICAL_LOAD_TO_PHYSICAL, Promise.LOGICAL_CREATE_TO_PHYSICAL, Promise.LOGICAL_CREATE_FROM_SELECT_TO_PHYSICAL, Promise.LOGICAL_CREATE_FUNCTION_TO_PHYSICAL, Promise.LOGICAL_CREATE_FUNCTION_FROM_SELECT_TO_PHYSICAL, Promise.LOGICAL_SAMPLE_TO_UNIFORMSAMPLE, Promise.LOGICAL_GET_TO_SEQSCAN, Promise.LOGICAL_DERIVED_GET_TO_PHYSICAL, Promise.LOGICAL_LATERAL_JOIN_TO_PHYSICAL, Promise.LOGICAL_JOIN_TO_PHYSICAL_HASH_JOIN, Promise.LOGICAL_JOIN_TO_PHYSICAL_NESTED_LOOP_JOIN, Promise.LOGICAL_FUNCTION_SCAN_TO_PHYSICAL, Promise.LOGICAL_FILTER_TO_PHYSICAL, Promise.LOGICAL_PROJECT_TO_PHYSICAL, Promise.LOGICAL_PROJECT_NO_TABLE_TO_PHYSICAL, Promise.LOGICAL_SHOW_TO_PHYSICAL, Promise.LOGICAL_EXPLAIN_TO_PHYSICAL, Promise.LOGICAL_CREATE_INDEX_TO_VECTOR_INDEX, Promise.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL, Promise.LOGICAL_VECTOR_INDEX_SCAN_TO_PHYSICAL]
        for promise in implementation_promises:
            self.assertTrue(promise < Promise.IMPLEMENTATION_DELIMITER)
        promise_count = len(Promise)
        rewrite_count = len(set(rewrite_promises))
        implementation_count = len(set(implementation_promises))
        self.assertEqual(rewrite_count + implementation_count + 4, promise_count)

    def test_supported_rules(self):
        supported_rewrite_rules = [EmbedFilterIntoGet(), EmbedSampleIntoGet(), XformLateralJoinToLinearFlow(), PushDownFilterThroughApplyAndMerge(), PushDownFilterThroughJoin(), CombineSimilarityOrderByAndLimitToVectorIndexScan(), ReorderPredicates(), XformExtractObjectToLinearFlow()]
        rewrite_rules = RulesManager().stage_one_rewrite_rules + RulesManager().stage_two_rewrite_rules
        self.assertEqual(len(supported_rewrite_rules), len(rewrite_rules))
        for rule in supported_rewrite_rules:
            self.assertTrue(any((isinstance(rule, type(x)) for x in rewrite_rules)))
        supported_logical_rules = [LogicalInnerJoinCommutativity(), CacheFunctionExpressionInApply(), CacheFunctionExpressionInFilter(), CacheFunctionExpressionInProject()]
        self.assertEqual(len(supported_logical_rules), len(RulesManager().logical_rules))
        for rule in supported_logical_rules:
            self.assertTrue(any((isinstance(rule, type(x)) for x in RulesManager().logical_rules)))
        ray_enabled = self.evadb.catalog().get_configuration_catalog_value('ray')
        ray_enabled_and_installed = is_ray_enabled_and_installed(ray_enabled)
        supported_implementation_rules = [LogicalCreateToPhysical(), LogicalCreateFromSelectToPhysical(), LogicalRenameToPhysical(), LogicalCreateFunctionToPhysical(), LogicalCreateFunctionFromSelectToPhysical(), LogicalDropObjectToPhysical(), LogicalInsertToPhysical(), LogicalDeleteToPhysical(), LogicalLoadToPhysical(), LogicalGetToSeqScan(), LogicalProjectToRayPhysical() if ray_enabled_and_installed else LogicalProjectToPhysical(), LogicalProjectNoTableToPhysical(), LogicalDerivedGetToPhysical(), LogicalUnionToPhysical(), LogicalGroupByToPhysical(), LogicalOrderByToPhysical(), LogicalLimitToPhysical(), LogicalJoinToPhysicalNestedLoopJoin(), LogicalLateralJoinToPhysical(), LogicalFunctionScanToPhysical(), LogicalJoinToPhysicalHashJoin(), LogicalFilterToPhysical(), LogicalApplyAndMergeToRayPhysical() if ray_enabled_and_installed else LogicalApplyAndMergeToPhysical(), LogicalShowToPhysical(), LogicalExplainToPhysical(), LogicalCreateIndexToVectorIndex(), LogicalVectorIndexScanToPhysical()]
        if ray_enabled_and_installed:
            supported_implementation_rules.append(LogicalExchangeToPhysical())
        self.assertEqual(len(supported_implementation_rules), len(RulesManager().implementation_rules))
        for rule in supported_implementation_rules:
            self.assertTrue(any((isinstance(rule, type(x)) for x in RulesManager().implementation_rules)))

    def test_simple_filter_into_get(self):
        rule = EmbedFilterIntoGet()
        predicate = MagicMock()
        logi_get = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        logi_filter = LogicalFilter(predicate, [logi_get])
        rewrite_opr = next(rule.apply(logi_filter, MagicMock()))
        self.assertFalse(rewrite_opr is logi_get)
        self.assertEqual(rewrite_opr.predicate, predicate)

    def test_embed_sample_into_get_does_not_work_with_structured_data(self):
        rule = EmbedSampleIntoGet()
        table_obj = TableCatalogEntry(name='foo', table_type=TableType.STRUCTURED_DATA, file_url=MagicMock())
        logi_get = LogicalGet(MagicMock(), table_obj, MagicMock(), MagicMock())
        logi_sample = LogicalSample(MagicMock(), MagicMock(), children=[logi_get])
        self.assertFalse(rule.check(logi_sample, MagicMock()))

    def test_disable_rules(self):
        rules_manager = RulesManager()
        with disable_rules(rules_manager, [PushDownFilterThroughApplyAndMerge()]):
            self.assertFalse(any((isinstance(PushDownFilterThroughApplyAndMerge, type(x)) for x in rules_manager.stage_two_rewrite_rules)))

    def test_xform_lateral_join_does_not_work_with_other_join(self):
        rule = XformLateralJoinToLinearFlow()
        logi_join = LogicalJoin(JoinType.INNER_JOIN)
        self.assertFalse(rule.check(logi_join, MagicMock()))

    def test_rule_base_errors(self):
        with patch.object(Rule, '__abstractmethods__', set()):
            rule = Rule(rule_type=RuleType.INVALID_RULE)
            with self.assertRaises(NotImplementedError):
                rule.promise()
            with self.assertRaises(NotImplementedError):
                rule.check(MagicMock(), MagicMock())
            with self.assertRaises(NotImplementedError):
                rule.apply(MagicMock())

def test_rules_promises_order(self):
    rewrite_promises = [Promise.LOGICAL_INNER_JOIN_COMMUTATIVITY, Promise.EMBED_FILTER_INTO_GET, Promise.EMBED_SAMPLE_INTO_GET, Promise.XFORM_LATERAL_JOIN_TO_LINEAR_FLOW, Promise.PUSHDOWN_FILTER_THROUGH_JOIN, Promise.PUSHDOWN_FILTER_THROUGH_APPLY_AND_MERGE, Promise.COMBINE_SIMILARITY_ORDERBY_AND_LIMIT_TO_VECTOR_INDEX_SCAN, Promise.REORDER_PREDICATES, Promise.XFORM_EXTRACT_OBJECT_TO_LINEAR_FLOW]
    for promise in rewrite_promises:
        self.assertTrue(promise > Promise.IMPLEMENTATION_DELIMITER)
    implementation_promises = [Promise.LOGICAL_EXCHANGE_TO_PHYSICAL, Promise.LOGICAL_UNION_TO_PHYSICAL, Promise.LOGICAL_GROUPBY_TO_PHYSICAL, Promise.LOGICAL_ORDERBY_TO_PHYSICAL, Promise.LOGICAL_LIMIT_TO_PHYSICAL, Promise.LOGICAL_INSERT_TO_PHYSICAL, Promise.LOGICAL_DELETE_TO_PHYSICAL, Promise.LOGICAL_RENAME_TO_PHYSICAL, Promise.LOGICAL_DROP_OBJECT_TO_PHYSICAL, Promise.LOGICAL_LOAD_TO_PHYSICAL, Promise.LOGICAL_CREATE_TO_PHYSICAL, Promise.LOGICAL_CREATE_FROM_SELECT_TO_PHYSICAL, Promise.LOGICAL_CREATE_FUNCTION_TO_PHYSICAL, Promise.LOGICAL_CREATE_FUNCTION_FROM_SELECT_TO_PHYSICAL, Promise.LOGICAL_SAMPLE_TO_UNIFORMSAMPLE, Promise.LOGICAL_GET_TO_SEQSCAN, Promise.LOGICAL_DERIVED_GET_TO_PHYSICAL, Promise.LOGICAL_LATERAL_JOIN_TO_PHYSICAL, Promise.LOGICAL_JOIN_TO_PHYSICAL_HASH_JOIN, Promise.LOGICAL_JOIN_TO_PHYSICAL_NESTED_LOOP_JOIN, Promise.LOGICAL_FUNCTION_SCAN_TO_PHYSICAL, Promise.LOGICAL_FILTER_TO_PHYSICAL, Promise.LOGICAL_PROJECT_TO_PHYSICAL, Promise.LOGICAL_PROJECT_NO_TABLE_TO_PHYSICAL, Promise.LOGICAL_SHOW_TO_PHYSICAL, Promise.LOGICAL_EXPLAIN_TO_PHYSICAL, Promise.LOGICAL_CREATE_INDEX_TO_VECTOR_INDEX, Promise.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL, Promise.LOGICAL_VECTOR_INDEX_SCAN_TO_PHYSICAL]
    for promise in implementation_promises:
        self.assertTrue(promise < Promise.IMPLEMENTATION_DELIMITER)
    promise_count = len(Promise)
    rewrite_count = len(set(rewrite_promises))
    implementation_count = len(set(implementation_promises))
    self.assertEqual(rewrite_count + implementation_count + 4, promise_count)

class AbstractExecutorTest(unittest.TestCase):

    def test_constructor_args(self):
        derived_executor_classes = list(get_all_subclasses(AbstractExecutor))
        for derived_executor_class in derived_executor_classes:
            sig = signature(derived_executor_class.__init__)
            params = sig.parameters
            self.assertTrue(len(params) < 10)

def test_constructor_args(self):
    derived_executor_classes = list(get_all_subclasses(AbstractExecutor))
    for derived_executor_class in derived_executor_classes:
        sig = signature(derived_executor_class.__init__)
        params = sig.parameters
        self.assertTrue(len(params) < 10)

class AbstractExpressionsTest(unittest.TestCase):

    def test_walk(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(1)
        const_exp3 = ConstantValueExpression(0)
        const_exp4 = ConstantValueExpression(5)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_GEQ, const_exp1, const_exp2)
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_GEQ, const_exp3, const_exp4)
        expr = LogicalExpression(ExpressionType.LOGICAL_AND, cmpr_exp1, cmpr_exp2)
        self.assertEqual(len(list(expr.walk())), 7)
        self.assertEqual(len(list(expr.walk(bfs=False))), 7)
        bfs = [expr, cmpr_exp1, cmpr_exp2, const_exp1, const_exp2, const_exp3, const_exp4]
        dfs = [expr, cmpr_exp1, const_exp1, const_exp2, cmpr_exp2, const_exp3, const_exp4]
        self.assertTrue(all((isinstance(exp, type(bfs[idx])) for idx, exp in enumerate(list(expr.walk())))))
        self.assertTrue(all((isinstance(exp, type(dfs[idx])) for idx, exp in enumerate(list(expr.walk(bfs=False))))))

    def test_find_all(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(1)
        const_exp3 = ConstantValueExpression(0)
        const_exp4 = ConstantValueExpression(5)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_GEQ, const_exp1, const_exp2)
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_GEQ, const_exp3, const_exp4)
        expr = LogicalExpression(ExpressionType.LOGICAL_AND, cmpr_exp1, cmpr_exp2)
        self.assertEqual([cmpr_exp1, cmpr_exp2], [exp for exp in list(expr.find_all(ComparisonExpression))])
        self.assertNotEqual([cmpr_exp2, cmpr_exp1], [exp for exp in list(expr.find_all(ComparisonExpression))])
        self.assertNotEqual([None], [exp for exp in list(expr.find_all(TupleValueExpression))])

    def test_not_implemented_functions(self):
        with self.assertRaises(TypeError):
            x = AbstractExpression(exp_type=ExpressionType.LOGICAL_AND)
        with patch.object(AbstractExpression, '__abstractmethods__', set()):
            x = AbstractExpression(exp_type=ExpressionType.LOGICAL_AND)
            x.evaluate()

def test_not_implemented_functions(self):
    with self.assertRaises(TypeError):
        x = AbstractExpression(exp_type=ExpressionType.LOGICAL_AND)
    with patch.object(AbstractExpression, '__abstractmethods__', set()):
        x = AbstractExpression(exp_type=ExpressionType.LOGICAL_AND)
        x.evaluate()

class AbstractFunctionTest(unittest.TestCase):

    def test_function_abstract_functions(self):
        derived_function_classes = list(get_all_subclasses(AbstractFunction))
        for derived_function_class in derived_function_classes:
            if issubclass(derived_function_class, (Yolo, AbstractHFFunction)):
                continue
            if isabstract(derived_function_class) is False:
                class_type = derived_function_class
                sig = inspect.signature(class_type.__init__)
                params = sig.parameters
                len_params = len(params)
                if 'kwargs' in params:
                    len_params = len_params - 1
                if 'args' in params:
                    len_params = len_params - 1
                dummy_object = get_mock_object(class_type, len_params)
                self.assertTrue(str(dummy_object.name) is not None)

    def test_all_classes(self):

        def get_all_classes(module, level):
            class_list = []
            if level == 4:
                return []
            for _, obj in inspect.getmembers(module):
                if inspect.ismodule(obj):
                    sublist = get_all_classes(obj, level + 1)
                    if sublist != []:
                        class_list.append(sublist)
                elif inspect.isclass(obj):
                    if inspect.isabstract(obj) is True:
                        sublist = get_all_classes(obj, level + 1)
                        if sublist != []:
                            class_list.append(sublist)
                    elif inspect.isbuiltin(obj) is False:
                        try:
                            source_file = inspect.getsourcefile(obj)
                            if source_file is None:
                                continue
                            if issubclass(obj, Enum):
                                continue
                            if 'python' not in str(source_file):
                                class_list.append([obj])
                        except OSError:
                            pass
                        except TypeError:
                            pass
            flat_class_list = [item for sublist in class_list for item in sublist]
            return set(flat_class_list)
        class_list = get_all_classes(evadb, 1)
        base_id = 0
        ref_object = None
        for class_type in class_list:
            base_id = base_id + 1
            sig = inspect.signature(class_type.__init__)
            params = sig.parameters
            len_params = len(params)
            if 'kwargs' in params:
                len_params = len_params - 1
            if 'args' in params:
                len_params = len_params - 1
            try:
                dummy_object = get_mock_object(class_type, len_params)
            except Exception:
                continue
            if base_id == 0:
                ref_object = dummy_object
            else:
                self.assertEqual(dummy_object, dummy_object)
                self.assertNotEqual(ref_object, dummy_object)
            try:
                inspect.signature(class_type.name)
            except Exception:
                continue
            name_str = dummy_object.name()
            self.assertTrue(name_str is not None)

def test_function_abstract_functions(self):
    derived_function_classes = list(get_all_subclasses(AbstractFunction))
    for derived_function_class in derived_function_classes:
        if issubclass(derived_function_class, (Yolo, AbstractHFFunction)):
            continue
        if isabstract(derived_function_class) is False:
            class_type = derived_function_class
            sig = inspect.signature(class_type.__init__)
            params = sig.parameters
            len_params = len(params)
            if 'kwargs' in params:
                len_params = len_params - 1
            if 'args' in params:
                len_params = len_params - 1
            dummy_object = get_mock_object(class_type, len_params)
            self.assertTrue(str(dummy_object.name) is not None)

def get_all_classes(module, level):
    class_list = []
    if level == 4:
        return []
    for _, obj in inspect.getmembers(module):
        if inspect.ismodule(obj):
            sublist = get_all_classes(obj, level + 1)
            if sublist != []:
                class_list.append(sublist)
        elif inspect.isclass(obj):
            if inspect.isabstract(obj) is True:
                sublist = get_all_classes(obj, level + 1)
                if sublist != []:
                    class_list.append(sublist)
            elif inspect.isbuiltin(obj) is False:
                try:
                    source_file = inspect.getsourcefile(obj)
                    if source_file is None:
                        continue
                    if issubclass(obj, Enum):
                        continue
                    if 'python' not in str(source_file):
                        class_list.append([obj])
                except OSError:
                    pass
                except TypeError:
                    pass
    flat_class_list = [item for sublist in class_list for item in sublist]
    return set(flat_class_list)

def test_all_classes(self):

    def get_all_classes(module, level):
        class_list = []
        if level == 4:
            return []
        for _, obj in inspect.getmembers(module):
            if inspect.ismodule(obj):
                sublist = get_all_classes(obj, level + 1)
                if sublist != []:
                    class_list.append(sublist)
            elif inspect.isclass(obj):
                if inspect.isabstract(obj) is True:
                    sublist = get_all_classes(obj, level + 1)
                    if sublist != []:
                        class_list.append(sublist)
                elif inspect.isbuiltin(obj) is False:
                    try:
                        source_file = inspect.getsourcefile(obj)
                        if source_file is None:
                            continue
                        if issubclass(obj, Enum):
                            continue
                        if 'python' not in str(source_file):
                            class_list.append([obj])
                    except OSError:
                        pass
                    except TypeError:
                        pass
        flat_class_list = [item for sublist in class_list for item in sublist]
        return set(flat_class_list)
    class_list = get_all_classes(evadb, 1)
    base_id = 0
    ref_object = None
    for class_type in class_list:
        base_id = base_id + 1
        sig = inspect.signature(class_type.__init__)
        params = sig.parameters
        len_params = len(params)
        if 'kwargs' in params:
            len_params = len_params - 1
        if 'args' in params:
            len_params = len_params - 1
        try:
            dummy_object = get_mock_object(class_type, len_params)
        except Exception:
            continue
        if base_id == 0:
            ref_object = dummy_object
        else:
            self.assertEqual(dummy_object, dummy_object)
            self.assertNotEqual(ref_object, dummy_object)
        try:
            inspect.signature(class_type.name)
        except Exception:
            continue
        name_str = dummy_object.name()
        self.assertTrue(name_str is not None)

def stop_server():
    """
    Stop the evadb server
    """
    for proc in process_iter():
        if proc.name() == 'evadb_server':
            proc.send_signal(SIGTERM)
    return 0

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

def clear_children(self):
    self.children.clear()

def __copy__(self):
    cls = self.__class__
    result = cls.__new__(cls)
    for k, v in self.__dict__.items():
        if k == '_children':
            setattr(result, k, [])
        else:
            setattr(result, k, v)
    return result

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

def __copy__(self):
    cls = self.__class__
    result = cls.__new__(cls)
    for k, v in self.__dict__.items():
        if k == '_children':
            setattr(result, k, [])
        else:
            setattr(result, k, v)
    return result

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

def __init__(self):
    self._group_exprs: Dict[int, GroupExpression] = dict()
    self._groups = dict()

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

def clear_grp_exprs(self):
    self._logical_exprs.clear()
    self._physical_exprs.clear()

@contextlib.contextmanager
def set_env(**environ):
    """
    Temporarily set the process environment variables.

    >>> with set_env(PLUGINS_DIR='test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)

def str_to_class(class_path: str):
    """
    Convert string representation of a class path to Class

    Arguments:
        class_path (str): absolute path of import

    Returns:
        type: A Class for given path
    """
    assert class_path is not None, 'Class path is not found'
    module_path, class_name = class_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def load_function_class_from_file(filepath, classname=None):
    """
    Load a class from a Python file. If the classname is not specified, the function will check if there is only one class in the file and load that. If there are multiple classes, it will raise an error.

    Args:
        filepath (str): The path to the Python file.
        classname (str, optional): The name of the class to load. If not specified, the function will try to load a class with the same name as the file. Defaults to None.

    Returns:
        The class instance.

    Raises:
        ImportError: If the module cannot be loaded.
        FileNotFoundError: If the file cannot be found.
        RuntimeError: Any othe type of runtime error.
    """
    try:
        abs_path = Path(filepath).resolve()
        spec = importlib.util.spec_from_file_location(abs_path.stem, abs_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError as e:
        err_msg = f"ImportError : Couldn't load function from {filepath} : {str(e)}. Not able to load the code provided in the file {abs_path}. Please ensure that the file contains the implementation code for the function."
        raise ImportError(err_msg)
    except FileNotFoundError as e:
        err_msg = f"FileNotFoundError : Couldn't load function from {filepath} : {str(e)}. This might be because the function implementation file does not exist. Please ensure the file exists at {abs_path}"
        raise FileNotFoundError(err_msg)
    except Exception as e:
        err_msg = f"Couldn't load function from {filepath} : {str(e)}."
        raise RuntimeError(err_msg)
    if classname and hasattr(module, classname):
        return getattr(module, classname)
    classes = [obj for _, obj in inspect.getmembers(module, inspect.isclass) if obj.__module__ == module.__name__]
    if len(classes) != 1:
        raise ImportError(f'{filepath} contains {len(classes)} classes, please specify the correct class to load by naming the function with the same name in the CREATE query.')
    return classes[0]

def get_size(obj, seen=None):
    """Recursively finds size of objects
    https://goshippo.com/blog/measure-real-size-any-python-object/
    """
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and (not isinstance(obj, (str, bytes, bytearray))):
        size += sum([get_size(i, seen) for i in obj])
    return size

def rebatch(it: Iterator, batch_mem_size: int=30000000) -> Iterator:
    """
    Utility function to rebatch the rows
    Args:
        it (Iterator): an iterator for rows, every row is a dictionary
        batch_mem_size (int): the maximum batch memory size
    Yields:
        data_batch (List): a list of rows, every row is a dictionary
    """
    data_batch = []
    row_size = None
    for row in it:
        data_batch.append(row)
        if row_size is None:
            row_size = get_size(data_batch)
        if len(data_batch) * row_size >= batch_mem_size:
            yield data_batch
            data_batch = []
    if data_batch:
        yield data_batch

def find_nearest_word(word, word_list):
    from thefuzz import process
    nearest_word_and_score = process.extractOne(word, word_list)
    nearest_word = nearest_word_and_score[0]
    return nearest_word

class DiskKVCache:
    """Disk key value cache

    Args:
        `path` (str): the path on disk where the cache will be stored
        `max_cache_size` (int, optional): an integer representing the maximum size of
            the cache. The system will make its best effort to enforce this limit, but it may slightly exceed it. The default value is 2**30.
        `shards` (int, optional): an integer representing the number of shards to use.
            This can improve concurrent writes. The default value is 3. size limit of
            individual cache shards is the `max_cache_size` divided by the number of
            shards.
    """

    def __init__(self, path: str, max_cache_size: int=2 ** 30, shards: int=3):
        default_settings = {'size_limit': max_cache_size, 'eviction_policy': 'least-recently-stored', 'disk_pickle_protocol': pickle.HIGHEST_PROTOCOL}
        self._path = path
        self._cache = FanoutCache(path, shards=shards, **default_settings)

    def get(self, key: Any):
        value = self._cache.get(key, default=None)
        return value

    def set(self, key: Any, value: Any):
        self._cache.set(key, value)

def set(self, key: Any, value: Any):
    self._cache.set(key, value)

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

def __init__(self, catalog: Callable):
    self._catalog = catalog
    self._table_alias_map: Dict[str, TableCatalogEntry] = dict()
    self._derived_table_alias_map: Dict[str, Dict[str, CatalogColumnType]] = dict()
    self._retrieve_audio = False
    self._retrieve_video = False

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

def extend_star(binder_context: StatementBinderContext) -> List[TupleValueExpression]:
    col_objs = binder_context._get_all_alias_and_col_name()
    target_list = list([TupleValueExpression(name=col_name, table_alias=alias) for alias, col_name in col_objs])
    return target_list

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

class CustomModel:
    """This overrides the default `_declarative_constructor` constructor.

    It skips the attributes that are not present for the model, thus if a
    dict is passed with some unknown attributes for the model on creation,
    it won't complain for `unknown field`s.
    Declares and int `_row_id` field for all tables
    """
    _row_id = Column('_row_id', Integer, primary_key=True)

    def __init__(self, **kwargs):
        cls_ = type(self)
        for k in kwargs:
            if hasattr(cls_, k):
                setattr(self, k, kwargs[k])
            else:
                continue

    def save(self, db_session):
        """Add and commit

        Returns: saved object

        """
        try:
            db_session.add(self)
            self._commit(db_session)
        except Exception as e:
            db_session.rollback()
            logger.error(f'Database save failed : {str(e)}')
            raise e
        return self

    def update(self, db_session, **kwargs):
        """Update and commit

        Args:
            **kwargs: attributes to update

        Returns: updated object

        """
        try:
            for attr, value in kwargs.items():
                if hasattr(self, attr):
                    setattr(self, attr, value)
            return self.save(db_session)
        except Exception as e:
            db_session.rollback()
            logger.error(f'Database update failed : {str(e)}')
            raise e

    def delete(self, db_session):
        """Delete and commit"""
        try:
            db_session.delete(self)
            self._commit(db_session)
        except Exception as e:
            db_session.rollback()
            logger.error(f'Database delete failed : {str(e)}')
            raise e

    def _commit(self, db_session):
        """Try to commit. If an error is raised, the session is rollbacked."""
        try:
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f'Database commit failed : {str(e)}')
            raise e

def __init__(self, **kwargs):
    cls_ = type(self)
    for k in kwargs:
        if hasattr(cls_, k):
            setattr(self, k, kwargs[k])
        else:
            continue

class Parser(object):
    """
    Parser based on EvaDB grammar: evadb.lark
    """
    _lark_parser = None

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Parser, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lark_parser = LarkParser()
        self._initialized = True

    def parse(self, query_string: str) -> list:
        lark_output = self._lark_parser.parse(query_string)
        return lark_output

def __new__(cls):
    if not hasattr(cls, '_instance'):
        cls._instance = super(Parser, cls).__new__(cls)
        cls._instance._initialized = False
    return cls._instance

class AbstractStatement:
    """
    Base class for all Statements

    Attributes
    ----------
    stmt_type : StatementType
        the type of this statement - Select or Insert etc
    """

    def __init__(self, stmt_type: StatementType):
        self._stmt_type = stmt_type

    @property
    def stmt_type(self):
        return self._stmt_type

    def __hash__(self) -> int:
        return hash(self.stmt_type)

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    def copy(self):
        """Returns a deepcopy of the statement."""
        return deepcopy(self)

def __deepcopy__(self, memo):
    cls = self.__class__
    result = cls.__new__(cls)
    memo[id(self)] = result
    for k, v in self.__dict__.items():
        setattr(result, k, deepcopy(v, memo))
    return result

def copy(self):
    """Returns a deepcopy of the statement."""
    return deepcopy(self)

class LarkParser(object):
    """
    Parser for EvaDB QL based on Lark
    """
    _parser = None

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(LarkParser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        lark_path = os.path.join(dir_path, 'evadb.lark')
        with open(lark_path) as f:
            sql_grammar = f.read()
        self._parser = Lark(sql_grammar, parser='lalr')

    def parse(self, query_string: str) -> list:
        query_string = query_string.rstrip()
        if not query_string.endswith(';'):
            query_string += ';'
        tree = self._parser.parse(query_string)
        output = LarkInterpreter(query_string).visit(tree)
        if isinstance(output, list):
            return output
        else:
            return [output]

def __new__(cls):
    if not hasattr(cls, '_instance'):
        cls._instance = super(LarkParser, cls).__new__(cls)
    return cls._instance

def dynamic_import(handler_dir):
    import_path = f'evadb.third_party.databases.{handler_dir}.{handler_dir}_handler'
    return importlib.import_module(import_path)

class GithubHandler(DBHandler):

    def __init__(self, name: str, **kwargs):
        """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
        super().__init__(name)
        self.owner = kwargs.get('owner', '')
        self.repo = kwargs.get('repo', '')
        self.github_token = kwargs.get('github_token', '')

    @property
    def supported_table(self):

        def _stargazer_generator():
            for stargazer in self.connection.get_repo('{}/{}'.format(self.owner, self.repo)).get_stargazers():
                yield {property_name: getattr(stargazer, property_name) for property_name, _ in STARGAZERS_COLUMNS}
        mapping = {'stargazers': {'columns': STARGAZERS_COLUMNS, 'generator': _stargazer_generator()}}
        return mapping

    def connect(self):
        """
        Set up the connection required by the handler.
        Returns:
            DBHandlerStatus
        """
        try:
            if self.github_token:
                self.connection = github.Github(self.github_token)
            else:
                self.connection = github.Github()
            return DBHandlerStatus(status=True)
        except Exception as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        Close any existing connections.
        """
        pass

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
            tables_df = pd.DataFrame(list(self.supported_table.keys()), columns=['table_name'])
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
            columns_df = pd.DataFrame(self.supported_table[table_name]['columns'], columns=['name', 'dtype'])
            return DBHandlerResponse(data=columns_df)
        except Exception as e:
            return DBHandlerResponse(data=None, error=str(e))

    def select(self, table_name: str) -> DBHandlerResponse:
        """
        Returns a generator that yields the data from the given table.
        Args:
            table_name (str): name of the table whose data is to be retrieved.
        Returns:
            DBHandlerResponse
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            if table_name not in self.supported_table:
                return DBHandlerResponse(data=None, error='{} is not supported or does not exist.'.format(table_name))
            return DBHandlerResponse(data=None, data_generator=self.supported_table[table_name]['generator'])
        except Exception as e:
            return DBHandlerResponse(data=None, error=str(e))

def _stargazer_generator():
    for stargazer in self.connection.get_repo('{}/{}'.format(self.owner, self.repo)).get_stargazers():
        yield {property_name: getattr(stargazer, property_name) for property_name, _ in STARGAZERS_COLUMNS}

class Open(AbstractFunction):

    def setup(self):
        self._data_cache = dict()
        try_to_import_cv2()

    @property
    def name(self):
        return 'Open'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Open image from server-side path.

        Returns:
            (pd.DataFrame): The opened image.
        """

        def _open(row: pd.Series) -> np.ndarray:
            path_str = row[0]
            if path_str in self._data_cache:
                data = self._data_cache[path_str]
            else:
                import cv2
                data = cv2.imread(path_str)
                assert data is not None, f'Failed to open file {path_str}'
            self._data_cache[path_str] = data
            return data
        ret = pd.DataFrame()
        ret['data'] = df.apply(_open, axis=1)
        return ret

def setup(self):
    self._data_cache = dict()
    try_to_import_cv2()

def load_io_from_function_decorators(function: Type[AbstractFunction], is_input=False) -> List[Type[FunctionIOCatalogEntry]]:
    """Load the inputs/outputs from the function decorators and return a list of FunctionIOCatalogEntry objects

    Args:
        function (Object): Function object
        is_input (bool, optional): True if inputs are to be loaded. Defaults to False.

    Returns:
        Type[FunctionIOCatalogEntry]: FunctionIOCatalogEntry object created from the input decorator in setup
    """
    tag_key = 'input' if is_input else 'output'
    io_signature = None
    if hasattr(function.forward, 'tags') and tag_key in function.forward.tags:
        io_signature = function.forward.tags[tag_key]
    else:
        for base_class in function.__bases__:
            if hasattr(base_class, 'forward') and hasattr(base_class.forward, 'tags'):
                if tag_key in base_class.forward.tags:
                    io_signature = base_class.forward.tags[tag_key]
                    break
    assert io_signature is not None, f'Cannot infer {tag_key} signature from the decorator for {function}.\n {missing_io_signature_helper()}'
    result_list = []
    for io in io_signature:
        result_list.extend(io.generate_catalog_entries(is_input))
    return result_list

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

def create_uml_graph(mappers, show_operations=True, show_attributes=True, show_inherited=True, show_multiplicity_one=False, show_datatypes=True, linewidth=1.0, font='Bitstream-Vera Sans'):
    graph = pydot.Dot(prog='neato', mode='major', overlap='0', sep='0.01', dim='3', pack='True', ratio='.75')
    relations = set()
    for mapper in mappers:
        graph.add_node(pydot.Node(escape(mapper.class_.__name__), shape='plaintext', label=_mk_label(mapper, show_operations, show_attributes, show_datatypes, show_inherited, linewidth), fontname=font, fontsize='8.0'))
        if mapper.inherits:
            graph.add_edge(pydot.Edge(escape(mapper.inherits.class_.__name__), escape(mapper.class_.__name__), arrowhead='none', arrowtail='empty', style='setlinewidth(%s)' % linewidth, arrowsize=str(linewidth)))
        for loader in mapper.iterate_properties:
            if isinstance(loader, RelationshipProperty) and loader.mapper in mappers:
                if hasattr(loader, 'reverse_property'):
                    relations.add(frozenset([loader, loader.reverse_property]))
                else:
                    relations.add(frozenset([loader]))
    for relation in relations:
        args = {}

        def multiplicity_indicator(prop):
            if prop.uselist:
                return ' *'
            if hasattr(prop, 'local_side'):
                cols = prop.local_side
            else:
                cols = prop.local_columns
            if any((col.nullable for col in cols)):
                return ' 0..1'
            if show_multiplicity_one:
                return ' 1'
            return ''
        if len(relation) == 2:
            src, dest = relation
            from_name = escape(src.parent.class_.__name__)
            to_name = escape(dest.parent.class_.__name__)

            def calc_label(src, dest):
                return '+' + src.key + multiplicity_indicator(src)
            args['headlabel'] = calc_label(src, dest)
            args['taillabel'] = calc_label(dest, src)
            args['arrowtail'] = 'none'
            args['arrowhead'] = 'none'
            args['constraint'] = False
        else:
            prop, = relation
            from_name = escape(prop.parent.class_.__name__)
            to_name = escape(prop.mapper.class_.__name__)
            args['headlabel'] = '+%s%s' % (prop.key, multiplicity_indicator(prop))
            args['arrowtail'] = 'none'
            args['arrowhead'] = 'vee'
        graph.add_edge(pydot.Edge(from_name, to_name, fontname=font, fontsize='7.0', style='setlinewidth(%s)' % linewidth, arrowsize=str(linewidth), **args))
    return graph

def calc_label(src, dest):
    return '+' + src.key + multiplicity_indicator(src)

def _render_table_html(table, metadata, show_indexes, show_datatypes, show_column_keys, show_schema_name, format_schema_name, format_table_name):
    use_column_key_attr = hasattr(ForeignKeyConstraint, 'column_keys')
    if show_column_keys:
        if use_column_key_attr:
            fk_col_names = set([h for f in table.foreign_key_constraints for h in f.columns.keys()])
        else:
            fk_col_names = set([h.name for f in table.foreign_keys for h in f.constraint.columns])
        pk_col_names = set([f for f in table.primary_key.columns.keys()])
    else:
        fk_col_names = set()
        pk_col_names = set()

    def format_col_type(col):
        try:
            return col.type.get_col_spec()
        except (AttributeError, NotImplementedError):
            return str(col.type)

    def format_col_str(col):
        suffix = '(FK)' if col.name in fk_col_names else '(PK)' if col.name in pk_col_names else ''
        if show_datatypes:
            return '- %s : %s' % (col.name + suffix, format_col_type(col))
        else:
            return '- %s' % (col.name + suffix)

    def format_name(obj_name, format_dict):
        if format_dict is not None:
            return '<FONT COLOR="{color}" POINT-SIZE="{size}">{bld}{it}{name}{e_it}{e_bld}</FONT>'.format(name=obj_name, color=format_dict.get('color') if 'color' in format_dict else 'initial', size=float(format_dict['fontsize']) if 'fontsize' in format_dict else 'initial', it='<I>' if format_dict.get('italics') else '', e_it='</I>' if format_dict.get('italics') else '', bld='<B>' if format_dict.get('bold') else '', e_bld='</B>' if format_dict.get('bold') else '')
        else:
            return obj_name
    schema_str = ''
    if show_schema_name == True and hasattr(table, 'schema') and (table.schema is not None):
        schema_str = format_name(table.schema, format_schema_name)
    table_str = format_name(table.name, format_table_name)
    html = '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0"><TR><TD ALIGN="CENTER">%s%s%s</TD></TR><TR><TD BORDER="1" CELLPADDING="0"></TD></TR>' % (schema_str, '.' if show_schema_name else '', table_str)
    html += ''.join(('<TR><TD ALIGN="LEFT" PORT="%s">%s</TD></TR>' % (col.name, format_col_str(col)) for col in table.columns))
    if metadata.bind and isinstance(metadata.bind.dialect, PGDialect):
        indexes = dict(((name, defin) for name, defin in metadata.bind.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '%s'" % table.name))))
        if indexes and show_indexes:
            html += '<TR><TD BORDER="1" CELLPADDING="0"></TD></TR>'
            for index, defin in indexes.items():
                ilabel = 'UNIQUE' in defin and 'UNIQUE ' or 'INDEX '
                ilabel += defin[defin.index('('):]
                html += '<TR><TD ALIGN="LEFT">%s</TD></TR>' % ilabel
    html += '</TABLE>>'
    return html

def create_schema_graph(tables=None, metadata=None, show_indexes=True, show_datatypes=True, font='Bitstream-Vera Sans', concentrate=True, relation_options={}, rankdir='TB', show_column_keys=False, restrict_tables=None, show_schema_name=False, format_schema_name=None, format_table_name=None):
    """
    Args:
      - metadata (sqlalchemy.MetaData, default=None): SqlAlchemy `MetaData` with reference to related tables.  If none
        is provided, uses metadata from first entry of `tables` argument.
      - concentrate (bool, default=True): Specifies if multiedges should be merged into a single edge & partially
        parallel edges to share overlapping path.  Passed to `pydot.Dot` object.
      - relation_options (dict, default: None): kwargs passed to pydot.Edge init.  Most attributes in
        pydot.EDGE_ATTRIBUTES are viable options.  A few values are set programmatically.
      - rankdir (string, default='TB'): Sets direction of graph layout.  Passed to `pydot.Dot` object.  Options are
        'TB' (top to bottom), 'BT' (bottom to top), 'LR' (left to right), 'RL' (right to left).
      - show_column_keys (bool, default=False): If true then add a PK/FK suffix to columns names that are primary and
        foreign keys.
      - restrict_tables (None or list of strings): Restrict the graph to only consider tables whose name are defined
        `restrict_tables`.
      - show_schema_name (bool, default=False): If true, then prepend '<schema name>.' to the table name resulting in
        '<schema name>.<table name>'.
      - format_schema_name (dict, default=None): If provided, allowed keys include: 'color' (hex color code incl #),
        'fontsize' as a float, and 'bold' and 'italics' as bools.
      - format_table_name (dict, default=None): If provided, allowed keys include: 'color' (hex color code incl #),
        'fontsize' as a float, and 'bold' and 'italics' as bools.
    """
    relation_kwargs = {'fontsize': '7.0', 'dir': 'both'}
    relation_kwargs.update(relation_options)
    if metadata is None and tables is not None and len(tables):
        metadata = tables[0].metadata
    elif tables is None and metadata is not None:
        if not len(metadata.tables):
            metadata.reflect()
        tables = metadata.tables.values()
    else:
        raise ValueError('You need to specify at least tables or metadata')
    if format_schema_name is not None and len(set(format_schema_name.keys()).difference({'color', 'fontsize', 'italics', 'bold'})) > 0:
        raise KeyError('Unrecognized keys were used in dict provided for `format_schema_name` parameter')
    if format_table_name is not None and len(set(format_table_name.keys()).difference({'color', 'fontsize', 'italics', 'bold'})) > 0:
        raise KeyError('Unrecognized keys were used in dict provided for `format_table_name` parameter')
    graph = pydot.Dot(prog='dot', mode='ipsep', overlap='ipsep', sep='0.01', concentrate=str(concentrate), rankdir=rankdir)
    if restrict_tables is None:
        restrict_tables = set([t.name.lower() for t in tables])
    else:
        restrict_tables = set([t.lower() for t in restrict_tables])
    tables = [t for t in tables if t.name.lower() in restrict_tables]
    for table in tables:
        graph.add_node(pydot.Node(str(table.name), shape='plaintext', label=_render_table_html(table, metadata, show_indexes, show_datatypes, show_column_keys, show_schema_name, format_schema_name, format_table_name), fontname=font, fontsize='7.0'))
    for table in tables:
        for fk in table.foreign_keys:
            if fk.column.table not in tables:
                continue
            edge = [table.name, fk.column.table.name]
            is_inheritance = fk.parent.primary_key and fk.column.primary_key
            if is_inheritance:
                edge = edge[::-1]
            graph_edge = pydot.Edge(*edge, headlabel='+ %s' % fk.column.name, taillabel='+ %s' % fk.parent.name, arrowhead=is_inheritance and 'none' or 'odot', arrowtail=(fk.parent.primary_key or fk.parent.unique) and 'empty' or 'crow', fontname=font, **relation_kwargs)
            graph.add_edge(graph_edge)
    return graph

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

