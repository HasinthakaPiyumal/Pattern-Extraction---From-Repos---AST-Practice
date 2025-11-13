# Cluster 21

class HuggingFaceTest(unittest.TestCase):

    def test_hugging_face_with_large_input(self):
        function_obj = MagicMock()
        function_obj.metadata = []
        text_summarization_model = TestTextHFModel(function_obj)
        large_text = pd.DataFrame([{'text': 'hello' * 4096}])
        try:
            text_summarization_model(large_text)
        except IndexError:
            self.fail('hugging face with large input raised IndexError.')

def test_hugging_face_with_large_input(self):
    function_obj = MagicMock()
    function_obj.metadata = []
    text_summarization_model = TestTextHFModel(function_obj)
    large_text = pd.DataFrame([{'text': 'hello' * 4096}])
    try:
        text_summarization_model(large_text)
    except IndexError:
        self.fail('hugging face with large input raised IndexError.')

@pytest.mark.notparallel
class SelectExecutorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        video_file_path = create_sample_video(NUM_FRAMES)
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(cls.evadb, load_query)
        load_functions_for_testing(cls.evadb)
        cls.table1 = create_table(cls.evadb, 'table1', 100, 3)
        cls.table2 = create_table(cls.evadb, 'table2', 500, 3)
        cls.table3 = create_table(cls.evadb, 'table3', 1000, 3)

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        file_remove('dummy.avi')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table1;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table2;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table3;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_should_load_and_sort_in_table(self):
        select_query = 'SELECT data, id FROM MyVideo ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_rows = [{'myvideo.id': i, 'myvideo.data': np.array(np.ones((32, 32, 3)) * i, dtype=np.uint8)} for i in range(NUM_FRAMES)]
        expected_batch = Batch(frames=pd.DataFrame(expected_rows))
        self.assertEqual(actual_batch, expected_batch)
        select_query = 'SELECT data, id FROM MyVideo ORDER BY id DESC;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_batch.reverse()
        self.assertEqual(actual_batch, expected_batch)

    def test_should_load_and_select_in_table(self):
        select_query = 'SELECT id FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_rows = [{'myvideo.id': i} for i in range(NUM_FRAMES)]
        expected_batch = Batch(frames=pd.DataFrame(expected_rows))
        self.assertEqual(actual_batch, expected_batch)
        select_query = 'SELECT * FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches())
        self.assertEqual([actual_batch], expected_batch)

    def test_should_raise_binder_error_on_native_datasource(self):
        select_query = 'SELECT * FROM test.MyVideo'
        self.assertRaises(BinderError, execute_query_fetch_all, self.evadb, select_query)

    def test_should_raise_binder_error_on_non_existent_column(self):
        select_query = 'SELECT b1 FROM table1;'
        with self.assertRaises(BinderError) as ctx:
            execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual("Cannot find column b1. Did you mean a1? The feasible columns are ['_row_id', 'a0', 'a1', 'a2'].", str(ctx.exception))

    def test_should_select_star_in_nested_query(self):
        select_query = 'SELECT * FROM (SELECT * FROM MyVideo) AS T;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches())[0]
        expected_batch.modify_column_alias('T')
        self.assertEqual(actual_batch, expected_batch)
        select_query = 'SELECT * FROM (SELECT id FROM MyVideo) AS T;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_rows = [{'T.id': i} for i in range(NUM_FRAMES)]
        expected_batch = Batch(frames=pd.DataFrame(expected_rows))
        self.assertEqual(actual_batch, expected_batch)

    @unittest.skip('Not supported in current version')
    def test_select_star_in_lateral_join(self):
        select_query = 'SELECT * FROM MyVideo JOIN LATERAL\n                          Yolo(data);'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(actual_batch.frames.columns, ['myvideo.id'])

    def test_should_throw_error_when_both_audio_and_video_selected(self):
        query = "LOAD VIDEO 'data/sample_videos/touchdown.mp4'\n                   INTO TOUCHDOWN1;"
        execute_query_fetch_all(self.evadb, query)
        select_query = 'SELECT id, audio, data FROM TOUCHDOWN1;'
        try:
            execute_query_fetch_all(self.evadb, select_query)
            self.fail("Didn't raise AssertionError")
        except AssertionError as e:
            self.assertEquals('Cannot query over both audio and video streams', e.args[0])

    def test_select_and_limit(self):
        select_query = 'SELECT * FROM MyVideo ORDER BY id LIMIT 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(num_frames=10, batch_size=5))
        self.assertEqual(len(actual_batch), len(expected_batch[0]))
        self.assertEqual(actual_batch, expected_batch[0])

    def test_select_and_aggregate(self):
        simple_aggregate_query = 'SELECT COUNT(*), AVG(id) FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, simple_aggregate_query)
        self.assertEqual(actual_batch.frames.iat[0, 0], 10)
        self.assertEqual(actual_batch.frames.iat[0, 1], 4.5)

    def test_select_and_iframe_sample(self):
        select_query = 'SELECT id FROM MyVideo SAMPLE IFRAMES 7 ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=range(0, NUM_FRAMES, 7)))
        expected_batch[0] = expected_batch[0].project(['myvideo.id'])
        self.assertEqual(len(actual_batch), len(expected_batch[0]))
        self.assertEqual(actual_batch, expected_batch[0])

    def test_select_and_iframe_sample_without_sampling_rate(self):
        select_query = 'SELECT id FROM MyVideo SAMPLE IFRAMES ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=range(0, NUM_FRAMES, 1)))
        expected_batch[0] = expected_batch[0].project(['myvideo.id'])
        self.assertEqual(len(actual_batch), len(expected_batch[0]))
        self.assertEqual(actual_batch, expected_batch[0])

    def test_select_and_groupby_first(self):
        segment_size = 3
        select_query = "SELECT FIRST(id), SEGMENT(data) FROM MyVideo GROUP BY '{} frames';".format(segment_size)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        ids = np.arange(NUM_FRAMES)
        segments = [ids[i:i + segment_size] for i in range(0, len(ids), segment_size)]
        segments = [i for i in segments if len(i) == segment_size]
        expected_batch = list(create_dummy_4d_batches(filters=segments))[0]
        self.assertEqual(len(actual_batch), len(expected_batch))
        expected_batch.rename(columns={'myvideo.id': 'FIRST.id', 'myvideo.data': 'SEGMENT.data'})
        self.assertEqual(actual_batch, expected_batch.project(['FIRST.id', 'SEGMENT.data']))

    def test_select_and_groupby_with_last(self):
        segment_size = 3
        select_query = "SELECT LAST(id), SEGMENT(data) FROM MyVideo GROUP BY '{}frames';".format(segment_size)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        ids = np.arange(NUM_FRAMES)
        segments = [ids[i:i + segment_size] for i in range(0, len(ids), segment_size)]
        segments = [i for i in segments if len(i) == segment_size]
        expected_batch = list(create_dummy_4d_batches(filters=segments, start_id=segment_size - 1))[0]
        self.assertEqual(len(actual_batch), len(expected_batch))
        expected_batch.rename(columns={'myvideo.id': 'LAST.id', 'myvideo.data': 'SEGMENT.data'})
        self.assertEqual(actual_batch, expected_batch.project(['LAST.id', 'SEGMENT.data']))

    def test_select_and_groupby_should_fail_with_incorrect_pattern(self):
        segment_size = '4a'
        select_query = "SELECT FIRST(id), SEGMENT(data) FROM MyVideo GROUP BY '{} frames';".format(segment_size)
        self.assertRaises(BinderError, execute_query_fetch_all, self.evadb, select_query)

    def test_select_and_groupby_should_fail_with_seconds(self):
        segment_size = 4
        select_query = "SELECT FIRST(id), SEGMENT(data) FROM MyVideo GROUP BY '{} seconds';".format(segment_size)
        self.assertRaises(BinderError, execute_query_fetch_all, self.evadb, select_query)

    def test_select_and_groupby_should_fail_with_non_video_table(self):
        segment_size = 4
        select_query = "SELECT FIRST(a1) FROM table1 GROUP BY '{} frames';".format(segment_size)
        self.assertRaises(BinderError, execute_query_fetch_all, self.evadb, select_query)

    def test_select_and_groupby_with_sample(self):
        segment_size = 2
        sampling_rate = 2
        select_query = "SELECT FIRST(id), SEGMENT(data) FROM MyVideo SAMPLE {} GROUP BY '{} frames';".format(sampling_rate, segment_size)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        ids = np.arange(0, NUM_FRAMES, sampling_rate)
        segments = [ids[i:i + segment_size] for i in range(0, len(ids), segment_size)]
        segments = [i for i in segments if len(i) == segment_size]
        expected_batch = list(create_dummy_4d_batches(filters=segments))[0]
        self.assertEqual(len(actual_batch), len(expected_batch))
        expected_batch.rename(columns={'myvideo.id': 'FIRST.id', 'myvideo.data': 'SEGMENT.data'})
        self.assertEqual(actual_batch, expected_batch.project(['FIRST.id', 'SEGMENT.data']))

    def test_select_and_groupby_and_aggregate_with_pdf(self):
        GROUPBY_SIZE = 8
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDFs;')
        pdf_path = 'test/data/uadetrac/small-data/pdf_data/fall_2023_orientation_document.pdf'
        load_query = f"LOAD PDF '{pdf_path}' INTO MyPDFs;"
        execute_query_fetch_all(self.evadb, load_query)
        select_all_query = 'SELECT * FROM MyPDFs;'
        all_pdf_batch = execute_query_fetch_all(self.evadb, select_all_query)
        select_query = f"SELECT COUNT(*) FROM MyPDFs GROUP BY '{GROUPBY_SIZE} paragraphs';"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertAlmostEqual(len(all_pdf_batch), len(actual_batch) * actual_batch.frames.iloc[0, 0], None, None, GROUPBY_SIZE)
        self.assertEqual(len(actual_batch), 99)
        n = len(actual_batch)
        for i in range(n):
            self.assertEqual(actual_batch.frames.iloc[i, 0], GROUPBY_SIZE)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDFs;')

    def test_lateral_join_with_unnest_and_sample(self):
        query = 'SELECT id, label\n                  FROM MyVideo SAMPLE 2 JOIN LATERAL\n                    UNNEST(DummyMultiObjectDetector(data).labels) AS T(label)\n                  WHERE id < 10 ORDER BY id;'
        unnest_batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 0, 2, 2, 4, 4, 6, 6, 8, 8], dtype=np.intp), 'T.label': np.array(['person', 'person', 'car', 'car', 'bicycle', 'bicycle', 'person', 'person', 'car', 'car'])}))
        self.assertEqual(len(unnest_batch), 10)
        self.assertEqual(unnest_batch, expected)

    def test_select_without_from(self):
        query = 'SELECT 1;'
        batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([{0: 1}]))
        self.assertEqual(batch, expected)
        query = 'SELECT 1>2;'
        batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([{0: False}]))
        self.assertEqual(batch, expected)

    def test_should_raise_error_with_missing_alias_in_lateral_join(self):
        function_name = 'DummyMultiObjectDetector'
        query = 'SELECT id, labels\n                  FROM MyVideo JOIN LATERAL DummyMultiObjectDetector(data).labels;'
        with self.assertRaises(SyntaxError) as cm:
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        self.assertEqual(str(cm.exception), f'TableValuedFunction {function_name} should have alias.')
        query = 'SELECT id, labels\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyMultiObjectDetector(data).labels);'
        with self.assertRaises(SyntaxError) as cm:
            execute_query_fetch_all(self.evadb, query)
        self.assertEqual(str(cm.exception), f'TableValuedFunction {function_name} should have alias.')
        query = 'SELECT id, labels\n                  FROM MyVideo JOIN LATERAL DummyMultiObjectDetector(data);'
        with self.assertRaises(SyntaxError) as cm:
            execute_query_fetch_all(self.evadb, query)
        self.assertEqual(str(cm.exception), f'TableValuedFunction {function_name} should have alias.')

    def test_should_raise_error_with_invalid_number_of_aliases(self):
        function_name = 'DummyMultiObjectDetector'
        query = 'SELECT id, labels\n                  FROM MyVideo JOIN LATERAL\n                    DummyMultiObjectDetector(data).bboxes AS T;'
        with self.assertRaises(BinderError) as cm:
            execute_query_fetch_all(self.evadb, query)
        self.assertEqual(str(cm.exception), f'Output bboxes does not exist for {function_name}.')

    def test_should_raise_error_with_invalid_output_lateral_join(self):
        query = 'SELECT id, a\n                  FROM MyVideo JOIN LATERAL\n                    DummyMultiObjectDetector(data) AS T(a, b);\n                '
        with self.assertRaises(AssertionError) as cm:
            execute_query_fetch_all(self.evadb, query)
        self.assertEqual(str(cm.exception), 'Expected 1 output columns for T, got 2.')

    def test_hash_join_with_one_on(self):
        select_query = 'SELECT * FROM table1 JOIN\n                        table2 ON table1.a1 = table2.a1;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = pd.merge(self.table1, self.table2, left_on=['table1.a1'], right_on=['table2.a1'], how='inner')
        if len(expected):
            expected_batch = Batch(expected)
            self.assertEqual(expected_batch.sort_orderby(['table1.a2']), actual_batch.sort_orderby(['table1.a2']))

    def test_hash_join_with_multiple_on(self):
        select_query = 'SELECT * FROM table1 JOIN\n                        table1 AS table2 ON table1.a1 = table2.a1 AND\n                        table1.a0 = table2.a0;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = pd.merge(self.table1, self.table1, left_on=['table1.a1', 'table1.a0'], right_on=['table1.a1', 'table1.a0'], how='inner')
        if len(expected):
            expected_batch = Batch(expected)
            self.assertEqual(expected_batch.sort_orderby(['table1.a1']), actual_batch.sort_orderby(['table1.a1']))

    def test_expression_tree_signature(self):
        plan = get_logical_query_plan(self.evadb, "SELECT id FROM MyVideo WHERE DummyMultiObjectDetector(data).labels @> ['person'];")
        signature = next(plan.find_all(LogicalFilter)).predicate.children[0].signature()
        function_id = self.evadb.catalog().get_function_catalog_entry_by_name('DummyMultiObjectDetector').row_id
        table_entry = self.evadb.catalog().get_table_catalog_entry('MyVideo')
        col_id = self.evadb.catalog().get_column_catalog_entry(table_entry, 'data').row_id
        self.assertEqual(signature, f'DummyMultiObjectDetector[{function_id}](MyVideo.data[{col_id}])')

    def test_function_with_no_input_arguments(self):
        select_query = 'SELECT DummyNoInputFunction();'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = Batch(pd.DataFrame([{'dummynoinputfunction.label': 'DummyNoInputFunction'}]))
        self.assertEqual(actual_batch, expected)

def test_should_throw_error_when_both_audio_and_video_selected(self):
    query = "LOAD VIDEO 'data/sample_videos/touchdown.mp4'\n                   INTO TOUCHDOWN1;"
    execute_query_fetch_all(self.evadb, query)
    select_query = 'SELECT id, audio, data FROM TOUCHDOWN1;'
    try:
        execute_query_fetch_all(self.evadb, select_query)
        self.fail("Didn't raise AssertionError")
    except AssertionError as e:
        self.assertEquals('Cannot query over both audio and video streams', e.args[0])

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

class TestBinder(unittest.TestCase):

    def helper_pre_order_match(self, cur_opr, res_opr):
        self.assertEqual(cur_opr.opr_type, res_opr.opr_type)
        self.assertEqual(len(cur_opr.children), len(res_opr.children))
        for i, child_opr in enumerate(cur_opr.children):
            self.helper_pre_order_match(child_opr, res_opr.children[i])

    def test_simple_binder_match(self):
        """
        Opr Tree:
                         LogicalFilter
                         /                             LogicalGet      LogicalGet

        Pattern:
                         LogicalFilter
                         /                             LogicalGet      LogicalGet
        """
        child1_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        child2_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        root_opr = LogicalFilter(MagicMock(), [child1_opr, child2_opr])
        child1_ptn = Pattern(OperatorType.LOGICALGET)
        child2_ptn = Pattern(OperatorType.LOGICALGET)
        root_ptn = Pattern(OperatorType.LOGICALFILTER)
        root_ptn.append_child(child1_ptn)
        root_ptn.append_child(child2_ptn)
        opt_ctxt = OptimizerContext(MagicMock(), CostModel())
        root_grp_expr = opt_ctxt.add_opr_to_group(root_opr)
        binder = Binder(root_grp_expr, root_ptn, opt_ctxt.memo)
        for match in iter(binder):
            self.helper_pre_order_match(root_opr, match)

    def test_nested_binder_match(self):
        """
        Opr Tree:
                         LogicalFilter
                         /                             LogicalGet      LogicalFilter
                                  /                                       LogicalGet       LogicalGet

        Pattern:
                         LogicalFilter
                         /                             LogicalGet      Dummy
        """
        sub_child_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        sub_child_opr_2 = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        sub_root_opr = LogicalFilter(MagicMock(), [sub_child_opr, sub_child_opr_2])
        child_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
        root_opr = LogicalFilter(MagicMock(), [child_opr, sub_root_opr])
        child_ptn = Pattern(OperatorType.LOGICALGET)
        root_ptn = Pattern(OperatorType.LOGICALFILTER)
        root_ptn.append_child(child_ptn)
        root_ptn.append_child(Pattern(OperatorType.DUMMY))
        opt_ctxt = OptimizerContext(MagicMock(), CostModel())
        root_grp_expr = opt_ctxt.add_opr_to_group(root_opr)
        binder = Binder(root_grp_expr, root_ptn, opt_ctxt.memo)
        expected_match = copy.copy(root_opr)
        expected_match.children = [child_opr, Dummy(2, None)]
        for match in iter(binder):
            self.helper_pre_order_match(expected_match, match)
        opt_ctxt = OptimizerContext(MagicMock(), CostModel())
        sub_root_grp_expr = opt_ctxt.add_opr_to_group(sub_root_opr)
        expected_match = copy.copy(sub_root_opr)
        expected_match.children = [sub_child_opr, Dummy(1, None)]
        binder = Binder(sub_root_grp_expr, root_ptn, opt_ctxt.memo)
        for match in iter(binder):
            self.helper_pre_order_match(expected_match, match)

def test_simple_binder_match(self):
    """
        Opr Tree:
                         LogicalFilter
                         /                             LogicalGet      LogicalGet

        Pattern:
                         LogicalFilter
                         /                             LogicalGet      LogicalGet
        """
    child1_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
    child2_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
    root_opr = LogicalFilter(MagicMock(), [child1_opr, child2_opr])
    child1_ptn = Pattern(OperatorType.LOGICALGET)
    child2_ptn = Pattern(OperatorType.LOGICALGET)
    root_ptn = Pattern(OperatorType.LOGICALFILTER)
    root_ptn.append_child(child1_ptn)
    root_ptn.append_child(child2_ptn)
    opt_ctxt = OptimizerContext(MagicMock(), CostModel())
    root_grp_expr = opt_ctxt.add_opr_to_group(root_opr)
    binder = Binder(root_grp_expr, root_ptn, opt_ctxt.memo)
    for match in iter(binder):
        self.helper_pre_order_match(root_opr, match)

def test_nested_binder_match(self):
    """
        Opr Tree:
                         LogicalFilter
                         /                             LogicalGet      LogicalFilter
                                  /                                       LogicalGet       LogicalGet

        Pattern:
                         LogicalFilter
                         /                             LogicalGet      Dummy
        """
    sub_child_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
    sub_child_opr_2 = LogicalGet(MagicMock(), MagicMock(), MagicMock())
    sub_root_opr = LogicalFilter(MagicMock(), [sub_child_opr, sub_child_opr_2])
    child_opr = LogicalGet(MagicMock(), MagicMock(), MagicMock())
    root_opr = LogicalFilter(MagicMock(), [child_opr, sub_root_opr])
    child_ptn = Pattern(OperatorType.LOGICALGET)
    root_ptn = Pattern(OperatorType.LOGICALFILTER)
    root_ptn.append_child(child_ptn)
    root_ptn.append_child(Pattern(OperatorType.DUMMY))
    opt_ctxt = OptimizerContext(MagicMock(), CostModel())
    root_grp_expr = opt_ctxt.add_opr_to_group(root_opr)
    binder = Binder(root_grp_expr, root_ptn, opt_ctxt.memo)
    expected_match = copy.copy(root_opr)
    expected_match.children = [child_opr, Dummy(2, None)]
    for match in iter(binder):
        self.helper_pre_order_match(expected_match, match)
    opt_ctxt = OptimizerContext(MagicMock(), CostModel())
    sub_root_grp_expr = opt_ctxt.add_opr_to_group(sub_root_opr)
    expected_match = copy.copy(sub_root_opr)
    expected_match.children = [sub_child_opr, Dummy(1, None)]
    binder = Binder(sub_root_grp_expr, root_ptn, opt_ctxt.memo)
    for match in iter(binder):
        self.helper_pre_order_match(expected_match, match)

class MemoTest(unittest.TestCase):

    def test_memo_add_with_no_id(self):
        group_expr = MagicMock()
        group_expr.group_id = UNDEFINED_GROUP_ID
        memo = Memo()
        memo.add_group_expr(group_expr)
        self.assertEqual(0, group_expr.group_id)

    def test_memo_add_with_forcing_id(self):
        group_expr = MagicMock()
        group_expr.group_id = 0
        memo = Memo()
        self.assertEqual(memo.add_group_expr(group_expr), group_expr)
        self.assertEqual(len(memo.groups), 1)

    def test_memo_add_under_existing_group(self):
        group_expr1 = MagicMock()
        group_expr1.group_id = UNDEFINED_GROUP_ID
        group_expr2 = MagicMock()
        group_expr2.group_id = 0
        memo = Memo()
        expr = memo.add_group_expr(group_expr1)
        ret_expr = memo.add_group_expr(group_expr2)
        self.assertEqual(expr.group_id, 0)
        self.assertEqual(ret_expr.group_id, 1)
        self.assertEqual(len(memo.groups), 2)
        self.assertEqual(len(memo.group_exprs), 2)
        memo = Memo()
        memo.add_group_expr(group_expr2)
        expr = memo.add_group_expr(group_expr1)
        self.assertEqual(expr.group_id, 1)
        self.assertEqual(len(memo.groups), 2)
        self.assertEqual(len(memo.group_exprs), 2)

def test_memo_add_with_no_id(self):
    group_expr = MagicMock()
    group_expr.group_id = UNDEFINED_GROUP_ID
    memo = Memo()
    memo.add_group_expr(group_expr)
    self.assertEqual(0, group_expr.group_id)

def test_memo_add_with_forcing_id(self):
    group_expr = MagicMock()
    group_expr.group_id = 0
    memo = Memo()
    self.assertEqual(memo.add_group_expr(group_expr), group_expr)
    self.assertEqual(len(memo.groups), 1)

def test_memo_add_under_existing_group(self):
    group_expr1 = MagicMock()
    group_expr1.group_id = UNDEFINED_GROUP_ID
    group_expr2 = MagicMock()
    group_expr2.group_id = 0
    memo = Memo()
    expr = memo.add_group_expr(group_expr1)
    ret_expr = memo.add_group_expr(group_expr2)
    self.assertEqual(expr.group_id, 0)
    self.assertEqual(ret_expr.group_id, 1)
    self.assertEqual(len(memo.groups), 2)
    self.assertEqual(len(memo.group_exprs), 2)
    memo = Memo()
    memo.add_group_expr(group_expr2)
    expr = memo.add_group_expr(group_expr1)
    self.assertEqual(expr.group_id, 1)
    self.assertEqual(len(memo.groups), 2)
    self.assertEqual(len(memo.group_exprs), 2)

class TestGroup(unittest.TestCase):

    def test_simple_add_group_expr(self):
        grp = Group(0)
        grp_expr1 = GroupExpression(MagicMock())
        grp_expr1.opr.is_logical = lambda: True
        grp_expr2 = GroupExpression(MagicMock())
        grp_expr2.opr.is_logical = lambda: False
        grp_expr3 = GroupExpression(MagicMock(), 0)
        grp_expr3.opr.is_logical = lambda: True
        grp.add_expr(grp_expr1)
        self.assertEquals(len(grp.logical_exprs), 1)
        grp.add_expr(grp_expr2)
        self.assertEquals(len(grp.logical_exprs), 1)
        self.assertEquals(len(grp.physical_exprs), 1)
        grp.add_expr(grp_expr3)
        self.assertEquals(len(grp.logical_exprs), 2)
        self.assertEquals(len(grp.physical_exprs), 1)

    def test_add_group_expr_with_unmatched_group_id(self):
        grp = Group(0)
        grp_expr1 = GroupExpression(MagicMock(), 1)
        grp_expr1.opr.is_logical = lambda: True
        grp.add_expr(grp_expr1)
        self.assertEquals(len(grp.logical_exprs), 0)
        self.assertEquals(len(grp.physical_exprs), 0)

    def test_add_group_expr_cost(self):
        grp = Group(0)
        prpty = Property(PropertyType(1))
        grp_expr1 = GroupExpression(MagicMock(), 1)
        grp_expr1.opr.is_logical = lambda: True
        grp_expr2 = GroupExpression(MagicMock())
        grp_expr2.opr.is_logical = lambda: False
        grp.add_expr(grp_expr1)
        grp.add_expr_cost(grp_expr1, prpty, 1)
        grp.add_expr(grp_expr2)
        grp.add_expr_cost(grp_expr2, prpty, 0)
        self.assertEqual(grp.get_best_expr(prpty), grp_expr2)
        self.assertEqual(grp.get_best_expr_cost(prpty), 0)

    def test_empty_group_expr(self):
        grp = Group(0)
        prpty = Property(PropertyType(1))
        self.assertEqual(grp.get_best_expr(prpty), None)
        self.assertEqual(grp.get_best_expr_cost(prpty), None)

def test_simple_add_group_expr(self):
    grp = Group(0)
    grp_expr1 = GroupExpression(MagicMock())
    grp_expr1.opr.is_logical = lambda: True
    grp_expr2 = GroupExpression(MagicMock())
    grp_expr2.opr.is_logical = lambda: False
    grp_expr3 = GroupExpression(MagicMock(), 0)
    grp_expr3.opr.is_logical = lambda: True
    grp.add_expr(grp_expr1)
    self.assertEquals(len(grp.logical_exprs), 1)
    grp.add_expr(grp_expr2)
    self.assertEquals(len(grp.logical_exprs), 1)
    self.assertEquals(len(grp.physical_exprs), 1)
    grp.add_expr(grp_expr3)
    self.assertEquals(len(grp.logical_exprs), 2)
    self.assertEquals(len(grp.physical_exprs), 1)

def test_add_group_expr_with_unmatched_group_id(self):
    grp = Group(0)
    grp_expr1 = GroupExpression(MagicMock(), 1)
    grp_expr1.opr.is_logical = lambda: True
    grp.add_expr(grp_expr1)
    self.assertEquals(len(grp.logical_exprs), 0)
    self.assertEquals(len(grp.physical_exprs), 0)

def test_add_group_expr_cost(self):
    grp = Group(0)
    prpty = Property(PropertyType(1))
    grp_expr1 = GroupExpression(MagicMock(), 1)
    grp_expr1.opr.is_logical = lambda: True
    grp_expr2 = GroupExpression(MagicMock())
    grp_expr2.opr.is_logical = lambda: False
    grp.add_expr(grp_expr1)
    grp.add_expr_cost(grp_expr1, prpty, 1)
    grp.add_expr(grp_expr2)
    grp.add_expr_cost(grp_expr2, prpty, 0)
    self.assertEqual(grp.get_best_expr(prpty), grp_expr2)
    self.assertEqual(grp.get_best_expr_cost(prpty), 0)

def test_empty_group_expr(self):
    grp = Group(0)
    prpty = Property(PropertyType(1))
    self.assertEqual(grp.get_best_expr(prpty), None)
    self.assertEqual(grp.get_best_expr_cost(prpty), None)

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

class OptimizerUtilsTest(unittest.TestCase):

    def test_column_definition_to_function_io(self):
        col = ColumnDefinition('data', ColumnType.NDARRAY, NdArrayType.UINT8, (None, None, None))
        col_list = [col, col]
        actual = column_definition_to_function_io(col_list, True)
        for io in actual:
            self.assertEqual(io.name, 'data')
            self.assertEqual(io.type, ColumnType.NDARRAY)
            self.assertEqual(io.is_nullable, False)
            self.assertEqual(io.array_type, NdArrayType.UINT8)
            self.assertEqual(io.array_dimensions, (None, None, None))
            self.assertEqual(io.is_input, True)
            self.assertEqual(io.function_id, None)
        actual2 = column_definition_to_function_io(col, True)
        for io in actual2:
            self.assertEqual(io.name, 'data')
            self.assertEqual(io.type, ColumnType.NDARRAY)
            self.assertEqual(io.is_nullable, False)
            self.assertEqual(io.array_type, NdArrayType.UINT8)
            self.assertEqual(io.array_dimensions, (None, None, None))
            self.assertEqual(io.is_input, True)
            self.assertEqual(io.function_id, None)

def test_column_definition_to_function_io(self):
    col = ColumnDefinition('data', ColumnType.NDARRAY, NdArrayType.UINT8, (None, None, None))
    col_list = [col, col]
    actual = column_definition_to_function_io(col_list, True)
    for io in actual:
        self.assertEqual(io.name, 'data')
        self.assertEqual(io.type, ColumnType.NDARRAY)
        self.assertEqual(io.is_nullable, False)
        self.assertEqual(io.array_type, NdArrayType.UINT8)
        self.assertEqual(io.array_dimensions, (None, None, None))
        self.assertEqual(io.is_input, True)
        self.assertEqual(io.function_id, None)
    actual2 = column_definition_to_function_io(col, True)
    for io in actual2:
        self.assertEqual(io.name, 'data')
        self.assertEqual(io.type, ColumnType.NDARRAY)
        self.assertEqual(io.is_nullable, False)
        self.assertEqual(io.array_type, NdArrayType.UINT8)
        self.assertEqual(io.array_dimensions, (None, None, None))
        self.assertEqual(io.is_input, True)
        self.assertEqual(io.function_id, None)

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

class TestOptimizerContext(unittest.TestCase):

    def test_add_root(self):
        fake_opr = MagicMock()
        fake_opr.children = []
        opt_ctxt = OptimizerContext(MagicMock(), CostModel())
        opt_ctxt.add_opr_to_group(fake_opr)
        self.assertEqual(len(opt_ctxt.memo.group_exprs), 1)

def test_add_root(self):
    fake_opr = MagicMock()
    fake_opr.children = []
    opt_ctxt = OptimizerContext(MagicMock(), CostModel())
    opt_ctxt.add_opr_to_group(fake_opr)
    self.assertEqual(len(opt_ctxt.memo.group_exprs), 1)

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

def test_xform_lateral_join_does_not_work_with_other_join(self):
    rule = XformLateralJoinToLinearFlow()
    logi_join = LogicalJoin(JoinType.INNER_JOIN)
    self.assertFalse(rule.check(logi_join, MagicMock()))

def merge_dict_of_dicts(dict1, dict2):
    """In case of conflict override with dict2"""
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if key in merged_dict.keys():
            if value is not None:
                if isinstance(merged_dict[key], dict) and isinstance(value, dict):
                    merged_dict[key] = merge_dict_of_dicts(merged_dict[key], value)
                else:
                    merged_dict[key] = value
        else:
            merged_dict[key] = value
    return merged_dict

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

def is_logical(self):
    return self.opr.is_logical()

class TopDownRewrite(OptimizerTask):

    def __init__(self, root_expr: GroupExpression, rule_set: List[Rule], optimizer_context: OptimizerContext):
        self.root_expr = root_expr
        self.rule_set = rule_set
        super().__init__(optimizer_context, OptimizerTaskType.TOP_DOWN_REWRITE)

    def execute(self):
        valid_rules = []
        for rule in self.rule_set:
            if not self.root_expr.is_rule_explored(rule.rule_type) and rule.top_match(self.root_expr.opr):
                valid_rules.append(rule)
        valid_rules = sorted(valid_rules, key=lambda x: x.promise())
        for rule in valid_rules:
            binder = Binder(self.root_expr, rule.pattern, self.optimizer_context.memo)
            for match in iter(binder):
                if not rule.check(match, self.optimizer_context):
                    continue
                after = rule.apply(match, self.optimizer_context)
                plans = list(after)
                assert len(plans) <= 1, 'Rewrite rule cannot generate more than open alternate plan.'
                for plan in plans:
                    new_expr = self.optimizer_context.replace_expression(plan, self.root_expr.group_id)
                    self.optimizer_context.task_stack.push(TopDownRewrite(new_expr, self.rule_set, self.optimizer_context))
                    return
                self.root_expr.mark_rule_explored(rule.rule_type)
        for child in self.root_expr.children:
            child_expr = self.optimizer_context.memo.groups[child].logical_exprs[0]
            self.optimizer_context.task_stack.push(TopDownRewrite(child_expr, self.rule_set, self.optimizer_context))

def execute(self):
    valid_rules = []
    for rule in self.rule_set:
        if not self.root_expr.is_rule_explored(rule.rule_type) and rule.top_match(self.root_expr.opr):
            valid_rules.append(rule)
    valid_rules = sorted(valid_rules, key=lambda x: x.promise())
    for rule in valid_rules:
        binder = Binder(self.root_expr, rule.pattern, self.optimizer_context.memo)
        for match in iter(binder):
            if not rule.check(match, self.optimizer_context):
                continue
            after = rule.apply(match, self.optimizer_context)
            plans = list(after)
            assert len(plans) <= 1, 'Rewrite rule cannot generate more than open alternate plan.'
            for plan in plans:
                new_expr = self.optimizer_context.replace_expression(plan, self.root_expr.group_id)
                self.optimizer_context.task_stack.push(TopDownRewrite(new_expr, self.rule_set, self.optimizer_context))
                return
            self.root_expr.mark_rule_explored(rule.rule_type)
    for child in self.root_expr.children:
        child_expr = self.optimizer_context.memo.groups[child].logical_exprs[0]
        self.optimizer_context.task_stack.push(TopDownRewrite(child_expr, self.rule_set, self.optimizer_context))

class BottomUpRewrite(OptimizerTask):

    def __init__(self, root_expr: GroupExpression, rule_set: List[Rule], optimizer_context: OptimizerContext, children_explored=False):
        super().__init__(optimizer_context, OptimizerTaskType.BOTTOM_UP_REWRITE)
        self._children_explored = children_explored
        self.root_expr = root_expr
        self.rule_set = rule_set

    def execute(self):
        if not self._children_explored:
            self.optimizer_context.task_stack.push(BottomUpRewrite(self.root_expr, self.rule_set, self.optimizer_context, True))
            for child in self.root_expr.children:
                child_expr = self.optimizer_context.memo.groups[child].logical_exprs[0]
                self.optimizer_context.task_stack.push(BottomUpRewrite(child_expr, self.rule_set, self.optimizer_context))
            return
        valid_rules = []
        for rule in self.rule_set:
            if not self.root_expr.is_rule_explored(rule.rule_type) and rule.top_match(self.root_expr.opr):
                valid_rules.append(rule)
        sorted(valid_rules, key=lambda x: x.promise())
        for rule in valid_rules:
            binder = Binder(self.root_expr, rule.pattern, self.optimizer_context.memo)
            for match in iter(binder):
                if not rule.check(match, self.optimizer_context):
                    continue
                logger.info('In BottomUp, Rule {} matched for {}'.format(rule, self.root_expr))
                after = rule.apply(match, self.optimizer_context)
                plans = list(after)
                assert len(plans) <= 1, 'Rewrite rule cannot generate more than open alternate plan.'
                for plan in plans:
                    new_expr = self.optimizer_context.replace_expression(plan, self.root_expr.group_id)
                    logger.info('After rewriting {}'.format(self.root_expr))
                    self.optimizer_context.task_stack.push(BottomUpRewrite(new_expr, self.rule_set, self.optimizer_context))
                    return
            self.root_expr.mark_rule_explored(rule.rule_type)

def execute(self):
    if not self._children_explored:
        self.optimizer_context.task_stack.push(BottomUpRewrite(self.root_expr, self.rule_set, self.optimizer_context, True))
        for child in self.root_expr.children:
            child_expr = self.optimizer_context.memo.groups[child].logical_exprs[0]
            self.optimizer_context.task_stack.push(BottomUpRewrite(child_expr, self.rule_set, self.optimizer_context))
        return
    valid_rules = []
    for rule in self.rule_set:
        if not self.root_expr.is_rule_explored(rule.rule_type) and rule.top_match(self.root_expr.opr):
            valid_rules.append(rule)
    sorted(valid_rules, key=lambda x: x.promise())
    for rule in valid_rules:
        binder = Binder(self.root_expr, rule.pattern, self.optimizer_context.memo)
        for match in iter(binder):
            if not rule.check(match, self.optimizer_context):
                continue
            logger.info('In BottomUp, Rule {} matched for {}'.format(rule, self.root_expr))
            after = rule.apply(match, self.optimizer_context)
            plans = list(after)
            assert len(plans) <= 1, 'Rewrite rule cannot generate more than open alternate plan.'
            for plan in plans:
                new_expr = self.optimizer_context.replace_expression(plan, self.root_expr.group_id)
                logger.info('After rewriting {}'.format(self.root_expr))
                self.optimizer_context.task_stack.push(BottomUpRewrite(new_expr, self.rule_set, self.optimizer_context))
                return
        self.root_expr.mark_rule_explored(rule.rule_type)

class OptimizeExpression(OptimizerTask):

    def __init__(self, root_expr: GroupExpression, optimizer_context: OptimizerContext, explore: bool):
        self.root_expr = root_expr
        self.explore = explore
        super().__init__(optimizer_context, OptimizerTaskType.OPTIMIZE_EXPRESSION)

    def execute(self):
        rules_manager = self.optimizer_context.rules_manager
        rules = rules_manager.logical_rules
        if not self.explore:
            rules = rules_manager.logical_rules + rules_manager.implementation_rules
        valid_rules = []
        for rule in rules:
            if rule.top_match(self.root_expr.opr):
                valid_rules.append(rule)
        valid_rules = sorted(valid_rules, key=lambda x: x.promise())
        for rule in valid_rules:
            self.optimizer_context.task_stack.push(ApplyRule(rule, self.root_expr, self.optimizer_context, self.explore))

def execute(self):
    rules_manager = self.optimizer_context.rules_manager
    rules = rules_manager.logical_rules
    if not self.explore:
        rules = rules_manager.logical_rules + rules_manager.implementation_rules
    valid_rules = []
    for rule in rules:
        if rule.top_match(self.root_expr.opr):
            valid_rules.append(rule)
    valid_rules = sorted(valid_rules, key=lambda x: x.promise())
    for rule in valid_rules:
        self.optimizer_context.task_stack.push(ApplyRule(rule, self.root_expr, self.optimizer_context, self.explore))

class ApplyRule(OptimizerTask):
    """apply a transformation or implementation rule"""

    def __init__(self, rule: Rule, root_expr: GroupExpression, optimizer_context: OptimizerContext, explore: bool):
        self.rule = rule
        self.root_expr = root_expr
        self.explore = explore
        super().__init__(optimizer_context, OptimizerTaskType.APPLY_RULE)

    def execute(self):
        if self.root_expr.is_rule_explored(self.rule.rule_type):
            return
        binder = Binder(self.root_expr, self.rule.pattern, self.optimizer_context.memo)
        for match in iter(binder):
            if not self.rule.check(match, self.optimizer_context):
                continue
            after = self.rule.apply(match, self.optimizer_context)
            for plan in after:
                new_expr = self.optimizer_context.add_opr_to_group(plan, self.root_expr.group_id)
                if new_expr.is_logical():
                    self.optimizer_context.task_stack.push(OptimizeExpression(new_expr, self.optimizer_context, self.explore))
                else:
                    self.optimizer_context.task_stack.push(OptimizeInputs(new_expr, self.optimizer_context))
        self.root_expr.mark_rule_explored(self.rule.rule_type)

def execute(self):
    if self.root_expr.is_rule_explored(self.rule.rule_type):
        return
    binder = Binder(self.root_expr, self.rule.pattern, self.optimizer_context.memo)
    for match in iter(binder):
        if not self.rule.check(match, self.optimizer_context):
            continue
        after = self.rule.apply(match, self.optimizer_context)
        for plan in after:
            new_expr = self.optimizer_context.add_opr_to_group(plan, self.root_expr.group_id)
            if new_expr.is_logical():
                self.optimizer_context.task_stack.push(OptimizeExpression(new_expr, self.optimizer_context, self.explore))
            else:
                self.optimizer_context.task_stack.push(OptimizeInputs(new_expr, self.optimizer_context))
    self.root_expr.mark_rule_explored(self.rule.rule_type)

class OptimizeGroup(OptimizerTask):

    def __init__(self, group: Group, optimizer_context: OptimizerContext):
        self.group = group
        super().__init__(optimizer_context, OptimizerTaskType.OPTIMIZE_GROUP)

    def execute(self):
        if self.group.get_best_expr(PropertyType.DEFAULT):
            return
        for expr in self.group.logical_exprs:
            self.optimizer_context.task_stack.push(OptimizeExpression(expr, self.optimizer_context, explore=False))
        for expr in self.group.physical_exprs:
            self.optimizer_context.task_stack.push(OptimizeInputs(expr, self.optimizer_context))

def execute(self):
    if self.group.get_best_expr(PropertyType.DEFAULT):
        return
    for expr in self.group.logical_exprs:
        self.optimizer_context.task_stack.push(OptimizeExpression(expr, self.optimizer_context, explore=False))
    for expr in self.group.physical_exprs:
        self.optimizer_context.task_stack.push(OptimizeInputs(expr, self.optimizer_context))

class OptimizeInputs(OptimizerTask):

    def __init__(self, root_expr: GroupExpression, optimizer_context: OptimizerContext):
        self.root_expr = root_expr
        super().__init__(optimizer_context, OptimizerTaskType.OPTIMIZE_INPUTS)

    def execute(self):
        cost = 0
        memo = self.optimizer_context.memo
        grp = memo.get_group_by_id(self.root_expr.group_id)
        for child_id in self.root_expr.children:
            child_grp = memo.get_group_by_id(child_id)
            if child_grp.get_best_expr(PropertyType.DEFAULT):
                cost += child_grp.get_best_expr_cost(PropertyType.DEFAULT)
            else:
                self.optimizer_context.task_stack.push(OptimizeInputs(self.root_expr, self.optimizer_context))
                self.optimizer_context.task_stack.push(OptimizeGroup(child_grp, self.optimizer_context))
                return
        cost += self.optimizer_context.cost_model.calculate_cost(self.root_expr)
        grp.add_expr_cost(self.root_expr, PropertyType.DEFAULT, cost)

def execute(self):
    cost = 0
    memo = self.optimizer_context.memo
    grp = memo.get_group_by_id(self.root_expr.group_id)
    for child_id in self.root_expr.children:
        child_grp = memo.get_group_by_id(child_id)
        if child_grp.get_best_expr(PropertyType.DEFAULT):
            cost += child_grp.get_best_expr_cost(PropertyType.DEFAULT)
        else:
            self.optimizer_context.task_stack.push(OptimizeInputs(self.root_expr, self.optimizer_context))
            self.optimizer_context.task_stack.push(OptimizeGroup(child_grp, self.optimizer_context))
            return
    cost += self.optimizer_context.cost_model.calculate_cost(self.root_expr)
    grp.add_expr_cost(self.root_expr, PropertyType.DEFAULT, cost)

class OptimizerContext:
    """
    Maintain context information for the optimizer

    Arguments:
        _task_queue(OptimizerTaskStack):
            stack to keep track outstanding tasks
    """

    def __init__(self, db: EvaDBDatabase, cost_model: CostModel, rules_manager: RulesManager=None):
        self._db = db
        self._task_stack = OptimizerTaskStack()
        self._memo = Memo()
        self._cost_model = cost_model
        is_ray_enabled = self.db.catalog().get_configuration_catalog_value('ray')
        self._rules_manager = rules_manager or RulesManager({'ray': is_ray_enabled})

    @property
    def db(self):
        return self._db

    @property
    def rules_manager(self):
        return self._rules_manager

    @property
    def cost_model(self):
        return self._cost_model

    @property
    def task_stack(self):
        return self._task_stack

    @property
    def memo(self):
        return self._memo

    def _xform_opr_to_group_expr(self, opr: Operator) -> GroupExpression:
        """
        Note: Internal function Generate a group expressions from a
        logical operator tree. Caller is responsible for assigning
        the group to the returned GroupExpression.
        """
        child_ids = []
        for child_opr in opr.children:
            if isinstance(child_opr, Dummy):
                child_ids.append(child_opr.group_id)
            else:
                child_expr = self._xform_opr_to_group_expr(opr=child_opr)
                memo_expr = self.memo.add_group_expr(child_expr)
                child_ids.append(memo_expr.group_id)
        opr_copy = copy.copy(opr)
        opr_copy.clear_children()
        expr = GroupExpression(opr=opr_copy, children=child_ids)
        return expr

    def replace_expression(self, opr: Operator, group_id: int):
        """
        Removes all the expressions from the specified group and
        create a new expression. This is called by rewrite rules. The
        new expr gets assigned a new group id
        """
        self.memo.erase_group(group_id)
        new_expr = self._xform_opr_to_group_expr(opr)
        new_expr = self.memo.add_group_expr(new_expr, group_id)
        return new_expr

    def add_opr_to_group(self, opr: Operator, group_id: int=UNDEFINED_GROUP_ID):
        """
        Convert operator to group_expression and add to the group
        """
        grp_expr = self._xform_opr_to_group_expr(opr)
        grp_expr = self.memo.add_group_expr(grp_expr, group_id)
        return grp_expr

def _xform_opr_to_group_expr(self, opr: Operator) -> GroupExpression:
    """
        Note: Internal function Generate a group expressions from a
        logical operator tree. Caller is responsible for assigning
        the group to the returned GroupExpression.
        """
    child_ids = []
    for child_opr in opr.children:
        if isinstance(child_opr, Dummy):
            child_ids.append(child_opr.group_id)
        else:
            child_expr = self._xform_opr_to_group_expr(opr=child_opr)
            memo_expr = self.memo.add_group_expr(child_expr)
            child_ids.append(memo_expr.group_id)
    opr_copy = copy.copy(opr)
    opr_copy.clear_children()
    expr = GroupExpression(opr=opr_copy, children=child_ids)
    return expr

def replace_expression(self, opr: Operator, group_id: int):
    """
        Removes all the expressions from the specified group and
        create a new expression. This is called by rewrite rules. The
        new expr gets assigned a new group id
        """
    self.memo.erase_group(group_id)
    new_expr = self._xform_opr_to_group_expr(opr)
    new_expr = self.memo.add_group_expr(new_expr, group_id)
    return new_expr

def add_opr_to_group(self, opr: Operator, group_id: int=UNDEFINED_GROUP_ID):
    """
        Convert operator to group_expression and add to the group
        """
    grp_expr = self._xform_opr_to_group_expr(opr)
    grp_expr = self.memo.add_group_expr(grp_expr, group_id)
    return grp_expr

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

class EmbedSampleIntoGet(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALSAMPLE)
        pattern.append_child(Pattern(OperatorType.LOGICALGET))
        super().__init__(RuleType.EMBED_SAMPLE_INTO_GET, pattern)

    def promise(self):
        return Promise.EMBED_SAMPLE_INTO_GET

    def check(self, before: LogicalSample, context: OptimizerContext):
        lget: LogicalGet = before.children[0]
        if lget.table_obj.table_type == TableType.VIDEO_DATA:
            return True
        return False

    def apply(self, before: LogicalSample, context: OptimizerContext):
        sample_freq = before.sample_freq.value
        sample_type = before.sample_type.value.value if before.sample_type else None
        lget: LogicalGet = before.children[0]
        new_get_opr = LogicalGet(lget.video, lget.table_obj, alias=lget.alias, predicate=lget.predicate, target_list=lget.target_list, sampling_rate=sample_freq, sampling_type=sample_type, children=lget.children)
        yield new_get_opr

def apply(self, before: LogicalSample, context: OptimizerContext):
    sample_freq = before.sample_freq.value
    sample_type = before.sample_type.value.value if before.sample_type else None
    lget: LogicalGet = before.children[0]
    new_get_opr = LogicalGet(lget.video, lget.table_obj, alias=lget.alias, predicate=lget.predicate, target_list=lget.target_list, sampling_rate=sample_freq, sampling_type=sample_type, children=lget.children)
    yield new_get_opr

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

def apply(self, before: LogicalProject, context: OptimizerContext):
    new_target_list = [expr.copy() for expr in before.target_list]
    for expr in new_target_list:
        enable_cache_on_expression_tree(context, expr)
    after = LogicalProject(target_list=new_target_list, children=before.children)
    yield after

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

def apply(self, before: LogicalFilter, context: OptimizerContext):
    after_predicate = before.predicate.copy()
    enable_cache_on_expression_tree(context, after_predicate)
    after_operator = LogicalFilter(predicate=after_predicate, children=before.children)
    yield after_operator

class PushDownFilterThroughJoin(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALFILTER)
        pattern_join = Pattern(OperatorType.LOGICALJOIN)
        pattern_join.append_child(Pattern(OperatorType.DUMMY))
        pattern_join.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(pattern_join)
        super().__init__(RuleType.PUSHDOWN_FILTER_THROUGH_JOIN, pattern)

    def promise(self):
        return Promise.PUSHDOWN_FILTER_THROUGH_JOIN

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalFilter, context: OptimizerContext):
        predicate = before.predicate
        join: LogicalJoin = before.children[0]
        left: Dummy = join.children[0]
        right: Dummy = join.children[1]
        new_join_node = LogicalJoin(join.join_type, join.join_predicate, join.left_keys, join.right_keys)
        left_group_aliases = context.memo.get_group_by_id(left.group_id).aliases
        right_group_aliases = context.memo.get_group_by_id(right.group_id).aliases
        left_pushdown_pred, rem_pred = extract_pushdown_predicate_for_alias(predicate, left_group_aliases)
        right_pushdown_pred, rem_pred = extract_pushdown_predicate_for_alias(rem_pred, right_group_aliases)
        if left_pushdown_pred:
            left_filter = LogicalFilter(predicate=left_pushdown_pred)
            left_filter.append_child(left)
            new_join_node.append_child(left_filter)
        else:
            new_join_node.append_child(left)
        if right_pushdown_pred:
            right_filter = LogicalFilter(predicate=right_pushdown_pred)
            right_filter.append_child(right)
            new_join_node.append_child(right_filter)
        else:
            new_join_node.append_child(right)
        if rem_pred:
            new_join_node._join_predicate = conjunction_list_to_expression_tree([rem_pred, new_join_node.join_predicate])
        yield new_join_node

def apply(self, before: LogicalFilter, context: OptimizerContext):
    predicate = before.predicate
    join: LogicalJoin = before.children[0]
    left: Dummy = join.children[0]
    right: Dummy = join.children[1]
    new_join_node = LogicalJoin(join.join_type, join.join_predicate, join.left_keys, join.right_keys)
    left_group_aliases = context.memo.get_group_by_id(left.group_id).aliases
    right_group_aliases = context.memo.get_group_by_id(right.group_id).aliases
    left_pushdown_pred, rem_pred = extract_pushdown_predicate_for_alias(predicate, left_group_aliases)
    right_pushdown_pred, rem_pred = extract_pushdown_predicate_for_alias(rem_pred, right_group_aliases)
    if left_pushdown_pred:
        left_filter = LogicalFilter(predicate=left_pushdown_pred)
        left_filter.append_child(left)
        new_join_node.append_child(left_filter)
    else:
        new_join_node.append_child(left)
    if right_pushdown_pred:
        right_filter = LogicalFilter(predicate=right_pushdown_pred)
        right_filter.append_child(right)
        new_join_node.append_child(right_filter)
    else:
        new_join_node.append_child(right)
    if rem_pred:
        new_join_node._join_predicate = conjunction_list_to_expression_tree([rem_pred, new_join_node.join_predicate])
    yield new_join_node

class PushDownFilterThroughApplyAndMerge(Rule):
    """If it is feasible to partially or fully push the predicate contained within the
    logical filter through the ApplyAndMerge operator, we should do so. This is often
    beneficial, for instance, in order to prevent decoding additional frames beyond
    those that satisfy the predicate.
    Eg:

    Filter(id < 10 and func.label = 'car')           Filter(func.label = 'car')
            |                                                   |
        ApplyAndMerge(func)                  ->          ApplyAndMerge(func)
            |                                                   |
            A                                            Filter(id < 10)
                                                                |
                                                                A

    """

    def __init__(self):
        appply_merge_pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
        appply_merge_pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern = Pattern(OperatorType.LOGICALFILTER)
        pattern.append_child(appply_merge_pattern)
        super().__init__(RuleType.PUSHDOWN_FILTER_THROUGH_APPLY_AND_MERGE, pattern)

    def promise(self):
        return Promise.PUSHDOWN_FILTER_THROUGH_APPLY_AND_MERGE

    def check(self, before: LogicalFilter, context: OptimizerContext):
        return True

    def apply(self, before: LogicalFilter, context: OptimizerContext):
        A: Dummy = before.children[0].children[0]
        apply_and_merge: LogicalApplyAndMerge = before.children[0]
        aliases = context.memo.get_group_by_id(A.group_id).aliases
        predicate = before.predicate
        pushdown_pred, rem_pred = extract_pushdown_predicate_for_alias(predicate, aliases)
        if pushdown_pred is None:
            return
        if pushdown_pred:
            pushdown_filter = LogicalFilter(predicate=pushdown_pred)
            pushdown_filter.append_child(A)
            apply_and_merge.children = [pushdown_filter]
        root_node = apply_and_merge
        if rem_pred:
            root_node = LogicalFilter(predicate=rem_pred)
            root_node.append_child(apply_and_merge)
        yield root_node

def apply(self, before: LogicalFilter, context: OptimizerContext):
    A: Dummy = before.children[0].children[0]
    apply_and_merge: LogicalApplyAndMerge = before.children[0]
    aliases = context.memo.get_group_by_id(A.group_id).aliases
    predicate = before.predicate
    pushdown_pred, rem_pred = extract_pushdown_predicate_for_alias(predicate, aliases)
    if pushdown_pred is None:
        return
    if pushdown_pred:
        pushdown_filter = LogicalFilter(predicate=pushdown_pred)
        pushdown_filter.append_child(A)
        apply_and_merge.children = [pushdown_filter]
    root_node = apply_and_merge
    if rem_pred:
        root_node = LogicalFilter(predicate=rem_pred)
        root_node.append_child(apply_and_merge)
    yield root_node

class LogicalInnerJoinCommutativity(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALJOIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_INNER_JOIN_COMMUTATIVITY, pattern)

    def promise(self):
        return Promise.LOGICAL_INNER_JOIN_COMMUTATIVITY

    def check(self, before: LogicalJoin, context: OptimizerContext):
        return before.join_type == JoinType.INNER_JOIN

    def apply(self, before: LogicalJoin, context: OptimizerContext):
        new_join = LogicalJoin(before.join_type, before.join_predicate)
        new_join.append_child(before.rhs())
        new_join.append_child(before.lhs())
        yield new_join

def apply(self, before: LogicalJoin, context: OptimizerContext):
    new_join = LogicalJoin(before.join_type, before.join_predicate)
    new_join.append_child(before.rhs())
    new_join.append_child(before.lhs())
    yield new_join

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

class LogicalLateralJoinToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALJOIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_LATERAL_JOIN_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_LATERAL_JOIN_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return before.join_type == JoinType.LATERAL_JOIN

    def apply(self, join_node: LogicalJoin, context: OptimizerContext):
        lateral_join_plan = LateralJoinPlan(join_node.join_predicate)
        lateral_join_plan.join_project = join_node.join_project
        lateral_join_plan.append_child(join_node.lhs())
        lateral_join_plan.append_child(join_node.rhs())
        yield lateral_join_plan

def apply(self, join_node: LogicalJoin, context: OptimizerContext):
    lateral_join_plan = LateralJoinPlan(join_node.join_predicate)
    lateral_join_plan.join_project = join_node.join_project
    lateral_join_plan.append_child(join_node.lhs())
    lateral_join_plan.append_child(join_node.rhs())
    yield lateral_join_plan

class LogicalJoinToPhysicalHashJoin(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALJOIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_JOIN_TO_PHYSICAL_HASH_JOIN, pattern)

    def promise(self):
        return Promise.LOGICAL_JOIN_TO_PHYSICAL_HASH_JOIN

    def check(self, before: Operator, context: OptimizerContext):
        """
        We don't want to apply this rule to the join when FuzzDistance
        is being used, which implies that the join is a FuzzyJoin
        """
        if before.join_predicate is None:
            return False
        j_child: FunctionExpression = before.join_predicate.children[0]
        if isinstance(j_child, FunctionExpression):
            if j_child.name.startswith('FuzzDistance'):
                return before.join_type == JoinType.INNER_JOIN and (not j_child or not j_child.name.startswith('FuzzDistance'))
        else:
            return before.join_type == JoinType.INNER_JOIN

    def apply(self, join_node: LogicalJoin, context: OptimizerContext):
        a: Dummy = join_node.lhs()
        b: Dummy = join_node.rhs()
        a_table_aliases = context.memo.get_group_by_id(a.group_id).aliases
        b_table_aliases = context.memo.get_group_by_id(b.group_id).aliases
        join_predicates = join_node.join_predicate
        a_join_keys, b_join_keys = extract_equi_join_keys(join_predicates, a_table_aliases, b_table_aliases)
        build_plan = HashJoinBuildPlan(join_node.join_type, a_join_keys)
        build_plan.append_child(a)
        probe_side = HashJoinProbePlan(join_node.join_type, b_join_keys, join_predicates, join_node.join_project)
        probe_side.append_child(build_plan)
        probe_side.append_child(b)
        yield probe_side

def apply(self, join_node: LogicalJoin, context: OptimizerContext):
    a: Dummy = join_node.lhs()
    b: Dummy = join_node.rhs()
    a_table_aliases = context.memo.get_group_by_id(a.group_id).aliases
    b_table_aliases = context.memo.get_group_by_id(b.group_id).aliases
    join_predicates = join_node.join_predicate
    a_join_keys, b_join_keys = extract_equi_join_keys(join_predicates, a_table_aliases, b_table_aliases)
    build_plan = HashJoinBuildPlan(join_node.join_type, a_join_keys)
    build_plan.append_child(a)
    probe_side = HashJoinProbePlan(join_node.join_type, b_join_keys, join_predicates, join_node.join_project)
    probe_side.append_child(build_plan)
    probe_side.append_child(b)
    yield probe_side

class LogicalJoinToPhysicalNestedLoopJoin(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALJOIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_JOIN_TO_PHYSICAL_NESTED_LOOP_JOIN, pattern)

    def promise(self):
        return Promise.LOGICAL_JOIN_TO_PHYSICAL_NESTED_LOOP_JOIN

    def check(self, before: LogicalJoin, context: OptimizerContext):
        """
        We want to apply this rule to the join when FuzzDistance
        is being used, which implies that the join is a FuzzyJoin
        """
        if before.join_predicate is None:
            return False
        j_child: FunctionExpression = before.join_predicate.children[0]
        if not isinstance(j_child, FunctionExpression):
            return False
        return before.join_type == JoinType.INNER_JOIN and j_child.name.startswith('FuzzDistance')

    def apply(self, join_node: LogicalJoin, context: OptimizerContext):
        nested_loop_join_plan = NestedLoopJoinPlan(join_node.join_type, join_node.join_predicate)
        nested_loop_join_plan.append_child(join_node.lhs())
        nested_loop_join_plan.append_child(join_node.rhs())
        yield nested_loop_join_plan

def apply(self, join_node: LogicalJoin, context: OptimizerContext):
    nested_loop_join_plan = NestedLoopJoinPlan(join_node.join_type, join_node.join_predicate)
    nested_loop_join_plan.append_child(join_node.lhs())
    nested_loop_join_plan.append_child(join_node.rhs())
    yield nested_loop_join_plan

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

