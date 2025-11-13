# Cluster 17

def get_mock_object(class_type, number_of_args):
    if number_of_args == 1:
        return class_type()
    elif number_of_args == 2:
        return class_type(MagicMock())
    elif number_of_args == 3:
        return class_type(MagicMock(), MagicMock())
    elif number_of_args == 4:
        return class_type(MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 5:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 6:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 7:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 8:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 9:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 10:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 11:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 12:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    elif number_of_args == 13:
        return class_type(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    else:
        raise Exception('Too many args')

def get_logical_query_plan(db, query: str) -> Operator:
    stmt = Parser().parse(query)[0]
    StatementBinder(StatementBinderContext(db.catalog)).bind(stmt)
    l_plan = StatementToPlanConverter().visit(stmt)
    return l_plan

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

def side_effect_func(name):
    if name == 'DummyMultiObjectDetector':
        return MagicMock(cost=10)
    else:
        return MagicMock(cost=5)

class EvaDBServerTest(unittest.IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @patch('evadb.evadb_server.start_evadb_server')
    @patch('asyncio.run')
    def test_main(self, mock_run, mock_start_evadb_server):
        main()
        mock_start_evadb_server.assert_called_once()
        mock_run.assert_called_once()

    @patch('evadb.evadb_server.start_evadb_server')
    @patch('asyncio.start_server')
    async def test_start_evadb_server(self, mock_start_evadb_server, mock_start):
        await start_evadb_server(EvaDB_DATABASE_DIR, '0.0.0.0', 8803)
        mock_start_evadb_server.assert_called_once()

@patch('evadb.evadb_server.start_evadb_server')
@patch('asyncio.run')
def test_main(self, mock_run, mock_start_evadb_server):
    main()
    mock_start_evadb_server.assert_called_once()
    mock_run.assert_called_once()

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

def test_open_same_path_should_use_cache(self):
    import cv2
    with patch('cv2.imread') as mock_cv2_imread:
        self.open_instance(pd.DataFrame([self.image_file_path]))
        mock_cv2_imread.assert_called_once_with(self.image_file_path)
    with patch('cv2.imread') as mock_cv2_imread:
        self.open_instance(pd.DataFrame([self.image_file_path]))
        mock_cv2_imread.assert_not_called()

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

def get_mock_stdin_reader(self) -> asyncio.StreamReader:
    stdin_reader = asyncio.StreamReader()
    stdin_reader.feed_data(b'EXIT;\n')
    stdin_reader.feed_eof()
    return stdin_reader

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

class DallEFunctionTest(unittest.TestCase):

    def setUp(self) -> None:
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        create_table_query = 'CREATE TABLE IF NOT EXISTS ImageGen (\n             prompt TEXT(100));\n                '
        execute_query_fetch_all(self.evadb, create_table_query)
        test_prompts = ['a surreal painting of a cat']
        for prompt in test_prompts:
            insert_query = f"INSERT INTO ImageGen (prompt) VALUES ('{prompt}')"
            execute_query_fetch_all(self.evadb, insert_query)

    def tearDown(self) -> None:
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS ImageGen;')

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'mocked_openai_key'})
    @patch('requests.get')
    @patch('openai.OpenAI')
    def test_dalle_image_generation(self, mock_openai, mock_requests_get):
        img = PILImage.new('RGB', (1, 1), color='white')
        img_byte_array = BytesIO()
        img.save(img_byte_array, format='PNG')
        mock_image_content = img_byte_array.getvalue()
        mock_response = MagicMock()
        mock_response.content = mock_image_content
        mock_requests_get.return_value = mock_response
        mock_openai_instance = mock_openai.return_value
        mock_openai_instance.images.generate.return_value = ImagesResponse(data=[Image(b64_json=None, revised_prompt=None, url='https://images.openai.com/1234.png')])
        function_name = 'DallE'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS {function_name}\n            IMPL 'evadb/functions/dalle.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        gpt_query = f'SELECT {function_name}(prompt) FROM ImageGen;'
        execute_query_fetch_all(self.evadb, gpt_query)
        mock_openai_instance.images.generate.assert_called_once_with(prompt='a surreal painting of a cat', n=1, size='1024x1024')

@patch.dict('os.environ', {'OPENAI_API_KEY': 'mocked_openai_key'})
@patch('requests.get')
@patch('openai.OpenAI')
def test_dalle_image_generation(self, mock_openai, mock_requests_get):
    img = PILImage.new('RGB', (1, 1), color='white')
    img_byte_array = BytesIO()
    img.save(img_byte_array, format='PNG')
    mock_image_content = img_byte_array.getvalue()
    mock_response = MagicMock()
    mock_response.content = mock_image_content
    mock_requests_get.return_value = mock_response
    mock_openai_instance = mock_openai.return_value
    mock_openai_instance.images.generate.return_value = ImagesResponse(data=[Image(b64_json=None, revised_prompt=None, url='https://images.openai.com/1234.png')])
    function_name = 'DallE'
    execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
    create_function_query = f"CREATE FUNCTION IF NOT EXISTS {function_name}\n            IMPL 'evadb/functions/dalle.py';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    gpt_query = f'SELECT {function_name}(prompt) FROM ImageGen;'
    execute_query_fetch_all(self.evadb, gpt_query)
    mock_openai_instance.images.generate.assert_called_once_with(prompt='a surreal painting of a cat', n=1, size='1024x1024')

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

@patch('asyncio.open_connection')
def test_get_connection(self, mock_open):
    server_reader = asyncio.StreamReader()
    server_writer = MagicMock()
    mock_open.return_value = (server_reader, server_writer)
    connection = connect_remote('localhost', port=1)
    self.assertNotEqual(connection, None)

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

def test_create_plan(self):
    dummy_info = TableInfo('dummy')
    columns = [ColumnCatalogEntry('id', ColumnType.INTEGER), ColumnCatalogEntry('name', ColumnType.TEXT, array_dimensions=[50])]
    dummy_plan_node = CreatePlan(dummy_info, columns, False)
    self.assertEqual(dummy_plan_node.opr_type, PlanOprType.CREATE)
    self.assertEqual(dummy_plan_node.if_not_exists, False)
    self.assertEqual(dummy_plan_node.table_info.table_name, 'dummy')
    self.assertEqual(dummy_plan_node.column_list[0].name, 'id')
    self.assertEqual(dummy_plan_node.column_list[1].name, 'name')

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

class StatementToOprTest(unittest.TestCase):

    @patch('evadb.optimizer.statement_to_opr_converter.LogicalGet')
    def test_visit_table_ref_should_create_logical_get_opr(self, mock_lget):
        converter = StatementToPlanConverter()
        table_ref = MagicMock(spec=TableRef, alias='alias', chunk_params={})
        table_ref.is_select.return_value = False
        table_ref.sample_freq = None
        converter.visit_table_ref(table_ref)
        mock_lget.assert_called_with(table_ref, table_ref.table.table_obj, 'alias', chunk_params=table_ref.chunk_params)
        self.assertEqual(mock_lget.return_value, converter._plan)

    @patch('evadb.optimizer.statement_to_opr_converter.LogicalFilter')
    def test_visit_select_predicate_should_add_logical_filter(self, mock_lfilter):
        converter = StatementToPlanConverter()
        select_predicate = MagicMock()
        converter._visit_select_predicate(select_predicate)
        mock_lfilter.assert_called_with(select_predicate)
        mock_lfilter.return_value.append_child.assert_called()
        self.assertEqual(mock_lfilter.return_value, converter._plan)

    @patch('evadb.optimizer.statement_to_opr_converter.LogicalProject')
    def test_visit_projection_should_add_logical_predicate(self, mock_lproject):
        converter = StatementToPlanConverter()
        projects = MagicMock()
        converter._plan = MagicMock()
        converter._visit_projection(projects)
        mock_lproject.assert_called_with(projects)
        mock_lproject.return_value.append_child.assert_called()
        self.assertEqual(mock_lproject.return_value, converter._plan)

    @patch('evadb.optimizer.statement_to_opr_converter.LogicalProject')
    def test_visit_projection_should_not_add_logical_predicate(self, mock_lproject):
        converter = StatementToPlanConverter()
        projects = MagicMock()
        converter._plan = None
        converter._visit_projection(projects)
        mock_lproject.assert_called_with(projects)
        mock_lproject.return_value.append_child.assert_not_called()
        self.assertEqual(mock_lproject.return_value, converter._plan)

    def test_visit_select_should_call_appropriate_visit_methods(self):
        converter = StatementToPlanConverter()
        converter.visit_table_ref = MagicMock()
        converter._visit_projection = MagicMock()
        converter._visit_select_predicate = MagicMock()
        converter._visit_union = MagicMock()
        statement = MagicMock()
        statement.from_table = MagicMock(spec=TableRef)
        converter.visit_select(statement)
        converter.visit_table_ref.assert_called_with(statement.from_table)
        converter._visit_projection.assert_called_with(statement.target_list)
        converter._visit_select_predicate.assert_called_with(statement.where_clause)

    def test_visit_select_should_not_call_visits_for_null_values(self):
        converter = StatementToPlanConverter()
        converter.visit_table_ref = MagicMock()
        converter._visit_projection = MagicMock()
        converter._visit_select_predicate = MagicMock()
        converter._visit_union = MagicMock()
        statement = SelectStatement()
        converter.visit_select(statement)
        converter.visit_table_ref.assert_not_called()
        converter._visit_projection.assert_not_called()
        converter._visit_select_predicate.assert_not_called()

    def test_visit_select_without_table_ref(self):
        converter = StatementToPlanConverter()
        converter.visit_table_ref = MagicMock()
        converter._visit_projection = MagicMock()
        converter._visit_select_predicate = MagicMock()
        converter._visit_union = MagicMock()
        converter._visit_groupby = MagicMock()
        converter._visit_orderby = MagicMock()
        converter._visit_limit = MagicMock()
        column_list = MagicMock()
        statement = SelectStatement(target_list=column_list)
        converter.visit_select(statement)
        converter.visit_table_ref.assert_not_called()
        converter._visit_projection.assert_called_once_with(column_list)
        converter._visit_select_predicate.assert_not_called()
        converter._visit_union.assert_not_called()
        converter._visit_groupby.assert_not_called()
        converter._visit_orderby.assert_not_called()
        converter._visit_limit.assert_not_called()

    @patch('evadb.optimizer.statement_to_opr_converter.LogicalCreateFunction')
    @patch('evadb.optimizer.statement_to_opr_converter.column_definition_to_function_io')
    @patch('evadb.optimizer.statement_to_opr_converter.metadata_definition_to_function_metadata')
    def test_visit_create_function(self, metadata_def_mock, col_def_mock, l_create_function_mock):
        converter = StatementToPlanConverter()
        stmt = MagicMock()
        stmt.name = 'name'
        stmt.or_replace = False
        stmt.if_not_exists = True
        stmt.inputs = ['inp']
        stmt.outputs = ['out']
        stmt.impl_path = 'tmp.py'
        stmt.function_type = 'classification'
        stmt.query = None
        stmt.metadata = [('key1', 'value1'), ('key2', 'value2')]
        col_def_mock.side_effect = ['inp', 'out']
        metadata_def_mock.side_effect = [{'key1': 'value1', 'key2': 'value2'}]
        converter.visit_create_function(stmt)
        col_def_mock.assert_any_call(stmt.inputs, True)
        col_def_mock.assert_any_call(stmt.outputs, False)
        metadata_def_mock.assert_any_call(stmt.metadata)
        l_create_function_mock.assert_called_once()
        l_create_function_mock.assert_called_with(stmt.name, stmt.or_replace, stmt.if_not_exists, 'inp', 'out', stmt.impl_path, stmt.function_type, {'key1': 'value1', 'key2': 'value2'})

    def test_visit_should_call_create_function(self):
        stmt = MagicMock(spec=CreateFunctionStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_create_function = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    @patch('evadb.optimizer.statement_to_opr_converter.LogicalDropObject')
    def test_visit_drop_object(self, l_drop_obj_mock):
        converter = StatementToPlanConverter()
        stmt = MagicMock()
        stmt.name = 'name'
        stmt.object_type = 'object_type'
        stmt.if_exists = True
        converter.visit_drop_object(stmt)
        l_drop_obj_mock.assert_called_once()
        l_drop_obj_mock.assert_called_with(stmt.object_type, stmt.name, stmt.if_exists)

    def test_visit_should_call_insert(self):
        stmt = MagicMock(spec=InsertTableStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_insert = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_create(self):
        stmt = MagicMock(spec=CreateTableStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_create = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_rename(self):
        stmt = MagicMock(spec=RenameTableStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_rename = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_explain(self):
        stmt = MagicMock(spec=ExplainStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_explain = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_once_with(stmt)

    def test_visit_should_call_drop(self):
        stmt = MagicMock(spec=DropObjectStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_drop_object = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_visit_should_call_create_index(self):
        stmt = MagicMock(spec=CreateIndexStatement)
        converter = StatementToPlanConverter()
        mock = MagicMock()
        converter.visit_create_index = mock
        converter.visit(stmt)
        mock.assert_called_once()
        mock.assert_called_with(stmt)

    def test_inequality_in_operator(self):
        dummy_plan = Dummy(MagicMock(), MagicMock())
        object = MagicMock()
        self.assertNotEqual(dummy_plan, object)

    def test_check_plan_equality(self):
        plans = []
        dummy_plan = Dummy(MagicMock(), MagicMock())
        create_plan = LogicalCreate(MagicMock(), MagicMock())
        create_function_plan = LogicalCreateFunction(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
        create_index_plan = LogicalCreateIndex(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
        delete_plan = LogicalDelete(MagicMock())
        insert_plan = LogicalInsert(MagicMock(), MagicMock(), [MagicMock()], [MagicMock()])
        query_derived_plan = LogicalQueryDerivedGet(MagicMock())
        load_plan = LogicalLoadData(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        limit_plan = LogicalLimit(MagicMock())
        rename_plan = LogicalRename(MagicMock(), MagicMock())
        explain_plan = LogicalExplain([MagicMock()])
        exchange_plan = LogicalExchange(MagicMock())
        show_plan = LogicalShow(MagicMock())
        drop_plan = LogicalDropObject(MagicMock(), MagicMock(), MagicMock())
        get_plan = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        sample_plan = LogicalSample(MagicMock(), MagicMock())
        filter_plan = LogicalFilter(MagicMock())
        faiss_plan = LogicalVectorIndexScan(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        groupby_plan = LogicalGroupBy(MagicMock())
        order_by_plan = LogicalOrderBy(MagicMock())
        union_plan = LogicalUnion(MagicMock())
        function_scan_plan = LogicalFunctionScan(MagicMock(), MagicMock())
        join_plan = LogicalJoin(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        project_plan = LogicalProject(MagicMock(), MagicMock())
        apply_and_merge_plan = LogicalApplyAndMerge(MagicMock(), MagicMock())
        extract_object_plan = LogicalExtractObject(MagicMock(), MagicMock(), MagicMock(), MagicMock())
        create_plan.append_child(create_function_plan)
        plans.append(dummy_plan)
        plans.append(create_plan)
        plans.append(create_function_plan)
        plans.append(create_index_plan)
        plans.append(delete_plan)
        plans.append(insert_plan)
        plans.append(query_derived_plan)
        plans.append(load_plan)
        plans.append(limit_plan)
        plans.append(rename_plan)
        plans.append(drop_plan)
        plans.append(get_plan)
        plans.append(sample_plan)
        plans.append(filter_plan)
        plans.append(groupby_plan)
        plans.append(order_by_plan)
        plans.append(union_plan)
        plans.append(function_scan_plan)
        plans.append(join_plan)
        plans.append(apply_and_merge_plan)
        plans.append(show_plan)
        plans.append(explain_plan)
        plans.append(exchange_plan)
        plans.append(faiss_plan)
        plans.append(project_plan)
        plans.append(extract_object_plan)
        derived_operators = list(get_all_subclasses(Operator))
        plan_type_list = []
        for plan in plans:
            plan_type_list.append(type(plan))
        length = len(plans)
        self.assertEqual(length, len(derived_operators))
        self.assertEqual(len(list(set(derived_operators) - set(plan_type_list))), 0)
        for i in range(length):
            self.assertEqual(plans[i], plans[i])
            self.assertNotEqual(str(plans[i]), None)
            if plans[i] != dummy_plan:
                self.assertNotEqual(plans[i], dummy_plan)
            if i >= 1:
                self.assertNotEqual(plans[i - 1], plans[i])
        derived_operators = list(get_all_subclasses(Operator))
        for derived_operator in derived_operators:
            sig = signature(derived_operator.__init__)
            params = sig.parameters
            self.assertLess(len(params), 15)

@patch('evadb.optimizer.statement_to_opr_converter.LogicalGet')
def test_visit_table_ref_should_create_logical_get_opr(self, mock_lget):
    converter = StatementToPlanConverter()
    table_ref = MagicMock(spec=TableRef, alias='alias', chunk_params={})
    table_ref.is_select.return_value = False
    table_ref.sample_freq = None
    converter.visit_table_ref(table_ref)
    mock_lget.assert_called_with(table_ref, table_ref.table.table_obj, 'alias', chunk_params=table_ref.chunk_params)
    self.assertEqual(mock_lget.return_value, converter._plan)

@patch('evadb.optimizer.statement_to_opr_converter.LogicalFilter')
def test_visit_select_predicate_should_add_logical_filter(self, mock_lfilter):
    converter = StatementToPlanConverter()
    select_predicate = MagicMock()
    converter._visit_select_predicate(select_predicate)
    mock_lfilter.assert_called_with(select_predicate)
    mock_lfilter.return_value.append_child.assert_called()
    self.assertEqual(mock_lfilter.return_value, converter._plan)

@patch('evadb.optimizer.statement_to_opr_converter.LogicalProject')
def test_visit_projection_should_add_logical_predicate(self, mock_lproject):
    converter = StatementToPlanConverter()
    projects = MagicMock()
    converter._plan = MagicMock()
    converter._visit_projection(projects)
    mock_lproject.assert_called_with(projects)
    mock_lproject.return_value.append_child.assert_called()
    self.assertEqual(mock_lproject.return_value, converter._plan)

@patch('evadb.optimizer.statement_to_opr_converter.LogicalProject')
def test_visit_projection_should_not_add_logical_predicate(self, mock_lproject):
    converter = StatementToPlanConverter()
    projects = MagicMock()
    converter._plan = None
    converter._visit_projection(projects)
    mock_lproject.assert_called_with(projects)
    mock_lproject.return_value.append_child.assert_not_called()
    self.assertEqual(mock_lproject.return_value, converter._plan)

def test_visit_select_should_call_appropriate_visit_methods(self):
    converter = StatementToPlanConverter()
    converter.visit_table_ref = MagicMock()
    converter._visit_projection = MagicMock()
    converter._visit_select_predicate = MagicMock()
    converter._visit_union = MagicMock()
    statement = MagicMock()
    statement.from_table = MagicMock(spec=TableRef)
    converter.visit_select(statement)
    converter.visit_table_ref.assert_called_with(statement.from_table)
    converter._visit_projection.assert_called_with(statement.target_list)
    converter._visit_select_predicate.assert_called_with(statement.where_clause)

def test_visit_select_should_not_call_visits_for_null_values(self):
    converter = StatementToPlanConverter()
    converter.visit_table_ref = MagicMock()
    converter._visit_projection = MagicMock()
    converter._visit_select_predicate = MagicMock()
    converter._visit_union = MagicMock()
    statement = SelectStatement()
    converter.visit_select(statement)
    converter.visit_table_ref.assert_not_called()
    converter._visit_projection.assert_not_called()
    converter._visit_select_predicate.assert_not_called()

def test_visit_select_without_table_ref(self):
    converter = StatementToPlanConverter()
    converter.visit_table_ref = MagicMock()
    converter._visit_projection = MagicMock()
    converter._visit_select_predicate = MagicMock()
    converter._visit_union = MagicMock()
    converter._visit_groupby = MagicMock()
    converter._visit_orderby = MagicMock()
    converter._visit_limit = MagicMock()
    column_list = MagicMock()
    statement = SelectStatement(target_list=column_list)
    converter.visit_select(statement)
    converter.visit_table_ref.assert_not_called()
    converter._visit_projection.assert_called_once_with(column_list)
    converter._visit_select_predicate.assert_not_called()
    converter._visit_union.assert_not_called()
    converter._visit_groupby.assert_not_called()
    converter._visit_orderby.assert_not_called()
    converter._visit_limit.assert_not_called()

@patch('evadb.optimizer.statement_to_opr_converter.LogicalCreateFunction')
@patch('evadb.optimizer.statement_to_opr_converter.column_definition_to_function_io')
@patch('evadb.optimizer.statement_to_opr_converter.metadata_definition_to_function_metadata')
def test_visit_create_function(self, metadata_def_mock, col_def_mock, l_create_function_mock):
    converter = StatementToPlanConverter()
    stmt = MagicMock()
    stmt.name = 'name'
    stmt.or_replace = False
    stmt.if_not_exists = True
    stmt.inputs = ['inp']
    stmt.outputs = ['out']
    stmt.impl_path = 'tmp.py'
    stmt.function_type = 'classification'
    stmt.query = None
    stmt.metadata = [('key1', 'value1'), ('key2', 'value2')]
    col_def_mock.side_effect = ['inp', 'out']
    metadata_def_mock.side_effect = [{'key1': 'value1', 'key2': 'value2'}]
    converter.visit_create_function(stmt)
    col_def_mock.assert_any_call(stmt.inputs, True)
    col_def_mock.assert_any_call(stmt.outputs, False)
    metadata_def_mock.assert_any_call(stmt.metadata)
    l_create_function_mock.assert_called_once()
    l_create_function_mock.assert_called_with(stmt.name, stmt.or_replace, stmt.if_not_exists, 'inp', 'out', stmt.impl_path, stmt.function_type, {'key1': 'value1', 'key2': 'value2'})

def test_visit_should_call_create_function(self):
    stmt = MagicMock(spec=CreateFunctionStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_create_function = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_with(stmt)

@patch('evadb.optimizer.statement_to_opr_converter.LogicalDropObject')
def test_visit_drop_object(self, l_drop_obj_mock):
    converter = StatementToPlanConverter()
    stmt = MagicMock()
    stmt.name = 'name'
    stmt.object_type = 'object_type'
    stmt.if_exists = True
    converter.visit_drop_object(stmt)
    l_drop_obj_mock.assert_called_once()
    l_drop_obj_mock.assert_called_with(stmt.object_type, stmt.name, stmt.if_exists)

def test_visit_should_call_insert(self):
    stmt = MagicMock(spec=InsertTableStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_insert = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_with(stmt)

def test_visit_should_call_create(self):
    stmt = MagicMock(spec=CreateTableStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_create = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_with(stmt)

def test_visit_should_call_rename(self):
    stmt = MagicMock(spec=RenameTableStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_rename = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_with(stmt)

def test_visit_should_call_explain(self):
    stmt = MagicMock(spec=ExplainStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_explain = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_once_with(stmt)

def test_visit_should_call_drop(self):
    stmt = MagicMock(spec=DropObjectStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_drop_object = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_with(stmt)

def test_visit_should_call_create_index(self):
    stmt = MagicMock(spec=CreateIndexStatement)
    converter = StatementToPlanConverter()
    mock = MagicMock()
    converter.visit_create_index = mock
    converter.visit(stmt)
    mock.assert_called_once()
    mock.assert_called_with(stmt)

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

def test_abstract_optimizer_task(self):
    task = OptimizerTask(MagicMock(), MagicMock())
    with self.assertRaises(NotImplementedError):
        task.execute()

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

def test_rule_base_errors(self):
    with patch.object(Rule, '__abstractmethods__', set()):
        rule = Rule(rule_type=RuleType.INVALID_RULE)
        with self.assertRaises(NotImplementedError):
            rule.promise()
        with self.assertRaises(NotImplementedError):
            rule.check(MagicMock(), MagicMock())
        with self.assertRaises(NotImplementedError):
            rule.apply(MagicMock())

class BatchMemSizeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()

    @classmethod
    def tearDownClass(cls):
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyCSV;')

    def test_batch_mem_size_for_sqlite_storage_engine(self):
        """
            This testcase make sure that the `batch_mem_size` is correctly passed to
        the storage engine.
        """
        test_batch_mem_size = 100
        execute_query_fetch_all(self.evadb, f'SET batch_mem_size={test_batch_mem_size}')
        create_table_query = '\n            CREATE TABLE IF NOT EXISTS MyCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER,\n                video_id INTEGER,\n                dataset_name TEXT(30),\n                label TEXT(30),\n                bbox NDARRAY FLOAT32(4),\n                object_id INTEGER\n            );'
        execute_query_fetch_all(self.evadb, create_table_query)
        select_table_query = 'SELECT * FROM MyCSV;'
        with patch.object(SQLStorageEngine, 'read') as mock_read:
            mock_read.__iter__.return_value = []
            execute_query_fetch_all(self.evadb, select_table_query)
            mock_read.assert_called_with(ANY, test_batch_mem_size)

def test_batch_mem_size_for_sqlite_storage_engine(self):
    """
            This testcase make sure that the `batch_mem_size` is correctly passed to
        the storage engine.
        """
    test_batch_mem_size = 100
    execute_query_fetch_all(self.evadb, f'SET batch_mem_size={test_batch_mem_size}')
    create_table_query = '\n            CREATE TABLE IF NOT EXISTS MyCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER,\n                video_id INTEGER,\n                dataset_name TEXT(30),\n                label TEXT(30),\n                bbox NDARRAY FLOAT32(4),\n                object_id INTEGER\n            );'
    execute_query_fetch_all(self.evadb, create_table_query)
    select_table_query = 'SELECT * FROM MyCSV;'
    with patch.object(SQLStorageEngine, 'read') as mock_read:
        mock_read.__iter__.return_value = []
        execute_query_fetch_all(self.evadb, select_table_query)
        mock_read.assert_called_with(ANY, test_batch_mem_size)

class PlanExecutorTest(unittest.TestCase):

    def test_tree_structure_for_build_execution_tree(self):
        """
            Build an Abstract Plan with nodes:
         ß               root
                      /  |                      c1   c2 c3
                    /
                   c1_1
        """
        predicate = None
        root_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
        child_1_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
        child_2_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
        child_3_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
        child_1_1_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
        root_abs_plan.append_child(child_1_abs_plan)
        root_abs_plan.append_child(child_2_abs_plan)
        root_abs_plan.append_child(child_3_abs_plan)
        child_1_abs_plan.append_child(child_1_1_abs_plan)
        'Build Execution Tree and check the nodes\n            are of the same type'
        root_abs_executor = PlanExecutor(MagicMock(), plan=root_abs_plan)._build_execution_tree(plan=root_abs_plan)
        self.assertEqual(root_abs_plan.opr_type, root_abs_executor._node.opr_type)
        for child_abs, child_exec in zip(root_abs_plan.children, root_abs_executor.children):
            self.assertEqual(child_abs.opr_type, child_exec._node.opr_type)
            for gc_abs, gc_exec in zip(child_abs.children, child_exec.children):
                self.assertEqual(gc_abs.opr_type, gc_exec._node.opr_type)

    def test_build_execution_tree_should_create_correct_exec_node(self):
        plan = SeqScanPlan(MagicMock(), [])
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, SequentialScanExecutor)
        plan = PPScanPlan(MagicMock())
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, PPExecutor)
        plan = CreatePlan(MagicMock(), [], False)
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, CreateExecutor)
        plan = InsertPlan(0, [], [])
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, InsertExecutor)
        plan = CreateFunctionPlan('test', False, [], [], MagicMock(), None)
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, CreateFunctionExecutor)
        plan = DropObjectPlan(MagicMock(), 'test', False)
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, DropObjectExecutor)
        plan = LoadDataPlan(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
        executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
        self.assertIsInstance(executor, LoadDataExecutor)

    @patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
    def test_execute_plan_for_seq_scan_plan(self, mock_build):
        batch_list = [Batch(pd.DataFrame([1])), Batch(pd.DataFrame([2])), Batch(pd.DataFrame([3]))]
        tree = MagicMock(node=SeqScanPlan(None, []))
        tree.exec.return_value = batch_list
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        mock_build.assert_called_once_with(None)
        tree.exec.assert_called_once()
        self.assertEqual(actual, batch_list)

    @patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
    def test_execute_plan_for_pp_scan_plan(self, mock_build):
        batch_list = [Batch(pd.DataFrame([1])), Batch(pd.DataFrame([2])), Batch(pd.DataFrame([3]))]
        tree = MagicMock(node=PPScanPlan(None))
        tree.exec.return_value = batch_list
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        mock_build.assert_called_once_with(None)
        tree.exec.assert_called_once()
        self.assertEqual(actual, batch_list)

    @patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
    def test_execute_plan_for_create_insert_load_upload_plans(self, mock_build):
        tree = MagicMock(node=CreatePlan(None, [], False))
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        tree.exec.assert_called_once()
        mock_build.assert_called_once_with(None)
        self.assertEqual(actual, [])
        mock_build.reset_mock()
        tree = MagicMock(node=InsertPlan(0, [], []))
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        tree.exec.assert_called_once()
        mock_build.assert_called_once_with(None)
        self.assertEqual(actual, [])
        mock_build.reset_mock()
        tree = MagicMock(node=CreateFunctionPlan(None, False, False, [], [], None))
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        tree.exec.assert_called_once()
        mock_build.assert_called_once_with(None)
        self.assertEqual(actual, [])
        mock_build.reset_mock()
        tree = MagicMock(node=LoadDataPlan(None, None, None, None, None))
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        tree.exec.assert_called_once()
        mock_build.assert_called_once_with(None)
        self.assertEqual(actual, [])

    @patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
    def test_execute_plan_for_rename_plans(self, mock_build):
        tree = MagicMock(node=RenamePlan(None, None))
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        tree.exec.assert_called_once()
        mock_build.assert_called_once_with(None)
        self.assertEqual(actual, [])

    @patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
    def test_execute_plan_for_drop_plans(self, mock_build):
        tree = MagicMock(node=DropObjectPlan(None, None, None))
        mock_build.return_value = tree
        actual = list(PlanExecutor(MagicMock(), None).execute_plan())
        tree.exec.assert_called_once()
        mock_build.assert_called_once_with(None)
        self.assertEqual(actual, [])

    @unittest.skip('disk_based_storage_deprecated')
    @patch('evadb.executor.disk_based_storage_executor.Loader')
    def test_should_return_the_new_path_after_execution(self, mock_class):
        class_instance = mock_class.return_value
        dummy_expr = type('dummy_expr', (), {'evaluate': lambda x=None: [True, False, True]})
        video = TableCatalogEntry('dataset', 'dummy.avi', table_type=TableType.VIDEO)
        batch_1 = Batch(pd.DataFrame({'data': [1, 2, 3]}))
        batch_2 = Batch(pd.DataFrame({'data': [4, 5, 6]}))
        class_instance.load.return_value = map(lambda x: x, [batch_1, batch_2])
        storage_plan = StoragePlan(video, batch_mem_size=3000)
        seq_scan = SeqScanPlan(predicate=dummy_expr, column_ids=[])
        seq_scan.append_child(storage_plan)
        executor = PlanExecutor(seq_scan)
        actual = executor.execute_plan()
        expected = batch_1[::2] + batch_2[::2]
        mock_class.assert_called_once()
        self.assertEqual(expected, actual)

def test_tree_structure_for_build_execution_tree(self):
    """
            Build an Abstract Plan with nodes:
         ß               root
                      /  |                      c1   c2 c3
                    /
                   c1_1
        """
    predicate = None
    root_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
    child_1_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
    child_2_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
    child_3_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
    child_1_1_abs_plan = SeqScanPlan(predicate=predicate, columns=[])
    root_abs_plan.append_child(child_1_abs_plan)
    root_abs_plan.append_child(child_2_abs_plan)
    root_abs_plan.append_child(child_3_abs_plan)
    child_1_abs_plan.append_child(child_1_1_abs_plan)
    'Build Execution Tree and check the nodes\n            are of the same type'
    root_abs_executor = PlanExecutor(MagicMock(), plan=root_abs_plan)._build_execution_tree(plan=root_abs_plan)
    self.assertEqual(root_abs_plan.opr_type, root_abs_executor._node.opr_type)
    for child_abs, child_exec in zip(root_abs_plan.children, root_abs_executor.children):
        self.assertEqual(child_abs.opr_type, child_exec._node.opr_type)
        for gc_abs, gc_exec in zip(child_abs.children, child_exec.children):
            self.assertEqual(gc_abs.opr_type, gc_exec._node.opr_type)

def test_build_execution_tree_should_create_correct_exec_node(self):
    plan = SeqScanPlan(MagicMock(), [])
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, SequentialScanExecutor)
    plan = PPScanPlan(MagicMock())
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, PPExecutor)
    plan = CreatePlan(MagicMock(), [], False)
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, CreateExecutor)
    plan = InsertPlan(0, [], [])
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, InsertExecutor)
    plan = CreateFunctionPlan('test', False, [], [], MagicMock(), None)
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, CreateFunctionExecutor)
    plan = DropObjectPlan(MagicMock(), 'test', False)
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, DropObjectExecutor)
    plan = LoadDataPlan(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    executor = PlanExecutor(MagicMock(), plan)._build_execution_tree(plan)
    self.assertIsInstance(executor, LoadDataExecutor)

@patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
def test_execute_plan_for_seq_scan_plan(self, mock_build):
    batch_list = [Batch(pd.DataFrame([1])), Batch(pd.DataFrame([2])), Batch(pd.DataFrame([3]))]
    tree = MagicMock(node=SeqScanPlan(None, []))
    tree.exec.return_value = batch_list
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    mock_build.assert_called_once_with(None)
    tree.exec.assert_called_once()
    self.assertEqual(actual, batch_list)

@patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
def test_execute_plan_for_pp_scan_plan(self, mock_build):
    batch_list = [Batch(pd.DataFrame([1])), Batch(pd.DataFrame([2])), Batch(pd.DataFrame([3]))]
    tree = MagicMock(node=PPScanPlan(None))
    tree.exec.return_value = batch_list
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    mock_build.assert_called_once_with(None)
    tree.exec.assert_called_once()
    self.assertEqual(actual, batch_list)

@patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
def test_execute_plan_for_create_insert_load_upload_plans(self, mock_build):
    tree = MagicMock(node=CreatePlan(None, [], False))
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    tree.exec.assert_called_once()
    mock_build.assert_called_once_with(None)
    self.assertEqual(actual, [])
    mock_build.reset_mock()
    tree = MagicMock(node=InsertPlan(0, [], []))
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    tree.exec.assert_called_once()
    mock_build.assert_called_once_with(None)
    self.assertEqual(actual, [])
    mock_build.reset_mock()
    tree = MagicMock(node=CreateFunctionPlan(None, False, False, [], [], None))
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    tree.exec.assert_called_once()
    mock_build.assert_called_once_with(None)
    self.assertEqual(actual, [])
    mock_build.reset_mock()
    tree = MagicMock(node=LoadDataPlan(None, None, None, None, None))
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    tree.exec.assert_called_once()
    mock_build.assert_called_once_with(None)
    self.assertEqual(actual, [])

@patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
def test_execute_plan_for_rename_plans(self, mock_build):
    tree = MagicMock(node=RenamePlan(None, None))
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    tree.exec.assert_called_once()
    mock_build.assert_called_once_with(None)
    self.assertEqual(actual, [])

@patch('evadb.executor.plan_executor.PlanExecutor._build_execution_tree')
def test_execute_plan_for_drop_plans(self, mock_build):
    tree = MagicMock(node=DropObjectPlan(None, None, None))
    mock_build.return_value = tree
    actual = list(PlanExecutor(MagicMock(), None).execute_plan())
    tree.exec.assert_called_once()
    mock_build.assert_called_once_with(None)
    self.assertEqual(actual, [])

@unittest.skip('disk_based_storage_deprecated')
@patch('evadb.executor.disk_based_storage_executor.Loader')
def test_should_return_the_new_path_after_execution(self, mock_class):
    class_instance = mock_class.return_value
    dummy_expr = type('dummy_expr', (), {'evaluate': lambda x=None: [True, False, True]})
    video = TableCatalogEntry('dataset', 'dummy.avi', table_type=TableType.VIDEO)
    batch_1 = Batch(pd.DataFrame({'data': [1, 2, 3]}))
    batch_2 = Batch(pd.DataFrame({'data': [4, 5, 6]}))
    class_instance.load.return_value = map(lambda x: x, [batch_1, batch_2])
    storage_plan = StoragePlan(video, batch_mem_size=3000)
    seq_scan = SeqScanPlan(predicate=dummy_expr, column_ids=[])
    seq_scan.append_child(storage_plan)
    executor = PlanExecutor(seq_scan)
    actual = executor.execute_plan()
    expected = batch_1[::2] + batch_2[::2]
    mock_class.assert_called_once()
    self.assertEqual(expected, actual)

class ExecutionContextTest(unittest.TestCase):

    @patch('evadb.executor.execution_context.get_gpu_count')
    @patch('evadb.executor.execution_context.is_gpu_available')
    def test_CUDA_VISIBLE_DEVICES_gets_populated_from_config(self, gpu_check, get_gpu_count):
        gpu_check.return_value = True
        get_gpu_count.return_value = 3
        context = Context([0, 1])
        self.assertEqual(context.gpus, [0, 1])

    @patch('evadb.executor.execution_context.os')
    @patch('evadb.executor.execution_context.get_gpu_count')
    @patch('evadb.executor.execution_context.is_gpu_available')
    def test_CUDA_VISIBLE_DEVICES_gets_populated_from_environment_if_no_config(self, is_gpu, get_gpu_count, os):
        is_gpu.return_value = True
        get_gpu_count.return_value = 3
        os.environ.get.return_value = '0,1'
        context = Context()
        os.environ.get.assert_called_with('CUDA_VISIBLE_DEVICES', '')
        self.assertEqual(context.gpus, [0, 1])

    @patch('evadb.executor.execution_context.os')
    @patch('evadb.executor.execution_context.get_gpu_count')
    @patch('evadb.executor.execution_context.is_gpu_available')
    def test_CUDA_VISIBLE_DEVICES_should_be_empty_if_nothing_provided(self, gpu_check, get_gpu_count, os):
        gpu_check.return_value = True
        get_gpu_count.return_value = 3
        os.environ.get.return_value = ''
        context = Context()
        os.environ.get.assert_called_with('CUDA_VISIBLE_DEVICES', '')
        self.assertEqual(context.gpus, [])

    @patch('evadb.executor.execution_context.os')
    @patch('evadb.executor.execution_context.is_gpu_available')
    def test_gpus_ignores_config_if_no_gpu_available(self, gpu_check, os):
        gpu_check.return_value = False
        os.environ.get.return_value = '0,1,2'
        context = Context([0, 1, 2])
        self.assertEqual(context.gpus, [])

    @patch('evadb.executor.execution_context.os')
    @patch('evadb.executor.execution_context.is_gpu_available')
    def test_gpu_device_should_return_NO_GPU_if_GPU_not_available(self, gpu_check, os):
        gpu_check.return_value = True
        os.environ.get.return_value = ''
        context = Context()
        os.environ.get.assert_called_with('CUDA_VISIBLE_DEVICES', '')
        self.assertEqual(context.gpu_device(), NO_GPU)

    @patch('evadb.executor.execution_context.get_gpu_count')
    @patch('evadb.executor.execution_context.is_gpu_available')
    def test_should_return_random_gpu_ID_if_available(self, gpu_check, get_gpu_count):
        gpu_check.return_value = True
        get_gpu_count.return_value = 1
        context = Context([0, 1, 2])
        selected_device = context.gpu_device()
        self.assertEqual(selected_device, 0)

@patch('evadb.executor.execution_context.get_gpu_count')
@patch('evadb.executor.execution_context.is_gpu_available')
def test_CUDA_VISIBLE_DEVICES_gets_populated_from_config(self, gpu_check, get_gpu_count):
    gpu_check.return_value = True
    get_gpu_count.return_value = 3
    context = Context([0, 1])
    self.assertEqual(context.gpus, [0, 1])

@patch('evadb.executor.execution_context.os')
@patch('evadb.executor.execution_context.get_gpu_count')
@patch('evadb.executor.execution_context.is_gpu_available')
def test_CUDA_VISIBLE_DEVICES_gets_populated_from_environment_if_no_config(self, is_gpu, get_gpu_count, os):
    is_gpu.return_value = True
    get_gpu_count.return_value = 3
    os.environ.get.return_value = '0,1'
    context = Context()
    os.environ.get.assert_called_with('CUDA_VISIBLE_DEVICES', '')
    self.assertEqual(context.gpus, [0, 1])

@patch('evadb.executor.execution_context.os')
@patch('evadb.executor.execution_context.get_gpu_count')
@patch('evadb.executor.execution_context.is_gpu_available')
def test_CUDA_VISIBLE_DEVICES_should_be_empty_if_nothing_provided(self, gpu_check, get_gpu_count, os):
    gpu_check.return_value = True
    get_gpu_count.return_value = 3
    os.environ.get.return_value = ''
    context = Context()
    os.environ.get.assert_called_with('CUDA_VISIBLE_DEVICES', '')
    self.assertEqual(context.gpus, [])

@patch('evadb.executor.execution_context.os')
@patch('evadb.executor.execution_context.is_gpu_available')
def test_gpus_ignores_config_if_no_gpu_available(self, gpu_check, os):
    gpu_check.return_value = False
    os.environ.get.return_value = '0,1,2'
    context = Context([0, 1, 2])
    self.assertEqual(context.gpus, [])

@patch('evadb.executor.execution_context.os')
@patch('evadb.executor.execution_context.is_gpu_available')
def test_gpu_device_should_return_NO_GPU_if_GPU_not_available(self, gpu_check, os):
    gpu_check.return_value = True
    os.environ.get.return_value = ''
    context = Context()
    os.environ.get.assert_called_with('CUDA_VISIBLE_DEVICES', '')
    self.assertEqual(context.gpu_device(), NO_GPU)

@patch('evadb.executor.execution_context.get_gpu_count')
@patch('evadb.executor.execution_context.is_gpu_available')
def test_should_return_random_gpu_ID_if_available(self, gpu_check, get_gpu_count):
    gpu_check.return_value = True
    get_gpu_count.return_value = 1
    context = Context([0, 1, 2])
    selected_device = context.gpu_device()
    self.assertEqual(selected_device, 0)

class CreateFunctionExecutorTest(unittest.TestCase):

    @patch('evadb.executor.create_function_executor.load_function_class_from_file')
    def test_should_create_function(self, load_function_class_from_file_mock):
        catalog_instance = MagicMock()
        catalog_instance().get_function_catalog_entry_by_name.return_value = None
        catalog_instance().insert_function_catalog_entry.return_value = 'function'
        impl_path = MagicMock()
        abs_path = impl_path.absolute.return_value = MagicMock()
        abs_path.as_posix.return_value = 'test.py'
        load_function_class_from_file_mock.return_value.return_value = 'mock_class'
        plan = type('CreateFunctionPlan', (), {'name': 'function', 'if_not_exists': False, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'classification', 'metadata': {'key1': 'value1', 'key2': 'value2'}})
        evadb = MagicMock
        evadb.catalog = catalog_instance
        evadb.config = MagicMock()
        create_function_executor = CreateFunctionExecutor(evadb, plan)
        next(create_function_executor.exec())
        catalog_instance().insert_function_catalog_entry.assert_called_with('function', 'test.py', 'classification', ['inp', 'out'], {'key1': 'value1', 'key2': 'value2'})

    def test_should_raise_or_replace_if_not_exists(self):
        plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': True, 'if_not_exists': True})
        evadb = MagicMock()
        create_function_executor = CreateFunctionExecutor(evadb, plan)
        with self.assertRaises(AssertionError) as cm:
            next(create_function_executor.exec())
        self.assertEqual(str(cm.exception), 'OR REPLACE and IF NOT EXISTS can not be both set for CREATE FUNCTION.')

    @patch('evadb.executor.create_function_executor.load_function_class_from_file')
    def test_should_skip_if_not_exists(self, load_function_class_from_file_mock):
        catalog_instance = MagicMock()
        catalog_instance().get_function_catalog_entry_by_name.return_value = True
        catalog_instance().insert_function_catalog_entry.return_value = 'function'
        impl_path = MagicMock()
        abs_path = impl_path.absolute.return_value = MagicMock()
        abs_path.as_posix.return_value = 'test.py'
        load_function_class_from_file_mock.return_value.return_value = 'mock_class'
        plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': False, 'if_not_exists': True, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'classification', 'metadata': {'key1': 'value1', 'key2': 'value2'}})
        evadb = MagicMock()
        evadb.catalog = catalog_instance
        evadb.config = MagicMock()
        create_function_executor = CreateFunctionExecutor(evadb, plan)
        actual_batch = next(create_function_executor.exec())
        catalog_instance().insert_function_catalog_entry.assert_not_called()
        self.assertEqual(actual_batch.frames[0][0], 'Function function already exists, nothing added.')

    @patch('evadb.executor.create_function_executor.load_function_class_from_file')
    def test_should_overwrite_or_replace(self, load_function_class_from_file_mock):
        catalog_instance = MagicMock()
        catalog_instance().get_function_catalog_entry_by_name.return_value = False
        catalog_instance().insert_function_catalog_entry.return_value = 'function'
        impl_path = MagicMock()
        abs_path = impl_path.absolute.return_value = MagicMock()
        abs_path.as_posix.return_value = 'test.py'
        load_function_class_from_file_mock.return_value.return_value = 'mock_class'
        plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': True, 'if_not_exists': False, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'classification', 'metadata': {'key1': 'value1', 'key2': 'value2'}})
        evadb = MagicMock()
        evadb.catalog = catalog_instance
        evadb.config = MagicMock()
        create_function_executor = CreateFunctionExecutor(evadb, plan)
        actual_batch = next(create_function_executor.exec())
        catalog_instance().insert_function_catalog_entry.assert_called_with('function', 'test.py', 'classification', ['inp', 'out'], {'key1': 'value1', 'key2': 'value2'})
        self.assertEqual(actual_batch.frames[0][0], 'Function function added to the database.')
        function_entry = MagicMock()
        cache = MagicMock()
        function_entry.dep_caches = [cache]
        catalog_instance().get_function_catalog_entry_by_name.return_value = function_entry
        plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': True, 'if_not_exists': False, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'prediction', 'metadata': {'key1': 'value3', 'key2': 'value4'}})
        create_function_executor = CreateFunctionExecutor(evadb, plan)
        actual_batch = next(create_function_executor.exec())
        catalog_instance().drop_function_cache_catalog_entry.assert_called_with(cache)
        catalog_instance().delete_function_catalog_entry_by_name.assert_called_with('function')
        catalog_instance().insert_function_catalog_entry.assert_called_with('function', 'test.py', 'prediction', ['inp', 'out'], {'key1': 'value3', 'key2': 'value4'})
        self.assertEqual(actual_batch.frames[0][0], 'Function function overwritten.')

    @patch('evadb.executor.create_function_executor.load_function_class_from_file')
    def test_should_raise_error_on_incorrect_io_definition(self, load_function_class_from_file_mock):
        catalog_instance = MagicMock()
        catalog_instance().get_function_catalog_entry_by_name.return_value = None
        catalog_instance().insert_function_catalog_entry.return_value = 'function'
        impl_path = MagicMock()
        abs_path = impl_path.absolute.return_value = MagicMock()
        abs_path.as_posix.return_value = 'test.py'
        load_function_class_from_file_mock.return_value.return_value = 'mock_class'
        incorrect_input_definition = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256), (3, 256, 256)])
        load_function_class_from_file_mock.return_value.forward.tags = {'input': [incorrect_input_definition], 'output': []}
        plan = type('CreateFunctionPlan', (), {'name': 'function', 'if_not_exists': False, 'inputs': [], 'outputs': [], 'impl_path': impl_path, 'function_type': 'classification'})
        evadb = MagicMock
        evadb.catalog = catalog_instance
        evadb.config = MagicMock()
        create_function_executor = CreateFunctionExecutor(evadb, plan)
        with self.assertRaises(RuntimeError) as exc:
            next(create_function_executor.exec())
        self.assertIn('Error creating function, input/output definition incorrect:', str(exc.exception))
        catalog_instance().insert_function_catalog_entry.assert_not_called()

@patch('evadb.executor.create_function_executor.load_function_class_from_file')
def test_should_create_function(self, load_function_class_from_file_mock):
    catalog_instance = MagicMock()
    catalog_instance().get_function_catalog_entry_by_name.return_value = None
    catalog_instance().insert_function_catalog_entry.return_value = 'function'
    impl_path = MagicMock()
    abs_path = impl_path.absolute.return_value = MagicMock()
    abs_path.as_posix.return_value = 'test.py'
    load_function_class_from_file_mock.return_value.return_value = 'mock_class'
    plan = type('CreateFunctionPlan', (), {'name': 'function', 'if_not_exists': False, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'classification', 'metadata': {'key1': 'value1', 'key2': 'value2'}})
    evadb = MagicMock
    evadb.catalog = catalog_instance
    evadb.config = MagicMock()
    create_function_executor = CreateFunctionExecutor(evadb, plan)
    next(create_function_executor.exec())
    catalog_instance().insert_function_catalog_entry.assert_called_with('function', 'test.py', 'classification', ['inp', 'out'], {'key1': 'value1', 'key2': 'value2'})

def test_should_raise_or_replace_if_not_exists(self):
    plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': True, 'if_not_exists': True})
    evadb = MagicMock()
    create_function_executor = CreateFunctionExecutor(evadb, plan)
    with self.assertRaises(AssertionError) as cm:
        next(create_function_executor.exec())
    self.assertEqual(str(cm.exception), 'OR REPLACE and IF NOT EXISTS can not be both set for CREATE FUNCTION.')

@patch('evadb.executor.create_function_executor.load_function_class_from_file')
def test_should_skip_if_not_exists(self, load_function_class_from_file_mock):
    catalog_instance = MagicMock()
    catalog_instance().get_function_catalog_entry_by_name.return_value = True
    catalog_instance().insert_function_catalog_entry.return_value = 'function'
    impl_path = MagicMock()
    abs_path = impl_path.absolute.return_value = MagicMock()
    abs_path.as_posix.return_value = 'test.py'
    load_function_class_from_file_mock.return_value.return_value = 'mock_class'
    plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': False, 'if_not_exists': True, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'classification', 'metadata': {'key1': 'value1', 'key2': 'value2'}})
    evadb = MagicMock()
    evadb.catalog = catalog_instance
    evadb.config = MagicMock()
    create_function_executor = CreateFunctionExecutor(evadb, plan)
    actual_batch = next(create_function_executor.exec())
    catalog_instance().insert_function_catalog_entry.assert_not_called()
    self.assertEqual(actual_batch.frames[0][0], 'Function function already exists, nothing added.')

@patch('evadb.executor.create_function_executor.load_function_class_from_file')
def test_should_overwrite_or_replace(self, load_function_class_from_file_mock):
    catalog_instance = MagicMock()
    catalog_instance().get_function_catalog_entry_by_name.return_value = False
    catalog_instance().insert_function_catalog_entry.return_value = 'function'
    impl_path = MagicMock()
    abs_path = impl_path.absolute.return_value = MagicMock()
    abs_path.as_posix.return_value = 'test.py'
    load_function_class_from_file_mock.return_value.return_value = 'mock_class'
    plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': True, 'if_not_exists': False, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'classification', 'metadata': {'key1': 'value1', 'key2': 'value2'}})
    evadb = MagicMock()
    evadb.catalog = catalog_instance
    evadb.config = MagicMock()
    create_function_executor = CreateFunctionExecutor(evadb, plan)
    actual_batch = next(create_function_executor.exec())
    catalog_instance().insert_function_catalog_entry.assert_called_with('function', 'test.py', 'classification', ['inp', 'out'], {'key1': 'value1', 'key2': 'value2'})
    self.assertEqual(actual_batch.frames[0][0], 'Function function added to the database.')
    function_entry = MagicMock()
    cache = MagicMock()
    function_entry.dep_caches = [cache]
    catalog_instance().get_function_catalog_entry_by_name.return_value = function_entry
    plan = type('CreateFunctionPlan', (), {'name': 'function', 'or_replace': True, 'if_not_exists': False, 'inputs': ['inp'], 'outputs': ['out'], 'impl_path': impl_path, 'function_type': 'prediction', 'metadata': {'key1': 'value3', 'key2': 'value4'}})
    create_function_executor = CreateFunctionExecutor(evadb, plan)
    actual_batch = next(create_function_executor.exec())
    catalog_instance().drop_function_cache_catalog_entry.assert_called_with(cache)
    catalog_instance().delete_function_catalog_entry_by_name.assert_called_with('function')
    catalog_instance().insert_function_catalog_entry.assert_called_with('function', 'test.py', 'prediction', ['inp', 'out'], {'key1': 'value3', 'key2': 'value4'})
    self.assertEqual(actual_batch.frames[0][0], 'Function function overwritten.')

@patch('evadb.executor.create_function_executor.load_function_class_from_file')
def test_should_raise_error_on_incorrect_io_definition(self, load_function_class_from_file_mock):
    catalog_instance = MagicMock()
    catalog_instance().get_function_catalog_entry_by_name.return_value = None
    catalog_instance().insert_function_catalog_entry.return_value = 'function'
    impl_path = MagicMock()
    abs_path = impl_path.absolute.return_value = MagicMock()
    abs_path.as_posix.return_value = 'test.py'
    load_function_class_from_file_mock.return_value.return_value = 'mock_class'
    incorrect_input_definition = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256), (3, 256, 256)])
    load_function_class_from_file_mock.return_value.forward.tags = {'input': [incorrect_input_definition], 'output': []}
    plan = type('CreateFunctionPlan', (), {'name': 'function', 'if_not_exists': False, 'inputs': [], 'outputs': [], 'impl_path': impl_path, 'function_type': 'classification'})
    evadb = MagicMock
    evadb.catalog = catalog_instance
    evadb.config = MagicMock()
    create_function_executor = CreateFunctionExecutor(evadb, plan)
    with self.assertRaises(RuntimeError) as exc:
        next(create_function_executor.exec())
    self.assertIn('Error creating function, input/output definition incorrect:', str(exc.exception))
    catalog_instance().insert_function_catalog_entry.assert_not_called()

def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError('Expected %s to not have been called.' % self._format_mock_call_signature(args, kwargs))

class StatementBinderTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_bind_tuple_value_expression(self):
        with patch.object(StatementBinderContext, 'get_binded_column') as mock:
            mock.return_value = ['table_alias', 'col_obj']
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            tve = MagicMock()
            tve.name = 'col_name'
            binder._bind_tuple_expr(tve)
            col_alias = '{}.{}'.format('table_alias', 'col_name')
            mock.assert_called_once()
            self.assertEqual(tve.col_object, 'col_obj')
            self.assertEqual(tve.col_alias, col_alias)

    @patch('evadb.binder.statement_binder.bind_table_info')
    def test_bind_tableref(self, mock_bind_table_info):
        with patch.object(StatementBinderContext, 'add_table_alias') as mock:
            catalog = MagicMock()
            binder = StatementBinder(StatementBinderContext(catalog))
            tableref = MagicMock()
            tableref.is_table_atom.return_value = True
            binder._bind_tableref(tableref)
            mock.assert_called_with(tableref.alias.alias_name, tableref.table.database_name, tableref.table.table_name)
            mock_bind_table_info.assert_called_once_with(catalog(), tableref.table)
        with patch.object(StatementBinder, 'bind') as mock_binder:
            with patch.object(StatementBinderContext, 'add_derived_table_alias') as mock_context:
                binder = StatementBinder(StatementBinderContext(MagicMock()))
                tableref = MagicMock()
                tableref.is_table_atom.return_value = False
                tableref.is_select.return_value = True
                binder._bind_tableref(tableref)
                mock_context.assert_called_with(tableref.alias.alias_name, tableref.select_statement.target_list)
                mock_binder.assert_called_with(tableref.select_statement)

    def test_bind_tableref_with_func_expr(self):
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            tableref = MagicMock()
            tableref.is_table_atom.return_value = False
            tableref.is_select.return_value = False
            tableref.is_join.return_value = False
            binder._bind_tableref(tableref)
            mock_binder.assert_called_with(tableref.table_valued_expr.func_expr)

    def test_bind_tableref_with_join(self):
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            tableref = MagicMock()
            tableref.is_table_atom.return_value = False
            tableref.is_select.return_value = False
            tableref.is_join.return_value = True
            binder._bind_tableref(tableref)
            mock_binder.assert_any_call(tableref.join_node.left)
            mock_binder.assert_any_call(tableref.join_node.right)

    def test_bind_tableref_should_raise(self):
        with patch.object(StatementBinder, 'bind'):
            with self.assertRaises(BinderError):
                binder = StatementBinder(StatementBinderContext(MagicMock()))
                tableref = MagicMock()
                tableref.is_select.return_value = False
                tableref.is_table_valued_expr.return_value = False
                tableref.is_join.return_value = False
                tableref.is_table_atom.return_value = False
                binder._bind_tableref(tableref)

    @patch('evadb.binder.statement_binder.StatementBinderContext')
    def test_bind_tableref_starts_new_context(self, mock_ctx):
        with patch.object(StatementBinder, 'bind'):
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            tableref = MagicMock()
            tableref.is_table_atom.return_value = False
            tableref.is_join.return_value = False
            tableref.is_select.return_value = True
            binder._bind_tableref(tableref)
            self.assertEqual(mock_ctx.call_count, 1)

    def test_bind_create_table_from_select_statement(self):
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            output_obj = MagicMock()
            output_obj.type = ColumnType.INTEGER
            output_obj.array_type = NdArrayType.UINT8
            output_obj.array_dimensions = (1, 1)
            create_statement = MagicMock()
            create_statement.column_list = []
            create_statement.query.target_list = [TupleValueExpression(name='id', col_object=output_obj), TupleValueExpression(name='label', col_object=output_obj)]
            binder._bind_create_statement(create_statement)
            mock_binder.assert_called_with(create_statement.query)
            self.assertEqual(2, len(create_statement.column_list))

    def test_bind_explain_statement(self):
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            stmt = MagicMock()
            binder._bind_explain_statement(stmt)
            mock_binder.assert_called_with(stmt.explainable_stmt)

    def test_bind_func_expr_with_star(self):
        func_expr = MagicMock(name='func_expr', alias=Alias('func_expr'), output_col_aliases=[])
        func_expr.name.lower.return_value = 'func_expr'
        func_expr.children = [TupleValueExpression(name='*')]
        binderContext = MagicMock()
        tvp1 = ('T', 'col1')
        tvp2 = ('T', 'col2')
        binderContext._catalog.return_value.get_function_catalog_entry_by_name.return_value = None
        binderContext._get_all_alias_and_col_name.return_value = [tvp1, tvp2]
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(binderContext)
            with self.assertRaises(BinderError):
                binder._bind_func_expr(func_expr)
            call1, call2 = mock_binder.call_args_list
            self.assertEqual(call1.args[0], TupleValueExpression(name=tvp1[1], table_alias=tvp1[0]))
            self.assertEqual(call2.args[0], TupleValueExpression(name=tvp2[1], table_alias=tvp2[0]))

    @patch('evadb.binder.function_expression_binder.load_function_class_from_file')
    def test_bind_func_expr(self, mock_load_function_class_from_file):
        func_expr = MagicMock(name='func_expr', alias=Alias('func_expr'), output_col_aliases=[])
        func_expr.name.lower.return_value = 'func_expr'
        obj1 = MagicMock()
        obj1.name.lower.return_value = 'out1'
        obj2 = MagicMock()
        obj2.name.lower.return_value = 'out2'
        func_output_objs = [obj1, obj2]
        function_obj = MagicMock()
        mock_catalog = MagicMock()
        mock_get_name = mock_catalog().get_function_catalog_entry_by_name = MagicMock()
        mock_get_name.return_value = function_obj
        mock_get_function_outputs = mock_catalog().get_function_io_catalog_output_entries = MagicMock()
        mock_get_function_outputs.return_value = func_output_objs
        mock_load_function_class_from_file.return_value.return_value = 'load_function_class_from_file'
        func_expr.output = 'out1'
        binder = StatementBinder(StatementBinderContext(mock_catalog))
        binder._bind_func_expr(func_expr)
        mock_get_name.assert_called_with(func_expr.name)
        mock_get_function_outputs.assert_called_with(function_obj)
        mock_load_function_class_from_file.assert_called_with(function_obj.impl_file_path, function_obj.name)
        self.assertEqual(func_expr.output_objs, [obj1])
        self.assertEqual(func_expr.alias, Alias('func_expr', ['out1']))
        self.assertEqual(func_expr.function(), 'load_function_class_from_file')
        func_expr.output = None
        func_expr.alias = Alias('func_expr')
        binder = StatementBinder(StatementBinderContext(mock_catalog))
        binder._bind_func_expr(func_expr)
        mock_get_name.assert_called_with(func_expr.name)
        mock_get_function_outputs.assert_called_with(function_obj)
        mock_load_function_class_from_file.assert_called_with(function_obj.impl_file_path, function_obj.name)
        self.assertEqual(func_expr.output_objs, func_output_objs)
        self.assertEqual(func_expr.alias, Alias('func_expr', ['out1', 'out2']))
        self.assertEqual(func_expr.function(), 'load_function_class_from_file')
        mock_load_function_class_from_file.reset_mock()
        mock_error_msg = 'mock_load_function_class_from_file_error'
        mock_load_function_class_from_file.side_effect = MagicMock(side_effect=RuntimeError(mock_error_msg))
        binder = StatementBinder(StatementBinderContext(mock_catalog))
        with self.assertRaises(BinderError) as cm:
            binder._bind_func_expr(func_expr)
        err_msg = f'{mock_error_msg}. Please verify that the function class name in the implementation file matches the function name.'
        self.assertEqual(str(cm.exception), err_msg)

    @patch('evadb.binder.statement_binder.check_table_object_is_groupable')
    @patch('evadb.binder.statement_binder.check_groupby_pattern')
    def test_bind_select_statement(self, is_groupable_mock, groupby_mock):
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            select_statement = MagicMock()
            mocks = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            select_statement.target_list = mocks[:2]
            select_statement.orderby_list = [(mocks[2], 0), (mocks[3], 0)]
            select_statement.groupby_clause = mocks[4]
            select_statement.groupby_clause.value = '8 frames'
            select_statement.from_table.chunk_params = None
            binder._bind_select_statement(select_statement)
            mock_binder.assert_any_call(select_statement.from_table)
            mock_binder.assert_any_call(select_statement.where_clause)
            mock_binder.assert_any_call(select_statement.groupby_clause)
            mock_binder.assert_any_call(select_statement.union_link)
            is_groupable_mock.assert_called()
            for mock in mocks:
                mock_binder.assert_any_call(mock)

    def test_bind_select_statement_without_from(self):
        with patch.object(StatementBinder, 'bind') as mock_binder:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            expr = MagicMock()
            from evadb.parser.select_statement import SelectStatement
            select_statement = SelectStatement(target_list=[expr])
            binder._bind_select_statement(select_statement)
            mock_binder.assert_not_called_with(select_statement.from_table)
            mock_binder.assert_any_call(expr)

    @patch('evadb.binder.statement_binder.StatementBinderContext')
    def test_bind_select_statement_union_starts_new_context(self, mock_ctx):
        with patch.object(StatementBinder, 'bind'):
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            select_statement = MagicMock()
            select_statement.union_link = None
            select_statement.groupby_clause = None
            select_statement.from_table.chunk_params = None
            binder._bind_select_statement(select_statement)
            self.assertEqual(mock_ctx.call_count, 0)
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            select_statement = MagicMock()
            select_statement.from_table.chunk_params = None
            select_statement.groupby_clause = None
            binder._bind_select_statement(select_statement)
            self.assertEqual(mock_ctx.call_count, 1)

    def test_bind_unknown_object(self):

        class UnknownType:
            pass
        with self.assertRaises(NotImplementedError):
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            binder.bind(UnknownType())

    def test_bind_create_index(self):
        with patch.object(StatementBinder, 'bind'):
            catalog = MagicMock()
            binder = StatementBinder(StatementBinderContext(catalog))
            create_index_statement = MagicMock()
            with self.assertRaises(AssertionError):
                binder._bind_create_index_statement(create_index_statement)
            col_def = MagicMock()
            col_def.name = 'a'
            create_index_statement.col_list = [col_def]
            col = MagicMock()
            col.name = 'a'
            create_index_statement.table_ref.table.table_obj.columns = [col]
            function_obj = MagicMock()
            output = MagicMock()
            function_obj.outputs = [output]
            create_index_statement.project_expr_list = [FunctionExpression(MagicMock(), name='a'), TupleValueExpression(name='*')]
            with patch.object(catalog(), 'get_function_catalog_entry_by_name', return_value=function_obj):
                with self.assertRaises(AssertionError):
                    binder._bind_create_index_statement(create_index_statement)
                output.array_type = NdArrayType.FLOAT32
                with self.assertRaises(AssertionError):
                    binder._bind_create_index_statement(create_index_statement)
                output.array_dimensions = [1, 100]
                binder._bind_create_index_statement(create_index_statement)
            create_index_statement.project_expr_list = [TupleValueExpression(name='*')]
            with self.assertRaises(AssertionError):
                binder._bind_create_index_statement(create_index_statement)
            col.array_type = NdArrayType.FLOAT32
            with self.assertRaises(AssertionError):
                binder._bind_create_index_statement(create_index_statement)
            col.array_dimensions = [1, 10]
            binder._bind_create_index_statement(create_index_statement)

    def test_bind_create_function_should_raise_without_predict_for_ludwig(self):
        with patch.object(StatementBinder, 'bind'):
            create_function_statement = MagicMock()
            create_function_statement.function_type = 'ludwig'
            create_function_statement.query.target_list = []
            create_function_statement.metadata = []
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            with self.assertRaises(AssertionError):
                binder._bind_create_function_statement(create_function_statement)

    def test_bind_create_function_should_drop_row_id_for_select_star(self):
        with patch.object(StatementBinder, 'bind'):
            create_function_statement = MagicMock()
            create_function_statement.function_type = 'ludwig'
            row_id_col_obj = ColumnCatalogEntry(name=IDENTIFIER_COLUMN, type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            input_col_obj = ColumnCatalogEntry(name='input_column', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            output_col_obj = ColumnCatalogEntry(name='predict_column', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            create_function_statement.query.target_list = [TupleValueExpression(name=IDENTIFIER_COLUMN, table_alias='a', col_object=row_id_col_obj), TupleValueExpression(name='input_column', table_alias='a', col_object=input_col_obj), TupleValueExpression(name='predict_column', table_alias='a', col_object=output_col_obj)]
            create_function_statement.metadata = [('predict', 'predict_column')]
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            binder._bind_create_function_statement(create_function_statement)
            self.assertEqual(create_function_statement.query.target_list, [TupleValueExpression(name='input_column', table_alias='a', col_object=input_col_obj), TupleValueExpression(name='predict_column', table_alias='a', col_object=output_col_obj)])
            expected_inputs = [ColumnDefinition('input_column', input_col_obj.type, input_col_obj.array_type, input_col_obj.array_dimensions)]
            expected_outputs = [ColumnDefinition('predict_column_predictions', output_col_obj.type, output_col_obj.array_type, output_col_obj.array_dimensions)]
            self.assertEqual(create_function_statement.inputs, expected_inputs)
            self.assertEqual(create_function_statement.outputs, expected_outputs)

    def test_bind_create_function_should_bind_forecast_with_default_columns(self):
        with patch.object(StatementBinder, 'bind'):
            create_function_statement = MagicMock()
            create_function_statement.function_type = 'forecasting'
            id_col_obj = ColumnCatalogEntry(name='unique_id', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            ds_col_obj = ColumnCatalogEntry(name='ds', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            y_col_obj = ColumnCatalogEntry(name='y', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            y_lo_col_obj = ColumnCatalogEntry(name='y-lo', type=ColumnType.FLOAT, array_type=None)
            y_hi_col_obj = ColumnCatalogEntry(name='y-hi', type=ColumnType.FLOAT, array_type=None)
            create_function_statement.query.target_list = [TupleValueExpression(name=id_col_obj.name, table_alias='a', col_object=id_col_obj), TupleValueExpression(name=ds_col_obj.name, table_alias='a', col_object=ds_col_obj), TupleValueExpression(name=y_col_obj.name, table_alias='a', col_object=y_col_obj)]
            create_function_statement.metadata = []
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            binder._bind_create_function_statement(create_function_statement)
            expected_inputs = [ColumnDefinition('horizon', ColumnType.INTEGER, None, None)]
            expected_outputs = list([ColumnDefinition(col_obj.name, col_obj.type, col_obj.array_type, col_obj.array_dimensions) for col_obj in (id_col_obj, ds_col_obj, y_col_obj, y_lo_col_obj, y_hi_col_obj)])
            self.assertEqual(create_function_statement.inputs, expected_inputs)
            self.assertEqual(create_function_statement.outputs, expected_outputs)

    def test_bind_create_function_should_bind_forecast_with_renaming_columns(self):
        with patch.object(StatementBinder, 'bind'):
            create_function_statement = MagicMock()
            create_function_statement.function_type = 'forecasting'
            id_col_obj = ColumnCatalogEntry(name='type', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            ds_col_obj = ColumnCatalogEntry(name='saledate', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            y_col_obj = ColumnCatalogEntry(name='ma', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            y_lo_col_obj = ColumnCatalogEntry(name='ma-lo', type=ColumnType.FLOAT, array_type=None)
            y_hi_col_obj = ColumnCatalogEntry(name='ma-hi', type=ColumnType.FLOAT, array_type=None)
            create_function_statement.query.target_list = [TupleValueExpression(name=id_col_obj.name, table_alias='a', col_object=id_col_obj), TupleValueExpression(name=ds_col_obj.name, table_alias='a', col_object=ds_col_obj), TupleValueExpression(name=y_col_obj.name, table_alias='a', col_object=y_col_obj)]
            create_function_statement.metadata = [('predict', 'ma'), ('id', 'type'), ('time', 'saledate')]
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            binder._bind_create_function_statement(create_function_statement)
            expected_inputs = [ColumnDefinition('horizon', ColumnType.INTEGER, None, None)]
            expected_outputs = list([ColumnDefinition(col_obj.name, col_obj.type, col_obj.array_type, col_obj.array_dimensions) for col_obj in (id_col_obj, ds_col_obj, y_col_obj, y_lo_col_obj, y_hi_col_obj)])
            self.assertEqual(create_function_statement.inputs, expected_inputs)
            self.assertEqual(create_function_statement.outputs, expected_outputs)

    def test_bind_create_function_should_raise_forecast_missing_required_columns(self):
        with patch.object(StatementBinder, 'bind'):
            create_function_statement = MagicMock()
            create_function_statement.function_type = 'forecasting'
            id_col_obj = ColumnCatalogEntry(name='type', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            ds_col_obj = ColumnCatalogEntry(name='saledate', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
            create_function_statement.query.target_list = [TupleValueExpression(name=id_col_obj.name, table_alias='a', col_object=id_col_obj), TupleValueExpression(name=ds_col_obj.name, table_alias='a', col_object=ds_col_obj)]
            create_function_statement.metadata = [('id', 'type'), ('time', 'saledate'), ('predict', 'ma')]
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            with self.assertRaises(AssertionError) as cm:
                binder._bind_create_function_statement(create_function_statement)
            err_msg = "Missing required {'ma'} columns for forecasting function."
            self.assertEqual(str(cm.exception), err_msg)

def test_bind_tuple_value_expression(self):
    with patch.object(StatementBinderContext, 'get_binded_column') as mock:
        mock.return_value = ['table_alias', 'col_obj']
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        tve = MagicMock()
        tve.name = 'col_name'
        binder._bind_tuple_expr(tve)
        col_alias = '{}.{}'.format('table_alias', 'col_name')
        mock.assert_called_once()
        self.assertEqual(tve.col_object, 'col_obj')
        self.assertEqual(tve.col_alias, col_alias)

@patch('evadb.binder.statement_binder.bind_table_info')
def test_bind_tableref(self, mock_bind_table_info):
    with patch.object(StatementBinderContext, 'add_table_alias') as mock:
        catalog = MagicMock()
        binder = StatementBinder(StatementBinderContext(catalog))
        tableref = MagicMock()
        tableref.is_table_atom.return_value = True
        binder._bind_tableref(tableref)
        mock.assert_called_with(tableref.alias.alias_name, tableref.table.database_name, tableref.table.table_name)
        mock_bind_table_info.assert_called_once_with(catalog(), tableref.table)
    with patch.object(StatementBinder, 'bind') as mock_binder:
        with patch.object(StatementBinderContext, 'add_derived_table_alias') as mock_context:
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            tableref = MagicMock()
            tableref.is_table_atom.return_value = False
            tableref.is_select.return_value = True
            binder._bind_tableref(tableref)
            mock_context.assert_called_with(tableref.alias.alias_name, tableref.select_statement.target_list)
            mock_binder.assert_called_with(tableref.select_statement)

def test_bind_tableref_with_func_expr(self):
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        tableref = MagicMock()
        tableref.is_table_atom.return_value = False
        tableref.is_select.return_value = False
        tableref.is_join.return_value = False
        binder._bind_tableref(tableref)
        mock_binder.assert_called_with(tableref.table_valued_expr.func_expr)

def test_bind_tableref_with_join(self):
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        tableref = MagicMock()
        tableref.is_table_atom.return_value = False
        tableref.is_select.return_value = False
        tableref.is_join.return_value = True
        binder._bind_tableref(tableref)
        mock_binder.assert_any_call(tableref.join_node.left)
        mock_binder.assert_any_call(tableref.join_node.right)

def test_bind_tableref_should_raise(self):
    with patch.object(StatementBinder, 'bind'):
        with self.assertRaises(BinderError):
            binder = StatementBinder(StatementBinderContext(MagicMock()))
            tableref = MagicMock()
            tableref.is_select.return_value = False
            tableref.is_table_valued_expr.return_value = False
            tableref.is_join.return_value = False
            tableref.is_table_atom.return_value = False
            binder._bind_tableref(tableref)

@patch('evadb.binder.statement_binder.StatementBinderContext')
def test_bind_tableref_starts_new_context(self, mock_ctx):
    with patch.object(StatementBinder, 'bind'):
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        tableref = MagicMock()
        tableref.is_table_atom.return_value = False
        tableref.is_join.return_value = False
        tableref.is_select.return_value = True
        binder._bind_tableref(tableref)
        self.assertEqual(mock_ctx.call_count, 1)

def test_bind_create_table_from_select_statement(self):
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        output_obj = MagicMock()
        output_obj.type = ColumnType.INTEGER
        output_obj.array_type = NdArrayType.UINT8
        output_obj.array_dimensions = (1, 1)
        create_statement = MagicMock()
        create_statement.column_list = []
        create_statement.query.target_list = [TupleValueExpression(name='id', col_object=output_obj), TupleValueExpression(name='label', col_object=output_obj)]
        binder._bind_create_statement(create_statement)
        mock_binder.assert_called_with(create_statement.query)
        self.assertEqual(2, len(create_statement.column_list))

def test_bind_explain_statement(self):
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        stmt = MagicMock()
        binder._bind_explain_statement(stmt)
        mock_binder.assert_called_with(stmt.explainable_stmt)

def test_bind_func_expr_with_star(self):
    func_expr = MagicMock(name='func_expr', alias=Alias('func_expr'), output_col_aliases=[])
    func_expr.name.lower.return_value = 'func_expr'
    func_expr.children = [TupleValueExpression(name='*')]
    binderContext = MagicMock()
    tvp1 = ('T', 'col1')
    tvp2 = ('T', 'col2')
    binderContext._catalog.return_value.get_function_catalog_entry_by_name.return_value = None
    binderContext._get_all_alias_and_col_name.return_value = [tvp1, tvp2]
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(binderContext)
        with self.assertRaises(BinderError):
            binder._bind_func_expr(func_expr)
        call1, call2 = mock_binder.call_args_list
        self.assertEqual(call1.args[0], TupleValueExpression(name=tvp1[1], table_alias=tvp1[0]))
        self.assertEqual(call2.args[0], TupleValueExpression(name=tvp2[1], table_alias=tvp2[0]))

@patch('evadb.binder.function_expression_binder.load_function_class_from_file')
def test_bind_func_expr(self, mock_load_function_class_from_file):
    func_expr = MagicMock(name='func_expr', alias=Alias('func_expr'), output_col_aliases=[])
    func_expr.name.lower.return_value = 'func_expr'
    obj1 = MagicMock()
    obj1.name.lower.return_value = 'out1'
    obj2 = MagicMock()
    obj2.name.lower.return_value = 'out2'
    func_output_objs = [obj1, obj2]
    function_obj = MagicMock()
    mock_catalog = MagicMock()
    mock_get_name = mock_catalog().get_function_catalog_entry_by_name = MagicMock()
    mock_get_name.return_value = function_obj
    mock_get_function_outputs = mock_catalog().get_function_io_catalog_output_entries = MagicMock()
    mock_get_function_outputs.return_value = func_output_objs
    mock_load_function_class_from_file.return_value.return_value = 'load_function_class_from_file'
    func_expr.output = 'out1'
    binder = StatementBinder(StatementBinderContext(mock_catalog))
    binder._bind_func_expr(func_expr)
    mock_get_name.assert_called_with(func_expr.name)
    mock_get_function_outputs.assert_called_with(function_obj)
    mock_load_function_class_from_file.assert_called_with(function_obj.impl_file_path, function_obj.name)
    self.assertEqual(func_expr.output_objs, [obj1])
    self.assertEqual(func_expr.alias, Alias('func_expr', ['out1']))
    self.assertEqual(func_expr.function(), 'load_function_class_from_file')
    func_expr.output = None
    func_expr.alias = Alias('func_expr')
    binder = StatementBinder(StatementBinderContext(mock_catalog))
    binder._bind_func_expr(func_expr)
    mock_get_name.assert_called_with(func_expr.name)
    mock_get_function_outputs.assert_called_with(function_obj)
    mock_load_function_class_from_file.assert_called_with(function_obj.impl_file_path, function_obj.name)
    self.assertEqual(func_expr.output_objs, func_output_objs)
    self.assertEqual(func_expr.alias, Alias('func_expr', ['out1', 'out2']))
    self.assertEqual(func_expr.function(), 'load_function_class_from_file')
    mock_load_function_class_from_file.reset_mock()
    mock_error_msg = 'mock_load_function_class_from_file_error'
    mock_load_function_class_from_file.side_effect = MagicMock(side_effect=RuntimeError(mock_error_msg))
    binder = StatementBinder(StatementBinderContext(mock_catalog))
    with self.assertRaises(BinderError) as cm:
        binder._bind_func_expr(func_expr)
    err_msg = f'{mock_error_msg}. Please verify that the function class name in the implementation file matches the function name.'
    self.assertEqual(str(cm.exception), err_msg)

@patch('evadb.binder.statement_binder.check_table_object_is_groupable')
@patch('evadb.binder.statement_binder.check_groupby_pattern')
def test_bind_select_statement(self, is_groupable_mock, groupby_mock):
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        select_statement = MagicMock()
        mocks = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        select_statement.target_list = mocks[:2]
        select_statement.orderby_list = [(mocks[2], 0), (mocks[3], 0)]
        select_statement.groupby_clause = mocks[4]
        select_statement.groupby_clause.value = '8 frames'
        select_statement.from_table.chunk_params = None
        binder._bind_select_statement(select_statement)
        mock_binder.assert_any_call(select_statement.from_table)
        mock_binder.assert_any_call(select_statement.where_clause)
        mock_binder.assert_any_call(select_statement.groupby_clause)
        mock_binder.assert_any_call(select_statement.union_link)
        is_groupable_mock.assert_called()
        for mock in mocks:
            mock_binder.assert_any_call(mock)

def test_bind_select_statement_without_from(self):
    with patch.object(StatementBinder, 'bind') as mock_binder:
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        expr = MagicMock()
        from evadb.parser.select_statement import SelectStatement
        select_statement = SelectStatement(target_list=[expr])
        binder._bind_select_statement(select_statement)
        mock_binder.assert_not_called_with(select_statement.from_table)
        mock_binder.assert_any_call(expr)

@patch('evadb.binder.statement_binder.StatementBinderContext')
def test_bind_select_statement_union_starts_new_context(self, mock_ctx):
    with patch.object(StatementBinder, 'bind'):
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        select_statement = MagicMock()
        select_statement.union_link = None
        select_statement.groupby_clause = None
        select_statement.from_table.chunk_params = None
        binder._bind_select_statement(select_statement)
        self.assertEqual(mock_ctx.call_count, 0)
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        select_statement = MagicMock()
        select_statement.from_table.chunk_params = None
        select_statement.groupby_clause = None
        binder._bind_select_statement(select_statement)
        self.assertEqual(mock_ctx.call_count, 1)

def test_bind_unknown_object(self):

    class UnknownType:
        pass
    with self.assertRaises(NotImplementedError):
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        binder.bind(UnknownType())

def test_bind_create_index(self):
    with patch.object(StatementBinder, 'bind'):
        catalog = MagicMock()
        binder = StatementBinder(StatementBinderContext(catalog))
        create_index_statement = MagicMock()
        with self.assertRaises(AssertionError):
            binder._bind_create_index_statement(create_index_statement)
        col_def = MagicMock()
        col_def.name = 'a'
        create_index_statement.col_list = [col_def]
        col = MagicMock()
        col.name = 'a'
        create_index_statement.table_ref.table.table_obj.columns = [col]
        function_obj = MagicMock()
        output = MagicMock()
        function_obj.outputs = [output]
        create_index_statement.project_expr_list = [FunctionExpression(MagicMock(), name='a'), TupleValueExpression(name='*')]
        with patch.object(catalog(), 'get_function_catalog_entry_by_name', return_value=function_obj):
            with self.assertRaises(AssertionError):
                binder._bind_create_index_statement(create_index_statement)
            output.array_type = NdArrayType.FLOAT32
            with self.assertRaises(AssertionError):
                binder._bind_create_index_statement(create_index_statement)
            output.array_dimensions = [1, 100]
            binder._bind_create_index_statement(create_index_statement)
        create_index_statement.project_expr_list = [TupleValueExpression(name='*')]
        with self.assertRaises(AssertionError):
            binder._bind_create_index_statement(create_index_statement)
        col.array_type = NdArrayType.FLOAT32
        with self.assertRaises(AssertionError):
            binder._bind_create_index_statement(create_index_statement)
        col.array_dimensions = [1, 10]
        binder._bind_create_index_statement(create_index_statement)

def test_bind_create_function_should_raise_without_predict_for_ludwig(self):
    with patch.object(StatementBinder, 'bind'):
        create_function_statement = MagicMock()
        create_function_statement.function_type = 'ludwig'
        create_function_statement.query.target_list = []
        create_function_statement.metadata = []
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        with self.assertRaises(AssertionError):
            binder._bind_create_function_statement(create_function_statement)

def test_bind_create_function_should_drop_row_id_for_select_star(self):
    with patch.object(StatementBinder, 'bind'):
        create_function_statement = MagicMock()
        create_function_statement.function_type = 'ludwig'
        row_id_col_obj = ColumnCatalogEntry(name=IDENTIFIER_COLUMN, type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        input_col_obj = ColumnCatalogEntry(name='input_column', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        output_col_obj = ColumnCatalogEntry(name='predict_column', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        create_function_statement.query.target_list = [TupleValueExpression(name=IDENTIFIER_COLUMN, table_alias='a', col_object=row_id_col_obj), TupleValueExpression(name='input_column', table_alias='a', col_object=input_col_obj), TupleValueExpression(name='predict_column', table_alias='a', col_object=output_col_obj)]
        create_function_statement.metadata = [('predict', 'predict_column')]
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        binder._bind_create_function_statement(create_function_statement)
        self.assertEqual(create_function_statement.query.target_list, [TupleValueExpression(name='input_column', table_alias='a', col_object=input_col_obj), TupleValueExpression(name='predict_column', table_alias='a', col_object=output_col_obj)])
        expected_inputs = [ColumnDefinition('input_column', input_col_obj.type, input_col_obj.array_type, input_col_obj.array_dimensions)]
        expected_outputs = [ColumnDefinition('predict_column_predictions', output_col_obj.type, output_col_obj.array_type, output_col_obj.array_dimensions)]
        self.assertEqual(create_function_statement.inputs, expected_inputs)
        self.assertEqual(create_function_statement.outputs, expected_outputs)

def test_bind_create_function_should_bind_forecast_with_default_columns(self):
    with patch.object(StatementBinder, 'bind'):
        create_function_statement = MagicMock()
        create_function_statement.function_type = 'forecasting'
        id_col_obj = ColumnCatalogEntry(name='unique_id', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        ds_col_obj = ColumnCatalogEntry(name='ds', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        y_col_obj = ColumnCatalogEntry(name='y', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        y_lo_col_obj = ColumnCatalogEntry(name='y-lo', type=ColumnType.FLOAT, array_type=None)
        y_hi_col_obj = ColumnCatalogEntry(name='y-hi', type=ColumnType.FLOAT, array_type=None)
        create_function_statement.query.target_list = [TupleValueExpression(name=id_col_obj.name, table_alias='a', col_object=id_col_obj), TupleValueExpression(name=ds_col_obj.name, table_alias='a', col_object=ds_col_obj), TupleValueExpression(name=y_col_obj.name, table_alias='a', col_object=y_col_obj)]
        create_function_statement.metadata = []
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        binder._bind_create_function_statement(create_function_statement)
        expected_inputs = [ColumnDefinition('horizon', ColumnType.INTEGER, None, None)]
        expected_outputs = list([ColumnDefinition(col_obj.name, col_obj.type, col_obj.array_type, col_obj.array_dimensions) for col_obj in (id_col_obj, ds_col_obj, y_col_obj, y_lo_col_obj, y_hi_col_obj)])
        self.assertEqual(create_function_statement.inputs, expected_inputs)
        self.assertEqual(create_function_statement.outputs, expected_outputs)

def test_bind_create_function_should_bind_forecast_with_renaming_columns(self):
    with patch.object(StatementBinder, 'bind'):
        create_function_statement = MagicMock()
        create_function_statement.function_type = 'forecasting'
        id_col_obj = ColumnCatalogEntry(name='type', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        ds_col_obj = ColumnCatalogEntry(name='saledate', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        y_col_obj = ColumnCatalogEntry(name='ma', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        y_lo_col_obj = ColumnCatalogEntry(name='ma-lo', type=ColumnType.FLOAT, array_type=None)
        y_hi_col_obj = ColumnCatalogEntry(name='ma-hi', type=ColumnType.FLOAT, array_type=None)
        create_function_statement.query.target_list = [TupleValueExpression(name=id_col_obj.name, table_alias='a', col_object=id_col_obj), TupleValueExpression(name=ds_col_obj.name, table_alias='a', col_object=ds_col_obj), TupleValueExpression(name=y_col_obj.name, table_alias='a', col_object=y_col_obj)]
        create_function_statement.metadata = [('predict', 'ma'), ('id', 'type'), ('time', 'saledate')]
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        binder._bind_create_function_statement(create_function_statement)
        expected_inputs = [ColumnDefinition('horizon', ColumnType.INTEGER, None, None)]
        expected_outputs = list([ColumnDefinition(col_obj.name, col_obj.type, col_obj.array_type, col_obj.array_dimensions) for col_obj in (id_col_obj, ds_col_obj, y_col_obj, y_lo_col_obj, y_hi_col_obj)])
        self.assertEqual(create_function_statement.inputs, expected_inputs)
        self.assertEqual(create_function_statement.outputs, expected_outputs)

def test_bind_create_function_should_raise_forecast_missing_required_columns(self):
    with patch.object(StatementBinder, 'bind'):
        create_function_statement = MagicMock()
        create_function_statement.function_type = 'forecasting'
        id_col_obj = ColumnCatalogEntry(name='type', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        ds_col_obj = ColumnCatalogEntry(name='saledate', type=MagicMock(), array_type=MagicMock(), array_dimensions=MagicMock())
        create_function_statement.query.target_list = [TupleValueExpression(name=id_col_obj.name, table_alias='a', col_object=id_col_obj), TupleValueExpression(name=ds_col_obj.name, table_alias='a', col_object=ds_col_obj)]
        create_function_statement.metadata = [('id', 'type'), ('time', 'saledate'), ('predict', 'ma')]
        binder = StatementBinder(StatementBinderContext(MagicMock()))
        with self.assertRaises(AssertionError) as cm:
            binder._bind_create_function_statement(create_function_statement)
        err_msg = "Missing required {'ma'} columns for forecasting function."
        self.assertEqual(str(cm.exception), err_msg)

@pytest.mark.notparallel
class StatementBinderTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_check_duplicate_alias(self):
        with self.assertRaises(BinderError):
            ctx = StatementBinderContext(MagicMock())
            ctx._derived_table_alias_map['alias'] = MagicMock()
            ctx._check_duplicate_alias('alias')
        with self.assertRaises(BinderError):
            ctx = StatementBinderContext(MagicMock())
            ctx._table_alias_map['alias'] = MagicMock()
            ctx._check_duplicate_alias('alias')
        ctx = StatementBinderContext(MagicMock())
        ctx._check_duplicate_alias('alias')

    def test_add_table_alias(self):
        mock_catalog = MagicMock()
        mock_get = mock_catalog().get_table_catalog_entry = MagicMock()
        mock_get.return_value = 'table_obj'
        ctx = StatementBinderContext(mock_catalog)
        mock_check = ctx._check_duplicate_alias = MagicMock()
        ctx.add_table_alias('alias', None, 'table_name')
        mock_check.assert_called_with('alias')
        mock_get.assert_called_with('table_name')
        self.assertEqual(ctx._table_alias_map['alias'], 'table_obj')

    def test_add_derived_table_alias(self):
        objs = [MagicMock(), MagicMock()]
        attributes = {'name': 'A', 'col_object': 'A_obj'}
        mock = MagicMock(spec=TupleValueExpression)
        for attr, value in attributes.items():
            setattr(mock, attr, value)
        exprs = [mock, MagicMock(spec=FunctionExpression, output_objs=objs)]
        ctx = StatementBinderContext(MagicMock())
        mock_check = ctx._check_duplicate_alias = MagicMock()
        ctx.add_derived_table_alias('alias', exprs)
        mock_check.assert_called_with('alias')
        col_map = {'A': 'A_obj', objs[0].name: objs[0], objs[1].name: objs[1]}
        self.assertEqual(ctx._derived_table_alias_map['alias'], col_map)

    def test_get_binded_column_should_search_all(self):
        ctx = StatementBinderContext(MagicMock())
        mock_search_all = ctx._search_all_alias_maps = MagicMock()
        mock_search_all.return_value = ('alias', 'col_obj')
        result = ctx.get_binded_column('col_name')
        mock_search_all.assert_called_once_with('col_name')
        self.assertEqual(result, ('alias', 'col_obj'))

    def test_get_binded_column_check_table_alias_map(self):
        ctx = StatementBinderContext(MagicMock())
        mock_table_map = ctx._check_table_alias_map = MagicMock()
        mock_table_map.return_value = 'col_obj'
        result = ctx.get_binded_column('col_name', 'alias')
        mock_table_map.assert_called_once_with('alias', 'col_name')
        self.assertEqual(result, ('alias', 'col_obj'))

    def test_get_binded_column_check_derived_table_alias_map(self):
        ctx = StatementBinderContext(MagicMock())
        mock_table_map = ctx._check_table_alias_map = MagicMock()
        mock_table_map.return_value = None
        mock_derived_map = ctx._check_derived_table_alias_map = MagicMock()
        mock_derived_map.return_value = 'col_obj'
        result = ctx.get_binded_column('col_name', 'alias')
        mock_table_map.assert_called_once_with('alias', 'col_name')
        mock_derived_map.assert_called_once_with('alias', 'col_name')
        self.assertEqual(result, ('alias', 'col_obj'))

    def test_get_binded_column_raise_error(self):
        with self.assertRaises(BinderError):
            ctx = StatementBinderContext(MagicMock())
            mock_search_all = ctx._search_all_alias_maps = MagicMock()
            mock_search_all.return_value = (None, None)
            ctx.get_binded_column('col_name')
        with self.assertRaises(BinderError):
            ctx = StatementBinderContext(MagicMock())
            mock_table_map = ctx._check_table_alias_map = MagicMock()
            mock_table_map.return_value = None
            mock_derived_map = ctx._check_derived_table_alias_map = MagicMock()
            mock_derived_map.return_value = None
            ctx.get_binded_column('col_name', 'alias')

    def test_check_table_alias_map(self):
        mock_catalog = MagicMock()
        mock_get_column_object = mock_catalog().get_column_catalog_entry = MagicMock()
        mock_get_column_object.return_value = 'catalog_value'
        ctx = StatementBinderContext(mock_catalog)
        table_obj = MagicMock()
        ctx._table_alias_map['alias'] = table_obj
        result = ctx._check_table_alias_map('alias', 'col_name')
        mock_get_column_object.assert_called_once_with(table_obj, 'col_name')
        self.assertEqual(result, 'catalog_value')
        mock_get_column_object.reset_mock()
        ctx = StatementBinderContext(mock_catalog)
        result = ctx._check_table_alias_map('alias', 'col_name')
        mock_get_column_object.assert_not_called()
        self.assertEqual(result, None)

    def test_check_derived_table_alias_map(self):
        ctx = StatementBinderContext(MagicMock())
        obj1 = MagicMock()
        obj2 = MagicMock()
        col_map = {'col1': obj1, 'col2': obj2}
        ctx._derived_table_alias_map['alias'] = col_map
        result = ctx._check_derived_table_alias_map('alias', 'col1')
        self.assertEqual(result, obj1)
        result = ctx._check_derived_table_alias_map('alias', 'col2')
        self.assertEqual(result, obj2)
        ctx = StatementBinderContext(MagicMock())
        result = ctx._check_derived_table_alias_map('alias', 'col3')
        self.assertEqual(result, None)

    def test_search_all_alias_maps(self):
        ctx = StatementBinderContext(MagicMock())
        check_table_map = ctx._check_table_alias_map = MagicMock()
        check_derived_map = ctx._check_derived_table_alias_map = MagicMock()
        check_table_map.return_value = 'col_obj'
        ctx._table_alias_map['alias'] = 'col_name'
        ctx._derived_table_alias_map = {}
        result = ctx._search_all_alias_maps('col_name')
        check_table_map.assert_called_once_with('alias', 'col_name')
        check_derived_map.assert_not_called()
        self.assertEqual(result, ('alias', 'col_obj'))
        check_derived_map.return_value = 'derived_col_obj'
        ctx._table_alias_map = {}
        ctx._derived_table_alias_map['alias'] = 'col_name'
        result = ctx._search_all_alias_maps('col_name')
        check_table_map.assert_called_once_with('alias', 'col_name')
        check_table_map.assert_called_once_with('alias', 'col_name')
        self.assertEqual(result, ('alias', 'derived_col_obj'))

    def test_search_all_alias_raise_duplicate_error(self):
        with self.assertRaises(BinderError):
            ctx = StatementBinderContext(MagicMock())
            ctx._check_table_alias_map = MagicMock()
            ctx._check_derived_table_alias_map = MagicMock()
            ctx._table_alias_map['alias'] = 'col_name'
            ctx._derived_table_alias_map['alias'] = 'col_name'
            ctx._search_all_alias_maps('col_name')

def test_check_duplicate_alias(self):
    with self.assertRaises(BinderError):
        ctx = StatementBinderContext(MagicMock())
        ctx._derived_table_alias_map['alias'] = MagicMock()
        ctx._check_duplicate_alias('alias')
    with self.assertRaises(BinderError):
        ctx = StatementBinderContext(MagicMock())
        ctx._table_alias_map['alias'] = MagicMock()
        ctx._check_duplicate_alias('alias')
    ctx = StatementBinderContext(MagicMock())
    ctx._check_duplicate_alias('alias')

def test_add_table_alias(self):
    mock_catalog = MagicMock()
    mock_get = mock_catalog().get_table_catalog_entry = MagicMock()
    mock_get.return_value = 'table_obj'
    ctx = StatementBinderContext(mock_catalog)
    mock_check = ctx._check_duplicate_alias = MagicMock()
    ctx.add_table_alias('alias', None, 'table_name')
    mock_check.assert_called_with('alias')
    mock_get.assert_called_with('table_name')
    self.assertEqual(ctx._table_alias_map['alias'], 'table_obj')

def test_add_derived_table_alias(self):
    objs = [MagicMock(), MagicMock()]
    attributes = {'name': 'A', 'col_object': 'A_obj'}
    mock = MagicMock(spec=TupleValueExpression)
    for attr, value in attributes.items():
        setattr(mock, attr, value)
    exprs = [mock, MagicMock(spec=FunctionExpression, output_objs=objs)]
    ctx = StatementBinderContext(MagicMock())
    mock_check = ctx._check_duplicate_alias = MagicMock()
    ctx.add_derived_table_alias('alias', exprs)
    mock_check.assert_called_with('alias')
    col_map = {'A': 'A_obj', objs[0].name: objs[0], objs[1].name: objs[1]}
    self.assertEqual(ctx._derived_table_alias_map['alias'], col_map)

def test_get_binded_column_should_search_all(self):
    ctx = StatementBinderContext(MagicMock())
    mock_search_all = ctx._search_all_alias_maps = MagicMock()
    mock_search_all.return_value = ('alias', 'col_obj')
    result = ctx.get_binded_column('col_name')
    mock_search_all.assert_called_once_with('col_name')
    self.assertEqual(result, ('alias', 'col_obj'))

def test_get_binded_column_check_table_alias_map(self):
    ctx = StatementBinderContext(MagicMock())
    mock_table_map = ctx._check_table_alias_map = MagicMock()
    mock_table_map.return_value = 'col_obj'
    result = ctx.get_binded_column('col_name', 'alias')
    mock_table_map.assert_called_once_with('alias', 'col_name')
    self.assertEqual(result, ('alias', 'col_obj'))

def test_get_binded_column_check_derived_table_alias_map(self):
    ctx = StatementBinderContext(MagicMock())
    mock_table_map = ctx._check_table_alias_map = MagicMock()
    mock_table_map.return_value = None
    mock_derived_map = ctx._check_derived_table_alias_map = MagicMock()
    mock_derived_map.return_value = 'col_obj'
    result = ctx.get_binded_column('col_name', 'alias')
    mock_table_map.assert_called_once_with('alias', 'col_name')
    mock_derived_map.assert_called_once_with('alias', 'col_name')
    self.assertEqual(result, ('alias', 'col_obj'))

def test_get_binded_column_raise_error(self):
    with self.assertRaises(BinderError):
        ctx = StatementBinderContext(MagicMock())
        mock_search_all = ctx._search_all_alias_maps = MagicMock()
        mock_search_all.return_value = (None, None)
        ctx.get_binded_column('col_name')
    with self.assertRaises(BinderError):
        ctx = StatementBinderContext(MagicMock())
        mock_table_map = ctx._check_table_alias_map = MagicMock()
        mock_table_map.return_value = None
        mock_derived_map = ctx._check_derived_table_alias_map = MagicMock()
        mock_derived_map.return_value = None
        ctx.get_binded_column('col_name', 'alias')

def test_check_table_alias_map(self):
    mock_catalog = MagicMock()
    mock_get_column_object = mock_catalog().get_column_catalog_entry = MagicMock()
    mock_get_column_object.return_value = 'catalog_value'
    ctx = StatementBinderContext(mock_catalog)
    table_obj = MagicMock()
    ctx._table_alias_map['alias'] = table_obj
    result = ctx._check_table_alias_map('alias', 'col_name')
    mock_get_column_object.assert_called_once_with(table_obj, 'col_name')
    self.assertEqual(result, 'catalog_value')
    mock_get_column_object.reset_mock()
    ctx = StatementBinderContext(mock_catalog)
    result = ctx._check_table_alias_map('alias', 'col_name')
    mock_get_column_object.assert_not_called()
    self.assertEqual(result, None)

def test_check_derived_table_alias_map(self):
    ctx = StatementBinderContext(MagicMock())
    obj1 = MagicMock()
    obj2 = MagicMock()
    col_map = {'col1': obj1, 'col2': obj2}
    ctx._derived_table_alias_map['alias'] = col_map
    result = ctx._check_derived_table_alias_map('alias', 'col1')
    self.assertEqual(result, obj1)
    result = ctx._check_derived_table_alias_map('alias', 'col2')
    self.assertEqual(result, obj2)
    ctx = StatementBinderContext(MagicMock())
    result = ctx._check_derived_table_alias_map('alias', 'col3')
    self.assertEqual(result, None)

def test_search_all_alias_maps(self):
    ctx = StatementBinderContext(MagicMock())
    check_table_map = ctx._check_table_alias_map = MagicMock()
    check_derived_map = ctx._check_derived_table_alias_map = MagicMock()
    check_table_map.return_value = 'col_obj'
    ctx._table_alias_map['alias'] = 'col_name'
    ctx._derived_table_alias_map = {}
    result = ctx._search_all_alias_maps('col_name')
    check_table_map.assert_called_once_with('alias', 'col_name')
    check_derived_map.assert_not_called()
    self.assertEqual(result, ('alias', 'col_obj'))
    check_derived_map.return_value = 'derived_col_obj'
    ctx._table_alias_map = {}
    ctx._derived_table_alias_map['alias'] = 'col_name'
    result = ctx._search_all_alias_maps('col_name')
    check_table_map.assert_called_once_with('alias', 'col_name')
    check_table_map.assert_called_once_with('alias', 'col_name')
    self.assertEqual(result, ('alias', 'derived_col_obj'))

def test_search_all_alias_raise_duplicate_error(self):
    with self.assertRaises(BinderError):
        ctx = StatementBinderContext(MagicMock())
        ctx._check_table_alias_map = MagicMock()
        ctx._check_derived_table_alias_map = MagicMock()
        ctx._table_alias_map['alias'] = 'col_name'
        ctx._derived_table_alias_map['alias'] = 'col_name'
        ctx._search_all_alias_maps('col_name')

@pytest.mark.notparallel
class CatalogManagerTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls) -> None:
        cls.mocks = [mock.patch('evadb.catalog.catalog_manager.SQLConfig'), mock.patch('evadb.catalog.catalog_manager.init_db')]
        for single_mock in cls.mocks:
            single_mock.start()
            cls.addClassCleanup(single_mock.stop)

    @mock.patch('evadb.catalog.catalog_manager.init_db')
    def test_catalog_bootstrap(self, mocked_db):
        x = CatalogManager(MagicMock())
        x._bootstrap_catalog()
        mocked_db.assert_called()

    @mock.patch('evadb.catalog.catalog_manager.CatalogManager.create_and_insert_table_catalog_entry')
    def test_create_multimedia_table_catalog_entry(self, mock):
        x = CatalogManager(MagicMock())
        name = 'myvideo'
        x.create_and_insert_multimedia_table_catalog_entry(name=name, format_type=FileFormatType.VIDEO)
        columns = get_video_table_column_definitions()
        mock.assert_called_once_with(TableInfo(name), columns, table_type=TableType.VIDEO_DATA)

    @mock.patch('evadb.catalog.catalog_manager.init_db')
    @mock.patch('evadb.catalog.catalog_manager.TableCatalogService')
    def test_insert_table_catalog_entry_should_create_table_and_columns(self, ds_mock, initdb_mock):
        catalog = CatalogManager(MagicMock())
        file_url = 'file1'
        table_name = 'name'
        columns = [ColumnCatalogEntry('c1', ColumnType.INTEGER)]
        catalog.insert_table_catalog_entry(table_name, file_url, columns)
        ds_mock.return_value.insert_entry.assert_called_with(table_name, file_url, identifier_column='id', table_type=TableType.VIDEO_DATA, column_list=[ANY] + columns)

    @mock.patch('evadb.catalog.catalog_manager.init_db')
    @mock.patch('evadb.catalog.catalog_manager.TableCatalogService')
    def test_get_table_catalog_entry_when_table_exists(self, ds_mock, initdb_mock):
        catalog = CatalogManager(MagicMock())
        table_name = 'name'
        database_name = 'database'
        row_id = 1
        table_obj = MagicMock(row_id=row_id)
        ds_mock.return_value.get_entry_by_name.return_value = table_obj
        actual = catalog.get_table_catalog_entry(table_name, database_name)
        ds_mock.return_value.get_entry_by_name.assert_called_with(database_name, table_name)
        self.assertEqual(actual.row_id, row_id)

    @mock.patch('evadb.catalog.catalog_manager.init_db')
    @mock.patch('evadb.catalog.catalog_manager.TableCatalogService')
    @mock.patch('evadb.catalog.catalog_manager.ColumnCatalogService')
    def test_get_table_catalog_entry_when_table_doesnot_exists(self, dcs_mock, ds_mock, initdb_mock):
        catalog = CatalogManager(MagicMock())
        table_name = 'name'
        database_name = 'database'
        table_obj = None
        ds_mock.return_value.get_entry_by_name.return_value = table_obj
        actual = catalog.get_table_catalog_entry(table_name, database_name)
        ds_mock.return_value.get_entry_by_name.assert_called_with(database_name, table_name)
        dcs_mock.return_value.filter_entries_by_table_id.assert_not_called()
        self.assertEqual(actual, table_obj)

    @mock.patch('evadb.catalog.catalog_manager.FunctionCatalogService')
    @mock.patch('evadb.catalog.catalog_manager.FunctionIOCatalogService')
    @mock.patch('evadb.catalog.catalog_manager.FunctionMetadataCatalogService')
    @mock.patch('evadb.catalog.catalog_manager.get_file_checksum')
    def test_insert_function(self, checksum_mock, functionmetadata_mock, functionio_mock, function_mock):
        catalog = CatalogManager(MagicMock())
        function_io_list = [MagicMock()]
        function_metadata_list = [MagicMock()]
        actual = catalog.insert_function_catalog_entry('function', 'sample.py', 'classification', function_io_list, function_metadata_list)
        function_mock.return_value.insert_entry.assert_called_with('function', 'sample.py', 'classification', checksum_mock.return_value, function_io_list, function_metadata_list)
        checksum_mock.assert_called_with('sample.py')
        self.assertEqual(actual, function_mock.return_value.insert_entry.return_value)

    @mock.patch('evadb.catalog.catalog_manager.FunctionCatalogService')
    def test_get_function_catalog_entry_by_name(self, function_mock):
        catalog = CatalogManager(MagicMock())
        actual = catalog.get_function_catalog_entry_by_name('name')
        function_mock.return_value.get_entry_by_name.assert_called_with('name')
        self.assertEqual(actual, function_mock.return_value.get_entry_by_name.return_value)

    @mock.patch('evadb.catalog.catalog_manager.FunctionCatalogService')
    def test_delete_function(self, function_mock):
        CatalogManager(MagicMock()).delete_function_catalog_entry_by_name('name')
        function_mock.return_value.delete_entry_by_name.assert_called_with('name')

    @mock.patch('evadb.catalog.catalog_manager.FunctionIOCatalogService')
    def test_get_function_outputs(self, function_mock):
        mock_func = function_mock.return_value.get_output_entries_by_function_id
        function_obj = MagicMock(spec=FunctionCatalogEntry)
        CatalogManager(MagicMock()).get_function_io_catalog_output_entries(function_obj)
        mock_func.assert_called_once_with(function_obj.row_id)

    @mock.patch('evadb.catalog.catalog_manager.FunctionIOCatalogService')
    def test_get_function_inputs(self, function_mock):
        mock_func = function_mock.return_value.get_input_entries_by_function_id
        function_obj = MagicMock(spec=FunctionCatalogEntry)
        CatalogManager(MagicMock()).get_function_io_catalog_input_entries(function_obj)
        mock_func.assert_called_once_with(function_obj.row_id)

@classmethod
def setUpClass(cls) -> None:
    cls.mocks = [mock.patch('evadb.catalog.catalog_manager.SQLConfig'), mock.patch('evadb.catalog.catalog_manager.init_db')]
    for single_mock in cls.mocks:
        single_mock.start()
        cls.addClassCleanup(single_mock.stop)

@mock.patch('evadb.catalog.catalog_manager.init_db')
def test_catalog_bootstrap(self, mocked_db):
    x = CatalogManager(MagicMock())
    x._bootstrap_catalog()
    mocked_db.assert_called()

@mock.patch('evadb.catalog.catalog_manager.CatalogManager.create_and_insert_table_catalog_entry')
def test_create_multimedia_table_catalog_entry(self, mock):
    x = CatalogManager(MagicMock())
    name = 'myvideo'
    x.create_and_insert_multimedia_table_catalog_entry(name=name, format_type=FileFormatType.VIDEO)
    columns = get_video_table_column_definitions()
    mock.assert_called_once_with(TableInfo(name), columns, table_type=TableType.VIDEO_DATA)

@mock.patch('evadb.catalog.catalog_manager.init_db')
@mock.patch('evadb.catalog.catalog_manager.TableCatalogService')
def test_insert_table_catalog_entry_should_create_table_and_columns(self, ds_mock, initdb_mock):
    catalog = CatalogManager(MagicMock())
    file_url = 'file1'
    table_name = 'name'
    columns = [ColumnCatalogEntry('c1', ColumnType.INTEGER)]
    catalog.insert_table_catalog_entry(table_name, file_url, columns)
    ds_mock.return_value.insert_entry.assert_called_with(table_name, file_url, identifier_column='id', table_type=TableType.VIDEO_DATA, column_list=[ANY] + columns)

@mock.patch('evadb.catalog.catalog_manager.init_db')
@mock.patch('evadb.catalog.catalog_manager.TableCatalogService')
def test_get_table_catalog_entry_when_table_exists(self, ds_mock, initdb_mock):
    catalog = CatalogManager(MagicMock())
    table_name = 'name'
    database_name = 'database'
    row_id = 1
    table_obj = MagicMock(row_id=row_id)
    ds_mock.return_value.get_entry_by_name.return_value = table_obj
    actual = catalog.get_table_catalog_entry(table_name, database_name)
    ds_mock.return_value.get_entry_by_name.assert_called_with(database_name, table_name)
    self.assertEqual(actual.row_id, row_id)

@mock.patch('evadb.catalog.catalog_manager.init_db')
@mock.patch('evadb.catalog.catalog_manager.TableCatalogService')
@mock.patch('evadb.catalog.catalog_manager.ColumnCatalogService')
def test_get_table_catalog_entry_when_table_doesnot_exists(self, dcs_mock, ds_mock, initdb_mock):
    catalog = CatalogManager(MagicMock())
    table_name = 'name'
    database_name = 'database'
    table_obj = None
    ds_mock.return_value.get_entry_by_name.return_value = table_obj
    actual = catalog.get_table_catalog_entry(table_name, database_name)
    ds_mock.return_value.get_entry_by_name.assert_called_with(database_name, table_name)
    dcs_mock.return_value.filter_entries_by_table_id.assert_not_called()
    self.assertEqual(actual, table_obj)

@mock.patch('evadb.catalog.catalog_manager.FunctionCatalogService')
@mock.patch('evadb.catalog.catalog_manager.FunctionIOCatalogService')
@mock.patch('evadb.catalog.catalog_manager.FunctionMetadataCatalogService')
@mock.patch('evadb.catalog.catalog_manager.get_file_checksum')
def test_insert_function(self, checksum_mock, functionmetadata_mock, functionio_mock, function_mock):
    catalog = CatalogManager(MagicMock())
    function_io_list = [MagicMock()]
    function_metadata_list = [MagicMock()]
    actual = catalog.insert_function_catalog_entry('function', 'sample.py', 'classification', function_io_list, function_metadata_list)
    function_mock.return_value.insert_entry.assert_called_with('function', 'sample.py', 'classification', checksum_mock.return_value, function_io_list, function_metadata_list)
    checksum_mock.assert_called_with('sample.py')
    self.assertEqual(actual, function_mock.return_value.insert_entry.return_value)

@mock.patch('evadb.catalog.catalog_manager.FunctionCatalogService')
def test_get_function_catalog_entry_by_name(self, function_mock):
    catalog = CatalogManager(MagicMock())
    actual = catalog.get_function_catalog_entry_by_name('name')
    function_mock.return_value.get_entry_by_name.assert_called_with('name')
    self.assertEqual(actual, function_mock.return_value.get_entry_by_name.return_value)

@mock.patch('evadb.catalog.catalog_manager.FunctionCatalogService')
def test_delete_function(self, function_mock):
    CatalogManager(MagicMock()).delete_function_catalog_entry_by_name('name')
    function_mock.return_value.delete_entry_by_name.assert_called_with('name')

@mock.patch('evadb.catalog.catalog_manager.FunctionIOCatalogService')
def test_get_function_outputs(self, function_mock):
    mock_func = function_mock.return_value.get_output_entries_by_function_id
    function_obj = MagicMock(spec=FunctionCatalogEntry)
    CatalogManager(MagicMock()).get_function_io_catalog_output_entries(function_obj)
    mock_func.assert_called_once_with(function_obj.row_id)

@mock.patch('evadb.catalog.catalog_manager.FunctionIOCatalogService')
def test_get_function_inputs(self, function_mock):
    mock_func = function_mock.return_value.get_input_entries_by_function_id
    function_obj = MagicMock(spec=FunctionCatalogEntry)
    CatalogManager(MagicMock()).get_function_io_catalog_input_entries(function_obj)
    mock_func.assert_called_once_with(function_obj.row_id)

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

@pytest.mark.notparallel
class MySQLNativeStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_mysql_params(self):
        return {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '3306', 'database': 'evadb'}

    def setUp(self):
        connection_params = self.get_mysql_params()
        self.evadb = get_evadb_for_testing()
        sys.modules['mysql'] = MagicMock()
        sys.modules['mysql.connector'] = MagicMock()
        self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
        self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
        self.execute_native_query_patcher = patch('evadb.third_party.databases.mysql.mysql_handler.MysqlHandler.execute_native_query')
        self.execute_native_query_mock = self.execute_native_query_patcher.start()
        self.connect_patcher = patch('evadb.third_party.databases.mysql.mysql_handler.MysqlHandler.connect')
        self.connect_mock = self.connect_patcher.start()
        self.disconnect_patcher = patch('evadb.third_party.databases.mysql.mysql_handler.MysqlHandler.disconnect')
        self.disconnect_mock = self.disconnect_patcher.start()
        self.execute_native_query_mock.return_value = NativeQueryResponse()
        self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='mysql', params=connection_params, row_id=1)

    def tearDown(self):
        self.get_database_catalog_entry_patcher.stop()
        self.execute_native_query_patcher.stop()
        self.connect_patcher.stop()
        self.disconnect_patcher.stop()

    def test_execute_mysql_select_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_mysql_insert_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                INSERT INTO test_table (\n                    name, age, comment\n                ) VALUES (\n                    'val', 5, 'testing'\n                )\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_mysql_update_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                UPDATE test_table\n                SET comment = 'update'\n                WHERE age > 5\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_mysql_delete_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DELETE FROM test_table\n                WHERE age < 5\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

def setUp(self):
    connection_params = self.get_mysql_params()
    self.evadb = get_evadb_for_testing()
    sys.modules['mysql'] = MagicMock()
    sys.modules['mysql.connector'] = MagicMock()
    self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
    self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
    self.execute_native_query_patcher = patch('evadb.third_party.databases.mysql.mysql_handler.MysqlHandler.execute_native_query')
    self.execute_native_query_mock = self.execute_native_query_patcher.start()
    self.connect_patcher = patch('evadb.third_party.databases.mysql.mysql_handler.MysqlHandler.connect')
    self.connect_mock = self.connect_patcher.start()
    self.disconnect_patcher = patch('evadb.third_party.databases.mysql.mysql_handler.MysqlHandler.disconnect')
    self.disconnect_mock = self.disconnect_patcher.start()
    self.execute_native_query_mock.return_value = NativeQueryResponse()
    self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='mysql', params=connection_params, row_id=1)

@pytest.mark.notparallel
class SnowFlakeNativeStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_snowflake_params(self):
        return {'database': 'evadb.db'}

    def setUp(self):
        connection_params = self.get_snowflake_params()
        self.evadb = get_evadb_for_testing()
        self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
        self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
        self.execute_native_query_patcher = patch('evadb.third_party.databases.snowflake.snowflake_handler.SnowFlakeDbHandler.execute_native_query')
        self.execute_native_query_mock = self.execute_native_query_patcher.start()
        self.connect_patcher = patch('evadb.third_party.databases.snowflake.snowflake_handler.SnowFlakeDbHandler.connect')
        self.connect_mock = self.connect_patcher.start()
        self.disconnect_patcher = patch('evadb.third_party.databases.snowflake.snowflake_handler.SnowFlakeDbHandler.disconnect')
        self.disconnect_mock = self.disconnect_patcher.start()
        self.execute_native_query_mock.return_value = NativeQueryResponse()
        self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='snowflake', params=connection_params, row_id=1)

    def tearDown(self):
        self.get_database_catalog_entry_patcher.stop()
        self.execute_native_query_patcher.stop()
        self.connect_patcher.stop()
        self.disconnect_patcher.stop()

    def test_execute_snowflake_select_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_snowflake_insert_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                INSERT INTO test_table (\n                    name, age, comment\n                ) VALUES (\n                    'val', 5, 'testing'\n                )\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_snowflake_update_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                UPDATE test_table\n                SET comment = 'update'\n                WHERE age > 5\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_snowflake_delete_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DELETE FROM test_table\n                WHERE age < 5\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

def setUp(self):
    connection_params = self.get_snowflake_params()
    self.evadb = get_evadb_for_testing()
    self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
    self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
    self.execute_native_query_patcher = patch('evadb.third_party.databases.snowflake.snowflake_handler.SnowFlakeDbHandler.execute_native_query')
    self.execute_native_query_mock = self.execute_native_query_patcher.start()
    self.connect_patcher = patch('evadb.third_party.databases.snowflake.snowflake_handler.SnowFlakeDbHandler.connect')
    self.connect_mock = self.connect_patcher.start()
    self.disconnect_patcher = patch('evadb.third_party.databases.snowflake.snowflake_handler.SnowFlakeDbHandler.disconnect')
    self.disconnect_mock = self.disconnect_patcher.start()
    self.execute_native_query_mock.return_value = NativeQueryResponse()
    self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='snowflake', params=connection_params, row_id=1)

@pytest.mark.notparallel
class PostgresNativeStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_postgres_params(self):
        return {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}

    def setUp(self):
        connection_params = self.get_postgres_params()
        self.evadb = get_evadb_for_testing()
        sys.modules['psycopg2'] = MagicMock()
        self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
        self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
        self.execute_native_query_patcher = patch('evadb.third_party.databases.postgres.postgres_handler.PostgresHandler.execute_native_query')
        self.execute_native_query_mock = self.execute_native_query_patcher.start()
        self.connect_patcher = patch('evadb.third_party.databases.postgres.postgres_handler.PostgresHandler.connect')
        self.connect_mock = self.connect_patcher.start()
        self.disconnect_patcher = patch('evadb.third_party.databases.postgres.postgres_handler.PostgresHandler.disconnect')
        self.disconnect_mock = self.disconnect_patcher.start()
        self.execute_native_query_mock.return_value = NativeQueryResponse()
        self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='postgres', params=connection_params, row_id=1)

    def tearDown(self):
        self.get_database_catalog_entry_patcher.stop()
        self.execute_native_query_patcher.stop()
        self.connect_patcher.stop()
        self.disconnect_patcher.stop()

    def test_execute_postgres_select_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_postgres_insert_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                INSERT INTO test_table (\n                    name, age, comment\n                ) VALUES (\n                    'val', 5, 'testing'\n                )\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_postgres_update_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                UPDATE test_table\n                SET comment = 'update'\n                WHERE age > 5\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_postgres_delete_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DELETE FROM test_table\n                WHERE age < 5\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

def setUp(self):
    connection_params = self.get_postgres_params()
    self.evadb = get_evadb_for_testing()
    sys.modules['psycopg2'] = MagicMock()
    self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
    self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
    self.execute_native_query_patcher = patch('evadb.third_party.databases.postgres.postgres_handler.PostgresHandler.execute_native_query')
    self.execute_native_query_mock = self.execute_native_query_patcher.start()
    self.connect_patcher = patch('evadb.third_party.databases.postgres.postgres_handler.PostgresHandler.connect')
    self.connect_mock = self.connect_patcher.start()
    self.disconnect_patcher = patch('evadb.third_party.databases.postgres.postgres_handler.PostgresHandler.disconnect')
    self.disconnect_mock = self.disconnect_patcher.start()
    self.execute_native_query_mock.return_value = NativeQueryResponse()
    self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='postgres', params=connection_params, row_id=1)

@pytest.mark.notparallel
class ClickHouseNativeStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_clickhouse_params(self):
        return {'database': 'evadb.db'}

    def setUp(self):
        connection_params = self.get_clickhouse_params()
        self.evadb = get_evadb_for_testing()
        self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
        self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
        self.execute_native_query_patcher = patch('evadb.third_party.databases.clickhouse.clickhouse_handler.ClickHouseHandler.execute_native_query')
        self.execute_native_query_mock = self.execute_native_query_patcher.start()
        self.connect_patcher = patch('evadb.third_party.databases.clickhouse.clickhouse_handler.ClickHouseHandler.connect')
        self.connect_mock = self.connect_patcher.start()
        self.disconnect_patcher = patch('evadb.third_party.databases.clickhouse.clickhouse_handler.ClickHouseHandler.disconnect')
        self.disconnect_mock = self.disconnect_patcher.start()
        self.execute_native_query_mock.return_value = NativeQueryResponse()
        self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='clickhouse', params=connection_params, row_id=1)

    def tearDown(self):
        self.get_database_catalog_entry_patcher.stop()
        self.execute_native_query_patcher.stop()
        self.connect_patcher.stop()
        self.disconnect_patcher.stop()

    def test_execute_clickhouse_select_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_clickhouse_insert_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                INSERT INTO test_table (\n                    name, age, comment\n                ) VALUES (\n                    'val', 5, 'testing'\n                )\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_clickhouse_update_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                UPDATE test_table\n                SET comment = 'update'\n                WHERE age > 5\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_clickhouse_delete_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DELETE FROM test_table\n                WHERE age < 5\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

def setUp(self):
    connection_params = self.get_clickhouse_params()
    self.evadb = get_evadb_for_testing()
    self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
    self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
    self.execute_native_query_patcher = patch('evadb.third_party.databases.clickhouse.clickhouse_handler.ClickHouseHandler.execute_native_query')
    self.execute_native_query_mock = self.execute_native_query_patcher.start()
    self.connect_patcher = patch('evadb.third_party.databases.clickhouse.clickhouse_handler.ClickHouseHandler.connect')
    self.connect_mock = self.connect_patcher.start()
    self.disconnect_patcher = patch('evadb.third_party.databases.clickhouse.clickhouse_handler.ClickHouseHandler.disconnect')
    self.disconnect_mock = self.disconnect_patcher.start()
    self.execute_native_query_mock.return_value = NativeQueryResponse()
    self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='clickhouse', params=connection_params, row_id=1)

@pytest.mark.notparallel
class SQLiteNativeStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_sqlite_params(self):
        return {'database': 'evadb.db'}

    def setUp(self):
        connection_params = self.get_sqlite_params()
        self.evadb = get_evadb_for_testing()
        self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
        self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
        self.execute_native_query_patcher = patch('evadb.third_party.databases.sqlite.sqlite_handler.SQLiteHandler.execute_native_query')
        self.execute_native_query_mock = self.execute_native_query_patcher.start()
        self.connect_patcher = patch('evadb.third_party.databases.sqlite.sqlite_handler.SQLiteHandler.connect')
        self.connect_mock = self.connect_patcher.start()
        self.disconnect_patcher = patch('evadb.third_party.databases.sqlite.sqlite_handler.SQLiteHandler.disconnect')
        self.disconnect_mock = self.disconnect_patcher.start()
        self.execute_native_query_mock.return_value = NativeQueryResponse()
        self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='sqlite', params=connection_params, row_id=1)

    def tearDown(self):
        self.get_database_catalog_entry_patcher.stop()
        self.execute_native_query_patcher.stop()
        self.connect_patcher.stop()
        self.disconnect_patcher.stop()

    def test_execute_sqlite_select_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_sqlite_insert_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                INSERT INTO test_table (\n                    name, age, comment\n                ) VALUES (\n                    'val', 5, 'testing'\n                )\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_sqlite_update_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                UPDATE test_table\n                SET comment = 'update'\n                WHERE age > 5\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_sqlite_delete_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DELETE FROM test_table\n                WHERE age < 5\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

def setUp(self):
    connection_params = self.get_sqlite_params()
    self.evadb = get_evadb_for_testing()
    self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
    self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
    self.execute_native_query_patcher = patch('evadb.third_party.databases.sqlite.sqlite_handler.SQLiteHandler.execute_native_query')
    self.execute_native_query_mock = self.execute_native_query_patcher.start()
    self.connect_patcher = patch('evadb.third_party.databases.sqlite.sqlite_handler.SQLiteHandler.connect')
    self.connect_mock = self.connect_patcher.start()
    self.disconnect_patcher = patch('evadb.third_party.databases.sqlite.sqlite_handler.SQLiteHandler.disconnect')
    self.disconnect_mock = self.disconnect_patcher.start()
    self.execute_native_query_mock.return_value = NativeQueryResponse()
    self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='sqlite', params=connection_params, row_id=1)

@pytest.mark.notparallel
class MariaDbStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_mariadb_params(self):
        return {'user': 'eva', 'password': 'password', 'database': 'evadb'}

    def setUp(self):
        connection_params = self.get_mariadb_params()
        self.evadb = get_evadb_for_testing()
        sys.modules['mariadb'] = MagicMock()
        self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
        self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
        self.execute_native_query_patcher = patch('evadb.third_party.databases.mariadb.mariadb_handler.MariaDbHandler.execute_native_query')
        self.execute_native_query_mock = self.execute_native_query_patcher.start()
        self.connect_patcher = patch('evadb.third_party.databases.mariadb.mariadb_handler.MariaDbHandler.connect')
        self.connect_mock = self.connect_patcher.start()
        self.disconnect_patcher = patch('evadb.third_party.databases.mariadb.mariadb_handler.MariaDbHandler.disconnect')
        self.disconnect_mock = self.disconnect_patcher.start()
        self.execute_native_query_mock.return_value = NativeQueryResponse()
        self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='mariadb', params=connection_params, row_id=1)

    def tearDown(self):
        self.get_database_catalog_entry_patcher.stop()
        self.execute_native_query_patcher.stop()
        self.connect_patcher.stop()
        self.disconnect_patcher.stop()

    def test_execute_mariadb_select_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_mariadb_insert_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                INSERT INTO test_table (\n                    name, age, comment\n                ) VALUES (\n                    'val', 5, 'testing'\n                )\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_mariadb_update_query(self):
        execute_query_fetch_all(self.evadb, "USE test_data_source {\n                UPDATE test_table\n                SET comment = 'update'\n                WHERE age > 5\n            }")
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

    def test_execute_mariadb_delete_query(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DELETE FROM test_table\n                WHERE age < 5\n            }')
        self.connect_mock.assert_called_once()
        self.execute_native_query_mock.assert_called_once()
        self.get_database_catalog_entry_mock.assert_called_once()
        self.disconnect_mock.assert_called_once()

def setUp(self):
    connection_params = self.get_mariadb_params()
    self.evadb = get_evadb_for_testing()
    sys.modules['mariadb'] = MagicMock()
    self.get_database_catalog_entry_patcher = patch('evadb.catalog.catalog_manager.CatalogManager.get_database_catalog_entry')
    self.get_database_catalog_entry_mock = self.get_database_catalog_entry_patcher.start()
    self.execute_native_query_patcher = patch('evadb.third_party.databases.mariadb.mariadb_handler.MariaDbHandler.execute_native_query')
    self.execute_native_query_mock = self.execute_native_query_patcher.start()
    self.connect_patcher = patch('evadb.third_party.databases.mariadb.mariadb_handler.MariaDbHandler.connect')
    self.connect_mock = self.connect_patcher.start()
    self.disconnect_patcher = patch('evadb.third_party.databases.mariadb.mariadb_handler.MariaDbHandler.disconnect')
    self.disconnect_mock = self.disconnect_patcher.start()
    self.execute_native_query_mock.return_value = NativeQueryResponse()
    self.get_database_catalog_entry_mock.return_value = DatabaseCatalogEntry(name='test_data_source', engine='mariadb', params=connection_params, row_id=1)

def execute_statement(evadb: EvaDBDatabase, stmt: AbstractStatement, do_not_raise_exceptions: bool=False, do_not_print_exceptions: bool=False, **kwargs) -> Iterator[Batch]:
    plan_generator = kwargs.get('plan_generator', PlanGenerator(evadb))
    if not isinstance(stmt, SKIP_BINDER_AND_OPTIMIZER_STATEMENTS):
        StatementBinder(StatementBinderContext(evadb.catalog)).bind(stmt)
        logical_plan = StatementToPlanConverter().visit(stmt)
        physical_plan = plan_generator.build(logical_plan)
    else:
        physical_plan = stmt
    output = PlanExecutor(evadb, physical_plan).execute_plan(do_not_raise_exceptions, do_not_print_exceptions)
    if output:
        batch_list = list(output)
        return Batch.concat(batch_list, copy=False)

class StatementToPlanConverter:

    def __init__(self):
        self._plan = None

    def visit_table_ref(self, table_ref: TableRef):
        """Bind table ref object and convert to LogicalGet, LogicalJoin,
            LogicalFunctionScan, or LogicalQueryDerivedGet

        Arguments:
            table {TableRef} - - [Input table ref object created by the parser]
        """
        if table_ref.is_table_atom():
            catalog_entry = table_ref.table.table_obj
            self._plan = LogicalGet(table_ref, catalog_entry, table_ref.alias, chunk_params=table_ref.chunk_params)
        elif table_ref.is_table_valued_expr():
            tve = table_ref.table_valued_expr
            if tve.func_expr.name.lower() == str(FunctionType.EXTRACT_OBJECT).lower():
                self._plan = LogicalExtractObject(detector=tve.func_expr.children[1], tracker=tve.func_expr.children[2], alias=table_ref.alias, do_unnest=tve.do_unnest)
            else:
                self._plan = LogicalFunctionScan(func_expr=tve.func_expr, alias=table_ref.alias, do_unnest=tve.do_unnest)
        elif table_ref.is_select():
            self.visit_select(table_ref.select_statement)
            child_plan = self._plan
            self._plan = LogicalQueryDerivedGet(table_ref.alias)
            self._plan.append_child(child_plan)
        elif table_ref.is_join():
            join_node = table_ref.join_node
            join_plan = LogicalJoin(join_type=join_node.join_type, join_predicate=join_node.predicate)
            self.visit_table_ref(join_node.left)
            join_plan.append_child(self._plan)
            self.visit_table_ref(join_node.right)
            join_plan.append_child(self._plan)
            self._plan = join_plan
        if table_ref.sample_freq:
            self._visit_sample(table_ref.sample_freq, table_ref.sample_type)

    def visit_select(self, statement: SelectStatement):
        """converter for select statement

        Arguments:
            statement {SelectStatement} - - [input select statement]
        """
        col_with_func_exprs = []
        if statement.orderby_list and statement.groupby_clause is None:
            projection_cols = []
            for col in statement.target_list:
                if isinstance(col, FunctionExpression):
                    col_with_func_exprs.append(col)
                    projection_cols.extend(get_bound_func_expr_outputs_as_tuple_value_expr(col))
                else:
                    projection_cols.append(col)
            statement.target_list = projection_cols
        table_ref = statement.from_table
        if not table_ref and col_with_func_exprs:
            self._visit_projection(col_with_func_exprs)
        else:
            for col in col_with_func_exprs:
                tve = TableValuedExpression(col)
                if table_ref:
                    table_ref = TableRef(JoinNode(table_ref, TableRef(tve, alias=col.alias), join_type=JoinType.LATERAL_JOIN))
            statement.from_table = table_ref
        if table_ref is not None:
            self.visit_table_ref(table_ref)
            predicate = statement.where_clause
            if predicate is not None:
                self._visit_select_predicate(predicate)
            if statement.groupby_clause is not None:
                self._visit_groupby(statement.groupby_clause)
        if statement.orderby_list is not None:
            self._visit_orderby(statement.orderby_list)
        if statement.limit_count is not None:
            self._visit_limit(statement.limit_count)
        if statement.target_list is not None:
            self._visit_projection(statement.target_list)
        if statement.union_link is not None:
            self._visit_union(statement.union_link, statement.union_all)

    def _visit_sample(self, sample_freq, sample_type):
        sample_opr = LogicalSample(sample_freq, sample_type)
        sample_opr.append_child(self._plan)
        self._plan = sample_opr

    def _visit_groupby(self, groupby_clause):
        groupby_opr = LogicalGroupBy(groupby_clause)
        groupby_opr.append_child(self._plan)
        self._plan = groupby_opr

    def _visit_orderby(self, orderby_list):
        orderby_opr = LogicalOrderBy(orderby_list)
        orderby_opr.append_child(self._plan)
        self._plan = orderby_opr

    def _visit_limit(self, limit_count):
        limit_opr = LogicalLimit(limit_count)
        limit_opr.append_child(self._plan)
        self._plan = limit_opr

    def _visit_union(self, target, all):
        left_child_plan = self._plan
        self.visit_select(target)
        right_child_plan = self._plan
        self._plan = LogicalUnion(all=all)
        self._plan.append_child(left_child_plan)
        self._plan.append_child(right_child_plan)

    def _visit_projection(self, select_columns):
        projection_opr = LogicalProject(select_columns)
        if self._plan is not None:
            projection_opr.append_child(self._plan)
        self._plan = projection_opr

    def _visit_select_predicate(self, predicate: AbstractExpression):
        filter_opr = LogicalFilter(predicate)
        filter_opr.append_child(self._plan)
        self._plan = filter_opr

    def visit_insert(self, statement: AbstractStatement):
        """Converter for parsed insert statement

        Arguments:
            statement {AbstractStatement} - - [input insert statement]
        """
        insert_data_opr = LogicalInsert(statement.table_ref, statement.column_list, statement.value_list)
        self._plan = insert_data_opr
        '\n        table_ref = statement.table\n        table_metainfo = bind_dataset(table_ref.table)\n        if table_metainfo is None:\n            # Create a new metadata object\n            table_metainfo = create_video_metadata(table_ref.table.table_name)\n\n        # populate self._column_map\n        self._populate_column_map(table_metainfo)\n\n        # Bind column_list\n        bind_columns_expr(statement.column_list, self._column_map)\n\n        # Nothing to be done for values as we add support for other variants of\n        # insert we will handle them\n        value_list = statement.value_list\n\n        # Ready to create Logical node\n        insert_opr = LogicalInsert(\n            table_ref, table_metainfo, statement.column_list, value_list)\n        self._plan = insert_opr\n        '

    def visit_create(self, statement: AbstractStatement):
        """Converter for parsed insert Statement

        Arguments:
            statement {AbstractStatement} - - [Create statement]
        """
        table_info = statement.table_info
        if table_info is None:
            logger.error('Missing Table Name In Create Statement')
        create_opr = LogicalCreate(table_info, statement.column_list, statement.if_not_exists)
        if statement.query is not None:
            self.visit_select(statement.query)
            create_opr.append_child(self._plan)
        self._plan = create_opr

    def visit_rename(self, statement: RenameTableStatement):
        """Converter for parsed rename statement
        Arguments:
            statement(RenameTableStatement): [Rename statement]
        """
        rename_opr = LogicalRename(statement.old_table_ref, statement.new_table_name)
        self._plan = rename_opr

    def visit_create_function(self, statement: CreateFunctionStatement):
        """Converter for parsed create function statement

        Arguments:
            statement {CreateFunctionStatement} - - CreateFunctionStatement
        """
        annotated_inputs = column_definition_to_function_io(statement.inputs, True)
        annotated_outputs = column_definition_to_function_io(statement.outputs, False)
        annotated_metadata = metadata_definition_to_function_metadata(statement.metadata)
        create_function_opr = LogicalCreateFunction(statement.name, statement.or_replace, statement.if_not_exists, annotated_inputs, annotated_outputs, statement.impl_path, statement.function_type, annotated_metadata)
        if statement.query is not None:
            self.visit_select(statement.query)
            create_function_opr.append_child(self._plan)
        self._plan = create_function_opr

    def visit_drop_object(self, statement: DropObjectStatement):
        self._plan = LogicalDropObject(statement.object_type, statement.name, statement.if_exists)

    def visit_load_data(self, statement: LoadDataStatement):
        """Converter for parsed load data statement
        Arguments:
            statement(LoadDataStatement): [Load data statement]
        """
        load_data_opr = LogicalLoadData(statement.table_info, statement.path, statement.column_list, statement.file_options)
        self._plan = load_data_opr

    def visit_show(self, statement: ShowStatement):
        show_opr = LogicalShow(statement.show_type, statement.show_val)
        self._plan = show_opr

    def visit_explain(self, statement: ExplainStatement):
        explain_opr = LogicalExplain([self.visit(statement.explainable_stmt)])
        self._plan = explain_opr

    def visit_create_index(self, statement: CreateIndexStatement):
        create_index_opr = LogicalCreateIndex(statement.name, statement.if_not_exists, statement.table_ref, statement.col_list, statement.vector_store_type, statement.project_expr_list, statement.index_def)
        self._plan = create_index_opr

    def visit_delete(self, statement: DeleteTableStatement):
        delete_opr = LogicalDelete(statement.table_ref, statement.where_clause)
        self._plan = delete_opr

    def visit(self, statement: AbstractStatement):
        """Based on the instance of the statement the corresponding
           visit is called.
           The logic is hidden from client.

        Arguments:
            statement {AbstractStatement} - - [Input statement]
        """
        if isinstance(statement, SelectStatement):
            self.visit_select(statement)
        elif isinstance(statement, InsertTableStatement):
            self.visit_insert(statement)
        elif isinstance(statement, CreateTableStatement):
            self.visit_create(statement)
        elif isinstance(statement, RenameTableStatement):
            self.visit_rename(statement)
        elif isinstance(statement, CreateFunctionStatement):
            self.visit_create_function(statement)
        elif isinstance(statement, DropObjectStatement):
            self.visit_drop_object(statement)
        elif isinstance(statement, LoadDataStatement):
            self.visit_load_data(statement)
        elif isinstance(statement, ShowStatement):
            self.visit_show(statement)
        elif isinstance(statement, ExplainStatement):
            self.visit_explain(statement)
        elif isinstance(statement, CreateIndexStatement):
            self.visit_create_index(statement)
        elif isinstance(statement, DeleteTableStatement):
            self.visit_delete(statement)
        return self._plan

    @property
    def plan(self):
        return self._plan

def visit(self, statement: AbstractStatement):
    """Based on the instance of the statement the corresponding
           visit is called.
           The logic is hidden from client.

        Arguments:
            statement {AbstractStatement} - - [Input statement]
        """
    if isinstance(statement, SelectStatement):
        self.visit_select(statement)
    elif isinstance(statement, InsertTableStatement):
        self.visit_insert(statement)
    elif isinstance(statement, CreateTableStatement):
        self.visit_create(statement)
    elif isinstance(statement, RenameTableStatement):
        self.visit_rename(statement)
    elif isinstance(statement, CreateFunctionStatement):
        self.visit_create_function(statement)
    elif isinstance(statement, DropObjectStatement):
        self.visit_drop_object(statement)
    elif isinstance(statement, LoadDataStatement):
        self.visit_load_data(statement)
    elif isinstance(statement, ShowStatement):
        self.visit_show(statement)
    elif isinstance(statement, ExplainStatement):
        self.visit_explain(statement)
    elif isinstance(statement, CreateIndexStatement):
        self.visit_create_index(statement)
    elif isinstance(statement, DeleteTableStatement):
        self.visit_delete(statement)
    return self._plan

class LogicalCreateToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALCREATE)
        super().__init__(RuleType.LOGICAL_CREATE_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_CREATE_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalCreate, context: OptimizerContext):
        after = CreatePlan(before.video, before.column_list, before.if_not_exists)
        yield after

def apply(self, before: LogicalCreate, context: OptimizerContext):
    after = CreatePlan(before.video, before.column_list, before.if_not_exists)
    yield after

class LogicalCreateFunctionToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALCREATEFUNCTION)
        super().__init__(RuleType.LOGICAL_CREATE_FUNCTION_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_CREATE_FUNCTION_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalCreateFunction, context: OptimizerContext):
        after = CreateFunctionPlan(before.name, before.or_replace, before.if_not_exists, before.inputs, before.outputs, before.impl_path, before.function_type, before.metadata)
        yield after

def apply(self, before: LogicalCreateFunction, context: OptimizerContext):
    after = CreateFunctionPlan(before.name, before.or_replace, before.if_not_exists, before.inputs, before.outputs, before.impl_path, before.function_type, before.metadata)
    yield after

class LogicalCreateFunctionFromSelectToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALCREATEFUNCTION)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_CREATE_FUNCTION_FROM_SELECT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_CREATE_FUNCTION_FROM_SELECT_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalCreateFunction, context: OptimizerContext):
        after = CreateFunctionPlan(before.name, before.or_replace, before.if_not_exists, before.inputs, before.outputs, before.impl_path, before.function_type, before.metadata)
        for child in before.children:
            after.append_child(child)
        yield after

def apply(self, before: LogicalCreateFunction, context: OptimizerContext):
    after = CreateFunctionPlan(before.name, before.or_replace, before.if_not_exists, before.inputs, before.outputs, before.impl_path, before.function_type, before.metadata)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalDropObjectToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICAL_DROP_OBJECT)
        super().__init__(RuleType.LOGICAL_DROP_OBJECT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_DROP_OBJECT_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalDropObject, context: OptimizerContext):
        after = DropObjectPlan(before.object_type, before.name, before.if_exists)
        yield after

def apply(self, before: LogicalDropObject, context: OptimizerContext):
    after = DropObjectPlan(before.object_type, before.name, before.if_exists)
    yield after

class LogicalInsertToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALINSERT)
        super().__init__(RuleType.LOGICAL_INSERT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_INSERT_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalInsert, context: OptimizerContext):
        after = InsertPlan(before.table, before.column_list, before.value_list)
        yield after

def apply(self, before: LogicalInsert, context: OptimizerContext):
    after = InsertPlan(before.table, before.column_list, before.value_list)
    yield after

class LogicalLoadToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALLOADDATA)
        super().__init__(RuleType.LOGICAL_LOAD_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_LOAD_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalLoadData, context: OptimizerContext):
        after = LoadDataPlan(before.table_info, before.path, before.column_list, before.file_options)
        yield after

def apply(self, before: LogicalLoadData, context: OptimizerContext):
    after = LoadDataPlan(before.table_info, before.path, before.column_list, before.file_options)
    yield after

def get_ray_env_dict():
    if len(Context().gpus) > 0:
        max_gpu_id = max(Context().gpus) + 1
        return {'CUDA_VISIBLE_DEVICES': ','.join([str(n) for n in range(max_gpu_id)])}
    else:
        return {}

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

def get_column_catalog_entry(self, table_obj: TableCatalogEntry, col_name: str) -> ColumnCatalogEntry:
    col_obj = self._column_service.filter_entry_by_table_id_and_name(table_obj.row_id, col_name)
    if col_obj:
        return col_obj
    else:
        if col_name == VideoColumnName.audio:
            return ColumnCatalogEntry(col_name, ColumnType.NDARRAY, table_id=table_obj.row_id, table_name=table_obj.name)
        return None

def get_catalog_instance(db_uri: str):
    from evadb.catalog.catalog_manager import CatalogManager
    return CatalogManager(db_uri)

class DatabaseCatalog(BaseModel):
    """The `DatabaseCatalog` catalog stores information about all databases.
    `_row_id:` an autogenerated unique identifier.
    `_name:` the database name.
    `_engine:` database engine
    `_param:` parameters specific to the database engine
    """
    __tablename__ = 'database_catalog'
    _name = Column('name', String(100), unique=True)
    _engine = Column('engine', String(100))
    _params = Column('params', TextPickleType())

    def __init__(self, name: str, engine: str, params: dict):
        self._name = name
        self._engine = engine
        self._params = params

    def as_dataclass(self) -> 'DatabaseCatalogEntry':
        return DatabaseCatalogEntry(row_id=self._row_id, name=self._name, engine=self._engine, params=self._params)

def as_dataclass(self) -> 'DatabaseCatalogEntry':
    return DatabaseCatalogEntry(row_id=self._row_id, name=self._name, engine=self._engine, params=self._params)

def try_binding(catalog: Callable, stmt: AbstractStatement):
    StatementBinder(StatementBinderContext(catalog)).bind(stmt.copy())

