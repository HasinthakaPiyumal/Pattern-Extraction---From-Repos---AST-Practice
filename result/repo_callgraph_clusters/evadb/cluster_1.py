# Cluster 1

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

def create_dummy_csv_batches(target_columns=None):
    if target_columns:
        df = pd.read_csv(os.path.join(get_tmp_dir(), 'dummy.csv'), converters={'bbox': convert_bbox}, usecols=target_columns)
    else:
        df = pd.read_csv(os.path.join(get_tmp_dir(), 'dummy.csv'), converters={'bbox': convert_bbox})
    yield Batch(df)

def create_table(db, table_name, num_rows, num_columns):
    columns = ''.join(('a{} INTEGER, '.format(i) for i in range(num_columns - 1)))
    columns += 'a{} INTEGER'.format(num_columns - 1)
    create_table_query = 'CREATE TABLE IF NOT EXISTS {} ( {} );'.format(table_name, columns)
    execute_query_fetch_all(db, create_table_query)
    columns = ['a{}'.format(i) for i in range(num_columns)]
    df, csv_file_path = create_csv(num_rows, columns)
    load_query = f"LOAD CSV '{csv_file_path}' INTO {table_name};"
    execute_query_fetch_all(db, load_query)
    df.columns = [f'{table_name}.{col}' for col in df.columns]
    return df

@pytest.mark.torchtest
@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
@pytest.mark.notparallel
def test_should_run_benchmark_pytorch_and_yolo(benchmark, setup_pytorch_tests):
    select_query = 'SELECT Yolo(data) FROM MyVideo\n                    WHERE id < 5;'
    actual_batch = benchmark(execute_query_fetch_all, setup_pytorch_tests, select_query)
    assert len(actual_batch) == 5

@pytest.mark.torchtest
@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
@pytest.mark.notparallel
def test_should_run_benchmark_pytorch_and_facenet(benchmark, setup_pytorch_tests):
    create_udf_query = "CREATE UDF IF NOT EXISTS FaceDetector\n                INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                OUTPUT (bboxes NDARRAY FLOAT32(ANYDIM, 4),\n                        scores NDARRAY FLOAT32(ANYDIM))\n                TYPE  FaceDetection\n                IMPL  'evadb/udfs/face_detector.py';\n    "
    execute_query_fetch_all(setup_pytorch_tests, create_udf_query)
    select_query = 'SELECT FaceDetector(data) FROM MyVideo\n                    WHERE id < 5;'
    actual_batch = benchmark(execute_query_fetch_all, setup_pytorch_tests, select_query)
    assert len(actual_batch) == 5

@pytest.mark.torchtest
@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
@pytest.mark.notparallel
def test_should_run_benchmark_pytorch_and_resnet50(benchmark, setup_pytorch_tests):
    create_udf_query = "CREATE UDF IF NOT EXISTS FeatureExtractor\n                INPUT  (frame NDARRAY UINT8(3, ANYDIM, ANYDIM))\n                OUTPUT (features NDARRAY FLOAT32(ANYDIM))\n                TYPE  Classification\n                IMPL  'evadb/udfs/feature_extractor.py';\n    "
    execute_query_fetch_all(setup_pytorch_tests, create_udf_query)
    select_query = 'SELECT FeatureExtractor(data) FROM MyVideo\n                    WHERE id < 5;'
    actual_batch = benchmark(execute_query_fetch_all, setup_pytorch_tests, select_query)
    assert len(actual_batch) == 5
    res = actual_batch.frames
    assert res['featureextractor.features'][0].shape == (1, 2048)

@pytest.mark.torchtest
@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
@pytest.mark.notparallel
def test_lateral_join(benchmark, setup_pytorch_tests):
    select_query = 'SELECT id, a FROM MyVideo JOIN LATERAL\n                    Yolo(data) AS T(a,b,c) WHERE id < 5;'
    actual_batch = benchmark(execute_query_fetch_all, setup_pytorch_tests, select_query)
    assert len(actual_batch) == 5
    assert list(actual_batch.columns) == ['myvideo.id', 'T.a']

@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
def test_automatic_speech_recognition(benchmark, setup_pytorch_tests):
    udf_name = 'SpeechRecognizer'
    create_udf = f"CREATE UDF {udf_name} TYPE HuggingFace TASK 'automatic-speech-recognition' MODEL 'openai/whisper-base';"
    execute_query_fetch_all(setup_pytorch_tests, create_udf)
    select_query = f'SELECT {udf_name}(audio) FROM VIDEOS;'
    output = benchmark(execute_query_fetch_all, setup_pytorch_tests, select_query)
    assert output.frames.shape == (1, 1)
    assert output.frames.iloc[0][0].count('touchdown') == 2
    drop_udf_query = f'DROP UDF {udf_name};'
    execute_query_fetch_all(setup_pytorch_tests, drop_udf_query)

@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
def test_summarization_from_video(benchmark, setup_pytorch_tests):
    asr_udf = 'SpeechRecognizer'
    create_udf = f"CREATE UDF {asr_udf} TYPE HuggingFace TASK 'automatic-speech-recognition' MODEL 'openai/whisper-base';"
    execute_query_fetch_all(setup_pytorch_tests, create_udf)
    summary_udf = 'Summarizer'
    create_udf = f"CREATE UDF {summary_udf} TYPE HuggingFace TASK 'summarization' MODEL 'philschmid/bart-large-cnn-samsum' MIN_LENGTH 10 MAX_LENGTH 100;"
    execute_query_fetch_all(setup_pytorch_tests, create_udf)
    select_query = f'SELECT {summary_udf}({asr_udf}(audio)) FROM VIDEOS;'
    output = benchmark(execute_query_fetch_all, setup_pytorch_tests, select_query)
    assert output.frames.shape == (1, 1)
    assert output.frames.iloc[0][0] == 'Jalen Hurts has scored his second rushing touchdown of the game.'
    drop_udf_query = f'DROP UDF {asr_udf};'
    execute_query_fetch_all(setup_pytorch_tests, drop_udf_query)
    drop_udf_query = f'DROP UDF {summary_udf};'
    execute_query_fetch_all(setup_pytorch_tests, drop_udf_query)

def _execute_query_list(query_list):
    for query in query_list:
        execute_query_fetch_all(setup_pytorch_tests, query)

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

def test_should_fail_to_load_missing_video(self):
    path = f'{EvaDB_ROOT_DIR}/data/sample_videos/missing.mp4'
    query = f'LOAD VIDEO "{path}" INTO MyVideos;'
    with self.assertRaises(ExecutorError) as exc_info:
        execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
    self.assertIn('Load VIDEO failed', str(exc_info.exception))

def test_should_fail_to_load_invalid_files_as_video(self):
    path = f'{EvaDB_ROOT_DIR}/data/README.md'
    query = f'LOAD VIDEO "{path}" INTO MyVideos;'
    with self.assertRaises(Exception):
        execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
    with self.assertRaises(BinderError):
        execute_query_fetch_all(self.evadb, 'SELECT name FROM MyVideos', do_not_print_exceptions=True)

def test_should_fail_to_load_missing_image(self):
    path = f'{EvaDB_ROOT_DIR}/data/sample_images/missing.jpg'
    query = f'LOAD IMAGE "{path}" INTO MyImages;'
    with self.assertRaises(ExecutorError) as exc_info:
        execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
    self.assertIn('Load IMAGE failed', str(exc_info.exception))

def test_should_fail_to_load_invalid_files_as_image(self):
    path = f'{EvaDB_ROOT_DIR}/data/README.md'
    query = f'LOAD IMAGE "{path}" INTO MyImages;'
    with self.assertRaises(Exception):
        execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)
    with self.assertRaises(BinderError):
        execute_query_fetch_all(self.evadb, 'SELECT name FROM MyImages;', do_not_print_exceptions=True)

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

def test_load_pdfs(self):
    execute_query_fetch_all(self.evadb, f"LOAD DOCUMENT '{EvaDB_ROOT_DIR}/data/documents/*.pdf' INTO pdfs;")
    result = execute_query_fetch_all(self.evadb, 'SELECT * from pdfs;')
    self.assertEqual(len(result.columns), 4)
    self.assertEqual(len(result), 26)

def test_load_query_incorrect_fileFormat(self):
    with self.assertRaises(ExecutorError):
        execute_query_fetch_all(self.evadb, f"LOAD document '{EvaDB_ROOT_DIR}/data/documents/*.pdf' INTO pdfs;")

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

def setUp(self):
    execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {self.job_name_1};')
    execute_query_fetch_all(self.evadb, f'DROP JOB IF EXISTS {self.job_name_2};')

@classmethod
def tearDownClass(cls):
    shutdown_ray()
    execute_query_fetch_all(cls.evadb, f'DROP JOB IF EXISTS {cls.job_name_1};')
    execute_query_fetch_all(cls.evadb, f'DROP JOB IF EXISTS {cls.job_name_2};')

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
def tearDownClass(cls):
    shutdown_ray()
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

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

def tearDown(self):
    shutdown_ray()
    file_remove('dummy.jpg')
    drop_table_query = 'DROP TABLE testOpenTable;'
    execute_query_fetch_all(self.evadb, drop_table_query)

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

def test_select_and_groupby_with_paragraphs(self):
    segment_size = 10
    select_query = "SELECT SEGMENT(data) FROM MyPDFs GROUP BY '{}paragraphs';".format(segment_size)
    output = execute_query_fetch_all(self.evadb, select_query)
    self.assertEqual(len(output.frames), 3)

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

@windows_skip_marker
def test_timer(self):
    sleep_time = Timer()
    with sleep_time:
        time.sleep(5)
    self.assertTrue(sleep_time.total_elapsed_time < 5.2)
    self.assertTrue(sleep_time.total_elapsed_time > 4.9)

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

def _load_hf_model(self):
    function_name = 'HFObjectDetector'
    create_function_query = f"CREATE FUNCTION {function_name}\n            TYPE HuggingFace\n            TASK 'object-detection'\n            MODEL 'facebook/detr-resnet-50';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)

def tearDown(self):
    shutdown_ray()
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS DETRAC;')
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS fruitTable;')

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

def tearDown(self):
    shutdown_ray()
    file_remove('dummy.avi')
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideo;')

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

def tearDown(self):
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDFs;')

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

def tearDown(self) -> None:
    shutdown_ray()

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

def test_check_unnest_with_predicate_on_yolo(self):
    query = "SELECT id, Yolo.label, Yolo.bbox, Yolo.score\n                  FROM MyVideo\n                  JOIN LATERAL UNNEST(Yolo(data)) AS Yolo(label, bbox, score)\n                  WHERE Yolo.label = 'car' AND id < 2;"
    actual_batch = execute_query_fetch_all(self.evadb, query)
    self.assertTrue(len(actual_batch) > 2)

@pytest.mark.notparallel
class SaliencyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_dir = suffix_pytest_xdist_worker_id_to_dir(EvaDB_DATABASE_DIR)
        cls.conn = connect(cls.db_dir)
        cls.evadb = cls.conn._evadb

    @classmethod
    def tearDownClass(cls):
        shutdown_ray()
        execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS SALIENCY;')

    @unittest.skip('Not supported in current version')
    def test_saliency(self):
        Saliency1 = f'{EvaDB_ROOT_DIR}/data/saliency/test1.jpeg'
        create_function_query = f"LOAD IMAGE '{Saliency1}' INTO SALIENCY;"
        execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS SALIENCY;')
        execute_query_fetch_all(self.evadb, create_function_query)
        execute_query_fetch_all(self.evadb, 'DROP FUNCTION IF EXISTS SaliencyFeatureExtractor')
        create_function_query = f"CREATE FUNCTION IF NOT EXISTS SaliencyFeatureExtractor\n                    IMPL  '{EvaDB_ROOT_DIR}/evadb/functions/saliency_feature_extractor.py';\n        "
        execute_query_fetch_all(self.evadb, create_function_query)
        select_query_saliency = 'SELECT data, SaliencyFeatureExtractor(data)\n                  FROM SALIENCY\n        '
        actual_batch_saliency = execute_query_fetch_all(self.evadb, select_query_saliency)
        self.assertEqual(len(actual_batch_saliency.columns), 2)

@classmethod
def tearDownClass(cls):
    shutdown_ray()
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS SALIENCY;')

@unittest.skip('Not supported in current version')
def test_saliency(self):
    Saliency1 = f'{EvaDB_ROOT_DIR}/data/saliency/test1.jpeg'
    create_function_query = f"LOAD IMAGE '{Saliency1}' INTO SALIENCY;"
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS SALIENCY;')
    execute_query_fetch_all(self.evadb, create_function_query)
    execute_query_fetch_all(self.evadb, 'DROP FUNCTION IF EXISTS SaliencyFeatureExtractor')
    create_function_query = f"CREATE FUNCTION IF NOT EXISTS SaliencyFeatureExtractor\n                    IMPL  '{EvaDB_ROOT_DIR}/evadb/functions/saliency_feature_extractor.py';\n        "
    execute_query_fetch_all(self.evadb, create_function_query)
    select_query_saliency = 'SELECT data, SaliencyFeatureExtractor(data)\n                  FROM SALIENCY\n        '
    actual_batch_saliency = execute_query_fetch_all(self.evadb, select_query_saliency)
    self.assertEqual(len(actual_batch_saliency.columns), 2)

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
def tearDownClass(cls):
    shutdown_ray()
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')
    file_remove('dummy.avi')

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
def tearDownClass(cls):
    file_remove('dummy.avi')
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

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

def tearDown(self):
    shutdown_ray()
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS mnist_video;')
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS meme_images;')
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS dummy_table;')

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

def tearDown(self):
    shutdown_ray()
    file_remove('dummy.avi')
    file_remove('dummy.csv')
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyVideos;')

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

def test_should_create_job_with_if_not_exists(self):
    if_not_exists = 'IF NOT EXISTS'
    queries = ["CREATE OR REPLACE FUNCTION HomeSalesForecast FROM\n                ( SELECT * FROM postgres_data.home_sales )\n                TYPE Forecasting\n                PREDICT 'price';", 'Select HomeSalesForecast(10);']
    query = "CREATE JOB {} {} AS {{\n                    {}\n                }}\n                START '2023-04-01'\n                END '2023-05-01'\n                EVERY 2 week;\n            "
    execute_query_fetch_all(self.evadb, query.format(if_not_exists, self.job_name, ''.join(queries)))
    with self.assertRaises(ExecutorError):
        execute_query_fetch_all(self.evadb, query.format('', self.job_name, ''.join(queries)))
    execute_query_fetch_all(self.evadb, query.format(if_not_exists, self.job_name, ''.join(queries)))

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
def tearDownClass(cls):
    shutdown_ray()
    file_remove('dummy.avi')
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table1;')
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table2;')
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS table3;')
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

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

def tearDown(self):
    file_remove('dummy.avi')

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
def tearDownClass(cls):
    shutdown_ray()

def test_use_should_raise_executor_error(self):
    query = 'USE not_available_ds {\n            SELECT * FROM table\n        }'
    with self.assertRaises(ExecutorError):
        execute_query_fetch_all(self.evadb, query)

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

def tearDown(self):
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS MyPDFs;')

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

def test_should_return_correct_class_for_path(self):
    vl = load_function_class_from_file('evadb/readers/decord_reader.py', 'DecordReader')
    assert vl.__qualname__ == DecordReader.__qualname__

def test_should_return_correct_class_for_path_without_classname(self):
    vl = load_function_class_from_file('evadb/readers/decord_reader.py')
    assert vl.__qualname__ == DecordReader.__qualname__

def test_should_raise_on_missing_file(self):
    with self.assertRaises(FileNotFoundError):
        load_function_class_from_file('evadb/readers/opencv_reader_abdfdsfds.py')

def test_should_raise_if_class_does_not_exists(self):
    with self.assertRaises(ImportError):
        load_function_class_from_file('evadb/utils/s3_utils.py')

def test_should_raise_if_multiple_classes_exist_and_no_class_mentioned(self):
    with self.assertRaises(ImportError):
        load_function_class_from_file('evadb/utils/generic_utils.py')

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

def tearDown(self) -> None:
    shutdown_ray()

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

def tearDown(self) -> None:
    shutdown_ray()

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

def tearDown(self) -> None:
    shutdown_ray()

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

def tearDown(self) -> None:
    execute_query_fetch_all(self.evadb, 'DROP TABLE IF EXISTS ImageGen;')

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

def tearDown(self):
    shutdown_ray()
    file_remove('dummy.avi')

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
def tearDownClass(cls):
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyVideo;')

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
def tearDownClass(cls):
    execute_query_fetch_all(cls.evadb, 'DROP TABLE IF EXISTS MyCSV;')

class ColumnTypeTests(unittest.TestCase):

    def test_ndarray_type_to_numpy_type(self):
        expected_type = [np.int8, np.uint8, np.int16, np.int32, np.int64, np.unicode_, np.bool_, np.float32, np.float64, Decimal, np.str_, np.datetime64]
        for ndarray_type, np_type in zip(NdArrayType, expected_type):
            self.assertEqual(NdArrayType.to_numpy_type(ndarray_type), np_type)

    def test_raise_exception_uknown_ndarray_type(self):
        self.assertRaises(ValueError, NdArrayType.to_numpy_type, ColumnType.TEXT)

def test_raise_exception_uknown_ndarray_type(self):
    self.assertRaises(ValueError, NdArrayType.to_numpy_type, ColumnType.TEXT)

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

def tearDown(self):
    file_remove('dummy.csv')

def test_should_return_one_batch(self):
    column_list = [TupleValueExpression(name='id', table_alias='dummy'), TupleValueExpression(name='frame_id', table_alias='dummy'), TupleValueExpression(name='video_id', table_alias='dummy')]
    csv_loader = CSVReader(file_url=self.csv_file_path, column_list=column_list)
    batches = list(csv_loader.read())
    expected = list(create_dummy_csv_batches(target_columns=['id', 'frame_id', 'video_id']))
    self.assertEqual(batches, expected)

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

@classmethod
def tearDownClass(self):
    file_remove('dummy.avi')

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

def test_should_fail_for_list(self):
    frames = [{'id': 0, 'data': [1, 2]}, {'id': 1, 'data': [1, 2]}]
    self.assertRaises(ValueError, Batch, frames)

def test_should_fail_for_dict(self):
    frames = {'id': 0, 'data': [1, 2]}
    self.assertRaises(ValueError, Batch, frames)

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

@mock.patch('pathlib.Path.mkdir')
def test_should_raise_file_exist_error(self, m):
    m.side_effect = FileExistsError
    with self.assertRaises(FileExistsError):
        self.video_engine.create(self.table, if_not_exists=False)
    self.video_engine.create(self.table, if_not_exists=True)

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

def __str__(self):
    return 'DeletePlan(table={},             where_clause={})'.format(self.table_ref, self._where_clause)

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

def __str__(self):
    plan = 'UnnestApplyAndMergePlan' if self._do_unnest else 'ApplyAndMergePlan'
    return '{}(func_expr={})'.format(plan, self._func_expr)

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

def __str__(self):
    return 'RenamePlan(old_table={},             new_name={})'.format(self._old_table, self._new_name)

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

def __str__(self):
    return 'PredicatePlan(predicate={})'.format(self.predicate)

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

def __str__(self):
    return 'HashJoinBuildPlan(join_type={},             build_keys={})'.format(self.join_type, self.build_keys)

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

def __str__(self):
    return 'VectorIndexScan(index_name={}, vector_store_type={}, limit_count={}, search_query_expr={})'.format(self._index.name, self._index.vector_store_type, self._limit_count, self._search_query_expr)

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

def __str__(self):
    return 'LateralJoinPlan(join_project={},             join_predicate={})'.format(self.join_project, self.join_predicate)

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

def __str__(self):
    return 'NestedLoopJoinPlan(join_type={},             predicate={})'.format(self.join_type, self.join_predicate)

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

def __str__(self):
    return 'OrderByPlan(orderby_list={})'.format(self._orderby_list)

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

def __str__(self):
    return 'StoragePlan(video={},             table_ref={},            batch_mem_size={},             skip_frames={},             offset={},             limit={},             total_shards={},             curr_shard={},             predicate={},             sampling_rate={},             sampling_type={})'.format(self._table, self._table_ref, self._batch_mem_size, self._skip_frames, self._offset, self._limit, self._total_shards, self._curr_shard, self._predicate, self._sampling_rate, self._sampling_type)

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

def __str__(self):
    return 'SeqScanPlan(predicate={},             columns={},             alias={})'.format(self._predicate, self._columns, self.alias)

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

def __str__(self):
    plan = 'UnnestFunctionScanPlan' if self._do_unnest else 'FunctionScanPlan'
    return '{}(func_expr={})'.format(plan, self._func_expr)

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

def __str__(self):
    return 'InsertPlan(table={},             column_list={},             value_list={})'.format(self.table_ref, self.column_list, self.value_list)

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

def __str__(self):
    return 'LimitPlan(limit_count={})'.format(self._limit_count)

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

def __str__(self):
    return 'CreateFromSelectPlan(table_info={},             column_lists={},             if_not_exists={})'.format(self._table_info, self._column_list, self._if_not_exists)

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

def __str__(self):
    return 'SamplePlan(sample_freq={})'.format(self._sample_freq)

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

def __str__(self):
    function_expr = None
    for project_expr in self._project_expr_list:
        if isinstance(project_expr, FunctionExpression):
            function_expr = project_expr
    return 'CreateIndexPlan(name={},             table_ref={},             col_list={},             vector_store_type={},             {})'.format(self._name, self._table_ref, tuple(self._col_list), self._vector_store_type, '' if function_expr is None else 'function={}'.format(function_expr))

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

def __str__(self):
    return 'CreateFunctionPlan(name={},             or_replace={},             if_not_exists={},             inputs={},             outputs={},             impl_file_path={},             function_type={},             metadata={})'.format(self._name, self._or_replace, self._if_not_exists, self._inputs, self._outputs, self._impl_path, self._function_type, self._metadata)

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

def __str__(self):
    return 'DropObjectPlan(object_type={}, name={}, if_exists={})'.format(self._object_type, self._name, self._if_exists)

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

def __str__(self):
    return 'LoadDataPlan(table_id={}, file_path={},             column_list={},             file_options={},             batch_mem_size={})'.format(self.table_info, self.file_path, self.column_list, self.file_options, self.batch_mem_size)

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

def __str__(self):
    return 'GroupByPlan(groupby_clause={})'.format(self._groupby_clause)

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

def __str__(self):
    return 'HashJoinProbePlan(join_type={},             probe_keys={},             join_predicate={},             join_project={})'.format(self.join_type, self.probe_keys, self.join_predicate, self.join_project)

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

def __str__(self):
    return 'CreatePlan(table_ref={},             column_list={},             if_not_exists={})'.format(self._table_info, self._column_list, self._if_not_exists)

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

def __str__(self):
    return 'NativePlan(database_name={}, query_string={})'.format(self._database_name, self._query_string)

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

def __str__(self):
    return 'ProjectPlan(target_list={})'.format(self.target_list)

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

def __str__(self):
    return 'LogicalLoadData(table: {}, path: {},                 column_list: {},                 file_options: {})'.format(self.table_info, self.path, self.column_list, self.file_options)

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

def _rollback_load(self, storage_engine: AbstractStorageEngine, table_obj: TableCatalogEntry, do_create: bool):
    if do_create:
        storage_engine.drop(table_obj)

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

def _populate_gpu_from_config(self) -> List:
    available_gpus = [i for i in range(get_gpu_count())]
    return list(set(available_gpus) & set(self._user_provided_gpu_conf))

def _populate_gpu_from_env(self) -> List:
    gpu_conf = map(lambda x: x.strip(), os.environ.get('CUDA_VISIBLE_DEVICES', '').strip().split(','))
    gpu_conf = list(filter(lambda x: x, gpu_conf))
    gpu_conf = [int(gpu_id) for gpu_id in gpu_conf]
    available_gpus = [i for i in range(get_gpu_count())]
    return list(set(available_gpus) & set(gpu_conf))

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

def log_elapsed_time(self, context: str):
    logger.info('{:s}: {:0.4f} sec'.format(context, self.total_elapsed_time))

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

def evaluate(self, batch: Batch, *args, **kwargs):
    return batch.project([self.col_alias])

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

def _bootstrap_catalog(self):
    """Bootstraps catalog.
        This method runs all tasks required for using catalog. Currently,
        it includes only one task ie. initializing database. It creates the
        catalog database and tables if they do not exist.
        """
    logger.info('Bootstrapping catalog')
    init_db(self._sql_config.engine)

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

@dataclass(unsafe_hash=True)
class FunctionIOCatalogEntry:
    """Class decouples the `FunctionIOCatalog` from the sqlalchemy."""
    name: str
    type: ColumnType
    is_nullable: bool = False
    array_type: NdArrayType = None
    array_dimensions: Tuple[int] = None
    is_input: bool = True
    function_id: int = None
    function_name: str = None
    row_id: int = None

    def display_format(self):
        data_type = self.type.name
        if self.type == ColumnType.NDARRAY:
            data_type = '{} {} {}'.format(data_type, self.array_type.name, self.array_dimensions)
        return {'name': self.name, 'data_type': data_type}

def display_format(self):
    data_type = self.type.name
    if self.type == ColumnType.NDARRAY:
        data_type = '{} {} {}'.format(data_type, self.array_type.name, self.array_dimensions)
    return {'name': self.name, 'data_type': data_type}

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

def __str__(self) -> str:
    print_str = 'CREATE TABLE {} ({}) \n'.format(self._table_info, self._if_not_exists)
    if self._query is not None:
        print_str = 'CREATE TABLE {} AS {}\n'.format(self._table_info, self._query)
    for column in self.column_list:
        print_str += str(column) + '\n'
    return print_str

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

def __str__(self) -> str:
    if self.predicate is not None:
        return '{} {} {} ON {}'.format(self.left, self.join_type, self.right, self.predicate)
    else:
        return '{} {} {}'.format(self.left, self.join_type, self.right)

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

def __str__(self) -> str:
    print_str = 'RENAME TABLE {} TO {} '.format(self._old_table_ref, self._new_table_name)
    return print_str

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

def __str__(self) -> str:
    print_str = 'EXPLAIN {}'.format(str(self._explainable_stmt))
    return print_str

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

@retry(tries=6, delay=20)
def completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)

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

@property
def labels(self):
    return list([str(num) for num in range(10)])

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

@property
def columns(self):
    return list(self._frames.columns)

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

def unnest(self, cols: List[str]=None) -> None:
    """
        Unnest columns and drop columns with no data
        """
    if cols is None:
        cols = list(self.columns)
    self._frames = self._frames.explode(cols)
    self._frames.dropna(inplace=True)

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

