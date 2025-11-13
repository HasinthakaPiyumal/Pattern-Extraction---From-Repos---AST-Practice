# Cluster 0

def read(path, encoding='utf-8'):
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path, encoding=encoding) as fp:
        return fp.read()

class MpsPrefixDirective(MpsDirective):
    domain = 'mps'
    name = 'prefix'
    has_content = True

    def run(self):
        targetid = self.content[0]
        self.state.document.mps_tag_prefix = targetid
        targetnode = nodes.target('', '', ids=[targetid])
        return [targetnode]

def run(self):
    targetid = self.content[0]
    self.state.document.mps_tag_prefix = targetid
    targetnode = nodes.target('', '', ids=[targetid])
    return [targetnode]

def mps_tag_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    try:
        targetid = '.'.join([inliner.document.mps_tag_prefix, text])
    except AttributeError:
        return ([], [inliner.document.reporter.warning('mps:tag without mps:prefix', line=lineno)])
    if len(text) == 0:
        return ([], [inliner.document.reporter.error('missing argument for mps:tag', line=lineno)])
    targetnode = nodes.target('', '', ids=[targetid])
    tag = '.{}:'.format(text)
    refnode = nodes.reference('', '', *[nodes.Text(tag)], refid=targetid, classes=['mpstag'])
    return ([targetnode, refnode], [])

def mps_ref_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    textnode = nodes.Text(text)
    if text.startswith('.'):
        try:
            targetid = inliner.document.mps_tag_prefix + text
            refnode = nodes.reference('', '', *[textnode], refid=targetid)
        except AttributeError:
            return ([textnode], [inliner.document.reporter.warning(':mps:ref without mps:prefix', line=lineno)])
    else:
        refnode = addnodes.pending_xref('', refdomain='std', reftarget=text, reftype='view')
        refnode += textnode
    return ([refnode], [])

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

def secnum_sub(m):
    return m.group(1) + '\n' + m.group(3) * len(m.group(1))

def citation_sub(m):
    groups = {k: re.sub('\\s+', ' ', v) for k, v in m.groupdict().items() if v}
    fmt = '.. {ref} {author}.'
    if 'organization' in groups:
        fmt += ' {organization}.'
    fmt += ' {date}.'
    if 'url' in groups:
        fmt += ' "`{title} <{url}>`__".'
    else:
        fmt += ' "{title}".'
    return fmt.format(**groups)

def index_sub(m):
    s = '\n.. index::\n'
    for term in index_term.finditer(m.group(1)):
        s += '   %s: %s\n' % (term.group(1), term.group(2))
    s += '\n'
    return s

def convert_file(name, source, dest):
    s = open(source, 'rb').read().decode('utf-8')
    m = index.search(s)
    if m:
        s = index_sub(m) + '.. _design-{0}:\n\n'.format(name) + s
    s = mode.sub('', s)
    s = prefix.sub('.. mps:prefix:: \\1', s)
    s = rst_tag.sub('', s)
    s = mps_tag.sub(':mps:tag:`\\1`', s)
    s = mps_ref.sub(':mps:ref:`\\1`', s)
    s = typedef.sub('.. c:type:: \\1', s)
    s = funcdef.sub('.. c:function:: \\1', s)
    s = macrodef.sub('.. c:macro:: \\1', s)
    s = typename.sub(':c:type:`\\1`', s)
    s = func.sub(':c:func:`\\1`', s)
    s = macro.sub(':c:macro:`\\1`', s)
    s = secnum.sub(secnum_sub, s)
    s = citation.sub(citation_sub, s)
    s = design_ref.sub('\\1.html', s)
    s = design_frag_ref.sub('\\1.html#design.mps.\\2.\\3', s)
    s = history.sub('', s)
    s = '.. highlight:: none\n\n' + s
    try:
        os.makedirs(os.path.dirname(dest))
    except:
        pass
    with open(dest, 'wb') as out:
        out.write(s.encode('utf-8'))

def newer(src, target):
    """Return True if src is newer (that is, modified more recently) than
    target, False otherwise.

    """
    return not os.path.isfile(target) or os.path.getmtime(target) < os.path.getmtime(src) or os.path.getmtime(target) < os.path.getmtime(__file__)

def convert_updated(app):
    for design in glob.iglob('../design/*.txt'):
        name = os.path.splitext(os.path.basename(design))[0]
        if name == 'index':
            continue
        converted = 'source/design/%s.rst' % name
        if newer(design, converted):
            app.info('converting design %s' % name)
            convert_file(name, design, converted)
    for diagram in glob.iglob('../design/*.svg'):
        target = os.path.join('source/design/', os.path.basename(diagram))
        if newer(diagram, target):
            shutil.copyfile(diagram, target)

@pytest.mark.benchmark(warmup=False, warmup_iterations=1, min_rounds=1)
def test_load_large_scale_image_dataset(benchmark, setup_pytorch_tests):
    tmp_dir = setup_pytorch_tests.config.get_value('storage', 'tmp_dir')
    statvfs = os.statvfs(tmp_dir)
    available_gb = statvfs.f_frsize * statvfs.f_bavail / 1024 ** 3
    img_dir = os.path.join(tmp_dir, 'large_scale_image_dataset_1000000')
    if not os.path.exists(img_dir):
        if available_gb < 10:
            return
        create_large_scale_image_dataset()

    def _execute_query_list(query_list):
        for query in query_list:
            execute_query_fetch_all(setup_pytorch_tests, query)
    drop_query = 'DROP TABLE IF EXISTS benchmarkImageDataset;'
    load_query = f"LOAD IMAGE '{img_dir}/*.jpg' INTO benchmarkImageDataset;"
    benchmark(_execute_query_list, [drop_query, load_query])

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

def test_should_fail_to_load_corrupt_video(self):
    tempfile_name = os.urandom(24).hex()
    tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
    with open(tempfile_path, 'wb') as tmp:
        query = f'LOAD VIDEO "{tmp.name}" INTO MyVideos;'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)

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

def test_should_fail_to_load_corrupt_image(self):
    tempfile_name = os.urandom(24).hex()
    tempfile_path = os.path.join(tempfile.gettempdir(), tempfile_name)
    with open(tempfile_path, 'wb') as tmp:
        query = f'LOAD IMAGE "{tmp.name}" INTO MyImages;'
        with self.assertRaises(Exception):
            execute_query_fetch_all(self.evadb, query, do_not_print_exceptions=True)

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

@ray_skip_marker
def test_check_configuration_file(self):
    config_file_path = os.path.join(EvaDB_ROOT_DIR, 'evadb', EvaDB_CONFIG_FILE)
    import yaml
    with open(config_file_path, 'r') as file:
        yaml_data = yaml.safe_load(file)
        ray_setting = yaml_data.get('experimental').get('ray')
        self.assertEquals(ray_setting, False)

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
def setUpClass(self):
    try_to_import_decord()
    self.video_file_url = create_sample_video()
    self.video_with_audio_file_url = f'{EvaDB_ROOT_DIR}/data/sample_videos/touchdown.mp4'
    self.frame_size = FRAME_SIZE[0] * FRAME_SIZE[1] * 3
    self.audio_frames = []
    for line in open(f'{EvaDB_ROOT_DIR}/test/data/touchdown_audio_frames.csv').readlines():
        self.audio_frames.append(np.fromstring(line, sep=','))

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

def __str__(self) -> str:
    return '%s[%s](%s)' % (type(self).__name__, hex(id(self)), ', '.join(('%s=%s' % item for item in vars(self).items())))

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

def __str__(self) -> str:
    return '%s(%s)' % (type(self).__name__, ', '.join(('%s=%s' % item for item in vars(self).items())))

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

def build(self, logical_plan: Operator):
    try:
        plan = self.optimize(logical_plan)
    except TimeoutError:
        raise ValueError('Optimizer timed out!')
    return plan

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

def __str__(self) -> str:
    return '%s(%s)' % (type(self).__name__, ', '.join(('%s=%s' % item for item in vars(self).items())))

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

def convert_to_numeric(self, x):
    x = re.sub('[^0-9.,]', '', str(x))
    locale.setlocale(locale.LC_ALL, '')
    x = float(locale.atof(x))
    if x.is_integer():
        return int(x)
    else:
        return x

def iter_path_regex(path_regex: Path) -> Generator[str, None, None]:
    return glob.iglob(os.path.expanduser(path_regex), recursive=True)

def validate_video(video_path: Path) -> bool:
    try:
        try_to_import_cv2()
        import cv2
        vid = cv2.VideoCapture(str(video_path))
        if not vid.isOpened():
            return False
        return True
    except Exception as e:
        logger.warning(f'Unexpected Exception {e} occurred while reading video file {video_path}')

def validate_media(file_path: Path, media_type: FileFormatType) -> bool:
    if media_type == FileFormatType.VIDEO:
        return validate_video(file_path)
    elif media_type == FileFormatType.IMAGE:
        return validate_image(file_path)
    elif media_type == FileFormatType.DOCUMENT:
        return validate_document(file_path)
    elif media_type == FileFormatType.PDF:
        return validate_pdf(file_path)
    else:
        raise ValueError(f'Unsupported Media type {str(media_type)}')

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

def execute(self):
    try:
        self._scan_and_execute_jobs()
    except KeyboardInterrupt:
        logger.debug('Exiting the job scheduler process due to interrupt')
        sys.exit()

def try_to_import_ray():
    try:
        import ray
        from ray.util.queue import Queue
    except ImportError:
        raise ValueError('Could not import ray python package.\n                Please install it with `pip install ray`.')

def try_to_import_statsforecast():
    try:
        from statsforecast import StatsForecast
    except ImportError:
        raise ValueError('Could not import StatsForecast python package.\n                Please install it with `pip install statsforecast`.')

def try_to_import_neuralforecast():
    try:
        from neuralforecast import NeuralForecast
    except ImportError:
        raise ValueError('Could not import NeuralForecast python package.\n                Please install it with `pip install neuralforecast`.')

def try_to_import_ludwig():
    try:
        import ludwig
        from ludwig.automl import auto_train
    except ImportError:
        raise ValueError('Could not import ludwig.\n                Please install it with `pip install evadb[ludwig]`.')

def try_to_import_flaml_automl():
    try:
        import flaml
        from flaml import AutoML
    except ImportError:
        raise ValueError('Could not import Flaml AutML.\n                Please install it with `pip install "flaml[automl]"`.')

def try_to_import_pillow():
    try:
        import PIL
    except ImportError:
        raise ValueError('Could not import pillow python package.\n                Please install it with `pip install pillow`.')

def try_to_import_torch():
    try:
        import torch
    except ImportError:
        raise ValueError('Could not import torch python package.\n                Please install them with `pip install torch`.')

def try_to_import_torchvision():
    try:
        import torchvision
    except ImportError:
        raise ValueError('Could not import torchvision python package.\n                Please install them with `pip install torchvision`.')

def try_to_import_cv2():
    try:
        import cv2
    except ImportError:
        raise ValueError('Could not import cv2 python package.\n                Please install it with `pip install opencv-python`.')

def try_to_import_timm():
    try:
        import timm
    except ImportError:
        raise ValueError('Could not import timm python package.\n                Please install them with `pip install timm`.')

def try_to_import_kornia():
    try:
        import kornia
    except ImportError:
        raise ValueError('Could not import kornia python package.\n                Please install it with `pip install kornia`.')

def try_to_import_decord():
    try:
        import decord
    except ImportError:
        raise ValueError('Could not import decord python package.\n                Please install it with `pip install eva-decord`.')

def try_to_import_ultralytics():
    try:
        import ultralytics
    except ImportError:
        raise ValueError('Could not import ultralytics python package.\n                Please install it with `pip install ultralytics`.')

def try_to_import_norfair():
    try:
        import norfair
    except ImportError:
        raise ValueError('Could not import norfair python package.\n                Please install it with `pip install norfair`.')

def try_to_import_transformers():
    try:
        import transformers
    except ImportError:
        raise ValueError('Could not import transformers python package.\n                Please install it with `pip install transformers`.')

def try_to_import_facenet_pytorch():
    try:
        import facenet_pytorch
    except ImportError:
        raise ValueError('Could not import facenet_pytorch python package.\n                Please install it with `pip install facenet-pytorch`.')

def try_to_import_openai():
    try:
        import openai
    except ImportError:
        raise ValueError('Could not import openai python package.\n                Please install them with `pip install openai`.')

def try_to_import_langchain():
    try:
        import langchain
    except ImportError:
        raise ValueError('Could not import langchain package.\n                Please install it with `pip install langchain`.')

def try_to_import_faiss():
    try:
        import faiss
    except ImportError:
        raise ValueError('Could not import faiss python package.\n                Please install it with `pip install faiss-cpu` or `pip install faiss-gpu`.')

def try_to_import_qdrant_client():
    try:
        import qdrant_client
    except ImportError:
        raise ValueError('Could not import qdrant_client python package.\n                Please install it with `pip install qdrant_client`.')

def try_to_import_pinecone_client():
    try:
        import pinecone
    except ImportError:
        raise ValueError("Could not import pinecone_client python package.\n                Please install it with 'pip install pinecone_client`.")

def try_to_import_chromadb_client():
    try:
        import chromadb
    except ImportError:
        raise ValueError("Could not import chromadb python package.\n                Please install it with 'pip install chromadb`.")

def try_to_import_weaviate_client():
    try:
        import weaviate
    except ImportError:
        raise ValueError("Could not import weaviate python package.\n                Please install it with 'pip install weaviate-client`.")

def try_to_import_milvus_client():
    try:
        import pymilvus
    except ImportError:
        raise ValueError("Could not import pymilvus python package.\n                Please install it with 'pip install pymilvus`.")

def is_pinecone_available() -> bool:
    try:
        try_to_import_pinecone_client()
        return True
    except ValueError:
        return False

def try_to_import_moto():
    try:
        import boto3
    except ImportError:
        raise ValueError('Could not import boto3 python package.\n                Please install it with `pip install moto[s3]`.')

def try_to_import_fitz():
    try:
        import fitz
    except ImportError:
        raise ValueError('Could not import fitz python package.\n                Please install it with `pip install pymupdfs`.')

def try_to_import_replicate():
    try:
        import replicate
    except ImportError:
        raise ValueError('Could not import replicate python package.\n                Please install it with `pip install replicate`.')

class NdArrayType(EvaDBEnum):
    INT8
    UINT8
    INT16
    INT32
    INT64
    UNICODE
    BOOL
    FLOAT32
    FLOAT64
    DECIMAL
    STR
    DATETIME
    ANYTYPE

    @classmethod
    def to_numpy_type(cls, t):
        from decimal import Decimal
        import numpy as np
        if t == cls.INT8:
            np_type = np.int8
        elif t == cls.UINT8:
            np_type = np.uint8
        elif t == cls.INT16:
            np_type = np.int16
        elif t == cls.INT32:
            np_type = np.int32
        elif t == cls.INT64:
            np_type = np.int64
        elif t == cls.UNICODE:
            np_type = np.unicode_
        elif t == cls.BOOL:
            np_type = np.bool_
        elif t == cls.FLOAT32:
            np_type = np.float32
        elif t == cls.FLOAT64:
            np_type = np.float64
        elif t == cls.DECIMAL:
            np_type = Decimal
        elif t == cls.STR:
            np_type = np.str_
        elif t == cls.DATETIME:
            np_type = np.datetime64
        elif t == cls.ANYTYPE:
            np_type = np.dtype(object)
        else:
            raise ValueError('Can not auto convert %s to numpy type' % t)
        return np_type

@classmethod
def to_numpy_type(cls, t):
    from decimal import Decimal
    import numpy as np
    if t == cls.INT8:
        np_type = np.int8
    elif t == cls.UINT8:
        np_type = np.uint8
    elif t == cls.INT16:
        np_type = np.int16
    elif t == cls.INT32:
        np_type = np.int32
    elif t == cls.INT64:
        np_type = np.int64
    elif t == cls.UNICODE:
        np_type = np.unicode_
    elif t == cls.BOOL:
        np_type = np.bool_
    elif t == cls.FLOAT32:
        np_type = np.float32
    elif t == cls.FLOAT64:
        np_type = np.float64
    elif t == cls.DECIMAL:
        np_type = Decimal
    elif t == cls.STR:
        np_type = np.str_
    elif t == cls.DATETIME:
        np_type = np.datetime64
    elif t == cls.ANYTYPE:
        np_type = np.dtype(object)
    else:
        raise ValueError('Can not auto convert %s to numpy type' % t)
    return np_type

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

def __init__(self):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    lark_path = os.path.join(dir_path, 'evadb.lark')
    with open(lark_path) as f:
        sql_grammar = f.read()
    self._parser = Lark(sql_grammar, parser='lalr')

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

def dotted_id(self, tree):
    dotted_id = str(tree.children[0])
    dotted_id = dotted_id.lstrip('.')
    return dotted_id

def real_literal(self, tree):
    real_literal = float(tree.children[0])
    return real_literal

def _get_database_handler(engine: str, **kwargs):
    """
    Return the database handler. User should modify this function for
    their new integrated handlers.
    """
    try:
        mod = dynamic_import(engine)
    except ImportError:
        req_file = os.path.join(os.path.dirname(__file__), engine, 'requirements.txt')
        if os.path.isfile(req_file):
            with open(req_file) as f:
                raise ImportError(f'Please install the following packages {f.read()}')
    if engine == 'postgres':
        return mod.PostgresHandler(engine, **kwargs)
    elif engine == 'sqlite':
        return mod.SQLiteHandler(engine, **kwargs)
    elif engine == 'mysql':
        return mod.MysqlHandler(engine, **kwargs)
    elif engine == 'mariadb':
        return mod.MariaDbHandler(engine, **kwargs)
    elif engine == 'clickhouse':
        return mod.ClickHouseHandler(engine, **kwargs)
    elif engine == 'snowflake':
        return mod.SnowFlakeDbHandler(engine, **kwargs)
    elif engine == 'github':
        return mod.GithubHandler(engine, **kwargs)
    elif engine == 'hackernews':
        return mod.HackernewsSearchHandler(engine, **kwargs)
    elif engine == 'slack':
        return mod.SlackHandler(engine, **kwargs)
    else:
        raise NotImplementedError(f'Engine {engine} is not supported')

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

def _sqlite_to_python_types(self, sqlite_type: str):
    mapping = {'INT': int, 'INTEGER': int, 'TINYINT': int, 'SMALLINT': int, 'MEDIUMINT': int, 'BIGINT': int, 'UNSIGNED BIG INT': int, 'INT2': int, 'INT8': int, 'CHARACTER': str, 'VARCHAR': str, 'VARYING CHARACTER': str, 'NCHAR': str, 'NATIVE CHARACTER': str, 'NVARCHAR': str, 'TEXT': str, 'CLOB': str, 'BLOB': bytes, 'REAL': float, 'DOUBLE': float, 'DOUBLE PRECISION': float, 'FLOAT': float, 'NUMERIC': float, 'DECIMAL': float, 'BOOLEAN': bool, 'DATE': datetime.date, 'DATETIME': datetime.datetime}
    sqlite_type = sqlite_type.split('(')[0].strip().upper()
    if sqlite_type in mapping:
        return mapping[sqlite_type]
    else:
        raise Exception(f'Unsupported column {sqlite_type} encountered in the sqlite table. Please raise a feature request!')

class PineconeVectorStore(VectorStore):

    def __init__(self, index_name: str, **kwargs) -> None:
        try_to_import_pinecone_client()
        global _pinecone_init_done
        self._index_name = index_name.strip().lower()
        self._api_key = kwargs.get('PINECONE_API_KEY')
        if not self._api_key:
            self._api_key = os.environ.get('PINECONE_API_KEY')
        assert self._api_key, 'Please set your `PINECONE_API_KEY` using set command or environment variable (PINECONE_KEY). It can be found at Pinecone Dashboard > API Keys > Value'
        self._environment = kwargs.get('PINECONE_ENV')
        if not self._environment:
            self._environment = os.environ.get('PINECONE_ENV')
        assert self._environment, 'Please set your `PINECONE_ENV` or environment variable (PINECONE_ENV). It can be found Pinecone Dashboard > API Keys > Environment.'
        if not _pinecone_init_done:
            import pinecone
            pinecone.init(api_key=self._api_key, environment=self._environment)
            _pinecone_init_done = True
        self._client = None

    def create(self, vector_dim: int):
        import pinecone
        pinecone.create_index(self._index_name, dimension=vector_dim, metric='cosine')
        logger.warning(f'Created index {self._index_name}. Please note that Pinecone is eventually consistent, hence any additions to the Vector Index may not get immediately reflected in queries.')
        self._client = pinecone.Index(self._index_name)

    def add(self, payload: List[FeaturePayload]):
        self._client.upsert(vectors=[{'id': str(row.id), 'values': row.embedding.reshape(-1).tolist()} for row in payload])

    def delete(self) -> None:
        import pinecone
        pinecone.delete_index(self._index_name)

    def query(self, query: VectorIndexQuery) -> VectorIndexQueryResult:
        import pinecone
        if not self._client:
            self._client = pinecone.Index(self._index_name)
        response = self._client.query(top_k=query.top_k, vector=query.embedding.reshape(-1).tolist())
        distances, ids = ([], [])
        for row in response['matches']:
            distances.append(row['score'])
            ids.append(int(row['id']))
        return VectorIndexQueryResult(distances, ids)

def __init__(self, index_name: str, **kwargs) -> None:
    try_to_import_pinecone_client()
    global _pinecone_init_done
    self._index_name = index_name.strip().lower()
    self._api_key = kwargs.get('PINECONE_API_KEY')
    if not self._api_key:
        self._api_key = os.environ.get('PINECONE_API_KEY')
    assert self._api_key, 'Please set your `PINECONE_API_KEY` using set command or environment variable (PINECONE_KEY). It can be found at Pinecone Dashboard > API Keys > Value'
    self._environment = kwargs.get('PINECONE_ENV')
    if not self._environment:
        self._environment = os.environ.get('PINECONE_ENV')
    assert self._environment, 'Please set your `PINECONE_ENV` or environment variable (PINECONE_ENV). It can be found Pinecone Dashboard > API Keys > Environment.'
    if not _pinecone_init_done:
        import pinecone
        pinecone.init(api_key=self._api_key, environment=self._environment)
        _pinecone_init_done = True
    self._client = None

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

class ForecastModel(AbstractFunction):

    @property
    def name(self) -> str:
        return 'ForecastModel'

    @setup(cacheable=False, function_type='Forecasting', batchable=True)
    def setup(self, model_name: str, model_path: str, predict_column_rename: str, time_column_rename: str, id_column_rename: str, horizon: int, library: str, conf: int):
        self.library = library
        if 'neuralforecast' in self.library:
            from neuralforecast import NeuralForecast
            loaded_model = NeuralForecast.load(path=model_path)
            self.model_name = model_name[4:] if 'Auto' in model_name else model_name
        else:
            with open(model_path, 'rb') as f:
                loaded_model = pickle.load(f)
            self.model_name = model_name
        self.model = loaded_model
        self.predict_column_rename = predict_column_rename
        self.time_column_rename = time_column_rename
        self.id_column_rename = id_column_rename
        self.horizon = int(horizon)
        self.library = library
        self.suggestion_dict = {1: "Predictions are flat. Consider using LIBRARY 'neuralforecast' for more accrate predictions."}
        self.conf = conf
        self.hypers = None
        self.rmse = None
        if os.path.isfile(model_path + '_rmse'):
            with open(model_path + '_rmse', 'r') as f:
                self.rmse = float(f.readline())
                if 'arima' in model_name.lower():
                    self.hypers = 'p,d,q: ' + f.readline()

    def forward(self, data) -> pd.DataFrame:
        log_str = ''
        if self.library == 'statsforecast':
            forecast_df = self.model.predict(h=self.horizon, level=[self.conf]).reset_index()
        else:
            forecast_df = self.model.predict().reset_index()
        if len(data) == 0 or list(list(data.iloc[0]))[0] is True:
            suggestion_list = []
            if self.library == 'statsforecast':
                for type_here in forecast_df['unique_id'].unique():
                    if forecast_df.loc[forecast_df['unique_id'] == type_here][self.model_name].nunique() == 1:
                        suggestion_list.append(1)
            for suggestion in set(suggestion_list):
                log_str += '\nSUGGESTION: ' + self.suggestion_dict[suggestion]
            if self.rmse is not None:
                log_str += '\nMean normalized RMSE: ' + str(self.rmse)
            if self.hypers is not None:
                log_str += '\nHyperparameters: ' + self.hypers
            print(log_str)
        forecast_df = forecast_df.rename(columns={'unique_id': self.id_column_rename, 'ds': self.time_column_rename, self.model_name if self.library == 'statsforecast' else self.model_name + '-median': self.predict_column_rename, self.model_name + '-lo-' + str(self.conf): self.predict_column_rename + '-lo', self.model_name + '-hi-' + str(self.conf): self.predict_column_rename + '-hi'})[:self.horizon * forecast_df['unique_id'].nunique()]
        return forecast_df

@setup(cacheable=False, function_type='Forecasting', batchable=True)
def setup(self, model_name: str, model_path: str, predict_column_rename: str, time_column_rename: str, id_column_rename: str, horizon: int, library: str, conf: int):
    self.library = library
    if 'neuralforecast' in self.library:
        from neuralforecast import NeuralForecast
        loaded_model = NeuralForecast.load(path=model_path)
        self.model_name = model_name[4:] if 'Auto' in model_name else model_name
    else:
        with open(model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        self.model_name = model_name
    self.model = loaded_model
    self.predict_column_rename = predict_column_rename
    self.time_column_rename = time_column_rename
    self.id_column_rename = id_column_rename
    self.horizon = int(horizon)
    self.library = library
    self.suggestion_dict = {1: "Predictions are flat. Consider using LIBRARY 'neuralforecast' for more accrate predictions."}
    self.conf = conf
    self.hypers = None
    self.rmse = None
    if os.path.isfile(model_path + '_rmse'):
        with open(model_path + '_rmse', 'r') as f:
            self.rmse = float(f.readline())
            if 'arima' in model_name.lower():
                self.hypers = 'p,d,q: ' + f.readline()

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

def try_to_import_sentence_transformers():
    try:
        import sentence_transformers
    except ImportError:
        raise ValueError('Could not import sentence-transformers python package.\n                Please install it with `pip install sentence-transformers`.')

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

def _multiline_query_transformation(self, query: str) -> str:
    query = query.replace('\n', ' ')
    query = query.lstrip()
    query = query.rstrip(' ;')
    query += ';'
    logger.debug('Query: ' + query)
    return query

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

def _xform_file_url_to_file_name(self, file_url: Path) -> str:
    file_path_str = str(file_url)
    file_path = re.sub('[^a-zA-Z0-9 \\.\\n]', '_', file_path_str)
    return file_path

class StorageEngine:
    storages = None

    @classmethod
    def _lazy_initialize_storages(cls, db: EvaDBDatabase):
        if not cls.storages:
            cls.storages = {TableType.STRUCTURED_DATA: SQLStorageEngine, TableType.VIDEO_DATA: DecordStorageEngine, TableType.IMAGE_DATA: ImageStorageEngine, TableType.DOCUMENT_DATA: DocumentStorageEngine, TableType.PDF_DATA: PDFStorageEngine, TableType.NATIVE_DATA: NativeStorageEngine}

    @classmethod
    def factory(cls, db: EvaDBDatabase, table: TableCatalogEntry) -> AbstractStorageEngine:
        cls._lazy_initialize_storages(db)
        if table is None:
            raise ValueError('Expected TableCatalogEntry, got None')
        if table.table_type in cls.storages:
            return cls.storages[table.table_type](db)
        raise RuntimeError(f'Invalid table type {table.table_type}')

@classmethod
def factory(cls, db: EvaDBDatabase, table: TableCatalogEntry) -> AbstractStorageEngine:
    cls._lazy_initialize_storages(db)
    if table is None:
        raise ValueError('Expected TableCatalogEntry, got None')
    if table.table_type in cls.storages:
        return cls.storages[table.table_type](db)
    raise RuntimeError(f'Invalid table type {table.table_type}')

def format_name(obj_name, format_dict):
    if format_dict is not None:
        return '<FONT COLOR="{color}" POINT-SIZE="{size}">{bld}{it}{name}{e_it}{e_bld}</FONT>'.format(name=obj_name, color=format_dict.get('color') if 'color' in format_dict else 'initial', size=float(format_dict['fontsize']) if 'fontsize' in format_dict else 'initial', it='<I>' if format_dict.get('italics') else '', e_it='</I>' if format_dict.get('italics') else '', bld='<B>' if format_dict.get('bold') else '', e_bld='</B>' if format_dict.get('bold') else '')
    else:
        return obj_name

def show_uml_graph(*args, **kwargs):
    from cStringIO import StringIO
    from PIL import Image
    iostream = StringIO(create_uml_graph(*args, **kwargs).create_png())
    Image.open(iostream).show(command=kwargs.get('command', 'gwenview'))

def show_schema_graph(*args, **kwargs):
    from cStringIO import StringIO
    from PIL import Image
    iostream = StringIO(create_schema_graph(*args, **kwargs).create_png())
    Image.open(iostream).show(command=kwargs.get('command', 'gwenview'))

def get_confirm_token(response):
    """
    Returns the confirm token from the response.
    Args:
        response: response object from the request
    """
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    """
    Writes the content of the response to the destination. 
    Args:
        response: response object from the request
        destination: path to save the file to
    """
    CHUNK_SIZE = 32768
    with open(destination, 'wb') as f:
        for chunk in tqdm(response.iter_content(CHUNK_SIZE)):
            if chunk:
                f.write(chunk)

def get_string_in_line(file_path, line_number):
    line = linecache.getline(file_path, line_number)
    return line.strip()

def get_changelog(github_timestamp):
    release_date = datetime.fromisoformat(github_timestamp[:-1])
    utc_timezone = pytz.timezone('UTC')
    release_date = utc_timezone.localize(release_date)
    os.chdir(EvaDB_DIR)
    run_command('git pull origin master')
    repo = git.Repo('.git')
    regexp = re.compile('\\#[0-9]*')
    changelog = ''
    for commit in repo.iter_commits('master'):
        if commit.authored_datetime < release_date:
            break
        output = regexp.search(commit.message)
        if '[BUMP]' in commit.message:
            continue
        if output is None:
            continue
        else:
            pr_number = output.group(0)
            key_message = commit.message.split('\n')[0]
            key_message = key_message.split('(')[0]
            pr_number = pr_number.split('#')[1]
            if '[RELEASE]' in key_message:
                continue
            changelog += f'* PR #{pr_number}: {key_message}\n'
    return changelog

def read_file(path, encoding='utf-8'):
    path = os.path.join(os.path.dirname(__file__), path)
    import io
    with io.open(path, encoding=encoding) as fp:
        return fp.read()

def release_version(current_version):
    version_path = os.path.join(os.path.join(EvaDB_DIR, 'evadb'), 'version.py')
    with open(version_path, 'r') as version_file:
        output = version_file.read()
        output = output.replace('+dev', '')
    with open(version_path, 'w') as version_file:
        version_file.write(output)
    NEXT_RELEASE = current_version
    run_command('git checkout -b release-' + NEXT_RELEASE)
    run_command('git add . -u')
    run_command("git commit -m '[RELEASE]: " + NEXT_RELEASE + "'")
    run_command('git push --set-upstream origin release-' + NEXT_RELEASE)
    run_command(f'git push origin release-{NEXT_RELEASE}')

def publish_wheels(tag):
    run_command('rm -rf dist build')
    run_command('python3 setup.py sdist')
    run_command('python3 setup.py bdist_wheel')
    run_command(f'python3 -m pip install dist/evadb-{tag}-py3-none-any.whl')
    run_command('python3 -c "import evadb; print(evadb.__version__)" ')
    print('Running twine to upload wheels')
    print('Ensure that you have .pypirc file in your $HOME folder')
    run_command('twine upload dist/* -r pypi')

def bump_up_version(next_version):
    version_path = os.path.join(os.path.join(EvaDB_DIR, 'evadb'), 'version.py')
    major_str = get_string_in_line(version_path, 1)
    minor_str = get_string_in_line(version_path, 2)
    patch_str = get_string_in_line(version_path, 3)
    assert 'dev' not in patch_str
    major_str = f'_MAJOR = "{str(next_version.major)}"\n'
    minor_str = f'_MINOR = "{str(next_version.minor)}"\n'
    patch_str = f'_REVISION = "{str(next_version.patch)}+dev"\n\n'
    footer = 'VERSION_SHORT = f"{_MAJOR}.{_MINOR}"\nVERSION = f"{_MAJOR}.{_MINOR}.{_REVISION}"'
    output = major_str + minor_str + patch_str + footer
    with open(version_path, 'w') as version_file:
        version_file.write(output)
    NEXT_RELEASE = f'v{str(next_version)}+dev'
    run_command('git checkout -b bump-' + NEXT_RELEASE)
    run_command('git add . -u')
    run_command("git commit -m '[BUMP]: " + NEXT_RELEASE + "'")
    run_command('git push --set-upstream origin bump-' + NEXT_RELEASE)
    run_command(f"gh pr create -B staging -H bump-{NEXT_RELEASE} --title 'Bump Version to {NEXT_RELEASE}' --body 'Bump Version to {NEXT_RELEASE}'")

def contains_commented_out_code(line):
    line = line.lstrip()
    if 'utf-8' in line:
        return False
    if not line.startswith('#'):
        return False
    line = line.lstrip(' \t\x0b\n#').strip()
    regex_list = ['def .+\\)[\\s]*[->]*[\\s]*[a-zA-Z_]*[a-zA-Z0-9_]*:$', 'with .+ as [a-zA-Z_][a-zA-Z0-9_]*:$', 'for [a-zA-Z_][a-zA-Z0-9_]* in .+:$', 'continue$', 'break$']
    for regex in regex_list:
        if re.search(regex, line):
            return True
    symbol_list = list('[]{}=%') + ['print', 'break', 'import ', 'elif ']
    for symbol in symbol_list:
        if symbol in line:
            return True
    if 'return' in line:
        if len(line.split(' ')) >= 2:
            return False
        else:
            return True
    return False

def validate_file(file):
    file = os.path.abspath(file)
    if not os.path.isfile(file):
        LOG.info('ERROR: ' + file + " isn't a file")
        sys.exit(EXIT_FAILURE)
    if not file.endswith('.py'):
        return True
    code_validation = True
    line_number = 1
    commented_code = False
    with open(file, 'r') as opened_file:
        for line in opened_file:
            if line.lstrip().startswith('#'):
                commented_code = contains_commented_out_code(line)
                if commented_code:
                    LOG.info('Commented code ' + 'in file ' + file + ' Line {}: {}'.format(line_number, line.strip()))
            for validator_pattern in VALIDATOR_PATTERNS:
                if validator_pattern.search(line):
                    code_validation = False
                    LOG.info('Unacceptable pattern:' + validator_pattern.pattern.strip() + ' in file ' + file + ' Line {}: {}'.format(line_number, line.strip()))
            line_number += 1
    return code_validation

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    from shutil import which
    req_version = None
    if name is FLAKE_BINARY:
        req_version = FLAKE8_VERSION_REQUIRED
    elif name is BLACK_BINARY:
        req_version = BLACK_VERSION_REQUIRED
    elif name is ISORT_BINARY:
        req_version = ISORT_VERSION_REQUIRED
    if which(name) is None:
        LOG.error(f'{name} is not installed. Install the python package with:pip install {name}=={req_version}')
        sys.exit(1)
    else:
        try:
            installed_version = pkg_resources.get_distribution(name).version
        except pkg_resources.DistributionNotFound:
            installed_version = 'not-found'
        if installed_version != req_version:
            LOG.warning(f'EvaDB uses {name} {req_version}. The installed version is {installed_version} which can result in different results.')

def check_header(file_path):
    abs_path = os.path.abspath(file_path)
    with open(abs_path, 'r+') as fd:
        file_data = fd.read()
        header_match = header_regex.match(file_data)
        if header_match is None:
            return False
        header_comment = header_match.group(1)
        if header_comment == header:
            return True
        else:
            return False

def format_file(file_path, add_header, strip_header, format_code):
    if file_path.endswith('version.py'):
        return
    abs_path = os.path.abspath(file_path)
    with open(abs_path, 'r+') as fd:
        file_data = fd.read()
        if add_header:
            LOG.info('Adding header: ' + file_path)
            new_file_data = header + file_data
            fd.seek(0, 0)
            fd.truncate()
            fd.write(new_file_data)
        elif strip_header:
            LOG.info('Stripping headers : ' + file_path)
            header_match = header_regex.match(file_data)
            if header_match is None:
                return
            header_comment = header_match.group(1)
            new_file_data = file_data.replace(header_comment, '')
            fd.seek(0, 0)
            fd.truncate()
            fd.write(new_file_data)
        elif format_code:
            isort_command = f'{ISORT_BINARY} --profile  black  {file_path}'
            os.system(isort_command)
            black_command = f'{BLACK_BINARY} -q {file_path}'
            os.system(black_command)
            autoflake_command = f"{FLAKE_BINARY} --config='{FLAKE8_CONFIG}' {file_path}"
            ret_val = os.system(autoflake_command)
            if ret_val:
                sys.exit(1)
            pylint_command = f'{PYLINT_BINARY} --spelling-private-dict-file {ignored_words_file} --rcfile={PYLINTRC}  {file_path}'
            with open(file_path, 'r') as file:
                for line_num, line in enumerate(file, start=1):
                    if file_path not in IGNORE_PRINT_FILES and ' print(' in line:
                        LOG.warning(f'print() found in {file_path}, line {line_num}: {line.strip()}')
                        sys.exit(1)
    fd.close()

def check_notebook_format(notebook_file):
    notebook_file_name = os.path.basename(notebook_file)
    if notebook_file_name == 'ignore_tag.ipynb':
        return True
    with open(notebook_file) as f:
        nb = nbformat.read(f, as_version=4)
    if not nb.cells:
        LOG.error(f'ERROR: Notebook {notebook_file} has no cells')
        sys.exit(1)
    for cell in nb.cells:
        if cell.cell_type not in ['code', 'markdown', 'raw']:
            LOG.error(f'ERROR: Notebook {notebook_file} contains an invalid cell type: {cell.cell_type}')
            sys.exit(1)
    for cell in nb.cells:
        if cell.cell_type == 'code' and (not cell.source.strip()):
            LOG.error(f'ERROR: Notebook {notebook_file} contains an empty code cell')
            sys.exit(1)
    contains_colab_link = False
    for cell in nb.cells:
        if cell.cell_type == 'markdown' and 'colab' in cell.source:
            if notebook_file_name in cell.source:
                contains_colab_link = True
                break
    if contains_colab_link is False:
        LOG.error(f'ERROR: Notebook {notebook_file} does not contain correct Colab link -- update the link.')
        sys.exit(1)
    return True
    import enchant
    from enchant.checker import SpellChecker
    chkr = SpellChecker('en_US')
    for cell in nb.cells:
        if cell.cell_type == 'code':
            continue
        chkr.set_text(cell.source)
        for err in chkr:
            if err.word not in ignored_words:
                LOG.warning(f'WARNING: Notebook {notebook_file} contains the misspelled word: {err.word}')

def try_to_import_pytube():
    try:
        import pytube
    except ImportError:
        raise ValueError('Could not import pytube python package.\n                Please install it with `pip install -r requirements.txt`.')

def download_story():
    parsed_file_path, orig_file_path = ('new_wp.txt', 'wp.txt')
    if not os.path.exists(parsed_file_path):
        urllib.request.urlretrieve('https://www.gutenberg.org/cache/epub/2600/pg2600.txt', orig_file_path)
    new_f = open(parsed_file_path, 'w')
    merge_line = ''
    with open(orig_file_path, 'r') as f:
        for line in f.readlines():
            if line == '\n':
                new_f.write(f'{merge_line}\n')
                merge_line = ''
            else:
                merge_line += line.rstrip('\n') + ' '
    return parsed_file_path

def read_text_line(path, num_token=1000):
    whitelist = set('.!?abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    with open(path, 'r') as f:
        line_itr = 0
        for line in f.readlines():
            line_itr = line_itr + 1
            if line_itr % 10 == 0:
                print('line: ' + str(line_itr))
            for i in range(0, len(line), num_token):
                cut_line = line[i:min(i + 1000, len(line))]
                cut_line = ''.join(filter(whitelist.__contains__, cut_line))
                yield cut_line
            if line_itr == 1000:
                break

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file detected')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            path = Path(UPLOAD_FOLDER + '/' + filename)
            if path.is_file():
                flash('File uploaded')
                return {'response': 'File saved'}
            else:
                flash('Failed to upload file')
                return redirect(request.url)
    return '<html>\n                <body>\n                    <form method="POST"\n                        enctype = "multipart/form-data">\n                        <input type = "file" name = "file" />\n                        <input type = "submit"/>\n                    </form>\n                </body>\n            </html>'

