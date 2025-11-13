# Cluster 8

def complete_message() -> None:
    """Logging to print once the visualization is ready."""
    logger.info('Done rendering!')

class DistributedScenarioFilter:
    """
    Class to distribute the work to build / filter scenarios across workers, and to break up those scenarios in chunks to be
    handled on individual machines
    """

    def __init__(self, cfg: DictConfig, worker: WorkerPool, node_rank: int, num_nodes: int, synchronization_path: str, timeout_seconds: int=7200, distributed_mode: DistributedMode=DistributedMode.SCENARIO_BASED):
        """
        :param cfg: top level config for the job (used to build scenario builder / scenario_filter)
        :param worker: worker to use in each node to parallelize the work
        :param node_rank: number from (0, num_nodes -1) denoting "which" node we are on
        :param num_nodes: total number of nodes the job is running on
        :param synchronization_path: path that can be in s3 or on a shared file system that will be used to synchronize
                                     across workers
        :param timeout_seconds: how long to wait during sync operations
        :param distributed_mode: what distributed mode to use to distribute computation
        """
        self._cfg = cfg
        self._worker = worker
        self._node_rank = node_rank
        self._num_nodes = num_nodes
        self.synchronization_path = synchronization_path
        self._timeout_seconds = timeout_seconds
        self._distributed_mode = distributed_mode

    def get_scenarios(self) -> List[AbstractScenario]:
        """
        Get all the scenarios that the current node should process
        :returns: list of scenarios for the current node
        """
        if self._num_nodes == 1 or self._distributed_mode == DistributedMode.SINGLE_NODE:
            logger.info('Building Scenarios in mode %s', DistributedMode.SINGLE_NODE)
            scenario_builder = build_scenario_builder(cfg=self._cfg)
            scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
        elif self._distributed_mode in (DistributedMode.LOG_FILE_BASED, DistributedMode.SCENARIO_BASED):
            logger.info('Getting Log Chunks')
            current_chunk = self._get_log_db_files_for_single_node()
            logger.info('Getting Scenarios From Log Chunk of size %d', len(current_chunk))
            scenarios = self._get_scenarios_from_list_of_log_files(current_chunk)
            if self._distributed_mode == DistributedMode.LOG_FILE_BASED:
                logger.info('Distributed mode is %s, so we are just returning the scenariosfound from log files on the current worker.  There are %d scenarios to processon node %d/%d', DistributedMode.LOG_FILE_BASED, len(scenarios), self._node_rank, self._num_nodes)
                return scenarios
            logger.info('Distributed mode is %s, so we are going to repartition the scenarios we got from the log files to better distribute the work', DistributedMode.SCENARIO_BASED)
            logger.info('Getting repartitioned scenario tokens')
            tokens, log_db_files = self._get_repartition_tokens(scenarios)
            OmegaConf.set_struct(self._cfg, False)
            self._cfg.scenario_filter.scenario_tokens = tokens
            self._cfg.scenario_builder.db_files = log_db_files
            OmegaConf.set_struct(self._cfg, True)
            logger.info('Building repartitioned scenarios')
            scenario_builder = build_scenario_builder(cfg=self._cfg)
            scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
        else:
            raise ValueError(f'Distributed mode must be one of {[x.name for x in fields(DistributedMode)]}, got {self._distributed_mode} instead!')
        scenarios = scenario_builder.get_scenarios(scenario_filter, self._worker)
        return scenarios

    def _get_repartition_tokens(self, scenarios: List[AbstractScenario]) -> Tuple[List[str], List[str]]:
        """
        Submit list of scenarios found by the current node, sync up with other nodes to get the full list of tokens,
        and calculate the current node's set of tokens to process
        :param scenarios: Scenarios found by the current node
        :returns: (list of tokens, list of db files)
        """
        unique_job_id = get_unique_job_id()
        token_distribution_file_dir = Path(self.synchronization_path) / Path('tokens') / Path(unique_job_id)
        token_distribution_barrier_dir = Path(self.synchronization_path) / Path('barrier') / Path(unique_job_id)
        if self.synchronization_path.startswith('s3'):
            token_distribution_file_dir = safe_path_to_string(token_distribution_file_dir)
            token_distribution_barrier_dir = safe_path_to_string(token_distribution_barrier_dir)
        self._write_token_csv_file(scenarios, token_distribution_file_dir)
        distributed_sync(token_distribution_barrier_dir, timeout_seconds=self._timeout_seconds)
        token_distribution = self._get_all_generated_csv(token_distribution_file_dir)
        db_files_path = Path(self._cfg.scenario_builder.db_files[0]).parent if isinstance(self._cfg.scenario_builder.db_files, (list, ListConfig)) else Path(self._cfg.scenario_builder.db_files)
        return self._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)

    def _get_all_generated_csv(self, token_distribution_file_dir: Union[Path, str]) -> List[Tuple[str, str]]:
        """
        Read the csv files that every machine in the cluster generated and get the full list of (token, db_file) pairs
        :param token_distribution_file_dir: path where to the csv files are stored
        :returns: full list of (token, db_file) pairs
        """
        if self.synchronization_path.startswith('s3'):
            token_distribution_file_list = [el for el in expand_s3_dir(token_distribution_file_dir) if el.endswith('.csv')]
            token_distribution_list = []
            bucket, file_path = split_s3_path(Path(token_distribution_file_list[0]))
            s3_store = S3Store(s3_prefix=os.path.join('s3://', bucket))
            for token_distribution_file in token_distribution_file_list:
                with s3_store.get(token_distribution_file) as f:
                    try:
                        token_distribution_list.append(pd.read_csv(f, delimiter=','))
                    except EmptyDataError:
                        logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', token_distribution_file)
        else:
            token_distribution_list = []
            for file_name in os.listdir(token_distribution_file_dir):
                try:
                    token_distribution_list.append(pd.read_csv(os.path.join(token_distribution_file_dir, str(file_name))))
                except EmptyDataError:
                    logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', file_name)
        if not token_distribution_list:
            raise AssertionError('No scenarios found to simulate!')
        token_distribution_df = pd.concat(token_distribution_list, ignore_index=True)
        token_distribution = token_distribution_df.values.tolist()
        return cast(List[Tuple[str, str]], token_distribution)

    def _get_token_and_log_chunk_on_single_node(self, token_distribution: List[Tuple[str, str]], db_files_path: Path) -> Tuple[List[str], List[str]]:
        """
        Get the list of tokens and the list of logs those tokens are found in restricted to the current node
        :param token_distribution: Full list of all (token, log_file) pairs to be divided among the nodes
        :param db_files_path: Path to the actual db files
        """
        db_files_path_sanitized = safe_path_to_string(db_files_path)
        if not check_s3_path_exists(db_files_path_sanitized):
            raise AssertionError(f'Multinode caching only works in S3, but db_files path given was {db_files_path_sanitized}')
        token_distribution_chunk = chunk_list(token_distribution, self._num_nodes)
        current_chunk = token_distribution_chunk[self._node_rank]
        current_logs_chunk = list({os.path.join(db_files_path_sanitized, f'{pair[1]}.db') for pair in current_chunk})
        current_token_chunk = [pair[0] for pair in current_chunk]
        return (current_token_chunk, current_logs_chunk)

    def _write_token_csv_file(self, scenarios: List[AbstractScenario], token_distribution_file_dir: Union[str, Path]) -> None:
        """
        Writes a csv file of format token,log_name that stores the tokens associated with the given scenarios
        :param scenarios: Scenarios to take token/log pairs from
        :param token_distribution_file_dir: directory to write our csv file to
        """
        token_distribution_file = os.path.join(token_distribution_file_dir, f'{self._node_rank}.csv')
        token_log_pairs = [(scenario.token, scenario.log_name) for scenario in scenarios]
        os.makedirs(token_distribution_file_dir, exist_ok=True)
        token_log_pairs_df = pd.DataFrame(token_log_pairs)
        token_log_pairs_df.to_csv(token_distribution_file, index=False)

    def _get_scenarios_from_list_of_log_files(self, log_db_files: List[str]) -> List[AbstractScenario]:
        """
        Gets the scenarios based on self._cfg, restricted to a list of log files
        :param log_db_files: list of log db files to restrict our search to
        :returns: list of scenarios
        """
        OmegaConf.set_struct(self._cfg, False)
        self._cfg.scenario_builder.db_files = log_db_files
        OmegaConf.set_struct(self._cfg, True)
        scenario_builder = build_scenario_builder(self._cfg)
        scenario_filter = build_scenario_filter(self._cfg.scenario_filter)
        scenarios: List[AbstractScenario] = scenario_builder.get_scenarios(scenario_filter, self._worker)
        return scenarios

    def _get_log_db_files_for_single_node(self) -> List[str]:
        """
        Get the list of log db files to be run on the current node
        :returns: list of log db files
        """
        if self._num_nodes == 1:
            return cast(List[str], self._cfg.scenario_builder.db_files)
        if not check_s3_path_exists(self._cfg.scenario_builder.db_files):
            raise AssertionError(f'DistributedScenarioFilter with multiple nodes only works in S3, but db_files path given was {self._cfg.scenario_builder.db_files}')
        all_files = get_db_filenames_from_load_path(self._cfg.scenario_builder.db_files)
        file_chunks = chunk_list(all_files, self._num_nodes)
        current_chunk = file_chunks[self._node_rank]
        return cast(List[str], current_chunk)

def get_scenarios(self) -> List[AbstractScenario]:
    """
        Get all the scenarios that the current node should process
        :returns: list of scenarios for the current node
        """
    if self._num_nodes == 1 or self._distributed_mode == DistributedMode.SINGLE_NODE:
        logger.info('Building Scenarios in mode %s', DistributedMode.SINGLE_NODE)
        scenario_builder = build_scenario_builder(cfg=self._cfg)
        scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
    elif self._distributed_mode in (DistributedMode.LOG_FILE_BASED, DistributedMode.SCENARIO_BASED):
        logger.info('Getting Log Chunks')
        current_chunk = self._get_log_db_files_for_single_node()
        logger.info('Getting Scenarios From Log Chunk of size %d', len(current_chunk))
        scenarios = self._get_scenarios_from_list_of_log_files(current_chunk)
        if self._distributed_mode == DistributedMode.LOG_FILE_BASED:
            logger.info('Distributed mode is %s, so we are just returning the scenariosfound from log files on the current worker.  There are %d scenarios to processon node %d/%d', DistributedMode.LOG_FILE_BASED, len(scenarios), self._node_rank, self._num_nodes)
            return scenarios
        logger.info('Distributed mode is %s, so we are going to repartition the scenarios we got from the log files to better distribute the work', DistributedMode.SCENARIO_BASED)
        logger.info('Getting repartitioned scenario tokens')
        tokens, log_db_files = self._get_repartition_tokens(scenarios)
        OmegaConf.set_struct(self._cfg, False)
        self._cfg.scenario_filter.scenario_tokens = tokens
        self._cfg.scenario_builder.db_files = log_db_files
        OmegaConf.set_struct(self._cfg, True)
        logger.info('Building repartitioned scenarios')
        scenario_builder = build_scenario_builder(cfg=self._cfg)
        scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
    else:
        raise ValueError(f'Distributed mode must be one of {[x.name for x in fields(DistributedMode)]}, got {self._distributed_mode} instead!')
    scenarios = scenario_builder.get_scenarios(scenario_filter, self._worker)
    return scenarios

def _get_scenarios_from_list_of_log_files(self, log_db_files: List[str]) -> List[AbstractScenario]:
    """
        Gets the scenarios based on self._cfg, restricted to a list of log files
        :param log_db_files: list of log db files to restrict our search to
        :returns: list of scenarios
        """
    OmegaConf.set_struct(self._cfg, False)
    self._cfg.scenario_builder.db_files = log_db_files
    OmegaConf.set_struct(self._cfg, True)
    scenario_builder = build_scenario_builder(self._cfg)
    scenario_filter = build_scenario_filter(self._cfg.scenario_filter)
    scenarios: List[AbstractScenario] = scenario_builder.get_scenarios(scenario_filter, self._worker)
    return scenarios

class TestIoUtils(unittest.TestCase):
    """
    A class to test that the I/O utilities in nuplan_devkit function properly.
    """

    def test_nupath(self) -> None:
        """
        Tests that converting NuPath to strings works properly.
        """
        example_s3_path = NuPath('s3://test-bucket/foo/bar/baz.txt')
        expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
        actual_s3_str = str(example_s3_path)
        self.assertEqual(expected_s3_str, actual_s3_str)
        example_local_path = NuPath('/foo/bar/baz')
        expected_local_str = '/foo/bar/baz'
        actual_local_str = str(example_local_path)
        self.assertEqual(expected_local_str, actual_local_str)

    def test_safe_path_to_string(self) -> None:
        """
        Tests that converting paths to strings safely works properly.
        """
        example_s3_path = Path('s3://test-bucket/foo/bar/baz.txt')
        expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
        actual_s3_str = safe_path_to_string(example_s3_path)
        self.assertEqual(expected_s3_str, actual_s3_str)
        example_local_path = Path('/foo/bar/baz')
        expected_local_str = '/foo/bar/baz'
        actual_local_str = safe_path_to_string(example_local_path)
        self.assertEqual(expected_local_str, actual_local_str)
        example_s3_str_path = 's3://test-bucket/foo/bar/baz.txt'
        expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
        actual_s3_str = safe_path_to_string(example_s3_str_path)
        self.assertEqual(expected_s3_str, actual_s3_str)
        example_local_str_path = '/foo/bar/baz'
        expected_local_str = '/foo/bar/baz'
        actual_local_str = safe_path_to_string(example_local_str_path)
        self.assertEqual(expected_local_str, actual_local_str)

    def test_save_buffer_locally(self) -> None:
        """
        Tests that saving a buffer locally works properly.
        """
        expected_buffer = b'test'
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'local_buffer.bin'
            save_buffer(output_file, expected_buffer)
            with open(output_file, 'rb') as f:
                reconstructed_buffer = f.read()
            self.assertEqual(expected_buffer, reconstructed_buffer)

    def test_save_buffer_s3(self) -> None:
        """
        Tests that saving a buffer to s3 works properly.
        """
        upload_bucket_name = 'ml-caches'
        upload_path = Path('foo/bar/baz.bin')
        uploaded_file_contents: Optional[bytes] = None

        async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
            """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
            nonlocal uploaded_file_contents
            self.assertEqual(upload_bucket_name, s3_bucket)
            self.assertEqual(upload_path, s3_key)
            with open(local_path, 'rb') as f:
                uploaded_file_contents = f.read()
        expected_buffer = b'test'
        with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
            output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
            save_buffer(output_file, expected_buffer)
            self.assertIsNotNone(uploaded_file_contents)
            assert uploaded_file_contents is not None
            self.assertEqual(expected_buffer, uploaded_file_contents)

    def test_save_object_as_pickle_locally(self) -> None:
        """
        Tests that saving a pickled object locally works properly.
        """
        expected_object = {'a': 1, 'b': 2}
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'local.pkl'
            save_object_as_pickle(output_file, expected_object)
            with open(output_file, 'rb') as f:
                reconstructed_object = pickle.load(f)
            self.assertEqual(expected_object, reconstructed_object)

    def test_save_object_as_pickle_s3(self) -> None:
        """
        Tests that saving a pickled object to s3 works properly.
        """
        upload_bucket_name = 'ml-caches'
        upload_path = Path('foo/bar/baz.pkl')
        uploaded_file_contents: Optional[bytes] = None

        async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
            """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
            nonlocal uploaded_file_contents
            self.assertEqual(upload_bucket_name, s3_bucket)
            self.assertEqual(upload_path, s3_key)
            with open(local_path, 'rb') as f:
                uploaded_file_contents = f.read()
        expected_object = {'a': 1, 'b': 2}
        with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
            output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
            save_object_as_pickle(output_file, expected_object)
            self.assertIsNotNone(uploaded_file_contents)
            assert uploaded_file_contents is not None
            reconstructed_object: Dict[str, int] = pickle.loads(uploaded_file_contents)
            self.assertEqual(expected_object, reconstructed_object)

    def test_save_text_locally(self) -> None:
        """
        Tests that saving a text file locally works properly.
        """
        expected_text = 'test_save_text_locally.'
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'local.txt'
            save_text(output_file, expected_text)
            with open(output_file, 'r') as f:
                reconstructed_text = f.read()
            self.assertEqual(expected_text, reconstructed_text)

    def test_save_text_s3(self) -> None:
        """
        Tests that saving a text file to s3 works properly.
        """
        upload_bucket_name = 'ml-caches'
        upload_path = Path('foo/bar/baz.pkl')
        uploaded_file_contents: Optional[str] = None

        async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
            """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
            nonlocal uploaded_file_contents
            self.assertEqual(upload_bucket_name, s3_bucket)
            self.assertEqual(upload_path, s3_key)
            with open(local_path, 'r') as f:
                uploaded_file_contents = f.read()
        expected_text = 'test_save_text_s3.'
        with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
            output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
            save_text(output_file, expected_text)
            self.assertIsNotNone(uploaded_file_contents)
            self.assertEqual(expected_text, uploaded_file_contents)

    def test_read_text_locally(self) -> None:
        """
        Tests that reading a text file locally works properly.
        """
        expected_text = 'some expected text.'
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'read_text_locally.txt'
            with open(output_file, 'w') as f:
                f.write(expected_text)
            reconstructed_text = read_text(output_file)
            self.assertEqual(expected_text, reconstructed_text)

    def test_read_text_from_s3(self) -> None:
        """
        Tests that reading a text file from S3 works properly.
        """
        download_bucket = 'ml-caches'
        download_key = 'my/file/path.txt'
        expected_text = 'some expected text.'
        full_filepath = Path(f's3://{download_bucket}') / download_key

        async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
            """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
            self.assertEqual(Path(download_key), s3_key)
            self.assertEqual(download_bucket, s3_bucket)
            return expected_text.encode('utf-8')
        with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
            reconstructed_text = read_text(full_filepath)
            self.assertEqual(expected_text, reconstructed_text)

    def test_read_pickle_locally(self) -> None:
        """
        Tests that reading a pickle file locally works properly.
        """
        expected_obj = {'foo': 'bar'}
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'read_text_locally.txt'
            with open(output_file, 'wb') as f:
                f.write(pickle.dumps(expected_obj))
            reconstructed_obj = read_pickle(output_file)
            self.assertEqual(expected_obj, reconstructed_obj)

    def test_read_pickle_from_s3(self) -> None:
        """
        Tests that reading a pickle file from S3 works properly.
        """
        download_bucket = 'ml-caches'
        download_key = 'my/file/path.txt'
        expected_obj = {'foo': 'bar'}
        full_filepath = Path(f's3://{download_bucket}') / download_key

        async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
            """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
            self.assertEqual(Path(download_key), s3_key)
            self.assertEqual(download_bucket, s3_bucket)
            return pickle.dumps(expected_obj)
        with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
            reconstructed_obj = read_pickle(full_filepath)
            self.assertEqual(expected_obj, reconstructed_obj)

    def test_read_binary_locally(self) -> None:
        """
        Tests that reading a binary file locally works properly.
        """
        expected_data = bytes([1, 2, 3, 4, 5])
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'read_text_locally.txt'
            with open(output_file, 'wb') as f:
                f.write(expected_data)
            reconstructed_data = read_binary(output_file)
            self.assertEqual(expected_data, reconstructed_data)

    def test_read_binary_from_s3(self) -> None:
        """
        Tests that reading a binary file from S3 works properly.
        """
        download_bucket = 'ml-caches'
        download_key = 'my/file/path.data'
        expected_data = bytes([1, 2, 3, 4, 5])
        full_filepath = Path(f's3://{download_bucket}') / download_key

        async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
            """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
            self.assertEqual(Path(download_key), s3_key)
            self.assertEqual(download_bucket, s3_bucket)
            return expected_data
        with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
            reconstructed_data = read_binary(full_filepath)
            self.assertEqual(expected_data, reconstructed_data)

    def test_path_exists_locally(self) -> None:
        """
        Tests that path_exists works for local files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            file_to_create = tmp_dir_path / 'existing.txt'
            file_to_not_create = tmp_dir_path / 'not_existing.txt'
            with open(file_to_create, 'w') as f:
                f.write('some irrelevant text.')
            self.assertTrue(path_exists(file_to_create))
            self.assertFalse(path_exists(file_to_not_create))
            self.assertTrue(path_exists(tmp_dir_path, include_directories=True))
            self.assertFalse(path_exists(tmp_dir_path, include_directories=False))

    def test_path_exists_s3(self) -> None:
        """
        Tests that path_exists works for s3 files.
        """
        test_bucket = 'ml-caches'
        test_parent_dir = 'my/file/that'
        test_existing_file = f'{test_parent_dir}/exists.txt'
        test_non_existing_file = f'{test_parent_dir}/does_not_exist.txt'
        test_dir_path = Path(f's3://{test_bucket}') / test_parent_dir
        test_existing_path = Path(f's3://{test_bucket}') / test_existing_file
        test_non_existing_path = Path(f's3://{test_bucket}') / test_non_existing_file

        async def patch_check_s3_object_exists_async(s3_key: Path, s3_bucket: str) -> bool:
            """
            Patches the check_s3_object_exists_async method.
            :param key: The s3 key to check.
            :param bucket: The s3 bucket to check.
            :return: The mocked return value.
            """
            self.assertEqual(test_bucket, s3_bucket)
            if str(s3_key) == test_existing_file:
                return True
            elif str(s3_key) in [test_non_existing_file, test_parent_dir]:
                return False
            self.fail(f'Unexpected path passed to check_s3_object_exists patch: {s3_key}')

        async def patch_check_s3_path_exists_async(s3_path: str) -> bool:
            """
            Patches the check_s3_object_exists_async method.
            :param s3_path: The s3 path to check.
            :return: The mocked return value.
            """
            if s3_path in [safe_path_to_string(test_existing_path), safe_path_to_string(test_dir_path)]:
                return True
            elif s3_path == safe_path_to_string(test_non_existing_path):
                return False
            self.fail(f'Unexpected path passed to check_s3_path_exists patch: {s3_path}')
        with patch_with_validation('nuplan.common.utils.io_utils.check_s3_object_exists_async', patch_check_s3_object_exists_async), patch_with_validation('nuplan.common.utils.io_utils.check_s3_path_exists_async', patch_check_s3_path_exists_async):
            self.assertTrue(path_exists(test_existing_path))
            self.assertFalse(path_exists(test_non_existing_path))
            self.assertTrue(path_exists(test_dir_path, include_directories=True))
            self.assertFalse(path_exists(test_dir_path, include_directories=False))

    def test_list_files_in_directory_locally(self) -> None:
        """
        Tests that list_files_in_directory works for local files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            self.assertEqual(list_files_in_directory(tmp_dir_path), [])
            test_file_contents = {'a.txt': 'test file a.', 'b.txt': 'test file b.'}
            for filename, contents in test_file_contents.items():
                with open(tmp_dir_path / filename, 'w') as f:
                    f.write(contents)
            output_files_in_directory = list_files_in_directory(tmp_dir_path)
            self.assertEqual(len(output_files_in_directory), len(test_file_contents))
            for output_filepath in output_files_in_directory:
                self.assertIn(output_filepath.name, test_file_contents)

    def test_list_files_in_directory_s3(self) -> None:
        """
        Tests that list_files_in_directory works for s3.
        """
        test_bucket = 'ml-caches'
        test_directory_key = Path('test_dir')
        test_directory_s3_path = Path(f's3://{test_bucket}/{test_directory_key}')
        test_files_in_s3 = ['a.txt', 'b.txt']
        expected_files = [Path(f'{test_directory_key}/{filename}') for filename in test_files_in_s3]
        expected_s3_paths = [Path(f's3://{test_bucket}') / filename for filename in expected_files]

        async def patch_list_files_in_s3_directory_async(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
            """
            Patches the list_files_in_s3_directory_async method.
            :param key: The s3 key of the directory.
            :param bucket: The s3 bucket of the directory.
            :param filter_suffix: Unused.
            :return: The mocked return value.
            """
            self.assertEqual(test_bucket, s3_bucket)
            self.assertEqual(test_directory_key, s3_key)
            return expected_files
        with patch_with_validation('nuplan.common.utils.io_utils.list_files_in_s3_directory_async', patch_list_files_in_s3_directory_async):
            output_filepaths = list_files_in_directory(test_directory_s3_path)
            self.assertEqual(output_filepaths, expected_s3_paths)

    def test_delete_file_locally(self) -> None:
        """
        Tests that delete_file works for local files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            test_file_contents = {'a.txt': 'test file a.', 'b.txt': 'test file b.'}
            test_file_paths = [tmp_dir_path / filename for filename in test_file_contents]
            for filename, contents in test_file_contents.items():
                with open(tmp_dir_path / filename, 'w') as f:
                    f.write(contents)
            self.assertEqual(set(tmp_dir_path.iterdir()), set(test_file_paths))
            for filename in test_file_contents:
                filepath = tmp_dir_path / filename
                delete_file(filepath)
                self.assertNotIn(filepath, tmp_dir_path.iterdir())
            self.assertEqual(len(list(tmp_dir_path.iterdir())), 0)
            with self.assertRaises(ValueError):
                delete_file(tmp_dir_path)

    def test_delete_file_s3(self) -> None:
        """
        Tests that delete_file works for s3.
        """
        test_bucket = 'ml-caches'
        test_directory_key = Path('test_dir')
        test_directory_s3_path = Path(f's3://{test_bucket}/{test_directory_key}')
        test_files_in_s3 = {'a.txt', 'b.txt'}

        def get_s3_key(filename: str) -> Path:
            """
            Turns a filename into an s3 key.
            """
            return Path(f'{test_directory_key}/{filename}')

        def list_s3_keys() -> List[Path]:
            """
            Lists the keys in s3.
            :return: S3 keys in the mocked test directory.
            """
            return [get_s3_key(filename) for filename in test_files_in_s3]

        async def patch_list_files_in_s3_directory_async(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
            """
            Patches the list_files_in_s3_directory_async method.
            :param key: The s3 key of the directory.
            :param bucket: The s3 bucket of the directory.
            :param filter_suffix: Unused.
            :return: The mocked return value.
            """
            self.assertEqual(test_bucket, s3_bucket)
            self.assertEqual(test_directory_key, s3_key)
            return list_s3_keys()

        async def patch_delete_file_from_s3_async(s3_key: Path, s3_bucket: str) -> None:
            """
            Patches the delete_file_from_s3_async method.
            :param s3_key: The s3 key to delete.
            :param s3_bucket: The s3 bucket.
            """
            nonlocal test_files_in_s3
            self.assertEqual(test_bucket, s3_bucket)
            self.assertEqual(test_directory_key, s3_key.parent)
            self.assertIn(s3_key.name, test_files_in_s3)
            test_files_in_s3.remove(s3_key.name)
        with patch_with_validation('nuplan.common.utils.io_utils.list_files_in_s3_directory_async', patch_list_files_in_s3_directory_async), patch_with_validation('nuplan.common.utils.io_utils.delete_file_from_s3_async', patch_delete_file_from_s3_async):
            initial_s3_keys = list_s3_keys()
            for filename in test_files_in_s3:
                self.assertIn(get_s3_key(filename), initial_s3_keys)
            for filename in set(test_files_in_s3):
                s3_path = test_directory_s3_path / filename
                delete_file(s3_path)
                self.assertNotIn(get_s3_key(filename), list_s3_keys())

def test_delete_file_s3(self) -> None:
    """
        Tests that delete_file works for s3.
        """
    test_bucket = 'ml-caches'
    test_directory_key = Path('test_dir')
    test_directory_s3_path = Path(f's3://{test_bucket}/{test_directory_key}')
    test_files_in_s3 = {'a.txt', 'b.txt'}

    def get_s3_key(filename: str) -> Path:
        """
            Turns a filename into an s3 key.
            """
        return Path(f'{test_directory_key}/{filename}')

    def list_s3_keys() -> List[Path]:
        """
            Lists the keys in s3.
            :return: S3 keys in the mocked test directory.
            """
        return [get_s3_key(filename) for filename in test_files_in_s3]

    async def patch_list_files_in_s3_directory_async(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
        """
            Patches the list_files_in_s3_directory_async method.
            :param key: The s3 key of the directory.
            :param bucket: The s3 bucket of the directory.
            :param filter_suffix: Unused.
            :return: The mocked return value.
            """
        self.assertEqual(test_bucket, s3_bucket)
        self.assertEqual(test_directory_key, s3_key)
        return list_s3_keys()

    async def patch_delete_file_from_s3_async(s3_key: Path, s3_bucket: str) -> None:
        """
            Patches the delete_file_from_s3_async method.
            :param s3_key: The s3 key to delete.
            :param s3_bucket: The s3 bucket.
            """
        nonlocal test_files_in_s3
        self.assertEqual(test_bucket, s3_bucket)
        self.assertEqual(test_directory_key, s3_key.parent)
        self.assertIn(s3_key.name, test_files_in_s3)
        test_files_in_s3.remove(s3_key.name)
    with patch_with_validation('nuplan.common.utils.io_utils.list_files_in_s3_directory_async', patch_list_files_in_s3_directory_async), patch_with_validation('nuplan.common.utils.io_utils.delete_file_from_s3_async', patch_delete_file_from_s3_async):
        initial_s3_keys = list_s3_keys()
        for filename in test_files_in_s3:
            self.assertIn(get_s3_key(filename), initial_s3_keys)
        for filename in set(test_files_in_s3):
            s3_path = test_directory_s3_path / filename
            delete_file(s3_path)
            self.assertNotIn(get_s3_key(filename), list_s3_keys())

def list_s3_keys() -> List[Path]:
    """
            Lists the keys in s3.
            :return: S3 keys in the mocked test directory.
            """
    return [get_s3_key(filename) for filename in test_files_in_s3]

class TestPatch(unittest.TestCase):
    """
    A class to test the patch utils.
    """

    def test_patch_with_validation_correct_patch(self) -> None:
        """
        Tests that the patch works with a correct patch.
        """

        def correct_patch(x: int) -> int:
            """
            A correct patch for the base_method.
            :param x: The input.
            :return: The output.
            """
            return x + 1
        with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', correct_patch):
            result = complex_method(x=1, y=2)
            self.assertEqual(4, result)

    def test_patch_with_validation_correct_patch_direct(self) -> None:
        """
        Tests that the patch works with a correct patch that is directly provided.
        """

        def correct_patch(x: int) -> int:
            """
            A correct patch for the base_method.
            :param x: The input.
            :return: The output.
            """
            return x + 1
        with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', correct_patch, override_function=swappable_with_base_method):
            result = complex_method(x=1, y=2)
            self.assertEqual(4, result)

    def test_patch_raises_with_incorrect_patch(self) -> None:
        """
        Tests that an incorrect patch causes an error to be rasied.
        """

        def incorrect_patch(x: float) -> int:
            """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
            return int(x) + 1
        with self.assertRaises(TypeError):
            with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', incorrect_patch):
                _ = complex_method(x=1, y=2)

    def test_patch_raises_with_incorrect_patch_direct(self) -> None:
        """
        Tests that an incorrect patch causes an error to be rasied.
        """

        def incorrect_patch(x: float) -> int:
            """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
            return int(x) + 1
        with self.assertRaises(TypeError):
            with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', incorrect_patch, override_function=swappable_with_base_method):
                _ = complex_method(x=1, y=2)

def test_patch_with_validation_correct_patch(self) -> None:
    """
        Tests that the patch works with a correct patch.
        """

    def correct_patch(x: int) -> int:
        """
            A correct patch for the base_method.
            :param x: The input.
            :return: The output.
            """
        return x + 1
    with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', correct_patch):
        result = complex_method(x=1, y=2)
        self.assertEqual(4, result)

def test_patch_with_validation_correct_patch_direct(self) -> None:
    """
        Tests that the patch works with a correct patch that is directly provided.
        """

    def correct_patch(x: int) -> int:
        """
            A correct patch for the base_method.
            :param x: The input.
            :return: The output.
            """
        return x + 1
    with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', correct_patch, override_function=swappable_with_base_method):
        result = complex_method(x=1, y=2)
        self.assertEqual(4, result)

def test_patch_raises_with_incorrect_patch(self) -> None:
    """
        Tests that an incorrect patch causes an error to be rasied.
        """

    def incorrect_patch(x: float) -> int:
        """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
        return int(x) + 1
    with self.assertRaises(TypeError):
        with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', incorrect_patch):
            _ = complex_method(x=1, y=2)

def test_patch_raises_with_incorrect_patch_direct(self) -> None:
    """
        Tests that an incorrect patch causes an error to be rasied.
        """

    def incorrect_patch(x: float) -> int:
        """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
        return int(x) + 1
    with self.assertRaises(TypeError):
        with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', incorrect_patch, override_function=swappable_with_base_method):
            _ = complex_method(x=1, y=2)

class mock_async_s3(ContextDecorator):
    """
    Class for mocking S3 that can be used as both a context manager, and function decorator.
    Only works in/on a synchronous function.
    """

    def __init__(self) -> None:
        """
        Context manager setup.
        """
        super().__init__()
        self.patch_special_case_error = patch('aiobotocore.handlers._looks_like_special_case_error', _looks_like_special_case_error_patch)
        self.patch_convert_to_response = patch('aiobotocore.endpoint.convert_to_response_dict', convert_to_response_dict_patch)
        self.s3_mocker = mock_s3()

    def __enter__(self) -> Type['mock_async_s3']:
        """
        Context manager enter.
        """
        self.patch_special_case_error.start()
        self.patch_convert_to_response.start()
        self.s3_mocker.start()
        return cast(Type['mock_async_s3'], self)

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], exc_traceback: Optional[TracebackType]) -> None:
        """
        Context manager exit.
        Note that we don't have to handle the incoming exception, by returning None, it will be re-raised.
        :param exc_type: Type of any exception that occured.
        :param exc_value: Exception that occured, or None.
        :param traceback: Traceback if an exception occured.
        :return: Always None, so exceptions are never swallowed.
        """
        self.patch_special_case_error.stop()
        self.patch_convert_to_response.stop()
        self.s3_mocker.stop()
        return None

def __enter__(self) -> Type['mock_async_s3']:
    """
        Context manager enter.
        """
    self.patch_special_case_error.start()
    self.patch_convert_to_response.start()
    self.s3_mocker.start()
    return cast(Type['mock_async_s3'], self)

def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], exc_traceback: Optional[TracebackType]) -> None:
    """
        Context manager exit.
        Note that we don't have to handle the incoming exception, by returning None, it will be re-raised.
        :param exc_type: Type of any exception that occured.
        :param exc_value: Exception that occured, or None.
        :param traceback: Traceback if an exception occured.
        :return: Always None, so exceptions are never swallowed.
        """
    self.patch_special_case_error.stop()
    self.patch_convert_to_response.stop()
    self.s3_mocker.stop()
    return None

@dataclass(frozen=True)
class WorkerResources:
    """Data class to indicate resources used by workers."""
    number_of_nodes: int
    number_of_gpus_per_node: int
    number_of_cpus_per_node: int

    @property
    def number_of_threads(self) -> int:
        """
        :return: the number of available threads across all nodes.
        """
        return self.number_of_nodes * self.number_of_cpus_per_node

    @staticmethod
    def current_node_cpu_count() -> int:
        """
        :return: the number of logical cores on the current machine.
        """
        return cpu_count(logical=True)

@staticmethod
def current_node_cpu_count() -> int:
    """
        :return: the number of logical cores on the current machine.
        """
    return cpu_count(logical=True)

class WorkerPool(abc.ABC):
    """
    This class executed function on list of arguments. This can either be distributed/parallel or sequential worker.
    """

    def __init__(self, config: WorkerResources):
        """
        Initialize worker with resource description.
        :param config: setup of this worker.
        """
        self.config = config
        if self.config.number_of_threads < 1:
            raise RuntimeError(f'Number of threads can not be 0, and it is {self.config.number_of_threads}!')
        logger.info(f'Worker: {self.__class__.__name__}')
        logger.info(f'{self}')

    def map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """
        Run function with arguments from item_lists, this function will make sure all arguments have the same
        number of elements.
        :param task: function to be run.
        :param item_lists: arguments to the function.
        :param verbose: Whether to increase logger verbosity.
        :return: type from the fn.
        """
        max_size, aligned_item_lists = align_size_of_arguments(*item_lists)
        if verbose:
            logger.info(f'Submitting {max_size} tasks!')
        return self._map(task, *aligned_item_lists, verbose=verbose)

    @abc.abstractmethod
    def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """
        Run function with arguments from item_lists. This function can assume that all the args in item_lists have
        the same number of elements.
        :param fn: function to be run.
        :param item_lists: arguments to the function.
        :param number_of_elements: number of calls to the function.
        :return: type from the fn.
        """

    @abc.abstractmethod
    def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
        """
        Submit a task to the worker.
        :param task: to be submitted.
        :param args: arguments for the task.
        :param kwargs: keyword arguments for the task.
        :return: future.
        """
        pass

    @property
    def number_of_threads(self) -> int:
        """
        :return: the number of available threads across all nodes.
        """
        return self.config.number_of_threads

    def __str__(self) -> str:
        """
        :return: string with information about this worker.
        """
        return f'Number of nodes: {self.config.number_of_nodes}\nNumber of CPUs per node: {self.config.number_of_cpus_per_node}\nNumber of GPUs per node: {self.config.number_of_gpus_per_node}\nNumber of threads across all nodes: {self.config.number_of_threads}'

def map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
    """
        Run function with arguments from item_lists, this function will make sure all arguments have the same
        number of elements.
        :param task: function to be run.
        :param item_lists: arguments to the function.
        :param verbose: Whether to increase logger verbosity.
        :return: type from the fn.
        """
    max_size, aligned_item_lists = align_size_of_arguments(*item_lists)
    if verbose:
        logger.info(f'Submitting {max_size} tasks!')
    return self._map(task, *aligned_item_lists, verbose=verbose)

def initialize_ray(master_node_ip: Optional[str]=None, threads_per_node: Optional[int]=None, local_mode: bool=False, log_to_driver: bool=True, use_distributed: bool=False) -> WorkerResources:
    """
    Initialize ray worker.
    ENV_VAR_MASTER_NODE_IP="master node IP".
    ENV_VAR_MASTER_NODE_PASSWORD="password to the master node".
    ENV_VAR_NUM_NODES="number of nodes available".
    :param master_node_ip: if available, ray will connect to remote cluster.
    :param threads_per_node: Number of threads to use per node.
    :param log_to_driver: If true, the output from all of the worker
            processes on all nodes will be directed to the driver.
    :param local_mode: If true, the code will be executed serially. This
            is useful for debugging.
    :param use_distributed: If true, and the env vars are available,
            ray will launch in distributed mode
    :return: created WorkerResources.
    """
    env_var_master_node_ip = 'ip_head'
    env_var_master_node_password = 'redis_password'
    env_var_num_nodes = 'num_nodes'
    number_of_cpus_per_node = threads_per_node if threads_per_node else cpu_count(logical=True)
    number_of_gpus_per_node = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if not number_of_gpus_per_node:
        logger.info('Not using GPU in ray')
    if master_node_ip and use_distributed:
        logger.info(f'Connecting to cluster at: {master_node_ip}!')
        ray.init(address=f'ray://{master_node_ip}:10001', local_mode=local_mode, log_to_driver=log_to_driver)
        number_of_nodes = 1
    elif env_var_master_node_ip in os.environ and use_distributed:
        number_of_nodes = int(os.environ[env_var_num_nodes])
        master_node_ip = os.environ[env_var_master_node_ip].split(':')[0]
        redis_password = os.environ[env_var_master_node_password].split(':')[0]
        logger.info(f'Connecting as part of a cluster at: {master_node_ip} with password: {redis_password}!')
        ray.init(address='auto', _node_ip_address=master_node_ip, _redis_password=redis_password, log_to_driver=log_to_driver, local_mode=local_mode)
    else:
        number_of_nodes = 1
        logger.info('Starting ray local!')
        ray.init(num_cpus=number_of_cpus_per_node, dashboard_host='0.0.0.0', local_mode=local_mode, log_to_driver=log_to_driver)
    return WorkerResources(number_of_nodes=number_of_nodes, number_of_cpus_per_node=number_of_cpus_per_node, number_of_gpus_per_node=number_of_gpus_per_node)

def chunk_list(input_list: List[Any], num_chunks: Optional[int]=None) -> List[List[Any]]:
    """
    Chunks a list to equal sized lists. The size of the last list might be truncated.
    :param input_list: List to be chunked.
    :param num_chunks: Number of chunks, equals to the number of cores if set to None.
    :return: List of equal sized lists.
    """
    num_chunks = num_chunks if num_chunks else cpu_count(logical=True)
    chunks = np.array_split(input_list, num_chunks)
    return [chunk.tolist() for chunk in chunks if len(chunk) != 0]

class STRTreeOccupancyMap(OccupancyMap):
    """
    OccupancyMap using an SR-tree to support efficient get-nearest queries.
    """

    def __init__(self, geom_map: GeometryMap):
        """
        Constructor of STRTreeOccupancyMap.
        :param geom_map: underlying geometries for occupancy map.
        """
        self._geom_map: GeometryMap = geom_map

    def get_nearest_entry_to(self, geometry_id: str) -> Tuple[str, Geometry, float]:
        """Inherited, see superclass."""
        assert self.contains(geometry_id), 'This occupancy map does not contain given geometry id'
        strtree, index_by_id = self._build_strtree(geometry_id)
        nearest_index = strtree.nearest(self.get(geometry_id))
        nearest = strtree.geometries.take(nearest_index)
        p1, p2 = nearest_points(self.get(geometry_id), nearest)
        return (index_by_id[id(nearest)], nearest, p1.distance(p2))

    def intersects(self, geometry: Geometry) -> OccupancyMap:
        """Inherited, see superclass."""
        strtree, index_by_id = self._build_strtree()
        indices = strtree.query(geometry)
        return STRTreeOccupancyMap({index_by_id[id(geom)]: geom for geom in strtree.geometries.take(indices) if geom.intersects(geometry)})

    def insert(self, geometry_id: str, geometry: Geometry) -> None:
        """Inherited, see superclass."""
        self._geom_map[geometry_id] = geometry

    def get(self, geometry_id: str) -> Geometry:
        """Inherited, see superclass."""
        return self._geom_map[geometry_id]

    def set(self, geometry_id: str, geometry: Geometry) -> None:
        """Inherited, see superclass."""
        self._geom_map[geometry_id] = geometry

    def get_all_ids(self) -> List[str]:
        """Inherited, see superclass."""
        return list(self._geom_map.keys())

    def get_all_geometries(self) -> List[Geometry]:
        """Inherited, see superclass."""
        return list(self._geom_map.values())

    @property
    def size(self) -> int:
        """Inherited, see superclass."""
        return len(self._geom_map)

    def is_empty(self) -> bool:
        """Inherited, see superclass."""
        return not self._geom_map

    def contains(self, geometry_id: str) -> bool:
        """Inherited, see superclass."""
        return geometry_id in self._geom_map

    def remove(self, geometry_ids: List[str]) -> None:
        """Remove geometries from the occupancy map by ids."""
        for id in geometry_ids:
            assert id in self._geom_map, 'Geometry does not exist in occupancy map'
            self._geom_map.pop(id)

    def _get_other_geometries(self, ignore_id: str) -> GeometryMap:
        """
        Returns all geometries as except for one specified by ignore_id

        :param ignore_id: the key corresponding to the geometry to be skipped
        :return: GeometryMap
        """
        return {geom_id: geom for geom_id, geom in self._geom_map.items() if geom_id not in ignore_id}

    def _build_strtree(self, ignore_id: Optional[str]=None) -> Tuple[STRtree, Dict[int, str]]:
        """
        Constructs an STRTree from the geometries stored in the geometry map. Additionally, returns a index-id
        mapping to the original keys of the geometries. Has the option to build a tree omitting on geometry
        :param ignore_id: the key corresponding to the geometry to be skipped
        :return: STRTree containing the values of _geom_map, index mapping to the original keys
        """
        if ignore_id is not None:
            temp_geom_map = self._get_other_geometries(ignore_id)
        else:
            temp_geom_map = self._geom_map
        strtree = STRtree(list(temp_geom_map.values()))
        index_by_id = {id(geom): geom_id for geom_id, geom in temp_geom_map.items()}
        return (strtree, index_by_id)

def remove(self, geometry_ids: List[str]) -> None:
    """Remove geometries from the occupancy map by ids."""
    for id in geometry_ids:
        assert id in self._geom_map, 'Geometry does not exist in occupancy map'
        self._geom_map.pop(id)

class OccupancyMapTests(unittest.TestCase):
    """Tests implementation of OccupancyMap"""

    def setUp(self) -> None:
        """Test setup"""
        self.p1 = Polygon([(0, 0), (0, 2), (3, 2), (3, 0)])
        self.p2 = Polygon([(2, 0), (2, 4), (3, 4), (3, 0)])
        self.p3 = Polygon([(4, 0), (4, 2), (5, 2), (5, 0)])
        self.p4 = Polygon([(0, 4), (0, 5), (1.5, 5), (1.5, 4)])
        self.l1 = LineString([(0, 3), (4, 3), (4, 1)])

    def test_intersects_polygon(self):
        """Tests polygon-polygon intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.p2)
            assert not intersection.is_empty()
            intersection = occupancy_map.intersects(self.p3)
            assert intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_intersects_linestring(self):
        """Tests polygon-linestring intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.l1)
            assert intersection.is_empty()
            occupancy_map.insert('2', self.p2)
            intersection = occupancy_map.intersects(self.l1)
            assert not intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_intersects_linestring_buffered(self):
        """Tests polygon-buffered linestring intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
            assert intersection.is_empty()
            occupancy_map.insert('4', self.p4.buffer(0.5, cap_style=2))
            intersection = occupancy_map.intersects(self.l1.buffer(0.1, cap_style=2))
            assert intersection.is_empty()
            occupancy_map.insert('2', self.p2)
            intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
            assert not intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_insert_get_set(self):
        """Tests the expected behavior of get and set"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            assert occupancy_map.size == 1
            occupancy_map.insert('2', self.p3)
            assert occupancy_map.size == 2
            assert self.p3 == occupancy_map.get('2')
            occupancy_map.set('2', self.p2)
            assert self.p2 == occupancy_map.get('2')
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_get_nearest_entry(self):
        """Tests expected behavior of get_nearest_entry"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
        strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

        def test(occupancy_map: OccupancyMap) -> None:
            nearest_id, nearest_polygon, distance = occupancy_map.get_nearest_entry_to('0')
            self.assertEqual(nearest_id, '2')
            self.assertEqual(nearest_polygon, self.p4)
            self.assertEqual(distance, 0.5)
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_get_all(self):
        """Tests the expected behavior of get_all_ids"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
        strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

        def test(occupancy_map: OccupancyMap) -> None:
            ids = occupancy_map.get_all_ids()
            assert set(ids) == {'0', '1', '2'}
            assert set(ids) != {'0', '1', '3'}
            geoms = occupancy_map.get_all_geometries()
            for actual, expect in zip(geoms, [self.p2, self.p3, self.p4]):
                assert actual == expect
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

def test_intersects_polygon(self):
    """Tests polygon-polygon intersections correctness"""
    gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
    strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

    def test(occupancy_map: OccupancyMap) -> None:
        intersection = occupancy_map.intersects(self.p2)
        assert not intersection.is_empty()
        intersection = occupancy_map.intersects(self.p3)
        assert intersection.is_empty()
    test(gp_occupancy_map)
    test(strtree_occupancy_map)

def test_intersects_linestring(self):
    """Tests polygon-linestring intersections correctness"""
    gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
    strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

    def test(occupancy_map: OccupancyMap) -> None:
        intersection = occupancy_map.intersects(self.l1)
        assert intersection.is_empty()
        occupancy_map.insert('2', self.p2)
        intersection = occupancy_map.intersects(self.l1)
        assert not intersection.is_empty()
    test(gp_occupancy_map)
    test(strtree_occupancy_map)

def test_intersects_linestring_buffered(self):
    """Tests polygon-buffered linestring intersections correctness"""
    gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
    strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

    def test(occupancy_map: OccupancyMap) -> None:
        intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
        assert intersection.is_empty()
        occupancy_map.insert('4', self.p4.buffer(0.5, cap_style=2))
        intersection = occupancy_map.intersects(self.l1.buffer(0.1, cap_style=2))
        assert intersection.is_empty()
        occupancy_map.insert('2', self.p2)
        intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
        assert not intersection.is_empty()
    test(gp_occupancy_map)
    test(strtree_occupancy_map)

def test_insert_get_set(self):
    """Tests the expected behavior of get and set"""
    gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
    strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

    def test(occupancy_map: OccupancyMap) -> None:
        assert occupancy_map.size == 1
        occupancy_map.insert('2', self.p3)
        assert occupancy_map.size == 2
        assert self.p3 == occupancy_map.get('2')
        occupancy_map.set('2', self.p2)
        assert self.p2 == occupancy_map.get('2')
    test(gp_occupancy_map)
    test(strtree_occupancy_map)

def test_get_nearest_entry(self):
    """Tests expected behavior of get_nearest_entry"""
    gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
    strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

    def test(occupancy_map: OccupancyMap) -> None:
        nearest_id, nearest_polygon, distance = occupancy_map.get_nearest_entry_to('0')
        self.assertEqual(nearest_id, '2')
        self.assertEqual(nearest_polygon, self.p4)
        self.assertEqual(distance, 0.5)
    test(gp_occupancy_map)
    test(strtree_occupancy_map)

def test_get_all(self):
    """Tests the expected behavior of get_all_ids"""
    gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
    strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

    def test(occupancy_map: OccupancyMap) -> None:
        ids = occupancy_map.get_all_ids()
        assert set(ids) == {'0', '1', '2'}
        assert set(ids) != {'0', '1', '3'}
        geoms = occupancy_map.get_all_geometries()
        for actual, expect in zip(geoms, [self.p2, self.p3, self.p4]):
            assert actual == expect
    test(gp_occupancy_map)
    test(strtree_occupancy_map)

class TestSimulationBufferInitialization(unittest.TestCase):
    """
    A class to test the simulation buffer initialization
    """

    def _test_simulation_buffer(self, time_step: float, simulation_history_buffer_duration: float) -> None:
        """
        Test the simulation buffer duration is equal or greater than simulation_history_buffer_duration.
        :param time_step: [s] The time interval of the simulation buffer.
        :param simulation_history_buffer_duration: [s] The requested simulation buffer duration.
        """
        scenario = MockAbstractScenario(number_of_past_iterations=200, time_step=time_step)
        sim_manager = StepSimulationTimeController(scenario)
        observation = TracksObservation(scenario)
        controller = PerfectTrackingController(scenario)
        setup = SimulationSetup(time_controller=sim_manager, observations=observation, ego_controller=controller, scenario=scenario)
        stepper = Simulation(simulation_setup=setup, callback=MultiCallback([]), simulation_history_buffer_duration=simulation_history_buffer_duration)
        stepper.initialize()
        simulation_buffer = stepper.history_buffer
        self.assertGreaterEqual(simulation_buffer.duration, simulation_history_buffer_duration)

    @settings(deadline=1000)
    @given(time_step=st.floats(min_value=0.05, max_value=1), simulation_history_buffer_duration=st.floats(min_value=1.0, max_value=10.0))
    @example(time_step=0.5, simulation_history_buffer_duration=2.0)
    def test_simulation_buffer(self, time_step: float, simulation_history_buffer_duration: float) -> None:
        """Test the simulation buffer initialization."""
        if simulation_history_buffer_duration % time_step > 1e-06:
            return
        if time_step > simulation_history_buffer_duration:
            with self.assertRaises(ValueError):
                self._test_simulation_buffer(time_step, simulation_history_buffer_duration)
        else:
            self._test_simulation_buffer(time_step, simulation_history_buffer_duration)

@settings(deadline=1000)
@given(time_step=st.floats(min_value=0.05, max_value=1), simulation_history_buffer_duration=st.floats(min_value=1.0, max_value=10.0))
@example(time_step=0.5, simulation_history_buffer_duration=2.0)
def test_simulation_buffer(self, time_step: float, simulation_history_buffer_duration: float) -> None:
    """Test the simulation buffer initialization."""
    if simulation_history_buffer_duration % time_step > 1e-06:
        return
    if time_step > simulation_history_buffer_duration:
        with self.assertRaises(ValueError):
            self._test_simulation_buffer(time_step, simulation_history_buffer_duration)
    else:
        self._test_simulation_buffer(time_step, simulation_history_buffer_duration)

class RemotePlanner(AbstractPlanner):
    """
    Remote planner delegates computation of trajectories to a docker container, with which communicates through
    grpc.
    """

    def __init__(self, submission_container_manager: Optional[SubmissionContainerManager]=None, submission_image: Optional[str]=None, container_name: Optional[str]=None, compute_trajectory_timeout: float=1) -> None:
        """
        Prepares the remote container for planning.
        :param submission_container_manager: Optional manager, if provided a container will be started by RemotePlanner
        :param submission_image: Docker image name for the submission_container_factory
        :param container_name: Name to assign to the submission container
        :param compute_trajectory_timeout: Timeout for computation of trajectory.
        """
        if submission_container_manager:
            missing_parameter_message = 'Parameters for SubmissionContainer are missing!'
            assert submission_image, missing_parameter_message
            assert container_name, missing_parameter_message
            self.port = None
        else:
            self.port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
        self.submission_container_manager = submission_container_manager
        self.submission_image = submission_image
        self.container_name = container_name
        self._channel = None
        self._stub = None
        self.serialized_observation: Optional[List[bytes]] = None
        self.serialized_state: Optional[List[bytes]] = None
        self.sample_interval: Optional[float] = None
        self._compute_trajectory_timeout = compute_trajectory_timeout

    def __reduce__(self) -> Tuple[Type[RemotePlanner], Tuple[Optional[SubmissionContainerManager], Optional[str], Optional[str]]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class
        """
        return (self.__class__, (self.submission_container_manager, self.submission_image, self.container_name))

    def name(self) -> str:
        """Inherited, see superclass."""
        return 'RemotePlanner'

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    @staticmethod
    def _planner_initializations_to_message(initialization: PlannerInitialization) -> chpb.PlannerInitializationLight:
        """
        Converts a PlannerInitialization to the message specified in the protocol files.
        :param initialization: The initialization parameters for the planner
        :return: A initialization message
        """
        try:
            mission_goal = proto_se2_from_se2(initialization.mission_goal)
        except AttributeError as e:
            logger.error('Mission goal was None!')
            raise e
        planner_initialization = chpb.PlannerInitializationLight(route_roadblock_ids=initialization.route_roadblock_ids, mission_goal=mission_goal, map_name=initialization.map_api.map_name)
        return planner_initialization

    def initialize(self, initialization: PlannerInitialization, timeout: float=5) -> None:
        """
        Creates the container manager, and runs the specified docker image. The communication port is created using
        the PID from the ray worker. Sends a request to initialize the remote planner.
        :param initialization: List of PlannerInitialization objects
        :param timeout: for planner initialization
        """
        if self.submission_container_manager:
            submission_container = try_n_times(self.submission_container_manager.get_submission_container, [self.submission_image, self.container_name, find_free_port_number()], {}, (docker.errors.APIError,), max_tries=10)
            self.port = submission_container.port
            submission_container.start()
            submission_container.wait_until_running(timeout=5)
        self._channel = grpc.insecure_channel(f'{NETWORK}:{self.port}')
        self._stub = chpb_grpc.DetectionTracksChallengeStub(self._channel)
        logger.info('Client sending planner initialization request...')
        planner_initializations_message = self._planner_initializations_to_message(initialization)
        logger.info(f'Trying to communicate on port {NETWORK}:{self.port}')
        try:
            _, _ = keep_trying(self._stub.InitializePlanner, [planner_initializations_message], {}, errors=(grpc.RpcError,), timeout=timeout)
        except Exception as e:
            submission_logger.error('Planner initialization failed!')
            submission_logger.error(e)
            raise e
        logger.info('Planner initialized!')

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Computes the ego vehicle trajectory.
        :param current_input: Planner input for which trajectory should be computed
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logger.debug('Client sending planner input: %s' % current_input)
        trajectory = self._compute_trajectory(self._stub, current_input=current_input)
        return trajectory

    def _compute_trajectory(self, stub: chpb_grpc.DetectionTracksChallengeStub, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Sends a request to compute the trajectory given the PlannerInput to the remote planner.
        :param stub: Service interface
        :param current_input: Planner input for which a trajectory should be computed.
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logging.debug('Client sending observation...')
        self.serialized_state, self.serialized_observation, self.sample_interval = self._get_history_update(current_input)
        serialized_simulation_iteration = chpb.SimulationIteration(time_us=current_input.iteration.time_us, index=current_input.iteration.index)
        if self.sample_interval:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=self.sample_interval)
        else:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=None)
        tl_data = self._build_tl_message_from_planner_input(current_input)
        planner_input = chpb.PlannerInput(simulation_iteration=serialized_simulation_iteration, simulation_history_buffer=serialized_buffer, traffic_light_data=tl_data)
        try:
            trajectory_message = stub.ComputeTrajectory(planner_input, timeout=self._compute_trajectory_timeout)
        except grpc.RpcError as e:
            submission_logger.error('Trajectory computation service failed!')
            submission_logger.error(e)
            raise e
        return interp_traj_from_proto_traj(trajectory_message)

    def _get_history_update(self, planner_input: PlannerInput) -> Tuple[List[bytes], List[bytes], Optional[float]]:
        """
        Gets the new states and observations from the input. If no cache is present, the entire history is
        serialized, otherwise just the last element.
        :param planner_input: The input for planners
        :return: Tuple with new serialized state and observations.
        """
        keep_all_history = not self.serialized_state and (not self.serialized_observation)
        if keep_all_history:
            serialized_state = [pickle.dumps(state) for state in planner_input.history.ego_states]
            serialized_observation = [pickle.dumps(obs) for obs in planner_input.history.observations]
        else:
            last_ego_state, last_observations = planner_input.history.current_state
            serialized_state = [pickle.dumps(last_ego_state)]
            serialized_observation = [pickle.dumps(last_observations)]
        sample_interval = planner_input.history.sample_interval if not self.sample_interval else None
        return (serialized_state, serialized_observation, sample_interval)

    @staticmethod
    def _build_tl_message_from_planner_input(planner_input: PlannerInput) -> chpb.TrafficLightStatusData:
        tl_status_data: List[List[chpb.TrafficLightStatusData]]
        if planner_input.traffic_light_data is None:
            tl_status_data = [[]]
        else:
            tl_status_data = [proto_tl_status_data_from_tl_status_data(tl_status_data) for tl_status_data in planner_input.traffic_light_data]
        return tl_status_data

def initialize(self, initialization: PlannerInitialization, timeout: float=5) -> None:
    """
        Creates the container manager, and runs the specified docker image. The communication port is created using
        the PID from the ray worker. Sends a request to initialize the remote planner.
        :param initialization: List of PlannerInitialization objects
        :param timeout: for planner initialization
        """
    if self.submission_container_manager:
        submission_container = try_n_times(self.submission_container_manager.get_submission_container, [self.submission_image, self.container_name, find_free_port_number()], {}, (docker.errors.APIError,), max_tries=10)
        self.port = submission_container.port
        submission_container.start()
        submission_container.wait_until_running(timeout=5)
    self._channel = grpc.insecure_channel(f'{NETWORK}:{self.port}')
    self._stub = chpb_grpc.DetectionTracksChallengeStub(self._channel)
    logger.info('Client sending planner initialization request...')
    planner_initializations_message = self._planner_initializations_to_message(initialization)
    logger.info(f'Trying to communicate on port {NETWORK}:{self.port}')
    try:
        _, _ = keep_trying(self._stub.InitializePlanner, [planner_initializations_message], {}, errors=(grpc.RpcError,), timeout=timeout)
    except Exception as e:
        submission_logger.error('Planner initialization failed!')
        submission_logger.error(e)
        raise e
    logger.info('Planner initialized!')

class MultiMainCallback(AbstractMainCallback):
    """
    Combines a set of of AbstractMainCallbacks.
    """

    def __init__(self, main_callbacks: List[AbstractMainCallback]):
        """
        Callback to handle a list of main callbacks.
        :param main_callbacks: A list of main callbacks.
        """
        self._main_callbacks = main_callbacks

    def __len__(self) -> int:
        """Support len() as counting the number of callbacks."""
        return len(self._main_callbacks)

    def on_run_simulation_start(self) -> None:
        """Callback after the simulation function starts."""
        for main_callback in self._main_callbacks:
            main_callback.on_run_simulation_start()

    def on_run_simulation_end(self) -> None:
        """Callback before the simulation function ends."""
        for main_callback in self._main_callbacks:
            main_callback.on_run_simulation_end()

def on_run_simulation_start(self) -> None:
    """Callback after the simulation function starts."""
    for main_callback in self._main_callbacks:
        main_callback.on_run_simulation_start()

class SkeletonTestSerializationCallback(unittest.TestCase):
    """Base class for TestsSerializationCallback* classes."""

    def _setUp(self) -> None:
        """Setup mocks for our tests."""
        self._serialization_type_to_extension_map = {'json': '.json', 'pickle': '.pkl.xz', 'msgpack': '.msgpack.xz'}
        self._serialization_type = getattr(self, '_serialization_type', '')
        self.assertIn(self._serialization_type, self._serialization_type_to_extension_map)
        self.output_folder = tempfile.TemporaryDirectory()
        self.callback = SerializationCallback(output_directory=self.output_folder.name, folder_name='sim', serialization_type=self._serialization_type, serialize_into_single_file=True)
        self.sim_manager = Mock(spec=AbstractSimulationTimeController)
        self.observation = Mock(spec=AbstractObservation)
        self.controller = Mock(spec=AbstractEgoController)
        super().setUp()

    @settings(deadline=None)
    @given(mock_timestamp=st.one_of(st.just(0), st.integers(min_value=1627066061949808, max_value=18446744073709551615)))
    def _dump_test_scenario(self, mock_timestamp: int) -> None:
        """
        Tests whether a scene can be dumped into a file and check that the keys are in the dumped scene.
        :param mock_timestamp: Mocked timestamp to pass to mock_get_traffic_light_status_at_iteration.
        """

        def mock_get_traffic_light_status_at_iteration(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
            """Mocks MockAbstractScenario.get_traffic_light_status_at_iteration to return large numbers."""
            dummy_tl_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=mock_timestamp)
            yield dummy_tl_data
        scenario = MockAbstractScenario()
        scenario.get_traffic_light_status_at_iteration = Mock(spec=scenario.get_traffic_light_status_at_iteration)
        scenario.get_traffic_light_status_at_iteration.side_effect = mock_get_traffic_light_status_at_iteration
        self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
        planner = Mock()
        planner.name = Mock(return_value='DummyPlanner')
        directory = self.callback._get_scenario_folder(planner.name(), scenario)
        self.assertEqual(str(directory), self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
        self.callback.on_initialization_start(self.setup, planner)
        history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
        for data in history.data:
            self.callback.on_step_end(self.setup, planner, data)
        self.callback.on_simulation_end(self.setup, planner, history)
        filename = 'mock_scenario_name' + self._serialization_type_to_extension_map[self._serialization_type]
        path = pathlib.Path(self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name/' + filename)
        self.assertTrue(path.exists())
        if self._serialization_type == 'json':
            with open(path.absolute()) as f:
                data = json.load(f)
        elif self._serialization_type == 'msgpack':
            with lzma.open(str(path), 'rb') as f:
                data = msgpack.unpackb(f.read())
        elif self._serialization_type == 'pickle':
            with lzma.open(str(path), 'rb') as f:
                data = pickle.load(f)
        self.assertTrue(len(data) > 0)
        data = data[0]
        self.assertTrue('world' in data.keys())
        self.assertTrue('ego' in data.keys())
        self.assertTrue('trajectories' in data.keys())
        self.assertTrue('map' in data.keys())
        expected_traffic_light_data = next(scenario.get_traffic_light_status_at_iteration(0))
        actual_traffic_light_data_dict = data['traffic_light_status'][0]
        self.assertEqual(actual_traffic_light_data_dict['timestamp'], expected_traffic_light_data.timestamp)

@settings(deadline=None)
@given(mock_timestamp=st.one_of(st.just(0), st.integers(min_value=1627066061949808, max_value=18446744073709551615)))
def _dump_test_scenario(self, mock_timestamp: int) -> None:
    """
        Tests whether a scene can be dumped into a file and check that the keys are in the dumped scene.
        :param mock_timestamp: Mocked timestamp to pass to mock_get_traffic_light_status_at_iteration.
        """

    def mock_get_traffic_light_status_at_iteration(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """Mocks MockAbstractScenario.get_traffic_light_status_at_iteration to return large numbers."""
        dummy_tl_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=mock_timestamp)
        yield dummy_tl_data
    scenario = MockAbstractScenario()
    scenario.get_traffic_light_status_at_iteration = Mock(spec=scenario.get_traffic_light_status_at_iteration)
    scenario.get_traffic_light_status_at_iteration.side_effect = mock_get_traffic_light_status_at_iteration
    self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
    planner = Mock()
    planner.name = Mock(return_value='DummyPlanner')
    directory = self.callback._get_scenario_folder(planner.name(), scenario)
    self.assertEqual(str(directory), self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
    self.callback.on_initialization_start(self.setup, planner)
    history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
    state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
    state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
    history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
    history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
    for data in history.data:
        self.callback.on_step_end(self.setup, planner, data)
    self.callback.on_simulation_end(self.setup, planner, history)
    filename = 'mock_scenario_name' + self._serialization_type_to_extension_map[self._serialization_type]
    path = pathlib.Path(self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name/' + filename)
    self.assertTrue(path.exists())
    if self._serialization_type == 'json':
        with open(path.absolute()) as f:
            data = json.load(f)
    elif self._serialization_type == 'msgpack':
        with lzma.open(str(path), 'rb') as f:
            data = msgpack.unpackb(f.read())
    elif self._serialization_type == 'pickle':
        with lzma.open(str(path), 'rb') as f:
            data = pickle.load(f)
    self.assertTrue(len(data) > 0)
    data = data[0]
    self.assertTrue('world' in data.keys())
    self.assertTrue('ego' in data.keys())
    self.assertTrue('trajectories' in data.keys())
    self.assertTrue('map' in data.keys())
    expected_traffic_light_data = next(scenario.get_traffic_light_status_at_iteration(0))
    actual_traffic_light_data_dict = data['traffic_light_status'][0]
    self.assertEqual(actual_traffic_light_data_dict['timestamp'], expected_traffic_light_data.timestamp)

class LightningModuleWrapper(pl.LightningModule):
    """
    Lightning module that wraps the training/validation/testing procedure and handles the objective/metric computation.
    """

    def __init__(self, model: TorchModuleWrapper, objectives: List[AbstractObjective], metrics: List[AbstractTrainingMetric], batch_size: int, optimizer: Optional[DictConfig]=None, lr_scheduler: Optional[DictConfig]=None, warm_up_lr_scheduler: Optional[DictConfig]=None, objective_aggregate_mode: str='mean') -> None:
        """
        Initializes the class.

        :param model: pytorch model
        :param objectives: list of learning objectives used for supervision at each step
        :param metrics: list of planning metrics computed at each step
        :param batch_size: batch_size taken from dataloader config
        :param optimizer: config for instantiating optimizer. Can be 'None' for older models.
        :param lr_scheduler: config for instantiating lr_scheduler. Can be 'None' for older models and when an lr_scheduler is not being used.
        :param warm_up_lr_scheduler: config for instantiating warm up lr scheduler. Can be 'None' for older models and when a warm up lr_scheduler is not being used.
        :param objective_aggregate_mode: how should different objectives be combined, can be 'sum', 'mean', and 'max'.
        """
        super().__init__()
        self.save_hyperparameters(ignore=['model'])
        self.model = model
        self.objectives = objectives
        self.metrics = metrics
        self.optimizer = optimizer
        self.lr_scheduler = lr_scheduler
        self.warm_up_lr_scheduler = warm_up_lr_scheduler
        self.objective_aggregate_mode = objective_aggregate_mode
        model_targets = {builder.get_feature_unique_name() for builder in model.get_list_of_computed_target()}
        for objective in self.objectives:
            for feature in objective.get_list_of_required_target_types():
                assert feature in model_targets, f'Objective target: "{feature}" is not in model computed targets!'
        for metric in self.metrics:
            for feature in metric.get_list_of_required_target_types():
                assert feature in model_targets, f'Metric target: "{feature}" is not in model computed targets!'

    def _step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], prefix: str) -> torch.Tensor:
        """
        Propagates the model forward and backwards and computes/logs losses and metrics.

        This is called either during training, validation or testing stage.

        :param batch: input batch consisting of features and targets
        :param prefix: prefix prepended at each artifact's name during logging
        :return: model's scalar loss
        """
        features, targets, scenarios = batch
        predictions = self.forward(features)
        objectives = self._compute_objectives(predictions, targets, scenarios)
        metrics = self._compute_metrics(predictions, targets)
        loss = aggregate_objectives(objectives, agg_mode=self.objective_aggregate_mode)
        self._log_step(loss, objectives, metrics, prefix)
        return loss

    def _compute_objectives(self, predictions: TargetsType, targets: TargetsType, scenarios: ScenarioListType) -> Dict[str, torch.Tensor]:
        """
        Computes a set of learning objectives used for supervision given the model's predictions and targets.

        :param predictions: model's output signal
        :param targets: supervisory signal
        :return: dictionary of objective names and values
        """
        return {objective.name(): objective.compute(predictions, targets, scenarios) for objective in self.objectives}

    def _compute_metrics(self, predictions: TargetsType, targets: TargetsType) -> Dict[str, torch.Tensor]:
        """
        Computes a set of planning metrics given the model's predictions and targets.

        :param predictions: model's predictions
        :param targets: ground truth targets
        :return: dictionary of metrics names and values
        """
        return {metric.name(): metric.compute(predictions, targets) for metric in self.metrics}

    def _log_step(self, loss: torch.Tensor, objectives: Dict[str, torch.Tensor], metrics: Dict[str, torch.Tensor], prefix: str, loss_name: str='loss') -> None:
        """
        Logs the artifacts from a training/validation/test step.

        :param loss: scalar loss value
        :type objectives: [type]
        :param metrics: dictionary of metrics names and values
        :param prefix: prefix prepended at each artifact's name
        :param loss_name: name given to the loss for logging
        """
        self.log(f'loss/{prefix}_{loss_name}', loss)
        for key, value in objectives.items():
            self.log(f'objectives/{prefix}_{key}', value)
        for key, value in metrics.items():
            self.log(f'metrics/{prefix}_{key}', value)

    def training_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during training.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'train')

    def validation_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during validation.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'val')

    def test_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during testing.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'test')

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Propagates a batch of features through the model.

        :param features: features batch
        :return: model's predictions
        """
        return self.model(features)

    def configure_optimizers(self) -> Union[Optimizer, Dict[str, Union[Optimizer, _LRScheduler]]]:
        """
        Configures the optimizers and learning schedules for the training.

        :return: optimizer or dictionary of optimizers and schedules
        """
        if self.optimizer is None:
            raise RuntimeError('To train, optimizer must not be None.')
        optimizer: Optimizer = instantiate(config=self.optimizer, params=self.parameters(), lr=self.optimizer.lr)
        logger.info(f'Using optimizer: {self.optimizer._target_}')
        lr_scheduler_params: Dict[str, Union[_LRScheduler, str, int]] = build_lr_scheduler(optimizer=optimizer, lr=self.optimizer.lr, warm_up_lr_scheduler_cfg=self.warm_up_lr_scheduler, lr_scheduler_cfg=self.lr_scheduler)
        optimizer_dict: Dict[str, Any] = {}
        optimizer_dict['optimizer'] = optimizer
        if lr_scheduler_params:
            logger.info(f'Using lr_schedulers {lr_scheduler_params}')
            optimizer_dict['lr_scheduler'] = lr_scheduler_params
        return optimizer_dict if 'lr_scheduler' in optimizer_dict else optimizer_dict['optimizer']

def configure_optimizers(self) -> Union[Optimizer, Dict[str, Union[Optimizer, _LRScheduler]]]:
    """
        Configures the optimizers and learning schedules for the training.

        :return: optimizer or dictionary of optimizers and schedules
        """
    if self.optimizer is None:
        raise RuntimeError('To train, optimizer must not be None.')
    optimizer: Optimizer = instantiate(config=self.optimizer, params=self.parameters(), lr=self.optimizer.lr)
    logger.info(f'Using optimizer: {self.optimizer._target_}')
    lr_scheduler_params: Dict[str, Union[_LRScheduler, str, int]] = build_lr_scheduler(optimizer=optimizer, lr=self.optimizer.lr, warm_up_lr_scheduler_cfg=self.warm_up_lr_scheduler, lr_scheduler_cfg=self.lr_scheduler)
    optimizer_dict: Dict[str, Any] = {}
    optimizer_dict['optimizer'] = optimizer
    if lr_scheduler_params:
        logger.info(f'Using lr_schedulers {lr_scheduler_params}')
        optimizer_dict['lr_scheduler'] = lr_scheduler_params
    return optimizer_dict if 'lr_scheduler' in optimizer_dict else optimizer_dict['optimizer']

def build_scenarios_from_config(cfg: DictConfig, scenario_builder: AbstractScenarioBuilder, worker: WorkerPool) -> List[AbstractScenario]:
    """
    Build scenarios from config file.
    :param cfg: Omegaconf dictionary
    :param scenario_builder: Scenario builder.
    :param worker: Worker to submit tasks which can be executed in parallel
    :return: A list of scenarios
    """
    scenario_filter = build_scenario_filter(cfg.scenario_filter)
    return scenario_builder.get_scenarios(scenario_filter, worker)

def cache_data(cfg: DictConfig, worker: WorkerPool) -> None:
    """
    Build the lightning datamodule and cache all samples.
    :param cfg: omegaconf dictionary
    :param worker: Worker to submit tasks which can be executed in parallel
    """
    assert cfg.cache.cache_path is not None, f'Cache path cannot be None when caching, got {cfg.cache.cache_path}'
    scenario_builder = build_scenario_builder(cfg)
    if int(os.environ.get('NUM_NODES', 1)) > 1 and cfg.distribute_by_scenario:
        repartition_strategy = scenario_builder.repartition_strategy
        if repartition_strategy == RepartitionStrategy.REPARTITION_FILE_DISK:
            scenario_filter = DistributedScenarioFilter(cfg=cfg, worker=worker, node_rank=int(os.environ.get('NODE_RANK', 0)), num_nodes=int(os.environ.get('NUM_NODES', 1)), synchronization_path=cfg.cache.cache_path, timeout_seconds=cfg.get('distributed_timeout_seconds', 3600), distributed_mode=cfg.get('distributed_mode', DistributedMode.LOG_FILE_BASED))
            scenarios = scenario_filter.get_scenarios()
        elif repartition_strategy == RepartitionStrategy.INLINE:
            scenarios = build_scenarios_from_config(cfg, scenario_builder, worker)
            num_nodes = int(os.environ.get('NUM_NODES', 1))
            node_id = int(os.environ.get('NODE_RANK', 0))
            scenarios = chunk_list(scenarios, num_nodes)[node_id]
        else:
            expected_repartition_strategies = [e.value for e in RepartitionStrategy]
            raise ValueError(f'Expected repartition strategy to be in {expected_repartition_strategies}, got {repartition_strategy}.')
    else:
        logger.debug("Building scenarios without distribution, if you're running on a multi-node system, make sure you aren'taccidentally caching each scenario multiple times!")
        scenarios = build_scenarios_from_config(cfg, scenario_builder, worker)
    data_points = [{'scenario': scenario, 'cfg': cfg} for scenario in scenarios]
    logger.info('Starting dataset caching of %s files...', str(len(data_points)))
    cache_results = worker_map(worker, cache_scenarios, data_points)
    num_success = sum((result.successes for result in cache_results))
    num_fail = sum((result.failures for result in cache_results))
    num_total = num_success + num_fail
    logger.info('Completed dataset caching! Failed features and targets: %s out of %s', str(num_fail), str(num_total))
    cached_metadata = [cache_metadata_entry for cache_result in cache_results for cache_metadata_entry in cache_result.cache_metadata if cache_metadata_entry is not None]
    node_id = int(os.environ.get('NODE_RANK', 0))
    logger.info(f'Node {node_id}: Storing metadata csv file containing cache paths for valid features and targets...')
    save_cache_metadata(cached_metadata, Path(cfg.cache.cache_path), node_id)
    logger.info('Done storing metadata csv file.')

class ProfileCallback(pl.Callback):
    """Profiling callback that produces an html report."""

    def __init__(self, output_dir: pathlib.Path, interval: float=0.01):
        """
        Initialize callback.
        :param output_dir: directory where output should be stored. Note, "profiling" sub-dir will be added
        :param interval: of the profiler
        """
        self._output_dir = output_dir / 'profiling'
        if not is_s3_path(self._output_dir):
            self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'Profiler will report into folder: {str(self._output_dir)}')
        self._profiler = Profiler(interval=interval)
        self._profiler_running = False

    def on_init_start(self, trainer: pl.Trainer) -> None:
        """
        Called during training initialization.
        :param trainer: Lightning trainer.
        """
        self.start_profiler('on_init_start')

    def on_init_end(self, trainer: pl.Trainer) -> None:
        """
        Called at the end of the training.
        :param trainer: Lightning trainer.
        """
        self.save_profiler('on_init_end')

    def on_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at each epoch start.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
        self.start_profiler('on_epoch_start')

    def on_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at each epoch end.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
        self.save_profiler('epoch_' + str(trainer.current_epoch) + '-on_epoch_end')

    def start_profiler(self, when: str) -> None:
        """
        Start the profiler.
        Raise: in case profiler is already running.
        :param when: Message to log when starting the profiler.
        """
        assert not self._profiler_running, 'Profiler can not be started twice!'
        logger.info(f'STARTING profiler: {when}')
        self._profiler_running = True
        self._profiler.start()

    def stop_profiler(self) -> None:
        """
        Start profiler
        Raise: in case profiler is not running
        """
        assert self._profiler_running, 'Profiler has to be running!!'
        self._profiler.stop()
        self._profiler_running = False

    def save_profiler(self, file_name: str) -> None:
        """
        Save profiling output to a html report
        :param file_name: File name to save report to.
        """
        self.stop_profiler()
        profiler_out_html = self._profiler.output_html()
        html_save_path = self._output_dir / file_name
        path = str(html_save_path.with_suffix('.html'))
        logger.info(f'Saving profiler output to: {path}')
        fp = open(path, 'w+')
        fp.write(profiler_out_html)
        fp.close()

def on_init_start(self, trainer: pl.Trainer) -> None:
    """
        Called during training initialization.
        :param trainer: Lightning trainer.
        """
    self.start_profiler('on_init_start')

def on_init_end(self, trainer: pl.Trainer) -> None:
    """
        Called at the end of the training.
        :param trainer: Lightning trainer.
        """
    self.save_profiler('on_init_end')

def on_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at each epoch start.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
    self.start_profiler('on_epoch_start')

def on_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at each epoch end.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
    self.save_profiler('epoch_' + str(trainer.current_epoch) + '-on_epoch_end')

def start_profiler(self, when: str) -> None:
    """
        Start the profiler.
        Raise: in case profiler is already running.
        :param when: Message to log when starting the profiler.
        """
    assert not self._profiler_running, 'Profiler can not be started twice!'
    logger.info(f'STARTING profiler: {when}')
    self._profiler_running = True
    self._profiler.start()

def stop_profiler(self) -> None:
    """
        Start profiler
        Raise: in case profiler is not running
        """
    assert self._profiler_running, 'Profiler has to be running!!'
    self._profiler.stop()
    self._profiler_running = False

@st.composite
def _get_valid_test_parameters(draw: Any) -> Dict[str, Union[int, float]]:
    """
    This function implements a strategy to define trajectory / time parameters
    for both MockAbstractScenario and TrajectorySampling, used by EgoTargetTrajectoryBuilder.
    :param draw: The draw function used to select a specific sample given the strategy.
    :return: A dictionary mapping parameters to sampled values to test.
    """
    test_time_step_samples = st.sampled_from(np.arange(MIN_TIME_INTERVAL, MIN_TIME_INTERVAL + MAX_TIME_INTERVAL, MIN_TIME_INTERVAL))
    test_number_of_future_iterations_samples = st.integers(min_value=MIN_FUTURE_ITERATIONS, max_value=MAX_FUTURE_ITERATIONS)
    test_field_to_set_none = st.one_of(st.none(), st.sampled_from(['num_poses', 'time_horizon', 'interval_length']))
    picked_time_step = draw(test_time_step_samples)
    picked_number_of_future_iterations = draw(test_number_of_future_iterations_samples)
    scenario_trajectory_full_horizon = picked_time_step * picked_number_of_future_iterations
    picked_interval_length = draw(st.sampled_from(np.arange(picked_time_step, scenario_trajectory_full_horizon - picked_time_step, picked_time_step)))
    picked_num_poses = draw(st.integers(min_value=1, max_value=int(scenario_trajectory_full_horizon / picked_interval_length)))
    picked_trajectory_horizon = picked_interval_length * picked_num_poses
    trajectory_sampling_dict = {'time_step': picked_time_step, 'number_of_future_iterations': picked_number_of_future_iterations, 'num_poses': picked_num_poses, 'time_horizon': picked_trajectory_horizon, 'interval_length': picked_interval_length}
    picked_field_to_set_none = draw(test_field_to_set_none)
    if picked_field_to_set_none is not None:
        trajectory_sampling_dict[picked_field_to_set_none] = None
    return trajectory_sampling_dict

class TestEgoTrajectoryTargetBuilder(unittest.TestCase):
    """Test class for EgoTrajectoryTargetBuilder."""

    @given(test_parameters=_get_valid_test_parameters())
    @example(test_parameters={'time_step': 0.05, 'number_of_future_iterations': 100, 'num_poses': 10, 'time_horizon': 5.0, 'interval_length': None})
    def test_get_targets(self, test_parameters: Dict[str, Union[int, float]]) -> None:
        """
        Parametrized test for target trajectory extraction.
        :param test_parameters: The dictionary mapping parameters to sampled values to apply in the test.
        """
        test_scenario = MockAbstractScenario(time_step=test_parameters['time_step'], number_of_future_iterations=test_parameters['number_of_future_iterations'])
        test_future_trajectory_sampling = TrajectorySampling(num_poses=test_parameters['num_poses'], time_horizon=test_parameters['time_horizon'], interval_length=test_parameters['interval_length'])
        builder = EgoTrajectoryTargetBuilder(future_trajectory_sampling=test_future_trajectory_sampling)
        generated_features = builder.get_targets(test_scenario)
        self.assertEqual(generated_features.num_of_iterations, test_future_trajectory_sampling.num_poses)
        self.assertIsInstance(generated_features, builder.get_feature_type())

    @given(num_poses_diff=st.integers(min_value=-MIN_FUTURE_ITERATIONS + 1, max_value=MIN_FUTURE_ITERATIONS))
    def test_runtime_error_due_to_expected_pose_mismatch(self, num_poses_diff: int) -> None:
        """This tests the edge case if the number of returned poses doesn't match the expected one in the builder."""
        test_scenario = MockAbstractScenario()
        test_future_trajectory_sampling = TrajectorySampling(num_poses=max(test_scenario._number_of_future_iterations, MIN_FUTURE_ITERATIONS), interval_length=test_scenario._time_step)
        builder = EgoTrajectoryTargetBuilder(future_trajectory_sampling=test_future_trajectory_sampling)
        with patch(f'{PATCH_STR}.convert_absolute_to_relative_poses') as mock_convert_absolute_to_relative_poses:
            mock_convert_absolute_to_relative_poses.return_value = np.zeros((builder._num_future_poses + num_poses_diff, 3), dtype=np.float32)
            if num_poses_diff == 0:
                generated_features = builder.get_targets(test_scenario)
                self.assertIsInstance(generated_features, builder.get_feature_type())
            else:
                with self.assertRaisesRegex(RuntimeError, 'Expected.*num poses but got.*'):
                    builder.get_targets(test_scenario)
        mock_convert_absolute_to_relative_poses.assert_called_once()

@given(test_parameters=_get_valid_test_parameters())
@example(test_parameters={'time_step': 0.05, 'number_of_future_iterations': 100, 'num_poses': 10, 'time_horizon': 5.0, 'interval_length': None})
def test_get_targets(self, test_parameters: Dict[str, Union[int, float]]) -> None:
    """
        Parametrized test for target trajectory extraction.
        :param test_parameters: The dictionary mapping parameters to sampled values to apply in the test.
        """
    test_scenario = MockAbstractScenario(time_step=test_parameters['time_step'], number_of_future_iterations=test_parameters['number_of_future_iterations'])
    test_future_trajectory_sampling = TrajectorySampling(num_poses=test_parameters['num_poses'], time_horizon=test_parameters['time_horizon'], interval_length=test_parameters['interval_length'])
    builder = EgoTrajectoryTargetBuilder(future_trajectory_sampling=test_future_trajectory_sampling)
    generated_features = builder.get_targets(test_scenario)
    self.assertEqual(generated_features.num_of_iterations, test_future_trajectory_sampling.num_poses)
    self.assertIsInstance(generated_features, builder.get_feature_type())

@given(num_poses_diff=st.integers(min_value=-MIN_FUTURE_ITERATIONS + 1, max_value=MIN_FUTURE_ITERATIONS))
def test_runtime_error_due_to_expected_pose_mismatch(self, num_poses_diff: int) -> None:
    """This tests the edge case if the number of returned poses doesn't match the expected one in the builder."""
    test_scenario = MockAbstractScenario()
    test_future_trajectory_sampling = TrajectorySampling(num_poses=max(test_scenario._number_of_future_iterations, MIN_FUTURE_ITERATIONS), interval_length=test_scenario._time_step)
    builder = EgoTrajectoryTargetBuilder(future_trajectory_sampling=test_future_trajectory_sampling)
    with patch(f'{PATCH_STR}.convert_absolute_to_relative_poses') as mock_convert_absolute_to_relative_poses:
        mock_convert_absolute_to_relative_poses.return_value = np.zeros((builder._num_future_poses + num_poses_diff, 3), dtype=np.float32)
        if num_poses_diff == 0:
            generated_features = builder.get_targets(test_scenario)
            self.assertIsInstance(generated_features, builder.get_feature_type())
        else:
            with self.assertRaisesRegex(RuntimeError, 'Expected.*num poses but got.*'):
                builder.get_targets(test_scenario)
    mock_convert_absolute_to_relative_poses.assert_called_once()

class NuBoard:
    """NuBoard application class."""

    def __init__(self, nuboard_paths: List[str], scenario_builder: AbstractScenarioBuilder, vehicle_parameters: VehicleParameters, port_number: int=5006, profiler_path: Optional[Path]=None, resource_prefix: Optional[str]=None, async_scenario_rendering: bool=True, scenario_rendering_frame_rate_cap_hz: int=60):
        """
        Nuboard main class.
        :param nuboard_paths: A list of paths to nuboard files.
        :param scenario_builder: Scenario builder instance.
        :param vehicle_parameters: vehicle parameters.
        :param port_number: Bokeh port number.
        :param profiler_path: Path to save the profiler.
        :param resource_prefix: Prefix to the resource path in HTML.
        :param async_scenario_rendering: Whether to use asynchronous scenario rendering in the scenario tab.
        :param scenario_rendering_frame_rate_cap_hz: Maximum frames to render in the scenario tab per second.
            Use lower values when running nuBoard in the cloud to prevent frame queues due to latency. The rule of thumb
            is to match the frame rate with the expected latency, e.g 5Hz for 200ms round-trip latency.
            Internally this value is capped at 60.
        """
        self._profiler_path = profiler_path
        self._nuboard_paths = check_nuboard_file_paths(nuboard_paths)
        self._scenario_builder = scenario_builder
        self._port_number = port_number
        self._vehicle_parameters = vehicle_parameters
        self._doc: Optional[Document] = None
        self._resource_prefix = resource_prefix if resource_prefix else ''
        self._resource_path = Path(__file__).parents[0] / 'resource'
        self._profiler_file_name = 'nuboard'
        self._profiler: Optional[ProfileCallback] = None
        self._async_scenario_rendering = async_scenario_rendering
        if scenario_rendering_frame_rate_cap_hz < 1 or scenario_rendering_frame_rate_cap_hz > 60:
            raise ValueError('scenario_rendering_frame_rate_cap_hz should be between 1 and 60')
        self._scenario_rendering_frame_rate_cap_hz = scenario_rendering_frame_rate_cap_hz

    def stop_handler(self, sig: Any, frame: Any) -> None:
        """Helper to handle stop signals."""
        logger.info('Stopping the Bokeh application.')
        if self._profiler:
            self._profiler.save_profiler(self._profiler_file_name)
        IOLoop.current().stop()

    def run(self) -> None:
        """Run nuBoard WebApp."""
        logger.info(f'Opening Bokeh application on http://localhost:{self._port_number}/')
        logger.info(f'Async rendering is set to: {self._async_scenario_rendering}')
        io_loop = IOLoop.current()
        if self._profiler_path is not None:
            signal.signal(signal.SIGTERM, self.stop_handler)
            signal.signal(signal.SIGINT, self.stop_handler)
            self._profiler = ProfileCallback(output_dir=self._profiler_path)
            self._profiler.start_profiler(self._profiler_file_name)
        bokeh_app = Application(FunctionHandler(self.main_page))
        server = Server({'/': bokeh_app}, io_loop=io_loop, port=self._port_number, allow_websocket_origin=['*'], extra_patterns=[('/resource/(.*)', StaticFileHandler, {'path': str(self._resource_path)})])
        server.start()
        io_loop.add_callback(server.show, '/')
        try:
            io_loop.start()
        except RuntimeError as e:
            logger.warning(f'{e}')

    def main_page(self, doc: Document) -> None:
        """
        Main nuBoard page.
        :param doc: HTML document.
        """
        self._doc = doc
        template_path = Path(os.path.dirname(os.path.realpath(__file__))) / 'templates'
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
        self._doc.template = env.get_template('index.html')
        self._doc.title = 'nuBoard'
        nuboard_files = read_nuboard_file_paths(file_paths=self._nuboard_paths)
        experiment_file_data = ExperimentFileData(file_paths=nuboard_files)
        overview_tab = OverviewTab(doc=self._doc, experiment_file_data=experiment_file_data)
        histogram_tab = HistogramTab(doc=self._doc, experiment_file_data=experiment_file_data)
        scenario_tab = ScenarioTab(experiment_file_data=experiment_file_data, scenario_builder=self._scenario_builder, doc=self._doc, vehicle_parameters=self._vehicle_parameters, async_rendering=self._async_scenario_rendering, frame_rate_cap_hz=self._scenario_rendering_frame_rate_cap_hz)
        configuration_tab = ConfigurationTab(experiment_file_data=experiment_file_data, doc=self._doc, tabs=[overview_tab, histogram_tab, scenario_tab])
        s3_tab = CloudTab(doc=self._doc, configuration_tab=configuration_tab)
        self._doc.add_root(configuration_tab.file_path_input)
        self._doc.add_root(configuration_tab.experiment_file_path_checkbox_group)
        self._doc.add_root(s3_tab.s3_bucket_name)
        self._doc.add_root(s3_tab.s3_bucket_text_input)
        self._doc.add_root(s3_tab.s3_error_text)
        self._doc.add_root(s3_tab.s3_access_key_id_text_input)
        self._doc.add_root(s3_tab.s3_secret_access_key_password_input)
        self._doc.add_root(s3_tab.s3_bucket_prefix_text_input)
        self._doc.add_root(s3_tab.s3_modal_query_btn)
        self._doc.add_root(s3_tab.s3_download_text_input)
        self._doc.add_root(s3_tab.s3_download_button)
        self._doc.add_root(s3_tab.data_table)
        self._doc.add_root(overview_tab.table)
        self._doc.add_root(overview_tab.planner_checkbox_group)
        self._doc.add_root(histogram_tab.scenario_type_multi_choice)
        self._doc.add_root(histogram_tab.metric_name_multi_choice)
        self._doc.add_root(histogram_tab.planner_checkbox_group)
        self._doc.add_root(histogram_tab.histogram_plots)
        self._doc.add_root(histogram_tab.bin_spinner)
        self._doc.add_root(histogram_tab.histogram_modal_query_btn)
        self._doc.add_root(scenario_tab.planner_checkbox_group)
        self._doc.add_root(scenario_tab.scenario_title_div)
        self._doc.add_root(scenario_tab.object_checkbox_group)
        self._doc.add_root(scenario_tab.traj_checkbox_group)
        self._doc.add_root(scenario_tab.map_checkbox_group)
        self._doc.add_root(scenario_tab.scalar_scenario_type_select)
        self._doc.add_root(scenario_tab.scalar_log_name_select)
        self._doc.add_root(scenario_tab.scalar_scenario_name_select)
        self._doc.add_root(scenario_tab.scenario_token_multi_choice)
        self._doc.add_root(scenario_tab.scenario_modal_query_btn)
        self._doc.add_root(scenario_tab.time_series_layout)
        self._doc.add_root(scenario_tab.ego_expert_states_layout)
        self._doc.add_root(scenario_tab.scenario_score_layout)
        self._doc.add_root(scenario_tab.simulation_tile_layout)

def stop_handler(self, sig: Any, frame: Any) -> None:
    """Helper to handle stop signals."""
    logger.info('Stopping the Bokeh application.')
    if self._profiler:
        self._profiler.save_profiler(self._profiler_file_name)
    IOLoop.current().stop()

def run(self) -> None:
    """Run nuBoard WebApp."""
    logger.info(f'Opening Bokeh application on http://localhost:{self._port_number}/')
    logger.info(f'Async rendering is set to: {self._async_scenario_rendering}')
    io_loop = IOLoop.current()
    if self._profiler_path is not None:
        signal.signal(signal.SIGTERM, self.stop_handler)
        signal.signal(signal.SIGINT, self.stop_handler)
        self._profiler = ProfileCallback(output_dir=self._profiler_path)
        self._profiler.start_profiler(self._profiler_file_name)
    bokeh_app = Application(FunctionHandler(self.main_page))
    server = Server({'/': bokeh_app}, io_loop=io_loop, port=self._port_number, allow_websocket_origin=['*'], extra_patterns=[('/resource/(.*)', StaticFileHandler, {'path': str(self._resource_path)})])
    server.start()
    io_loop.add_callback(server.show, '/')
    try:
        io_loop.start()
    except RuntimeError as e:
        logger.warning(f'{e}')

@dataclass
class SimulationFigure:
    """Simulation figure data."""
    planner_name: str
    scenario: AbstractScenario
    simulation_history: SimulationHistory
    vehicle_parameters: VehicleParameters
    figure: Figure
    file_path_index: int
    slider: Slider
    video_button: Button
    first_button: Button
    prev_button: Button
    play_button: Button
    next_button: Button
    last_button: Button
    figure_title_name: str
    x_y_coordinate_title: Title
    time_us: Optional[List[int]] = None
    mission_goal_plot: Optional[GlyphRenderer] = None
    expert_trajectory_plot: Optional[GlyphRenderer] = None
    legend_state: bool = False
    map_polygon_plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    map_line_plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    traffic_light_plot: Optional[TrafficLightPlot] = None
    ego_state_plot: Optional[EgoStatePlot] = None
    ego_state_trajectory_plot: Optional[EgoStateTrajectoryPlot] = None
    agent_state_plot: Optional[AgentStatePlot] = None
    agent_state_heading_plot: Optional[AgentStateHeadingPlot] = None
    lane_connectors: Optional[Dict[str, LaneConnector]] = None
    glyph_names_from_checkbox_group: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        """Initialize all plots and data sources."""
        if self.lane_connectors is None:
            self.lane_connectors = {}
        if self.time_us is None:
            self.time_us = []
        if self.traffic_light_plot is None:
            self.traffic_light_plot = TrafficLightPlot()
        if self.ego_state_plot is None:
            self.ego_state_plot = EgoStatePlot(vehicle_parameters=self.vehicle_parameters)
        if self.ego_state_trajectory_plot is None:
            self.ego_state_trajectory_plot = EgoStateTrajectoryPlot()
        if self.agent_state_plot is None:
            self.agent_state_plot = AgentStatePlot()
        if self.agent_state_heading_plot is None:
            self.agent_state_heading_plot = AgentStateHeadingPlot()

    def is_rendering(self) -> bool:
        """:return: true if at least one plot is currently rendering a frame request."""
        plots = [self.traffic_light_plot, self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]
        return any((plot.render_event.is_set() if plot.render_event else False for plot in plots if plot))

    def figure_title_name_with_timestamp(self, frame_index: int) -> str:
        """
        Return figure title with a timestamp.
        :param frame_index: Frame index.
        """
        if self.time_us:
            return f'{self.figure_title_name} (Frame: {frame_index}, Time_us: {self.time_us[frame_index]})'
        else:
            return self.figure_title_name

    def copy_datasources(self, other: SimulationFigure) -> None:
        """
        Copy data sources from another simulation figure.
        :param other: Another SimulationFigure object.
        """
        self.time_us = other.time_us
        self.scenario = other.scenario
        self.simulation_history = other.simulation_history
        self.lane_connectors = other.lane_connectors
        self.traffic_light_plot.data_sources = other.traffic_light_plot.data_sources
        self.ego_state_plot.data_sources = other.ego_state_plot.data_sources
        self.ego_state_trajectory_plot.data_sources = other.ego_state_trajectory_plot.data_sources
        self.agent_state_plot.data_sources = other.agent_state_plot.data_sources
        self.agent_state_heading_plot.data_sources = other.agent_state_heading_plot.data_sources

    def update_data_sources(self) -> None:
        """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
        if len(self.simulation_history.data) == 0:
            raise ValueError('SimulationHistory cannot be empty!')
        self.slider.end = len(self.simulation_history.data) - 1
        self.time_us = [sample.ego_state.time_us for sample in self.simulation_history.data]
        for plot in [self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]:
            if plot:
                t = threading.Thread(target=plot.update_data_sources, args=(self.simulation_history,), daemon=True)
                t.start()

    def update_map_dependent_data_sources(self) -> None:
        """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
        if len(self.simulation_history.data) == 0:
            raise ValueError('SimulationHistory cannot be empty!')
        if self.lane_connectors is not None and len(self.lane_connectors):
            if not self.traffic_light_plot:
                return
            thread = threading.Thread(target=self.traffic_light_plot.update_data_sources, args=(self.scenario, self.simulation_history, self.lane_connectors), daemon=True)
            thread.start()

    def render_mission_goal(self, mission_goal_state: StateSE2) -> None:
        """
        Render the mission goal.
        :param mission_goal_state: Mission goal state.
        """
        source = ColumnDataSource(dict(xs=[mission_goal_state.x], ys=[mission_goal_state.y], heading=[mission_goal_state.heading]))
        self.mission_goal_plot = self.figure.rect(x='xs', y='ys', height=self.vehicle_parameters.height, width=self.vehicle_parameters.length, angle='heading', fill_alpha=simulation_tile_style['mission_goal_alpha'], color=simulation_tile_style['mission_goal_color'], line_width=simulation_tile_style['mission_goal_line_width'], source=source)

    def render_expert_trajectory(self, expert_ego_trajectory_state: ColumnDataSource) -> None:
        """
        Render expert trajectory.
        :param expert_ego_trajectory_state: A list of trajectory states.
        """
        self.expert_trajectory_plot = self.figure.line(x='xs', y='ys', line_color=simulation_tile_trajectory_style['expert_ego']['line_color'], line_alpha=simulation_tile_trajectory_style['expert_ego']['line_alpha'], line_width=simulation_tile_trajectory_style['expert_ego']['line_width'], source=expert_ego_trajectory_state)

    @staticmethod
    def _update_glyph_visibility(glyphs: List[Optional[GlyphRenderer]]) -> None:
        """
        Update visibility in a list of glyphs.
        :param glyphs: A list of glyphs.
        """
        for glyph in glyphs:
            if glyph is not None:
                glyph.visible = not glyph.visible

    def get_glyph_name_from_checkbox_group(self, glyph_checkbox_group_name: str) -> str:
        """
        Get the correct glyph name of each glyph type based on the name from checkbox group.
        :param glyph_checkbox_group_name: glyph name from a checkbox group.
        :return Correct glyph name based on the glyph name from checkbox groups.
        """
        if not self.glyph_names_from_checkbox_group:
            self.glyph_names_from_checkbox_group = {'Vehicle': 'vehicles', 'Pedestrian': 'pedestrians', 'Bicycle': 'bicycles', 'Generic': 'genericobjects', 'Traffic Cone': 'traffic_cone', 'Barrier': 'barrier', 'Czone Sign': 'czone_sign', 'Lane': SemanticMapLayer.LANE.name, 'Intersection': SemanticMapLayer.INTERSECTION.name, 'Stop Line': SemanticMapLayer.STOP_LINE.name, 'Crosswalk': SemanticMapLayer.CROSSWALK.name, 'Walkway': SemanticMapLayer.WALKWAYS.name, 'Carpark': SemanticMapLayer.CARPARK_AREA.name, 'RoadBlock': SemanticMapLayer.ROADBLOCK.name, 'Lane Connector': SemanticMapLayer.LANE_CONNECTOR.name, 'Lane Line': SemanticMapLayer.LANE.name}
        name = self.glyph_names_from_checkbox_group.get(glyph_checkbox_group_name, None)
        if not name:
            raise ValueError(f'{glyph_checkbox_group_name} is not a valid glyph name!')
        return name

    def _get_trajectory_glyph_to_update(self, glyph_name: str) -> List[Optional[GlyphRenderer]]:
        """
        Get a trajectory glyph to update its visibility.
        :param glyph_name: Glyph name.
        :return A list of glyphs to be updated.
        """
        if glyph_name == 'Expert Trajectory':
            return [self.expert_trajectory_plot if self.expert_trajectory_plot is not None else None]
        elif glyph_name == 'Ego Trajectory':
            return [self.ego_state_trajectory_plot.plot if self.ego_state_trajectory_plot is not None else None]
        elif glyph_name == 'Goal':
            return [self.mission_goal_plot]
        elif glyph_name == 'Traffic Light':
            return [self.traffic_light_plot.plot if self.traffic_light_plot is not None else None]
        else:
            raise ValueError(f'{glyph_name} is not a valid trajectory name.')

    def _get_agent_glyph_to_update(self, glyph_name: str) -> List[Optional[GlyphRenderer]]:
        """
        Update an agent glyph to update its visibility.
        :param glyph_name: Glyph name.
        :return A list of glyphs to be updated.
        """
        object_type_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
        return [self.agent_state_plot.plots.get(object_type_name, None) if self.agent_state_plot is not None else None, self.agent_state_heading_plot.plots.get(object_type_name, None) if self.agent_state_heading_plot is not None else None]

    def update_glyphs_visibility(self, glyph_names: Optional[List[str]]=None) -> None:
        """
        Update glyphs' visibility based on a list of glyph names.
        :param glyph_names: List of glyph names to update their visibility.
        """
        if not glyph_names:
            return
        glyphs = []
        for glyph_name in glyph_names:
            if glyph_name == 'Ego':
                glyphs += [self.ego_state_plot.plot if self.ego_state_plot is not None else None]
            elif glyph_name in ['Expert Trajectory', 'Ego Trajectory', 'Goal', 'Traffic Light']:
                glyphs += self._get_trajectory_glyph_to_update(glyph_name=glyph_name)
            elif glyph_name in ['Vehicle', 'Pedestrian', 'Bicycle', 'Generic', 'Traffic Cone', 'Barrier', 'Czone Sign']:
                glyphs += self._get_agent_glyph_to_update(glyph_name=glyph_name)
            elif glyph_name in ['Lane', 'Intersection', 'Stop Line', 'Crosswalk', 'Walkway', 'Carpark', 'RoadBlock']:
                map_polygon_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
                glyphs += [self.map_polygon_plots.get(map_polygon_name, None)]
            elif glyph_name in ['Lane Connector', 'Lane Line']:
                map_line_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
                glyphs += [self.map_line_plots.get(map_line_name, None)]
        self._update_glyph_visibility(glyphs=glyphs)

    def update_legend(self) -> None:
        """Update legend."""
        if self.legend_state:
            return
        if not self.agent_state_heading_plot or not self.agent_state_plot:
            return
        agent_legends = [(category.capitalize(), [plot, self.agent_state_heading_plot.plots[category]]) for category, plot in self.agent_state_plot.plots.items()]
        selected_map_polygon_layers = [SemanticMapLayer.LANE.name, SemanticMapLayer.INTERSECTION.name, SemanticMapLayer.STOP_LINE.name, SemanticMapLayer.CROSSWALK.name, SemanticMapLayer.WALKWAYS.name, SemanticMapLayer.CARPARK_AREA.name]
        map_polygon_legend_items = []
        for map_polygon_layer in selected_map_polygon_layers:
            map_polygon_legend_items.append((map_polygon_layer.capitalize(), [self.map_polygon_plots[map_polygon_layer]]))
        selected_map_line_layers = [SemanticMapLayer.LANE.name, SemanticMapLayer.LANE_CONNECTOR.name]
        map_line_legend_items = []
        for map_line_layer in selected_map_line_layers:
            map_line_legend_items.append((map_line_layer.capitalize(), [self.map_line_plots[map_line_layer]]))
        if not self.ego_state_plot or not self.ego_state_trajectory_plot:
            return
        legend_items = [('Ego', [self.ego_state_plot.plot]), ('Ego traj', [self.ego_state_trajectory_plot.plot])]
        if self.mission_goal_plot is not None:
            legend_items.append(('Goal', [self.mission_goal_plot]))
        if self.expert_trajectory_plot is not None:
            legend_items.append(('Expert traj', [self.expert_trajectory_plot]))
        legend_items += agent_legends
        legend_items += map_polygon_legend_items
        legend_items += map_line_legend_items
        if self.traffic_light_plot and self.traffic_light_plot.plot is not None:
            legend_items.append(('Traffic light', [self.traffic_light_plot.plot]))
        legend = Legend(items=legend_items)
        legend.click_policy = 'hide'
        self.figure.add_layout(legend)
        self.legend_state = True
        self.figure.legend.label_text_font_size = '0.8em'

def update_data_sources(self) -> None:
    """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
    if len(self.simulation_history.data) == 0:
        raise ValueError('SimulationHistory cannot be empty!')
    self.slider.end = len(self.simulation_history.data) - 1
    self.time_us = [sample.ego_state.time_us for sample in self.simulation_history.data]
    for plot in [self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]:
        if plot:
            t = threading.Thread(target=plot.update_data_sources, args=(self.simulation_history,), daemon=True)
            t.start()

def update_map_dependent_data_sources(self) -> None:
    """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
    if len(self.simulation_history.data) == 0:
        raise ValueError('SimulationHistory cannot be empty!')
    if self.lane_connectors is not None and len(self.lane_connectors):
        if not self.traffic_light_plot:
            return
        thread = threading.Thread(target=self.traffic_light_plot.update_data_sources, args=(self.scenario, self.simulation_history, self.lane_connectors), daemon=True)
        thread.start()

class SimulationTile:
    """Scenario simulation tile for visualization."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, vehicle_parameters: VehicleParameters, map_factory: AbstractMapFactory, period_milliseconds: int=5000, radius: float=300.0, async_rendering: bool=True, frame_rate_cap_hz: int=60):
        """
        Scenario simulation tile.
        :param doc: Bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        :param vehicle_parameters: Ego pose parameters.
        :param map_factory: Map factory for building maps.
        :param period_milliseconds: Milliseconds to update the tile.
        :param radius: Map radius.
        :param async_rendering: When true, will use threads to render asynchronously.
        :param frame_rate_cap_hz: Maximum frames to render per second. Internally this value is capped at 60.
        """
        self._doc = doc
        self._vehicle_parameters = vehicle_parameters
        self._map_factory = map_factory
        self._experiment_file_data = experiment_file_data
        self._period_milliseconds = period_milliseconds
        self._radius = radius
        self._selected_scenario_keys: List[SimulationScenarioKey] = []
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._maps: Dict[str, AbstractMap] = {}
        self._figures: List[SimulationFigure] = []
        self._nearest_vector_map: Dict[SemanticMapLayer, List[MapObject]] = {}
        self._async_rendering = async_rendering
        self._plot_render_queue: Optional[Tuple[SimulationFigure, int]] = None
        self._doc.add_periodic_callback(self._periodic_callback, period_milliseconds=1000)
        self._last_frame_time = time.time()
        self._current_frame_index = 0
        self._last_frame_index = 0
        self._playback_callback_handle: Optional[PeriodicCallback] = None
        if frame_rate_cap_hz < 1 or frame_rate_cap_hz > 60:
            raise ValueError('frame_rate_cap_hz should be between 1 and 60')
        self._minimum_frame_time_seconds = 1.0 / float(frame_rate_cap_hz)
        logger.info('Minimum frame time=%4.3f s', self._minimum_frame_time_seconds)

    @property
    def get_figure_data(self) -> List[SimulationFigure]:
        """Return figure data."""
        return self._figures

    @property
    def is_in_playback(self) -> bool:
        """Returns True if we're currently rendering a playback of a figure."""
        return self._playback_callback_handle is not None

    def _on_mouse_move(self, event: PointEvent, figure_index: int) -> None:
        """
        Event when mouse moving in a figure.
        :param event: Point event.
        :param figure_index: Figure index where the mouse is moving.
        """
        main_figure = self._figures[figure_index]
        main_figure.x_y_coordinate_title.text = f'x [m]: {np.round(event.x, simulation_tile_style['decimal_points'])}, y [m]: {np.round(event.y, simulation_tile_style['decimal_points'])}'

    def _create_frame_control_button(self, button_config: ScenarioTabFrameButtonConfig, click_callback: EventCallback, figure_index: int) -> Button:
        """
        Helper function to create a frame control button (prev, play, etc.) based on the provided config.
        :param button_config: Configuration object for the frame control button.
        :param click_callback: Button click event callback that will be registered to the created button.
        :param figure_index: The figure index to be passed to the button's click event callback.
        :return: The created Bokeh Button instance.
        """
        button_instance = Button(label=button_config.label, margin=button_config.margin, css_classes=button_config.css_classes, width=button_config.width)
        button_instance.on_click(partial(click_callback, figure_index=figure_index))
        return button_instance

    def _create_initial_figure(self, figure_index: int, figure_sizes: List[int], backend: Optional[str]='webgl') -> SimulationFigure:
        """
        Create an initial Bokeh figure.
        :param figure_index: Figure index.
        :param figure_sizes: width and height in pixels.
        :param backend: Bokeh figure backend.
        :return: A Bokeh figure.
        """
        selected_scenario_key = self._selected_scenario_keys[figure_index]
        experiment_path = Path(self._experiment_file_data.file_paths[selected_scenario_key.nuboard_file_index].metric_main_path)
        planner_name = selected_scenario_key.planner_name
        presented_planner_name = planner_name + f' ({experiment_path.stem})'
        simulation_figure = Figure(x_range=(-self._radius, self._radius), y_range=(-self._radius, self._radius), width=figure_sizes[0], height=figure_sizes[1], title=f'{presented_planner_name}', tools=['pan', 'wheel_zoom', 'save', 'reset'], match_aspect=True, active_scroll='wheel_zoom', margin=simulation_tile_style['figure_margins'], background_fill_color=simulation_tile_style['background_color'], output_backend=backend)
        simulation_figure.on_event('mousemove', partial(self._on_mouse_move, figure_index=figure_index))
        simulation_figure.axis.visible = False
        simulation_figure.xgrid.visible = False
        simulation_figure.ygrid.visible = False
        simulation_figure.title.text_font_size = simulation_tile_style['figure_title_text_font_size']
        x_y_coordinate_title = Title(text='x [m]: , y [m]: ')
        simulation_figure.add_layout(x_y_coordinate_title, 'below')
        slider = Slider(start=0, end=1, value=0, step=1, title='Frame', margin=simulation_tile_style['slider_margins'], css_classes=['scenario-frame-slider'])
        slider.on_change('value', partial(self._slider_on_change, figure_index=figure_index))
        video_button = Button(label='Render video', margin=simulation_tile_style['video_button_margins'], css_classes=['scenario-video-button'])
        video_button.on_click(partial(self._video_button_on_click, figure_index=figure_index))
        first_button = self._create_frame_control_button(first_button_config, self._first_button_on_click, figure_index)
        prev_button = self._create_frame_control_button(prev_button_config, self._prev_button_on_click, figure_index)
        play_button = self._create_frame_control_button(play_button_config, self._play_button_on_click, figure_index)
        next_button = self._create_frame_control_button(next_button_config, self._next_button_on_click, figure_index)
        last_button = self._create_frame_control_button(last_button_config, self._last_button_on_click, figure_index)
        assert len(selected_scenario_key.files) == 1, 'Expected one file containing the serialized SimulationLog.'
        simulation_file = next(iter(selected_scenario_key.files))
        simulation_log = SimulationLog.load_data(simulation_file)
        simulation_figure_data = SimulationFigure(figure=simulation_figure, file_path_index=selected_scenario_key.nuboard_file_index, figure_title_name=presented_planner_name, slider=slider, video_button=video_button, first_button=first_button, prev_button=prev_button, play_button=play_button, next_button=next_button, last_button=last_button, vehicle_parameters=self._vehicle_parameters, planner_name=planner_name, scenario=simulation_log.scenario, simulation_history=simulation_log.simulation_history, x_y_coordinate_title=x_y_coordinate_title)
        return simulation_figure_data

    def _map_api(self, map_name: str) -> AbstractMap:
        """
        Get a map api.
        :param map_name: Map name.
        :return Map api.
        """
        if map_name not in self._maps:
            self._maps[map_name] = self._map_factory.build_map_from_name(map_name)
        return self._maps[map_name]

    def init_simulations(self, figure_sizes: List[int]) -> None:
        """
        Initialization of the visualization of simulation panel.
        :param figure_sizes: Width and height in pixels.
        """
        self._figures = []
        for figure_index in range(len(self._selected_scenario_keys)):
            simulation_figure = self._create_initial_figure(figure_index=figure_index, figure_sizes=figure_sizes)
            self._figures.append(simulation_figure)

    @property
    def figures(self) -> List[SimulationFigure]:
        """
        Access bokeh figures.
        :return A list of bokeh figures.
        """
        return self._figures

    def _render_simulation_layouts(self) -> List[SimulationData]:
        """
        Render simulation layouts.
        :return: A list of columns or rows.
        """
        grid_layouts: List[SimulationData] = []
        for simulation_figure in self.figures:
            grid_layouts.append(SimulationData(planner_name=simulation_figure.planner_name, simulation_figure=simulation_figure, plot=gridplot([[simulation_figure.slider], [row([simulation_figure.first_button, simulation_figure.prev_button, simulation_figure.play_button, simulation_figure.next_button, simulation_figure.last_button])], [simulation_figure.figure], [simulation_figure.video_button]], toolbar_location='left')))
        return grid_layouts

    def render_simulation_tiles(self, selected_scenario_keys: List[SimulationScenarioKey], figure_sizes: List[int]=simulation_tile_style['figure_sizes'], hidden_glyph_names: Optional[List[str]]=None) -> List[SimulationData]:
        """
        Render simulation tiles.
        :param selected_scenario_keys: A list of selected scenario keys.
        :param figure_sizes: Width and height in pixels.
        :param hidden_glyph_names: A list of glyph names to be hidden.
        :return A list of bokeh layouts.
        """
        self._selected_scenario_keys = selected_scenario_keys
        self.init_simulations(figure_sizes=figure_sizes)
        for main_figure in tqdm(self._figures, desc='Rendering a scenario'):
            self._render_scenario(main_figure, hidden_glyph_names=hidden_glyph_names)
        layouts = self._render_simulation_layouts()
        return layouts

    @gen.coroutine
    @without_document_lock
    def _video_button_on_click(self, figure_index: int) -> None:
        """
        Callback to video button click event.
        Note that this callback in run on a background thread.
        :param figure_index: Figure index.
        """
        self._figures[figure_index].video_button.disabled = True
        self._figures[figure_index].video_button.label = 'Rendering video now...'
        self._executor.submit(self._video_button_next_tick, figure_index)

    def _reset_video_button(self, figure_index: int) -> None:
        """
        Reset a video button after exporting is done.
        :param figure_index: Figure index.
        """
        self.figures[figure_index].video_button.label = 'Render video'
        self.figures[figure_index].video_button.disabled = False

    def _update_video_button_label(self, figure_index: int, label: str) -> None:
        """
        Update a video button label to show progress when rendering a video.
        :param figure_index: Figure index.
        :param label: New video button text.
        """
        self.figures[figure_index].video_button.label = label

    def _video_button_next_tick(self, figure_index: int) -> None:
        """
        Synchronous callback to the video button on click event.
        :param figure_index: Figure index.
        """
        if not len(self._figures):
            return
        images = []
        scenario_key = self._selected_scenario_keys[figure_index]
        scenario_name = scenario_key.scenario_name
        scenario_type = scenario_key.scenario_type
        planner_name = scenario_key.planner_name
        video_name = scenario_type + '_' + planner_name + '_' + scenario_name + '.avi'
        nuboard_file_index = scenario_key.nuboard_file_index
        video_path = Path(self._experiment_file_data.file_paths[nuboard_file_index].simulation_main_path) / 'video_screenshot'
        if not video_path.exists():
            video_path.mkdir(parents=True, exist_ok=True)
        video_save_path = video_path / video_name
        scenario = self.figures[figure_index].scenario
        database_interval = scenario.database_interval
        selected_simulation_figure = self._figures[figure_index]
        try:
            if len(selected_simulation_figure.ego_state_plot.data_sources):
                chrome_options = webdriver.ChromeOptions()
                chrome_options.headless = True
                driver = webdriver.Chrome(chrome_options=chrome_options)
                driver.set_window_size(1920, 1080)
                shape = None
                simulation_figure = self._create_initial_figure(figure_index=figure_index, backend='canvas', figure_sizes=simulation_tile_style['render_figure_sizes'])
                simulation_figure.copy_datasources(selected_simulation_figure)
                self._render_scenario(main_figure=simulation_figure)
                length = len(selected_simulation_figure.ego_state_plot.data_sources)
                for frame_index in tqdm(range(length), desc='Rendering video'):
                    self._render_plots(main_figure=simulation_figure, frame_index=frame_index)
                    image = get_screenshot_as_png(column(simulation_figure.figure), driver=driver)
                    shape = image.size
                    images.append(image)
                    label = f'Rendering video now... ({frame_index}/{length})'
                    self._doc.add_next_tick_callback(partial(self._update_video_button_label, figure_index=figure_index, label=label))
                fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                if database_interval:
                    fps = 1 / database_interval
                else:
                    fps = 20
                video_obj = cv2.VideoWriter(filename=str(video_save_path), fourcc=fourcc, fps=fps, frameSize=shape)
                for index, image in enumerate(images):
                    cv2_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    video_obj.write(cv2_image)
                video_obj.release()
                logger.info('Video saved to %s' % str(video_save_path))
        except (RuntimeError, Exception) as e:
            logger.warning('%s' % e)
        self._doc.add_next_tick_callback(partial(self._reset_video_button, figure_index=figure_index))

    def _first_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the first button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_specific_frame(figure=figure, frame_index=0)

    def _prev_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the prev button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_previous_frame(figure)

    def _play_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the play button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._process_play_request(figure)

    def _next_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the next button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_next_frame(figure)

    def _last_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the last button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_specific_frame(figure=figure, frame_index=len(figure.simulation_history.data) - 1)

    def _slider_on_change(self, attr: str, old: int, frame_index: int, figure_index: int) -> None:
        """
        The function that's called every time the slider's value has changed.
        All frame requests are routed through slider's event handling since currently there's no way to manually
        set the slider's value programatically (to sync the slider value) without triggering this event.
        :param attr: Attribute name.
        :param old: Old value.
        :param frame_index: The new value of the slider, which is the requested frame index.
        :param figure_index: Figure index.
        """
        del attr, old
        selected_figure = self._figures[figure_index]
        self._request_plot_rendering(figure=selected_figure, frame_index=frame_index)

    def _request_specific_frame(self, figure: SimulationFigure, frame_index: int) -> None:
        """
        Requests to render the previous frame of the specified SimulationFigure.
        :param figure: The SimulationFigure render.
        :param frame_index: The frame index to render
        """
        figure.slider.value = frame_index

    def _request_previous_frame(self, figure: SimulationFigure) -> None:
        """
        Requests to render the previous frame of the specified SimulationFigure.
        :param figure: The SimulationFigure render.
        """
        if self._current_frame_index > 0:
            figure.slider.value = self._current_frame_index - 1

    def _request_next_frame(self, figure: SimulationFigure) -> bool:
        """
        Requests to render next frame of the specified SimulationFigure.
        :param figure: The SimulationFigure render.
        :return True if the request is valid, False otherwise.
        """
        result = False
        if self._current_frame_index < len(figure.simulation_history.data) - 1:
            figure.slider.value = self._current_frame_index + 1
            result = True
        return result

    def _request_plot_rendering(self, figure: SimulationFigure, frame_index: int) -> None:
        """
        Request the SimulationTile to render a frame of the plot. The requested frame will be enqueued if frame rate cap
        is reached or the figure is currently rendering a frame.
        :param figure: The SimulationFigure to render.
        :param frame_index: The requested frame index to render.
        """
        current_time = time.time()
        if current_time - self._last_frame_time < self._minimum_frame_time_seconds or figure.is_rendering():
            logger.info('Frame deferred: %d', frame_index)
            self._plot_render_queue = (figure, frame_index)
        else:
            self._process_plot_render_request(figure=figure, frame_index=frame_index)
            self._last_frame_time = time.time()

    def _stop_playback(self, figure: SimulationFigure) -> None:
        """
        Stops the playback for the given figure.
        :param figure: SimulationFigure to stop rendering.
        """
        if self._playback_callback_handle:
            self._doc.remove_periodic_callback(self._playback_callback_handle)
            self._playback_callback_handle = None
            figure.play_button.label = 'play'

    def _start_playback(self, figure: SimulationFigure) -> None:
        """
        Starts the playback for the given figure.
        :param figure: SimulationFigure to stop rendering.
        """
        callback_period_seconds = figure.simulation_history.interval_seconds
        callback_period_seconds = max(self._minimum_frame_time_seconds, callback_period_seconds)
        callback_period_ms = 1000.0 * callback_period_seconds
        self._playback_callback_handle = self._doc.add_periodic_callback(partial(self._playback_callback, figure), callback_period_ms)
        figure.play_button.label = 'stop'

    def _playback_callback(self, figure: SimulationFigure) -> None:
        """The callback that will advance the simulation frame. Will automatically stop the playback once we reach the final frame."""
        if not self._request_next_frame(figure):
            self._stop_playback(figure)

    def _process_play_request(self, figure: SimulationFigure) -> None:
        """
        Processes play request. When play mode is activated, the frame auto-advances, at the rate of the currently set frame rate cap.
        :param figure: The SimulationFigure to render.
        """
        if self._playback_callback_handle:
            self._stop_playback(figure)
        else:
            self._start_playback(figure)

    def _process_plot_render_request(self, figure: SimulationFigure, frame_index: int) -> None:
        """
        Process plot render requests, coming either from the slider or the render queue.
        :param figure: The SimulationFigure to render.
        :param frame_index: The requested frame index to render.
        """
        if frame_index != len(figure.simulation_history.data):
            if self._async_rendering:
                thread = threading.Thread(target=self._render_plots, kwargs={'main_figure': figure, 'frame_index': frame_index}, daemon=True)
                thread.start()
            else:
                self._render_plots(main_figure=figure, frame_index=frame_index)

    def _render_scenario(self, main_figure: SimulationFigure, hidden_glyph_names: Optional[List[str]]=None) -> None:
        """
        Render scenario.
        :param main_figure: Simulation figure object.
        :param hidden_glyph_names: A list of glyph names to be hidden.
        """
        if self._async_rendering:

            def render() -> None:
                """Wrapper for the non-map-dependent parts of the rendering logic."""
                main_figure.update_data_sources()
                self._render_expert_trajectory(main_figure=main_figure)
                mission_goal = main_figure.scenario.get_mission_goal()
                if mission_goal is not None:
                    main_figure.render_mission_goal(mission_goal_state=mission_goal)
                self._render_plots(main_figure=main_figure, frame_index=0, hidden_glyph_names=hidden_glyph_names)

            def render_map_dependent() -> None:
                """Wrapper for the map-dependent parts of the rendering logic."""
                self._load_map_data(main_figure=main_figure)
                main_figure.update_map_dependent_data_sources()
                self._render_map(main_figure=main_figure)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            executor.submit(render)
            executor.submit(render_map_dependent)
            executor.shutdown(wait=False)
        else:
            main_figure.update_data_sources()
            self._load_map_data(main_figure=main_figure)
            main_figure.update_map_dependent_data_sources()
            self._render_map(main_figure=main_figure)
            self._render_expert_trajectory(main_figure=main_figure)
            mission_goal = main_figure.scenario.get_mission_goal()
            if mission_goal is not None:
                main_figure.render_mission_goal(mission_goal_state=mission_goal)
            self._render_plots(main_figure=main_figure, frame_index=0, hidden_glyph_names=hidden_glyph_names)

    def _load_map_data(self, main_figure: SimulationFigure) -> None:
        """
        Load the map data of the simulation tile.
        :param main_figure: Simulation figure.
        """
        map_name = main_figure.scenario.map_api.map_name
        map_api = self._map_api(map_name)
        layer_names = [SemanticMapLayer.LANE_CONNECTOR, SemanticMapLayer.LANE, SemanticMapLayer.CROSSWALK, SemanticMapLayer.INTERSECTION, SemanticMapLayer.STOP_LINE, SemanticMapLayer.WALKWAYS, SemanticMapLayer.CARPARK_AREA]
        assert main_figure.simulation_history.data, 'No simulation history samples, unable to render the map.'
        ego_pose = main_figure.simulation_history.data[0].ego_state.center
        center = Point2D(ego_pose.x, ego_pose.y)
        self._nearest_vector_map = map_api.get_proximal_map_objects(center, self._radius, layer_names)
        if SemanticMapLayer.STOP_LINE in self._nearest_vector_map:
            stop_polygons = self._nearest_vector_map[SemanticMapLayer.STOP_LINE]
            self._nearest_vector_map[SemanticMapLayer.STOP_LINE] = [stop_polygon for stop_polygon in stop_polygons if stop_polygon.stop_line_type != StopLineType.TURN_STOP]
        main_figure.lane_connectors = {lane_connector.id: lane_connector for lane_connector in self._nearest_vector_map[SemanticMapLayer.LANE_CONNECTOR]}

    def _render_map_polygon_layers(self, main_figure: SimulationFigure) -> None:
        """Renders the polygon layers of the map."""
        polygon_layer_names = [(SemanticMapLayer.LANE, simulation_map_layer_color[SemanticMapLayer.LANE]), (SemanticMapLayer.INTERSECTION, simulation_map_layer_color[SemanticMapLayer.INTERSECTION]), (SemanticMapLayer.STOP_LINE, simulation_map_layer_color[SemanticMapLayer.STOP_LINE]), (SemanticMapLayer.CROSSWALK, simulation_map_layer_color[SemanticMapLayer.CROSSWALK]), (SemanticMapLayer.WALKWAYS, simulation_map_layer_color[SemanticMapLayer.WALKWAYS]), (SemanticMapLayer.CARPARK_AREA, simulation_map_layer_color[SemanticMapLayer.CARPARK_AREA])]
        roadblock_ids = main_figure.scenario.get_route_roadblock_ids()
        if roadblock_ids:
            polygon_layer_names.append((SemanticMapLayer.ROADBLOCK, simulation_map_layer_color[SemanticMapLayer.ROADBLOCK]))
        for layer_name, color in polygon_layer_names:
            map_polygon = MapPoint(point_2d=[])
            if layer_name == SemanticMapLayer.ROADBLOCK:
                layer = self._nearest_vector_map[SemanticMapLayer.LANE] + self._nearest_vector_map[SemanticMapLayer.LANE_CONNECTOR]
                for map_obj in layer:
                    roadblock_id = map_obj.get_roadblock_id()
                    if roadblock_id in roadblock_ids:
                        coords = map_obj.polygon.exterior.coords
                        points = [Point2D(x=x, y=y) for x, y in coords]
                        map_polygon.point_2d.append(points)
            else:
                layer = self._nearest_vector_map[layer_name]
                for map_obj in layer:
                    coords = map_obj.polygon.exterior.coords
                    points = [Point2D(x=x, y=y) for x, y in coords]
                    map_polygon.point_2d.append(points)
            polygon_source = ColumnDataSource(dict(xs=map_polygon.polygon_xs, ys=map_polygon.polygon_ys))
            layer_map_polygon_plot = main_figure.figure.multi_polygons(xs='xs', ys='ys', fill_color=color['fill_color'], fill_alpha=color['fill_color_alpha'], line_color=color['line_color'], source=polygon_source)
            layer_map_polygon_plot.level = 'underlay'
            main_figure.map_polygon_plots[layer_name.name] = layer_map_polygon_plot

    def _render_map_line_layers(self, main_figure: SimulationFigure) -> None:
        """Renders the line layers of the map."""
        line_layer_names = [(SemanticMapLayer.LANE, simulation_map_layer_color[SemanticMapLayer.BASELINE_PATHS]), (SemanticMapLayer.LANE_CONNECTOR, simulation_map_layer_color[SemanticMapLayer.LANE_CONNECTOR])]
        for layer_name, color in line_layer_names:
            layer = self._nearest_vector_map[layer_name]
            map_line = MapPoint(point_2d=[])
            for map_obj in layer:
                path = map_obj.baseline_path.discrete_path
                points = [Point2D(x=pose.x, y=pose.y) for pose in path]
                map_line.point_2d.append(points)
            line_source = ColumnDataSource(dict(xs=map_line.line_xs, ys=map_line.line_ys))
            layer_map_line_plot = main_figure.figure.multi_line(xs='xs', ys='ys', line_color=color['line_color'], line_alpha=color['line_color_alpha'], line_width=0.5, line_dash='dashed', source=line_source)
            layer_map_line_plot.level = 'underlay'
            main_figure.map_line_plots[layer_name.name] = layer_map_line_plot

    def _render_map(self, main_figure: SimulationFigure) -> None:
        """
        Render a map.
        :param main_figure: Simulation figure.
        """

        def render() -> None:
            """Wrapper for the actual render logic, for multi-threading compatibility."""
            self._render_map_polygon_layers(main_figure)
            self._render_map_line_layers(main_figure)
        self._doc.add_next_tick_callback(lambda: render())

    @staticmethod
    def _render_expert_trajectory(main_figure: SimulationFigure) -> None:
        """
        Render expert trajectory.
        :param main_figure: Main simulation figure.
        """
        expert_ego_trajectory = main_figure.scenario.get_expert_ego_trajectory()
        source = extract_source_from_states(expert_ego_trajectory)
        main_figure.render_expert_trajectory(expert_ego_trajectory_state=source)

    def _render_plots(self, main_figure: SimulationFigure, frame_index: int, hidden_glyph_names: Optional[List[str]]=None) -> None:
        """
        Render plot with a frame index.
        :param main_figure: Main figure to render.
        :param frame_index: A frame index.
        :param hidden_glyph_names: A list of glyph names to be hidden.
        """
        if main_figure.lane_connectors is not None and len(main_figure.lane_connectors):
            main_figure.traffic_light_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)
        main_figure.ego_state_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, radius=self._radius, doc=self._doc)
        main_figure.ego_state_trajectory_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)
        main_figure.agent_state_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)
        main_figure.agent_state_heading_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)

        def update_decorations() -> None:
            main_figure.figure.title.text = main_figure.figure_title_name_with_timestamp(frame_index=frame_index)
            main_figure.update_glyphs_visibility(glyph_names=hidden_glyph_names)
        self._doc.add_next_tick_callback(lambda: update_decorations())
        self._last_frame_index = self._current_frame_index
        self._current_frame_index = frame_index

    def _periodic_callback(self) -> None:
        """Periodic callback registered to the bokeh.Document."""
        if self._plot_render_queue:
            figure, frame_index = self._plot_render_queue
            last_frame_direction = math.copysign(1, self._current_frame_index - self._last_frame_index)
            request_frame_direction = math.copysign(1, frame_index - self._current_frame_index)
            if request_frame_direction != last_frame_direction:
                logger.info('Frame dropped %d', frame_index)
                self._plot_render_queue = None
            elif not figure.is_rendering():
                logger.info('Processing render queue for frame %d', frame_index)
                self._plot_render_queue = None
                self._process_plot_render_request(figure=figure, frame_index=frame_index)

def _request_plot_rendering(self, figure: SimulationFigure, frame_index: int) -> None:
    """
        Request the SimulationTile to render a frame of the plot. The requested frame will be enqueued if frame rate cap
        is reached or the figure is currently rendering a frame.
        :param figure: The SimulationFigure to render.
        :param frame_index: The requested frame index to render.
        """
    current_time = time.time()
    if current_time - self._last_frame_time < self._minimum_frame_time_seconds or figure.is_rendering():
        logger.info('Frame deferred: %d', frame_index)
        self._plot_render_queue = (figure, frame_index)
    else:
        self._process_plot_render_request(figure=figure, frame_index=frame_index)
        self._last_frame_time = time.time()

def _process_plot_render_request(self, figure: SimulationFigure, frame_index: int) -> None:
    """
        Process plot render requests, coming either from the slider or the render queue.
        :param figure: The SimulationFigure to render.
        :param frame_index: The requested frame index to render.
        """
    if frame_index != len(figure.simulation_history.data):
        if self._async_rendering:
            thread = threading.Thread(target=self._render_plots, kwargs={'main_figure': figure, 'frame_index': frame_index}, daemon=True)
            thread.start()
        else:
            self._render_plots(main_figure=figure, frame_index=frame_index)

def _periodic_callback(self) -> None:
    """Periodic callback registered to the bokeh.Document."""
    if self._plot_render_queue:
        figure, frame_index = self._plot_render_queue
        last_frame_direction = math.copysign(1, self._current_frame_index - self._last_frame_index)
        request_frame_direction = math.copysign(1, frame_index - self._current_frame_index)
        if request_frame_direction != last_frame_direction:
            logger.info('Frame dropped %d', frame_index)
            self._plot_render_queue = None
        elif not figure.is_rendering():
            logger.info('Processing render queue for frame %d', frame_index)
            self._plot_render_queue = None
            self._process_plot_render_request(figure=figure, frame_index=frame_index)

class TestSimulationTile(unittest.TestCase):
    """Test simulation_tile functionality."""

    def set_up_simulation_log(self, output_path: Path) -> None:
        """
        Create a simulation log and save it to disk.
        :param output path: to write the simulation log to.
        """
        simulation_log = create_sample_simulation_log(output_path)
        simulation_log.save_to_file()

    def setUp(self) -> None:
        """Set up simulation tile with nuboard file."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.vehicle_parameters = get_pacifica_parameters()
        simulation_log_path = Path(self.tmp_dir.name) / 'test_simulation_tile_simulation_log.msgpack.xz'
        self.set_up_simulation_log(simulation_log_path)
        nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulation', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        self.scenario_keys = [SimulationScenarioKey(nuboard_file_index=0, log_name='dummy_log', planner_name='SimplePlanner', scenario_type='common', scenario_name='test', files=[simulation_log_path])]
        self.doc = Document()
        self.map_factory = MockMapFactory()
        self.experiment_file_data = ExperimentFileData(file_paths=[nuboard_file])
        self.simulation_tile = SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)

    @given(frame_rate_cap=st.integers(min_value=1, max_value=60))
    def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests valid frame rate cap range."""
        SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

    @given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
    def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests invalid frame rate cap range."""
        with self.assertRaises(ValueError):
            SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

    def test_simulation_tile_layout(self) -> None:
        """Test layout design."""
        layout = self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        self.assertEqual(len(layout), 1)

    def test_periodic_callback(self) -> None:
        """Tests that _periodic_callback is registered correctly to the bokeh Document."""
        with patch.object(SimulationTile, '_periodic_callback', autospec=True) as mock_periodic_callback:
            SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)
            for cb in self.doc.callbacks.session_callbacks:
                cb.callback()
            self.assertEqual(mock_periodic_callback.call_count, 1)

    def _trigger_button_click_event(self, figure_index: int, button_name: str) -> None:
        """
        Trigger a bokeh.model.Button click event.
        :param figure_index: The index of the SimulationTile figure.
        :param button_name: The name of SimulationTile button.
        """
        button = getattr(self.simulation_tile.figures[figure_index], button_name)
        button._trigger_event(ButtonClick(button))

    def _test_frame_index_request_button(self, button_name: str, frame_index_request: FrameIndexRequest) -> None:
        """
        Helper function to test that frame index request buttons (first, prev, next, last) work correctly.
        :param click_callback_name: Button click callback function name in SimulationTile that's registered to bokeh.
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_index_request: FrameIndexRequest object representing the frame index requested.
        """
        with patch.object(self.simulation_tile, '_render_plots'):
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            figure = self.simulation_tile.figures[figure_index]
            if frame_index_request == FrameIndexRequest.FIRST or frame_index_request == FrameIndexRequest.LAST:
                self._trigger_button_click_event(figure_index, button_name)
                frame_index = len(figure.simulation_history) - 1 if frame_index_request == FrameIndexRequest.LAST else 0
                self.assertEqual(figure.slider.value, frame_index)
            elif frame_index_request == FrameIndexRequest.NEXT:
                self.simulation_tile._current_frame_index = 0
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index + 1)
                self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)
            elif frame_index_request == FrameIndexRequest.PREV:
                self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index - 1)
                self.simulation_tile._current_frame_index = 0
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)

    def test_first_frame_button(self) -> None:
        """Tests that go to first frame button works correctly."""
        self._test_frame_index_request_button(button_name='first_button', frame_index_request=FrameIndexRequest.FIRST)

    def test_last_frame_button(self) -> None:
        """Tests that go to last frame button works correctly."""
        self._test_frame_index_request_button(button_name='last_button', frame_index_request=FrameIndexRequest.LAST)

    def _test_symbolic_frame_request_callback_called(self, button_name: str, frame_request_callback_name: str) -> None:
        """
        Helper function to test that the provided symbolic frame request (previous, next, play/stop) callback is called when a button is clicked
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_request_callback_name: Frame request callback function name in SimulationTile that's supposed to be called.
        """
        with patch.object(self.simulation_tile, frame_request_callback_name, autospec=True) as mock_request_frame:
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            button = getattr(self.simulation_tile.figures[figure_index], button_name)
            button._trigger_event(ButtonClick(button))
            mock_request_frame.assert_called_once_with(self.simulation_tile.figures[figure_index])

    def test_prev_button(self) -> None:
        """Tests that show prev frame button works correctly."""
        self._test_frame_index_request_button(button_name='prev_button', frame_index_request=FrameIndexRequest.PREV)

    def test_next_button(self) -> None:
        """Tests that show next frame button works correctly."""
        self._test_frame_index_request_button(button_name='next_button', frame_index_request=FrameIndexRequest.NEXT)

    def test_play_button(self) -> None:
        """Tests that the play button works correctly."""
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        button_name = 'play_button'
        self.assertFalse(self.simulation_tile.is_in_playback)
        self._trigger_button_click_event(figure_index, button_name)
        self.assertTrue(self.simulation_tile.is_in_playback)
        self._trigger_button_click_event(figure_index, button_name)
        self.assertFalse(self.simulation_tile.is_in_playback)

    def test_playback_callback(self) -> None:
        """Tests that the playback callback is registered correctly to the bokeh Document & behaves correctly."""
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        figure = self.simulation_tile.figures[figure_index]
        button_name = 'play_button'
        previous_request_index = figure.slider.value
        self._trigger_button_click_event(figure_index, button_name)
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertTrue(self.simulation_tile.is_in_playback)
        self.assertTrue(figure.slider.value, previous_request_index + 1)
        self.simulation_tile._current_frame_index = len(figure.simulation_history) - 1
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertFalse(self.simulation_tile.is_in_playback)

    def test_deferred_plot_rendering(self) -> None:
        """Tests that plot rendering request will be deferred if successive requests are triggered faster than the frame rate cap configured."""
        self.assertIsNone(self.simulation_tile._plot_render_queue)
        with patch.object(self.simulation_tile, '_last_frame_time', new=time.time()):
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            figure = self.simulation_tile.figures[figure_index]
            trigger_count = 2
            for _ in range(trigger_count):
                figure.slider.trigger(attr='value', old=0, new=1)
            self.assertIsNotNone(self.simulation_tile._plot_render_queue)

    def tearDown(self) -> None:
        """Clean up temporary folder and files."""
        self.tmp_dir.cleanup()

@given(frame_rate_cap=st.integers(min_value=1, max_value=60))
def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
    """Tests valid frame rate cap range."""
    SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

@given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
    """Tests invalid frame rate cap range."""
    with self.assertRaises(ValueError):
        SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

class TestNuBoard(unittest.TestCase):
    """Test nuboard functionality."""

    def setUp(self) -> None:
        """Set up nuboard a bokeh main page."""
        self.vehicle_parameters = get_pacifica_parameters()
        self.doc = Document()
        self.scenario_builder = MockAbstractScenarioBuilder()
        self.tmp_dir = tempfile.TemporaryDirectory()
        if not os.getenv('NUPLAN_EXP_ROOT', None):
            os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric')
        metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.main_paths = [str(self.nuboard_file_name)]
        self.nuboard = NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters)

    def test_main_page(self) -> None:
        """Test if successfully construct a bokeh main page."""
        self.nuboard.main_page(doc=self.doc)
        self.assertEqual(len(self.doc.roots), 34)

    @given(frame_rate_cap=st.integers(min_value=1, max_value=60))
    def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests valid frame rate cap range."""
        NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters, scenario_rendering_frame_rate_cap_hz=frame_rate_cap)

    @given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
    def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests invalid frame rate cap range."""
        with self.assertRaises(ValueError):
            NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters, scenario_rendering_frame_rate_cap_hz=frame_rate_cap)

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

@given(frame_rate_cap=st.integers(min_value=1, max_value=60))
def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
    """Tests valid frame rate cap range."""
    NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters, scenario_rendering_frame_rate_cap_hz=frame_rate_cap)

@given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
    """Tests invalid frame rate cap range."""
    with self.assertRaises(ValueError):
        NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters, scenario_rendering_frame_rate_cap_hz=frame_rate_cap)

def initialize_nuboard(cfg: DictConfig) -> NuBoard:
    """
    Sets up dependencies and instantiates a NuBoard object.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: NuBoard object.
    """
    update_config_for_nuboard(cfg=cfg)
    scenario_builder = build_scenario_builder(cfg)
    vehicle_parameters: VehicleParameters = instantiate(cfg.scenario_builder.vehicle_parameters)
    profiler_path = None
    if cfg.profiler_path:
        profiler_path = Path(cfg.profiler_path)
    nuboard = NuBoard(profiler_path=profiler_path, nuboard_paths=cfg.simulation_path, scenario_builder=scenario_builder, port_number=cfg.port_number, resource_prefix=cfg.resource_prefix, vehicle_parameters=vehicle_parameters, async_scenario_rendering=cfg.async_scenario_rendering, scenario_rendering_frame_rate_cap_hz=cfg.scenario_rendering_frame_rate_cap_hz)
    return nuboard

def set_default_path() -> None:
    """
    This function sets the default paths as environment variables if none are set.
    These can then be used by Hydra, unless the user overwrites them from the command line.
    """
    if 'NUPLAN_DATA_ROOT' not in os.environ:
        logger.info(f'Setting default NUPLAN_DATA_ROOT: {DEFAULT_DATA_ROOT}')
        os.environ['NUPLAN_DATA_ROOT'] = DEFAULT_DATA_ROOT
    if 'NUPLAN_EXP_ROOT' not in os.environ:
        logger.info(f'Setting default NUPLAN_EXP_ROOT: {DEFAULT_EXP_ROOT}')
        os.environ['NUPLAN_EXP_ROOT'] = DEFAULT_EXP_ROOT

def set_up_common_builder(cfg: DictConfig, profiler_name: str) -> CommonBuilder:
    """
    Set up a common builder when running simulations.
    :param cfg: Hydra configuration.
    :param profiler_name: Profiler name.
    :return A data classes with common builders.
    """
    multi_main_callback = build_main_multi_callback(cfg)
    multi_main_callback.on_run_simulation_start()
    update_config_for_simulation(cfg=cfg)
    build_logger(cfg)
    worker = build_worker(cfg)
    build_simulation_experiment_folder(cfg=cfg)
    output_dir = Path(cfg.output_dir)
    profiler = None
    if cfg.enable_profiling:
        logger.info('Profiler is enabled!')
        profiler = ProfileCallback(output_dir=output_dir)
    if profiler:
        profiler.start_profiler(profiler_name)
    return CommonBuilder(worker=worker, multi_main_callback=multi_main_callback, output_dir=output_dir, profiler=profiler)

def run_runners(runners: List[AbstractRunner], common_builder: CommonBuilder, profiler_name: str, cfg: DictConfig) -> None:
    """
    Run a list of runners.
    :param runners: A list of runners.
    :param common_builder: Common builder.
    :param profiler_name: Profiler name.
    :param cfg: Hydra config.
    """
    assert len(runners) > 0, 'No scenarios found to simulate!'
    if common_builder.profiler:
        common_builder.profiler.start_profiler(profiler_name)
    logger.info('Executing runners...')
    reports = execute_runners(runners=runners, worker=common_builder.worker, num_gpus=cfg.number_of_gpus_allocated_per_simulation, num_cpus=cfg.number_of_cpus_allocated_per_simulation, exit_on_failure=cfg.exit_on_failure, verbose=cfg.verbose)
    logger.info('Finished executing runners!')
    save_runner_reports(reports, common_builder.output_dir, cfg.runner_report_file)
    distributed_sync(Path(cfg.output_dir / Path('barrier')), cfg.distributed_timeout_seconds)
    if int(os.environ.get('NODE_RANK', 0)) == 0:
        common_builder.multi_main_callback.on_run_simulation_end()
    if common_builder.profiler:
        common_builder.profiler.save_profiler(profiler_name)

def run_simulation(cfg: DictConfig, planners: Optional[Union[AbstractPlanner, List[AbstractPlanner]]]=None) -> None:
    """
    Execute all available challenges simultaneously on the same scenario. Helper function for main to allow planner to
    be specified via config or directly passed as argument.
    :param cfg: Configuration that is used to run the experiment.
        Already contains the changes merged from the experiment's config to default config.
    :param planners: Pre-built planner(s) to run in simulation. Can either be a single planner or list of planners.
    """
    pl.seed_everything(cfg.seed, workers=True)
    profiler_name = 'building_simulation'
    common_builder = set_up_common_builder(cfg=cfg, profiler_name=profiler_name)
    callbacks_worker_pool = build_callbacks_worker(cfg)
    callbacks = build_simulation_callbacks(cfg=cfg, output_dir=common_builder.output_dir, worker=callbacks_worker_pool)
    if planners and 'planner' in cfg.keys():
        logger.info('Using pre-instantiated planner. Ignoring planner in config')
        OmegaConf.set_struct(cfg, False)
        cfg.pop('planner')
        OmegaConf.set_struct(cfg, True)
    if isinstance(planners, AbstractPlanner):
        planners = [planners]
    runners = build_simulations(cfg=cfg, callbacks=callbacks, worker=common_builder.worker, pre_built_planners=planners, callbacks_worker=callbacks_worker_pool)
    if common_builder.profiler:
        common_builder.profiler.save_profiler(profiler_name)
    logger.info('Running simulation...')
    run_runners(runners=runners, common_builder=common_builder, cfg=cfg, profiler_name='running_simulation')
    logger.info('Finished running simulation!')

def clean_up_s3_artifacts() -> None:
    """
    Cleanup lingering s3 artifacts that are written locally.
    This happens because some minor write-to-s3 functionality isn't yet implemented.
    """
    working_path = os.getcwd()
    s3_dirname = 's3:'
    s3_ind = working_path.find(s3_dirname)
    if s3_ind != -1:
        local_s3_path = working_path[:working_path.find(s3_dirname) + len(s3_dirname)]
        rmtree(local_s3_path)

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> Optional[TrainingEngine]:
    """
    Main entrypoint for training/validation experiments.
    :param cfg: omegaconf dictionary
    """
    pl.seed_everything(cfg.seed, workers=True)
    build_logger(cfg)
    update_config_for_training(cfg)
    build_training_experiment_folder(cfg=cfg)
    worker = build_worker(cfg)
    if cfg.py_func == 'train':
        with ProfilerContextManager(cfg.output_dir, cfg.enable_profiling, 'build_training_engine'):
            engine = build_training_engine(cfg, worker)
        logger.info('Starting training...')
        with ProfilerContextManager(cfg.output_dir, cfg.enable_profiling, 'training'):
            engine.trainer.fit(model=engine.model, datamodule=engine.datamodule)
        return engine
    elif cfg.py_func == 'test':
        with ProfilerContextManager(cfg.output_dir, cfg.enable_profiling, 'build_training_engine'):
            engine = build_training_engine(cfg, worker)
        logger.info('Starting testing...')
        with ProfilerContextManager(cfg.output_dir, cfg.enable_profiling, 'testing'):
            engine.trainer.test(model=engine.model, datamodule=engine.datamodule)
        return engine
    elif cfg.py_func == 'cache':
        logger.info('Starting caching...')
        if cfg.worker == 'ray_distributed' and cfg.worker.use_distributed:
            raise AssertionError('ray in distributed mode will not work with this job')
        with ProfilerContextManager(cfg.output_dir, cfg.enable_profiling, 'caching'):
            cache_data(cfg=cfg, worker=worker)
        return None
    else:
        raise NameError(f'Function {cfg.py_func} does not exist')

class ProfilerContextManager:
    """
    Class to wrap calls with a profiler callback.
    """

    def __init__(self, output_dir: str, enable_profiling: bool, name: str):
        """
        Build a profiler context.
        :param output_dir: dir to save profiling results in
        :param enable_profiling: whether we have profiling enabled or not
        :param name: name of the code segment we are profiling
        """
        self.profiler = ProfileCallback(pathlib.Path(output_dir)) if enable_profiling else None
        self.name = name

    def __enter__(self) -> None:
        """Start the profiler context."""
        if self.profiler:
            self.profiler.start_profiler(self.name)

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
        """
        Stop the profiler context and save the results.
        :param exc_type: type of exception raised while context is active
        :param exc_val: value of exception raised while context is active
        :param exc_tb: traceback of exception raised while context is active
        """
        if self.profiler:
            self.profiler.save_profiler(self.name)

def __init__(self, output_dir: str, enable_profiling: bool, name: str):
    """
        Build a profiler context.
        :param output_dir: dir to save profiling results in
        :param enable_profiling: whether we have profiling enabled or not
        :param name: name of the code segment we are profiling
        """
    self.profiler = ProfileCallback(pathlib.Path(output_dir)) if enable_profiling else None
    self.name = name

def __enter__(self) -> None:
    """Start the profiler context."""
    if self.profiler:
        self.profiler.start_profiler(self.name)

def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> None:
    """
        Stop the profiler context and save the results.
        :param exc_type: type of exception raised while context is active
        :param exc_val: value of exception raised while context is active
        :param exc_tb: traceback of exception raised while context is active
        """
    if self.profiler:
        self.profiler.save_profiler(self.name)

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> None:
    """
    Execute metrics with simulation logs only.
    :param cfg: Configuration that is used to run the experiment.
        Already contains the changes merged from the experiment's config to default config.
    """
    assert cfg.simulation_log_main_path is not None, 'Simulation_log_main_path must be set when running metrics.'
    pl.seed_everything(cfg.seed, workers=True)
    profiler_name = 'building_metrics'
    common_builder = set_up_common_builder(cfg=cfg, profiler_name=profiler_name)
    simulation_logs = build_simulation_logs(cfg=cfg)
    runners = build_metric_runners(cfg=cfg, simulation_logs=simulation_logs)
    if common_builder.profiler:
        common_builder.profiler.save_profiler(profiler_name)
    logger.info('Running metrics...')
    run_runners(runners=runners, common_builder=common_builder, cfg=cfg, profiler_name='running_metrics')
    logger.info('Finished running metrics!')

def _build_planner(planner_cfg: DictConfig, scenario: Optional[AbstractScenario]) -> AbstractPlanner:
    """
    Instantiate planner
    :param planner_cfg: config of a planner
    :param scenario: scenario
    :return AbstractPlanner
    """
    config = planner_cfg.copy()
    if is_target_type(planner_cfg, MLPlanner):
        torch_module_wrapper = build_torch_module_wrapper(planner_cfg.model_config)
        model = LightningModuleWrapper.load_from_checkpoint(planner_cfg.checkpoint_path, model=torch_module_wrapper).model
        OmegaConf.set_struct(config, False)
        config.pop('model_config')
        config.pop('checkpoint_path')
        OmegaConf.set_struct(config, True)
        planner: AbstractPlanner = instantiate(config, model=model)
    else:
        planner_cls: Type[AbstractPlanner] = _locate(config._target_)
        if planner_cls.requires_scenario:
            assert scenario is not None, f'Scenario was not provided to build the planner. Planner {config} can not be build!'
            planner = cast(AbstractPlanner, instantiate(config, scenario=scenario))
        else:
            planner = cast(AbstractPlanner, instantiate(config))
    return planner

def build_lr_scheduler(optimizer: Optimizer, lr: float, warm_up_lr_scheduler_cfg: Optional[DictConfig], lr_scheduler_cfg: Optional[DictConfig]) -> _LRScheduler:
    """
    :param optimizer: Optimizer object
    :param lr: Initial learning rate to be used. If using OneCycleLR, this will be the max learning rate to be used instead.
    :param lr_warm_up: DictConfig for warm up scheduler
    :param lr_scheduler: DictConfig for actual scheduler
    :return: aggregate lr_scheduler
    """
    lr_scheduler_params: Dict[str, Any] = {}
    if lr_scheduler_cfg is not None:
        lr_scheduler_params = _instantiate_main_lr_scheduler(optimizer=optimizer, lr_scheduler_cfg=lr_scheduler_cfg, lr=lr)
        logger.info(f'Using lr_scheduler provided: {lr_scheduler_cfg._target_}')
    if warm_up_lr_scheduler_cfg is not None:
        initial_lr = _get_lr_from_optimizer(optimizer)
        lr_scheduler_params = _instantiate_warm_up_lr_scheduler(optimizer=optimizer, warm_up_lr_scheduler_cfg=warm_up_lr_scheduler_cfg, initial_lr=initial_lr, lr_scheduler_params=lr_scheduler_params)
    else:
        logger.info('Not using any lr_schedulers.')
    return lr_scheduler_params

def _instantiate_main_lr_scheduler(optimizer: Optimizer, lr_scheduler_cfg: DictConfig, lr: float) -> Dict[str, Any]:
    """
    Instantiates the main learning rate scheduler to be used during training.
    :param optimizer: Optimizer used for training.
    :param lr_scheduler_cfg: Learning rate scheduler config
    :param lr: Learning rate to be used. If using OneCycleLR, then this is the maximum learning rate to be reached during training.
    :return: Learning rate scheduler and associated parameters
    """
    lr_scheduler_params: Dict[str, Any] = {}
    if is_target_type(lr_scheduler_cfg, OneCycleLR):
        lr_scheduler_cfg.max_lr = lr
        lr_scheduler_params['interval'] = 'step'
        frequency_of_lr_scheduler_step = lr_scheduler_cfg.epochs
        lr_scheduler_params['frequency'] = frequency_of_lr_scheduler_step
        logger.info(f'lr_scheduler.step() will be called every {frequency_of_lr_scheduler_step} batches')
    lr_scheduler: _LRScheduler = instantiate(config=lr_scheduler_cfg, optimizer=optimizer)
    lr_scheduler_params['scheduler'] = lr_scheduler
    return lr_scheduler_params

def _instantiate_warm_up_lr_scheduler(optimizer: Optimizer, warm_up_lr_scheduler_cfg: DictConfig, initial_lr: float, lr_scheduler_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Instantiates the warm up learning rate scheduler to be used during training.
    :param optimizer: Optimizer used for training.
    :param warm_up_lr_scheduler_cfg: Learning rate scheduler config for warm_up phase
    :param initial_lr: Initial learning rate. To be scaled down further during warm_up phase.
    :param lr: Learning rate to be used. If using OneCycleLR, then this is the maximum learning rate to be reached during training.
    :return: Learning rate scheduler and associated parameters
    """
    using_main_lr_scheduler = 'scheduler' in lr_scheduler_params
    if using_main_lr_scheduler:
        warm_up_lr_scheduler = instantiate(config=warm_up_lr_scheduler_cfg, optimizer=optimizer, lr_lambda=instantiate(config=warm_up_lr_scheduler_cfg.lr_lambda, final_div_factor=1.0))
        lr_schedulers = [warm_up_lr_scheduler, lr_scheduler_params['scheduler']]
        sequential_lr_scheduler = SequentialLR(optimizer=optimizer, schedulers=lr_schedulers, milestones=[warm_up_lr_scheduler_cfg.lr_lambda.warm_up_steps])
        lr_scheduler_params['scheduler'] = sequential_lr_scheduler
        logger.info(f'Added Warm up learning rate scheduler before main scheduler with {warm_up_lr_scheduler_cfg.lr_lambda.warm_up_strategy} strategy.')
    else:
        warm_up_lr_scheduler = instantiate(config=warm_up_lr_scheduler_cfg, optimizer=optimizer, lr_lambda=instantiate(config=warm_up_lr_scheduler_cfg.lr_lambda, final_div_factor=1.0))
        warm_up_phase_initial_lr = initial_lr / warm_up_lr_scheduler_cfg.lr_lambda.warm_up_steps
        for group in optimizer.param_groups:
            group['initial_lr'] = warm_up_phase_initial_lr
        lr_scheduler_params['scheduler'] = warm_up_lr_scheduler
        logger.info(f'Using Warm up learning rate scheduler with {warm_up_lr_scheduler_cfg.lr_lambda.warm_up_strategy} strategy.')
    return lr_scheduler_params

def build_simulation_callbacks(cfg: DictConfig, output_dir: pathlib.Path, worker: Optional[WorkerPool]=None) -> List[AbstractCallback]:
    """
    Builds callback.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :param output_dir: directory for all experiment results.
    :param worker: to run certain callbacks in the background (everything runs in main process if None).
    :return: List of callbacks.
    """
    logger.info('Building AbstractCallback...')
    callbacks = []
    for config in cfg.callback.values():
        if is_target_type(config, SerializationCallback):
            callback: SerializationCallback = instantiate(config, output_directory=output_dir)
        elif is_target_type(config, TimingCallback):
            tensorboard = torch.utils.tensorboard.SummaryWriter(log_dir=output_dir)
            callback = instantiate(config, writer=tensorboard)
        elif is_target_type(config, SimulationLogCallback) or is_target_type(config, MetricCallback):
            continue
        else:
            callback = instantiate(config)
        validate_type(callback, AbstractCallback)
        callbacks.append(callback)
    logger.info(f'Building AbstractCallback: {len(callbacks)}...DONE!')
    return callbacks

def build_main_multi_callback(cfg: DictConfig) -> MultiMainCallback:
    """
    Build a multi main callback.
    :param cfg: Configuration that is used to run the experiment.
    """
    logger.info('Building MultiMainCallback...')
    main_callbacks = []
    for callback_name, config in cfg.main_callback.items():
        if is_target_type(config, MetricAggregatorCallback):
            metric_aggregators = build_metrics_aggregators(cfg)
            callback: MetricAggregatorCallback = instantiate(config, metric_aggregators=metric_aggregators)
        else:
            callback = instantiate(config)
        validate_type(callback, AbstractMainCallback)
        main_callbacks.append(callback)
    multi_main_callback = MultiMainCallback(main_callbacks)
    logger.info(f'Building MultiMainCallback: {len(multi_main_callback)}...DONE!')
    return multi_main_callback

def build_objectives(cfg: DictConfig) -> List[AbstractObjective]:
    """
    Build objectives based on config
    :param cfg: config
    :return list of objectives.
    """
    instantiated_objectives = []
    scenario_type_loss_weighting = cfg.scenario_type_weights.scenario_type_loss_weights if 'scenario_type_weights' in cfg and 'scenario_type_loss_weights' in cfg.scenario_type_weights else {}
    for objective_name, objective_type in cfg.objective.items():
        new_objective: AbstractObjective = instantiate(objective_type, scenario_type_loss_weighting=scenario_type_loss_weighting)
        validate_type(new_objective, AbstractObjective)
        instantiated_objectives.append(new_objective)
    return instantiated_objectives

def build_trainer(cfg: DictConfig) -> pl.Trainer:
    """
    Builds the lightning trainer from the config.
    :param cfg: omegaconf dictionary
    :return: built object.
    """
    params = cfg.lightning.trainer.params
    callbacks = build_callbacks(cfg)
    plugins = [pl.plugins.DDPPlugin(find_unused_parameters=False, num_nodes=params.num_nodes)]
    loggers = [pl.loggers.TensorBoardLogger(save_dir=cfg.group, name=cfg.experiment, log_graph=False, version='', prefix='')]
    if cfg.lightning.trainer.overfitting.enable:
        OmegaConf.set_struct(cfg, False)
        params = OmegaConf.merge(params, cfg.lightning.trainer.overfitting.params)
        params.check_val_every_n_epoch = params.max_epochs + 1
        OmegaConf.set_struct(cfg, True)
        return pl.Trainer(plugins=plugins, **params)
    if cfg.lightning.trainer.checkpoint.resume_training:
        output_dir = Path(cfg.output_dir)
        date_format = cfg.date_format
        OmegaConf.set_struct(cfg, False)
        last_checkpoint = extract_last_checkpoint_from_experiment(output_dir, date_format)
        if not last_checkpoint:
            raise ValueError('Resume Training is enabled but no checkpoint was found!')
        params.resume_from_checkpoint = str(last_checkpoint)
        latest_epoch = torch.load(last_checkpoint)['epoch']
        params.max_epochs += latest_epoch
        logger.info(f'Resuming at epoch {latest_epoch} from checkpoint {last_checkpoint}')
        OmegaConf.set_struct(cfg, True)
    trainer = pl.Trainer(callbacks=callbacks, plugins=plugins, logger=loggers, **params)
    return trainer

def build_splitter(cfg: DictConfig) -> AbstractSplitter:
    """
    Build the splitter.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: Instance of Splitter.
    """
    logger.info('Building Splitter...')
    splitter: AbstractSplitter = instantiate(cfg)
    validate_type(splitter, AbstractSplitter)
    logger.info('Building Splitter...DONE!')
    return splitter

def build_worker(cfg: DictConfig) -> WorkerPool:
    """
    Builds the worker.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: Instance of WorkerPool.
    """
    logger.info('Building WorkerPool...')
    worker: WorkerPool = instantiate(cfg.worker, output_dir=cfg.output_dir) if is_target_type(cfg.worker, RayDistributed) else instantiate(cfg.worker)
    validate_type(worker, WorkerPool)
    logger.info('Building WorkerPool...DONE!')
    return worker

def build_scenario_builder(cfg: DictConfig) -> AbstractScenarioBuilder:
    """
    Builds scenario builder.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: Instance of scenario builder.
    """
    logger.info('Building AbstractScenarioBuilder...')
    scenario_builder = instantiate(cfg.scenario_builder)
    validate_type(scenario_builder, AbstractScenarioBuilder)
    logger.info('Building AbstractScenarioBuilder...DONE!')
    return scenario_builder

def build_training_metrics(cfg: DictConfig) -> List[AbstractTrainingMetric]:
    """
    Build metrics based on config
    :param cfg: config
    :return list of metrics.
    """
    instantiated_metrics = []
    for metric_name, cfg_metric in cfg.training_metric.items():
        new_metric: AbstractTrainingMetric = instantiate(cfg_metric)
        validate_type(new_metric, AbstractTrainingMetric)
        instantiated_metrics.append(new_metric)
    return instantiated_metrics

def build_scenario_filter(cfg: DictConfig) -> ScenarioFilter:
    """
    Builds the scenario filter.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :param db: dabatase.
    :return: Instance of ScenarioFilter.
    """
    logger.info('Building ScenarioFilter...')
    if cfg.scenario_tokens and (not all(map(is_valid_token, cfg.scenario_tokens))):
        raise RuntimeError('Expected all scenario tokens to be 16-character strings. Your shell may strip quotes causing hydra to parse a token as a float, so consider passing them like scenario_filter.scenario_tokens=\'["595322e649225137", ...]\'')
    scenario_filter: ScenarioFilter = instantiate(cfg)
    validate_type(scenario_filter, ScenarioFilter)
    logger.info('Building ScenarioFilter...DONE!')
    return scenario_filter

def build_torch_module_wrapper(cfg: DictConfig) -> TorchModuleWrapper:
    """
    Builds the NN module.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: Instance of TorchModuleWrapper.
    """
    logger.info('Building TorchModuleWrapper...')
    model = instantiate(cfg)
    validate_type(model, TorchModuleWrapper)
    logger.info('Building TorchModuleWrapper...DONE!')
    return model

def build_callbacks(cfg: DictConfig) -> List[pl.Callback]:
    """
    Build callbacks based on config.
    :param cfg: Dict config.
    :return List of callbacks.
    """
    logger.info('Building callbacks...')
    instantiated_callbacks = []
    for callback_type in cfg.callbacks.values():
        callback: pl.Callback = instantiate(callback_type)
        validate_type(callback, pl.Callback)
        instantiated_callbacks.append(callback)
    if 'data_augmentation_scheduler' in cfg:
        instantiated_callbacks.extend([instantiate(scheduler) for scheduler in cfg.data_augmentation_scheduler.values()])
    if cfg.lightning.trainer.params.gpus:
        instantiated_callbacks.append(pl.callbacks.GPUStatsMonitor(intra_step_time=True, inter_step_time=True))
    logger.info('Building callbacks...DONE!')
    return instantiated_callbacks

def build_observations(observation_cfg: DictConfig, scenario: AbstractScenario) -> AbstractObservation:
    """
    Instantiate observations
    :param observation_cfg: config of a planner
    :param scenario: scenario
    :return AbstractObservation
    """
    if is_TorchModuleWrapper_config(observation_cfg):
        torch_module_wrapper = build_torch_module_wrapper(observation_cfg.model_config)
        model = LightningModuleWrapper.load_from_checkpoint(observation_cfg.checkpoint_path, model=torch_module_wrapper).model
        config = observation_cfg.copy()
        OmegaConf.set_struct(config, False)
        config.pop('model_config')
        config.pop('checkpoint_path')
        OmegaConf.set_struct(config, True)
        observation: AbstractObservation = instantiate(config, model=model, scenario=scenario)
    else:
        observation = cast(AbstractObservation, instantiate(observation_cfg, scenario=scenario))
    return observation

def build_agent_augmentor(cfg: DictConfig) -> List[AbstractAugmentor]:
    """
    Build list of augmentors based on config.
    :param cfg: Dict config.
    :return List of augmentor objects.
    """
    logger.info('Building augmentors...')
    instantiated_augmentors = []
    for augmentor_type in cfg.values():
        augmentor: AbstractAugmentor = instantiate(augmentor_type)
        validate_type(augmentor, AbstractAugmentor)
        instantiated_augmentors.append(augmentor)
    logger.info('Building augmentors...DONE!')
    return instantiated_augmentors

def build_high_level_metric(cfg: DictConfig, base_metrics: Dict[str, AbstractMetricBuilder]) -> AbstractMetricBuilder:
    """
    Build a high level metric.
    :param cfg: High level metric config.
    :param base_metrics: A dict of base metrics.
    :return A high level metric.
    """
    OmegaConf.set_struct(cfg, False)
    required_metrics: Dict[str, str] = cfg.pop('required_metrics', {})
    OmegaConf.set_struct(cfg, True)
    metric_params = {}
    for metric_param, metric_name in required_metrics.items():
        metric_params[metric_param] = base_metrics[metric_name]
    return instantiate(cfg, **metric_params)

def extract_scenarios_from_dataset(cfg: DictConfig, worker: WorkerPool) -> List[AbstractScenario]:
    """
    Extract and filter scenarios by loading a dataset using the scenario builder.
    :param cfg: Omegaconf dictionary.
    :param worker: Worker to submit tasks which can be executed in parallel.
    :return: List of extracted scenarios.
    """
    scenario_builder = build_scenario_builder(cfg)
    scenario_filter = build_scenario_filter(cfg.scenario_filter)
    scenarios: List[AbstractScenario] = scenario_builder.get_scenarios(scenario_filter, worker)
    return scenarios

def build_scenarios(cfg: DictConfig, worker: WorkerPool, model: TorchModuleWrapper) -> List[AbstractScenario]:
    """
    Build the scenario objects that comprise the training dataset.
    :param cfg: Omegaconf dictionary.
    :param worker: Worker to submit tasks which can be executed in parallel.
    :param model: NN model used for training.
    :return: List of extracted scenarios.
    """
    scenarios = extract_scenarios_from_cache(cfg, worker, model) if cfg.cache.use_cache_without_dataset else extract_scenarios_from_dataset(cfg, worker)
    logger.info(f'Extracted {len(scenarios)} scenarios for training')
    assert len(scenarios) > 0, 'No scenarios were retrieved for training, check the scenario_filter parameters!'
    return scenarios

def validate_dict_type(instantiated_dict: Dict[str, Any], desired_type: Type[Any]) -> None:
    """
    Validate that all entries in dict is indeed the desired one
    :param instantiated_dict: dictionary that was created
    :param desired_type: type that the created class should have
    """
    for value in instantiated_dict.values():
        if isinstance(value, dict):
            validate_dict_type(value, desired_type)
        else:
            validate_type(value, desired_type)

def update_config_for_training(cfg: DictConfig) -> None:
    """
    Updates the config based on some conditions.
    :param cfg: omegaconf dictionary that is used to run the experiment.
    """
    OmegaConf.set_struct(cfg, False)
    if cfg.cache.cache_path is None:
        logger.warning('Parameter cache_path is not set, caching is disabled')
    elif not str(cfg.cache.cache_path).startswith('s3://'):
        if cfg.cache.cleanup_cache and Path(cfg.cache.cache_path).exists():
            rmtree(cfg.cache.cache_path)
        Path(cfg.cache.cache_path).mkdir(parents=True, exist_ok=True)
    if cfg.lightning.trainer.overfitting.enable:
        cfg.data_loader.params.num_workers = 0
    if cfg.gpu and torch.cuda.is_available():
        cfg.lightning.trainer.params.gpus = -1
    else:
        cfg.lightning.trainer.params.gpus = None
        cfg.lightning.trainer.params.accelerator = None
        cfg.lightning.trainer.params.precision = 32
    OmegaConf.resolve(cfg)
    OmegaConf.set_struct(cfg, True)
    if cfg.log_config:
        logger.info(f'Creating experiment name [{cfg.experiment}] in group [{cfg.group}] with config...')
        logger.info('\n' + OmegaConf.to_yaml(cfg))

def update_config_for_simulation(cfg: DictConfig) -> None:
    """
    Updates the config based on some conditions.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    """
    OmegaConf.set_struct(cfg, False)
    if cfg.max_number_of_workers:
        cfg.callbacks = [callback for callback in cfg.callback.values() if not is_target_type(callback, TimingCallback)]
    OmegaConf.resolve(cfg)
    OmegaConf.set_struct(cfg, True)
    if cfg.log_config:
        logger.info(f'Creating experiment: {cfg.experiment}')
        logger.info('\n' + OmegaConf.to_yaml(cfg))

def update_config_for_nuboard(cfg: DictConfig) -> None:
    """
    Updates the config based on some conditions.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    """
    OmegaConf.set_struct(cfg, False)
    if cfg.simulation_path is None:
        cfg.simulation_path = []
    elif not (isinstance(cfg.simulation_path, list) or isinstance(cfg.simulation_path, ListConfig)):
        cfg.simulation_path = [cfg.simulation_path]
    OmegaConf.resolve(cfg)
    OmegaConf.set_struct(cfg, True)
    if cfg.log_config:
        logger.info('\n' + OmegaConf.to_yaml(cfg))

def update_distributed_optimizer_config(cfg: DictConfig) -> DictConfig:
    """
    Scale the learning rate according to scaling method provided in distributed setting with ddp strategy.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return cfg: DictConfig. Updated configuration that is used to run the experiment.
    """
    lr_scale = get_num_gpus_used(cfg)
    logger.info(f'World size: {lr_scale}')
    logger.info(f'Learning rate before: {cfg.optimizer.lr}')
    scaling_method = 'Equal Variance' if cfg.lightning.distributed_training.equal_variance_scaling_strategy else 'Linearly'
    logger.info(f'Scaling method: {scaling_method}')
    cfg.optimizer.lr = scale_parameter(parameter=cfg.optimizer.lr, world_size=lr_scale, equal_variance_scaling_strategy=cfg.lightning.distributed_training.equal_variance_scaling_strategy)
    if is_target_type(cfg.optimizer, torch.optim.Adam) or is_target_type(cfg.optimizer, torch.optim.AdamW):
        cfg.optimizer.betas[0] = scale_parameter(parameter=cfg.optimizer.betas[0], world_size=lr_scale, equal_variance_scaling_strategy=cfg.lightning.distributed_training.equal_variance_scaling_strategy, raise_power=True)
        cfg.optimizer.betas[1] = scale_parameter(parameter=cfg.optimizer.betas[1], world_size=lr_scale, equal_variance_scaling_strategy=cfg.lightning.distributed_training.equal_variance_scaling_strategy, raise_power=True)
        logger.info(f'Betas after scaling: {cfg.optimizer.betas}')
    logger.info(f'Learning rate after scaling: {cfg.optimizer.lr}')
    return cfg

def update_distributed_lr_scheduler_config(cfg: DictConfig, num_train_batches: int) -> DictConfig:
    """
    Updates the learning rate scheduler config that modifies optimizer parameters over time.
    Optimizer and LR Scheduler is built in configure_optimizers() methods of the model.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :param num_train_batches: Number of batches in train dataloader.
    :return cfg: Configuration with the updated lr_scheduler key.
    """
    logger.info('Updating Learning Rate Scheduler Config...')
    number_gpus = get_num_gpus_used(cfg)
    if is_target_type(cfg.lr_scheduler, OneCycleLR):
        enable_overfitting = cfg.lightning.trainer.overfitting.enable
        overfit_batches = cfg.lightning.trainer.overfitting.params.overfit_batches
        if enable_overfitting and overfit_batches != 0:
            if overfit_batches >= 1.0:
                num_train_batches = overfit_batches
            else:
                num_train_batches = math.ceil(num_train_batches * overfit_batches)
        cfg.lr_scheduler.steps_per_epoch = scale_oclr_steps_per_epoch(num_train_batches=num_train_batches, world_size=number_gpus, epochs=cfg.lightning.trainer.params.max_epochs, warm_up_steps=cfg.warm_up_lr_scheduler.lr_lambda.warm_up_steps if 'warm_up_lr_scheduler' in cfg else 0)
        logger.info(f'Updating learning rate scheduler config Completed. Using {cfg.lr_scheduler._target_}.')
    else:
        logger.info(f'Updating {cfg.lr_scheduler._target_} in ddp setting is not yet supported. Learning rate scheduler config will not be updated.')
    return cfg

def scale_cfg_for_distributed_training(cfg: DictConfig, datamodule: pl.LightningDataModule, worker: WorkerPool) -> DictConfig:
    """
    Adjusts parameters in cfg for ddp.
    :param cfg: Config with parameters for instantiation.
    :param datamodule: Datamodule which will be used for updating the lr_scheduler parameters.
    :return cfg: Updated config.
    """
    OmegaConf.set_struct(cfg, False)
    cfg = update_distributed_optimizer_config(cfg)
    if 'lr_scheduler' in cfg:
        num_train_samples = int(len(datamodule._splitter.get_train_samples(datamodule._all_samples, worker)) * datamodule._train_fraction)
        cfg = update_distributed_lr_scheduler_config(cfg=cfg, num_train_batches=num_train_samples // cfg.data_loader.params.batch_size)
    OmegaConf.set_struct(cfg, True)
    logger.info('Optimizer and LR Scheduler configs updated according to ddp strategy.')
    return cfg

def get_num_gpus_used(cfg: DictConfig) -> int:
    """
    Gets the number of gpus used in ddp by searching through the environment variable WORLD_SIZE, PytorchLightning Trainer specified number of GPUs, and torch.cuda.device_count() in that order.
    :param cfg: Config with experiment parameters.
    :return num_gpus: Number of gpus used in ddp.
    """
    num_gpus = os.getenv('WORLD_SIZE', -1)
    if num_gpus == -1:
        logger.info('WORLD_SIZE was not set.')
        trainer_num_gpus = cfg.lightning.trainer.params.gpus
        if isinstance(trainer_num_gpus, str):
            raise RuntimeError('Error, please specify gpus as integer. Received string.')
        trainer_num_gpus = cast(int, trainer_num_gpus)
        if trainer_num_gpus == -1:
            logger.info('PytorchLightning Trainer gpus was set to -1, finding number of GPUs used from torch.cuda.device_count().')
            cuda_num_gpus = torch.cuda.device_count() * int(os.getenv('NUM_NODES', 1))
            num_gpus = cuda_num_gpus
        else:
            logger.info(f'Trainer gpus was set to {trainer_num_gpus}, using this as the number of gpus.')
            num_gpus = trainer_num_gpus
    num_gpus = int(num_gpus)
    logger.info(f'Number of gpus found to be in use: {num_gpus}')
    return num_gpus

class TestUtilsConfig(unittest.TestCase):
    """Tests for the non-distributed training functions in utils_config.py."""
    specific_world_size = 4

    @staticmethod
    def _generate_mock_training_config() -> DictConfig:
        """
        Returns a mock training configuration with sensible default values.
        :return: DictConfig representing the training configuration.
        """
        return DictConfig({'log_config': True, 'experiment': 'mock_experiment_name', 'group': 'mock_group_name', 'cache': {'cleanup_cache': False, 'cache_path': None}, 'data_loader': {'params': {'num_workers': None}}, 'lightning': {'trainer': {'params': {'gpus': None, 'accelerator': None, 'precision': None}, 'overfitting': {'enable': False}}}, 'gpu': False})

    @staticmethod
    def _generate_mock_simulation_config() -> DictConfig:
        """
        Returns a mock simulation configuration with sensible default values.
        :return: DictConfig representing the simulation configuration.
        """
        return DictConfig({'log_config': True, 'experiment': 'mock_experiment_name', 'group': 'mock_group_name', 'callback': {'timing_callback': {'_target_': 'nuplan.planning.simulation.callback.timing_callback.TimingCallback'}, 'simulation_log_callback': {'_target_': 'nuplan.planning.simulation.callback.simulation_log_callback.SimulationLogCallback'}, 'metric_callback': {'_target_': 'nuplan.planning.simulation.callback.metric_callback.MetricCallback'}}})

    @staticmethod
    def _patch_return_false() -> bool:
        """A patch function that will always return False."""
        return False

    @staticmethod
    def _patch_return_true() -> bool:
        """A patch function that will always return True."""
        return True

    @given(cache_path=st.one_of(st.none(), st.just('s3://bucket/key')))
    @settings(deadline=None)
    def test_update_config_for_training_cache_path_none_or_s3(self, cache_path: Optional[str]) -> None:
        """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path is either
        None or an S3 path.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.cache.cache_path = cache_path
        with TemporaryDirectory() as tmp_dir:
            with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
                update_config_for_training(mock_config)
            self.assertTrue(Path(tmp_dir).exists())

    def test_update_config_for_training_cache_path_local_non_existing(self) -> None:
        """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path doesn't exist yet.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        with TemporaryDirectory() as tmp_dir:
            mock_config.cache.cache_path = tmp_dir
            rmtree(tmp_dir)
            with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
                update_config_for_training(mock_config)
            self.assertTrue(Path(tmp_dir).exists())

    def test_update_config_for_training_cache_path_local_cleanup(self) -> None:
        """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path exists and
        cleanup_cache is requested.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        with TemporaryDirectory() as tmp_dir:
            _, tmp_file = mkstemp(dir=tmp_dir)
            mock_config.cache.cache_path = tmp_dir
            mock_config.cache.cleanup_cache = True
            self.assertTrue(Path(tmp_file).exists())
            with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
                update_config_for_training(mock_config)
            self.assertFalse(Path(tmp_file).exists())
            self.assertTrue(Path(tmp_dir).exists())
        self.assertFalse(Path(tmp_dir).exists())

    def test_update_config_for_training_overfitting(self) -> None:
        """
        Tests the behavior of update_config_for_training in regard to overfitting configurations.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        num_workers = 32
        mock_config.data_loader.params.num_workers = num_workers
        mock_config.lightning.trainer.overfitting.enable = False
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertEqual(num_workers, mock_config.data_loader.params.num_workers)
        mock_config.lightning.trainer.overfitting.enable = True
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertEqual(0, mock_config.data_loader.params.num_workers)

    @given(is_gpu_enabled=st.booleans(), is_cuda_available=st.booleans())
    @settings(deadline=None)
    def test_update_config_for_training_gpu(self, is_gpu_enabled: bool, is_cuda_available: bool) -> None:
        """
        Tests the behavior of update_config_for_training in regard to gpu configurations.
        """
        invalid_value = -99
        cuda_patch = TestUtilsConfig._patch_return_true if is_cuda_available else TestUtilsConfig._patch_return_false

        def get_expected_gpu_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
            return -1 if gpu_enabled and cuda_available else None

        def get_expected_accelerator_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
            return invalid_value if gpu_enabled and cuda_available else None

        def get_expected_precision_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
            return invalid_value if gpu_enabled and cuda_available else 32
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.gpu = is_gpu_enabled
        mock_config.lightning.trainer.params.gpus = invalid_value
        mock_config.lightning.trainer.params.accelerator = invalid_value
        mock_config.lightning.trainer.params.precision = invalid_value
        with patch_with_validation('torch.cuda.is_available', cuda_patch):
            update_config_for_training(mock_config)
        self.assertEqual(get_expected_gpu_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.gpus)
        self.assertEqual(get_expected_accelerator_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.accelerator)
        self.assertEqual(get_expected_precision_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.precision)

    @given(max_number_of_workers=st.one_of(st.none(), st.just(0)))
    @settings(deadline=None)
    def test_update_config_for_simulation_falsy_max_number_of_workers(self, max_number_of_workers: int) -> None:
        """
        Tests that update_config_for_simulation works as expected.
        When max number of workers is falsy, timing_callback won't be removed
        """
        mock_config = TestUtilsConfig._generate_mock_simulation_config()
        mock_config.max_number_of_workers = max_number_of_workers
        update_config_for_simulation(mock_config)
        self.assertEqual(3, len(mock_config.callback))

    @given(max_number_of_workers=st.integers(min_value=1))
    @settings(deadline=None)
    def test_update_config_for_simulation_truthy_max_number_of_workers(self, max_number_of_workers: int) -> None:
        """
        Tests that update_config_for_simulation works as expected. When max number of workers is truthy, a new
        `callbacks` entry will be added. The values are taken from `callback` with timing_callback target removed.
        """
        mock_config = TestUtilsConfig._generate_mock_simulation_config()
        mock_config.max_number_of_workers = max_number_of_workers
        update_config_for_simulation(mock_config)
        self.assertEqual(3, len(mock_config.callback))
        self.assertEqual(2, len(mock_config.callbacks))
        callbacks_targets = [callback['_target_'] for callback in mock_config.callbacks]
        self.assertNotIn('nuplan.planning.simulation.callback.timing_callback.TimingCallback', callbacks_targets)

    def test_update_config_for_nuboard(self) -> None:
        """Tests that update_config_for_nuboard works as expected."""
        mock_config = DictConfig({'log_config': True})
        mock_config.simulation_path = None
        update_config_for_nuboard(mock_config)
        self.assertIsNotNone(mock_config.simulation_path)
        self.assertEqual(0, len(mock_config.simulation_path))
        simulation_path_list = ['/mock/path', '/to/somewhere']
        mock_config.simulation_path = simulation_path_list
        update_config_for_nuboard(mock_config)
        self.assertEqual(simulation_path_list, mock_config.simulation_path)
        simulation_path_list_config = ListConfig(element_type=str, content=['/mock/path', '/to/somewhere'])
        mock_config.simulation_path = simulation_path_list_config
        update_config_for_nuboard(mock_config)
        self.assertEqual(simulation_path_list_config, mock_config.simulation_path)
        simulation_path = '/mock/path'
        mock_config.simulation_path = simulation_path
        update_config_for_nuboard(mock_config)
        expected_simulation_path_list = [simulation_path]
        self.assertEqual(expected_simulation_path_list, mock_config.simulation_path)

    @patch.dict(os.environ, {'WORLD_SIZE': str(specific_world_size)}, clear=True)
    def test_get_num_gpus_used_from_world_size(self) -> None:
        """
        Tests that that get_num_gpus_used works as expected. When WORLD_SIZE is set to a specific value, the function
        will simply return that value.
        """
        mock_config = DictConfig({})
        num_gpus = get_num_gpus_used(mock_config)
        self.assertEqual(self.specific_world_size, num_gpus)

    @given(num_gpus_config=st.integers(min_value=-1), cuda_device_count=st.integers(min_value=0), num_nodes=st.integers(min_value=1))
    @example(num_gpus_config=-1, cuda_device_count=2, num_nodes=2)
    @settings(deadline=None)
    def test_get_num_gpus_used_from_config(self, num_gpus_config: int, cuda_device_count: int, num_nodes: int) -> None:
        """
        Tests that that get_num_gpus_used works as expected when WORLD_SIZE environment variable is not set.
        """

        def patch_get_cuda_device_count() -> int:
            return cuda_device_count
        with patch.dict(os.environ, {'NUM_NODES': str(num_nodes)}, clear=True), patch_with_validation('torch.cuda.device_count', patch_get_cuda_device_count):
            mock_config = TestUtilsConfig._generate_mock_training_config()
            mock_config.lightning.trainer.params.gpus = num_gpus_config
            num_gpus = get_num_gpus_used(mock_config)
            expected_num_gpus = num_gpus_config if num_gpus_config != -1 else cuda_device_count * num_nodes
            self.assertEqual(expected_num_gpus, num_gpus)

    def test_get_num_gpus_used_invalid_config(self) -> None:
        """
        Tests that that get_num_gpus_used raises a RuntimeError when WORLD_SIZE environment variable is not set and
        a string is passed as the value of mock_config.lightning.trainer.params.gpus.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.lightning.trainer.params.gpus = '1'
        with self.assertRaises(RuntimeError):
            get_num_gpus_used(mock_config)

@given(cache_path=st.one_of(st.none(), st.just('s3://bucket/key')))
@settings(deadline=None)
def test_update_config_for_training_cache_path_none_or_s3(self, cache_path: Optional[str]) -> None:
    """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path is either
        None or an S3 path.
        """
    mock_config = TestUtilsConfig._generate_mock_training_config()
    mock_config.cache.cache_path = cache_path
    with TemporaryDirectory() as tmp_dir:
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertTrue(Path(tmp_dir).exists())

def test_update_config_for_training_cache_path_local_non_existing(self) -> None:
    """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path doesn't exist yet.
        """
    mock_config = TestUtilsConfig._generate_mock_training_config()
    with TemporaryDirectory() as tmp_dir:
        mock_config.cache.cache_path = tmp_dir
        rmtree(tmp_dir)
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertTrue(Path(tmp_dir).exists())

def test_update_config_for_training_overfitting(self) -> None:
    """
        Tests the behavior of update_config_for_training in regard to overfitting configurations.
        """
    mock_config = TestUtilsConfig._generate_mock_training_config()
    num_workers = 32
    mock_config.data_loader.params.num_workers = num_workers
    mock_config.lightning.trainer.overfitting.enable = False
    with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
        update_config_for_training(mock_config)
    self.assertEqual(num_workers, mock_config.data_loader.params.num_workers)
    mock_config.lightning.trainer.overfitting.enable = True
    with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
        update_config_for_training(mock_config)
    self.assertEqual(0, mock_config.data_loader.params.num_workers)

@given(is_gpu_enabled=st.booleans(), is_cuda_available=st.booleans())
@settings(deadline=None)
def test_update_config_for_training_gpu(self, is_gpu_enabled: bool, is_cuda_available: bool) -> None:
    """
        Tests the behavior of update_config_for_training in regard to gpu configurations.
        """
    invalid_value = -99
    cuda_patch = TestUtilsConfig._patch_return_true if is_cuda_available else TestUtilsConfig._patch_return_false

    def get_expected_gpu_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
        return -1 if gpu_enabled and cuda_available else None

    def get_expected_accelerator_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
        return invalid_value if gpu_enabled and cuda_available else None

    def get_expected_precision_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
        return invalid_value if gpu_enabled and cuda_available else 32
    mock_config = TestUtilsConfig._generate_mock_training_config()
    mock_config.gpu = is_gpu_enabled
    mock_config.lightning.trainer.params.gpus = invalid_value
    mock_config.lightning.trainer.params.accelerator = invalid_value
    mock_config.lightning.trainer.params.precision = invalid_value
    with patch_with_validation('torch.cuda.is_available', cuda_patch):
        update_config_for_training(mock_config)
    self.assertEqual(get_expected_gpu_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.gpus)
    self.assertEqual(get_expected_accelerator_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.accelerator)
    self.assertEqual(get_expected_precision_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.precision)

@given(max_number_of_workers=st.one_of(st.none(), st.just(0)))
@settings(deadline=None)
def test_update_config_for_simulation_falsy_max_number_of_workers(self, max_number_of_workers: int) -> None:
    """
        Tests that update_config_for_simulation works as expected.
        When max number of workers is falsy, timing_callback won't be removed
        """
    mock_config = TestUtilsConfig._generate_mock_simulation_config()
    mock_config.max_number_of_workers = max_number_of_workers
    update_config_for_simulation(mock_config)
    self.assertEqual(3, len(mock_config.callback))

@given(max_number_of_workers=st.integers(min_value=1))
@settings(deadline=None)
def test_update_config_for_simulation_truthy_max_number_of_workers(self, max_number_of_workers: int) -> None:
    """
        Tests that update_config_for_simulation works as expected. When max number of workers is truthy, a new
        `callbacks` entry will be added. The values are taken from `callback` with timing_callback target removed.
        """
    mock_config = TestUtilsConfig._generate_mock_simulation_config()
    mock_config.max_number_of_workers = max_number_of_workers
    update_config_for_simulation(mock_config)
    self.assertEqual(3, len(mock_config.callback))
    self.assertEqual(2, len(mock_config.callbacks))
    callbacks_targets = [callback['_target_'] for callback in mock_config.callbacks]
    self.assertNotIn('nuplan.planning.simulation.callback.timing_callback.TimingCallback', callbacks_targets)

@patch.dict(os.environ, {'WORLD_SIZE': str(specific_world_size)}, clear=True)
def test_get_num_gpus_used_from_world_size(self) -> None:
    """
        Tests that that get_num_gpus_used works as expected. When WORLD_SIZE is set to a specific value, the function
        will simply return that value.
        """
    mock_config = DictConfig({})
    num_gpus = get_num_gpus_used(mock_config)
    self.assertEqual(self.specific_world_size, num_gpus)

@given(num_gpus_config=st.integers(min_value=-1), cuda_device_count=st.integers(min_value=0), num_nodes=st.integers(min_value=1))
@example(num_gpus_config=-1, cuda_device_count=2, num_nodes=2)
@settings(deadline=None)
def test_get_num_gpus_used_from_config(self, num_gpus_config: int, cuda_device_count: int, num_nodes: int) -> None:
    """
        Tests that that get_num_gpus_used works as expected when WORLD_SIZE environment variable is not set.
        """

    def patch_get_cuda_device_count() -> int:
        return cuda_device_count
    with patch.dict(os.environ, {'NUM_NODES': str(num_nodes)}, clear=True), patch_with_validation('torch.cuda.device_count', patch_get_cuda_device_count):
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.lightning.trainer.params.gpus = num_gpus_config
        num_gpus = get_num_gpus_used(mock_config)
        expected_num_gpus = num_gpus_config if num_gpus_config != -1 else cuda_device_count * num_nodes
        self.assertEqual(expected_num_gpus, num_gpus)

def test_get_num_gpus_used_invalid_config(self) -> None:
    """
        Tests that that get_num_gpus_used raises a RuntimeError when WORLD_SIZE environment variable is not set and
        a string is passed as the value of mock_config.lightning.trainer.params.gpus.
        """
    mock_config = TestUtilsConfig._generate_mock_training_config()
    mock_config.lightning.trainer.params.gpus = '1'
    with self.assertRaises(RuntimeError):
        get_num_gpus_used(mock_config)

class TestUtilsType(unittest.TestCase):
    """Test utils_type functions."""

    def test_is_TorchModuleWrapper_config(self) -> None:
        """Tests that is_TorchModuleWrapper_config works as expected."""
        mock_config = DictConfig({'model_config': 'some_value', 'checkpoint_path': 'some_value', 'some_other_key': 'some_value'})
        expect_true = is_TorchModuleWrapper_config(mock_config)
        self.assertTrue(expect_true)
        mock_config.pop('some_other_key')
        expect_true = is_TorchModuleWrapper_config(mock_config)
        self.assertTrue(expect_true)
        mock_config.pop('model_config')
        expect_false = is_TorchModuleWrapper_config(mock_config)
        self.assertFalse(expect_false)
        mock_config.pop('checkpoint_path')
        expect_false = is_TorchModuleWrapper_config(mock_config)
        self.assertFalse(expect_false)

    def test_is_target_type(self) -> None:
        """Tests that is_target_type works as expected."""
        mock_config_test_utils_mock_type = DictConfig({'_target_': f'{__name__}.TestUtilsTypeMockType'})
        mock_config_test_utils_another_mock_type = DictConfig({'_target_': f'{__name__}.TestUtilsTypeAnotherMockType'})
        expect_true = is_target_type(mock_config_test_utils_mock_type, TestUtilsTypeMockType)
        self.assertTrue(expect_true)
        expect_true = is_target_type(mock_config_test_utils_another_mock_type, TestUtilsTypeAnotherMockType)
        self.assertTrue(expect_true)
        expect_false = is_target_type(mock_config_test_utils_mock_type, TestUtilsTypeAnotherMockType)
        self.assertFalse(expect_false)
        expect_false = is_target_type(mock_config_test_utils_another_mock_type, TestUtilsTypeMockType)
        self.assertFalse(expect_false)

    def test_validate_type(self) -> None:
        """Tests that validate_type works as expected."""
        test_utils_type_mock_type = TestUtilsTypeMockType()
        validate_type(test_utils_type_mock_type, TestUtilsTypeMockType)
        with self.assertRaises(AssertionError):
            validate_type(test_utils_type_mock_type, TestUtilsTypeAnotherMockType)

    def test_are_the_same_type(self) -> None:
        """Tests that are_the_same_type works as expected."""
        test_utils_type_mock_type = TestUtilsTypeMockType()
        another_test_utils_type_mock_type = TestUtilsTypeMockType()
        test_utils_type_another_mock_type = TestUtilsTypeAnotherMockType()
        are_the_same_type(test_utils_type_mock_type, another_test_utils_type_mock_type)
        with self.assertRaises(AssertionError):
            are_the_same_type(test_utils_type_mock_type, test_utils_type_another_mock_type)

    def test_validate_dict_type(self) -> None:
        """Tests that validate_dict_type works as expected."""
        mock_config = DictConfig({'_convert_': 'all', 'correct_object': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}, 'correct_object_2': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}})
        instantiated_config = hydra.utils.instantiate(mock_config)
        validate_dict_type(instantiated_config, TestUtilsTypeMockType)
        mock_config.other_object = {'_target_': f'{__name__}.TestUtilsTypeAnotherMockType', 'c': 1}
        instantiated_config = hydra.utils.instantiate(mock_config)
        with self.assertRaises(AssertionError):
            validate_dict_type(instantiated_config, TestUtilsTypeMockType)

    def test_find_builder_in_config(self) -> None:
        """Tests that find_builder_in_config works as expected."""
        mock_config = DictConfig({'correct_object': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}, 'other_object': {'_target_': f'{__name__}.TestUtilsTypeAnotherMockType', 'c': 1}})
        test_utils_mock_type = find_builder_in_config(mock_config, TestUtilsTypeMockType)
        self.assertTrue(is_target_type(test_utils_mock_type, TestUtilsTypeMockType))
        test_utils_another_mock_type = find_builder_in_config(mock_config, TestUtilsTypeAnotherMockType)
        self.assertTrue(is_target_type(test_utils_another_mock_type, TestUtilsTypeAnotherMockType))
        del mock_config.other_object
        with self.assertRaises(ValueError):
            find_builder_in_config(mock_config, TestUtilsTypeAnotherMockType)

def test_validate_dict_type(self) -> None:
    """Tests that validate_dict_type works as expected."""
    mock_config = DictConfig({'_convert_': 'all', 'correct_object': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}, 'correct_object_2': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}})
    instantiated_config = hydra.utils.instantiate(mock_config)
    validate_dict_type(instantiated_config, TestUtilsTypeMockType)
    mock_config.other_object = {'_target_': f'{__name__}.TestUtilsTypeAnotherMockType', 'c': 1}
    instantiated_config = hydra.utils.instantiate(mock_config)
    with self.assertRaises(AssertionError):
        validate_dict_type(instantiated_config, TestUtilsTypeMockType)

class TestSimulationCallbackBuilder(unittest.TestCase):
    """Unit tests for functions in simulation_callback_builder.py."""
    mock_cpu_node_count = 4

    @staticmethod
    def _generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation: int=1, max_callback_workers: int=1, disable_callback_parallelization: bool=False) -> DictConfig:
        """
        Utility function to generate a mocked callback worker configuration with Sequential worker type. Parameters are
        used directly as the config values.
        """
        return DictConfig({'worker': {'_target_': 'nuplan.planning.utils.multithreading.worker_sequential.Sequential'}, 'number_of_cpus_allocated_per_simulation': number_of_cpus_allocated_per_simulation, 'max_callback_workers': max_callback_workers, 'disable_callback_parallelization': disable_callback_parallelization})

    @staticmethod
    def _calculate_expected_number_of_threads(max_callback_workers: int) -> int:
        """
        Utility function to calculate the expected number of threads available to the workers. The calculation is based on
        the current build_callbacks_worker implementation.
        :param max_callback_workers: Config value passed from Sequential worker config.
        """
        return min(TestSimulationCallbackBuilder.mock_cpu_node_count - 1, max_callback_workers)

    @given(number_of_cpus_allocated_per_simulation=st.one_of(st.none(), st.just(1)), max_callback_workers=st.integers(min_value=1))
    def test_build_callbacks_worker_nominal(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
        """Tests the nominal case of build_callbacks_worker."""
        with mock.patch('nuplan.planning.utils.multithreading.worker_pool.WorkerResources.current_node_cpu_count', return_value=self.mock_cpu_node_count):
            mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers)
            worker_pool = build_callbacks_worker(mock_config)
            expected_number_of_threads = TestSimulationCallbackBuilder._calculate_expected_number_of_threads(max_callback_workers)
            self.assertEqual(worker_pool.number_of_threads, expected_number_of_threads)
            self.assertTrue(isinstance(worker_pool, SingleMachineParallelExecutor))

    @given(number_of_cpus_allocated_per_simulation=st.one_of(st.integers(max_value=0), st.integers(min_value=2)), max_callback_workers=st.integers(min_value=1))
    def test_build_callbacks_worker_edge_case_invalid_cpus_allocated(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
        """Tests an edge case of build_callbacks_worker, where an invalid cpu allocation setting is passed."""
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=False)
        with self.assertRaises(ValueError):
            build_callbacks_worker(mock_config)

    @given(number_of_cpus_allocated_per_simulation=st.one_of(st.none(), st.just(1)), max_callback_workers=st.integers(min_value=1))
    def test_build_callbacks_worker_edge_cases(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
        """Tests other edge cases of build_callbacks_worker."""
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=False)
        mock_config.worker._target_ = 'nuplan.planning.utils.multithreading.worker_parallel.SingleMachineParallelExecutor'
        worker_pool = build_callbacks_worker(mock_config)
        self.assertIsNone(worker_pool)
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=True)
        worker_pool = build_callbacks_worker(mock_config)
        self.assertIsNone(worker_pool)

    def test_build_simulation_callbacks_serialization_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed SerializationCallback config.
        """
        mock_config = DictConfig({'callback': {'serialization_callback': {'_target_': 'nuplan.planning.simulation.callback.serialization_callback.SerializationCallback', 'folder_name': 'mock_folder', 'serialization_type': 'pickle', 'serialize_into_single_file': False}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_serialization_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_serialization_callback, SerializationCallback))

    def test_build_simulation_callbacks_timing_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed TimingCallback config.
        """
        mock_config = DictConfig({'callback': {'timing_callback': {'_target_': 'nuplan.planning.simulation.callback.timing_callback.TimingCallback'}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_timing_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_timing_callback, TimingCallback))

    def test_build_simulation_callbacks_simulation_log_metric_callbacks(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed SimulationLogCallback
        & MetricCallback configurations.
        """
        mock_config = DictConfig({'callback': {'simulation_log_callback': {'_target_': 'nuplan.planning.simulation.callback.simulation_log_callback.SimulationLogCallback'}, 'metric_callback': {'_target_': 'nuplan.planning.simulation.callback.metric_callback.MetricCallback'}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        self.assertEqual(0, len(callbacks))

    def test_build_simulation_callbacks_multi_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed MultiCallback config.
        """
        mock_config = DictConfig({'callback': {'multi_callback': {'_target_': 'nuplan.planning.simulation.callback.multi_callback.MultiCallback', 'callbacks': []}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_multi_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_multi_callback, MultiCallback))

    def test_build_simulation_callbacks_visualization_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed MultiCallback config.
        """
        mock_config = DictConfig({'callback': {'visualization_callback': {'_target_': 'nuplan.planning.simulation.callback.visualization_callback.VisualizationCallback', 'renderer': {}}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_visualization_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_visualization_callback, VisualizationCallback))

@given(number_of_cpus_allocated_per_simulation=st.one_of(st.none(), st.just(1)), max_callback_workers=st.integers(min_value=1))
def test_build_callbacks_worker_nominal(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
    """Tests the nominal case of build_callbacks_worker."""
    with mock.patch('nuplan.planning.utils.multithreading.worker_pool.WorkerResources.current_node_cpu_count', return_value=self.mock_cpu_node_count):
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers)
        worker_pool = build_callbacks_worker(mock_config)
        expected_number_of_threads = TestSimulationCallbackBuilder._calculate_expected_number_of_threads(max_callback_workers)
        self.assertEqual(worker_pool.number_of_threads, expected_number_of_threads)
        self.assertTrue(isinstance(worker_pool, SingleMachineParallelExecutor))

@given(number_of_cpus_allocated_per_simulation=st.one_of(st.integers(max_value=0), st.integers(min_value=2)), max_callback_workers=st.integers(min_value=1))
def test_build_callbacks_worker_edge_case_invalid_cpus_allocated(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
    """Tests an edge case of build_callbacks_worker, where an invalid cpu allocation setting is passed."""
    mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=False)
    with self.assertRaises(ValueError):
        build_callbacks_worker(mock_config)

@given(number_of_cpus_allocated_per_simulation=st.one_of(st.none(), st.just(1)), max_callback_workers=st.integers(min_value=1))
def test_build_callbacks_worker_edge_cases(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
    """Tests other edge cases of build_callbacks_worker."""
    mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=False)
    mock_config.worker._target_ = 'nuplan.planning.utils.multithreading.worker_parallel.SingleMachineParallelExecutor'
    worker_pool = build_callbacks_worker(mock_config)
    self.assertIsNone(worker_pool)
    mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=True)
    worker_pool = build_callbacks_worker(mock_config)
    self.assertIsNone(worker_pool)

class TestDataLoader(unittest.TestCase):
    """
    Tests data loading functionality
    """

    def setUp(self) -> None:
        """Setup hydra config."""
        seed = 10
        pl.seed_everything(seed, workers=True)
        main_path = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(main_path, '../config/training/')
        self.group = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.group.name, 'cache_path')

    def tearDown(self) -> None:
        """Remove temporary folder."""
        self.group.cleanup()

    @staticmethod
    def validate_cfg(cfg: DictConfig) -> None:
        """Validate hydra config."""
        update_config_for_training(cfg)
        OmegaConf.set_struct(cfg, False)
        cfg.scenario_filter.limit_total_scenarios = 0.001
        cfg.data_loader.datamodule.train_fraction = 1.0
        cfg.data_loader.datamodule.val_fraction = 1.0
        cfg.data_loader.datamodule.test_fraction = 1.0
        cfg.data_loader.params.batch_size = 2
        cfg.data_loader.params.num_workers = 2
        cfg.data_loader.params.pin_memory = False
        OmegaConf.set_struct(cfg, True)

    @staticmethod
    def _iterate_dataloader(dataloader: torch.utils.data.DataLoader) -> None:
        """
        Iterate a fixed number of batches of the dataloader.
        :param dataloader: Data loader to iterate.
        """
        num_batches = 5
        dataloader_iter = iter(dataloader)
        iterations = min(len(dataloader), num_batches)
        for _ in range(iterations):
            next(dataloader_iter)

    def _run_dataloader(self, cfg: DictConfig) -> None:
        """
        Test that the training dataloader can be iterated without errors.
        :param cfg: Hydra config.
        """
        worker = build_worker(cfg)
        lightning_module_wrapper = build_torch_module_wrapper(cfg.model)
        datamodule = build_lightning_datamodule(cfg, worker, lightning_module_wrapper)
        datamodule.setup('fit')
        datamodule.setup('test')
        train_dataloader = datamodule.train_dataloader()
        val_dataloader = datamodule.val_dataloader()
        test_dataloader = datamodule.test_dataloader()
        for dataloader in [train_dataloader, val_dataloader]:
            assert len(dataloader) > 0
            self._iterate_dataloader(dataloader)
        self._iterate_dataloader(test_dataloader)

    def test_dataloader(self) -> None:
        """Test dataloader on nuPlan DB."""
        log_names = ['2021.07.16.20.45.29_veh-35_01095_01486', '2021.08.17.18.54.02_veh-45_00665_01065', '2021.06.08.12.54.54_veh-26_04262_04732', '2021.10.06.07.26.10_veh-52_00006_00398']
        overrides = ['scenario_builder=nuplan_mini', 'worker=sequential', 'splitter=nuplan', f'scenario_filter.log_names={log_names}', f'group={self.group.name}', f'cache.cache_path={self.cache_path}', 'output_dir=${group}/${experiment}', 'scenario_type_weights=default_scenario_type_weights']
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*overrides, '+training=training_raster_model'])
            self.validate_cfg(cfg)
            self._run_dataloader(cfg)

@staticmethod
def validate_cfg(cfg: DictConfig) -> None:
    """Validate hydra config."""
    update_config_for_training(cfg)
    OmegaConf.set_struct(cfg, False)
    cfg.scenario_filter.limit_total_scenarios = 0.001
    cfg.data_loader.datamodule.train_fraction = 1.0
    cfg.data_loader.datamodule.val_fraction = 1.0
    cfg.data_loader.datamodule.test_fraction = 1.0
    cfg.data_loader.params.batch_size = 2
    cfg.data_loader.params.num_workers = 2
    cfg.data_loader.params.pin_memory = False
    OmegaConf.set_struct(cfg, True)

class SubmissionContainer:
    """Class handling a submission Docker container"""

    def __init__(self, submission_image: str, container_name: str, port: int):
        """
        :param submission_image: Name of the docker image of the submission
        :param container_name: Name for the container to be run
        :param port: Port number to be used for communication
        """
        self.submission_image = submission_image
        self.container_name = container_name
        self.port = port
        self.client: docker.client.DockerClient | None = None

    def __del__(self) -> None:
        """Stop the running container when the destructor is called."""
        self.stop()

    def start(self, cpus: str='0,1', gpus: list[str] | None=None) -> Any:
        """
        Starts the submission container given a docker client, and the submission details. It exposes the specified
        port, and volume mounts (read only) the data directory to make it available to the container.
        :param cpus: CPUs to be used by the submission container
        :param gpus: GPUs to be used by the submission container
        """
        if gpus is None:
            gpus = ['0']
        self.client = docker.from_env()
        self.stop()
        ports = {f'{str(self.port)}': self.port}
        self.client.containers.run(self.submission_image, name=self.container_name, detach=True, ports=ports, tty=True, environment={'SUBMISSION_CONTAINER_PORT': str(self.port)}, device_requests=[docker.types.DeviceRequest(device_ids=gpus, capabilities=[['gpu']])], cpuset_cpus=cpus, volumes={os.getenv('NUPLAN_DATA_ROOT', '~/nuplan/dataset'): {'bind': '/data/sets/nuplan', 'mode': 'ro'}})
        logging.debug(f'Started submission container with image: {self.submission_image} with port: {self.port}')
        return self.client.containers.get(self.container_name)

    def stop(self) -> None:
        """Checks if the submission container is running, if it is it stops and removes it."""
        try:
            container = self.client.containers.get(self.container_name)
        except NotFound:
            pass
        else:
            logging.debug('Stopping and removing pre-existing container')
            try:
                container.kill()
            except docker.errors.APIError:
                pass
            container.remove()

    def wait_until_running(self, timeout: float=3) -> None:
        """
        Waits until a container is running until timeout.
        :param timeout: timeout in seconds
        """

        def is_running(manager: SubmissionContainer) -> bool:
            """
            Checks if the container is running
            :param manager: The container manager
            :returns: True if the container is in running state
            """
            return bool(manager.client.api.inspect_container(manager.container_name)['State']['Status'] == 'running')
        keep_trying(is_running, [self], {}, (docker.errors.NotFound,), timeout)

def __del__(self) -> None:
    """Stop the running container when the destructor is called."""
    self.stop()

def start(self, cpus: str='0,1', gpus: list[str] | None=None) -> Any:
    """
        Starts the submission container given a docker client, and the submission details. It exposes the specified
        port, and volume mounts (read only) the data directory to make it available to the container.
        :param cpus: CPUs to be used by the submission container
        :param gpus: GPUs to be used by the submission container
        """
    if gpus is None:
        gpus = ['0']
    self.client = docker.from_env()
    self.stop()
    ports = {f'{str(self.port)}': self.port}
    self.client.containers.run(self.submission_image, name=self.container_name, detach=True, ports=ports, tty=True, environment={'SUBMISSION_CONTAINER_PORT': str(self.port)}, device_requests=[docker.types.DeviceRequest(device_ids=gpus, capabilities=[['gpu']])], cpuset_cpus=cpus, volumes={os.getenv('NUPLAN_DATA_ROOT', '~/nuplan/dataset'): {'bind': '/data/sets/nuplan', 'mode': 'ro'}})
    logging.debug(f'Started submission container with image: {self.submission_image} with port: {self.port}')
    return self.client.containers.get(self.container_name)

class SubmissionPlanner:
    """
    Class holding a planner and exposing functionalities as a server. The services are planner initialization and
    trajectory computation.
    """

    def __init__(self, planner_config: DictConfig):
        """
        Prepares the planner and the server. The communication port is read from an environmental variable.
        :param planner_config: The planner configuration to instantiate the planner
        """
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        map_version = os.getenv('NUPLAN_MAP_VERSION', 'nuplan-maps-v1.0')
        map_factory = NuPlanMapFactory(GPKGMapsDB(map_version=map_version, map_root=os.path.join(os.getenv('NUPLAN_DATA_ROOT', '~/nuplan/dataset'), 'maps')))
        map_manager = MapManager(map_factory)
        chpb_grpc.add_DetectionTracksChallengeServicer_to_server(DetectionTracksChallengeServicer(planner_config, map_manager), self.server)
        port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
        logger.info(f'Submission container starting with port {port}')
        if not port:
            raise RuntimeError("Environment variable not specified: 'SUBMISSION_CONTAINER_PORT'")
        self.server.add_insecure_port(f'[::]:{port}')

    def serve(self) -> None:
        """Starts the server."""
        logger.info('Server starting...')
        self.server.start()
        logger.info('Server started!')
        self.server.wait_for_termination()
        logger.info('Server terminated!')

def serve(self) -> None:
    """Starts the server."""
    logger.info('Server starting...')
    self.server.start()
    logger.info('Server started!')
    self.server.wait_for_termination()
    logger.info('Server terminated!')

class ImageIsRunnableValidator(BaseSubmissionValidator):
    """Checks if an image is runnable without errors"""

    def validate(self, submission: str) -> bool:
        """
        Checks that the queried image is runnable.
        :param submission: Queried image name
        :return: False if the image is not runnable, or the next validator on the chain if the validation passes
        """
        container_name = container_name_from_image_name(submission)
        submission_container = SubmissionContainer(submission_image=submission, container_name=container_name, port=find_free_port_number())
        _ = submission_container.start()
        try:
            submission_container.wait_until_running(timeout=1)
            logger.debug('Image is runnable')
        except TimeoutError:
            logger.error('Image is not runnable')
            self._failing_validator = ImageIsRunnableValidator
            return False
        try:
            submission_container.stop()
        except docker.errors.APIError:
            pass
        return bool(super().validate(submission))

def validate(self, submission: str) -> bool:
    """
        Checks that the queried image is runnable.
        :param submission: Queried image name
        :return: False if the image is not runnable, or the next validator on the chain if the validation passes
        """
    container_name = container_name_from_image_name(submission)
    submission_container = SubmissionContainer(submission_image=submission, container_name=container_name, port=find_free_port_number())
    _ = submission_container.start()
    try:
        submission_container.wait_until_running(timeout=1)
        logger.debug('Image is runnable')
    except TimeoutError:
        logger.error('Image is not runnable')
        self._failing_validator = ImageIsRunnableValidator
        return False
    try:
        submission_container.stop()
    except docker.errors.APIError:
        pass
    return bool(super().validate(submission))

class ImageExistsValidator(BaseSubmissionValidator):
    """SubmissionValidator that checks if an image is present"""

    def validate(self, submission: str) -> bool:
        """
        Checks that the queried image exists locally.
        :param submission: Queried image name
        :return: False if the image is not available, or the next validator on the chain if the validation passes
        """
        client = docker.from_env()
        tags = []
        for image in client.images.list(name=submission):
            tags.extend(image.tags)
        if submission not in tags:
            self._failing_validator = ImageExistsValidator
            logger.error("Image doesn't exist")
            return False
        logger.debug('Image exists')
        return bool(super().validate(submission))

def validate(self, submission: str) -> bool:
    """
        Checks that the queried image exists locally.
        :param submission: Queried image name
        :return: False if the image is not available, or the next validator on the chain if the validation passes
        """
    client = docker.from_env()
    tags = []
    for image in client.images.list(name=submission):
        tags.extend(image.tags)
    if submission not in tags:
        self._failing_validator = ImageExistsValidator
        logger.error("Image doesn't exist")
        return False
    logger.debug('Image exists')
    return bool(super().validate(submission))

