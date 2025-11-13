# Cluster 6

def suffix_pytest_xdist_worker_id_to_dir(path: str):
    try:
        worker_id = os.environ['PYTEST_XDIST_WORKER']
        path = Path(str(worker_id) + '_' + path)
    except KeyError:
        pass
    return Path(path)

def custom_list_of_dicts_equal(one, two):
    for v1, v2 in zip(one, two):
        if v1.keys() != v2.keys():
            return False
        for key in v1.keys():
            if isinstance(v1[key], np.ndarray):
                if not np.array_equal(v1[key], v2[key]):
                    return False
            elif v1[key] != v2[key]:
                return False
    return True

@pytest.mark.notparallel
class TextFilteringTests(unittest.TestCase):

    def setUp(self):
        self.db_dir = suffix_pytest_xdist_worker_id_to_dir(EvaDB_DATABASE_DIR)
        self.conn = connect(self.db_dir)
        self.evadb = self.conn._evadb
        self.evadb.catalog().reset()

    def tearDown(self):
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDFs;')

    def test_text_filter(self):
        pdf_path = f'{EvaDB_ROOT_DIR}/data/documents/layout-parser-paper.pdf'
        cursor = self.conn.cursor()
        cursor.load(pdf_path, 'MyPDFs', 'pdf').df()
        load_pdf_data = cursor.table('MyPDFs').df()
        cursor.create_function('TextFilterKeyword', True, f'{EvaDB_ROOT_DIR}/evadb/functions/text_filter_keyword.py').df()
        filtered_data = cursor.table('MyPDFs').cross_apply("TextFilterKeyword(data, ['References'])", 'objs(filtered)').df()
        filtered_data.dropna(inplace=True)
        import pandas as pd
        pd.set_option('display.max_colwidth', None)
        self.assertNotEqual(len(filtered_data), len(load_pdf_data))

def test_text_filter(self):
    pdf_path = f'{EvaDB_ROOT_DIR}/data/documents/layout-parser-paper.pdf'
    cursor = self.conn.cursor()
    cursor.load(pdf_path, 'MyPDFs', 'pdf').df()
    load_pdf_data = cursor.table('MyPDFs').df()
    cursor.create_function('TextFilterKeyword', True, f'{EvaDB_ROOT_DIR}/evadb/functions/text_filter_keyword.py').df()
    filtered_data = cursor.table('MyPDFs').cross_apply("TextFilterKeyword(data, ['References'])", 'objs(filtered)').df()
    filtered_data.dropna(inplace=True)
    import pandas as pd
    pd.set_option('display.max_colwidth', None)
    self.assertNotEqual(len(filtered_data), len(load_pdf_data))

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

def assertBatchEqual(self, a: Batch, b: Batch, msg: str):
    try:
        pd_testing.assert_frame_equal(a.frames, b.frames)
    except AssertionError as e:
        raise self.failureException(msg) from e

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

@pytest.mark.notparallel
class ShowExecutorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        queries = [Fastrcnn_function_query, ArrayCount_function_query]
        for query in queries:
            execute_query_fetch_all(cls.evadb, query)
        ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
        mnist = f'{EvaDB_ROOT_DIR}/data/mnist/mnist.mp4'
        actions = f'{EvaDB_ROOT_DIR}/data/actions/actions.mp4'
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO MyVideo;")
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{mnist}' INTO MNIST;")
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{actions}' INTO Actions;")
        import os
        cls.current_file_dir = os.path.dirname(os.path.abspath(__file__))
        for i in range(NUM_DATABASES):
            database_path = f'{cls.current_file_dir}/testing_{i}.db'
            params = {'database': database_path}
            query = 'CREATE DATABASE test_data_source_{}\n                        WITH ENGINE = "sqlite",\n                        PARAMETERS = {};'.format(i, params)
            execute_query_fetch_all(cls.evadb, query)

    @classmethod
    def tearDownClass(cls):
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS Actions;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MNIST;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')
        for i in range(NUM_DATABASES):
            execute_query_fetch_all(cls.evadb, f'DROP DATABASE IF EXISTS test_data_source_{i};')
            database_path = f'{cls.current_file_dir}/testing_{i}.db'
            import contextlib
            with contextlib.suppress(FileNotFoundError):
                os.remove(database_path)

    def test_show_functions(self):
        result = execute_query_fetch_all(self.evadb, 'SHOW FUNCTIONS;')
        self.assertEqual(len(result.columns), 6)
        expected = {'name': ['FastRCNNObjectDetector', 'ArrayCount'], 'type': ['Classification', 'NdarrayFunction']}
        expected_df = pd.DataFrame(expected)
        self.assertTrue(all(expected_df.name == result.frames.name))
        self.assertTrue(all(expected_df.type == result.frames.type))

    @windows_skip_marker
    def test_show_tables(self):
        result = execute_query_fetch_all(self.evadb, 'SHOW TABLES;')
        self.assertEqual(len(result), 3)
        expected = {'name': ['MyVideo', 'MNIST', 'Actions']}
        expected_df = pd.DataFrame(expected)
        self.assertEqual(result, Batch(expected_df))
        os.system('nohup evadb_server --stop')
        os.system('nohup evadb_server --start &')
        result = execute_query_fetch_all(self.evadb, 'SHOW TABLES;')
        self.assertEqual(len(result), 3)
        expected = {'name': ['MyVideo', 'MNIST', 'Actions']}
        expected_df = pd.DataFrame(expected)
        self.assertEqual(result, Batch(expected_df))
        os.system('nohup evadb_server --stop')

    def test_show_config_execution(self):
        execute_query_fetch_all(self.evadb, "SET OPENAIKEY = 'ABCD';")
        expected_output = Batch(pd.DataFrame({'OPENAIKEY': ['ABCD']}))
        show_config_value = execute_query_fetch_all(self.evadb, 'SHOW OPENAIKEY')
        self.assertEqual(show_config_value, expected_output)
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, 'SHOW BADCONFIG')

    def test_show_all_configs(self):
        show_all_config_value = execute_query_fetch_all(self.evadb, 'SHOW CONFIGS')
        columns = show_all_config_value.columns
        self.assertEqual(columns == list(BASE_EVADB_CONFIG.keys()), True)

    def test_show_databases(self):
        result = execute_query_fetch_all(self.evadb, 'SHOW DATABASES;')
        self.assertEqual(len(result.columns), 3)
        self.assertEqual(len(result), 6)
        expected = {'name': [f'test_data_source_{i}' for i in range(NUM_DATABASES)], 'engine': ['sqlite' for _ in range(NUM_DATABASES)]}
        expected_df = pd.DataFrame(expected)
        self.assertTrue(all(expected_df.name == result.frames.name))
        self.assertTrue(all(expected_df.engine == result.frames.engine))

def test_show_all_configs(self):
    show_all_config_value = execute_query_fetch_all(self.evadb, 'SHOW CONFIGS')
    columns = show_all_config_value.columns
    self.assertEqual(columns == list(BASE_EVADB_CONFIG.keys()), True)

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

def test_write(self):
    batch = MagicMock()
    batch.frames = []
    table = MagicMock()
    table.file_url = Exception()
    with self.assertRaises(Exception):
        self.video_engine.write(table, batch)

class EvaServer:
    """
    Receives messages and offloads them to another task for processing them.
    """

    def __init__(self):
        self._server = None
        self._clients = {}
        self._evadb = None

    async def start_evadb_server(self, db_dir: str, host: string, port: int, custom_db_uri: str=None):
        """
        Start the server
        Server objects are asynchronous context managers.

        hostname: hostname of the server
        port: port of the server
        """
        from pprint import pprint
        pprint(f'EvaDB server started at host {host} and port {port}')
        self._evadb = init_evadb_instance(db_dir, host, port, custom_db_uri)
        self._server = await asyncio.start_server(self.accept_client, host, port)
        mode = self._evadb.catalog().get_configuration_catalog_value('mode')
        init_builtin_functions(self._evadb, mode=mode)
        async with self._server:
            await self._server.serve_forever()
        logger.warn('EvaDB server stopped')

    async def stop_evadb_server(self):
        logger.warn('EvaDB server stopped')
        if self._server is not None:
            await self._server.close()

    async def accept_client(self, client_reader: StreamReader, client_writer: StreamWriter):
        task = asyncio.Task(self.handle_client(client_reader, client_writer))
        self._clients[task] = (client_reader, client_writer)

        def close_client(task):
            del self._clients[task]
            client_writer.close()
            logger.info('End connection')
        logger.info('New client connection')
        task.add_done_callback(close_client)

    async def handle_client(self, client_reader: StreamReader, client_writer: StreamWriter):
        try:
            while True:
                data = await asyncio.wait_for(client_reader.readline(), timeout=None)
                if data == b'':
                    break
                message = data.decode().rstrip()
                logger.debug('Received --|%s|--', message)
                if message.upper() in ['EXIT;', 'QUIT;']:
                    logger.info('Close client')
                    return
                logger.debug('Handle request')
                from evadb.server.command_handler import handle_request
                asyncio.create_task(handle_request(self._evadb, client_writer, message))
        except Exception as e:
            logger.critical('Error reading from client.', exc_info=e)

def close_client(task):
    del self._clients[task]
    client_writer.close()
    logger.info('End connection')

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

def get_group_by_id(self, group_id: int) -> GroupExpression:
    if group_id in self._groups.keys():
        return self._groups[group_id]
    else:
        logger.error('Missing group id')

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

def _exec(self, node: AbstractPlan, depth: int):
    cur_str = ' ' * depth * 4 + '|__ ' + str(node.__class__.__name__) + '\n'
    for child in node.children:
        cur_str += self._exec(child, depth + 1)
    return cur_str

def parse_s3_uri(s3_uri):
    """
    Parses the S3 URI and returns the bucket name and key
    """
    s3_uri = s3_uri.replace('s3:/', '')
    bucket_name, key = s3_uri.split('/', 1)
    return (bucket_name, key)

class Timer:
    """Class used for logging time metrics.

    This is not thread safe"""

    def __init__(self):
        self._start_time = None
        self._total_time = 0.0

    def __enter__(self):
        assert self._start_time is None, 'Concurrent calls are not supported'
        self._start_time = time.perf_counter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._start_time is not None, 'exit called with starting the context'
        time_elapsed = time.perf_counter() - self._start_time
        self._total_time += time_elapsed
        self._start_time = None

    @property
    def total_elapsed_time(self):
        return self._total_time

    def log_elapsed_time(self, context: str):
        logger.info('{:s}: {:0.4f} sec'.format(context, self.total_elapsed_time))

def __enter__(self):
    assert self._start_time is None, 'Concurrent calls are not supported'
    self._start_time = time.perf_counter()

def __exit__(self, exc_type, exc_val, exc_tb):
    assert self._start_time is not None, 'exit called with starting the context'
    time_elapsed = time.perf_counter() - self._start_time
    self._total_time += time_elapsed
    self._start_time = None

def parse_config_yml():
    """
    Parses the 'evadb.yml' file and returns the config object.
    """
    import yaml
    f = open(Path(EvaDB_INSTALLATION_DIR) / 'evadb.yml', 'r+')
    config_obj = yaml.load(f, Loader=yaml.FullLoader)
    f.close()
    return config_obj

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

def signature(self) -> str:
    return str(self)

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

def __str__(self) -> str:
    args = [str(child) for child in self.children]
    expr_str = f'{self.name}({','.join(args)})'
    return expr_str

class SQLConfig(metaclass=SingletonMeta):

    def __init__(self, uri):
        """Initializes the engine and session for database operations"""
        self.worker_uri = str(uri)
        connect_args = {'timeout': 1000}
        self.engine = create_engine(self.worker_uri, connect_args=connect_args)
        if self.engine.url.get_backend_name() == 'sqlite':

            def _enable_sqlite_pragma(dbapi_con, con_record):
                dbapi_con.execute('pragma foreign_keys=ON')
                dbapi_con.execute('pragma synchronous=NORMAL')
            event.listen(self.engine, 'connect', _enable_sqlite_pragma)
        self.session = scoped_session(sessionmaker(bind=self.engine))
        self.session.close()

def __init__(self, uri):
    """Initializes the engine and session for database operations"""
    self.worker_uri = str(uri)
    connect_args = {'timeout': 1000}
    self.engine = create_engine(self.worker_uri, connect_args=connect_args)
    if self.engine.url.get_backend_name() == 'sqlite':

        def _enable_sqlite_pragma(dbapi_con, con_record):
            dbapi_con.execute('pragma foreign_keys=ON')
            dbapi_con.execute('pragma synchronous=NORMAL')
        event.listen(self.engine, 'connect', _enable_sqlite_pragma)
    self.session = scoped_session(sessionmaker(bind=self.engine))
    self.session.close()

def _enable_sqlite_pragma(dbapi_con, con_record):
    dbapi_con.execute('pragma foreign_keys=ON')
    dbapi_con.execute('pragma synchronous=NORMAL')

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

def insert_database_catalog_entry(self, name: str, engine: str, params: dict):
    """A new entry is persisted in the database catalog."

        Args:
            name: database name
            engine: engine name
            params: required params as a dictionary for the database
        """
    self._db_catalog_service.insert_entry(name, engine, params)

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

def insert_index_catalog_entry(self, name: str, save_file_path: str, vector_store_type: VectorStoreType, feat_column: ColumnCatalogEntry, function_signature: str, index_def: str) -> IndexCatalogEntry:
    index_catalog_entry = self._index_service.insert_entry(name, save_file_path, vector_store_type, feat_column, function_signature, index_def)
    return index_catalog_entry

class SchemaUtils(object):

    @staticmethod
    def xform_to_sqlalchemy_column(df_column: ColumnCatalogEntry) -> Column:
        column_type = df_column.type
        sqlalchemy_column = None
        if column_type == ColumnType.INTEGER:
            sqlalchemy_column = Column(Integer)
        elif column_type == ColumnType.FLOAT:
            sqlalchemy_column = Column(Float)
        elif column_type == ColumnType.TEXT:
            sqlalchemy_column = Column(TEXT)
        elif column_type == ColumnType.NDARRAY:
            sqlalchemy_column = Column(LargeBinary)
        else:
            msg = 'Invalid column type: ' + str(column_type)
            logger.error(msg)
            raise NotImplementedError
        return sqlalchemy_column

    @staticmethod
    def xform_to_sqlalchemy_schema(column_list: List[ColumnCatalogEntry]) -> Dict[str, Column]:
        """Converts the list of DataFrameColumns to SQLAlchemyColumns

        Args:
            column_list (List[ColumnCatalog]): columns to be converted

        Returns:
            Dict[str, Column]: mapping from column_name to sqlalchemy column object
        """
        return {column.name: SchemaUtils.xform_to_sqlalchemy_column(column) for column in column_list}

@staticmethod
def xform_to_sqlalchemy_column(df_column: ColumnCatalogEntry) -> Column:
    column_type = df_column.type
    sqlalchemy_column = None
    if column_type == ColumnType.INTEGER:
        sqlalchemy_column = Column(Integer)
    elif column_type == ColumnType.FLOAT:
        sqlalchemy_column = Column(Float)
    elif column_type == ColumnType.TEXT:
        sqlalchemy_column = Column(TEXT)
    elif column_type == ColumnType.NDARRAY:
        sqlalchemy_column = Column(LargeBinary)
    else:
        msg = 'Invalid column type: ' + str(column_type)
        logger.error(msg)
        raise NotImplementedError
    return sqlalchemy_column

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

def get_entries_by_function_id(self, function_id: int) -> List[FunctionMetadataCatalogEntry]:
    try:
        result = self.session.execute(select(self.model).filter(self.model._function_id == function_id)).scalars().all()
        return [obj.as_dataclass() for obj in result]
    except Exception as e:
        error = f'Getting metadata entries for function id {function_id} raised {e}'
        logger.error(error)
        raise CatalogError(error)

class BaseService:
    """
    Base service for all the models. Implemented by all other services.
    The services perform business logic using the model provided
    """

    def __init__(self, model: BaseModel, session: Session):
        self.model = model
        self.session = session
        self.query = session.query(model)

    def get_all_entries(self) -> List:
        try:
            entries = self.query.all()
            return [entry.as_dataclass() for entry in entries]
        except NoResultFound:
            return []

def __init__(self, model: BaseModel, session: Session):
    self.model = model
    self.session = session
    self.query = session.query(model)

def get_all_entries(self) -> List:
    try:
        entries = self.query.all()
        return [entry.as_dataclass() for entry in entries]
    except NoResultFound:
        return []

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

def as_dataclass(self) -> 'ColumnCatalogEntry':
    return ColumnCatalogEntry(row_id=self._row_id, name=self._name, type=self._type, is_nullable=self._is_nullable, array_type=self._array_type, array_dimensions=self.array_dimensions, table_id=self._table_id, table_name=self._table_catalog._name, dep_caches=[cache.as_dataclass() for cache in self._dep_caches])

def init_db(engine: Engine):
    """Create database if doesn't exist and create all tables."""
    if not database_exists(engine.url):
        logger.info('Database does not exist, creating database.')
        create_database(engine.url)
    logger.info('Creating tables')
    BaseModel.metadata.create_all(bind=engine)

def truncate_catalog_tables(engine: Engine, tables_not_to_truncate: List[str]=[]):
    """Truncate all the catalog tables"""
    BaseModel.metadata.reflect(bind=engine)
    insp = sqlalchemy.inspect(engine)
    if database_exists(engine.url):
        with contextlib.closing(engine.connect()) as con:
            trans = con.begin()
            for table in reversed(BaseModel.metadata.sorted_tables):
                if table.name not in tables_not_to_truncate:
                    if insp.has_table(table.name):
                        con.execute(table.delete())
            trans.commit()

def drop_all_tables_except_catalog(engine: Engine):
    """drop all the tables except the catalog"""
    BaseModel.metadata.reflect(bind=engine)
    insp = sqlalchemy.inspect(engine)
    if database_exists(engine.url):
        with contextlib.closing(engine.connect()) as con:
            trans = con.begin()
            for table in reversed(BaseModel.metadata.sorted_tables):
                if table.name not in CATALOG_TABLES:
                    if insp.has_table(table.name):
                        table.drop(con)
            trans.commit()

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

def __init__(self, name: str, function_id: int, cache_path: str, args: Tuple[str]):
    self._name = name
    self._function_id = function_id
    self._cache_path = cache_path
    self._args = str(args)

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

def __init__(self, name: str, type: ColumnType, is_nullable: bool=False, array_type: NdArrayType=None, array_dimensions: Tuple[int]=None, is_input: bool=True, function_id: int=None):
    self._name = name
    self._type = type
    self._is_nullable = is_nullable
    self._array_type = array_type
    self.array_dimensions = array_dimensions or str(())
    self._is_input = is_input
    self._function_id = function_id

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

def __str__(self):
    start_str = f'\nSTART {self.start_time}' if self.start_time is not None else ''
    end_str = f'\nEND {self.end_time}' if self.end_time is not None else ''
    repeat_str = f'\nEVERY {self.repeat_interval} {self.repeat_period}' if self.repeat_interval is not None else ''
    return f'CREATE JOB {self.job_name} AS\n({(str(q) for q in self.queries)}){start_str} {end_str} {repeat_str}'

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

def __str__(self):
    return f'SET {str(self.config_name)} = {str(self.config_value)}'

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

def __str__(self):
    msg = f'{self.alias_name}'
    if len(self.col_names) > 0:
        msg += f'({str(self.col_names)})'
    return msg

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

def __str__(self) -> str:
    delete_str = f'DELETE FROM {self._table_ref}'
    if self._where_clause is not None:
        delete_str += ' WHERE ' + str(self._where_clause)
    return delete_str

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

def uid(self, tree):
    if hasattr(tree.children[0], 'type') and tree.children[0].type == 'REVERSE_QUOTE_ID':
        tree.children[0].type = 'simple_id'
        non_tick_string = str(tree.children[0]).replace('`', '')
        return non_tick_string
    return self.visit(tree.children[0])

def simple_id(self, tree):
    simple_id = str(tree.children[0])
    return simple_id

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

def connect(self):
    try:
        self.client = WebClient(token=self.token)
        return DBHandlerStatus(status=True)
    except Exception as e:
        return DBHandlerStatus(status=False, error=str(e))

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

def connect(self):
    """
        Set up the connection required by the handler.
        Returns:
            DBHandlerStatus
        """
    return DBHandlerStatus(status=True)

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

def add(self, payload: List[FeaturePayload]):
    milvus_data = [{'id': feature_payload.id, 'vector': feature_payload.embedding.reshape(-1).tolist()} for feature_payload in payload]
    ids = [feature_payload.id for feature_payload in payload]
    self._client.delete(collection_name=self._collection_name, pks=ids)
    self._client.insert(collection_name=self._collection_name, data=milvus_data)

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

def all_true(self) -> bool:
    return self._frames.all().bool()

def all_false(self) -> bool:
    inverted = ~self._frames
    return inverted.all().bool()

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

def create_table(uri: str, table_name: str, columns: dict):
    """
    Create a table in the database using sqlalchmey.

    Parameters:
    uri (str): the sqlalchmey uri to connect to the database
    table_name (str): The name of the table to create.
    columns (dict): A dictionary where keys are column names and values are column types.
    """
    Base = declarative_base()
    attr_dict = {'__tablename__': table_name}
    column_name, column_type = columns.popitem()
    attr_dict.update({column_name: Column(column_type.type, primary_key=True)})
    attr_dict.update(columns)
    _ = type(f'__placeholder_class_name__{table_name}', (Base,), attr_dict)()
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    session.commit()
    session.close()

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

def format_col_type(col):
    try:
        return col.type.get_col_spec()
    except (AttributeError, NotImplementedError):
        return str(col.type)

def run_command(command_str: str):
    output = subprocess.check_output(command_str, shell=True, universal_newlines=True).rstrip()
    pprint(command_str)
    if 'version' in command_str:
        pprint(output)
    return output

def upload_assets(changelog, tag):
    access_token = os.environ['GITHUB_KEY']
    repo_owner = 'georgia-tech-db'
    repo_name = 'evadb'
    tag_name = 'v' + tag
    assert 'vv' not in tag
    asset_filepaths = [f'dist/evadb-{tag}-py3-none-any.whl', f'dist/evadb-{tag}.tar.gz']
    g = Github(access_token)
    repo = g.get_repo(f'{repo_owner}/{repo_name}')
    release_name = tag_name
    release_message = f'{tag_name}\n\n {changelog}'
    release = repo.create_git_release(tag=tag_name, name=release_name, message=release_message, draft=False, prerelease=False)
    release = repo.get_release(tag_name)
    for filepath in asset_filepaths:
        asset_name = filepath.split('/')[-1]
        asset_path = Path(f'{EvaDB_DIR}/{filepath}')
        print('path: ' + str(asset_path))
        release.upload_asset(str(asset_path), asset_name)
    print('Release created and published successfully.')

def receive_user_input() -> Dict:
    """Receives user input.

    Returns:
        user_input (dict): global configurations
    """
    print('🔮 Welcome to EvaDB! This app lets you ask questions on any local or YouTube online video.\nYou will only need to supply a Youtube URL and an OpenAI API key.\n')
    from_youtube = str(input("📹 Are you querying an online Youtube video or a local video? ('yes' for online/ 'no' for local): ")).lower() in ['y', 'yes']
    user_input = {'from_youtube': from_youtube}
    if from_youtube:
        video_link = str(input('🌐 Enter the URL of the YouTube video (press Enter to use our default Youtube video URL): '))
        if video_link == '':
            video_link = DEFAULT_VIDEO_LINK
        user_input['video_link'] = video_link
    else:
        video_local_path = str(input('💽 Enter the local path to your video (press Enter to use our demo video): '))
        if video_local_path == '':
            video_local_path = DEFAULT_VIDEO_PATH
        user_input['video_local_path'] = video_local_path
    try:
        api_key = os.environ['OPENAI_API_KEY']
    except KeyError:
        api_key = str(input('🔑 Enter your OpenAI key: '))
        os.environ['OPENAI_API_KEY'] = api_key
    return user_input

def download_youtube_video_transcript(video_link: str):
    """Downloads a YouTube video's transcript.

    Args:
        video_link (str): url of the target YouTube video.
    """
    video_id = extract.video_id(video_link)
    print('⏳ Transcript download in progress...')
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print('✅ Video transcript downloaded successfully.')
    return transcript

def download_youtube_video_from_link(video_link: str):
    """Downloads a YouTube video from url.

    Args:
        video_link (str): url of the target YouTube video.
    """
    yt = YouTube(video_link).streams.filter(file_extension='mp4', progressive='True').first()
    try:
        print('⏳ video download in progress...')
        yt.download(filename=ONLINE_VIDEO_PATH)
    except Exception as e:
        print(f'⛔️ Video download failed with error: \n{e}')
    print('✅ Video downloaded successfully.')

def generate_online_video_transcript(cursor: evadb.EvaDBCursor) -> str:
    """Extracts speech from video for llm processing.

    Args:
        cursor (EVADBCursor): evadb api cursor.

    Returns:
        str: video transcript text.
    """
    print('\n⏳ Analyzing YouTube video. This may take a while...')
    cursor.query('DROP TABLE IF EXISTS youtube_video;').execute()
    cursor.query(f"LOAD VIDEO '{ONLINE_VIDEO_PATH}' INTO youtube_video;").execute()
    cursor.query('DROP TABLE IF EXISTS youtube_video_text;').execute()
    cursor.query('CREATE TABLE IF NOT EXISTS youtube_video_text AS SELECT SpeechRecognizer(audio) FROM youtube_video;').execute()
    print('✅ Video analysis completed.')
    raw_transcript_string = cursor.query('SELECT text FROM youtube_video_text;').df()['youtube_video_text.text'][0]
    return raw_transcript_string

def generate_local_video_transcript(cursor: evadb.EvaDBCursor, video_path: str) -> str:
    """Extracts speech from video for llm processing.

    Args:
        cursor (EVADBCursor): evadb api cursor.
        video_path (str): video path.

    Returns:
        str: video transcript text.
    """
    print(f'\n⏳ Analyzing local video from {video_path}. This may take a while...')
    cursor.query('DROP TABLE IF EXISTS local_video;').execute()
    cursor.query(f"LOAD VIDEO '{video_path}' INTO local_video;").execute()
    cursor.query('DROP TABLE IF EXISTS local_video_text;').execute()
    cursor.query('CREATE TABLE IF NOT EXISTS local_video_text AS SELECT SpeechRecognizer(audio) FROM local_video;').execute()
    print('✅ Video analysis completed.')
    raw_transcript_string = cursor.query('SELECT text FROM local_video_text;').df()['local_video_text.text'][0]
    return raw_transcript_string

def generate_summary(cursor: evadb.EvaDBCursor):
    """Generate summary of a video transcript if it is too long (exceeds llm token limits)

    Args:
        cursor (EVADBCursor): evadb api cursor.
    """
    transcript_list = cursor.query('SELECT text FROM Transcript;').df()['transcript.text']
    if len(transcript_list) == 1:
        summary = transcript_list[0]
        df = pd.DataFrame([{'summary': summary}])
        df.to_csv(SUMMARY_PATH)
        cursor.query('DROP TABLE IF EXISTS Summary;').execute()
        cursor.query('CREATE TABLE IF NOT EXISTS Summary (summary TEXT(100));').execute()
        cursor.query(f"LOAD CSV '{SUMMARY_PATH}' INTO Summary;").execute()
        return
    generate_summary_text_query = "SELECT ChatGPT('summarize the video in detail', text) FROM Transcript;"
    responses = cursor.query(generate_summary_text_query).df()['chatgpt.response']
    summary = ''
    for r in responses:
        summary += f'{r} \n'
    df = pd.DataFrame([{'summary': summary}])
    df.to_csv(SUMMARY_PATH)
    need_to_summarize = len(summary) > MAX_CHUNK_SIZE
    while need_to_summarize:
        partitioned_summary = partition_summary(summary)
        df = pd.DataFrame([{'summary': partitioned_summary}])
        df.to_csv(SUMMARY_PATH)
        cursor.query('DROP TABLE IF EXISTS Summary;').execute()
        cursor.query('CREATE TABLE IF NOT EXISTS Summary (summary TEXT(100));').execute()
        cursor.query(f"LOAD CSV '{SUMMARY_PATH}' INTO Summary;").execute()
        generate_summary_text_query = "SELECT ChatGPT('summarize in detail', summary) FROM Summary;"
        responses = cursor.query(generate_summary_text_query).df()['chatgpt.response']
        summary = ' '.join(responses)
        if len(summary) <= MAX_CHUNK_SIZE:
            need_to_summarize = False
    cursor.query('DROP TABLE IF EXISTS Summary;').execute()
    cursor.query('CREATE TABLE IF NOT EXISTS Summary (summary TEXT(100));').execute()
    cursor.query(f"LOAD CSV '{SUMMARY_PATH}' INTO Summary;").execute()

def generate_response(cursor: evadb.EvaDBCursor, question: str) -> str:
    """Generates question response with llm.

    Args:
        cursor (EVADBCursor): evadb api cursor.
        question (str): question to ask to llm.

    Returns
        str: response from llm.
    """
    if len(cursor.query('SELECT text FROM Transcript;').df()['transcript.text']) == 1:
        return cursor.query(f"SELECT ChatGPT('{question}', text) FROM Transcript;").df()['chatgpt.response'][0]
    else:
        if not os.path.exists(SUMMARY_PATH):
            generate_summary(cursor)
        return cursor.query(f"SELECT ChatGPT('{question}', summary) FROM Summary;").df()['chatgpt.response'][0]

def generate_blog_sections(cursor: evadb.EvaDBCursor) -> List:
    """Generates logical sections of the blog post.

    Args:
        cursor (EVADBCursor): evadb api cursor.

    Returns
        List: list of blog sections
    """
    sections_query = 'list 7 logical sections of a blog post from the transcript as a python list'
    sections_string = str(cursor.query(f"SELECT ChatGPT('{sections_query}', summary) FROM Summary;").df()['chatgpt.response'][0])
    begin = sections_string.find('[')
    end = sections_string.find(']')
    assert begin != -1 and end != -1, 'cannot infer blog sections.'
    sections_string = sections_string[begin + 1:end]
    sections_string = sections_string.replace('\n', '')
    sections_string = sections_string.replace('\t', '')
    sections_string = sections_string.replace('"', '')
    sections = sections_string.split(',')
    for i in range(len(sections)):
        sections[i] = sections[i].strip()
    print(sections)
    return sections

def generate_blog_post(cursor: evadb.EvaDBCursor):
    """Generates blog post.

    Args:
        cursor (EVADBCursor): evadb api cursor.
    """
    to_generate = str(input('\nWould you like to generate a blog post based on the video? (yes/no): '))
    if to_generate.lower() == 'yes' or to_generate.lower() == 'y':
        print('⏳ Generating blog post (may take a while)...')
        if not os.path.exists(SUMMARY_PATH):
            generate_summary(cursor)
        sections = generate_blog_sections(cursor)
        title_query = 'generate a creative title of a blog post from the transcript'
        generate_title_rel = cursor.query(f"SELECT ChatGPT('{title_query}', summary) FROM Summary;")
        blog = '# ' + generate_title_rel.df()['chatgpt.response'][0].replace('"', '')
        i = 1
        for section in sections:
            print(f'--⏳ Generating body ({i}/{len(sections)}) titled {section}...')
            if 'introduction' in section.lower():
                section_query = f'write a section about {section} from transcript'
                section_prompt = 'generate response in markdown format and highlight important technical terms with hyperlinks'
            elif 'conclusion' in section.lower():
                section_query = 'write a creative conclusion from transcript'
                section_prompt = 'generate response in markdown format'
            else:
                section_query = f'write a single detailed section about {section} from transcript'
                section_prompt = 'generate response in markdown format with information from the internet'
            generate_section_rel = cursor.query(f"SELECT ChatGPT('{section_query}', summary, '{section_prompt}') FROM Summary;")
            generated_section = generate_section_rel.df()['chatgpt.response'][0]
            print(generated_section)
            blog += '\n' + generated_section + '\n'
            i += 1
        source_query = 'generate a short list of keywords for the transcript with hyperlinks'
        source_prompt = 'generate response in markdown format'
        print('--⏳ Wrapping up...')
        generate_source_rel = cursor.query(f"SELECT ChatGPT('{source_query}', summary, '{source_prompt}') FROM Summary;")
        blog += '\n## Sources\n' + generate_source_rel.df()['chatgpt.response'][0]
        print(blog)
        if os.path.exists(BLOG_PATH):
            os.remove(BLOG_PATH)
        with open(BLOG_PATH, 'w') as file:
            file.write(blog)
        print(f'✅ blog post is saved to file {os.path.abspath(BLOG_PATH)}')

def ask_question(story_path: str):
    llm = GPT4All('ggml-model-gpt4all-falcon-q4_0.bin')
    path = os.path.dirname(evadb.__file__)
    cursor = evadb.connect().cursor()
    story_table = 'TablePPText'
    story_feat_table = 'FeatTablePPText'
    index_table = 'IndexTable'
    timestamps = {}
    t_i = 0
    timestamps[t_i] = perf_counter()
    print('Setup Function')
    Text_feat_function_query = f"CREATE FUNCTION IF NOT EXISTS SentenceFeatureExtractor\n            IMPL  '{path}/functions/sentence_feature_extractor.py';\n            "
    cursor.query('DROP FUNCTION IF EXISTS SentenceFeatureExtractor;').execute()
    cursor.query(Text_feat_function_query).execute()
    cursor.query(f'DROP TABLE IF EXISTS {story_table};').execute()
    cursor.query(f'DROP TABLE IF EXISTS {story_feat_table};').execute()
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print('Create table')
    cursor.query(f'CREATE TABLE {story_table} (id INTEGER, data TEXT(1000));').execute()
    for i, text in enumerate(read_text_line(story_path)):
        print('text: --' + text + '--')
        ascii_text = unidecode(text)
        cursor.query(f"INSERT INTO {story_table} (id, data)\n                VALUES ({i}, '{ascii_text}');").execute()
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print('Extract features')
    cursor.query(f'CREATE TABLE {story_feat_table} AS\n        SELECT SentenceFeatureExtractor(data), data FROM {story_table};').execute()
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print('Create index')
    cursor.query(f'CREATE INDEX {index_table} ON {story_feat_table} (features) USING QDRANT;').execute()
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print('Query')
    question = 'Who is Count Cyril Vladmirovich?'
    ascii_question = unidecode(question)
    res_batch = cursor.query(f"SELECT data FROM {story_feat_table}\n        ORDER BY Similarity(SentenceFeatureExtractor('{ascii_question}'),features)\n        LIMIT 5;").execute()
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print('Merge')
    context_list = []
    for i in range(len(res_batch)):
        context_list.append(res_batch.frames[f'{story_feat_table.lower()}.data'][i])
    context = '\n'.join(context_list)
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print('LLM')
    query = f'If the context is not relevant, please answer the question by using your own knowledge about the topic.\n    \n    {context}\n    \n    Question : {question}'
    full_response = llm.generate(query)
    print(full_response)
    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f'Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms')
    print(f'Total Time: {(timestamps[t_i] - timestamps[0]) * 1000:.3f} ms')

def try_execute(conn, query):
    try:
        conn.query(query).execute()
    except Exception:
        pass

@app.route('/query', methods=['POST', 'GET'])
def query_from_db():
    if request.method == 'POST':
        query = request.form['query']
        res = cursor.query(query).df()
        return {'api response': res.to_json()}
    return '<html>\n                <body>\n                    <form method="POST"\n                        enctype = "multipart/form-data">\n                        <input type = "input" name = "query" placeholder="Enter query"/>\n                        <input type = "submit"/>\n                    </form>\n                </body>\n            </html>'

def query(question):
    context_docs = cursor.query(f"\n        SELECT data\n        FROM embedding_table\n        ORDER BY Similarity(embedding('{question}'), features)\n        LIMIT 5;\n    ").df()
    context = '\n'.join(context_docs['embedding_table.data'])
    llm = GPT4All('ggml-model-gpt4all-falcon-q4_0.bin')
    llm.set_thread_count(16)
    message = f'If the context is not relevant, please answer the question by using your own knowledge about the topic.\n    \n    {context}\n    \n    Question : {question}'
    answer = llm.generate(message)
    print('\n> Answer:', answer)

def load_data(source_folder_path: str):
    path = os.path.dirname(evadb.__file__)
    cursor = evadb.connect(path).cursor()
    cursor.query('DROP FUNCTION IF EXISTS embedding;').execute()
    text_feat_function_query = f"CREATE FUNCTION IF NOT EXISTS embedding\n            IMPL  '{path}/functions/sentence_feature_extractor.py';\n            "
    print(text_feat_function_query)
    cursor.query(text_feat_function_query).execute()
    print('🧹 Dropping existing tables in EvaDB')
    cursor.query('DROP TABLE IF EXISTS data_table;').execute()
    cursor.query('DROP TABLE IF EXISTS embedding_table;').execute()
    print('📄 Loading PDFs into EvaDB')
    text_load_query = f"LOAD PDF '{source_folder_path}/*.pdf' INTO data_table;"
    print(text_load_query)
    cursor.query(text_load_query).execute()
    print('🤖 Extracting Feature Embeddings. This may take some time ...')
    cursor.query('CREATE TABLE IF NOT EXISTS embedding_table AS SELECT embedding(data), data FROM data_table;').execute()
    print('🔍 Building FAISS Index ...')
    cursor.query('\n        CREATE INDEX embedding_index\n        ON embedding_table (features)\n        USING FAISS;\n    ').execute()

def receive_user_input() -> Dict:
    """Receives user input.

    Returns:
        user_input (dict): global configurations
    """
    print('🔮 Welcome to EvaDB! This app lets you to run data analytics on a csv file like in a conversational manner.\nYou will only need to supply a path to csv file and an OpenAI API key.\n\n')
    user_input = dict()
    csv_path = str(input('📋 Enter the csv file path (press Enter to use our default csv file): '))
    if csv_path == '':
        csv_path = DEFAULT_CSV_PATH
    user_input['csv_path'] = csv_path
    try:
        api_key = os.environ['OPENAI_API_KEY']
    except KeyError:
        api_key = str(input('🔑 Enter your OpenAI key: '))
        os.environ['OPENAI_API_KEY'] = api_key
    return user_input

def generate_script(cursor: evadb.EvaDBCursor, df: pd.DataFrame, question: str) -> str:
    """Generates script with llm.

    Args:
        cursor (EVADBCursor): evadb api cursor.
        question (str): question to ask to llm.

    Returns
        str: script generated by llm.
    """
    all_columns = list(df)
    df[all_columns] = df[all_columns].astype(str)
    prompt = f'There is a dataframe in pandas (python). The name of the\n            dataframe is df. This is the result of print(df.head()):\n            {str(df.head())}. Return a python script with comments to get the answer to the following question: {question}. Do not write code to load the CSV file.'
    question_df = pd.DataFrame([{'prompt': prompt}])
    question_df.to_csv(QUESTION_PATH)
    cursor.drop_table('Question', if_exists=True).execute()
    cursor.query('CREATE TABLE IF NOT EXISTS Question (prompt TEXT(50));').execute()
    cursor.load(QUESTION_PATH, 'Question', 'csv').execute()
    pd.set_option('display.max_colwidth', None)
    query = cursor.table('Question').select('ChatGPT(prompt)')
    script_body = query.df()['chatgpt.response'][0]
    return script_body

