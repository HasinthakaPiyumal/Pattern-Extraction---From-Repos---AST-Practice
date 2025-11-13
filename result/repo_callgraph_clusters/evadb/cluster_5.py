# Cluster 5

def visit_admonition_node(self, node):
    name = type(node).__name__ + ('s' if node.plural else '')
    self.visit_admonition(node, name=name)

@pytest.mark.notparallel
@gpu_skip_marker
class OptimizerRulesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO MyVideo;")
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO MyVideo2;")
        load_functions_for_testing(cls.evadb, mode='debug')

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    @patch('evadb.expression.function_expression.FunctionExpression.evaluate')
    @patch('evadb.models.storage.batch.Batch.merge_column_wise')
    def test_should_benefit_from_pushdown(self, merge_mock, evaluate_mock):
        evaluate_mock.return_value = Batch(pd.DataFrame({'obj.labels': ['car'], 'obj.bboxes': [np.array([1, 2, 3, 4])], 'obj.scores': [0.8]}))
        query = 'SELECT id, obj.labels\n                  FROM MyVideo JOIN LATERAL\n                    FastRCNNObjectDetector(data) AS obj(labels, bboxes, scores)\n                  WHERE id < 2;'
        time_with_rule = Timer()
        result_with_rule = None
        with time_with_rule:
            result_with_rule = execute_query_fetch_all(self.evadb, query)
        evaluate_count_with_rule = evaluate_mock.call_count
        time_without_rule = Timer()
        result_without_pushdown_rules = None
        with time_without_rule:
            rules_manager = RulesManager()
            with disable_rules(rules_manager, [PushDownFilterThroughApplyAndMerge(), PushDownFilterThroughJoin()]):
                custom_plan_generator = PlanGenerator(self.evadb, rules_manager)
                result_without_pushdown_rules = execute_query_fetch_all(self.evadb, query, plan_generator=custom_plan_generator)
        self.assertEqual(result_without_pushdown_rules, result_with_rule)
        evaluate_count_without_rule = evaluate_mock.call_count - evaluate_count_with_rule
        self.assertGreater(evaluate_count_without_rule, 3 * evaluate_count_with_rule)

    def test_should_pushdown_without_pushdown_join_rule(self):
        query = 'SELECT id, obj.labels\n                    FROM MyVideo JOIN LATERAL\n                    FastRCNNObjectDetector(data) AS obj(labels, bboxes, scores)\n                    WHERE id < 2;'
        time_with_rule = Timer()
        result_with_rule = None
        with time_with_rule:
            result_with_rule = execute_query_fetch_all(self.evadb, query)
            query_plan = execute_query_fetch_all(self.evadb, f'EXPLAIN {query}')
        time_without_rule = Timer()
        result_without_pushdown_join_rule = None
        with time_without_rule:
            rules_manager = RulesManager()
            with disable_rules(rules_manager, [PushDownFilterThroughJoin()]):
                custom_plan_generator = PlanGenerator(self.evadb, rules_manager)
                result_without_pushdown_join_rule = execute_query_fetch_all(self.evadb, query, plan_generator=custom_plan_generator)
                query_plan_without_pushdown_join_rule = execute_query_fetch_all(self.evadb, f'EXPLAIN {query}', plan_generator=custom_plan_generator)
        self.assertEqual(result_without_pushdown_join_rule, result_with_rule)
        self.assertEqual(query_plan, query_plan_without_pushdown_join_rule)

    @patch('evadb.catalog.catalog_manager.CatalogManager.get_function_cost_catalog_entry')
    def test_should_reorder_predicates(self, mock):

        def _check_reorder(cost_func):
            mock.side_effect = cost_func
            pred_1 = "DummyObjectDetector(data).label = ['person']"
            pred_2 = "DummyMultiObjectDetector(data).labels @> ['person']"
            query = f'SELECT id FROM MyVideo WHERE {pred_2} AND {pred_1};'
            plan = get_physical_query_plan(self.evadb, query)
            predicate_plans = list(plan.find_all(PredicatePlan))
            self.assertEqual(len(predicate_plans), 1)
            left: ComparisonExpression = predicate_plans[0].predicate.children[0]
            right: ComparisonExpression = predicate_plans[0].predicate.children[1]
            self.assertEqual(left.children[0].name, 'DummyObjectDetector')
            self.assertEqual(right.children[0].name, 'DummyMultiObjectDetector')
        _check_reorder(lambda name: MagicMock(cost=10) if name == 'DummyMultiObjectDetector' else MagicMock(cost=5))
        _check_reorder(lambda name: MagicMock(cost=5) if name == 'DummyObjectDetector' else None)

    @patch('evadb.catalog.catalog_manager.CatalogManager.get_function_cost_catalog_entry')
    def test_should_not_reorder_predicates(self, mock):

        def _check_no_reorder(cost_func):
            mock.side_effect = cost_func
            cheap_pred = "DummyObjectDetector(data).label = ['person']"
            costly_pred = "DummyMultiObjectDetector(data).labels @> ['person']"
            query = f'SELECT id FROM MyVideo WHERE {cheap_pred} AND {costly_pred};'
            plan = get_physical_query_plan(self.evadb, query)
            predicate_plans = list(plan.find_all(PredicatePlan))
            self.assertEqual(len(predicate_plans), 1)
            left: ComparisonExpression = predicate_plans[0].predicate.children[0]
            right: ComparisonExpression = predicate_plans[0].predicate.children[1]
            self.assertEqual(left.children[0].name, 'DummyObjectDetector')
            self.assertEqual(right.children[0].name, 'DummyMultiObjectDetector')
        _check_no_reorder(lambda name: MagicMock(cost=10) if name == 'DummyMultiObjectDetector' else MagicMock(cost=5))
        _check_no_reorder(lambda name: MagicMock(cost=5) if name == 'DummyMultiObjectDetector' else MagicMock(cost=5))
        _check_no_reorder(lambda name: MagicMock(cost=5) if name == 'DummyObjectDetector' else None)
        _check_no_reorder(lambda name: None)

    @patch('evadb.catalog.catalog_manager.CatalogManager.get_function_cost_catalog_entry')
    def test_should_reorder_multiple_predicates(self, mock):

        def side_effect_func(name):
            if name == 'DummyMultiObjectDetector':
                return MagicMock(cost=10)
            else:
                return MagicMock(cost=5)
        mock.side_effect = side_effect_func
        cheapest_pred = 'id<10'
        cheap_pred = "DummyObjectDetector(data).label = ['person']"
        costly_pred = "DummyMultiObjectDetector(data).labels @> ['person']"
        query = f'SELECT id FROM MyVideo WHERE {costly_pred} AND {cheap_pred} AND {cheapest_pred};'
        plan = get_physical_query_plan(self.evadb, query)
        predicate_plans = list(plan.find_all(PredicatePlan))
        self.assertEqual(len(predicate_plans), 1)
        left = predicate_plans[0].predicate.children[0]
        right = predicate_plans[0].predicate.children[1]
        self.assertIsInstance(left, ComparisonExpression)
        self.assertIsInstance(right, ComparisonExpression)
        self.assertEqual(left.children[0].name, 'DummyObjectDetector')
        self.assertEqual(right.children[0].name, 'DummyMultiObjectDetector')

    def test_reorder_rule_should_not_have_side_effects(self):
        query = 'SELECT id FROM MyVideo WHERE id < 20 AND id > 10;'
        result = execute_query_fetch_all(self.evadb, query)
        rules_manager = RulesManager()
        with disable_rules(rules_manager, [ReorderPredicates()]):
            custom_plan_generator = PlanGenerator(self.evadb, rules_manager)
            expected = execute_query_fetch_all(self.evadb, query, plan_generator=custom_plan_generator)
            self.assertEqual(result, expected)

def _check_reorder(cost_func):
    mock.side_effect = cost_func
    pred_1 = "DummyObjectDetector(data).label = ['person']"
    pred_2 = "DummyMultiObjectDetector(data).labels @> ['person']"
    query = f'SELECT id FROM MyVideo WHERE {pred_2} AND {pred_1};'
    plan = get_physical_query_plan(self.evadb, query)
    predicate_plans = list(plan.find_all(PredicatePlan))
    self.assertEqual(len(predicate_plans), 1)
    left: ComparisonExpression = predicate_plans[0].predicate.children[0]
    right: ComparisonExpression = predicate_plans[0].predicate.children[1]
    self.assertEqual(left.children[0].name, 'DummyObjectDetector')
    self.assertEqual(right.children[0].name, 'DummyMultiObjectDetector')

def _check_no_reorder(cost_func):
    mock.side_effect = cost_func
    cheap_pred = "DummyObjectDetector(data).label = ['person']"
    costly_pred = "DummyMultiObjectDetector(data).labels @> ['person']"
    query = f'SELECT id FROM MyVideo WHERE {cheap_pred} AND {costly_pred};'
    plan = get_physical_query_plan(self.evadb, query)
    predicate_plans = list(plan.find_all(PredicatePlan))
    self.assertEqual(len(predicate_plans), 1)
    left: ComparisonExpression = predicate_plans[0].predicate.children[0]
    right: ComparisonExpression = predicate_plans[0].predicate.children[1]
    self.assertEqual(left.children[0].name, 'DummyObjectDetector')
    self.assertEqual(right.children[0].name, 'DummyMultiObjectDetector')

@patch('evadb.catalog.catalog_manager.CatalogManager.get_function_cost_catalog_entry')
def test_should_reorder_multiple_predicates(self, mock):

    def side_effect_func(name):
        if name == 'DummyMultiObjectDetector':
            return MagicMock(cost=10)
        else:
            return MagicMock(cost=5)
    mock.side_effect = side_effect_func
    cheapest_pred = 'id<10'
    cheap_pred = "DummyObjectDetector(data).label = ['person']"
    costly_pred = "DummyMultiObjectDetector(data).labels @> ['person']"
    query = f'SELECT id FROM MyVideo WHERE {costly_pred} AND {cheap_pred} AND {cheapest_pred};'
    plan = get_physical_query_plan(self.evadb, query)
    predicate_plans = list(plan.find_all(PredicatePlan))
    self.assertEqual(len(predicate_plans), 1)
    left = predicate_plans[0].predicate.children[0]
    right = predicate_plans[0].predicate.children[1]
    self.assertIsInstance(left, ComparisonExpression)
    self.assertIsInstance(right, ComparisonExpression)
    self.assertEqual(left.children[0].name, 'DummyObjectDetector')
    self.assertEqual(right.children[0].name, 'DummyMultiObjectDetector')

class HuggingFaceTests(unittest.TestCase):
    """
    The tests below essentially check for the output format returned by HF.
    We need to ensure that it is in the format that we expect.
    """

    def setUp(self) -> None:
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        query = "LOAD VIDEO 'data/ua_detrac/ua_detrac.mp4' INTO DETRAC;"
        execute_query_fetch_all(self.evadb, query)
        query = "LOAD VIDEO 'data/sample_videos/touchdown.mp4' INTO VIDEOS"
        execute_query_fetch_all(self.evadb, query)
        query = "LOAD PDF 'data/documents/pdf_sample1.pdf' INTO MyPDFs;"
        execute_query_fetch_all(self.evadb, query)
        self.csv_file_path = create_text_csv()

    def tearDown(self) -> None:
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS DETRAC;')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS VIDEOS;')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyCSV;')
        file_remove(self.csv_file_path)

    def test_io_catalog_entries_populated(self):
        function_name, task = ('HFObjectDetector', 'image-classification')
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK '{task}'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        catalog = self.evadb.catalog()
        function = catalog.get_function_catalog_entry_by_name(function_name)
        input_entries = catalog.get_function_io_catalog_input_entries(function)
        output_entries = catalog.get_function_io_catalog_output_entries(function)
        self.assertEqual(len(input_entries), 1)
        self.assertEqual(input_entries[0].name, f'{function_name}_IMAGE')
        self.assertEqual(len(output_entries), 2)
        self.assertEqual(output_entries[0].name, 'score')
        self.assertEqual(output_entries[1].name, 'label')

    def test_raise_error_on_unsupported_task(self):
        function_name = 'HFUnsupportedTask'
        task = 'zero-shot-object-detection'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK '{task}'\n        "
        with self.assertRaises(ExecutorError) as exc_info:
            execute_query_fetch_all(self.evadb, create_function_query, do_not_print_exceptions=True)
        self.assertIn(f'Task {task} not supported in EvaDB currently', str(exc_info.exception))

    def test_object_detection(self):
        function_name = 'HFObjectDetector'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'object-detection'\n            MODEL 'facebook/detr-resnet-50';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = f'SELECT {function_name}(data) FROM DETRAC WHERE id < 4;'
        output = execute_query_fetch_all(self.evadb, select_query)
        output_frames = output.frames
        self.assertEqual(len(output_frames.columns), 3)
        self.assertEqual(len(output.frames), 4)
        self.assertTrue(function_name.lower() + '.score' in output_frames.columns)
        self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.score'])))
        self.assertTrue(function_name.lower() + '.label' in output_frames.columns)
        self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.label'])))
        self.assertTrue(function_name.lower() + '.box' in output_frames.columns)
        for bbox in output.frames[function_name.lower() + '.box']:
            self.assertTrue(isinstance(bbox, list))
            bbox = bbox[0]
            self.assertTrue(isinstance(bbox, dict))
            self.assertTrue(len(bbox) == 4)
            self.assertTrue('xmin' in bbox)
            self.assertTrue('ymin' in bbox)
            self.assertTrue('xmax' in bbox)
            self.assertTrue('ymax' in bbox)
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    def test_image_classification(self):
        function_name = 'HFImageClassifier'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'image-classification'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = f'SELECT {function_name}(data) FROM DETRAC WHERE id < 3;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames.columns), 2)
        self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
        self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.score'])))
        self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
        self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.label'])))
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    @pytest.mark.benchmark
    def test_text_classification(self):
        create_table_query = 'CREATE TABLE IF NOT EXISTS MyCSV (\n                id INTEGER UNIQUE,\n                comment TEXT(30)\n            );'
        execute_query_fetch_all(self.evadb, create_table_query)
        load_table_query = f"LOAD CSV '{self.csv_file_path}' INTO MyCSV;"
        execute_query_fetch_all(self.evadb, load_table_query)
        function_name = 'HFTextClassifier'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'text-classification'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = f'SELECT {function_name}(comment) FROM MyCSV;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames.columns), 2)
        self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
        self.assertTrue(all((x in ['POSITIVE', 'NEGATIVE'] for x in output.frames[function_name.lower() + '.label'])))
        self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
        self.assertTrue(all((isinstance(x, float) for x in output.frames[function_name.lower() + '.score'])))
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)
        execute_query_fetch_all(self.evadb, 'DROP TABLE MyCSV;')

    @pytest.mark.benchmark
    def test_automatic_speech_recognition(self):
        function_name = 'SpeechRecognizer'
        create_function = f"CREATE FUNCTION {function_name} TYPE HuggingFace TASK 'automatic-speech-recognition' MODEL 'openai/whisper-base';"
        execute_query_fetch_all(self.evadb, create_function)
        select_query = f'SELECT {function_name}(audio) FROM VIDEOS;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertTrue(output.frames.shape == (1, 1))
        self.assertTrue(output.frames.iloc[0][0].count('touchdown') == 2)
        select_query_with_group_by = f"SELECT {function_name}(SEGMENT(audio)) FROM VIDEOS GROUP BY '240 samples';"
        output = execute_query_fetch_all(self.evadb, select_query_with_group_by)
        self.assertEquals(output.frames.shape, (4, 1))
        self.assertEquals(output.frames.iloc[0][0].count('touchdown'), 1)
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    @pytest.mark.benchmark
    def test_summarization_from_video(self):
        asr_function = 'SpeechRecognizer'
        create_function = f"CREATE FUNCTION {asr_function} TYPE HuggingFace TASK 'automatic-speech-recognition' MODEL 'openai/whisper-base';"
        execute_query_fetch_all(self.evadb, create_function)
        summary_function = 'Summarizer'
        create_function = f"CREATE FUNCTION {summary_function} TYPE HuggingFace TASK 'summarization' MODEL 'philschmid/bart-large-cnn-samsum' MIN_LENGTH 10 MAX_NEW_TOKENS 100;"
        execute_query_fetch_all(self.evadb, create_function)
        select_query = f'SELECT {summary_function}({asr_function}(audio)) FROM VIDEOS;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertTrue(output.frames.shape == (1, 1))
        self.assertTrue(output.frames.iloc[0][0] == 'Jalen Hurts has scored his second rushing touchdown of the game.')
        drop_function_query = f'DROP FUNCTION {asr_function};'
        execute_query_fetch_all(self.evadb, drop_function_query)
        drop_function_query = f'DROP FUNCTION {summary_function};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    def test_toxicity_classification(self):
        function_name = 'HFToxicityClassifier'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'text-classification'\n            MODEL 'martin-ha/toxic-comment-model'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        drop_table_query = 'DROP TABLE IF EXISTS MyCSV;'
        execute_query_fetch_all(self.evadb, drop_table_query)
        create_table_query = 'CREATE TABLE IF NOT EXISTS MyCSV (\n                id INTEGER UNIQUE,\n                comment TEXT(30)\n            );'
        execute_query_fetch_all(self.evadb, create_table_query)
        load_table_query = f"LOAD CSV '{self.csv_file_path}' INTO MyCSV;"
        execute_query_fetch_all(self.evadb, load_table_query)
        select_query = f'SELECT {function_name}(comment) FROM MyCSV;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames.columns), 2)
        self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
        self.assertTrue(all((x in ['non-toxic', 'toxic'] for x in output.frames[function_name.lower() + '.label'])))
        self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
        self.assertTrue(all((isinstance(x, float) for x in output.frames[function_name.lower() + '.score'])))
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    @pytest.mark.benchmark
    def test_multilingual_toxicity_classification(self):
        function_name = 'HFMultToxicityClassifier'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'text-classification'\n            MODEL 'EIStakovskii/xlm_roberta_base_multilingual_toxicity_classifier_plus'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        drop_table_query = 'DROP TABLE IF EXISTS MyCSV;'
        execute_query_fetch_all(self.evadb, drop_table_query)
        create_table_query = 'CREATE TABLE MyCSV (\n                id INTEGER UNIQUE,\n                comment TEXT(30)\n            );'
        execute_query_fetch_all(self.evadb, create_table_query)
        load_table_query = f"LOAD CSV '{self.csv_file_path}' INTO MyCSV;"
        execute_query_fetch_all(self.evadb, load_table_query)
        select_query = f'SELECT {function_name}(comment) FROM MyCSV;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames.columns), 2)
        self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
        self.assertTrue(all((x in ['LABEL_1', 'LABEL_0'] for x in output.frames[function_name.lower() + '.label'])))
        self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
        self.assertTrue(all((isinstance(x, float) for x in output.frames[function_name.lower() + '.score'])))
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    @pytest.mark.benchmark
    def test_named_entity_recognition_model_all_pdf_data(self):
        function_name = 'HFNERModel'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'ner'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = f'SELECT data, {function_name}(data) FROM MyPDFs;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames.columns), 7)
        self.assertTrue(function_name.lower() + '.entity' in output.frames.columns)
        self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

    def test_select_and_groupby_with_paragraphs(self):
        segment_size = 10
        select_query = "SELECT SEGMENT(data) FROM MyPDFs GROUP BY '{}paragraphs';".format(segment_size)
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames), 3)

    @pytest.mark.benchmark
    def test_named_entity_recognition_model_no_ner_data_exists(self):
        function_name = 'HFNERModel'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'ner'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = f'SELECT data, {function_name}(data)\n                  FROM MyPDFs\n                  WHERE page = 3\n                  AND paragraph >= 1 AND paragraph <= 3;'
        output = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(output.frames.columns), 1)
        self.assertFalse(function_name.lower() + '.entity' in output.frames.columns)
        drop_function_query = f'DROP FUNCTION {function_name};'
        execute_query_fetch_all(self.evadb, drop_function_query)

def test_object_detection(self):
    function_name = 'HFObjectDetector'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'object-detection'\n            MODEL 'facebook/detr-resnet-50';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = f'SELECT {function_name}(data) FROM DETRAC WHERE id < 4;'
    output = execute_query_fetch_all(self.evadb, select_query)
    output_frames = output.frames
    self.assertEqual(len(output_frames.columns), 3)
    self.assertEqual(len(output.frames), 4)
    self.assertTrue(function_name.lower() + '.score' in output_frames.columns)
    self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.score'])))
    self.assertTrue(function_name.lower() + '.label' in output_frames.columns)
    self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.label'])))
    self.assertTrue(function_name.lower() + '.box' in output_frames.columns)
    for bbox in output.frames[function_name.lower() + '.box']:
        self.assertTrue(isinstance(bbox, list))
        bbox = bbox[0]
        self.assertTrue(isinstance(bbox, dict))
        self.assertTrue(len(bbox) == 4)
        self.assertTrue('xmin' in bbox)
        self.assertTrue('ymin' in bbox)
        self.assertTrue('xmax' in bbox)
        self.assertTrue('ymax' in bbox)
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)

def test_image_classification(self):
    function_name = 'HFImageClassifier'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'image-classification'\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = f'SELECT {function_name}(data) FROM DETRAC WHERE id < 3;'
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames.columns), 2)
    self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
    self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.score'])))
    self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
    self.assertTrue(all((isinstance(x, list) for x in output.frames[function_name.lower() + '.label'])))
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)

@pytest.mark.benchmark
def test_text_classification(self):
    create_table_query = 'CREATE TABLE IF NOT EXISTS MyCSV (\n                id INTEGER UNIQUE,\n                comment TEXT(30)\n            );'
    execute_query_fetch_all(self.evadb, create_table_query)
    load_table_query = f"LOAD CSV '{self.csv_file_path}' INTO MyCSV;"
    execute_query_fetch_all(self.evadb, load_table_query)
    function_name = 'HFTextClassifier'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'text-classification'\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = f'SELECT {function_name}(comment) FROM MyCSV;'
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames.columns), 2)
    self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
    self.assertTrue(all((x in ['POSITIVE', 'NEGATIVE'] for x in output.frames[function_name.lower() + '.label'])))
    self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
    self.assertTrue(all((isinstance(x, float) for x in output.frames[function_name.lower() + '.score'])))
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)
    execute_query_fetch_all(self.evadb, 'DROP TABLE MyCSV;')

def test_toxicity_classification(self):
    function_name = 'HFToxicityClassifier'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'text-classification'\n            MODEL 'martin-ha/toxic-comment-model'\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    drop_table_query = 'DROP TABLE IF EXISTS MyCSV;'
    execute_query_fetch_all(self.evadb, drop_table_query)
    create_table_query = 'CREATE TABLE IF NOT EXISTS MyCSV (\n                id INTEGER UNIQUE,\n                comment TEXT(30)\n            );'
    execute_query_fetch_all(self.evadb, create_table_query)
    load_table_query = f"LOAD CSV '{self.csv_file_path}' INTO MyCSV;"
    execute_query_fetch_all(self.evadb, load_table_query)
    select_query = f'SELECT {function_name}(comment) FROM MyCSV;'
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames.columns), 2)
    self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
    self.assertTrue(all((x in ['non-toxic', 'toxic'] for x in output.frames[function_name.lower() + '.label'])))
    self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
    self.assertTrue(all((isinstance(x, float) for x in output.frames[function_name.lower() + '.score'])))
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)

@pytest.mark.benchmark
def test_multilingual_toxicity_classification(self):
    function_name = 'HFMultToxicityClassifier'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'text-classification'\n            MODEL 'EIStakovskii/xlm_roberta_base_multilingual_toxicity_classifier_plus'\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    drop_table_query = 'DROP TABLE IF EXISTS MyCSV;'
    execute_query_fetch_all(self.evadb, drop_table_query)
    create_table_query = 'CREATE TABLE MyCSV (\n                id INTEGER UNIQUE,\n                comment TEXT(30)\n            );'
    execute_query_fetch_all(self.evadb, create_table_query)
    load_table_query = f"LOAD CSV '{self.csv_file_path}' INTO MyCSV;"
    execute_query_fetch_all(self.evadb, load_table_query)
    select_query = f'SELECT {function_name}(comment) FROM MyCSV;'
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames.columns), 2)
    self.assertTrue(function_name.lower() + '.label' in output.frames.columns)
    self.assertTrue(all((x in ['LABEL_1', 'LABEL_0'] for x in output.frames[function_name.lower() + '.label'])))
    self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
    self.assertTrue(all((isinstance(x, float) for x in output.frames[function_name.lower() + '.score'])))
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)

@pytest.mark.benchmark
def test_named_entity_recognition_model_all_pdf_data(self):
    function_name = 'HFNERModel'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'ner'\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = f'SELECT data, {function_name}(data) FROM MyPDFs;'
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames.columns), 7)
    self.assertTrue(function_name.lower() + '.entity' in output.frames.columns)
    self.assertTrue(function_name.lower() + '.score' in output.frames.columns)
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)

@pytest.mark.benchmark
def test_named_entity_recognition_model_no_ner_data_exists(self):
    function_name = 'HFNERModel'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'ner'\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = f'SELECT data, {function_name}(data)\n                  FROM MyPDFs\n                  WHERE page = 3\n                  AND paragraph >= 1 AND paragraph <= 3;'
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames.columns), 1)
    self.assertFalse(function_name.lower() + '.entity' in output.frames.columns)
    drop_function_query = f'DROP FUNCTION {function_name};'
    execute_query_fetch_all(self.evadb, drop_function_query)

@pytest.mark.notparallel
class PytorchTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))
        ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
        mnist = f'{EvaDB_ROOT_DIR}/data/mnist/mnist.mp4'
        actions = f'{EvaDB_ROOT_DIR}/data/actions/actions.mp4'
        asl_actions = f'{EvaDB_ROOT_DIR}/data/actions/computer_asl.mp4'
        meme1 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme1.jpg'
        meme2 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme2.jpg'
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO MyVideo;")
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{mnist}' INTO MNIST;")
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{actions}' INTO Actions;")
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{asl_actions}' INTO Asl_actions;")
        execute_query_fetch_all(cls.evadb, f"LOAD IMAGE '{meme1}' INTO MemeImages;")
        execute_query_fetch_all(cls.evadb, f"LOAD IMAGE '{meme2}' INTO MemeImages;")
        load_functions_for_testing(cls.evadb)

    @classmethod
    def tearDownClass(cls):
        file_remove('ua_detrac.mp4')
        file_remove('mnist.mp4')
        file_remove('actions.mp4')
        file_remove('computer_asl.mp4')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS Actions;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MNIST;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS Asl_actions;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MemeImages;')

    def assertBatchEqual(self, a: Batch, b: Batch, msg: str):
        try:
            pd_testing.assert_frame_equal(a.frames, b.frames)
        except AssertionError as e:
            raise self.failureException(msg) from e

    def setUp(self):
        self.addTypeEqualityFunc(Batch, self.assertBatchEqual)

    def tearDown(self) -> None:
        shutdown_ray()

    @ray_skip_marker
    def test_should_apply_parallel_match_sequential(self):
        select_query = 'SELECT id, obj.labels\n                          FROM MyVideo JOIN LATERAL\n                          FastRCNNObjectDetector(data)\n                          AS obj(labels, bboxes, scores)\n                         WHERE id < 20;'
        par_batch = execute_query_fetch_all(self.evadb, select_query)
        self.evadb.config.update_value('experimental', 'ray', False)
        select_query = 'SELECT id, obj.labels\n                          FROM MyVideo JOIN LATERAL\n                          FastRCNNObjectDetector(data)\n                          AS obj(labels, bboxes, scores)\n                         WHERE id < 20;'
        seq_batch = execute_query_fetch_all(self.evadb, select_query)
        self.evadb.config.update_value('experimental', 'ray', True)
        self.assertEqual(len(par_batch), len(seq_batch))
        self.assertEqual(par_batch, seq_batch)

    @ray_skip_marker
    def test_should_project_parallel_match_sequential(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS FaceDetector\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  FaceDetection\n                  IMPL  'evadb/functions/face_detector.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT FaceDetector(data) FROM MyVideo WHERE id < 5;'
        par_batch = execute_query_fetch_all(self.evadb, select_query)
        self.evadb.config.update_value('experimental', 'ray', False)
        seq_batch = execute_query_fetch_all(self.evadb, select_query)
        self.evadb.config.update_value('experimental', 'ray', True)
        self.assertEqual(len(par_batch), len(seq_batch))
        self.assertEqual(par_batch, seq_batch)

    def test_should_raise_exception_with_parallel(self):
        video_path = create_sample_video(100)
        load_query = f"LOAD VIDEO '{video_path}' INTO parallelErrorVideo;"
        execute_query_fetch_all(self.evadb, load_query)
        file_remove('dummy.avi')
        select_query = 'SELECT id, obj.labels\n                          FROM parallelErrorVideo JOIN LATERAL\n                          FastRCNNObjectDetector(data)\n                          AS obj(labels, bboxes, scores)\n                         WHERE id < 2;'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, select_query, do_not_print_exceptions=True)

    @pytest.mark.torchtest
    def test_should_run_pytorch_and_fastrcnn_with_lateral_join(self):
        select_query = 'SELECT id, obj.labels\n                          FROM MyVideo JOIN LATERAL\n                          FastRCNNObjectDetector(data)\n                          AS obj(labels, bboxes, scores)\n                         WHERE id < 2;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 2)

    @pytest.mark.torchtest
    def test_should_run_pytorch_and_yolo_and_mvit(self):
        execute_query_fetch_all(self.evadb, Mvit_function_query)
        select_query = "SELECT FIRST(id),\n                            Yolo(FIRST(data)),\n                            MVITActionRecognition(SEGMENT(data))\n                            FROM Actions\n                            WHERE id < 32\n                            GROUP BY '16 frames'; "
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 2)
        res = actual_batch.frames
        for idx in res.index:
            self.assertTrue('person' in res['yolo.labels'][idx] and 'yoga' in res['mvitactionrecognition.labels'][idx])

    @pytest.mark.torchtest
    def test_should_run_pytorch_and_asl(self):
        execute_query_fetch_all(self.evadb, Asl_function_query)
        select_query = "SELECT FIRST(id), ASLActionRecognition(SEGMENT(data))\n                        FROM Asl_actions\n                        SAMPLE 5\n                        GROUP BY '16 frames';"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        res = actual_batch.frames
        self.assertEqual(len(res), 1)
        for idx in res.index:
            self.assertTrue('computer' in res['aslactionrecognition.labels'][idx])

    @pytest.mark.torchtest
    def test_should_run_pytorch_and_facenet(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS FaceDetector\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  FaceDetection\n                  IMPL  'evadb/functions/face_detector.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT FaceDetector(data) FROM MyVideo\n                        WHERE id < 5 order by scores;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 5)

    @pytest.mark.torchtest
    @windows_skip_marker
    @ocr_skip_marker
    def test_should_run_pytorch_and_ocr(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS OCRExtractor\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (labels NDARRAY STR(10),\n                          bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  OCRExtraction\n                  IMPL  'evadb/functions/ocr_extractor.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT OCRExtractor(data) FROM MNIST\n                        WHERE id >= 150 AND id < 155;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 5)
        res = actual_batch.frames
        self.assertTrue(res['ocrextractor.labels'][0][0] == '4')
        self.assertTrue(res['ocrextractor.scores'][2][0] > 0.9)

    @pytest.mark.torchtest
    def test_should_run_pytorch_and_resnet50(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS FeatureExtractor\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (features NDARRAY FLOAT32(ANYDIM))\n                  TYPE  Classification\n                  IMPL  'evadb/functions/feature_extractor.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT FeatureExtractor(data) FROM MyVideo\n                        WHERE id < 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 5)
        res = actual_batch.frames
        self.assertEqual(res['featureextractor.features'][0].shape, (1, 2048))

    @pytest.mark.torchtest
    def test_should_run_pytorch_and_similarity(self):
        create_open_function_query = 'CREATE FUNCTION IF NOT EXISTS Open\n                INPUT (img_path TEXT(1000))\n                OUTPUT (data NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                TYPE NdarrayFUNCTION\n                IMPL "evadb/functions/ndarray/open.py";\n        '
        execute_query_fetch_all(self.evadb, create_open_function_query)
        create_similarity_function_query = 'CREATE FUNCTION IF NOT EXISTS Similarity\n                    INPUT (Frame_Array_Open NDARRAY UINT8(3, ANYDIM, ANYDIM),\n                           Frame_Array_Base NDARRAY UINT8(3, ANYDIM, ANYDIM),\n                           Feature_Extractor_Name TEXT(100))\n                    OUTPUT (distance FLOAT(32, 7))\n                    TYPE NdarrayFUNCTION\n                    IMPL "evadb/functions/ndarray/similarity.py";\n        '
        execute_query_fetch_all(self.evadb, create_similarity_function_query)
        create_feat_function_query = 'CREATE FUNCTION IF NOT EXISTS FeatureExtractor\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (features NDARRAY FLOAT32(ANYDIM))\n                  TYPE  Classification\n                  IMPL  "evadb/functions/feature_extractor.py";\n        '
        execute_query_fetch_all(self.evadb, create_feat_function_query)
        select_query = 'SELECT data FROM MyVideo WHERE id = 1;'
        batch_res = execute_query_fetch_all(self.evadb, select_query)
        img = batch_res.frames['myvideo.data'][0]
        tmp_dir_from_config = self.evadb.catalog().get_configuration_catalog_value('tmp_dir')
        img_save_path = os.path.join(tmp_dir_from_config, 'dummy.jpg')
        try:
            os.remove(img_save_path)
        except FileNotFoundError:
            pass
        try_to_import_cv2()
        import cv2
        cv2.imwrite(img_save_path, img)
        similarity_query = 'SELECT data FROM MyVideo WHERE id < 5\n                    ORDER BY Similarity(FeatureExtractor(Open("{}")),\n                                        FeatureExtractor(data))\n                    LIMIT 1;'.format(img_save_path)
        actual_batch = execute_query_fetch_all(self.evadb, similarity_query)
        similar_data = actual_batch.frames['myvideo.data'][0]
        self.assertTrue(np.array_equal(img, similar_data))

    @pytest.mark.torchtest
    @windows_skip_marker
    @ocr_skip_marker
    def test_should_run_ocr_on_cropped_data(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS OCRExtractor\n                  INPUT  (text NDARRAY STR(100))\n                  OUTPUT (labels NDARRAY STR(10),\n                          bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  OCRExtraction\n                  IMPL  'evadb/functions/ocr_extractor.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT OCRExtractor(Crop(data, [2, 2, 24, 24])) FROM MNIST\n                        WHERE id >= 150 AND id < 155;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 5)
        res = actual_batch.frames
        self.assertTrue(res['ocrextractor.labels'][0][0] == '4')
        self.assertTrue(res['ocrextractor.scores'][2][0] > 0.9)

    @pytest.mark.torchtest
    @gpu_skip_marker
    def test_should_run_extract_object(self):
        select_query = '\n            SELECT id, T.iids, T.bboxes, T.scores, T.labels\n            FROM MyVideo JOIN LATERAL EXTRACT_OBJECT(data, Yolo, NorFairTracker)\n                AS T(iids, labels, bboxes, scores)\n            WHERE id < 30;\n            '
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 30)
        num_of_entries = actual_batch.frames['T.iids'].apply(lambda x: len(x)).sum()
        select_query = '\n            SELECT id, T.iid, T.bbox, T.score, T.label\n            FROM MyVideo JOIN LATERAL\n                UNNEST(EXTRACT_OBJECT(data, Yolo, NorFairTracker)) AS T(iid, label, bbox, score)\n            WHERE id < 30;\n            '
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), num_of_entries)

    def test_check_unnest_with_predicate_on_yolo(self):
        query = "SELECT id, Yolo.label, Yolo.bbox, Yolo.score\n                  FROM MyVideo\n                  JOIN LATERAL UNNEST(Yolo(data)) AS Yolo(label, bbox, score)\n                  WHERE Yolo.label = 'car' AND id < 2;"
        actual_batch = execute_query_fetch_all(self.evadb, query)
        self.assertTrue(len(actual_batch) > 2)

@ray_skip_marker
def test_should_apply_parallel_match_sequential(self):
    select_query = 'SELECT id, obj.labels\n                          FROM MyVideo JOIN LATERAL\n                          FastRCNNObjectDetector(data)\n                          AS obj(labels, bboxes, scores)\n                         WHERE id < 20;'
    par_batch = execute_query_fetch_all(self.evadb, select_query)
    self.evadb.config.update_value('experimental', 'ray', False)
    select_query = 'SELECT id, obj.labels\n                          FROM MyVideo JOIN LATERAL\n                          FastRCNNObjectDetector(data)\n                          AS obj(labels, bboxes, scores)\n                         WHERE id < 20;'
    seq_batch = execute_query_fetch_all(self.evadb, select_query)
    self.evadb.config.update_value('experimental', 'ray', True)
    self.assertEqual(len(par_batch), len(seq_batch))
    self.assertEqual(par_batch, seq_batch)

@ray_skip_marker
def test_should_project_parallel_match_sequential(self):
    create_function_query = "CREATE FUNCTION IF NOT EXISTS FaceDetector\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  FaceDetection\n                  IMPL  'evadb/functions/face_detector.py';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = 'SELECT FaceDetector(data) FROM MyVideo WHERE id < 5;'
    par_batch = execute_query_fetch_all(self.evadb, select_query)
    self.evadb.config.update_value('experimental', 'ray', False)
    seq_batch = execute_query_fetch_all(self.evadb, select_query)
    self.evadb.config.update_value('experimental', 'ray', True)
    self.assertEqual(len(par_batch), len(seq_batch))
    self.assertEqual(par_batch, seq_batch)

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

def test_rename_plan(self):
    dummy_info = TableInfo('old')
    dummy_old = TableRef(dummy_info)
    dummy_new = TableInfo('new')
    dummy_plan_node = RenamePlan(dummy_old, dummy_new)
    self.assertEqual(dummy_plan_node.opr_type, PlanOprType.RENAME)
    self.assertEqual(dummy_plan_node.old_table.table.table_name, 'old')
    self.assertEqual(dummy_plan_node.new_name.table_name, 'new')

class ParserStatementTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_parser_statement_types(self):
        parser = Parser()
        queries = ['CREATE INDEX testindex ON MyVideo (featCol) USING FAISS;', 'CREATE TABLE IF NOT EXISTS Persons (\n                  Frame_ID INTEGER UNIQUE,\n                  Frame_Data TEXT(10),\n                  Frame_Value FLOAT(1000, 201),\n                  Frame_Array NDARRAY UINT8(5, 100, 2432, 4324, 100)\n            )', 'RENAME TABLE student TO student_info', 'DROP TABLE IF EXISTS student_info', 'DROP TABLE student_info', 'DROP FUNCTION FastRCNN;', 'SELECT MIN(id), MAX(id), SUM(id) FROM ABC', "SELECT CLASS FROM TAIPAI                 WHERE (CLASS = 'VAN' AND REDNESS < 300)  OR REDNESS > 500;", 'SELECT CLASS, REDNESS FROM TAIPAI             UNION ALL SELECT CLASS, REDNESS FROM SHANGHAI;', 'SELECT CLASS, REDNESS FROM TAIPAI             UNION SELECT CLASS, REDNESS FROM SHANGHAI;', "SELECT FIRST(id) FROM TAIPAI GROUP BY '8 frames';", "SELECT CLASS, REDNESS FROM TAIPAI                     WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700                     ORDER BY CLASS, REDNESS DESC;", "INSERT INTO MyVideo (Frame_ID, Frame_Path)                                    VALUES    (1, '/mnt/frames/1.png');", 'INSERT INTO testDeleteOne (id, feat, salary, input)\n                VALUES (15, 2.5, [[100, 100, 100]], [[100, 100, 100]]);', 'DELETE FROM Foo WHERE id < 6', "LOAD VIDEO 'data/video.mp4' INTO MyVideo", "LOAD IMAGE 'data/pic.jpg' INTO MyImage", "LOAD CSV 'data/meta.csv' INTO\n                             MyMeta (id, frame_id, video_id, label);", "SELECT Licence_plate(bbox) FROM\n                            (SELECT Yolo(frame).bbox FROM autonomous_vehicle_1\n                              WHERE Yolo(frame).label = 'vehicle') AS T\n                          WHERE Is_suspicious(bbox) = 1 AND\n                                Licence_plate(bbox) = '12345';", 'CREATE TABLE uadtrac_fastRCNN AS\n               SELECT id, Yolo(frame).labels FROM MyVideo\n                        WHERE id<5; ', 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a WHERE table1.a <= 5', 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a JOIN table3\n            ON table3.a = table1.a WHERE table1.a <= 5', 'SELECT frame FROM MyVideo JOIN LATERAL\n                            ObjectDet(frame) AS OD;', "CREATE FUNCTION FaceDetector\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  FaceDetection\n                  IMPL  'evadb/functions/face_detector.py';\n            ", 'SHOW TABLES;', 'SHOW FUNCTIONS;', 'SHOW DATABASES;', 'EXPLAIN SELECT a FROM foo;', 'SELECT HomeRentalForecast(12);', 'SELECT data FROM MyVideo WHERE id < 5\n                    ORDER BY Similarity(FeatureExtractor(Open("abc.jpg")),\n                                        FeatureExtractor(data))\n                    LIMIT 1;']
        randomized_cases = ['Create index TestIndex on MyVideo (featCol) using FAISS;', 'create table if not exists Persons (\n                    Frame_ID integer unique,\n                    Frame_Data text(10),\n                    Frame_Value float(1000, 201),\n                    Frame_Array ndArray uint8(5, 100, 2432, 4324, 100)\n            )', 'Rename Table STUDENT to student_info', 'drop table if exists Student_info', 'drop table Student_Info', 'Drop function FASTRCNN;', 'Select min(id), max(Id), Sum(Id) from ABC', "select CLASS from Taipai where (Class = 'VAN' and REDNESS < 300) or Redness > 500;", 'select class, REDNESS from TAIPAI Union all select Class, redness from Shanghai;', 'Select class, redness from Taipai Union Select CLASS, redness from Shanghai;', "Select first(Id) from Taipai group by '8F';", "Select Class, redness from TAIPAI\n                where (CLASS = 'VAN' and redness < 400 ) or REDNESS > 700\n                order by Class, redness DESC;", "Insert into MyVideo (Frame_ID, Frame_Path) values (1, '/mnt/frames/1.png');", 'insert into testDeleteOne (Id, feat, salary, input)\n                values (15, 2.5, [[100, 100, 100]], [[100, 100, 100]]);', 'delete from Foo where ID < 6', "Load video 'data/video.mp4' into MyVideo", "Load image 'data/pic.jpg' into MyImage", "Load csv 'data/meta.csv' into\n                MyMeta (id, Frame_ID, video_ID, label);", "select Licence_plate(bbox) from\n                (select Yolo(Frame).bbox from autonomous_vehicle_1\n                where Yolo(frame).label = 'vehicle') as T\n                where is_suspicious(bbox) = 1 and\n                Licence_plate(bbox) = '12345';", 'Create TABLE UADTrac_FastRCNN as\n                Select id, YoloV5(Frame).labels from MyVideo\n                    where id<5; ', 'Select Table1.A from Table1 join Table2\n                on Table1.A = Table2.a where Table1.A <= 5', 'Select Table1.A from Table1 Join Table2\n                    On Table1.a = Table2.A Join Table3\n                On Table3.A = Table1.A where Table1.a <= 5', 'Select Frame from MyVideo Join Lateral\n                ObjectDet(Frame) as OD;', "Create FUNCTION FaceDetector\n                Input (Frame ndArray uint8(3, anydim, anydim))\n                Output (bboxes ndArray float32(anydim, 4),\n                scores ndArray float32(ANYdim))\n                Type FaceDetection\n                Impl 'evadb/functions/face_detector.py';\n            ", 'CREATE DATABASE example_db\n                WITH ENGINE = "postgres",\n                PARAMETERS = {\n                    "user": "demo_user",\n                    "password": "demo_password",\n                    "host": "3.220.66.106",\n                    "port": "5432",\n                    "database": "demo"\n                };\n            ']
        queries = queries + randomized_cases
        ref_stmt = parser.parse(queries[0])[0]
        self.assertNotEqual(ref_stmt, None)
        self.assertNotEqual(ref_stmt.__str__(), None)
        statement_to_query_dict = {}
        statement_to_query_dict[ref_stmt] = queries[0]
        for other_query in queries[1:]:
            stmt = parser.parse(other_query)[0]
            self.assertNotEqual(stmt, ref_stmt)
            self.assertEqual(stmt, stmt)
            self.assertNotEqual(stmt, None)
            self.assertNotEqual(stmt.__str__(), None)
            statement_to_query_dict[stmt] = other_query

def test_parser_statement_types(self):
    parser = Parser()
    queries = ['CREATE INDEX testindex ON MyVideo (featCol) USING FAISS;', 'CREATE TABLE IF NOT EXISTS Persons (\n                  Frame_ID INTEGER UNIQUE,\n                  Frame_Data TEXT(10),\n                  Frame_Value FLOAT(1000, 201),\n                  Frame_Array NDARRAY UINT8(5, 100, 2432, 4324, 100)\n            )', 'RENAME TABLE student TO student_info', 'DROP TABLE IF EXISTS student_info', 'DROP TABLE student_info', 'DROP FUNCTION FastRCNN;', 'SELECT MIN(id), MAX(id), SUM(id) FROM ABC', "SELECT CLASS FROM TAIPAI                 WHERE (CLASS = 'VAN' AND REDNESS < 300)  OR REDNESS > 500;", 'SELECT CLASS, REDNESS FROM TAIPAI             UNION ALL SELECT CLASS, REDNESS FROM SHANGHAI;', 'SELECT CLASS, REDNESS FROM TAIPAI             UNION SELECT CLASS, REDNESS FROM SHANGHAI;', "SELECT FIRST(id) FROM TAIPAI GROUP BY '8 frames';", "SELECT CLASS, REDNESS FROM TAIPAI                     WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700                     ORDER BY CLASS, REDNESS DESC;", "INSERT INTO MyVideo (Frame_ID, Frame_Path)                                    VALUES    (1, '/mnt/frames/1.png');", 'INSERT INTO testDeleteOne (id, feat, salary, input)\n                VALUES (15, 2.5, [[100, 100, 100]], [[100, 100, 100]]);', 'DELETE FROM Foo WHERE id < 6', "LOAD VIDEO 'data/video.mp4' INTO MyVideo", "LOAD IMAGE 'data/pic.jpg' INTO MyImage", "LOAD CSV 'data/meta.csv' INTO\n                             MyMeta (id, frame_id, video_id, label);", "SELECT Licence_plate(bbox) FROM\n                            (SELECT Yolo(frame).bbox FROM autonomous_vehicle_1\n                              WHERE Yolo(frame).label = 'vehicle') AS T\n                          WHERE Is_suspicious(bbox) = 1 AND\n                                Licence_plate(bbox) = '12345';", 'CREATE TABLE uadtrac_fastRCNN AS\n               SELECT id, Yolo(frame).labels FROM MyVideo\n                        WHERE id<5; ', 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a WHERE table1.a <= 5', 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a JOIN table3\n            ON table3.a = table1.a WHERE table1.a <= 5', 'SELECT frame FROM MyVideo JOIN LATERAL\n                            ObjectDet(frame) AS OD;', "CREATE FUNCTION FaceDetector\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  FaceDetection\n                  IMPL  'evadb/functions/face_detector.py';\n            ", 'SHOW TABLES;', 'SHOW FUNCTIONS;', 'SHOW DATABASES;', 'EXPLAIN SELECT a FROM foo;', 'SELECT HomeRentalForecast(12);', 'SELECT data FROM MyVideo WHERE id < 5\n                    ORDER BY Similarity(FeatureExtractor(Open("abc.jpg")),\n                                        FeatureExtractor(data))\n                    LIMIT 1;']
    randomized_cases = ['Create index TestIndex on MyVideo (featCol) using FAISS;', 'create table if not exists Persons (\n                    Frame_ID integer unique,\n                    Frame_Data text(10),\n                    Frame_Value float(1000, 201),\n                    Frame_Array ndArray uint8(5, 100, 2432, 4324, 100)\n            )', 'Rename Table STUDENT to student_info', 'drop table if exists Student_info', 'drop table Student_Info', 'Drop function FASTRCNN;', 'Select min(id), max(Id), Sum(Id) from ABC', "select CLASS from Taipai where (Class = 'VAN' and REDNESS < 300) or Redness > 500;", 'select class, REDNESS from TAIPAI Union all select Class, redness from Shanghai;', 'Select class, redness from Taipai Union Select CLASS, redness from Shanghai;', "Select first(Id) from Taipai group by '8F';", "Select Class, redness from TAIPAI\n                where (CLASS = 'VAN' and redness < 400 ) or REDNESS > 700\n                order by Class, redness DESC;", "Insert into MyVideo (Frame_ID, Frame_Path) values (1, '/mnt/frames/1.png');", 'insert into testDeleteOne (Id, feat, salary, input)\n                values (15, 2.5, [[100, 100, 100]], [[100, 100, 100]]);', 'delete from Foo where ID < 6', "Load video 'data/video.mp4' into MyVideo", "Load image 'data/pic.jpg' into MyImage", "Load csv 'data/meta.csv' into\n                MyMeta (id, Frame_ID, video_ID, label);", "select Licence_plate(bbox) from\n                (select Yolo(Frame).bbox from autonomous_vehicle_1\n                where Yolo(frame).label = 'vehicle') as T\n                where is_suspicious(bbox) = 1 and\n                Licence_plate(bbox) = '12345';", 'Create TABLE UADTrac_FastRCNN as\n                Select id, YoloV5(Frame).labels from MyVideo\n                    where id<5; ', 'Select Table1.A from Table1 join Table2\n                on Table1.A = Table2.a where Table1.A <= 5', 'Select Table1.A from Table1 Join Table2\n                    On Table1.a = Table2.A Join Table3\n                On Table3.A = Table1.A where Table1.a <= 5', 'Select Frame from MyVideo Join Lateral\n                ObjectDet(Frame) as OD;', "Create FUNCTION FaceDetector\n                Input (Frame ndArray uint8(3, anydim, anydim))\n                Output (bboxes ndArray float32(anydim, 4),\n                scores ndArray float32(ANYdim))\n                Type FaceDetection\n                Impl 'evadb/functions/face_detector.py';\n            ", 'CREATE DATABASE example_db\n                WITH ENGINE = "postgres",\n                PARAMETERS = {\n                    "user": "demo_user",\n                    "password": "demo_password",\n                    "host": "3.220.66.106",\n                    "port": "5432",\n                    "database": "demo"\n                };\n            ']
    queries = queries + randomized_cases
    ref_stmt = parser.parse(queries[0])[0]
    self.assertNotEqual(ref_stmt, None)
    self.assertNotEqual(ref_stmt.__str__(), None)
    statement_to_query_dict = {}
    statement_to_query_dict[ref_stmt] = queries[0]
    for other_query in queries[1:]:
        stmt = parser.parse(other_query)[0]
        self.assertNotEqual(stmt, ref_stmt)
        self.assertEqual(stmt, stmt)
        self.assertNotEqual(stmt, None)
        self.assertNotEqual(stmt.__str__(), None)
        statement_to_query_dict[stmt] = other_query

class ParserTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_select_from_data_source(self):
        parser = Parser()
        query = 'SELECT * FROM DemoDB.DemoTable'
        evadb_stmt_list = parser.parse(query)
        self.assertIsInstance(evadb_stmt_list, list)
        self.assertEqual(len(evadb_stmt_list), 1)
        self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_stmt_list[0]
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'DemoTable')
        self.assertEqual(select_stmt.from_table.table.database_name, 'DemoDB')

    def test_use_statement(self):
        parser = Parser()
        query_list = ['SELECT * FROM DemoTable', 'SELECT * FROM DemoTable WHERE col == "xxx"\n            ', "SELECT * FROM DemoTable WHERE col == 'xxx'\n            "]
        for query in query_list:
            use_query = f'USE DemoDB {{{query}}};'
            evadb_stmt_list = parser.parse(use_query)
            self.assertIsInstance(evadb_stmt_list, list)
            self.assertEqual(len(evadb_stmt_list), 1)
            self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.USE)
            expected_stmt = UseStatement('DemoDB', query)
            actual_stmt = evadb_stmt_list[0]
            self.assertEqual(actual_stmt, expected_stmt)

    def test_create_index_statement(self):
        parser = Parser()
        create_index_query = 'CREATE INDEX testindex ON MyVideo (featCol) USING FAISS;'
        evadb_stmt_list = parser.parse(create_index_query)
        self.assertIsInstance(evadb_stmt_list, list)
        self.assertEqual(len(evadb_stmt_list), 1)
        self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.CREATE_INDEX)
        expected_stmt = CreateIndexStatement('testindex', False, TableRef(TableInfo('MyVideo')), [ColumnDefinition('featCol', None, None, None)], VectorStoreType.FAISS, [TupleValueExpression(name='featCol')])
        actual_stmt = evadb_stmt_list[0]
        self.assertEqual(actual_stmt, expected_stmt)
        self.assertEqual(actual_stmt.index_def, create_index_query)
        expected_stmt = CreateIndexStatement('testindex', True, TableRef(TableInfo('MyVideo')), [ColumnDefinition('featCol', None, None, None)], VectorStoreType.FAISS, [TupleValueExpression(name='featCol')])
        create_index_query = 'CREATE INDEX IF NOT EXISTS testindex ON MyVideo (featCol) USING FAISS;'
        evadb_stmt_list = parser.parse(create_index_query)
        actual_stmt = evadb_stmt_list[0]
        expected_stmt._if_not_exists = True
        self.assertEqual(actual_stmt, expected_stmt)
        self.assertEqual(actual_stmt.index_def, create_index_query)
        create_index_query = 'CREATE INDEX testindex ON MyVideo (FeatureExtractor(featCol)) USING FAISS;'
        evadb_stmt_list = parser.parse(create_index_query)
        self.assertIsInstance(evadb_stmt_list, list)
        self.assertEqual(len(evadb_stmt_list), 1)
        self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.CREATE_INDEX)
        func_expr = FunctionExpression(None, 'FeatureExtractor')
        func_expr.append_child(TupleValueExpression('featCol'))
        expected_stmt = CreateIndexStatement('testindex', False, TableRef(TableInfo('MyVideo')), [ColumnDefinition('featCol', None, None, None)], VectorStoreType.FAISS, [func_expr])
        actual_stmt = evadb_stmt_list[0]
        self.assertEqual(actual_stmt, expected_stmt)
        self.assertEqual(actual_stmt.index_def, create_index_query)

    @unittest.skip('Skip parser exception handling testcase, moved to binder')
    def test_create_index_exception_statement(self):
        parser = Parser()
        create_index_query = 'CREATE INDEX testindex USING FAISS ON MyVideo (featCol1, featCol2);'
        with self.assertRaises(Exception):
            parser.parse(create_index_query)

    def test_explain_dml_statement(self):
        parser = Parser()
        explain_query = 'EXPLAIN SELECT CLASS FROM TAIPAI;'
        evadb_statement_list = parser.parse(explain_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.EXPLAIN)
        inner_stmt = evadb_statement_list[0].explainable_stmt
        self.assertEqual(inner_stmt.stmt_type, StatementType.SELECT)
        self.assertIsNotNone(inner_stmt.from_table)
        self.assertIsInstance(inner_stmt.from_table, TableRef)
        self.assertEqual(inner_stmt.from_table.table.table_name, 'TAIPAI')

    def test_explain_ddl_statement(self):
        parser = Parser()
        select_query = 'SELECT id, Yolo(frame).labels FROM MyVideo\n                        WHERE id<5; '
        explain_query = 'EXPLAIN CREATE TABLE uadtrac_fastRCNN AS {}'.format(select_query)
        evadb_statement_list = parser.parse(explain_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.EXPLAIN)
        inner_stmt = evadb_statement_list[0].explainable_stmt
        self.assertEqual(inner_stmt.stmt_type, StatementType.CREATE)
        self.assertIsNotNone(inner_stmt.table_info, TableRef(TableInfo('uadetrac_fastRCNN')))

    def test_create_table_statement(self):
        parser = Parser()
        single_queries = []
        single_queries.append('CREATE TABLE IF NOT EXISTS Persons (\n                  Frame_ID INTEGER UNIQUE,\n                  Frame_Data TEXT,\n                  Frame_Value FLOAT,\n                  Frame_Array NDARRAY UINT8(5, 100, 2432, 4324, 100)\n            );')
        expected_cci = ColConstraintInfo()
        expected_cci.nullable = True
        unique_cci = ColConstraintInfo()
        unique_cci.unique = True
        unique_cci.nullable = False
        expected_stmt = CreateTableStatement(TableInfo('Persons'), True, [ColumnDefinition('Frame_ID', ColumnType.INTEGER, None, (), unique_cci), ColumnDefinition('Frame_Data', ColumnType.TEXT, None, (), expected_cci), ColumnDefinition('Frame_Value', ColumnType.FLOAT, None, (), expected_cci), ColumnDefinition('Frame_Array', ColumnType.NDARRAY, NdArrayType.UINT8, (5, 100, 2432, 4324, 100), expected_cci)])
        for query in single_queries:
            evadb_statement_list = parser.parse(query)
            self.assertIsInstance(evadb_statement_list, list)
            self.assertEqual(len(evadb_statement_list), 1)
            self.assertIsInstance(evadb_statement_list[0], AbstractStatement)
            self.assertEqual(evadb_statement_list[0], expected_stmt)

    def test_create_table_with_dimension_statement(self):
        parser = Parser()
        single_queries = []
        single_queries.append('CREATE TABLE IF NOT EXISTS Persons (\n                  Frame_ID INTEGER UNIQUE,\n                  Frame_Data TEXT(10),\n                  Frame_Value FLOAT(1000, 201),\n                  Frame_Array NDARRAY UINT8(5, 100, 2432, 4324, 100)\n            );')
        expected_cci = ColConstraintInfo()
        expected_cci.nullable = True
        unique_cci = ColConstraintInfo()
        unique_cci.unique = True
        unique_cci.nullable = False
        expected_stmt = CreateTableStatement(TableInfo('Persons'), True, [ColumnDefinition('Frame_ID', ColumnType.INTEGER, None, (), unique_cci), ColumnDefinition('Frame_Data', ColumnType.TEXT, None, (10,), expected_cci), ColumnDefinition('Frame_Value', ColumnType.FLOAT, None, (1000, 201), expected_cci), ColumnDefinition('Frame_Array', ColumnType.NDARRAY, NdArrayType.UINT8, (5, 100, 2432, 4324, 100), expected_cci)])
        for query in single_queries:
            evadb_statement_list = parser.parse(query)
            self.assertIsInstance(evadb_statement_list, list)
            self.assertEqual(len(evadb_statement_list), 1)
            self.assertIsInstance(evadb_statement_list[0], AbstractStatement)
            self.assertEqual(evadb_statement_list[0], expected_stmt)

    def test_create_table_statement_with_rare_datatypes(self):
        parser = Parser()
        query = 'CREATE TABLE IF NOT EXISTS Dummy (\n                  C NDARRAY UINT8(5),\n                  D NDARRAY INT16(5),\n                  E NDARRAY INT32(5),\n                  F NDARRAY INT64(5),\n                  G NDARRAY UNICODE(5),\n                  H NDARRAY BOOLEAN(5),\n                  I NDARRAY FLOAT64(5),\n                  J NDARRAY DECIMAL(5),\n                  K NDARRAY DATETIME(5)\n            );'
        evadb_statement_list = parser.parse(query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertIsInstance(evadb_statement_list[0], AbstractStatement)

    def test_create_table_statement_without_proper_datatype(self):
        parser = Parser()
        query = 'CREATE TABLE IF NOT EXISTS Dummy (\n                  C NDARRAY INT(5)\n                );'
        with self.assertRaises(Exception):
            parser.parse(query)

    def test_create_table_exception_statement(self):
        parser = Parser()
        create_table_query = 'CREATE TABLE ();'
        with self.assertRaises(Exception):
            parser.parse(create_table_query)

    def test_rename_table_statement(self):
        parser = Parser()
        rename_queries = 'RENAME TABLE student TO student_info'
        expected_stmt = RenameTableStatement(TableRef(TableInfo('student')), TableInfo('student_info'))
        evadb_statement_list = parser.parse(rename_queries)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.RENAME)
        rename_stmt = evadb_statement_list[0]
        self.assertEqual(rename_stmt, expected_stmt)

    def test_drop_table_statement(self):
        parser = Parser()
        drop_queries = 'DROP TABLE student_info'
        expected_stmt = DropObjectStatement(ObjectType.TABLE, 'student_info', False)
        evadb_statement_list = parser.parse(drop_queries)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.DROP_OBJECT)
        drop_stmt = evadb_statement_list[0]
        self.assertEqual(drop_stmt, expected_stmt)

    def test_drop_function_statement_str(self):
        drop_func_query1 = 'DROP FUNCTION MyFunc;'
        drop_func_query2 = 'DROP FUNCTION IF EXISTS MyFunc;'
        expected_stmt1 = DropObjectStatement(ObjectType.FUNCTION, 'MyFunc', False)
        expected_stmt2 = DropObjectStatement(ObjectType.FUNCTION, 'MyFunc', True)
        self.assertEqual(str(expected_stmt1), drop_func_query1)
        self.assertEqual(str(expected_stmt2), drop_func_query2)

    def test_single_statement_queries(self):
        parser = Parser()
        single_queries = []
        single_queries.append('SELECT CLASS FROM TAIPAI;')
        single_queries.append("SELECT CLASS FROM TAIPAI WHERE CLASS = 'VAN';")
        single_queries.append("SELECT CLASS,REDNESS FROM TAIPAI             WHERE CLASS = 'VAN' AND REDNESS > 20.5;")
        single_queries.append("SELECT CLASS FROM TAIPAI             WHERE (CLASS = 'VAN' AND REDNESS < 300 ) OR REDNESS > 500;")
        single_queries.append("SELECT CLASS FROM TAIPAI             WHERE (CLASS = 'VAN' AND REDNESS < 300 ) OR REDNESS > 500;")
        for query in single_queries:
            evadb_statement_list = parser.parse(query)
            self.assertIsInstance(evadb_statement_list, list)
            self.assertEqual(len(evadb_statement_list), 1)
            self.assertIsInstance(evadb_statement_list[0], AbstractStatement)

    def test_multiple_statement_queries(self):
        parser = Parser()
        multiple_queries = []
        multiple_queries.append("SELECT CLASS FROM TAIPAI                 WHERE (CLASS != 'VAN' AND REDNESS < 300)  OR REDNESS > 500;                 SELECT REDNESS FROM TAIPAI                 WHERE (CLASS = 'VAN' AND REDNESS = 300)")
        for query in multiple_queries:
            evadb_statement_list = parser.parse(query)
            self.assertIsInstance(evadb_statement_list, list)
            self.assertEqual(len(evadb_statement_list), 2)
            self.assertIsInstance(evadb_statement_list[0], AbstractStatement)
            self.assertIsInstance(evadb_statement_list[1], AbstractStatement)

    def test_select_statement(self):
        parser = Parser()
        select_query = "SELECT CLASS, REDNESS FROM TAIPAI                 WHERE (CLASS = 'VAN' AND REDNESS < 300 ) OR REDNESS > 500;"
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 2)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
        self.assertIsNotNone(select_stmt.where_clause)

    def test_select_with_empty_string_literal(self):
        parser = Parser()
        select_query = "SELECT '' FROM TAIPAI;"
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

    def test_string_literal_with_escaped_single_quote(self):
        parser = Parser()
        select_query = "SELECT ChatGPT('Here\\'s a question', 'This is the context') FROM TAIPAI;"
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

    def test_string_literal_with_semi_colon(self):
        parser = Parser()
        select_query = 'SELECT ChatGPT("Here\'s a; question", "This is the context") FROM TAIPAI;'
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

    def test_string_literal_with_single_quotes_from_variable(self):
        parser = Parser()
        question = json.dumps("Here's a question")
        answer = json.dumps('This is "the" context')
        select_query = f'SELECT ChatGPT({question}, {answer}) FROM TAIPAI;'
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

    def test_select_union_statement(self):
        parser = Parser()
        select_union_query = 'SELECT CLASS, REDNESS FROM TAIPAI             UNION ALL SELECT CLASS, REDNESS FROM SHANGHAI;'
        evadb_statement_list = parser.parse(select_union_query)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.union_link)
        self.assertEqual(select_stmt.union_all, True)
        second_select_stmt = select_stmt.union_link
        self.assertIsNone(second_select_stmt.union_link)

    def test_select_statement_class(self):
        """Testing setting different clauses for Select
        Statement class
        Class: SelectStatement"""
        select_stmt_new = SelectStatement()
        parser = Parser()
        select_query_new = "SELECT CLASS, REDNESS FROM TAIPAI             WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700;"
        evadb_statement_list = parser.parse(select_query_new)
        select_stmt = evadb_statement_list[0]
        select_stmt_new.where_clause = select_stmt.where_clause
        select_stmt_new.target_list = select_stmt.target_list
        select_stmt_new.from_table = select_stmt.from_table
        self.assertEqual(select_stmt_new.where_clause, select_stmt.where_clause)
        self.assertEqual(select_stmt_new.target_list, select_stmt.target_list)
        self.assertEqual(select_stmt_new.from_table, select_stmt.from_table)
        self.assertEqual(str(select_stmt_new), str(select_stmt))

    def test_select_statement_where_class(self):
        """
        Unit test for logical operators in the where clause.
        """

        def _verify_select_statement(evadb_statement_list):
            self.assertIsInstance(evadb_statement_list, list)
            self.assertEqual(len(evadb_statement_list), 1)
            self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
            select_stmt = evadb_statement_list[0]
            self.assertIsNotNone(select_stmt.target_list)
            self.assertEqual(len(select_stmt.target_list), 2)
            self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
            self.assertEqual(select_stmt.target_list[0].name, 'CLASS')
            self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
            self.assertEqual(select_stmt.target_list[1].name, 'REDNESS')
            self.assertIsNotNone(select_stmt.from_table)
            self.assertIsInstance(select_stmt.from_table, TableRef)
            self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
            self.assertIsNotNone(select_stmt.where_clause)
            self.assertIsInstance(select_stmt.where_clause, LogicalExpression)
            self.assertEqual(select_stmt.where_clause.etype, ExpressionType.LOGICAL_AND)
            self.assertEqual(len(select_stmt.where_clause.children), 2)
            left = select_stmt.where_clause.children[0]
            right = select_stmt.where_clause.children[1]
            self.assertEqual(left.etype, ExpressionType.COMPARE_EQUAL)
            self.assertEqual(right.etype, ExpressionType.COMPARE_LESSER)
            self.assertEqual(len(left.children), 2)
            self.assertEqual(left.children[0].etype, ExpressionType.TUPLE_VALUE)
            self.assertEqual(left.children[0].name, 'CLASS')
            self.assertEqual(left.children[1].etype, ExpressionType.CONSTANT_VALUE)
            self.assertEqual(left.children[1].value, 'VAN')
            self.assertEqual(len(right.children), 2)
            self.assertEqual(right.children[0].etype, ExpressionType.TUPLE_VALUE)
            self.assertEqual(right.children[0].name, 'REDNESS')
            self.assertEqual(right.children[1].etype, ExpressionType.CONSTANT_VALUE)
            self.assertEqual(right.children[1].value, 400)
        parser = Parser()
        select_query = "SELECT CLASS, REDNESS FROM TAIPAI WHERE CLASS = 'VAN' AND REDNESS < 400;"
        _verify_select_statement(parser.parse(select_query))
        select_query = "select CLASS, REDNESS from TAIPAI where CLASS = 'VAN' and REDNESS < 400;"
        _verify_select_statement(parser.parse(select_query))
        select_query = "SELECT CLASS, REDNESS FROM TAIPAI WHERE CLASS = 'VAN' XOR REDNESS < 400;"
        with self.assertRaises(NotImplementedError) as cm:
            parser.parse(select_query)
        self.assertEqual(str(cm.exception), 'Unsupported logical operator: XOR')

    def test_select_statement_groupby_class(self):
        """Testing sample frequency"""
        parser = Parser()
        select_query = "SELECT FIRST(id) FROM TAIPAI GROUP BY '8 frames';"
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 1)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.AGGREGATION_FIRST)
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
        self.assertEqual(select_stmt.groupby_clause, ConstantValueExpression('8 frames', v_type=ColumnType.TEXT))

    def test_select_statement_orderby_class(self):
        """Testing order by clause in select statement
        Class: SelectStatement"""
        parser = Parser()
        select_query = "SELECT CLASS, REDNESS FROM TAIPAI                     WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700                     ORDER BY CLASS, REDNESS DESC;"
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 2)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
        self.assertIsNotNone(select_stmt.where_clause)
        self.assertIsNotNone(select_stmt.orderby_list)
        self.assertEqual(len(select_stmt.orderby_list), 2)
        self.assertEqual(select_stmt.orderby_list[0][0].name, 'CLASS')
        self.assertEqual(select_stmt.orderby_list[0][1], ParserOrderBySortType.ASC)
        self.assertEqual(select_stmt.orderby_list[1][0].name, 'REDNESS')
        self.assertEqual(select_stmt.orderby_list[1][1], ParserOrderBySortType.DESC)

    def test_select_statement_limit_class(self):
        """Testing limit clause in select statement
        Class: SelectStatement"""
        parser = Parser()
        select_query = "SELECT CLASS, REDNESS FROM TAIPAI                     WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700                     ORDER BY CLASS, REDNESS DESC LIMIT 3;"
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 2)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
        self.assertIsNotNone(select_stmt.where_clause)
        self.assertIsNotNone(select_stmt.orderby_list)
        self.assertEqual(len(select_stmt.orderby_list), 2)
        self.assertEqual(select_stmt.orderby_list[0][0].name, 'CLASS')
        self.assertEqual(select_stmt.orderby_list[0][1], ParserOrderBySortType.ASC)
        self.assertEqual(select_stmt.orderby_list[1][0].name, 'REDNESS')
        self.assertEqual(select_stmt.orderby_list[1][1], ParserOrderBySortType.DESC)
        self.assertIsNotNone(select_stmt.limit_count)
        self.assertEqual(select_stmt.limit_count, ConstantValueExpression(3))

    def test_select_statement_sample_class(self):
        """Testing sample frequency"""
        parser = Parser()
        select_query = 'SELECT CLASS, REDNESS FROM TAIPAI SAMPLE 5;'
        evadb_statement_list = parser.parse(select_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 2)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
        self.assertEqual(select_stmt.from_table.sample_freq, ConstantValueExpression(5))

    def test_select_function_star(self):
        parser = Parser()
        query = 'SELECT DemoFunc(*) FROM DemoDB.DemoTable;'
        evadb_stmt_list = parser.parse(query)
        self.assertIsInstance(evadb_stmt_list, list)
        self.assertEqual(len(evadb_stmt_list), 1)
        self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_stmt_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 1)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.FUNCTION_EXPRESSION)
        self.assertEqual(len(select_stmt.target_list[0].children), 1)
        self.assertEqual(select_stmt.target_list[0].children[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[0].children[0].name, '*')
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'DemoTable')
        self.assertEqual(select_stmt.from_table.table.database_name, 'DemoDB')

    def test_select_without_table_source(self):
        parser = Parser()
        query = 'SELECT DemoFunc(12);'
        evadb_stmt_list = parser.parse(query)
        self.assertIsInstance(evadb_stmt_list, list)
        self.assertEqual(len(evadb_stmt_list), 1)
        self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_stmt_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 1)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.FUNCTION_EXPRESSION)
        self.assertEqual(len(select_stmt.target_list[0].children), 1)
        self.assertEqual(select_stmt.target_list[0].children[0].etype, ExpressionType.CONSTANT_VALUE)
        self.assertEqual(select_stmt.target_list[0].children[0].value, 12)
        self.assertIsNone(select_stmt.from_table)

    def test_table_ref(self):
        """Testing table info in TableRef
        Class: TableInfo
        """
        table_info = TableInfo('TAIPAI', 'Schema', 'Database')
        table_ref_obj = TableRef(table_info)
        select_stmt_new = SelectStatement()
        select_stmt_new.from_table = table_ref_obj
        self.assertEqual(select_stmt_new.from_table.table.table_name, 'TAIPAI')
        self.assertEqual(select_stmt_new.from_table.table.schema_name, 'Schema')
        self.assertEqual(select_stmt_new.from_table.table.database_name, 'Database')

    def test_insert_statement(self):
        parser = Parser()
        insert_query = "INSERT INTO MyVideo (Frame_ID, Frame_Path)\n                                    VALUES    (1, '/mnt/frames/1.png');\n                        "
        expected_stmt = InsertTableStatement(TableRef(TableInfo('MyVideo')), [TupleValueExpression('Frame_ID'), TupleValueExpression('Frame_Path')], [[ConstantValueExpression(1), ConstantValueExpression('/mnt/frames/1.png', ColumnType.TEXT)]])
        evadb_statement_list = parser.parse(insert_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.INSERT)
        insert_stmt = evadb_statement_list[0]
        self.assertEqual(insert_stmt, expected_stmt)

    def test_delete_statement(self):
        parser = Parser()
        delete_statement = 'DELETE FROM Foo WHERE id > 5'
        evadb_statement_list = parser.parse(delete_statement)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.DELETE)
        delete_stmt = evadb_statement_list[0]
        expected_stmt = DeleteTableStatement(TableRef(TableInfo('Foo')), ComparisonExpression(ExpressionType.COMPARE_GREATER, TupleValueExpression('id'), ConstantValueExpression(5)))
        self.assertEqual(delete_stmt, expected_stmt)

    def test_set_statement(self):
        parser = Parser()
        set_statement = "SET OPENAIKEY = 'ABCD'"
        evadb_statement_list = parser.parse(set_statement)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SET)
        set_stmt = evadb_statement_list[0]
        expected_stmt = SetStatement('OPENAIKEY', ConstantValueExpression('ABCD', ColumnType.TEXT))
        self.assertEqual(set_stmt, expected_stmt)
        set_statement = "SET OPENAIKEY TO 'ABCD'"
        evadb_statement_list = parser.parse(set_statement)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SET)
        set_stmt = evadb_statement_list[0]
        expected_stmt = SetStatement('OPENAIKEY', ConstantValueExpression('ABCD', ColumnType.TEXT))
        self.assertEqual(set_stmt, expected_stmt)

    def test_show_config_statement(self):
        parser = Parser()
        show_config_statement = 'SHOW OPENAIKEY'
        evadb_statement_list = parser.parse(show_config_statement)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SHOW)
        show_config_stmt = evadb_statement_list[0]
        expected_stmt = ShowStatement(show_type=ShowType.CONFIGS, show_val='OPENAIKEY')
        self.assertEqual(show_config_stmt, expected_stmt)

    def test_create_predict_function_statement(self):
        parser = Parser()
        create_func_query = "\n            CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n            ( SELECT * FROM postgres_data.home_sales )\n            TYPE Forecasting\n            PREDICT 'price';\n        "
        evadb_statement_list = parser.parse(create_func_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.CREATE_FUNCTION)
        create_func_stmt = evadb_statement_list[0]
        self.assertEqual(create_func_stmt.name, 'HomeSalesForecast')
        self.assertEqual(create_func_stmt.or_replace, True)
        self.assertEqual(create_func_stmt.if_not_exists, False)
        self.assertEqual(create_func_stmt.impl_path, None)
        self.assertEqual(create_func_stmt.inputs, [])
        self.assertEqual(create_func_stmt.outputs, [])
        self.assertEqual(create_func_stmt.function_type, 'Forecasting')
        self.assertEqual(create_func_stmt.metadata, [('predict', 'price')])
        nested_select_stmt = create_func_stmt.query
        self.assertEqual(nested_select_stmt.stmt_type, StatementType.SELECT)
        self.assertEqual(len(nested_select_stmt.target_list), 1)
        self.assertEqual(nested_select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(nested_select_stmt.target_list[0].name, '*')
        self.assertIsInstance(nested_select_stmt.from_table, TableRef)
        self.assertIsInstance(nested_select_stmt.from_table.table, TableInfo)
        self.assertEqual(nested_select_stmt.from_table.table.table_name, 'home_sales')
        self.assertEqual(nested_select_stmt.from_table.table.database_name, 'postgres_data')

    def test_create_function_statement(self):
        parser = Parser()
        create_func_query = 'CREATE FUNCTION IF NOT EXISTS FastRCNN\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (Labels NDARRAY STR(10), Bbox NDARRAY UINT8(10, 4))\n                  TYPE  Classification\n                  IMPL  \'data/fastrcnn.py\'\n                  PREDICT "VALUE";\n        '
        expected_cci = ColConstraintInfo()
        expected_cci.nullable = True
        expected_stmt = CreateFunctionStatement('FastRCNN', False, True, Path('data/fastrcnn.py'), [ColumnDefinition('Frame_Array', ColumnType.NDARRAY, NdArrayType.UINT8, (3, 256, 256), expected_cci)], [ColumnDefinition('Labels', ColumnType.NDARRAY, NdArrayType.STR, (10,), expected_cci), ColumnDefinition('Bbox', ColumnType.NDARRAY, NdArrayType.UINT8, (10, 4), expected_cci)], 'Classification', None, [('predict', 'VALUE')])
        evadb_statement_list = parser.parse(create_func_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.CREATE_FUNCTION)
        self.assertEqual(str(evadb_statement_list[0]), str(expected_stmt))
        create_func_stmt = evadb_statement_list[0]
        self.assertEqual(create_func_stmt, expected_stmt)

    def test_load_video_data_statement(self):
        parser = Parser()
        load_data_query = "LOAD VIDEO 'data/video.mp4'\n                             INTO MyVideo"
        file_options = {}
        file_options['file_format'] = FileFormatType.VIDEO
        column_list = None
        expected_stmt = LoadDataStatement(TableInfo('MyVideo'), Path('data/video.mp4'), column_list, file_options)
        evadb_statement_list = parser.parse(load_data_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.LOAD_DATA)
        load_data_stmt = evadb_statement_list[0]
        self.assertEqual(load_data_stmt, expected_stmt)

    def test_load_csv_data_statement(self):
        parser = Parser()
        load_data_query = "LOAD CSV 'data/meta.csv'\n                             INTO\n                             MyMeta (id, frame_id, video_id, label);"
        file_options = {}
        file_options['file_format'] = FileFormatType.CSV
        expected_stmt = LoadDataStatement(TableInfo('MyMeta'), Path('data/meta.csv'), [TupleValueExpression('id'), TupleValueExpression('frame_id'), TupleValueExpression('video_id'), TupleValueExpression('label')], file_options)
        evadb_statement_list = parser.parse(load_data_query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.LOAD_DATA)
        load_data_stmt = evadb_statement_list[0]
        self.assertEqual(load_data_stmt, expected_stmt)

    def test_nested_select_statement(self):
        parser = Parser()
        sub_query = "SELECT CLASS FROM TAIPAI WHERE CLASS = 'VAN'"
        nested_query = 'SELECT ID FROM ({}) AS T;'.format(sub_query)
        parsed_sub_query = parser.parse(sub_query)[0]
        actual_stmt = parser.parse(nested_query)[0]
        self.assertEqual(actual_stmt.stmt_type, StatementType.SELECT)
        self.assertEqual(actual_stmt.target_list[0].name, 'ID')
        self.assertEqual(actual_stmt.from_table, TableRef(parsed_sub_query, alias=Alias('T')))
        sub_query = "SELECT Yolo(frame).bbox FROM autonomous_vehicle_1\n                              WHERE Yolo(frame).label = 'vehicle'"
        nested_query = "SELECT Licence_plate(bbox) FROM\n                            ({}) AS T\n                          WHERE Is_suspicious(bbox) = 1 AND\n                                Licence_plate(bbox) = '12345';\n                      ".format(sub_query)
        query = "SELECT Licence_plate(bbox) FROM TAIPAI\n                    WHERE Is_suspicious(bbox) = 1 AND\n                        Licence_plate(bbox) = '12345';\n                "
        query_stmt = parser.parse(query)[0]
        actual_stmt = parser.parse(nested_query)[0]
        sub_query_stmt = parser.parse(sub_query)[0]
        self.assertEqual(actual_stmt.from_table, TableRef(sub_query_stmt, alias=Alias('T')))
        self.assertEqual(actual_stmt.where_clause, query_stmt.where_clause)
        self.assertEqual(actual_stmt.target_list, query_stmt.target_list)

    def test_should_return_false_for_unequal_expression(self):
        table = TableRef(TableInfo('MyVideo'))
        load_stmt = LoadDataStatement(table, Path('data/video.mp4'), FileFormatType.VIDEO)
        insert_stmt = InsertTableStatement(table)
        create_func = CreateFunctionStatement('func', False, False, Path('data/fastrcnn.py'), [ColumnDefinition('frame', ColumnType.NDARRAY, NdArrayType.UINT8, (3, 256, 256))], [ColumnDefinition('labels', ColumnType.NDARRAY, NdArrayType.STR, 10)], 'Classification')
        select_stmt = SelectStatement()
        self.assertNotEqual(load_stmt, insert_stmt)
        self.assertNotEqual(insert_stmt, load_stmt)
        self.assertNotEqual(create_func, insert_stmt)
        self.assertNotEqual(select_stmt, create_func)

    def test_create_table_from_select(self):
        select_query = 'SELECT id, Yolo(frame).labels FROM MyVideo\n                        WHERE id<5; '
        query = 'CREATE TABLE uadtrac_fastRCNN AS {}'.format(select_query)
        parser = Parser()
        mat_view_stmt = parser.parse(query)
        select_stmt = parser.parse(select_query)
        expected_stmt = CreateTableStatement(TableInfo('uadtrac_fastRCNN'), False, [], select_stmt[0])
        self.assertEqual(mat_view_stmt[0], expected_stmt)

    def test_join(self):
        select_query = 'SELECT table1.a FROM table1 JOIN table2\n                    ON table1.a = table2.a; '
        parser = Parser()
        select_stmt = parser.parse(select_query)[0]
        table1_col_a = TupleValueExpression('a', 'table1')
        table2_col_a = TupleValueExpression('a', 'table2')
        select_list = [table1_col_a]
        from_table = TableRef(JoinNode(TableRef(TableInfo('table1')), TableRef(TableInfo('table2')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table1_col_a, table2_col_a), join_type=JoinType.INNER_JOIN))
        expected_stmt = SelectStatement(select_list, from_table)
        self.assertEqual(select_stmt, expected_stmt)

    def test_join_with_where(self):
        select_query = 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a WHERE table1.a <= 5'
        parser = Parser()
        select_stmt = parser.parse(select_query)[0]
        table1_col_a = TupleValueExpression('a', 'table1')
        table2_col_a = TupleValueExpression('a', 'table2')
        select_list = [table1_col_a]
        from_table = TableRef(JoinNode(TableRef(TableInfo('table1')), TableRef(TableInfo('table2')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table1_col_a, table2_col_a), join_type=JoinType.INNER_JOIN))
        where_clause = ComparisonExpression(ExpressionType.COMPARE_LEQ, table1_col_a, ConstantValueExpression(5))
        expected_stmt = SelectStatement(select_list, from_table, where_clause)
        self.assertEqual(select_stmt, expected_stmt)

    def test_multiple_join_with_multiple_ON(self):
        select_query = 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a JOIN table3\n            ON table3.a = table1.a WHERE table1.a <= 5'
        parser = Parser()
        select_stmt = parser.parse(select_query)[0]
        table1_col_a = TupleValueExpression('a', 'table1')
        table2_col_a = TupleValueExpression('a', 'table2')
        table3_col_a = TupleValueExpression('a', 'table3')
        select_list = [table1_col_a]
        child_join = TableRef(JoinNode(TableRef(TableInfo('table1')), TableRef(TableInfo('table2')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table1_col_a, table2_col_a), join_type=JoinType.INNER_JOIN))
        from_table = TableRef(JoinNode(child_join, TableRef(TableInfo('table3')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table3_col_a, table1_col_a), join_type=JoinType.INNER_JOIN))
        where_clause = ComparisonExpression(ExpressionType.COMPARE_LEQ, table1_col_a, ConstantValueExpression(5))
        expected_stmt = SelectStatement(select_list, from_table, where_clause)
        self.assertEqual(select_stmt, expected_stmt)

    def test_lateral_join(self):
        select_query = 'SELECT frame FROM MyVideo JOIN LATERAL\n                            ObjectDet(frame) AS OD;'
        parser = Parser()
        select_stmt = parser.parse(select_query)[0]
        tuple_frame = TupleValueExpression('frame')
        func_expr = FunctionExpression(func=None, name='ObjectDet', children=[tuple_frame])
        from_table = TableRef(JoinNode(TableRef(TableInfo('MyVideo')), TableRef(TableValuedExpression(func_expr), alias=Alias('OD')), join_type=JoinType.LATERAL_JOIN))
        expected_stmt = SelectStatement([tuple_frame], from_table)
        self.assertEqual(select_stmt, expected_stmt)

    def test_class_equality(self):
        table_info = TableInfo('MyVideo')
        table_ref = TableRef(TableInfo('MyVideo'))
        tuple_frame = TupleValueExpression('frame')
        func_expr = FunctionExpression(func=None, name='ObjectDet', children=[tuple_frame])
        join_node = JoinNode(TableRef(TableInfo('MyVideo')), TableRef(TableValuedExpression(func_expr), alias=Alias('OD')), join_type=JoinType.LATERAL_JOIN)
        self.assertNotEqual(table_info, table_ref)
        self.assertNotEqual(tuple_frame, table_ref)
        self.assertNotEqual(join_node, table_ref)
        self.assertNotEqual(table_ref, table_info)

    def test_create_job(self):
        queries = ["CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n                ( SELECT * FROM postgres_data.home_sales )\n                TYPE Forecasting\n                PREDICT 'price';", 'Select HomeSalesForecast(10);']
        job_query = f"CREATE JOB my_job AS {{\n            {''.join(queries)}\n        }}\n        START '2023-04-01'\n        END '2023-05-01'\n        EVERY 2 hour\n        "
        parser = Parser()
        job_stmt = parser.parse(job_query)[0]
        self.assertEqual(job_stmt.job_name, 'my_job')
        self.assertEqual(len(job_stmt.queries), 2)
        self.assertTrue(queries[0].rstrip(';') == str(job_stmt.queries[0]))
        self.assertTrue(queries[1].rstrip(';') == str(job_stmt.queries[1]))
        self.assertEqual(job_stmt.start_time, '2023-04-01')
        self.assertEqual(job_stmt.end_time, '2023-05-01')
        self.assertEqual(job_stmt.repeat_interval, 2)
        self.assertEqual(job_stmt.repeat_period, 'hour')

def test_select_from_data_source(self):
    parser = Parser()
    query = 'SELECT * FROM DemoDB.DemoTable'
    evadb_stmt_list = parser.parse(query)
    self.assertIsInstance(evadb_stmt_list, list)
    self.assertEqual(len(evadb_stmt_list), 1)
    self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_stmt_list[0]
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'DemoTable')
    self.assertEqual(select_stmt.from_table.table.database_name, 'DemoDB')

def test_use_statement(self):
    parser = Parser()
    query_list = ['SELECT * FROM DemoTable', 'SELECT * FROM DemoTable WHERE col == "xxx"\n            ', "SELECT * FROM DemoTable WHERE col == 'xxx'\n            "]
    for query in query_list:
        use_query = f'USE DemoDB {{{query}}};'
        evadb_stmt_list = parser.parse(use_query)
        self.assertIsInstance(evadb_stmt_list, list)
        self.assertEqual(len(evadb_stmt_list), 1)
        self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.USE)
        expected_stmt = UseStatement('DemoDB', query)
        actual_stmt = evadb_stmt_list[0]
        self.assertEqual(actual_stmt, expected_stmt)

def test_create_index_statement(self):
    parser = Parser()
    create_index_query = 'CREATE INDEX testindex ON MyVideo (featCol) USING FAISS;'
    evadb_stmt_list = parser.parse(create_index_query)
    self.assertIsInstance(evadb_stmt_list, list)
    self.assertEqual(len(evadb_stmt_list), 1)
    self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.CREATE_INDEX)
    expected_stmt = CreateIndexStatement('testindex', False, TableRef(TableInfo('MyVideo')), [ColumnDefinition('featCol', None, None, None)], VectorStoreType.FAISS, [TupleValueExpression(name='featCol')])
    actual_stmt = evadb_stmt_list[0]
    self.assertEqual(actual_stmt, expected_stmt)
    self.assertEqual(actual_stmt.index_def, create_index_query)
    expected_stmt = CreateIndexStatement('testindex', True, TableRef(TableInfo('MyVideo')), [ColumnDefinition('featCol', None, None, None)], VectorStoreType.FAISS, [TupleValueExpression(name='featCol')])
    create_index_query = 'CREATE INDEX IF NOT EXISTS testindex ON MyVideo (featCol) USING FAISS;'
    evadb_stmt_list = parser.parse(create_index_query)
    actual_stmt = evadb_stmt_list[0]
    expected_stmt._if_not_exists = True
    self.assertEqual(actual_stmt, expected_stmt)
    self.assertEqual(actual_stmt.index_def, create_index_query)
    create_index_query = 'CREATE INDEX testindex ON MyVideo (FeatureExtractor(featCol)) USING FAISS;'
    evadb_stmt_list = parser.parse(create_index_query)
    self.assertIsInstance(evadb_stmt_list, list)
    self.assertEqual(len(evadb_stmt_list), 1)
    self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.CREATE_INDEX)
    func_expr = FunctionExpression(None, 'FeatureExtractor')
    func_expr.append_child(TupleValueExpression('featCol'))
    expected_stmt = CreateIndexStatement('testindex', False, TableRef(TableInfo('MyVideo')), [ColumnDefinition('featCol', None, None, None)], VectorStoreType.FAISS, [func_expr])
    actual_stmt = evadb_stmt_list[0]
    self.assertEqual(actual_stmt, expected_stmt)
    self.assertEqual(actual_stmt.index_def, create_index_query)

@unittest.skip('Skip parser exception handling testcase, moved to binder')
def test_create_index_exception_statement(self):
    parser = Parser()
    create_index_query = 'CREATE INDEX testindex USING FAISS ON MyVideo (featCol1, featCol2);'
    with self.assertRaises(Exception):
        parser.parse(create_index_query)

def test_explain_dml_statement(self):
    parser = Parser()
    explain_query = 'EXPLAIN SELECT CLASS FROM TAIPAI;'
    evadb_statement_list = parser.parse(explain_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.EXPLAIN)
    inner_stmt = evadb_statement_list[0].explainable_stmt
    self.assertEqual(inner_stmt.stmt_type, StatementType.SELECT)
    self.assertIsNotNone(inner_stmt.from_table)
    self.assertIsInstance(inner_stmt.from_table, TableRef)
    self.assertEqual(inner_stmt.from_table.table.table_name, 'TAIPAI')

def test_explain_ddl_statement(self):
    parser = Parser()
    select_query = 'SELECT id, Yolo(frame).labels FROM MyVideo\n                        WHERE id<5; '
    explain_query = 'EXPLAIN CREATE TABLE uadtrac_fastRCNN AS {}'.format(select_query)
    evadb_statement_list = parser.parse(explain_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.EXPLAIN)
    inner_stmt = evadb_statement_list[0].explainable_stmt
    self.assertEqual(inner_stmt.stmt_type, StatementType.CREATE)
    self.assertIsNotNone(inner_stmt.table_info, TableRef(TableInfo('uadetrac_fastRCNN')))

def test_create_table_statement(self):
    parser = Parser()
    single_queries = []
    single_queries.append('CREATE TABLE IF NOT EXISTS Persons (\n                  Frame_ID INTEGER UNIQUE,\n                  Frame_Data TEXT,\n                  Frame_Value FLOAT,\n                  Frame_Array NDARRAY UINT8(5, 100, 2432, 4324, 100)\n            );')
    expected_cci = ColConstraintInfo()
    expected_cci.nullable = True
    unique_cci = ColConstraintInfo()
    unique_cci.unique = True
    unique_cci.nullable = False
    expected_stmt = CreateTableStatement(TableInfo('Persons'), True, [ColumnDefinition('Frame_ID', ColumnType.INTEGER, None, (), unique_cci), ColumnDefinition('Frame_Data', ColumnType.TEXT, None, (), expected_cci), ColumnDefinition('Frame_Value', ColumnType.FLOAT, None, (), expected_cci), ColumnDefinition('Frame_Array', ColumnType.NDARRAY, NdArrayType.UINT8, (5, 100, 2432, 4324, 100), expected_cci)])
    for query in single_queries:
        evadb_statement_list = parser.parse(query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertIsInstance(evadb_statement_list[0], AbstractStatement)
        self.assertEqual(evadb_statement_list[0], expected_stmt)

def test_create_table_with_dimension_statement(self):
    parser = Parser()
    single_queries = []
    single_queries.append('CREATE TABLE IF NOT EXISTS Persons (\n                  Frame_ID INTEGER UNIQUE,\n                  Frame_Data TEXT(10),\n                  Frame_Value FLOAT(1000, 201),\n                  Frame_Array NDARRAY UINT8(5, 100, 2432, 4324, 100)\n            );')
    expected_cci = ColConstraintInfo()
    expected_cci.nullable = True
    unique_cci = ColConstraintInfo()
    unique_cci.unique = True
    unique_cci.nullable = False
    expected_stmt = CreateTableStatement(TableInfo('Persons'), True, [ColumnDefinition('Frame_ID', ColumnType.INTEGER, None, (), unique_cci), ColumnDefinition('Frame_Data', ColumnType.TEXT, None, (10,), expected_cci), ColumnDefinition('Frame_Value', ColumnType.FLOAT, None, (1000, 201), expected_cci), ColumnDefinition('Frame_Array', ColumnType.NDARRAY, NdArrayType.UINT8, (5, 100, 2432, 4324, 100), expected_cci)])
    for query in single_queries:
        evadb_statement_list = parser.parse(query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertIsInstance(evadb_statement_list[0], AbstractStatement)
        self.assertEqual(evadb_statement_list[0], expected_stmt)

def test_create_table_statement_with_rare_datatypes(self):
    parser = Parser()
    query = 'CREATE TABLE IF NOT EXISTS Dummy (\n                  C NDARRAY UINT8(5),\n                  D NDARRAY INT16(5),\n                  E NDARRAY INT32(5),\n                  F NDARRAY INT64(5),\n                  G NDARRAY UNICODE(5),\n                  H NDARRAY BOOLEAN(5),\n                  I NDARRAY FLOAT64(5),\n                  J NDARRAY DECIMAL(5),\n                  K NDARRAY DATETIME(5)\n            );'
    evadb_statement_list = parser.parse(query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertIsInstance(evadb_statement_list[0], AbstractStatement)

def test_create_table_statement_without_proper_datatype(self):
    parser = Parser()
    query = 'CREATE TABLE IF NOT EXISTS Dummy (\n                  C NDARRAY INT(5)\n                );'
    with self.assertRaises(Exception):
        parser.parse(query)

def test_create_table_exception_statement(self):
    parser = Parser()
    create_table_query = 'CREATE TABLE ();'
    with self.assertRaises(Exception):
        parser.parse(create_table_query)

def test_rename_table_statement(self):
    parser = Parser()
    rename_queries = 'RENAME TABLE student TO student_info'
    expected_stmt = RenameTableStatement(TableRef(TableInfo('student')), TableInfo('student_info'))
    evadb_statement_list = parser.parse(rename_queries)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.RENAME)
    rename_stmt = evadb_statement_list[0]
    self.assertEqual(rename_stmt, expected_stmt)

def test_drop_table_statement(self):
    parser = Parser()
    drop_queries = 'DROP TABLE student_info'
    expected_stmt = DropObjectStatement(ObjectType.TABLE, 'student_info', False)
    evadb_statement_list = parser.parse(drop_queries)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.DROP_OBJECT)
    drop_stmt = evadb_statement_list[0]
    self.assertEqual(drop_stmt, expected_stmt)

def test_drop_function_statement_str(self):
    drop_func_query1 = 'DROP FUNCTION MyFunc;'
    drop_func_query2 = 'DROP FUNCTION IF EXISTS MyFunc;'
    expected_stmt1 = DropObjectStatement(ObjectType.FUNCTION, 'MyFunc', False)
    expected_stmt2 = DropObjectStatement(ObjectType.FUNCTION, 'MyFunc', True)
    self.assertEqual(str(expected_stmt1), drop_func_query1)
    self.assertEqual(str(expected_stmt2), drop_func_query2)

def test_single_statement_queries(self):
    parser = Parser()
    single_queries = []
    single_queries.append('SELECT CLASS FROM TAIPAI;')
    single_queries.append("SELECT CLASS FROM TAIPAI WHERE CLASS = 'VAN';")
    single_queries.append("SELECT CLASS,REDNESS FROM TAIPAI             WHERE CLASS = 'VAN' AND REDNESS > 20.5;")
    single_queries.append("SELECT CLASS FROM TAIPAI             WHERE (CLASS = 'VAN' AND REDNESS < 300 ) OR REDNESS > 500;")
    single_queries.append("SELECT CLASS FROM TAIPAI             WHERE (CLASS = 'VAN' AND REDNESS < 300 ) OR REDNESS > 500;")
    for query in single_queries:
        evadb_statement_list = parser.parse(query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertIsInstance(evadb_statement_list[0], AbstractStatement)

def test_multiple_statement_queries(self):
    parser = Parser()
    multiple_queries = []
    multiple_queries.append("SELECT CLASS FROM TAIPAI                 WHERE (CLASS != 'VAN' AND REDNESS < 300)  OR REDNESS > 500;                 SELECT REDNESS FROM TAIPAI                 WHERE (CLASS = 'VAN' AND REDNESS = 300)")
    for query in multiple_queries:
        evadb_statement_list = parser.parse(query)
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 2)
        self.assertIsInstance(evadb_statement_list[0], AbstractStatement)
        self.assertIsInstance(evadb_statement_list[1], AbstractStatement)

def test_select_statement(self):
    parser = Parser()
    select_query = "SELECT CLASS, REDNESS FROM TAIPAI                 WHERE (CLASS = 'VAN' AND REDNESS < 300 ) OR REDNESS > 500;"
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 2)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
    self.assertIsNotNone(select_stmt.where_clause)

def test_select_with_empty_string_literal(self):
    parser = Parser()
    select_query = "SELECT '' FROM TAIPAI;"
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

def test_string_literal_with_escaped_single_quote(self):
    parser = Parser()
    select_query = "SELECT ChatGPT('Here\\'s a question', 'This is the context') FROM TAIPAI;"
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

def test_string_literal_with_semi_colon(self):
    parser = Parser()
    select_query = 'SELECT ChatGPT("Here\'s a; question", "This is the context") FROM TAIPAI;'
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

def test_string_literal_with_single_quotes_from_variable(self):
    parser = Parser()
    question = json.dumps("Here's a question")
    answer = json.dumps('This is "the" context')
    select_query = f'SELECT ChatGPT({question}, {answer}) FROM TAIPAI;'
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)

def test_select_union_statement(self):
    parser = Parser()
    select_union_query = 'SELECT CLASS, REDNESS FROM TAIPAI             UNION ALL SELECT CLASS, REDNESS FROM SHANGHAI;'
    evadb_statement_list = parser.parse(select_union_query)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.union_link)
    self.assertEqual(select_stmt.union_all, True)
    second_select_stmt = select_stmt.union_link
    self.assertIsNone(second_select_stmt.union_link)

def test_select_statement_class(self):
    """Testing setting different clauses for Select
        Statement class
        Class: SelectStatement"""
    select_stmt_new = SelectStatement()
    parser = Parser()
    select_query_new = "SELECT CLASS, REDNESS FROM TAIPAI             WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700;"
    evadb_statement_list = parser.parse(select_query_new)
    select_stmt = evadb_statement_list[0]
    select_stmt_new.where_clause = select_stmt.where_clause
    select_stmt_new.target_list = select_stmt.target_list
    select_stmt_new.from_table = select_stmt.from_table
    self.assertEqual(select_stmt_new.where_clause, select_stmt.where_clause)
    self.assertEqual(select_stmt_new.target_list, select_stmt.target_list)
    self.assertEqual(select_stmt_new.from_table, select_stmt.from_table)
    self.assertEqual(str(select_stmt_new), str(select_stmt))

def _verify_select_statement(evadb_statement_list):
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 2)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[0].name, 'CLASS')
    self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[1].name, 'REDNESS')
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
    self.assertIsNotNone(select_stmt.where_clause)
    self.assertIsInstance(select_stmt.where_clause, LogicalExpression)
    self.assertEqual(select_stmt.where_clause.etype, ExpressionType.LOGICAL_AND)
    self.assertEqual(len(select_stmt.where_clause.children), 2)
    left = select_stmt.where_clause.children[0]
    right = select_stmt.where_clause.children[1]
    self.assertEqual(left.etype, ExpressionType.COMPARE_EQUAL)
    self.assertEqual(right.etype, ExpressionType.COMPARE_LESSER)
    self.assertEqual(len(left.children), 2)
    self.assertEqual(left.children[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(left.children[0].name, 'CLASS')
    self.assertEqual(left.children[1].etype, ExpressionType.CONSTANT_VALUE)
    self.assertEqual(left.children[1].value, 'VAN')
    self.assertEqual(len(right.children), 2)
    self.assertEqual(right.children[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(right.children[0].name, 'REDNESS')
    self.assertEqual(right.children[1].etype, ExpressionType.CONSTANT_VALUE)
    self.assertEqual(right.children[1].value, 400)

def test_select_statement_where_class(self):
    """
        Unit test for logical operators in the where clause.
        """

    def _verify_select_statement(evadb_statement_list):
        self.assertIsInstance(evadb_statement_list, list)
        self.assertEqual(len(evadb_statement_list), 1)
        self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
        select_stmt = evadb_statement_list[0]
        self.assertIsNotNone(select_stmt.target_list)
        self.assertEqual(len(select_stmt.target_list), 2)
        self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[0].name, 'CLASS')
        self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(select_stmt.target_list[1].name, 'REDNESS')
        self.assertIsNotNone(select_stmt.from_table)
        self.assertIsInstance(select_stmt.from_table, TableRef)
        self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
        self.assertIsNotNone(select_stmt.where_clause)
        self.assertIsInstance(select_stmt.where_clause, LogicalExpression)
        self.assertEqual(select_stmt.where_clause.etype, ExpressionType.LOGICAL_AND)
        self.assertEqual(len(select_stmt.where_clause.children), 2)
        left = select_stmt.where_clause.children[0]
        right = select_stmt.where_clause.children[1]
        self.assertEqual(left.etype, ExpressionType.COMPARE_EQUAL)
        self.assertEqual(right.etype, ExpressionType.COMPARE_LESSER)
        self.assertEqual(len(left.children), 2)
        self.assertEqual(left.children[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(left.children[0].name, 'CLASS')
        self.assertEqual(left.children[1].etype, ExpressionType.CONSTANT_VALUE)
        self.assertEqual(left.children[1].value, 'VAN')
        self.assertEqual(len(right.children), 2)
        self.assertEqual(right.children[0].etype, ExpressionType.TUPLE_VALUE)
        self.assertEqual(right.children[0].name, 'REDNESS')
        self.assertEqual(right.children[1].etype, ExpressionType.CONSTANT_VALUE)
        self.assertEqual(right.children[1].value, 400)
    parser = Parser()
    select_query = "SELECT CLASS, REDNESS FROM TAIPAI WHERE CLASS = 'VAN' AND REDNESS < 400;"
    _verify_select_statement(parser.parse(select_query))
    select_query = "select CLASS, REDNESS from TAIPAI where CLASS = 'VAN' and REDNESS < 400;"
    _verify_select_statement(parser.parse(select_query))
    select_query = "SELECT CLASS, REDNESS FROM TAIPAI WHERE CLASS = 'VAN' XOR REDNESS < 400;"
    with self.assertRaises(NotImplementedError) as cm:
        parser.parse(select_query)
    self.assertEqual(str(cm.exception), 'Unsupported logical operator: XOR')

def test_select_statement_groupby_class(self):
    """Testing sample frequency"""
    parser = Parser()
    select_query = "SELECT FIRST(id) FROM TAIPAI GROUP BY '8 frames';"
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 1)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.AGGREGATION_FIRST)
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
    self.assertEqual(select_stmt.groupby_clause, ConstantValueExpression('8 frames', v_type=ColumnType.TEXT))

def test_select_statement_orderby_class(self):
    """Testing order by clause in select statement
        Class: SelectStatement"""
    parser = Parser()
    select_query = "SELECT CLASS, REDNESS FROM TAIPAI                     WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700                     ORDER BY CLASS, REDNESS DESC;"
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 2)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
    self.assertIsNotNone(select_stmt.where_clause)
    self.assertIsNotNone(select_stmt.orderby_list)
    self.assertEqual(len(select_stmt.orderby_list), 2)
    self.assertEqual(select_stmt.orderby_list[0][0].name, 'CLASS')
    self.assertEqual(select_stmt.orderby_list[0][1], ParserOrderBySortType.ASC)
    self.assertEqual(select_stmt.orderby_list[1][0].name, 'REDNESS')
    self.assertEqual(select_stmt.orderby_list[1][1], ParserOrderBySortType.DESC)

def test_select_statement_limit_class(self):
    """Testing limit clause in select statement
        Class: SelectStatement"""
    parser = Parser()
    select_query = "SELECT CLASS, REDNESS FROM TAIPAI                     WHERE (CLASS = 'VAN' AND REDNESS < 400 ) OR REDNESS > 700                     ORDER BY CLASS, REDNESS DESC LIMIT 3;"
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 2)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
    self.assertIsNotNone(select_stmt.where_clause)
    self.assertIsNotNone(select_stmt.orderby_list)
    self.assertEqual(len(select_stmt.orderby_list), 2)
    self.assertEqual(select_stmt.orderby_list[0][0].name, 'CLASS')
    self.assertEqual(select_stmt.orderby_list[0][1], ParserOrderBySortType.ASC)
    self.assertEqual(select_stmt.orderby_list[1][0].name, 'REDNESS')
    self.assertEqual(select_stmt.orderby_list[1][1], ParserOrderBySortType.DESC)
    self.assertIsNotNone(select_stmt.limit_count)
    self.assertEqual(select_stmt.limit_count, ConstantValueExpression(3))

def test_select_statement_sample_class(self):
    """Testing sample frequency"""
    parser = Parser()
    select_query = 'SELECT CLASS, REDNESS FROM TAIPAI SAMPLE 5;'
    evadb_statement_list = parser.parse(select_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_statement_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 2)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[1].etype, ExpressionType.TUPLE_VALUE)
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'TAIPAI')
    self.assertEqual(select_stmt.from_table.sample_freq, ConstantValueExpression(5))

def test_select_function_star(self):
    parser = Parser()
    query = 'SELECT DemoFunc(*) FROM DemoDB.DemoTable;'
    evadb_stmt_list = parser.parse(query)
    self.assertIsInstance(evadb_stmt_list, list)
    self.assertEqual(len(evadb_stmt_list), 1)
    self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_stmt_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 1)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.FUNCTION_EXPRESSION)
    self.assertEqual(len(select_stmt.target_list[0].children), 1)
    self.assertEqual(select_stmt.target_list[0].children[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(select_stmt.target_list[0].children[0].name, '*')
    self.assertIsNotNone(select_stmt.from_table)
    self.assertIsInstance(select_stmt.from_table, TableRef)
    self.assertEqual(select_stmt.from_table.table.table_name, 'DemoTable')
    self.assertEqual(select_stmt.from_table.table.database_name, 'DemoDB')

def test_select_without_table_source(self):
    parser = Parser()
    query = 'SELECT DemoFunc(12);'
    evadb_stmt_list = parser.parse(query)
    self.assertIsInstance(evadb_stmt_list, list)
    self.assertEqual(len(evadb_stmt_list), 1)
    self.assertEqual(evadb_stmt_list[0].stmt_type, StatementType.SELECT)
    select_stmt = evadb_stmt_list[0]
    self.assertIsNotNone(select_stmt.target_list)
    self.assertEqual(len(select_stmt.target_list), 1)
    self.assertEqual(select_stmt.target_list[0].etype, ExpressionType.FUNCTION_EXPRESSION)
    self.assertEqual(len(select_stmt.target_list[0].children), 1)
    self.assertEqual(select_stmt.target_list[0].children[0].etype, ExpressionType.CONSTANT_VALUE)
    self.assertEqual(select_stmt.target_list[0].children[0].value, 12)
    self.assertIsNone(select_stmt.from_table)

def test_table_ref(self):
    """Testing table info in TableRef
        Class: TableInfo
        """
    table_info = TableInfo('TAIPAI', 'Schema', 'Database')
    table_ref_obj = TableRef(table_info)
    select_stmt_new = SelectStatement()
    select_stmt_new.from_table = table_ref_obj
    self.assertEqual(select_stmt_new.from_table.table.table_name, 'TAIPAI')
    self.assertEqual(select_stmt_new.from_table.table.schema_name, 'Schema')
    self.assertEqual(select_stmt_new.from_table.table.database_name, 'Database')

def test_insert_statement(self):
    parser = Parser()
    insert_query = "INSERT INTO MyVideo (Frame_ID, Frame_Path)\n                                    VALUES    (1, '/mnt/frames/1.png');\n                        "
    expected_stmt = InsertTableStatement(TableRef(TableInfo('MyVideo')), [TupleValueExpression('Frame_ID'), TupleValueExpression('Frame_Path')], [[ConstantValueExpression(1), ConstantValueExpression('/mnt/frames/1.png', ColumnType.TEXT)]])
    evadb_statement_list = parser.parse(insert_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.INSERT)
    insert_stmt = evadb_statement_list[0]
    self.assertEqual(insert_stmt, expected_stmt)

def test_delete_statement(self):
    parser = Parser()
    delete_statement = 'DELETE FROM Foo WHERE id > 5'
    evadb_statement_list = parser.parse(delete_statement)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.DELETE)
    delete_stmt = evadb_statement_list[0]
    expected_stmt = DeleteTableStatement(TableRef(TableInfo('Foo')), ComparisonExpression(ExpressionType.COMPARE_GREATER, TupleValueExpression('id'), ConstantValueExpression(5)))
    self.assertEqual(delete_stmt, expected_stmt)

def test_set_statement(self):
    parser = Parser()
    set_statement = "SET OPENAIKEY = 'ABCD'"
    evadb_statement_list = parser.parse(set_statement)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SET)
    set_stmt = evadb_statement_list[0]
    expected_stmt = SetStatement('OPENAIKEY', ConstantValueExpression('ABCD', ColumnType.TEXT))
    self.assertEqual(set_stmt, expected_stmt)
    set_statement = "SET OPENAIKEY TO 'ABCD'"
    evadb_statement_list = parser.parse(set_statement)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SET)
    set_stmt = evadb_statement_list[0]
    expected_stmt = SetStatement('OPENAIKEY', ConstantValueExpression('ABCD', ColumnType.TEXT))
    self.assertEqual(set_stmt, expected_stmt)

def test_show_config_statement(self):
    parser = Parser()
    show_config_statement = 'SHOW OPENAIKEY'
    evadb_statement_list = parser.parse(show_config_statement)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.SHOW)
    show_config_stmt = evadb_statement_list[0]
    expected_stmt = ShowStatement(show_type=ShowType.CONFIGS, show_val='OPENAIKEY')
    self.assertEqual(show_config_stmt, expected_stmt)

def test_create_predict_function_statement(self):
    parser = Parser()
    create_func_query = "\n            CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n            ( SELECT * FROM postgres_data.home_sales )\n            TYPE Forecasting\n            PREDICT 'price';\n        "
    evadb_statement_list = parser.parse(create_func_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.CREATE_FUNCTION)
    create_func_stmt = evadb_statement_list[0]
    self.assertEqual(create_func_stmt.name, 'HomeSalesForecast')
    self.assertEqual(create_func_stmt.or_replace, True)
    self.assertEqual(create_func_stmt.if_not_exists, False)
    self.assertEqual(create_func_stmt.impl_path, None)
    self.assertEqual(create_func_stmt.inputs, [])
    self.assertEqual(create_func_stmt.outputs, [])
    self.assertEqual(create_func_stmt.function_type, 'Forecasting')
    self.assertEqual(create_func_stmt.metadata, [('predict', 'price')])
    nested_select_stmt = create_func_stmt.query
    self.assertEqual(nested_select_stmt.stmt_type, StatementType.SELECT)
    self.assertEqual(len(nested_select_stmt.target_list), 1)
    self.assertEqual(nested_select_stmt.target_list[0].etype, ExpressionType.TUPLE_VALUE)
    self.assertEqual(nested_select_stmt.target_list[0].name, '*')
    self.assertIsInstance(nested_select_stmt.from_table, TableRef)
    self.assertIsInstance(nested_select_stmt.from_table.table, TableInfo)
    self.assertEqual(nested_select_stmt.from_table.table.table_name, 'home_sales')
    self.assertEqual(nested_select_stmt.from_table.table.database_name, 'postgres_data')

def test_create_function_statement(self):
    parser = Parser()
    create_func_query = 'CREATE FUNCTION IF NOT EXISTS FastRCNN\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (Labels NDARRAY STR(10), Bbox NDARRAY UINT8(10, 4))\n                  TYPE  Classification\n                  IMPL  \'data/fastrcnn.py\'\n                  PREDICT "VALUE";\n        '
    expected_cci = ColConstraintInfo()
    expected_cci.nullable = True
    expected_stmt = CreateFunctionStatement('FastRCNN', False, True, Path('data/fastrcnn.py'), [ColumnDefinition('Frame_Array', ColumnType.NDARRAY, NdArrayType.UINT8, (3, 256, 256), expected_cci)], [ColumnDefinition('Labels', ColumnType.NDARRAY, NdArrayType.STR, (10,), expected_cci), ColumnDefinition('Bbox', ColumnType.NDARRAY, NdArrayType.UINT8, (10, 4), expected_cci)], 'Classification', None, [('predict', 'VALUE')])
    evadb_statement_list = parser.parse(create_func_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.CREATE_FUNCTION)
    self.assertEqual(str(evadb_statement_list[0]), str(expected_stmt))
    create_func_stmt = evadb_statement_list[0]
    self.assertEqual(create_func_stmt, expected_stmt)

def test_load_video_data_statement(self):
    parser = Parser()
    load_data_query = "LOAD VIDEO 'data/video.mp4'\n                             INTO MyVideo"
    file_options = {}
    file_options['file_format'] = FileFormatType.VIDEO
    column_list = None
    expected_stmt = LoadDataStatement(TableInfo('MyVideo'), Path('data/video.mp4'), column_list, file_options)
    evadb_statement_list = parser.parse(load_data_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.LOAD_DATA)
    load_data_stmt = evadb_statement_list[0]
    self.assertEqual(load_data_stmt, expected_stmt)

def test_load_csv_data_statement(self):
    parser = Parser()
    load_data_query = "LOAD CSV 'data/meta.csv'\n                             INTO\n                             MyMeta (id, frame_id, video_id, label);"
    file_options = {}
    file_options['file_format'] = FileFormatType.CSV
    expected_stmt = LoadDataStatement(TableInfo('MyMeta'), Path('data/meta.csv'), [TupleValueExpression('id'), TupleValueExpression('frame_id'), TupleValueExpression('video_id'), TupleValueExpression('label')], file_options)
    evadb_statement_list = parser.parse(load_data_query)
    self.assertIsInstance(evadb_statement_list, list)
    self.assertEqual(len(evadb_statement_list), 1)
    self.assertEqual(evadb_statement_list[0].stmt_type, StatementType.LOAD_DATA)
    load_data_stmt = evadb_statement_list[0]
    self.assertEqual(load_data_stmt, expected_stmt)

def test_nested_select_statement(self):
    parser = Parser()
    sub_query = "SELECT CLASS FROM TAIPAI WHERE CLASS = 'VAN'"
    nested_query = 'SELECT ID FROM ({}) AS T;'.format(sub_query)
    parsed_sub_query = parser.parse(sub_query)[0]
    actual_stmt = parser.parse(nested_query)[0]
    self.assertEqual(actual_stmt.stmt_type, StatementType.SELECT)
    self.assertEqual(actual_stmt.target_list[0].name, 'ID')
    self.assertEqual(actual_stmt.from_table, TableRef(parsed_sub_query, alias=Alias('T')))
    sub_query = "SELECT Yolo(frame).bbox FROM autonomous_vehicle_1\n                              WHERE Yolo(frame).label = 'vehicle'"
    nested_query = "SELECT Licence_plate(bbox) FROM\n                            ({}) AS T\n                          WHERE Is_suspicious(bbox) = 1 AND\n                                Licence_plate(bbox) = '12345';\n                      ".format(sub_query)
    query = "SELECT Licence_plate(bbox) FROM TAIPAI\n                    WHERE Is_suspicious(bbox) = 1 AND\n                        Licence_plate(bbox) = '12345';\n                "
    query_stmt = parser.parse(query)[0]
    actual_stmt = parser.parse(nested_query)[0]
    sub_query_stmt = parser.parse(sub_query)[0]
    self.assertEqual(actual_stmt.from_table, TableRef(sub_query_stmt, alias=Alias('T')))
    self.assertEqual(actual_stmt.where_clause, query_stmt.where_clause)
    self.assertEqual(actual_stmt.target_list, query_stmt.target_list)

def test_should_return_false_for_unequal_expression(self):
    table = TableRef(TableInfo('MyVideo'))
    load_stmt = LoadDataStatement(table, Path('data/video.mp4'), FileFormatType.VIDEO)
    insert_stmt = InsertTableStatement(table)
    create_func = CreateFunctionStatement('func', False, False, Path('data/fastrcnn.py'), [ColumnDefinition('frame', ColumnType.NDARRAY, NdArrayType.UINT8, (3, 256, 256))], [ColumnDefinition('labels', ColumnType.NDARRAY, NdArrayType.STR, 10)], 'Classification')
    select_stmt = SelectStatement()
    self.assertNotEqual(load_stmt, insert_stmt)
    self.assertNotEqual(insert_stmt, load_stmt)
    self.assertNotEqual(create_func, insert_stmt)
    self.assertNotEqual(select_stmt, create_func)

def test_create_table_from_select(self):
    select_query = 'SELECT id, Yolo(frame).labels FROM MyVideo\n                        WHERE id<5; '
    query = 'CREATE TABLE uadtrac_fastRCNN AS {}'.format(select_query)
    parser = Parser()
    mat_view_stmt = parser.parse(query)
    select_stmt = parser.parse(select_query)
    expected_stmt = CreateTableStatement(TableInfo('uadtrac_fastRCNN'), False, [], select_stmt[0])
    self.assertEqual(mat_view_stmt[0], expected_stmt)

def test_join(self):
    select_query = 'SELECT table1.a FROM table1 JOIN table2\n                    ON table1.a = table2.a; '
    parser = Parser()
    select_stmt = parser.parse(select_query)[0]
    table1_col_a = TupleValueExpression('a', 'table1')
    table2_col_a = TupleValueExpression('a', 'table2')
    select_list = [table1_col_a]
    from_table = TableRef(JoinNode(TableRef(TableInfo('table1')), TableRef(TableInfo('table2')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table1_col_a, table2_col_a), join_type=JoinType.INNER_JOIN))
    expected_stmt = SelectStatement(select_list, from_table)
    self.assertEqual(select_stmt, expected_stmt)

def test_join_with_where(self):
    select_query = 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a WHERE table1.a <= 5'
    parser = Parser()
    select_stmt = parser.parse(select_query)[0]
    table1_col_a = TupleValueExpression('a', 'table1')
    table2_col_a = TupleValueExpression('a', 'table2')
    select_list = [table1_col_a]
    from_table = TableRef(JoinNode(TableRef(TableInfo('table1')), TableRef(TableInfo('table2')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table1_col_a, table2_col_a), join_type=JoinType.INNER_JOIN))
    where_clause = ComparisonExpression(ExpressionType.COMPARE_LEQ, table1_col_a, ConstantValueExpression(5))
    expected_stmt = SelectStatement(select_list, from_table, where_clause)
    self.assertEqual(select_stmt, expected_stmt)

def test_multiple_join_with_multiple_ON(self):
    select_query = 'SELECT table1.a FROM table1 JOIN table2\n            ON table1.a = table2.a JOIN table3\n            ON table3.a = table1.a WHERE table1.a <= 5'
    parser = Parser()
    select_stmt = parser.parse(select_query)[0]
    table1_col_a = TupleValueExpression('a', 'table1')
    table2_col_a = TupleValueExpression('a', 'table2')
    table3_col_a = TupleValueExpression('a', 'table3')
    select_list = [table1_col_a]
    child_join = TableRef(JoinNode(TableRef(TableInfo('table1')), TableRef(TableInfo('table2')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table1_col_a, table2_col_a), join_type=JoinType.INNER_JOIN))
    from_table = TableRef(JoinNode(child_join, TableRef(TableInfo('table3')), predicate=ComparisonExpression(ExpressionType.COMPARE_EQUAL, table3_col_a, table1_col_a), join_type=JoinType.INNER_JOIN))
    where_clause = ComparisonExpression(ExpressionType.COMPARE_LEQ, table1_col_a, ConstantValueExpression(5))
    expected_stmt = SelectStatement(select_list, from_table, where_clause)
    self.assertEqual(select_stmt, expected_stmt)

def test_lateral_join(self):
    select_query = 'SELECT frame FROM MyVideo JOIN LATERAL\n                            ObjectDet(frame) AS OD;'
    parser = Parser()
    select_stmt = parser.parse(select_query)[0]
    tuple_frame = TupleValueExpression('frame')
    func_expr = FunctionExpression(func=None, name='ObjectDet', children=[tuple_frame])
    from_table = TableRef(JoinNode(TableRef(TableInfo('MyVideo')), TableRef(TableValuedExpression(func_expr), alias=Alias('OD')), join_type=JoinType.LATERAL_JOIN))
    expected_stmt = SelectStatement([tuple_frame], from_table)
    self.assertEqual(select_stmt, expected_stmt)

def test_class_equality(self):
    table_info = TableInfo('MyVideo')
    table_ref = TableRef(TableInfo('MyVideo'))
    tuple_frame = TupleValueExpression('frame')
    func_expr = FunctionExpression(func=None, name='ObjectDet', children=[tuple_frame])
    join_node = JoinNode(TableRef(TableInfo('MyVideo')), TableRef(TableValuedExpression(func_expr), alias=Alias('OD')), join_type=JoinType.LATERAL_JOIN)
    self.assertNotEqual(table_info, table_ref)
    self.assertNotEqual(tuple_frame, table_ref)
    self.assertNotEqual(join_node, table_ref)
    self.assertNotEqual(table_ref, table_info)

def test_create_job(self):
    queries = ["CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n                ( SELECT * FROM postgres_data.home_sales )\n                TYPE Forecasting\n                PREDICT 'price';", 'Select HomeSalesForecast(10);']
    job_query = f"CREATE JOB my_job AS {{\n            {''.join(queries)}\n        }}\n        START '2023-04-01'\n        END '2023-05-01'\n        EVERY 2 hour\n        "
    parser = Parser()
    job_stmt = parser.parse(job_query)[0]
    self.assertEqual(job_stmt.job_name, 'my_job')
    self.assertEqual(len(job_stmt.queries), 2)
    self.assertTrue(queries[0].rstrip(';') == str(job_stmt.queries[0]))
    self.assertTrue(queries[1].rstrip(';') == str(job_stmt.queries[1]))
    self.assertEqual(job_stmt.start_time, '2023-04-01')
    self.assertEqual(job_stmt.end_time, '2023-05-01')
    self.assertEqual(job_stmt.repeat_interval, 2)
    self.assertEqual(job_stmt.repeat_period, 'hour')

def execute_query(evadb: EvaDBDatabase, query, report_time: bool=False, do_not_raise_exceptions: bool=False, do_not_print_exceptions: bool=False, **kwargs) -> Iterator[Batch]:
    """
    Execute the query and return a result generator.
    """
    query_compile_time = Timer()
    with query_compile_time:
        stmt = Parser().parse(query)[0]
        res_batch = execute_statement(evadb, stmt, do_not_raise_exceptions, do_not_print_exceptions, **kwargs)
    if report_time is True:
        query_compile_time.log_elapsed_time('Query Compile Time')
    return res_batch

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

def walk(self, bfs=True):
    """
        Returns a generator which visits all nodes in physical plan tree.
        """
    if bfs:
        yield from self.bfs()
    else:
        yield from self.dfs()

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

class LogicalGet(Operator):

    def __init__(self, video: TableRef, table_obj: TableCatalogEntry, alias: str, predicate: AbstractExpression=None, target_list: List[AbstractExpression]=None, sampling_rate: int=None, sampling_type: str=None, chunk_params: dict={}, children=None):
        self._video = video
        self._table_obj = table_obj
        self._alias = alias
        self._predicate = predicate
        self._target_list = target_list
        self._sampling_rate = sampling_rate
        self._sampling_type = sampling_type
        self.chunk_params = chunk_params
        super().__init__(OperatorType.LOGICALGET, children)

    @property
    def video(self):
        return self._video

    @property
    def table_obj(self):
        return self._table_obj

    @property
    def alias(self):
        return self._alias

    @property
    def predicate(self):
        return self._predicate

    @property
    def target_list(self):
        return self._target_list

    @property
    def sampling_rate(self):
        return self._sampling_rate

    @property
    def sampling_type(self):
        return self._sampling_type

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalGet):
            return False
        return is_subtree_equal and self.video == other.video and (self.table_obj == other.table_obj) and (self.alias == other.alias) and (self.predicate == other.predicate) and (self.target_list == other.target_list) and (self.sampling_rate == other.sampling_rate) and (self.sampling_type == other.sampling_type) and (self.chunk_params == other.chunk_params)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.alias, self.video, self.table_obj, self.predicate, tuple(self.target_list or []), self.sampling_rate, self.sampling_type, frozenset(self.chunk_params.items())))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalGet):
        return False
    return is_subtree_equal and self.video == other.video and (self.table_obj == other.table_obj) and (self.alias == other.alias) and (self.predicate == other.predicate) and (self.target_list == other.target_list) and (self.sampling_rate == other.sampling_rate) and (self.sampling_type == other.sampling_type) and (self.chunk_params == other.chunk_params)

class LogicalQueryDerivedGet(Operator):

    def __init__(self, alias: str, predicate: AbstractExpression=None, target_list: List[AbstractExpression]=None, children: List=None):
        super().__init__(OperatorType.LOGICALQUERYDERIVEDGET, children=children)
        self._alias = alias
        self.predicate = predicate
        self.target_list = target_list or []

    @property
    def alias(self):
        return self._alias

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalQueryDerivedGet):
            return False
        return is_subtree_equal and self.predicate == other.predicate and (self.target_list == other.target_list) and (self.alias == other.alias)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.alias, self.predicate, tuple(self.target_list)))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalQueryDerivedGet):
        return False
    return is_subtree_equal and self.predicate == other.predicate and (self.target_list == other.target_list) and (self.alias == other.alias)

class LogicalFilter(Operator):

    def __init__(self, predicate: AbstractExpression, children=None):
        self._predicate = predicate
        super().__init__(OperatorType.LOGICALFILTER, children)

    @property
    def predicate(self):
        return self._predicate

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalFilter):
            return False
        return is_subtree_equal and self.predicate == other.predicate

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.predicate))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalFilter):
        return False
    return is_subtree_equal and self.predicate == other.predicate

class LogicalProject(Operator):

    def __init__(self, target_list: List[AbstractExpression], children=None):
        super().__init__(OperatorType.LOGICALPROJECT, children)
        self._target_list = target_list

    @property
    def target_list(self):
        return self._target_list

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalProject):
            return False
        return is_subtree_equal and self.target_list == other.target_list

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self.target_list)))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalProject):
        return False
    return is_subtree_equal and self.target_list == other.target_list

class LogicalGroupBy(Operator):

    def __init__(self, groupby_clause: ConstantValueExpression, children: List=None):
        super().__init__(OperatorType.LOGICALGROUPBY, children)
        self._groupby_clause = groupby_clause

    @property
    def groupby_clause(self):
        return self._groupby_clause

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalGroupBy):
            return False
        return is_subtree_equal and self.groupby_clause == other.groupby_clause

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.groupby_clause))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalGroupBy):
        return False
    return is_subtree_equal and self.groupby_clause == other.groupby_clause

class LogicalOrderBy(Operator):

    def __init__(self, orderby_list: List, children: List=None):
        super().__init__(OperatorType.LOGICALORDERBY, children)
        self._orderby_list = orderby_list

    @property
    def orderby_list(self):
        return self._orderby_list

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalOrderBy):
            return False
        return is_subtree_equal and self.orderby_list == other.orderby_list

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self.orderby_list)))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalOrderBy):
        return False
    return is_subtree_equal and self.orderby_list == other.orderby_list

class LogicalLimit(Operator):

    def __init__(self, limit_count: ConstantValueExpression, children: List=None):
        super().__init__(OperatorType.LOGICALLIMIT, children)
        self._limit_count = limit_count

    @property
    def limit_count(self):
        return self._limit_count

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalLimit):
            return False
        return is_subtree_equal and self.limit_count == other.limit_count

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.limit_count))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalLimit):
        return False
    return is_subtree_equal and self.limit_count == other.limit_count

class LogicalSample(Operator):

    def __init__(self, sample_freq: ConstantValueExpression, sample_type: ConstantValueExpression, children: List=None):
        super().__init__(OperatorType.LOGICALSAMPLE, children)
        self._sample_freq = sample_freq
        self._sample_type = sample_type

    @property
    def sample_freq(self):
        return self._sample_freq

    @property
    def sample_type(self):
        return self._sample_type

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalSample):
            return False
        return is_subtree_equal and self.sample_freq == other.sample_freq and (self.sample_type == other.sample_type)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.sample_freq, self.sample_type))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalSample):
        return False
    return is_subtree_equal and self.sample_freq == other.sample_freq and (self.sample_type == other.sample_type)

class LogicalUnion(Operator):

    def __init__(self, all: bool, children: List=None):
        super().__init__(OperatorType.LOGICALUNION, children)
        self._all = all

    @property
    def all(self):
        return self._all

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalUnion):
            return False
        return is_subtree_equal and self.all == other.all

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.all))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalUnion):
        return False
    return is_subtree_equal and self.all == other.all

class LogicalInsert(Operator):
    """[Logical Node for Insert operation]

    Arguments:
        table(TableCatalogEntry): table to insert data into
        column_list{List[AbstractExpression]}:
            [After binding annotated column_list]
        value_list{List[AbstractExpression]}:
            [value list to insert]
    """

    def __init__(self, table: TableCatalogEntry, column_list: List[AbstractExpression], value_list: List[AbstractExpression], children: List=None):
        super().__init__(OperatorType.LOGICALINSERT, children)
        self._table = table
        self._column_list = column_list
        self._value_list = value_list

    @property
    def table(self):
        return self._table

    @property
    def value_list(self):
        return self._value_list

    @property
    def column_list(self):
        return self._column_list

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalInsert):
            return False
        return is_subtree_equal and self.table == other.table and (self.value_list == other.value_list) and (self.column_list == other.column_list)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table, tuple((tuple(i) for i in self.value_list)), tuple(self.column_list)))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalInsert):
        return False
    return is_subtree_equal and self.table == other.table and (self.value_list == other.value_list) and (self.column_list == other.column_list)

class LogicalDelete(Operator):
    """[Logical Node for Delete Operation]

    Arguments:
        table_ref(TableCatalogEntry): table to delete tuples from,
        where_clause(AbstractExpression): the predicate used to select which rows to delete,

    """

    def __init__(self, table_ref: TableRef, where_clause: AbstractExpression=None, children=None):
        super().__init__(OperatorType.LOGICALDELETE, children)
        self._table_ref = table_ref
        self._where_clause = where_clause

    @property
    def table_ref(self):
        return self._table_ref

    @property
    def where_clause(self):
        return self._where_clause

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalDelete):
            return False
        return is_subtree_equal and self.table_ref == other.table_ref and (self.where_clause == other.where_clause)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_ref, self.where_clause))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalDelete):
        return False
    return is_subtree_equal and self.table_ref == other.table_ref and (self.where_clause == other.where_clause)

class LogicalCreate(Operator):
    """Logical node for create table operations

    Arguments:
        video {TableRef}: [video table that is to be created]
        column_list {List[ColumnDefinition]}:
        if_not_exists {bool}: [create table if exists]

    """

    def __init__(self, video: TableInfo, column_list: List[ColumnDefinition], if_not_exists: bool=False, children: List=None):
        super().__init__(OperatorType.LOGICALCREATE, children)
        self._video = video
        self._column_list = column_list
        self._if_not_exists = if_not_exists

    @property
    def video(self):
        return self._video

    @property
    def column_list(self):
        return self._column_list

    @property
    def if_not_exists(self):
        return self._if_not_exists

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalCreate):
            return False
        return is_subtree_equal and self.video == other.video and (self.column_list == other.column_list) and (self.if_not_exists == other.if_not_exists)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.video, tuple(self.column_list), self.if_not_exists))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalCreate):
        return False
    return is_subtree_equal and self.video == other.video and (self.column_list == other.column_list) and (self.if_not_exists == other.if_not_exists)

class LogicalRename(Operator):
    """Logical node for rename table operations

    Arguments:
        old_table {TableRef}: [old table that is to be renamed]
        new_name {TableInfo}: [new name for the old table]
    """

    def __init__(self, old_table_ref: TableRef, new_name: TableInfo, children=None):
        super().__init__(OperatorType.LOGICALRENAME, children)
        self._new_name = new_name
        self._old_table_ref = old_table_ref

    @property
    def new_name(self):
        return self._new_name

    @property
    def old_table_ref(self):
        return self._old_table_ref

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalRename):
            return False
        return is_subtree_equal and self._new_name == other._new_name and (self._old_table_ref == other._old_table_ref)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._new_name, self._old_table_ref))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalRename):
        return False
    return is_subtree_equal and self._new_name == other._new_name and (self._old_table_ref == other._old_table_ref)

class LogicalCreateFunction(Operator):
    """
    Logical node for create function operations

    Attributes:
        name: str
            function_name provided by the user required
        or_replace: bool
            if true should overwrite if function with same name exists
        if_not_exists: bool
            if true should skip if function with same name exists
        inputs: List[FunctionIOCatalogEntry]
            function inputs, annotated list similar to table columns
        outputs: List[FunctionIOCatalogEntry]
            function outputs, annotated list similar to table columns
        impl_path: Path
            file path which holds the implementation of the function.
            This file should be placed in the function directory and
            the path provided should be relative to the function dir.
        function_type: str
            function type. it ca be object detection, classification etc.
    """

    def __init__(self, name: str, or_replace: bool, if_not_exists: bool, inputs: List[FunctionIOCatalogEntry], outputs: List[FunctionIOCatalogEntry], impl_path: Path, function_type: str=None, metadata: List[FunctionMetadataCatalogEntry]=None, children: List=None):
        super().__init__(OperatorType.LOGICALCREATEFUNCTION, children)
        self._name = name
        self._or_replace = or_replace
        self._if_not_exists = if_not_exists
        self._inputs = inputs
        self._outputs = outputs
        self._impl_path = impl_path
        self._function_type = function_type
        self._metadata = metadata

    @property
    def name(self):
        return self._name

    @property
    def or_replace(self):
        return self._or_replace

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def impl_path(self):
        return self._impl_path

    @property
    def function_type(self):
        return self._function_type

    @property
    def metadata(self):
        return self._metadata

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalCreateFunction):
            return False
        return is_subtree_equal and self.name == other.name and (self.or_replace == other.or_replace) and (self.if_not_exists == other.if_not_exists) and (self.inputs == other.inputs) and (self.outputs == other.outputs) and (self.function_type == other.function_type) and (self.impl_path == other.impl_path) and (self.metadata == other.metadata)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.name, self.or_replace, self.if_not_exists, tuple(self.inputs), tuple(self.outputs), self.function_type, self.impl_path, tuple(self.metadata)))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalCreateFunction):
        return False
    return is_subtree_equal and self.name == other.name and (self.or_replace == other.or_replace) and (self.if_not_exists == other.if_not_exists) and (self.inputs == other.inputs) and (self.outputs == other.outputs) and (self.function_type == other.function_type) and (self.impl_path == other.impl_path) and (self.metadata == other.metadata)

class LogicalDropObject(Operator):
    """
    Logical node for DROP Object operations

    Attributes:
        object_type: ObjectType
        name: str
            Function name provided by the user
        if_exists: bool
            if false, throws an error when no function with name exists
            else logs a warning
    """

    def __init__(self, object_type: ObjectType, name: str, if_exists: bool, children: List=None):
        super().__init__(OperatorType.LOGICAL_DROP_OBJECT, children)
        self._object_type = object_type
        self._name = name
        self._if_exists = if_exists

    @property
    def object_type(self):
        return self._object_type

    @property
    def name(self):
        return self._name

    @property
    def if_exists(self):
        return self._if_exists

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalDropObject):
            return False
        return is_subtree_equal and self.object_type == other.object_type and (self.name == other.name) and (self.if_exists == other.if_exists)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.object_type, self.name, self.if_exists))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalDropObject):
        return False
    return is_subtree_equal and self.object_type == other.object_type and (self.name == other.name) and (self.if_exists == other.if_exists)

class LogicalLoadData(Operator):
    """Logical node for load data operation

    Arguments:
        table(TableCatalogEntry): table to load data into
        path(Path): file path from where we are loading data
    """

    def __init__(self, table_info: TableInfo, path: Path, column_list: List[AbstractExpression]=None, file_options: dict=dict(), children: List=None):
        super().__init__(OperatorType.LOGICALLOADDATA, children=children)
        self._table_info = table_info
        self._path = path
        self._column_list = column_list or []
        self._file_options = file_options

    @property
    def table_info(self):
        return self._table_info

    @property
    def path(self):
        return self._path

    @property
    def column_list(self):
        return self._column_list

    @property
    def file_options(self):
        return self._file_options

    def __str__(self):
        return 'LogicalLoadData(table: {}, path: {},                 column_list: {},                 file_options: {})'.format(self.table_info, self.path, self.column_list, self.file_options)

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalLoadData):
            return False
        return is_subtree_equal and self.table_info == other.table_info and (self.path == other.path) and (self.column_list == other.column_list) and (self.file_options == other.file_options)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_info, self.path, tuple(self.column_list), frozenset(self.file_options.items())))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalLoadData):
        return False
    return is_subtree_equal and self.table_info == other.table_info and (self.path == other.path) and (self.column_list == other.column_list) and (self.file_options == other.file_options)

class LogicalFunctionScan(Operator):
    """
    Logical node for function table scans

    Attributes:
        func_expr: AbstractExpression
            function_expression that yield a table like output
    """

    def __init__(self, func_expr: AbstractExpression, alias: Alias, do_unnest: bool=False, children: List=None):
        super().__init__(OperatorType.LOGICALFUNCTIONSCAN, children)
        self._func_expr = func_expr
        self._do_unnest = do_unnest
        self._alias = alias

    @property
    def alias(self):
        return self._alias

    @property
    def func_expr(self):
        return self._func_expr

    @property
    def do_unnest(self):
        return self._do_unnest

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalFunctionScan):
            return False
        return is_subtree_equal and self.func_expr == other.func_expr and (self.do_unnest == other.do_unnest) and (self.alias == other.alias)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.func_expr, self.do_unnest, self.alias))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalFunctionScan):
        return False
    return is_subtree_equal and self.func_expr == other.func_expr and (self.do_unnest == other.do_unnest) and (self.alias == other.alias)

class LogicalExtractObject(Operator):

    def __init__(self, detector: FunctionExpression, tracker: FunctionExpression, alias: Alias, do_unnest: bool=False, children: List=None):
        super().__init__(OperatorType.LOGICAL_EXTRACT_OBJECT, children)
        self.detector = detector
        self.tracker = tracker
        self.do_unnest = do_unnest
        self.alias = alias

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalExtractObject):
            return False
        return is_subtree_equal and self.detector == other.detector and (self.tracker == other.tracker) and (self.do_unnest == other.do_unnest) and (self.alias == other.alias)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.detector, self.tracker, self.do_unnest, self.alias))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalExtractObject):
        return False
    return is_subtree_equal and self.detector == other.detector and (self.tracker == other.tracker) and (self.do_unnest == other.do_unnest) and (self.alias == other.alias)

class LogicalJoin(Operator):
    """
    Logical node for join operators

    Attributes:
        join_type: JoinType
            Join type provided by the user - Lateral, Inner, Outer
        join_predicate: AbstractExpression
            condition/predicate expression used to join the tables
    """

    def __init__(self, join_type: JoinType, join_predicate: AbstractExpression=None, left_keys: List[ColumnCatalogEntry]=None, right_keys: List[ColumnCatalogEntry]=None, children: List=None):
        super().__init__(OperatorType.LOGICALJOIN, children)
        self._join_type = join_type
        self._join_predicate = join_predicate
        self._left_keys = left_keys
        self._right_keys = right_keys
        self._join_project = None

    @property
    def join_type(self):
        return self._join_type

    @property
    def join_predicate(self):
        return self._join_predicate

    @property
    def left_keys(self):
        return self._left_keys

    @property
    def right_keys(self):
        return self._right_keys

    @property
    def join_project(self):
        return self._join_project

    def lhs(self):
        return self.children[0]

    def rhs(self):
        return self.children[1]

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalJoin):
            return False
        return is_subtree_equal and self.join_type == other.join_type and (self.join_predicate == other.join_predicate) and (self.left_keys == other.left_keys) and (self.right_keys == other.right_keys) and (self.join_project == other.join_project)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.join_type, self.join_predicate, self.left_keys, self.right_keys, tuple(self.join_project or [])))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalJoin):
        return False
    return is_subtree_equal and self.join_type == other.join_type and (self.join_predicate == other.join_predicate) and (self.left_keys == other.left_keys) and (self.right_keys == other.right_keys) and (self.join_project == other.join_project)

class LogicalShow(Operator):

    def __init__(self, show_type: ShowType, show_val: Optional[str]='', children: List=None):
        super().__init__(OperatorType.LOGICAL_SHOW, children)
        self._show_type = show_type
        self._show_val = show_val

    @property
    def show_type(self):
        return self._show_type

    @property
    def show_val(self):
        return self._show_val

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalShow):
            return False
        return is_subtree_equal and self.show_type == other.show_type and (self.show_val == other.show_val)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.show_type, self.show_val))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalShow):
        return False
    return is_subtree_equal and self.show_type == other.show_type and (self.show_val == other.show_val)

class LogicalExchange(Operator):

    def __init__(self, children=None):
        super().__init__(OperatorType.LOGICALEXCHANGE, children)

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalExchange):
            return False
        return is_subtree_equal

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalExchange):
        return False
    return is_subtree_equal

class LogicalExplain(Operator):

    def __init__(self, children: List=None):
        super().__init__(OperatorType.LOGICALEXPLAIN, children)
        assert len(children) == 1, 'EXPLAIN command only takes one child'
        self._explainable_opr = children[0]

    @property
    def explainable_opr(self):
        return self._explainable_opr

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalExplain):
            return False
        return is_subtree_equal and self._explainable_opr == other.explainable_opr

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._explainable_opr))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalExplain):
        return False
    return is_subtree_equal and self._explainable_opr == other.explainable_opr

class LogicalCreateIndex(Operator):

    def __init__(self, name: str, if_not_exists: bool, table_ref: TableRef, col_list: List[ColumnDefinition], vector_store_type: VectorStoreType, project_expr_list: List[AbstractExpression], index_def: str, children: List=None):
        super().__init__(OperatorType.LOGICALCREATEINDEX, children)
        self._name = name
        self._if_not_exists = if_not_exists
        self._table_ref = table_ref
        self._col_list = col_list
        self._vector_store_type = vector_store_type
        self._project_expr_list = project_expr_list
        self._index_def = index_def

    @property
    def name(self):
        return self._name

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def table_ref(self):
        return self._table_ref

    @property
    def col_list(self):
        return self._col_list

    @property
    def vector_store_type(self):
        return self._vector_store_type

    @property
    def project_expr_list(self):
        return self._project_expr_list

    @property
    def index_def(self):
        return self._index_def

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalCreateIndex):
            return False
        return is_subtree_equal and self.name == other.name and (self.if_not_exists == other.if_not_exists) and (self.table_ref == other.table_ref) and (self.col_list == other.col_list) and (self.vector_store_type == other.vector_store_type) and (self.project_expr_list == other.project_expr_list) and (self.index_def == other.index_def)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.name, self.if_not_exists, self.table_ref, tuple(self.col_list), self.vector_store_type, tuple(self.project_expr_list), self.index_def))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalCreateIndex):
        return False
    return is_subtree_equal and self.name == other.name and (self.if_not_exists == other.if_not_exists) and (self.table_ref == other.table_ref) and (self.col_list == other.col_list) and (self.vector_store_type == other.vector_store_type) and (self.project_expr_list == other.project_expr_list) and (self.index_def == other.index_def)

class LogicalApplyAndMerge(Operator):
    """Evaluate the function expression on the input data and return the merged output.
    This operator simplifies the process of evaluating functions on a table source.
    Currently, it performs an inner join while merging the function output with the
    input data. This means that if the function does not return any output for a given
    input row, that row will be dropped from the output. We can consider expanding this
    to support left joins and other types of joins in the future.
    """

    def __init__(self, func_expr: FunctionExpression, alias: Alias, do_unnest: bool=False, children: List=None):
        super().__init__(OperatorType.LOGICAL_APPLY_AND_MERGE, children)
        self._func_expr = func_expr
        self._do_unnest = do_unnest
        self._alias = alias
        self._merge_type = JoinType.INNER_JOIN

    @property
    def alias(self):
        return self._alias

    @property
    def func_expr(self):
        return self._func_expr

    @property
    def do_unnest(self):
        return self._do_unnest

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalApplyAndMerge):
            return False
        return is_subtree_equal and self.func_expr == other.func_expr and (self.do_unnest == other.do_unnest) and (self.alias == other.alias) and (self._merge_type == other._merge_type)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.func_expr, self.do_unnest, self.alias, self._merge_type))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalApplyAndMerge):
        return False
    return is_subtree_equal and self.func_expr == other.func_expr and (self.do_unnest == other.do_unnest) and (self.alias == other.alias) and (self._merge_type == other._merge_type)

class LogicalVectorIndexScan(Operator):

    def __init__(self, index: IndexCatalogEntry, limit_count: ConstantValueExpression, search_query_expr: FunctionExpression, children: List=None):
        super().__init__(OperatorType.LOGICAL_VECTOR_INDEX_SCAN, children)
        self._index = index
        self._limit_count = limit_count
        self._search_query_expr = search_query_expr

    @property
    def index(self):
        return self._index

    @property
    def limit_count(self):
        return self._limit_count

    @property
    def search_query_expr(self):
        return self._search_query_expr

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalVectorIndexScan):
            return False
        return is_subtree_equal and self.index == other.index and (self.limit_count == other.limit_count) and (self.search_query_expr == other.search_query_expr)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.index, self.limit_count, self.search_query_expr))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalVectorIndexScan):
        return False
    return is_subtree_equal and self.index == other.index and (self.limit_count == other.limit_count) and (self.search_query_expr == other.search_query_expr)

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

def __init__(self, opr: Operator, group_id: int=UNDEFINED_GROUP_ID, children: List[int]=[]):
    assert len(opr.children) == 0, 'Cannot create a group expression\n                                from operator with children'
    self._opr = opr
    self._group_id = group_id
    self._children = children
    self._rules_explored = RuleType.INVALID_RULE

def __eq__(self, other: 'GroupExpression'):
    if not isinstance(other, GroupExpression):
        return False
    return self.group_id == other.group_id and self.opr == other.opr and (self.children == other.children)

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

@cost.register(ApplyAndMergePlan)
def cost_apply_and_merge(opr: ApplyAndMergePlan):
    if opr.func_expr.has_cache():
        return 0
    return 1

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
def _grp_binder(idx: int, pattern: Pattern, memo: Memo):
    grp = memo.groups[idx]
    for expr in grp.logical_exprs:
        yield from Binder._binder(expr, pattern, memo)

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

def optimize_cache_key(context: 'OptimizerContext', expr: FunctionExpression):
    """Optimize the cache key

    It tries to reduce the caching overhead by replacing the caching key with
    logically equivalent key. For instance, frame data can be replaced with frame id.

    Args:
        expr (FunctionExpression): expression to optimize the caching key for.

    Example:
        Yolo(data) -> return id

    Todo: Optimize complex expression
        FaceDet(Crop(data, bbox)) -> return

    """
    keys = expr.children
    optimize_key_mapping_f = {TupleValueExpression: optimize_cache_key_for_tuple_value_expression, ConstantValueExpression: optimize_cache_key_for_constant_value_expression}
    optimized_keys = []
    for key in keys:
        if type(key) not in optimize_key_mapping_f:
            raise RuntimeError(f'Optimize cache key of {type(key)} is not implemented')
        optimized_keys += optimize_key_mapping_f[type(key)](context, key)
    return optimized_keys

def enable_cache(context: 'OptimizerContext', func_expr: FunctionExpression) -> FunctionExpression:
    """Enables cache for a function expression.

    The cache key is optimized by replacing it with logical equivalent expressions.
    A cache entry is inserted in the catalog corresponding to the expression.

    Args:
        context (OptimizerContext): associated optimizer context
        func_expr (FunctionExpression): The function expression to enable cache for.

    Returns:
        FunctionExpression: The function expression with cache enabled.
    """
    cache = enable_cache_init(context, func_expr)
    return func_expr.copy().enable_cache(cache)

def enable_cache_on_expression_tree(context: 'OptimizerContext', expr_tree: AbstractExpression):
    func_exprs = list(expr_tree.find_all(FunctionExpression))
    func_exprs = list(filter(lambda expr: check_expr_validity_for_cache(expr), func_exprs))
    for expr in func_exprs:
        cache = enable_cache_init(context, expr)
        expr.enable_cache(cache)

def check_expr_validity_for_cache(expr: FunctionExpression):
    valid = expr.name in CACHEABLE_FUNCTIONS and (not expr.has_cache())
    if len(expr.children) == 1:
        valid &= isinstance(expr.children[0], TupleValueExpression)
    elif len(expr.children) == 2:
        valid &= isinstance(expr.children[0], ConstantValueExpression) and isinstance(expr.children[1], TupleValueExpression)
    return valid

class Property:

    def __init__(self, property_type):
        self._property_type = property_type

    def property_type(self):
        return self._property_type

    def __eq__(self, other):
        if not isinstance(other, Property):
            return False
        return self.property_type == other.property_type

    def __hash__(self):
        return hash(self._property_type)

def __eq__(self, other):
    if not isinstance(other, Property):
        return False
    return self.property_type == other.property_type

class CacheFunctionExpressionInProject(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALPROJECT)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.CACHE_FUNCTION_EXPRESISON_IN_PROJECT, pattern)

    def promise(self):
        return Promise.CACHE_FUNCTION_EXPRESISON_IN_PROJECT

    def check(self, before: LogicalProject, context: OptimizerContext):
        valid_exprs = []
        for expr in before.target_list:
            if isinstance(expr, FunctionExpression):
                func_exprs = list(expr.find_all(FunctionExpression))
                valid_exprs.extend(filter(lambda expr: check_expr_validity_for_cache(expr), func_exprs))
        if len(valid_exprs) > 0:
            return True
        return False

    def apply(self, before: LogicalProject, context: OptimizerContext):
        new_target_list = [expr.copy() for expr in before.target_list]
        for expr in new_target_list:
            enable_cache_on_expression_tree(context, expr)
        after = LogicalProject(target_list=new_target_list, children=before.children)
        yield after

def check(self, before: LogicalProject, context: OptimizerContext):
    valid_exprs = []
    for expr in before.target_list:
        if isinstance(expr, FunctionExpression):
            func_exprs = list(expr.find_all(FunctionExpression))
            valid_exprs.extend(filter(lambda expr: check_expr_validity_for_cache(expr), func_exprs))
    if len(valid_exprs) > 0:
        return True
    return False

class CacheFunctionExpressionInFilter(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALFILTER)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.CACHE_FUNCTION_EXPRESISON_IN_FILTER, pattern)

    def promise(self):
        return Promise.CACHE_FUNCTION_EXPRESISON_IN_FILTER

    def check(self, before: LogicalFilter, context: OptimizerContext):
        func_exprs = list(before.predicate.find_all(FunctionExpression))
        valid_exprs = list(filter(lambda expr: check_expr_validity_for_cache(expr), func_exprs))
        if len(valid_exprs) > 0:
            return True
        return False

    def apply(self, before: LogicalFilter, context: OptimizerContext):
        after_predicate = before.predicate.copy()
        enable_cache_on_expression_tree(context, after_predicate)
        after_operator = LogicalFilter(predicate=after_predicate, children=before.children)
        yield after_operator

def check(self, before: LogicalFilter, context: OptimizerContext):
    func_exprs = list(before.predicate.find_all(FunctionExpression))
    valid_exprs = list(filter(lambda expr: check_expr_validity_for_cache(expr), func_exprs))
    if len(valid_exprs) > 0:
        return True
    return False

class CacheFunctionExpressionInApply(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.CACHE_FUNCTION_EXPRESISON_IN_APPLY, pattern)

    def promise(self):
        return Promise.CACHE_FUNCTION_EXPRESISON_IN_APPLY

    def check(self, before: LogicalApplyAndMerge, context: OptimizerContext):
        expr = before.func_expr
        if expr.has_cache() or expr.name not in CACHEABLE_FUNCTIONS:
            return False
        if len(expr.children) > 1 or not isinstance(expr.children[0], TupleValueExpression):
            return False
        return True

    def apply(self, before: LogicalApplyAndMerge, context: OptimizerContext):
        new_func_expr = enable_cache(context, before.func_expr)
        after = LogicalApplyAndMerge(func_expr=new_func_expr, alias=before.alias, do_unnest=before.do_unnest)
        after.append_child(before.children[0])
        yield after

def check(self, before: LogicalApplyAndMerge, context: OptimizerContext):
    expr = before.func_expr
    if expr.has_cache() or expr.name not in CACHEABLE_FUNCTIONS:
        return False
    if len(expr.children) > 1 or not isinstance(expr.children[0], TupleValueExpression):
        return False
    return True

class CombineSimilarityOrderByAndLimitToVectorIndexScan(Rule):
    """
    This rule currently rewrites Order By + Limit to a vector index scan.
    Because vector index only works for similarity search, the rule will
    only be applied when the Order By is on Similarity expression. For
    simplicity, we also only enable this rule when the Similarity expression
    applies to the full table. Predicated query will yield incorrect results
    if we use an index scan.

    Limit(10)
        |
    OrderBy(func)        ->        IndexScan(10)
        |                               |
        A                               A
    """

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALLIMIT)
        orderby_pattern = Pattern(OperatorType.LOGICALORDERBY)
        orderby_pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(orderby_pattern)
        super().__init__(RuleType.COMBINE_SIMILARITY_ORDERBY_AND_LIMIT_TO_VECTOR_INDEX_SCAN, pattern)
        self._index_catalog_entry = None
        self._query_func_expr = None

    def promise(self):
        return Promise.COMBINE_SIMILARITY_ORDERBY_AND_LIMIT_TO_VECTOR_INDEX_SCAN

    def check(self, before: LogicalLimit, context: OptimizerContext):
        return True

    def apply(self, before: LogicalLimit, context: OptimizerContext):
        catalog_manager = context.db.catalog
        limit_node = before
        orderby_node = before.children[0]
        sub_tree_root = orderby_node.children[0]

        def _exists_predicate(opr):
            if isinstance(opr, LogicalGet):
                return opr.predicate is not None
            return True
        if _exists_predicate(sub_tree_root.opr):
            return
        func_orderby_expr = None
        for column, sort_type in orderby_node.orderby_list:
            if isinstance(column, FunctionExpression) and sort_type == ParserOrderBySortType.ASC:
                func_orderby_expr = column
        if not func_orderby_expr or func_orderby_expr.name != 'Similarity':
            return
        tb_catalog_entry = list(sub_tree_root.opr.find_all(LogicalGet))[0].table_obj
        db_catalog_entry = catalog_manager().get_database_catalog_entry(tb_catalog_entry.database_name)
        is_postgres_data_source = db_catalog_entry is not None and db_catalog_entry.engine == 'postgres'
        query_func_expr, base_func_expr = func_orderby_expr.children
        tv_expr = base_func_expr
        while not isinstance(tv_expr, TupleValueExpression):
            tv_expr = tv_expr.children[0]
        column_catalog_entry = tv_expr.col_object
        if not is_postgres_data_source:
            function_signature = None if isinstance(base_func_expr, TupleValueExpression) else base_func_expr.signature()
            index_catalog_entry = catalog_manager().get_index_catalog_entry_by_column_and_function_signature(column_catalog_entry, function_signature)
            if not index_catalog_entry:
                return
        else:
            index_catalog_entry = IndexCatalogEntry(name='', save_file_path='', type=VectorStoreType.PGVECTOR, feat_column=column_catalog_entry)
        vector_index_scan_node = LogicalVectorIndexScan(index_catalog_entry, limit_node.limit_count, query_func_expr)
        for child in orderby_node.children:
            vector_index_scan_node.append_child(child)
        yield vector_index_scan_node

def _exists_predicate(opr):
    if isinstance(opr, LogicalGet):
        return opr.predicate is not None
    return True

def apply(self, before: LogicalLimit, context: OptimizerContext):
    catalog_manager = context.db.catalog
    limit_node = before
    orderby_node = before.children[0]
    sub_tree_root = orderby_node.children[0]

    def _exists_predicate(opr):
        if isinstance(opr, LogicalGet):
            return opr.predicate is not None
        return True
    if _exists_predicate(sub_tree_root.opr):
        return
    func_orderby_expr = None
    for column, sort_type in orderby_node.orderby_list:
        if isinstance(column, FunctionExpression) and sort_type == ParserOrderBySortType.ASC:
            func_orderby_expr = column
    if not func_orderby_expr or func_orderby_expr.name != 'Similarity':
        return
    tb_catalog_entry = list(sub_tree_root.opr.find_all(LogicalGet))[0].table_obj
    db_catalog_entry = catalog_manager().get_database_catalog_entry(tb_catalog_entry.database_name)
    is_postgres_data_source = db_catalog_entry is not None and db_catalog_entry.engine == 'postgres'
    query_func_expr, base_func_expr = func_orderby_expr.children
    tv_expr = base_func_expr
    while not isinstance(tv_expr, TupleValueExpression):
        tv_expr = tv_expr.children[0]
    column_catalog_entry = tv_expr.col_object
    if not is_postgres_data_source:
        function_signature = None if isinstance(base_func_expr, TupleValueExpression) else base_func_expr.signature()
        index_catalog_entry = catalog_manager().get_index_catalog_entry_by_column_and_function_signature(column_catalog_entry, function_signature)
        if not index_catalog_entry:
            return
    else:
        index_catalog_entry = IndexCatalogEntry(name='', save_file_path='', type=VectorStoreType.PGVECTOR, feat_column=column_catalog_entry)
    vector_index_scan_node = LogicalVectorIndexScan(index_catalog_entry, limit_node.limit_count, query_func_expr)
    for child in orderby_node.children:
        vector_index_scan_node.append_child(child)
    yield vector_index_scan_node

class ReorderPredicates(Rule):
    """
    The current implementation orders conjuncts based on their individual cost.
    The optimization for OR clauses has `not` been implemented yet. Additionally, we do
    not optimize predicates that are not user-defined functions since we assume that
    they will likely be pushed to the underlying relational database, which will handle
    the optimization process.
    """

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALFILTER)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.REORDER_PREDICATES, pattern)

    def promise(self):
        return Promise.REORDER_PREDICATES

    def check(self, before: LogicalFilter, context: OptimizerContext):
        return len(list(before.predicate.find_all(FunctionExpression))) > 0

    def apply(self, before: LogicalFilter, context: OptimizerContext):
        conjuncts = to_conjunction_list(before.predicate)
        contains_func_exprs = []
        simple_exprs = []
        for conjunct in conjuncts:
            if list(conjunct.find_all(FunctionExpression)):
                contains_func_exprs.append(conjunct)
            else:
                simple_exprs.append(conjunct)
        function_expr_cost_tuples = [(expr, get_expression_execution_cost(context, expr)) for expr in contains_func_exprs]
        function_expr_cost_tuples = sorted(function_expr_cost_tuples, key=lambda x: x[1])
        ordered_conjuncts = simple_exprs + [expr for expr, _ in function_expr_cost_tuples]
        if ordered_conjuncts != conjuncts:
            reordered_predicate = conjunction_list_to_expression_tree(ordered_conjuncts)
            reordered_filter_node = LogicalFilter(predicate=reordered_predicate)
            reordered_filter_node.append_child(before.children[0])
            yield reordered_filter_node

def check(self, before: LogicalFilter, context: OptimizerContext):
    return len(list(before.predicate.find_all(FunctionExpression))) > 0

class LogicalRenameToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALRENAME)
        super().__init__(RuleType.LOGICAL_RENAME_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_RENAME_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalRename, context: OptimizerContext):
        after = RenamePlan(before.old_table_ref, before.new_name)
        yield after

def apply(self, before: LogicalRename, context: OptimizerContext):
    after = RenamePlan(before.old_table_ref, before.new_name)
    yield after

class LimitExecutor(AbstractExecutor):
    """
    Limits the number of rows returned

    Arguments:
        node (AbstractPlan): The Limit Plan

    """

    def __init__(self, db: EvaDBDatabase, node: LimitPlan):
        super().__init__(db, node)
        self._limit_count = node.limit_value

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        remaining_tuples = self._limit_count
        for batch in child_executor.exec(**kwargs):
            if len(batch) > remaining_tuples:
                yield batch[:remaining_tuples]
                return
            remaining_tuples -= len(batch)
            yield batch
            if remaining_tuples <= 0:
                assert remaining_tuples == 0
                return

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    child_executor = self.children[0]
    remaining_tuples = self._limit_count
    for batch in child_executor.exec(**kwargs):
        if len(batch) > remaining_tuples:
            yield batch[:remaining_tuples]
            return
        remaining_tuples -= len(batch)
        yield batch
        if remaining_tuples <= 0:
            assert remaining_tuples == 0
            return

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

def instrument_function_expression_cost(expr: Union[AbstractExpression, List[AbstractExpression]], catalog: 'CatalogManager'):
    """We are expecting an instance of a catalog. An optimization can be to avoid creating a catalog instance if there is no function expression. An easy fix is to pass the function handler and create the catalog instance only if there is a function expression. In the past, this was problematic because of Ray. We can revisit it again."""
    if expr is None:
        return
    list_expr = expr
    if not isinstance(expr, list):
        list_expr = [expr]
    for expr in list_expr:
        for func_expr in expr.find_all(FunctionExpression):
            if func_expr.function_obj and func_expr._stats:
                function_id = func_expr.function_obj.row_id
                catalog.upsert_function_cost_catalog_entry(function_id, func_expr.function_obj.name, func_expr._stats.prev_cost)

def validate_kwargs(kwargs, allowed_keys: List[str], required_keys: List[str], error_message='Keyword argument not understood:'):
    """Checks that all keyword arguments are in the set of allowed keys."""
    if required_keys is None:
        required_keys = allowed_keys
    for kwarg in kwargs:
        if kwarg not in allowed_keys:
            raise TypeError(error_message, kwarg)
    missing_keys = [key for key in required_keys if key not in kwargs]
    assert len(missing_keys) == 0, f'Missing required keys, {missing_keys}'

class PickleSerializer(object):

    @classmethod
    def serialize(cls, data):
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls, data):
        return pickle.loads(data)

@classmethod
def serialize(cls, data):
    return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

def string_comparison_case_insensitive(string_1, string_2) -> bool:
    """
    Case insensitive string comparison for two strings which gives
    a bool response whether the strings are the same or not

    Arguments:
        string_1 (str)
        string_2 (str)

    Returns:
        True/False (bool): Returns True if the strings are same, false otherwise
    """
    if string_1 is None or string_2 is None:
        return False
    return string_1.lower() == string_2.lower()

def create_row_num_tv_expr(table_alias):
    tv_expr = TupleValueExpression(name=ROW_NUM_COLUMN)
    tv_expr.table_alias = table_alias
    tv_expr.col_alias = f'{table_alias}.{ROW_NUM_COLUMN.lower()}'
    tv_expr.col_object = ColumnCatalogEntry(name=ROW_NUM_COLUMN, type=ColumnType.INTEGER)
    return tv_expr

def resolve_alias_table_value_expression(node: FunctionExpression):
    default_alias_name = node.name.lower()
    default_output_col_aliases = [str(obj.name.lower()) for obj in node.output_objs]
    if not node.alias:
        node.alias = Alias(default_alias_name, default_output_col_aliases)
    elif not len(node.alias.col_names):
        node.alias = Alias(node.alias.alias_name, default_output_col_aliases)
    else:
        output_aliases = [str(col_name.lower()) for col_name in node.alias.col_names]
        node.alias = Alias(node.alias.alias_name, output_aliases)
    assert len(node.alias.col_names) == len(node.output_objs), f'Expected {len(node.output_objs)} output columns for {node.alias.alias_name}, got {len(node.alias.col_names)}.'

def handle_bind_extract_object_function(node: FunctionExpression, binder_context: StatementBinderContext):
    """Handles the binding of extract_object function.
        1. Bind the source video data
        2. Create and bind the detector function expression using the provided name.
        3. Create and bind the tracker function expression.
            Its inputs are id, data, output of detector.
        4. Bind the EXTRACT_OBJECT function expression and append the new children.
        5. Handle the alias and populate the outputs of the EXTRACT_OBJECT function

    Args:
        node (FunctionExpression): The function expression representing the extract object operation.
        binder_context (StatementBinderContext): The context object used to bind expressions in the statement.

    Raises:
        AssertionError: If the number of children in the `node` is not equal to 3.
    """
    assert len(node.children) == 3, f'Invalid arguments provided to {node}. Example correct usage, (data, Detector, Tracker)'
    video_data = node.children[0]
    binder_context.bind(video_data)
    detector = FunctionExpression(None, node.children[1].name)
    detector.append_child(video_data.copy())
    binder_context.bind(detector)
    tracker = FunctionExpression(None, node.children[2].name)
    columns = get_video_table_column_definitions()
    tracker.append_child(TupleValueExpression(name=columns[1].name, table_alias=video_data.table_alias))
    tracker.append_child(video_data.copy())
    binder_context.bind(tracker)
    for obj in detector.output_objs:
        col_alias = '{}.{}'.format(obj.function_name.lower(), obj.name.lower())
        child = TupleValueExpression(obj.name, table_alias=obj.function_name.lower(), col_object=obj, col_alias=col_alias)
        tracker.append_child(child)
    node.children = []
    node.children = [video_data, detector, tracker]
    node.output_objs = tracker.output_objs
    node.projection_columns = [obj.name.lower() for obj in node.output_objs]
    resolve_alias_table_value_expression(node)
    tracker.alias = node.alias

def bind_tuple_expr(binder: StatementBinder, node: TupleValueExpression):
    table_alias, col_obj = binder._binder_context.get_binded_column(node.name, node.table_alias)
    node.table_alias = table_alias
    if node.name == VideoColumnName.audio:
        binder._binder_context.enable_audio_retrieval()
    if node.name == VideoColumnName.data:
        binder._binder_context.enable_video_retrieval()
    node.col_alias = '{}.{}'.format(table_alias, node.name.lower())
    node.col_object = col_obj

def handle_bind_extract_object_function(node: FunctionExpression, binder_context: StatementBinder):
    """Handles the binding of extract_object function.
        1. Bind the source video data
        2. Create and bind the detector function expression using the provided name.
        3. Create and bind the tracker function expression.
            Its inputs are id, data, output of detector.
        4. Bind the EXTRACT_OBJECT function expression and append the new children.
        5. Handle the alias and populate the outputs of the EXTRACT_OBJECT function
    Args:
        node (FunctionExpression): The function expression representing the extract object operation.
        binder_context (StatementBinder): The binder object used to bind expressions in the statement.
    Raises:
        AssertionError: If the number of children in the `node` is not equal to 3.
    """
    assert len(node.children) == 3, f'Invalid arguments provided to {node}. Example correct usage, (data, Detector, Tracker)'
    video_data = node.children[0]
    binder_context.bind(video_data)
    detector = FunctionExpression(None, node.children[1].name)
    detector.append_child(video_data.copy())
    binder_context.bind(detector)
    tracker = FunctionExpression(None, node.children[2].name)
    columns = get_video_table_column_definitions()
    tracker.append_child(TupleValueExpression(name=columns[1].name, table_alias=video_data.table_alias))
    tracker.append_child(video_data.copy())
    binder_context.bind(tracker)
    for obj in detector.output_objs:
        col_alias = '{}.{}'.format(obj.function_name.lower(), obj.name.lower())
        child = TupleValueExpression(obj.name, table_alias=obj.function_name.lower(), col_object=obj, col_alias=col_alias)
        tracker.append_child(child)
    node.children = []
    node.children = [video_data, detector, tracker]
    node.output_objs = tracker.output_objs
    node.projection_columns = [obj.name.lower() for obj in node.output_objs]
    resolve_alias_table_value_expression(node)
    tracker.alias = node.alias

class AggregationExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.INTEGER, children=children)

    def evaluate(self, *args, **kwargs):
        batch: Batch = self.get_child(0).evaluate(*args, **kwargs)
        if self.etype == ExpressionType.AGGREGATION_FIRST:
            batch = batch[0]
        elif self.etype == ExpressionType.AGGREGATION_LAST:
            batch = batch[-1]
        elif self.etype == ExpressionType.AGGREGATION_SEGMENT:
            batch = Batch.stack(batch)
        elif self.etype == ExpressionType.AGGREGATION_SUM:
            batch.aggregate('sum')
        elif self.etype == ExpressionType.AGGREGATION_COUNT:
            batch.aggregate('count')
        elif self.etype == ExpressionType.AGGREGATION_AVG:
            batch.aggregate('mean')
        elif self.etype == ExpressionType.AGGREGATION_MIN:
            batch.aggregate('min')
        elif self.etype == ExpressionType.AGGREGATION_MAX:
            batch.aggregate('max')
        batch.reset_index()
        column_name = self.etype.name
        if column_name.find('AGGREGATION_') != -1:
            updated_column_name = column_name.replace('AGGREGATION_', '')
            batch.modify_column_alias(updated_column_name)
        return batch

    def get_symbol(self) -> str:
        if self.etype == ExpressionType.AGGREGATION_FIRST:
            return 'FIRST'
        if self.etype == ExpressionType.AGGREGATION_LAST:
            return 'LAST'
        if self.etype == ExpressionType.AGGREGATION_SEGMENT:
            return 'SEGMENT'
        if self.etype == ExpressionType.AGGREGATION_SUM:
            return 'SUM'
        elif self.etype == ExpressionType.AGGREGATION_COUNT:
            return 'COUNT'
        elif self.etype == ExpressionType.AGGREGATION_AVG:
            return 'AVG'
        elif self.etype == ExpressionType.AGGREGATION_MIN:
            return 'MIN'
        elif self.etype == ExpressionType.AGGREGATION_MAX:
            return 'MAX'
        else:
            raise NotImplementedError

    def signature(self) -> str:
        child_sigs = []
        for child in self.children:
            child_sigs.append(child.signature())
        return f'{self.get_symbol().lower()}({','.join(child_sigs)})'

    def __str__(self) -> str:
        expr_str = ''
        if self.etype:
            expr_str = f'{str(self.get_symbol())}()'
        return expr_str

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, AggregationExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.etype))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, AggregationExpression):
        return False
    return is_subtree_equal and self.etype == other.etype

class TupleValueExpression(AbstractExpression):

    def __init__(self, name: str=None, table_alias: str=None, col_object: Union[ColumnCatalogEntry, FunctionIOCatalogEntry]=None, col_alias=None):
        super().__init__(ExpressionType.TUPLE_VALUE, rtype=ExpressionReturnType.INVALID)
        self._name = name
        self._table_alias = table_alias
        self._col_object = col_object
        self._col_alias = col_alias

    @property
    def table_alias(self) -> str:
        return self._table_alias

    @table_alias.setter
    def table_alias(self, table_alias):
        self._table_alias = table_alias

    @property
    def name(self) -> str:
        return self._name

    @property
    def col_object(self) -> Union[ColumnCatalogEntry, FunctionIOCatalogEntry]:
        return self._col_object

    @col_object.setter
    def col_object(self, value: Union[ColumnCatalogEntry, FunctionIOCatalogEntry]):
        self._col_object = value

    @property
    def col_alias(self) -> str:
        return self._col_alias

    @col_alias.setter
    def col_alias(self, value: str):
        self._col_alias = value

    def evaluate(self, batch: Batch, *args, **kwargs):
        return batch.project([self.col_alias])

    def signature(self):
        """It constructs the signature of the tuple value expression.
        It assumes the col_object attribute is populated by the binder with the catalog
        entries. For a standard column in the table, it returns `table_name.col_name`,
        and for function output columns it returns `function_name.col_name`
        Raises:
            ValueError: If the col_object is not a `Union[ColumnCatalogEntry, FunctionIOCatalogEntry]`. This can occur if the expression has not been bound using the binder.
        Returns:
            str: signature string
        """
        assert isinstance(self.col_object, ColumnCatalogEntry) or isinstance(self.col_object, FunctionIOCatalogEntry), f'Unsupported type of self.col_object {type(self.col_object)}, expected ColumnCatalogEntry or FunctionIOCatalogEntry'
        col_name = self.col_object.name
        row_id = self.col_object.row_id
        if isinstance(self.col_object, ColumnCatalogEntry):
            return f'{self.col_object.table_name}.{col_name}[{row_id}]'
        elif isinstance(self.col_object, FunctionIOCatalogEntry):
            return f'{self.col_object.function_name}.{col_name}[{row_id}]'

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, TupleValueExpression):
            return False
        return is_subtree_equal and self.table_alias == other.table_alias and (self.name == other.name) and (self.col_alias == other.col_alias) and (self.col_object == other.col_object)

    def __str__(self) -> str:
        expr_str = ''
        if self.table_alias:
            expr_str += f'{str(self.table_alias)}.'
        if self.name:
            expr_str += f'{str(self.name)}'
        if self.col_alias:
            expr_str += f' AS {str(self.col_alias)}'
        expr_str += ''
        return expr_str

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_alias, self.name, self.col_alias, self.col_object))

def signature(self):
    """It constructs the signature of the tuple value expression.
        It assumes the col_object attribute is populated by the binder with the catalog
        entries. For a standard column in the table, it returns `table_name.col_name`,
        and for function output columns it returns `function_name.col_name`
        Raises:
            ValueError: If the col_object is not a `Union[ColumnCatalogEntry, FunctionIOCatalogEntry]`. This can occur if the expression has not been bound using the binder.
        Returns:
            str: signature string
        """
    assert isinstance(self.col_object, ColumnCatalogEntry) or isinstance(self.col_object, FunctionIOCatalogEntry), f'Unsupported type of self.col_object {type(self.col_object)}, expected ColumnCatalogEntry or FunctionIOCatalogEntry'
    col_name = self.col_object.name
    row_id = self.col_object.row_id
    if isinstance(self.col_object, ColumnCatalogEntry):
        return f'{self.col_object.table_name}.{col_name}[{row_id}]'
    elif isinstance(self.col_object, FunctionIOCatalogEntry):
        return f'{self.col_object.function_name}.{col_name}[{row_id}]'

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, TupleValueExpression):
        return False
    return is_subtree_equal and self.table_alias == other.table_alias and (self.name == other.name) and (self.col_alias == other.col_alias) and (self.col_object == other.col_object)

class ConstantValueExpression(AbstractExpression):

    def __init__(self, value: Any, v_type: ColumnType=ColumnType.INTEGER):
        super().__init__(ExpressionType.CONSTANT_VALUE)
        self._value = value
        self._v_type = v_type

    def evaluate(self, batch: Batch, **kwargs):
        batch = Batch(pd.DataFrame({0: [self._value] * len(batch)}))
        return batch

    def signature(self) -> str:
        return str(self)

    @property
    def value(self):
        return self._value

    @property
    def v_type(self):
        return self._v_type

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, ConstantValueExpression):
            return False
        is_equal = is_subtree_equal and self.v_type == other.v_type
        if self.v_type == ColumnType.NDARRAY:
            return is_equal and all(self.value == other.value)
        else:
            return is_equal and self.value == other.value

    def __str__(self) -> str:
        expr_str = ''
        if not isinstance(self._value, np.ndarray):
            expr_str = f'{str(self._value)}'
        else:
            expr_str = f'{np.array_str(self._value)}'
        return expr_str

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.v_type, str(self.value)))

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, ConstantValueExpression):
        return False
    is_equal = is_subtree_equal and self.v_type == other.v_type
    if self.v_type == ColumnType.NDARRAY:
        return is_equal and all(self.value == other.value)
    else:
        return is_equal and self.value == other.value

def __str__(self) -> str:
    expr_str = ''
    if not isinstance(self._value, np.ndarray):
        expr_str = f'{str(self._value)}'
    else:
        expr_str = f'{np.array_str(self._value)}'
    return expr_str

class ArithmeticExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.FLOAT, children=children)

    def evaluate(self, *args, **kwargs):
        vl = self.get_child(0).evaluate(*args, **kwargs)
        vr = self.get_child(1).evaluate(*args, **kwargs)
        return Batch.combine_batches(vl, vr, self.etype)

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, ArithmeticExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, ArithmeticExpression):
        return False
    return is_subtree_equal and self.etype == other.etype

class LogicalExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.BOOLEAN, children=children)

    def evaluate(self, batch, **kwargs):
        if self.get_children_count() == 2:
            left_batch = self.get_child(0).evaluate(batch, **kwargs)
            if self.etype == ExpressionType.LOGICAL_AND:
                if left_batch.all_false():
                    return left_batch
                mask = left_batch.create_mask()
            elif self.etype == ExpressionType.LOGICAL_OR:
                if left_batch.all_true():
                    return left_batch
                mask = left_batch.create_inverted_mask()
            pushdown_batch = batch[mask]
            pushdown_batch.reset_index()
            right_batch = self.get_child(1).evaluate(pushdown_batch, **kwargs)
            left_batch.update_indices(mask, right_batch)
            return left_batch
        else:
            batch = self.get_child(0).evaluate(batch, **kwargs)
            if self.etype == ExpressionType.LOGICAL_NOT:
                batch.invert()
                return batch

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

    def get_symbol(self) -> str:
        if self.etype == ExpressionType.LOGICAL_AND:
            return 'AND'
        elif self.etype == ExpressionType.LOGICAL_OR:
            return 'OR'
        elif self.etype == ExpressionType.LOGICAL_NOT:
            return 'NOT'
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        expr_str = '('
        if self.get_child(0):
            expr_str += f'{str(self.get_child(0))}'
        if self.etype:
            expr_str += f' {str(self.get_symbol())} '
        if self.get_child(1):
            expr_str += f'{str(self.get_child(1))}'
        expr_str += ')'
        return expr_str

    def __hash__(self) -> int:
        return super().__hash__()

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, LogicalExpression):
        return False
    return is_subtree_equal and self.etype == other.etype

def conjunction_list_to_expression_tree(expression_list: List[AbstractExpression]) -> AbstractExpression:
    """Convert expression list to expression tree using conjunction connector

    [a, b, c] -> AND( AND(a, b), c)
    Args:
        expression_list (List[AbstractExpression]): list of conjunctives

    Returns:
        AbstractExpression: expression tree

    Example:
        conjunction_list_to_expression_tree([a, b, c] ): AND( AND(a, b), c)
    """
    if len(expression_list) == 0:
        return None
    prev_expr = expression_list[0]
    for expr in expression_list[1:]:
        if expr is not None:
            prev_expr = LogicalExpression(ExpressionType.LOGICAL_AND, prev_expr, expr)
    return prev_expr

def extract_range_list_from_comparison_expr(expr: ComparisonExpression, lower_bound: int, upper_bound: int) -> List:
    """Extracts the valid range from the comparison expression.

    The expression needs to be amongst <, >, <=, >=, =, !=.

    Args:
        expr (ComparisonExpression): comparison expression with two children
            that are leaf expression nodes. If the input does not match,
            the function return False
        lower_bound (int): lower bound of the comparison predicate
        upper_bound (int): upper bound of the comparison predicate

    Returns:
        List[Tuple(int)]: list of valid ranges

    Raises:
        RuntimeError: Invalid expression

    Example:
        extract_range_from_comparison_expr(id < 10, 0, inf): True, [(0,9)]
    """
    if not isinstance(expr, ComparisonExpression):
        raise RuntimeError(f'Expected Comparison Expression, got {type(expr)}')
    left = expr.children[0]
    right = expr.children[1]
    expr_type = expr.etype
    val = None
    const_first = False
    if isinstance(left, TupleValueExpression) and isinstance(right, ConstantValueExpression):
        val = right.value
    elif isinstance(left, ConstantValueExpression) and isinstance(right, TupleValueExpression):
        val = left.value
        const_first = True
    else:
        raise RuntimeError(f'Only supports extracting range from Comparison Expression                 with two children TupleValueExpression and                 ConstantValueExpression, got {left} and {right}')
    if const_first:
        if expr_type is ExpressionType.COMPARE_GREATER:
            expr_type = ExpressionType.COMPARE_LESSER
        elif expr_type is ExpressionType.COMPARE_LESSER:
            expr_type = ExpressionType.COMPARE_GREATER
        elif expr_type is ExpressionType.COMPARE_GEQ:
            expr_type = ExpressionType.COMPARE_LEQ
        elif expr_type is ExpressionType.COMPARE_LEQ:
            expr_type = ExpressionType.COMPARE_GEQ
    valid_ranges = []
    if expr_type == ExpressionType.COMPARE_EQUAL:
        valid_ranges.append((val, val))
    elif expr_type == ExpressionType.COMPARE_NEQ:
        valid_ranges.append((lower_bound, val - 1))
        valid_ranges.append((val + 1, upper_bound))
    elif expr_type == ExpressionType.COMPARE_GREATER:
        valid_ranges.append((val + 1, upper_bound))
    elif expr_type == ExpressionType.COMPARE_GEQ:
        valid_ranges.append((val, upper_bound))
    elif expr_type == ExpressionType.COMPARE_LESSER:
        valid_ranges.append((lower_bound, val - 1))
    elif expr_type == ExpressionType.COMPARE_LEQ:
        valid_ranges.append((lower_bound, val))
    else:
        raise RuntimeError(f'Unsupported Expression Type {expr_type}')
    return valid_ranges

def extract_range_list_from_predicate(predicate: AbstractExpression, lower_bound: int, upper_bound: int) -> List:
    """The function converts the range predicate on the column in the
        `predicate` to a list of [(start_1, end_1), ... ] pairs.

        It assumes the predicate contains conditions on only one column.
        It is the responsibility of the caller that `predicate` does not contains conditions on multiple columns.

    Args:
        predicate (AbstractExpression): Input predicate to extract
            valid ranges. The predicate should contain conditions on
            only one columns, else it raise error.
        lower_bound (int): lower bound of the comparison predicate
        upper_bound (int): upper bound of the comparison predicate

    Returns:
        List[Tuple]: list of (start, end) pairs of valid ranges

    Example:
            id < 10 : [(0, 9)]
            id > 5 AND id < 10 : [(6, 9)]
            id < 10 OR id >20 : [(0, 9), (21, Inf)]
    """

    def overlap(x, y):
        overlap = (max(x[0], y[0]), min(x[1], y[1]))
        if overlap[0] <= overlap[1]:
            return overlap

    def union(ranges: List):
        reduced_list = []
        for begin, end in sorted(ranges):
            if reduced_list and reduced_list[-1][1] >= begin - 1:
                reduced_list[-1] = (reduced_list[-1][0], max(reduced_list[-1][1], end))
            else:
                reduced_list.append((begin, end))
        return reduced_list
    if predicate.etype == ExpressionType.LOGICAL_AND:
        left_ranges = extract_range_list_from_predicate(predicate.children[0], lower_bound, upper_bound)
        right_ranges = extract_range_list_from_predicate(predicate.children[1], lower_bound, upper_bound)
        valid_overlaps = []
        for left_range in left_ranges:
            for right_range in right_ranges:
                over = overlap(left_range, right_range)
                if over:
                    valid_overlaps.append(over)
        return union(valid_overlaps)
    elif predicate.etype == ExpressionType.LOGICAL_OR:
        left_ranges = extract_range_list_from_predicate(predicate.children[0], lower_bound, upper_bound)
        right_ranges = extract_range_list_from_predicate(predicate.children[1], lower_bound, upper_bound)
        return union(left_ranges + right_ranges)
    elif isinstance(predicate, ComparisonExpression):
        return union(extract_range_list_from_comparison_expr(predicate, lower_bound, upper_bound))
    else:
        raise RuntimeError(f'Contains unsupported expression {type(predicate)}')

def get_columns_in_predicate(predicate: AbstractExpression) -> Set[str]:
    """Get columns accessed in the predicate

    Args:
        predicate (AbstractExpression): input predicate

    Returns:
        Set[str]: list of column aliases used in the predicate
    """
    if isinstance(predicate, TupleValueExpression):
        return set([predicate.col_alias])
    cols = set()
    for child in predicate.children:
        child_cols = get_columns_in_predicate(child)
        if len(child_cols):
            cols.update(child_cols)
    return cols

def contains_single_column(predicate: AbstractExpression, column: str=None) -> bool:
    """Checks if predicate contains conditions on single predicate

    Args:
        predicate (AbstractExpression): predicate expression
        column_alias (str): check if the single column matches
            the input column_alias
    Returns:
        bool: True, if contains single predicate, else False
            if predicate is None, return False
    """
    if not predicate:
        return False
    cols = get_columns_in_predicate(predicate)
    if len(cols) == 1:
        if column is None:
            return True
        pred_col = cols.pop()
        if pred_col == column:
            return True
    return False

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

def get_child(self, index: int):
    assert self._children is not None
    assert index >= 0 and index < len(self._children)
    return self._children[index]

def get_children_count(self) -> int:
    return len(self._children)

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

def _gpu_enabled_function(self):
    if self._function_instance is None:
        self._function_instance = self.function()
        if isinstance(self._function_instance, GPUCompatible):
            device = self._context.gpu_device()
            if device != NO_GPU:
                self._function_instance = self._function_instance.to_device(device)
    return self._function_instance

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, FunctionExpression):
        return False
    return is_subtree_equal and self.name == other.name and (self.output == other.output) and (self.alias == other.alias) and (self.function == other.function) and (self.output_objs == other.output_objs) and (self._cache == other._cache)

class ComparisonExpression(AbstractExpression):

    def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
        children = []
        if left is not None:
            children.append(left)
        if right is not None:
            children.append(right)
        super().__init__(exp_type, rtype=ExpressionReturnType.BOOLEAN, children=children)

    def evaluate(self, *args, **kwargs):
        lbatch = self.get_child(0).evaluate(*args, **kwargs)
        rbatch = self.get_child(1).evaluate(*args, **kwargs)
        assert len(lbatch) == len(rbatch), f'Left and Right batch does not have equal elements: left: {len(lbatch)} right: {len(rbatch)}'
        assert self.etype in [ExpressionType.COMPARE_EQUAL, ExpressionType.COMPARE_GREATER, ExpressionType.COMPARE_LESSER, ExpressionType.COMPARE_GEQ, ExpressionType.COMPARE_LEQ, ExpressionType.COMPARE_NEQ, ExpressionType.COMPARE_CONTAINS, ExpressionType.COMPARE_IS_CONTAINED, ExpressionType.COMPARE_LIKE], f'Expression type not supported {self.etype}'
        if self.etype == ExpressionType.COMPARE_EQUAL:
            return Batch.from_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_GREATER:
            return Batch.from_greater(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_LESSER:
            return Batch.from_lesser(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_GEQ:
            return Batch.from_greater_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_LEQ:
            return Batch.from_lesser_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_NEQ:
            return Batch.from_not_eq(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_CONTAINS:
            return Batch.compare_contains(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_IS_CONTAINED:
            return Batch.compare_is_contained(lbatch, rbatch)
        elif self.etype == ExpressionType.COMPARE_LIKE:
            return Batch.compare_like(lbatch, rbatch)

    def get_symbol(self) -> str:
        if self.etype == ExpressionType.COMPARE_EQUAL:
            return '='
        elif self.etype == ExpressionType.COMPARE_GREATER:
            return '>'
        elif self.etype == ExpressionType.COMPARE_LESSER:
            return '<'
        elif self.etype == ExpressionType.COMPARE_GEQ:
            return '>='
        elif self.etype == ExpressionType.COMPARE_LEQ:
            return '<='
        elif self.etype == ExpressionType.COMPARE_NEQ:
            return '!='
        elif self.etype == ExpressionType.COMPARE_CONTAINS:
            return '@>'
        elif self.etype == ExpressionType.COMPARE_IS_CONTAINED:
            return '<@'

    def __str__(self) -> str:
        expr_str = '('
        if self.get_child(0):
            expr_str += f'{self.get_child(0)}'
        if self.etype:
            expr_str += f' {self.get_symbol()} '
        if self.get_child(1):
            expr_str += f'{self.get_child(1)}'
        expr_str += ')'
        return expr_str

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, ComparisonExpression):
            return False
        return is_subtree_equal and self.etype == other.etype

    def __hash__(self) -> int:
        return super().__hash__()

def __eq__(self, other):
    is_subtree_equal = super().__eq__(other)
    if not isinstance(other, ComparisonExpression):
        return False
    return is_subtree_equal and self.etype == other.etype

class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """
    _instances = WeakValueDictionary()
    _lock: Lock = Lock()

    def __call__(cls, uri):
        key = (cls, uri)
        with cls._lock:
            if key not in cls._instances:
                instance = super().__call__(uri)
                cls._instances[key] = instance
        return cls._instances[key]

def __call__(cls, uri):
    key = (cls, uri)
    with cls._lock:
        if key not in cls._instances:
            instance = super().__call__(uri)
            cls._instances[key] = instance
    return cls._instances[key]

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

class VideoColumnName(EvaDBEnum):
    name
    id
    data
    seconds
    audio

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, EvaDBEnum):
            return self.value == other.value
        return False

def __eq__(self, other):
    if isinstance(other, str):
        return self.name == other
    if isinstance(other, EvaDBEnum):
        return self.value == other.value
    return False

def get_video_table_column_definitions() -> List[ColumnDefinition]:
    """
    name: video path
    id: frame id
    data: frame data
    audio: frame audio
    """
    columns = [ColumnDefinition(VideoColumnName.name.name, ColumnType.TEXT, None, None, ColConstraintInfo(unique=True)), ColumnDefinition(VideoColumnName.id.name, ColumnType.INTEGER, None, None), ColumnDefinition(VideoColumnName.data.name, ColumnType.NDARRAY, NdArrayType.UINT8, (None, None, None)), ColumnDefinition(VideoColumnName.seconds.name, ColumnType.FLOAT, None, [])]
    return columns

def get_image_table_column_definitions() -> List[ColumnDefinition]:
    """
    name: image path
    data: image decoded data
    """
    columns = [ColumnDefinition(ImageColumnName.name.name, ColumnType.TEXT, None, None, ColConstraintInfo(unique=True)), ColumnDefinition(ImageColumnName.data.name, ColumnType.NDARRAY, NdArrayType.UINT8, (None, None, None))]
    return columns

def get_document_table_column_definitions() -> List[ColumnDefinition]:
    """
    name: file path
    chunk_id: chunk id (0-indexed for each file)
    data: text data associated with the chunk
    """
    columns = [ColumnDefinition(DocumentColumnName.name.name, ColumnType.TEXT, None, None, ColConstraintInfo(unique=True)), ColumnDefinition(DocumentColumnName.chunk_id.name, ColumnType.INTEGER, None, None), ColumnDefinition(DocumentColumnName.data.name, ColumnType.TEXT, None, None)]
    return columns

def get_pdf_table_column_definitions() -> List[ColumnDefinition]:
    """
    name: pdf name
    page: page no
    paragraph: paragraph no
    data: pdf paragraph data
    """
    columns = [ColumnDefinition(PDFColumnName.name.name, ColumnType.TEXT, None, None), ColumnDefinition(PDFColumnName.page.name, ColumnType.INTEGER, None, None), ColumnDefinition(PDFColumnName.paragraph.name, ColumnType.INTEGER, None, None), ColumnDefinition(PDFColumnName.data.name, ColumnType.TEXT, None, None)]
    return columns

class TextPickleType(TypeDecorator):
    """Used to handle serialization and deserialization to Text
    https://stackoverflow.com/questions/1378325/python-dicts-in-sqlalchemy
    """
    impl = sqlalchemy.String(1024)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

def process_bind_param(self, value, dialect):
    if value is not None:
        value = json.dumps(value)
    return value

class InsertTableStatement(AbstractStatement):
    """
    Insert Table Statement constructed after parsing the input query

    Attributes
    ----------
    TableRef:
        table reference in the insert table statement
    ColumnList:
        list of columns
    ValueList:
        list of values to fill
    """

    def __init__(self, table_ref: TableRef, column_list: List[AbstractExpression]=None, value_list: List[AbstractExpression]=None):
        super().__init__(StatementType.INSERT)
        self._table_ref = table_ref
        self._column_list = column_list
        self._value_list = value_list

    def __str__(self) -> str:
        column_list_str = ''
        if self._column_list is not None:
            for expr in self._column_list:
                column_list_str += str(expr) + ', '
            column_list_str = column_list_str.rstrip(', ')
        value_list_str = ''
        if self._value_list is not None:
            for expr in self._value_list:
                value_list_str += str(expr) + ', '
            value_list_str = value_list_str.rstrip(', ')
        print_str = 'INSERT INTO {}({}) VALUES ({}) '.format(self._table_ref, column_list_str, value_list_str)
        return print_str

    @property
    def table_ref(self) -> TableRef:
        return self._table_ref

    @property
    def column_list(self) -> List[AbstractExpression]:
        return self._column_list

    @property
    def value_list(self) -> List[AbstractExpression]:
        return self._value_list

    def __eq__(self, other):
        if not isinstance(other, InsertTableStatement):
            return False
        return self.table_ref == other.table_ref and self.column_list == other.column_list and (self.value_list == other.value_list)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_ref, tuple(self.column_list), tuple((tuple(val) for val in self.value_list))))

def __eq__(self, other):
    if not isinstance(other, InsertTableStatement):
        return False
    return self.table_ref == other.table_ref and self.column_list == other.column_list and (self.value_list == other.value_list)

class ColConstraintInfo:

    def __init__(self, nullable=False, default_value=None, primary=False, unique=False):
        self.nullable = nullable
        self.default_value = default_value
        self.primary = primary
        self.unique = unique

    def __eq__(self, other):
        if not isinstance(other, ColConstraintInfo):
            return False
        return self.nullable == other.nullable and self.default_value == other.default_value and (self.primary == other.primary) and (self.unique == other.unique)

    def __hash__(self) -> int:
        return hash((self.nullable, self.default_value, self.primary, self.unique))

def __eq__(self, other):
    if not isinstance(other, ColConstraintInfo):
        return False
    return self.nullable == other.nullable and self.default_value == other.default_value and (self.primary == other.primary) and (self.unique == other.unique)

class ColumnDefinition:

    def __init__(self, col_name: str, col_type: ColumnType, col_array_type: NdArrayType, col_dim: Tuple[int], cci: ColConstraintInfo=ColConstraintInfo()):
        self._name = col_name
        self._type = col_type
        self._array_type = col_array_type
        self._dimension = col_dim or ()
        self._cci = cci

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def type(self):
        return self._type

    @property
    def array_type(self):
        return self._array_type

    @property
    def dimension(self):
        return self._dimension

    @property
    def cci(self):
        return self._cci

    def __str__(self):
        dimension_str = ''
        if self._dimension is not None:
            dimension_str += '['
            for dim in self._dimension:
                dimension_str += str(dim) + ', '
            dimension_str = dimension_str.rstrip(', ')
            dimension_str += ']'
        if self.array_type is None:
            return '{} {}'.format(self._name, self._type)
        else:
            return '{} {} {} {}'.format(self._name, self._type, self.array_type, dimension_str)

    def __eq__(self, other):
        if not isinstance(other, ColumnDefinition):
            return False
        return self.name == other.name and self.type == other.type and (self.array_type == other.array_type) and (self.dimension == other.dimension) and (self.cci == other.cci)

    def __hash__(self) -> int:
        return hash((self.name, self.type, self.array_type, self.dimension, self.cci))

def __init__(self, col_name: str, col_type: ColumnType, col_array_type: NdArrayType, col_dim: Tuple[int], cci: ColConstraintInfo=ColConstraintInfo()):
    self._name = col_name
    self._type = col_type
    self._array_type = col_array_type
    self._dimension = col_dim or ()
    self._cci = cci

def __eq__(self, other):
    if not isinstance(other, ColumnDefinition):
        return False
    return self.name == other.name and self.type == other.type and (self.array_type == other.array_type) and (self.dimension == other.dimension) and (self.cci == other.cci)

class CreateTableStatement(AbstractStatement):
    """Create Table Statement constructed after parsing the input query

    Attributes:
        TableRef: table reference in the create table statement
        ColumnList: list of columns
    """

    def __init__(self, table_info: TableInfo, if_not_exists: bool, column_list: List[ColumnDefinition]=None, query: SelectStatement=None):
        super().__init__(StatementType.CREATE)
        self._table_info = table_info
        self._if_not_exists = if_not_exists
        self._column_list = column_list
        self._query = query

    def __str__(self) -> str:
        print_str = 'CREATE TABLE {} ({}) \n'.format(self._table_info, self._if_not_exists)
        if self._query is not None:
            print_str = 'CREATE TABLE {} AS {}\n'.format(self._table_info, self._query)
        for column in self.column_list:
            print_str += str(column) + '\n'
        return print_str

    @property
    def table_info(self):
        return self._table_info

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def column_list(self):
        return self._column_list

    @property
    def query(self):
        return self._query

    @column_list.setter
    def column_list(self, value):
        self._column_list = value

    def __eq__(self, other):
        if not isinstance(other, CreateTableStatement):
            return False
        return self.table_info == other.table_info and self.if_not_exists == other.if_not_exists and (self.column_list == other.column_list) and (self.query == other.query)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_info, self.if_not_exists, tuple(self.column_list or []), self.query))

def __eq__(self, other):
    if not isinstance(other, CreateTableStatement):
        return False
    return self.table_info == other.table_info and self.if_not_exists == other.if_not_exists and (self.column_list == other.column_list) and (self.query == other.query)

class CreateDatabaseStatement(AbstractStatement):

    def __init__(self, database_name: str, if_not_exists: bool, engine: str, param_dict: dict):
        super().__init__(StatementType.CREATE_DATABASE)
        self.database_name = database_name
        self.if_not_exists = if_not_exists
        self.engine = engine
        self.param_dict = param_dict

    def __eq__(self, other):
        if not isinstance(other, CreateDatabaseStatement):
            return False
        return self.database_name == other.database_name and self.if_not_exists == other.if_not_exists and (self.engine == other.engine) and (self.param_dict == other.param_dict)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.database_name, self.if_not_exists, self.engine, hash(frozenset(self.param_dict.items()))))

    def __str__(self) -> str:
        return f"CREATE DATABASE {self.database_name} \nWITH ENGINE '{self.engine}' , \nPARAMETERS = {self.param_dict};"

def __eq__(self, other):
    if not isinstance(other, CreateDatabaseStatement):
        return False
    return self.database_name == other.database_name and self.if_not_exists == other.if_not_exists and (self.engine == other.engine) and (self.param_dict == other.param_dict)

class SetStatement(AbstractStatement):

    def __init__(self, config_name: str, config_value: Any):
        super().__init__(StatementType.SET)
        self._config_name = config_name
        self._config_value = config_value

    @property
    def config_name(self):
        return self._config_name

    @property
    def config_value(self):
        return self._config_value

    def __str__(self):
        return f'SET {str(self.config_name)} = {str(self.config_value)}'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SetStatement):
            return False
        return self.config_name == other.config_name and self.config_value == other.config_value

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.config_name, self.config_value))

def __eq__(self, other: object) -> bool:
    if not isinstance(other, SetStatement):
        return False
    return self.config_name == other.config_name and self.config_value == other.config_value

def parse_expression(expr: str):
    mock_query = f'SELECT {expr} FROM DUMMY;'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, SelectStatement), 'Expected a select statement'
    return stmt.target_list

def parse_predicate_expression(expr: str):
    mock_query = f'SELECT * FROM DUMMY WHERE {expr};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, SelectStatement), 'Expected a select statement'
    return stmt.where_clause

def parse_table_clause(expr: str, chunk_size: int=None, chunk_overlap: int=None):
    mock_query_parts = [f'SELECT * FROM {expr}']
    if chunk_size is not None:
        mock_query_parts.append(f'CHUNK_SIZE {chunk_size}')
    if chunk_overlap is not None:
        mock_query_parts.append(f'CHUNK_OVERLAP {chunk_overlap}')
    mock_query_parts.append(';')
    mock_query = ' '.join(mock_query_parts)
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, SelectStatement), 'Expected a select statement'
    assert stmt.from_table.is_table_atom
    return stmt.from_table

def parse_create_function(function_name: str, if_not_exists: bool, function_file_path: str, type: str, **kwargs):
    mock_query = f'CREATE FUNCTION IF NOT EXISTS {function_name}' if if_not_exists else f'CREATE FUNCTION {function_name}'
    if type is not None:
        mock_query += f' TYPE {type}'
        task, model = (kwargs['task'], kwargs['model'])
        if task is not None and model is not None:
            mock_query += f" TASK '{task}' MODEL '{model}'"
    else:
        mock_query += f" IMPL '{function_file_path}'"
    mock_query += ';'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, CreateFunctionStatement), 'Expected a create function statement'
    return stmt

def parse_create_table(table_name: str, if_not_exists: bool, columns: str, **kwargs):
    mock_query = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns});' if if_not_exists else f'CREATE TABLE {table_name} ({columns});'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, CreateTableStatement), 'Expected a create table statement'
    return stmt

def parse_show(show_type: str, **kwargs):
    mock_query = f'SHOW {show_type};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, ShowStatement), 'Expected a show statement'
    return stmt

def parse_explain(query: str, **kwargs):
    mock_query = f'EXPLAIN {query};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, ExplainStatement), 'Expected a explain statement'
    return stmt

def parse_insert(table_name: str, columns: str, values: str, **kwargs):
    mock_query = f'INSERT INTO {table_name} {columns} VALUES {values};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, InsertTableStatement), 'Expected a insert statement'
    return stmt

def parse_load(table_name: str, file_regex: str, format: str, **kwargs):
    mock_query = f"LOAD {format.upper()} '{file_regex}' INTO {table_name};"
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, LoadDataStatement), 'Expected a load statement'
    return stmt

def parse_drop(object_type: ObjectType, name: str, if_exists: bool):
    mock_query = f'DROP {object_type}'
    mock_query = f' {mock_query} IF EXISTS {name} ' if if_exists else f'{mock_query} {name}'
    mock_query += ';'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, DropObjectStatement), 'Expected a drop object statement'
    return stmt

def parse_query(query):
    stmt = Parser().parse(query)
    assert len(stmt) == 1
    return stmt[0]

def parse_lateral_join(expr: str, alias: str):
    mock_query = f'SELECT * FROM DUMMY JOIN LATERAL {expr} AS {alias};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, SelectStatement), 'Expected a select statement'
    assert stmt.from_table.is_join()
    return stmt.from_table.join_node.right

def parse_create_vector_index(index_name: str, table_name: str, expr: str, using: str):
    mock_query = f'CREATE INDEX {index_name} ON {table_name} ({expr}) USING {using};'
    stmt = Parser().parse(mock_query)[0]
    return stmt

def parse_sql_orderby_expr(expr: str):
    mock_query = f'SELECT * FROM DUMMY ORDER BY {expr};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, SelectStatement), 'Expected a select statement'
    return stmt.orderby_list

def parse_rename(old_name: str, new_name: str):
    mock_query = f'RENAME TABLE {old_name} TO {new_name};'
    stmt = Parser().parse(mock_query)[0]
    assert isinstance(stmt, RenameTableStatement), 'Expected a rename statement'
    return stmt

class Alias:

    def __init__(self, alias_name: str, col_names: List[str]=[]) -> None:
        self._alias_name = alias_name
        self._col_names = col_names

    @property
    def alias_name(self):
        return self._alias_name

    @property
    def col_names(self):
        return self._col_names

    def __hash__(self) -> int:
        return hash((self.alias_name, tuple(self.col_names)))

    def __eq__(self, other):
        if not isinstance(other, Alias):
            return False
        return self.alias_name == other.alias_name and self.col_names == other.col_names

    def __str__(self):
        msg = f'{self.alias_name}'
        if len(self.col_names) > 0:
            msg += f'({str(self.col_names)})'
        return msg

def __eq__(self, other):
    if not isinstance(other, Alias):
        return False
    return self.alias_name == other.alias_name and self.col_names == other.col_names

class DeleteTableStatement(AbstractStatement):
    """Delete Table Statement constructed after parsing the input query

    Attributes:
        TableRef: table reference in the delete table statement
        _where_clause : predicate of the select query, represented as a expression tree.
    """

    def __init__(self, table_ref: TableRef, where_clause: AbstractExpression=None):
        super().__init__(StatementType.DELETE)
        self._table_ref = table_ref
        self._where_clause = where_clause

    def __str__(self) -> str:
        delete_str = f'DELETE FROM {self._table_ref}'
        if self._where_clause is not None:
            delete_str += ' WHERE ' + str(self._where_clause)
        return delete_str

    @property
    def table_ref(self):
        return self._table_ref

    @property
    def where_clause(self):
        return self._where_clause

    def __eq__(self, other):
        if not isinstance(other, DeleteTableStatement):
            return False
        return self._table_ref == other._table_ref and self.where_clause == other.where_clause

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._table_ref, self.where_clause))

def __eq__(self, other):
    if not isinstance(other, DeleteTableStatement):
        return False
    return self._table_ref == other._table_ref and self.where_clause == other.where_clause

class SelectStatement(AbstractStatement):
    """
    Select Statement constructed after parsing the input query

    Attributes
    ----------
    _target_list : List[AbstractExpression]
        list of target attributes in the select query,
        each attribute is represented as a Abstract Expression
    _from_table : TableRef | Select Statement
        table reference in the select query, can be a select statement
        in nested queries
    _where_clause : AbstractExpression
        predicate of the select query, represented as a expression tree.
    **kwargs : to support other functionality, Orderby, Distinct, Groupby.
    """

    def __init__(self, target_list: List[AbstractExpression]=None, from_table: Union[TableRef, SelectStatement]=None, where_clause: AbstractExpression=None, **kwargs):
        super().__init__(StatementType.SELECT)
        self._from_table = from_table
        self._where_clause = where_clause
        self._target_list = target_list
        self._union_link = None
        self._union_all = False
        self._groupby_clause = kwargs.get('groupby_clause', None)
        self._orderby_list = kwargs.get('orderby_list', None)
        self._limit_count = kwargs.get('limit_count', None)

    @property
    def union_link(self):
        return self._union_link

    @union_link.setter
    def union_link(self, next_select: 'SelectStatement'):
        self._union_link = next_select

    @property
    def union_all(self):
        return self._union_all

    @union_all.setter
    def union_all(self, all: bool):
        self._union_all = all

    @property
    def where_clause(self):
        return self._where_clause

    @where_clause.setter
    def where_clause(self, where_expr: AbstractExpression):
        self._where_clause = where_expr

    @property
    def target_list(self):
        return self._target_list

    @target_list.setter
    def target_list(self, target_expr_list: List[AbstractExpression]):
        self._target_list = target_expr_list

    @property
    def from_table(self):
        return self._from_table

    @from_table.setter
    def from_table(self, table: TableRef):
        self._from_table = table

    @property
    def groupby_clause(self):
        return self._groupby_clause

    @groupby_clause.setter
    def groupby_clause(self, groupby_clause):
        self._groupby_clause = groupby_clause

    @property
    def orderby_list(self):
        return self._orderby_list

    @orderby_list.setter
    def orderby_list(self, orderby_list):
        self._orderby_list = orderby_list

    @property
    def limit_count(self):
        return self._limit_count

    @limit_count.setter
    def limit_count(self, limit_count):
        self._limit_count = limit_count

    def __str__(self) -> str:
        target_list_str = ''
        if self._target_list is not None:
            for expr in self._target_list:
                target_list_str += str(expr) + ', '
            target_list_str = target_list_str.rstrip(', ')
        orderby_list_str = ''
        if self._orderby_list is not None:
            for expr in self._orderby_list:
                sort_str = ''
                if expr[1] == ParserOrderBySortType.ASC:
                    sort_str = 'ASC'
                elif expr[1] == ParserOrderBySortType.DESC:
                    sort_str = 'DESC'
                orderby_list_str += str(expr[0]) + ' ' + sort_str + ', '
            orderby_list_str = orderby_list_str.rstrip(', ')
        select_str = f'SELECT {target_list_str}'
        if self._from_table is not None:
            select_str += ' FROM ' + str(self._from_table)
        if self._where_clause is not None:
            select_str += ' WHERE ' + str(self._where_clause)
        if self._union_link is not None:
            if not self._union_all:
                select_str += ' UNION ' + str(self._union_link)
            else:
                select_str += ' UNION ALL ' + str(self._union_link)
        if self._groupby_clause is not None:
            select_str += ' GROUP BY ' + str(self._groupby_clause)
        if self._orderby_list is not None:
            select_str += ' ORDER BY ' + orderby_list_str
        if self._limit_count is not None:
            select_str += ' LIMIT ' + str(self._limit_count)
        select_str = select_str.rstrip(' ')
        return select_str

    def __eq__(self, other):
        if not isinstance(other, SelectStatement):
            return False
        return self.from_table == other.from_table and self.target_list == other.target_list and (self.where_clause == other.where_clause) and (self.union_link == other.union_link) and (self.union_all == other.union_all) and (self._groupby_clause == other.groupby_clause) and (self.orderby_list == other.orderby_list) and (self.limit_count == other.limit_count)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.from_table, tuple(self.target_list or []), self.where_clause, self.union_link, self.union_all, self.groupby_clause, tuple(self.orderby_list or []), self.limit_count))

def __eq__(self, other):
    if not isinstance(other, SelectStatement):
        return False
    return self.from_table == other.from_table and self.target_list == other.target_list and (self.where_clause == other.where_clause) and (self.union_link == other.union_link) and (self.union_all == other.union_all) and (self._groupby_clause == other.groupby_clause) and (self.orderby_list == other.orderby_list) and (self.limit_count == other.limit_count)

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

def parse(self, query_string: str) -> list:
    lark_output = self._lark_parser.parse(query_string)
    return lark_output

class LoadDataStatement(AbstractStatement):
    """
    Load Data Statement constructed after parsing the input query

    Arguments:
    table (TableInfo): table to load into
    path (str): path from where data needs to be loaded
    """

    def __init__(self, table_info: TableInfo, path: str, column_list: List[AbstractExpression]=None, file_options: dict=None):
        super().__init__(StatementType.LOAD_DATA)
        self._table_info = table_info
        self._path = Path(path)
        self._column_list = column_list
        self._file_options = file_options

    def __str__(self) -> str:
        file_option_str = ''
        for key, value in self._file_options.items():
            file_option_str += f'{str(key)}: {str(value)}'
        column_list_str = ''
        if self._column_list is not None:
            for col in self._column_list:
                column_list_str += str(col) + ', '
            column_list_str = column_list_str.rstrip(', ')
        if self._column_list is None:
            load_stmt_str = 'LOAD {} INTO {} WITH {}'.format(self._path.name, self._table_info, file_option_str)
        else:
            load_stmt_str = 'LOAD {} INTO {} ({}) WITH {}'.format(self._path.name, self._table_info, column_list_str, file_option_str)
        return load_stmt_str

    @property
    def table_info(self) -> TableInfo:
        return self._table_info

    @property
    def path(self) -> Path:
        return self._path

    @property
    def column_list(self) -> List[AbstractExpression]:
        return self._column_list

    @property
    def file_options(self) -> dict:
        return self._file_options

    def __eq__(self, other):
        if not isinstance(other, LoadDataStatement):
            return False
        return self.table_info == other.table_info and self.path == other.path and (self.column_list == other.column_list) and (self.file_options == other.file_options)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_info, self.path, tuple(self.column_list or []), frozenset(self.file_options.items())))

def __eq__(self, other):
    if not isinstance(other, LoadDataStatement):
        return False
    return self.table_info == other.table_info and self.path == other.path and (self.column_list == other.column_list) and (self.file_options == other.file_options)

class TableInfo:
    """
    stores all the table info, inspired from postgres
    """

    def __init__(self, table_name=None, schema_name=None, database_name=None):
        self._table_name = table_name
        self._schema_name = schema_name
        self._database_name = database_name
        self._table_obj = None

    @property
    def table_name(self):
        return self._table_name

    @property
    def schema_name(self):
        return self._schema_name

    @property
    def database_name(self):
        return self._database_name

    @property
    def table_obj(self):
        return self._table_obj

    @table_obj.setter
    def table_obj(self, obj):
        self._table_obj = obj

    def __str__(self):
        table_info_str = self._table_name
        return table_info_str

    def __eq__(self, other):
        if not isinstance(other, TableInfo):
            return False
        return self.table_name == other.table_name and self.schema_name == other.schema_name and (self.database_name == other.database_name) and (self.table_obj == other.table_obj)

    def __hash__(self) -> int:
        return hash((self.table_name, self.schema_name, self.database_name, self.table_obj))

def __eq__(self, other):
    if not isinstance(other, TableInfo):
        return False
    return self.table_name == other.table_name and self.schema_name == other.schema_name and (self.database_name == other.database_name) and (self.table_obj == other.table_obj)

class JoinNode:

    def __init__(self, left: 'TableRef'=None, right: 'TableRef'=None, predicate: AbstractExpression=None, join_type: JoinType=None) -> None:
        self.left = left
        self.right = right
        self.predicate = predicate
        self.join_type = join_type

    def __eq__(self, other):
        if not isinstance(other, JoinNode):
            return False
        return self.left == other.left and self.right == other.right and (self.predicate == other.predicate) and (self.join_type == other.join_type)

    def __str__(self) -> str:
        if self.predicate is not None:
            return '{} {} {} ON {}'.format(self.left, self.join_type, self.right, self.predicate)
        else:
            return '{} {} {}'.format(self.left, self.join_type, self.right)

    def __hash__(self) -> int:
        return hash((self.join_type, self.left, self.right, self.predicate))

def __eq__(self, other):
    if not isinstance(other, JoinNode):
        return False
    return self.left == other.left and self.right == other.right and (self.predicate == other.predicate) and (self.join_type == other.join_type)

class TableValuedExpression:

    def __init__(self, func_expr: FunctionExpression, do_unnest: bool=False) -> None:
        self._func_expr = func_expr
        self._do_unnest = do_unnest

    @property
    def func_expr(self):
        return self._func_expr

    @property
    def do_unnest(self):
        return self._do_unnest

    def __str__(self) -> str:
        if self.do_unnest:
            return f'unnest({self._func_expr})'
        return f'{self._func_expr}'

    def __eq__(self, other):
        if not isinstance(other, TableValuedExpression):
            return False
        return self.func_expr == other.func_expr and self.do_unnest == other.do_unnest

    def __hash__(self) -> int:
        return hash((self.func_expr, self.do_unnest))

def __eq__(self, other):
    if not isinstance(other, TableValuedExpression):
        return False
    return self.func_expr == other.func_expr and self.do_unnest == other.do_unnest

class TableRef:
    """
    Attributes:
        : can be one of the following based on the query type:
            TableInfo: expression of table name and database name,
            TableValuedExpression: lateral function calls
            SelectStatement: select statement in case of nested queries,
            JoinNode: join node in case of join queries
        sample_freq: sampling frequency for the table reference
    """

    def __init__(self, table: Union[TableInfo, TableValuedExpression, SelectStatement, JoinNode], alias: Alias=None, sample_freq: float=None, sample_type: str=None, get_audio: bool=False, get_video: bool=False, chunk_params: dict={}):
        self._ref_handle = table
        self._sample_freq = sample_freq
        self._sample_type = sample_type
        self._get_audio = get_audio
        self._get_video = get_video
        self.chunk_params = chunk_params
        self.alias = alias or self.generate_alias()

    @property
    def sample_freq(self):
        return self._sample_freq

    @property
    def sample_type(self):
        return self._sample_type

    @property
    def get_audio(self):
        return self._get_audio

    @property
    def get_video(self):
        return self._get_video

    @get_audio.setter
    def get_audio(self, get_audio):
        self._get_audio = get_audio

    @get_video.setter
    def get_video(self, get_video):
        self._get_video = get_video

    def is_table_atom(self) -> bool:
        return isinstance(self._ref_handle, TableInfo)

    def is_table_valued_expr(self) -> bool:
        return isinstance(self._ref_handle, TableValuedExpression)

    def is_select(self) -> bool:
        return isinstance(self._ref_handle, SelectStatement)

    def is_join(self) -> bool:
        return isinstance(self._ref_handle, JoinNode)

    @property
    def ref_handle(self) -> Union[TableInfo, TableValuedExpression, SelectStatement, JoinNode]:
        return self._ref_handle

    @property
    def table(self) -> TableInfo:
        assert isinstance(self._ref_handle, TableInfo), 'Expected                 TableInfo, got {}'.format(type(self._ref_handle))
        return self._ref_handle

    @property
    def table_valued_expr(self) -> TableValuedExpression:
        assert isinstance(self._ref_handle, TableValuedExpression), 'Expected                 TableValuedExpression, got {}'.format(type(self._ref_handle))
        return self._ref_handle

    @property
    def join_node(self) -> JoinNode:
        assert isinstance(self._ref_handle, JoinNode), 'Expected                 JoinNode, got {}'.format(type(self._ref_handle))
        return self._ref_handle

    @property
    def select_statement(self) -> SelectStatement:
        assert isinstance(self._ref_handle, SelectStatement), 'Expected                 SelectStatement, got{}'.format(type(self._ref_handle))
        return self._ref_handle

    def generate_alias(self) -> Alias:
        if isinstance(self._ref_handle, TableInfo):
            return Alias(self._ref_handle.table_name.lower())

    def __str__(self):
        parts = []
        if self.is_select():
            parts.append(f'( {str(self._ref_handle)} ) AS {self.alias}')
        else:
            parts.append(str(self._ref_handle))
        if self.sample_freq is not None:
            parts.append(str(self.sample_freq))
        if self.sample_type is not None:
            parts.append(str(self.sample_type))
        if self.chunk_params is not None:
            parts.append(' '.join([f'{key}: {value}' for key, value in self.chunk_params.items()]))
        return ' '.join(parts)

    def __eq__(self, other):
        if not isinstance(other, TableRef):
            return False
        return self._ref_handle == other._ref_handle and self.alias == other.alias and (self.sample_freq == other.sample_freq) and (self.sample_type == other.sample_type) and (self.get_video == other.get_video) and (self.get_audio == other.get_audio) and (self.chunk_params == other.chunk_params)

    def __hash__(self) -> int:
        return hash((self._ref_handle, self.alias, self.sample_freq, self.sample_type, self.get_video, self.get_audio, frozenset(self.chunk_params.items())))

def is_table_atom(self) -> bool:
    return isinstance(self._ref_handle, TableInfo)

def is_table_valued_expr(self) -> bool:
    return isinstance(self._ref_handle, TableValuedExpression)

def is_select(self) -> bool:
    return isinstance(self._ref_handle, SelectStatement)

def is_join(self) -> bool:
    return isinstance(self._ref_handle, JoinNode)

@property
def table(self) -> TableInfo:
    assert isinstance(self._ref_handle, TableInfo), 'Expected                 TableInfo, got {}'.format(type(self._ref_handle))
    return self._ref_handle

@property
def table_valued_expr(self) -> TableValuedExpression:
    assert isinstance(self._ref_handle, TableValuedExpression), 'Expected                 TableValuedExpression, got {}'.format(type(self._ref_handle))
    return self._ref_handle

@property
def join_node(self) -> JoinNode:
    assert isinstance(self._ref_handle, JoinNode), 'Expected                 JoinNode, got {}'.format(type(self._ref_handle))
    return self._ref_handle

@property
def select_statement(self) -> SelectStatement:
    assert isinstance(self._ref_handle, SelectStatement), 'Expected                 SelectStatement, got{}'.format(type(self._ref_handle))
    return self._ref_handle

def generate_alias(self) -> Alias:
    if isinstance(self._ref_handle, TableInfo):
        return Alias(self._ref_handle.table_name.lower())

def __eq__(self, other):
    if not isinstance(other, TableRef):
        return False
    return self._ref_handle == other._ref_handle and self.alias == other.alias and (self.sample_freq == other.sample_freq) and (self.sample_type == other.sample_type) and (self.get_video == other.get_video) and (self.get_audio == other.get_audio) and (self.chunk_params == other.chunk_params)

class CreateIndexStatement(AbstractStatement):

    def __init__(self, name: str, if_not_exists: bool, table_ref: TableRef, col_list: List[ColumnDefinition], vector_store_type: VectorStoreType, project_expr_list: List[AbstractStatement]):
        super().__init__(StatementType.CREATE_INDEX)
        self._name = name
        self._if_not_exists = if_not_exists
        self._table_ref = table_ref
        self._col_list = col_list
        self._vector_store_type = vector_store_type
        self._project_expr_list = project_expr_list
        self._index_def = self.__str__()

    def __str__(self) -> str:
        function_expr = None
        for project_expr in self._project_expr_list:
            if isinstance(project_expr, FunctionExpression):
                function_expr = project_expr
        print_str = 'CREATE INDEX'
        if self._if_not_exists:
            print_str += ' IF NOT EXISTS'
        print_str += f' {self._name}'
        print_str += ' ON'
        print_str += f' {self._table_ref.table.table_name}'
        if function_expr is None:
            print_str += f' ({self.col_list[0].name})'
        else:

            def traverse_create_function_expression_str(expr):
                if isinstance(expr, TupleValueExpression):
                    return f'{self.col_list[0].name}'
                return f'{expr.name}({traverse_create_function_expression_str(expr.children[0])})'
            print_str += f' ({traverse_create_function_expression_str(function_expr)})'
        print_str += f' USING {self._vector_store_type};'
        return print_str

    @property
    def name(self):
        return self._name

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def table_ref(self):
        return self._table_ref

    @property
    def col_list(self):
        return self._col_list

    @property
    def vector_store_type(self):
        return self._vector_store_type

    @property
    def project_expr_list(self):
        return self._project_expr_list

    @project_expr_list.setter
    def project_expr_list(self, project_expr_list: List[AbstractExpression]):
        self._project_expr_list = project_expr_list

    @property
    def index_def(self):
        return self._index_def

    def __eq__(self, other):
        if not isinstance(other, CreateIndexStatement):
            return False
        return self._name == other.name and self._if_not_exists == other.if_not_exists and (self._table_ref == other.table_ref) and (self.col_list == other.col_list) and (self._vector_store_type == other.vector_store_type) and (self._project_expr_list == other.project_expr_list) and (self._index_def == other.index_def)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._name, self._if_not_exists, self._table_ref, tuple(self.col_list), self._vector_store_type, tuple(self._project_expr_list), self._index_def))

def __str__(self) -> str:
    function_expr = None
    for project_expr in self._project_expr_list:
        if isinstance(project_expr, FunctionExpression):
            function_expr = project_expr
    print_str = 'CREATE INDEX'
    if self._if_not_exists:
        print_str += ' IF NOT EXISTS'
    print_str += f' {self._name}'
    print_str += ' ON'
    print_str += f' {self._table_ref.table.table_name}'
    if function_expr is None:
        print_str += f' ({self.col_list[0].name})'
    else:

        def traverse_create_function_expression_str(expr):
            if isinstance(expr, TupleValueExpression):
                return f'{self.col_list[0].name}'
            return f'{expr.name}({traverse_create_function_expression_str(expr.children[0])})'
        print_str += f' ({traverse_create_function_expression_str(function_expr)})'
    print_str += f' USING {self._vector_store_type};'
    return print_str

def traverse_create_function_expression_str(expr):
    if isinstance(expr, TupleValueExpression):
        return f'{self.col_list[0].name}'
    return f'{expr.name}({traverse_create_function_expression_str(expr.children[0])})'

def __eq__(self, other):
    if not isinstance(other, CreateIndexStatement):
        return False
    return self._name == other.name and self._if_not_exists == other.if_not_exists and (self._table_ref == other.table_ref) and (self.col_list == other.col_list) and (self._vector_store_type == other.vector_store_type) and (self._project_expr_list == other.project_expr_list) and (self._index_def == other.index_def)

class RenameTableStatement(AbstractStatement):
    """Rename Table Statement constructed after parsing the input query

    Attributes:
        old_table_ref: table reference in the rename table statement
        new_table_name: new name of the table
    """

    def __init__(self, old_table_ref: TableRef, new_table_name: TableInfo):
        super().__init__(StatementType.RENAME)
        self._old_table_ref = old_table_ref
        self._new_table_name = new_table_name

    def __str__(self) -> str:
        print_str = 'RENAME TABLE {} TO {} '.format(self._old_table_ref, self._new_table_name)
        return print_str

    @property
    def old_table_ref(self):
        return self._old_table_ref

    @property
    def new_table_name(self):
        return self._new_table_name

    def __eq__(self, other):
        if not isinstance(other, RenameTableStatement):
            return False
        return self.old_table_ref == other.old_table_ref and self.new_table_name == other.new_table_name

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.old_table_ref, self.new_table_name))

def __eq__(self, other):
    if not isinstance(other, RenameTableStatement):
        return False
    return self.old_table_ref == other.old_table_ref and self.new_table_name == other.new_table_name

class CreateFunctionStatement(AbstractStatement):
    """CreateFunctionStatement constructed after parsing the input query

    Attributes:
        name: str
            function_name provided by the user required
        if_not_exists: bool
            if true should throw an error if function with same name exists
            else will replace the existing
        inputs: List[ColumnDefinition]
            function inputs, represented similar to a table column definition
        outputs: List[ColumnDefinition]
            function outputs, represented similar to a table column definition
        impl_file_path: str
            file path which holds the implementation of the function.
            This file should be placed in the function directory and
            the path provided should be relative to the function dir.
        query: SelectStatement
            data source for the model train or fine tune.
        function_type: str
            function type. it can be object detection, classification etc.
        metadata: List[Tuple[str, str]]
            metadata, list of key value pairs used for storing metadata of functions, mostly used for advanced function types
    """

    def __init__(self, name: str, or_replace: bool, if_not_exists: bool, impl_path: str, inputs: List[ColumnDefinition]=[], outputs: List[ColumnDefinition]=[], function_type: str=None, query: SelectStatement=None, metadata: List[Tuple[str, str]]=None):
        super().__init__(StatementType.CREATE_FUNCTION)
        self._name = name
        self._or_replace = or_replace
        self._if_not_exists = if_not_exists
        self._inputs = inputs
        self._outputs = outputs
        self._impl_path = Path(impl_path) if impl_path else None
        self._function_type = function_type
        self._query = query
        self._metadata = metadata

    def __str__(self) -> str:
        s = 'CREATE'
        if self._or_replace:
            s += ' OR REPLACE'
        s += ' ' + 'FUNCTION'
        if self._if_not_exists:
            s += ' IF NOT EXISTS'
        s += ' ' + self._name
        if self._query is not None:
            s += f' FROM ({self._query})'
        if self._function_type is not None:
            s += ' TYPE ' + str(self._function_type)
        if self._impl_path:
            s += f' IMPL {self._impl_path.name}'
        if self._metadata is not None:
            for key, value in self._metadata:
                s += f" {key.upper()} '{value}'"
        return s

    @property
    def name(self):
        return self._name

    @property
    def or_replace(self):
        return self._or_replace

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, value):
        self._inputs = value

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, value):
        self._outputs = value

    @property
    def impl_path(self):
        return self._impl_path

    @property
    def function_type(self):
        return self._function_type

    @property
    def query(self):
        return self._query

    @property
    def metadata(self):
        return self._metadata

    def __eq__(self, other):
        if not isinstance(other, CreateFunctionStatement):
            return False
        return self.name == other.name and self.or_replace == other.or_replace and (self.if_not_exists == other.if_not_exists) and (self.inputs == other.inputs) and (self.outputs == other.outputs) and (self.impl_path == other.impl_path) and (self.function_type == other.function_type) and (self.query == other.query) and (self.metadata == other.metadata)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.name, self.or_replace, self.if_not_exists, tuple(self.inputs), tuple(self.outputs), self.impl_path, self.function_type, self.query, tuple(self.metadata)))

def __str__(self) -> str:
    s = 'CREATE'
    if self._or_replace:
        s += ' OR REPLACE'
    s += ' ' + 'FUNCTION'
    if self._if_not_exists:
        s += ' IF NOT EXISTS'
    s += ' ' + self._name
    if self._query is not None:
        s += f' FROM ({self._query})'
    if self._function_type is not None:
        s += ' TYPE ' + str(self._function_type)
    if self._impl_path:
        s += f' IMPL {self._impl_path.name}'
    if self._metadata is not None:
        for key, value in self._metadata:
            s += f" {key.upper()} '{value}'"
    return s

def __eq__(self, other):
    if not isinstance(other, CreateFunctionStatement):
        return False
    return self.name == other.name and self.or_replace == other.or_replace and (self.if_not_exists == other.if_not_exists) and (self.inputs == other.inputs) and (self.outputs == other.outputs) and (self.impl_path == other.impl_path) and (self.function_type == other.function_type) and (self.query == other.query) and (self.metadata == other.metadata)

class ExplainStatement(AbstractStatement):

    def __init__(self, explainable_stmt: AbstractStatement):
        super().__init__(StatementType.EXPLAIN)
        self._explainable_stmt = explainable_stmt

    def __str__(self) -> str:
        print_str = 'EXPLAIN {}'.format(str(self._explainable_stmt))
        return print_str

    @property
    def explainable_stmt(self) -> AbstractStatement:
        return self._explainable_stmt

    def __eq__(self, other):
        if not isinstance(other, ExplainStatement):
            return False
        return self._explainable_stmt == other.explainable_stmt

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.explainable_stmt))

def __eq__(self, other):
    if not isinstance(other, ExplainStatement):
        return False
    return self._explainable_stmt == other.explainable_stmt

class UseStatement(AbstractStatement):

    def __init__(self, database_name: str, query_string: str):
        super().__init__(StatementType.USE)
        self._database_name = database_name
        self._query_string = query_string

    @property
    def database_name(self):
        return self._database_name

    @property
    def query_string(self):
        return self._query_string

    def __str__(self):
        return f'USE {self.database_name} ({self.query_string})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UseStatement):
            return False
        return self.database_name == other.database_name and self.query_string == other.query_string

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.database_name, self.query_string))

def __eq__(self, other: object) -> bool:
    if not isinstance(other, UseStatement):
        return False
    return self.database_name == other.database_name and self.query_string == other.query_string

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

class ShowStatement(AbstractStatement):

    def __init__(self, show_type: ShowType, show_val: Optional[str]=''):
        super().__init__(StatementType.SHOW)
        self._show_type = show_type
        self._show_val = show_val.upper()

    @property
    def show_type(self):
        return self._show_type

    @property
    def show_val(self):
        return self._show_val

    def __str__(self):
        show_str = ''
        if self.show_type == ShowType.FUNCTIONS:
            show_str = 'FUNCTIONS'
        elif self.show_type == ShowType.TABLES:
            show_str = 'TABLES'
        elif self.show_type == ShowType.CONFIGS:
            show_str = self.show_val
        elif self.show_type == ShowType.DATABASES:
            show_str = 'DATABASES'
        return f'SHOW {show_str}'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ShowStatement):
            return False
        return self.show_type == other.show_type and self.show_val == other.show_val

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.show_type, self.show_val))

def __eq__(self, other: object) -> bool:
    if not isinstance(other, ShowStatement):
        return False
    return self.show_type == other.show_type and self.show_val == other.show_val

class DropObjectStatement(AbstractStatement):
    """Drop Object Statement constructed after parsing the input query

    Attributes:
        object_type: ObjectType
        name (str
            name of the object to drop
        if_exists: bool
            if false, throws an error when no function with name exists
            else logs a warning
    """

    def __init__(self, object_type: ObjectType, name: str, if_exists: bool):
        super().__init__(StatementType.DROP_OBJECT)
        self._object_type = object_type
        self._name = name
        self._if_exists = if_exists

    def __str__(self) -> str:
        if self._if_exists:
            print_str = f'DROP {self._object_type} IF EXISTS {self._name};'
        else:
            print_str = f'DROP {self._object_type} {self._name};'
        return print_str

    @property
    def object_type(self):
        return self._object_type

    @property
    def name(self):
        return self._name

    @property
    def if_exists(self):
        return self._if_exists

    def __eq__(self, other):
        if not isinstance(other, DropObjectStatement):
            return False
        return self.object_type == other.object_type and self.name == other.name and (self.if_exists == other.if_exists)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.object_type, self.name, self.if_exists))

def __eq__(self, other):
    if not isinstance(other, DropObjectStatement):
        return False
    return self.object_type == other.object_type and self.name == other.name and (self.if_exists == other.if_exists)

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

class Load:

    def load_statement(self, tree):
        file_format = FileFormatType.VIDEO
        file_format = self.visit(tree.children[1])
        file_options = {}
        file_options['file_format'] = file_format
        file_path = self.visit(tree.children[2]).value
        table = self.visit(tree.children[4])
        column_list = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid_list':
                    column_list = self.visit(child)
        stmt = LoadDataStatement(table, file_path, column_list, file_options)
        return stmt

    def file_format(self, tree):
        file_format = None
        file_format_string = tree.children[0]
        if file_format_string == 'VIDEO':
            file_format = FileFormatType.VIDEO
        elif file_format_string == 'CSV':
            file_format = FileFormatType.CSV
        elif file_format_string == 'IMAGE':
            file_format = FileFormatType.IMAGE
        elif file_format_string == 'DOCUMENT':
            file_format = FileFormatType.DOCUMENT
        elif file_format_string == 'PDF':
            file_format = FileFormatType.PDF
        return file_format

    def file_options(self, tree):
        file_options = {}
        file_format = self.visit(tree.children[1])
        file_options['file_format'] = file_format
        return file_options

def load_statement(self, tree):
    file_format = FileFormatType.VIDEO
    file_format = self.visit(tree.children[1])
    file_options = {}
    file_options['file_format'] = file_format
    file_path = self.visit(tree.children[2]).value
    table = self.visit(tree.children[4])
    column_list = None
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'uid_list':
                column_list = self.visit(child)
    stmt = LoadDataStatement(table, file_path, column_list, file_options)
    return stmt

def file_options(self, tree):
    file_options = {}
    file_format = self.visit(tree.children[1])
    file_options['file_format'] = file_format
    return file_options

class LarkBaseInterpreter(visitors.Interpreter):

    def visit_children(self, tree: Tree[_Leaf_T]) -> List:
        output = [self._visit_tree(child) if isinstance(child, Tree) else child for child in tree.children]
        if len(output) == 1:
            output = output[0]
        return output

def visit_children(self, tree: Tree[_Leaf_T]) -> List:
    output = [self._visit_tree(child) if isinstance(child, Tree) else child for child in tree.children]
    if len(output) == 1:
        output = output[0]
    return output

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

def start(self, tree):
    return self.visit_children(tree)

def sql_statement(self, tree):
    return self.visit(tree.children[0])

class DropObject:

    def drop_table(self, tree):
        table_name = None
        if_exists = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_exists':
                    if_exists = True
                elif child.data == 'uid':
                    table_name = self.visit(child)
        return DropObjectStatement(ObjectType.TABLE, table_name, if_exists)

    def drop_index(self, tree):
        index_name = None
        if_exists = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_exists':
                    if_exists = True
                elif child.data == 'uid':
                    index_name = self.visit(child)
        return DropObjectStatement(ObjectType.INDEX, index_name, if_exists)

    def drop_function(self, tree):
        function_name = None
        if_exists = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid':
                    function_name = self.visit(child)
                elif child.data == 'if_exists':
                    if_exists = True
        return DropObjectStatement(ObjectType.FUNCTION, function_name, if_exists)

    def drop_database(self, tree):
        database_name = None
        if_exists = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_exists':
                    if_exists = True
                elif child.data == 'uid':
                    database_name = self.visit(child)
        return DropObjectStatement(ObjectType.DATABASE, database_name, if_exists)

    def drop_job(self, tree):
        job_name = None
        if_exists = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_exists':
                    if_exists = True
                elif child.data == 'uid':
                    job_name = self.visit(child)
        return DropObjectStatement(ObjectType.JOB, job_name, if_exists)

def drop_table(self, tree):
    table_name = None
    if_exists = False
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'if_exists':
                if_exists = True
            elif child.data == 'uid':
                table_name = self.visit(child)
    return DropObjectStatement(ObjectType.TABLE, table_name, if_exists)

def drop_index(self, tree):
    index_name = None
    if_exists = False
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'if_exists':
                if_exists = True
            elif child.data == 'uid':
                index_name = self.visit(child)
    return DropObjectStatement(ObjectType.INDEX, index_name, if_exists)

def drop_function(self, tree):
    function_name = None
    if_exists = False
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'uid':
                function_name = self.visit(child)
            elif child.data == 'if_exists':
                if_exists = True
    return DropObjectStatement(ObjectType.FUNCTION, function_name, if_exists)

def drop_database(self, tree):
    database_name = None
    if_exists = False
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'if_exists':
                if_exists = True
            elif child.data == 'uid':
                database_name = self.visit(child)
    return DropObjectStatement(ObjectType.DATABASE, database_name, if_exists)

def drop_job(self, tree):
    job_name = None
    if_exists = False
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'if_exists':
                if_exists = True
            elif child.data == 'uid':
                job_name = self.visit(child)
    return DropObjectStatement(ObjectType.JOB, job_name, if_exists)

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

class CreateIndex:

    def create_index(self, tree):
        index_name = None
        if_not_exists = False
        table_name = None
        vector_store_type = None
        index_elem = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid':
                    index_name = self.visit(child)
                if child.data == 'if_not_exists':
                    if_not_exists = True
                elif child.data == 'table_name':
                    table_name = self.visit(child)
                    table_ref = TableRef(table_name)
                elif child.data == 'vector_store_type':
                    vector_store_type = self.visit(child)
                elif child.data == 'index_elem':
                    index_elem = self.visit(child)
        project_expr_list = []
        if not isinstance(index_elem, list):
            project_expr_list += [index_elem]
            while not isinstance(index_elem, TupleValueExpression):
                index_elem = index_elem.children[0]
            index_elem = [index_elem]
        else:
            project_expr_list += index_elem
        col_list = []
        for tv_expr in index_elem:
            col_list += [ColumnDefinition(tv_expr.name, None, None, None)]
        return CreateIndexStatement(index_name, if_not_exists, table_ref, col_list, vector_store_type, project_expr_list)

    def vector_store_type(self, tree):
        vector_store_type = None
        token = tree.children[1]
        if str.upper(token) == 'FAISS':
            vector_store_type = VectorStoreType.FAISS
        elif str.upper(token) == 'QDRANT':
            vector_store_type = VectorStoreType.QDRANT
        elif str.upper(token) == 'PINECONE':
            vector_store_type = VectorStoreType.PINECONE
        elif str.upper(token) == 'PGVECTOR':
            vector_store_type = VectorStoreType.PGVECTOR
        elif str.upper(token) == 'CHROMADB':
            vector_store_type = VectorStoreType.CHROMADB
        elif str.upper(token) == 'WEAVIATE':
            vector_store_type = VectorStoreType.WEAVIATE
        elif str.upper(token) == 'MILVUS':
            vector_store_type = VectorStoreType.MILVUS
        return vector_store_type

def create_index(self, tree):
    index_name = None
    if_not_exists = False
    table_name = None
    vector_store_type = None
    index_elem = None
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'uid':
                index_name = self.visit(child)
            if child.data == 'if_not_exists':
                if_not_exists = True
            elif child.data == 'table_name':
                table_name = self.visit(child)
                table_ref = TableRef(table_name)
            elif child.data == 'vector_store_type':
                vector_store_type = self.visit(child)
            elif child.data == 'index_elem':
                index_elem = self.visit(child)
    project_expr_list = []
    if not isinstance(index_elem, list):
        project_expr_list += [index_elem]
        while not isinstance(index_elem, TupleValueExpression):
            index_elem = index_elem.children[0]
        index_elem = [index_elem]
    else:
        project_expr_list += index_elem
    col_list = []
    for tv_expr in index_elem:
        col_list += [ColumnDefinition(tv_expr.name, None, None, None)]
    return CreateIndexStatement(index_name, if_not_exists, table_ref, col_list, vector_store_type, project_expr_list)

def vector_store_type(self, tree):
    vector_store_type = None
    token = tree.children[1]
    if str.upper(token) == 'FAISS':
        vector_store_type = VectorStoreType.FAISS
    elif str.upper(token) == 'QDRANT':
        vector_store_type = VectorStoreType.QDRANT
    elif str.upper(token) == 'PINECONE':
        vector_store_type = VectorStoreType.PINECONE
    elif str.upper(token) == 'PGVECTOR':
        vector_store_type = VectorStoreType.PGVECTOR
    elif str.upper(token) == 'CHROMADB':
        vector_store_type = VectorStoreType.CHROMADB
    elif str.upper(token) == 'WEAVIATE':
        vector_store_type = VectorStoreType.WEAVIATE
    elif str.upper(token) == 'MILVUS':
        vector_store_type = VectorStoreType.MILVUS
    return vector_store_type

class CreateDatabase:

    def create_database(self, tree):
        database_name = None
        if_not_exists = False
        engine = None
        param_dict = {}
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_not_exists':
                    if_not_exists = True
                elif child.data == 'uid':
                    database_name = self.visit(child)
                elif child.data == 'create_database_engine_clause':
                    engine, param_dict = self.visit(child)
        create_stmt = CreateDatabaseStatement(database_name, if_not_exists, engine, param_dict)
        return create_stmt

    def create_database_engine_clause(self, tree):
        engine = None
        param_dict = {}
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'string_literal':
                    engine = self.visit(child).value
                elif child.data == 'colon_param_dict':
                    param_dict = self.visit(child)
        return (engine, param_dict)

def create_database(self, tree):
    database_name = None
    if_not_exists = False
    engine = None
    param_dict = {}
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'if_not_exists':
                if_not_exists = True
            elif child.data == 'uid':
                database_name = self.visit(child)
            elif child.data == 'create_database_engine_clause':
                engine, param_dict = self.visit(child)
    create_stmt = CreateDatabaseStatement(database_name, if_not_exists, engine, param_dict)
    return create_stmt

def create_database_engine_clause(self, tree):
    engine = None
    param_dict = {}
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'string_literal':
                engine = self.visit(child).value
            elif child.data == 'colon_param_dict':
                param_dict = self.visit(child)
    return (engine, param_dict)

class CreateJob:

    def create_job(self, tree):
        job_name = None
        queries = []
        start_time = None
        end_time = None
        repeat_interval = None
        repeat_period = None
        if_not_exists = False
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'if_not_exists':
                    if_not_exists = True
                if child.data == 'uid':
                    job_name = self.visit(child)
                if child.data == 'job_sql_statements':
                    queries = self.visit(child)
                elif child.data == 'start_time':
                    start_time = self.visit(child)
                elif child.data == 'end_time':
                    end_time = self.visit(child)
                elif child.data == 'repeat_clause':
                    repeat_interval, repeat_period = self.visit(child)
        create_job = CreateJobStatement(job_name, queries, if_not_exists, start_time, end_time, repeat_interval, repeat_period)
        return create_job

    def start_time(self, tree):
        return self.visit(tree.children[1]).value

    def end_time(self, tree):
        return self.visit(tree.children[1]).value

    def repeat_clause(self, tree):
        return (self.visit(tree.children[1]), self.visit(tree.children[2]))

def create_job(self, tree):
    job_name = None
    queries = []
    start_time = None
    end_time = None
    repeat_interval = None
    repeat_period = None
    if_not_exists = False
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'if_not_exists':
                if_not_exists = True
            if child.data == 'uid':
                job_name = self.visit(child)
            if child.data == 'job_sql_statements':
                queries = self.visit(child)
            elif child.data == 'start_time':
                start_time = self.visit(child)
            elif child.data == 'end_time':
                end_time = self.visit(child)
            elif child.data == 'repeat_clause':
                repeat_interval, repeat_period = self.visit(child)
    create_job = CreateJobStatement(job_name, queries, if_not_exists, start_time, end_time, repeat_interval, repeat_period)
    return create_job

def start_time(self, tree):
    return self.visit(tree.children[1]).value

def end_time(self, tree):
    return self.visit(tree.children[1]).value

def repeat_clause(self, tree):
    return (self.visit(tree.children[1]), self.visit(tree.children[2]))

class RenameTable:

    def rename_table(self, tree):
        old_table_info = self.visit(tree.children[2])
        new_table_info = self.visit(tree.children[4])
        return RenameTableStatement(TableRef(old_table_info), new_table_info)

def rename_table(self, tree):
    old_table_info = self.visit(tree.children[2])
    new_table_info = self.visit(tree.children[4])
    return RenameTableStatement(TableRef(old_table_info), new_table_info)

class Select:

    def simple_select(self, tree):
        select_stmt = self.visit_children(tree)
        return select_stmt

    def order_by_clause(self, tree):
        orderby_clause_data = []
        for child in tree.children:
            if isinstance(child, Tree):
                orderby_clause_data.append(self.visit(child))
        return orderby_clause_data

    def order_by_expression(self, tree):
        expr = None
        sort_order = ParserOrderBySortType.ASC
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('expression'):
                    expr = self.visit(child)
                elif child.data == 'sort_order':
                    sort_order = self.visit(child)
        return (expr, sort_order)

    def sort_order(self, tree):
        token = tree.children[0]
        sort_order = None
        if str.upper(token) == 'ASC':
            sort_order = ParserOrderBySortType.ASC
        elif str.upper(token) == 'DESC':
            sort_order = ParserOrderBySortType.DESC
        return sort_order

    def limit_clause(self, tree):
        output = ConstantValueExpression(self.visit(tree.children[1]))
        return output

def simple_select(self, tree):
    select_stmt = self.visit_children(tree)
    return select_stmt

def order_by_clause(self, tree):
    orderby_clause_data = []
    for child in tree.children:
        if isinstance(child, Tree):
            orderby_clause_data.append(self.visit(child))
    return orderby_clause_data

def order_by_expression(self, tree):
    expr = None
    sort_order = ParserOrderBySortType.ASC
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data.endswith('expression'):
                expr = self.visit(child)
            elif child.data == 'sort_order':
                sort_order = self.visit(child)
    return (expr, sort_order)

def sort_order(self, tree):
    token = tree.children[0]
    sort_order = None
    if str.upper(token) == 'ASC':
        sort_order = ParserOrderBySortType.ASC
    elif str.upper(token) == 'DESC':
        sort_order = ParserOrderBySortType.DESC
    return sort_order

def limit_clause(self, tree):
    output = ConstantValueExpression(self.visit(tree.children[1]))
    return output

class Set:

    def set_statement(self, tree):
        config_name = None
        config_value = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'config_name':
                    config_name = self.visit(child)
                elif child.data == 'config_value':
                    config_value = self.visit(child)
        set_stmt = SetStatement(config_name, config_value)
        return set_stmt

def set_statement(self, tree):
    config_name = None
    config_value = None
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'config_name':
                config_name = self.visit(child)
            elif child.data == 'config_value':
                config_value = self.visit(child)
    set_stmt = SetStatement(config_name, config_value)
    return set_stmt

class Delete:

    def delete_statement(self, tree):
        table_ref = None
        where_clause = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_name':
                    table_name = self.visit(child)
                    table_ref = TableRef(table_name)
                elif child.data == 'where_expr':
                    where_clause = self.visit(child)
        delete_stmt = DeleteTableStatement(table_ref, where_clause)
        return delete_stmt

def delete_statement(self, tree):
    table_ref = None
    where_clause = None
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'table_name':
                table_name = self.visit(child)
                table_ref = TableRef(table_name)
            elif child.data == 'where_expr':
                where_clause = self.visit(child)
    delete_stmt = DeleteTableStatement(table_ref, where_clause)
    return delete_stmt

class Insert:

    def insert_statement(self, tree):
        table_ref = None
        column_list = []
        value_list = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'table_name':
                    table_name = self.visit(child)
                    table_ref = TableRef(table_name)
                elif child.data == 'uid_list':
                    column_list = self.visit(child)
                elif child.data == 'insert_statement_value':
                    value_list = self.visit(child)
        insert_stmt = InsertTableStatement(table_ref, column_list, value_list)
        return insert_stmt

    def uid_list(self, tree):
        uid_expr_list = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'uid':
                    uid = self.visit(child)
                    uid_expr = TupleValueExpression(uid)
                    uid_expr_list.append(uid_expr)
        return uid_expr_list

    def insert_statement_value(self, tree):
        insert_stmt_value = []
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'expressions_with_defaults':
                    expr = self.visit(child)
                    insert_stmt_value.append(expr)
        return insert_stmt_value

def insert_statement(self, tree):
    table_ref = None
    column_list = []
    value_list = []
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'table_name':
                table_name = self.visit(child)
                table_ref = TableRef(table_name)
            elif child.data == 'uid_list':
                column_list = self.visit(child)
            elif child.data == 'insert_statement_value':
                value_list = self.visit(child)
    insert_stmt = InsertTableStatement(table_ref, column_list, value_list)
    return insert_stmt

def uid_list(self, tree):
    uid_expr_list = []
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'uid':
                uid = self.visit(child)
                uid_expr = TupleValueExpression(uid)
                uid_expr_list.append(uid_expr)
    return uid_expr_list

def insert_statement_value(self, tree):
    insert_stmt_value = []
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'expressions_with_defaults':
                expr = self.visit(child)
                insert_stmt_value.append(expr)
    return insert_stmt_value

class CommonClauses:

    def table_name(self, tree):
        child = self.visit(tree.children[0])
        if isinstance(child, tuple):
            database_name, table_name = (child[0], child[1])
        else:
            database_name, table_name = (None, child)
        if table_name is not None:
            return TableInfo(table_name=table_name, database_name=database_name)
        else:
            error = 'Invalid Table Name'
            logger.error(error)

    def full_id(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        elif len(tree.children) == 2:
            return (self.visit(tree.children[0]), self.visit(tree.children[1]))

    def uid(self, tree):
        if hasattr(tree.children[0], 'type') and tree.children[0].type == 'REVERSE_QUOTE_ID':
            tree.children[0].type = 'simple_id'
            non_tick_string = str(tree.children[0]).replace('`', '')
            return non_tick_string
        return self.visit(tree.children[0])

    def full_column_name(self, tree):
        uid = self.visit(tree.children[0])
        if len(tree.children) > 1:
            dotted_id = self.visit(tree.children[1])
            return TupleValueExpression(table_alias=uid, name=dotted_id)
        else:
            return TupleValueExpression(name=uid)

    def dotted_id(self, tree):
        dotted_id = str(tree.children[0])
        dotted_id = dotted_id.lstrip('.')
        return dotted_id

    def simple_id(self, tree):
        simple_id = str(tree.children[0])
        return simple_id

    def decimal_literal(self, tree):
        decimal = None
        token = tree.children[0]
        if str.upper(token) == 'ANYDIM':
            decimal = Dimension.ANYDIM
        else:
            decimal = int(str(token))
        return decimal

    def real_literal(self, tree):
        real_literal = float(tree.children[0])
        return real_literal

def table_name(self, tree):
    child = self.visit(tree.children[0])
    if isinstance(child, tuple):
        database_name, table_name = (child[0], child[1])
    else:
        database_name, table_name = (None, child)
    if table_name is not None:
        return TableInfo(table_name=table_name, database_name=database_name)
    else:
        error = 'Invalid Table Name'
        logger.error(error)

def full_id(self, tree):
    if len(tree.children) == 1:
        return self.visit(tree.children[0])
    elif len(tree.children) == 2:
        return (self.visit(tree.children[0]), self.visit(tree.children[1]))

def full_column_name(self, tree):
    uid = self.visit(tree.children[0])
    if len(tree.children) > 1:
        dotted_id = self.visit(tree.children[1])
        return TupleValueExpression(table_alias=uid, name=dotted_id)
    else:
        return TupleValueExpression(name=uid)

def decimal_literal(self, tree):
    decimal = None
    token = tree.children[0]
    if str.upper(token) == 'ANYDIM':
        decimal = Dimension.ANYDIM
    else:
        decimal = int(str(token))
    return decimal

class Use:

    def use_statement(self, tree):
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == 'database_name':
                    database_name = self.visit(child)
                if child.data == 'query_string':
                    query_string = self.visit(child)
        return UseStatement(database_name, query_string)

def use_statement(self, tree):
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data == 'database_name':
                database_name = self.visit(child)
            if child.data == 'query_string':
                query_string = self.visit(child)
    return UseStatement(database_name, query_string)

class Show:

    def show_statement(self, tree):
        token = tree.children[1]
        if isinstance(token, str) and str.upper(token) == 'FUNCTIONS':
            return ShowStatement(show_type=ShowType.FUNCTIONS)
        elif isinstance(token, str) and str.upper(token) == 'TABLES':
            return ShowStatement(show_type=ShowType.TABLES)
        elif isinstance(token, str) and str.upper(token) == 'DATABASES':
            return ShowStatement(show_type=ShowType.DATABASES)
        elif token is not None:
            return ShowStatement(show_type=ShowType.CONFIGS, show_val=self.visit(token))

def show_statement(self, tree):
    token = tree.children[1]
    if isinstance(token, str) and str.upper(token) == 'FUNCTIONS':
        return ShowStatement(show_type=ShowType.FUNCTIONS)
    elif isinstance(token, str) and str.upper(token) == 'TABLES':
        return ShowStatement(show_type=ShowType.TABLES)
    elif isinstance(token, str) and str.upper(token) == 'DATABASES':
        return ShowStatement(show_type=ShowType.DATABASES)
    elif token is not None:
        return ShowStatement(show_type=ShowType.CONFIGS, show_val=self.visit(token))

class Explain:

    def explain_statement(self, tree):
        explainable_stmt = None
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data.endswith('explainable_statement'):
                    explainable_stmt = self.visit(child)
        return ExplainStatement(explainable_stmt)

def explain_statement(self, tree):
    explainable_stmt = None
    for child in tree.children:
        if isinstance(child, Tree):
            if child.data.endswith('explainable_statement'):
                explainable_stmt = self.visit(child)
    return ExplainStatement(explainable_stmt)

def infer_output_name_and_type(**pipeline_args):
    """
    Infer the name and type for each output of the HuggingFace Function
    """
    assert 'task' in pipeline_args, 'Task Not Found In Model Definition'
    task = pipeline_args['task']
    assert task in INPUT_TYPE_FOR_SUPPORTED_TASKS, f'Task {task} not supported in EvaDB currently'
    try_to_import_transformers()
    from transformers import pipeline
    pipe = pipeline(**pipeline_args)
    input_type = INPUT_TYPE_FOR_SUPPORTED_TASKS[task]
    model_input = gen_sample_input(input_type)
    model_output = pipe(model_input)
    output_types = {}
    if isinstance(model_output, list):
        sample_out = model_output[0]
    else:
        sample_out = model_output
    for key, value in sample_out.items():
        output_types[key] = type(value)
    return (input_type, output_types)

def assign_hf_function(function_obj: FunctionCatalogEntry):
    """
    Assigns the correct HF Model to the Function. The model assigned depends on
    the task type for the Function. This is done so that we can
    process the input correctly before passing it to the HF model.
    """
    inputs = function_obj.args
    assert len(inputs) == 1, 'Only single input models are supported.'
    task = get_metadata_entry_or_val(function_obj, 'task', None)
    assert task is not None, 'task not specified in Hugging Face Function'
    model_class = MODEL_FOR_TASK[task]
    return lambda: model_class(function_obj)

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

def _convert_json_response_to_DataFrame(self, json_response):
    messages = json_response['messages']
    columns = ['text', 'ts', 'user']
    data_df = pd.DataFrame(columns=columns)
    for message in messages:
        if message['text'] and message['ts'] and message['user']:
            data_df.loc[len(data_df.index)] = [message['text'], message['ts'], message['user']]
    return data_df

class PytorchAbstractTransformationFunction(AbstractTransformationFunction, Compose):
    """
    Use PyTorch torchvision transforms as EvaDB transforms.
    """

    def __init__(self, transforms):
        Compose.__init__(self, transforms)

    def transform(self, frames: ArrayLike) -> ArrayLike:
        return Compose.__call__(self, frames)

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            return nn.Module.__call__(self, *args, **kwargs)
        frames = args[0]
        if isinstance(frames, pd.DataFrame):
            frames = frames.transpose().values.tolist()[0]
        return Compose.__call__(self, frames, **kwargs)

def transform(self, frames: ArrayLike) -> ArrayLike:
    return Compose.__call__(self, frames)

def __call__(self, *args, **kwargs):
    if len(args) == 0:
        return nn.Module.__call__(self, *args, **kwargs)
    frames = args[0]
    if isinstance(frames, pd.DataFrame):
        frames = frames.transpose().values.tolist()[0]
    return Compose.__call__(self, frames, **kwargs)

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

def to_device(self, device: str) -> GPUCompatible:
    try_to_import_transformers()
    from transformers import pipeline
    self.hf_function_obj = pipeline(**self.pipeline_args, device=device)
    return self

class Upper(AbstractFunction):

    def setup(self):
        pass

    @property
    def name(self):
        return 'UPPER'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the string to Uppercase.

        Returns:
            ret (pd.DataFrame): String converted to Upper Case.
        """
        ret = pd.DataFrame()
        ret['output'] = df.map(lambda s: s.upper() if type(s) is str else s)
        return ret

def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    """
        Converts the string to Uppercase.

        Returns:
            ret (pd.DataFrame): String converted to Upper Case.
        """
    ret = pd.DataFrame()
    ret['output'] = df.map(lambda s: s.upper() if type(s) is str else s)
    return ret

class Lower(AbstractFunction):

    def setup(self):
        pass

    @property
    def name(self):
        return 'LOWER'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the string to Lower Case.

        Returns:
            ret (pd.DataFrame): String converted to Lower Case.
        """
        ret = pd.DataFrame()
        ret['output'] = df.map(lambda s: s.lower() if type(s) is str else s)
        return ret

def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    """
        Converts the string to Lower Case.

        Returns:
            ret (pd.DataFrame): String converted to Lower Case.
        """
    ret = pd.DataFrame()
    ret['output'] = df.map(lambda s: s.lower() if type(s) is str else s)
    return ret

class EvaDBCursor(object):

    def __init__(self, connection):
        self._connection = connection
        self._evadb = connection._evadb
        self._pending_query = False
        self._result = None

    async def execute_async(self, query: str):
        """
        Send query to the EvaDB server.
        """
        if self._pending_query:
            raise SystemError('EvaDB does not support concurrent queries.                     Call fetch_all() to complete the pending query')
        query = self._multiline_query_transformation(query)
        self._connection._writer.write((query + '\n').encode())
        await self._connection._writer.drain()
        self._pending_query = True
        return self

    async def fetch_one_async(self) -> Response:
        """
        fetch_one returns one batch instead of one row for now.
        """
        response = Response()
        prefix = await self._connection._reader.readline()
        if prefix != b'':
            message_length = int(prefix)
            message = await self._connection._reader.readexactly(message_length)
            response = Response.deserialize(message)
        self._pending_query = False
        return response

    async def fetch_all_async(self) -> Response:
        """
        fetch_all is the same as fetch_one for now.
        """
        return await self.fetch_one_async()

    def _multiline_query_transformation(self, query: str) -> str:
        query = query.replace('\n', ' ')
        query = query.lstrip()
        query = query.rstrip(' ;')
        query += ';'
        logger.debug('Query: ' + query)
        return query

    def stop_query(self):
        self._pending_query = False

    def __getattr__(self, name):
        """
        Auto generate sync function calls from async
        Sync function calls should not be used in an async environment.
        """
        function_name_list = ['table', 'load', 'execute', 'query', 'create_function', 'create_table', 'create_vector_index', 'drop_table', 'drop_function', 'drop_index', 'df', 'show', 'insertexplain', 'rename', 'fetch_one']
        if name not in function_name_list:
            nearest_function = find_nearest_word(name, function_name_list)
            raise AttributeError(f"EvaDBCursor does not contain a function named: '{name}'. Did you mean to run: '{nearest_function}()'?")
        try:
            func = object.__getattribute__(self, '%s_async' % name)
        except Exception as e:
            raise e

        def func_sync(*args, **kwargs):
            loop = asyncio.get_event_loop()
            res = loop.run_until_complete(func(*args, **kwargs))
            return res
        return func_sync

    def table(self, table_name: str, chunk_size: int=None, chunk_overlap: int=None) -> EvaDBQuery:
        """
        Retrieves data from a table in the database.

        Args:
            table_name (str): The name of the table to retrieve data from.
            chunk_size (int, optional): The size of the chunk to break the document into. Only valid for DOCUMENT tables.
                If not provided, the default value is 4000.
            chunk_overlap (int, optional): The overlap between consecutive chunks. Only valid for DOCUMENT tables.
                If not provided, the default value is 200.

        Returns:
            EvaDBQuery: An EvaDBQuery object representing the table query.

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation = cursor.select('*')
            >>> relation.df()
               col1  col2
            0     1     2
            1     3     4
            2     5     6

            Read a document table using chunk_size 100 and chunk_overlap 10.

            >>> relation = cursor.table("doc_table", chunk_size=100, chunk_overlap=10)
        """
        table = parse_table_clause(table_name, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        select_stmt = SelectStatement(target_list=[TupleValueExpression(name='*')], from_table=table)
        try_binding(self._evadb.catalog, select_stmt)
        return EvaDBQuery(self._evadb, select_stmt, alias=Alias(table_name.lower()))

    def df(self) -> pandas.DataFrame:
        """
        Returns the result as a pandas DataFrame.

        Returns:
            pandas.DataFrame: The result as a DataFrame.

        Raises:
            Exception: If no valid result is available with the current connection.

        Examples:
            >>> result = cursor.query("CREATE TABLE IF NOT EXISTS youtube_video_text AS SELECT SpeechRecognizer(audio) FROM youtube_video;").df()
            >>> result
            Empty DataFrame
            >>> relation = cursor.table("youtube_video_text").select('*').df()
                speechrecognizer.response
            0	"Sample Text from speech recognizer"
        """
        if not self._result:
            raise Exception('No valid result with the current cursor')
        return self._result.frames

    def create_vector_index(self, index_name: str, table_name: str, expr: str, using: str) -> 'EvaDBCursor':
        """
        Creates a vector index using the provided expr on the table.
        This feature directly works on IMAGE tables.
        For VIDEO tables, the feature should be extracted first and stored in an intermediate table, before creating the index.

        Args:
            index_name (str): Name of the index.
            table_name (str): Name of the table.
            expr (str): Expression used to build the vector index.

            using (str): Method used for indexing, can be `FAISS` or `QDRANT` or `PINECONE` or `CHROMADB` or `WEAVIATE` or `MILVUS`.

        Returns:
            EvaDBCursor: The EvaDBCursor object.

        Examples:
            Create a Vector Index using QDRANT

            >>> cursor.create_vector_index(
                    "faiss_index",
                    table_name="meme_images",
                    expr="SiftFeatureExtractor(data)",
                    using="QDRANT"
                ).df()
                        0
                0	Index faiss_index successfully added to the database
            >>> relation = cursor.table("PDFs")
            >>> relation.order("Similarity(ImageFeatureExtractor(Open('/images/my_meme')), ImageFeatureExtractor(data) ) DESC")
            >>> relation.df()


        """
        stmt = parse_create_vector_index(index_name, table_name, expr, using)
        self._result = execute_statement(self._evadb, stmt)
        return self

    def load(self, file_regex: str, table_name: str, format: str, **kwargs) -> EvaDBQuery:
        """
        Loads data from files into a table.

        Args:
            file_regex (str): Regular expression specifying the files to load.
            table_name (str): Name of the table.
            format (str): File format of the data.
            **kwargs: Additional keyword arguments for configuring the load operation.

        Returns:
            EvaDBQuery: The EvaDBQuery object representing the load query.

        Examples:
            Load the online_video.mp4 file into table named 'youtube_video'.

            >>> cursor.load(file_regex="online_video.mp4", table_name="youtube_video", format="video").df()
                    0
            0	Number of loaded VIDEO: 1

        """
        stmt = parse_load(table_name, file_regex, format, **kwargs)
        return EvaDBQuery(self._evadb, stmt)

    def drop_table(self, table_name: str, if_exists: bool=True) -> 'EvaDBQuery':
        """
        Drop a table in the database.

        Args:
            table_name (str): Name of the table to be dropped.
            if_exists (bool): If True, do not raise an error if the Table does not already exist. If False, raise an error.

        Returns:
            EvaDBQuery: The EvaDBQuery object representing the DROP TABLE.

        Examples:
            Drop table 'sample_table'

            >>> cursor.drop_table("sample_table", if_exists = True).df()
                0
            0	Table Successfully dropped: sample_table
        """
        stmt = parse_drop_table(table_name, if_exists)
        return EvaDBQuery(self._evadb, stmt)

    def drop_function(self, function_name: str, if_exists: bool=True) -> 'EvaDBQuery':
        """
        Drop a function in the database.

        Args:
            function_name (str): Name of the function to be dropped.
            if_exists (bool): If True, do not raise an error if the function does not already exist. If False, raise an error.

        Returns:
            EvaDBQuery: The EvaDBQuery object representing the DROP FUNCTION.

        Examples:
            Drop FUNCTION 'ObjectDetector'

            >>> cursor.drop_function("ObjectDetector", if_exists = True)
                0
            0	Function Successfully dropped: ObjectDetector
        """
        stmt = parse_drop_function(function_name, if_exists)
        return EvaDBQuery(self._evadb, stmt)

    def drop_index(self, index_name: str, if_exists: bool=True) -> 'EvaDBQuery':
        """
        Drop an index in the database.

        Args:
            index_name (str): Name of the index to be dropped.
            if_exists (bool): If True, do not raise an error if the index does not already exist. If False, raise an error.

        Returns:
            EvaDBQuery: The EvaDBQuery object representing the DROP INDEX.

        Examples:
            Drop the index with name 'faiss_index'

            >>> cursor.drop_index("faiss_index", if_exists = True)
        """
        stmt = parse_drop_index(index_name, if_exists)
        return EvaDBQuery(self._evadb, stmt)

    def create_function(self, function_name: str, if_not_exists: bool=True, impl_path: str=None, type: str=None, **kwargs) -> 'EvaDBQuery':
        """
        Create a function in the database.

        Args:
            function_name (str): Name of the function to be created.
            if_not_exists (bool): If True, do not raise an error if the function already exist. If False, raise an error.
            impl_path (str): Path string to function's implementation.
            type (str): Type of the function (e.g. HuggingFace).
            **kwargs: Additional keyword arguments for configuring the create function operation.

        Returns:
            EvaDBQuery: The EvaDBQuery object representing the function created.

        Examples:
            >>> cursor.create_function("MnistImageClassifier", if_exists = True, 'mnist_image_classifier.py')
                0
            0	Function Successfully created: MnistImageClassifier
        """
        stmt = parse_create_function(function_name, if_not_exists, impl_path, type, **kwargs)
        return EvaDBQuery(self._evadb, stmt)

    def create_table(self, table_name: str, if_not_exists: bool=True, columns: str=None, **kwargs) -> 'EvaDBQuery':
        '''
        Create a function in the database.

        Args:
            function_name (str): Name of the function to be created.
            if_not_exists (bool): If True, do not raise an error if the function already exist. If False, raise an error.
            impl_path (str): Path string to function's implementation.
            type (str): Type of the function (e.g. HuggingFace).
            **kwargs: Additional keyword arguments for configuring the create function operation.

        Returns:
            EvaDBQuery: The EvaDBQuery object representing the function created.

        Examples:
            >>> cursor.create_table("MyCSV", if_exists = True, columns="""
                    id INTEGER UNIQUE,
                    frame_id INTEGER,
                    video_id INTEGER,
                    dataset_name TEXT(30),
                    label TEXT(30),
                    bbox NDARRAY FLOAT32(4),
                    object_id INTEGER"""
                    )
                0
            0	Table Successfully created: MyCSV
        '''
        stmt = parse_create_table(table_name, if_not_exists, columns, **kwargs)
        return EvaDBQuery(self._evadb, stmt)

    def query(self, sql_query: str) -> EvaDBQuery:
        """
        Executes a SQL query.

        Args:
            sql_query (str): The SQL query to be executed

        Returns:
            EvaDBQuery: The EvaDBQuery object.

        Examples:
            >>> cursor.query("DROP FUNCTION IF EXISTS SentenceFeatureExtractor;")
            >>> cursor.query('SELECT * FROM sample_table;').df()
               col1  col2
            0     1     2
            1     3     4
            2     5     6
        """
        stmt = parse_query(sql_query)
        return EvaDBQuery(self._evadb, stmt)

    def show(self, object_type: str, **kwargs) -> EvaDBQuery:
        """
        Shows all entries of the current object_type.

        Args:
            show_type (str): The type of SHOW query to be executed
            **kwargs: Additional keyword arguments for configuring the SHOW operation.

        Returns:
            EvaDBQuery: The EvaDBQuery object.

        Examples:
            >>> cursor.show("tables").df()
                name
            0	SampleTable1
            1	SampleTable2
            2	SampleTable3
        """
        stmt = parse_show(object_type, **kwargs)
        return EvaDBQuery(self._evadb, stmt)

    def explain(self, sql_query: str) -> EvaDBQuery:
        """
        Executes an EXPLAIN query.

        Args:
            sql_query (str): The SQL query to be explained

        Returns:
            EvaDBQuery: The EvaDBQuery object.

        Examples:
            >>> proposed_plan = cursor.explain("SELECT * FROM sample_table;").df()
            >>> for step in proposed_plan[0]:
            >>>   pprint(step)
             |__ ProjectPlan
                |__ SeqScanPlan
                    |__ StoragePlan
        """
        stmt = parse_explain(sql_query)
        return EvaDBQuery(self._evadb, stmt)

    def insert(self, table_name, columns, values, **kwargs) -> EvaDBQuery:
        """
        Executes an INSERT query.

        Args:
            table_name (str): The name of the table to insert into
            columns (list): The list of columns to insert into
            values (list): The list of values to insert
            **kwargs: Additional keyword arguments for configuring the INSERT operation.

        Returns:
            EvaDBQuery: The EvaDBQuery object.

        Examples:
            >>> cursor.insert("sample_table", ["id", "name"], [1, "Alice"])
        """
        stmt = parse_insert(table_name, columns, values, **kwargs)
        return EvaDBQuery(self._evadb, stmt)

    def rename(self, table_name, new_table_name, **kwargs) -> EvaDBQuery:
        """
        Executes a RENAME query.

        Args:
            table_name (str): The name of the table to rename
            new_table_name (str): The new name of the table
            **kwargs: Additional keyword arguments for configuring the RENAME operation.

        Returns:
            EvaDBQuery: The EvaDBQuery object.

        Examples:
            >>> cursor.show("tables").df()
                name
            0	SampleVideoTable
            1	SampleTable
            2	MyCSV
            3	videotable
            >>> cursor.rename("videotable", "sample_table").df()
            _
            >>> cursor.show("tables").df()
                        name
            0	SampleVideoTable
            1	SampleTable
            2	MyCSV
            3	sample_table

        """
        stmt = parse_rename(table_name, new_table_name, **kwargs)
        return EvaDBQuery(self._evadb, stmt)

    def close(self):
        """
        Closes the connection.

        Args: None

        Returns:  None

        Examples:
            >>> cursor.close()
        """
        self._evadb.catalog().close()
        ray_enabled = self._evadb.config.get_value('experimental', 'ray')
        if is_ray_enabled_and_installed(ray_enabled):
            import ray
            ray.shutdown()

def table(self, table_name: str, chunk_size: int=None, chunk_overlap: int=None) -> EvaDBQuery:
    """
        Retrieves data from a table in the database.

        Args:
            table_name (str): The name of the table to retrieve data from.
            chunk_size (int, optional): The size of the chunk to break the document into. Only valid for DOCUMENT tables.
                If not provided, the default value is 4000.
            chunk_overlap (int, optional): The overlap between consecutive chunks. Only valid for DOCUMENT tables.
                If not provided, the default value is 200.

        Returns:
            EvaDBQuery: An EvaDBQuery object representing the table query.

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation = cursor.select('*')
            >>> relation.df()
               col1  col2
            0     1     2
            1     3     4
            2     5     6

            Read a document table using chunk_size 100 and chunk_overlap 10.

            >>> relation = cursor.table("doc_table", chunk_size=100, chunk_overlap=10)
        """
    table = parse_table_clause(table_name, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    select_stmt = SelectStatement(target_list=[TupleValueExpression(name='*')], from_table=table)
    try_binding(self._evadb.catalog, select_stmt)
    return EvaDBQuery(self._evadb, select_stmt, alias=Alias(table_name.lower()))

def handle_select_clause(query: SelectStatement, alias: str, clause: str, value: Union[str, int, list]) -> SelectStatement:
    """
    Modifies a SELECT statement object by adding or modifying a specific clause.

    Args:
        query (SelectStatement): The SELECT statement object.
        alias (str): Alias for the table reference.
        clause (str): The clause to be handled.
        value (str, int, list): The value to be set for the clause.

    Returns:
        SelectStatement: The modified SELECT statement object.

    Raises:
        AssertionError: If the query is not an instance of SelectStatement class.
        AssertionError: If the clause is not in the accepted clauses list.
    """
    assert isinstance(query, SelectStatement), 'query must be an instance of SelectStatement'
    accepted_clauses = ['where_clause', 'target_list', 'groupby_clause', 'orderby_list', 'limit_count']
    assert clause in accepted_clauses, f'Unknown clause: {clause}'
    if clause == 'target_list' and getattr(query, clause) == create_star_expression():
        setattr(query, clause, None)
    if getattr(query, clause) is None:
        setattr(query, clause, value)
    else:
        query = SelectStatement(target_list=create_star_expression(), from_table=TableRef(query, alias=alias))
        setattr(query, clause, value)
    return query

class EvaDBQuery:

    def __init__(self, evadb: EvaDBDatabase, query_node: Union[AbstractStatement, TableRef], alias: Alias=None):
        self._evadb = evadb
        self._query_node = query_node
        self._alias = alias

    def alias(self, alias: str) -> 'EvaDBQuery':
        """Returns a new Relation with an alias set.

        Args:
            alias (str): an alias name to be set for the Relation.

        Returns:
            EvaDBQuery: Aliased Relation.

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.alias('table')
        """
        self._alias = Alias(alias)

    def cross_apply(self, expr: str, alias: str) -> 'EvaDBQuery':
        """Execute a expr on all the rows of the relation

        Args:
            expr (str): sql expression
            alias (str): alias of the output of the expr

        Returns:
            `EvaDBQuery`: relation

        Examples:

            Runs Yolo on all the frames of the input table

            >>> relation = cursor.table("videos")
            >>> relation.cross_apply("Yolo(data)", "objs(labels, bboxes, scores)")

            Runs Yolo on all the frames of the input table and unnest each object as separate row.

            >>> relation.cross_apply("unnest(Yolo(data))", "obj(label, bbox, score)")
        """
        assert self._query_node.from_table is not None
        table_ref = string_to_lateral_join(expr, alias=alias)
        join_table = TableRef(JoinNode(TableRef(self._query_node, alias=self._alias), table_ref, join_type=JoinType.LATERAL_JOIN))
        self._query_node = SelectStatement(target_list=create_star_expression(), from_table=join_table)
        self._alias = Alias('Relation')
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def df(self, drop_alias: bool=True) -> pandas.DataFrame:
        """
        Execute and fetch all rows as a pandas DataFrame

        Args:
            drop_alias (bool): whether to drop the table name in the output dataframe. Default: True.

        Returns:
            pandas.DataFrame:

        Example:

        Runs a SQL query and get a panda Dataframe.
            >>> cursor.query("SELECT * FROM MyTable;").df()
                col1  col2
            0      1     2
            1      3     4
            2      5     6
        """
        batch = self.execute(drop_alias=drop_alias)
        assert batch.frames is not None, 'relation execute failed'
        return batch.frames

    def execute(self, drop_alias: bool=True) -> Batch:
        """Transform the relation into a result set

        Args:
            drop_alias (bool): whether to drop the table name in the output batch. Default: True.

        Returns:
            Batch: result as evadb Batch

        Example:

            Runs a SQL query and get a Batch
            >>> batch = cursor.query("SELECT * FROM MyTable;").execute()
        """
        result = execute_statement(self._evadb, self._query_node.copy())
        if drop_alias:
            result.drop_column_alias()
        assert result is not None
        return result

    def filter(self, expr: str) -> 'EvaDBQuery':
        """
        Filters rows using the given condition. Multiple filters can be chained using `AND`

        Parameters:
            expr (str): The filter expression.

        Returns:
            EvaDBQuery : Filtered EvaDBQuery.
        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.filter("col1 > 10")

            Filter by sql string

            >>> relation.filter("col1 > 10 AND col1 < 20")

        """
        parsed_expr = sql_predicate_to_expresssion_tree(expr)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'where_clause', parsed_expr)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def limit(self, num: int) -> 'EvaDBQuery':
        """Limits the result count to the number specified.

        Args:
            num (int): Number of records to return. Will return num records or all records if the Relation contains fewer records.

        Returns:
            EvaDBQuery: Relation with subset of records

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.limit(10)

        """
        limit_expr = create_limit_expression(num)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'limit_count', limit_expr)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def order(self, order_expr: str) -> 'EvaDBQuery':
        """Reorder the relation based on the order_expr

        Args:
            order_expr (str): sql expression to order the relation

        Returns:
            EvaDBQuery: A EvaDBQuery ordered based on the order_expr.

        Examples:
            >>> relation = cursor.table("PDFs")
            >>> relation.order("Similarity(SentenceTransformerFeatureExtractor('When was the NATO created?'), SentenceTransformerFeatureExtractor(data) ) DESC")

        """
        parsed_expr = parse_sql_orderby_expr(order_expr)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'orderby_list', parsed_expr)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def select(self, expr: str) -> 'EvaDBQuery':
        """
        Projects a set of expressions and returns a new EvaDBQuery.

        Parameters:
            exprs (Union[str, List[str]]): The expression(s) to be selected. If '*' is provided, it expands to all columns in the current EvaDBQuery.

        Returns:
            EvaDBQuery: A EvaDBQuery with subset (or all) of columns.

        Examples:
            >>> relation = cursor.table("sample_table")

            Select all columns in the EvaDBQuery.

            >>> relation.select("*")

            Select all subset of columns in the EvaDBQuery.

            >>> relation.select("col1")
            >>> relation.select("col1, col2")
        """
        parsed_exprs = sql_string_to_expresssion_list(expr)
        self._query_node = handle_select_clause(self._query_node, self._alias, 'target_list', parsed_exprs)
        try_binding(self._evadb.catalog, self._query_node)
        return self

    def show(self) -> pandas.DataFrame:
        """Execute and fetch all rows as a pandas DataFrame

        Returns:
            pandas.DataFrame:
        """
        batch = self.execute()
        assert batch is not None, 'relation execute failed'
        return batch.frames

    def sql_query(self) -> str:
        """Get the SQL query that is equivalent to the relation

        Returns:
            str: the sql query

        Examples:
            >>> relation = cursor.table("sample_table").project('i')
            >>> relation.sql_query()
        """
        return str(self._query_node)

def alias(self, alias: str) -> 'EvaDBQuery':
    """Returns a new Relation with an alias set.

        Args:
            alias (str): an alias name to be set for the Relation.

        Returns:
            EvaDBQuery: Aliased Relation.

        Examples:
            >>> relation = cursor.table("sample_table")
            >>> relation.alias('table')
        """
    self._alias = Alias(alias)

def cross_apply(self, expr: str, alias: str) -> 'EvaDBQuery':
    """Execute a expr on all the rows of the relation

        Args:
            expr (str): sql expression
            alias (str): alias of the output of the expr

        Returns:
            `EvaDBQuery`: relation

        Examples:

            Runs Yolo on all the frames of the input table

            >>> relation = cursor.table("videos")
            >>> relation.cross_apply("Yolo(data)", "objs(labels, bboxes, scores)")

            Runs Yolo on all the frames of the input table and unnest each object as separate row.

            >>> relation.cross_apply("unnest(Yolo(data))", "obj(label, bbox, score)")
        """
    assert self._query_node.from_table is not None
    table_ref = string_to_lateral_join(expr, alias=alias)
    join_table = TableRef(JoinNode(TableRef(self._query_node, alias=self._alias), table_ref, join_type=JoinType.LATERAL_JOIN))
    self._query_node = SelectStatement(target_list=create_star_expression(), from_table=join_table)
    self._alias = Alias('Relation')
    try_binding(self._evadb.catalog, self._query_node)
    return self

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

def __init__(self, frames=None):
    self._frames = pd.DataFrame() if frames is None else frames
    if not isinstance(self._frames, pd.DataFrame):
        raise ValueError(f'Batch constructor not properly called.\nExpected pandas.DataFrame, got {type(self._frames)}')

def __len__(self):
    return len(self._frames)

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

def empty(self):
    """Checks if the batch is empty
        Returns:
            True if the batch_size == 0
        """
    return len(self) == 0

