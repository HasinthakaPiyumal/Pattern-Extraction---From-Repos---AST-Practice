# Cluster 31

def create_sample_csv(num_frames=NUM_FRAMES):
    try:
        os.remove(os.path.join(get_tmp_dir(), 'dummy.csv'))
    except FileNotFoundError:
        pass
    sample_meta = {}
    index = 0
    sample_labels = ['car', 'pedestrian', 'bicycle']
    num_videos = 2
    for video_id in range(num_videos):
        for frame_id in range(num_frames):
            random_coords = 200 + 300 * np.random.random(4)
            sample_meta[index] = {'id': index, 'frame_id': frame_id, 'video_id': video_id, 'dataset_name': 'test_dataset', 'label': sample_labels[np.random.choice(len(sample_labels))], 'bbox': ','.join([str(coord) for coord in random_coords]), 'object_id': np.random.choice(3)}
            index += 1
    df_sample_meta = pd.DataFrame.from_dict(sample_meta, 'index')
    df_sample_meta.to_csv(os.path.join(get_tmp_dir(), 'dummy.csv'), index=False)
    return os.path.join(get_tmp_dir(), 'dummy.csv')

def create_csv_with_comlumn_name_spaces(num_frames=NUM_FRAMES):
    try:
        os.remove(os.path.join(get_tmp_dir(), 'dummy.csv'))
    except FileNotFoundError:
        pass
    sample_meta = {}
    index = 0
    sample_labels = ['car', 'pedestrian', 'bicycle']
    num_videos = 2
    for video_id in range(num_videos):
        for frame_id in range(num_frames):
            random_coords = 200 + 300 * np.random.random(4)
            sample_meta[index] = {'id': index, 'frame id': frame_id, 'video id': video_id, 'dataset name': 'test_dataset', 'label': sample_labels[np.random.choice(len(sample_labels))], 'bbox': ','.join([str(coord) for coord in random_coords]), 'object id': np.random.choice(3)}
            index += 1
    df_sample_meta = pd.DataFrame.from_dict(sample_meta, 'index')
    df_sample_meta.to_csv(os.path.join(get_tmp_dir(), 'dummy.csv'), index=False)
    return os.path.join(get_tmp_dir(), 'dummy.csv')

def create_csv(num_rows, columns):
    csv_path = os.path.join(get_tmp_dir(), 'dummy.csv')
    try:
        os.remove(csv_path)
    except FileNotFoundError:
        pass
    df = pd.DataFrame(columns=columns)
    for col in columns:
        df[col] = np.random.randint(1, 100, num_rows)
    df.to_csv(csv_path, index=False)
    return (df, csv_path)

def create_text_csv(num_rows=30):
    """
    Creates a csv with 2 columns: id and comment
    The comment column has 2 values: "I like this" and "I don't like this" that are alternated
    """
    csv_path = os.path.join(get_tmp_dir(), 'dummy.csv')
    try:
        os.remove(csv_path)
    except FileNotFoundError:
        pass
    df = pd.DataFrame(columns=['id', 'comment'])
    df['id'] = np.arange(num_rows)
    df['comment'] = np.where(df['id'] % 2 == 0, 'I like this', "I don't like this")
    df.to_csv(csv_path, index=False)
    return csv_path

def create_sample_image():
    img_path = os.path.join(get_tmp_dir(), 'dummy.jpg')
    try:
        os.remove(img_path)
    except FileNotFoundError:
        pass
    img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
    img[0] -= 1
    img[2] += 1
    try_to_import_cv2()
    import cv2
    cv2.imwrite(img_path, img)
    return img_path

def create_random_image(i, path):
    img = np.random.random_sample([400, 400, 3]).astype(np.uint8)
    try_to_import_cv2()
    import cv2
    cv2.imwrite(os.path.join(path, f'img{i}.jpg'), img)

def create_sample_video(num_frames=NUM_FRAMES):
    file_name = os.path.join(get_tmp_dir(), 'dummy.avi')
    try:
        os.remove(file_name)
    except FileNotFoundError:
        pass
    duration = 1
    fps = NUM_FRAMES
    try_to_import_cv2()
    import cv2
    out = cv2.VideoWriter(file_name, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, (32, 32), False)
    for i in range(fps * duration):
        data = np.array(np.ones((FRAME_SIZE[1], FRAME_SIZE[0])) * i, dtype=np.uint8)
        out.write(data)
    out.release()
    return file_name

def file_remove(path, parent_dir=None):
    parent_dir = parent_dir or get_tmp_dir()
    try:
        os.remove(os.path.join(parent_dir, path))
    except FileNotFoundError:
        pass

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

@decorators.setup(cacheable=True, function_type='object_detection', batchable=True)
def setup(self, *args, **kwargs):
    pass

class DummyNoInputFunction(AbstractFunction):

    @decorators.setup(cacheable=False, function_type='test', batchable=False)
    def setup(self, *args, **kwargs):
        pass

    @property
    def name(self) -> str:
        return 'DummyNoInputFunction'

    @decorators.forward(input_signatures=[], output_signatures=[PandasDataframe(columns=['label'], column_types=[NdArrayType.STR], column_shapes=[(None,)])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        ret = pd.DataFrame([{'label': 'DummyNoInputFunction'}])
        return ret

@decorators.setup(cacheable=False, function_type='test', batchable=False)
def setup(self, *args, **kwargs):
    pass

class DummyLLM(AbstractFunction):

    @property
    def name(self) -> str:
        return 'DummyLLM'

    @decorators.setup(cacheable=True, function_type='chat-completion', batchable=True)
    def setup(self, *args, **kwargs):
        pass

    @decorators.forward(input_signatures=[PandasDataframe(columns=['query', 'content', 'prompt'], column_types=[NdArrayType.STR, NdArrayType.STR, NdArrayType.STR], column_shapes=[(1,), (1,), (None,)])], output_signatures=[PandasDataframe(columns=['response'], column_types=[NdArrayType.STR], column_shapes=[(1,)])])
    def forward(self, text_df):
        queries = text_df[text_df.columns[0]]
        content = text_df[text_df.columns[0]]
        if len(text_df.columns) > 1:
            queries = text_df.iloc[:, 0]
            content = text_df.iloc[:, 1]
        prompt = None
        if len(text_df.columns) > 2:
            prompt = text_df.iloc[0, 2]
        results = []
        for query, content in zip(queries, content):
            results.append(('' if prompt is None else prompt) + query + ' ' + content)
        df = pd.DataFrame({'response': results})
        time.sleep(1)
        return df

@decorators.setup(cacheable=True, function_type='chat-completion', batchable=True)
def setup(self, *args, **kwargs):
    pass

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

def create_dummy_csv_file(catalog) -> str:
    tmp_dir_from_config = catalog.get_configuration_catalog_value('tmp_dir')
    df_dict = [{'prompt': 'summarize', 'content': 'There are times when the night sky glows with bands of color. The bands may begin as cloud shapes and then spread into a great arc across the entire sky. They may fall in folds like a curtain drawn across the heavens. The lights usually grow brighter, then suddenly dim. During this time the sky glows with pale yellow, pink, green, violet, blue, and red. These lights are called the Aurora Borealis. Some people call them the Northern Lights. Scientists have been watching them for hundreds of years. They are not quite sure what causes them'}]
    df = pd.DataFrame(df_dict)
    dummy_file_path = tmp_dir_from_config + '/queries.csv'
    df.to_csv(dummy_file_path)
    return dummy_file_path

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

def _load_image(self, path):
    try_to_import_cv2()
    import cv2
    assert path.exists(), f'File does not exist at the path {str(path)}'
    img = cv2.imread(str(path))
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

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

def _load_image(self, path):
    try_to_import_cv2()
    import cv2
    img = cv2.imread(path)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def numpy_to_yolo_format(numpy_image):
    numpy_image = numpy_image.astype(np.float64)
    numpy_image = numpy_image / 255
    try_to_import_torch()
    import torch
    r = torch.tensor(numpy_image[:, :, 0])
    g = torch.tensor(numpy_image[:, :, 1])
    b = torch.tensor(numpy_image[:, :, 2])
    rgb = torch.stack((r, g, b), dim=0)
    rgb = rgb.unsqueeze(0)
    return rgb

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

def _load_image(self, path):
    try_to_import_cv2()
    import cv2
    img = cv2.imread(path)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

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

def _load_image(self, path):
    assert path.exists(), f'File does not exist at the path {str(path)}'
    try_to_import_cv2()
    import cv2
    img = cv2.imread(str(path))
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

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

def setUp(self):
    self.open_instance = Open()
    self.image_file_path = create_sample_image()
    try_to_import_cv2()

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

def setUp(self):
    self.gb_instance = GaussianBlur()
    self.tmp_file = f'{EvaDB_ROOT_DIR}/test/unit_tests/functions/data/tmp.jpeg'

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

@classmethod
def tearDownClass(cls):
    shutdown_ray()
    execute_query_fetch_all(cls.evadb, 'DROP DATABASE IF EXISTS test_data_source;')
    execute_query_fetch_all(cls.evadb, 'DROP DATABASE IF EXISTS demo;')
    if os.path.exists(cls.db_path):
        os.remove(cls.db_path)

class DecoratorTests(unittest.TestCase):

    def test_setup_flags_are_updated(self):

        @setup(cacheable=True, function_type='classification', batchable=True)
        def setup_func():
            pass
        setup_func()
        self.assertTrue(setup_func.tags['cacheable'])
        self.assertTrue(setup_func.tags['batchable'])
        self.assertEqual(setup_func.tags['function_type'], 'classification')

    def test_setup_flags_are_updated_with_default_values(self):

        @setup()
        def setup_func():
            pass
        setup_func()
        self.assertFalse(setup_func.tags['cacheable'])
        self.assertTrue(setup_func.tags['batchable'])
        self.assertEqual(setup_func.tags['function_type'], 'Abstract')

    def test_forward_flags_are_updated(self):
        input_type = PandasDataframe(columns=['Frame_Array'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256)])
        output_type = NumpyArray(name='label', type=NdArrayType.STR)

        @forward(input_signatures=[input_type], output_signatures=[output_type])
        def forward_func():
            pass
        forward_func()
        self.assertEqual(forward_func.tags['input'], [input_type])
        self.assertEqual(forward_func.tags['output'], [output_type])

@setup()
def setup_func():
    pass

class RulesManager:

    def __init__(self, configs: dict={}):
        self._logical_rules = [LogicalInnerJoinCommutativity(), CacheFunctionExpressionInApply(), CacheFunctionExpressionInFilter(), CacheFunctionExpressionInProject()]
        self._stage_one_rewrite_rules = [XformLateralJoinToLinearFlow(), XformExtractObjectToLinearFlow()]
        self._stage_two_rewrite_rules = [EmbedFilterIntoGet(), EmbedSampleIntoGet(), PushDownFilterThroughJoin(), PushDownFilterThroughApplyAndMerge(), CombineSimilarityOrderByAndLimitToVectorIndexScan(), ReorderPredicates()]
        self._implementation_rules = [LogicalCreateToPhysical(), LogicalCreateFromSelectToPhysical(), LogicalRenameToPhysical(), LogicalCreateFunctionToPhysical(), LogicalCreateFunctionFromSelectToPhysical(), LogicalDropObjectToPhysical(), LogicalInsertToPhysical(), LogicalDeleteToPhysical(), LogicalLoadToPhysical(), LogicalGetToSeqScan(), LogicalDerivedGetToPhysical(), LogicalUnionToPhysical(), LogicalGroupByToPhysical(), LogicalOrderByToPhysical(), LogicalLimitToPhysical(), LogicalJoinToPhysicalNestedLoopJoin(), LogicalLateralJoinToPhysical(), LogicalJoinToPhysicalHashJoin(), LogicalFunctionScanToPhysical(), LogicalFilterToPhysical(), LogicalShowToPhysical(), LogicalExplainToPhysical(), LogicalCreateIndexToVectorIndex(), LogicalVectorIndexScanToPhysical(), LogicalProjectNoTableToPhysical()]
        ray_enabled = configs.get('ray', False)
        if is_ray_enabled_and_installed(ray_enabled):
            self._implementation_rules.extend([LogicalExchangeToPhysical(), LogicalApplyAndMergeToRayPhysical(), LogicalProjectToRayPhysical()])
        else:
            self._implementation_rules.extend([LogicalApplyAndMergeToPhysical(), LogicalProjectToPhysical()])
        self._all_rules = self._stage_one_rewrite_rules + self._stage_two_rewrite_rules + self._logical_rules + self._implementation_rules

    @property
    def stage_one_rewrite_rules(self):
        return self._stage_one_rewrite_rules

    @property
    def stage_two_rewrite_rules(self):
        return self._stage_two_rewrite_rules

    @property
    def implementation_rules(self):
        return self._implementation_rules

    @property
    def logical_rules(self):
        return self._logical_rules

    def disable_rules(self, rules: List[Rule]):

        def _remove_from_list(rule_list, rule_to_remove):
            for rule in rule_list:
                if rule.rule_type == rule_to_remove.rule_type:
                    rule_list.remove(rule)
        for rule in rules:
            assert rule.is_implementation_rule() or rule.is_stage_one_rewrite_rules() or rule.is_stage_two_rewrite_rules() or rule.is_logical_rule(), f'Provided Invalid rule {rule}'
            if rule.is_implementation_rule():
                _remove_from_list(self.implementation_rules, rule)
            elif rule.is_stage_one_rewrite_rules():
                _remove_from_list(self.stage_one_rewrite_rules, rule)
            elif rule.is_stage_two_rewrite_rules():
                _remove_from_list(self.stage_two_rewrite_rules, rule)
            elif rule.is_logical_rule():
                _remove_from_list(self.logical_rules, rule)

    def add_rules(self, rules: List[Rule]):

        def _add_to_list(rule_list, rule_to_remove):
            if any([rule.rule_type != rule_to_remove.rule_type for rule in rule_list]):
                rule_list.append(rule)
        for rule in rules:
            assert rule.is_implementation_rule() or rule.is_stage_one_rewrite_rules() or rule.is_stage_two_rewrite_rules() or rule.is_logical_rule(), f'Provided Invalid rule {rule}'
            if rule.is_implementation_rule():
                _add_to_list(self.implementation_rules, rule)
            elif rule.is_stage_one_rewrite_rules():
                _add_to_list(self.stage_one_rewrite_rules, rule)
            elif rule.is_stage_two_rewrite_rules():
                _add_to_list(self.stage_two_rewrite_rules, rule)
            elif rule.is_logical_rule():
                _add_to_list(self.logical_rules, rule)

def _remove_from_list(rule_list, rule_to_remove):
    for rule in rule_list:
        if rule.rule_type == rule_to_remove.rule_type:
            rule_list.remove(rule)

class Context:
    """
    Stores the context information of the executor, i.e.,
    if using spark, name of the application, current spark executors,
    if using horovod: current rank etc.
    """

    def __init__(self, user_provided_gpu_conf=[]):
        self._user_provided_gpu_conf = user_provided_gpu_conf
        self._gpus = self._populate_gpu_ids()

    @property
    def gpus(self):
        return self._gpus

    def _populate_gpu_from_config(self) -> List:
        available_gpus = [i for i in range(get_gpu_count())]
        return list(set(available_gpus) & set(self._user_provided_gpu_conf))

    def _populate_gpu_from_env(self) -> List:
        gpu_conf = map(lambda x: x.strip(), os.environ.get('CUDA_VISIBLE_DEVICES', '').strip().split(','))
        gpu_conf = list(filter(lambda x: x, gpu_conf))
        gpu_conf = [int(gpu_id) for gpu_id in gpu_conf]
        available_gpus = [i for i in range(get_gpu_count())]
        return list(set(available_gpus) & set(gpu_conf))

    def _populate_gpu_ids(self) -> List:
        if not is_gpu_available():
            return []
        gpus = self._populate_gpu_from_config()
        if len(gpus) == 0:
            gpus = self._populate_gpu_from_env()
        return gpus

    def _select_random_gpu(self) -> str:
        """
        A random GPU selection strategy
        Returns:
            (str): GPU device ID
        """
        return random.choice(self.gpus)

    def gpu_device(self) -> str:
        """
        Selects a GPU on which the task can be executed
        Returns:
             (str): GPU device ID
        """
        if self.gpus:
            return self._select_random_gpu()
        return NO_GPU

def _select_random_gpu(self) -> str:
    """
        A random GPU selection strategy
        Returns:
            (str): GPU device ID
        """
    return random.choice(self.gpus)

def root_mean_squared_error(y_true, y_pred):
    return np.sqrt(np.mean(np.square(y_pred - y_true)))

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

def handle_huggingface_function(self):
    """Handle HuggingFace functions

        HuggingFace functions are special functions that are not loaded from a file.
        So we do not need to call the setup method on them like we do for other functions.
        """
    try_to_import_torch()
    impl_path = f'{self.function_dir}/abstract/hf_abstract_function.py'
    io_list = gen_hf_io_catalog_entries(self.node.name, self.node.metadata)
    return (self.node.name, impl_path, self.node.function_type, io_list, self.node.metadata)

def validate_image(image_path: Path) -> bool:
    try:
        try_to_import_cv2()
        import cv2
        data = cv2.imread(str(image_path))
        return data is not None
    except Exception as e:
        logger.warning(f'Unexpected Exception {e} occurred while reading image file {image_path}')
        return False

class JobScheduler:

    def __init__(self, evadb: EvaDBDatabase) -> None:
        self.poll_interval_seconds = 30
        self._evadb = evadb

    def _update_next_schedule_run(self, job_catalog_entry: JobCatalogEntry) -> bool:
        job_end_time = job_catalog_entry.end_time
        active_status = False
        if job_catalog_entry.repeat_interval and job_catalog_entry.repeat_interval > 0:
            next_trigger_time = datetime.datetime.now() + datetime.timedelta(seconds=job_catalog_entry.repeat_interval)
            if not job_end_time or next_trigger_time < job_end_time:
                active_status = True
        next_trigger_time = next_trigger_time if active_status else job_catalog_entry.next_scheduled_run
        self._evadb.catalog().update_job_catalog_entry(job_catalog_entry.name, next_trigger_time, active_status)
        return (active_status, next_trigger_time)

    def _get_sleep_time(self, next_job_entry: JobCatalogEntry) -> int:
        sleep_time = self.poll_interval_seconds
        if next_job_entry:
            sleep_time = min(sleep_time, (next_job_entry.next_scheduled_run - datetime.datetime.now()).total_seconds())
        sleep_time = max(0, sleep_time)
        return sleep_time

    def _scan_and_execute_jobs(self):
        while True:
            try:
                for next_executable_job in iter(lambda: self._evadb.catalog().get_next_executable_job(only_past_jobs=True), None):
                    execution_time = datetime.datetime.now()
                    self._evadb.catalog().insert_job_history_catalog_entry(next_executable_job.row_id, next_executable_job.name, execution_time, None)
                    execution_results = [execute_query(self._evadb, query) for query in next_executable_job.queries]
                    logger.debug(f'Exection result for job: {next_executable_job.name} results: {execution_results}')
                    self._update_next_schedule_run(next_executable_job)
                    self._evadb.catalog().update_job_history_end_time(next_executable_job.row_id, execution_time, datetime.datetime.now())
                next_executable_job = self._evadb.catalog().get_next_executable_job(only_past_jobs=False)
                sleep_time = self._get_sleep_time(next_executable_job)
                if sleep_time > 0:
                    logger.debug(f'Job scheduler process sleeping for {sleep_time} seconds')
                    time.sleep(sleep_time)
            except Exception as e:
                logger.error(f'Got an exception in job scheduler: {str(e)}')
                time.sleep(self.poll_interval_seconds * 0.2)

    def execute(self):
        try:
            self._scan_and_execute_jobs()
        except KeyboardInterrupt:
            logger.debug('Exiting the job scheduler process due to interrupt')
            sys.exit()

def _get_sleep_time(self, next_job_entry: JobCatalogEntry) -> int:
    sleep_time = self.poll_interval_seconds
    if next_job_entry:
        sleep_time = min(sleep_time, (next_job_entry.next_scheduled_run - datetime.datetime.now()).total_seconds())
    sleep_time = max(0, sleep_time)
    return sleep_time

def is_gpu_available() -> bool:
    """
    Checks if the system has GPUS available to execute tasks
    Returns:
        [bool] True if system has GPUs, else False
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

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

def consolidate_stats(self):
    if self.function_obj is None:
        return
    if self.has_cache() and self._stats.cache_misses > 0:
        cost_per_func_call = self._stats.timer.total_elapsed_time / self._stats.cache_misses
    else:
        cost_per_func_call = self._stats.timer.total_elapsed_time / self._stats.num_calls
    if abs(self._stats.prev_cost - cost_per_func_call) > cost_per_func_call / 10:
        self._stats.prev_cost = cost_per_func_call

def sample_image():
    from PIL import Image, ImageDraw
    width, height = (224, 224)
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    circle_radius = min(width, height) // 4
    circle_center = (width // 2, height // 2)
    circle_bbox = (circle_center[0] - circle_radius, circle_center[1] - circle_radius, circle_center[0] + circle_radius, circle_center[1] + circle_radius)
    draw.ellipse(circle_bbox, fill='yellow')
    return image

class ImageHFModel(AbstractHFFunction):
    """
    Base Model for all HF Models that take in images as input
    """

    def input_formatter(self, inputs: Any):
        frames_list = inputs.values.tolist()
        frames = np.vstack(frames_list)
        from PIL import Image
        images = [Image.fromarray(row) for row in frames]
        return images

def input_formatter(self, inputs: Any):
    frames_list = inputs.values.tolist()
    frames = np.vstack(frames_list)
    from PIL import Image
    images = [Image.fromarray(row) for row in frames]
    return images

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

def _read(self) -> Iterator[Dict]:
    try_to_import_cv2()
    import cv2
    im_bgr = cv2.imread(str(self.file_url))
    im_rgb = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2RGB)
    assert im_rgb is not None, f'Failed to read image file {self.file_url}'
    yield {'data': im_rgb}

class FeatureExtractor(PytorchAbstractClassifierFunction):
    """ """

    def setup(self):
        self.model = models.resnet50(weights='IMAGENET1K_V2', progress=False)
        for param in self.model.parameters():
            param.requires_grad = False
        self.model.fc = torch.nn.Identity()
        self.model.eval()

    @property
    def name(self) -> str:
        return 'FeatureExtractor'

    @property
    def labels(self) -> List[str]:
        return []

    def forward(self, frames: Tensor) -> pd.DataFrame:
        """
        Performs feature extraction on input frames
        Arguments:
            frames (np.ndarray): Frames on which predictions need
            to be performed

        Returns:
            features (List[float])
        """
        outcome = []
        for f in frames:
            with torch.no_grad():
                outcome.append({'features': self.as_numpy(self.model(torch.unsqueeze(f, 0)))})
        return pd.DataFrame(outcome, columns=['features'])

def setup(self):
    self.model = models.resnet50(weights='IMAGENET1K_V2', progress=False)
    for param in self.model.parameters():
        param.requires_grad = False
    self.model.fc = torch.nn.Identity()
    self.model.eval()

def forward(self, frames: Tensor) -> pd.DataFrame:
    """
        Performs feature extraction on input frames
        Arguments:
            frames (np.ndarray): Frames on which predictions need
            to be performed

        Returns:
            features (List[float])
        """
    outcome = []
    for f in frames:
        with torch.no_grad():
            outcome.append({'features': self.as_numpy(self.model(torch.unsqueeze(f, 0)))})
    return pd.DataFrame(outcome, columns=['features'])

class ChatGPT(AbstractFunction):
    """
    Arguments:
        model (str) : ID of the OpenAI model to use. Refer to '_VALID_CHAT_COMPLETION_MODEL' for a list of supported models.
        temperature (float) : Sampling temperature to use in the model. Higher value results in a more random output.

    Input Signatures:
        query (str)   : The task / question that the user wants the model to accomplish / respond.
        content (str) : Any relevant context that the model can use to complete its tasks and generate the response.
        prompt (str)  : An optional prompt that can be passed to the model. It can contain instructions to the model,
                        or a set of examples to help the model generate a better response.
                        If not provided, the system prompt defaults to that of an helpful assistant that accomplishes user tasks.

    Output Signatures:
        response (str) : Contains the response generated by the model based on user input. Any errors encountered
                         will also be passed in the response.

    Example Usage:
        Assume we have the transcripts for a few videos stored in a table 'video_transcripts' in a column named 'text'.
        If the user wants to retrieve the summary of each video, the ChatGPT function can be used as:

            query = "Generate the summary of the video"
            cursor.table("video_transcripts").select(f"ChatGPT({query}, text)")

        In the above function invocation, the 'query' passed would be the user task to generate video summaries, and the
        'content' passed would be the video transcripts that need to be used in order to generate the summary. Since
        no prompt is passed, the default system prompt will be used.

        Now assume the user wants to create the video summary in 50 words and in French. Instead of passing these instructions
        along with each query, a prompt can be set as such:

            prompt = "Generate your responses in 50 words or less. Also, generate the response in French."
            cursor.table("video_transcripts").select(f"ChatGPT({query}, text, {prompt})")

        In the above invocation, an additional argument is passed as prompt. While the query and content arguments remain
        the same, the 'prompt' argument will be set as a system message in model params.

        Both of the above cases would generate a summary for each row / video transcript of the table in the response.
    """

    @property
    def name(self) -> str:
        return 'ChatGPT'

    @setup(cacheable=True, function_type='chat-completion', batchable=True)
    def setup(self, model='gpt-3.5-turbo', temperature: float=0, openai_api_key='') -> None:
        assert model in _VALID_CHAT_COMPLETION_MODEL, f'Unsupported ChatGPT {model}'
        self.model = model
        self.temperature = temperature
        self.openai_api_key = openai_api_key

    @forward(input_signatures=[PandasDataframe(columns=['query', 'content', 'prompt'], column_types=[NdArrayType.STR, NdArrayType.STR, NdArrayType.STR], column_shapes=[(1,), (1,), (None,)])], output_signatures=[PandasDataframe(columns=['response'], column_types=[NdArrayType.STR], column_shapes=[(1,)])])
    def forward(self, text_df):
        try_to_import_openai()
        from openai import OpenAI
        api_key = self.openai_api_key
        if len(self.openai_api_key) == 0:
            api_key = os.environ.get('OPENAI_API_KEY', '')
        assert len(api_key) != 0, "Please set your OpenAI API key using SET OPENAI_API_KEY = 'sk-' or environment variable (OPENAI_API_KEY)"
        client = OpenAI(api_key=api_key)

        @retry(tries=6, delay=20)
        def completion_with_backoff(**kwargs):
            return client.chat.completions.create(**kwargs)
        queries = text_df[text_df.columns[0]]
        content = text_df[text_df.columns[0]]
        if len(text_df.columns) > 1:
            queries = text_df.iloc[:, 0]
            content = text_df.iloc[:, 1]
        prompt = None
        if len(text_df.columns) > 2:
            prompt = text_df.iloc[0, 2]
        results = []
        for query, content in zip(queries, content):
            params = {'model': self.model, 'temperature': self.temperature, 'messages': []}
            def_sys_prompt_message = {'role': 'system', 'content': prompt if prompt is not None else 'You are a helpful assistant that accomplishes user tasks.'}
            params['messages'].append(def_sys_prompt_message)
            params['messages'].extend([{'role': 'user', 'content': f'Here is some context : {content}'}, {'role': 'user', 'content': f'Complete the following task: {query}'}])
            response = completion_with_backoff(**params)
            answer = response.choices[0].message.content
            results.append(answer)
        df = pd.DataFrame({'response': results})
        return df

@setup(cacheable=True, function_type='chat-completion', batchable=True)
def setup(self, model='gpt-3.5-turbo', temperature: float=0, openai_api_key='') -> None:
    assert model in _VALID_CHAT_COMPLETION_MODEL, f'Unsupported ChatGPT {model}'
    self.model = model
    self.temperature = temperature
    self.openai_api_key = openai_api_key

class MVITActionRecognition(PytorchAbstractClassifierFunction):

    @property
    def name(self) -> str:
        return 'MVITActionRecognition'

    def setup(self):
        try_to_import_torchvision()
        try_to_import_torch()
        from torchvision.models.video import MViT_V2_S_Weights, mvit_v2_s
        self.weights = MViT_V2_S_Weights.DEFAULT
        self.model = mvit_v2_s(weights=self.weights)
        self.preprocess = self.weights.transforms()
        self.model.eval()

    @property
    def labels(self) -> np.array([str]):
        return np.array(self.weights.meta['categories'])

    def forward(self, segments):
        return self.classify(segments)

    def transform(self, segments):
        import torch
        segments = torch.Tensor(segments)
        segments = segments.permute(0, 3, 1, 2)
        return self.preprocess(segments).unsqueeze(0)

    def classify(self, segments) -> pd.DataFrame:
        import torch
        with torch.no_grad():
            preds = self.model(segments).softmax(1)
        label_indices = preds.argmax(axis=1)
        actions = self.labels[label_indices]
        if np.isscalar(actions) == 1:
            outcome = pd.DataFrame({'labels': np.array([actions])})
        return outcome

def setup(self):
    try_to_import_torchvision()
    try_to_import_torch()
    from torchvision.models.video import MViT_V2_S_Weights, mvit_v2_s
    self.weights = MViT_V2_S_Weights.DEFAULT
    self.model = mvit_v2_s(weights=self.weights)
    self.preprocess = self.weights.transforms()
    self.model.eval()

def transform(self, segments):
    import torch
    segments = torch.Tensor(segments)
    segments = segments.permute(0, 3, 1, 2)
    return self.preprocess(segments).unsqueeze(0)

def classify(self, segments) -> pd.DataFrame:
    import torch
    with torch.no_grad():
        preds = self.model(segments).softmax(1)
    label_indices = preds.argmax(axis=1)
    actions = self.labels[label_indices]
    if np.isscalar(actions) == 1:
        outcome = pd.DataFrame({'labels': np.array([actions])})
    return outcome

class SiftFeatureExtractor(AbstractFunction, GPUCompatible):

    @setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
    def setup(self):
        try_to_import_kornia()
        import kornia
        self.model = kornia.feature.SIFTDescriptor(100)

    def to_device(self, device: str) -> GPUCompatible:
        self.model = self.model.to(device)
        return self

    @property
    def name(self) -> str:
        return 'SiftFeatureExtractor'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.UINT8], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['features'], column_types=[NdArrayType.FLOAT32], column_shapes=[(1, 128)])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:

        def _forward(row: pd.Series) -> np.ndarray:
            rgb_img = row[0]
            try_to_import_cv2()
            import cv2
            gray_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
            resized_gray_img = cv2.resize(gray_img, (100, 100), interpolation=cv2.INTER_AREA)
            resized_gray_img = np.moveaxis(resized_gray_img, -1, 0)
            batch_resized_gray_img = np.expand_dims(resized_gray_img, axis=0)
            batch_resized_gray_img = np.expand_dims(batch_resized_gray_img, axis=0)
            batch_resized_gray_img = batch_resized_gray_img.astype(np.float32)
            try_to_import_torch()
            import torch
            with torch.no_grad():
                torch_feat = self.model(torch.from_numpy(batch_resized_gray_img))
                feat = torch_feat.numpy()
            feat = feat.reshape(1, -1)
            return feat
        ret = pd.DataFrame()
        ret['features'] = df.apply(_forward, axis=1)
        return ret

@setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
def setup(self):
    try_to_import_kornia()
    import kornia
    self.model = kornia.feature.SIFTDescriptor(100)

def to_device(self, device: str) -> GPUCompatible:
    self.model = self.model.to(device)
    return self

def _forward(row: pd.Series) -> np.ndarray:
    rgb_img = row[0]
    try_to_import_cv2()
    import cv2
    gray_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
    resized_gray_img = cv2.resize(gray_img, (100, 100), interpolation=cv2.INTER_AREA)
    resized_gray_img = np.moveaxis(resized_gray_img, -1, 0)
    batch_resized_gray_img = np.expand_dims(resized_gray_img, axis=0)
    batch_resized_gray_img = np.expand_dims(batch_resized_gray_img, axis=0)
    batch_resized_gray_img = batch_resized_gray_img.astype(np.float32)
    try_to_import_torch()
    import torch
    with torch.no_grad():
        torch_feat = self.model(torch.from_numpy(batch_resized_gray_img))
        feat = torch_feat.numpy()
    feat = feat.reshape(1, -1)
    return feat

class FuzzDistance(AbstractFunction):

    @setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
    def setup(self):
        pass

    @property
    def name(self) -> str:
        return 'FuzzDistance'

    @forward(input_signatures=[PandasDataframe(columns=['data1', 'data2'], column_types=[NdArrayType.STR, NdArrayType.STR], column_shapes=[1, 1])], output_signatures=[PandasDataframe(columns=['distance'], column_types=[NdArrayType.FLOAT32], column_shapes=[1])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:

        def _forward(row: pd.Series) -> np.ndarray:
            data1 = row.iloc[0]
            data2 = row.iloc[1]
            distance = fuzz.ratio(data1, data2)
            return distance
        ret = pd.DataFrame()
        ret['distance'] = df.apply(_forward, axis=1)
        return ret

@setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
def setup(self):
    pass

class FastRCNNObjectDetector(PytorchAbstractClassifierFunction):
    """
    Arguments:
        threshold (float): Threshold for classifier confidence score

    """

    @property
    def name(self) -> str:
        return 'fastrcnn'

    @setup(cacheable=True, function_type='object_detection', batchable=True)
    def setup(self, threshold=0.85):
        try_to_import_torch()
        try_to_import_torchvision()
        import torchvision
        self.threshold = threshold
        self.model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights='COCO_V1', progress=False)
        self.model.eval()

    @property
    def labels(self) -> List[str]:
        return ['__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table', 'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

    @forward(input_signatures=[PyTorchTensor(name='input_col', is_nullable=False, type=NdArrayType.FLOAT32, dimensions=(1, 3, 540, 960))], output_signatures=[PandasDataframe(columns=['labels', 'bboxes', 'scores'], column_types=[NdArrayType.STR, NdArrayType.FLOAT32, NdArrayType.FLOAT32], column_shapes=[(None,), (None,), (None,)])])
    def forward(self, frames) -> pd.DataFrame:
        """
        Performs predictions on input frames
        Arguments:
            frames (np.ndarray): Frames on which predictions need
            to be performed

        Returns:
            tuple containing predicted_classes (List[List[str]]),
            predicted_boxes (List[List[BoundingBox]]),
            predicted_scores (List[List[float]])

        """
        predictions = self.model(frames)
        outcome = []
        for prediction in predictions:
            pred_class = [str(self.labels[i]) for i in list(self.as_numpy(prediction['labels']))]
            pred_boxes = [[i[0], i[1], i[2], i[3]] for i in list(self.as_numpy(prediction['boxes']))]
            pred_score = list(self.as_numpy(prediction['scores']))
            valid_pred = [pred_score.index(x) for x in pred_score if x > self.threshold]
            if valid_pred:
                pred_t = valid_pred[-1]
            else:
                pred_t = -1
            pred_boxes = np.array(pred_boxes[:pred_t + 1])
            pred_class = np.array(pred_class[:pred_t + 1])
            pred_score = np.array(pred_score[:pred_t + 1])
            outcome.append({'labels': pred_class, 'scores': pred_score, 'bboxes': pred_boxes})
        return pd.DataFrame(outcome, columns=['labels', 'scores', 'bboxes'])

@setup(cacheable=True, function_type='object_detection', batchable=True)
def setup(self, threshold=0.85):
    try_to_import_torch()
    try_to_import_torchvision()
    import torchvision
    self.threshold = threshold
    self.model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights='COCO_V1', progress=False)
    self.model.eval()

class SaliencyFeatureExtractor(AbstractFunction, GPUCompatible):

    @setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
    def setup(self):
        self.model = torchvision.models.resnet18(pretrained=True)
        self.model.eval()

    def to_device(self, device: str) -> GPUCompatible:
        self.model = self.model.to(device)
        return self

    @property
    def name(self) -> str:
        return 'SaliencyFeatureExtractor'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.UINT8], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['saliency'], column_types=[NdArrayType.FLOAT32], column_shapes=[(1, 224, 224)])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:

        def _forward(row: pd.Series) -> np.ndarray:
            rgb_img = row[0]
            composed = Compose([Resize((224, 224)), ToTensor()])
            transformed_img = composed(Image.fromarray(rgb_img[:, :, ::-1])).unsqueeze(0)
            transformed_img.requires_grad_()
            outputs = self.model(transformed_img)
            score_max_index = outputs.argmax()
            score_max = outputs[0, score_max_index]
            score_max.backward()
            saliency, _ = torch.max(transformed_img.grad.data.abs(), dim=1)
            return saliency
        ret = pd.DataFrame()
        ret['saliency'] = df.apply(_forward, axis=1)
        return ret

@setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
def setup(self):
    self.model = torchvision.models.resnet18(pretrained=True)
    self.model.eval()

def to_device(self, device: str) -> GPUCompatible:
    self.model = self.model.to(device)
    return self

def _forward(row: pd.Series) -> np.ndarray:
    rgb_img = row[0]
    composed = Compose([Resize((224, 224)), ToTensor()])
    transformed_img = composed(Image.fromarray(rgb_img[:, :, ::-1])).unsqueeze(0)
    transformed_img.requires_grad_()
    outputs = self.model(transformed_img)
    score_max_index = outputs.argmax()
    score_max = outputs[0, score_max_index]
    score_max.backward()
    saliency, _ = torch.max(transformed_img.grad.data.abs(), dim=1)
    return saliency

class Yolo(AbstractFunction, GPUCompatible):
    """
    Arguments:
        threshold (float): Threshold for classifier confidence score
    """

    @property
    def name(self) -> str:
        return 'yolo'

    @setup(cacheable=True, function_type='object_detection', batchable=True)
    def setup(self, model: str, threshold=0.3):
        try_to_import_ultralytics()
        from ultralytics import YOLO
        self.threshold = threshold
        self.model = YOLO(model)
        self.device = 'cpu'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['labels', 'bboxes', 'scores'], column_types=[NdArrayType.STR, NdArrayType.FLOAT32, NdArrayType.FLOAT32], column_shapes=[(None,), (None,), (None,)])])
    def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
        """
        Performs predictions on input frames
        Arguments:
            frames (np.ndarray): Frames on which predictions need
            to be performed
        Returns:
            tuple containing predicted_classes (List[List[str]]),
            predicted_boxes (List[List[BoundingBox]]),
            predicted_scores (List[List[float]])
        """
        outcome = []
        frames = np.ravel(frames.to_numpy())
        list_of_numpy_images = [its for its in frames]
        predictions = self.model.predict(list_of_numpy_images, device=self.device, conf=self.threshold, verbose=False)
        for pred in predictions:
            single_result = pred.boxes
            pred_class = [self.model.names[i] for i in single_result.cls.tolist()]
            pred_score = single_result.conf.tolist()
            pred_score = [round(conf, 2) for conf in single_result.conf.tolist()]
            pred_boxes = single_result.xyxy.tolist()
            sorted_list = list(map(lambda i: i < self.threshold, pred_score))
            t = sorted_list.index(True) if True in sorted_list else len(sorted_list)
            outcome.append({'labels': pred_class[:t], 'bboxes': pred_boxes[:t], 'scores': pred_score[:t]})
        return pd.DataFrame(outcome, columns=['labels', 'bboxes', 'scores'])

    def to_device(self, device: str):
        self.device = device
        return self

@setup(cacheable=True, function_type='object_detection', batchable=True)
def setup(self, model: str, threshold=0.3):
    try_to_import_ultralytics()
    from ultralytics import YOLO
    self.threshold = threshold
    self.model = YOLO(model)
    self.device = 'cpu'

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

@setup(cacheable=False, function_type='TextProcessing', batchable=False)
def setup(self):
    pass

class ASLActionRecognition(PytorchAbstractClassifierFunction):

    @property
    def name(self) -> str:
        return 'ASLActionRecognition'

    def download_weights(self):
        try_to_import_torch()
        import torch
        if not os.path.exists(self.asl_weights_path):
            torch.hub.download_url_to_file(self.asl_weights_url, self.asl_weights_path, hash_prefix=None, progress=True)

    def setup(self):
        self.asl_weights_url = 'https://www.dropbox.com/s/s9l1mezuplc6ttl/asl_top20_resnet_wts.pth?raw=1'
        import torch
        self.asl_weights_path = torch.hub.get_dir() + '/asl_weights.pth'
        self.download_weights()
        try_to_import_torchvision()
        from torchvision.models.video import R3D_18_Weights, r3d_18
        self.weights = R3D_18_Weights.DEFAULT
        self.model = r3d_18(weights=self.weights)
        in_feats = self.model.fc.in_features
        self.model.fc = torch.nn.Linear(in_feats, 20)
        self.model.load_state_dict(torch.load(self.asl_weights_path, map_location='cpu'))
        self.model.eval()
        self.preprocess = self.weights.transforms()

    @property
    def labels(self) -> np.array([str]):
        current_file_path = os.path.dirname(os.path.realpath(__file__))
        pkl_file_path = os.path.join(current_file_path, 'asl_20_actions_map.pkl')
        with open(pkl_file_path, 'rb') as f:
            action_to_index_map = pkl.load(f)
        actions_arr = [''] * len(action_to_index_map)
        for action, index in action_to_index_map.items():
            actions_arr[index] = action
        return np.asarray(actions_arr)

    def forward(self, segments):
        return self.classify(segments)

    def transform(self, segments):
        import torch
        segments = torch.Tensor(segments)
        permute_order = [2, 1, 0]
        segments = segments[:, :, :, permute_order]
        segments = segments.permute(0, 3, 1, 2).to(torch.uint8)
        return self.preprocess(segments).unsqueeze(0)

    def classify(self, segments) -> pd.DataFrame:
        import torch
        with torch.no_grad():
            preds = self.model(segments).softmax(1)
        label_indices = preds.argmax(axis=1)
        actions = self.labels[label_indices]
        if np.isscalar(actions) == 1:
            outcome = pd.DataFrame({'labels': np.array([actions])})
        return outcome

def setup(self):
    self.asl_weights_url = 'https://www.dropbox.com/s/s9l1mezuplc6ttl/asl_top20_resnet_wts.pth?raw=1'
    import torch
    self.asl_weights_path = torch.hub.get_dir() + '/asl_weights.pth'
    self.download_weights()
    try_to_import_torchvision()
    from torchvision.models.video import R3D_18_Weights, r3d_18
    self.weights = R3D_18_Weights.DEFAULT
    self.model = r3d_18(weights=self.weights)
    in_feats = self.model.fc.in_features
    self.model.fc = torch.nn.Linear(in_feats, 20)
    self.model.load_state_dict(torch.load(self.asl_weights_path, map_location='cpu'))
    self.model.eval()
    self.preprocess = self.weights.transforms()

def transform(self, segments):
    import torch
    segments = torch.Tensor(segments)
    permute_order = [2, 1, 0]
    segments = segments[:, :, :, permute_order]
    segments = segments.permute(0, 3, 1, 2).to(torch.uint8)
    return self.preprocess(segments).unsqueeze(0)

def classify(self, segments) -> pd.DataFrame:
    import torch
    with torch.no_grad():
        preds = self.model(segments).softmax(1)
    label_indices = preds.argmax(axis=1)
    actions = self.labels[label_indices]
    if np.isscalar(actions) == 1:
        outcome = pd.DataFrame({'labels': np.array([actions])})
    return outcome

class SentenceTransformerFeatureExtractor(AbstractFunction, GPUCompatible):

    @setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
    def setup(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def to_device(self, device: str) -> GPUCompatible:
        self.model = self.model.to(device)
        return self

    @property
    def name(self) -> str:
        return 'SentenceTransformerFeatureExtractor'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.STR], column_shapes=[1])], output_signatures=[PandasDataframe(columns=['features'], column_types=[NdArrayType.FLOAT32], column_shapes=[(1, 384)])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:

        def _forward(row: pd.Series) -> np.ndarray:
            data = row
            embedded_list = self.model.encode(data)
            return embedded_list
        ret = pd.DataFrame()
        ret['features'] = df.apply(_forward, axis=1)
        return ret

@setup(cacheable=False, function_type='FeatureExtraction', batchable=False)
def setup(self):
    self.model = SentenceTransformer('all-MiniLM-L6-v2')

def to_device(self, device: str) -> GPUCompatible:
    self.model = self.model.to(device)
    return self

class MnistImageClassifier(PytorchAbstractClassifierFunction):

    @property
    def name(self) -> str:
        return 'MnistImageClassifier'

    def setup(self):
        try_to_import_torch()
        try_to_import_torchvision()
        import torch
        import torch.nn as nn
        model_urls = {'mnist': 'http://ml.cs.tsinghua.edu.cn/~chenxi/pytorch-models/mnist-b07bb66b.pth'}

        class MLP(nn.Module):

            def __init__(self, input_dims, n_hiddens, n_class):
                super(MLP, self).__init__()
                assert isinstance(input_dims, int), 'Please provide int for input_dims'
                self.input_dims = input_dims
                current_dims = input_dims
                layers = OrderedDict()
                if isinstance(n_hiddens, int):
                    n_hiddens = [n_hiddens]
                else:
                    n_hiddens = list(n_hiddens)
                for i, n_hidden in enumerate(n_hiddens):
                    layers['fc{}'.format(i + 1)] = nn.Linear(current_dims, n_hidden)
                    layers['relu{}'.format(i + 1)] = nn.ReLU()
                    layers['drop{}'.format(i + 1)] = nn.Dropout(0.2)
                    current_dims = n_hidden
                layers['out'] = nn.Linear(current_dims, n_class)
                self.model = nn.Sequential(layers)

            def forward(self, input):
                input = input.view(input.size(0), -1)
                assert input.size(1) == self.input_dims
                return self.model.forward(input)

        def mnist(input_dims=784, n_hiddens=[256, 256], n_class=10, pretrained=None):
            model = MLP(input_dims, n_hiddens, n_class)
            import torch.utils.model_zoo as model_zoo
            if pretrained is not None:
                m = model_zoo.load_url(model_urls['mnist'], map_location=torch.device('cpu'))
                state_dict = m.state_dict() if isinstance(m, nn.Module) else m
                assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
                model.load_state_dict(state_dict)
            return model
        self.model = mnist(pretrained=True)
        self.model.eval()

    @property
    def labels(self):
        return list([str(num) for num in range(10)])

    def transform(self, images):
        from PIL import Image
        from torchvision.transforms import Compose, Grayscale, Normalize, ToTensor
        composed = Compose([Grayscale(num_output_channels=1), ToTensor(), Normalize((0.1307,), (0.3081,))])
        return composed(Image.fromarray(images[:, :, ::-1])).unsqueeze(0)

    def forward(self, frames) -> pd.DataFrame:
        outcome = []
        predictions = self.model(frames)
        for prediction in predictions:
            label = self.as_numpy(prediction.data.argmax())
            outcome.append({'label': str(label)})
        return pd.DataFrame(outcome, columns=['label'])

def setup(self):
    try_to_import_torch()
    try_to_import_torchvision()
    import torch
    import torch.nn as nn
    model_urls = {'mnist': 'http://ml.cs.tsinghua.edu.cn/~chenxi/pytorch-models/mnist-b07bb66b.pth'}

    class MLP(nn.Module):

        def __init__(self, input_dims, n_hiddens, n_class):
            super(MLP, self).__init__()
            assert isinstance(input_dims, int), 'Please provide int for input_dims'
            self.input_dims = input_dims
            current_dims = input_dims
            layers = OrderedDict()
            if isinstance(n_hiddens, int):
                n_hiddens = [n_hiddens]
            else:
                n_hiddens = list(n_hiddens)
            for i, n_hidden in enumerate(n_hiddens):
                layers['fc{}'.format(i + 1)] = nn.Linear(current_dims, n_hidden)
                layers['relu{}'.format(i + 1)] = nn.ReLU()
                layers['drop{}'.format(i + 1)] = nn.Dropout(0.2)
                current_dims = n_hidden
            layers['out'] = nn.Linear(current_dims, n_class)
            self.model = nn.Sequential(layers)

        def forward(self, input):
            input = input.view(input.size(0), -1)
            assert input.size(1) == self.input_dims
            return self.model.forward(input)

    def mnist(input_dims=784, n_hiddens=[256, 256], n_class=10, pretrained=None):
        model = MLP(input_dims, n_hiddens, n_class)
        import torch.utils.model_zoo as model_zoo
        if pretrained is not None:
            m = model_zoo.load_url(model_urls['mnist'], map_location=torch.device('cpu'))
            state_dict = m.state_dict() if isinstance(m, nn.Module) else m
            assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
            model.load_state_dict(state_dict)
        return model
    self.model = mnist(pretrained=True)
    self.model.eval()

class MLP(nn.Module):

    def __init__(self, input_dims, n_hiddens, n_class):
        super(MLP, self).__init__()
        assert isinstance(input_dims, int), 'Please provide int for input_dims'
        self.input_dims = input_dims
        current_dims = input_dims
        layers = OrderedDict()
        if isinstance(n_hiddens, int):
            n_hiddens = [n_hiddens]
        else:
            n_hiddens = list(n_hiddens)
        for i, n_hidden in enumerate(n_hiddens):
            layers['fc{}'.format(i + 1)] = nn.Linear(current_dims, n_hidden)
            layers['relu{}'.format(i + 1)] = nn.ReLU()
            layers['drop{}'.format(i + 1)] = nn.Dropout(0.2)
            current_dims = n_hidden
        layers['out'] = nn.Linear(current_dims, n_class)
        self.model = nn.Sequential(layers)

    def forward(self, input):
        input = input.view(input.size(0), -1)
        assert input.size(1) == self.input_dims
        return self.model.forward(input)

def __init__(self, input_dims, n_hiddens, n_class):
    super(MLP, self).__init__()
    assert isinstance(input_dims, int), 'Please provide int for input_dims'
    self.input_dims = input_dims
    current_dims = input_dims
    layers = OrderedDict()
    if isinstance(n_hiddens, int):
        n_hiddens = [n_hiddens]
    else:
        n_hiddens = list(n_hiddens)
    for i, n_hidden in enumerate(n_hiddens):
        layers['fc{}'.format(i + 1)] = nn.Linear(current_dims, n_hidden)
        layers['relu{}'.format(i + 1)] = nn.ReLU()
        layers['drop{}'.format(i + 1)] = nn.Dropout(0.2)
        current_dims = n_hidden
    layers['out'] = nn.Linear(current_dims, n_class)
    self.model = nn.Sequential(layers)

def mnist(input_dims=784, n_hiddens=[256, 256], n_class=10, pretrained=None):
    model = MLP(input_dims, n_hiddens, n_class)
    import torch.utils.model_zoo as model_zoo
    if pretrained is not None:
        m = model_zoo.load_url(model_urls['mnist'], map_location=torch.device('cpu'))
        state_dict = m.state_dict() if isinstance(m, nn.Module) else m
        assert isinstance(state_dict, (dict, OrderedDict)), type(state_dict)
        model.load_state_dict(state_dict)
    return model

def transform(self, images):
    from PIL import Image
    from torchvision.transforms import Compose, Grayscale, Normalize, ToTensor
    composed = Compose([Grayscale(num_output_channels=1), ToTensor(), Normalize((0.1307,), (0.3081,))])
    return composed(Image.fromarray(images[:, :, ::-1])).unsqueeze(0)

def forward(self, frames) -> pd.DataFrame:
    outcome = []
    predictions = self.model(frames)
    for prediction in predictions:
        label = self.as_numpy(prediction.data.argmax())
        outcome.append({'label': str(label)})
    return pd.DataFrame(outcome, columns=['label'])

class EmotionDetector(PytorchAbstractClassifierFunction):
    """
    Arguments:
        threshold (float): Threshold for classifier confidence score
    """

    @property
    def name(self) -> str:
        return 'EmotionDetector'

    def _download_weights(self, weights_url, weights_path):
        import torch
        if not os.path.exists(weights_path):
            torch.hub.download_url_to_file(weights_url, weights_path, hash_prefix=None, progress=True)

    def setup(self, threshold=0.85):
        self.threshold = threshold
        try_to_import_pillow()
        try_to_import_torch()
        try_to_import_torchvision()
        import torch
        import torch.nn.functional as F
        model_url = 'https://www.dropbox.com/s/85b63eahka5r439/emotion_detector.t7?raw=1'
        model_weights_path = torch.hub.get_dir() + '/emotion_detector.t7'
        self._download_weights(model_url, model_weights_path)

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
        self.model = VGG('VGG19')
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_state = torch.load(model_weights_path, map_location=device)
        self.model.load_state_dict(model_state['net'])
        self.model.eval()
        self.cut_size = 44

    def transforms_ed(self, frame):
        """
        Performs augmentation on input frame
        Arguments:
            frame (Tensor): Frame on which augmentation needs
            to be performed
        Returns:
            frame (Tensor): Augmented frame
        """
        from torchvision import transforms
        frame = frame.convert('L')
        frame = transforms.functional.resize(frame, (48, 48))
        frame = transforms.functional.to_tensor(frame)
        return frame

    def transform(self, images: np.ndarray):
        from PIL import Image
        return self.transforms_ed(Image.fromarray(images[:, :, ::-1]))

    @property
    def labels(self) -> List[str]:
        return ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

    def forward(self, frames) -> pd.DataFrame:
        """
        Performs predictions on input frames
        Arguments:
            frames (Tensor): Frames on which predictions need
            to be performed
        Returns:
            outcome (pd.DataFrame): Emotion Predictions for input frames
        """
        outcome = []
        import torch
        import torch.nn.functional as F
        from torchvision import transforms
        frames = frames.repeat(3, 1, 1)
        frames = transforms.functional.ten_crop(frames, self.cut_size)
        frames = torch.stack([crop for crop in frames])
        predictions = self.model(frames)
        predictions = torch.mean(predictions, dim=0)
        score = F.softmax(predictions, dim=0)
        _, predicted = torch.max(predictions.data, 0)
        outcome.append({'labels': self.labels[predicted.item()], 'scores': score.cpu().detach().numpy()[predicted.item()]})
        return pd.DataFrame(outcome, columns=['labels', 'scores'])

def setup(self, threshold=0.85):
    self.threshold = threshold
    try_to_import_pillow()
    try_to_import_torch()
    try_to_import_torchvision()
    import torch
    import torch.nn.functional as F
    model_url = 'https://www.dropbox.com/s/85b63eahka5r439/emotion_detector.t7?raw=1'
    model_weights_path = torch.hub.get_dir() + '/emotion_detector.t7'
    self._download_weights(model_url, model_weights_path)

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
    self.model = VGG('VGG19')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_state = torch.load(model_weights_path, map_location=device)
    self.model.load_state_dict(model_state['net'])
    self.model.eval()
    self.cut_size = 44

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

def transforms_ed(self, frame):
    """
        Performs augmentation on input frame
        Arguments:
            frame (Tensor): Frame on which augmentation needs
            to be performed
        Returns:
            frame (Tensor): Augmented frame
        """
    from torchvision import transforms
    frame = frame.convert('L')
    frame = transforms.functional.resize(frame, (48, 48))
    frame = transforms.functional.to_tensor(frame)
    return frame

def transform(self, images: np.ndarray):
    from PIL import Image
    return self.transforms_ed(Image.fromarray(images[:, :, ::-1]))

def forward(self, frames) -> pd.DataFrame:
    """
        Performs predictions on input frames
        Arguments:
            frames (Tensor): Frames on which predictions need
            to be performed
        Returns:
            outcome (pd.DataFrame): Emotion Predictions for input frames
        """
    outcome = []
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    frames = frames.repeat(3, 1, 1)
    frames = transforms.functional.ten_crop(frames, self.cut_size)
    frames = torch.stack([crop for crop in frames])
    predictions = self.model(frames)
    predictions = torch.mean(predictions, dim=0)
    score = F.softmax(predictions, dim=0)
    _, predicted = torch.max(predictions.data, 0)
    outcome.append({'labels': self.labels[predicted.item()], 'scores': score.cpu().detach().numpy()[predicted.item()]})
    return pd.DataFrame(outcome, columns=['labels', 'scores'])

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

def setup(self, threshold=0.85):
    self.threshold = threshold
    try_to_import_torch()
    try_to_import_torchvision()
    try_to_import_facenet_pytorch()
    from facenet_pytorch import MTCNN
    self.model = MTCNN()

def to_device(self, device: str):
    try_to_import_facenet_pytorch()
    import torch
    from facenet_pytorch import MTCNN
    gpu = 'cuda:{}'.format(device)
    self.model = MTCNN(device=torch.device(gpu))
    return self

class GaussianBlur(AbstractFunction):

    @setup(cacheable=False, function_type='cv2-transformation', batchable=True)
    def setup(self):
        pass

    @property
    def name(self):
        return 'GaussianBlur'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['blurred_frame_array'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, frame: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Gaussian Blur to the frame

         Returns:
             ret (pd.DataFrame): The modified frame.
        """

        def gaussianBlur(row: pd.Series) -> np.ndarray:
            row = row.to_list()
            frame = row[0]
            try_to_import_cv2()
            import cv2
            frame = cv2.GaussianBlur(frame, (5, 5), cv2.BORDER_DEFAULT)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        ret = pd.DataFrame()
        ret['blurred_frame_array'] = frame.apply(gaussianBlur, axis=1)
        return ret

@setup(cacheable=False, function_type='cv2-transformation', batchable=True)
def setup(self):
    pass

def gaussianBlur(row: pd.Series) -> np.ndarray:
    row = row.to_list()
    frame = row[0]
    try_to_import_cv2()
    import cv2
    frame = cv2.GaussianBlur(frame, (5, 5), cv2.BORDER_DEFAULT)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame

class Annotate(AbstractFunction):

    @setup(cacheable=False, function_type='cv2-transformation', batchable=True)
    def setup(self):
        pass

    @property
    def name(self):
        return 'Annotate'

    @forward(input_signatures=[PandasDataframe(columns=['data', 'labels', 'bboxes'], column_types=[NdArrayType.FLOAT32, NdArrayType.STR, NdArrayType.FLOAT32], column_shapes=[(None, None, 3), (None,), (None,)])], output_signatures=[PandasDataframe(columns=['annotated_frame_array'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Modify the frame to annotate the bbox on it.

         Returns:
             ret (pd.DataFrame): The modified frame.
        """

        def annotate(row: pd.Series) -> np.ndarray:
            row = row.to_list()
            frame = row[0]
            bboxes = row[2]
            try_to_import_cv2()
            import cv2
            for bbox in bboxes:
                x1, y1, x2, y2 = np.asarray(bbox, dtype='int')
                x1, y1, x2, y2 = (int(x1), int(y1), int(x2), int(y2))
                frame = cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            return frame
        ret = pd.DataFrame()
        ret['annotated_frame_array'] = df.apply(annotate, axis=1)
        return ret

@setup(cacheable=False, function_type='cv2-transformation', batchable=True)
def setup(self):
    pass

def annotate(row: pd.Series) -> np.ndarray:
    row = row.to_list()
    frame = row[0]
    bboxes = row[2]
    try_to_import_cv2()
    import cv2
    for bbox in bboxes:
        x1, y1, x2, y2 = np.asarray(bbox, dtype='int')
        x1, y1, x2, y2 = (int(x1), int(y1), int(x2), int(y2))
        frame = cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    return frame

class Crop(AbstractFunction):

    def setup(self):
        pass

    @property
    def name(self):
        return 'Crop'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Crop the frame given the bbox - Crop(frame, bbox)
        If one of the side of the crop box is 0, it automatically sets it to 1 pixel

        Returns:
            ret (pd.DataFrame): The cropped frame.
        """

        def crop(row: pd.Series) -> np.ndarray:
            row = row.to_list()
            frame = row[0]
            bboxes = row[1]
            x0, y0, x1, y1 = np.asarray(bboxes, dtype='int')
            x0 = max(0, x0)
            y0 = max(0, y0)
            if x1 == x0:
                x1 = x0 + 1
            if y1 == y0:
                y1 = y0 + 1
            return frame[y0:y1, x0:x1]
        ret = pd.DataFrame()
        ret['cropped_frame_array'] = df.apply(crop, axis=1)
        return ret

def crop(row: pd.Series) -> np.ndarray:
    row = row.to_list()
    frame = row[0]
    bboxes = row[1]
    x0, y0, x1, y1 = np.asarray(bboxes, dtype='int')
    x0 = max(0, x0)
    y0 = max(0, y0)
    if x1 == x0:
        x1 = x0 + 1
    if y1 == y0:
        y1 = y0 + 1
    return frame[y0:y1, x0:x1]

class VerticalFlip(AbstractFunction):

    @setup(cacheable=False, function_type='cv2-transformation', batchable=True)
    def setup(self):
        try_to_import_cv2()

    @property
    def name(self):
        return 'VerticalFlip'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['vertically_flipped_frame_array'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, frame: pd.DataFrame) -> pd.DataFrame:
        """
        Apply vertical flip to the frame

         Returns:
             ret (pd.DataFrame): The modified frame.
        """

        def verticalFlip(row: pd.Series) -> np.ndarray:
            row = row.to_list()
            frame = row[0]
            try_to_import_cv2()
            import cv2
            frame = cv2.flip(frame, 0)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        ret = pd.DataFrame()
        ret['vertically_flipped_frame_array'] = frame.apply(verticalFlip, axis=1)
        return ret

@setup(cacheable=False, function_type='cv2-transformation', batchable=True)
def setup(self):
    try_to_import_cv2()

def verticalFlip(row: pd.Series) -> np.ndarray:
    row = row.to_list()
    frame = row[0]
    try_to_import_cv2()
    import cv2
    frame = cv2.flip(frame, 0)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame

class HorizontalFlip(AbstractFunction):

    @setup(cacheable=False, function_type='cv2-transformation', batchable=True)
    def setup(self):
        try_to_import_cv2()

    @property
    def name(self):
        return 'HorizontalFlip'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['horizontally_flipped_frame_array'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, frame: pd.DataFrame) -> pd.DataFrame:
        """
        Apply horizontal flip to the frame

         Returns:
             ret (pd.DataFrame): The modified frame.
        """

        def horizontalFlip(row: pd.Series) -> np.ndarray:
            row = row.to_list()
            frame = row[0]
            try_to_import_cv2()
            import cv2
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        ret = pd.DataFrame()
        ret['horizontally_flipped_frame_array'] = frame.apply(horizontalFlip, axis=1)
        return ret

@setup(cacheable=False, function_type='cv2-transformation', batchable=True)
def setup(self):
    try_to_import_cv2()

def horizontalFlip(row: pd.Series) -> np.ndarray:
    row = row.to_list()
    frame = row[0]
    try_to_import_cv2()
    import cv2
    frame = cv2.flip(frame, 1)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame

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

class ToGrayscale(AbstractFunction):

    @setup(cacheable=False, function_type='cv2-transformation', batchable=True)
    def setup(self):
        try_to_import_cv2()

    @property
    def name(self):
        return 'ToGrayscale'

    @forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])], output_signatures=[PandasDataframe(columns=['grayscale_frame_array'], column_types=[NdArrayType.FLOAT32], column_shapes=[(None, None, 3)])])
    def forward(self, frame: pd.DataFrame) -> pd.DataFrame:
        """
        Convert the frame from BGR to grayscale

         Returns:
             ret (pd.DataFrame): The modified frame.
        """

        def toGrayscale(row: pd.Series) -> np.ndarray:
            row = row.to_list()
            frame = row[0]
            import cv2
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            return frame
        ret = pd.DataFrame()
        ret['grayscale_frame_array'] = frame.apply(toGrayscale, axis=1)
        return ret

@setup(cacheable=False, function_type='cv2-transformation', batchable=True)
def setup(self):
    try_to_import_cv2()

def toGrayscale(row: pd.Series) -> np.ndarray:
    row = row.to_list()
    frame = row[0]
    import cv2
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    return frame

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

@setup(cacheable=False, function_type='object_tracker', batchable=False)
def setup(self, *args, **kwargs):
    super().setup(*args, **kwargs)

class PytorchAbstractClassifierFunction(AbstractClassifierFunction, nn.Module, GPUCompatible):
    """
    A pytorch based classifier. Used to make sure we make maximum
    utilization of features provided by pytorch without reinventing the wheel.
    """

    def __init__(self, *args, **kwargs):
        self.transforms = [transforms.ToTensor()]
        nn.Module.__init__(self, *args, **kwargs)
        self.setup(*args, **kwargs)

    def get_device(self):
        return next(self.parameters()).device

    def transform(self, images: np.ndarray):
        composed = Compose(self.transforms)
        return composed(Image.fromarray(images)).unsqueeze(0)

    def __call__(self, *args, **kwargs) -> pd.DataFrame:
        """
        This method transforms the list of frames by
        running pytorch transforms then splits them into batches.

        Arguments:
            frames: List of input frames

        Returns:
            DataFrame with features key and associated frame
        """
        frames = args[0]
        if isinstance(frames, pd.DataFrame):
            frames = frames.transpose().values.tolist()[0]
        gpu_batch_size = 1
        import torch
        tens_batch = torch.cat([self.transform(x) for x in frames]).to(self.get_device())
        if gpu_batch_size:
            chunks = torch.split(tens_batch, gpu_batch_size)
            outcome = pd.DataFrame()
            for tensor in chunks:
                outcome = pd.concat([outcome, self.forward(tensor)], ignore_index=True)
            return outcome
        else:
            return self.forward(frames)

    def as_numpy(self, val) -> np.ndarray:
        """
        Given a tensor in GPU, detach and get the numpy output
        Arguments:
             val (Tensor): tensor to be converted
        Returns:
            np.ndarray: numpy array representation
        """
        return val.detach().cpu().numpy()

    def to_device(self, device: str) -> GPUCompatible:
        """
        Required to make class a member of GPUCompatible Protocol.
        """
        import torch
        return self.to(torch.device('cuda:{}'.format(device)))

def __init__(self, *args, **kwargs):
    self.transforms = [transforms.ToTensor()]
    nn.Module.__init__(self, *args, **kwargs)
    self.setup(*args, **kwargs)

def get_device(self):
    return next(self.parameters()).device

def transform(self, images: np.ndarray):
    composed = Compose(self.transforms)
    return composed(Image.fromarray(images)).unsqueeze(0)

def as_numpy(self, val) -> np.ndarray:
    """
        Given a tensor in GPU, detach and get the numpy output
        Arguments:
             val (Tensor): tensor to be converted
        Returns:
            np.ndarray: numpy array representation
        """
    return val.detach().cpu().numpy()

def to_device(self, device: str) -> GPUCompatible:
    """
        Required to make class a member of GPUCompatible Protocol.
        """
    import torch
    return self.to(torch.device('cuda:{}'.format(device)))

class AbstractFunction(metaclass=ABCMeta):
    """
    Abstract class for Functions. All the Functions in EvaDB will inherit from this.

    Load and initialize the machine learning model in the __init__.

    """

    def __init__(self, *args, **kwargs):
        self.setup(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.forward(args[0])

    def __str__(self):
        return self.name
    'Abstract Methods all Functions must implement. '

    @abstractmethod
    def setup(self, *args, **kwargs) -> None:
        """
        Do necessary setup in here. Gets called automatically on initialization.
        """
        pass

    @abstractmethod
    def forward(self, frames: InputType) -> InputType:
        """
        Implement function function call by overriding this function.
        Gets called automatically by __call__.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

def __init__(self, *args, **kwargs):
    self.setup(*args, **kwargs)

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

def setup(self, *args, **kwargs) -> None:
    super().setup(*args, **kwargs)

