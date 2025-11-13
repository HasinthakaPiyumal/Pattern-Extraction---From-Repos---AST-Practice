# Cluster 14

def get_physical_query_plan(db, query: str, rule_manager=None, cost_model=None) -> AbstractPlan:
    l_plan = get_logical_query_plan(db, query)
    p_plan = PlanGenerator(db, rule_manager, cost_model).build(l_plan)
    return p_plan

def remove_function_cache(db, query):
    plan = next(get_logical_query_plan(db, query).find_all(LogicalFilter))
    func_exprs = plan.predicate.find_all(FunctionExpression)
    for expr in func_exprs:
        cache_name = expr.signature()
        function_cache = db.catalog.get_function_cache_catalog_entry_by_name(cache_name)
        if function_cache is not None:
            cache_dir = Path(function_cache.cache_path)
            if cache_dir.exists():
                shutil.rmtree(cache_dir)

def create_large_scale_image_dataset(num=1000000):
    img_dir = os.path.join(get_tmp_dir(), f'large_scale_image_dataset_{num}')
    Path(img_dir).mkdir(parents=True, exist_ok=True)
    image_idx_list = list(range(num))
    Pool(mp.cpu_count()).starmap(create_random_image, zip(image_idx_list, repeat(img_dir)))
    return img_dir

@pytest.fixture(autouse=False)
def setup_pytorch_tests():
    evadb = get_evadb_for_testing()
    evadb.catalog().reset()
    execute_query_fetch_all(evadb, "LOAD VIDEO 'data/ua_detrac/ua_detrac.mp4' INTO MyVideo;")
    execute_query_fetch_all(evadb, "LOAD VIDEO 'data/mnist/mnist.mp4' INTO MNIST;")
    execute_query_fetch_all(evadb, "LOAD VIDEO 'data/sample_videos/touchdown.mp4' INTO VIDEOS")
    init_builtin_functions(evadb, mode='release')
    return evadb

@pytest.mark.notparallel
class SingleDocumentSimilarityTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        load_functions_for_testing(self.evadb)

    def test_single_pdf_should_work(self):
        try_to_import_fitz()
        import fitz
        text_list = ['EvaDB is an AI-powered database', 'I love playing switch when I am not doing research', 'Playing basketball is a good exercise']
        doc = fitz.open()
        for text in text_list:
            doc.insert_page(-1, text=text, fontsize=11, width=595, height=842, fontname='Helvetica', color=(0, 0, 0))
        doc.save('test.pdf')
        all_text = set(deepcopy(text_list))
        execute_query_fetch_all(self.evadb, "LOAD PDF 'test.pdf' INTO MyPDF")
        res_batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM MyPDF')
        for i in range(len(res_batch)):
            all_text.remove(res_batch.frames['mypdf.data'][i])
        self.assertEqual(len(all_text), 0)
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION IF EXISTS SentenceFeatureExtractor')
        execute_query_fetch_all(self.evadb, "CREATE FUNCTION SentenceFeatureExtractor IMPL 'evadb/functions/sentence_feature_extractor.py'")
        execute_query_fetch_all(self.evadb, '\n            CREATE INDEX qdrant_index\n            ON MyPDF (SentenceFeatureExtractor(data))\n            USING FAISS\n        ')
        query = "\n            SELECT data\n            FROM MyPDF\n            ORDER BY Similarity(SentenceFeatureExtractor('{}'), SentenceFeatureExtractor(data))\n            LIMIT 1\n        "
        res_batch = execute_query_fetch_all(self.evadb, f'EXPLAIN {query.format('xx')}')
        self.assertTrue('IndexScan' in res_batch.frames[0][0])
        all_text = set(deepcopy(text_list))
        for text in text_list:
            res_batch = execute_query_fetch_all(self.evadb, query.format(text))
            res_text = res_batch.frames['mypdf.data'][0]
            self.assertTrue(res_text in all_text)
            all_text.remove(res_text)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDF')
        os.remove('test.pdf')

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    load_functions_for_testing(self.evadb)

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

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video()
    self.image_files_path = Path(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/*.jpg')
    self.csv_file_path = create_sample_csv()

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

def test_should_use_parallel_load(self):
    large_scale_image_files_path = create_large_scale_image_dataset(mp.cpu_count() * 10)
    load_query = f"LOAD IMAGE '{large_scale_image_files_path}/**/*.jpg' INTO MyLargeScaleImages;"
    execute_query_fetch_all(self.evadb, load_query)
    drop_query = 'DROP TABLE IF EXISTS MyLargeScaleImages;'
    execute_query_fetch_all(self.evadb, drop_query)
    shutil.rmtree(large_scale_image_files_path)

@pytest.mark.notparallel
class GithubDataSourceTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()

    def tearDown(self):
        execute_query_fetch_all(self.evadb, 'DROP DATABASE IF EXISTS github_data;')

    @pytest.mark.skip(reason='Need https://github.com/georgia-tech-db/evadb/pull/1280 for a cost-based rebatch optimization')
    @pytest.mark.xfail(reason='Flaky testcase due to `bad request` error message')
    def test_should_run_select_query_in_github(self):
        params = {'owner': 'georgia-tech-db', 'repo': 'evadb'}
        query = f'CREATE DATABASE github_data\n                    WITH ENGINE = "github",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        query = 'SELECT * FROM github_data.stargazers LIMIT 10;'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(batch), 10)
        expected_column = list(['stargazers.{}'.format(col) for col, _ in STARGAZERS_COLUMNS])
        self.assertEqual(batch.columns, expected_column)

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()

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

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    cls.job_name_1 = 'test_async_job_1'
    cls.job_name_2 = 'test_async_job_2'

@pytest.mark.notparallel
class DeleteExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        load_functions_for_testing(self.evadb, mode='debug')
        create_table_query = '\n                CREATE TABLE IF NOT EXISTS testDeleteOne\n                (\n                 id INTEGER,\n                 dummyfloat FLOAT(5, 3),\n                 feat   NDARRAY FLOAT32(1, 3),\n                 input  NDARRAY UINT8(1, 3)\n                 );\n                '
        execute_query_fetch_all(self.evadb, create_table_query)
        insert_query1 = '\n                INSERT INTO testDeleteOne (id, dummyfloat, feat, input)\n                VALUES (5, 1.5, [[0, 0, 0]], [[0, 0, 0]]);\n        '
        execute_query_fetch_all(self.evadb, insert_query1)
        insert_query2 = '\n                INSERT INTO testDeleteOne (id, dummyfloat,feat, input)\n                VALUES (15, 2.5, [[100, 100, 100]], [[100, 100, 100]]);\n        '
        execute_query_fetch_all(self.evadb, insert_query2)
        insert_query3 = '\n                INSERT INTO testDeleteOne (id, dummyfloat,feat, input)\n                VALUES (25, 3.5, [[200, 200, 200]], [[200, 200, 200]]);\n        '
        execute_query_fetch_all(self.evadb, insert_query3)
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4'
        query = f'LOAD VIDEO "{path}" INTO TestDeleteVideos;'
        _ = execute_query_fetch_all(self.evadb, query)

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')

    @unittest.skip('Not supported in current version')
    def test_should_delete_single_video_in_table(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/2.mp4'
        delete_query = f'DELETE FROM TestDeleteVideos WHERE name="{path}";'
        batch = execute_query_fetch_all(self.evadb, delete_query)
        query = 'SELECT name FROM MyVideo'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['data'][0], np.array([[[40, 40, 40], [40, 40, 40]], [[40, 40, 40], [40, 40, 40]]])))
        query = 'SELECT id, data FROM MyVideo WHERE id = 41;'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['data'][0], np.array([[[41, 41, 41], [41, 41, 41]], [[41, 41, 41], [41, 41, 41]]])))

    @unittest.skip('Not supported in current version')
    def test_should_delete_single_image_in_table(self):
        path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/2.mp4'
        delete_query = f'DELETE FROM TestDeleteVideos WHERE name="{path}";'
        batch = execute_query_fetch_all(self.evadb, delete_query)
        query = 'SELECT name FROM MyVideo'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['data'][0], np.array([[[40, 40, 40], [40, 40, 40]], [[40, 40, 40], [40, 40, 40]]])))
        query = 'SELECT id, data FROM MyVideo WHERE id = 41;'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['data'][0], np.array([[[41, 41, 41], [41, 41, 41]], [[41, 41, 41], [41, 41, 41]]])))

    def test_should_delete_tuple_in_table(self):
        delete_query = 'DELETE FROM testDeleteOne WHERE\n               id < 20 OR dummyfloat < 2 AND id < 5 AND 20 > id\n               AND id <= 20 AND id >= 5 OR id != 15 OR id = 15;'
        batch = execute_query_fetch_all(self.evadb, delete_query)
        query = 'SELECT * FROM testDeleteOne;'
        batch = execute_query_fetch_all(self.evadb, query)
        np.testing.assert_array_equal(batch.frames['testdeleteone.id'].array, np.array([25], dtype=np.int64))

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    load_functions_for_testing(self.evadb, mode='debug')
    create_table_query = '\n                CREATE TABLE IF NOT EXISTS testDeleteOne\n                (\n                 id INTEGER,\n                 dummyfloat FLOAT(5, 3),\n                 feat   NDARRAY FLOAT32(1, 3),\n                 input  NDARRAY UINT8(1, 3)\n                 );\n                '
    execute_query_fetch_all(self.evadb, create_table_query)
    insert_query1 = '\n                INSERT INTO testDeleteOne (id, dummyfloat, feat, input)\n                VALUES (5, 1.5, [[0, 0, 0]], [[0, 0, 0]]);\n        '
    execute_query_fetch_all(self.evadb, insert_query1)
    insert_query2 = '\n                INSERT INTO testDeleteOne (id, dummyfloat,feat, input)\n                VALUES (15, 2.5, [[100, 100, 100]], [[100, 100, 100]]);\n        '
    execute_query_fetch_all(self.evadb, insert_query2)
    insert_query3 = '\n                INSERT INTO testDeleteOne (id, dummyfloat,feat, input)\n                VALUES (25, 3.5, [[200, 200, 200]], [[200, 200, 200]]);\n        '
    execute_query_fetch_all(self.evadb, insert_query3)
    path = f'{EvaDB_ROOT_DIR}/data/sample_videos/1/*.mp4'
    query = f'LOAD VIDEO "{path}" INTO TestDeleteVideos;'
    _ = execute_query_fetch_all(self.evadb, query)

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

@pytest.mark.notparallel
class HackernewsDataSourceTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()

    def tearDown(self):
        execute_query_fetch_all(self.evadb, 'DROP DATABASE IF EXISTS hackernews_data;')

    @pytest.mark.xfail(reason='Flaky testcase due to `bad request` error message')
    def test_should_run_select_query_in_hackernews(self):
        params = {'query': 'EVADB', 'tags': 'story'}
        query = f'CREATE DATABASE hackernews_data\n                    WITH ENGINE = "hackernews",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        query = 'SELECT * FROM hackernews_data.search_results LIMIT 5;'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(batch), 10)
        expected_column = list(['search_results.{}'.format(col) for col, _ in HACKERNEWS_COLUMNS])
        self.assertEqual(batch.columns, expected_column)

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()

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

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
    execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO MyVideo;")
    execute_query_fetch_all(cls.evadb, f"LOAD VIDEO '{ua_detrac}' INTO MyVideo2;")
    load_functions_for_testing(cls.evadb, mode='debug')

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

class ReuseTest(unittest.TestCase):

    def _load_hf_model(self):
        function_name = 'HFObjectDetector'
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'object-detection'\n            MODEL 'facebook/detr-resnet-50';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
        execute_query_fetch_all(self.evadb, f"LOAD VIDEO '{ua_detrac}' INTO DETRAC;")
        execute_query_fetch_all(self.evadb, 'CREATE TABLE fruitTable (data TEXT(100))')
        data_list = ['The color of apple is red', 'The color of banana is yellow']
        for data in data_list:
            execute_query_fetch_all(self.evadb, f"INSERT INTO fruitTable (data) VALUES ('{data}')")
        load_functions_for_testing(self.evadb)
        self._load_hf_model()

    def tearDown(self):
        shutdown_ray()
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS DETRAC;')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS fruitTable;')

    def _verify_reuse_correctness(self, query, reuse_batch):
        gc.collect()
        rules_manager = RulesManager()
        with disable_rules(rules_manager, [CacheFunctionExpressionInApply(), CacheFunctionExpressionInFilter(), CacheFunctionExpressionInProject()]):
            custom_plan_generator = PlanGenerator(self.evadb, rules_manager)
            without_reuse_batch = execute_query_fetch_all(self.evadb, query, plan_generator=custom_plan_generator)
        self.assertEqual(reuse_batch.columns, reuse_batch.columns)
        reuse_batch.sort_orderby(by=[reuse_batch.columns[0]])
        without_reuse_batch.sort_orderby(by=[reuse_batch.columns[0]])
        self.assertEqual(without_reuse_batch, reuse_batch, msg=f'Without reuse {without_reuse_batch} \n With reuse{reuse_batch}')

    def _reuse_experiment(self, queries):
        exec_times = []
        batches = []
        for query in queries:
            timer = Timer()
            with timer:
                batches.append(execute_query_fetch_all(self.evadb, query))
            exec_times.append(timer.total_elapsed_time)
        return (batches, exec_times)

    def _strict_reuse_experiment(self, queries):
        exec_times = []
        batches = []
        for i, query in enumerate(queries):
            timer = Timer()
            if i != 0:
                with timer, patch.object(Batch, 'apply_function_expression') as mock_batch_func:
                    mock_batch_func.side_effect = Exception('Results are not reused')
                    batches.append(execute_query_fetch_all(self.evadb, query))
            else:
                with timer:
                    batches.append(execute_query_fetch_all(self.evadb, query))
            exec_times.append(timer.total_elapsed_time)
        return (batches, exec_times)

    def test_reuse_chatgpt(self):
        from evadb.constants import CACHEABLE_FUNCTIONS
        CACHEABLE_FUNCTIONS += ['DummyLLM']
        select_query = "SELECT DummyLLM('What is the fruit described in this sentence', data)\n            FROM fruitTable"
        batches, exec_times = self._strict_reuse_experiment([select_query, select_query])
        self._verify_reuse_correctness(select_query, batches[1])
        self.assertTrue(exec_times[0] > exec_times[1])

    def test_reuse_when_query_is_duplicate(self):
        select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL HFObjectDetector(data) AS Obj(score, label, bbox) WHERE id < 15;'
        batches, exec_times = self._strict_reuse_experiment([select_query, select_query])
        self._verify_reuse_correctness(select_query, batches[1])
        self.assertTrue(exec_times[0] > exec_times[1])

    @gpu_skip_marker
    def test_reuse_partial(self):
        select_query1 = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL HFObjectDetector(data) AS Obj(score, label, bbox) WHERE id < 5;'
        select_query2 = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL HFObjectDetector(data) AS Obj(score, label, bbox) WHERE id < 15;'
        batches, exec_times = self._reuse_experiment([select_query1, select_query2])
        self._verify_reuse_correctness(select_query2, batches[1])

    @gpu_skip_marker
    def test_reuse_in_with_multiple_occurrences(self):
        select_query1 = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL HFObjectDetector(data) AS Obj(score, label, bbox) WHERE id < 10;'
        select_query2 = 'SELECT id, HFObjectDetector(data).label FROM DETRAC JOIN\n            LATERAL HFObjectDetector(data) AS Obj(score, label, bbox) WHERE id < 5;'
        batches, exec_times = self._reuse_experiment([select_query1, select_query2])
        self._verify_reuse_correctness(select_query2, batches[1])
        select_query = 'SELECT id, HFObjectDetector(data).label FROM DETRAC WHERE id < 15;'
        reuse_batch = execute_query_fetch_all(self.evadb, select_query)
        self._verify_reuse_correctness(select_query, reuse_batch)
        select_query = "SELECT id, HFObjectDetector(data).label FROM DETRAC WHERE ['car'] <@ HFObjectDetector(data).label AND id < 20"
        reuse_batch = execute_query_fetch_all(self.evadb, select_query)
        self._verify_reuse_correctness(select_query, reuse_batch)

    @gpu_skip_marker
    def test_reuse_logical_project_with_duplicate_query(self):
        project_query = 'SELECT id, HFObjectDetector(data).label FROM DETRAC WHERE id < 10;'
        batches, exec_times = self._reuse_experiment([project_query, project_query])
        self._verify_reuse_correctness(project_query, batches[1])
        self.assertGreater(exec_times[0], exec_times[1])

    @gpu_skip_marker
    def test_reuse_with_function_in_predicate(self):
        select_query = "SELECT id FROM DETRAC WHERE ['car'] <@ HFObjectDetector(data).label AND id < 4"
        batches, exec_times = self._reuse_experiment([select_query, select_query])
        self._verify_reuse_correctness(select_query, batches[1])
        self.assertGreater(exec_times[0], exec_times[1])

    @gpu_skip_marker
    def test_reuse_across_different_predicate_using_same_function(self):
        query1 = "SELECT id FROM DETRAC WHERE ['car'] <@ HFObjectDetector(data).label AND id < 15"
        query2 = "SELECT id FROM DETRAC WHERE ArrayCount(HFObjectDetector(data).label, 'car') > 3 AND id < 12;"
        batches, exec_times = self._reuse_experiment([query1, query2])
        self._verify_reuse_correctness(query2, batches[1])
        self.assertGreater(exec_times[0], exec_times[1])

    @gpu_skip_marker
    def test_reuse_filter_with_project(self):
        project_query = '\n            SELECT id, Yolo(data).labels FROM DETRAC WHERE id < 5;'
        select_query = "\n            SELECT id FROM DETRAC\n            WHERE ArrayCount(Yolo(data).labels, 'car') > 3 AND id < 5;"
        batches, exec_times = self._reuse_experiment([project_query, select_query])
        self._verify_reuse_correctness(select_query, batches[1])
        self.assertGreater(exec_times[0], exec_times[1])

    @gpu_skip_marker
    def test_reuse_in_extract_object(self):
        select_query = '\n            SELECT id, T.iids, T.bboxes, T.scores, T.labels\n            FROM DETRAC JOIN LATERAL EXTRACT_OBJECT(data, Yolo, NorFairTracker)\n                AS T(iids, labels, bboxes, scores)\n            WHERE id < 30;\n            '
        batches, exec_times = self._reuse_experiment([select_query, select_query])
        self._verify_reuse_correctness(select_query, batches[1])
        self.assertGreater(exec_times[0], exec_times[1])

    @windows_skip_marker
    def test_reuse_after_server_shutdown(self):
        select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL Yolo(data) AS Obj(label, bbox, conf) WHERE id < 4;'
        execute_query_fetch_all(self.evadb, select_query)
        os.system('nohup evadb_server --stop')
        os.system('nohup evadb_server --start &')
        select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL Yolo(data) AS Obj(label, bbox, conf) WHERE id < 6;'
        reuse_batch = execute_query_fetch_all(self.evadb, select_query)
        self._verify_reuse_correctness(select_query, reuse_batch)
        os.system('nohup evadb_server --stop')

    def test_drop_function_should_remove_cache(self):
        select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL Yolo(data) AS Obj(label, bbox, conf) WHERE id < 5;'
        execute_query_fetch_all(self.evadb, select_query)
        plan = next(get_logical_query_plan(self.evadb, select_query).find_all(LogicalFunctionScan))
        cache_name = plan.func_expr.signature()
        function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
        cache_dir = Path(function_cache.cache_path)
        self.assertIsNotNone(function_cache)
        self.assertTrue(cache_dir.exists())
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION Yolo;')
        function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
        self.assertIsNone(function_cache)
        self.assertFalse(cache_dir.exists())

    def test_drop_table_should_remove_cache(self):
        select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL Yolo(data) AS Obj(label, bbox, conf) WHERE id < 5;'
        execute_query_fetch_all(self.evadb, select_query)
        plan = next(get_logical_query_plan(self.evadb, select_query).find_all(LogicalFunctionScan))
        cache_name = plan.func_expr.signature()
        function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
        cache_dir = Path(function_cache.cache_path)
        self.assertIsNotNone(function_cache)
        self.assertTrue(cache_dir.exists())
        execute_query_fetch_all(self.evadb, 'DROP TABLE DETRAC;')
        function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
        self.assertIsNone(function_cache)
        self.assertFalse(cache_dir.exists())

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    ua_detrac = f'{EvaDB_ROOT_DIR}/data/ua_detrac/ua_detrac.mp4'
    execute_query_fetch_all(self.evadb, f"LOAD VIDEO '{ua_detrac}' INTO DETRAC;")
    execute_query_fetch_all(self.evadb, 'CREATE TABLE fruitTable (data TEXT(100))')
    data_list = ['The color of apple is red', 'The color of banana is yellow']
    for data in data_list:
        execute_query_fetch_all(self.evadb, f"INSERT INTO fruitTable (data) VALUES ('{data}')")
    load_functions_for_testing(self.evadb)
    self._load_hf_model()

def test_drop_function_should_remove_cache(self):
    select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL Yolo(data) AS Obj(label, bbox, conf) WHERE id < 5;'
    execute_query_fetch_all(self.evadb, select_query)
    plan = next(get_logical_query_plan(self.evadb, select_query).find_all(LogicalFunctionScan))
    cache_name = plan.func_expr.signature()
    function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
    cache_dir = Path(function_cache.cache_path)
    self.assertIsNotNone(function_cache)
    self.assertTrue(cache_dir.exists())
    execute_query_fetch_all(self.evadb, 'DROP FUNCTION Yolo;')
    function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
    self.assertIsNone(function_cache)
    self.assertFalse(cache_dir.exists())

def test_drop_table_should_remove_cache(self):
    select_query = 'SELECT id, label FROM DETRAC JOIN\n            LATERAL Yolo(data) AS Obj(label, bbox, conf) WHERE id < 5;'
    execute_query_fetch_all(self.evadb, select_query)
    plan = next(get_logical_query_plan(self.evadb, select_query).find_all(LogicalFunctionScan))
    cache_name = plan.func_expr.signature()
    function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
    cache_dir = Path(function_cache.cache_path)
    self.assertIsNotNone(function_cache)
    self.assertTrue(cache_dir.exists())
    execute_query_fetch_all(self.evadb, 'DROP TABLE DETRAC;')
    function_cache = self.evadb.catalog().get_function_cache_catalog_entry_by_name(cache_name)
    self.assertIsNone(function_cache)
    self.assertFalse(cache_dir.exists())

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

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    video_file_path = create_sample_video(NUM_FRAMES)
    load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(self.evadb, load_query)
    create_function_query = "CREATE FUNCTION DummyObjectDetector\n                  INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n                  OUTPUT (label NDARRAY STR(10))\n                  TYPE  Classification\n                  IMPL  'test/util.py';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)

def test_function_cost_entry_created(self):
    execute_query_fetch_all(self.evadb, 'SELECT DummyObjectDetector(data) FROM MyVideo')
    entry = self.evadb.catalog().get_function_cost_catalog_entry('DummyObjectDetector')
    self.assertIsNotNone(entry)

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

def setUp(self):
    self.db_dir = suffix_pytest_xdist_worker_id_to_dir(EvaDB_DATABASE_DIR)
    self.conn = connect(self.db_dir)
    self.evadb = self.conn._evadb
    self.evadb.catalog().reset()

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

@pytest.mark.notparallel
class CreateIndexTest(unittest.TestCase):

    def _index_save_path(self):
        return str(Path(self.evadb.catalog().get_configuration_catalog_value('index_dir')) / Path('{}_{}.index'.format('FAISS', 'testCreateIndexName')))

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        load_functions_for_testing(cls.evadb, mode='debug')
        feat1 = np.array([[0, 0, 0]]).astype(np.float32)
        feat2 = np.array([[100, 100, 100]]).astype(np.float32)
        feat3 = np.array([[200, 200, 200]]).astype(np.float32)
        input1 = np.array([[0, 0, 0]]).astype(np.uint8)
        input2 = np.array([[100, 100, 100]]).astype(np.uint8)
        input3 = np.array([[200, 200, 200]]).astype(np.uint8)
        execute_query_fetch_all(cls.evadb, 'create table if not exists testCreateIndexFeatTable (\n                feat NDARRAY FLOAT32(1,3)\n            );')
        execute_query_fetch_all(cls.evadb, 'create table if not exists testCreateIndexInputTable (\n                input NDARRAY UINT8(1,3)\n            );')
        feat_batch_data = Batch(pd.DataFrame(data={'feat': [feat1, feat2, feat3]}))
        feat_tb_entry = cls.evadb.catalog().get_table_catalog_entry('testCreateIndexFeatTable')
        storage_engine = StorageEngine.factory(cls.evadb, feat_tb_entry)
        storage_engine.write(feat_tb_entry, feat_batch_data)
        input_batch_data = Batch(pd.DataFrame(data={'input': [input1, input2, input3]}))
        input_tb_entry = cls.evadb.catalog().get_table_catalog_entry('testCreateIndexInputTable')
        storage_engine.write(input_tb_entry, input_batch_data)

    @classmethod
    def tearDown(cls):
        query = 'DROP INDEX testCreateIndexName;'
        execute_query_fetch_all(cls.evadb, query)

    @classmethod
    def tearDownClass(cls):
        query = 'DROP TABLE testCreateIndexFeatTable;'
        execute_query_fetch_all(cls.evadb, query)
        query = 'DROP TABLE testCreateIndexInputTable;'
        execute_query_fetch_all(cls.evadb, query)

    @macos_skip_marker
    def test_index_already_exist(self):
        query = 'CREATE INDEX testCreateIndexName ON testCreateIndexFeatTable (feat) USING FAISS;'
        execute_query_fetch_all(self.evadb, query)
        self.assertEqual(self.evadb.catalog().get_index_catalog_entry_by_name('testCreateIndexName').type, VectorStoreType.FAISS)
        query = 'CREATE INDEX testCreateIndexName ON testCreateIndexFeatTable (feat) USING FAISS;'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)
        query = 'CREATE INDEX IF NOT EXISTS testCreateIndexName ON testCreateIndexFeatTable (feat) USING QDRANT;'
        execute_query_fetch_all(self.evadb, query)
        self.assertEqual(self.evadb.catalog().get_index_catalog_entry_by_name('testCreateIndexName').type, VectorStoreType.FAISS)

    @macos_skip_marker
    def test_should_create_index_faiss(self):
        query = 'CREATE INDEX testCreateIndexName ON testCreateIndexFeatTable (feat) USING FAISS;'
        execute_query_fetch_all(self.evadb, query)
        index_catalog_entry = self.evadb.catalog().get_index_catalog_entry_by_name('testCreateIndexName')
        self.assertEqual(index_catalog_entry.type, VectorStoreType.FAISS)
        self.assertEqual(index_catalog_entry.save_file_path, self._index_save_path())
        self.assertEqual(index_catalog_entry.function_signature, None)
        feat_table_entry = self.evadb.catalog().get_table_catalog_entry('testCreateIndexFeatTable')
        feat_column = [col for col in feat_table_entry.columns if col.name == 'feat'][0]
        self.assertEqual(index_catalog_entry.feat_column_id, feat_column.row_id)
        self.assertEqual(index_catalog_entry.feat_column, feat_column)
        try_to_import_faiss()
        import faiss
        index = faiss.read_index(index_catalog_entry.save_file_path)
        distance, row_id = index.search(np.array([[0, 0, 0]]).astype(np.float32), 1)
        self.assertEqual(distance[0][0], 0)
        self.assertEqual(row_id[0][0], 1)

    @macos_skip_marker
    def test_should_create_index_with_function(self):
        query = 'CREATE INDEX testCreateIndexName ON testCreateIndexInputTable (DummyFeatureExtractor(input)) USING FAISS;'
        execute_query_fetch_all(self.evadb, query)
        index_catalog_entry = self.evadb.catalog().get_index_catalog_entry_by_name('testCreateIndexName')
        self.assertEqual(index_catalog_entry.type, VectorStoreType.FAISS)
        self.assertEqual(index_catalog_entry.save_file_path, self._index_save_path())
        input_table_entry = self.evadb.catalog().get_table_catalog_entry('testCreateIndexInputTable')
        input_column = [col for col in input_table_entry.columns if col.name == 'input'][0]
        self.assertEqual(index_catalog_entry.feat_column_id, input_column.row_id)
        self.assertEqual(index_catalog_entry.feat_column, input_column)
        try_to_import_faiss()
        import faiss
        index = faiss.read_index(index_catalog_entry.save_file_path)
        distance, row_id = index.search(np.array([[0, 0, 0]]).astype(np.float32), 1)
        self.assertEqual(distance[0][0], 0)
        self.assertEqual(row_id[0][0], 1)

def _index_save_path(self):
    return str(Path(self.evadb.catalog().get_configuration_catalog_value('index_dir')) / Path('{}_{}.index'.format('FAISS', 'testCreateIndexName')))

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    load_functions_for_testing(cls.evadb, mode='debug')
    feat1 = np.array([[0, 0, 0]]).astype(np.float32)
    feat2 = np.array([[100, 100, 100]]).astype(np.float32)
    feat3 = np.array([[200, 200, 200]]).astype(np.float32)
    input1 = np.array([[0, 0, 0]]).astype(np.uint8)
    input2 = np.array([[100, 100, 100]]).astype(np.uint8)
    input3 = np.array([[200, 200, 200]]).astype(np.uint8)
    execute_query_fetch_all(cls.evadb, 'create table if not exists testCreateIndexFeatTable (\n                feat NDARRAY FLOAT32(1,3)\n            );')
    execute_query_fetch_all(cls.evadb, 'create table if not exists testCreateIndexInputTable (\n                input NDARRAY UINT8(1,3)\n            );')
    feat_batch_data = Batch(pd.DataFrame(data={'feat': [feat1, feat2, feat3]}))
    feat_tb_entry = cls.evadb.catalog().get_table_catalog_entry('testCreateIndexFeatTable')
    storage_engine = StorageEngine.factory(cls.evadb, feat_tb_entry)
    storage_engine.write(feat_tb_entry, feat_batch_data)
    input_batch_data = Batch(pd.DataFrame(data={'input': [input1, input2, input3]}))
    input_tb_entry = cls.evadb.catalog().get_table_catalog_entry('testCreateIndexInputTable')
    storage_engine.write(input_tb_entry, input_batch_data)

@macos_skip_marker
def test_should_create_index_faiss(self):
    query = 'CREATE INDEX testCreateIndexName ON testCreateIndexFeatTable (feat) USING FAISS;'
    execute_query_fetch_all(self.evadb, query)
    index_catalog_entry = self.evadb.catalog().get_index_catalog_entry_by_name('testCreateIndexName')
    self.assertEqual(index_catalog_entry.type, VectorStoreType.FAISS)
    self.assertEqual(index_catalog_entry.save_file_path, self._index_save_path())
    self.assertEqual(index_catalog_entry.function_signature, None)
    feat_table_entry = self.evadb.catalog().get_table_catalog_entry('testCreateIndexFeatTable')
    feat_column = [col for col in feat_table_entry.columns if col.name == 'feat'][0]
    self.assertEqual(index_catalog_entry.feat_column_id, feat_column.row_id)
    self.assertEqual(index_catalog_entry.feat_column, feat_column)
    try_to_import_faiss()
    import faiss
    index = faiss.read_index(index_catalog_entry.save_file_path)
    distance, row_id = index.search(np.array([[0, 0, 0]]).astype(np.float32), 1)
    self.assertEqual(distance[0][0], 0)
    self.assertEqual(row_id[0][0], 1)

@macos_skip_marker
def test_should_create_index_with_function(self):
    query = 'CREATE INDEX testCreateIndexName ON testCreateIndexInputTable (DummyFeatureExtractor(input)) USING FAISS;'
    execute_query_fetch_all(self.evadb, query)
    index_catalog_entry = self.evadb.catalog().get_index_catalog_entry_by_name('testCreateIndexName')
    self.assertEqual(index_catalog_entry.type, VectorStoreType.FAISS)
    self.assertEqual(index_catalog_entry.save_file_path, self._index_save_path())
    input_table_entry = self.evadb.catalog().get_table_catalog_entry('testCreateIndexInputTable')
    input_column = [col for col in input_table_entry.columns if col.name == 'input'][0]
    self.assertEqual(index_catalog_entry.feat_column_id, input_column.row_id)
    self.assertEqual(index_catalog_entry.feat_column, input_column)
    try_to_import_faiss()
    import faiss
    index = faiss.read_index(index_catalog_entry.save_file_path)
    distance, row_id = index.search(np.array([[0, 0, 0]]).astype(np.float32), 1)
    self.assertEqual(distance[0][0], 0)
    self.assertEqual(row_id[0][0], 1)

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

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    video_file_path = create_sample_video(NUM_FRAMES)
    load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(cls.evadb, load_query)
    load_functions_for_testing(cls.evadb, mode='debug')

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

@pytest.mark.notparallel
class ModelTrainTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        create_table_query = '\n           CREATE TABLE IF NOT EXISTS HomeRentals (\n               number_of_rooms INTEGER,\n               number_of_bathrooms INTEGER,\n               sqft INTEGER,\n               location TEXT(128),\n               days_on_market INTEGER,\n               initial_price INTEGER,\n               neighborhood TEXT(128),\n               rental_price FLOAT(64,64)\n           );'
        execute_query_fetch_all(cls.evadb, create_table_query)
        path = f'{EvaDB_ROOT_DIR}/data/ludwig/home_rentals.csv'
        load_query = f"LOAD CSV '{path}' INTO HomeRentals;"
        execute_query_fetch_all(cls.evadb, load_query)
        create_table_query = '\n           CREATE TABLE IF NOT EXISTS Employee (\n               education TEXT(128),\n               joining_year INTEGER,\n               city TEXT(128),\n               payment_tier INTEGER,\n               age INTEGER,\n               gender TEXT(128),\n               ever_benched TEXT(128),\n               experience_in_current_domain INTEGER,\n               leave_or_not INTEGER\n           );'
        execute_query_fetch_all(cls.evadb, create_table_query)
        path = f'{EvaDB_ROOT_DIR}/data/classification/Employee.csv'
        load_query = f"LOAD CSV '{path}' INTO Employee;"
        execute_query_fetch_all(cls.evadb, load_query)

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS HomeRentals;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS Employee;')
        execute_query_fetch_all(cls.evadb, 'DROP FUNCTION IF EXISTS PredictHouseRentLudwig;')
        execute_query_fetch_all(cls.evadb, 'DROP FUNCTION IF EXISTS PredictHouseRentSklearn;')
        execute_query_fetch_all(cls.evadb, 'DROP FUNCTION IF EXISTS PredictRentXgboost;')
        execute_query_fetch_all(cls.evadb, 'DROP FUNCTION IF EXISTS PredictEmployeeXgboost;')

    @pytest.mark.skip(reason='Model training intergration test takes too long to complete.')
    @ludwig_skip_marker
    def test_ludwig_automl(self):
        create_predict_function = "\n            CREATE OR REPLACE FUNCTION PredictHouseRentLudwig FROM\n            ( SELECT * FROM HomeRentals )\n            TYPE Ludwig\n            PREDICT 'rental_price'\n            TIME_LIMIT 120;\n        "
        execute_query_fetch_all(self.evadb, create_predict_function)
        predict_query = '\n            SELECT PredictHouseRentLudwig(*) FROM HomeRentals LIMIT 10;\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result.columns), 1)
        self.assertEqual(len(result), 10)

    @pytest.mark.skip(reason='Model training intergration test takes too long to complete.')
    @sklearn_skip_marker
    def test_sklearn_regression(self):
        create_predict_function = "\n            CREATE OR REPLACE FUNCTION PredictHouseRentSklearn FROM\n            ( SELECT number_of_rooms, number_of_bathrooms, days_on_market, rental_price FROM HomeRentals )\n            TYPE Sklearn\n            PREDICT 'rental_price'\n            MODEL 'extra_tree'\n            METRIC 'r2';\n        "
        execute_query_fetch_all(self.evadb, create_predict_function)
        predict_query = '\n            SELECT PredictHouseRentSklearn(number_of_rooms, number_of_bathrooms, days_on_market, rental_price) FROM HomeRentals LIMIT 10;\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result.columns), 1)
        self.assertEqual(len(result), 10)

    @xgboost_skip_marker
    def test_xgboost_regression(self):
        create_predict_function = "\n            CREATE OR REPLACE FUNCTION PredictRentXgboost FROM\n            ( SELECT number_of_rooms, number_of_bathrooms, days_on_market, rental_price FROM HomeRentals )\n            TYPE XGBoost\n            PREDICT 'rental_price'\n            TIME_LIMIT 180\n            METRIC 'r2'\n            TASK 'regression';\n        "
        result = execute_query_fetch_all(self.evadb, create_predict_function)
        self.assertEqual(len(result.columns), 1)
        self.assertEqual(len(result), 3)
        predict_query = '\n            SELECT PredictRentXgboost(number_of_rooms, number_of_bathrooms, days_on_market, rental_price) FROM HomeRentals LIMIT 10;\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result.columns), 1)
        self.assertEqual(len(result), 10)

    @xgboost_skip_marker
    def test_xgboost_classification(self):
        create_predict_function = "\n            CREATE OR REPLACE FUNCTION PredictEmployeeXgboost FROM\n            ( SELECT payment_tier, age, gender, experience_in_current_domain, leave_or_not FROM Employee )\n            TYPE XGBoost\n            PREDICT 'leave_or_not'\n            TIME_LIMIT 180\n            METRIC 'accuracy'\n            TASK 'classification';\n        "
        result = execute_query_fetch_all(self.evadb, create_predict_function)
        self.assertEqual(len(result.columns), 1)
        self.assertEqual(len(result), 3)
        predict_query = '\n            SELECT PredictEmployeeXgboost(payment_tier, age, gender, experience_in_current_domain, leave_or_not) FROM Employee LIMIT 10;\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result.columns), 1)
        self.assertEqual(len(result), 10)

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    create_table_query = '\n           CREATE TABLE IF NOT EXISTS HomeRentals (\n               number_of_rooms INTEGER,\n               number_of_bathrooms INTEGER,\n               sqft INTEGER,\n               location TEXT(128),\n               days_on_market INTEGER,\n               initial_price INTEGER,\n               neighborhood TEXT(128),\n               rental_price FLOAT(64,64)\n           );'
    execute_query_fetch_all(cls.evadb, create_table_query)
    path = f'{EvaDB_ROOT_DIR}/data/ludwig/home_rentals.csv'
    load_query = f"LOAD CSV '{path}' INTO HomeRentals;"
    execute_query_fetch_all(cls.evadb, load_query)
    create_table_query = '\n           CREATE TABLE IF NOT EXISTS Employee (\n               education TEXT(128),\n               joining_year INTEGER,\n               city TEXT(128),\n               payment_tier INTEGER,\n               age INTEGER,\n               gender TEXT(128),\n               ever_benched TEXT(128),\n               experience_in_current_domain INTEGER,\n               leave_or_not INTEGER\n           );'
    execute_query_fetch_all(cls.evadb, create_table_query)
    path = f'{EvaDB_ROOT_DIR}/data/classification/Employee.csv'
    load_query = f"LOAD CSV '{path}' INTO Employee;"
    execute_query_fetch_all(cls.evadb, load_query)

@pytest.mark.notparallel
class FuzzyJoinTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()
        self.image_files_path = Path(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/*.jpg')
        self.csv_file_path = create_sample_csv()
        create_table_query = '\n            CREATE TABLE IF NOT EXISTS MyVideoCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER,\n                video_id INTEGER,\n                dataset_name TEXT(30),\n                label TEXT(30),\n                bbox NDARRAY FLOAT32(4),\n                object_id INTEGER\n            );\n            '
        execute_query_fetch_all(self.evadb, create_table_query)
        load_query = f"LOAD CSV '{self.csv_file_path}' INTO MyVideoCSV;"
        execute_query_fetch_all(self.evadb, load_query)
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')
        file_remove('dummy.csv')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideoCSV;')

    @pytest.mark.xfail(reason='https://github.com/georgia-tech-db/evadb/issues/1242')
    def test_fuzzyjoin(self):
        execute_query_fetch_all(self.evadb, fuzzy_function_query)
        fuzzy_join_query = 'SELECT * FROM MyVideo a JOIN MyVideoCSV b\n                      ON FuzzDistance(a.id, b.id) = 100;'
        actual_batch = execute_query_fetch_all(self.evadb, fuzzy_join_query)
        self.assertEqual(len(actual_batch), 10)

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video()
    self.image_files_path = Path(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/*.jpg')
    self.csv_file_path = create_sample_csv()
    create_table_query = '\n            CREATE TABLE IF NOT EXISTS MyVideoCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER,\n                video_id INTEGER,\n                dataset_name TEXT(30),\n                label TEXT(30),\n                bbox NDARRAY FLOAT32(4),\n                object_id INTEGER\n            );\n            '
    execute_query_fetch_all(self.evadb, create_table_query)
    load_query = f"LOAD CSV '{self.csv_file_path}' INTO MyVideoCSV;"
    execute_query_fetch_all(self.evadb, load_query)
    query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(self.evadb, query)

@pytest.mark.notparallel
class ExplainExecutorTest(unittest.TestCase):

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
        file_remove('dummy.avi')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_explain_simple_select(self):
        select_query = 'EXPLAIN SELECT id, data FROM MyVideo'
        batch = execute_query_fetch_all(self.evadb, select_query)
        expected_output = '|__ ProjectPlan\n    |__ SeqScanPlan\n        |__ StoragePlan\n'
        self.assertEqual(batch.frames[0][0], expected_output)
        rules_manager = RulesManager()
        with disable_rules(rules_manager, [XformLateralJoinToLinearFlow()]):
            custom_plan_generator = PlanGenerator(self.evadb, rules_manager)
            select_query = 'EXPLAIN SELECT id, data FROM MyVideo JOIN LATERAL DummyObjectDetector(data) AS T ;'
            batch = execute_query_fetch_all(self.evadb, select_query, plan_generator=custom_plan_generator)
            expected_output = '|__ ProjectPlan\n    |__ LateralJoinPlan\n        |__ SeqScanPlan\n            |__ StoragePlan\n        |__ FunctionScanPlan\n'
            self.assertEqual(batch.frames[0][0], expected_output)
        rules_manager = RulesManager()
        with disable_rules(rules_manager, [XformLateralJoinToLinearFlow(), EmbedFilterIntoGet(), LogicalInnerJoinCommutativity()]):
            custom_plan_generator = PlanGenerator(self.evadb, rules_manager)
            select_query = 'EXPLAIN SELECT id, data FROM MyVideo JOIN LATERAL DummyObjectDetector(data) AS T ;'
            batch = execute_query_fetch_all(self.evadb, select_query, plan_generator=custom_plan_generator)
            expected_output = '|__ ProjectPlan\n    |__ LateralJoinPlan\n        |__ SeqScanPlan\n            |__ StoragePlan\n        |__ FunctionScanPlan\n'
            self.assertEqual(batch.frames[0][0], expected_output)

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    video_file_path = create_sample_video(NUM_FRAMES)
    load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(cls.evadb, load_query)
    load_functions_for_testing(cls.evadb, mode='debug')

class ErrorHandlingRayTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        os.environ['ray'] = str(self.evadb.catalog().get_configuration_catalog_value('ray'))
        self.evadb.catalog().reset()
        load_functions_for_testing(self.evadb, mode='debug')
        img_path = create_sample_image()
        execute_query_fetch_all(self.evadb, f"LOAD IMAGE '{img_path}' INTO testRayErrorHandling;")
        Path(img_path).unlink()

    def tearDown(self):
        shutdown_ray()
        drop_table_query = 'DROP TABLE testRayErrorHandling;'
        execute_query_fetch_all(self.evadb, drop_table_query)

    @ray_skip_marker
    def test_ray_error_populate_to_all_stages(self):
        function_name, task = ('HFObjectDetector', 'image-classification')
        create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK '{task}'\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT HFObjectDetector(data) FROM testRayErrorHandling;'
        with self.assertRaises(ExecutorError):
            _ = execute_query_fetch_all(self.evadb, select_query)
        time.sleep(3)
        self.assertFalse(is_ray_stage_running())

def setUp(self):
    self.evadb = get_evadb_for_testing()
    os.environ['ray'] = str(self.evadb.catalog().get_configuration_catalog_value('ray'))
    self.evadb.catalog().reset()
    load_functions_for_testing(self.evadb, mode='debug')
    img_path = create_sample_image()
    execute_query_fetch_all(self.evadb, f"LOAD IMAGE '{img_path}' INTO testRayErrorHandling;")
    Path(img_path).unlink()

class LikeTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        meme1 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme1.jpg'
        meme2 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme2.jpg'
        execute_query_fetch_all(self.evadb, f"LOAD IMAGE '{meme1}' INTO MemeImages;")
        execute_query_fetch_all(self.evadb, f"LOAD IMAGE '{meme2}' INTO MemeImages;")

    def tearDown(self):
        shutdown_ray()
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MemeImages;')

    @ocr_skip_marker
    def test_like_with_ocr(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS OCRExtractor\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (labels NDARRAY STR(10),\n                          bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  OCRExtraction\n                  IMPL  'evadb/functions/ocr_extractor.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT X.label, X.x, X.y FROM MemeImages JOIN LATERAL UNNEST(OCRExtractor(data)) AS X(label, x, y) WHERE label LIKE {};'.format("'.*SWAG.*'")
        actual_batch = execute_query_fetch_all(self.evadb, select_query)
        self.assertEqual(len(actual_batch), 1)

    @ocr_skip_marker
    def test_like_fails_on_non_string_col(self):
        create_function_query = "CREATE FUNCTION IF NOT EXISTS OCRExtractor\n                  INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                  OUTPUT (labels NDARRAY STR(10),\n                          bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                          scores NDARRAY FLOAT32(ANYDIM))\n                  TYPE  OCRExtraction\n                  IMPL  'evadb/functions/ocr_extractor.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query = 'SELECT * FROM MemeImages JOIN LATERAL UNNEST(OCRExtractor(data)) AS X(label, x, y) WHERE x LIKE "[A-Za-z]*CANT";'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, select_query)

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    meme1 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme1.jpg'
    meme2 = f'{EvaDB_ROOT_DIR}/data/detoxify/meme2.jpg'
    execute_query_fetch_all(self.evadb, f"LOAD IMAGE '{meme1}' INTO MemeImages;")
    execute_query_fetch_all(self.evadb, f"LOAD IMAGE '{meme2}' INTO MemeImages;")

@pytest.mark.notparallel
class ModelTrainTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        create_table_query = '\n            CREATE TABLE AirData (            unique_id TEXT(30),            ds TEXT(30),            y INTEGER);'
        execute_query_fetch_all(cls.evadb, create_table_query)
        create_table_query = '\n            CREATE TABLE AirDataPanel (            unique_id TEXT(30),            ds TEXT(30),            y INTEGER,            trend INTEGER,            ylagged INTEGER);'
        execute_query_fetch_all(cls.evadb, create_table_query)
        create_table_query = '\n            CREATE TABLE HomeData (            saledate TEXT(30),            ma INTEGER,\n            type TEXT(30),            bedrooms INTEGER);'
        execute_query_fetch_all(cls.evadb, create_table_query)
        path = f'{EvaDB_ROOT_DIR}/data/forecasting/air-passengers.csv'
        load_query = f"LOAD CSV '{path}' INTO AirData;"
        execute_query_fetch_all(cls.evadb, load_query)
        path = f'{EvaDB_ROOT_DIR}/data/forecasting/AirPassengersPanel.csv'
        load_query = f"LOAD CSV '{path}' INTO AirDataPanel;"
        execute_query_fetch_all(cls.evadb, load_query)
        path = f'{EvaDB_ROOT_DIR}/data/forecasting/home_sales.csv'
        load_query = f"LOAD CSV '{path}' INTO HomeData;"
        execute_query_fetch_all(cls.evadb, load_query)

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS AirData;')
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS HomeData;')
        execute_query_fetch_all(cls.evadb, 'DROP FUNCTION IF EXISTS AirForecast;')
        execute_query_fetch_all(cls.evadb, 'DROP FUNCTION IF EXISTS HomeForecast;')

    @forecast_skip_marker
    def test_forecast(self):
        create_predict_udf = "\n            CREATE FUNCTION AirForecast FROM\n            (SELECT unique_id, ds, y FROM AirData)\n            TYPE Forecasting\n            HORIZON 12\n            PREDICT 'y';\n        "
        execute_query_fetch_all(self.evadb, create_predict_udf)
        predict_query = '\n            SELECT AirForecast() order by y;\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result), 12)
        self.assertEqual(result.columns, ['airforecast.unique_id', 'airforecast.ds', 'airforecast.y', 'airforecast.y-lo', 'airforecast.y-hi'])

    @pytest.mark.skip(reason='Neuralforecast intergration test takes too long to complete without GPU.')
    @forecast_skip_marker
    def test_forecast_neuralforecast(self):
        create_predict_udf = "\n            CREATE FUNCTION AirPanelForecast FROM\n            (SELECT unique_id, ds, y, trend FROM AirDataPanel)\n            TYPE Forecasting\n            HORIZON 12\n            PREDICT 'y'\n            LIBRARY 'neuralforecast'\n            AUTO 'false'\n            FREQUENCY 'M';\n        "
        execute_query_fetch_all(self.evadb, create_predict_udf)
        predict_query = '\n            SELECT AirPanelForecast() order by y;\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result), 24)
        self.assertEqual(result.columns, ['airpanelforecast.unique_id', 'airpanelforecast.ds', 'airpanelforecast.y', 'airpanelforecast.y-lo', 'airpanelforecast.y-hi'])

    @forecast_skip_marker
    def test_forecast_with_column_rename(self):
        create_predict_udf = "\n            CREATE FUNCTION HomeForecast FROM\n            (\n                SELECT type, saledate, ma FROM HomeData\n                WHERE bedrooms = 2\n            )\n            TYPE Forecasting\n            HORIZON 12\n            PREDICT 'ma'\n            ID 'type'\n            TIME 'saledate'\n            FREQUENCY 'M';\n        "
        execute_query_fetch_all(self.evadb, create_predict_udf)
        predict_query = '\n            SELECT HomeForecast();\n        '
        result = execute_query_fetch_all(self.evadb, predict_query)
        self.assertEqual(len(result), 24)
        self.assertEqual(result.columns, ['homeforecast.type', 'homeforecast.saledate', 'homeforecast.ma', 'homeforecast.ma-lo', 'homeforecast.ma-hi'])

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    create_table_query = '\n            CREATE TABLE AirData (            unique_id TEXT(30),            ds TEXT(30),            y INTEGER);'
    execute_query_fetch_all(cls.evadb, create_table_query)
    create_table_query = '\n            CREATE TABLE AirDataPanel (            unique_id TEXT(30),            ds TEXT(30),            y INTEGER,            trend INTEGER,            ylagged INTEGER);'
    execute_query_fetch_all(cls.evadb, create_table_query)
    create_table_query = '\n            CREATE TABLE HomeData (            saledate TEXT(30),            ma INTEGER,\n            type TEXT(30),            bedrooms INTEGER);'
    execute_query_fetch_all(cls.evadb, create_table_query)
    path = f'{EvaDB_ROOT_DIR}/data/forecasting/air-passengers.csv'
    load_query = f"LOAD CSV '{path}' INTO AirData;"
    execute_query_fetch_all(cls.evadb, load_query)
    path = f'{EvaDB_ROOT_DIR}/data/forecasting/AirPassengersPanel.csv'
    load_query = f"LOAD CSV '{path}' INTO AirDataPanel;"
    execute_query_fetch_all(cls.evadb, load_query)
    path = f'{EvaDB_ROOT_DIR}/data/forecasting/home_sales.csv'
    load_query = f"LOAD CSV '{path}' INTO HomeData;"
    execute_query_fetch_all(cls.evadb, load_query)

class ChatGPTTest(unittest.TestCase):

    def setUp(self) -> None:
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        create_table_query = 'CREATE TABLE IF NOT EXISTS MyTextCSV (\n                prompt TEXT(30),\n                content TEXT (100)\n            );'
        execute_query_fetch_all(self.evadb, create_table_query)
        self.csv_file_path = create_dummy_csv_file(self.evadb.catalog())
        csv_query = f"LOAD CSV '{self.csv_file_path}' INTO MyTextCSV;"
        execute_query_fetch_all(self.evadb, csv_query)
        os.environ['OPENAI_API_KEY'] = 'sk-...'

    def tearDown(self) -> None:
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyTextCSV;')

    @chatgpt_skip_marker
    def test_openai_chat_completion_function(self):
        function_name = 'ChatGPT'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS{function_name}\n            IMPL 'evadb/functions/chatgpt.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        gpt_query = f"SELECT {function_name}('summarize', content) FROM MyTextCSV;"
        output_batch = execute_query_fetch_all(self.evadb, gpt_query)
        self.assertEqual(output_batch.columns, ['chatgpt.response'])

def setUp(self) -> None:
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    create_table_query = 'CREATE TABLE IF NOT EXISTS MyTextCSV (\n                prompt TEXT(30),\n                content TEXT (100)\n            );'
    execute_query_fetch_all(self.evadb, create_table_query)
    self.csv_file_path = create_dummy_csv_file(self.evadb.catalog())
    csv_query = f"LOAD CSV '{self.csv_file_path}' INTO MyTextCSV;"
    execute_query_fetch_all(self.evadb, csv_query)
    os.environ['OPENAI_API_KEY'] = 'sk-...'

class StableDiffusionTest(unittest.TestCase):

    def setUp(self) -> None:
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        create_table_query = 'CREATE TABLE IF NOT EXISTS ImageGen (\n             prompt TEXT);\n                '
        execute_query_fetch_all(self.evadb, create_table_query)
        test_prompts = ['pink cat riding a rocket to the moon']
        for prompt in test_prompts:
            insert_query = f"INSERT INTO ImageGen (prompt) VALUES ('{prompt}')"
            execute_query_fetch_all(self.evadb, insert_query)

    def tearDown(self) -> None:
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS ImageGen;')

    @stable_diffusion_skip_marker
    @pytest.mark.xfail(reason='API call might be flaky due to rate limits or other issues.')
    def test_stable_diffusion_image_generation(self):
        function_name = 'StableDiffusion'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS {function_name}\n            IMPL 'evadb/functions/stable_diffusion.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        gpt_query = f'SELECT {function_name}(prompt) FROM ImageGen;'
        output_batch = execute_query_fetch_all(self.evadb, gpt_query)
        self.assertEqual(output_batch.columns, ['stablediffusion.response'])
        img_data = output_batch.frames['stablediffusion.response'][0]
        self.assertIsInstance(img_data, np.ndarray)
        self.assertEqual(img_data.shape[2], 3)

def setUp(self) -> None:
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    create_table_query = 'CREATE TABLE IF NOT EXISTS ImageGen (\n             prompt TEXT);\n                '
    execute_query_fetch_all(self.evadb, create_table_query)
    test_prompts = ['pink cat riding a rocket to the moon']
    for prompt in test_prompts:
        insert_query = f"INSERT INTO ImageGen (prompt) VALUES ('{prompt}')"
        execute_query_fetch_all(self.evadb, insert_query)

class StrHelperTest(unittest.TestCase):

    def setUp(self) -> None:
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        create_table_query = 'CREATE TABLE IF NOT EXISTS Test (\n             input TEXT);\n                '
        execute_query_fetch_all(self.evadb, create_table_query)
        test_prompts = ['EvaDB']
        for prompt in test_prompts:
            insert_query = f"INSERT INTO Test (input) VALUES ('{prompt}')"
            execute_query_fetch_all(self.evadb, insert_query)

    def tearDown(self) -> None:
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS Test;')

    def test_upper_function(self):
        function_name = 'UPPER'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS {function_name}\n        INPUT  (inp ANYTYPE)\n        OUTPUT (output NDARRAY STR(ANYDIM))\n        TYPE HelperFunction\n        IMPL 'evadb/functions/helpers/upper.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        query = 'SELECT UPPER(input) FROM Test;'
        output_batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(output_batch), 1)
        self.assertEqual(output_batch.frames['upper.output'][0], 'EVADB')
        query = "SELECT UPPER('test5')"
        output_batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(output_batch), 1)
        self.assertEqual(output_batch.frames['upper.output'][0], 'TEST5')

    def test_lower_function(self):
        function_name = 'LOWER'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS {function_name}\n        INPUT  (inp ANYTYPE)\n        OUTPUT (output NDARRAY STR(ANYDIM))\n        TYPE HelperFunction\n        IMPL 'evadb/functions/helpers/lower.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        query = 'SELECT LOWER(input) FROM Test;'
        output_batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(output_batch), 1)
        self.assertEqual(output_batch.frames['lower.output'][0], 'evadb')
        query = "SELECT LOWER('TEST5')"
        output_batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(output_batch), 1)
        self.assertEqual(output_batch.frames['lower.output'][0], 'test5')

    def test_concat_function(self):
        function_name = 'CONCAT'
        execute_query_fetch_all(self.evadb, f'DROP FUNCTION IF EXISTS {function_name};')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS {function_name}\n        INPUT  (inp ANYTYPE)\n        OUTPUT (output NDARRAY STR(ANYDIM))\n        TYPE HelperFunction\n        IMPL 'evadb/functions/helpers/concat.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION IF EXISTS UPPER;')
        create_function_query = "CREATE FUNCTION IF NOT EXISTS UPPER\n        INPUT  (inp ANYTYPE)\n        OUTPUT (output NDARRAY STR(ANYDIM))\n        TYPE HelperFunction\n        IMPL 'evadb/functions/helpers/upper.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        query = "SELECT CONCAT(UPPER('Eva'), 'DB');"
        output_batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(output_batch), 1)
        self.assertEqual(output_batch.frames['concat.output'][0], 'EVADB')
        query = "SELECT CONCAT(input, '.com') FROM Test;"
        output_batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(output_batch), 1)
        self.assertEqual(output_batch.frames['concat.output'][0], 'EvaDB.com')

def setUp(self) -> None:
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    create_table_query = 'CREATE TABLE IF NOT EXISTS Test (\n             input TEXT);\n                '
    execute_query_fetch_all(self.evadb, create_table_query)
    test_prompts = ['EvaDB']
    for prompt in test_prompts:
        insert_query = f"INSERT INTO Test (input) VALUES ('{prompt}')"
        execute_query_fetch_all(self.evadb, insert_query)

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

def setUp(self):
    self.evadb.catalog().reset()
    self.mnist_path = f'{EvaDB_ROOT_DIR}/data/mnist/mnist.mp4'
    load_functions_for_testing(self.evadb)
    self.images = f'{EvaDB_ROOT_DIR}/data/detoxify/*.jpg'

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

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video()
    self.image_files_path = Path(f'{EvaDB_ROOT_DIR}/test/data/uadetrac/small-data/MVI_20011/*.jpg')
    self.csv_file_path = create_sample_csv()

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

class CreateJobTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        cls.job_name = 'test_async_job'

    def setUp(self):
        execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {self.job_name};')

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, f'DROP JOB IF EXISTS {cls.job_name};')

    def test_invalid_query_in_job_should_raise_exception(self):
        query = f"CREATE JOB {self.job_name} AS {{\n                    CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n                        ( SELECT * FROM postgres_data.home_sales\n                    TYPE Forecasting\n                    PREDICT 'price';\n                }}\n                START '2023-04-01 01:10:00'\n                END '2023-05-01'\n                EVERY 2 week;\n            "
        with self.assertRaisesRegex(Exception, 'Failed to parse the job query'):
            execute_query_fetch_all(self.evadb, query)

    def test_create_job_should_add_the_entry(self):
        queries = ["CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n                ( SELECT * FROM postgres_data.home_sales )\n                TYPE Forecasting\n                PREDICT 'price';", 'Select HomeSalesForecast(10);']
        start = '2023-04-01 01:10:00'
        end = '2023-05-01'
        repeat_interval = 2
        repeat_period = 'week'
        all_queries = ''.join(queries)
        query = f"CREATE JOB {self.job_name} AS {{\n                   {all_queries}\n                }}\n                START '{start}'\n                END '{end}'\n                EVERY {repeat_interval} {repeat_period};"
        execute_query_fetch_all(self.evadb, query)
        datetime_format = '%Y-%m-%d %H:%M:%S'
        date_format = '%Y-%m-%d'
        job_entry = self.evadb.catalog().get_job_catalog_entry(self.job_name)
        self.assertEqual(job_entry.name, self.job_name)
        self.assertEqual(job_entry.start_time, datetime.strptime(start, datetime_format))
        self.assertEqual(job_entry.end_time, datetime.strptime(end, date_format))
        self.assertEqual(job_entry.repeat_interval, 2 * 7 * 24 * 60 * 60)
        self.assertEqual(job_entry.active, True)
        self.assertEqual(len(job_entry.queries), len(queries))

    def test_should_create_job_with_if_not_exists(self):
        if_not_exists = 'IF NOT EXISTS'
        queries = ["CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n                ( SELECT * FROM postgres_data.home_sales )\n                TYPE Forecasting\n                PREDICT 'price';", 'Select HomeSalesForecast(10);']
        query = "CREATE JOB {} {} AS {{\n                    {}\n                }}\n                START '2023-04-01'\n                END '2023-05-01'\n                EVERY 2 week;\n            "
        execute_query_fetch_all(self.evadb, query.format(if_not_exists, self.job_name, ''.join(queries)))
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query.format('', self.job_name, ''.join(queries)))
        execute_query_fetch_all(self.evadb, query.format(if_not_exists, self.job_name, ''.join(queries)))

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    cls.job_name = 'test_async_job'

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
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    cls.db_path = f'{os.path.dirname(os.path.abspath(__file__))}/testing.db'

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

def test_expression_tree_signature(self):
    plan = get_logical_query_plan(self.evadb, "SELECT id FROM MyVideo WHERE DummyMultiObjectDetector(data).labels @> ['person'];")
    signature = next(plan.find_all(LogicalFilter)).predicate.children[0].signature()
    function_id = self.evadb.catalog().get_function_catalog_entry_by_name('DummyMultiObjectDetector').row_id
    table_entry = self.evadb.catalog().get_table_catalog_entry('MyVideo')
    col_id = self.evadb.catalog().get_column_catalog_entry(table_entry, 'data').row_id
    self.assertEqual(signature, f'DummyMultiObjectDetector[{function_id}](MyVideo.data[{col_id}])')

@pytest.mark.notparallel
class DropObjectExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()

    def tearDown(self):
        file_remove('dummy.avi')

    def _create_index(self, index_name):
        import numpy as np
        feat1 = np.array([[0, 0, 0]]).astype(np.float32)
        feat2 = np.array([[100, 100, 100]]).astype(np.float32)
        feat3 = np.array([[200, 200, 200]]).astype(np.float32)
        execute_query_fetch_all(self.evadb, 'create table if not exists testCreateIndexFeatTable (\n                feat NDARRAY FLOAT32(1,3)\n            );')
        feat_batch_data = Batch(pd.DataFrame(data={'feat': [feat1, feat2, feat3]}))
        feat_tb_entry = self.evadb.catalog().get_table_catalog_entry('testCreateIndexFeatTable')
        storage_engine = StorageEngine.factory(self.evadb, feat_tb_entry)
        storage_engine.write(feat_tb_entry, feat_batch_data)
        query = f'CREATE INDEX {index_name} ON testCreateIndexFeatTable (feat) USING FAISS;'
        execute_query_fetch_all(self.evadb, query)

    def test_should_drop_table(self):
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        table_catalog_entry = self.evadb.catalog().get_table_catalog_entry('MyVideo')
        video_dir = table_catalog_entry.file_url
        self.assertFalse(table_catalog_entry is None)
        column_objects = self.evadb.catalog().get_column_catalog_entries_by_table(table_catalog_entry)
        self.assertEqual(len(column_objects), len(get_video_table_column_definitions()) + 1)
        self.assertTrue(Path(video_dir).exists())
        video_metadata_table = self.evadb.catalog().get_multimedia_metadata_table_catalog_entry(table_catalog_entry)
        self.assertTrue(video_metadata_table is not None)
        drop_query = 'DROP TABLE IF EXISTS MyVideo;'
        execute_query_fetch_all(self.evadb, drop_query)
        self.assertTrue(self.evadb.catalog().get_table_catalog_entry('MyVideo') is None)
        column_objects = self.evadb.catalog().get_column_catalog_entries_by_table(table_catalog_entry)
        self.assertEqual(len(column_objects), 0)
        self.assertFalse(Path(video_dir).exists())
        drop_query = 'DROP TABLE MyVideo;'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, drop_query, do_not_print_exceptions=True)
        execute_query_fetch_all(self.evadb, query)
        execute_query_fetch_all(self.evadb, drop_query)

    def run_create_function_query(self):
        create_function_query = "CREATE FUNCTION DummyObjectDetector\n            INPUT  (Frame_Array NDARRAY UINT8(3, 256, 256))\n            OUTPUT (label NDARRAY STR(10))\n            TYPE  Classification\n            IMPL  'test/util.py';"
        execute_query_fetch_all(self.evadb, create_function_query)

    def test_should_drop_function(self):
        self.run_create_function_query()
        function_name = 'DummyObjectDetector'
        function = self.evadb.catalog().get_function_catalog_entry_by_name(function_name)
        self.assertTrue(function is not None)
        drop_query = 'DROP FUNCTION IF EXISTS {};'.format(function_name)
        execute_query_fetch_all(self.evadb, drop_query)
        function = self.evadb.catalog().get_function_catalog_entry_by_name(function_name)
        self.assertTrue(function is None)
        self.run_create_function_query()
        execute_query_fetch_all(self.evadb, drop_query)

    def test_drop_wrong_function_name(self):
        self.run_create_function_query()
        right_function_name = 'DummyObjectDetector'
        wrong_function_name = 'FakeDummyObjectDetector'
        function = self.evadb.catalog().get_function_catalog_entry_by_name(right_function_name)
        self.assertTrue(function is not None)
        drop_query = 'DROP FUNCTION {};'.format(wrong_function_name)
        try:
            execute_query_fetch_all(self.evadb, drop_query, do_not_print_exceptions=True)
        except Exception as e:
            err_msg = 'Function {} does not exist, therefore cannot be dropped.'.format(wrong_function_name)
            self.assertTrue(str(e) == err_msg)
        function = self.evadb.catalog().get_function_catalog_entry_by_name(right_function_name)
        self.assertTrue(function is not None)

    def test_should_drop_index(self):
        index_name = 'index_name'
        self._create_index(index_name)
        index_obj = self.evadb.catalog().get_index_catalog_entry_by_name(index_name)
        self.assertTrue(index_obj is not None)
        wrong_function_name = 'wrong_function_name'
        drop_query = f'DROP INDEX {wrong_function_name};'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, drop_query, do_not_print_exceptions=True)
        obj = self.evadb.catalog().get_index_catalog_entry_by_name(index_name)
        self.assertTrue(obj is not None)
        drop_query = f'DROP INDEX IF EXISTS {index_name};'
        execute_query_fetch_all(self.evadb, drop_query)
        index_obj = self.evadb.catalog().get_index_catalog_entry_by_name(index_name)
        self.assertTrue(index_obj is None)

    def test_should_drop_database(self):
        database_name = 'test_data_source'
        params = {'database': 'evadb.db'}
        query = f'CREATE DATABASE {database_name}\n                    WITH ENGINE = "sqlite",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self.assertIsNotNone(self.evadb.catalog().get_database_catalog_entry(database_name))
        execute_query_fetch_all(self.evadb, f'DROP DATABASE {database_name}')
        self.assertIsNone(self.evadb.catalog().get_database_catalog_entry(database_name))
        result = execute_query_fetch_all(self.evadb, f'DROP DATABASE IF EXISTS {database_name}')
        self.assertTrue('does not exist' in result.frames.to_string())
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, f'DROP DATABASE {database_name}', do_not_print_exceptions=True)
        execute_query_fetch_all(self.evadb, query)
        result = execute_query_fetch_all(self.evadb, f'DROP DATABASE IF EXISTS {database_name}')

    def test_should_drop_job(self):
        job_name = 'test_async_job'
        query = f"CREATE JOB {job_name} AS {{\n            SELECT * from job_catalog;\n        }}\n        START '2023-04-01'\n        END '2023-05-01'\n        EVERY 2 week;"
        execute_query_fetch_all(self.evadb, query)
        self.assertIsNotNone(self.evadb.catalog().get_job_catalog_entry(job_name))
        execute_query_fetch_all(self.evadb, f'DROP JOB {job_name}')
        self.assertIsNone(self.evadb.catalog().get_job_catalog_entry(job_name))
        result = execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {job_name}')
        self.assertTrue('does not exist' in result.frames.to_string())
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, f'DROP JOB {job_name}', do_not_print_exceptions=True)
        execute_query_fetch_all(self.evadb, query)
        result = execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {job_name}')

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video()

def _create_index(self, index_name):
    import numpy as np
    feat1 = np.array([[0, 0, 0]]).astype(np.float32)
    feat2 = np.array([[100, 100, 100]]).astype(np.float32)
    feat3 = np.array([[200, 200, 200]]).astype(np.float32)
    execute_query_fetch_all(self.evadb, 'create table if not exists testCreateIndexFeatTable (\n                feat NDARRAY FLOAT32(1,3)\n            );')
    feat_batch_data = Batch(pd.DataFrame(data={'feat': [feat1, feat2, feat3]}))
    feat_tb_entry = self.evadb.catalog().get_table_catalog_entry('testCreateIndexFeatTable')
    storage_engine = StorageEngine.factory(self.evadb, feat_tb_entry)
    storage_engine.write(feat_tb_entry, feat_batch_data)
    query = f'CREATE INDEX {index_name} ON testCreateIndexFeatTable (feat) USING FAISS;'
    execute_query_fetch_all(self.evadb, query)

def test_should_drop_table(self):
    query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(self.evadb, query)
    table_catalog_entry = self.evadb.catalog().get_table_catalog_entry('MyVideo')
    video_dir = table_catalog_entry.file_url
    self.assertFalse(table_catalog_entry is None)
    column_objects = self.evadb.catalog().get_column_catalog_entries_by_table(table_catalog_entry)
    self.assertEqual(len(column_objects), len(get_video_table_column_definitions()) + 1)
    self.assertTrue(Path(video_dir).exists())
    video_metadata_table = self.evadb.catalog().get_multimedia_metadata_table_catalog_entry(table_catalog_entry)
    self.assertTrue(video_metadata_table is not None)
    drop_query = 'DROP TABLE IF EXISTS MyVideo;'
    execute_query_fetch_all(self.evadb, drop_query)
    self.assertTrue(self.evadb.catalog().get_table_catalog_entry('MyVideo') is None)
    column_objects = self.evadb.catalog().get_column_catalog_entries_by_table(table_catalog_entry)
    self.assertEqual(len(column_objects), 0)
    self.assertFalse(Path(video_dir).exists())
    drop_query = 'DROP TABLE MyVideo;'
    with self.assertRaises(ExecutorError):
        execute_query_fetch_all(self.evadb, drop_query, do_not_print_exceptions=True)
    execute_query_fetch_all(self.evadb, query)
    execute_query_fetch_all(self.evadb, drop_query)

@pytest.mark.notparallel
class InsertExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()
        query = 'CREATE TABLE IF NOT EXISTS CSVTable\n            (\n                name TEXT(100)\n            );\n        '
        execute_query_fetch_all(self.evadb, query)
        query = 'CREATE TABLE IF NOT EXISTS books\n            (\n                name    TEXT(100),\n                author  TEXT(100),\n                year    INTEGER\n            );\n        '
        execute_query_fetch_all(self.evadb, query)

    def tearDown(self):
        shutdown_ray()
        file_remove('dummy.avi')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS books;')

    @unittest.skip('Not supported in current version')
    def test_should_load_video_in_table(self):
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        insert_query = ' INSERT INTO MyVideo (id, data) VALUES\n            (40, [[40, 40, 40], [40, 40, 40]],\n                 [[40, 40, 40], [40, 40, 40]]);'
        execute_query_fetch_all(self.evadb, insert_query)
        insert_query_2 = ' INSERT INTO MyVideo (id, data) VALUES\n        ( 41, [[41, 41, 41] , [41, 41, 41]],\n                [[41, 41, 41], [41, 41, 41]]);'
        execute_query_fetch_all(self.evadb, insert_query_2)
        query = 'SELECT id, data FROM MyVideo WHERE id = 40'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['data'][0], np.array([[[40, 40, 40], [40, 40, 40]], [[40, 40, 40], [40, 40, 40]]])))
        query = 'SELECT id, data FROM MyVideo WHERE id = 41;'
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['data'][0], np.array([[[41, 41, 41], [41, 41, 41]], [[41, 41, 41], [41, 41, 41]]])))

    def test_should_insert_tuples_in_table(self):
        data = pd.read_csv('./test/data/features.csv')
        for i in data.iterrows():
            logger.info(i[1][1])
            query = f"INSERT INTO CSVTable (name) VALUES (\n                            '{i[1][1]}'\n                        );"
            logger.info(query)
            batch = execute_query_fetch_all(self.evadb, query)
        query = 'SELECT name FROM CSVTable;'
        batch = execute_query_fetch_all(self.evadb, query)
        logger.info(batch)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['csvtable.name'].array, np.array(['test_evadb/similarity/data/sad.jpg', 'test_evadb/similarity/data/happy.jpg', 'test_evadb/similarity/data/angry.jpg'])))
        query = "SELECT name FROM CSVTable WHERE name LIKE '.*(sad|happy)';"
        batch = execute_query_fetch_all(self.evadb, query)
        self.assertEqual(len(batch._frames), 2)

    def test_insert_one_tuple_in_table(self):
        query = "\n            INSERT INTO books (name, author, year) VALUES (\n                'Harry Potter', 'JK Rowling', 1997\n            );\n        "
        execute_query_fetch_all(self.evadb, query)
        query = 'SELECT * FROM books;'
        batch = execute_query_fetch_all(self.evadb, query)
        logger.info(batch)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['books.name'].array, np.array(['Harry Potter'])))
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['books.author'].array, np.array(['JK Rowling'])))
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['books.year'].array, np.array([1997])))

    def test_insert_multiple_tuples_in_table(self):
        query = "\n            INSERT INTO books (name, author, year) VALUES\n            ('Fantastic Beasts Collection', 'JK Rowling', 2001),\n            ('Magic Tree House Collection', 'Mary Pope Osborne', 1992),\n            ('Sherlock Holmes', 'Arthur Conan Doyle', 1887);\n        "
        execute_query_fetch_all(self.evadb, query)
        query = 'SELECT * FROM books;'
        batch = execute_query_fetch_all(self.evadb, query)
        logger.info(batch)
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['books.name'].array, np.array(['Fantastic Beasts Collection', 'Magic Tree House Collection', 'Sherlock Holmes'])))
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['books.author'].array, np.array(['JK Rowling', 'Mary Pope Osborne', 'Arthur Conan Doyle'])))
        self.assertIsNone(np.testing.assert_array_equal(batch.frames['books.year'].array, np.array([2001, 1992, 1887])))

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video()
    query = 'CREATE TABLE IF NOT EXISTS CSVTable\n            (\n                name TEXT(100)\n            );\n        '
    execute_query_fetch_all(self.evadb, query)
    query = 'CREATE TABLE IF NOT EXISTS books\n            (\n                name    TEXT(100),\n                author  TEXT(100),\n                year    INTEGER\n            );\n        '
    execute_query_fetch_all(self.evadb, query)

@pytest.mark.notparallel
class RenameExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()
        self.video_file_path = create_sample_video()
        self.csv_file_path = create_sample_csv()

    def tearDown(self):
        file_remove('dummy.avi')
        file_remove('dummy.csv')

    def test_should_rename_table(self):
        catalog_manager = self.evadb.catalog()
        query = f"LOAD VIDEO '{self.video_file_path}' INTO MyVideo;"
        execute_query_fetch_all(self.evadb, query)
        self.assertTrue(catalog_manager.get_table_catalog_entry('MyVideo') is not None)
        self.assertTrue(catalog_manager.get_table_catalog_entry('MyVideo1') is None)
        rename_query = 'RENAME TABLE MyVideo TO MyVideo1;'
        execute_query_fetch_all(self.evadb, rename_query)
        self.assertTrue(catalog_manager.get_table_catalog_entry('MyVideo') is None)
        self.assertTrue(catalog_manager.get_table_catalog_entry('MyVideo1') is not None)
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

    def test_should_fail_on_rename_structured_table(self):
        create_table_query = '\n\n            CREATE TABLE IF NOT EXISTS MyVideoCSV (\n                id INTEGER UNIQUE,\n                frame_id INTEGER NOT NULL,\n                video_id INTEGER NOT NULL,\n                dataset_name TEXT(30) NOT NULL\n            );\n            '
        execute_query_fetch_all(self.evadb, create_table_query)
        load_query = f"LOAD CSV '{self.csv_file_path}' INTO MyVideoCSV (id, frame_id, video_id, dataset_name);"
        execute_query_fetch_all(self.evadb, load_query)
        with self.assertRaises(Exception) as cm:
            rename_query = 'RENAME TABLE MyVideoCSV TO MyVideoCSV1;'
            execute_query_fetch_all(self.evadb, rename_query)
        self.assertEqual(str(cm.exception), 'Rename not yet supported on structured data')
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideoCSV;')

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video()
    self.csv_file_path = create_sample_csv()

class CreateDatabaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()

    def test_use_should_raise_executor_error(self):
        query = 'USE not_available_ds {\n            SELECT * FROM table\n        }'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()

@pytest.mark.notparallel
class LoadPDFExecutorTests(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()

    def tearDown(self):
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDFs;')

    def test_load_pdfs(self):
        pdf_path = f'{EvaDB_ROOT_DIR}/data/documents/pdf_sample1.pdf'
        import fitz
        doc = fitz.open(pdf_path)
        number_of_paragraphs = 0
        for page in doc:
            blocks = page.get_text('dict')['blocks']
            for b in blocks:
                if b['type'] == 0:
                    block_string = ''
                    for lines in b['lines']:
                        for span in lines['spans']:
                            if span['text'].strip():
                                block_string += span['text']
                    number_of_paragraphs += 1
        execute_query_fetch_all(self.evadb, f"LOAD PDF '{pdf_path}' INTO MyPDFs;")
        result = execute_query_fetch_all(self.evadb, 'SELECT * from MyPDFs;')
        self.assertEqual(len(result.columns), 5)
        self.assertEqual(len(result), number_of_paragraphs)

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()

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

def test_should_raise_on_empty_file(self):
    Path('/tmp/empty_file.py').touch()
    with self.assertRaises(ImportError):
        load_function_class_from_file('/tmp/empty_file.py')
    Path('/tmp/empty_file.py').unlink()

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

@pytest.mark.notparallel
class SetExecutorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_set_execution(self):
        execute_query_fetch_all(self.evadb, "SET OPENAIKEY = 'ABCD';")
        current_config_value = self.evadb.catalog().get_configuration_catalog_value('OPENAIKEY')
        self.assertEqual('ABCD', current_config_value)

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()

def test_set_execution(self):
    execute_query_fetch_all(self.evadb, "SET OPENAIKEY = 'ABCD';")
    current_config_value = self.evadb.catalog().get_configuration_catalog_value('OPENAIKEY')
    self.assertEqual('ABCD', current_config_value)

class YoutubeChannelQATest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self) -> None:
        shutdown_ray()

    def test_should_run_youtube_channel_qa_app(self):
        app_path = Path('apps', 'youtube_channel_qa', 'youtube_channel_qa.py')
        input1 = '\n\n\n'
        input2 = 'What is this video about?\n'
        input3 = 'exit\n'
        inputs = input1 + input2 + input3
        command = ['python', app_path]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(inputs.encode())
        decoded_stdout = stdout.decode()
        assert 'keyboards' or 'AliExpress' or 'Rate limit' in decoded_stdout
        print(decoded_stdout)
        print(stderr.decode())

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

def test_should_run_youtube_channel_qa_app(self):
    app_path = Path('apps', 'youtube_channel_qa', 'youtube_channel_qa.py')
    input1 = '\n\n\n'
    input2 = 'What is this video about?\n'
    input3 = 'exit\n'
    inputs = input1 + input2 + input3
    command = ['python', app_path]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(inputs.encode())
    decoded_stdout = stdout.decode()
    assert 'keyboards' or 'AliExpress' or 'Rate limit' in decoded_stdout
    print(decoded_stdout)
    print(stderr.decode())

@pytest.mark.notparallel
class PrivateGPTTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self) -> None:
        shutdown_ray()
        source_directory = 'source_documents'
        if shutil.os.path.exists(source_directory):
            shutil.rmtree(source_directory)

    @unittest.skip('disable test due to inference time')
    def test_should_run_privategpt(self):
        print('INGEST')
        source_directory = 'source_documents'
        if shutil.os.path.exists(source_directory):
            shutil.rmtree(source_directory)
        url = 'https://www.eisenhowerlibrary.gov/sites/default/files/file/1953_state_of_the_union.pdf'
        pdf_destination = 'state_of_the_union.pdf'
        response = requests.get(url)
        if response.status_code == 200:
            with open(pdf_destination, 'wb') as file:
                file.write(response.content)
        os.makedirs(source_directory, exist_ok=True)
        shutil.move(pdf_destination, source_directory)
        app_path = Path('apps', 'privategpt', 'ingest.py')
        inputs = ''
        command = ['python', app_path, '--directory', 'source_documents']
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(inputs.encode())
        decoded_stdout = stdout.decode()
        assert 'Data ingestion complete' in decoded_stdout
        decoded_stderr = stderr.decode()
        assert 'Ray' in decoded_stderr
        inputs = 'When was NATO created?\nexit\n'
        app_path = Path('apps', 'privategpt', 'privateGPT.py')
        command = ['python', app_path]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(inputs.encode())
        decoded_stdout = stdout.decode()
        assert 'April 4, 1949' in decoded_stdout

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

def tearDown(self) -> None:
    shutdown_ray()
    source_directory = 'source_documents'
    if shutil.os.path.exists(source_directory):
        shutil.rmtree(source_directory)

@unittest.skip('disable test due to inference time')
def test_should_run_privategpt(self):
    print('INGEST')
    source_directory = 'source_documents'
    if shutil.os.path.exists(source_directory):
        shutil.rmtree(source_directory)
    url = 'https://www.eisenhowerlibrary.gov/sites/default/files/file/1953_state_of_the_union.pdf'
    pdf_destination = 'state_of_the_union.pdf'
    response = requests.get(url)
    if response.status_code == 200:
        with open(pdf_destination, 'wb') as file:
            file.write(response.content)
    os.makedirs(source_directory, exist_ok=True)
    shutil.move(pdf_destination, source_directory)
    app_path = Path('apps', 'privategpt', 'ingest.py')
    inputs = ''
    command = ['python', app_path, '--directory', 'source_documents']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(inputs.encode())
    decoded_stdout = stdout.decode()
    assert 'Data ingestion complete' in decoded_stdout
    decoded_stderr = stderr.decode()
    assert 'Ray' in decoded_stderr
    inputs = 'When was NATO created?\nexit\n'
    app_path = Path('apps', 'privategpt', 'privateGPT.py')
    command = ['python', app_path]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(inputs.encode())
    decoded_stdout = stdout.decode()
    assert 'April 4, 1949' in decoded_stdout

class YoutubeQATest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self) -> None:
        shutdown_ray()

    @chatgpt_skip_marker
    def test_should_run_youtube_qa_app(self):
        app_path = Path('apps', 'youtube_qa', 'youtube_qa.py')
        input1 = 'yes\n\n'
        input2 = 'What is this video on?\n'
        input3 = 'exit\nexit\n'
        inputs = input1 + input2 + input3
        command = ['python', app_path]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(inputs.encode())
        decoded_stdout = stdout.decode()
        assert 'Julia' or 'Rate limit' in decoded_stdout
        print(decoded_stdout)
        print(stderr.decode())

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

@chatgpt_skip_marker
def test_should_run_youtube_qa_app(self):
    app_path = Path('apps', 'youtube_qa', 'youtube_qa.py')
    input1 = 'yes\n\n'
    input2 = 'What is this video on?\n'
    input3 = 'exit\nexit\n'
    inputs = input1 + input2 + input3
    command = ['python', app_path]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(inputs.encode())
    decoded_stdout = stdout.decode()
    assert 'Julia' or 'Rate limit' in decoded_stdout
    print(decoded_stdout)
    print(stderr.decode())

class PandasQATest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self) -> None:
        shutdown_ray()

    @chatgpt_skip_marker
    def test_should_run_pandas_qa_app(self):
        app_path = Path('apps', 'pandas_qa', 'pandas_qa.py')
        input1 = '\n'
        input2 = 'Print country with highest gdp\n\n'
        input3 = 'yes\n\n'
        inputs = input1 + input2 + input3
        command = ['python', app_path]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(inputs.encode())
        decoded_stdout = stdout.decode()
        assert 'Country' or 'Rate' in decoded_stdout

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    os.environ['ray'] = str(cls.evadb.catalog().get_configuration_catalog_value('ray'))

@chatgpt_skip_marker
def test_should_run_pandas_qa_app(self):
    app_path = Path('apps', 'pandas_qa', 'pandas_qa.py')
    input1 = '\n'
    input2 = 'Print country with highest gdp\n\n'
    input3 = 'yes\n\n'
    inputs = input1 + input2 + input3
    command = ['python', app_path]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(inputs.encode())
    decoded_stdout = stdout.decode()
    assert 'Country' or 'Rate' in decoded_stdout

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

def setUp(self) -> None:
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    create_table_query = 'CREATE TABLE IF NOT EXISTS ImageGen (\n             prompt TEXT(100));\n                '
    execute_query_fetch_all(self.evadb, create_table_query)
    test_prompts = ['a surreal painting of a cat']
    for prompt in test_prompts:
        insert_query = f"INSERT INTO ImageGen (prompt) VALUES ('{prompt}')"
        execute_query_fetch_all(self.evadb, insert_query)

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

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()
    self.video_file_path = create_sample_video(NUM_FRAMES)

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

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    video_file_path = create_sample_video()
    load_query = f"LOAD VIDEO '{video_file_path}' INTO MyVideo;"
    execute_query_fetch_all(cls.evadb, load_query)

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

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()

class CSVLoaderTest(unittest.TestCase):

    def setUp(self):
        self.csv_file_path = create_sample_csv()

    def tearDown(self):
        file_remove('dummy.csv')

    def test_should_return_one_batch(self):
        column_list = [TupleValueExpression(name='id', table_alias='dummy'), TupleValueExpression(name='frame_id', table_alias='dummy'), TupleValueExpression(name='video_id', table_alias='dummy')]
        csv_loader = CSVReader(file_url=self.csv_file_path, column_list=column_list)
        batches = list(csv_loader.read())
        expected = list(create_dummy_csv_batches(target_columns=['id', 'frame_id', 'video_id']))
        self.assertEqual(batches, expected)

def setUp(self):
    self.csv_file_path = create_sample_csv()

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

def setUp(self):
    self.table = self.create_sample_table()

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

def setUp(self):
    evadb = get_evadb_for_testing()
    mock.table_type = TableType.VIDEO_DATA
    self.video_engine = StorageEngine.factory(evadb, mock)
    self.table = self.create_sample_table()

@pytest.mark.notparallel
class NativeExecutorTest(unittest.TestCase):

    def setUp(self):
        self.evadb = get_evadb_for_testing()
        self.evadb.catalog().reset()

    def tearDown(self):
        shutdown_ray()
        self._drop_table_in_native_database()
        self._drop_table_in_evadb_database()

    def _create_table_in_native_database(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                CREATE TABLE test_table (\n                    name VARCHAR(10),\n                    Age INT,\n                    comment VARCHAR (100)\n                )\n            }')

    def _insert_value_into_native_database(self, col1, col2, col3):
        execute_query_fetch_all(self.evadb, f"USE test_data_source {{\n                INSERT INTO test_table (\n                    name, Age, comment\n                ) VALUES (\n                    '{col1}', {col2}, '{col3}'\n                )\n            }}")

    def _drop_table_in_native_database(self):
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DROP TABLE IF EXISTS test_table\n            }')
        execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                DROP TABLE IF EXISTS derived_table\n            }')

    def _drop_table_in_evadb_database(self):
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS eva_table;')

    def _create_evadb_table_using_select_query(self):
        execute_query_fetch_all(self.evadb, 'CREATE TABLE eva_table AS SELECT name, Age FROM test_data_source.test_table;')
        res_batch = execute_query_fetch_all(self.evadb, 'Select * from eva_table')
        self.assertEqual(len(res_batch), 2)
        self.assertEqual(res_batch.frames['eva_table.name'][0], 'aa')
        self.assertEqual(res_batch.frames['eva_table.age'][0], 1)
        self.assertEqual(res_batch.frames['eva_table.name'][1], 'bb')
        self.assertEqual(res_batch.frames['eva_table.age'][1], 2)

    def _create_native_table_using_select_query(self):
        execute_query_fetch_all(self.evadb, 'CREATE TABLE test_data_source.derived_table AS SELECT name, age FROM test_data_source.test_table;')
        res_batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM test_data_source.derived_table')
        self.assertEqual(len(res_batch), 2)
        self.assertEqual(res_batch.frames['derived_table.name'][0], 'aa')
        self.assertEqual(res_batch.frames['derived_table.age'][0], 1)
        self.assertEqual(res_batch.frames['derived_table.name'][1], 'bb')
        self.assertEqual(res_batch.frames['derived_table.age'][1], 2)

    def _execute_evadb_query(self):
        self._create_table_in_native_database()
        self._insert_value_into_native_database('aa', 1, 'aaaa')
        self._insert_value_into_native_database('bb', 2, 'bbbb')
        res_batch = execute_query_fetch_all(self.evadb, 'SELECT * FROM test_data_source.test_table')
        self.assertEqual(len(res_batch), 2)
        self.assertEqual(res_batch.frames['test_table.name'][0], 'aa')
        self.assertEqual(res_batch.frames['test_table.age'][0], 1)
        self.assertEqual(res_batch.frames['test_table.name'][1], 'bb')
        self.assertEqual(res_batch.frames['test_table.age'][1], 2)
        self._create_evadb_table_using_select_query()
        self._create_native_table_using_select_query()
        self._drop_table_in_native_database()
        self._drop_table_in_evadb_database()

    def _execute_native_query(self):
        self._create_table_in_native_database()
        self._insert_value_into_native_database('aa', 1, 'aaaa')
        res_batch = execute_query_fetch_all(self.evadb, 'USE test_data_source {\n                SELECT * FROM test_table\n            }')
        self.assertEqual(len(res_batch), 1)
        self.assertEqual(res_batch.frames['name'][0], 'aa')
        self.assertEqual(res_batch.frames['age'][0], 1)
        self.assertEqual(res_batch.frames['comment'][0], 'aaaa')
        self._drop_table_in_native_database()

    def _raise_error_on_multiple_creation(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)

    def _raise_error_on_invalid_connection(self):
        params = {'user': 'xxxxxx', 'password': 'xxxxxx', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE invaid\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        with self.assertRaises(ExecutorError):
            execute_query_fetch_all(self.evadb, query)

    def test_should_run_query_in_postgres(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()
        self._raise_error_on_multiple_creation()
        self._raise_error_on_invalid_connection()

    def test_should_run_query_in_mariadb(self):
        params = {'user': 'eva', 'password': 'password', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "mariadb",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    def test_should_run_query_in_clickhouse(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '9000', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "clickhouse",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    @pytest.mark.skip(reason='Snowflake does not come with a free version of account, so integration test is not feasible')
    def test_should_run_query_in_snowflake(self):
        params = {'user': 'eva', 'password': 'password', 'account': 'account_number', 'database': 'EVADB', 'schema': 'SAMPLE_DATA', 'warehouse': 'warehouse'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "snowflake",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    def test_should_run_query_in_sqlite(self):
        import os
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        params = {'database': f'{current_file_dir}/evadb.db'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "sqlite",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

    def test_should_run_query_in_mysql(self):
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '3306', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "mysql",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(self.evadb, query)
        self._execute_native_query()
        self._execute_evadb_query()

def setUp(self):
    self.evadb = get_evadb_for_testing()
    self.evadb.catalog().reset()

@pytest.mark.notparallel
class CreateIndexTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evadb = get_evadb_for_testing()
        cls.evadb.catalog().reset()
        cls.img_path = create_sample_image()
        load_functions_for_testing(cls.evadb, mode='debug')
        params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
        query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
        execute_query_fetch_all(cls.evadb, query)

    @classmethod
    def tearDownClass(cls):
        query = 'USE test_data_source { DROP INDEX test_index }'
        execute_query_fetch_all(cls.evadb, query)
        query = 'USE test_data_source { DROP TABLE test_vector }'
        execute_query_fetch_all(cls.evadb, query)

    def test_native_engine_should_create_index(self):
        query = 'USE test_data_source {\n            CREATE TABLE test_vector (idx INTEGER, dummy INTEGER, embedding vector(27))\n        }'
        execute_query_fetch_all(self.evadb, query)
        vector_list = [[0.0 for _ in range(9)] + [1.0 for _ in range(9)] + [2.0 for _ in range(9)], [1.0 for _ in range(9)] + [2.0 for _ in range(9)] + [3.0 for _ in range(9)], [2.0 for _ in range(9)] + [3.0 for _ in range(9)] + [4.0 for _ in range(9)], [3.0 for _ in range(9)] + [4.0 for _ in range(9)] + [5.0 for _ in range(9)], [4.0 for _ in range(9)] + [5.0 for _ in range(9)] + [6.0 for _ in range(9)]]
        for idx, vector in enumerate(vector_list):
            query = f"USE test_data_source {{\n                INSERT INTO test_vector (idx, dummy, embedding) VALUES ({idx}, {idx}, '{vector}')\n            }}"
            execute_query_fetch_all(self.evadb, query)
        query = 'CREATE INDEX test_index\n            ON test_data_source.test_vector (embedding)\n            USING PGVECTOR'
        execute_query_fetch_all(self.evadb, query)
        query = "USE test_data_source {\n            SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'test_vector'\n        }"
        df = execute_query_fetch_all(self.evadb, query).frames
        self.assertEqual(len(df), 1)
        self.assertEqual(df['indexname'][0], 'test_index')
        self.assertEqual(df['indexdef'][0], 'CREATE INDEX test_index ON public.test_vector USING hnsw (embedding vector_l2_ops)')
        query = f"SELECT idx, embedding FROM test_data_source.test_vector\n            ORDER BY Similarity(DummyFeatureExtractor(Open('{self.img_path}')), embedding)\n            LIMIT 1"
        df = execute_query_fetch_all(self.evadb, f'EXPLAIN {query}').frames
        self.assertIn('VectorIndexScan', df[0][0])
        df = execute_query_fetch_all(self.evadb, query).frames
        self.assertEqual(df['test_vector.idx'][0], 0)
        self.assertNotIn('test_vector.dummy', df.columns)

@classmethod
def setUpClass(cls):
    cls.evadb = get_evadb_for_testing()
    cls.evadb.catalog().reset()
    cls.img_path = create_sample_image()
    load_functions_for_testing(cls.evadb, mode='debug')
    params = {'user': 'eva', 'password': 'password', 'host': 'localhost', 'port': '5432', 'database': 'evadb'}
    query = f'CREATE DATABASE test_data_source\n                    WITH ENGINE = "postgres",\n                    PARAMETERS = {params};'
    execute_query_fetch_all(cls.evadb, query)

def get_default_db_uri(evadb_dir: Path):
    return f'sqlite:///{evadb_dir.resolve()}/{DB_DEFAULT_NAME}'

def init_evadb_instance(db_dir: str, host: str=None, port: int=None, custom_db_uri: str=None):
    if db_dir is None:
        db_dir = EvaDB_DATABASE_DIR
    config_obj = bootstrap_environment(Path(db_dir), evadb_installation_dir=Path(EvaDB_INSTALLATION_DIR))
    catalog_uri = custom_db_uri or get_default_db_uri(Path(db_dir))
    bootstrap_configs(get_catalog_instance(catalog_uri), config_obj)
    return EvaDBDatabase(db_dir, catalog_uri, get_catalog_instance)

def get_default_db_uri(evadb_dir: Path):
    """
    Get the default database uri.

    Arguments:
        evadb_dir: path to evadb database directory
    """
    return f'sqlite:///{evadb_dir.resolve()}/{DB_DEFAULT_NAME}'

def bootstrap_environment(evadb_dir: Path, evadb_installation_dir: Path):
    """
    Populates necessary configuration for EvaDB to be able to run.

    Arguments:
        evadb_dir: path to evadb database directory
        evadb_installation_dir: path to evadb package
    """
    config_obj = BASE_EVADB_CONFIG
    config_default_dict = create_directories_and_get_default_config_values(Path(evadb_dir), Path(evadb_installation_dir))
    assert evadb_dir.exists(), f'{evadb_dir} does not exist'
    assert evadb_installation_dir.exists(), f'{evadb_installation_dir} does not exist'
    config_obj = merge_dict_of_dicts(config_default_dict, config_obj)
    mode = config_obj['mode']
    level = logging.WARN if mode == 'release' else logging.DEBUG
    evadb_logger.setLevel(level)
    evadb_logger.debug(f'Setting logging level to: {str(level)}')
    return config_obj

def create_directories_and_get_default_config_values(evadb_dir: Path, evadb_installation_dir: Path) -> Union[dict, str]:
    default_install_dir = evadb_installation_dir
    dataset_location = evadb_dir / EvaDB_DATASET_DIR
    index_dir = evadb_dir / INDEX_DIR
    cache_dir = evadb_dir / CACHE_DIR
    s3_dir = evadb_dir / S3_DOWNLOAD_DIR
    tmp_dir = evadb_dir / TMP_DIR
    function_dir = evadb_dir / FUNCTION_DIR
    model_dir = evadb_dir / MODEL_DIR
    if not evadb_dir.exists():
        evadb_dir.mkdir(parents=True, exist_ok=True)
    if not dataset_location.exists():
        dataset_location.mkdir(parents=True, exist_ok=True)
    if not index_dir.exists():
        index_dir.mkdir(parents=True, exist_ok=True)
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
    if not s3_dir.exists():
        s3_dir.mkdir(parents=True, exist_ok=True)
    if not tmp_dir.exists():
        tmp_dir.mkdir(parents=True, exist_ok=True)
    if not function_dir.exists():
        function_dir.mkdir(parents=True, exist_ok=True)
    if not model_dir.exists():
        model_dir.mkdir(parents=True, exist_ok=True)
    config_obj = {}
    config_obj['evadb_installation_dir'] = str(default_install_dir.resolve())
    config_obj['datasets_dir'] = str(dataset_location.resolve())
    config_obj['catalog_database_uri'] = get_default_db_uri(evadb_dir)
    config_obj['index_dir'] = str(index_dir.resolve())
    config_obj['cache_dir'] = str(cache_dir.resolve())
    config_obj['s3_download_dir'] = str(s3_dir.resolve())
    config_obj['tmp_dir'] = str(tmp_dir.resolve())
    config_obj['function_dir'] = str(function_dir.resolve())
    config_obj['model_dir'] = str(model_dir.resolve())
    return config_obj

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

def __init__(self, db: EvaDBDatabase, cost_model: CostModel, rules_manager: RulesManager=None):
    self._db = db
    self._task_stack = OptimizerTaskStack()
    self._memo = Memo()
    self._cost_model = cost_model
    is_ray_enabled = self.db.catalog().get_configuration_catalog_value('ray')
    self._rules_manager = rules_manager or RulesManager({'ray': is_ray_enabled})

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

def __init__(self, db: EvaDBDatabase, rules_manager: RulesManager=None, cost_model: CostModel=None) -> None:
    self.db = db
    is_ray_enabled = self.db.catalog().get_configuration_catalog_value('ray')
    self.rules_manager = rules_manager or RulesManager({'ray': is_ray_enabled})
    self.cost_model = cost_model or CostModel()

def optimize_cache_key_for_tuple_value_expression(context: 'OptimizerContext', tv_expr: TupleValueExpression):
    catalog = context.db.catalog()
    col_catalog_obj = tv_expr.col_object
    new_keys = []
    if isinstance(col_catalog_obj, ColumnCatalogEntry):
        table_obj = catalog.get_table_catalog_entry(col_catalog_obj.table_name)
        for col in get_table_primary_columns(table_obj):
            new_obj = catalog.get_column_catalog_entry(table_obj, col.name)
            new_keys.append(TupleValueExpression(name=col.name, table_alias=tv_expr.table_alias, col_object=new_obj, col_alias=f'{tv_expr.table_alias}.{col.name}'))
        return new_keys
    return [tv_expr]

def enable_cache_init(context: 'OptimizerContext', func_expr: FunctionExpression) -> FunctionExpressionCache:
    optimized_key = optimize_cache_key(context, func_expr)
    if optimized_key == func_expr.children:
        optimized_key = [None]
    catalog = context.db.catalog()
    name = func_expr.signature()
    cache_entry = catalog.get_function_cache_catalog_entry_by_name(name)
    if not cache_entry:
        cache_entry = catalog.insert_function_cache_catalog_entry(func_expr)
    cache = FunctionExpressionCache(key=tuple(optimized_key), store=DiskKVCache(cache_entry.cache_path))
    return cache

def get_expression_execution_cost(context: 'OptimizerContext', expr: AbstractExpression) -> float:
    """
    This function computes the estimated cost of executing the given abstract expression
    based on the statistics in the catalog. The function assumes that all the
    expression, except for the FunctionExpression, have a cost of zero.
    For FunctionExpression, it checks the catalog for relevant statistics; if none are
    available, it uses a default cost of DEFAULT_FUNCTION_EXPRESSION_COST.

    Args:
        context (OptimizerContext): the associated optimizer context
        expr (AbstractExpression): The AbstractExpression object whose cost
        needs to be computed.

    Returns:
        float: The estimated cost of executing the function expression.
    """
    total_cost = 0
    for child_expr in expr.find_all(FunctionExpression):
        cost_entry = context.db.catalog().get_function_cost_catalog_entry(child_expr.name)
        if cost_entry:
            total_cost += cost_entry.cost
        else:
            total_cost += DEFAULT_FUNCTION_EXPRESSION_COST
    return total_cost

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

def apply(self, before: LogicalCreateIndex, context: OptimizerContext):
    after = CreateIndexPlan(before.name, before.if_not_exists, before.table_ref, before.col_list, before.vector_store_type, before.project_expr_list, before.index_def)
    child = SeqScanPlan(None, before.project_expr_list, before.table_ref.alias)
    batch_mem_size = context.db.catalog().get_configuration_catalog_value('batch_mem_size')
    child.append_child(StoragePlan(before.table_ref.table.table_obj, before.table_ref, batch_mem_size=batch_mem_size))
    after.append_child(child)
    yield after

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

def apply(self, before: LogicalGet, context: OptimizerContext):
    after = SeqScanPlan(None, before.target_list, before.alias)
    batch_mem_size = context.db.catalog().get_configuration_catalog_value('batch_mem_size')
    after.append_child(StoragePlan(before.table_obj, before.video, predicate=before.predicate, sampling_rate=before.sampling_rate, sampling_type=before.sampling_type, chunk_params=before.chunk_params, batch_mem_size=batch_mem_size))
    yield after

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

def _is_media_valid(self, file_path: Path):
    file_path = Path(file_path)
    if validate_media(file_path, self.media_type):
        return True
    return False

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

def catalog(self) -> 'CatalogManager':
    """The object is intentionally generated on demand to prevent serialization issues. Having a SQLAlchemy object as a member variable can cause problems with multiprocessing. See get_catalog_instance()"""
    return self._db.catalog() if self._db else None

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

def _populate_gpu_ids(self) -> List:
    if not is_gpu_available():
        return []
    gpus = self._populate_gpu_from_config()
    if len(gpus) == 0:
        gpus = self._populate_gpu_from_env()
    return gpus

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

def handle_vector_store_params(vector_store_type: VectorStoreType, index_path: str, catalog) -> dict:
    """Handle vector store parameters based on the vector store type and index path.

    Args:
        vector_store_type (VectorStoreType): The type of vector store.
        index_path (str): The path to store the index.

    Returns:
        dict: Dictionary containing the appropriate vector store parameters.


    Raises:
        ValueError: If the vector store type in the node is not supported.
    """
    if vector_store_type == VectorStoreType.FAISS:
        return {'index_path': index_path}
    elif vector_store_type == VectorStoreType.QDRANT:
        return {'index_db': str(Path(index_path).parent)}
    elif vector_store_type == VectorStoreType.CHROMADB:
        return {'index_path': str(Path(index_path).parent)}
    elif vector_store_type == VectorStoreType.PINECONE:
        return {'PINECONE_API_KEY': catalog().get_configuration_catalog_value('PINECONE_API_KEY'), 'PINECONE_ENV': catalog().get_configuration_catalog_value('PINECONE_ENV')}
    elif vector_store_type == VectorStoreType.WEAVIATE:
        return {'WEAVIATE_API_KEY': catalog().get_configuration_catalog_value('WEAVIATE_API_KEY'), 'WEAVIATE_API_URL': catalog().get_configuration_catalog_value('WEAVIATE_API_URL')}
    elif vector_store_type == VectorStoreType.MILVUS:
        return {'MILVUS_URI': catalog().get_configuration_catalog_value('MILVUS_URI'), 'MILVUS_USER': catalog().get_configuration_catalog_value('MILVUS_USER'), 'MILVUS_PASSWORD': catalog().get_configuration_catalog_value('MILVUS_PASSWORD'), 'MILVUS_DB_NAME': catalog().get_configuration_catalog_value('MILVUS_DB_NAME'), 'MILVUS_TOKEN': catalog().get_configuration_catalog_value('MILVUS_TOKEN')}
    else:
        raise ValueError('Unsupported vector store type: {}'.format(vector_store_type))

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

def _get_evadb_index_save_path(self) -> Path:
    index_dir = Path(self.db.catalog().get_configuration_catalog_value('index_dir'))
    if not index_dir.exists():
        index_dir.mkdir(parents=True, exist_ok=True)
    return str(index_dir / Path('{}_{}.index'.format(self.vector_store_type, self.name)))

def download_from_s3(s3_uri, save_dir):
    """
    Downloads a file from s3 to the local file system
    """
    try_to_import_moto()
    import boto3
    s3_client = boto3.client('s3')
    s3_uri = s3_uri.as_posix()
    bucket_name, regex_key = parse_s3_uri(s3_uri)
    s3_bucket = boto3.resource('s3').Bucket(bucket_name)
    file_save_paths = []
    for obj in s3_bucket.objects.all():
        if re.search(re.sub('\\*', '.*', regex_key), obj.key):
            key = obj.key.replace('/', '_')
            save_path = Path(save_dir) / key
            s3_client.download_file(bucket_name, key, save_path)
            file_save_paths.append(save_path)
    return file_save_paths

def generate_file_path(dataset_location: str, name: str='') -> Path:
    """Generates a arbitrary file_path(md5 hash) based on the a random salt
    and name

    Arguments:
        dataset_location(str): parent directory where a file needs to be created
        name (str): Input file_name.

    Returns:
        Path: pathlib.Path object

    """
    dataset_location = Path(dataset_location)
    dataset_location.mkdir(parents=True, exist_ok=True)
    salt = uuid.uuid4().hex
    file_name = hashlib.md5(salt.encode() + name.encode()).hexdigest()
    path = dataset_location / file_name
    return path.resolve()

def get_str_hash(s: str) -> str:
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def get_file_checksum(fname: str) -> str:
    """Compute checksum of the file contents

    Args:
        fname (str): file path

    Returns:
        str: hash string representing the checksum of the file content
    """
    hash_md5 = hashlib.md5()
    with open(fname, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def remove_directory_contents(dir_path):
    if os.path.exists(dir_path):
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.warning(f'Failed to delete {file_path}. Reason: {str(e)}')

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

def drop_database_catalog_entry(self, database_entry: DatabaseCatalogEntry) -> bool:
    """
        This method deletes the database from  catalog.

        Arguments:
           database_entry: database catalog entry to remove

        Returns:
           True if successfully deleted else False
        """
    return self._db_catalog_service.delete_entry(database_entry)

def drop_job_catalog_entry(self, job_entry: JobCatalogEntry) -> bool:
    """
        This method deletes the job from  catalog.

        Arguments:
           job_entry: job catalog entry to remove

        Returns:
           True if successfully deleted else False
        """
    return self._job_catalog_service.delete_entry(job_entry)

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

def insert_function_cache_catalog_entry(self, func_expr: FunctionExpression):
    cache_dir = self.get_configuration_catalog_value('cache_dir')
    entry = construct_function_cache_catalog_entry(func_expr, cache_dir=cache_dir)
    return self._function_cache_service.insert_entry(entry)

def drop_function_cache_catalog_entry(self, entry: FunctionCacheCatalogEntry) -> bool:
    if entry:
        shutil.rmtree(entry.cache_path)
    return self._function_cache_service.delete_entry(entry)

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

def bootstrap_configs(catalog, configs: dict):
    """
    load all the configuration values into the catalog table configuration_catalog
    """
    for key, value in configs.items():
        catalog.upsert_configuration_catalog_entry(key, value)

def get_configuration_value(key: str):
    catalog = get_catalog_instance()
    return catalog.get_configuration_catalog_value(key)

@dataclass(unsafe_hash=True)
class FunctionCatalogEntry:
    """Dataclass representing an entry in the `FunctionCatalog`.
    This is done to ensure we don't expose the sqlalchemy dependencies beyond catalog service. Further, sqlalchemy does not allow sharing of objects across threads.
    """
    name: str
    impl_file_path: str
    type: str
    checksum: str
    row_id: int = None
    args: List[FunctionIOCatalogEntry] = field(compare=False, default_factory=list)
    outputs: List[FunctionIOCatalogEntry] = field(compare=False, default_factory=list)
    metadata: List[FunctionMetadataCatalogEntry] = field(compare=False, default_factory=list)
    dep_caches: List[FunctionIOCatalogEntry] = field(compare=False, default_factory=list)

    def display_format(self):

        def _to_str(col):
            col_display = col.display_format()
            return f'{col_display['name']} {col_display['data_type']}'
        return {'name': self.name, 'inputs': [_to_str(col) for col in self.args], 'outputs': [_to_str(col) for col in self.outputs], 'type': self.type, 'impl': self.impl_file_path, 'metadata': self.metadata}

def _to_str(col):
    col_display = col.display_format()
    return f'{col_display['name']} {col_display['data_type']}'

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

def create(self, vectorizer: str='text2vec-openai', properties: list=None, module_config: dict=None):
    properties = properties or []
    module_config = module_config or {}
    collection_obj = {'class': self._collection_name, 'properties': properties, 'vectorizer': vectorizer, 'moduleConfig': module_config}
    if self._client.schema.exists(self._collection_name):
        self._client.schema.delete_class(self._collection_name)
    self._client.schema.create_class(collection_obj)

def delete(self) -> None:
    self._client.schema.delete_class(self._collection_name)

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

def delete(self):
    index_path = Path(self._index_path)
    if index_path.exists():
        index_path.unlink()

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

def __init__(self, file_url: str, batch_mem_size: int=30000000):
    if not Path(file_url).exists():
        raise DatasetFileNotFoundError()
    if isinstance(file_url, Path):
        file_url = str(file_url)
    self.file_url = file_url
    self.batch_mem_size = batch_mem_size

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

def download_weights(self):
    try_to_import_torch()
    import torch
    if not os.path.exists(self.asl_weights_path):
        torch.hub.download_url_to_file(self.asl_weights_url, self.asl_weights_path, hash_prefix=None, progress=True)

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

def _forward(row: pd.Series) -> np.ndarray:
    data = row
    embedded_list = self.model.encode(data)
    return embedded_list

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

def _download_weights(self, weights_url, weights_path):
    import torch
    if not os.path.exists(weights_path):
        torch.hub.download_url_to_file(weights_url, weights_path, hash_prefix=None, progress=True)

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

def setup(self):
    try_to_import_faiss()
    pass

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

def _get_metadata_table(self, table: TableCatalogEntry):
    return self.db.catalog().get_multimedia_metadata_table_catalog_entry(table)

def _create_metadata_table(self, table: TableCatalogEntry):
    return self.db.catalog().create_and_insert_multimedia_metadata_table_catalog_entry(table)

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

def validate_directory(directory_list):
    code_validation = True
    for dir in directory_list:
        for dir_path, _, files in os.walk(dir):
            for each_file in files:
                file_path = dir_path + os.path.sep + each_file
                if not validate_file(file_path):
                    code_validation = False
    return code_validation

def format_dir(dir_path, add_header, strip_header, format_code):
    for subdir, dir, files in os.walk(dir_path):
        for file in files:
            if file in IGNORE_FILES:
                continue
            file_path = subdir + os.path.sep + file
            if file_path.endswith('.py'):
                format_file(file_path, add_header, strip_header, format_code)

@background
def check_file(file):
    valid = False
    file_path = str(Path(file).absolute())
    for source_dir in DEFAULT_DIRS:
        source_path = str(Path(source_dir).resolve())
        if file_path.startswith(source_path):
            valid = True
    if valid:
        if not check_header(file):
            format_file(file, False, True, False)
            format_file(file, True, False, False)
        format_file(file, False, False, True)

def cleanup():
    """Removes any temporary file / directory created by EvaDB."""
    if os.path.exists('evadb_data'):
        shutil.rmtree('evadb_data')

def cleanup():
    """Removes any temporary file / directory created by EvaDB."""
    if os.path.exists('evadb_data'):
        shutil.rmtree('evadb_data')
    if os.path.exists(QUESTION_PATH):
        os.remove(QUESTION_PATH)
    if os.path.exists(SCRIPT_PATH):
        os.remove(SCRIPT_PATH)

