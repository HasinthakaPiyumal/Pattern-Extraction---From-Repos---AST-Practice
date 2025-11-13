# Cluster 10

def create_dataframe(num_frames=1) -> pd.DataFrame:
    frames = []
    for i in range(1, num_frames + 1):
        frames.append({'id': i, 'data': i * np.ones((1, 1))})
    return pd.DataFrame(frames)

def create_dataframe_same(times=1):
    base_df = create_dataframe()
    for i in range(1, times):
        base_df = pd.concat([base_df, create_dataframe()], ignore_index=True)
    return base_df

def convert_bbox(bbox):
    return np.array([np.float32(coord) for coord in bbox.split(',')])

def create_dummy_batches(num_frames=NUM_FRAMES, filters=[], batch_size=10, start_id=0, video_dir=None, is_from_storage=False):
    video_dir = video_dir or get_tmp_dir()
    if not filters:
        filters = range(num_frames)
    data = []
    for i in filters:
        data.append({'myvideo._row_id': 1, 'myvideo.name': os.path.join(video_dir, 'dummy.avi'), 'myvideo.id': i + start_id, 'myvideo.data': np.array(np.ones((FRAME_SIZE[1], FRAME_SIZE[0], 3)) * i, dtype=np.uint8), 'myvideo.seconds': np.float32(i / num_frames)})
        if is_from_storage:
            data[-1]['myvideo._row_number'] = i + start_id
        if len(data) % batch_size == 0:
            yield Batch(pd.DataFrame(data))
            data = []
    if data:
        yield Batch(pd.DataFrame(data))

def create_dummy_4d_batches(num_frames=NUM_FRAMES, filters=[], batch_size=10, start_id=0):
    if not filters:
        filters = range(num_frames)
    data = []
    for segment in filters:
        segment_data = []
        for i in segment:
            segment_data.append(np.ones((FRAME_SIZE[1], FRAME_SIZE[0], 3)) * i)
        segment_data = np.stack(np.array(segment_data, dtype=np.uint8))
        data.append({'myvideo.name': 'dummy.avi', 'myvideo.id': segment[0] + start_id, 'myvideo.data': segment_data, 'myvideo.seconds': np.float32(i / num_frames)})
        if len(data) % batch_size == 0:
            df = pd.DataFrame(data)
            df = df.astype({'myvideo.id': np.intp})
            yield Batch(df)
            data = []
    if data:
        df = pd.DataFrame(data)
        df = df.astype({'myvideo.id': np.intp})
        yield Batch(df)

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

def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    ret = pd.DataFrame()
    ret['label'] = df.apply(self.classify_one, axis=1)
    return ret

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

def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    ret = pd.DataFrame()
    ret['labels'] = df.apply(self.classify_one, axis=1)
    return ret

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

def forward(self, df: pd.DataFrame) -> pd.DataFrame:

    def _extract_feature(row: pd.Series):
        feat_input = row[0]
        feat_input = feat_input.reshape(1, -1)
        feat_input = feat_input.astype(np.float32)
        return feat_input
    ret = pd.DataFrame()
    ret['features'] = df.apply(_extract_feature, axis=1)
    return ret

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

@decorators.forward(input_signatures=[PandasDataframe(columns=['Frame_Array'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256)])], output_signatures=[NumpyArray(name='label', type=NdArrayType.STR)])
def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    ret = pd.DataFrame()
    ret['label'] = df.apply(self.classify_one, axis=1)
    return ret

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

@decorators.forward(input_signatures=[], output_signatures=[PandasDataframe(columns=['label'], column_types=[NdArrayType.STR], column_shapes=[(None,)])])
def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    ret = pd.DataFrame([{'label': 'DummyNoInputFunction'}])
    return ret

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

@pytest.mark.notparallel
class LoadExecutorTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()
        self.image_files_path = Path(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/*.jpg')
        self.csv_file_path = create_sample_csv()

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')
        file_remove('dummy.csv')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

    def test_should_load_video_in_table(self):
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        select_query = 'SELECT * FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches())[0]
        self.assertEqual(actual_batch, expected_batch)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_should_form_symlink_to_individual_video(self):
        catalog_manager = self.evadb.catalog()
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        table_catalog_entry = catalog_manager.get_table_catalog_entry('MyVideo')
        video_dir = table_catalog_entry.file_url
        self.assertEqual(len(os.listdir(video_dir)), 1)
        video_file = os.listdir(video_dir)[0]
        video_file_path = os.path.join(video_dir, video_file)
        self.assertTrue(os.path.islink(video_file_path))
        self.assertEqual(os.readlink(video_file_path), str(Path(self.video_file_path).resolve()))
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_should_raise_error_on_removing_symlinked_file(self):
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        select_query = 'SELECT * FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches())[0]
        self.assertEqual(actual_batch, expected_batch)
        file_remove('dummy.avi')
        with self.assertRaises(ExecutorError) as e:
            execute_query_fetch_all(self.evadb, select_query, do_not_print_exceptions=True)
        self.assertEqual(str(e.exception), 'The dataset file could not be found. Please verify that the file exists in the specified path.')
        create_sample_video()

    def test_should_form_symlink_to_multiple_videos(self):
        catalog_manager = self.evadb.catalog()
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        execute_query_fetch_all(self.evadb, query)
        table_catalog_entry = catalog_manager.get_table_catalog_entry('MyVideos')
        video_dir = table_catalog_entry.file_url
        self.assertEqual(len(os.listdir(video_dir)), 2)
        video_files = os.listdir(video_dir)
        for video_file in video_files:
            video_file_path = os.path.join(video_dir, video_file)
            self.assertTrue(os.path.islink(video_file_path))
            self.assertTrue(os.readlink(video_file_path).startswith(f'{EvaDB_ROOT_DIR}/data/sample_videos/1'))

    def test_should_load_videos_with_same_name_but_different_path(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/**/*.mp4'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        result = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 4']))
        self.assertEqual(result, expected)

    def test_should_fail_to_load_videos_with_same_path(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/2/*.mp4'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        result = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 1']))
        self.assertEqual(result, expected)
        expected_output = execute_query_fetch_all(self.evadb, 'SELECT id FROM MyVideos;')
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/**/*.mp4'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        after_load_fail = execute_query_fetch_all(self.evadb, 'SELECT id FROM MyVideos;')
        self.assertEqual(expected_output, after_load_fail)

    def test_should_fail_to_load_missing_video(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/missing.mp4'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        with self.assertRaises(ExecutorError) as exc_info:
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        self.assertIn('Load VIDEO failed', str(exc_info.exception))

    def test_should_fail_to_load_corrupt_video(self):
        tempfile_name = os.urandom(24).hex()
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
        with open(tempfile_path, 'wb') as tmp:
            query = f'LOAD VIDEO "{tmp.name}" INTO MyVideos;'
            with self.assertRaises(Exception):
                execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)

    def test_should_fail_to_load_invalid_files_as_video(self):
        path = f'{EvaDB_ROOT_DIR}/data/README.md'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        with self.assertRaises(BinderError):
            execute_query_fetch_all(self.evadb, 'SELECT name FROM MyVideos', do_not_print_exceptions=True)

    def test_should_rollback_or_skip_if_video_load_fails(self):
        path_regex = Path(f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4')
        valid_videos = glob.glob(str(path_regex.expanduser()), recursive=True)
        tempfile_name = os.urandom(24).hex()
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
        with open(tempfile_path, 'wb') as empty_file:
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD VIDEO "{path}" INTO MyVideos;'
                with self.assertRaises(Exception):
                    execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
                with self.assertRaises(BinderError):
                    execute_query_fetch_all(self.evadb, 'SELECT name FROM MyVideos', do_not_print_exceptions=True)
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(valid_videos[0]), tmp_dir)
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD VIDEO "{path}" INTO MyVideos;'
                result = execute_query_fetch_all(self.evadb, query)
                expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 1']))
                self.assertEqual(result, expected)
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(valid_videos[0]), tmp_dir)
                shutil.copy2(str(valid_videos[1]), tmp_dir)
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD VIDEO "{path}" INTO MyVideos;'
                result = execute_query_fetch_all(self.evadb, query)
                expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 2']))
                self.assertEqual(result, expected)

    def test_should_rollback_and_preserve_previous_state(self):
        path_regex = Path(f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4')
        valid_videos = glob.glob(str(path_regex.expanduser()), recursive=True)
        load_file = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/1.mp4'
        execute_query_fetch_all(self.evadb, f'LOAD VIDEO "{load_file}" INTO MyVideos;')
        tempfile_name = os.urandom(24).hex()
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
        with open(tempfile_path, 'wb') as empty_file:
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD VIDEO "{path}" INTO MyVideos;'
                with self.assertRaises(Exception):
                    execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
                result = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyVideos')
                file_names = np.unique(result.frames)
                self.assertEqual(len(file_names), 1)
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(valid_videos[1]), tmp_dir)
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD VIDEO "{path}" INTO MyVideos;'
                result = execute_query_fetch_all(self.evadb, query)
                expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 1']))
                self.assertEqual(result, expected)
                result = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyVideos')
                file_names = np.unique(result.frames)
                self.assertEqual(len(file_names), 2)

    def test_should_fail_to_load_missing_image(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_images/missing.jpg'
        query = f'LOAD IMAGE "{path}" INTO MyImages;'
        with self.assertRaises(ExecutorError) as exc_info:
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        self.assertIn('Load IMAGE failed', str(exc_info.exception))

    def test_should_fail_to_load_images_with_same_path(self):
        image_files = glob.glob(os.path.expanduser(self.image_files_path), recursive=True)
        query = f'LOAD IMAGE "{image_files[0]}" INTO MyImages;'
        result = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: 1']))
        self.assertEqual(result, expected)
        expected_output = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;')
        query = f'LOAD IMAGE "{image_files[0]}" INTO MyImages;'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        after_load_fail = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;')
        self.assertEqual(expected_output, after_load_fail)

    def test_should_fail_to_load_corrupt_image(self):
        tempfile_name = os.urandom(24).hex()
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
        with open(tempfile_path, 'wb') as tmp:
            query = f'LOAD IMAGE "{tmp.name}" INTO MyImages;'
            with self.assertRaises(Exception):
                execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)

    def test_should_fail_to_load_invalid_files_as_image(self):
        path = f'{EvaDB_ROOT_DIR}/data/README.md'
        query = f'LOAD IMAGE "{path}" INTO MyImages;'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
        with self.assertRaises(BinderError):
            execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;', do_not_print_exceptions=True)

    def test_should_rollback_or_pass_if_image_load_fails(self):
        valid_images = glob.glob(str(self.image_files_path.expanduser()), recursive=True)
        tempfile_name = os.urandom(24).hex()
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
        with open(tempfile_path, 'wb') as empty_file:
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD IMAGE "{path}" INTO MyImages;'
                with self.assertRaises(Exception):
                    execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
                with self.assertRaises(BinderError):
                    execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;', do_not_print_exceptions=True)
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(valid_images[0]), tmp_dir)
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD IMAGE "{path}" INTO MyImages;'
                result = execute_query_fetch_all(self.evadb, query)
                expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: 1']))
                self.assertEqual(result, expected)
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(valid_images[0]), tmp_dir)
                shutil.copy2(str(valid_images[1]), tmp_dir)
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD IMAGE "{path}" INTO MyImages;'
                result = execute_query_fetch_all(self.evadb, query)
                expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: 2']))
                self.assertEqual(result, expected)

    def test_should_rollback_or_pass_and_preserve_previous_state_for_load_images(self):
        valid_images = glob.glob(str(self.image_files_path.expanduser()), recursive=True)
        execute_query_fetch_all(self.evadb, f'LOAD IMAGE "{valid_images[0]}" INTO MyImages;')
        tempfile_name = os.urandom(24).hex()
        tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
        with open(tempfile_path, 'wb') as empty_file:
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD IMAGE "{path}" INTO MyImages;'
                with self.assertRaises(Exception):
                    execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
                result = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages')
                self.assertEqual(len(result), 1)
                expected = Batch(pd.DataFrame([{'myimages.name': valid_images[0]}]))
                self.assertEqual(expected, result)
            with tempfile.TemporaryDirectory() as tmp_dir:
                shutil.copy2(str(valid_images[1]), tmp_dir)
                shutil.copy2(str(empty_file.name), tmp_dir)
                path = Path(tmp_dir) / '*'
                query = f'LOAD IMAGE "{path}" INTO MyImages;'
                result = execute_query_fetch_all(self.evadb, query)
                expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: 1']))
                self.assertEqual(result, expected)
                result = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages')
                self.assertEqual(len(result), 2)
                expected = Batch(pd.DataFrame([{'myimages.name': valid_images[0]}, {'myimages.name': os.path.join(tmp_dir, os.path.basename(valid_images[1]))}]))
                self.assertEqual(expected, result)

    def test_should_load_csv_with_columns_in_table(self):
        create_table_query = '\n\n            CREATE TABLE IF NOT EXISTS MyVideoCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER NOT NULL,\n                video_id INTEGER NOT NULL,\n                dataset_name TEXT(30) NOT NULL\n            );\n            '
        execute_query_fetch_all(self.evadb, create_table_query)
        load_query = "LOAD CSV '{}' INTO MyVideoCSV (id, frame_id, video_id, dataset_name);".format(self.csv_file_path)
        execute_query_fetch_all(self.evadb, load_query)
        select_query = 'SELECT id, frame_id, video_id, dataset_name\n                          FROM MyVideoCSV;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        select_columns = ['id', 'frame_id', 'video_id', 'dataset_name']
        expected_batch = next(create_dummy_csv_batches(target_columns=select_columns))
        expected_batch.modify_column_alias('myvideocsv')
        self.assertEqual(actual_batch, expected_batch)
        drop_query = 'DROP TABLE IF EXISTS MyVideoCSV;'
        execute_query_fetch_all(self.evadb, drop_query)

    def test_should_use_parallel_load(self):
        large_scale_image_files_path = create_large_scale_image_dataset(mp.cpu_count() * 10)
        load_query = f"LOAD IMAGE '{large_scale_image_files_path}/**/*.jpg' INTO MyLargeScaleImages;"
        execute_query_fetch_all(self.evadb, load_query)
        drop_query = 'DROP TABLE IF EXISTS MyLargeScaleImages;'
        execute_query_fetch_all(self.evadb, drop_query)
        shutil.rmtree(large_scale_image_files_path)

    def test_parallel_load_should_raise_exception_or_pass(self):
        large_scale_image_files_path = create_large_scale_image_dataset(mp.cpu_count() * 10)
        with open(os.path.join(large_scale_image_files_path, 'img0.jpg'), 'w') as f:
            f.write('aa')
        load_query = f"LOAD IMAGE '{large_scale_image_files_path}/**/*.jpg' INTO MyLargeScaleImages;"
        result = execute_query_fetch_all(self.evadb, load_query)
        file_count = len([entry for entry in os.listdir(large_scale_image_files_path) if os.path.isfile(os.path.join(large_scale_image_files_path, entry))])
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: {file_count - 1}']))
        self.assertEqual(result, expected)
        drop_query = 'DROP TABLE IF EXISTS MyLargeScaleImages;'
        execute_query_fetch_all(self.evadb, drop_query)
        shutil.rmtree(large_scale_image_files_path)

    def test_load_pdfs(self):
        execute_query_fetch_all(self.evadb, f"LOAD DOCUMENT '{EvaDB_ROOT_DIR}/data/documents/*.pdf' INTO pdfs;")
        result = execute_query_fetch_all(self.evadb, 'SELECT * from pdfs;')
        self.assertEqual(len(result.columns), 4)
        self.assertEqual(len(result), 26)

    def test_load_query_incorrect_fileFormat(self):
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, f"LOAD document '{EvaDB_ROOT_DIR}/data/documents/*.pdf' INTO pdfs;")

def test_should_load_videos_with_same_name_but_different_path(self):
    path = f'{EvaDB_ROOT_DIR}/data/sample_videos/**/*.mp4'
    query = f'LOAD VIDEO "{path}" INTO MyVideos;'
    result = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 4']))
    self.assertEqual(result, expected)

def test_should_fail_to_load_videos_with_same_path(self):
    path = f'{EvaDB_ROOT_DIR}/data/sample_videos/2/*.mp4'
    query = f'LOAD VIDEO "{path}" INTO MyVideos;'
    result = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 1']))
    self.assertEqual(result, expected)
    expected_output = execute_query_fetch_all(self.evadb, 'SELECT id FROM MyVideos;')
    path = f'{EvaDB_ROOT_DIR}/data/sample_videos/**/*.mp4'
    query = f'LOAD VIDEO "{path}" INTO MyVideos;'
    with self.assertRaises(ExecutorError):
        execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
    after_load_fail = execute_query_fetch_all(self.evadb, 'SELECT id FROM MyVideos;')
    self.assertEqual(expected_output, after_load_fail)

def test_should_fail_to_load_images_with_same_path(self):
    image_files = glob.glob(os.path.expanduser(self.image_files_path), recursive=True)
    query = f'LOAD IMAGE "{image_files[0]}" INTO MyImages;'
    result = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: 1']))
    self.assertEqual(result, expected)
    expected_output = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;')
    query = f'LOAD IMAGE "{image_files[0]}" INTO MyImages;'
    with self.assertRaises(Exception):
        execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
    after_load_fail = execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;')
    self.assertEqual(expected_output, after_load_fail)

@pytest.mark.notparallel
class SimilarityTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        load_functions_for_testing(self.evadb, mode='debug')
        self.img_path = create_sample_image()
        create_table_query = 'CREATE TABLE IF NOT EXISTS testSimilarityTable\n                                  (data_col NDARRAY UINT8(3, ANYDIM, ANYDIM),\n                                   dummy INTEGER);'
        execute_query_fetch_all(self.evadb, create_table_query)
        create_table_query = 'CREATE TABLE IF NOT EXISTS testSimilarityFeatureTable\n                                  (feature_col NDARRAY FLOAT32(1, ANYDIM),\n                                   dummy INTEGER);'
        execute_query_fetch_all(self.evadb, create_table_query)
        base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
        base_img[0] -= 1
        base_img[2] += 1
        base_img += 4
        base_table_catalog_entry = self.evadb.catalog().get_table_catalog_entry('testSimilarityTable')
        feature_table_catalog_entry = self.evadb.catalog().get_table_catalog_entry('testSimilarityFeatureTable')
        self.img_path_list = []
        storage_engine = StorageEngine.factory(self.evadb, base_table_catalog_entry)
        for i in range(5):
            storage_engine.write(base_table_catalog_entry, Batch(pd.DataFrame([{'data_col': base_img, 'dummy': i}])))
            storage_engine.write(feature_table_catalog_entry, Batch(pd.DataFrame([{'feature_col': base_img.astype(np.float32).reshape(1, -1), 'dummy': i}])))
            img_save_path = os.path.join(self.evadb.catalog().get_configuration_catalog_value('tmp_dir'), f'test_similar_img{i}.jpg')
            try_to_import_cv2()
            import cv2
            cv2.imwrite(img_save_path, base_img)
            load_image_query = f"LOAD IMAGE '{img_save_path}' INTO testSimilarityImageDataset;"
            execute_query_fetch_all(self.evadb, load_image_query)
            self.img_path_list.append(img_save_path)
            base_img -= 1
        self.original_pinecone_key = os.environ.get('PINECONE_API_KEY')
        self.original_pinecone_env = os.environ.get('PINECONE_ENV')
        os.environ['PINECONE_API_KEY'] = '657e4fae-7208-4555-b0f2-9847dfa5b818'
        os.environ['PINECONE_ENV'] = 'gcp-starter'
        self.original_milvus_uri = os.environ.get('MILVUS_URI')
        self.original_milvus_db_name = os.environ.get('MILVUS_DB_NAME')
        os.environ['MILVUS_URI'] = 'http://localhost:19530'
        os.environ['MILVUS_DB_NAME'] = 'default'
        self.original_weaviate_key = os.environ.get('WEAVIATE_API_KEY')
        self.original_weaviate_env = os.environ.get('WEAVIATE_API_URL')
        os.environ['WEAVIATE_API_KEY'] = 'NM4adxLmhtJDF1dPXDiNhEGTN7hhGDpymmO0'
        os.environ['WEAVIATE_API_URL'] = 'https://cs6422-test2-zn83syib.weaviate.network'

    def tearDown(self):
        shutdown_ray()
        drop_table_query = 'DROP TABLE testSimilarityTable;'
        execute_query_fetch_all(self.evadb, drop_table_query)
        drop_table_query = 'DROP TABLE testSimilarityFeatureTable;'
        execute_query_fetch_all(self.evadb, drop_table_query)
        drop_table_query = 'DROP TABLE IF EXISTS testSimilarityImageDataset;'
        execute_query_fetch_all(self.evadb, drop_table_query)
        if self.original_pinecone_key:
            os.environ['PINECONE_API_KEY'] = self.original_pinecone_key
        else:
            del os.environ['PINECONE_API_KEY']
        if self.original_pinecone_env:
            os.environ['PINECONE_ENV'] = self.original_pinecone_env
        else:
            del os.environ['PINECONE_ENV']
        if self.original_milvus_uri:
            os.environ['MILVUS_URI'] = self.original_milvus_uri
        else:
            del os.environ['MILVUS_URI']
        if self.original_milvus_db_name:
            os.environ['MILVUS_DB_NAME'] = self.original_milvus_db_name
        else:
            del os.environ['MILVUS_DB_NAME']

    def test_similarity_should_work_in_order(self):
        select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 1;'.format(self.img_path)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
        base_img[0] -= 1
        base_img[2] += 1
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
        self.assertTrue(np.array_equal(actual_open, base_img))
        select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 2;'.format(self.img_path)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
        self.assertTrue(np.array_equal(actual_open, base_img))
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[1]
        self.assertTrue(np.array_equal(actual_open, base_img + 1))
        select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col)) DESC\n                            LIMIT 2;'.format(self.img_path)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
        self.assertTrue(np.array_equal(actual_open, base_img + 4))
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[1]
        self.assertTrue(np.array_equal(actual_open, base_img + 3))
        select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 1;'.format(self.img_path)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
        base_img[0] -= 1
        base_img[2] += 1
        base_img = base_img.astype(np.float32).reshape(1, -1)
        actual_open = actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[0]
        self.assertTrue(np.array_equal(actual_open, base_img))
        select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 2;'.format(self.img_path)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_open = actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[0]
        self.assertTrue(np.array_equal(actual_open, base_img))
        actual_open = actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[1]
        self.assertTrue(np.array_equal(actual_open, base_img + 1))

    def test_should_do_vector_index_scan(self):
        select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 3;'.format(self.img_path)
        expected_batch = execute_query_fetch_all(self.evadb, select_query)
        create_index_query = 'CREATE INDEX testFaissIndexScanRewrite1\n                                    ON testSimilarityFeatureTable (feature_col)\n                                    USING FAISS;'
        execute_query_fetch_all(self.evadb, create_index_query)
        select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 3;'.format(self.img_path)
        explain_query = 'EXPLAIN {}'.format(select_query)
        explain_batch = execute_query_fetch_all(self.evadb, explain_query)
        self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 3)
        for i in range(3):
            self.assertTrue(np.array_equal(expected_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[i], actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[i]))
        select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 3;'.format(self.img_path)
        expected_batch = execute_query_fetch_all(self.evadb, select_query)
        create_index_query = 'CREATE INDEX testFaissIndexScanRewrite2\n                                    ON testSimilarityTable (DummyFeatureExtractor(data_col))\n                                    USING FAISS;'
        execute_query_fetch_all(self.evadb, create_index_query)
        select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 3;'.format(self.img_path)
        explain_query = 'EXPLAIN {}'.format(select_query)
        explain_batch = execute_query_fetch_all(self.evadb, explain_query)
        self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 3)
        for i in range(3):
            self.assertTrue(np.array_equal(expected_batch.frames['testsimilaritytable.data_col'].to_numpy()[i], actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[i]))
        drop_query = 'DROP INDEX testFaissIndexScanRewrite1'
        execute_query_fetch_all(self.evadb, drop_query)
        drop_query = 'DROP INDEX testFaissIndexScanRewrite2'
        execute_query_fetch_all(self.evadb, drop_query)

    def test_should_not_do_vector_index_scan_with_desc_order(self):
        create_index_query = 'CREATE INDEX testFaissIndexScanRewrite\n                                    ON testSimilarityTable (DummyFeatureExtractor(data_col))\n                                    USING FAISS;'
        execute_query_fetch_all(self.evadb, create_index_query)
        explain_query = '\n            EXPLAIN\n                SELECT data_col FROM testSimilarityTable WHERE dummy = 0\n                  ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                  LIMIT 3;\n        '.format('dummypath')
        batch = execute_query_fetch_all(self.evadb, explain_query)
        self.assertFalse('FaissIndexScan' in batch.frames[0][0])
        base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
        base_img[0] -= 1
        base_img[2] += 1
        select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col)) DESC\n                            LIMIT 2;'.format(self.img_path)
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
        self.assertTrue(np.array_equal(actual_open, base_img + 4))
        actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[1]
        self.assertTrue(np.array_equal(actual_open, base_img + 3))
        drop_query = 'DROP INDEX testFaissIndexScanRewrite'
        execute_query_fetch_all(self.evadb, drop_query)

    def test_should_not_do_vector_index_scan_with_predicate(self):
        create_index_query = 'CREATE INDEX testFaissIndexScanRewrite\n                                    ON testSimilarityTable (DummyFeatureExtractor(data_col))\n                                    USING FAISS;'
        execute_query_fetch_all(self.evadb, create_index_query)
        explain_query = '\n            EXPLAIN\n                SELECT data_col FROM testSimilarityTable WHERE dummy = 0\n                  ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                  LIMIT 3;\n        '.format('dummypath')
        batch = execute_query_fetch_all(self.evadb, explain_query)
        self.assertFalse('FaissIndexScan' in batch.frames[0][0])
        drop_query = 'DROP INDEX testFaissIndexScanRewrite'
        execute_query_fetch_all(self.evadb, drop_query)

    def test_end_to_end_index_scan_should_work_correctly_on_image_dataset_faiss(self):
        for _ in range(2):
            create_index_query = 'CREATE INDEX testFaissIndexImageDataset\n                                        ON testSimilarityImageDataset (DummyFeatureExtractor(data))\n                                        USING FAISS;'
            execute_query_fetch_all(self.evadb, create_index_query)
            select_query = 'SELECT _row_id FROM testSimilarityImageDataset\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data))\n                                LIMIT 1;'.format(self.img_path)
            explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
            self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
            res_batch = execute_query_fetch_all(self.evadb, select_query)
            self.assertEqual(res_batch.frames['testsimilarityimagedataset._row_id'][0], 5)
            drop_query = 'DROP INDEX testFaissIndexImageDataset'
            execute_query_fetch_all(self.evadb, drop_query)

    def _helper_for_auto_update_during_insertion_with_faiss(self, if_exists: bool):
        for i, img_path in enumerate(self.img_path_list):
            insert_query = f"INSERT INTO testIndexAutoUpdate (img_path) VALUES ('{img_path}')"
            execute_query_fetch_all(self.evadb, insert_query)
            if i == 0:
                if_exists_str = 'IF NOT EXISTS ' if if_exists else ''
                create_index_query = f'CREATE INDEX {if_exists_str}testIndex ON testIndexAutoUpdate(DummyFeatureExtractor(Open(img_path))) USING FAISS'
                execute_query_fetch_all(self.evadb, create_index_query)
        select_query = 'SELECT _row_id FROM testIndexAutoUpdate\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(Open(img_path)))\n                                LIMIT 1;'.format(self.img_path)
        explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
        self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
        res_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(res_batch.frames['testindexautoupdate._row_id'][0], 5)

    def test_index_auto_update_on_structured_table_during_insertion_with_faiss(self):
        create_query = 'CREATE TABLE testIndexAutoUpdate (img_path TEXT(100))'
        drop_query = 'DROP TABLE testIndexAutoUpdate'
        execute_query_fetch_all(self.evadb, create_query)
        self._helper_for_auto_update_during_insertion_with_faiss(False)
        execute_query_fetch_all(self.evadb, drop_query)
        execute_query_fetch_all(self.evadb, create_query)
        self._helper_for_auto_update_during_insertion_with_faiss(True)

    @qdrant_skip_marker
    def test_end_to_end_index_scan_should_work_correctly_on_image_dataset_qdrant(self):
        for _ in range(2):
            create_index_query = 'CREATE INDEX testQdrantIndexImageDataset\n                                        ON testSimilarityImageDataset (DummyFeatureExtractor(data))\n                                        USING QDRANT;'
            execute_query_fetch_all(self.evadb, create_index_query)
            select_query = 'SELECT _row_id FROM testSimilarityImageDataset\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data))\n                                LIMIT 1;'.format(self.img_path)
            explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
            self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
            '|__ ProjectPlan\n                |__ VectorIndexScanPlan\n                    |__ SeqScanPlan\n                        |__ StoragePlan'
            res_batch = execute_query_fetch_all(self.evadb, select_query)
            self.assertEqual(res_batch.frames['testsimilarityimagedataset._row_id'][0], 5)
            drop_query = 'DROP INDEX testQdrantIndexImageDataset'
            execute_query_fetch_all(self.evadb, drop_query)

    @chromadb_skip_marker
    def test_end_to_end_index_scan_should_work_correctly_on_image_dataset_chromadb(self):
        for _ in range(2):
            create_index_query = 'CREATE INDEX testChromaDBIndexImageDataset\n                                    ON testSimilarityImageDataset (DummyFeatureExtractor(data))\n                                    USING CHROMADB;'
            execute_query_fetch_all(self.evadb, create_index_query)
            select_query = 'SELECT _row_id FROM testSimilarityImageDataset\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data))\n                                LIMIT 1;'.format(self.img_path)
            explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
            self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
            res_batch = execute_query_fetch_all(self.evadb, select_query)
            self.assertEqual(res_batch.frames['testsimilarityimagedataset._row_id'][0], 5)
            drop_query = 'DROP INDEX testChromaDBIndexImageDataset'
            execute_query_fetch_all(self.evadb, drop_query)

    @pytest.mark.skip(reason='Flaky testcase due to `bad request` error message')
    @pinecone_skip_marker
    def test_end_to_end_index_scan_should_work_correctly_on_image_dataset_pinecone(self):
        for _ in range(2):
            create_index_query = 'CREATE INDEX testpineconeindeximagedataset\n                                    ON testSimilarityImageDataset (DummyFeatureExtractor(data))\n                                    USING PINECONE;'
            execute_query_fetch_all(self.evadb, create_index_query)
            time.sleep(20)
            select_query = 'SELECT _row_id FROM testSimilarityImageDataset\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data))\n                                LIMIT 1;'.format(self.img_path)
            explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
            self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
            res_batch = execute_query_fetch_all(self.evadb, select_query)
            self.assertEqual(res_batch.frames['testsimilarityimagedataset._row_id'][0], 5)
            drop_index_query = 'DROP INDEX testpineconeindeximagedataset;'
            execute_query_fetch_all(self.evadb, drop_index_query)

    @pytest.mark.skip(reason='Requires running local Milvus instance')
    @milvus_skip_marker
    def test_end_to_end_index_scan_should_work_correctly_on_image_dataset_milvus(self):
        for _ in range(2):
            create_index_query = 'CREATE INDEX testMilvusIndexImageDataset\n                                    ON testSimilarityImageDataset (DummyFeatureExtractor(data))\n                                    USING MILVUS;'
            execute_query_fetch_all(self.evadb, create_index_query)
            select_query = 'SELECT _row_id FROM testSimilarityImageDataset\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data))\n                                LIMIT 1;'.format(self.img_path)
            explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
            self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
            res_batch = execute_query_fetch_all(self.evadb, select_query)
            self.assertEqual(res_batch.frames['testsimilarityimagedataset._row_id'][0], 5)
            drop_query = 'DROP INDEX testMilvusIndexImageDataset'
            execute_query_fetch_all(self.evadb, drop_query)

    @pytest.mark.skip(reason='Requires running Weaviate instance')
    @weaviate_skip_marker
    def test_end_to_end_index_scan_should_work_correctly_on_image_dataset_weaviate(self):
        for _ in range(2):
            create_index_query = 'CREATE INDEX testWeaviateIndexImageDataset\n                                    ON testSimilarityImageDataset (DummyFeatureExtractor(data))\n                                    USING WEAVIATE;'
            execute_query_fetch_all(self.evadb, create_index_query)
            select_query = 'SELECT _row_id FROM testSimilarityImageDataset\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data))\n                                LIMIT 1;'.format(self.img_path)
            explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
            self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
            res_batch = execute_query_fetch_all(self.evadb, select_query)
            self.assertEqual(res_batch.frames['testsimilarityimagedataset._row_id'][0], 5)
            drop_query = 'DROP INDEX testWeaviateIndexImageDataset'
            execute_query_fetch_all(self.evadb, drop_query)

def test_similarity_should_work_in_order(self):
    select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 1;'.format(self.img_path)
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
    base_img[0] -= 1
    base_img[2] += 1
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
    self.assertTrue(np.array_equal(actual_open, base_img))
    select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 2;'.format(self.img_path)
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
    self.assertTrue(np.array_equal(actual_open, base_img))
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[1]
    self.assertTrue(np.array_equal(actual_open, base_img + 1))
    select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col)) DESC\n                            LIMIT 2;'.format(self.img_path)
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
    self.assertTrue(np.array_equal(actual_open, base_img + 4))
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[1]
    self.assertTrue(np.array_equal(actual_open, base_img + 3))
    select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 1;'.format(self.img_path)
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
    base_img[0] -= 1
    base_img[2] += 1
    base_img = base_img.astype(np.float32).reshape(1, -1)
    actual_open = actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[0]
    self.assertTrue(np.array_equal(actual_open, base_img))
    select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 2;'.format(self.img_path)
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    actual_open = actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[0]
    self.assertTrue(np.array_equal(actual_open, base_img))
    actual_open = actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[1]
    self.assertTrue(np.array_equal(actual_open, base_img + 1))

def test_should_do_vector_index_scan(self):
    select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 3;'.format(self.img_path)
    expected_batch = execute_query_fetch_all(self.evadb, select_query)
    create_index_query = 'CREATE INDEX testFaissIndexScanRewrite1\n                                    ON testSimilarityFeatureTable (feature_col)\n                                    USING FAISS;'
    execute_query_fetch_all(self.evadb, create_index_query)
    select_query = 'SELECT feature_col FROM testSimilarityFeatureTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), feature_col)\n                            LIMIT 3;'.format(self.img_path)
    explain_query = 'EXPLAIN {}'.format(select_query)
    explain_batch = execute_query_fetch_all(self.evadb, explain_query)
    self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(actual_batch), 3)
    for i in range(3):
        self.assertTrue(np.array_equal(expected_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[i], actual_batch.frames['testsimilarityfeaturetable.feature_col'].to_numpy()[i]))
    select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 3;'.format(self.img_path)
    expected_batch = execute_query_fetch_all(self.evadb, select_query)
    create_index_query = 'CREATE INDEX testFaissIndexScanRewrite2\n                                    ON testSimilarityTable (DummyFeatureExtractor(data_col))\n                                    USING FAISS;'
    execute_query_fetch_all(self.evadb, create_index_query)
    select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                            LIMIT 3;'.format(self.img_path)
    explain_query = 'EXPLAIN {}'.format(select_query)
    explain_batch = execute_query_fetch_all(self.evadb, explain_query)
    self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(actual_batch), 3)
    for i in range(3):
        self.assertTrue(np.array_equal(expected_batch.frames['testsimilaritytable.data_col'].to_numpy()[i], actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[i]))
    drop_query = 'DROP INDEX testFaissIndexScanRewrite1'
    execute_query_fetch_all(self.evadb, drop_query)
    drop_query = 'DROP INDEX testFaissIndexScanRewrite2'
    execute_query_fetch_all(self.evadb, drop_query)

def test_should_not_do_vector_index_scan_with_desc_order(self):
    create_index_query = 'CREATE INDEX testFaissIndexScanRewrite\n                                    ON testSimilarityTable (DummyFeatureExtractor(data_col))\n                                    USING FAISS;'
    execute_query_fetch_all(self.evadb, create_index_query)
    explain_query = '\n            EXPLAIN\n                SELECT data_col FROM testSimilarityTable WHERE dummy = 0\n                  ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col))\n                  LIMIT 3;\n        '.format('dummypath')
    batch = execute_query_fetch_all(self.evadb, explain_query)
    self.assertFalse('FaissIndexScan' in batch.frames[0][0])
    base_img = np.array(np.ones((3, 3, 3)), dtype=np.uint8)
    base_img[0] -= 1
    base_img[2] += 1
    select_query = 'SELECT data_col FROM testSimilarityTable\n                            ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(data_col)) DESC\n                            LIMIT 2;'.format(self.img_path)
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[0]
    self.assertTrue(np.array_equal(actual_open, base_img + 4))
    actual_open = actual_batch.frames['testsimilaritytable.data_col'].to_numpy()[1]
    self.assertTrue(np.array_equal(actual_open, base_img + 3))
    drop_query = 'DROP INDEX testFaissIndexScanRewrite'
    execute_query_fetch_all(self.evadb, drop_query)

def _helper_for_auto_update_during_insertion_with_faiss(self, if_exists: bool):
    for i, img_path in enumerate(self.img_path_list):
        insert_query = f"INSERT INTO testIndexAutoUpdate (img_path) VALUES ('{img_path}')"
        execute_query_fetch_all(self.evadb, insert_query)
        if i == 0:
            if_exists_str = 'IF NOT EXISTS ' if if_exists else ''
            create_index_query = f'CREATE INDEX {if_exists_str}testIndex ON testIndexAutoUpdate(DummyFeatureExtractor(Open(img_path))) USING FAISS'
            execute_query_fetch_all(self.evadb, create_index_query)
    select_query = 'SELECT _row_id FROM testIndexAutoUpdate\n                                ORDER BY Similarity(DummyFeatureExtractor(Open("{}")), DummyFeatureExtractor(Open(img_path)))\n                                LIMIT 1;'.format(self.img_path)
    explain_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {select_query}')
    self.assertTrue('VectorIndexScan' in explain_batch.frames[0][0])
    res_batch = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(res_batch.frames['testindexautoupdate._row_id'][0], 5)

@pytest.mark.notparallel
class OpenTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        load_functions_for_testing(self.evadb, mode='debug')
        self.img_path = create_sample_image()
        create_table_query = 'CREATE TABLE IF NOT EXISTS testOpenTable (num INTEGER);'
        execute_query_fetch_all(self.evadb, create_table_query)
        table_catalog_entry = self.evadb.catalog().get_table_catalog_entry('testOpenTable')
        storage_engine = StorageEngine.factory(self.evadb, table_catalog_entry)
        storage_engine.write(table_catalog_entry, Batch(pd.DataFrame([{'num': 1}, {'num': 2}])))

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.jpg')
        drop_table_query = 'DROP TABLE testOpenTable;'
        execute_query_fetch_all(self.evadb, drop_table_query)

    def test_open_should_open_image(self):
        select_query = 'SELECT num, Open("{}") FROM testOpenTable;'.format(self.img_path)
        batch_res = execute_query_fetch_all(self.evadb, select_query)
        expected_img = np.array(np.ones((3, 3, 3)), dtype=np.float32)
        expected_img[0] -= 1
        expected_img[2] += 1
        expected_batch = Batch(pd.DataFrame({'testopentable.num': [1, 2], 'open.data': [expected_img, expected_img]}))
        batch_res.sort_orderby(by=['testopentable.num'])
        expected_batch.sort_orderby(by=['testopentable.num'])
        self.assertEqual(expected_batch, batch_res)

def test_open_should_open_image(self):
    select_query = 'SELECT num, Open("{}") FROM testOpenTable;'.format(self.img_path)
    batch_res = execute_query_fetch_all(self.evadb, select_query)
    expected_img = np.array(np.ones((3, 3, 3)), dtype=np.float32)
    expected_img[0] -= 1
    expected_img[2] += 1
    expected_batch = Batch(pd.DataFrame({'testopentable.num': [1, 2], 'open.data': [expected_img, expected_img]}))
    batch_res.sort_orderby(by=['testopentable.num'])
    expected_batch.sort_orderby(by=['testopentable.num'])
    self.assertEqual(expected_batch, batch_res)

@pytest.mark.notparallel
class SelectExecutorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        video_file_path = create_sample_video(NUM_FRAMES)
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(cls.evadb, load_query)
        ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
        load_query = f"LOAD VIDEO '{ua_detrac}' INTO DETRAC;"
        execute_query_fetch_all(cls.evadb, load_query)
        load_functions_for_testing(cls.evadb)
        cls.table1 = create_table(cls.evadb, 'table1', 100, 3)
        cls.table2 = create_table(cls.evadb, 'table2', 500, 3)
        cls.table3 = create_table(cls.evadb, 'table3', 1000, 3)
        cls.meme1 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme1.jpg'
        cls.meme2 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme2.jpg'
        execute_query_fetch_all(cls.evadb, f"LOAD IMAGE '{cls.meme1}' INTO MemeImages;")
        execute_query_fetch_all(cls.evadb, f"LOAD IMAGE '{cls.meme2}' INTO MemeImages;")

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        file_remove('dummy.avi')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table1;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table2;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table3;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MemeImages;')

    def test_should_load_and_select_real_audio_in_table(self):
        query = "LOAD VIDEO 'data/sample_videos/touchdown.mp4'\n                   INTO TOUCHDOWN;"
        execute_query_fetch_all(self.evadb, query)
        select_query = 'SELECT id, audio FROM TOUCHDOWN;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort('touchdown.id')
        video_reader = DecordReader('data/sample_videos/touchdown.mp4', read_audio=True)
        expected_batch = Batch(frames=pd.DataFrame())
        for batch in video_reader.read():
            batch.frames['name'] = 'touchdown.mp4'
            expected_batch += batch
        expected_batch.modify_column_alias('touchdown')
        expected_batch = expected_batch.project(['touchdown.id', 'touchdown.audio'])
        self.assertEqual(actual_batch, expected_batch)

    def test_chunk_param_should_fail(self):
        with self.assertRaises(AssertionError):
            execute_query_fetch_all(self.evadb, 'SELECT data from MyVideo chunk_size 4000 chunk_overlap 200;')
        with self.assertRaises(AssertionError):
            execute_query_fetch_all(self.evadb, 'SELECT data from MemeImages chunk_size 4000 chunk_overlap 200;')

    @pytest.mark.torchtest
    def test_lateral_join(self):
        select_query = 'SELECT id, a FROM DETRAC JOIN LATERAL\n                        Yolo(data) AS T(a,b,c) WHERE id < 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(list(actual_batch.columns), ['detrac.id', 'T.a'])
        self.assertEqual(len(actual_batch), 5)

    def test_complex_logical_expressions(self):
        query = "SELECT id FROM MyVideo\n            WHERE DummyObjectDetector(data).label = ['{}']  ORDER BY id;"
        persons = execute_query_fetch_all(self.evadb, query.format('person')).frames.to_numpy()
        bicycles = execute_query_fetch_all(self.evadb, query.format('bicycle')).frames.to_numpy()
        import numpy as np
        self.assertTrue(len(np.intersect1d(persons, bicycles)) == 0)
        query_or = "SELECT id FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person']\n                OR DummyObjectDetector(data).label = ['bicycle']\n            ORDER BY id;"
        actual = execute_query_fetch_all(self.evadb, query_or)
        expected = execute_query_fetch_all(self.evadb, 'SELECT id FROM MyVideo ORDER BY id')
        self.assertEqual(expected, actual)
        query_and = "SELECT id FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person']\n                AND DummyObjectDetector(data).label = ['bicycle']\n            ORDER BY id;"
        expected = execute_query_fetch_all(self.evadb, query_and)
        self.assertEqual(len(expected), 0)

    def test_select_and_union_video_in_table(self):
        select_query = 'SELECT * FROM MyVideo WHERE id < 3\n            UNION ALL SELECT * FROM MyVideo WHERE id > 7;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort('myvideo.id')
        expected_batch = list(create_dummy_batches(filters=[i for i in range(NUM_FRAMES) if i < 3 or i > 7]))[0]
        self.assertEqual(actual_batch, expected_batch)
        select_query = 'SELECT * FROM MyVideo WHERE id < 2\n            UNION ALL SELECT * FROM MyVideo WHERE id > 4 AND id < 6\n            UNION ALL SELECT * FROM MyVideo WHERE id > 7;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort('myvideo.id')
        expected_batch = list(create_dummy_batches(filters=[i for i in range(NUM_FRAMES) if i < 2 or i == 5 or i > 7]))[0]
        self.assertEqual(actual_batch, expected_batch)

    def test_sort_on_nonprojected_column(self):
        """This tests doing an order by on a column
        that is not projected. The orderby_executor currently
        catches the KeyError, passes, and returns the untouched
        data
        """
        select_query = 'SELECT data FROM MyVideo ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        select_query = 'SELECT data FROM MyVideo'
        expected_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), len(expected_batch))

    def test_should_load_and_select_real_video_in_table(self):
        query = "LOAD VIDEO 'data/mnist/mnist.mp4'\n                   INTO MNIST;"
        execute_query_fetch_all(self.evadb, query)
        select_query = 'SELECT id, data FROM MNIST;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort('mnist.id')
        video_reader = DecordReader('data/mnist/mnist.mp4')
        expected_batch = Batch(frames=pd.DataFrame())
        for batch in video_reader.read():
            batch.frames['name'] = 'mnist.mp4'
            expected_batch += batch
        expected_batch.modify_column_alias('mnist')
        expected_batch = expected_batch.project(['mnist.id', 'mnist.data'])
        self.assertEqual(actual_batch, expected_batch)

    def test_project_identifier_column(self):
        batch = execute_query_fetch_all(self.evadb, 'SELECT _row_id, id FROM MyVideo;')
        expected = Batch(pd.DataFrame({'myvideo._row_id': [1] * NUM_FRAMES, 'myvideo.id': range(NUM_FRAMES)}))
        self.assertEqual(batch, expected)
        batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM MyVideo;')
        self.assertTrue('myvideo._row_id' in batch.columns)
        batch = execute_query_fetch_all(self.evadb, 'SELECT _row_id, name FROM MemeImages;')
        expected = Batch(pd.DataFrame({'memeimages._row_id': [1, 2], 'memeimages.name': [self.meme1, self.meme2]}))
        self.assertEqual(batch, expected)
        batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM MemeImages;')
        self.assertTrue('memeimages._row_id' in batch.columns)
        batch = execute_query_fetch_all(self.evadb, 'SELECT _row_id FROM table1;')
        expected = Batch(pd.DataFrame({'table1._row_id': range(1, 101)}))
        self.assertEqual(batch, expected)
        batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM table1;')
        self.assertTrue('table1._row_id' in batch.columns)

    def test_select_and_sample(self):
        select_query = 'SELECT id FROM MyVideo SAMPLE 7 ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=range(0, NUM_FRAMES, 7)))
        expected_batch[0] = expected_batch[0].project(['myvideo.id'])
        self.assertEqual(len(actual_batch), len(expected_batch[0]))
        self.assertEqual(actual_batch, expected_batch[0])

    def test_select_and_where_video_in_table(self):
        select_query = 'SELECT * FROM MyVideo WHERE id = 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_batch = list(create_dummy_batches(filters=[5]))[0]
        self.assertEqual(actual_batch, expected_batch)
        select_query = 'SELECT data FROM MyVideo WHERE id = 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(actual_batch, expected_batch.project(['myvideo.data']))
        select_query = 'SELECT id, data FROM MyVideo WHERE id >= 2;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=range(2, NUM_FRAMES)))[0]
        self.assertEqual(actual_batch, expected_batch.project(['myvideo.id', 'myvideo.data']))
        select_query = 'SELECT * FROM MyVideo WHERE id >= 2 AND id < 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=range(2, 5)))[0]
        self.assertEqual(actual_batch, expected_batch)

    def test_hash_join_with_multiple_tables(self):
        select_query = 'SELECT * FROM table1 JOIN table2\n                          ON table2.a0 = table1.a0 JOIN table3\n                          ON table3.a1 = table1.a1 WHERE table1.a2 > 50;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        tmp = pd.merge(self.table1, self.table2, left_on=['table1.a0'], right_on=['table2.a0'], how='inner')
        expected = pd.merge(tmp, self.table3, left_on=['table1.a1'], right_on=['table3.a1'], how='inner')
        expected = expected.where(expected['table1.a2'] > 50)
        if len(expected):
            expected_batch = Batch(expected)
            self.assertEqual(expected_batch.sort_orderby(['table1.a0']), actual_batch.sort_orderby(['table1.a0']))

    def test_nested_select_video_in_table(self):
        nested_select_query = 'SELECT * FROM\n            (SELECT * FROM MyVideo WHERE id >= 2 AND id < 5) AS T\n            WHERE id >= 3;'
        actual_batch = execute_query_fetch_all(self.evadb, nested_select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=range(3, 5)))[0]
        expected_batch.modify_column_alias('T')
        self.assertEqual(actual_batch, expected_batch)
        nested_select_query = 'SELECT * FROM\n            (SELECT * FROM MyVideo WHERE id >= 2 AND id < 5) AS T\n            WHERE id >= 3;'
        actual_batch = execute_query_fetch_all(self.evadb, nested_select_query)
        actual_batch.sort('T.id')
        expected_batch = list(create_dummy_batches(filters=range(3, 5)))[0]
        expected_batch.modify_column_alias('T')
        self.assertEqual(actual_batch, expected_batch)

    def test_select_and_sample_with_predicate(self):
        select_query = 'SELECT id FROM MyVideo SAMPLE 2 WHERE id > 5 ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_batch = list(create_dummy_batches(filters=range(6, NUM_FRAMES, 2)))
        self.assertEqual(actual_batch, expected_batch[0].project(['myvideo.id']))
        select_query = 'SELECT id FROM MyVideo SAMPLE 4 WHERE id > 2 ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_batch = list(create_dummy_batches(filters=range(4, NUM_FRAMES, 4)))
        self.assertEqual(actual_batch, expected_batch[0].project(['myvideo.id']))
        select_query = 'SELECT id FROM MyVideo SAMPLE 2 WHERE id > 2 AND id < 8 ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_batch = list(create_dummy_batches(filters=range(4, 8, 2)))
        self.assertEqual(actual_batch, expected_batch[0].project(['myvideo.id']))

    def test_lateral_join_with_unnest_on_subset_of_outputs(self):
        query = 'SELECT id, label\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyMultiObjectDetector(data).labels) AS T(label)\n                  WHERE id < 2 ORDER BY id;'
        unnest_batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 0, 1, 1], np.intp), 'T.label': np.array(['person', 'person', 'bicycle', 'bicycle'])}))
        self.assertEqual(unnest_batch, expected)
        query = 'SELECT id, label\n                FROM MyVideo JOIN LATERAL\n                UNNEST(DummyMultiObjectDetector(data).labels) AS T(label)\n                WHERE id < 2 AND T.label = "person" ORDER BY id;'
        unnest_batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 0], np.intp), 'T.label': np.array(['person', 'person'])}))
        self.assertEqual(unnest_batch, expected)

    def test_lateral_join_with_unnest(self):
        query = 'SELECT id, label\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyObjectDetector(data)) AS T(label)\n                  WHERE id < 2 ORDER BY id;'
        unnest_batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 1], dtype=np.intp), 'T.label': np.array(['person', 'bicycle'])}))
        self.assertEqual(unnest_batch, expected)
        query = 'SELECT id, label\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyObjectDetector(data)) AS T\n                  WHERE id < 2 ORDER BY id;'
        unnest_batch = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 1], dtype=np.intp), 'T.label': np.array(['person', 'bicycle'])}))
        self.assertEqual(unnest_batch, expected)

    @pytest.mark.torchtest
    def test_lateral_join_with_multiple_projects(self):
        select_query = 'SELECT id, T.labels FROM DETRAC JOIN LATERAL\n                        Yolo(data) AS T WHERE id < 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertTrue(all(actual_batch.frames.columns == ['detrac.id', 'T.labels']))
        self.assertEqual(len(actual_batch), 5)

    def test_should_select_star_in_table(self):
        select_query = 'SELECT * FROM MyVideo;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches())[0]
        self.assertEqual(actual_batch, expected_batch)
        select_query = 'SELECT * FROM MyVideo WHERE id = 5;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected_batch = list(create_dummy_batches(filters=[5]))[0]
        self.assertEqual(actual_batch, expected_batch)

def test_complex_logical_expressions(self):
    query = "SELECT id FROM MyVideo\n            WHERE DummyObjectDetector(data).label = ['{}']  ORDER BY id;"
    persons = execute_query_fetch_all(self.evadb, query.format('person')).frames.to_numpy()
    bicycles = execute_query_fetch_all(self.evadb, query.format('bicycle')).frames.to_numpy()
    import numpy as np
    self.assertTrue(len(np.intersect1d(persons, bicycles)) == 0)
    query_or = "SELECT id FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person']\n                OR DummyObjectDetector(data).label = ['bicycle']\n            ORDER BY id;"
    actual = execute_query_fetch_all(self.evadb, query_or)
    expected = execute_query_fetch_all(self.evadb, 'SELECT id FROM MyVideo ORDER BY id')
    self.assertEqual(expected, actual)
    query_and = "SELECT id FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person']\n                AND DummyObjectDetector(data).label = ['bicycle']\n            ORDER BY id;"
    expected = execute_query_fetch_all(self.evadb, query_and)
    self.assertEqual(len(expected), 0)

def test_project_identifier_column(self):
    batch = execute_query_fetch_all(self.evadb, 'SELECT _row_id, id FROM MyVideo;')
    expected = Batch(pd.DataFrame({'myvideo._row_id': [1] * NUM_FRAMES, 'myvideo.id': range(NUM_FRAMES)}))
    self.assertEqual(batch, expected)
    batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM MyVideo;')
    self.assertTrue('myvideo._row_id' in batch.columns)
    batch = execute_query_fetch_all(self.evadb, 'SELECT _row_id, name FROM MemeImages;')
    expected = Batch(pd.DataFrame({'memeimages._row_id': [1, 2], 'memeimages.name': [self.meme1, self.meme2]}))
    self.assertEqual(batch, expected)
    batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM MemeImages;')
    self.assertTrue('memeimages._row_id' in batch.columns)
    batch = execute_query_fetch_all(self.evadb, 'SELECT _row_id FROM table1;')
    expected = Batch(pd.DataFrame({'table1._row_id': range(1, 101)}))
    self.assertEqual(batch, expected)
    batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM table1;')
    self.assertTrue('table1._row_id' in batch.columns)

def test_hash_join_with_multiple_tables(self):
    select_query = 'SELECT * FROM table1 JOIN table2\n                          ON table2.a0 = table1.a0 JOIN table3\n                          ON table3.a1 = table1.a1 WHERE table1.a2 > 50;'
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    tmp = pd.merge(self.table1, self.table2, left_on=['table1.a0'], right_on=['table2.a0'], how='inner')
    expected = pd.merge(tmp, self.table3, left_on=['table1.a1'], right_on=['table3.a1'], how='inner')
    expected = expected.where(expected['table1.a2'] > 50)
    if len(expected):
        expected_batch = Batch(expected)
        self.assertEqual(expected_batch.sort_orderby(['table1.a0']), actual_batch.sort_orderby(['table1.a0']))

def test_lateral_join_with_unnest_on_subset_of_outputs(self):
    query = 'SELECT id, label\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyMultiObjectDetector(data).labels) AS T(label)\n                  WHERE id < 2 ORDER BY id;'
    unnest_batch = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 0, 1, 1], np.intp), 'T.label': np.array(['person', 'person', 'bicycle', 'bicycle'])}))
    self.assertEqual(unnest_batch, expected)
    query = 'SELECT id, label\n                FROM MyVideo JOIN LATERAL\n                UNNEST(DummyMultiObjectDetector(data).labels) AS T(label)\n                WHERE id < 2 AND T.label = "person" ORDER BY id;'
    unnest_batch = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 0], np.intp), 'T.label': np.array(['person', 'person'])}))
    self.assertEqual(unnest_batch, expected)

def test_lateral_join_with_unnest(self):
    query = 'SELECT id, label\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyObjectDetector(data)) AS T(label)\n                  WHERE id < 2 ORDER BY id;'
    unnest_batch = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 1], dtype=np.intp), 'T.label': np.array(['person', 'bicycle'])}))
    self.assertEqual(unnest_batch, expected)
    query = 'SELECT id, label\n                  FROM MyVideo JOIN LATERAL\n                    UNNEST(DummyObjectDetector(data)) AS T\n                  WHERE id < 2 ORDER BY id;'
    unnest_batch = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame({'myvideo.id': np.array([0, 1], dtype=np.intp), 'T.label': np.array(['person', 'bicycle'])}))
    self.assertEqual(unnest_batch, expected)

class CreateTableTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        video_file_path = create_sample_video()
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(cls.evadb, load_query)
        ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
        execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO UATRAC;")
        load_functions_for_testing(cls.evadb)

    @classmethod
    def tearDownClass(cls):
        file_remove('dummy.avi')
        file_remove('ua_detrac.mp4')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS UATRAC;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS uadtrac_fastRCNN;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS dummy_table;')
        shutdown_ray()

    def _test_currently_cannot_create_boolean_table(self):
        query = ' CREATE TABLE BooleanTable( A BOOLEAN);'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)

    def test_should_create_table_from_select(self):
        create_query = 'CREATE TABLE dummy_table\n            AS SELECT id, DummyObjectDetector(data).label FROM MyVideo;\n        '
        execute_query_fetch_all(self.evadb, create_query)
        select_query = 'SELECT id, label FROM dummy_table;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        labels = DummyObjectDetector().labels
        expected = [{'dummy_table.id': i, 'dummy_table.label': [labels[1 + i % 2]]} for i in range(NUM_FRAMES)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS dummy_table;')
        execute_query_fetch_all(self.evadb, create_query)

    @macos_skip_marker
    @pytest.mark.torchtest
    def test_should_create_table_from_select_lateral_join(self):
        select_query = 'SELECT id, label, bbox FROM UATRAC JOIN LATERAL Yolo(data) AS T(label, bbox, score) WHERE id < 5;'
        query = f'CREATE TABLE IF NOT EXISTS uadtrac_fastRCNN AS {select_query};'
        execute_query_fetch_all(self.evadb, query)
        select_view_query = 'SELECT id, label, bbox FROM uadtrac_fastRCNN'
        actual_batch = execute_query_fetch_all(self.evadb, select_view_query)
        actual_batch.sort()
        self.assertEqual(len(actual_batch), 5)
        res = actual_batch.frames
        for idx in res.index:
            self.assertTrue('car' in res['uadtrac_fastrcnn.label'][idx])
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS uadtrac_fastRCNN;')
        query = f'CREATE TABLE IF NOT EXISTS uadtrac_fastRCNN AS {select_query};'
        execute_query_fetch_all(self.evadb, query)

    def test_create_table_with_incorrect_info(self):
        create_table = 'CREATE TABLE SlackCSV(metadata TEXT(1000));'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, create_table)
        create_table = 'CREATE TABLE SlackCSV(user_profile TEXT(1000));'
        execute_query_fetch_all(self.evadb, create_table)
        execute_query_fetch_all(self.evadb, 'DROP TABLE SlackCSV;')

    def test_create_table_with_restricted_keywords(self):
        create_table = 'CREATE TABLE hello (_row_id INTEGER, price TEXT);'
        with self.assertRaises(AssertionError):
            execute_query_fetch_all(self.evadb, create_table)
        create_table = 'CREATE TABLE hello2 (_ROW_id INTEGER, price TEXT);'
        with self.assertRaises(AssertionError):
            execute_query_fetch_all(self.evadb, create_table)

def test_should_create_table_from_select(self):
    create_query = 'CREATE TABLE dummy_table\n            AS SELECT id, DummyObjectDetector(data).label FROM MyVideo;\n        '
    execute_query_fetch_all(self.evadb, create_query)
    select_query = 'SELECT id, label FROM dummy_table;'
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    actual_batch.sort()
    labels = DummyObjectDetector().labels
    expected = [{'dummy_table.id': i, 'dummy_table.label': [labels[1 + i % 2]]} for i in range(NUM_FRAMES)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS dummy_table;')
    execute_query_fetch_all(self.evadb, create_query)

@pytest.mark.notparallel
class FunctionExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        video_file_path = create_sample_video(NUM_FRAMES)
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, load_query)
        create_function_query = "CREATE FUNCTION DummyObjectDetector\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_should_load_and_select_using_function_video_in_table(self):
        select_query = 'SELECT id,DummyObjectDetector(data) FROM MyVideo             ORDER BY id;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        labels = DummyObjectDetector().labels
        expected = [{'myvideo.id': i, 'dummyobjectdetector.label': np.array([labels[1 + i % 2]])} for i in range(NUM_FRAMES)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)

    def test_should_load_and_select_using_function_video(self):
        select_query = "SELECT id,DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person'] ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = [{'myvideo.id': i * 2, 'dummyobjectdetector.label': np.array(['person'])} for i in range(NUM_FRAMES // 2)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)
        select_query = "SELECT id,DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label @> ['person'] ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(actual_batch, expected_batch)
        select_query = "SELECT id,DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label <@ ['person', 'bicycle']             ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = [{'myvideo.id': i * 2, 'dummyobjectdetector.label': np.array(['person'])} for i in range(NUM_FRAMES // 2)]
        expected += [{'myvideo.id': i, 'dummyobjectdetector.label': np.array(['bicycle'])} for i in range(NUM_FRAMES) if i % 2 + 1 == 2]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        expected_batch.sort()
        self.assertEqual(actual_batch, expected_batch)
        nested_select_query = "SELECT name, id, data FROM\n            (SELECT name, id, data, DummyObjectDetector(data) FROM MyVideo\n                WHERE id >= 2\n            ) AS T\n            WHERE ['person'] <@ label;\n            "
        actual_batch = execute_query_fetch_all(self.evadb, nested_select_query)
        actual_batch.sort()
        expected_batch = list(create_dummy_batches(filters=[i for i in range(2, NUM_FRAMES) if i % 2 == 0]))[0]
        expected_batch = expected_batch.project(['myvideo.name', 'myvideo.id', 'myvideo.data'])
        expected_batch.modify_column_alias('T')
        self.assertEqual(actual_batch, expected_batch)

    def test_create_function(self):
        function_name = 'DummyObjectDetector'
        create_function_query = "CREATE FUNCTION {}\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
        with self.assertRaises(ExecutorError):
            actual = execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
            expected = Batch(pd.DataFrame([f'Function {function_name} already exists.']))
            self.assertEqual(actual, expected)
        actual = execute_query_fetch_all(self.evadb, create_function_query.format('IF NOT EXISTS ' + function_name))
        expected = Batch(pd.DataFrame([f'Function {function_name} already exists, nothing added.']))
        self.assertEqual(actual, expected)

    def test_create_or_replace(self):
        function_name = 'DummyObjectDetector'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = "CREATE OR REPLACE FUNCTION {}\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
        actual = execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
        expected = Batch(pd.DataFrame([f'Function {function_name} added to the database.']))
        self.assertEqual(actual, expected)
        actual = execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
        expected = Batch(pd.DataFrame([f'Function {function_name} overwritten.']))
        self.assertEqual(actual, expected)

    def test_should_create_function_with_metadata(self):
        function_name = 'DummyObjectDetector'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION {function_name};')
        create_function_query = 'CREATE FUNCTION {}\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  \'test/util.py\'\n                  CACHE TRUE\n                  BATCH FALSE\n                  INT_VAL 1\n                  FLOAT_VAL 1.5\n                  STR_VAL "gg";\n        '
        execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
        entries = self.evadb.catalog().get_function_metadata_entries_by_function_name(function_name)
        self.assertEqual(len(entries), 5)
        metadata = [(entry.key, entry.value) for entry in entries]
        expected_metadata = [('cache', True), ('batch', False), ('int_val', 1), ('float_val', 1.5), ('str_val', 'gg')]
        self.assertEqual(set(metadata), set(expected_metadata))

    def test_should_return_empty_metadata_list_for_missing_function(self):
        entries = self.evadb.catalog().get_function_metadata_entries_by_function_name('randomFunction')
        self.assertEqual(len(entries), 0)

    def test_should_return_empty_metadata_list_if_function_is_removed(self):
        function_name = 'DummyObjectDetector'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION {function_name};')
        create_function_query = "CREATE FUNCTION {}\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py'\n                  CACHE 'TRUE'\n                  BATCH 'FALSE';\n        "
        execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
        entries = self.evadb.catalog().get_function_metadata_entries_by_function_name(function_name)
        self.assertEqual(len(entries), 2)
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION {function_name};')
        entries = self.evadb.catalog().get_function_metadata_entries_by_function_name(function_name)
        self.assertEqual(len(entries), 0)

    def test_should_raise_using_missing_function(self):
        select_query = 'SELECT id,DummyObjectDetector1(data) FROM MyVideo             ORDER BY id;'
        with self.assertRaises(BinderError) as cm:
            execute_query_fetch_all(self.evadb, select_query, do_not_print_exceptions=True)
        err_msg = "Function 'DummyObjectDetector1' does not exist in the catalog. Please create the function using CREATE FUNCTION command."
        self.assertEqual(str(cm.exception), err_msg)

    def test_should_raise_for_function_name_mismatch(self):
        create_function_query = "CREATE FUNCTION TestFUNCTION\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, create_function_query, do_not_print_exceptions=True)

    def test_should_raise_if_function_file_is_modified(self):
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION DummyObjectDetector;')
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION IF EXISTS DummyObjectDetector;')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as tmp_file:
            with open('test/util.py', 'r') as file:
                tmp_file.write(file.read())
            tmp_file.seek(0)
            function_name = 'DummyObjectDetector'
            create_function_query = "CREATE FUNCTION {}\n                    INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                    OUTPUT (label NDARRAY STR(10))\n                    TYPE  Classification\n                    IMPL  '{}';\n            "
            execute_query_fetch_all(self.evadb, create_function_query.format(function_name, tmp_file.name))
            tmp_file.seek(0, 2)
            tmp_file.write('#comment')
            tmp_file.seek(0)
            select_query = 'SELECT id,DummyObjectDetector(data) FROM MyVideo ORDER BY id;'
            execute_query_fetch_all(self.evadb, select_query)

    def test_create_function_with_decorators(self):
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION IF EXISTS DummyObjectDetectorDecorators;')
        create_function_query = "CREATE FUNCTION DummyObjectDetectorDecorators\n                  IMPL  'test/util.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        catalog_manager = self.evadb.catalog()
        function_obj = catalog_manager.get_function_catalog_entry_by_name('DummyObjectDetectorDecorators')
        function_inputs = catalog_manager.get_function_io_catalog_input_entries(function_obj)
        self.assertEquals(len(function_inputs), 1)
        function_input = function_inputs[0]
        expected_input_attributes = {'name': 'Frame_Array', 'type': ColumnType.NDARRAY, 'is_nullable': False, 'array_type': NdArrayType.UINT8, 'array_dimensions': (3, 256, 256), 'is_input': True}
        for attr in expected_input_attributes:
            self.assertEquals(getattr(function_input, attr), expected_input_attributes[attr])
        function_outputs = catalog_manager.get_function_io_catalog_output_entries(function_obj)
        self.assertEquals(len(function_outputs), 1)
        function_output = function_outputs[0]
        expected_output_attributes = {'name': 'label', 'type': ColumnType.NDARRAY, 'is_nullable': False, 'array_type': NdArrayType.STR, 'array_dimensions': (), 'is_input': False}
        for attr in expected_output_attributes:
            self.assertEquals(getattr(function_output, attr), expected_output_attributes[attr])

    def test_function_cost_entry_created(self):
        execute_query_fetch_all(self.evadb, 'SELECT DummyObjectDetector(data) FROM MyVideo')
        entry = self.evadb.catalog().get_function_cost_catalog_entry('DummyObjectDetector')
        self.assertIsNotNone(entry)

def test_should_load_and_select_using_function_video_in_table(self):
    select_query = 'SELECT id,DummyObjectDetector(data) FROM MyVideo             ORDER BY id;'
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    labels = DummyObjectDetector().labels
    expected = [{'myvideo.id': i, 'dummyobjectdetector.label': np.array([labels[1 + i % 2]])} for i in range(NUM_FRAMES)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)

def test_create_function(self):
    function_name = 'DummyObjectDetector'
    create_function_query = "CREATE FUNCTION {}\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
    with self.assertRaises(ExecutorError):
        actual = execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
        expected = Batch(pd.DataFrame([f'Function {function_name} already exists.']))
        self.assertEqual(actual, expected)
    actual = execute_query_fetch_all(self.evadb, create_function_query.format('IF NOT EXISTS ' + function_name))
    expected = Batch(pd.DataFrame([f'Function {function_name} already exists, nothing added.']))
    self.assertEqual(actual, expected)

def test_create_or_replace(self):
    function_name = 'DummyObjectDetector'
    execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
    create_function_query = "CREATE OR REPLACE FUNCTION {}\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
    actual = execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
    expected = Batch(pd.DataFrame([f'Function {function_name} added to the database.']))
    self.assertEqual(actual, expected)
    actual = execute_query_fetch_all(self.evadb, create_function_query.format(function_name))
    expected = Batch(pd.DataFrame([f'Function {function_name} overwritten.']))
    self.assertEqual(actual, expected)

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
@gpu_skip_marker
def test_should_run_extract_object(self):
    select_query = '\n            SELECT id, T.iids, T.bboxes, T.scores, T.labels\n            FROM MyVideo JOIN LATERAL EXTRACT_OBJECT(data, Yolo, NorFairTracker)\n                AS T(iids, labels, bboxes, scores)\n            WHERE id < 30;\n            '
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(actual_batch), 30)
    num_of_entries = actual_batch.frames['T.iids'].apply(lambda x: len(x)).sum()
    select_query = '\n            SELECT id, T.iid, T.bbox, T.score, T.label\n            FROM MyVideo JOIN LATERAL\n                UNNEST(EXTRACT_OBJECT(data, Yolo, NorFairTracker)) AS T(iid, label, bbox, score)\n            WHERE id < 30;\n            '
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(actual_batch), num_of_entries)

@pytest.mark.notparallel
class ArrayCountTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        video_file_path = create_sample_video(NUM_FRAMES)
        load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(cls.evadb, load_query)
        load_functions_for_testing(cls.evadb, mode='debug')

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')
        file_remove('dummy.avi')

    def test_should_load_and_select_using_function_video(self):
        select_query = "SELECT id,DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person'] ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = [{'myvideo.id': i * 2, 'dummyobjectdetector.label': ['person']} for i in range(NUM_FRAMES // 2)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)
        select_query = "SELECT id, DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label <@ ['person'] ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(actual_batch, expected_batch)
        select_query = "SELECT id FROM MyVideo WHERE             DummyMultiObjectDetector(data).labels @> ['person'] ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = [{'myvideo.id': i} for i in range(0, NUM_FRAMES, 3)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)

    def test_array_count_integration_test(self):
        select_query = "SELECT id FROM MyVideo WHERE\n            ArrayCount(DummyMultiObjectDetector(data).labels, 'person') = 2\n            ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = [{'myvideo.id': i} for i in range(0, NUM_FRAMES, 3)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)
        select_query = "SELECT id FROM MyVideo\n            WHERE ArrayCount(DummyObjectDetector(data).label, 'bicycle') = 1\n            ORDER BY id;"
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        expected = [{'myvideo.id': i} for i in range(1, NUM_FRAMES, 2)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)

def test_should_load_and_select_using_function_video(self):
    select_query = "SELECT id,DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label = ['person'] ORDER BY id;"
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    expected = [{'myvideo.id': i * 2, 'dummyobjectdetector.label': ['person']} for i in range(NUM_FRAMES // 2)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)
    select_query = "SELECT id, DummyObjectDetector(data) FROM MyVideo             WHERE DummyObjectDetector(data).label <@ ['person'] ORDER BY id;"
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(actual_batch, expected_batch)
    select_query = "SELECT id FROM MyVideo WHERE             DummyMultiObjectDetector(data).labels @> ['person'] ORDER BY id;"
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    expected = [{'myvideo.id': i} for i in range(0, NUM_FRAMES, 3)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)

def test_array_count_integration_test(self):
    select_query = "SELECT id FROM MyVideo WHERE\n            ArrayCount(DummyMultiObjectDetector(data).labels, 'person') = 2\n            ORDER BY id;"
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    expected = [{'myvideo.id': i} for i in range(0, NUM_FRAMES, 3)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)
    select_query = "SELECT id FROM MyVideo\n            WHERE ArrayCount(DummyObjectDetector(data).label, 'bicycle') = 1\n            ORDER BY id;"
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    expected = [{'myvideo.id': i} for i in range(1, NUM_FRAMES, 2)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)

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

def test_s3_multiple_file_load_executor(self):
    bucket_name = 'multiple-file-bucket'
    self.upload_multiple_files(bucket_name)
    query = f'LOAD VIDEO "s3://{bucket_name}/*.mp4" INTO MyVideos;'
    result = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 2']))
    self.assertEqual(result, expected)
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

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

def setUp(self):
    try_to_import_pillow()
    self.annotate_instance = Annotate()

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

def test_open_path_should_raise_error(self):
    with self.assertRaises((AssertionError, FileNotFoundError)):
        self.open_instance(pd.DataFrame(['incorrect_path']))

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

@pytest.mark.notparallel
class LoadExecutorTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()
        self.image_files_path = Path(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/*.jpg')
        self.csv_file_path = create_sample_csv()

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')
        file_remove('dummy.csv')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

    def test_should_load_videos_in_table(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4'
        query = f'LOAD VIDEO "{path}" INTO MyVideos;'
        result = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 2']))
        self.assertEqual(result, expected)

    def test_should_load_images_in_table(self):
        num_files = len(glob.glob(os.path.expanduser(self.image_files_path), recursive=True))
        query = f'LOAD IMAGE "{self.image_files_path}" INTO MyImages;'
        result = execute_query_fetch_all(self.evadb, query)
        expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: {num_files}']))
        self.assertEqual(result, expected)

    def test_should_load_csv_in_table(self):
        create_table_query = '\n\n            CREATE TABLE IF NOT EXISTS MyVideoCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER,\n                video_id INTEGER,\n                dataset_name TEXT(30),\n                label TEXT(30),\n                bbox NDARRAY FLOAT32(4),\n                object_id INTEGER\n            );\n\n            '
        execute_query_fetch_all(self.evadb, create_table_query)
        load_query = f"LOAD CSV '{self.csv_file_path}' INTO MyVideoCSV;"
        execute_query_fetch_all(self.evadb, load_query)
        select_query = 'SELECT id, frame_id, video_id,\n                          dataset_name, label, bbox,\n                          object_id\n                          FROM MyVideoCSV;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = next(create_dummy_csv_batches())
        expected_batch.modify_column_alias('myvideocsv')
        self.assertEqual(actual_batch, expected_batch)
        drop_query = 'DROP TABLE IF EXISTS MyVideoCSV;'
        execute_query_fetch_all(self.evadb, drop_query)

    def test_should_load_csv_in_table_with_spaces_in_column_name(self):
        create_table_query = '\n\n            CREATE TABLE IF NOT EXISTS MyVideoCSV (\n                id INTEGER UNIQUE,\n                `frame id` INTEGER,\n                `video id` INTEGER,\n                `dataset name` TEXT(30),\n                label TEXT(30),\n                bbox NDARRAY FLOAT32(4),\n                `object id` INTEGER\n            );\n\n            '
        execute_query_fetch_all(self.evadb, create_table_query)
        load_query = f"LOAD CSV '{create_csv_with_comlumn_name_spaces()}' INTO MyVideoCSV;"
        execute_query_fetch_all(self.evadb, load_query)
        select_query = 'SELECT id, `frame id`, `video id`,\n                          `dataset name`, label, bbox,\n                          `object id`\n                          FROM MyVideoCSV;'
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected_batch = next(create_dummy_csv_batches())
        expected_batch.modify_column_alias('myvideocsv')
        self.assertEqual(actual_batch, expected_batch)
        drop_query = 'DROP TABLE IF EXISTS MyVideoCSV;'
        execute_query_fetch_all(self.evadb, drop_query)

def test_should_load_videos_in_table(self):
    path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4'
    query = f'LOAD VIDEO "{path}" INTO MyVideos;'
    result = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.VIDEO.name}: 2']))
    self.assertEqual(result, expected)

def test_should_load_images_in_table(self):
    num_files = len(glob.glob(os.path.expanduser(self.image_files_path), recursive=True))
    query = f'LOAD IMAGE "{self.image_files_path}" INTO MyImages;'
    result = execute_query_fetch_all(self.evadb, query)
    expected = Batch(pd.DataFrame([f'Number of loaded {FileFormatType.IMAGE.name}: {num_files}']))
    self.assertEqual(result, expected)

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

def test_show_databases(self):
    result = execute_query_fetch_all(self.evadb, 'SHOW DATABASES;')
    self.assertEqual(len(result.columns), 3)
    self.assertEqual(len(result), 6)
    expected = {'name': [f'test_data_source_{i}' for i in range(NUM_DATABASES)], 'engine': ['sqlite' for _ in range(NUM_DATABASES)]}
    expected_df = pd.DataFrame(expected)
    self.assertTrue(all(expected_df.name == result.frames.name))
    self.assertTrue(all(expected_df.engine == result.frames.engine))

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

def test_function_with_no_input_arguments(self):
    select_query = 'SELECT DummyNoInputFunction();'
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    expected = Batch(pd.DataFrame([{'dummynoinputfunction.label': 'DummyNoInputFunction'}]))
    self.assertEqual(actual_batch, expected)

class ModulePathTest(unittest.TestCase):

    def test_helper_validates_kwargs(self):
        with self.assertRaises(TypeError):
            validate_kwargs({'a': 1, 'b': 2}, ['a'], 'Invalid keyword argument:')

    def test_should_return_correct_class_for_string(self):
        vl = str_to_class('evadb.readers.decord_reader.DecordReader')
        self.assertEqual(vl, DecordReader)

    def test_should_return_correct_class_for_path(self):
        vl = load_function_class_from_file('evadb/readers/decord_reader.py', 'DecordReader')
        assert vl.__qualname__ == DecordReader.__qualname__

    def test_should_return_correct_class_for_path_without_classname(self):
        vl = load_function_class_from_file('evadb/readers/decord_reader.py')
        assert vl.__qualname__ == DecordReader.__qualname__

    def test_should_raise_on_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_function_class_from_file('evadb/readers/opencv_reader_abdfdsfds.py')

    def test_should_raise_on_empty_file(self):
        Path('/tmp/empty_file.py').touch()
        with self.assertRaises(ImportError):
            load_function_class_from_file('/tmp/empty_file.py')
        Path('/tmp/empty_file.py').unlink()

    def test_should_raise_if_class_does_not_exists(self):
        with self.assertRaises(ImportError):
            load_function_class_from_file('evadb/utils/s3_utils.py')

    def test_should_raise_if_multiple_classes_exist_and_no_class_mentioned(self):
        with self.assertRaises(ImportError):
            load_function_class_from_file('evadb/utils/generic_utils.py')

    def test_should_use_torch_to_check_if_gpu_is_available(self):
        try:
            import builtins
        except ImportError:
            import __builtin__ as builtins
        realimport = builtins.__import__

        def missing_import(name, globals, locals, fromlist, level):
            if name == 'torch':
                raise ImportError
            return realimport(name, globals, locals, fromlist, level)
        builtins.__import__ = missing_import
        self.assertFalse(is_gpu_available())
        builtins.__import__ = realimport
        is_gpu_available()

    @windows_skip_marker
    def test_should_return_a_random_full_path(self):
        actual = generate_file_path(EvaDB_DATASET_DIR, 'test')
        self.assertTrue(actual.is_absolute())
        self.assertTrue(EvaDB_DATASET_DIR in str(actual.parent))

def test_should_return_correct_class_for_string(self):
    vl = str_to_class('evadb.readers.decord_reader.DecordReader')
    self.assertEqual(vl, DecordReader)

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

def helper_pre_order_match(self, cur_opr, res_opr):
    self.assertEqual(cur_opr.opr_type, res_opr.opr_type)
    self.assertEqual(len(cur_opr.children), len(res_opr.children))
    for i, child_opr in enumerate(cur_opr.children):
        self.helper_pre_order_match(child_opr, res_opr.children[i])

@pytest.mark.notparallel
class CascadeOptimizer(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video(NUM_FRAMES)

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')

    def test_logical_to_physical_function(self):
        load_query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, load_query)
        create_function_query = "CREATE FUNCTION DummyObjectDetector\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = "SELECT id, DummyObjectDetector(data)\n                    FROM MyVideo\n                    WHERE DummyObjectDetector(data).label = ['person'];\n        "
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        actual_batch.sort()
        expected = [{'myvideo.id': i * 2, 'dummyobjectdetector.label': ['person']} for i in range(NUM_FRAMES // 2)]
        expected_batch = Batch(frames=pd.DataFrame(expected))
        self.assertEqual(actual_batch, expected_batch)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

def test_logical_to_physical_function(self):
    load_query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(self.evadb, load_query)
    create_function_query = "CREATE FUNCTION DummyObjectDetector\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query = "SELECT id, DummyObjectDetector(data)\n                    FROM MyVideo\n                    WHERE DummyObjectDetector(data).label = ['person'];\n        "
    actual_batch = execute_query_fetch_all(self.evadb, select_query)
    actual_batch.sort()
    expected = [{'myvideo.id': i * 2, 'dummyobjectdetector.label': ['person']} for i in range(NUM_FRAMES // 2)]
    expected_batch = Batch(frames=pd.DataFrame(expected))
    self.assertEqual(actual_batch, expected_batch)
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

class ProjectExecutorTest(unittest.TestCase):

    def test_should_return_expr_without_table_source(self):
        constant = Batch(pd.DataFrame([1]))
        expression = [type('AbstractExpression', (), {'evaluate': lambda x: constant, 'find_all': lambda expr: []})]
        plan = type('ProjectPlan', (), {'predicate': None, 'target_list': expression})
        proj_executor = ProjectExecutor(MagicMock(), plan)
        actual = list(proj_executor.exec())[0]
        self.assertEqual(constant, actual)

def test_should_return_expr_without_table_source(self):
    constant = Batch(pd.DataFrame([1]))
    expression = [type('AbstractExpression', (), {'evaluate': lambda x: constant, 'find_all': lambda expr: []})]
    plan = type('ProjectPlan', (), {'predicate': None, 'target_list': expression})
    proj_executor = ProjectExecutor(MagicMock(), plan)
    actual = list(proj_executor.exec())[0]
    self.assertEqual(constant, actual)

class OrderByExecutorTest(unittest.TestCase):

    def test_should_return_sorted_frames(self):
        """
        data (3 batches):
        'A' 'B' 'C'
        [1, 1, 1]
        ----------
        [1, 5, 6]
        [4, 7, 10]
        ----------
        [2, 9, 7]
        [4, 1, 2]
        [4, 2, 4]
        """
        df1 = pd.DataFrame(np.array([[1, 1, 1]]), columns=['A', 'B', 'C'])
        df2 = pd.DataFrame(np.array([[1, 5, 6], [4, 7, 10]]), columns=['A', 'B', 'C'])
        df3 = pd.DataFrame(np.array([[2, 9, 7], [4, 1, 2], [4, 2, 4]]), columns=['A', 'B', 'C'])
        batches = [Batch(frames=df) for df in [df1, df2, df3]]
        'query: .... ORDER BY A ASC, B DESC '
        plan = OrderByPlan([(TupleValueExpression(col_alias='A'), ParserOrderBySortType.ASC), (TupleValueExpression(col_alias='B'), ParserOrderBySortType.DESC)])
        orderby_executor = OrderByExecutor(MagicMock(), plan)
        orderby_executor.append_child(DummyExecutor(batches))
        sorted_batches = list(orderby_executor.exec())
        '\n           A  B   C\n        0  1  5   6\n        1  1  1   1\n        2  2  9   7\n        3  4  7  10\n        4  4  2   4\n        5  4  1   2\n        '
        expected_df1 = pd.DataFrame(np.array([[1, 5, 6]]), columns=['A', 'B', 'C'])
        expected_df2 = pd.DataFrame(np.array([[1, 1, 1], [2, 9, 7]]), columns=['A', 'B', 'C'])
        expected_df3 = pd.DataFrame(np.array([[4, 7, 10], [4, 2, 4], [4, 1, 2]]), columns=['A', 'B', 'C'])
        expected_batches = [Batch(frames=df) for df in [expected_df1, expected_df2, expected_df3]]
        self.assertEqual(expected_batches[0], sorted_batches[0])
        self.assertEqual(expected_batches[1], sorted_batches[1])
        self.assertEqual(expected_batches[2], sorted_batches[2])

def test_should_return_sorted_frames(self):
    """
        data (3 batches):
        'A' 'B' 'C'
        [1, 1, 1]
        ----------
        [1, 5, 6]
        [4, 7, 10]
        ----------
        [2, 9, 7]
        [4, 1, 2]
        [4, 2, 4]
        """
    df1 = pd.DataFrame(np.array([[1, 1, 1]]), columns=['A', 'B', 'C'])
    df2 = pd.DataFrame(np.array([[1, 5, 6], [4, 7, 10]]), columns=['A', 'B', 'C'])
    df3 = pd.DataFrame(np.array([[2, 9, 7], [4, 1, 2], [4, 2, 4]]), columns=['A', 'B', 'C'])
    batches = [Batch(frames=df) for df in [df1, df2, df3]]
    'query: .... ORDER BY A ASC, B DESC '
    plan = OrderByPlan([(TupleValueExpression(col_alias='A'), ParserOrderBySortType.ASC), (TupleValueExpression(col_alias='B'), ParserOrderBySortType.DESC)])
    orderby_executor = OrderByExecutor(MagicMock(), plan)
    orderby_executor.append_child(DummyExecutor(batches))
    sorted_batches = list(orderby_executor.exec())
    '\n           A  B   C\n        0  1  5   6\n        1  1  1   1\n        2  2  9   7\n        3  4  7  10\n        4  4  2   4\n        5  4  1   2\n        '
    expected_df1 = pd.DataFrame(np.array([[1, 5, 6]]), columns=['A', 'B', 'C'])
    expected_df2 = pd.DataFrame(np.array([[1, 1, 1], [2, 9, 7]]), columns=['A', 'B', 'C'])
    expected_df3 = pd.DataFrame(np.array([[4, 7, 10], [4, 2, 4], [4, 1, 2]]), columns=['A', 'B', 'C'])
    expected_batches = [Batch(frames=df) for df in [expected_df1, expected_df2, expected_df3]]
    self.assertEqual(expected_batches[0], sorted_batches[0])
    self.assertEqual(expected_batches[1], sorted_batches[1])
    self.assertEqual(expected_batches[2], sorted_batches[2])

class LimitExecutorTest(unittest.TestCase):

    def test_should_return_smaller_num_rows(self):
        dfs = [pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')) for _ in range(4)]
        batches = [Batch(frames=df) for df in dfs]
        limit_value = 125
        plan = LimitPlan(ConstantValueExpression(limit_value))
        limit_executor = LimitExecutor(MagicMock(), plan)
        limit_executor.append_child(DummyExecutor(batches))
        reduced_batches = list(limit_executor.exec())
        total_size = 0
        for batch in reduced_batches:
            total_size += len(batch)
        self.assertEqual(total_size, limit_value)

    def test_should_return_limit_greater_than_size(self):
        """This should return the exact same data
        if the limit value is greater than what is present.
        This will also leave a warning"""
        dfs = [pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')) for _ in range(4)]
        batches = [Batch(frames=df) for df in dfs]
        previous_total_size = 0
        for batch in batches:
            previous_total_size += len(batch)
        limit_value = 500
        plan = LimitPlan(ConstantValueExpression(limit_value))
        limit_executor = LimitExecutor(MagicMock(), plan)
        limit_executor.append_child(DummyExecutor(batches))
        reduced_batches = list(limit_executor.exec())
        after_total_size = 0
        for batch in reduced_batches:
            after_total_size += len(batch)
        self.assertEqual(previous_total_size, after_total_size)

    def test_should_return_top_frames_after_sorting(self):
        """
        Checks if limit returns the top 2 rows from the data
        after sorting

        data (3 batches):
        'A' 'B' 'C'
        [1, 1, 1]
        ----------
        [1, 5, 6]
        [4, 7, 10]
        ----------
        [2, 9, 7]
        [4, 1, 2]
        [4, 2, 4]
        """
        df1 = pd.DataFrame(np.array([[1, 1, 1]]), columns=['A', 'B', 'C'])
        df2 = pd.DataFrame(np.array([[1, 5, 6], [4, 7, 10]]), columns=['A', 'B', 'C'])
        df3 = pd.DataFrame(np.array([[2, 9, 7], [4, 1, 2], [4, 2, 4]]), columns=['A', 'B', 'C'])
        batches = [Batch(frames=df) for df in [df1, df2, df3]]
        'query: .... ORDER BY A ASC, B DESC limit 2'
        plan = OrderByPlan([(TupleValueExpression(col_alias='A'), ParserOrderBySortType.ASC), (TupleValueExpression(col_alias='B'), ParserOrderBySortType.DESC)])
        orderby_executor = OrderByExecutor(MagicMock(), plan)
        orderby_executor.append_child(DummyExecutor(batches))
        sorted_batches = list(orderby_executor.exec())
        limit_value = 2
        plan = LimitPlan(ConstantValueExpression(limit_value))
        limit_executor = LimitExecutor(MagicMock(), plan)
        limit_executor.append_child(DummyExecutor(sorted_batches))
        reduced_batches = list(limit_executor.exec())
        aggregated_batch = Batch.concat(reduced_batches, copy=False)
        '\n           A  B   C\n        0  1  5   6\n        1  1  1   1\n        '
        expected_df1 = pd.DataFrame(np.array([[1, 5, 6], [1, 1, 1]]), columns=['A', 'B', 'C'])
        expected_batches = [Batch(frames=df) for df in [expected_df1]]
        self.assertEqual(expected_batches[0], aggregated_batch)

def test_should_return_smaller_num_rows(self):
    dfs = [pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')) for _ in range(4)]
    batches = [Batch(frames=df) for df in dfs]
    limit_value = 125
    plan = LimitPlan(ConstantValueExpression(limit_value))
    limit_executor = LimitExecutor(MagicMock(), plan)
    limit_executor.append_child(DummyExecutor(batches))
    reduced_batches = list(limit_executor.exec())
    total_size = 0
    for batch in reduced_batches:
        total_size += len(batch)
    self.assertEqual(total_size, limit_value)

def test_should_return_limit_greater_than_size(self):
    """This should return the exact same data
        if the limit value is greater than what is present.
        This will also leave a warning"""
    dfs = [pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')) for _ in range(4)]
    batches = [Batch(frames=df) for df in dfs]
    previous_total_size = 0
    for batch in batches:
        previous_total_size += len(batch)
    limit_value = 500
    plan = LimitPlan(ConstantValueExpression(limit_value))
    limit_executor = LimitExecutor(MagicMock(), plan)
    limit_executor.append_child(DummyExecutor(batches))
    reduced_batches = list(limit_executor.exec())
    after_total_size = 0
    for batch in reduced_batches:
        after_total_size += len(batch)
    self.assertEqual(previous_total_size, after_total_size)

def test_should_return_top_frames_after_sorting(self):
    """
        Checks if limit returns the top 2 rows from the data
        after sorting

        data (3 batches):
        'A' 'B' 'C'
        [1, 1, 1]
        ----------
        [1, 5, 6]
        [4, 7, 10]
        ----------
        [2, 9, 7]
        [4, 1, 2]
        [4, 2, 4]
        """
    df1 = pd.DataFrame(np.array([[1, 1, 1]]), columns=['A', 'B', 'C'])
    df2 = pd.DataFrame(np.array([[1, 5, 6], [4, 7, 10]]), columns=['A', 'B', 'C'])
    df3 = pd.DataFrame(np.array([[2, 9, 7], [4, 1, 2], [4, 2, 4]]), columns=['A', 'B', 'C'])
    batches = [Batch(frames=df) for df in [df1, df2, df3]]
    'query: .... ORDER BY A ASC, B DESC limit 2'
    plan = OrderByPlan([(TupleValueExpression(col_alias='A'), ParserOrderBySortType.ASC), (TupleValueExpression(col_alias='B'), ParserOrderBySortType.DESC)])
    orderby_executor = OrderByExecutor(MagicMock(), plan)
    orderby_executor.append_child(DummyExecutor(batches))
    sorted_batches = list(orderby_executor.exec())
    limit_value = 2
    plan = LimitPlan(ConstantValueExpression(limit_value))
    limit_executor = LimitExecutor(MagicMock(), plan)
    limit_executor.append_child(DummyExecutor(sorted_batches))
    reduced_batches = list(limit_executor.exec())
    aggregated_batch = Batch.concat(reduced_batches, copy=False)
    '\n           A  B   C\n        0  1  5   6\n        1  1  1   1\n        '
    expected_df1 = pd.DataFrame(np.array([[1, 5, 6], [1, 1, 1]]), columns=['A', 'B', 'C'])
    expected_batches = [Batch(frames=df) for df in [expected_df1]]
    self.assertEqual(expected_batches[0], aggregated_batch)

class SampleExecutorTest(unittest.TestCase):

    def test_should_return_smaller_num_rows(self):
        dfs = [pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')) for _ in range(4)]
        batches = [Batch(frames=df) for df in dfs]
        sample_value = 3
        plan = SamplePlan(ConstantValueExpression(sample_value))
        sample_executor = SampleExecutor(MagicMock(), plan)
        sample_executor.append_child(DummyExecutor(batches))
        reduced_batches = list(sample_executor.exec())
        original = Batch.concat(batches)
        filter = range(0, len(original), sample_value)
        original = original._get_frames_from_indices(filter)
        original = Batch.concat([original])
        reduced = Batch.concat(reduced_batches)
        self.assertEqual(len(original), len(reduced))
        self.assertEqual(original, reduced)

def test_should_return_smaller_num_rows(self):
    dfs = [pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')) for _ in range(4)]
    batches = [Batch(frames=df) for df in dfs]
    sample_value = 3
    plan = SamplePlan(ConstantValueExpression(sample_value))
    sample_executor = SampleExecutor(MagicMock(), plan)
    sample_executor.append_child(DummyExecutor(batches))
    reduced_batches = list(sample_executor.exec())
    original = Batch.concat(batches)
    filter = range(0, len(original), sample_value)
    original = original._get_frames_from_indices(filter)
    original = Batch.concat([original])
    reduced = Batch.concat(reduced_batches)
    self.assertEqual(len(original), len(reduced))
    self.assertEqual(original, reduced)

class SeqScanExecutorTest(unittest.TestCase):

    def test_should_return_only_frames_satisfy_predicate(self):
        dataframe = create_dataframe(3)
        batch = Batch(frames=dataframe)
        expression = type('AbstractExpression', (), {'evaluate': lambda x: Batch(pd.DataFrame([False, False, True])), 'find_all': lambda expr: []})
        plan = type('ScanPlan', (), {'predicate': expression, 'columns': None, 'alias': None})
        predicate_executor = SequentialScanExecutor(MagicMock(), plan)
        predicate_executor.append_child(DummyExecutor([batch]))
        expected = Batch(batch.frames[batch.frames.index == 2].reset_index(drop=True))
        filtered = list(predicate_executor.exec())[0]
        self.assertEqual(expected, filtered)

    def test_should_return_all_frames_when_no_predicate_is_applied(self):
        dataframe = create_dataframe(3)
        batch = Batch(frames=dataframe)
        plan = type('ScanPlan', (), {'predicate': None, 'columns': None, 'alias': None})
        predicate_executor = SequentialScanExecutor(MagicMock(), plan)
        predicate_executor.append_child(DummyExecutor([batch]))
        filtered = list(predicate_executor.exec())[0]
        self.assertEqual(batch, filtered)

    def test_should_return_projected_columns(self):
        dataframe = create_dataframe(3)
        batch = Batch(frames=dataframe)
        proj_batch = Batch(frames=pd.DataFrame(dataframe['data']))
        expression = [type('AbstractExpression', (), {'evaluate': lambda x: Batch(pd.DataFrame(x.frames['data'])), 'find_all': lambda expr: []})]
        plan = type('ScanPlan', (), {'predicate': None, 'columns': expression, 'alias': None})
        proj_executor = SequentialScanExecutor(MagicMock(), plan)
        proj_executor.append_child(DummyExecutor([batch]))
        actual = list(proj_executor.exec())[0]
        self.assertEqual(proj_batch, actual)

def test_should_return_only_frames_satisfy_predicate(self):
    dataframe = create_dataframe(3)
    batch = Batch(frames=dataframe)
    expression = type('AbstractExpression', (), {'evaluate': lambda x: Batch(pd.DataFrame([False, False, True])), 'find_all': lambda expr: []})
    plan = type('ScanPlan', (), {'predicate': expression, 'columns': None, 'alias': None})
    predicate_executor = SequentialScanExecutor(MagicMock(), plan)
    predicate_executor.append_child(DummyExecutor([batch]))
    expected = Batch(batch.frames[batch.frames.index == 2].reset_index(drop=True))
    filtered = list(predicate_executor.exec())[0]
    self.assertEqual(expected, filtered)

def test_should_return_all_frames_when_no_predicate_is_applied(self):
    dataframe = create_dataframe(3)
    batch = Batch(frames=dataframe)
    plan = type('ScanPlan', (), {'predicate': None, 'columns': None, 'alias': None})
    predicate_executor = SequentialScanExecutor(MagicMock(), plan)
    predicate_executor.append_child(DummyExecutor([batch]))
    filtered = list(predicate_executor.exec())[0]
    self.assertEqual(batch, filtered)

def test_should_return_projected_columns(self):
    dataframe = create_dataframe(3)
    batch = Batch(frames=dataframe)
    proj_batch = Batch(frames=pd.DataFrame(dataframe['data']))
    expression = [type('AbstractExpression', (), {'evaluate': lambda x: Batch(pd.DataFrame(x.frames['data'])), 'find_all': lambda expr: []})]
    plan = type('ScanPlan', (), {'predicate': None, 'columns': expression, 'alias': None})
    proj_executor = SequentialScanExecutor(MagicMock(), plan)
    proj_executor.append_child(DummyExecutor([batch]))
    actual = list(proj_executor.exec())[0]
    self.assertEqual(proj_batch, actual)

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

class ExpressionEvaluationTest(unittest.TestCase):

    def test_if_expr_tree_is_equal(self):
        const_exp1 = ConstantValueExpression(0)
        const_exp2 = ConstantValueExpression(0)
        columnName1 = TupleValueExpression(name='DATA')
        columnName2 = TupleValueExpression(name='DATA')
        aggr_expr1 = AggregationExpression(ExpressionType.AGGREGATION_AVG, None, columnName1)
        aggr_expr2 = AggregationExpression(ExpressionType.AGGREGATION_AVG, None, columnName2)
        cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_NEQ, aggr_expr1, const_exp1)
        cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_NEQ, aggr_expr2, const_exp2)
        self.assertEqual(cmpr_exp1, cmpr_exp2)

    def test_should_return_false_for_unequal_expressions(self):
        const_exp1 = ConstantValueExpression(0)
        const_exp2 = ConstantValueExpression(1)
        func_expr = FunctionExpression(lambda x: x + 1, name='test')
        cmpr_exp = ComparisonExpression(ExpressionType.COMPARE_NEQ, const_exp1, const_exp2)
        tuple_expr = TupleValueExpression(name='id')
        aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_MAX, None, tuple_expr)
        logical_expr = LogicalExpression(ExpressionType.LOGICAL_OR, cmpr_exp, cmpr_exp)
        self.assertNotEqual(const_exp1, const_exp2)
        self.assertNotEqual(cmpr_exp, const_exp1)
        self.assertNotEqual(func_expr, cmpr_exp)
        self.assertNotEqual(tuple_expr, aggr_expr)
        self.assertNotEqual(aggr_expr, tuple_expr)
        self.assertNotEqual(tuple_expr, cmpr_exp)
        self.assertNotEqual(logical_expr, cmpr_exp)

def test_if_expr_tree_is_equal(self):
    const_exp1 = ConstantValueExpression(0)
    const_exp2 = ConstantValueExpression(0)
    columnName1 = TupleValueExpression(name='DATA')
    columnName2 = TupleValueExpression(name='DATA')
    aggr_expr1 = AggregationExpression(ExpressionType.AGGREGATION_AVG, None, columnName1)
    aggr_expr2 = AggregationExpression(ExpressionType.AGGREGATION_AVG, None, columnName2)
    cmpr_exp1 = ComparisonExpression(ExpressionType.COMPARE_NEQ, aggr_expr1, const_exp1)
    cmpr_exp2 = ComparisonExpression(ExpressionType.COMPARE_NEQ, aggr_expr2, const_exp2)
    self.assertEqual(cmpr_exp1, cmpr_exp2)

def test_should_return_false_for_unequal_expressions(self):
    const_exp1 = ConstantValueExpression(0)
    const_exp2 = ConstantValueExpression(1)
    func_expr = FunctionExpression(lambda x: x + 1, name='test')
    cmpr_exp = ComparisonExpression(ExpressionType.COMPARE_NEQ, const_exp1, const_exp2)
    tuple_expr = TupleValueExpression(name='id')
    aggr_expr = AggregationExpression(ExpressionType.AGGREGATION_MAX, None, tuple_expr)
    logical_expr = LogicalExpression(ExpressionType.LOGICAL_OR, cmpr_exp, cmpr_exp)
    self.assertNotEqual(const_exp1, const_exp2)
    self.assertNotEqual(cmpr_exp, const_exp1)
    self.assertNotEqual(func_expr, cmpr_exp)
    self.assertNotEqual(tuple_expr, aggr_expr)
    self.assertNotEqual(aggr_expr, tuple_expr)
    self.assertNotEqual(tuple_expr, cmpr_exp)
    self.assertNotEqual(logical_expr, cmpr_exp)

class ConstantExpressionsTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_constant_with_input_relationship(self):
        const_expr = ConstantValueExpression(1)
        input_size = 10
        self.assertEqual([1] * input_size, const_expr.evaluate(Batch(pd.DataFrame([0] * input_size))).frames[0].tolist())

def test_constant_with_input_relationship(self):
    const_expr = ConstantValueExpression(1)
    input_size = 10
    self.assertEqual([1] * input_size, const_expr.evaluate(Batch(pd.DataFrame([0] * input_size))).frames[0].tolist())

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

class ExpressionUtilsTest(unittest.TestCase):

    def gen_cmp_expr(self, val, expr_type=ExpressionType.COMPARE_GREATER, name='id', const_first=False):
        constexpr = ConstantValueExpression(val)
        colname = TupleValueExpression(name=name, col_alias=f'T.{name}')
        if const_first:
            return ComparisonExpression(expr_type, constexpr, colname)
        return ComparisonExpression(expr_type, colname, constexpr)

    def test_extract_range_list_from_comparison_expr(self):
        expr_types = [ExpressionType.COMPARE_NEQ, ExpressionType.COMPARE_EQUAL, ExpressionType.COMPARE_GREATER, ExpressionType.COMPARE_LESSER, ExpressionType.COMPARE_GEQ, ExpressionType.COMPARE_LEQ]
        results = []
        for expr_type in expr_types:
            cmpr_exp = self.gen_cmp_expr(10, expr_type, const_first=True)
            results.append(extract_range_list_from_comparison_expr(cmpr_exp, 0, 100))
        expected = [[(0, 9), (11, 100)], [(10, 10)], [(0, 9)], [(11, 100)], [(0, 10)], [(10, 100)]]
        self.assertEqual(results, expected)
        results = []
        for expr_type in expr_types:
            cmpr_exp = self.gen_cmp_expr(10, expr_type)
            results.append(extract_range_list_from_comparison_expr(cmpr_exp, 0, 100))
        expected = [[(0, 9), (11, 100)], [(10, 10)], [(11, 100)], [(0, 9)], [(10, 100)], [(0, 10)]]
        self.assertEqual(results, expected)
        with self.assertRaises(RuntimeError):
            cmpr_exp = LogicalExpression(ExpressionType.LOGICAL_AND, Mock(), Mock())
            extract_range_list_from_comparison_expr(cmpr_exp, 0, 100)
        with self.assertRaises(RuntimeError):
            cmpr_exp = self.gen_cmp_expr(10, ExpressionType.COMPARE_CONTAINS)
            extract_range_list_from_comparison_expr(cmpr_exp, 0, 100)
        with self.assertRaises(RuntimeError):
            cmpr_exp = self.gen_cmp_expr(10, ExpressionType.COMPARE_IS_CONTAINED)
            extract_range_list_from_comparison_expr(cmpr_exp, 0, 100)

    def test_extract_range_list_from_predicate(self):
        expr = LogicalExpression(ExpressionType.LOGICAL_AND, self.gen_cmp_expr(10), self.gen_cmp_expr(20))
        self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(21, 100)])
        expr = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10), self.gen_cmp_expr(20))
        self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(11, 100)])
        expr1 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10), self.gen_cmp_expr(20))
        expr2 = LogicalExpression(ExpressionType.LOGICAL_AND, self.gen_cmp_expr(10), self.gen_cmp_expr(5, ExpressionType.COMPARE_LESSER))
        expr = LogicalExpression(ExpressionType.LOGICAL_OR, expr1, expr2)
        self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(11, 100)])
        expr = LogicalExpression(ExpressionType.LOGICAL_AND, expr1, expr2)
        self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [])
        expr1 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_LESSER), self.gen_cmp_expr(20))
        expr2 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(25), self.gen_cmp_expr(5, ExpressionType.COMPARE_LESSER))
        expr = LogicalExpression(ExpressionType.LOGICAL_OR, expr1, expr2)
        self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(0, 9), (21, 100)])
        with self.assertRaises(RuntimeError):
            expr = ArithmeticExpression(ExpressionType.AGGREGATION_COUNT, Mock(), Mock())
            extract_range_list_from_predicate(expr, 0, 100)

    def test_predicate_contains_single_column(self):
        self.assertTrue(contains_single_column(self.gen_cmp_expr(10)))
        expr1 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'), self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'))
        self.assertTrue(contains_single_column(expr1))
        expr2 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'), self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'y'))
        self.assertFalse(contains_single_column(expr2))
        expr = LogicalExpression(ExpressionType.LOGICAL_OR, expr1, expr2)
        self.assertFalse(contains_single_column(expr))

    def test_is_simple_predicate(self):
        self.assertTrue(is_simple_predicate(self.gen_cmp_expr(10)))
        expr = ArithmeticExpression(ExpressionType.AGGREGATION_COUNT, Mock(), Mock())
        self.assertFalse(is_simple_predicate(expr))
        expr = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'), self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'y'))
        self.assertFalse(is_simple_predicate(expr))

    def test_and_(self):
        expr1 = self.gen_cmp_expr(10)
        expr2 = self.gen_cmp_expr(20)
        new_expr = conjunction_list_to_expression_tree([expr1, expr2])
        self.assertEqual(new_expr.etype, ExpressionType.LOGICAL_AND)
        self.assertEqual(new_expr.children[0], expr1)
        self.assertEqual(new_expr.children[1], expr2)

def gen_cmp_expr(self, val, expr_type=ExpressionType.COMPARE_GREATER, name='id', const_first=False):
    constexpr = ConstantValueExpression(val)
    colname = TupleValueExpression(name=name, col_alias=f'T.{name}')
    if const_first:
        return ComparisonExpression(expr_type, constexpr, colname)
    return ComparisonExpression(expr_type, colname, constexpr)

def test_extract_range_list_from_comparison_expr(self):
    expr_types = [ExpressionType.COMPARE_NEQ, ExpressionType.COMPARE_EQUAL, ExpressionType.COMPARE_GREATER, ExpressionType.COMPARE_LESSER, ExpressionType.COMPARE_GEQ, ExpressionType.COMPARE_LEQ]
    results = []
    for expr_type in expr_types:
        cmpr_exp = self.gen_cmp_expr(10, expr_type, const_first=True)
        results.append(extract_range_list_from_comparison_expr(cmpr_exp, 0, 100))
    expected = [[(0, 9), (11, 100)], [(10, 10)], [(0, 9)], [(11, 100)], [(0, 10)], [(10, 100)]]
    self.assertEqual(results, expected)
    results = []
    for expr_type in expr_types:
        cmpr_exp = self.gen_cmp_expr(10, expr_type)
        results.append(extract_range_list_from_comparison_expr(cmpr_exp, 0, 100))
    expected = [[(0, 9), (11, 100)], [(10, 10)], [(11, 100)], [(0, 9)], [(10, 100)], [(0, 10)]]
    self.assertEqual(results, expected)
    with self.assertRaises(RuntimeError):
        cmpr_exp = LogicalExpression(ExpressionType.LOGICAL_AND, Mock(), Mock())
        extract_range_list_from_comparison_expr(cmpr_exp, 0, 100)
    with self.assertRaises(RuntimeError):
        cmpr_exp = self.gen_cmp_expr(10, ExpressionType.COMPARE_CONTAINS)
        extract_range_list_from_comparison_expr(cmpr_exp, 0, 100)
    with self.assertRaises(RuntimeError):
        cmpr_exp = self.gen_cmp_expr(10, ExpressionType.COMPARE_IS_CONTAINED)
        extract_range_list_from_comparison_expr(cmpr_exp, 0, 100)

def test_extract_range_list_from_predicate(self):
    expr = LogicalExpression(ExpressionType.LOGICAL_AND, self.gen_cmp_expr(10), self.gen_cmp_expr(20))
    self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(21, 100)])
    expr = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10), self.gen_cmp_expr(20))
    self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(11, 100)])
    expr1 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10), self.gen_cmp_expr(20))
    expr2 = LogicalExpression(ExpressionType.LOGICAL_AND, self.gen_cmp_expr(10), self.gen_cmp_expr(5, ExpressionType.COMPARE_LESSER))
    expr = LogicalExpression(ExpressionType.LOGICAL_OR, expr1, expr2)
    self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(11, 100)])
    expr = LogicalExpression(ExpressionType.LOGICAL_AND, expr1, expr2)
    self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [])
    expr1 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_LESSER), self.gen_cmp_expr(20))
    expr2 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(25), self.gen_cmp_expr(5, ExpressionType.COMPARE_LESSER))
    expr = LogicalExpression(ExpressionType.LOGICAL_OR, expr1, expr2)
    self.assertEqual(extract_range_list_from_predicate(expr, 0, 100), [(0, 9), (21, 100)])
    with self.assertRaises(RuntimeError):
        expr = ArithmeticExpression(ExpressionType.AGGREGATION_COUNT, Mock(), Mock())
        extract_range_list_from_predicate(expr, 0, 100)

def test_predicate_contains_single_column(self):
    self.assertTrue(contains_single_column(self.gen_cmp_expr(10)))
    expr1 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'), self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'))
    self.assertTrue(contains_single_column(expr1))
    expr2 = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'), self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'y'))
    self.assertFalse(contains_single_column(expr2))
    expr = LogicalExpression(ExpressionType.LOGICAL_OR, expr1, expr2)
    self.assertFalse(contains_single_column(expr))

def test_is_simple_predicate(self):
    self.assertTrue(is_simple_predicate(self.gen_cmp_expr(10)))
    expr = ArithmeticExpression(ExpressionType.AGGREGATION_COUNT, Mock(), Mock())
    self.assertFalse(is_simple_predicate(expr))
    expr = LogicalExpression(ExpressionType.LOGICAL_OR, self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'x'), self.gen_cmp_expr(10, ExpressionType.COMPARE_GREATER, 'y'))
    self.assertFalse(is_simple_predicate(expr))

def test_and_(self):
    expr1 = self.gen_cmp_expr(10)
    expr2 = self.gen_cmp_expr(20)
    new_expr = conjunction_list_to_expression_tree([expr1, expr2])
    self.assertEqual(new_expr.etype, ExpressionType.LOGICAL_AND)
    self.assertEqual(new_expr.children[0], expr1)
    self.assertEqual(new_expr.children[1], expr2)

class FunctionExpressionTest(unittest.TestCase):

    @patch('evadb.expression.function_expression.Context')
    def test_function_move_the_device_to_gpu_if_compatible(self, context):
        context_instance = context.return_value
        mock_function = MagicMock(spec=GPUCompatible)
        gpu_mock_function = Mock(return_value=pd.DataFrame())
        gpu_device_id = '2'
        mock_function.to_device.return_value = gpu_mock_function
        context_instance.gpu_device.return_value = gpu_device_id
        expression = FunctionExpression(lambda: mock_function, name='test', alias=Alias('func_expr'))
        input_batch = Batch(frames=pd.DataFrame())
        expression.evaluate(input_batch)
        mock_function.to_device.assert_called_with(gpu_device_id)
        gpu_mock_function.assert_called()

    def test_should_use_the_same_function_if_not_gpu_compatible(self):
        mock_function = MagicMock(return_value=pd.DataFrame())
        expression = FunctionExpression(lambda: mock_function, name='test', alias=Alias('func_expr'))
        input_batch = Batch(frames=pd.DataFrame())
        expression.evaluate(input_batch)
        mock_function.assert_called()

    @patch('evadb.expression.function_expression.Context')
    def test_should_execute_same_function_if_no_gpu(self, context):
        context_instance = context.return_value
        mock_function = MagicMock(spec=GPUCompatible, return_value=pd.DataFrame())
        context_instance.gpu_device.return_value = NO_GPU
        expression = FunctionExpression(lambda: mock_function, name='test', alias=Alias('func_expr'))
        input_batch = Batch(frames=pd.DataFrame())
        expression.evaluate(input_batch)
        mock_function.assert_called()

@patch('evadb.expression.function_expression.Context')
def test_function_move_the_device_to_gpu_if_compatible(self, context):
    context_instance = context.return_value
    mock_function = MagicMock(spec=GPUCompatible)
    gpu_mock_function = Mock(return_value=pd.DataFrame())
    gpu_device_id = '2'
    mock_function.to_device.return_value = gpu_mock_function
    context_instance.gpu_device.return_value = gpu_device_id
    expression = FunctionExpression(lambda: mock_function, name='test', alias=Alias('func_expr'))
    input_batch = Batch(frames=pd.DataFrame())
    expression.evaluate(input_batch)
    mock_function.to_device.assert_called_with(gpu_device_id)
    gpu_mock_function.assert_called()

def test_should_use_the_same_function_if_not_gpu_compatible(self):
    mock_function = MagicMock(return_value=pd.DataFrame())
    expression = FunctionExpression(lambda: mock_function, name='test', alias=Alias('func_expr'))
    input_batch = Batch(frames=pd.DataFrame())
    expression.evaluate(input_batch)
    mock_function.assert_called()

@patch('evadb.expression.function_expression.Context')
def test_should_execute_same_function_if_no_gpu(self, context):
    context_instance = context.return_value
    mock_function = MagicMock(spec=GPUCompatible, return_value=pd.DataFrame())
    context_instance.gpu_device.return_value = NO_GPU
    expression = FunctionExpression(lambda: mock_function, name='test', alias=Alias('func_expr'))
    input_batch = Batch(frames=pd.DataFrame())
    expression.evaluate(input_batch)
    mock_function.assert_called()

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

def test_forward_flags_are_updated(self):
    input_type = PandasDataframe(columns=['Frame_Array'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256)])
    output_type = NumpyArray(name='label', type=NdArrayType.STR)

    @forward(input_signatures=[input_type], output_signatures=[output_type])
    def forward_func():
        pass
    forward_func()
    self.assertEqual(forward_func.tags['input'], [input_type])
    self.assertEqual(forward_func.tags['output'], [output_type])

@forward(input_signatures=[input_type], output_signatures=[output_type])
def forward_func():
    pass

class FunctionIODescriptorsTests(unittest.TestCase):

    def test_catalog_entry_for_numpy_entry(self):
        numpy_array = NumpyArray(name='input', is_nullable=False, type=NdArrayType.UINT8, dimensions=(2, 2))
        catalog_entries = numpy_array.generate_catalog_entries()
        self.assertEqual(len(catalog_entries), 1)
        catalog_entry = catalog_entries[0]
        self.assertEqual(catalog_entry.name, 'input')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
        self.assertEqual(catalog_entry.array_dimensions, (2, 2))
        self.assertEqual(catalog_entry.is_input, False)

    def test_catalog_entry_for_pytorch_entry(self):
        pytorch_tensor = PyTorchTensor(name='input', is_nullable=False, type=NdArrayType.UINT8, dimensions=(2, 2))
        catalog_entries = pytorch_tensor.generate_catalog_entries()
        self.assertEqual(len(catalog_entries), 1)
        catalog_entry = catalog_entries[0]
        self.assertEqual(catalog_entry.name, 'input')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
        self.assertEqual(catalog_entry.array_dimensions, (2, 2))
        self.assertEqual(catalog_entry.is_input, False)

    def test_catalog_entry_for_pandas_entry_with_single_column_simple(self):
        pandas_dataframe = PandasDataframe(columns=['Frame_Array'])
        catalog_entries = pandas_dataframe.generate_catalog_entries()
        self.assertEqual(len(catalog_entries), 1)
        catalog_entry = catalog_entries[0]
        self.assertEqual(catalog_entry.name, 'Frame_Array')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.ANYTYPE)
        self.assertEqual(catalog_entry.array_dimensions, Dimension.ANYDIM)

    def test_catalog_entry_for_pandas_entry_with_single_column(self):
        pandas_dataframe = PandasDataframe(columns=['Frame_Array'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256)])
        catalog_entries = pandas_dataframe.generate_catalog_entries()
        self.assertEqual(len(catalog_entries), 1)
        catalog_entry = catalog_entries[0]
        self.assertEqual(catalog_entry.name, 'Frame_Array')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
        self.assertEqual(catalog_entry.array_dimensions, (3, 256, 256))
        self.assertEqual(catalog_entry.is_input, False)

    def test_catalog_entry_for_pandas_entry_with_multiple_columns_simple(self):
        pandas_dataframe = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'])
        catalog_entries = pandas_dataframe.generate_catalog_entries()
        self.assertEqual(len(catalog_entries), 2)
        catalog_entry = catalog_entries[0]
        self.assertEqual(catalog_entry.name, 'Frame_Array')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.ANYTYPE)
        self.assertEqual(catalog_entry.array_dimensions, Dimension.ANYDIM)
        catalog_entry = catalog_entries[1]
        self.assertEqual(catalog_entry.name, 'Frame_Array_2')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.ANYTYPE)
        self.assertEqual(catalog_entry.array_dimensions, Dimension.ANYDIM)

    def test_catalog_entry_for_pandas_entry_with_multiple_columns(self):
        pandas_dataframe = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'], column_types=[NdArrayType.UINT8, NdArrayType.FLOAT32], column_shapes=[(3, 256, 256), (3, 256, 256)])
        catalog_entries = pandas_dataframe.generate_catalog_entries()
        self.assertEqual(len(catalog_entries), 2)
        catalog_entry = catalog_entries[0]
        self.assertEqual(catalog_entry.name, 'Frame_Array')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
        self.assertEqual(catalog_entry.array_dimensions, (3, 256, 256))
        self.assertEqual(catalog_entry.is_input, False)
        catalog_entry = catalog_entries[1]
        self.assertEqual(catalog_entry.name, 'Frame_Array_2')
        self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
        self.assertEqual(catalog_entry.is_nullable, False)
        self.assertEqual(catalog_entry.array_type, NdArrayType.FLOAT32)
        self.assertEqual(catalog_entry.array_dimensions, (3, 256, 256))
        self.assertEqual(catalog_entry.is_input, False)

    def test_raises_error_on_incorrect_pandas_definition(self):
        pandas_dataframe = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256), (3, 256, 256)])
        with self.assertRaises(FunctionIODefinitionError):
            pandas_dataframe.generate_catalog_entries()

def test_catalog_entry_for_numpy_entry(self):
    numpy_array = NumpyArray(name='input', is_nullable=False, type=NdArrayType.UINT8, dimensions=(2, 2))
    catalog_entries = numpy_array.generate_catalog_entries()
    self.assertEqual(len(catalog_entries), 1)
    catalog_entry = catalog_entries[0]
    self.assertEqual(catalog_entry.name, 'input')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
    self.assertEqual(catalog_entry.array_dimensions, (2, 2))
    self.assertEqual(catalog_entry.is_input, False)

def test_catalog_entry_for_pytorch_entry(self):
    pytorch_tensor = PyTorchTensor(name='input', is_nullable=False, type=NdArrayType.UINT8, dimensions=(2, 2))
    catalog_entries = pytorch_tensor.generate_catalog_entries()
    self.assertEqual(len(catalog_entries), 1)
    catalog_entry = catalog_entries[0]
    self.assertEqual(catalog_entry.name, 'input')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
    self.assertEqual(catalog_entry.array_dimensions, (2, 2))
    self.assertEqual(catalog_entry.is_input, False)

def test_catalog_entry_for_pandas_entry_with_single_column_simple(self):
    pandas_dataframe = PandasDataframe(columns=['Frame_Array'])
    catalog_entries = pandas_dataframe.generate_catalog_entries()
    self.assertEqual(len(catalog_entries), 1)
    catalog_entry = catalog_entries[0]
    self.assertEqual(catalog_entry.name, 'Frame_Array')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.ANYTYPE)
    self.assertEqual(catalog_entry.array_dimensions, Dimension.ANYDIM)

def test_catalog_entry_for_pandas_entry_with_single_column(self):
    pandas_dataframe = PandasDataframe(columns=['Frame_Array'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256)])
    catalog_entries = pandas_dataframe.generate_catalog_entries()
    self.assertEqual(len(catalog_entries), 1)
    catalog_entry = catalog_entries[0]
    self.assertEqual(catalog_entry.name, 'Frame_Array')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
    self.assertEqual(catalog_entry.array_dimensions, (3, 256, 256))
    self.assertEqual(catalog_entry.is_input, False)

def test_catalog_entry_for_pandas_entry_with_multiple_columns_simple(self):
    pandas_dataframe = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'])
    catalog_entries = pandas_dataframe.generate_catalog_entries()
    self.assertEqual(len(catalog_entries), 2)
    catalog_entry = catalog_entries[0]
    self.assertEqual(catalog_entry.name, 'Frame_Array')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.ANYTYPE)
    self.assertEqual(catalog_entry.array_dimensions, Dimension.ANYDIM)
    catalog_entry = catalog_entries[1]
    self.assertEqual(catalog_entry.name, 'Frame_Array_2')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.ANYTYPE)
    self.assertEqual(catalog_entry.array_dimensions, Dimension.ANYDIM)

def test_catalog_entry_for_pandas_entry_with_multiple_columns(self):
    pandas_dataframe = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'], column_types=[NdArrayType.UINT8, NdArrayType.FLOAT32], column_shapes=[(3, 256, 256), (3, 256, 256)])
    catalog_entries = pandas_dataframe.generate_catalog_entries()
    self.assertEqual(len(catalog_entries), 2)
    catalog_entry = catalog_entries[0]
    self.assertEqual(catalog_entry.name, 'Frame_Array')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.UINT8)
    self.assertEqual(catalog_entry.array_dimensions, (3, 256, 256))
    self.assertEqual(catalog_entry.is_input, False)
    catalog_entry = catalog_entries[1]
    self.assertEqual(catalog_entry.name, 'Frame_Array_2')
    self.assertEqual(catalog_entry.type, ColumnType.NDARRAY)
    self.assertEqual(catalog_entry.is_nullable, False)
    self.assertEqual(catalog_entry.array_type, NdArrayType.FLOAT32)
    self.assertEqual(catalog_entry.array_dimensions, (3, 256, 256))
    self.assertEqual(catalog_entry.is_input, False)

def test_raises_error_on_incorrect_pandas_definition(self):
    pandas_dataframe = PandasDataframe(columns=['Frame_Array', 'Frame_Array_2'], column_types=[NdArrayType.UINT8], column_shapes=[(3, 256, 256), (3, 256, 256)])
    with self.assertRaises(FunctionIODefinitionError):
        pandas_dataframe.generate_catalog_entries()

class ResponseTest(unittest.TestCase):

    def test_server_response_serialize_deserialize(self):
        batch = Batch(frames=create_dataframe())
        response = Response(status=ResponseStatus.SUCCESS, batch=batch)
        response2 = Response.deserialize(response.serialize())
        self.assertEqual(response, response2)

def test_server_response_serialize_deserialize(self):
    batch = Batch(frames=create_dataframe())
    response = Response(status=ResponseStatus.SUCCESS, batch=batch)
    response2 = Response.deserialize(response.serialize())
    self.assertEqual(response, response2)

class FrameInfoTest(unittest.TestCase):

    def test_frame_info_equality(self):
        info1 = FrameInfo(height=250, width=250, channels=3, color_space=ColorSpace.GRAY)
        info2 = FrameInfo(250, 250, 3, color_space=ColorSpace.GRAY)
        self.assertEqual(info1, info2)

def test_frame_info_equality(self):
    info1 = FrameInfo(height=250, width=250, channels=3, color_space=ColorSpace.GRAY)
    info2 = FrameInfo(250, 250, 3, color_space=ColorSpace.GRAY)
    self.assertEqual(info1, info2)

class BatchTest(unittest.TestCase):

    def test_batch_serialize_deserialize(self):
        batch = Batch(frames=create_dataframe())
        batch2 = Batch.deserialize(batch.serialize())
        self.assertEqual(batch, batch2)

    def test_frames_as_numpy_array_should_frames_as_numpy_array(self):
        batch = Batch(frames=create_dataframe_same(2))
        expected = list(np.ones((2, 1, 1)))
        actual = list(batch.column_as_numpy_array(batch.columns[0]))
        self.assertEqual(expected, actual)

    def test_return_only_frames_specified_in_the_indices(self):
        batch = Batch(frames=create_dataframe(2))
        expected = Batch(frames=create_dataframe())
        output = batch[[0]]
        self.assertEqual(expected, output)

    def test_fetching_frames_by_index(self):
        batch = Batch(frames=create_dataframe_same(2))
        expected = Batch(frames=create_dataframe())
        self.assertEqual(expected, batch[0])

    def test_fetching_frames_by_index_should_raise(self):
        batch = Batch(frames=create_dataframe_same(2))
        with self.assertRaises(TypeError):
            batch[1.0]

    def test_slicing_on_batched_should_return_new_batch_frame(self):
        batch = Batch(frames=create_dataframe(2))
        expected = Batch(frames=create_dataframe())
        self.assertEqual(batch, batch[:])
        self.assertEqual(expected, batch[:-1])

    def test_slicing_should_word_for_negative_stop_value(self):
        batch = Batch(frames=create_dataframe(2))
        expected = Batch(frames=create_dataframe())
        self.assertEqual(expected, batch[:-1])

    def test_slicing_should_work_with_skip_value(self):
        batch = Batch(frames=create_dataframe(3))
        expected = Batch(frames=create_dataframe(3).iloc[[0, 2], :])
        self.assertEqual(expected, batch[::2])

    def test_add_should_raise_error_for_incompatible_type(self):
        batch = Batch(frames=create_dataframe())
        with self.assertRaises(TypeError):
            batch + 1

    def test_adding_to_empty_frame_batch_returns_itself(self):
        batch_1 = Batch(frames=pd.DataFrame())
        batch_2 = Batch(frames=create_dataframe())
        self.assertEqual(batch_2, batch_1 + batch_2)
        self.assertEqual(batch_2, batch_2 + batch_1)

    def test_adding_batch_frame_with_outcomes_returns_new_batch_frame(self):
        batch_1 = Batch(frames=create_dataframe())
        batch_2 = Batch(frames=create_dataframe())
        batch_3 = Batch(frames=create_dataframe_same(2))
        self.assertEqual(batch_3, batch_1 + batch_2)

    def test_concat_batch(self):
        batch_1 = Batch(frames=create_dataframe())
        batch_2 = Batch(frames=create_dataframe())
        batch_3 = Batch(frames=create_dataframe_same(2))
        self.assertEqual(batch_3, Batch.concat([batch_1, batch_2], copy=False))

    def test_concat_empty_batch_list_raise_exception(self):
        self.assertEqual(Batch(), Batch.concat([]))

    def test_project_batch_frame(self):
        batch_1 = Batch(frames=pd.DataFrame([{'id': 1, 'data': 2, 'info': 3}]))
        batch_2 = batch_1.project(['id', 'info'])
        batch_3 = Batch(frames=pd.DataFrame([{'id': 1, 'info': 3}]))
        self.assertEqual(batch_2, batch_3)

    def test_merge_column_wise_batch_frame(self):
        batch_1 = Batch(frames=pd.DataFrame([{'id': 0}]))
        batch_2 = Batch(frames=pd.DataFrame([{'data': 1}]))
        batch_3 = Batch.merge_column_wise([batch_1, batch_2])
        batch_4 = Batch(frames=pd.DataFrame([{'id': 0, 'data': 1}]))
        self.assertEqual(batch_3, batch_4)
        self.assertEqual(Batch.merge_column_wise([]), Batch())
        batch_1 = Batch(frames=pd.DataFrame({'id': [0, None, 1]}))
        batch_2 = Batch(frames=pd.DataFrame({'data': [None, 0, None]}))
        batch_res = Batch(frames=pd.DataFrame({'id': [0, None, 1], 'data': [None, 0, None]}))
        self.assertEqual(Batch.merge_column_wise([batch_1, batch_2]), batch_res)
        df_1 = pd.DataFrame({'id': [-10, 1, 2]})
        df_2 = pd.DataFrame({'data': [-20, 2, 3]})
        df_1 = df_1[df_1 < 0].dropna()
        df_1.reset_index(drop=True, inplace=True)
        df_2 = df_2[df_2 < 0].dropna()
        df_2.reset_index(drop=True, inplace=True)
        batch_1 = Batch(frames=df_1)
        batch_2 = Batch(frames=df_2)
        df_res = pd.DataFrame({'id': [-10, 1, 2], 'data': [-20, 2, 3]})
        df_res = df_res[df_res < 0].dropna()
        df_res.reset_index(drop=True, inplace=True)
        batch_res = Batch(frames=df_res)
        self.assertEqual(Batch.merge_column_wise([batch_1, batch_2]), batch_res)

    def test_should_fail_for_list(self):
        frames = [{'id': 0, 'data': [1, 2]}, {'id': 1, 'data': [1, 2]}]
        self.assertRaises(ValueError, Batch, frames)

    def test_should_fail_for_dict(self):
        frames = {'id': 0, 'data': [1, 2]}
        self.assertRaises(ValueError, Batch, frames)

    def test_should_return_correct_length(self):
        batch = Batch(create_dataframe(5))
        self.assertEqual(5, len(batch))

    def test_should_return_empty_dataframe(self):
        batch = Batch()
        self.assertEqual(batch, Batch(create_dataframe(0)))

    def test_stack_batch_more_than_one_column_should_raise_exception(self):
        batch = Batch(create_dataframe_same(2))
        self.assertRaises(ValueError, Batch.stack, batch)

    def test_modify_column_alias_should_raise_exception(self):
        batch = Batch(create_dataframe(5))
        dummy_alias = Alias('dummy', col_names=['t1'])
        with self.assertRaises(RuntimeError):
            batch.modify_column_alias(dummy_alias)

    def test_drop_column_alias_should_work_on_frame_without_alias(self):
        batch = Batch(create_dataframe(5))
        batch.drop_column_alias()

    def test_sort_orderby_should_raise_exception_on_missing_column(self):
        batch = Batch(create_dataframe(5))
        with self.assertRaises(AssertionError):
            batch.sort_orderby(by=['foo'])

def test_batch_serialize_deserialize(self):
    batch = Batch(frames=create_dataframe())
    batch2 = Batch.deserialize(batch.serialize())
    self.assertEqual(batch, batch2)

def test_frames_as_numpy_array_should_frames_as_numpy_array(self):
    batch = Batch(frames=create_dataframe_same(2))
    expected = list(np.ones((2, 1, 1)))
    actual = list(batch.column_as_numpy_array(batch.columns[0]))
    self.assertEqual(expected, actual)

def test_return_only_frames_specified_in_the_indices(self):
    batch = Batch(frames=create_dataframe(2))
    expected = Batch(frames=create_dataframe())
    output = batch[[0]]
    self.assertEqual(expected, output)

def test_fetching_frames_by_index(self):
    batch = Batch(frames=create_dataframe_same(2))
    expected = Batch(frames=create_dataframe())
    self.assertEqual(expected, batch[0])

def test_fetching_frames_by_index_should_raise(self):
    batch = Batch(frames=create_dataframe_same(2))
    with self.assertRaises(TypeError):
        batch[1.0]

def test_slicing_on_batched_should_return_new_batch_frame(self):
    batch = Batch(frames=create_dataframe(2))
    expected = Batch(frames=create_dataframe())
    self.assertEqual(batch, batch[:])
    self.assertEqual(expected, batch[:-1])

def test_slicing_should_word_for_negative_stop_value(self):
    batch = Batch(frames=create_dataframe(2))
    expected = Batch(frames=create_dataframe())
    self.assertEqual(expected, batch[:-1])

def test_slicing_should_work_with_skip_value(self):
    batch = Batch(frames=create_dataframe(3))
    expected = Batch(frames=create_dataframe(3).iloc[[0, 2], :])
    self.assertEqual(expected, batch[::2])

def test_add_should_raise_error_for_incompatible_type(self):
    batch = Batch(frames=create_dataframe())
    with self.assertRaises(TypeError):
        batch + 1

def test_adding_to_empty_frame_batch_returns_itself(self):
    batch_1 = Batch(frames=pd.DataFrame())
    batch_2 = Batch(frames=create_dataframe())
    self.assertEqual(batch_2, batch_1 + batch_2)
    self.assertEqual(batch_2, batch_2 + batch_1)

def test_adding_batch_frame_with_outcomes_returns_new_batch_frame(self):
    batch_1 = Batch(frames=create_dataframe())
    batch_2 = Batch(frames=create_dataframe())
    batch_3 = Batch(frames=create_dataframe_same(2))
    self.assertEqual(batch_3, batch_1 + batch_2)

def test_concat_batch(self):
    batch_1 = Batch(frames=create_dataframe())
    batch_2 = Batch(frames=create_dataframe())
    batch_3 = Batch(frames=create_dataframe_same(2))
    self.assertEqual(batch_3, Batch.concat([batch_1, batch_2], copy=False))

def test_concat_empty_batch_list_raise_exception(self):
    self.assertEqual(Batch(), Batch.concat([]))

def test_project_batch_frame(self):
    batch_1 = Batch(frames=pd.DataFrame([{'id': 1, 'data': 2, 'info': 3}]))
    batch_2 = batch_1.project(['id', 'info'])
    batch_3 = Batch(frames=pd.DataFrame([{'id': 1, 'info': 3}]))
    self.assertEqual(batch_2, batch_3)

def test_merge_column_wise_batch_frame(self):
    batch_1 = Batch(frames=pd.DataFrame([{'id': 0}]))
    batch_2 = Batch(frames=pd.DataFrame([{'data': 1}]))
    batch_3 = Batch.merge_column_wise([batch_1, batch_2])
    batch_4 = Batch(frames=pd.DataFrame([{'id': 0, 'data': 1}]))
    self.assertEqual(batch_3, batch_4)
    self.assertEqual(Batch.merge_column_wise([]), Batch())
    batch_1 = Batch(frames=pd.DataFrame({'id': [0, None, 1]}))
    batch_2 = Batch(frames=pd.DataFrame({'data': [None, 0, None]}))
    batch_res = Batch(frames=pd.DataFrame({'id': [0, None, 1], 'data': [None, 0, None]}))
    self.assertEqual(Batch.merge_column_wise([batch_1, batch_2]), batch_res)
    df_1 = pd.DataFrame({'id': [-10, 1, 2]})
    df_2 = pd.DataFrame({'data': [-20, 2, 3]})
    df_1 = df_1[df_1 < 0].dropna()
    df_1.reset_index(drop=True, inplace=True)
    df_2 = df_2[df_2 < 0].dropna()
    df_2.reset_index(drop=True, inplace=True)
    batch_1 = Batch(frames=df_1)
    batch_2 = Batch(frames=df_2)
    df_res = pd.DataFrame({'id': [-10, 1, 2], 'data': [-20, 2, 3]})
    df_res = df_res[df_res < 0].dropna()
    df_res.reset_index(drop=True, inplace=True)
    batch_res = Batch(frames=df_res)
    self.assertEqual(Batch.merge_column_wise([batch_1, batch_2]), batch_res)

def test_should_return_correct_length(self):
    batch = Batch(create_dataframe(5))
    self.assertEqual(5, len(batch))

def test_should_return_empty_dataframe(self):
    batch = Batch()
    self.assertEqual(batch, Batch(create_dataframe(0)))

def test_stack_batch_more_than_one_column_should_raise_exception(self):
    batch = Batch(create_dataframe_same(2))
    self.assertRaises(ValueError, Batch.stack, batch)

def test_modify_column_alias_should_raise_exception(self):
    batch = Batch(create_dataframe(5))
    dummy_alias = Alias('dummy', col_names=['t1'])
    with self.assertRaises(RuntimeError):
        batch.modify_column_alias(dummy_alias)

def test_drop_column_alias_should_work_on_frame_without_alias(self):
    batch = Batch(create_dataframe(5))
    batch.drop_column_alias()

def test_sort_orderby_should_raise_exception_on_missing_column(self):
    batch = Batch(create_dataframe(5))
    with self.assertRaises(AssertionError):
        batch.sort_orderby(by=['foo'])

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    child_executor = self.children[0]
    cumm_batches = [batch for batch in child_executor.exec() if not batch.empty()]
    cumm_batches = Batch.concat(cumm_batches)
    hash_keys = [key.col_alias for key in self.build_keys]
    cumm_batches.reassign_indices_to_hash(hash_keys)
    yield cumm_batches

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

def __call__(self, *args, **kwargs) -> Generator[Batch, None, None]:
    yield from self.exec(*args, **kwargs)

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    child_executor = self.children[0]
    current = 0
    for batch in child_executor.exec():
        result_batch = batch[current::self._sample_freq]
        result_batch.reset_index()
        yield result_batch
        current = (current - len(batch)) % self._sample_freq

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    child_executor = self.children[0]
    for batch in child_executor.exec(**kwargs):
        batch = apply_predicate(batch, self.predicate)
        if not batch.empty():
            yield batch
    instrument_function_expression_cost(self.predicate, self.catalog())

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    table_catalog = self.node.table_ref.table.table_obj
    storage_engine = StorageEngine.factory(self.db, table_catalog)
    assert table_catalog.table_type == TableType.STRUCTURED_DATA, 'DELETE only implemented for structured data'
    table_to_delete_from = storage_engine._try_loading_table_via_reflection(table_catalog.name)
    sqlalchemy_filter_clause = self.predicate_node_to_filter_clause(table_to_delete_from, predicate_node=self.predicate)
    storage_engine.delete(table_catalog, sqlalchemy_filter_clause)
    yield Batch(pd.DataFrame(['Deleted rows']))

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    child_executor = self.children[0]
    buffer = Batch(pd.DataFrame())
    for batch in child_executor.exec(**kwargs):
        new_batch = buffer + batch
        while len(new_batch) >= self._segment_length:
            yield new_batch[:self._segment_length]
            new_batch = new_batch[self._segment_length:]
        buffer = new_batch

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    child_executor = self.children[0]
    for batch in child_executor.exec():
        outcomes = self.predicate.evaluate(batch)
        required_frame_ids = []
        for i, outcome in enumerate(outcomes):
            if outcome:
                required_frame_ids.append(i)
        yield batch[required_frame_ids]

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

def _get_search_query_results(self):
    dummy_batch = Batch(frames=pd.DataFrame({'0': [0]}))
    search_batch = self.search_query_expr.evaluate(dummy_batch)
    feature_col_name = self.search_query_expr.output_objs[0].name
    search_batch.drop_column_alias()
    search_feat = search_batch.column_as_numpy_array(feature_col_name)[0]
    search_feat = search_feat.reshape(1, -1)
    return search_feat

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

def exec(self, *args, **kwargs) -> Iterator[Batch]:
    assert self.node.all is True, 'Only UNION ALL is supported now.'
    for child in self.children:
        for batch in child.exec():
            yield batch

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

def extract_column_names(self):
    """extracts the string name of the column"""
    col_name_list = []
    for col in self._columns:
        col_name_list += self._extract_column_name(col)
    return col_name_list

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

def apply_project(batch: Batch, project_list: List[AbstractExpression]):
    if not batch.empty() and project_list:
        batches = [expr.evaluate(batch) for expr in project_list]
        batch = Batch.merge_column_wise(batches)
    return batch

def apply_predicate(batch: Batch, predicate: AbstractExpression) -> Batch:
    if not batch.empty() and predicate is not None:
        outcomes = predicate.evaluate(batch)
        batch.drop_zero(outcomes)
        batch.reset_index()
    return batch

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

def exec(self, *args, **kwargs):
    plan_str = self._exec(self._node.children[0], 0)
    yield Batch(pd.DataFrame([plan_str]))

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

def exec(self, *args, **kwargs):
    if self.vector_store_type == VectorStoreType.PGVECTOR:
        self._create_native_index()
    else:
        self._create_evadb_index()
    yield Batch(pd.DataFrame([f'Index {self.name} successfully added to the database.']))

def get_centroid(bboxes):
    """
    https://adipandas.github.io/multi-object-tracker/_modules/motrackers/utils/misc.html
    Calculate centroids for multiple bounding boxes.

    Args:
        bboxes (numpy.ndarray): Array of shape `(n, 4)` or of shape `(4,)` where
            each row contains `(xmin, ymin, width, height)`.

    Returns:
        numpy.ndarray: Centroid (x, y) coordinates of shape `(n, 2)` or `(2,)`.

    """
    one_bbox = False
    if len(bboxes.shape) == 1:
        one_bbox = True
        bboxes = bboxes[None, :]
    xmin = bboxes[:, 0]
    ymin = bboxes[:, 1]
    w, h = (bboxes[:, 2], bboxes[:, 3])
    xc = xmin + 0.5 * w
    yc = ymin + 0.5 * h
    x = np.hstack([xc[:, None], yc[:, None]])
    if one_bbox:
        x = x.flatten()
    return x

def is_replicate_available():
    try:
        try_to_import_replicate()
        return True
    except ValueError:
        return False

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

def evaluate(self, batch: Batch, **kwargs):
    batch = Batch(pd.DataFrame({0: [self._value] * len(batch)}))
    return batch

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

class IndexCatalog(BaseModel):
    """The `IndexCatalogEntry` catalog stores information about all the indexes in the system.
    `_row_id:` an autogenerated unique identifier.
    `_name:` the name of the index.
    `_save_file_path:` the path to the index file on disk
    `_type:` the type of the index (refer to `VectorStoreType`)
    `_feat_column_id:` the `_row_id` of the `ColumnCatalog` entry for the column on which the index is built.
    `_function_signature:` if the index is created by running function expression on input column, this will store
                      the function signature of the used function. Otherwise, this field is None.
    `_index_def:` the original SQL statement that is used to create this index. We record this to rerun create index
                on updated table.
    """
    __tablename__ = 'index_catalog'
    _name = Column('name', String(100), unique=True)
    _save_file_path = Column('save_file_path', String(128))
    _type = Column('type', Enum(VectorStoreType), default=Enum)
    _feat_column_id = Column('column_id', Integer, ForeignKey('column_catalog._row_id', ondelete='CASCADE'))
    _function_signature = Column('function', String, default=None)
    _index_def = Column('index_def', String, default=None)
    _feat_column = relationship('ColumnCatalog', back_populates='_index_column')

    def __init__(self, name: str, save_file_path: str, type: VectorStoreType, feat_column_id: int=None, function_signature: str=None, index_def: str=None):
        self._name = name
        self._save_file_path = save_file_path
        self._type = type
        self._feat_column_id = feat_column_id
        self._function_signature = function_signature
        self._index_def = index_def

    def as_dataclass(self) -> 'IndexCatalogEntry':
        feat_column = self._feat_column.as_dataclass() if self._feat_column else None
        return IndexCatalogEntry(row_id=self._row_id, name=self._name, save_file_path=self._save_file_path, type=self._type, feat_column_id=self._feat_column_id, function_signature=self._function_signature, index_def=self._index_def, feat_column=feat_column)

def as_dataclass(self) -> 'IndexCatalogEntry':
    feat_column = self._feat_column.as_dataclass() if self._feat_column else None
    return IndexCatalogEntry(row_id=self._row_id, name=self._name, save_file_path=self._save_file_path, type=self._type, feat_column_id=self._feat_column_id, function_signature=self._function_signature, index_def=self._index_def, feat_column=feat_column)

class FunctionCatalog(BaseModel):
    """The `FunctionCatalog` catalog stores information about the user-defined functions (Functions) in the system. It maintains the following information for each Function
    `_row_id:` an autogenerated identifier
    `_impl_file_path: ` the path to the implementation script for the Function
    `_type:` an optional tag associated with the function (useful for grouping similar Functions, such as multiple object detection Functions)
    """
    __tablename__ = 'function_catalog'
    _name = Column('name', String(128), unique=True)
    _impl_file_path = Column('impl_file_path', String(128))
    _type = Column('type', String(128))
    _checksum = Column('checksum', String(512))
    _attributes = relationship('FunctionIOCatalog', back_populates='_function', cascade='all, delete, delete-orphan')
    _metadata = relationship('FunctionMetadataCatalog', back_populates='_function', cascade='all, delete, delete-orphan')
    _dep_caches = relationship('FunctionCacheCatalog', secondary=depend_function_and_function_cache, back_populates='_function_depends', cascade='all, delete')

    def __init__(self, name: str, impl_file_path: str, type: str, checksum: str):
        self._name = name
        self._impl_file_path = impl_file_path
        self._type = type
        self._checksum = checksum

    def as_dataclass(self) -> 'FunctionCatalogEntry':
        args = []
        outputs = []
        for attribute in self._attributes:
            if attribute._is_input:
                args.append(attribute.as_dataclass())
            else:
                outputs.append(attribute.as_dataclass())
        metadata = []
        for meta_key_value in self._metadata:
            metadata.append(meta_key_value.as_dataclass())
        return FunctionCatalogEntry(row_id=self._row_id, name=self._name, impl_file_path=self._impl_file_path, type=self._type, checksum=self._checksum, args=args, outputs=outputs, metadata=metadata, dep_caches=[entry.as_dataclass() for entry in self._dep_caches])

def as_dataclass(self) -> 'FunctionCatalogEntry':
    args = []
    outputs = []
    for attribute in self._attributes:
        if attribute._is_input:
            args.append(attribute.as_dataclass())
        else:
            outputs.append(attribute.as_dataclass())
    metadata = []
    for meta_key_value in self._metadata:
        metadata.append(meta_key_value.as_dataclass())
    return FunctionCatalogEntry(row_id=self._row_id, name=self._name, impl_file_path=self._impl_file_path, type=self._type, checksum=self._checksum, args=args, outputs=outputs, metadata=metadata, dep_caches=[entry.as_dataclass() for entry in self._dep_caches])

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

class TextHFModel(AbstractHFFunction):
    """
    Base Model for all HF Models that take in text as input
    """

    def __call__(self, *args, **kwargs):
        return self.forward(args[0], truncation=True)

    def input_formatter(self, inputs: Any):
        return inputs.values.flatten().tolist()

def __call__(self, *args, **kwargs):
    return self.forward(args[0], truncation=True)

def input_formatter(self, inputs: Any):
    return inputs.values.flatten().tolist()

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

def convert_csv_string_to_ndarray(row_string):
    """
            Convert a string of comma separated values to a numpy
            float array
            """
    return np.array([np.float32(val) for val in row_string.split(',')])

class AbstractReader(metaclass=ABCMeta):
    """
    Abstract class for defining data reader. All other media readers use this
    abstract class. Media readers are expected to return Batch
    in an iterative manner.

    Attributes:
        file_url (str): path to read data from
    """

    def __init__(self, file_url: str, batch_mem_size: int=30000000):
        if not Path(file_url).exists():
            raise DatasetFileNotFoundError()
        if isinstance(file_url, Path):
            file_url = str(file_url)
        self.file_url = file_url
        self.batch_mem_size = batch_mem_size

    def read(self) -> Iterator[Batch]:
        """
        This calls the sub class read implementation and
        yields the batch to the caller
        """
        data_batch = []
        row_size = None
        for data in self._read():
            if row_size is None:
                row_size = 0
                row_size = get_size(data)
            data_batch.append(data)
            if len(data_batch) * row_size >= self.batch_mem_size:
                yield Batch(pd.DataFrame(data_batch))
                data_batch = []
        if data_batch:
            yield Batch(pd.DataFrame(data_batch))

    @abstractmethod
    def _read(self) -> Iterator[Dict]:
        """
        Every sub class implements it's own logic
        to read the file and yields an object iterator.
        """

def read(self) -> Iterator[Batch]:
    """
        This calls the sub class read implementation and
        yields the batch to the caller
        """
    data_batch = []
    row_size = None
    for data in self._read():
        if row_size is None:
            row_size = 0
            row_size = get_size(data)
        data_batch.append(data)
        if len(data_batch) * row_size >= self.batch_mem_size:
            yield Batch(pd.DataFrame(data_batch))
            data_batch = []
    if data_batch:
        yield Batch(pd.DataFrame(data_batch))

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

@property
def labels(self) -> np.array([str]):
    return np.array(self.weights.meta['categories'])

def forward(self, segments):
    return self.classify(segments)

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

def _forward(row: pd.Series) -> np.ndarray:
    data1 = row.iloc[0]
    data2 = row.iloc[1]
    distance = fuzz.ratio(data1, data2)
    return distance

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

def forward(self, segments):
    return self.classify(segments)

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

@forward(input_signatures=[PandasDataframe(columns=['data'], column_types=[NdArrayType.STR], column_shapes=[1])], output_signatures=[PandasDataframe(columns=['features'], column_types=[NdArrayType.FLOAT32], column_shapes=[(1, 384)])])
def forward(self, df: pd.DataFrame) -> pd.DataFrame:

    def _forward(row: pd.Series) -> np.ndarray:
        data = row
        embedded_list = self.model.encode(data)
        return embedded_list
    ret = pd.DataFrame()
    ret['features'] = df.apply(_forward, axis=1)
    return ret

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

class FuzzDistance(AbstractFunction):

    def setup(self):
        pass

    @property
    def name(self):
        return 'FuzzDistance'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find the distance between two dataframes using <> distance metric.

        Returns:
            ret (pd.DataFrame): The cropped frame.
        """
        ret = pd.DataFrame()
        ret['distance'] = df.apply(lambda row: fuzz.ratio(str(row[0]), str(row[1])), axis=1)
        return ret

def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    """
        Find the distance between two dataframes using <> distance metric.

        Returns:
            ret (pd.DataFrame): The cropped frame.
        """
    ret = pd.DataFrame()
    ret['distance'] = df.apply(lambda row: fuzz.ratio(str(row[0]), str(row[1])), axis=1)
    return ret

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

class ArrayCount(AbstractFunction):

    @property
    def name(self) -> str:
        return 'ArrayCount'

    def setup(self):
        pass

    def forward(self, frames: pd.DataFrame) -> pd.DataFrame:
        """
        It will return a count of search element for each tuple.
        The idea is to flatten the input array along the first dimension and
        count the search element in this flattened array.
        For example,
        a tuple of shape (3,4,5) will be flattened into three (4,5) elements.
        And the search key is expected to be of shape (4,5),
        else we throw an error.

        frames: DataFrame
            col1        col2
        0   ndarray1    search_key
        1   ndarray2    search_key

        out: DataFrame
            count
        0   int
        1   int

        """
        if len(frames.columns) != 2:
            raise ValueError('input contains more than one column')
        search_element = frames[frames.columns[-1]][0]
        values = pd.DataFrame(frames[frames.columns[0]])
        count_result = values.apply(lambda x: self.count_in_row(x[0], search_element), axis=1)
        return pd.DataFrame({'key_count': count_result.values})

    def count_in_row(self, row_val, search_element):
        row_val = np.array(row_val)
        search_element = np.array(search_element)
        if row_val.ndim - search_element.ndim != 1:
            raise ValueError('inconsistent dimensions for row value and search element')
        result = row_val == search_element
        return result.reshape(result.shape[0], -1).all(axis=1).sum()

def count_in_row(self, row_val, search_element):
    row_val = np.array(row_val)
    search_element = np.array(search_element)
    if row_val.ndim - search_element.ndim != 1:
        raise ValueError('inconsistent dimensions for row value and search element')
    result = row_val == search_element
    return result.reshape(result.shape[0], -1).all(axis=1).sum()

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

def __call__(self, *args, **kwargs):
    return self.forward(args[0])

class AbstractTransformationFunction(AbstractFunction):

    @abstractmethod
    def transform(self, frames: ArrayLike) -> ArrayLike:
        """
        Takes as input a batch of frames and transforms them
        by applying the frame transformation model.

        Arguments:
            frames: Input batch of frames on which prediction
            needs to be made

        Returns:
            Transformed frames
        """

    def __call__(self, *args, **kwargs):
        return self.transform(*args, **kwargs)

def __call__(self, *args, **kwargs):
    return self.transform(*args, **kwargs)

class Concat(AbstractFunction):

    def setup(self):
        pass

    @property
    def name(self):
        return 'CONCAT'

    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Concats all the df values into one.

        Returns:
            ret (pd.DataFrame): Concatenated string.
        """
        ret = pd.DataFrame()
        ret['output'] = pd.Series(df.fillna('').values.tolist()).str.join('')
        return ret

def forward(self, df: pd.DataFrame) -> pd.DataFrame:
    """
        Concats all the df values into one.

        Returns:
            ret (pd.DataFrame): Concatenated string.
        """
    ret = pd.DataFrame()
    ret['output'] = pd.Series(df.fillna('').values.tolist()).str.join('')
    return ret

def create_star_expression():
    return [TupleValueExpression(name='*')]

def create_limit_expression(num: int):
    return ConstantValueExpression(num)

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

@classmethod
def deserialize(cls, data):
    obj = PickleSerializer.deserialize(data)
    return obj

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

def column_as_numpy_array(self, column_name: str) -> np.ndarray:
    """Return a column as numpy array

        Args:
            column_name (str): the name of the required column

        Returns:
            numpy.ndarray: the column data as a numpy array
        """
    return self._frames[column_name].to_numpy()

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

def __eq__(self, other: Batch):
    return self._frames[sorted(self.columns)].equals(other.frames[sorted(other.columns)])

def _get_frames_from_indices(self, required_frame_ids):
    new_frames = self._frames.iloc[required_frame_ids, :]
    new_batch = Batch(new_frames)
    return new_batch

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

def to_numpy(self):
    return self._frames.to_numpy()

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

def _deserialize_sql_row(self, sql_row: dict, columns: List[ColumnCatalogEntry]):
    dict_row = {}
    for idx, col in enumerate(columns):
        if col.type == ColumnType.NDARRAY:
            dict_row[col.name] = self._serializer.deserialize(sql_row[col.name])
        else:
            dict_row[col.name] = sql_row[col.name]
    dict_row[ROW_NUM_COLUMN] = dict_row[IDENTIFIER_COLUMN]
    return dict_row

def _deserialize_sql_row(sql_row: tuple, columns: List[ColumnCatalogEntry]):
    dict_row = {}
    for idx, col in enumerate(columns):
        if col.type == ColumnType.NDARRAY and isinstance(sql_row[col.name], bytes):
            dict_row[col.name] = PickleSerializer.deserialize(sql_row[idx])
        else:
            dict_row[col.name] = sql_row[idx]
    return dict_row

