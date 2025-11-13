# Cluster 9

class JobSchedulerIntegrationTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        cls.job_name_1 = 'test_async_job_1'
        cls.job_name_2 = 'test_async_job_2'

    def setUp(self):
        execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {self.job_name_1};')
        execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {self.job_name_2};')

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, f'DROP JOB IF EXISTS {cls.job_name_1};')
        execute_query_fetch_all(cls.evadb, f'DROP JOB IF EXISTS {cls.job_name_2};')

    def create_jobs(self):
        datetime_format = '%Y-%m-%d %H:%M:%S'
        start_time = (datetime.now() - timedelta(seconds=10)).strftime(datetime_format)
        end_time = (datetime.now() + timedelta(seconds=60)).strftime(datetime_format)
        create_csv_query = 'CREATE TABLE IF NOT EXISTS MyCSV (\n                                    id INTEGER UNIQUE,\n                                    frame_id INTEGER,\n                                    video_id INTEGER\n                                );\n                            '
        job_1_query = f"CREATE JOB IF NOT EXISTS {self.job_name_1} AS {{\n                                SELECT * FROM MyCSV;\n                            }}\n                            START '{start_time}'\n                            END '{end_time}'\n                            EVERY 4 seconds;\n                        "
        job_2_query = f"CREATE JOB IF NOT EXISTS {self.job_name_2} AS {{\n                            SHOW FUNCTIONS;\n                        }}\n                        START '{start_time}'\n                        END '{end_time}'\n                        EVERY 2 seconds;\n                    "
        execute_query_fetch_all(self.evadb, create_csv_query)
        execute_query_fetch_all(self.evadb, job_1_query)
        execute_query_fetch_all(self.evadb, job_2_query)

    def test_should_execute_the_scheduled_jobs(self):
        self.create_jobs()
        connection = EvaDBConnection(self.evadb, MagicMock(), MagicMock())
        connection.start_jobs()
        time.sleep(15)
        connection.stop_jobs()
        job_1_execution_count = len(self.evadb.catalog().get_job_history_by_job_id(1))
        job_2_execution_count = len(self.evadb.catalog().get_job_history_by_job_id(2))
        self.assertGreater(job_2_execution_count, job_1_execution_count)
        self.assertGreater(job_2_execution_count, 2)
        self.assertGreater(job_1_execution_count, 2)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class TimerTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @windows_skip_marker
    def test_timer(self):
        sleep_time = Timer()
        with sleep_time:
            time.sleep(5)
        self.assertTrue(sleep_time.total_elapsed_time < 5.2)
        self.assertTrue(sleep_time.total_elapsed_time > 4.9)

    @pytest.mark.notparallel
    def test_timer_with_query(self):
        evadb = get_evadb_for_testing()
        evadb.catalog().reset()
        video_file_path = create_sample_video(NUM_FRAMES)
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        transport = MagicMock()
        transport.write = MagicMock(return_value='response_message')
        response = asyncio.run(handle_request(evadb, transport, load_query))
        self.assertTrue(response.error is None)
        self.assertTrue(response.query_time is not None)
        load_query = "LOAD INFILE 'dummy.avi' INTO MyVideo;"
        transport = MagicMock()
        transport.write = MagicMock(return_value='response_message')
        response = asyncio.run(handle_request(evadb, transport, load_query))
        self.assertTrue(response.error is not None)
        self.assertTrue(response.query_time is None)
        file_remove('dummy.avi')

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class EmotionDetector(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = Path(EvaDB_TEST_DATA_DIR) / 'data' / 'emotion_detector'

    def _load_image(self, path):
        try_to_import_cv2()
        import cv2
        assert path.exists(), f'File does not exist at the path {str(path)}'
        img = cv2.imread(str(path))
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @unittest.skip('disable test due to model downloading time')
    def test_should_return_correct_emotion(self):
        from evadb.functions.emotion_detector import EmotionDetector
        happy_img = self.base_path / 'happy.jpg'
        sad_img = self.base_path / 'sad.jpg'
        angry_img = self.base_path / 'angry.jpg'
        frame_happy = {'id': 1, 'data': self._load_image(happy_img)}
        frame_sad = {'id': 2, 'data': self._load_image(sad_img)}
        frame_angry = {'id': 3, 'data': self._load_image(angry_img)}
        frame_batch = Batch(pd.DataFrame([frame_happy, frame_sad, frame_angry]))
        detector = EmotionDetector()
        result = detector.classify(frame_batch.project(['data']).frames)
        self.assertEqual('happy', result.iloc[0]['labels'])
        self.assertEqual('sad', result.iloc[1]['labels'])
        self.assertEqual('angry', result.iloc[2]['labels'])

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.base_path = Path(EvaDB_TEST_DATA_DIR) / 'data' / 'emotion_detector'

class FastRCNNObjectDetectorTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = os.path.dirname(os.path.abspath(__file__))

    def _load_image(self, path):
        try_to_import_cv2()
        import cv2
        img = cv2.imread(path)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @unittest.skip('disable test due to model downloading time')
    def test_should_return_batches_equivalent_to_number_of_frames(self):
        from evadb.functions.fastrcnn_object_detector import FastRCNNObjectDetector
        frame_dog = {'id': 1, 'data': self._load_image(os.path.join(self.base_path, 'data', 'dog.jpeg'))}
        frame_dog_cat = {'id': 2, 'data': self._load_image(os.path.join(self.base_path, 'data', 'dog_cat.jpg'))}
        frame_batch = Batch(pd.DataFrame([frame_dog, frame_dog_cat]))
        detector = FastRCNNObjectDetector()
        result = detector.classify(frame_batch)
        self.assertEqual(['dog'], result[0].labels)
        self.assertEqual(['cat', 'dog'], result[1].labels)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.base_path = os.path.dirname(os.path.abspath(__file__))

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.base_path = os.path.dirname(os.path.abspath(__file__))

class FaceNet(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_path = Path(EvaDB_TEST_DATA_DIR) / 'data' / 'facenet'

    def _load_image(self, path):
        assert path.exists(), f'File does not exist at the path {str(path)}'
        try_to_import_cv2()
        import cv2
        img = cv2.imread(str(path))
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @windows_skip_marker
    def test_should_return_batches_equivalent_to_number_of_frames(self):
        from evadb.functions.face_detector import FaceDetector
        single_face_img = Path('data/facenet/one.jpg')
        multi_face_img = Path('data/facenet/multiface.jpg')
        frame_single_face = {'id': 1, 'data': self._load_image(single_face_img)}
        frame_multifaces = {'id': 2, 'data': self._load_image(multi_face_img)}
        frame_batch = Batch(pd.DataFrame([frame_single_face, frame_single_face]))
        detector = FaceDetector()
        result = detector(frame_batch.project(['data']).frames)
        self.assertEqual(1, len(result.iloc[0]['bboxes']))
        self.assertEqual(1, len(result.iloc[1]['bboxes']))
        frame_batch = Batch(pd.DataFrame([frame_multifaces]))
        detector = FaceDetector()
        result = detector(frame_batch.project(['data']).frames)
        self.assertEqual(6, len(result.iloc[0]['bboxes']))

    @unittest.skip('Needs GPU')
    def test_should_run_on_gpu(self):
        from evadb.functions.face_detector import FaceDetector
        single_face_img = Path('data/facenet/one.jpg')
        frame_single_face = {'id': 1, 'data': self._load_image(single_face_img)}
        frame_batch = Batch(pd.DataFrame([frame_single_face, frame_single_face]))
        detector = FaceDetector().to_device(0)
        result = detector(frame_batch.project(['data']).frames)
        self.assertEqual(6, len(result.iloc[0]['bboxes']))

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.base_path = Path(EvaDB_TEST_DATA_DIR) / 'data' / 'facenet'

class RelationalAPI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.db_dir = suffix_pytest_xdist_worker_id_to_dir(EvaDB_DATABASE_DIR)
        cls.conn = connect(cls.db_dir)
        cls.evadb = cls.conn._evadb

    def setUp(self):
        self.evadb.catalog().reset()
        self.mnist_path = f'{EvaDB_ROOT_DIR}/data/mnist/mnist.mp4'
        load_functions_for_testing(self.evadb)
        self.images = f'{EvaDB_ROOT_DIR}/data/detoxify/*.jpg'

    def tearDown(self):
        shutdown_ray()
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS mnist_video;')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS meme_images;')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS dummy_table;')

    def test_relation_apis(self):
        cursor = self.conn.cursor()
        rel = cursor.load(self.mnist_path, table_name='mnist_video', format='video')
        rel.execute()
        rel = cursor.table('mnist_video')
        assert_frame_equal(rel.df(), cursor.query('select * from mnist_video;').df())
        rel = rel.select('_row_id, id, data')
        assert_frame_equal(rel.df(), cursor.query('select _row_id, id, data from mnist_video;').df())
        rel = rel.filter('id < 10')
        assert_frame_equal(rel.df(), cursor.query('select _row_id, id, data from mnist_video where id < 10;').df())
        rel = rel.cross_apply('unnest(MnistImageClassifier(data))', 'mnist(label)').filter('mnist.label = 1').select('_row_id, id')
        query = ' select _row_id, id\n                    from mnist_video\n                        join lateral unnest(MnistImageClassifier(data)) AS mnist(label)\n                    where id < 10 AND mnist.label = 1;'
        assert_frame_equal(rel.df(), cursor.query(query).df())
        rel = cursor.load(self.images, table_name='meme_images', format='image')
        rel.execute()
        rel = cursor.table('meme_images').select('_row_id, name')
        assert_frame_equal(rel.df(), cursor.query('select _row_id, name from meme_images;').df())
        rel = rel.filter('_row_id < 3')
        assert_frame_equal(rel.df(), cursor.query('select _row_id, name from meme_images where _row_id < 3;').df())

    def test_relation_api_chaining(self):
        cursor = self.conn.cursor()
        rel = cursor.load(self.mnist_path, table_name='mnist_video', format='video')
        rel.execute()
        rel = cursor.table('mnist_video').select('id, data').filter('id > 10').filter('id < 20')
        assert_frame_equal(rel.df(), cursor.query('select id, data from mnist_video where id > 10 AND id < 20;').df())

    def test_interleaving_calls(self):
        cursor = self.conn.cursor()
        rel = cursor.load(self.mnist_path, table_name='mnist_video', format='video')
        rel.execute()
        rel = cursor.table('mnist_video')
        filtered_rel = rel.filter('id > 10')
        assert_frame_equal(rel.filter('id > 10').df(), cursor.query('select * from mnist_video where id > 10;').df())
        assert_frame_equal(filtered_rel.select('_row_id, id').df(), cursor.query('select _row_id, id from mnist_video where id > 10;').df())

    @qdrant_skip_marker
    def test_create_index(self):
        cursor = self.conn.cursor()
        rel = cursor.load(self.images, table_name='meme_images', format='image')
        rel.execute()
        cursor.query(f"CREATE FUNCTION IF NOT EXISTS SiftFeatureExtractor\n                IMPL  '{EvaDB_ROOT_DIR}/evadb/functions/sift_feature_extractor.py'").df()
        cursor.create_vector_index('faiss_index', table_name='meme_images', expr='SiftFeatureExtractor(data)', using='QDRANT').df()
        base_image = f'{EvaDB_ROOT_DIR}/data/detoxify/meme1.jpg'
        rel = cursor.table('meme_images').order(f"Similarity(SiftFeatureExtractor(Open('{base_image}')), SiftFeatureExtractor(data))").limit(1).select('name')
        similarity_sql = 'SELECT name FROM meme_images\n                            ORDER BY\n                                Similarity(SiftFeatureExtractor(Open("{}")), SiftFeatureExtractor(data))\n                            LIMIT 1;'.format(base_image)
        assert_frame_equal(rel.df(), cursor.query(similarity_sql).df())

    def test_create_function_with_relational_api(self):
        video_file_path = create_sample_video(10)
        cursor = self.conn.cursor()
        rel = cursor.load(video_file_path, table_name='dummy_video', format='video')
        rel.execute()
        create_dummy_object_detector_function = cursor.create_function('DummyObjectDetector', if_not_exists=True, impl_path='test/util.py')
        create_dummy_object_detector_function.execute()
        args = {'task': 'automatic-speech-recognition', 'model': 'openai/whisper-base'}
        create_speech_recognizer_function_if_not_exists = cursor.create_function('SpeechRecognizer', if_not_exists=True, type='HuggingFace', **args)
        query = create_speech_recognizer_function_if_not_exists.sql_query()
        self.assertEqual(query, "CREATE FUNCTION IF NOT EXISTS SpeechRecognizer TYPE HuggingFace TASK 'automatic-speech-recognition' MODEL 'openai/whisper-base'")
        create_speech_recognizer_function_if_not_exists.execute()
        create_speech_recognizer_function = cursor.create_function('SpeechRecognizer', if_not_exists=False, type='HuggingFace', **args)
        query = create_speech_recognizer_function.sql_query()
        self.assertEqual(query, "CREATE FUNCTION SpeechRecognizer TYPE HuggingFace TASK 'automatic-speech-recognition' MODEL 'openai/whisper-base'")
        with self.assertRaises(ExecutorError):
            create_speech_recognizer_function.execute()
        select_query_sql = 'SELECT id, DummyObjectDetector(data) FROM dummy_video ORDER BY id;'
        actual_batch = cursor.query(select_query_sql).execute()
        labels = DummyObjectDetector().labels
        expected = [{'id': i, 'label': np.array([labels[1 + i % 2]])} for i in range(10)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)
        actual_batch = cursor.query(select_query_sql).execute(drop_alias=False)
        expected = [{'dummy_video.id': i, 'dummyobjectdetector.label': np.array([labels[1 + i % 2]])} for i in range(10)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)

    def test_drop_with_relational_api(self):
        video_file_path = create_sample_video(10)
        cursor = self.conn.cursor()
        rel = cursor.load(video_file_path, table_name='dummy_video', format='video')
        rel.execute()
        create_dummy_object_detector_function = cursor.create_function('DummyObjectDetector', if_not_exists=True, impl_path='test/util.py')
        create_dummy_object_detector_function.execute()
        drop_dummy_object_detector_function = cursor.drop_function('DummyObjectDetector', if_exists=True)
        drop_dummy_object_detector_function.execute()
        select_query_sql = 'SELECT id, DummyObjectDetector(data) FROM dummy_video ORDER BY id;'
        with self.assertRaises(BinderError):
            cursor.query(select_query_sql).execute()
        drop_dummy_object_detector_function = cursor.drop_function('DummyObjectDetector', if_exists=True)
        drop_dummy_object_detector_function.execute()
        drop_dummy_object_detector_function = cursor.drop_function('DummyObjectDetector', if_exists=False)
        with self.assertRaises(ExecutorError):
            drop_dummy_object_detector_function.execute()
        drop_table = cursor.drop_table('dummy_video', if_exists=True)
        drop_table.execute()
        select_query_sql = 'SELECT id, data FROM dummy_video ORDER BY id;'
        with self.assertRaises(BinderError):
            cursor.query(select_query_sql).execute()
        drop_table = cursor.drop_table('dummy_video', if_exists=True)
        drop_table.execute()
        drop_table = cursor.drop_table('dummy_video', if_exists=False)
        with self.assertRaises(ExecutorError):
            drop_table.execute()

    def test_pdf_similarity_search(self):
        conn = connect()
        cursor = conn.cursor()
        pdf_path = f'{EvaDB_ROOT_DIR}/data/documents/state_of_the_union.pdf'
        load_pdf = cursor.load(file_regex=pdf_path, format='PDF', table_name='PDFs')
        load_pdf.execute()
        function_check = cursor.drop_function('SentenceFeatureExtractor')
        function_check.df()
        function = cursor.create_function('SentenceFeatureExtractor', True, f'{EvaDB_ROOT_DIR}/evadb/functions/sentence_feature_extractor.py')
        function.execute()
        cursor.create_vector_index('faiss_index', table_name='PDFs', expr='SentenceFeatureExtractor(data)', using='FAISS').df()
        query = cursor.table('PDFs').order("Similarity(\n                    SentenceFeatureExtractor('When was the NATO created?'), SentenceFeatureExtractor(data)\n                ) DESC").limit(3).select('data')
        output = query.df()
        self.assertEqual(len(output), 3)
        self.assertTrue('data' in output.columns)
        output = query.df(drop_alias=False)
        self.assertTrue('pdfs.data' in output.columns)
        cursor.drop_index('faiss_index').df()

    def test_langchain_split_doc(self):
        conn = connect()
        cursor = conn.cursor()
        pdf_path1 = f'{EvaDB_ROOT_DIR}/data/documents/state_of_the_union.pdf'
        load_pdf = cursor.load(file_regex=pdf_path1, format='DOCUMENT', table_name='docs')
        load_pdf.execute()
        result1 = cursor.table('docs', chunk_size=2000, chunk_overlap=DEFAULT_DOCUMENT_CHUNK_OVERLAP).select('data').df()
        result2 = cursor.table('docs', chunk_size=DEFAULT_DOCUMENT_CHUNK_SIZE, chunk_overlap=2000).select('data').df()
        result3 = cursor.table('docs', chunk_size=DEFAULT_DOCUMENT_CHUNK_SIZE, chunk_overlap=0).select('data').df()
        self.assertGreater(len(result1), len(result2))
        self.assertGreater(len(result2), len(result3))
        result5 = cursor.table('docs', chunk_size=2000).select('data').df()
        self.assertEqual(len(result5), len(result1))
        result4 = cursor.table('docs', chunk_overlap=0).select('data').df()
        self.assertEqual(len(result3), len(result4))
        result1 = cursor.table('docs').select('data').df()
        result2 = cursor.query(f'SELECT data from docs chunk_size {DEFAULT_DOCUMENT_CHUNK_SIZE} chunk_overlap {DEFAULT_DOCUMENT_CHUNK_OVERLAP}').df()
        self.assertEqual(len(result1), len(result2))

    def test_show_relational(self):
        video_file_path = create_sample_video(10)
        cursor = self.conn.cursor()
        rel = cursor.load(video_file_path, table_name='dummy_video', format='video')
        rel.execute()
        result = cursor.show('tables').df()
        self.assertEqual(len(result), 1)
        self.assertEqual(result['name'][0], 'dummy_video')

    def test_explain_relational(self):
        video_file_path = create_sample_video(10)
        cursor = self.conn.cursor()
        rel = cursor.load(video_file_path, table_name='dummy_video', format='video')
        rel.execute()
        result = cursor.explain('SELECT * FROM dummy_video').df()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], '|__ ProjectPlan\n    |__ SeqScanPlan\n        |__ StoragePlan\n')

    def test_rename_relational(self):
        video_file_path = create_sample_video(10)
        cursor = self.conn.cursor()
        rel = cursor.load(video_file_path, table_name='dummy_video', format='video')
        rel.execute()
        cursor.rename('dummy_video', 'dummy_video_renamed').df()
        result = cursor.show('tables').df()
        self.assertEqual(len(result), 1)
        self.assertEqual(result['name'][0], 'dummy_video_renamed')

    def test_create_table_relational(self):
        cursor = self.conn.cursor()
        cursor.create_table(table_name='dummy_table', if_not_exists=True, columns='id INTEGER, name text(30)').df()
        result = cursor.show('tables').df()
        self.assertEqual(len(result), 1)
        self.assertEqual(result['name'][0], 'dummy_table')
        rel = cursor.create_table(table_name='dummy_table', if_not_exists=False, columns='id INTEGER, name text(30)')
        with self.assertRaises(ExecutorError):
            rel.execute()

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class EvaDBImportTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_evadb_cli_imports(self):
        """
        Testing imports for running client and server packages,
        when current working directory is changed.
        """
        cur_dir = os.getcwd()
        new_dir = os.path.join('test_evadb', 'test')
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        os.chdir(new_dir)
        _ = importlib.import_module('evadb.evadb_cmd_client')
        _ = importlib.import_module('evadb.evadb_server')
        os.chdir(cur_dir)
        shutil.rmtree(new_dir)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class ServerTests(unittest.IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @patch('asyncio.start_server')
    async def test_server_functions(self, mock_start):
        evadb_server = EvaServer()
        host = 'localhost'
        port = 8803
        await evadb_server.start_evadb_server(EvaDB_DATABASE_DIR, host, port)
        client_reader1 = asyncio.StreamReader()
        client_writer1 = MagicMock()
        client_reader2 = asyncio.StreamReader()
        client_writer2 = MagicMock()
        client_reader1.feed_data(b'SHOW FUNCTIONS;\n')
        client_reader1.feed_data(b'EXIT;\n')
        await evadb_server.accept_client(client_reader1, client_writer1)
        assert len(evadb_server._clients) == 1
        client_reader2.feed_data(b'\xc4pple')
        client_reader2.feed_eof()
        await evadb_server.accept_client(client_reader2, client_writer2)
        assert len(evadb_server._clients) == 2
        await evadb_server.handle_client(client_reader2, client_writer2)
        await evadb_server.stop_evadb_server()

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class ConfigurationFileTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @ray_skip_marker
    def test_check_configuration_file(self):
        config_file_path = os.path.join(EvaDB_ROOT_DIR, 'evadb', EvaDB_CONFIG_FILE)
        import yaml
        with open(config_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
            ray_setting = yaml_data.get('experimental').get('ray')
            self.assertEquals(ray_setting, False)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class InterpreterTests(unittest.IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @patch('asyncio.open_connection')
    @patch('evadb.server.interpreter.create_stdin_reader')
    @patch('evadb.interfaces.relational.db.EvaDBCursor.execute_async')
    @patch('evadb.interfaces.relational.db.EvaDBCursor.fetch_all_async')
    async def test_start_cmd_client(self, mock_fetch, mock_execute, mock_stdin_reader, mock_open):
        host = 'localhost'
        port = find_free_port()
        server_reader = asyncio.StreamReader()
        server_writer = MagicMock()
        server_reader.feed_data(b'SHOW FUNCTIONS;\n')
        server_reader.feed_data(b'EXIT;\n')
        mock_open.return_value = (server_reader, server_writer)
        stdin_reader = asyncio.StreamReader()
        stdin_reader.feed_data(b'SHOW FUNCTIONS;\n')
        stdin_reader.feed_data(b'EXIT;\n')
        stdin_reader.feed_eof()
        mock_stdin_reader.return_value = stdin_reader
        await start_cmd_client(host, port)

    @patch('asyncio.open_connection')
    async def test_exception_in_start_cmd_client(self, mock_open):
        mock_open.side_effect = Exception('open')
        await start_cmd_client(MagicMock(), MagicMock())

    @macos_skip_marker
    @patch('asyncio.events.AbstractEventLoop.connect_read_pipe')
    async def test_create_stdin_reader(self, mock_read_pipe):
        try:
            stdin_reader = await create_stdin_reader()
            self.assertNotEqual(stdin_reader, None)
        except Exception:
            pass

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

def test_union_plan(self):
    all = True
    plan = UnionPlan(all)
    self.assertEqual(plan.opr_type, PlanOprType.UNION)
    self.assertEqual(plan.all, all)

class JobSchedulerTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_dummy_job_catalog_entry(self, active, job_name, next_run):
        return JobCatalogEntry(name=job_name, queries=None, start_time=None, end_time=None, repeat_interval=None, active=active, next_scheduled_run=next_run, created_at=None, updated_at=None)

    def test_sleep_time_calculation(self):
        past_job = self.get_dummy_job_catalog_entry(True, 'past_job', datetime.now() - timedelta(seconds=10))
        future_job = self.get_dummy_job_catalog_entry(True, 'future_job', datetime.now() + timedelta(seconds=20))
        job_scheduler = JobScheduler(MagicMock())
        self.assertEqual(job_scheduler._get_sleep_time(past_job), 0)
        self.assertGreaterEqual(job_scheduler._get_sleep_time(future_job), 10)
        self.assertEqual(job_scheduler._get_sleep_time(None), 30)

    def test_update_next_schedule_run(self):
        future_time = datetime.now() + timedelta(seconds=1000)
        job_scheduler = JobScheduler(MagicMock())
        job_entry = self.get_dummy_job_catalog_entry(True, 'job', datetime.now())
        job_entry.end_time = future_time
        status, next_run = job_scheduler._update_next_schedule_run(job_entry)
        self.assertEqual(status, False, 'status for one time job should be false')
        job_entry.end_time = future_time
        job_entry.repeat_interval = 120
        expected_next_run = datetime.now() + timedelta(seconds=120)
        status, next_run = job_scheduler._update_next_schedule_run(job_entry)
        self.assertEqual(status, True, 'status for recurring time job should be true')
        self.assertGreaterEqual(next_run, expected_next_run)
        job_entry.end_time = datetime.now() + timedelta(seconds=60)
        job_entry.repeat_interval = 120
        expected_next_run = datetime.now() + timedelta(seconds=120)
        status, next_run = job_scheduler._update_next_schedule_run(job_entry)
        self.assertEqual(status, False, 'status for rexpired ecurring time job should be false')
        self.assertLessEqual(next_run, datetime.now())

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class ConstantExpressionsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_constant_with_input_relationship(self):
        const_expr = ConstantValueExpression(1)
        input_size = 10
        self.assertEqual([1] * input_size, const_expr.evaluate(Batch(pd.DataFrame([0] * input_size))).frames[0].tolist())

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class LogicalExpressionsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = Batch(pd.DataFrame([0]))

    def test_logical_and(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(1)
        comparison_expression_left = ComparisonExpression(ExpressionType.COMPARE_EQUAL, const_exp1, const_exp2)
        const_exp1 = ConstantValueExpression(2)
        const_exp2 = ConstantValueExpression(1)
        comparison_expression_right = ComparisonExpression(ExpressionType.COMPARE_GREATER, const_exp1, const_exp2)
        logical_expr = LogicalExpression(ExpressionType.LOGICAL_AND, comparison_expression_left, comparison_expression_right)
        self.assertEqual([True], logical_expr.evaluate(self.batch).frames[0].tolist())

    def test_logical_or(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(1)
        comparison_expression_left = ComparisonExpression(ExpressionType.COMPARE_EQUAL, const_exp1, const_exp2)
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(2)
        comparison_expression_right = ComparisonExpression(ExpressionType.COMPARE_GREATER, const_exp1, const_exp2)
        logical_expr = LogicalExpression(ExpressionType.LOGICAL_OR, comparison_expression_left, comparison_expression_right)
        self.assertEqual([True], logical_expr.evaluate(self.batch).frames[0].tolist())

    def test_logical_not(self):
        const_exp1 = ConstantValueExpression(0)
        const_exp2 = ConstantValueExpression(1)
        comparison_expression_right = ComparisonExpression(ExpressionType.COMPARE_GREATER, const_exp1, const_exp2)
        logical_expr = LogicalExpression(ExpressionType.LOGICAL_NOT, None, comparison_expression_right)
        self.assertEqual([True], logical_expr.evaluate(self.batch).frames[0].tolist())

    def test_short_circuiting_and_complete(self):
        tup_val_exp_l = TupleValueExpression(name=0)
        tup_val_exp_l.col_alias = 0
        tup_val_exp_r = TupleValueExpression(name=1)
        tup_val_exp_r.col_alias = 1
        comp_exp_l = ComparisonExpression(ExpressionType.COMPARE_EQUAL, tup_val_exp_l, tup_val_exp_r)
        comp_exp_r = Mock(spec=ComparisonExpression)
        logical_exp = LogicalExpression(ExpressionType.LOGICAL_AND, comp_exp_l, comp_exp_r)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [4, 5, 6]}))
        self.assertEqual([False, False, False], logical_exp.evaluate(tuples).frames[0].tolist())
        comp_exp_r.evaluate.assert_not_called()

    def test_short_circuiting_or_complete(self):
        tup_val_exp_l = TupleValueExpression(name=0)
        tup_val_exp_l.col_alias = 0
        tup_val_exp_r = TupleValueExpression(name=1)
        tup_val_exp_r.col_alias = 1
        comp_exp_l = ComparisonExpression(ExpressionType.COMPARE_EQUAL, tup_val_exp_l, tup_val_exp_r)
        comp_exp_r = Mock(spec=ComparisonExpression)
        logical_exp = LogicalExpression(ExpressionType.LOGICAL_OR, comp_exp_l, comp_exp_r)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [1, 2, 3]}))
        self.assertEqual([True, True, True], logical_exp.evaluate(tuples).frames[0].tolist())
        comp_exp_r.evaluate.assert_not_called()

    def test_short_circuiting_and_partial(self):
        tup_val_exp_l = TupleValueExpression(name=0)
        tup_val_exp_l.col_alias = 0
        tup_val_exp_r = TupleValueExpression(name=1)
        tup_val_exp_r.col_alias = 1
        comp_exp_l = ComparisonExpression(ExpressionType.COMPARE_EQUAL, tup_val_exp_l, tup_val_exp_r)
        comp_exp_r = Mock(spec=ComparisonExpression)
        comp_exp_r.evaluate = Mock(return_value=Mock(_frames=[[True], [False]]))
        logical_exp = LogicalExpression(ExpressionType.LOGICAL_AND, comp_exp_l, comp_exp_r)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3, 4], 1: [1, 2, 5, 6]}))
        self.assertEqual([True, False, False, False], logical_exp.evaluate(tuples).frames[0].tolist())
        comp_exp_r.evaluate.assert_called_once_with(tuples[[0, 1]])

    def test_short_circuiting_or_partial(self):
        tup_val_exp_l = TupleValueExpression(name=0)
        tup_val_exp_l.col_alias = 0
        tup_val_exp_r = TupleValueExpression(name=1)
        tup_val_exp_r.col_alias = 1
        comp_exp_l = ComparisonExpression(ExpressionType.COMPARE_EQUAL, tup_val_exp_l, tup_val_exp_r)
        comp_exp_r = Mock(spec=ComparisonExpression)
        comp_exp_r.evaluate = Mock(return_value=Mock(_frames=[[True], [False]]))
        logical_exp = LogicalExpression(ExpressionType.LOGICAL_OR, comp_exp_l, comp_exp_r)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3, 4], 1: [5, 6, 3, 4]}))
        self.assertEqual([True, False, True, True], logical_exp.evaluate(tuples).frames[0].tolist())
        comp_exp_r.evaluate.assert_called_once_with(tuples[[0, 1]])

    def test_multiple_logical(self):
        batch = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        comp_left = ComparisonExpression(ExpressionType.COMPARE_GREATER, TupleValueExpression(col_alias='col'), ConstantValueExpression(1))
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[list(range(2, 10))]
        batch_copy.drop_zero(comp_left.evaluate(batch))
        self.assertEqual(batch_copy, expected)
        comp_right = ComparisonExpression(ExpressionType.COMPARE_LESSER, TupleValueExpression(col_alias='col'), ConstantValueExpression(8))
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[list(range(0, 8))]
        batch_copy.drop_zero(comp_right.evaluate(batch))
        self.assertEqual(batch_copy, expected)
        comp_expr = ComparisonExpression(ExpressionType.COMPARE_GEQ, TupleValueExpression(col_alias='col'), ConstantValueExpression(5))
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[list(range(5, 10))]
        batch_copy.drop_zero(comp_expr.evaluate(batch))
        self.assertEqual(batch_copy, expected)
        l_expr = LogicalExpression(ExpressionType.LOGICAL_AND, comp_left, comp_right)
        root_l_expr = LogicalExpression(ExpressionType.LOGICAL_AND, comp_expr, l_expr)
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[[5, 6, 7]]
        batch_copy.drop_zero(root_l_expr.evaluate(batch))
        self.assertEqual(batch_copy, expected)
        root_l_expr = LogicalExpression(ExpressionType.LOGICAL_AND, l_expr, comp_expr)
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[[5, 6, 7]]
        batch_copy.drop_zero(root_l_expr.evaluate(batch))
        self.assertEqual(batch_copy, expected)
        between_4_7 = LogicalExpression(ExpressionType.LOGICAL_AND, ComparisonExpression(ExpressionType.COMPARE_GEQ, TupleValueExpression(col_alias='col'), ConstantValueExpression(4)), ComparisonExpression(ExpressionType.COMPARE_LEQ, TupleValueExpression(col_alias='col'), ConstantValueExpression(7)))
        test_expr = LogicalExpression(ExpressionType.LOGICAL_AND, between_4_7, l_expr)
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[[4, 5, 6, 7]]
        batch_copy.drop_zero(test_expr.evaluate(batch))
        self.assertEqual(batch_copy, expected)
        test_expr = LogicalExpression(ExpressionType.LOGICAL_OR, between_4_7, l_expr)
        batch_copy = Batch(pd.DataFrame({'col': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}))
        expected = batch[[2, 3, 4, 5, 6, 7]]
        batch_copy.drop_zero(test_expr.evaluate(batch))
        self.assertEqual(batch_copy, expected)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.batch = Batch(pd.DataFrame([0]))

class ComparisonExpressionsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = Batch(pd.DataFrame([0]))

    def test_comparison_compare_equal(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(1)
        cmpr_exp = ComparisonExpression(ExpressionType.COMPARE_EQUAL, const_exp1, const_exp2)
        self.assertEqual([True], cmpr_exp.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp), None)

    def test_comparison_compare_greater(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(0)
        cmpr_exp = ComparisonExpression(ExpressionType.COMPARE_GREATER, const_exp1, const_exp2)
        self.assertEqual([True], cmpr_exp.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp), None)

    def test_comparison_compare_lesser(self):
        const_exp1 = ConstantValueExpression(0)
        const_exp2 = ConstantValueExpression(2)
        cmpr_exp = ComparisonExpression(ExpressionType.COMPARE_LESSER, const_exp1, const_exp2)
        self.assertEqual([True], cmpr_exp.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp), None)

    def test_comparison_compare_geq(self):
        const_exp1 = ConstantValueExpression(1)
        const_exp2 = ConstantValueExpression(1)
        const_exp3 = ConstantValueExpression(0)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_GEQ, const_exp1, const_exp2)
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_GEQ, const_exp1, const_exp3)
        self.assertEqual([True], cmpr_exp1.evaluate(self.batch).frames[0].tolist())
        self.assertEqual([True], cmpr_exp2.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp1), None)

    def test_comparison_compare_leq(self):
        const_exp1 = ConstantValueExpression(0)
        const_exp2 = ConstantValueExpression(2)
        const_exp3 = ConstantValueExpression(2)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_LEQ, const_exp1, const_exp2)
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_LEQ, const_exp2, const_exp3)
        self.assertEqual([True], cmpr_exp1.evaluate(self.batch).frames[0].tolist())
        self.assertEqual([True], cmpr_exp2.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp1), None)

    def test_comparison_compare_neq(self):
        const_exp1 = ConstantValueExpression(0)
        const_exp2 = ConstantValueExpression(1)
        cmpr_exp = ComparisonExpression(ExpressionType.COMPARE_NEQ, const_exp1, const_exp2)
        self.assertEqual([True], cmpr_exp.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp), None)

    def test_comparison_compare_contains(self):
        const_exp1 = ConstantValueExpression([1, 2], ColumnType.NDARRAY)
        const_exp2 = ConstantValueExpression([1, 5], ColumnType.NDARRAY)
        const_exp3 = ConstantValueExpression([1, 2, 3, 4], ColumnType.NDARRAY)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_CONTAINS, const_exp3, const_exp1)
        self.assertEqual([True], cmpr_exp1.evaluate(self.batch).frames[0].tolist())
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_CONTAINS, const_exp3, const_exp2)
        self.assertEqual([False], cmpr_exp2.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp1), None)

    def test_comparison_compare_is_contained(self):
        const_exp1 = ConstantValueExpression([1, 2], ColumnType.NDARRAY)
        const_exp2 = ConstantValueExpression([1, 5], ColumnType.NDARRAY)
        const_exp3 = ConstantValueExpression([1, 2, 3, 4], ColumnType.NDARRAY)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_IS_CONTAINED, const_exp1, const_exp3)
        self.assertEqual([True], cmpr_exp1.evaluate(self.batch).frames[0].tolist())
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_IS_CONTAINED, const_exp2, const_exp3)
        self.assertEqual([False], cmpr_exp2.evaluate(self.batch).frames[0].tolist())
        self.assertNotEqual(str(cmpr_exp1), None)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.batch = Batch(pd.DataFrame([0]))

class ArithmeticExpressionsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = Batch(pd.DataFrame([None]))

    def test_addition(self):
        const_exp1 = ConstantValueExpression(2)
        const_exp2 = ConstantValueExpression(5)
        cmpr_exp = ArithmeticExpression(ExpressionType.ARITHMETIC_ADD, const_exp1, const_exp2)
        self.assertEqual([7], cmpr_exp.evaluate(self.batch).frames[0].tolist())

    def test_subtraction(self):
        const_exp1 = ConstantValueExpression(5)
        const_exp2 = ConstantValueExpression(2)
        cmpr_exp = ArithmeticExpression(ExpressionType.ARITHMETIC_SUBTRACT, const_exp1, const_exp2)
        self.assertEqual([3], cmpr_exp.evaluate(self.batch).frames[0].tolist())

    def test_multiply(self):
        const_exp1 = ConstantValueExpression(3)
        const_exp2 = ConstantValueExpression(5)
        cmpr_exp = ArithmeticExpression(ExpressionType.ARITHMETIC_MULTIPLY, const_exp1, const_exp2)
        self.assertEqual([15], cmpr_exp.evaluate(self.batch).frames[0].tolist())

    def test_divide(self):
        const_exp1 = ConstantValueExpression(5)
        const_exp2 = ConstantValueExpression(5)
        cmpr_exp = ArithmeticExpression(ExpressionType.ARITHMETIC_DIVIDE, const_exp1, const_exp2)
        self.assertEqual([1], cmpr_exp.evaluate(self.batch).frames[0].tolist())

    def test_aaequality(self):
        const_exp1 = ConstantValueExpression(5)
        const_exp2 = ConstantValueExpression(15)
        cmpr_exp = ArithmeticExpression(ExpressionType.ARITHMETIC_DIVIDE, const_exp1, const_exp2)
        cmpr_exp2 = ArithmeticExpression(ExpressionType.ARITHMETIC_MULTIPLY, const_exp1, const_exp2)
        cmpr_exp3 = ArithmeticExpression(ExpressionType.ARITHMETIC_MULTIPLY, const_exp2, const_exp1)
        self.assertNotEqual(cmpr_exp, cmpr_exp2)
        self.assertNotEqual(cmpr_exp2, cmpr_exp3)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.batch = Batch(pd.DataFrame([None]))

class AggregationExpressionsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_aggregation_first(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_FIRST, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(1, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_last(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_LAST, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(3, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_segment(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_SEGMENT, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertTrue((np.array([1, 2, 3]) == batch.frames.iloc[0][0]).all())
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_sum(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_SUM, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(6, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_count(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_COUNT, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(3, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_avg(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_AVG, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(2, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_min(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_MIN, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(1, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_max(self):
        columnName = TupleValueExpression(name=0)
        columnName.col_alias = 0
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_MAX, None, columnName)
        tuples = Batch(pd.DataFrame({0: [1, 2, 3], 1: [2, 3, 4], 2: [3, 4, 5]}))
        batch = aggr_expr.evaluate(tuples, None)
        self.assertEqual(3, batch.frames.iloc[0][0])
        self.assertNotEqual(str(aggr_expr), None)

    def test_aggregation_incorrect_etype(self):
        incorrect_etype = 100
        columnName = TupleValueExpression(name=0)
        aggr_expr = AggregationExpression(incorrect_etype, columnName, columnName)
        with pytest.raises(NotImplementedError):
            str(aggr_expr)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

@pytest.mark.notparallel
class SQLStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = None

    def create_sample_table(self):
        table_info = TableCatalogEntry(str(suffix_pytest_xdist_worker_id_to_dir('dataset')), str(suffix_pytest_xdist_worker_id_to_dir('dataset')), table_type=TableType.VIDEO_DATA)
        column_pk = ColumnCatalogEntry(IDENTIFIER_COLUMN, ColumnType.INTEGER, is_nullable=False)
        column_0 = ColumnCatalogEntry('name', ColumnType.TEXT, is_nullable=False)
        column_1 = ColumnCatalogEntry('id', ColumnType.INTEGER, is_nullable=False)
        column_2 = ColumnCatalogEntry('data', ColumnType.NDARRAY, False, NdArrayType.UINT8, [2, 2, 3])
        table_info.columns = [column_pk, column_0, column_1, column_2]
        return table_info

    def setUp(self):
        self.table = self.create_sample_table()

    def tearDown(self):
        try:
            shutil.rmtree(suffix_pytest_xdist_worker_id_to_dir('dataset'), ignore_errors=True)
        except ValueError:
            pass

    def test_should_create_empty_table(self):
        evadb = get_evadb_for_testing()
        sqlengine = SQLStorageEngine(evadb)
        sqlengine.create(self.table)
        records = list(sqlengine.read(self.table, batch_mem_size=3000))
        self.assertEqual(len(records), 0)
        sqlengine.drop(self.table)

    def test_should_write_rows_to_table(self):
        dummy_batches = list(create_dummy_batches())
        dummy_batches = [batch.project(batch.columns[1:]) for batch in dummy_batches]
        evadb = get_evadb_for_testing()
        sqlengine = SQLStorageEngine(evadb)
        sqlengine.create(self.table)
        for batch in dummy_batches:
            batch.drop_column_alias()
            sqlengine.write(self.table, batch)
        read_batch = list(sqlengine.read(self.table, batch_mem_size=3000))
        self.assertTrue(read_batch, dummy_batches)
        sqlengine.drop(self.table)

    def test_rename(self):
        table_info = TableCatalogEntry('new_name', 'new_name', table_type=TableType.VIDEO_DATA)
        evadb = get_evadb_for_testing()
        sqlengine = SQLStorageEngine(evadb)
        with pytest.raises(Exception):
            sqlengine.rename(self.table, table_info)

    def test_sqlite_storage_engine_exceptions(self):
        evadb = get_evadb_for_testing()
        sqlengine = SQLStorageEngine(evadb)
        missing_table_info = TableCatalogEntry('missing_table', None, table_type=TableType.VIDEO_DATA)
        with self.assertRaises(Exception):
            sqlengine.drop(missing_table_info)
        with self.assertRaises(Exception):
            sqlengine.write(missing_table_info, None)
        with self.assertRaises(Exception):
            read_batch = list(sqlengine.read(missing_table_info))
            self.assertEqual(read_batch, None)
        with self.assertRaises(Exception):
            sqlengine.delete(missing_table_info, None)

    def test_cannot_delete_missing_column(self):
        evadb = get_evadb_for_testing()
        sqlengine = SQLStorageEngine(evadb)
        sqlengine.create(self.table)
        incorrect_where_clause = {'foo': None}
        with self.assertRaises(Exception):
            sqlengine.delete(self.table, incorrect_where_clause)
        sqlengine.drop(self.table)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.table = None

@pytest.mark.notparallel
class VideoStorageEngineTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table = None

    def create_sample_table(self):
        table_info = TableCatalogEntry(str(suffix_pytest_xdist_worker_id_to_dir('dataset')), str(suffix_pytest_xdist_worker_id_to_dir('dataset')), table_type=TableType.VIDEO_DATA)
        column_1 = ColumnCatalogEntry('id', ColumnType.INTEGER, False)
        column_2 = ColumnCatalogEntry('data', ColumnType.NDARRAY, False, NdArrayType.UINT8, [2, 2, 3])
        table_info.schema = [column_1, column_2]
        return table_info

    def setUp(self):
        evadb = get_evadb_for_testing()
        mock.table_type = TableType.VIDEO_DATA
        self.video_engine = StorageEngine.factory(evadb, mock)
        self.table = self.create_sample_table()

    def tearDown(self):
        pass

    @mock.patch('pathlib.Path.mkdir')
    def test_should_raise_file_exist_error(self, m):
        m.side_effect = FileExistsError
        with self.assertRaises(FileExistsError):
            self.video_engine.create(self.table, if_not_exists=False)
        self.video_engine.create(self.table, if_not_exists=True)

    def test_write(self):
        batch = MagicMock()
        batch.frames = []
        table = MagicMock()
        table.file_url = Exception()
        with self.assertRaises(Exception):
            self.video_engine.write(table, batch)

    def test_delete(self):
        batch = MagicMock()
        batch.frames = []
        table = MagicMock()
        table.file_url = Exception()
        with self.assertRaises(Exception):
            self.video_engine.delete(table, batch)
        self.video_engine.create(self.table, if_not_exists=True)
        video_file_path = create_sample_video()
        df = pd.DataFrame([video_file_path], columns=['file_path'])
        batch = Batch(df)
        with self.assertRaises(Exception):
            self.video_engine.delete(self.table, batch)
        self.video_engine.drop(self.table)

    def test_rename(self):
        table_info = TableCatalogEntry('new_name', 'new_name', table_type=TableType.VIDEO_DATA)
        with pytest.raises(Exception):
            self.video_engine.rename(self.table, table_info)

    def test_media_storage_engine_exceptions(self):
        missing_table_info = TableCatalogEntry('missing_table', None, table_type=TableType.VIDEO_DATA)
        with self.assertRaises(Exception):
            self.video_engine.drop(missing_table_info)
        with self.assertRaises(Exception):
            self.video_engine.write(missing_table_info, None)
        with self.assertRaises(Exception):
            read_batch = list(self.video_engine.read(missing_table_info))
            self.assertEqual(read_batch, None)
        with self.assertRaises(Exception):
            self.video_engine.delete(missing_table_info, None)

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.table = None

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class DeletePlan(AbstractPlan):
    """This plan is used for storing information required for insert
    operations.

    Args:
        table (TableCatalogEntry): table to insert into
        column_list (List[AbstractExpression]): list of annotated column
        value_list (List[AbstractExpression]): list of abstract expression
                                                for the values to insert
    """

    def __init__(self, table_ref: TableRef, where_clause: AbstractExpression=None):
        super().__init__(PlanOprType.DELETE)
        self._table_ref = table_ref
        self._where_clause = where_clause

    @property
    def table_ref(self):
        return self._table_ref

    @property
    def where_clause(self):
        return self._where_clause

    def __str__(self):
        return 'DeletePlan(table={},             where_clause={})'.format(self.table_ref, self._where_clause)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_ref, self._where_clause))

def __init__(self, table_ref: TableRef, where_clause: AbstractExpression=None):
    super().__init__(PlanOprType.DELETE)
    self._table_ref = table_ref
    self._where_clause = where_clause

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_ref, self._where_clause))

class ApplyAndMergePlan(AbstractPlan):
    """
    This dataclass stores metadata to perform apply and merge operation.

    Arguments:
        func_expr(FunctionExpression): parameterized function expression that
            reference columns from a table expression that precedes it.
        do_unnest(bool): if True perform unnest operation on the output of FunctionScan
    """

    def __init__(self, func_expr: FunctionExpression, alias: Alias, do_unnest: bool=False):
        self._func_expr = func_expr
        self._alias = alias
        self._do_unnest = do_unnest
        super().__init__(PlanOprType.APPLY_AND_MERGE)

    @property
    def func_expr(self):
        return self._func_expr

    @property
    def alias(self):
        return self._alias

    @property
    def do_unnest(self):
        return self._do_unnest

    def __str__(self):
        plan = 'UnnestApplyAndMergePlan' if self._do_unnest else 'ApplyAndMergePlan'
        return '{}(func_expr={})'.format(plan, self._func_expr)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.func_expr, self.alias, self.do_unnest))

def __init__(self, func_expr: FunctionExpression, alias: Alias, do_unnest: bool=False):
    self._func_expr = func_expr
    self._alias = alias
    self._do_unnest = do_unnest
    super().__init__(PlanOprType.APPLY_AND_MERGE)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.func_expr, self.alias, self.do_unnest))

class RenamePlan(AbstractPlan):
    """
    This plan is used for storing information required for rename table
    operations.
    Arguments:
        old_table {TableRef} -- table ref for table to be renamed in storage
        new_name {TableInfo} -- new name of old_table
    """

    def __init__(self, old_table: TableRef, new_name: TableInfo):
        super().__init__(PlanOprType.RENAME)
        self._old_table = old_table
        self._new_name = new_name

    @property
    def old_table(self):
        return self._old_table

    @property
    def new_name(self):
        return self._new_name

    def __str__(self):
        return 'RenamePlan(old_table={},             new_name={})'.format(self._old_table, self._new_name)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.old_table, self.new_name))

def __init__(self, old_table: TableRef, new_name: TableInfo):
    super().__init__(PlanOprType.RENAME)
    self._old_table = old_table
    self._new_name = new_name

def __hash__(self) -> int:
    return hash((super().__hash__(), self.old_table, self.new_name))

class PredicatePlan(AbstractPlan):
    """
    Arguments:
        predicate (AbstractExpression): A predicate expression used for
        filtering frames
    """

    def __init__(self, predicate: AbstractExpression):
        self.predicate = predicate
        super().__init__(PlanOprType.PREDICATE_FILTER)

    def __str__(self):
        return 'PredicatePlan(predicate={})'.format(self.predicate)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.predicate))

def __init__(self, predicate: AbstractExpression):
    self.predicate = predicate
    super().__init__(PlanOprType.PREDICATE_FILTER)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.predicate))

class HashJoinBuildPlan(AbstractPlan):
    """
    This plan is used for storing information required for hashjoin build side.
    It prepares the hash table of preferably the smaller relation
    which is used by the probe side to find relevant rows.
    Arguments:
        build_keys (List[ColumnCatalogEntry]) : list of equi-key columns.
                        If empty, then Cartesian product.
    """

    def __init__(self, join_type: JoinType, build_keys: List[ColumnCatalogEntry]):
        self.join_type = join_type
        self.build_keys = build_keys
        super().__init__(PlanOprType.HASH_BUILD)

    def __str__(self):
        return 'HashJoinBuildPlan(join_type={},             build_keys={})'.format(self.join_type, self.build_keys)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.join_type, tuple(self.build_keys or [])))

def __init__(self, join_type: JoinType, build_keys: List[ColumnCatalogEntry]):
    self.join_type = join_type
    self.build_keys = build_keys
    super().__init__(PlanOprType.HASH_BUILD)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.join_type, tuple(self.build_keys or [])))

class VectorIndexScanPlan(AbstractPlan):
    """
    The plan first evaluates the `search_query_expr` expression and searches the output
    in the vector index. The plan finally projects `limit_count` number of results.

    Arguments:
        index_name (str): The vector index name.
        limit_count (ConstantValueExpression): Number of top results to project.
        search_query_expr (FunctionExpression): function expression to evaluate, whose
        results will be searched in the vector index.
    """

    def __init__(self, index: IndexCatalogEntry, limit_count: ConstantValueExpression, search_query_expr: FunctionExpression):
        super().__init__(PlanOprType.VECTOR_INDEX_SCAN)
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

    def __str__(self):
        return 'VectorIndexScan(index_name={}, vector_store_type={}, limit_count={}, search_query_expr={})'.format(self._index.name, self._index.vector_store_type, self._limit_count, self._search_query_expr)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.index, self.limit_count, self.search_query_expr))

def __init__(self, index: IndexCatalogEntry, limit_count: ConstantValueExpression, search_query_expr: FunctionExpression):
    super().__init__(PlanOprType.VECTOR_INDEX_SCAN)
    self._index = index
    self._limit_count = limit_count
    self._search_query_expr = search_query_expr

def __hash__(self) -> int:
    return hash((super().__hash__(), self.index, self.limit_count, self.search_query_expr))

class LateralJoinPlan(AbstractJoin):
    """
    This plan is used for storing information required for lateral join
    """

    def __init__(self, join_predicate: AbstractExpression):
        self.join_project = []
        super().__init__(PlanOprType.LATERAL_JOIN, JoinType.LATERAL_JOIN, join_predicate)

    def __str__(self):
        return 'LateralJoinPlan(join_project={},             join_predicate={})'.format(self.join_project, self.join_predicate)

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self.join_project or [])))

def __init__(self, join_predicate: AbstractExpression):
    self.join_project = []
    super().__init__(PlanOprType.LATERAL_JOIN, JoinType.LATERAL_JOIN, join_predicate)

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self.join_project or [])))

class NestedLoopJoinPlan(AbstractJoin):
    """
    This plan is used for storing information required for a nested loop join.
    """

    def __init__(self, join_type: JoinType, join_predicate: AbstractExpression=None):
        self._join_predicate = join_predicate
        super().__init__(PlanOprType.NESTED_LOOP_JOIN, join_type, join_predicate)

    @property
    def join_predicate(self):
        return self._join_predicate

    def __str__(self):
        return 'NestedLoopJoinPlan(join_type={},             predicate={})'.format(self.join_type, self.join_predicate)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.join_type, self.join_predicate))

def __init__(self, join_type: JoinType, join_predicate: AbstractExpression=None):
    self._join_predicate = join_predicate
    super().__init__(PlanOprType.NESTED_LOOP_JOIN, join_type, join_predicate)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.join_type, self.join_predicate))

class AbstractScan(AbstractPlan):
    """Abstract class for all the scan based planners

    Arguments:
        predicate (AbstractExpression): An expression used for filtering
    """

    def __init__(self, opr_type: PlanOprType, predicate: AbstractExpression):
        super(AbstractScan, self).__init__(opr_type)
        self._predicate = predicate

    @property
    def predicate(self) -> AbstractExpression:
        return self._predicate

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.predicate))

def __init__(self, opr_type: PlanOprType, predicate: AbstractExpression):
    super(AbstractScan, self).__init__(opr_type)
    self._predicate = predicate

def __hash__(self) -> int:
    return hash((super().__hash__(), self.predicate))

class ExplainPlan(AbstractPlan):

    def __init__(self, explainable_plan: AbstractPlan):
        super().__init__(PlanOprType.EXPLAIN)
        self._explainable_plan = explainable_plan

    def __str__(self) -> str:
        return 'ExplainPlan()'

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._explainable_plan))

def __init__(self, explainable_plan: AbstractPlan):
    super().__init__(PlanOprType.EXPLAIN)
    self._explainable_plan = explainable_plan

def __hash__(self) -> int:
    return hash((super().__hash__(), self._explainable_plan))

class OrderByPlan(AbstractPlan):
    """
    This plan is used for storing information required for order by
    operations.

    Arguments:
        orderby_list: List[(TupleValueExpression, EnumInt), ...]
            A tuple of the column names string and the type of sort in the plan
    """

    def __init__(self, orderby_list):
        self._orderby_list = orderby_list
        super().__init__(PlanOprType.ORDER_BY)

    @property
    def columns(self):
        return [_[0] for _ in self._orderby_list]

    @property
    def sort_types(self):
        return [_[1] for _ in self._orderby_list]

    @property
    def orderby_list(self):
        return self._orderby_list

    def __str__(self):
        return 'OrderByPlan(orderby_list={})'.format(self._orderby_list)

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self._orderby_list)))

def __init__(self, orderby_list):
    self._orderby_list = orderby_list
    super().__init__(PlanOprType.ORDER_BY)

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self._orderby_list)))

class StoragePlan(AbstractPlan):
    """
    This is the plan used for retrieving the frames from the storage and
    and returning to the higher levels.

    Arguments:
        table (TableCatalogEntry): table for fetching data
        batch_mem_size (int): memory size of the batch read from disk
        skip_frames (int): skip frequency
        offset (int): storage offset for retrieving data
        limit (int): limit on data records to be retrieved
        total_shards (int): number of shards of data (if sharded)
        curr_shard (int): current curr_shard if data is sharded
        sampling_rate (int): uniform sampling rate
        sampling_type (str): special sampling type like IFRAMES
    """

    def __init__(self, table: TableCatalogEntry, table_ref: TableRef, skip_frames: int=0, offset: int=None, limit: int=None, total_shards: int=0, curr_shard: int=0, predicate: AbstractExpression=None, sampling_rate: int=None, batch_mem_size: int=30000000, sampling_type: str=None, chunk_params: dict={}):
        super().__init__(PlanOprType.STORAGE_PLAN)
        self._table = table
        self._table_ref = table_ref
        self._batch_mem_size = batch_mem_size
        self._skip_frames = skip_frames
        self._offset = offset
        self._limit = limit
        self._total_shards = total_shards
        self._curr_shard = curr_shard
        self._predicate = predicate
        self._sampling_rate = sampling_rate
        self._sampling_type = sampling_type
        self.chunk_params = chunk_params

    @property
    def table(self):
        return self._table

    @property
    def table_ref(self):
        return self._table_ref

    @property
    def batch_mem_size(self):
        return self._batch_mem_size

    @property
    def skip_frames(self):
        return self._skip_frames

    @property
    def offset(self):
        return self._offset

    @property
    def limit(self):
        return self._limit

    @property
    def total_shards(self):
        return self._total_shards

    @property
    def curr_shard(self):
        return self._curr_shard

    @property
    def predicate(self):
        return self._predicate

    @property
    def sampling_rate(self):
        return self._sampling_rate

    @property
    def sampling_type(self):
        return self._sampling_type

    def __str__(self):
        return 'StoragePlan(video={},             table_ref={},            batch_mem_size={},             skip_frames={},             offset={},             limit={},             total_shards={},             curr_shard={},             predicate={},             sampling_rate={},             sampling_type={})'.format(self._table, self._table_ref, self._batch_mem_size, self._skip_frames, self._offset, self._limit, self._total_shards, self._curr_shard, self._predicate, self._sampling_rate, self._sampling_type)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table, self.table_ref, self.batch_mem_size, self.skip_frames, self.offset, self.limit, self.total_shards, self.curr_shard, self.predicate, self.sampling_rate, self.sampling_type, frozenset(self.chunk_params.items())))

def __init__(self, table: TableCatalogEntry, table_ref: TableRef, skip_frames: int=0, offset: int=None, limit: int=None, total_shards: int=0, curr_shard: int=0, predicate: AbstractExpression=None, sampling_rate: int=None, batch_mem_size: int=30000000, sampling_type: str=None, chunk_params: dict={}):
    super().__init__(PlanOprType.STORAGE_PLAN)
    self._table = table
    self._table_ref = table_ref
    self._batch_mem_size = batch_mem_size
    self._skip_frames = skip_frames
    self._offset = offset
    self._limit = limit
    self._total_shards = total_shards
    self._curr_shard = curr_shard
    self._predicate = predicate
    self._sampling_rate = sampling_rate
    self._sampling_type = sampling_type
    self.chunk_params = chunk_params

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table, self.table_ref, self.batch_mem_size, self.skip_frames, self.offset, self.limit, self.total_shards, self.curr_shard, self.predicate, self.sampling_rate, self.sampling_type, frozenset(self.chunk_params.items())))

class AbstractJoin(AbstractPlan):
    """Abstract class for all the join based planners

    Arguments:
        join_type: JoinType
            type of join, INNER, OUTER , LATERAL etc
        join_predicate: AbstractExpression
            An expression used for joining
    """

    def __init__(self, node_type: PlanOprType, join_type: JoinType, join_predicate: AbstractExpression):
        super().__init__(node_type)
        self._join_type = join_type
        self._join_predicate = join_predicate

    @property
    def join_type(self) -> AbstractExpression:
        return self._join_type

    @property
    def join_predicate(self) -> AbstractExpression:
        return self._join_predicate

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.join_type, self.join_predicate))

def __init__(self, node_type: PlanOprType, join_type: JoinType, join_predicate: AbstractExpression):
    super().__init__(node_type)
    self._join_type = join_type
    self._join_predicate = join_predicate

def __hash__(self) -> int:
    return hash((super().__hash__(), self.join_type, self.join_predicate))

class SeqScanPlan(AbstractScan):
    """
    This plan is used for storing information required for sequential scan
    operations.

    Arguments:
        columns: List[AbstractExpression]
            list of column names string in the plan
        predicate: AbstractExpression
            An expression used for filtering
    """

    def __init__(self, predicate: AbstractExpression, columns: List[AbstractExpression], alias: str=None):
        self._columns = columns
        self.alias = alias
        super().__init__(PlanOprType.SEQUENTIAL_SCAN, predicate)

    @property
    def columns(self):
        return self._columns

    def __str__(self):
        return 'SeqScanPlan(predicate={},             columns={},             alias={})'.format(self._predicate, self._columns, self.alias)

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self.columns or []), self.alias))

def __init__(self, predicate: AbstractExpression, columns: List[AbstractExpression], alias: str=None):
    self._columns = columns
    self.alias = alias
    super().__init__(PlanOprType.SEQUENTIAL_SCAN, predicate)

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self.columns or []), self.alias))

class FunctionScanPlan(AbstractPlan):
    """
    This plan used to store metadata to perform function table scan.

    Arguments:
        func_expr(FunctionExpression): parameterized function expression that
            reference columns from a table expression that precedes it.
        do_unnest(bool): if True perform unnest operation on the output of FunctionScan
    """

    def __init__(self, func_expr: FunctionExpression, do_unnest: bool=False):
        self._func_expr = func_expr
        self._do_unnest = do_unnest
        super().__init__(PlanOprType.FUNCTION_SCAN)

    @property
    def func_expr(self):
        return self._func_expr

    @property
    def do_unnest(self):
        return self._do_unnest

    def __str__(self):
        plan = 'UnnestFunctionScanPlan' if self._do_unnest else 'FunctionScanPlan'
        return '{}(func_expr={})'.format(plan, self._func_expr)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.func_expr, self.do_unnest))

def __init__(self, func_expr: FunctionExpression, do_unnest: bool=False):
    self._func_expr = func_expr
    self._do_unnest = do_unnest
    super().__init__(PlanOprType.FUNCTION_SCAN)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.func_expr, self.do_unnest))

class InsertPlan(AbstractPlan):
    """This plan is used for storing information required for insert
    operations.

    Args:
        table (TableCatalogEntry): table to insert into
        column_list (List[AbstractExpression]): list of annotated column
        value_list (List[AbstractExpression]): list of abstract expression
                                                for the values to insert
    """

    def __init__(self, table_ref: TableCatalogEntry, column_list: List[AbstractExpression], value_list: List[AbstractExpression]):
        super().__init__(PlanOprType.INSERT)
        self.table_ref = table_ref
        self.column_list = column_list
        self.value_list = value_list

    def __str__(self):
        return 'InsertPlan(table={},             column_list={},             value_list={})'.format(self.table_ref, self.column_list, self.value_list)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_ref, tuple(self.column_list), tuple((tuple(val) for val in self.value_list))))

def __init__(self, table_ref: TableCatalogEntry, column_list: List[AbstractExpression], value_list: List[AbstractExpression]):
    super().__init__(PlanOprType.INSERT)
    self.table_ref = table_ref
    self.column_list = column_list
    self.value_list = value_list

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_ref, tuple(self.column_list), tuple((tuple(val) for val in self.value_list))))

class LimitPlan(AbstractPlan):
    """
    This plan is used for storing information required for limit
    operations.

    Arguments:
        limit_count: ConstantValueExpression
            A ConstantValueExpression which is the count of the
            number of rows returned
    """

    def __init__(self, limit_count: ConstantValueExpression):
        self._limit_count = limit_count
        super().__init__(PlanOprType.LIMIT)

    @property
    def limit_value(self):
        return self._limit_count.value

    def __str__(self):
        return 'LimitPlan(limit_count={})'.format(self._limit_count)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._limit_count))

def __init__(self, limit_count: ConstantValueExpression):
    self._limit_count = limit_count
    super().__init__(PlanOprType.LIMIT)

def __hash__(self) -> int:
    return hash((super().__hash__(), self._limit_count))

class CreateFromSelectPlan(AbstractPlan):
    """
    This plan is used for storing information required for creating
    a table from select query.
    Arguments:
        table_info {TableInfo} -- table info for view to be created in storage
        col_list{List[ColumnDefinition]} -- column names in the view
        if_not_exists {bool} -- Whether to override if there is existing view
    """

    def __init__(self, table_info: TableInfo, column_list: List[ColumnDefinition], if_not_exists: bool=False):
        super().__init__(PlanOprType.CREATE)
        self._table_info = table_info
        self._column_list = column_list
        self._if_not_exists = if_not_exists

    @property
    def table_info(self):
        return self._table_info

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def column_list(self):
        return self._column_list

    def __str__(self):
        return 'CreateFromSelectPlan(table_info={},             column_lists={},             if_not_exists={})'.format(self._table_info, self._column_list, self._if_not_exists)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_info, self.if_not_exists, tuple(self.column_list)))

def __init__(self, table_info: TableInfo, column_list: List[ColumnDefinition], if_not_exists: bool=False):
    super().__init__(PlanOprType.CREATE)
    self._table_info = table_info
    self._column_list = column_list
    self._if_not_exists = if_not_exists

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_info, self.if_not_exists, tuple(self.column_list)))

class ShowInfoPlan(AbstractPlan):

    def __init__(self, show_type: ShowType, show_val: Optional[str]=''):
        self._show_type = show_type
        self._show_val = show_val
        super().__init__(PlanOprType.SHOW_INFO)

    @property
    def show_type(self):
        return self._show_type

    @property
    def show_val(self):
        return self._show_val

    def __str__(self):
        if self._show_type == ShowType.FUNCTIONS:
            return 'ShowFunctionPlan'
        if self._show_type == ShowType.DATABASES:
            return 'ShowDatabasePlan'
        elif self._show_type == ShowType.TABLES:
            return 'ShowTablePlan'
        elif self._show_type == ShowType.CONFIGS:
            return 'ShowConfigPlan'

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.show_type, self.show_val))

def __init__(self, show_type: ShowType, show_val: Optional[str]=''):
    self._show_type = show_type
    self._show_val = show_val
    super().__init__(PlanOprType.SHOW_INFO)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.show_type, self.show_val))

class SamplePlan(AbstractPlan):
    """
    This plan is used for storing information required for sample
    operations.

    Arguments:
        sample_freq: ConstantValueExpression
            A ConstantValueExpression which is the count of the
            gap between frames sampled.
    """

    def __init__(self, sample_freq: ConstantValueExpression):
        self._sample_freq = sample_freq
        super().__init__(PlanOprType.SAMPLE)

    @property
    def sample_freq(self):
        return self._sample_freq

    def __str__(self):
        return 'SamplePlan(sample_freq={})'.format(self._sample_freq)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.sample_freq))

def __init__(self, sample_freq: ConstantValueExpression):
    self._sample_freq = sample_freq
    super().__init__(PlanOprType.SAMPLE)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.sample_freq))

class CreateIndexPlan(AbstractPlan):

    def __init__(self, name: str, if_not_exists: bool, table_ref: TableRef, col_list: List[ColumnDefinition], vector_store_type: VectorStoreType, project_expr_list: List[AbstractExpression], index_def: str):
        super().__init__(PlanOprType.CREATE_INDEX)
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

    def __str__(self):
        function_expr = None
        for project_expr in self._project_expr_list:
            if isinstance(project_expr, FunctionExpression):
                function_expr = project_expr
        return 'CreateIndexPlan(name={},             table_ref={},             col_list={},             vector_store_type={},             {})'.format(self._name, self._table_ref, tuple(self._col_list), self._vector_store_type, '' if function_expr is None else 'function={}'.format(function_expr))

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.name, self.if_not_exists, self.table_ref, tuple(self.col_list), self.vector_store_type, tuple(self.project_expr_list), self.index_def))

def __init__(self, name: str, if_not_exists: bool, table_ref: TableRef, col_list: List[ColumnDefinition], vector_store_type: VectorStoreType, project_expr_list: List[AbstractExpression], index_def: str):
    super().__init__(PlanOprType.CREATE_INDEX)
    self._name = name
    self._if_not_exists = if_not_exists
    self._table_ref = table_ref
    self._col_list = col_list
    self._vector_store_type = vector_store_type
    self._project_expr_list = project_expr_list
    self._index_def = index_def

def __hash__(self) -> int:
    return hash((super().__hash__(), self.name, self.if_not_exists, self.table_ref, tuple(self.col_list), self.vector_store_type, tuple(self.project_expr_list), self.index_def))

class CreateFunctionPlan(AbstractPlan):
    """
    This plan is used for storing information required to create function operators

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
        impl_file_path: Path
            file path which holds the implementation of the function.
        function_type: str
            function type. it ca be object detection, classification etc.
    """

    def __init__(self, name: str, or_replace: bool, if_not_exists: bool, inputs: List[FunctionIOCatalogEntry], outputs: List[FunctionIOCatalogEntry], impl_file_path: Path, function_type: str=None, metadata: List[FunctionMetadataCatalogEntry]=None):
        super().__init__(PlanOprType.CREATE_FUNCTION)
        self._name = name
        self._or_replace = or_replace
        self._if_not_exists = if_not_exists
        self._inputs = inputs
        self._outputs = outputs
        self._impl_path = impl_file_path
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

    def __str__(self):
        return 'CreateFunctionPlan(name={},             or_replace={},             if_not_exists={},             inputs={},             outputs={},             impl_file_path={},             function_type={},             metadata={})'.format(self._name, self._or_replace, self._if_not_exists, self._inputs, self._outputs, self._impl_path, self._function_type, self._metadata)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.or_replace, self.if_not_exists, tuple(self.inputs), tuple(self.outputs), self.impl_path, self.function_type, tuple(self.metadata)))

def __init__(self, name: str, or_replace: bool, if_not_exists: bool, inputs: List[FunctionIOCatalogEntry], outputs: List[FunctionIOCatalogEntry], impl_file_path: Path, function_type: str=None, metadata: List[FunctionMetadataCatalogEntry]=None):
    super().__init__(PlanOprType.CREATE_FUNCTION)
    self._name = name
    self._or_replace = or_replace
    self._if_not_exists = if_not_exists
    self._inputs = inputs
    self._outputs = outputs
    self._impl_path = impl_file_path
    self._function_type = function_type
    self._metadata = metadata

def __hash__(self) -> int:
    return hash((super().__hash__(), self.or_replace, self.if_not_exists, tuple(self.inputs), tuple(self.outputs), self.impl_path, self.function_type, tuple(self.metadata)))

class ExchangePlan(AbstractPlan):
    """
    This plan is used for storing information required for union operations.

    Arguments:
        all: Bool
            UNION (deduplication) vs UNION ALL (non-deduplication)
    """

    def __init__(self, inner_plan: AbstractPlan, parallelism: int=1, ray_pull_env_conf_dict: Dict[str, Any]={}, ray_parallel_env_conf_dict: List[Dict[str, Any]]=[{}]):
        self.inner_plan = inner_plan
        self.parallelism = parallelism
        self.ray_parallel_env_conf_dict = ray_parallel_env_conf_dict
        self.ray_pull_env_conf_dict = ray_pull_env_conf_dict
        super().__init__(PlanOprType.EXCHANGE)

    def __str__(self) -> str:
        return 'ExchangePlan'

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.inner_plan, self.parallelism))

def __init__(self, inner_plan: AbstractPlan, parallelism: int=1, ray_pull_env_conf_dict: Dict[str, Any]={}, ray_parallel_env_conf_dict: List[Dict[str, Any]]=[{}]):
    self.inner_plan = inner_plan
    self.parallelism = parallelism
    self.ray_parallel_env_conf_dict = ray_parallel_env_conf_dict
    self.ray_pull_env_conf_dict = ray_pull_env_conf_dict
    super().__init__(PlanOprType.EXCHANGE)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.inner_plan, self.parallelism))

class UnionPlan(AbstractPlan):
    """
    This plan is used for storing information required for union operations.

    Arguments:
        all: Bool
            UNION (deduplication) vs UNION ALL (non-deduplication)
    """

    def __init__(self, all: bool):
        self._all = all
        super().__init__(PlanOprType.UNION)

    @property
    def all(self):
        return self._all

    def __str__(self):
        return 'UnionAllPlan' if self._all else 'UnionPlan'

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._all))

def __init__(self, all: bool):
    self._all = all
    super().__init__(PlanOprType.UNION)

def __hash__(self) -> int:
    return hash((super().__hash__(), self._all))

class DropObjectPlan(AbstractPlan):

    def __init__(self, object_type: ObjectType, name: str, if_exists: bool):
        super().__init__(PlanOprType.DROP_OBJECT)
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

    def __str__(self):
        return 'DropObjectPlan(object_type={}, name={}, if_exists={})'.format(self._object_type, self._name, self._if_exists)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.object_type, self.name, self.if_exists))

def __init__(self, object_type: ObjectType, name: str, if_exists: bool):
    super().__init__(PlanOprType.DROP_OBJECT)
    self._object_type = object_type
    self._name = name
    self._if_exists = if_exists

def __hash__(self) -> int:
    return hash((super().__hash__(), self.object_type, self.name, self.if_exists))

class LoadDataPlan(AbstractPlan):
    """
    This plan is used for storing information required for load data
    operations.

    Arguments:
        table(TableCatalogEntry): table to load into
        file_path(Path): file path from where we will load the data
        batch_mem_size(int): memory size of the batch loaded from disk
    """

    def __init__(self, table_info: TableInfo, file_path: Path, column_list: List[AbstractExpression]=None, file_options: dict=None, batch_mem_size: int=30000000):
        super().__init__(PlanOprType.LOAD_DATA)
        self._table_info = table_info
        self._file_path = file_path
        self._column_list = column_list
        self._file_options = file_options
        self._batch_mem_size = batch_mem_size

    @property
    def table_info(self):
        return self._table_info

    @property
    def file_path(self):
        return self._file_path

    @property
    def batch_mem_size(self):
        return self._batch_mem_size

    @property
    def column_list(self):
        return self._column_list

    @property
    def file_options(self):
        return self._file_options

    def __str__(self):
        return 'LoadDataPlan(table_id={}, file_path={},             column_list={},             file_options={},             batch_mem_size={})'.format(self.table_info, self.file_path, self.column_list, self.file_options, self.batch_mem_size)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_info, self.file_path, tuple(self.column_list), frozenset(self.file_options.items()), self.batch_mem_size))

def __init__(self, table_info: TableInfo, file_path: Path, column_list: List[AbstractExpression]=None, file_options: dict=None, batch_mem_size: int=30000000):
    super().__init__(PlanOprType.LOAD_DATA)
    self._table_info = table_info
    self._file_path = file_path
    self._column_list = column_list
    self._file_options = file_options
    self._batch_mem_size = batch_mem_size

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_info, self.file_path, tuple(self.column_list), frozenset(self.file_options.items()), self.batch_mem_size))

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

@abstractmethod
def __hash__(self) -> int:
    return hash(self.opr_type)

class PPScanPlan(AbstractScan):
    """
    This plan is used for storing information required for probabilistic
    predicate.

    Arguments:
        predicate (AbstractExpression): A predicate expression used for
        filtering frames
    """

    def __init__(self, predicate: AbstractExpression):
        super().__init__(PlanOprType.PP_FILTER, predicate)

    def __str__(self):
        return 'AbstractPlan'

def __init__(self, predicate: AbstractExpression):
    super().__init__(PlanOprType.PP_FILTER, predicate)

class GroupByPlan(AbstractPlan):
    """
    This plan is used for storing information required for group by
    operations.

    Arguments:
        groupby_clause: ConstantValueExpression
            A ConstantValueExpression which is the number of elements to
            group together.
    """

    def __init__(self, groupby_clause: ConstantValueExpression):
        self._groupby_clause = groupby_clause
        super().__init__(PlanOprType.GROUP_BY)

    @property
    def groupby_clause(self):
        return self._groupby_clause

    def __str__(self):
        return 'GroupByPlan(groupby_clause={})'.format(self._groupby_clause)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.groupby_clause))

def __init__(self, groupby_clause: ConstantValueExpression):
    self._groupby_clause = groupby_clause
    super().__init__(PlanOprType.GROUP_BY)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.groupby_clause))

class HashJoinProbePlan(AbstractJoin):
    """
    This plan is used for storing information required for
    hash join probe side. It scans over the preferably larger relation
    and uses build side hash table to join.
    Arguments:
        join_type: JoinType
        probe_keys (List[ColumnCatalogEntry]) : list of equi-key columns.
                        Must be equal to build side keys.
        predicate (AbstractExpression)
    """

    def __init__(self, join_type: JoinType, probe_keys: List[ColumnCatalogEntry], join_predicate: AbstractExpression, join_project: List[AbstractExpression]):
        self.probe_keys = probe_keys
        self.join_project = join_project
        super().__init__(PlanOprType.HASH_JOIN, join_type, join_predicate)

    def __str__(self):
        return 'HashJoinProbePlan(join_type={},             probe_keys={},             join_predicate={},             join_project={})'.format(self.join_type, self.probe_keys, self.join_predicate, self.join_project)

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self.probe_keys or []), tuple(self.join_project or [])))

def __init__(self, join_type: JoinType, probe_keys: List[ColumnCatalogEntry], join_predicate: AbstractExpression, join_project: List[AbstractExpression]):
    self.probe_keys = probe_keys
    self.join_project = join_project
    super().__init__(PlanOprType.HASH_JOIN, join_type, join_predicate)

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self.probe_keys or []), tuple(self.join_project or [])))

class CreatePlan(AbstractPlan):
    """
    This plan is used for storing information required for create table
    operations.
    Arguments:
        video_ref {TableInfo} -- video ref for table to be created in storage
        column_list {List[ColumnCatalogEntry]} -- Columns to be added
        if_not_exists {bool} -- Whether to override if there is existing table
    """

    def __init__(self, table_info: TableInfo, column_list: List[ColumnCatalogEntry], if_not_exists: bool=False):
        super().__init__(PlanOprType.CREATE)
        self._table_info = table_info
        self._column_list = column_list
        self._if_not_exists = if_not_exists

    @property
    def table_info(self):
        return self._table_info

    @property
    def if_not_exists(self):
        return self._if_not_exists

    @property
    def column_list(self):
        return self._column_list

    def __str__(self):
        return 'CreatePlan(table_ref={},             column_list={},             if_not_exists={})'.format(self._table_info, self._column_list, self._if_not_exists)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.table_info, self.if_not_exists, tuple(self.column_list)))

def __init__(self, table_info: TableInfo, column_list: List[ColumnCatalogEntry], if_not_exists: bool=False):
    super().__init__(PlanOprType.CREATE)
    self._table_info = table_info
    self._column_list = column_list
    self._if_not_exists = if_not_exists

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_info, self.if_not_exists, tuple(self.column_list)))

class NativePlan(AbstractPlan):
    """
    This plan is used for pushing down query string directly to
    backend database engine.
    """

    def __init__(self, plan_type: PlanOprType, database_name: str, query_string: str):
        self._database_name = database_name
        self._query_string = query_string
        super().__init__(plan_type)

    @property
    def database_name(self):
        return self._database_name

    @property
    def query_string(self):
        return self._query_string

    def __str__(self):
        return 'NativePlan(database_name={}, query_string={})'.format(self._database_name, self._query_string)

    def __hash__(self) -> int:
        return hash((super().__hash__(), self._database_name, self._query_string))

def __init__(self, plan_type: PlanOprType, database_name: str, query_string: str):
    self._database_name = database_name
    self._query_string = query_string
    super().__init__(plan_type)

def __hash__(self) -> int:
    return hash((super().__hash__(), self._database_name, self._query_string))

class SQLAlchemyPlan(NativePlan):

    def __init__(self, database_name: str, query_string: str):
        super().__init__(PlanOprType.SQLALCHEMY, database_name, query_string)

def __init__(self, database_name: str, query_string: str):
    super().__init__(PlanOprType.SQLALCHEMY, database_name, query_string)

class ProjectPlan(AbstractPlan):
    """
    Arguments:
        target_list List[(AbstractExpression)]: projection list
    """

    def __init__(self, target_list: List[AbstractExpression]):
        self.target_list = target_list
        super().__init__(PlanOprType.PROJECT)

    def __str__(self):
        return 'ProjectPlan(target_list={})'.format(self.target_list)

    def __hash__(self) -> int:
        return hash((super().__hash__(), tuple(self.target_list)))

def __init__(self, target_list: List[AbstractExpression]):
    self.target_list = target_list
    super().__init__(PlanOprType.PROJECT)

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self.target_list)))

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

def __hash__(self) -> int:
    return hash((self.opr_type, tuple(self.children)))

class Dummy(Operator):
    """
    Acts as a placeholder for matching any operator in optimizer.
    It tracks the group_id of the matching operator.
    """

    def __init__(self, group_id: int, opr: Operator):
        super().__init__(OperatorType.DUMMY, None)
        self.group_id = group_id
        self.opr = opr

def __init__(self, group_id: int, opr: Operator):
    super().__init__(OperatorType.DUMMY, None)
    self.group_id = group_id
    self.opr = opr

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

def __hash__(self) -> int:
    return hash((super().__hash__(), self.alias, self.video, self.table_obj, self.predicate, tuple(self.target_list or []), self.sampling_rate, self.sampling_type, frozenset(self.chunk_params.items())))

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

def __init__(self, alias: str, predicate: AbstractExpression=None, target_list: List[AbstractExpression]=None, children: List=None):
    super().__init__(OperatorType.LOGICALQUERYDERIVEDGET, children=children)
    self._alias = alias
    self.predicate = predicate
    self.target_list = target_list or []

def __hash__(self) -> int:
    return hash((super().__hash__(), self.alias, self.predicate, tuple(self.target_list)))

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

def __init__(self, predicate: AbstractExpression, children=None):
    self._predicate = predicate
    super().__init__(OperatorType.LOGICALFILTER, children)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.predicate))

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

def __init__(self, target_list: List[AbstractExpression], children=None):
    super().__init__(OperatorType.LOGICALPROJECT, children)
    self._target_list = target_list

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self.target_list)))

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

def __init__(self, groupby_clause: ConstantValueExpression, children: List=None):
    super().__init__(OperatorType.LOGICALGROUPBY, children)
    self._groupby_clause = groupby_clause

def __hash__(self) -> int:
    return hash((super().__hash__(), self.groupby_clause))

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

def __init__(self, orderby_list: List, children: List=None):
    super().__init__(OperatorType.LOGICALORDERBY, children)
    self._orderby_list = orderby_list

def __hash__(self) -> int:
    return hash((super().__hash__(), tuple(self.orderby_list)))

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

def __init__(self, limit_count: ConstantValueExpression, children: List=None):
    super().__init__(OperatorType.LOGICALLIMIT, children)
    self._limit_count = limit_count

def __hash__(self) -> int:
    return hash((super().__hash__(), self.limit_count))

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

def __init__(self, sample_freq: ConstantValueExpression, sample_type: ConstantValueExpression, children: List=None):
    super().__init__(OperatorType.LOGICALSAMPLE, children)
    self._sample_freq = sample_freq
    self._sample_type = sample_type

def __hash__(self) -> int:
    return hash((super().__hash__(), self.sample_freq, self.sample_type))

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

def __init__(self, all: bool, children: List=None):
    super().__init__(OperatorType.LOGICALUNION, children)
    self._all = all

def __hash__(self) -> int:
    return hash((super().__hash__(), self.all))

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

def __init__(self, table: TableCatalogEntry, column_list: List[AbstractExpression], value_list: List[AbstractExpression], children: List=None):
    super().__init__(OperatorType.LOGICALINSERT, children)
    self._table = table
    self._column_list = column_list
    self._value_list = value_list

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table, tuple((tuple(i) for i in self.value_list)), tuple(self.column_list)))

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

def __init__(self, table_ref: TableRef, where_clause: AbstractExpression=None, children=None):
    super().__init__(OperatorType.LOGICALDELETE, children)
    self._table_ref = table_ref
    self._where_clause = where_clause

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_ref, self.where_clause))

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

def __init__(self, video: TableInfo, column_list: List[ColumnDefinition], if_not_exists: bool=False, children: List=None):
    super().__init__(OperatorType.LOGICALCREATE, children)
    self._video = video
    self._column_list = column_list
    self._if_not_exists = if_not_exists

def __hash__(self) -> int:
    return hash((super().__hash__(), self.video, tuple(self.column_list), self.if_not_exists))

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

def __init__(self, old_table_ref: TableRef, new_name: TableInfo, children=None):
    super().__init__(OperatorType.LOGICALRENAME, children)
    self._new_name = new_name
    self._old_table_ref = old_table_ref

def __hash__(self) -> int:
    return hash((super().__hash__(), self._new_name, self._old_table_ref))

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

def __hash__(self) -> int:
    return hash((super().__hash__(), self.name, self.or_replace, self.if_not_exists, tuple(self.inputs), tuple(self.outputs), self.function_type, self.impl_path, tuple(self.metadata)))

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

def __init__(self, object_type: ObjectType, name: str, if_exists: bool, children: List=None):
    super().__init__(OperatorType.LOGICAL_DROP_OBJECT, children)
    self._object_type = object_type
    self._name = name
    self._if_exists = if_exists

def __hash__(self) -> int:
    return hash((super().__hash__(), self.object_type, self.name, self.if_exists))

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

def __init__(self, table_info: TableInfo, path: Path, column_list: List[AbstractExpression]=None, file_options: dict=dict(), children: List=None):
    super().__init__(OperatorType.LOGICALLOADDATA, children=children)
    self._table_info = table_info
    self._path = path
    self._column_list = column_list or []
    self._file_options = file_options

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_info, self.path, tuple(self.column_list), frozenset(self.file_options.items())))

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

def __init__(self, func_expr: AbstractExpression, alias: Alias, do_unnest: bool=False, children: List=None):
    super().__init__(OperatorType.LOGICALFUNCTIONSCAN, children)
    self._func_expr = func_expr
    self._do_unnest = do_unnest
    self._alias = alias

def __hash__(self) -> int:
    return hash((super().__hash__(), self.func_expr, self.do_unnest, self.alias))

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

def __init__(self, detector: FunctionExpression, tracker: FunctionExpression, alias: Alias, do_unnest: bool=False, children: List=None):
    super().__init__(OperatorType.LOGICAL_EXTRACT_OBJECT, children)
    self.detector = detector
    self.tracker = tracker
    self.do_unnest = do_unnest
    self.alias = alias

def __hash__(self) -> int:
    return hash((super().__hash__(), self.detector, self.tracker, self.do_unnest, self.alias))

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

def __init__(self, join_type: JoinType, join_predicate: AbstractExpression=None, left_keys: List[ColumnCatalogEntry]=None, right_keys: List[ColumnCatalogEntry]=None, children: List=None):
    super().__init__(OperatorType.LOGICALJOIN, children)
    self._join_type = join_type
    self._join_predicate = join_predicate
    self._left_keys = left_keys
    self._right_keys = right_keys
    self._join_project = None

def __hash__(self) -> int:
    return hash((super().__hash__(), self.join_type, self.join_predicate, self.left_keys, self.right_keys, tuple(self.join_project or [])))

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

def __init__(self, show_type: ShowType, show_val: Optional[str]='', children: List=None):
    super().__init__(OperatorType.LOGICAL_SHOW, children)
    self._show_type = show_type
    self._show_val = show_val

def __hash__(self) -> int:
    return hash((super().__hash__(), self.show_type, self.show_val))

class LogicalExchange(Operator):

    def __init__(self, children=None):
        super().__init__(OperatorType.LOGICALEXCHANGE, children)

    def __eq__(self, other):
        is_subtree_equal = super().__eq__(other)
        if not isinstance(other, LogicalExchange):
            return False
        return is_subtree_equal

def __init__(self, children=None):
    super().__init__(OperatorType.LOGICALEXCHANGE, children)

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

def __init__(self, children: List=None):
    super().__init__(OperatorType.LOGICALEXPLAIN, children)
    assert len(children) == 1, 'EXPLAIN command only takes one child'
    self._explainable_opr = children[0]

def __hash__(self) -> int:
    return hash((super().__hash__(), self._explainable_opr))

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

def __init__(self, name: str, if_not_exists: bool, table_ref: TableRef, col_list: List[ColumnDefinition], vector_store_type: VectorStoreType, project_expr_list: List[AbstractExpression], index_def: str, children: List=None):
    super().__init__(OperatorType.LOGICALCREATEINDEX, children)
    self._name = name
    self._if_not_exists = if_not_exists
    self._table_ref = table_ref
    self._col_list = col_list
    self._vector_store_type = vector_store_type
    self._project_expr_list = project_expr_list
    self._index_def = index_def

def __hash__(self) -> int:
    return hash((super().__hash__(), self.name, self.if_not_exists, self.table_ref, tuple(self.col_list), self.vector_store_type, tuple(self.project_expr_list), self.index_def))

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

def __init__(self, func_expr: FunctionExpression, alias: Alias, do_unnest: bool=False, children: List=None):
    super().__init__(OperatorType.LOGICAL_APPLY_AND_MERGE, children)
    self._func_expr = func_expr
    self._do_unnest = do_unnest
    self._alias = alias
    self._merge_type = JoinType.INNER_JOIN

def __hash__(self) -> int:
    return hash((super().__hash__(), self.func_expr, self.do_unnest, self.alias, self._merge_type))

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

def __init__(self, index: IndexCatalogEntry, limit_count: ConstantValueExpression, search_query_expr: FunctionExpression, children: List=None):
    super().__init__(OperatorType.LOGICAL_VECTOR_INDEX_SCAN, children)
    self._index = index
    self._limit_count = limit_count
    self._search_query_expr = search_query_expr

def __hash__(self) -> int:
    return hash((super().__hash__(), self.index, self.limit_count, self.search_query_expr))

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

def __hash__(self):
    return hash((self.opr, tuple(self.children)))

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

def __init__(self, root_expr: GroupExpression, rule_set: List[Rule], optimizer_context: OptimizerContext):
    self.root_expr = root_expr
    self.rule_set = rule_set
    super().__init__(optimizer_context, OptimizerTaskType.TOP_DOWN_REWRITE)

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

def __init__(self, root_expr: GroupExpression, rule_set: List[Rule], optimizer_context: OptimizerContext, children_explored=False):
    super().__init__(optimizer_context, OptimizerTaskType.BOTTOM_UP_REWRITE)
    self._children_explored = children_explored
    self.root_expr = root_expr
    self.rule_set = rule_set

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

def __init__(self, root_expr: GroupExpression, optimizer_context: OptimizerContext, explore: bool):
    self.root_expr = root_expr
    self.explore = explore
    super().__init__(optimizer_context, OptimizerTaskType.OPTIMIZE_EXPRESSION)

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

def __init__(self, rule: Rule, root_expr: GroupExpression, optimizer_context: OptimizerContext, explore: bool):
    self.rule = rule
    self.root_expr = root_expr
    self.explore = explore
    super().__init__(optimizer_context, OptimizerTaskType.APPLY_RULE)

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

def __init__(self, group: Group, optimizer_context: OptimizerContext):
    self.group = group
    super().__init__(optimizer_context, OptimizerTaskType.OPTIMIZE_GROUP)

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

def __init__(self, root_expr: GroupExpression, optimizer_context: OptimizerContext):
    self.root_expr = root_expr
    super().__init__(optimizer_context, OptimizerTaskType.OPTIMIZE_INPUTS)

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

def find_duplicate_expr(self, expr: GroupExpression) -> GroupExpression:
    if hash(expr) in self.group_exprs:
        return self.group_exprs[hash(expr)]
    else:
        return None

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

def __hash__(self):
    return hash(self._property_type)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALFILTER)
    pattern.append_child(Pattern(OperatorType.LOGICALGET))
    super().__init__(RuleType.EMBED_FILTER_INTO_GET, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALSAMPLE)
    pattern.append_child(Pattern(OperatorType.LOGICALGET))
    super().__init__(RuleType.EMBED_SAMPLE_INTO_GET, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALPROJECT)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.CACHE_FUNCTION_EXPRESISON_IN_PROJECT, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALFILTER)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.CACHE_FUNCTION_EXPRESISON_IN_FILTER, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.CACHE_FUNCTION_EXPRESISON_IN_APPLY, pattern)

def apply(self, before: LogicalApplyAndMerge, context: OptimizerContext):
    new_func_expr = enable_cache(context, before.func_expr)
    after = LogicalApplyAndMerge(func_expr=new_func_expr, alias=before.alias, do_unnest=before.do_unnest)
    after.append_child(before.children[0])
    yield after

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALFILTER)
    pattern_join = Pattern(OperatorType.LOGICALJOIN)
    pattern_join.append_child(Pattern(OperatorType.DUMMY))
    pattern_join.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(pattern_join)
    super().__init__(RuleType.PUSHDOWN_FILTER_THROUGH_JOIN, pattern)

class XformLateralJoinToLinearFlow(Rule):
    """If the inner node of a lateral join is a function-valued expression, we
    eliminate the join node and make the inner node the parent of the outer node. This
    produces a linear data flow path. Because this scenario is common in our system,
    we chose to explicitly convert it to a linear flow, which simplifies the
    implementation of other optimizations such as function reuse and parallelized plans by
    removing the join."""

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALJOIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.LOGICALFUNCTIONSCAN))
        super().__init__(RuleType.XFORM_LATERAL_JOIN_TO_LINEAR_FLOW, pattern)

    def promise(self):
        return Promise.XFORM_LATERAL_JOIN_TO_LINEAR_FLOW

    def check(self, before: LogicalJoin, context: OptimizerContext):
        if before.join_type == JoinType.LATERAL_JOIN:
            if before.join_predicate is None and (not before.join_project):
                return True
        return False

    def apply(self, before: LogicalJoin, context: OptimizerContext):
        A: Dummy = before.children[0]
        logical_func_scan: LogicalFunctionScan = before.children[1]
        logical_apply_merge = LogicalApplyAndMerge(logical_func_scan.func_expr, logical_func_scan.alias, logical_func_scan.do_unnest)
        logical_apply_merge.append_child(A)
        yield logical_apply_merge

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALJOIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.LOGICALFUNCTIONSCAN))
    super().__init__(RuleType.XFORM_LATERAL_JOIN_TO_LINEAR_FLOW, pattern)

def apply(self, before: LogicalJoin, context: OptimizerContext):
    A: Dummy = before.children[0]
    logical_func_scan: LogicalFunctionScan = before.children[1]
    logical_apply_merge = LogicalApplyAndMerge(logical_func_scan.func_expr, logical_func_scan.alias, logical_func_scan.do_unnest)
    logical_apply_merge.append_child(A)
    yield logical_apply_merge

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

def __init__(self):
    appply_merge_pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
    appply_merge_pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern = Pattern(OperatorType.LOGICALFILTER)
    pattern.append_child(appply_merge_pattern)
    super().__init__(RuleType.PUSHDOWN_FILTER_THROUGH_APPLY_AND_MERGE, pattern)

class XformExtractObjectToLinearFlow(Rule):
    """If the inner node of a lateral join is a Extract_Object function-valued
    expression, we eliminate the join node and make the inner node the parent of the
    outer node. This produces a linear data flow path.
    TODO: We need to add a sorting operation after detector to ensure we always provide tracker data in order.
    """

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALJOIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.LOGICAL_EXTRACT_OBJECT))
        super().__init__(RuleType.XFORM_EXTRACT_OBJECT_TO_LINEAR_FLOW, pattern)

    def promise(self):
        return Promise.XFORM_EXTRACT_OBJECT_TO_LINEAR_FLOW

    def check(self, before: LogicalJoin, context: OptimizerContext):
        if before.join_type == JoinType.LATERAL_JOIN:
            return True
        return False

    def apply(self, before: LogicalJoin, context: OptimizerContext):
        A: Dummy = before.children[0]
        logical_extract_obj: LogicalExtractObject = before.children[1]
        detector = LogicalApplyAndMerge(logical_extract_obj.detector, alias=logical_extract_obj.detector.alias)
        tracker = LogicalApplyAndMerge(logical_extract_obj.tracker, alias=logical_extract_obj.alias, do_unnest=logical_extract_obj.do_unnest)
        detector.append_child(A)
        tracker.append_child(detector)
        yield tracker

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALJOIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.LOGICAL_EXTRACT_OBJECT))
    super().__init__(RuleType.XFORM_EXTRACT_OBJECT_TO_LINEAR_FLOW, pattern)

def apply(self, before: LogicalJoin, context: OptimizerContext):
    A: Dummy = before.children[0]
    logical_extract_obj: LogicalExtractObject = before.children[1]
    detector = LogicalApplyAndMerge(logical_extract_obj.detector, alias=logical_extract_obj.detector.alias)
    tracker = LogicalApplyAndMerge(logical_extract_obj.tracker, alias=logical_extract_obj.alias, do_unnest=logical_extract_obj.do_unnest)
    detector.append_child(A)
    tracker.append_child(detector)
    yield tracker

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALLIMIT)
    orderby_pattern = Pattern(OperatorType.LOGICALORDERBY)
    orderby_pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(orderby_pattern)
    super().__init__(RuleType.COMBINE_SIMILARITY_ORDERBY_AND_LIMIT_TO_VECTOR_INDEX_SCAN, pattern)
    self._index_catalog_entry = None
    self._query_func_expr = None

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALJOIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_INNER_JOIN_COMMUTATIVITY, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALFILTER)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.REORDER_PREDICATES, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALCREATE)
    super().__init__(RuleType.LOGICAL_CREATE_TO_PHYSICAL, pattern)

class LogicalCreateFromSelectToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALCREATE)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_CREATE_FROM_SELECT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_CREATE_FROM_SELECT_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalCreate, context: OptimizerContext):
        after = CreateFromSelectPlan(before.video, before.column_list, before.if_not_exists)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALCREATE)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_CREATE_FROM_SELECT_TO_PHYSICAL, pattern)

def apply(self, before: LogicalCreate, context: OptimizerContext):
    after = CreateFromSelectPlan(before.video, before.column_list, before.if_not_exists)
    for child in before.children:
        after.append_child(child)
    yield after

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALRENAME)
    super().__init__(RuleType.LOGICAL_RENAME_TO_PHYSICAL, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALCREATEFUNCTION)
    super().__init__(RuleType.LOGICAL_CREATE_FUNCTION_TO_PHYSICAL, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALCREATEFUNCTION)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_CREATE_FUNCTION_FROM_SELECT_TO_PHYSICAL, pattern)

class LogicalCreateIndexToVectorIndex(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALCREATEINDEX)
        super().__init__(RuleType.LOGICAL_CREATE_INDEX_TO_VECTOR_INDEX, pattern)

    def promise(self):
        return Promise.LOGICAL_CREATE_INDEX_TO_VECTOR_INDEX

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalCreateIndex, context: OptimizerContext):
        after = CreateIndexPlan(before.name, before.if_not_exists, before.table_ref, before.col_list, before.vector_store_type, before.project_expr_list, before.index_def)
        child = SeqScanPlan(None, before.project_expr_list, before.table_ref.alias)
        batch_mem_size = context.db.catalog().get_configuration_catalog_value('batch_mem_size')
        child.append_child(StoragePlan(before.table_ref.table.table_obj, before.table_ref, batch_mem_size=batch_mem_size))
        after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALCREATEINDEX)
    super().__init__(RuleType.LOGICAL_CREATE_INDEX_TO_VECTOR_INDEX, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICAL_DROP_OBJECT)
    super().__init__(RuleType.LOGICAL_DROP_OBJECT_TO_PHYSICAL, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALINSERT)
    super().__init__(RuleType.LOGICAL_INSERT_TO_PHYSICAL, pattern)

class LogicalDeleteToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALDELETE)
        super().__init__(RuleType.LOGICAL_DELETE_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_DELETE_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalDelete, context: OptimizerContext):
        after = DeletePlan(before.table_ref, before.where_clause)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALDELETE)
    super().__init__(RuleType.LOGICAL_DELETE_TO_PHYSICAL, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALLOADDATA)
    super().__init__(RuleType.LOGICAL_LOAD_TO_PHYSICAL, pattern)

class LogicalGetToSeqScan(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALGET)
        super().__init__(RuleType.LOGICAL_GET_TO_SEQSCAN, pattern)

    def promise(self):
        return Promise.LOGICAL_GET_TO_SEQSCAN

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalGet, context: OptimizerContext):
        after = SeqScanPlan(None, before.target_list, before.alias)
        batch_mem_size = context.db.catalog().get_configuration_catalog_value('batch_mem_size')
        after.append_child(StoragePlan(before.table_obj, before.video, predicate=before.predicate, sampling_rate=before.sampling_rate, sampling_type=before.sampling_type, chunk_params=before.chunk_params, batch_mem_size=batch_mem_size))
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALGET)
    super().__init__(RuleType.LOGICAL_GET_TO_SEQSCAN, pattern)

class LogicalDerivedGetToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALQUERYDERIVEDGET)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_DERIVED_GET_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_DERIVED_GET_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalQueryDerivedGet, context: OptimizerContext):
        after = SeqScanPlan(before.predicate, before.target_list, before.alias)
        after.append_child(before.children[0])
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALQUERYDERIVEDGET)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_DERIVED_GET_TO_PHYSICAL, pattern)

def apply(self, before: LogicalQueryDerivedGet, context: OptimizerContext):
    after = SeqScanPlan(before.predicate, before.target_list, before.alias)
    after.append_child(before.children[0])
    yield after

class LogicalUnionToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALUNION)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_UNION_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_UNION_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalUnion, context: OptimizerContext):
        after = UnionPlan(before.all)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALUNION)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_UNION_TO_PHYSICAL, pattern)

def apply(self, before: LogicalUnion, context: OptimizerContext):
    after = UnionPlan(before.all)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalGroupByToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALGROUPBY)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_GROUPBY_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_GROUPBY_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalGroupBy, context: OptimizerContext):
        after = GroupByPlan(before.groupby_clause)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALGROUPBY)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_GROUPBY_TO_PHYSICAL, pattern)

def apply(self, before: LogicalGroupBy, context: OptimizerContext):
    after = GroupByPlan(before.groupby_clause)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalOrderByToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALORDERBY)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_ORDERBY_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_ORDERBY_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalOrderBy, context: OptimizerContext):
        after = OrderByPlan(before.orderby_list)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALORDERBY)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_ORDERBY_TO_PHYSICAL, pattern)

def apply(self, before: LogicalOrderBy, context: OptimizerContext):
    after = OrderByPlan(before.orderby_list)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalLimitToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALLIMIT)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_LIMIT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_LIMIT_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalLimit, context: OptimizerContext):
        after = LimitPlan(before.limit_count)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALLIMIT)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_LIMIT_TO_PHYSICAL, pattern)

def apply(self, before: LogicalLimit, context: OptimizerContext):
    after = LimitPlan(before.limit_count)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalFunctionScanToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALFUNCTIONSCAN)
        super().__init__(RuleType.LOGICAL_FUNCTION_SCAN_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_FUNCTION_SCAN_TO_PHYSICAL

    def check(self, before: Operator, context: OptimizerContext):
        return True

    def apply(self, before: LogicalFunctionScan, context: OptimizerContext):
        after = FunctionScanPlan(before.func_expr, before.do_unnest)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALFUNCTIONSCAN)
    super().__init__(RuleType.LOGICAL_FUNCTION_SCAN_TO_PHYSICAL, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALJOIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_LATERAL_JOIN_TO_PHYSICAL, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALJOIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_JOIN_TO_PHYSICAL_HASH_JOIN, pattern)

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

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALJOIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_JOIN_TO_PHYSICAL_NESTED_LOOP_JOIN, pattern)

class LogicalFilterToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALFILTER)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_FILTER_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_FILTER_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalFilter, context: OptimizerContext):
        after = PredicatePlan(before.predicate)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALFILTER)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_FILTER_TO_PHYSICAL, pattern)

def apply(self, before: LogicalFilter, context: OptimizerContext):
    after = PredicatePlan(before.predicate)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalProjectToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALPROJECT)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_PROJECT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_PROJECT_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalProject, context: OptimizerContext):
        after = ProjectPlan(before.target_list)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALPROJECT)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_PROJECT_TO_PHYSICAL, pattern)

def apply(self, before: LogicalProject, context: OptimizerContext):
    after = ProjectPlan(before.target_list)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalProjectNoTableToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALPROJECT)
        super().__init__(RuleType.LOGICAL_PROJECT_NO_TABLE_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_PROJECT_NO_TABLE_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalProject, context: OptimizerContext):
        after = ProjectPlan(before.target_list)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALPROJECT)
    super().__init__(RuleType.LOGICAL_PROJECT_NO_TABLE_TO_PHYSICAL, pattern)

def apply(self, before: LogicalProject, context: OptimizerContext):
    after = ProjectPlan(before.target_list)
    yield after

class LogicalShowToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICAL_SHOW)
        super().__init__(RuleType.LOGICAL_SHOW_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_SHOW_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalShow, context: OptimizerContext):
        after = ShowInfoPlan(before.show_type, before.show_val)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICAL_SHOW)
    super().__init__(RuleType.LOGICAL_SHOW_TO_PHYSICAL, pattern)

class LogicalExplainToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALEXPLAIN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_EXPLAIN_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_EXPLAIN_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalExplain, context: OptimizerContext):
        after = ExplainPlan(before.explainable_opr)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALEXPLAIN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_EXPLAIN_TO_PHYSICAL, pattern)

def apply(self, before: LogicalExplain, context: OptimizerContext):
    after = ExplainPlan(before.explainable_opr)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalApplyAndMergeToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalApplyAndMerge, context: OptimizerContext):
        after = ApplyAndMergePlan(before.func_expr, before.alias, before.do_unnest)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL, pattern)

def apply(self, before: LogicalApplyAndMerge, context: OptimizerContext):
    after = ApplyAndMergePlan(before.func_expr, before.alias, before.do_unnest)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalVectorIndexScanToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICAL_VECTOR_INDEX_SCAN)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_VECTOR_INDEX_SCAN_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_VECTOR_INDEX_SCAN_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalVectorIndexScan, context: OptimizerContext):
        after = VectorIndexScanPlan(before.index, before.limit_count, before.search_query_expr)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICAL_VECTOR_INDEX_SCAN)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_VECTOR_INDEX_SCAN_TO_PHYSICAL, pattern)

def apply(self, before: LogicalVectorIndexScan, context: OptimizerContext):
    after = VectorIndexScanPlan(before.index, before.limit_count, before.search_query_expr)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalExchangeToPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALEXCHANGE)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_EXCHANGE_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_EXCHANGE_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalExchange, context: OptimizerContext):
        after = ExchangePlan(before.view)
        for child in before.children:
            after.append_child(child)
        yield after

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALEXCHANGE)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_EXCHANGE_TO_PHYSICAL, pattern)

def apply(self, before: LogicalExchange, context: OptimizerContext):
    after = ExchangePlan(before.view)
    for child in before.children:
        after.append_child(child)
    yield after

class LogicalApplyAndMergeToRayPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL

    def check(self, grp_id: int, context: OptimizerContext):
        return True

    def apply(self, before: LogicalApplyAndMerge, context: OptimizerContext):
        apply_plan = ApplyAndMergePlan(before.func_expr, before.alias, before.do_unnest)
        parallelism = 2
        ray_process_env_dict = get_ray_env_dict()
        ray_parallel_env_conf_dict = [ray_process_env_dict for _ in range(parallelism)]
        exchange_plan = ExchangePlan(inner_plan=apply_plan, parallelism=parallelism, ray_pull_env_conf_dict=ray_process_env_dict, ray_parallel_env_conf_dict=ray_parallel_env_conf_dict)
        for child in before.children:
            exchange_plan.append_child(child)
        yield exchange_plan

def __init__(self):
    pattern = Pattern(OperatorType.LOGICAL_APPLY_AND_MERGE)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_APPLY_AND_MERGE_TO_PHYSICAL, pattern)

def apply(self, before: LogicalApplyAndMerge, context: OptimizerContext):
    apply_plan = ApplyAndMergePlan(before.func_expr, before.alias, before.do_unnest)
    parallelism = 2
    ray_process_env_dict = get_ray_env_dict()
    ray_parallel_env_conf_dict = [ray_process_env_dict for _ in range(parallelism)]
    exchange_plan = ExchangePlan(inner_plan=apply_plan, parallelism=parallelism, ray_pull_env_conf_dict=ray_process_env_dict, ray_parallel_env_conf_dict=ray_parallel_env_conf_dict)
    for child in before.children:
        exchange_plan.append_child(child)
    yield exchange_plan

class LogicalProjectToRayPhysical(Rule):

    def __init__(self):
        pattern = Pattern(OperatorType.LOGICALPROJECT)
        pattern.append_child(Pattern(OperatorType.DUMMY))
        super().__init__(RuleType.LOGICAL_PROJECT_TO_PHYSICAL, pattern)

    def promise(self):
        return Promise.LOGICAL_PROJECT_TO_PHYSICAL

    def check(self, before: LogicalProject, context: OptimizerContext):
        return True

    def apply(self, before: LogicalProject, context: OptimizerContext):
        project_plan = ProjectPlan(before.target_list)
        if before.target_list is None or not any([isinstance(expr, FunctionExpression) for expr in before.target_list]):
            for child in before.children:
                project_plan.append_child(child)
            yield project_plan
        else:
            parallelism = 2
            ray_process_env_dict = get_ray_env_dict()
            ray_parallel_env_conf_dict = [ray_process_env_dict for _ in range(parallelism)]
            exchange_plan = ExchangePlan(inner_plan=project_plan, parallelism=parallelism, ray_pull_env_conf_dict=ray_process_env_dict, ray_parallel_env_conf_dict=ray_parallel_env_conf_dict)
            for child in before.children:
                exchange_plan.append_child(child)
            yield exchange_plan

def __init__(self):
    pattern = Pattern(OperatorType.LOGICALPROJECT)
    pattern.append_child(Pattern(OperatorType.DUMMY))
    super().__init__(RuleType.LOGICAL_PROJECT_TO_PHYSICAL, pattern)

def apply(self, before: LogicalProject, context: OptimizerContext):
    project_plan = ProjectPlan(before.target_list)
    if before.target_list is None or not any([isinstance(expr, FunctionExpression) for expr in before.target_list]):
        for child in before.children:
            project_plan.append_child(child)
        yield project_plan
    else:
        parallelism = 2
        ray_process_env_dict = get_ray_env_dict()
        ray_parallel_env_conf_dict = [ray_process_env_dict for _ in range(parallelism)]
        exchange_plan = ExchangePlan(inner_plan=project_plan, parallelism=parallelism, ray_pull_env_conf_dict=ray_process_env_dict, ray_parallel_env_conf_dict=ray_parallel_env_conf_dict)
        for child in before.children:
            exchange_plan.append_child(child)
        yield exchange_plan

class LoadMultimediaExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: LoadDataPlan):
        super().__init__(db, node)
        self.media_type = self.node.file_options['file_format']
        if self.media_type == FileFormatType.IMAGE:
            try_to_import_cv2()
        elif self.media_type == FileFormatType.VIDEO:
            try_to_import_decord()
            try_to_import_cv2()

    def exec(self, *args, **kwargs):
        storage_engine = None
        table_obj = None
        try:
            video_files = []
            valid_files = []
            if self.node.file_path.as_posix().startswith('s3:/'):
                s3_dir = Path(self.catalog().get_configuration_catalog_value('s3_download_dir'))
                dst_path = s3_dir / self.node.table_info.table_name
                dst_path.mkdir(parents=True, exist_ok=True)
                video_files = download_from_s3(self.node.file_path, dst_path)
            else:
                video_files = list(iter_path_regex(self.node.file_path))
            valid_files, invalid_files = ([], [])
            if len(video_files) < mp.cpu_count() * 2:
                valid_bitmap = [self._is_media_valid(path) for path in video_files]
            else:
                pool = Pool(mp.cpu_count())
                valid_bitmap = pool.map(self._is_media_valid, video_files)
            if False in valid_bitmap:
                invalid_files = [str(path) for path, is_valid in zip(video_files, valid_bitmap) if not is_valid]
                invalid_files_str = '\n'.join(invalid_files)
                err_msg = f"no valid file found at -- '{invalid_files_str}'."
                logger.error(err_msg)
            valid_files = [str(path) for path, is_valid in zip(video_files, valid_bitmap) if is_valid]
            if not valid_files:
                raise DatasetFileNotFoundError(f"no file found at -- '{str(self.node.file_path)}'.")
            table_info = self.node.table_info
            database_name = table_info.database_name
            table_name = table_info.table_name
            do_create = False
            table_obj = self.catalog().get_table_catalog_entry(table_name, database_name)
            if table_obj:
                msg = f'Adding to an existing table {table_name}.'
                logger.info(msg)
            else:
                table_obj = self.catalog().create_and_insert_multimedia_table_catalog_entry(table_name, self.media_type)
                do_create = True
            storage_engine = StorageEngine.factory(self.db, table_obj)
            if do_create:
                storage_engine.create(table_obj)
            storage_engine.write(table_obj, Batch(pd.DataFrame({'file_path': valid_files})))
        except Exception as e:
            if storage_engine and table_obj:
                self._rollback_load(storage_engine, table_obj, do_create)
            err_msg = f'Load {self.media_type.name} failed: {str(e)}'
            raise ExecutorError(err_msg)
        else:
            yield Batch(pd.DataFrame([f'Number of loaded {self.media_type.name}: {str(len(valid_files))}']))

    def _rollback_load(self, storage_engine: AbstractStorageEngine, table_obj: TableCatalogEntry, do_create: bool):
        if do_create:
            storage_engine.drop(table_obj)

    def _is_media_valid(self, file_path: Path):
        file_path = Path(file_path)
        if validate_media(file_path, self.media_type):
            return True
        return False

def __init__(self, db: EvaDBDatabase, node: LoadDataPlan):
    super().__init__(db, node)
    self.media_type = self.node.file_options['file_format']
    if self.media_type == FileFormatType.IMAGE:
        try_to_import_cv2()
    elif self.media_type == FileFormatType.VIDEO:
        try_to_import_decord()
        try_to_import_cv2()

class BuildJoinExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: HashJoinBuildPlan):
        super().__init__(db, node)
        self.predicate = None
        self.join_type = node.join_type
        self.build_keys = node.build_keys

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        cumm_batches = [batch for batch in child_executor.exec() if not batch.empty()]
        cumm_batches = Batch.concat(cumm_batches)
        hash_keys = [key.col_alias for key in self.build_keys]
        cumm_batches.reassign_indices_to_hash(hash_keys)
        yield cumm_batches

def __init__(self, db: EvaDBDatabase, node: HashJoinBuildPlan):
    super().__init__(db, node)
    self.predicate = None
    self.join_type = node.join_type
    self.build_keys = node.build_keys

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

def __init__(self, db: EvaDBDatabase, node: LimitPlan):
    super().__init__(db, node)
    self._limit_count = node.limit_value

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

def __init__(self, db: EvaDBDatabase, node: DropObjectPlan):
    super().__init__(db, node)

class LoadCSVExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: LoadDataPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        """
        Read the input csv file using pandas and persist data
        using storage engine
        """
        table_info = self.node.table_info
        database_name = table_info.database_name
        table_name = table_info.table_name
        table_obj = self.catalog().get_table_catalog_entry(table_name, database_name)
        if table_obj is None:
            error = f'{table_name} does not exist.'
            logger.error(error)
            raise ExecutorError(error)
        column_list = []
        for column in table_obj.columns:
            column_list.append(TupleValueExpression(name=column.name, table_alias=table_obj.name.lower(), col_object=column))
        csv_reader = CSVReader(self.node.file_path, column_list=column_list, batch_mem_size=self.node.batch_mem_size)
        storage_engine = StorageEngine.factory(self.db, table_obj)
        num_loaded_frames = 0
        for batch in csv_reader.read():
            storage_engine.write(table_obj, batch)
            num_loaded_frames += len(batch)
        df_yield_result = Batch(pd.DataFrame({'CSV': str(self.node.file_path), 'Number of loaded rows': num_loaded_frames}, index=[0]))
        yield df_yield_result

def __init__(self, db: EvaDBDatabase, node: LoadDataPlan):
    super().__init__(db, node)

class CreateExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: CreatePlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        is_native_table = self.node.table_info.database_name is not None
        check_if_exists = handle_if_not_exists(self.catalog(), self.node.table_info, self.node.if_not_exists)
        name = self.node.table_info.table_name
        if check_if_exists:
            yield Batch(pd.DataFrame([f'Table {name} already exists']))
            return
        create_table_done = False
        logger.debug(f'Creating table {self.node.table_info}')
        if not is_native_table:
            catalog_entry = self.catalog().create_and_insert_table_catalog_entry(self.node.table_info, self.node.column_list)
        else:
            catalog_entry = create_table_catalog_entry_for_native_table(self.node.table_info, self.node.column_list)
        storage_engine = StorageEngine.factory(self.db, catalog_entry)
        try:
            storage_engine.create(table=catalog_entry)
            create_table_done = True
            msg = f'The table {name} has been successfully created'
            if self.children != []:
                assert len(self.children) == 1, 'Create table from query expects 1 child, finds {}'.format(len(self.children))
                child = self.children[0]
                rows = 0
                for batch in child.exec():
                    batch.drop_column_alias()
                    storage_engine.write(catalog_entry, batch)
                    rows += len(batch)
                msg = f'The table {name} has been successfully created with {rows} rows.'
            yield Batch(pd.DataFrame([msg]))
        except Exception as e:
            with contextlib.suppress(CatalogError):
                if create_table_done:
                    storage_engine.drop(catalog_entry)
            with contextlib.suppress(CatalogError):
                self.catalog().delete_table_catalog_entry(catalog_entry)
            raise e

def __init__(self, db: EvaDBDatabase, node: CreatePlan):
    super().__init__(db, node)

class CreateDatabaseExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: CreateDatabaseStatement):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        db_catalog_entry = self.catalog().get_database_catalog_entry(self.node.database_name)
        if db_catalog_entry is not None:
            if self.node.if_not_exists:
                msg = f'{self.node.database_name} already exists, nothing added.'
                yield Batch(pd.DataFrame([msg]))
                return
            else:
                raise ExecutorError(f'{self.node.database_name} already exists.')
        logger.debug(f'Trying to connect to the provided engine {self.node.engine} with params {self.node.param_dict}')
        with get_database_handler(self.node.engine, **self.node.param_dict):
            pass
        logger.debug(f'Creating database {self.node}')
        self.catalog().insert_database_catalog_entry(self.node.database_name, self.node.engine, self.node.param_dict)
        yield Batch(pd.DataFrame([f'The database {self.node.database_name} has been successfully created.']))

def __init__(self, db: EvaDBDatabase, node: CreateDatabaseStatement):
    super().__init__(db, node)

class SampleExecutor(AbstractExecutor):
    """
    Samples uniformly from the rows.

    Arguments:
        node (AbstractPlan): The Sample Plan

    """

    def __init__(self, db: EvaDBDatabase, node: SamplePlan):
        super().__init__(db, node)
        self._sample_freq = node.sample_freq.value

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        current = 0
        for batch in child_executor.exec():
            result_batch = batch[current::self._sample_freq]
            result_batch.reset_index()
            yield result_batch
            current = (current - len(batch)) % self._sample_freq

def __init__(self, db: EvaDBDatabase, node: SamplePlan):
    super().__init__(db, node)
    self._sample_freq = node.sample_freq.value

class PredicateExecutor(AbstractExecutor):
    """ """

    def __init__(self, db: EvaDBDatabase, node: PredicatePlan):
        super().__init__(db, node)
        self.predicate = node.predicate

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        for batch in child_executor.exec(**kwargs):
            batch = apply_predicate(batch, self.predicate)
            if not batch.empty():
                yield batch
        instrument_function_expression_cost(self.predicate, self.catalog())

def __init__(self, db: EvaDBDatabase, node: PredicatePlan):
    super().__init__(db, node)
    self.predicate = node.predicate

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

def __init__(self, db: EvaDBDatabase, node: UseStatement):
    super().__init__(db, node)
    self._database_name = node.database_name
    self._query_string = node.query_string

class DeleteExecutor(AbstractExecutor):
    """ """

    def __init__(self, db: EvaDBDatabase, node: ProjectPlan):
        super().__init__(db, node)
        self.predicate = node.where_clause

    def predicate_node_to_filter_clause(self, table: TableCatalogEntry, predicate_node: ComparisonExpression):
        filter_clause = None
        left = predicate_node.get_child(0)
        right = predicate_node.get_child(1)
        if isinstance(left, TupleValueExpression):
            column = left.name
            x = table.columns[column]
        elif isinstance(left, ConstantValueExpression):
            value = left.value
            x = value
        else:
            left_filter_clause = self.predicate_node_to_filter_clause(table, left)
        if isinstance(right, TupleValueExpression):
            column = right.name
            y = table.columns[column]
        elif isinstance(right, ConstantValueExpression):
            value = right.value
            y = value
        else:
            right_filter_clause = self.predicate_node_to_filter_clause(table, right)
        if isinstance(predicate_node, LogicalExpression):
            if predicate_node.etype == ExpressionType.LOGICAL_AND:
                filter_clause = and_(left_filter_clause, right_filter_clause)
            elif predicate_node.etype == ExpressionType.LOGICAL_OR:
                filter_clause = or_(left_filter_clause, right_filter_clause)
        elif isinstance(predicate_node, ComparisonExpression):
            assert predicate_node.etype != ExpressionType.COMPARE_CONTAINS and predicate_node.etype != ExpressionType.COMPARE_IS_CONTAINED, f'Predicate type {predicate_node.etype} not supported in delete'
            if predicate_node.etype == ExpressionType.COMPARE_EQUAL:
                filter_clause = x == y
            elif predicate_node.etype == ExpressionType.COMPARE_GREATER:
                filter_clause = x > y
            elif predicate_node.etype == ExpressionType.COMPARE_LESSER:
                filter_clause = x < y
            elif predicate_node.etype == ExpressionType.COMPARE_GEQ:
                filter_clause = x >= y
            elif predicate_node.etype == ExpressionType.COMPARE_LEQ:
                filter_clause = x <= y
            elif predicate_node.etype == ExpressionType.COMPARE_NEQ:
                filter_clause = x != y
        return filter_clause

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        table_catalog = self.node.table_ref.table.table_obj
        storage_engine = StorageEngine.factory(self.db, table_catalog)
        assert table_catalog.table_type == TableType.STRUCTURED_DATA, 'DELETE only implemented for structured data'
        table_to_delete_from = storage_engine._try_loading_table_via_reflection(table_catalog.name)
        sqlalchemy_filter_clause = self.predicate_node_to_filter_clause(table_to_delete_from, predicate_node=self.predicate)
        storage_engine.delete(table_catalog, sqlalchemy_filter_clause)
        yield Batch(pd.DataFrame(['Deleted rows']))

def __init__(self, db: EvaDBDatabase, node: ProjectPlan):
    super().__init__(db, node)
    self.predicate = node.where_clause

class GroupByExecutor(AbstractExecutor):
    """
    Group inputs into 4d segments of length provided in the query
    E.g., "GROUP BY '8 frames'" groups every 8 frames into one segment

    Arguments:
        node (AbstractPlan): The GroupBy Plan

    """

    def __init__(self, db: EvaDBDatabase, node: GroupByPlan):
        super().__init__(db, node)
        numbers_only = re.sub('\\D', '', node.groupby_clause.value)
        self._segment_length = int(numbers_only)

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        buffer = Batch(pd.DataFrame())
        for batch in child_executor.exec(**kwargs):
            new_batch = buffer + batch
            while len(new_batch) >= self._segment_length:
                yield new_batch[:self._segment_length]
                new_batch = new_batch[self._segment_length:]
            buffer = new_batch

def __init__(self, db: EvaDBDatabase, node: GroupByPlan):
    super().__init__(db, node)
    numbers_only = re.sub('\\D', '', node.groupby_clause.value)
    self._segment_length = int(numbers_only)

class QueueReaderExecutor(AbstractExecutor):

    def __init__(self):
        super().__init__(None, None)

    def exec(self, **kwargs) -> Iterator[Batch]:
        assert 'input_queue' in kwargs, 'Invalid ray execution. No input_queue found'
        input_queue = kwargs['input_queue']
        while True:
            next_item = input_queue.get(block=True)
            if next_item is StageCompleteSignal:
                input_queue.put(StageCompleteSignal)
                break
            elif isinstance(next_item, ExecutorError):
                input_queue.put(next_item)
                raise next_item
            else:
                yield next_item

def __init__(self):
    super().__init__(None, None)

def exec(self, **kwargs) -> Iterator[Batch]:
    assert 'input_queue' in kwargs, 'Invalid ray execution. No input_queue found'
    input_queue = kwargs['input_queue']
    while True:
        next_item = input_queue.get(block=True)
        if next_item is StageCompleteSignal:
            input_queue.put(StageCompleteSignal)
            break
        elif isinstance(next_item, ExecutorError):
            input_queue.put(next_item)
            raise next_item
        else:
            yield next_item

class ExchangeExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: ExchangePlan):
        self.inner_plan = node.inner_plan
        self.parallelism = node.parallelism
        self.ray_pull_env_conf_dict = node.ray_pull_env_conf_dict
        self.ray_parallel_env_conf_dict = node.ray_parallel_env_conf_dict
        super().__init__(db, node)

    def build_inner_executor(self, inner_executor):
        self.inner_executor = inner_executor
        self.inner_executor.children = [QueueReaderExecutor()]

    def exec(self) -> Iterator[Batch]:
        from ray.util.queue import Queue
        input_queue = Queue(maxsize=100)
        output_queue = Queue(maxsize=100)
        assert len(self.children) == 1, 'Exchange currently only supports parallelization of node with only one child'
        ray_pull_task = ray_pull().remote(self.ray_pull_env_conf_dict, self.children[0], input_queue)
        ray_parallel_task_list = []
        for i in range(self.parallelism):
            ray_parallel_task_list.append(ray_parallel().remote(self.ray_parallel_env_conf_dict[i], self.inner_executor, input_queue, output_queue))
        ray_wait_and_alert().remote([ray_pull_task], input_queue)
        ray_wait_and_alert().remote(ray_parallel_task_list, output_queue)
        while True:
            res = output_queue.get(block=True)
            if res is StageCompleteSignal:
                break
            elif isinstance(res, ExecutorError):
                raise res
            else:
                yield res

def __init__(self, db: EvaDBDatabase, node: ExchangePlan):
    self.inner_plan = node.inner_plan
    self.parallelism = node.parallelism
    self.ray_pull_env_conf_dict = node.ray_pull_env_conf_dict
    self.ray_parallel_env_conf_dict = node.ray_parallel_env_conf_dict
    super().__init__(db, node)

def exec(self) -> Iterator[Batch]:
    from ray.util.queue import Queue
    input_queue = Queue(maxsize=100)
    output_queue = Queue(maxsize=100)
    assert len(self.children) == 1, 'Exchange currently only supports parallelization of node with only one child'
    ray_pull_task = ray_pull().remote(self.ray_pull_env_conf_dict, self.children[0], input_queue)
    ray_parallel_task_list = []
    for i in range(self.parallelism):
        ray_parallel_task_list.append(ray_parallel().remote(self.ray_parallel_env_conf_dict[i], self.inner_executor, input_queue, output_queue))
    ray_wait_and_alert().remote([ray_pull_task], input_queue)
    ray_wait_and_alert().remote(ray_parallel_task_list, output_queue)
    while True:
        res = output_queue.get(block=True)
        if res is StageCompleteSignal:
            break
        elif isinstance(res, ExecutorError):
            raise res
        else:
            yield res

class PPExecutor(AbstractExecutor):
    """
    Applies PP to filter out the frames that doesn't satisfy the condition
    Arguments:
        node (AbstractPlan): ...

    Note: This look kind of redundant. This logic for now is similar to that
    of sequential scan executor. Will decide to delete it depending on how
    sequential scan evolves.
    """

    def __init__(self, db: EvaDBDatabase, node: PPScanPlan):
        super().__init__(db, node)
        self.predicate = node.predicate

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        for batch in child_executor.exec():
            outcomes = self.predicate.evaluate(batch)
            required_frame_ids = []
            for i, outcome in enumerate(outcomes):
                if outcome:
                    required_frame_ids.append(i)
            yield batch[required_frame_ids]

def __init__(self, db: EvaDBDatabase, node: PPScanPlan):
    super().__init__(db, node)
    self.predicate = node.predicate

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

def __init__(self, db: EvaDBDatabase, node: VectorIndexScanPlan):
    super().__init__(db, node)
    self.index_name = node.index.name
    self.vector_store_type = node.index.type
    self.feat_column = node.index.feat_column
    self.limit_count = node.limit_count
    self.search_query_expr = node.search_query_expr

class UnionExecutor(AbstractExecutor):
    """
    Merge the seq scan queries
    Arguments:
        node (AbstractPlan): The UnionPlan

    """

    def __init__(self, db: EvaDBDatabase, node: UnionPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        assert self.node.all is True, 'Only UNION ALL is supported now.'
        for child in self.children:
            for batch in child.exec():
                yield batch

def __init__(self, db: EvaDBDatabase, node: UnionPlan):
    super().__init__(db, node)

class ProjectExecutor(AbstractExecutor):
    """ """

    def __init__(self, db: EvaDBDatabase, node: ProjectPlan):
        super().__init__(db, node)
        self.target_list = node.target_list

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        if len(self.children) == 0:
            dummy_batch = Batch(pd.DataFrame([0]))
            batch = apply_project(dummy_batch, self.target_list)
            if not batch.empty():
                yield batch
        elif len(self.children) == 1:
            child_executor = self.children[0]
            for batch in child_executor.exec(**kwargs):
                batch = apply_project(batch, self.target_list)
                if not batch.empty():
                    yield batch
        else:
            raise ExecutorError('ProjectExecutor has more than 1 children.')
        instrument_function_expression_cost(self.target_list, self.catalog())

def __init__(self, db: EvaDBDatabase, node: ProjectPlan):
    super().__init__(db, node)
    self.target_list = node.target_list

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

def __init__(self, db: EvaDBDatabase, node: OrderByPlan):
    super().__init__(db, node)
    self._orderby_list = node.orderby_list
    self._columns = node.columns
    self._sort_types = node.sort_types
    self.batch_sizes = []

class NestedLoopJoinExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: NestedLoopJoinPlan):
        super().__init__(db, node)
        self.predicate = node.join_predicate

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        outer = self.children[0]
        inner = self.children[1]
        for row1 in outer.exec(**kwargs):
            for row2 in inner.exec(**kwargs):
                result_batch = Batch.join(row1, row2)
                result_batch.reset_index()
                result_batch = apply_predicate(result_batch, self.predicate)
                if not result_batch.empty():
                    yield result_batch
        if self.predicate:
            instrument_function_expression_cost(self.predicate, self.catalog())

def __init__(self, db: EvaDBDatabase, node: NestedLoopJoinPlan):
    super().__init__(db, node)
    self.predicate = node.join_predicate

class SequentialScanExecutor(AbstractExecutor):
    """
    Applies predicates to filter the frames which satisfy the condition
    Arguments:
        node (AbstractPlan): The SequentialScanPlan

    """

    def __init__(self, db: EvaDBDatabase, node: SeqScanPlan):
        super().__init__(db, node)
        self.predicate = node.predicate
        self.project_expr = node.columns
        self.alias = node.alias

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        for batch in child_executor.exec(**kwargs):
            if self.alias:
                batch.modify_column_alias(self.alias)
            batch = apply_predicate(batch, self.predicate)
            batch = apply_project(batch, self.project_expr)
            if not batch.empty():
                yield batch
        if self.predicate or self.project_expr:
            catalog = self.catalog()
            instrument_function_expression_cost(self.predicate, catalog)
            instrument_function_expression_cost(self.project_expr, catalog)

def __init__(self, db: EvaDBDatabase, node: SeqScanPlan):
    super().__init__(db, node)
    self.predicate = node.predicate
    self.project_expr = node.columns
    self.alias = node.alias

class SetExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: SetStatement):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        """
        NOTE :- Currently adding adding all configs in 'default' category.
        The idea is to deprecate category to maintain the same format for
        the query as DuckDB and Postgres

        Ref :-
        https://www.postgresql.org/docs/7.0/sql-set.htm
        https://duckdb.org/docs/sql/configuration.html

        This design change for configuration manager will be taken care of
        as a separate PR for the issue #1140, where all instances of config use
        will be replaced
        """
        if self.node.config_name in RESERVED_CONFIG_KEYWORDS:
            raise Exception('{} is a reserved keyword for configurations. Please use a word other than the following list: {}'.format(self.node.config_name, RESERVED_CONFIG_KEYWORDS))
        self.catalog().upsert_configuration_catalog_entry(key=self.node.config_name, value=self.node.config_value.value)

def __init__(self, db: EvaDBDatabase, node: SetStatement):
    super().__init__(db, node)

class InsertExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: InsertPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        storage_engine = None
        table_catalog_entry = None
        table_name = self.node.table_ref.table.table_name
        database_name = self.node.table_ref.table.database_name
        table_catalog_entry = self.catalog().get_table_catalog_entry(table_name, database_name)
        assert table_catalog_entry.table_type == TableType.STRUCTURED_DATA, 'INSERT only implemented for structured data'
        tuples_to_insert = [tuple((i.value for i in val_node)) for val_node in self.node.value_list]
        columns_to_insert = [col_node.name for col_node in self.node.column_list]
        dataframe = pd.DataFrame(tuples_to_insert, columns=columns_to_insert)
        batch = Batch(dataframe)
        storage_engine = StorageEngine.factory(self.db, table_catalog_entry)
        storage_engine.write(table_catalog_entry, batch)
        for index in self.db.catalog().get_all_index_catalog_entries():
            is_index_on_current_table = False
            for column in table_catalog_entry.columns:
                if column == index.feat_column:
                    is_index_on_current_table = True
                    break
            if is_index_on_current_table:
                create_index_query = index.index_def
                create_index_query_list = create_index_query.split(' ')
                if_not_exists = ' '.join(create_index_query_list[2:5]).lower()
                if if_not_exists != 'if not exists':
                    create_index_query = ' '.join(create_index_query_list[:2]) + ' IF NOT EXISTS ' + ' '.join(create_index_query_list[2:])
                from evadb.server.command_handler import execute_query_fetch_all
                execute_query_fetch_all(self.db, create_index_query)
        yield Batch(pd.DataFrame([f'Number of rows loaded: {str(len(tuples_to_insert))}']))

def __init__(self, db: EvaDBDatabase, node: InsertPlan):
    super().__init__(db, node)

@ray.remote(num_cpus=0)
def _ray_wait_and_alert(tasks: List[ray.ObjectRef], queue: Queue):
    try:
        ray.get(tasks)
        queue.put(StageCompleteSignal)
    except RayTaskError as e:
        queue.put(ExecutorError(e.cause))

@ray.remote(max_calls=1)
def _ray_parallel(conf_dict: Dict[str, str], executor: Callable, input_queue: Queue, output_queue: Queue):
    for k, v in conf_dict.items():
        os.environ[k] = v
    gen = executor(input_queue=input_queue)
    for next_item in gen:
        output_queue.put(next_item)

@ray.remote(max_calls=1)
def _ray_pull(conf_dict: Dict[str, str], executor: Callable, input_queue: Queue):
    for k, v in conf_dict.items():
        os.environ[k] = v
    for next_item in executor():
        input_queue.put(next_item)

class ApplyAndMergeExecutor(AbstractExecutor):
    """
    Apply the function expression to the input data, merge the output of the function
    with the input data, and yield the result to the parent. The current implementation
    assumes an inner join while merging. Therefore, if the function does not return any
    output, the input rows are dropped.
    Arguments:
        node (AbstractPlan): ApplyAndMergePlan

    """

    def __init__(self, db: EvaDBDatabase, node: ApplyAndMergePlan):
        super().__init__(db, node)
        self.func_expr = node.func_expr
        self.do_unnest = node.do_unnest
        self.alias = node.alias

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        child_executor = self.children[0]
        for batch in child_executor.exec(**kwargs):
            func_result = self.func_expr.evaluate(batch)
            output = Batch.merge_column_wise([batch, func_result])
            if self.do_unnest:
                output.unnest(func_result.columns)
                output.reset_index()
            yield output
        instrument_function_expression_cost(self.func_expr, self.catalog())

def __init__(self, db: EvaDBDatabase, node: ApplyAndMergePlan):
    super().__init__(db, node)
    self.func_expr = node.func_expr
    self.do_unnest = node.do_unnest
    self.alias = node.alias

class ShowInfoExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: ShowInfoPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        show_entries = []
        assert self.node.show_type is ShowType.FUNCTIONS or ShowType.TABLES or ShowType.DATABASES or ShowType.CONFIGS, f'Show command does not support type {self.node.show_type}'
        if self.node.show_type is ShowType.FUNCTIONS:
            functions = self.catalog().get_all_function_catalog_entries()
            for function in functions:
                show_entries.append(function.display_format())
        elif self.node.show_type is ShowType.TABLES:
            tables = self.catalog().get_all_table_catalog_entries()
            for table in tables:
                if table.table_type != TableType.SYSTEM_STRUCTURED_DATA:
                    show_entries.append(table.name)
            show_entries = {'name': show_entries}
        elif self.node.show_type is ShowType.DATABASES:
            databases = self.catalog().get_all_database_catalog_entries()
            for db in databases:
                show_entries.append(db.display_format())
        elif self.node.show_type is ShowType.CONFIGS:
            show_entries = {}
            if self.node.show_val.upper() == ShowType.CONFIGS.name:
                configs = self.catalog().get_all_configuration_catalog_entries()
                for config in configs:
                    show_entries[config.key] = config.value
            else:
                value = self.catalog().get_configuration_catalog_value(key=self.node.show_val.upper())
                show_entries = {}
                if value is not None:
                    show_entries = {self.node.show_val: [value]}
                else:
                    raise Exception('No configuration found with key {}'.format(self.node.show_val))
        yield Batch(pd.DataFrame(show_entries))

def __init__(self, db: EvaDBDatabase, node: ShowInfoPlan):
    super().__init__(db, node)

class CreateJobExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: CreateJobStatement):
        super().__init__(db, node)

    def _parse_datetime_str(self, datetime_str: str) -> datetime:
        datetime_format = '%Y-%m-%d %H:%M:%S'
        date_format = '%Y-%m-%d'
        if re.match('\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}', datetime_str):
            try:
                return datetime.strptime(datetime_str, datetime_format)
            except ValueError:
                raise ExecutorError(f'{datetime_str} is not in the correct datetime format. expected format: {datetime_format}.')
        elif re.match('\\d{4}-\\d{2}-\\d{2}', datetime_str):
            try:
                return datetime.strptime(datetime_str, date_format)
            except ValueError:
                raise ExecutorError(f'{datetime_str} is not in the correct date format. expected format: {date_format}.')
        else:
            raise ValueError(f'{datetime_str} does not match the expected date or datetime format')

    def _get_repeat_time_interval_seconds(self, repeat_interval: int, repeat_period: str) -> int:
        unit_to_seconds = {'seconds': 1, 'minute': 60, 'minutes': 60, 'min': 60, 'hour': 3600, 'hours': 3600, 'day': 86400, 'days': 86400, 'week': 604800, 'weeks': 604800, 'month': 2592000, 'months': 2592000}
        assert repeat_period is None or repeat_period in unit_to_seconds, 'repeat period should be one of these values: seconds | minute | minutes | min | hour | hours | day | days | week | weeks | month | months'
        repeat_interval = 1 if repeat_interval is None else repeat_interval
        return repeat_interval * unit_to_seconds.get(repeat_period, 0)

    def exec(self, *args, **kwargs):
        job_catalog_entry = self.catalog().get_job_catalog_entry(self.node.job_name)
        if job_catalog_entry is not None:
            if self.node.if_not_exists:
                msg = f'A job with name {self.node.job_name} already exists, nothing added.'
                yield Batch(pd.DataFrame([msg]))
                return
            else:
                raise ExecutorError(f'A job with name {self.node.job_name} already exists.')
        logger.debug(f'Creating job {self.node}')
        job_name = self.node.job_name
        queries = []
        parser = Parser()
        for q in self.node.queries:
            try:
                curr_query = str(q)
                parser.parse(curr_query)
                queries.append(curr_query)
            except Exception:
                error_msg = f'Failed to parse the job query: {curr_query}'
                logger.exception(error_msg)
                raise ExecutorError(error_msg)
        start_time = self._parse_datetime_str(self.node.start_time) if self.node.start_time is not None else datetime.datetime.now()
        end_time = self._parse_datetime_str(self.node.end_time) if self.node.end_time is not None else None
        repeat_interval = self._get_repeat_time_interval_seconds(self.node.repeat_interval, self.node.repeat_period)
        active = True
        next_schedule_run = start_time
        self.catalog().insert_job_catalog_entry(job_name, queries, start_time, end_time, repeat_interval, active, next_schedule_run)
        yield Batch(pd.DataFrame([f'The job {self.node.job_name} has been successfully created.']))

def __init__(self, db: EvaDBDatabase, node: CreateJobStatement):
    super().__init__(db, node)

def _get_repeat_time_interval_seconds(self, repeat_interval: int, repeat_period: str) -> int:
    unit_to_seconds = {'seconds': 1, 'minute': 60, 'minutes': 60, 'min': 60, 'hour': 3600, 'hours': 3600, 'day': 86400, 'days': 86400, 'week': 604800, 'weeks': 604800, 'month': 2592000, 'months': 2592000}
    assert repeat_period is None or repeat_period in unit_to_seconds, 'repeat period should be one of these values: seconds | minute | minutes | min | hour | hours | day | days | week | weeks | month | months'
    repeat_interval = 1 if repeat_interval is None else repeat_interval
    return repeat_interval * unit_to_seconds.get(repeat_period, 0)

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

def __init__(self, db: EvaDBDatabase, node: StoragePlan):
    super().__init__(db, node)

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

def __init__(self, db: EvaDBDatabase, node: LoadDataPlan):
    super().__init__(db, node)

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

def __init__(self, db: EvaDBDatabase, node: CreateFunctionPlan):
    super().__init__(db, node)
    self.function_dir = Path(EvaDB_INSTALLATION_DIR) / 'functions'

class HashJoinExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: HashJoinProbePlan):
        super().__init__(db, node)
        self.predicate = node.join_predicate
        self.join_type = node.join_type
        self.probe_keys = node.probe_keys
        self.join_project = node.join_project

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        build_table = self.children[0]
        probe_table = self.children[1]
        hash_keys = [key.col_alias for key in self.probe_keys]
        for build_batch in build_table.exec():
            for probe_batch in probe_table.exec():
                probe_batch.reassign_indices_to_hash(hash_keys)
                join_batch = Batch.join(probe_batch, build_batch)
                join_batch.reset_index()
                join_batch = apply_predicate(join_batch, self.predicate)
                join_batch = apply_project(join_batch, self.join_project)
                yield join_batch
        if self.predicate or self.join_project:
            catalog = self.catalog()
            instrument_function_expression_cost(self.predicate, catalog)
            instrument_function_expression_cost(self.join_project, catalog)

def __init__(self, db: EvaDBDatabase, node: HashJoinProbePlan):
    super().__init__(db, node)
    self.predicate = node.join_predicate
    self.join_type = node.join_type
    self.probe_keys = node.probe_keys
    self.join_project = node.join_project

class RenameExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: RenamePlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        """rename table executor

        Calls the catalog to modified catalog entry corresponding to the table.
        """
        obj = self.node.old_table.table.table_obj
        storage_engine = StorageEngine.factory(self.db, obj)
        storage_engine.rename(obj, self.node.new_name)

def __init__(self, db: EvaDBDatabase, node: RenamePlan):
    super().__init__(db, node)

class ExplainExecutor(AbstractExecutor):

    def __init__(self, db: EvaDBDatabase, node: ExplainPlan):
        super().__init__(db, node)

    def exec(self, *args, **kwargs):
        plan_str = self._exec(self._node.children[0], 0)
        yield Batch(pd.DataFrame([plan_str]))

    def _exec(self, node: AbstractPlan, depth: int):
        cur_str = ' ' * depth * 4 + '|__ ' + str(node.__class__.__name__) + '\n'
        for child in node.children:
            cur_str += self._exec(child, depth + 1)
        return cur_str

def __init__(self, db: EvaDBDatabase, node: ExplainPlan):
    super().__init__(db, node)

class FunctionScanExecutor(AbstractExecutor):
    """
    Executes functional expression which yields a table of rows
    Arguments:
        node (AbstractPlan): FunctionScanPlan

    """

    def __init__(self, db: EvaDBDatabase, node: FunctionScanPlan):
        super().__init__(db, node)
        self.func_expr = node.func_expr
        self.do_unnest = node.do_unnest

    def exec(self, *args, **kwargs) -> Iterator[Batch]:
        assert 'lateral_input' in kwargs, 'Key lateral_input not passed to the FunctionScan'
        lateral_input = kwargs.get('lateral_input')
        if not lateral_input.empty():
            res = self.func_expr.evaluate(lateral_input)
            if not res.empty():
                if self.do_unnest:
                    res.unnest(res.columns)
                yield res
            instrument_function_expression_cost(self.func_expr, self.catalog())

def __init__(self, db: EvaDBDatabase, node: FunctionScanPlan):
    super().__init__(db, node)
    self.func_expr = node.func_expr
    self.do_unnest = node.do_unnest

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

def __init__(self, db: EvaDBDatabase, node: CreateIndexPlan):
    super().__init__(db, node)
    self.name = self.node.name
    self.if_not_exists = self.node.if_not_exists
    self.table_ref = self.node.table_ref
    self.col_list = self.node.col_list
    self.vector_store_type = self.node.vector_store_type
    self.project_expr_list = self.node.project_expr_list
    self.index_def = self.node.index_def

def is_weaviate_available() -> bool:
    try:
        try_to_import_weaviate_client()
        return True
    except ValueError:
        return False

class DatasetFileNotFoundError(Exception):

    def __init__(self, message='The dataset file could not be found. Please verify that the file exists in the specified path.'):
        super().__init__(message)

def __init__(self, message='The dataset file could not be found. Please verify that the file exists in the specified path.'):
    super().__init__(message)

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

def get(self, key: Any):
    value = self._cache.get(key, default=None)
    return value

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

def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
    children = []
    if left is not None:
        children.append(left)
    if right is not None:
        children.append(right)
    super().__init__(exp_type, rtype=ExpressionReturnType.INTEGER, children=children)

def __hash__(self) -> int:
    return hash((super().__hash__(), self.etype))

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

def __init__(self, name: str=None, table_alias: str=None, col_object: Union[ColumnCatalogEntry, FunctionIOCatalogEntry]=None, col_alias=None):
    super().__init__(ExpressionType.TUPLE_VALUE, rtype=ExpressionReturnType.INVALID)
    self._name = name
    self._table_alias = table_alias
    self._col_object = col_object
    self._col_alias = col_alias

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_alias, self.name, self.col_alias, self.col_object))

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

def __init__(self, value: Any, v_type: ColumnType=ColumnType.INTEGER):
    super().__init__(ExpressionType.CONSTANT_VALUE)
    self._value = value
    self._v_type = v_type

def __hash__(self) -> int:
    return hash((super().__hash__(), self.v_type, str(self.value)))

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

def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
    children = []
    if left is not None:
        children.append(left)
    if right is not None:
        children.append(right)
    super().__init__(exp_type, rtype=ExpressionReturnType.FLOAT, children=children)

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

def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
    children = []
    if left is not None:
        children.append(left)
    if right is not None:
        children.append(right)
    super().__init__(exp_type, rtype=ExpressionReturnType.BOOLEAN, children=children)

def __hash__(self) -> int:
    return super().__hash__()

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

def __hash__(self) -> int:
    return hash((self.etype, self.rtype, tuple(self.children)))

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

def __hash__(self) -> int:
    return hash((super().__hash__(), self.name, self.output, self.alias, self.function, tuple(self.output_objs), self._cache))

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

def __init__(self, exp_type: ExpressionType, left: AbstractExpression, right: AbstractExpression):
    children = []
    if left is not None:
        children.append(left)
    if right is not None:
        children.append(right)
    super().__init__(exp_type, rtype=ExpressionReturnType.BOOLEAN, children=children)

def __hash__(self) -> int:
    return super().__hash__()

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

class FunctionCacheCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(FunctionCacheCatalog, db_session)
        self._column_service: ColumnCatalogService = ColumnCatalogService(db_session)
        self._function_service: FunctionCatalogService = FunctionCatalogService(db_session)

    def insert_entry(self, entry: FunctionCacheCatalogEntry) -> FunctionCacheCatalogEntry:
        """Insert a new function cache entry into function cache catalog.
        Arguments:
            `name` (str): name of the cache table
            `function_id` (int): `row_id` of the function on which the cache is built
            `cache_path` (str): path of the cache table
            `args` (List[Any]): arguments of the function whose output is being cached
            `function_depends` (List[FunctionCatalogEntry]): dependent function  entries
            `col_depends` (List[ColumnCatalogEntry]): dependent column entries
        Returns:
            `FunctionCacheCatalogEntry`
        """
        try:
            cache_obj = self.model(name=entry.name, function_id=entry.function_id, cache_path=entry.cache_path, args=entry.args)
            cache_obj._function_depends = [self._function_service.get_entry_by_id(function_id, return_alchemy=True) for function_id in entry.function_depends]
            cache_obj._col_depends = [self._column_service.get_entry_by_id(col_id, return_alchemy=True) for col_id in entry.col_depends]
            cache_obj = cache_obj.save(self.session)
        except Exception as e:
            err_msg = f'Failed to insert entry into function cache catalog with exception {str(e)}'
            logger.exception(err_msg)
            raise CatalogError(err_msg)
        else:
            return cache_obj.as_dataclass()

    def get_entry_by_name(self, name: str) -> FunctionCacheCatalogEntry:
        try:
            entry = self.session.execute(select(self.model).filter(self.model._name == name)).scalar_one()
            return entry.as_dataclass()
        except NoResultFound:
            return None

    def delete_entry(self, cache: FunctionCacheCatalogEntry):
        """Delete cache table from the db
        Arguments:
            cache  (FunctionCacheCatalogEntry): cache to delete
        Returns:
            True if successfully removed else false
        """
        try:
            obj = self.session.execute(select(self.model).filter(self.model._row_id == cache.row_id)).scalar_one()
            obj.delete(self.session)
            return True
        except Exception as e:
            err_msg = f'Delete cache failed for {cache} with error {str(e)}.'
            logger.exception(err_msg)
            raise CatalogError(err_msg)

def __init__(self, db_session: Session):
    super().__init__(FunctionCacheCatalog, db_session)
    self._column_service: ColumnCatalogService = ColumnCatalogService(db_session)
    self._function_service: FunctionCatalogService = FunctionCatalogService(db_session)

class IndexCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(IndexCatalog, db_session)

    def insert_entry(self, name: str, save_file_path: str, type: VectorStoreType, feat_column: ColumnCatalogEntry, function_signature: str, index_def: str) -> IndexCatalogEntry:
        index_entry = IndexCatalog(name, save_file_path, type, feat_column.row_id, function_signature, index_def)
        index_entry = index_entry.save(self.session)
        return index_entry.as_dataclass()

    def get_entry_by_name(self, name: str) -> IndexCatalogEntry:
        try:
            entry = self.query.filter(self.model._name == name).one()
            return entry.as_dataclass()
        except NoResultFound:
            return None

    def get_entry_by_id(self, id: int) -> IndexCatalogEntry:
        try:
            entry = self.query.filter(self.model._row_id == id).one()
            return entry.as_dataclass()
        except NoResultFound:
            return None

    def get_entry_by_column_and_function_signature(self, column: ColumnCatalogEntry, function_signature: str):
        try:
            entry = self.query.filter(self.model._feat_column_id == column.row_id, self.model._function_signature == function_signature).one()
            return entry.as_dataclass()
        except NoResultFound:
            return None

    def delete_entry_by_name(self, name: str):
        try:
            index_obj = self.query.filter(self.model._name == name).one()
            index_metadata = index_obj.as_dataclass()
            if os.path.exists(index_metadata.save_file_path):
                if os.path.isfile(index_metadata.save_file_path):
                    os.remove(index_metadata.save_file_path)
            index_obj.delete(self.session)
        except Exception:
            logger.exception('Delete index failed for name {}'.format(name))
            return False
        return True

def __init__(self, db_session: Session):
    super().__init__(IndexCatalog, db_session)

class ConfigurationCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(ConfigurationCatalog, db_session)

    def insert_entry(self, key: str, value: any):
        try:
            config_catalog_obj = self.model(key=key, value=value)
            config_catalog_obj = config_catalog_obj.save(self.session)
        except Exception as e:
            logger.exception(f'Failed to insert entry into database catalog with exception {str(e)}')
            raise CatalogError(e)

    def get_entry_by_name(self, key: str) -> ConfigurationCatalogEntry:
        """
        Get the table catalog entry with given table name.
        Arguments:
            key  (str): key name
        Returns:
            Configuration Catalog Entry - catalog entry for given key name
        """
        entry = self.session.execute(select(self.model).filter(self.model._key == key)).scalar_one_or_none()
        if entry:
            return entry.as_dataclass()
        return entry

    def upsert_entry(self, key: str, value: any):
        try:
            entry = self.session.execute(select(self.model).filter(self.model._key == key)).scalar_one_or_none()
            if entry:
                entry.update(self.session, _value=value)
            else:
                self.insert_entry(key, value)
        except Exception as e:
            raise CatalogError(f'Error while upserting entry to ConfigurationCatalog: {str(e)}')

def __init__(self, db_session: Session):
    super().__init__(ConfigurationCatalog, db_session)

class JobCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(JobCatalog, db_session)

    def insert_entry(self, name: str, queries: list, start_time: datetime, end_time: datetime, repeat_interval: int, active: bool, next_schedule_run: datetime) -> JobCatalogEntry:
        try:
            job_catalog_obj = self.model(name=name, queries=json.dumps(queries), start_time=start_time, end_time=end_time, repeat_interval=repeat_interval, active=active, next_schedule_run=next_schedule_run)
            job_catalog_obj = job_catalog_obj.save(self.session)
        except Exception as e:
            logger.exception(f'Failed to insert entry into job catalog with exception {str(e)}')
            raise CatalogError(e)
        return job_catalog_obj.as_dataclass()

    def get_entry_by_name(self, job_name: str) -> JobCatalogEntry:
        """
        Get the job catalog entry with given job name.
        Arguments:
            job_name  (str): Job name
        Returns:
            JobCatalogEntry - catalog entry for given job name
        """
        entry = self.session.execute(select(self.model).filter(self.model._name == job_name)).scalar_one_or_none()
        if entry:
            return entry.as_dataclass()
        return entry

    def delete_entry(self, job_entry: JobCatalogEntry):
        """Delete Job from the catalog
        Arguments:
            job  (JobCatalogEntry): job to delete
        Returns:
            True if successfully removed else false
        """
        try:
            job_catalog_obj = self.session.execute(select(self.model).filter(self.model._row_id == job_entry.row_id)).scalar_one_or_none()
            job_catalog_obj.delete(self.session)
            return True
        except Exception as e:
            err_msg = f'Delete Job failed for {job_entry} with error {str(e)}.'
            logger.exception(err_msg)
            raise CatalogError(err_msg)

    def get_all_overdue_jobs(self) -> list:
        """Get the list of jobs that are overdue to be triggered
        Arguments:
            None
        Returns:
            Returns the list of all active overdue jobs
        """
        entries = self.session.execute(select(self.model).filter(and_(self.model._next_scheduled_run <= datetime.datetime.now(), self.model._active == true()))).scalars().all()
        entries = [row.as_dataclass() for row in entries]
        return entries

    def get_next_executable_job(self, only_past_jobs: bool) -> JobCatalogEntry:
        """Get the oldest job that is ready to be triggered by trigger time
        Arguments:
            only_past_jobs (bool): boolean flag to denote if only jobs with trigger time in
                past should be considered
        Returns:
            Returns the first job to be triggered
        """
        entry = self.session.execute(select(self.model).filter(and_(self.model._next_scheduled_run <= datetime.datetime.now(), self.model._active == true()) if only_past_jobs else self.model._active == true()).order_by(self.model._next_scheduled_run.asc()).limit(1)).scalar_one_or_none()
        if entry:
            return entry.as_dataclass()
        return entry

    def update_next_scheduled_run(self, job_name: str, next_scheduled_run: datetime, active: bool):
        """Update the next_scheduled_run and active column as per the provided values
        Arguments:
            job_name (str): job which should be updated

            next_run_time (datetime): the next trigger time for the job

            active (bool): the active status for the job
        Returns:
            void
        """
        job = self.session.query(self.model).filter(self.model._name == job_name).first()
        if job:
            job._next_scheduled_run = next_scheduled_run
            job._active = active
            self.session.commit()

def __init__(self, db_session: Session):
    super().__init__(JobCatalog, db_session)

class TableCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(TableCatalog, db_session)
        self._column_service: ColumnCatalogService = ColumnCatalogService(db_session)

    def insert_entry(self, name: str, file_url: str, identifier_column: str, table_type: TableType, column_list) -> TableCatalogEntry:
        """Insert a new table entry into table catalog.
        Arguments:
            name (str): name of the table
            file_url (str): file path of the table.
            table_type (TableType): type of data in the table
        Returns:
            TableCatalogEntry
        """
        try:
            table_catalog_obj = self.model(name=name, file_url=file_url, identifier_column=identifier_column, table_type=table_type)
            table_catalog_obj = table_catalog_obj.save(self.session)
            for column in column_list:
                column.table_id = table_catalog_obj._row_id
            column_list = self._column_service.create_entries(column_list)
            try:
                self.session.add_all(column_list)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                self.session.delete(table_catalog_obj)
                self.session.commit()
                logger.exception(f'Failed to insert entry into table catalog with exception {str(e)}')
                raise CatalogError(e)
        except Exception as e:
            logger.exception(f'Failed to insert entry into table catalog with exception {str(e)}')
            raise CatalogError(e)
        else:
            return table_catalog_obj.as_dataclass()

    def get_entry_by_id(self, table_id: int, return_alchemy=False) -> TableCatalogEntry:
        """
        Returns the table by ID
        Arguments:
            table_id (int)
            return_alchemy (bool): if True, return a sqlalchemy object
        Returns:
           TableCatalogEntry
        """
        entry = self.session.execute(select(self.model).filter(self.model._row_id == table_id)).scalar_one()
        return entry if return_alchemy else entry.as_dataclass()

    def get_entry_by_name(self, database_name, table_name, return_alchemy=False) -> TableCatalogEntry:
        """
        Get the table catalog entry with given table name.
        Arguments:
            database_name  (str): Database to which table belongs # TODO:
            use this field
            table_name (str): name of the table
        Returns:
            TableCatalogEntry - catalog entry for given table_name
        """
        entry = self.session.execute(select(self.model).filter(self.model._name == table_name)).scalar_one_or_none()
        if entry:
            return entry if return_alchemy else entry.as_dataclass()
        return entry

    def delete_entry(self, table: TableCatalogEntry):
        """Delete table from the db
        Arguments:
            table  (TableCatalogEntry): table to delete
        Returns:
            True if successfully removed else false
        """
        try:
            table_obj = self.session.execute(select(self.model).filter(self.model._row_id == table.row_id)).scalar_one_or_none()
            table_obj.delete(self.session)
            return True
        except Exception as e:
            err_msg = f'Delete table failed for {table} with error {str(e)}.'
            logger.exception(err_msg)
            raise CatalogError(err_msg)

    def rename_entry(self, table: TableCatalogEntry, new_name: str):
        try:
            table_obj = self.session.execute(select(self.model).filter(self.model._row_id == table.row_id)).scalar_one_or_none()
            if table_obj:
                table_obj.update(self.session, _name=new_name)
        except Exception as e:
            err_msg = 'Update table name failed for {} with error {}'.format(table.name, str(e))
            logger.error(err_msg)
            raise RuntimeError(err_msg)

def __init__(self, db_session: Session):
    super().__init__(TableCatalog, db_session)
    self._column_service: ColumnCatalogService = ColumnCatalogService(db_session)

class FunctionCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(FunctionCatalog, db_session)
        self._function_io_service = FunctionIOCatalogService(db_session)
        self._function_metadata_service = FunctionMetadataCatalogService(db_session)

    def insert_entry(self, name: str, impl_path: str, type: str, checksum: str, function_io_list: List[FunctionIOCatalogEntry], function_metadata_list: List[FunctionMetadataCatalogEntry]) -> FunctionCatalogEntry:
        """Insert a new function entry

        Arguments:
            name (str): name of the function
            impl_path (str): path to the function implementation relative to evadb/function
            type (str): function operator kind, classification or detection or etc
            checksum(str): checksum of the function file content, used for consistency

        Returns:
            FunctionCatalogEntry: Returns the new entry created
        """
        function_obj = self.model(name, impl_path, type, checksum)
        function_obj = function_obj.save(self.session)
        for function_io in function_io_list:
            function_io.function_id = function_obj._row_id
        io_objs = self._function_io_service.create_entries(function_io_list)
        for function_metadata in function_metadata_list:
            function_metadata.function_id = function_obj._row_id
        metadata_objs = self._function_metadata_service.create_entries(function_metadata_list)
        try:
            self.session.add_all(io_objs)
            self.session.add_all(metadata_objs)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.session.delete(function_obj)
            self.session.commit()
            logger.exception(f'Failed to insert entry into function catalog with exception {str(e)}')
            raise CatalogError(e)
        else:
            return function_obj.as_dataclass()

    def get_entry_by_name(self, name: str) -> FunctionCatalogEntry:
        """return the function entry that matches the name provided.
           None if no such entry found.

        Arguments:
            name (str): name to be searched
        """
        function_obj = self.session.execute(select(self.model).filter(self.model._name == name)).scalar_one_or_none()
        if function_obj:
            return function_obj.as_dataclass()
        return None

    def get_entry_by_id(self, id: int, return_alchemy=False) -> FunctionCatalogEntry:
        """return the function entry that matches the id provided.
           None if no such entry found.

        Arguments:
            id (int): id to be searched
        """
        function_obj = self.session.execute(select(self.model).filter(self.model._row_id == id)).scalar_one_or_none()
        if function_obj:
            return function_obj if return_alchemy else function_obj.as_dataclass()
        return function_obj

    def delete_entry_by_name(self, name: str):
        """Delete a function entry from the catalog FunctionCatalog

        Arguments:
            name (str): function name to be deleted

        Returns:
            True if successfully deleted else True
        """
        try:
            function_obj = self.session.execute(select(self.model).filter(self.model._name == name)).scalar_one()
            function_obj.delete(self.session)
        except Exception as e:
            logger.exception(f'Delete function failed for name {name} with error {str(e)}')
            return False
        return True

def __init__(self, db_session: Session):
    super().__init__(FunctionCatalog, db_session)
    self._function_io_service = FunctionIOCatalogService(db_session)
    self._function_metadata_service = FunctionMetadataCatalogService(db_session)

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

def __init__(self, db_session: Session):
    super().__init__(FunctionIOCatalog, db_session)

class DatabaseCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(DatabaseCatalog, db_session)

    def insert_entry(self, name: str, engine: str, params: dict):
        try:
            db_catalog_obj = self.model(name=name, engine=engine, params=params)
            db_catalog_obj = db_catalog_obj.save(self.session)
        except Exception as e:
            logger.exception(f'Failed to insert entry into database catalog with exception {str(e)}')
            raise CatalogError(e)

    def get_entry_by_name(self, database_name: str) -> DatabaseCatalogEntry:
        """
        Get the table catalog entry with given table name.
        Arguments:
            database_name  (str): Database name
        Returns:
            DatabaseCatalogEntry - catalog entry for given database name
        """
        entry = self.session.execute(select(self.model).filter(self.model._name == database_name)).scalar_one_or_none()
        if entry:
            return entry.as_dataclass()
        return entry

    def delete_entry(self, database_entry: DatabaseCatalogEntry):
        """Delete database from the catalog
        Arguments:
            database  (DatabaseCatalogEntry): database to delete
        Returns:
            True if successfully removed else false
        """
        try:
            db_catalog_obj = self.session.execute(select(self.model).filter(self.model._row_id == database_entry.row_id)).scalar_one_or_none()
            db_catalog_obj.delete(self.session)
            return True
        except Exception as e:
            err_msg = f'Delete database failed for {database_entry} with error {str(e)}.'
            logger.exception(err_msg)
            raise CatalogError(err_msg)

def __init__(self, db_session: Session):
    super().__init__(DatabaseCatalog, db_session)

class JobHistoryCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(JobHistoryCatalog, db_session)

    def insert_entry(self, job_id: str, job_name: str, execution_start_time: datetime, execution_end_time: datetime) -> JobHistoryCatalogEntry:
        try:
            job_history_catalog_obj = self.model(job_id=job_id, job_name=job_name, execution_start_time=execution_start_time, execution_end_time=execution_end_time)
            job_history_catalog_obj = job_history_catalog_obj.save(self.session)
        except Exception as e:
            logger.exception(f'Failed to insert entry into job history catalog with exception {str(e)}')
            raise CatalogError(e)
        return job_history_catalog_obj.as_dataclass()

    def get_entry_by_job_id(self, job_id: int) -> List[JobHistoryCatalogEntry]:
        """
        Get all the job history catalog entry with given job id.
        Arguments:
            job_id (int): Job id
        Returns:
            list[JobHistoryCatalogEntry]: all history catalog entries for given job id
        """
        entries = self.session.execute(select(self.model).filter(self.model._job_id == job_id)).scalars().all()
        entries = [row.as_dataclass() for row in entries]
        return entries

    def update_entry_end_time(self, job_id: int, execution_start_time: datetime, execution_end_time: datetime):
        """Update the execution_end_time of the entry as per the provided values
        Arguments:
            job_id (int): id of the job whose history entry which should be updated

            execution_start_time (datetime): the start time for the job history entry

            execution_end_time (datetime): the end time for the job history entry
        Returns:
            void
        """
        job_history_entry = self.session.query(self.model).filter(and_(self.model._job_id == job_id, self.model._execution_start_time == execution_start_time)).first()
        if job_history_entry:
            job_history_entry._execution_end_time = execution_end_time
            self.session.commit()

def __init__(self, db_session: Session):
    super().__init__(JobHistoryCatalog, db_session)

class FunctionCostCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(FunctionCostCatalog, db_session)

    def insert_entry(self, function_id: int, name: str, cost: int) -> FunctionCostCatalogEntry:
        """Insert a new function cost entry

        Arguments:
            function_id(int): id of the function
            name (str) : name of the function
            cost(int)  : cost of the function

        Returns:
            FunctionCostCatalogEntry: Returns the new entry created
        """
        try:
            function_obj = self.model(function_id, name, cost)
            function_obj.save(self.session)
        except Exception as e:
            raise CatalogError(f'Error while inserting entry to FunctionCostCatalog: {str(e)}')

    def upsert_entry(self, function_id: int, name: str, new_cost: int):
        """Upserts a new function cost entry

        Arguments:
            function_id(int): id of the function
            name (str) : name of the function
            cost(int)  : cost of the function
        """
        try:
            function_obj = self.session.execute(select(self.model).filter(self.model._function_id == function_id)).scalar_one_or_none()
            if function_obj:
                function_obj.update(self.session, _cost=new_cost)
            else:
                self.insert_entry(function_id, name, new_cost)
        except Exception as e:
            raise CatalogError(f'Error while upserting entry to FunctionCostCatalog: {str(e)}')

    def get_entry_by_name(self, name: str) -> FunctionCostCatalogEntry:
        """return the function cost entry that matches the name provided.
           None if no such entry found.

        Arguments:
            name (str): name to be searched
        """
        try:
            function_obj = self.session.execute(select(self.model).filter(self.model._function_name == name)).scalar_one_or_none()
            if function_obj:
                return function_obj.as_dataclass()
            return None
        except Exception as e:
            raise CatalogError(f'Error while getting entry for function {name} from FunctionCostCatalog: {str(e)}')

def __init__(self, db_session: Session):
    super().__init__(FunctionCostCatalog, db_session)

class ColumnCatalogService(BaseService):

    def __init__(self, db_session: Session):
        super().__init__(ColumnCatalog, db_session)

    def filter_entry_by_table_id_and_name(self, table_id, column_name) -> ColumnCatalogEntry:
        entry = self.session.execute(select(self.model).filter(self.model._table_id == table_id, self.model._name == column_name)).scalar_one_or_none()
        if entry:
            return entry.as_dataclass()
        return entry

    def filter_entries_by_table_id(self, table_id: int) -> List[ColumnCatalogEntry]:
        """return all the columns for table table_id"""
        entries = self.session.execute(select(self.model).filter(self.model._table_id == table_id)).scalars().all()
        return [entry.as_dataclass() for entry in entries]

    def get_entry_by_id(self, col_id: int, return_alchemy=False) -> List[ColumnCatalogEntry]:
        entry = self.session.execute(select(self.model).filter(self.model._row_id == col_id)).scalar_one_or_none()
        if entry:
            return entry if return_alchemy else entry.as_dataclass()
        return entry

    def create_entries(self, column_list: List[ColumnCatalogEntry]):
        catalog_column_objs = [self.model(name=col.name, type=col.type, is_nullable=col.is_nullable, array_type=col.array_type, array_dimensions=col.array_dimensions, table_id=col.table_id) for col in column_list]
        return catalog_column_objs

    def filter_entries_by_table(self, table: TableCatalogEntry) -> List[ColumnCatalogEntry]:
        try:
            entries = self.session.execute(select(self.model).filter(self.model._table_id == table.row_id)).scalars().all()
            return [entry.as_dataclass() for entry in entries]
        except NoResultFound:
            return None

def __init__(self, db_session: Session):
    super().__init__(ColumnCatalog, db_session)

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

def __init__(self, db_session: Session):
    super().__init__(FunctionMetadataCatalog, db_session)

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

def __init__(self, table_ref: TableRef, column_list: List[AbstractExpression]=None, value_list: List[AbstractExpression]=None):
    super().__init__(StatementType.INSERT)
    self._table_ref = table_ref
    self._column_list = column_list
    self._value_list = value_list

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_ref, tuple(self.column_list), tuple((tuple(val) for val in self.value_list))))

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

def __hash__(self) -> int:
    return hash((self.nullable, self.default_value, self.primary, self.unique))

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

def __hash__(self) -> int:
    return hash((self.name, self.type, self.array_type, self.dimension, self.cci))

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

def __init__(self, table_info: TableInfo, if_not_exists: bool, column_list: List[ColumnDefinition]=None, query: SelectStatement=None):
    super().__init__(StatementType.CREATE)
    self._table_info = table_info
    self._if_not_exists = if_not_exists
    self._column_list = column_list
    self._query = query

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_info, self.if_not_exists, tuple(self.column_list or []), self.query))

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

def __init__(self, database_name: str, if_not_exists: bool, engine: str, param_dict: dict):
    super().__init__(StatementType.CREATE_DATABASE)
    self.database_name = database_name
    self.if_not_exists = if_not_exists
    self.engine = engine
    self.param_dict = param_dict

def __hash__(self) -> int:
    return hash((super().__hash__(), self.database_name, self.if_not_exists, self.engine, hash(frozenset(self.param_dict.items()))))

@dataclass
class CreateJobStatement(AbstractStatement):
    job_name: str
    queries: list
    if_not_exists: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    repeat_interval: Optional[int] = None
    repeat_period: Optional[str] = None

    def __hash__(self):
        return hash((super().__hash__(), self.job_name, tuple(self.queries), self.start_time, self.end_time, self.repeat_interval, self.repeat_period))

    def __post_init__(self):
        super().__init__(StatementType.CREATE_JOB)

    def __str__(self):
        start_str = f'\nSTART {self.start_time}' if self.start_time is not None else ''
        end_str = f'\nEND {self.end_time}' if self.end_time is not None else ''
        repeat_str = f'\nEVERY {self.repeat_interval} {self.repeat_period}' if self.repeat_interval is not None else ''
        return f'CREATE JOB {self.job_name} AS\n({(str(q) for q in self.queries)}){start_str} {end_str} {repeat_str}'

def __hash__(self):
    return hash((super().__hash__(), self.job_name, tuple(self.queries), self.start_time, self.end_time, self.repeat_interval, self.repeat_period))

def __post_init__(self):
    super().__init__(StatementType.CREATE_JOB)

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

def __init__(self, config_name: str, config_value: Any):
    super().__init__(StatementType.SET)
    self._config_name = config_name
    self._config_value = config_value

def __hash__(self) -> int:
    return hash((super().__hash__(), self.config_name, self.config_value))

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

def __hash__(self) -> int:
    return hash((self.alias_name, tuple(self.col_names)))

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

def __init__(self, table_ref: TableRef, where_clause: AbstractExpression=None):
    super().__init__(StatementType.DELETE)
    self._table_ref = table_ref
    self._where_clause = where_clause

def __hash__(self) -> int:
    return hash((super().__hash__(), self._table_ref, self.where_clause))

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

def __hash__(self) -> int:
    return hash((super().__hash__(), self.from_table, tuple(self.target_list or []), self.where_clause, self.union_link, self.union_all, self.groupby_clause, tuple(self.orderby_list or []), self.limit_count))

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

def __init__(self, table_info: TableInfo, path: str, column_list: List[AbstractExpression]=None, file_options: dict=None):
    super().__init__(StatementType.LOAD_DATA)
    self._table_info = table_info
    self._path = Path(path)
    self._column_list = column_list
    self._file_options = file_options

def __hash__(self) -> int:
    return hash((super().__hash__(), self.table_info, self.path, tuple(self.column_list or []), frozenset(self.file_options.items())))

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

def __hash__(self) -> int:
    return hash((self.table_name, self.schema_name, self.database_name, self.table_obj))

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

def __hash__(self) -> int:
    return hash((self.join_type, self.left, self.right, self.predicate))

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

def __hash__(self) -> int:
    return hash((self.func_expr, self.do_unnest))

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

def __hash__(self) -> int:
    return hash((self._ref_handle, self.alias, self.sample_freq, self.sample_type, self.get_video, self.get_audio, frozenset(self.chunk_params.items())))

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

def __init__(self, name: str, if_not_exists: bool, table_ref: TableRef, col_list: List[ColumnDefinition], vector_store_type: VectorStoreType, project_expr_list: List[AbstractStatement]):
    super().__init__(StatementType.CREATE_INDEX)
    self._name = name
    self._if_not_exists = if_not_exists
    self._table_ref = table_ref
    self._col_list = col_list
    self._vector_store_type = vector_store_type
    self._project_expr_list = project_expr_list
    self._index_def = self.__str__()

def __hash__(self) -> int:
    return hash((super().__hash__(), self._name, self._if_not_exists, self._table_ref, tuple(self.col_list), self._vector_store_type, tuple(self._project_expr_list), self._index_def))

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

def __init__(self, old_table_ref: TableRef, new_table_name: TableInfo):
    super().__init__(StatementType.RENAME)
    self._old_table_ref = old_table_ref
    self._new_table_name = new_table_name

def __hash__(self) -> int:
    return hash((super().__hash__(), self.old_table_ref, self.new_table_name))

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

def __hash__(self) -> int:
    return hash((super().__hash__(), self.name, self.or_replace, self.if_not_exists, tuple(self.inputs), tuple(self.outputs), self.impl_path, self.function_type, self.query, tuple(self.metadata)))

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

def __init__(self, explainable_stmt: AbstractStatement):
    super().__init__(StatementType.EXPLAIN)
    self._explainable_stmt = explainable_stmt

def __hash__(self) -> int:
    return hash((super().__hash__(), self.explainable_stmt))

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

def __hash__(self) -> int:
    return hash(self.stmt_type)

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

def __init__(self, database_name: str, query_string: str):
    super().__init__(StatementType.USE)
    self._database_name = database_name
    self._query_string = query_string

def __hash__(self) -> int:
    return hash((super().__hash__(), self.database_name, self.query_string))

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

def __init__(self, show_type: ShowType, show_val: Optional[str]=''):
    super().__init__(StatementType.SHOW)
    self._show_type = show_type
    self._show_val = show_val.upper()

def __hash__(self) -> int:
    return hash((super().__hash__(), self.show_type, self.show_val))

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

def __init__(self, object_type: ObjectType, name: str, if_exists: bool):
    super().__init__(StatementType.DROP_OBJECT)
    self._object_type = object_type
    self._name = name
    self._if_exists = if_exists

def __hash__(self) -> int:
    return hash((super().__hash__(), self.object_type, self.name, self.if_exists))

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

def __init__(self, query):
    super().__init__()
    self.query = query

class MariaDbHandler(DBHandler):
    """
    Class for implementing the Maria DB handler as a backend store for
    EvaDB.
    """

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

    def connect(self):
        """
        Establish connection to the database.
        Returns:
          DBHandlerStatus
        """
        try:
            self.connection = mariadb.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database)
            self.connection.autocommit = True
            return DBHandlerStatus(status=True)
        except mariadb.Error as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        Disconnect from the database.
        """
        if self.connection:
            self.connection.close()

    def get_sqlalchmey_uri(self) -> str:
        return f'mariadb+mariadbconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'

    def check_connection(self) -> DBHandlerStatus:
        """
        Method for checking the status of database connection.
        Returns:
          DBHandlerStatus
        """
        if self.connection:
            return DBHandlerStatus(status=True)
        else:
            return DBHandlerStatus(status=False, error='Not connected to the database.')

    def get_tables(self) -> DBHandlerResponse:
        """
        Method to get the list of tables from database.
        Returns:
          DBHandlerStatus
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f"SELECT table_name as 'table_name' FROM information_schema.tables WHERE table_schema='{self.database}'"
            tables_df = pd.read_sql_query(query, self.connection)
            return DBHandlerResponse(data=tables_df)
        except mariadb.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        """
        Method to retrieve the columns of the specified table from the database.
        Args:
          table_name (str): name of the table whose columns are to be retrieved.
        Returns:
          DBHandlerStatus
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f"SELECT column_name as 'name', data_type as 'dtype' FROM information_schema.columns WHERE table_name='{table_name}'"
            columns_df = pd.read_sql_query(query, self.connection)
            columns_df['dtype'] = columns_df['dtype'].apply(self._mariadb_to_python_types)
            return DBHandlerResponse(data=columns_df)
        except mariadb.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _fetch_results_as_df(self, cursor):
        """
        Fetch results from the cursor for the executed query and return the
        query results as dataframe.
        """
        try:
            res = cursor.fetchall()
            res_df = pd.DataFrame(res, columns=[desc[0].lower() for desc in cursor.description])
            return res_df
        except mariadb.ProgrammingError as e:
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
        except mariadb.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _mariadb_to_python_types(self, mariadb_type: str):
        mapping = {'tinyint': int, 'smallint': int, 'mediumint': int, 'bigint': int, 'int': int, 'decimal': float, 'float': float, 'double': float, 'text': str, 'string literals': str, 'char': str, 'varchar': str, 'boolean': bool}
        if mariadb_type in mapping:
            return mapping[mariadb_type]
        else:
            raise Exception(f'Unsupported column {mariadb_type} encountered in the MariaDB. Please raise a feature request!')

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

def __init__(self, name: str, **kwargs):
    super().__init__(name)
    self.token = kwargs.get('token')
    self.channel_name = kwargs.get('channel')

class MysqlHandler(DBHandler):

    def __init__(self, name: str, **kwargs):
        super().__init__(name)
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.database = kwargs.get('database')

    def connect(self):
        try:
            self.connection = mysql.connector.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database)
            self.connection.autocommit = True
            return DBHandlerStatus(status=True)
        except mysql.connector.Error as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def get_sqlalchmey_uri(self) -> str:
        return f'mysql+mysqlconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'

    def check_connection(self) -> DBHandlerStatus:
        if self.connection:
            return DBHandlerStatus(status=True)
        else:
            return DBHandlerStatus(status=False, error='Not connected to the database.')

    def get_tables(self) -> DBHandlerResponse:
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f"SELECT table_name as 'table_name' FROM information_schema.tables WHERE table_schema='{self.database}'"
            tables_df = pd.read_sql_query(query, self.connection)
            return DBHandlerResponse(data=tables_df)
        except mysql.connector.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f"SELECT column_name as 'name', data_type as dtype FROM information_schema.columns WHERE table_name='{table_name}'"
            columns_df = pd.read_sql_query(query, self.connection)
            columns_df['dtype'] = columns_df['dtype'].apply(self._mysql_to_python_types)
            return DBHandlerResponse(data=columns_df)
        except mysql.connector.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _fetch_results_as_df(self, cursor):
        """
        This is currently the only clean solution that we have found so far.
        Reference to MySQL API: https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-fetchall.html
        In short, currently there is no very clean programming way to differentiate
        CREATE, INSERT, SELECT. CREATE and INSERT do not return any result, so calling
        fetchall() on those will yield a programming error. Cursor has an attribute
        rowcount, but it indicates # of rows that are affected. In that case, for both
        INSERT and SELECT rowcount is not 0, so we also cannot use this API to
        differentiate INSERT and SELECT.
        """
        try:
            res = cursor.fetchall()
            if not res:
                return pd.DataFrame({'status': ['success']})
            res_df = pd.DataFrame(res, columns=[desc[0].lower() for desc in cursor.description])
            return res_df
        except mysql.connector.ProgrammingError as e:
            if str(e) == 'no results to fetch':
                return pd.DataFrame({'status': ['success']})
            raise e

    def execute_native_query(self, query_string: str) -> DBHandlerResponse:
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            cursor = self.connection.cursor()
            cursor.execute(query_string)
            return DBHandlerResponse(data=self._fetch_results_as_df(cursor))
        except mysql.connector.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _mysql_to_python_types(self, mysql_type: str):
        mapping = {'char': str, 'varchar': str, 'text': str, 'boolean': bool, 'integer': int, 'int': int, 'float': float, 'double': float}
        if mysql_type in mapping:
            return mapping[mysql_type]
        else:
            raise Exception(f'Unsupported column {mysql_type} encountered in the mysql table. Please raise a feature request!')

def __init__(self, name: str, **kwargs):
    super().__init__(name)
    self.host = kwargs.get('host')
    self.port = kwargs.get('port')
    self.user = kwargs.get('user')
    self.password = kwargs.get('password')
    self.database = kwargs.get('database')

class SnowFlakeDbHandler(DBHandler):
    """
    Class for implementing the SnowFlake DB handler as a backend store for
    EvaDB.
    """

    def __init__(self, name: str, **kwargs):
        """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
        super().__init__(name)
        self.user = kwargs.get('user')
        self.password = kwargs.get('password')
        self.database = kwargs.get('database')
        self.warehouse = kwargs.get('warehouse')
        self.account = kwargs.get('account')
        self.schema = kwargs.get('schema')

    def connect(self):
        """
        Establish connection to the database.
        Returns:
          DBHandlerStatus
        """
        try:
            self.connection = snowflake.connector.connect(user=self.user, password=self.password, database=self.database, warehouse=self.warehouse, schema=self.schema, account=self.account)
            self.connection.autocommit = True
            return DBHandlerStatus(status=True)
        except snowflake.connector.errors.Error as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        Disconnect from the database.
        """
        if self.connection:
            self.connection.close()

    def check_connection(self) -> DBHandlerStatus:
        """
        Method for checking the status of database connection.
        Returns:
          DBHandlerStatus
        """
        if self.connection:
            return DBHandlerStatus(status=True)
        else:
            return DBHandlerStatus(status=False, error='Not connected to the database.')

    def get_tables(self) -> DBHandlerResponse:
        """
        Method to get the list of tables from database.
        Returns:
          DBHandlerStatus
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f"SELECT table_name as table_name FROM information_schema.tables WHERE table_schema='{self.schema}'"
            cursor = self.connection.cursor()
            cursor.execute(query)
            tables_df = self._fetch_results_as_df(cursor)
            return DBHandlerResponse(data=tables_df)
        except snowflake.connector.errors.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def get_columns(self, table_name: str) -> DBHandlerResponse:
        """
        Method to retrieve the columns of the specified table from the database.
        Args:
          table_name (str): name of the table whose columns are to be retrieved.
        Returns:
          DBHandlerStatus
        """
        if not self.connection:
            return DBHandlerResponse(data=None, error='Not connected to the database.')
        try:
            query = f"SELECT column_name as name, data_type as dtype FROM information_schema.columns WHERE table_name='{table_name}'"
            cursor = self.connection.cursor()
            cursor.execute(query)
            columns_df = self._fetch_results_as_df(cursor)
            columns_df['dtype'] = columns_df['dtype'].apply(self._snowflake_to_python_types)
            return DBHandlerResponse(data=columns_df)
        except snowflake.connector.errors.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _fetch_results_as_df(self, cursor):
        """
        Fetch results from the cursor for the executed query and return the
        query results as dataframe.
        """
        try:
            res = cursor.fetchall()
            res_df = pd.DataFrame(res, columns=[desc[0].lower() for desc in cursor.description])
            return res_df
        except snowflake.connector.errors.ProgrammingError as e:
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
        except snowflake.connector.errors.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _snowflake_to_python_types(self, snowflake_type: str):
        mapping = {'TEXT': str, 'NUMBER': int, 'INT': int, 'DECIMAL': float, 'STRING': str, 'CHAR': str, 'BOOLEAN': bool, 'BINARY': bytes, 'DATE': datetime.date, 'TIME': datetime.time, 'TIMESTAMP': datetime.datetime}
        if snowflake_type in mapping:
            return mapping[snowflake_type]
        else:
            raise Exception(f'Unsupported column {snowflake_type} encountered in the snowflake. Please raise a feature request!')

def __init__(self, name: str, **kwargs):
    """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
    super().__init__(name)
    self.user = kwargs.get('user')
    self.password = kwargs.get('password')
    self.database = kwargs.get('database')
    self.warehouse = kwargs.get('warehouse')
    self.account = kwargs.get('account')
    self.schema = kwargs.get('schema')

class PostgresHandler(DBHandler):

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
        self.connection = None

    def connect(self) -> DBHandlerStatus:
        """
        Set up the connection required by the handler.
        Returns:
            DBHandlerStatus
        """
        try:
            self.connection = psycopg2.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database)
            self.connection.autocommit = True
            return DBHandlerStatus(status=True)
        except psycopg2.Error as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        Close any existing connections.
        """
        if self.connection:
            self.connection.close()

    def get_sqlalchmey_uri(self) -> str:
        return f'postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'

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
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')"
            tables_df = pd.read_sql_query(query, self.connection)
            return DBHandlerResponse(data=tables_df)
        except psycopg2.Error as e:
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
            query = f"SELECT column_name as name, data_type as dtype, udt_name FROM information_schema.columns WHERE table_name='{table_name}'"
            columns_df = pd.read_sql_query(query, self.connection)
            columns_df['dtype'] = columns_df.apply(lambda x: self._pg_to_python_types(x['dtype'], x['udt_name']), axis=1)
            return DBHandlerResponse(data=columns_df)
        except psycopg2.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _fetch_results_as_df(self, cursor):
        """
        This is currently the only clean solution that we have found so far.
        Reference to Postgres API: https://www.psycopg.org/docs/cursor.html#fetch

        In short, currently there is no very clean programming way to differentiate
        CREATE, INSERT, SELECT. CREATE and INSERT do not return any result, so calling
        fetchall() on those will yield a programming error. Cursor has an attribute
        rowcount, but it indicates # of rows that are affected. In that case, for both
        INSERT and SELECT rowcount is not 0, so we also cannot use this API to
        differentiate INSERT and SELECT.
        """
        try:
            res = cursor.fetchall()
            res_df = pd.DataFrame(res, columns=[desc[0].lower() for desc in cursor.description])
            return res_df
        except psycopg2.ProgrammingError as e:
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
        except psycopg2.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _pg_to_python_types(self, pg_type: str, udt_name: str):
        primitive_type_mapping = {'integer': int, 'bigint': int, 'smallint': int, 'numeric': float, 'real': float, 'double precision': float, 'character': str, 'character varying': str, 'text': str, 'boolean': bool}
        user_defined_type_mapping = {'vector': np.ndarray}
        if pg_type in primitive_type_mapping:
            return primitive_type_mapping[pg_type]
        elif pg_type == 'USER-DEFINED' and udt_name in user_defined_type_mapping:
            return user_defined_type_mapping[udt_name]
        else:
            raise Exception(f'Unsupported column {pg_type} encountered in the postgres table. Please raise a feature request!')

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
    self.connection = None

class SQLiteHandler(DBHandler):

    def __init__(self, name: str, **kwargs):
        """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
        super().__init__(name)
        self.database = kwargs.get('database')
        self.connection = None

    def connect(self):
        """
        Set up the connection required by the handler.
        Returns:
            DBHandlerStatus
        """
        try:
            self.connection = sqlite3.connect(database=self.database, isolation_level=None)
            return DBHandlerStatus(status=True)
        except sqlite3.Error as e:
            return DBHandlerStatus(status=False, error=str(e))

    def disconnect(self):
        """
        Close any existing connections.
        """
        if self.connection:
            self.connection.close()

    def get_sqlalchmey_uri(self) -> str:
        return f'sqlite:///{self.database}'

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
            query = "SELECT name AS table_name FROM sqlite_master WHERE type = 'table'"
            tables_df = pd.read_sql_query(query, self.connection)
            return DBHandlerResponse(data=tables_df)
        except sqlite3.Error as e:
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
        '\n        SQLite does not provide an in-built way to get the column names using a SELECT statement.\n        Hence we have to use the PRAGMA command and filter the required columns.\n        '
        try:
            query = f"PRAGMA table_info('{table_name}')"
            pragma_df = pd.read_sql_query(query, self.connection)
            columns_df = pragma_df[['name', 'type']].copy()
            columns_df.rename(columns={'type': 'dtype'}, inplace=True)
            columns_df['dtype'] = columns_df['dtype'].apply(self._sqlite_to_python_types)
            return DBHandlerResponse(data=columns_df)
        except sqlite3.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _fetch_results_as_df(self, cursor):
        try:
            res = cursor.fetchall()
            res_df = pd.DataFrame(res, columns=[desc[0].lower() for desc in cursor.description] if cursor.description else [])
            return res_df
        except sqlite3.ProgrammingError as e:
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
        except sqlite3.Error as e:
            return DBHandlerResponse(data=None, error=str(e))

    def _sqlite_to_python_types(self, sqlite_type: str):
        mapping = {'INT': int, 'INTEGER': int, 'TINYINT': int, 'SMALLINT': int, 'MEDIUMINT': int, 'BIGINT': int, 'UNSIGNED BIG INT': int, 'INT2': int, 'INT8': int, 'CHARACTER': str, 'VARCHAR': str, 'VARYING CHARACTER': str, 'NCHAR': str, 'NATIVE CHARACTER': str, 'NVARCHAR': str, 'TEXT': str, 'CLOB': str, 'BLOB': bytes, 'REAL': float, 'DOUBLE': float, 'DOUBLE PRECISION': float, 'FLOAT': float, 'NUMERIC': float, 'DECIMAL': float, 'BOOLEAN': bool, 'DATE': datetime.date, 'DATETIME': datetime.datetime}
        sqlite_type = sqlite_type.split('(')[0].strip().upper()
        if sqlite_type in mapping:
            return mapping[sqlite_type]
        else:
            raise Exception(f'Unsupported column {sqlite_type} encountered in the sqlite table. Please raise a feature request!')

def __init__(self, name: str, **kwargs):
    """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
    super().__init__(name)
    self.database = kwargs.get('database')
    self.connection = None

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

class HackernewsSearchHandler(DBHandler):

    def connection():
        return requests.get('https://www.google.com/').status_code == 200

    def __init__(self, name: str, **kwargs):
        """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
        super().__init__(name)
        self.query = kwargs.get('query', '')
        self.tags = kwargs.get('tags', '')

    @property
    def supported_table(self):

        def _hackernews_topics_generator():
            url = 'http://hn.algolia.com/api/v1/search?'
            url += 'query=' + self.query
            url += '&tags=' + ('story' if self.tags == '' else +self.tags)
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception('Could not reach website.')
            json_result = response.content
            dict_result = json.loads(json_result)
            for row in dict_result:
                yield {property_name: row[property_name] for property_name, _ in HACKERNEWS_COLUMNS}
        mapping = {'search_results': {'columns': HACKERNEWS_COLUMNS, 'generator': _hackernews_topics_generator()}}
        return mapping

    def connect(self):
        """
        Set up the connection required by the handler.
        Returns:
            DBHandlerStatus
        """
        return DBHandlerStatus(status=True)

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
        if self.connection():
            return DBHandlerStatus(status=True)
        else:
            return DBHandlerStatus(status=False, error='Not connected to the internet.')

    def get_tables(self) -> DBHandlerResponse:
        """
        Return the list of tables in the database.
        Returns:
            DBHandlerResponse
        """
        if not self.connection():
            return DBHandlerResponse(data=None, error='Not connected to the internet.')
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
        if not self.connection():
            return DBHandlerResponse(data=None, error='Not connected to the internet.')
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

def connection():
    return requests.get('https://www.google.com/').status_code == 200

def __init__(self, name: str, **kwargs):
    """
        Initialize the handler.
        Args:
            name (str): name of the DB handler instance
            **kwargs: arbitrary keyword arguments for establishing the connection.
        """
    super().__init__(name)
    self.query = kwargs.get('query', '')
    self.tags = kwargs.get('tags', '')

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

class CSVReader(AbstractReader):

    def __init__(self, *args, column_list, **kwargs):
        """
        Reads a CSV file and yields frame data.
        Args:
            column_list: list of columns (TupleValueExpression)
            to read from the CSV file
        """
        self._column_list = column_list
        super().__init__(*args, **kwargs)

    def _read(self) -> Iterator[Dict]:

        def convert_csv_string_to_ndarray(row_string):
            """
            Convert a string of comma separated values to a numpy
            float array
            """
            return np.array([np.float32(val) for val in row_string.split(',')])
        logger.info('Reading CSV frames')
        col_list_names = [col.name for col in self._column_list if col.name != IDENTIFIER_COLUMN]
        col_map = {col.name: col for col in self._column_list}
        for chunk in pd.read_csv(self.file_url, chunksize=512, usecols=col_list_names):
            for col in chunk.columns:
                if isinstance(chunk[col].iloc[0], str) and col_map[col].col_object.type.name == 'NDARRAY':
                    chunk[col] = chunk[col].apply(convert_csv_string_to_ndarray)
            for chunk_index, chunk_row in chunk.iterrows():
                yield chunk_row

def __init__(self, *args, column_list, **kwargs):
    """
        Reads a CSV file and yields frame data.
        Args:
            column_list: list of columns (TupleValueExpression)
            to read from the CSV file
        """
    self._column_list = column_list
    super().__init__(*args, **kwargs)

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

class PDFReader(AbstractReader):

    def __init__(self, *args, **kwargs):
        """
        Reads a PDF file and yields frame data.
        Args:
            column_list: list of columns (TupleValueExpression)
            to read from the PDF file
        """
        super().__init__(*args, **kwargs)
        try_to_import_fitz()

    def _read(self) -> Iterator[Dict]:
        import fitz
        doc = fitz.open(self.file_url)
        row_num = 0
        for page_no, page in enumerate(doc):
            blocks = page.get_text('dict')['blocks']
            for paragraph_no, b in enumerate(blocks):
                if b['type'] == 0:
                    block_string = ''
                    for lines in b['lines']:
                        for span in lines['spans']:
                            if span['text'].strip():
                                block_string += span['text']
                    yield {ROW_NUM_COLUMN: row_num, 'page': page_no + 1, 'paragraph': paragraph_no + 1, 'data': block_string}
                    row_num += 1

def __init__(self, *args, **kwargs):
    """
        Reads a PDF file and yields frame data.
        Args:
            column_list: list of columns (TupleValueExpression)
            to read from the PDF file
        """
    super().__init__(*args, **kwargs)
    try_to_import_fitz()

class CVImageReader(AbstractReader):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _read(self) -> Iterator[Dict]:
        try_to_import_cv2()
        import cv2
        im_bgr = cv2.imread(str(self.file_url))
        im_rgb = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2RGB)
        assert im_rgb is not None, f'Failed to read image file {self.file_url}'
        yield {'data': im_rgb}

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class DocumentReader(AbstractReader):

    def __init__(self, *args, chunk_params, **kwargs):
        super().__init__(*args, **kwargs)
        self._LOADER_MAPPING = _lazy_import_loader()
        self._splitter_class = _lazy_import_text_splitter()
        self._chunk_size = chunk_params.get('chunk_size', DEFAULT_DOCUMENT_CHUNK_SIZE)
        self._chunk_overlap = chunk_params.get('chunk_overlap', DEFAULT_DOCUMENT_CHUNK_OVERLAP)

    def _read(self) -> Iterator[Dict]:
        ext = Path(self.file_url).suffix
        assert ext in self._LOADER_MAPPING, f'File Format {ext} not supported'
        loader_class, loader_args = self._LOADER_MAPPING[ext]
        loader = loader_class(self.file_url, **loader_args)
        langchain_text_splitter = self._splitter_class(chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap)
        row_num = 0
        for data in loader.load():
            for chunk_id, row in enumerate(langchain_text_splitter.split_documents([data])):
                yield {'chunk_id': chunk_id, 'data': row.page_content, ROW_NUM_COLUMN: row_num}
                row_num += 1

def __init__(self, *args, chunk_params, **kwargs):
    super().__init__(*args, **kwargs)
    self._LOADER_MAPPING = _lazy_import_loader()
    self._splitter_class = _lazy_import_text_splitter()
    self._chunk_size = chunk_params.get('chunk_size', DEFAULT_DOCUMENT_CHUNK_SIZE)
    self._chunk_overlap = chunk_params.get('chunk_overlap', DEFAULT_DOCUMENT_CHUNK_OVERLAP)

class VGG(torch.nn.Module):

    def __init__(self, vgg_name):
        super(VGG, self).__init__()
        self.features = self._make_layers(cfg[vgg_name])
        self.classifier = torch.nn.Linear(512, 7)

    def forward(self, x):
        out = self.features(x)
        out = out.view(out.size(0), -1)
        out = F.dropout(out, p=0.5, training=self.training)
        out = self.classifier(out)
        return out

    def _make_layers(self, cfg):
        layers = []
        in_channels = 3
        for x in cfg:
            if x == 'M':
                layers += [torch.nn.MaxPool2d(kernel_size=2, stride=2)]
            else:
                layers += [torch.nn.Conv2d(in_channels, x, kernel_size=3, padding=1), torch.nn.BatchNorm2d(x), torch.nn.ReLU(inplace=True)]
                in_channels = x
        layers += [torch.nn.AvgPool2d(kernel_size=1, stride=1)]
        return torch.nn.Sequential(*layers)

def __init__(self, vgg_name):
    super(VGG, self).__init__()
    self.features = self._make_layers(cfg[vgg_name])
    self.classifier = torch.nn.Linear(512, 7)

class NumpyArray(IOColumnArgument):
    """Descriptor data type for Numpy Array"""

    def __init__(self, name: str, is_nullable: bool=False, type: NdArrayType=None, dimensions: Tuple[int]=None) -> None:
        super().__init__(name=name, type=ColumnType.NDARRAY, is_nullable=is_nullable, array_type=type, array_dimensions=dimensions)

def __init__(self, name: str, is_nullable: bool=False, type: NdArrayType=None, dimensions: Tuple[int]=None) -> None:
    super().__init__(name=name, type=ColumnType.NDARRAY, is_nullable=is_nullable, array_type=type, array_dimensions=dimensions)

class PyTorchTensor(IOColumnArgument):
    """Descriptor data type for PyTorch Tensor"""

    def __init__(self, name: str, is_nullable: bool=False, type: NdArrayType=None, dimensions: Tuple[int]=None) -> None:
        super().__init__(name=name, type=ColumnType.NDARRAY, is_nullable=is_nullable, array_type=type, array_dimensions=dimensions)

def __init__(self, name: str, is_nullable: bool=False, type: NdArrayType=None, dimensions: Tuple[int]=None) -> None:
    super().__init__(name=name, type=ColumnType.NDARRAY, is_nullable=is_nullable, array_type=type, array_dimensions=dimensions)

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

def __init__(self, columns, column_types=[], column_shapes=[]) -> None:
    super().__init__()
    self.columns = columns
    self.column_types = column_types
    self.column_shapes = column_shapes

class EvaDBTrackerAbstractFunction(AbstractFunction):
    """
    An abstract class for all EvaDB object trackers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @setup(cacheable=False, function_type='object_tracker', batchable=False)
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)

    @forward(input_signatures=[PandasDataframe(columns=['frame_id', 'frame', 'bboxes', 'scores', 'labels'], column_types=[NdArrayType.INT32, NdArrayType.FLOAT32, NdArrayType.FLOAT32, NdArrayType.FLOAT32, NdArrayType.STR], column_shapes=[(1,), (None, None, 3), (None, 4), (None,), (None,)])], output_signatures=[PandasDataframe(columns=['track_ids', 'track_labels', 'track_bboxes', 'track_scores'], column_types=[NdArrayType.INT32, NdArrayType.INT32, NdArrayType.FLOAT32, NdArrayType.FLOAT32], column_shapes=[(None,), (None,), (None, 4), (None,)])])
    def forward(self, frame_id: numpy.ndarray, frame: numpy.ndarray, labels: numpy.ndarray, bboxes: numpy.ndarray, scores: numpy.ndarray) -> typing.Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
        """
        Args:
            frame_id (numpy.ndarray): the frame id of current frame
            frame (numpy.ndarray): the input frame with shape (C, H, W)
            labels (numpy.ndarray): Corresponding labels for each box
            bboxes (numpy.ndarray): Array of shape `(n, 4)` or of shape `(4,)` where
            each row contains `(xmin, ymin, width, height)`.
            scores (numpy.ndarray): Corresponding scores for each box
        Returns:
            track_ids (numpy.ndarray): Corresponding track id for each box
            track_labels (numpy.ndarray): Corresponding labels for each box
            track_bboxes (numpy.ndarray):  Array of shape `(n, 4)` of tracked objects
            track_scores (numpy.ndarray): Corresponding scores for each box
        """
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        assert isinstance(args[0], pd.DataFrame), f'Expecting pd.DataFrame, got {type(args[0])}'
        results = []
        for _, row in args[0].iterrows():
            tuple = (numpy.array(row[0]), numpy.array(row[1]), numpy.stack(row[2]), numpy.stack(row[3]), numpy.stack(row[4]))
            results.append(self.forward(*tuple))
        return pd.DataFrame(results, columns=['track_ids', 'track_labels', 'track_bboxes', 'track_scores'])

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, transforms):
    Compose.__init__(self, transforms)

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

def reassign_indices_to_hash(self, indices) -> None:
    """
        Hash indices and replace the indices with those hash values.
        """
    self._frames.index = self._frames[indices].apply(lambda x: hash(tuple(x)), axis=1)

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

def __init__(self, db: EvaDBDatabase):
    """
        Grab the existing sql session
        """
    super().__init__(db)
    self._sql_session = db.catalog().sql_config.session
    self._sql_engine = db.catalog().sql_config.engine
    self._serializer = PickleSerializer

class ImageStorageEngine(AbstractMediaStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        super().__init__(db)

    def read(self, table: TableCatalogEntry) -> Iterator[Batch]:
        for image_files in self._rdb_handler.read(self._get_metadata_table(table)):
            for _, (row_id, file_name, _) in image_files.iterrows():
                system_file_name = self._xform_file_url_to_file_name(file_name)
                image_file = Path(table.file_url) / system_file_name
                reader = CVImageReader(str(image_file), batch_mem_size=1)
                for batch in reader.read():
                    batch.frames[table.columns[0].name] = row_id
                    batch.frames[table.columns[1].name] = str(file_name)
                    batch.frames[ROW_NUM_COLUMN] = batch.frames[table.columns[0].name]
                    yield batch

def __init__(self, db: EvaDBDatabase):
    super().__init__(db)

class DocumentStorageEngine(AbstractMediaStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        super().__init__(db)

    def read(self, table: TableCatalogEntry, chunk_params: dict) -> Iterator[Batch]:
        for doc_files in self._rdb_handler.read(self._get_metadata_table(table), 12):
            for _, (row_id, file_name, _) in doc_files.iterrows():
                system_file_name = self._xform_file_url_to_file_name(file_name)
                doc_file = Path(table.file_url) / system_file_name
                reader = DocumentReader(str(doc_file), batch_mem_size=1, chunk_params=chunk_params)
                for batch in reader.read():
                    batch.frames[table.columns[0].name] = row_id
                    batch.frames[table.columns[1].name] = str(file_name)
                    batch.frames[ROW_NUM_COLUMN] = row_id * ROW_NUM_MAGIC + batch.frames[ROW_NUM_COLUMN]
                    yield batch

def __init__(self, db: EvaDBDatabase):
    super().__init__(db)

class AbstractMediaStorageEngine(AbstractStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        super().__init__(db)
        self._rdb_handler: SQLStorageEngine = SQLStorageEngine(db)

    def _get_metadata_table(self, table: TableCatalogEntry):
        return self.db.catalog().get_multimedia_metadata_table_catalog_entry(table)

    def _create_metadata_table(self, table: TableCatalogEntry):
        return self.db.catalog().create_and_insert_multimedia_metadata_table_catalog_entry(table)

    def _xform_file_url_to_file_name(self, file_url: Path) -> str:
        file_path_str = str(file_url)
        file_path = re.sub('[^a-zA-Z0-9 \\.\\n]', '_', file_path_str)
        return file_path

    def create(self, table: TableCatalogEntry, if_not_exists=True):
        """
        Create the directory to store the images.
        Create a sqlite table to persist the file urls
        """
        dir_path = Path(table.file_url)
        try:
            dir_path.mkdir(parents=True)
        except FileExistsError:
            if if_not_exists:
                return True
            error = 'Failed to load the image as directory                         already exists: {}'.format(dir_path)
            logger.error(error)
            raise FileExistsError(error)
        self._rdb_handler.create(self._create_metadata_table(table))
        return True

    def drop(self, table: TableCatalogEntry):
        try:
            dir_path = Path(table.file_url)
            shutil.rmtree(str(dir_path))
            metadata_table = self._get_metadata_table(table)
            self._rdb_handler.drop(metadata_table)
            self.db.catalog().delete_table_catalog_entry(metadata_table)
        except Exception as e:
            err_msg = f'Failed to drop the image table {e}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def delete(self, table: TableCatalogEntry, rows: Batch):
        try:
            media_metadata_table = self._get_metadata_table(table)
            for media_file_path in rows.file_paths():
                dst_file_name = self._xform_file_url_to_file_name(Path(media_file_path))
                image_file = Path(table.file_url) / dst_file_name
                self._rdb_handler.delete(media_metadata_table, where_clause={media_metadata_table.identifier_column: str(media_file_path)})
                image_file.unlink()
        except Exception as e:
            error = f'Deleting file path {media_file_path} failed with exception {e}'
            logger.exception(error)
            raise RuntimeError(error)
        return True

    def write(self, table: TableCatalogEntry, rows: Batch):
        try:
            dir_path = Path(table.file_url)
            copied_files = []
            for media_file_path in rows.file_paths():
                media_file = Path(media_file_path)
                dst_file_name = self._xform_file_url_to_file_name(media_file)
                dst_path = dir_path / dst_file_name
                if dst_path.exists():
                    raise FileExistsError(f'Duplicate File: {media_file} already exists in the table {table.name}')
                src_path = Path.cwd() / media_file
                os.symlink(src_path, dst_path)
                copied_files.append(dst_path)
            self._rdb_handler.write(self._get_metadata_table(table), Batch(pd.DataFrame({'file_url': list(rows.file_paths())})))
        except Exception as e:
            for file in copied_files:
                logger.info(f'Rollback file {file}')
                file.unlink()
            logger.exception(str(e))
            raise RuntimeError(str(e))
        else:
            return True

    def rename(self, old_table: TableCatalogEntry, new_name: TableInfo):
        try:
            self.db.catalog().rename_table_catalog_entry(old_table, new_name)
        except Exception as e:
            raise Exception(f'Failed to rename table {new_name} with exception {e}')

def __init__(self, db: EvaDBDatabase):
    super().__init__(db)
    self._rdb_handler: SQLStorageEngine = SQLStorageEngine(db)

class PDFStorageEngine(AbstractMediaStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        super().__init__(db)

    def read(self, table: TableCatalogEntry) -> Iterator[Batch]:
        for image_files in self._rdb_handler.read(self._get_metadata_table(table), 12):
            for _, (row_id, file_name, _) in image_files.iterrows():
                system_file_name = self._xform_file_url_to_file_name(file_name)
                image_file = Path(table.file_url) / system_file_name
                reader = PDFReader(str(image_file), batch_mem_size=1)
                for batch in reader.read():
                    batch.frames[table.columns[0].name] = row_id
                    batch.frames[table.columns[1].name] = str(file_name)
                    batch.frames[ROW_NUM_COLUMN] = row_id * ROW_NUM_MAGIC + batch.frames[ROW_NUM_COLUMN]
                    yield batch

def __init__(self, db: EvaDBDatabase):
    super().__init__(db)

class DecordStorageEngine(AbstractMediaStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        super().__init__(db)

    def read(self, table: TableCatalogEntry, batch_mem_size: int, predicate: AbstractExpression=None, sampling_rate: int=None, sampling_type: str=None, read_audio: bool=False, read_video: bool=True) -> Iterator[Batch]:
        for video_files in self._rdb_handler.read(self._get_metadata_table(table), 12):
            for _, (row_id, video_file_name, _) in video_files.iterrows():
                system_file_name = self._xform_file_url_to_file_name(video_file_name)
                video_file = Path(table.file_url) / system_file_name
                if read_audio:
                    batch_mem_size = sys.maxsize
                reader = DecordReader(str(video_file), batch_mem_size=batch_mem_size, predicate=predicate, sampling_rate=sampling_rate, sampling_type=sampling_type, read_audio=read_audio, read_video=read_video)
                for batch in reader.read():
                    batch.frames[table.columns[0].name] = row_id
                    batch.frames[table.columns[1].name] = str(video_file_name)
                    batch.frames[ROW_NUM_COLUMN] = row_id * ROW_NUM_MAGIC + batch.frames[ROW_NUM_COLUMN]
                    yield batch

def __init__(self, db: EvaDBDatabase):
    super().__init__(db)

class NativeStorageEngine(AbstractStorageEngine):

    def __init__(self, db: EvaDBDatabase):
        super().__init__(db)

    def _get_database_catalog_entry(self, database_name):
        db_catalog_entry = self.db.catalog().get_database_catalog_entry(database_name)
        if db_catalog_entry is None:
            raise Exception(f'Could not find database with name {database_name}. Please register the database using the `CREATE DATABASE` command.')
        return db_catalog_entry

    def create(self, table: TableCatalogEntry):
        try:
            db_catalog_entry = self._get_database_catalog_entry(table.database_name)
            uri = None
            with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
                uri = handler.get_sqlalchmey_uri()
            sqlalchemy_schema = SchemaUtils.xform_to_sqlalchemy_schema(table.columns)
            create_table(uri, table.name, sqlalchemy_schema)
        except Exception as e:
            err_msg = f'Failed to create the table {table.name} in data source {table.database_name} with exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def write(self, table: TableCatalogEntry, rows: Batch):
        try:
            db_catalog_entry = self._get_database_catalog_entry(table.database_name)
            with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
                uri = handler.get_sqlalchmey_uri()
            engine = create_engine(uri)
            metadata = MetaData()
            table_to_update = Table(table.name, metadata, autoload_with=engine)
            columns = rows.frames.keys()
            data = []
            for record in rows.frames.values:
                row_data = {col: record[idx] for idx, col in enumerate(columns)}
                data.append(_dict_to_sql_row(row_data, table.columns))
            Session = sessionmaker(bind=engine)
            session = Session()
            session.execute(table_to_update.insert(), data)
            session.commit()
            session.close()
        except Exception as e:
            err_msg = f'Failed to write to the table {table.name} in data source {table.database_name} with exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def read(self, table: TableCatalogEntry, batch_mem_size: int=30000000) -> Iterator[Batch]:
        try:
            db_catalog_entry = self._get_database_catalog_entry(table.database_name)
            with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
                handler_response = handler.select(table.name)
                result = []
                if handler_response.data_generator:
                    result = handler_response.data_generator
                elif handler_response.data:
                    result = handler_response.data
                if handler.is_sqlalchmey_compatible():
                    cols = result[0]._fields
                    index_dict = {element.lower(): index for index, element in enumerate(cols)}
                    try:
                        ordered_columns = sorted(table.columns, key=lambda x: index_dict[x.name.lower()])
                    except KeyError as e:
                        raise Exception(f'Column mismatch with error {e}')
                    result = (_deserialize_sql_row(row, ordered_columns) for row in result)
                for df in rebatch(result, batch_mem_size):
                    yield Batch(pd.DataFrame(df))
        except Exception as e:
            err_msg = f'Failed to read the table {table.name} in data source {table.database_name} with exception {str(e)}'
            logger.exception(err_msg)
            raise Exception(err_msg)

    def drop(self, table: TableCatalogEntry):
        try:
            db_catalog_entry = self._get_database_catalog_entry(table.database_name)
            with get_database_handler(db_catalog_entry.engine, **db_catalog_entry.params) as handler:
                uri = handler.get_sqlalchmey_uri()
            engine = create_engine(uri)
            metadata = MetaData()
            Session = sessionmaker(bind=engine)
            session = Session()
            table_to_remove = Table(table.name, metadata, autoload_with=engine)
            table_to_remove.drop(engine)
            session.commit()
            session.close()
        except Exception as e:
            err_msg = f'Failed to drop the table {table.name} in data source {table.database_name} with exception {str(e)}'
            logger.error(err_msg)
            raise Exception(err_msg)

def __init__(self, db: EvaDBDatabase):
    super().__init__(db)

def download_file_from_google_drive(file_name, destination):
    """
    Downloads a zip file from google drive. Assumes the file has open access. 
    Args:
        file_name: name of the file to download
        destination: path to save the file to
    """
    URL = 'https://drive.google.com/uc?export=download'
    id = file_id_map[file_name]
    session = requests.Session()
    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)
    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    save_response_content(response, destination)

def get_commit_id_of_latest_release():
    import requests
    repo = 'georgia-tech-db/evadb'
    url = f'https://api.github.com/repos/{repo}/releases'
    response = requests.get(url)
    data = response.json()
    latest_release = data[0]
    release_date = latest_release['created_at']
    return release_date

