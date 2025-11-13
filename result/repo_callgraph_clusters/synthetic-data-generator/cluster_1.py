# Cluster 1

@pytest.fixture
def manager():
    yield DataExporterManager()

@pytest.fixture
def manager():
    yield ModelManager()

@pytest.fixture
def manager():
    yield DataConnectorManager()

@pytest.fixture
def manager():
    yield DataProcessorManager()

class Synthesizer:
    """
    Synthesizer is the high level interface for synthesizing data.

    We provided several example usage in our `Github repository <https://github.com/hitsz-ids/synthetic-data-generator/tree/main/example>`_.

    Args:

        model (str | SynthesizerModel | type[SynthesizerModel]): The name of the model or the model itself. Type of model must be :class:`~sdgx.models.base.SynthesizerModel`.
            When model is a string, it must be registered in :class:`~sdgx.models.manager.ModelManager`.
        model_path (str | Path, optional): The path to the model file. Defaults to None. Used to load the model if ``model`` is a string or type of :class:`~sdgx.models.base.SynthesizerModel`.
        model_kwargs (dict[str, Any], optional): The keyword arguments for model. Defaults to None.
        metadata (Metadata, optional): The metadata to use. Defaults to None.
        metadata_path (str | Path, optional): The path to the metadata file. Defaults to None. Used to load the metadata if ``metadata`` is None.
        data_connector (DataConnector | type[DataConnector] | str, optional): The data connector to use. Defaults to None.
            When data_connector is a string, it must be registered in :class:`~sdgx.data_connectors.manager.DataConnectorManager`.
        data_connector_kwargs (dict[str, Any], optional): The keyword arguments for data connectors. Defaults to None.
        raw_data_loaders_kwargs (dict[str, Any], optional): The keyword arguments for raw data loaders. Defaults to None.
        processed_data_loaders_kwargs (dict[str, Any], optional): The keyword arguments for processed data loaders. Defaults to None.
        data_processors (list[str | DataProcessor | type[DataProcessor]], optional): The data processors to use. Defaults to None.
            When data_processor is a string, it must be registered in :class:`~sdgx.data_processors.manager.DataProcessorManager`.
        data_processors_kwargs (dict[str, dict[str, Any]], optional): The keyword arguments for data processors. Defaults to None.

    Example:

        .. code-block:: python

            from sdgx.data_connectors.csv_connector import CsvConnector
            from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
            from sdgx.synthesizer import Synthesizer
            from sdgx.utils import download_demo_data

            dataset_csv = download_demo_data()
            data_connector = CsvConnector(path=dataset_csv)
            synthesizer = Synthesizer(
                model=CTGANSynthesizerModel(epochs=1),  # For quick demo
                data_connector=data_connector,
            )
            synthesizer.fit()
            sampled_data = synthesizer.sample(1000)
    """
    METADATA_SAVE_NAME = 'metadata.json'
    '\n    Default name for metadata file\n    '
    MODEL_SAVE_DIR = 'model'
    '\n    Default name for model directory\n    '

    def __init__(self, model: str | SynthesizerModel | type[SynthesizerModel], model_path: None | str | Path=None, model_kwargs: None | dict[str, Any]=None, metadata: None | Metadata=None, metadata_path: None | str | Path=None, data_connector: None | str | DataConnector | type[DataConnector]=None, data_connector_kwargs: None | dict[str, Any]=None, raw_data_loaders_kwargs: None | dict[str, Any]=None, processed_data_loaders_kwargs: None | dict[str, Any]=None, data_processors: None | list[str | DataProcessor | type[DataProcessor]]=None, data_processors_kwargs: None | dict[str, Any]=None):
        if isinstance(data_connector, str) or isinstance(data_connector, type):
            data_connector = DataConnectorManager().init_data_connector(data_connector, **data_connector_kwargs or {})
        if data_connector:
            self.dataloader = DataLoader(data_connector, **raw_data_loaders_kwargs or {})
        else:
            logger.warning('No data_connector provided, will not support `fit`')
            self.dataloader = None
        self.data_processors_manager = DataProcessorManager()
        if not data_processors:
            data_processors = self.data_processors_manager.registed_default_processor_list
        logger.info(f'Using data processors: {data_processors}')
        self.data_processors = [d if isinstance(d, DataProcessor) else self.data_processors_manager.init_data_processor(d, **data_processors_kwargs or {}) for d in data_processors]
        if metadata and metadata_path:
            raise SynthesizerInitError('metadata and metadata_path cannot be specified at the same time')
        if metadata:
            self.metadata = metadata
        elif metadata_path:
            self.metadata = Metadata.load(metadata_path)
        else:
            self.metadata = None
        self.model_manager = ModelManager()
        if isinstance(model, SynthesizerModel) and model_path:
            raise SynthesizerInitError('model as instance and model_path cannot be specified at the same time')
        if (isinstance(model, str) or isinstance(model, type)) and model_path:
            self.model = self.model_manager.load(model, model_path, **model_kwargs or {})
            if model_kwargs:
                logger.warning('model_kwargs will be ignored when loading model from model_path')
        elif isinstance(model, str) or isinstance(model, type):
            self.model = self.model_manager.init_model(model, **model_kwargs or {})
        elif isinstance(model, SynthesizerModel) or isinstance(model, StatisticSynthesizerModel):
            self.model = model
            if model_kwargs:
                logger.warning('model_kwargs will be ignored when using already initialized model')
        else:
            raise SynthesizerInitError('model or model_path must be specified')
        self.processed_data_loaders_kwargs = processed_data_loaders_kwargs or {}

    def save(self, save_dir: str | Path) -> Path:
        """
        Dump metadata and model to file

        Args:
            save_dir (str | Path): The directory to save the model.

        Returns:
            Path: The directory to save the synthesizer.
        """
        save_dir = Path(save_dir).expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'Saving synthesizer to {save_dir}')
        if self.metadata:
            self.metadata.save(save_dir / self.METADATA_SAVE_NAME)
        model_save_dir = save_dir / self.MODEL_SAVE_DIR
        model_save_dir.mkdir(parents=True, exist_ok=True)
        self.model.save(model_save_dir)
        return save_dir

    @classmethod
    def load(cls, load_dir: str | Path, model: str | type[SynthesizerModel], metadata: None | Metadata=None, data_connector: None | str | DataConnector | type[DataConnector]=None, data_connector_kwargs: None | dict[str, Any]=None, raw_data_loaders_kwargs: None | dict[str, Any]=None, processed_data_loaders_kwargs: None | dict[str, Any]=None, data_processors: None | list[str | DataProcessor | type[DataProcessor]]=None, data_processors_kwargs: None | dict[str, dict[str, Any]]=None, model_kwargs=None) -> 'Synthesizer':
        """
        Load metadata and model, allow rebuilding Synthesizer for finetuning or other use cases.

        We need ``model`` as not every model support *pickle* way to save and load.

        Args:
            load_dir (str | Path): The directory to load the model.
            model (str | type[SynthesizerModel]): The name of the model or the model itself. Type of model must be :class:`~sdgx.models.base.SynthesizerModel`.
                When model is a string, it must be registered in :class:`~sdgx.models.manager.ModelManager`.
            metadata (Metadata, optional): The metadata to use. Defaults to None.
            data_connector (DataConnector | type[DataConnector] | str, optional): The data connector to use. Defaults to None.
                When data_connector is a string, it must be registered in :class:`~sdgx.data_connectors.manager.DataConnectorManager`.
            data_connector_kwargs (dict[str, Any], optional): The keyword arguments for data connectors. Defaults to None.
            raw_data_loaders_kwargs (dict[str, Any], optional): The keyword arguments for raw data loaders. Defaults to None.
            processed_data_loaders_kwargs (dict[str, Any], optional): The keyword arguments for processed data loaders. Defaults to None.
            data_processors (list[str | DataProcessor | type[DataProcessor]], optional): The data processors to use. Defaults to None.
                When data_processor is a string, it must be registered in :class:`~sdgx.data_processors.manager.DataProcessorManager`.
            data_processors_kwargs (dict[str, dict[str, Any]], optional): The keyword arguments for data processors. Defaults to None.

        Returns:
            Synthesizer: The synthesizer instance.
        """
        load_dir = Path(load_dir).expanduser().resolve()
        logger.info(f'Loading synthesizer from {load_dir}')
        if not load_dir.exists():
            raise SynthesizerInitError(f'{load_dir.as_posix()} does not exist')
        model_path = load_dir / cls.MODEL_SAVE_DIR
        if not model_path.exists():
            raise SynthesizerInitError(f'{model_path.as_posix()} does not exist, cannot load model.')
        metadata_path = load_dir / cls.METADATA_SAVE_NAME
        if not metadata_path.exists():
            metadata_path = None
        return Synthesizer(model=model, model_path=model_path, metadata=metadata, metadata_path=metadata_path, model_kwargs=model_kwargs, data_connector=data_connector, data_connector_kwargs=data_connector_kwargs, raw_data_loaders_kwargs=raw_data_loaders_kwargs, processed_data_loaders_kwargs=processed_data_loaders_kwargs, data_processors=data_processors, data_processors_kwargs=data_processors_kwargs)

    def fit(self, metadata: None | Metadata=None, inspector_max_chunk: int=10, metadata_include_inspectors: None | list[str]=None, metadata_exclude_inspectors: None | list[str]=None, inspector_init_kwargs: None | dict[str, Any]=None, model_fit_kwargs: None | dict[str, Any]=None):
        """
        Fit the synthesizer with metadata and data processors.

        Raw data will be loaded from the dataloader and processed by the data processors in a Generator.
        The Generator, which prevents the processed data, will be wrapped into a DataLoader, aka ProcessedDataLoader.
        The ProcessedDataLoader will be used to fit the model.

        For more information about DataLoaders, please refer to the :class:`~sdgx.data_loaders.base.DataLoader`.

        For more information about DataProcessors, please refer to the :class:`~sdgx.data_processors.base.DataProcessor`.

        For more information about DataConnectors, please refer to the :class:`~sdgx.data_connectors.base.DataConnector`. Especially, the :class:`~sdgx.data_connectors.generator_connector.GeneratorConnector`.

        Args:
            metadata (Metadata, optional): The metadata to use. Defaults to None. If None, it will be inferred from the dataloader with the :func:`~sdgx.data_models.metadata.Metadata.from_dataloader` method.
            inspector_max_chunk (int, optional): The maximum number of chunks to inspect. Defaults to 10.
            metadata_include_inspectors (list[str], optional): The list of metadata inspectors to include. Defaults to None.
            metadata_exclude_inspectors (list[str], optional): The list of metadata inspectors to exclude. Defaults to None.
            inspector_init_kwargs (dict[str, Any], optional): The keyword arguments for metadata inspectors. Defaults to None.
            model_fit_kwargs (dict[str, Any], optional): The keyword arguments for model.fit. Defaults to None.
        """
        if self.dataloader is None:
            raise SynthesizerInitError('Cannot fit without dataloader, check `data_connector` parameter when initializing Synthesizer')
        metadata = metadata or self.metadata or Metadata.from_dataloader(self.dataloader, max_chunk=inspector_max_chunk, include_inspectors=metadata_include_inspectors, exclude_inspectors=metadata_exclude_inspectors, inspector_init_kwargs=inspector_init_kwargs)
        self.metadata = metadata.model_copy()
        logger.info('Fitting data processors...')
        if not self.dataloader:
            logger.info('Fitting without dataloader.')
        start_time = time.time()
        for d in self.data_processors:
            if self.dataloader:
                d.fit(metadata=metadata, tabular_data=self.dataloader)
            else:
                d.fit(metadata=metadata)
        logger.info(f'Fitted {len(self.data_processors)} data processors in  {time.time() - start_time}s.')

        def chunk_generator() -> Generator[pd.DataFrame, None, None]:
            for chunk in self.dataloader.iter():
                for d in self.data_processors:
                    chunk = d.convert(chunk)
                yield chunk
        logger.info('Initializing processed data loader...')
        start_time = time.time()
        processed_dataloader = DataLoader(GeneratorConnector(chunk_generator), identity=self.dataloader.identity, **self.processed_data_loaders_kwargs)
        logger.info(f'Initialized processed data loader in {time.time() - start_time}s')
        try:
            logger.info('Model fit Started...')
            self.model.fit(metadata, processed_dataloader, **model_fit_kwargs or {})
            logger.info('Model fit... Finished')
        finally:
            processed_dataloader.finalize(clear_cache=True)

    def sample(self, count: int, chunksize: None | int=None, metadata: None | Metadata=None, model_sample_args: None | dict[str, Any]=None) -> pd.DataFrame | Generator[pd.DataFrame, None, None]:
        """
        Sample data from the synthesizer.

        Args:
            count (int): The number of samples to generate.
            chunksize (int, optional): The chunksize to use. Defaults to None. If is not None, the data will be sampled in chunks.
                And will return a generator that yields chunks of samples.
            metadata (Metadata, optional): The metadata to use. Defaults to None. If None, will use the metadata in fit first.
            model_sample_args (dict[str, Any], optional): The keyword arguments for model.sample. Defaults to None.

        Returns:
            pd.DataFrame | typing.Generator[pd.DataFrame, None, None]: The sampled data. When chunksize is not None, it will be a generator.
        """
        logger.info('Sampling...')
        metadata = metadata or self.metadata
        self.metadata = metadata
        if not model_sample_args:
            model_sample_args = {}
        if chunksize is None:
            return self._sample_once(count, model_sample_args)
        if chunksize > count:
            raise SynthesizerSampleError('chunksize must be less than or equal to count')

        def generator_sample_caller():
            sample_times = count // chunksize
            for _ in range(sample_times):
                sample_data = self._sample_once(chunksize, model_sample_args)
                for d in self.data_processors:
                    sample_data = d.reverse_convert(sample_data)
                yield sample_data
            if count % chunksize > 0:
                sample_data = self._sample_once(count % chunksize, model_sample_args)
                for d in self.data_processors:
                    sample_data = d.reverse_convert(sample_data)
                yield sample_data
        return generator_sample_caller()

    def _sample_once(self, count: int, model_sample_args: None | dict[str, Any]=None) -> pd.DataFrame:
        """
        Sample data once.

        DataProcessors may drop some broken data after reverse_convert.
        So we oversample first and then take the first `count` samples.

        TODO:

            - Use an adaptive scale for oversampling will be better for performance.

        """
        missing_count = count
        max_trails = 50
        sample_data_list = []
        psb = tqdm.tqdm(total=count, desc='Sampling')
        batch_size: int = 0
        multiply_factor: float = 4.0
        if isinstance(self.model, BatchedSynthesizer):
            batch_size = self.model.get_batch_size()
            multiply_factor = 1.2
            if isinstance(self.model, CTGANSynthesizerModel):
                model_sample_args = {'drop_more': False}
        while missing_count > 0 and max_trails > 0:
            sample_data = self.model.sample(max(int(missing_count * multiply_factor), batch_size), **model_sample_args)
            for d in self.data_processors:
                sample_data = d.reverse_convert(sample_data)
            sample_data = sample_data.dropna(how='all')
            sample_data_list.append(sample_data)
            missing_count = missing_count - len(sample_data)
            psb.update(len(sample_data))
            max_trails -= 1
        return pd.concat(sample_data_list)[:count]

    def cleanup(self):
        """
        Cleanup resources. This will cause model unavailable and clear the cache.

        It useful when Synthesizer object is no longer needed and may hold large resources like GPUs.
        """
        if self.dataloader:
            self.dataloader.finalize(clear_cache=True)
        if hasattr(self, 'model'):
            del self.model

    def __del__(self):
        self.cleanup()

def __init__(self, model: str | SynthesizerModel | type[SynthesizerModel], model_path: None | str | Path=None, model_kwargs: None | dict[str, Any]=None, metadata: None | Metadata=None, metadata_path: None | str | Path=None, data_connector: None | str | DataConnector | type[DataConnector]=None, data_connector_kwargs: None | dict[str, Any]=None, raw_data_loaders_kwargs: None | dict[str, Any]=None, processed_data_loaders_kwargs: None | dict[str, Any]=None, data_processors: None | list[str | DataProcessor | type[DataProcessor]]=None, data_processors_kwargs: None | dict[str, Any]=None):
    if isinstance(data_connector, str) or isinstance(data_connector, type):
        data_connector = DataConnectorManager().init_data_connector(data_connector, **data_connector_kwargs or {})
    if data_connector:
        self.dataloader = DataLoader(data_connector, **raw_data_loaders_kwargs or {})
    else:
        logger.warning('No data_connector provided, will not support `fit`')
        self.dataloader = None
    self.data_processors_manager = DataProcessorManager()
    if not data_processors:
        data_processors = self.data_processors_manager.registed_default_processor_list
    logger.info(f'Using data processors: {data_processors}')
    self.data_processors = [d if isinstance(d, DataProcessor) else self.data_processors_manager.init_data_processor(d, **data_processors_kwargs or {}) for d in data_processors]
    if metadata and metadata_path:
        raise SynthesizerInitError('metadata and metadata_path cannot be specified at the same time')
    if metadata:
        self.metadata = metadata
    elif metadata_path:
        self.metadata = Metadata.load(metadata_path)
    else:
        self.metadata = None
    self.model_manager = ModelManager()
    if isinstance(model, SynthesizerModel) and model_path:
        raise SynthesizerInitError('model as instance and model_path cannot be specified at the same time')
    if (isinstance(model, str) or isinstance(model, type)) and model_path:
        self.model = self.model_manager.load(model, model_path, **model_kwargs or {})
        if model_kwargs:
            logger.warning('model_kwargs will be ignored when loading model from model_path')
    elif isinstance(model, str) or isinstance(model, type):
        self.model = self.model_manager.init_model(model, **model_kwargs or {})
    elif isinstance(model, SynthesizerModel) or isinstance(model, StatisticSynthesizerModel):
        self.model = model
        if model_kwargs:
            logger.warning('model_kwargs will be ignored when using already initialized model')
    else:
        raise SynthesizerInitError('model or model_path must be specified')
    self.processed_data_loaders_kwargs = processed_data_loaders_kwargs or {}

def save(self, save_dir: str | Path) -> Path:
    """
        Dump metadata and model to file

        Args:
            save_dir (str | Path): The directory to save the model.

        Returns:
            Path: The directory to save the synthesizer.
        """
    save_dir = Path(save_dir).expanduser().resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'Saving synthesizer to {save_dir}')
    if self.metadata:
        self.metadata.save(save_dir / self.METADATA_SAVE_NAME)
    model_save_dir = save_dir / self.MODEL_SAVE_DIR
    model_save_dir.mkdir(parents=True, exist_ok=True)
    self.model.save(model_save_dir)
    return save_dir

@classmethod
def load(cls, load_dir: str | Path, model: str | type[SynthesizerModel], metadata: None | Metadata=None, data_connector: None | str | DataConnector | type[DataConnector]=None, data_connector_kwargs: None | dict[str, Any]=None, raw_data_loaders_kwargs: None | dict[str, Any]=None, processed_data_loaders_kwargs: None | dict[str, Any]=None, data_processors: None | list[str | DataProcessor | type[DataProcessor]]=None, data_processors_kwargs: None | dict[str, dict[str, Any]]=None, model_kwargs=None) -> 'Synthesizer':
    """
        Load metadata and model, allow rebuilding Synthesizer for finetuning or other use cases.

        We need ``model`` as not every model support *pickle* way to save and load.

        Args:
            load_dir (str | Path): The directory to load the model.
            model (str | type[SynthesizerModel]): The name of the model or the model itself. Type of model must be :class:`~sdgx.models.base.SynthesizerModel`.
                When model is a string, it must be registered in :class:`~sdgx.models.manager.ModelManager`.
            metadata (Metadata, optional): The metadata to use. Defaults to None.
            data_connector (DataConnector | type[DataConnector] | str, optional): The data connector to use. Defaults to None.
                When data_connector is a string, it must be registered in :class:`~sdgx.data_connectors.manager.DataConnectorManager`.
            data_connector_kwargs (dict[str, Any], optional): The keyword arguments for data connectors. Defaults to None.
            raw_data_loaders_kwargs (dict[str, Any], optional): The keyword arguments for raw data loaders. Defaults to None.
            processed_data_loaders_kwargs (dict[str, Any], optional): The keyword arguments for processed data loaders. Defaults to None.
            data_processors (list[str | DataProcessor | type[DataProcessor]], optional): The data processors to use. Defaults to None.
                When data_processor is a string, it must be registered in :class:`~sdgx.data_processors.manager.DataProcessorManager`.
            data_processors_kwargs (dict[str, dict[str, Any]], optional): The keyword arguments for data processors. Defaults to None.

        Returns:
            Synthesizer: The synthesizer instance.
        """
    load_dir = Path(load_dir).expanduser().resolve()
    logger.info(f'Loading synthesizer from {load_dir}')
    if not load_dir.exists():
        raise SynthesizerInitError(f'{load_dir.as_posix()} does not exist')
    model_path = load_dir / cls.MODEL_SAVE_DIR
    if not model_path.exists():
        raise SynthesizerInitError(f'{model_path.as_posix()} does not exist, cannot load model.')
    metadata_path = load_dir / cls.METADATA_SAVE_NAME
    if not metadata_path.exists():
        metadata_path = None
    return Synthesizer(model=model, model_path=model_path, metadata=metadata, metadata_path=metadata_path, model_kwargs=model_kwargs, data_connector=data_connector, data_connector_kwargs=data_connector_kwargs, raw_data_loaders_kwargs=raw_data_loaders_kwargs, processed_data_loaders_kwargs=processed_data_loaders_kwargs, data_processors=data_processors, data_processors_kwargs=data_processors_kwargs)

def fit(self, metadata: None | Metadata=None, inspector_max_chunk: int=10, metadata_include_inspectors: None | list[str]=None, metadata_exclude_inspectors: None | list[str]=None, inspector_init_kwargs: None | dict[str, Any]=None, model_fit_kwargs: None | dict[str, Any]=None):
    """
        Fit the synthesizer with metadata and data processors.

        Raw data will be loaded from the dataloader and processed by the data processors in a Generator.
        The Generator, which prevents the processed data, will be wrapped into a DataLoader, aka ProcessedDataLoader.
        The ProcessedDataLoader will be used to fit the model.

        For more information about DataLoaders, please refer to the :class:`~sdgx.data_loaders.base.DataLoader`.

        For more information about DataProcessors, please refer to the :class:`~sdgx.data_processors.base.DataProcessor`.

        For more information about DataConnectors, please refer to the :class:`~sdgx.data_connectors.base.DataConnector`. Especially, the :class:`~sdgx.data_connectors.generator_connector.GeneratorConnector`.

        Args:
            metadata (Metadata, optional): The metadata to use. Defaults to None. If None, it will be inferred from the dataloader with the :func:`~sdgx.data_models.metadata.Metadata.from_dataloader` method.
            inspector_max_chunk (int, optional): The maximum number of chunks to inspect. Defaults to 10.
            metadata_include_inspectors (list[str], optional): The list of metadata inspectors to include. Defaults to None.
            metadata_exclude_inspectors (list[str], optional): The list of metadata inspectors to exclude. Defaults to None.
            inspector_init_kwargs (dict[str, Any], optional): The keyword arguments for metadata inspectors. Defaults to None.
            model_fit_kwargs (dict[str, Any], optional): The keyword arguments for model.fit. Defaults to None.
        """
    if self.dataloader is None:
        raise SynthesizerInitError('Cannot fit without dataloader, check `data_connector` parameter when initializing Synthesizer')
    metadata = metadata or self.metadata or Metadata.from_dataloader(self.dataloader, max_chunk=inspector_max_chunk, include_inspectors=metadata_include_inspectors, exclude_inspectors=metadata_exclude_inspectors, inspector_init_kwargs=inspector_init_kwargs)
    self.metadata = metadata.model_copy()
    logger.info('Fitting data processors...')
    if not self.dataloader:
        logger.info('Fitting without dataloader.')
    start_time = time.time()
    for d in self.data_processors:
        if self.dataloader:
            d.fit(metadata=metadata, tabular_data=self.dataloader)
        else:
            d.fit(metadata=metadata)
    logger.info(f'Fitted {len(self.data_processors)} data processors in  {time.time() - start_time}s.')

    def chunk_generator() -> Generator[pd.DataFrame, None, None]:
        for chunk in self.dataloader.iter():
            for d in self.data_processors:
                chunk = d.convert(chunk)
            yield chunk
    logger.info('Initializing processed data loader...')
    start_time = time.time()
    processed_dataloader = DataLoader(GeneratorConnector(chunk_generator), identity=self.dataloader.identity, **self.processed_data_loaders_kwargs)
    logger.info(f'Initialized processed data loader in {time.time() - start_time}s')
    try:
        logger.info('Model fit Started...')
        self.model.fit(metadata, processed_dataloader, **model_fit_kwargs or {})
        logger.info('Model fit... Finished')
    finally:
        processed_dataloader.finalize(clear_cache=True)

def download_demo_data(data_dir: str | Path='./dataset') -> Path:
    """
    Download demo data if not exist

    Args:
        data_dir(str | Path): data directory

    Returns:
        pathlib.Path: demo data path
    """
    data_dir = Path(data_dir).expanduser().resolve()
    demo_data_path = data_dir / 'adult.csv'
    if not demo_data_path.exists():
        demo_data_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info('Downloading demo data from github data source to {}'.format(demo_data_path))
        url = 'https://raw.githubusercontent.com/saravrajavelu/Adult-Income-Analysis/master/adult.csv'
        urllib.request.urlretrieve(url, demo_data_path)
    return demo_data_path

def download_multi_table_demo_data(data_dir: str | Path='./dataset', dataset_name='rossman') -> dict[str, Path]:
    """
    Download multi-table demo data "Rossman Store Sales" or "Rossmann Store Sales" if not exist

    Args:
        data_dir(str | Path): data directory

    Returns:
        dict[str, pathlib.Path]: dict, the key is table name, value is demo data path
    """
    demo_data_info = MULTI_TABLE_DEMO_DATA[dataset_name]
    data_dir = Path(data_dir).expanduser().resolve()
    parent_file_name = dataset_name + '_' + demo_data_info['parent_table'] + '.csv'
    child_file_name = dataset_name + '_' + demo_data_info['child_table'] + '.csv'
    demo_data_path_parent = data_dir / parent_file_name
    demo_data_path_child = data_dir / child_file_name
    if not demo_data_path_parent.exists():
        demo_data_path_parent.parent.mkdir(parents=True, exist_ok=True)
        logger.info('Downloading parent table from github to {}'.format(demo_data_path_parent))
        parent_url = demo_data_info['parent_url']
        urllib.request.urlretrieve(parent_url, demo_data_path_parent)
    if not demo_data_path_child.exists():
        demo_data_path_child.parent.mkdir(parents=True, exist_ok=True)
        logger.info('Downloading child table from github to {}'.format(demo_data_path_child))
        parent_url = demo_data_info['child_url']
        urllib.request.urlretrieve(parent_url, demo_data_path_child)
    return {demo_data_info['parent_table']: demo_data_path_parent, demo_data_info['child_table']: demo_data_path_child}

class DataLoader:
    """
    Combine :ref:`Cacher` and :ref:`DataConnector` to load data in an efficient way.

    Default Cacher is :ref:`DiskCache`. Use ``cacher`` or ``cache_mode`` to specify a :ref:`Cacher`.

    GeneratorConnector must combine with Cacher, we will warmup cache for generator to support random access.

    Args:
        data_connector (:ref:`DataConnector`): The data connector
        chunksize (int, optional): The chunksize of the cacher. Defaults to 1000.
        cacher (:ref:`Cacher`, optional): The cacher. Defaults to None.
        cache_mode (str, optional): The cache mode(cachers' name). Defaults to "DiskCache", more info in :ref:`DiskCache`.
        cacher_kwargs (dict, optional): The kwargs for cacher. Defaults to None
        identity (str, optional): The identity of the data source.
            When using :ref:`GeneratorConnector`, it can be pointed to the original data source, makes it possible to work with :ref:`MetadataCombiner`.

    Example:

        Load and cache data from existing csv file or other data source.

        .. code-block:: python

            from sdgx.data_loader import DataLoader
            from sdgx.data_connectors.csv_connector import CsvConnector
            from sdgx.utils import download_demo_data

            dataset_csv = download_demo_data()
            data_connector = CsvConnector(path=dataset_csv)

            # Use DataConnector to initialize

            dataloader = DataLoader(data_connector)

            # Access data

            dataloader.load_all()  # This will read all data from csv, and cache it.
            dataloader.load_all()  # This will read all data from cache.

            dataloader[:10] # dataloader support slicing

            for df in dataloader.iter():  # dataloader support iteration
                print(df.shape)

    Advanced usage:

        Load and cache data from a generator.

        .. code-block:: python

            from sdgx.data_loader import DataLoader
            from sdgx.data_connectors.generator_connector import GeneratorConnector

            def generator() -> Generator[pd.DataFrame, None, None]:
                for i in range(100):
                    yield pd.DataFrame({"a": [i], "b": [i]})

            data_connector = GeneratorConnector(generator)

            # Use DataConnector to initialize.
            # Generator is not support random access, but we can achieve it by caching.
            dataloader = DataLoader(data_connector)

            # Access data
            dataloader.load_all()  # This will read all data from cache
            dataloader.load_all()  # This will read all data from cache.

            dataloader[:10] # dataloader support slicing

            for df in dataloader.iter():  # dataloader support iteration
                print(df.shape)


    """
    DEFAULT_CACHER_INITIAL = DiskCache

    def __init__(self, data_connector: DataConnector, chunksize: int=10000, cacher: Cacher | str | type[Cacher] | None=None, cacher_kwargs: None | dict[str, Any]=None, identity: str | None=None) -> None:
        if isinstance(data_connector, DataFrameConnector):
            self.DEFAULT_CACHER = NoCache
        else:
            self.DEFAULT_CACHER = DataLoader.DEFAULT_CACHER_INITIAL
        self.data_connector = data_connector
        self.chunksize = chunksize
        self.cache_manager = CacherManager()
        self.identity = identity or self.data_connector.identity or str(id(self))
        if not cacher_kwargs:
            cacher_kwargs = {}
        cacher_kwargs.setdefault('blocksize', self.chunksize)
        cacher_kwargs.setdefault('identity', self.data_connector.identity)
        if isinstance(cacher, Cacher):
            self.cacher = cacher
        elif isinstance(cacher, str) or isinstance(cacher, type):
            self.cacher = self.cache_manager.init_cacher(cacher, **cacher_kwargs)
        else:
            self.cacher = self.cache_manager.init_cacher(self.DEFAULT_CACHER, **cacher_kwargs)
        self.cacher.clear_invalid_cache()
        if isinstance(data_connector, GeneratorConnector):
            if isinstance(self.cacher, NoCache):
                raise DataLoaderInitError("NoCache can't be used with GeneratorConnector")
            self.load_all()

    def iter(self) -> Generator[pd.DataFrame, None, None]:
        """
        Load data from cache in chunk.
        """
        for d in self.cacher.iter(self.chunksize, self.data_connector):
            yield d

    def keys(self) -> list:
        """
        Same as ``columns``
        """
        return self.data_connector.keys()

    def columns(self) -> list:
        """
        Peak columns.

        Returns:
            list: name of columns
        """
        return self.data_connector.columns()

    def load_all(self) -> pd.DataFrame:
        """
        Load all data from cache.
        """
        return self.cacher.load_all(self.data_connector)

    def finalize(self, clear_cache=False) -> None:
        """
        Finalize the dataloader.
        """
        self.data_connector.finalize()
        if clear_cache:
            self.cacher.clear_cache()

    def __getitem__(self, key: int | slice | list) -> pd.DataFrame:
        """
        Support get data by index and slice.
        """
        if isinstance(key, int):
            return self.cacher.load(offset=key // self.chunksize * self.chunksize, chunksize=self.chunksize, data_connector=self.data_connector)[0]
        if isinstance(key, list):
            return pd.concat((d[key] for d in self.iter()), ignore_index=True)
        assert isinstance(key, slice)
        start = key.start or 0
        stop = key.stop or len(self)
        step = key.step or 1
        offset = start // self.chunksize * self.chunksize
        n_iter = (stop - start) // self.chunksize + 1
        tables = (self.cacher.load(offset=offset + i * self.chunksize, chunksize=self.chunksize, data_connector=self.data_connector) for i in range(n_iter))
        return pd.concat(tables, ignore_index=True)[start - offset:stop - offset:step]

    @cache
    def __len__(self):
        return sum((len(l) for l in self.iter()))

    @cached_property
    def shape(self):
        return (len(self), len(self.columns()))

def finalize(self, clear_cache=False) -> None:
    """
        Finalize the dataloader.
        """
    self.data_connector.finalize()
    if clear_cache:
        self.cacher.clear_cache()

@click.command()
@torch_run_warpper
@click.option('--save_dir', type=str, required=True, default='', help='The directory to save the synthesizer')
@click.option('--model', type=str, required=True, help='The name of the model.')
@click.option('--model_path', type=str, default=None, help='The path of the model to load')
@click.option('--model_kwargs', type=str, default=None, help='[Json String] The kwargs of the model for initialization')
@click.option('--load_dir', type=str, default=None, help='The directory to load the synthesizer, if it is specified, ``model_path`` will be ignored.')
@click.option('--metadata_path', type=str, default=None, help='The path of the metadata to load')
@click.option('--data_connector', type=str, default=None, help='The name of the data connector to use')
@click.option('--data_connector_kwargs', type=str, default=None, help='[Json String] The kwargs of the data connector to use')
@click.option('--raw_data_loaders_kwargs', type=str, default=None, help='[Json String] The kwargs of the raw data loader to use')
@click.option('--processed_data_loaders_kwargs', type=str, default=None, help='[Json String] The kwargs of the processed data loader to use')
@click.option('--data_processors', type=str, default=None, help="[Comma separated list] The name of the data processors to use, e.g. 'processor_x,processor_y'")
@click.option('--data_processors_kwargs', type=str, default=None, help='[Json String] The kwargs of the data processors to use')
@click.option('--inspector_max_chunk', type=int, default=None, help='The max chunk of the inspector to load')
@click.option('--metadata_include_inspectors', type=str, default=None, help="[Comma separated list] The name of the inspectors to include, e.g. 'inspector_x,inspector_y'")
@click.option('--metadata_exclude_inspectors', type=str, default=None, help="[Comma separated list] The name of the inspectors to exclude, e.g. 'inspector_x,inspector_y'")
@click.option('--inspector_init_kwargs', type=str, default=None, help='[Json String] The kwargs of the inspector to use')
@click.option('--model_fit_kwargs', type=str, default=None, help='[Json String] The kwargs of the model fit method')
@click.option('--dry_run', type=bool, default=False, help='Only init the synthesizer without fitting and save.')
@cli_wrapper
def fit(save_dir: str, model: str, model_path: str | None, model_kwargs: str | None, load_dir: str | None, metadata_path: str | None, data_connector: str | None, data_connector_kwargs: str | None, raw_data_loaders_kwargs: str | None, processed_data_loaders_kwargs: str | None, data_processors: str | None, data_processors_kwargs: str | None, inspector_max_chunk: int | None, metadata_include_inspectors: str | None, metadata_exclude_inspectors: str | None=None, inspector_init_kwargs: str | None=None, model_fit_kwargs: str | None=None, dry_run: bool=False):
    """
    Fit the synthesizer or load a synthesizer for fitnuning/retraining/continue training...
    """
    if data_processors is not None:
        data_processors = data_processors.strip().split(',')
    if model_kwargs is not None:
        model_kwargs = json.loads(model_kwargs)
    if data_connector_kwargs is not None:
        data_connector_kwargs = json.loads(data_connector_kwargs)
    if raw_data_loaders_kwargs is not None:
        raw_data_loaders_kwargs = json.loads(raw_data_loaders_kwargs)
    if processed_data_loaders_kwargs is not None:
        processed_data_loaders_kwargs = json.loads(processed_data_loaders_kwargs)
    if data_processors_kwargs is not None:
        data_processors_kwargs = json.loads(data_processors_kwargs)
    fit_kwargs = {}
    if inspector_max_chunk is not None:
        fit_kwargs['inspector_max_chunk'] = inspector_max_chunk
    if metadata_include_inspectors is not None:
        fit_kwargs['metadata_include_inspectors'] = metadata_include_inspectors.strip().split(',')
    if metadata_exclude_inspectors is not None:
        fit_kwargs['metadata_exclude_inspectors'] = metadata_exclude_inspectors.strip().split(',')
    if inspector_init_kwargs is not None:
        fit_kwargs['inspector_init_kwargs'] = json.loads(inspector_init_kwargs)
    if model_fit_kwargs is not None:
        fit_kwargs['model_fit_kwargs'] = json.loads(model_fit_kwargs)
    if not save_dir:
        save_dir = Path(f'./sdgx-fit-model-{model}-{time.time()}')
    else:
        save_dir = Path(save_dir).expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
    if load_dir:
        if model_path:
            logger.warning('Both ``model_path`` and ``load_dir`` are specified, ``model_path`` will be ignored.')
        synthesizer = Synthesizer.load(load_dir=load_dir, metadata_path=metadata_path, data_connector=data_connector, data_connector_kwargs=data_connector_kwargs, raw_data_loaders_kwargs=raw_data_loaders_kwargs, processed_data_loaders_kwargs=processed_data_loaders_kwargs, data_processors=data_processors, data_processors_kwargs=data_processors_kwargs)
    else:
        if model_kwargs and model_path:
            logger.warning('Both ``model_kwargs`` and ``model_path`` are specified, ``model_kwargs`` will be ignored.')
        synthesizer = Synthesizer(model=model, model_kwargs=model_kwargs, model_path=model_path, metadata_path=metadata_path, data_connector=data_connector, data_connector_kwargs=data_connector_kwargs, raw_data_loaders_kwargs=raw_data_loaders_kwargs, processed_data_loaders_kwargs=processed_data_loaders_kwargs, data_processors=data_processors, data_processors_kwargs=data_processors_kwargs)
    if dry_run:
        return
    synthesizer.fit(**fit_kwargs)
    save_dir = synthesizer.save(save_dir)
    return save_dir.absolute().as_posix()

@click.command()
@torch_run_warpper
@click.option('--load_dir', type=str, required=True, help='The directory to load the synthesizer.')
@click.option('--model', type=str, required=True, help='The name of the model.')
@click.option('--raw_data_loaders_kwargs', type=str, default=None, help='[Json String] The kwargs of the raw data loaders.')
@click.option('--processed_data_loaders_kwargs', type=str, default=None, help='[Json String] The kwargs of the processed data loaders.')
@click.option('--data_processors', type=str, default=None, help="[Comma separated list] The name of the data processors, e.g. 'data_processor_1,data_processor_2'.")
@click.option('--data_processors_kwargs', type=str, default=None, help='[Json String] The kwargs of the data processors.')
@click.option('--count', type=int, default=100, help='The number of samples to generate.')
@click.option('--chunksize', type=int, default=None, help='The size of each chunk. If count is very large, chunksize is recommended.')
@click.option('--model_sample_args', type=str, default=None, help='[Json String] The kwargs of the model.sample.')
@click.option('--data_exporter', type=str, default='CsvExporter', required=True, help='The name of the data exporter.')
@click.option('--data_exporter_kwargs', type=str, default=None, help='[Json String] The kwargs of the data exporter.')
@click.option('--export_dst', type=str, default=None, help='The destination of the exported data.')
@click.option('--dry_run', type=bool, default=False, help='Dry run. Only initialize the synthesizer without sampling.')
@cli_wrapper
def sample(load_dir: str, model: str, raw_data_loaders_kwargs: str | None, processed_data_loaders_kwargs: str | None, data_processors: str | None, data_processors_kwargs: str | None, count: int, chunksize: int | None, model_sample_args: str | None, data_exporter: str, data_exporter_kwargs: str | None, export_dst: str | None, dry_run: bool):
    """
    Load a synthesizer and sample.

    ``load_dir`` should contain model and metadata. Please check :ref:`Synthesizer <Synthesizer>`'s `load` method for more details.
    """
    if data_processors is not None:
        data_processors = data_processors.strip().split(',')
    if raw_data_loaders_kwargs is not None:
        raw_data_loaders_kwargs = json.loads(raw_data_loaders_kwargs)
    if processed_data_loaders_kwargs is not None:
        processed_data_loaders_kwargs = json.loads(processed_data_loaders_kwargs)
    if data_processors_kwargs is not None:
        data_processors_kwargs = json.loads(data_processors_kwargs)
    if model_sample_args is not None:
        model_sample_args = json.loads(model_sample_args)
    if data_exporter_kwargs is not None:
        data_exporter_kwargs = json.loads(data_exporter_kwargs)
    else:
        data_exporter_kwargs = {}
    if not export_dst:
        export_dst = Path(f'./sdgx-{model}-{time.time()}/sample-data.csv').expanduser().resolve()
    synthesizer = Synthesizer.load(load_dir=load_dir, model=model, raw_data_loaders_kwargs=raw_data_loaders_kwargs, processed_data_loaders_kwargs=processed_data_loaders_kwargs, data_processors=data_processors, data_processors_kwargs=data_processors_kwargs)
    exporter = DataExporterManager().init_exporter(data_exporter, **data_exporter_kwargs)
    if dry_run:
        return
    exporter.write(export_dst, synthesizer.sample(count=count, chunksize=chunksize, model_sample_args=model_sample_args))
    return export_dst

@click.command()
@cli_wrapper
def list_models():
    for model_name, model_cls in ModelManager().registed_models.items():
        print(f'{model_name} is registed as class: {model_cls}.')

@click.command()
@cli_wrapper
def list_data_connectors():
    for model_name, model_cls in DataConnectorManager().registed_data_connectors.items():
        print(f'{model_name} is registed as class: {model_cls}.')

@click.command()
@cli_wrapper
def list_data_processors():
    for model_name, model_cls in DataProcessorManager().registed_data_processors.items():
        print(f'{model_name} is registed as class: {model_cls}.')

@click.command()
@cli_wrapper
def list_data_exporters():
    for model_name, model_cls in DataExporterManager().registed_exporters.items():
        print(f'{model_name} is registed as class: {model_cls}.')

@click.group()
def cli():
    pass

class ExitMessage(BaseModel):
    code: int
    msg: str
    payload: dict = {}

    def _dump_json(self) -> str:
        return self.model_dump_json()

    def send(self):
        print(self._dump_json(), flush=True, end='')

def send(self):
    print(self._dump_json(), flush=True, end='')

class DiskCache(Cacher):
    """
    Cacher that cache data in disk with parquet format

    Args:
        blocksize (int): The blocksize of the cache.
        cache_dir (str | Path | None, optional): The directory where the cache will be stored. Defaults to None.
        identity (str | None, optional): The identity of the data source. Defaults to None.

    Todo:
        * Add partial cache when blocksize > chunksize
        * Improve cache invalidation
        * Improve performance if blocksize > chunksize
    """

    def __init__(self, cache_dir: str | Path | None=None, identity: str | None=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not cache_dir:
            cache_dir = Path.cwd() / '.sdgx_cache'
            if identity:
                cache_dir = cache_dir / identity
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def clear_cache(self) -> None:
        """
        Clear all cache in cache_dir.
        """
        for f in self.cache_dir.glob('*.parquet'):
            f.unlink()
        shutil.rmtree(self.cache_dir, ignore_errors=True)

    def clear_invalid_cache(self):
        """
        Clear all cache in cache_dir.

        TODO: Improve cache invalidation
        """
        return self.clear_cache()

    def _get_cache_filename(self, offset: int) -> Path:
        """
        Get cache filename
        """
        return self.cache_dir / f'{offset}.parquet'

    def is_cached(self, offset: int) -> bool:
        """
        Check if the data is cached by checking if the cache file exists
        """
        return self._get_cache_filename(offset).exists()

    def _refresh(self, offset: int, data: pd.DataFrame) -> None:
        """
        Refresh cache, will write data to cache file in parquet format.
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if len(data) < self.blocksize:
            data.to_parquet(self._get_cache_filename(offset))
        elif len(data) > self.blocksize:
            for i in range(0, len(data), self.blocksize):
                data[i:i + self.blocksize].to_parquet(self._get_cache_filename(offset + i))
        else:
            data.to_parquet(self._get_cache_filename(offset))

    def load(self, offset: int, chunksize: int, data_connector: DataConnector) -> pd.DataFrame:
        """
        Load data from data_connector or cache
        """
        if chunksize % self.blocksize != 0:
            raise CacheError('chunksize must be multiple of blocksize, current chunksize is {} and blocksize is {}'.format(chunksize, self.blocksize))
        if chunksize != self.blocksize:
            logger.warning('chunksize must be equal to blocksize, may cause performance issue.')
        if self.is_cached(offset):
            cached_data = pd.read_parquet(self._get_cache_filename(offset))
            if len(cached_data) >= chunksize:
                return cached_data[:chunksize]
            return cached_data
        limit = max(self.blocksize, chunksize)
        data = data_connector.read(offset=offset, limit=limit)
        if data is None:
            return data
        data_list: List[pd.DataFrame] = [data]
        while len(data) < limit:
            next_data = data_connector.read(offset=offset + len(data), limit=limit - len(data))
            if next_data is None or len(next_data) == 0:
                break
            data_list.append(next_data)
        data = pd.concat(data_list, ignore_index=True) if len(data_list) > 1 else data
        self._refresh(offset, data)
        if len(data) < chunksize:
            return data
        return data[:chunksize]

    def iter(self, chunksize: int, data_connector: DataConnector) -> Generator[pd.DataFrame, None, None]:
        """
        Load data from data_connector or cache in chunk
        """
        offset = 0
        while True:
            data = self.load(offset, chunksize, data_connector)
            if data is None or len(data) == 0:
                break
            yield data
            offset += len(data)

def __init__(self, cache_dir: str | Path | None=None, identity: str | None=None, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    if not cache_dir:
        cache_dir = Path.cwd() / '.sdgx_cache'
        if identity:
            cache_dir = cache_dir / identity
    self.cache_dir = Path(cache_dir)
    self.cache_dir.mkdir(parents=True, exist_ok=True)

def clear_cache(self) -> None:
    """
        Clear all cache in cache_dir.
        """
    for f in self.cache_dir.glob('*.parquet'):
        f.unlink()
    shutil.rmtree(self.cache_dir, ignore_errors=True)

def clear_invalid_cache(self):
    """
        Clear all cache in cache_dir.

        TODO: Improve cache invalidation
        """
    return self.clear_cache()

def is_cached(self, offset: int) -> bool:
    """
        Check if the data is cached by checking if the cache file exists
        """
    return self._get_cache_filename(offset).exists()

def _refresh(self, offset: int, data: pd.DataFrame) -> None:
    """
        Refresh cache, will write data to cache file in parquet format.
        """
    self.cache_dir.mkdir(parents=True, exist_ok=True)
    if len(data) < self.blocksize:
        data.to_parquet(self._get_cache_filename(offset))
    elif len(data) > self.blocksize:
        for i in range(0, len(data), self.blocksize):
            data[i:i + self.blocksize].to_parquet(self._get_cache_filename(offset + i))
    else:
        data.to_parquet(self._get_cache_filename(offset))

class Relationship(BaseModel):
    """Relationship between tables

    For parent table, we don't need define primary key here.
    The primary key is pre-defined in parent table's metadata.

    Child table's foreign key should be defined here.
    """
    version: str = '1.0'
    parent_table: str
    child_table: str
    foreign_keys: List[KeyTuple]
    '\n    foreign keys.\n\n    If key is a tuple, the first element is parent column name and the second element is child column name\n    '

    @classmethod
    def build(cls, parent_table: str, child_table: str, foreign_keys: Iterable[str | tuple[str, str] | KeyTuple], parent_metadata: Metadata | None=None, child_metadata: Metadata | None=None) -> 'Relationship':
        """
        Build relationship from parent table, child table and foreign keys

        Args:
            parent_table (str): parent table
            parent_metadata : metadata of parent table
            child_table (str): child table
            child_metadata : metadata of child table
            foreign_keys (Iterable[str | tuple[str, str]]): foreign keys. If key is a tuple, the first element is parent column name and the second element is child column name
        """
        if not parent_table:
            raise RelationshipInitError('parent table cannot be empty')
        if not child_table:
            raise RelationshipInitError('child table cannot be empty')
        foreign_keys = [KeyTuple(key, key) if isinstance(key, str) else KeyTuple(*key) for key in foreign_keys]
        if not foreign_keys:
            raise RelationshipInitError('foreign keys cannot be empty')
        if parent_table == child_table:
            raise RelationshipInitError('child table and parent table cannot be the same')
        if parent_metadata and child_metadata:
            for key in foreign_keys:
                if type(parent_metadata) is not dict:
                    if key[0] not in parent_metadata.id_columns:
                        raise RelationshipInitError('type of foreign key in parent table is not id')
                    if key[1] not in child_metadata.id_columns:
                        raise RelationshipInitError('type of foreign key in child table is not id')
                else:
                    if key[0] not in parent_metadata['id_columns']:
                        raise RelationshipInitError('type of foreign key in parent table is not id')
                    if key[1] not in child_metadata['id_columns']:
                        raise RelationshipInitError('type of foreign key in child table is not id')
        return cls(parent_table=parent_table, child_table=child_table, foreign_keys=foreign_keys)

    def _dump_json(self):
        return self.model_dump_json()

    def save(self, path: str | Path):
        """
        Save relationship to json file.
        """
        with path.open('w') as f:
            f.write(self._dump_json())

    @classmethod
    def load(cls, path: str | Path) -> 'Relationship':
        """
        Load relationship from json file.
        """
        path = Path(path).expanduser().resolve()
        fields = json.load(path.open('r'))
        version = fields.pop('version', None)
        if version:
            cls.upgrade(version, fields)
        return Relationship.build(**fields)

    @classmethod
    def upgrade(cls, old_version: str, fields: dict[str, Any]) -> None:
        pass

def save(self, path: str | Path):
    """
        Save relationship to json file.
        """
    with path.open('w') as f:
        f.write(self._dump_json())

@classmethod
def load(cls, path: str | Path) -> 'Relationship':
    """
        Load relationship from json file.
        """
    path = Path(path).expanduser().resolve()
    fields = json.load(path.open('r'))
    version = fields.pop('version', None)
    if version:
        cls.upgrade(version, fields)
    return Relationship.build(**fields)

class Metadata(BaseModel):
    """
    Metadata is mainly used to describe the data types of all columns in a single data table.

    For each column, there should be an instance of the Data Type object.

    .. Note::

        Use ``get``, ``set``, ``add``, ``delete`` to update tags in the metadata. And use `query` for querying a column for its tags.

    Args:
        primary_keys(List[str]): The primary key, a field used to uniquely identify each row in the table.
        The primary key of each row must be unique and not empty.

        column_list(list[str]): list of the comlumn name in the table, other columns lists are used to store column information.
    """
    primary_keys: Set[str] = set()
    '\n    primary_keys is used to store single primary key or composite primary key\n    '
    column_list: List[str] = Field(default_factory=list, title='The List of Column Names')
    '"\n    column_list is the actual value of self.column_list\n    '

    @field_validator('column_list')
    @classmethod
    def check_column_list(cls, value) -> Any:
        if len(value) == len(set(value)):
            return value
        raise MetadataInitError('column_list has duplicate element!')
    column_inspect_level: Dict[str, int] = defaultdict(lambda: 10)
    "\n    column_inspect_level is used to store every inspector's level, to specify the true type of each column.\n    "
    pii_columns: Set[str] = set()
    "\n    pii_columns is used to store all PII columns' name\n    "
    id_columns: Set[str] = set()
    int_columns: Set[str] = set()
    float_columns: Set[str] = set()
    bool_columns: Set[str] = set()
    discrete_columns: Set[str] = set()
    datetime_columns: Set[str] = set()
    const_columns: Set[str] = set()
    datetime_format: Dict = defaultdict(str)
    numeric_format: Dict = defaultdict(list)
    categorical_encoder: Union[Dict[str, CategoricalEncoderType], None] = defaultdict(str)
    categorical_threshold: Union[Dict[int, CategoricalEncoderType], None] = None
    version: str = '1.0'
    _extend: Dict[str, Set[str]] = defaultdict(set)
    '\n    For extend information, use ``get`` and ``set``\n    '

    def get_column_encoder_by_categorical_threshold(self, num_categories: int) -> Union[CategoricalEncoderType, None]:
        encoder_type = None
        if self.categorical_threshold is None:
            return encoder_type
        for threshold in sorted(self.categorical_threshold.keys()):
            if num_categories > threshold:
                encoder_type = self.categorical_threshold[threshold]
            else:
                break
        return encoder_type

    def get_column_encoder_by_name(self, column_name) -> Union[CategoricalEncoderType, None]:
        encoder_type = None
        if self.categorical_encoder and column_name in self.categorical_encoder:
            encoder_type = self.categorical_encoder[column_name]
        return encoder_type

    @property
    def tag_fields(self) -> Iterable[str]:
        """
        Return all tag fields in this metadata.
        """
        return chain((k for k in self.model_fields if k.endswith('_columns')), (k for k in self._extend.keys() if k.endswith('_columns')))

    @property
    def format_fields(self) -> Iterable[str]:
        """
        Return all tag fields in this metadata.
        """
        return chain((k for k in self.model_fields if k.endswith('_format')), (k for k in self._extend.keys() if k.endswith('_format')))

    def __eq__(self, other):
        if not isinstance(other, Metadata):
            return super().__eq__(other)
        return set(self.tag_fields) == set(other.tag_fields) and all((self.get(key) == other.get(key) for key in set(chain(self.tag_fields, other.tag_fields)))) and all((self.get(key) == other.get(key) for key in set(chain(self.format_fields, other.format_fields)))) and (self.version == other.version)

    def query(self, field: str) -> Iterable[str]:
        """
        Query all tags of a field.

        Args:
            field(str): The field to query.

        Example:

            .. code-block:: python

                # Assume that user_id looks like 1,2,3,4
                m.query("user_id") == ["id_columns", "numeric_columns"]
        """
        return (k for k in self.tag_fields if field in self.get(k))

    def get(self, key: str) -> Set[str]:
        """
        Get all tags by key.

        Args:
            key(str): The key to get.

        Example:

            .. code-block:: python

                # Get all id columns
                m.get("id_columns") == {"user_id", "ticket_id"}
        """
        if key == '_extend':
            raise MetadataInitError('Cannot get _extend directly')
        return getattr(self, key) if key in self.model_fields else self._extend[key]

    def set(self, key: str, value: Any):
        """
        Set tags, will convert value to set if value is not a set.

        Args:
            key(str): The key to set.
            value(Any): The value to set.

        Example:

            .. code-block:: python

                # Set all id columns
                m.set("id_columns", {"user_id", "ticket_id"})
        """
        if key == '_extend':
            raise MetadataInitError('Cannot set _extend directly')
        old_value = self.get(key)
        if key in self.model_fields and key not in self.tag_fields and (key not in self.format_fields):
            raise MetadataInitError(f'Set {key} not in tag_fields, try set it directly as m.{key} = value')
        if isinstance(old_value, Iterable) and (not isinstance(old_value, str)):
            value = value if isinstance(value, Iterable) and (not isinstance(value, str)) else [value]
            try:
                value = type(old_value)(value)
            except TypeError as e:
                if type(old_value) == defaultdict:
                    value = dict(value)
                else:
                    raise e
        if key in self.model_fields:
            setattr(self, key, value)
        else:
            self._extend[key] = value

    def add(self, key: str, values: str | Iterable[str]):
        """
        Add tags.

        Args:
            key(str): The key to add.
            values(str | Iterable[str]): The value to add.

        Example:

            .. code-block:: python

                # Add all id columns
                m.add("id_columns", "user_id")
                m.add("id_columns", "ticket_id")
                # OR
                m.add("id_columns", ["user_id", "ticket_id"])
                # OR
                # add datetime format
                m.add('datetime_format',{"col_1": "%Y-%m-%d %H:%M:%S", "col_2": "%d %b %Y"})
        """
        values = values if isinstance(values, Iterable) and (not isinstance(values, str)) else [values]
        if isinstance(values, dict):
            if key in list(self.format_fields):
                self.get(key).update(values)
            if self._extend.get(key, None) is None:
                self._extend[key] = values
            else:
                self._extend[key].update(values)
            return
        for value in values:
            self.get(key).add(value)

    def delete(self, key: str, value: str):
        """
        Delete tags.

        Args:
            key(str): The key to delete.
            value(str): The value to delete.

        Example:

            .. code-block:: python

                # Delete misidentification id columns
                m.delete("id_columns", "not_an_id_columns")

        """
        try:
            self.get(key).remove(value)
        except KeyError:
            pass

    def update(self, attributes: dict[str, Any]):
        """
        Update tags.
        """
        for k, v in attributes.items():
            self.add(k, v)
        return self

    @classmethod
    def from_dataloader(cls, dataloader: DataLoader, max_chunk: int=10, primary_keys: Set[str]=None, include_inspectors: Iterable[str] | None=None, exclude_inspectors: Iterable[str] | None=None, inspector_init_kwargs: dict[str, Any] | None=None, check: bool=False) -> 'Metadata':
        """Initialize a metadata from DataLoader and Inspectors

        Args:
            dataloader(DataLoader): the input DataLoader.
            max_chunk(int): max chunk count.
            primary_keys(list[str]): primary keys, see :class:`~sdgx.data_models.metadata.Metadata` for more details.
            include_inspectors(list[str]): data type inspectors used in this metadata (table).
            exclude_inspectors(list[str]): data type inspectors NOT used in this metadata (table).
            inspector_init_kwargs(dict): inspector args.
        """
        logger.info('Inspecting metadata...')
        im = InspectorManager()
        exclude_inspectors = exclude_inspectors or []
        exclude_inspectors.extend((name for name, inspector_type in im.registed_inspectors.items() if issubclass(inspector_type, RelationshipInspector)))
        inspectors = im.init_inspcetors(include_inspectors, exclude_inspectors, **inspector_init_kwargs or {})
        for inspector in inspectors:
            inspector.ready = False
        for i, chunk in enumerate(dataloader.iter()):
            for inspector in inspectors:
                if not inspector.ready:
                    inspector.fit(chunk)
            if all((i.ready for i in inspectors)) or i > max_chunk:
                break
        if primary_keys is None:
            primary_keys = set()
        metadata = Metadata(primary_keys=primary_keys, column_list=dataloader.columns())
        for inspector in inspectors:
            inspect_res = inspector.inspect()
            metadata.update(inspect_res)
            if inspector.pii:
                for each_key in inspect_res:
                    metadata.update({'pii_columns': inspect_res[each_key]})
            for each_key in inspect_res:
                if 'columns' in each_key:
                    metadata.column_inspect_level[each_key] = inspector.inspect_level
        if not primary_keys:
            metadata.update_primary_key(metadata.id_columns)
        if check:
            metadata.check()
        return metadata

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, include_inspectors: list[str] | None=None, exclude_inspectors: list[str] | None=None, inspector_init_kwargs: dict[str, Any] | None=None, check: bool=False) -> 'Metadata':
        """Initialize a metadata from DataFrame and Inspectors

        Args:
            df(pd.DataFrame): the input DataFrame.
            include_inspectors(list[str]): data type inspectors used in this metadata (table).
            exclude_inspectors(list[str]): data type inspectors NOT used in this metadata (table).
            inspector_init_kwargs(dict): inspector args.
        """
        im = InspectorManager()
        exclude_inspectors = exclude_inspectors or []
        exclude_inspectors.extend((name for name, inspector_type in im.registed_inspectors.items() if issubclass(inspector_type, RelationshipInspector)))
        inspectors = im.init_inspcetors(include_inspectors, exclude_inspectors, **inspector_init_kwargs or {})
        for inspector in inspectors:
            inspector.fit(df)
        metadata = Metadata(primary_keys=[df.columns[0]], column_list=df.columns)
        for inspector in inspectors:
            inspect_res = inspector.inspect()
            metadata.update(inspect_res)
            if inspector.pii:
                for each_key in inspect_res:
                    metadata.update({'pii_columns': inspect_res[each_key]})
            for each_key in inspect_res:
                if 'columns' in each_key:
                    metadata.column_inspect_level[each_key] = inspector.inspect_level
        if check:
            metadata.check()
        return metadata

    def _dump_json(self) -> str:
        return self.model_dump_json(indent=4)

    def save(self, path: str | Path):
        """
        Save metadata to json file.
        """
        with path.open('w') as f:
            f.write(self._dump_json())

    @classmethod
    def loads(cls, attributes):
        return Metadata(**attributes)

    @classmethod
    def load(cls, path: str | Path) -> 'Metadata':
        """
        Load metadata from json file.
        """
        path = Path(path).expanduser().resolve()
        attributes = json.load(path.open('r'))
        version = attributes.get('version', None)
        if version:
            cls.upgrade(version, attributes)
        m = Metadata(**attributes)
        return m

    @classmethod
    def upgrade(cls, old_version: str, fields: dict[str, Any]) -> None:
        pass

    def check_single_primary_key(self, input_key: str):
        """Check whether a primary key in column_list and has ID data type.

        Args:
            input_key(str): the input primary_key str
        """
        if input_key not in self.column_list:
            raise MetadataInvalidError(f'Primary Key {input_key} not Exist in columns.')

    def get_all_data_type_columns(self):
        """Get all column names from `self.xxx_columns`.

        All Lists with the suffix _columns in model fields and extend fields need to be collected.
        All defined column names will be counted.

        Returns:
            all_dtype_cols(set): set of all column names.
        """
        all_dtype_cols = set()
        for each_key in list(self.model_fields.keys()) + list(self._extend.keys()):
            if each_key.endswith('_columns'):
                column_names = self.get(each_key)
                all_dtype_cols = all_dtype_cols.union(set(column_names))
        return all_dtype_cols

    def check(self):
        """Checks column info.

        When passing as input to the next module, perform necessary checks, including:
            -Is the primary key correctly defined(in column list) and has ID data type.
            -Is there any missing definition of each column in table.
            -Are there any unknown columns that have been incorrectly updated.
        """
        for each_key in self.primary_keys:
            self.check_single_primary_key(each_key)
        if len(self.primary_keys) == 1 and list(self.primary_keys)[0] not in self.id_columns:
            raise MetadataInvalidError(f'Primary Key {self.primary_keys} should has ID DataType.')
        all_dtype_columns = self.get_all_data_type_columns()
        if set(self.column_list) - set(all_dtype_columns):
            raise MetadataInvalidError(f'Undefined data type for column {set(self.column_list) - set(all_dtype_columns)}.')
        if set(all_dtype_columns) - set(self.column_list):
            raise MetadataInvalidError(f'Found undefined column: {set(all_dtype_columns) - set(self.column_list)}.')
        if self.categorical_encoder is not None:
            for i in self.categorical_encoder.keys():
                if not isinstance(i, str) or i not in self.discrete_columns:
                    raise MetadataInvalidError(f'categorical_encoder key {i} is invalid, it should be an str and is a discrete column name.')
            if self.categorical_encoder.values() not in CategoricalEncoderType:
                raise MetadataInvalidError(f'In categorical_encoder values, categorical encoder type invalid, now supports {list(CategoricalEncoderType)}.')
        if self.categorical_threshold is not None:
            for i in self.categorical_threshold.keys():
                if not isinstance(i, int) or i < 0:
                    raise MetadataInvalidError(f'categorical threshold {i} is invalid, it should be an positive int.')
            if self.categorical_threshold.values() not in CategoricalEncoderType:
                raise MetadataInvalidError(f'In categorical_threshold values, categorical encoder type invalid, now supports {list(CategoricalEncoderType)}.')
        logger.debug('Metadata check succeed.')

    def update_primary_key(self, primary_keys: Iterable[str] | str):
        """Update the primary key of the table

        When update the primary key, the original primary key will be erased.

        Args:
            primary_keys(Iterable[str]): the primary keys of this table.
        """
        if not isinstance(primary_keys, Iterable) and (not isinstance(primary_keys, str)):
            raise MetadataInvalidError('Primary key should be Iterable or str.')
        primary_keys = set(primary_keys if isinstance(primary_keys, Iterable) else [primary_keys])
        if not primary_keys.issubset(set(self.column_list)):
            raise MetadataInvalidError('Primary key not exist in table columns.')
        self.primary_keys = primary_keys
        logger.info(f'Primary Key updated: {primary_keys}.')

    def dump(self):
        """Dump model dict, can be used in downstream process, like processor.

        Returns:
            dict: dumped dict.
        """
        model_dict = self.model_dump()
        model_dict['column_data_type'] = {}
        for each_col in self.column_list:
            model_dict['column_data_type'][each_col] = self.get_column_data_type(each_col)
        return model_dict

    def get_column_data_type(self, column_name: str):
        """Get the exact type of specific column.
        Args:
            column_name(str): The query colmun name.
        Returns:
            str: The data type query result.
        """
        if column_name not in self.column_list:
            raise MetadataInvalidError(f'Column {column_name}not exists in metadata.')
        current_type = None
        current_level = 0
        for each_key in list(self.model_fields.keys()) + list(self._extend.keys()):
            if each_key != 'pii_columns' and each_key.endswith('_columns') and (column_name in self.get(each_key)) and (current_level < self.column_inspect_level[each_key]):
                current_level = self.column_inspect_level[each_key]
                current_type = each_key
        if not current_type:
            raise MetadataInvalidError(f'Column {column_name} has no data type.')
        return current_type.split('_columns')[0]

    def get_column_pii(self, column_name: str):
        """Return if a column is a PII column.
        Args:
            column_name(str): The query colmun name.
        Returns:
            bool: The PII query result.
        """
        if column_name not in self.column_list:
            raise MetadataInvalidError(f'Column {column_name}not exists in metadata.')
        if column_name in self.pii_columns:
            return True
        return False

    def change_column_type(self, column_names: str | List[str], column_original_type: str, column_new_type: str):
        """Change the type of column."""
        if not column_names:
            return
        if isinstance(column_names, str):
            column_names = [column_names]
        all_fields = list(self.tag_fields)
        original_type = f'{column_original_type}_columns'
        new_type = f'{column_new_type}_columns'
        if original_type not in all_fields:
            raise MetadataInvalidError(f'Column type {column_original_type} not exist in metadata.')
        if new_type not in all_fields:
            raise MetadataInvalidError(f'Column type {column_new_type} not exist in metadata.')
        type_columns = self.get(original_type)
        diff = set(column_names).difference(type_columns)
        if diff:
            raise MetadataInvalidError(f'Columns {column_names} not exist in {original_type}.')
        self.add(new_type, column_names)
        type_columns = type_columns.difference(column_names)
        self.set(original_type, type_columns)

    def remove_column(self, column_names: List[str] | str):
        """
        Remove a column from all columns type.
        Args:
            column_names: List[str]: To removed columns name list.
        """
        if not column_names:
            return
        if isinstance(column_names, str):
            column_names = [column_names]
        column_names = frozenset(column_names)
        inter = column_names.intersection(self.column_list)
        if not inter:
            raise MetadataInvalidError(f'Columns {inter} not exist in metadata.')

        def do_remove_columns(key, get=True, to_removes=column_names):
            obj = self
            if get:
                target = obj.get(key)
            else:
                target = getattr(obj, key)
            res = None
            if isinstance(target, list):
                res = [item for item in target if item not in to_removes]
            elif isinstance(target, dict):
                if key == 'numeric_format':
                    obj.set(key, {k: {v2 for v2 in v if v2 not in to_removes} for k, v in target.items()})
                else:
                    res = {k: v for k, v in target.items() if k not in to_removes}
            elif isinstance(target, set):
                res = target.difference(to_removes)
            if res is not None:
                if get:
                    obj.set(key, res)
                else:
                    setattr(obj, key, res)
        to_remove_attribute = list(self.tag_fields)
        to_remove_attribute.extend(list(self.format_fields))
        for attr in to_remove_attribute:
            do_remove_columns(attr)
        for attr in ['column_list', 'primary_keys']:
            do_remove_columns(attr, False)
        self.check()

def save(self, path: str | Path):
    """
        Save metadata to json file.
        """
    with path.open('w') as f:
        f.write(self._dump_json())

@classmethod
def loads(cls, attributes):
    return Metadata(**attributes)

@classmethod
def load(cls, path: str | Path) -> 'Metadata':
    """
        Load metadata from json file.
        """
    path = Path(path).expanduser().resolve()
    attributes = json.load(path.open('r'))
    version = attributes.get('version', None)
    if version:
        cls.upgrade(version, attributes)
    m = Metadata(**attributes)
    return m

class MetadataCombiner(BaseModel):
    """
    Combine different tables with relationship, used for describing the relationship between tables.

    Args:
        version (str): version
        named_metadata (Dict[str, Any]): pairs of table name and metadata
        relationships (List[Any]): list of relationships
    """
    version: str = '1.0'
    named_metadata: Dict[str, Metadata] = {}
    relationships: List[Relationship] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def check(self):
        """Do necessary checks:

        - Whether number of tables corresponds to relationships.
        - Whether table names corresponds to the relationship between tables;
        """
        for m in self.named_metadata.values():
            m.check()
        table_names = set(self.named_metadata.keys())
        relationship_parents = set((r.parent_table for r in self.relationships))
        relationship_children = set((r.child_table for r in self.relationships))
        if not table_names.issuperset(relationship_parents):
            raise MetadataCombinerInvalidError(f"Relationships' parent table {relationship_parents - table_names} is missing.")
        if not table_names.issuperset(relationship_children):
            raise MetadataCombinerInvalidError(f"Relationships' child table {relationship_children - table_names} is missing.")
        if not (relationship_parents | relationship_children).issuperset(table_names):
            raise MetadataCombinerInvalidError(f'Table {table_names - (relationship_parents + relationship_children)} is missing in relationships.')
        logger.info('MultiTableCombiner check finished.')

    @classmethod
    def from_dataloader(cls, dataloaders: list[DataLoader], metadata_from_dataloader_kwargs: None | dict=None, relationshipe_inspector: None | str | type[Inspector]='SubsetRelationshipInspector', relationships_inspector_kwargs: None | dict=None, relationships: None | list[Relationship]=None):
        """
        Combine multiple dataloaders with relationship.

        Args:
            dataloaders (list[DataLoader]): list of dataloaders
            max_chunk (int): max chunk count for relationship inspector.
            metadata_from_dataloader_kwargs (dict): kwargs for :func:`Metadata.from_dataloader`
            relationshipe_inspector (str | type[Inspector]): relationship inspector
            relationships_inspector_kwargs (dict): kwargs for :func:`InspectorManager.init`
            relationships (list[Relationship]): list of relationships
        """
        if not isinstance(dataloaders, list):
            dataloaders = [dataloaders]
        metadata_from_dataloader_kwargs = metadata_from_dataloader_kwargs or {}
        named_metadata = {d.identity: Metadata.from_dataloader(d, **metadata_from_dataloader_kwargs) for d in dataloaders}
        if relationships is None and relationshipe_inspector is not None:
            if relationships_inspector_kwargs is None:
                relationships_inspector_kwargs = {}
            inspector = InspectorManager().init(relationshipe_inspector, **relationships_inspector_kwargs)
            for d in dataloaders:
                for chunk in d.iter():
                    inspector.fit(chunk, name=d.identity, metadata=named_metadata[d.identity])
            relationships = inspector.inspect()['relationships']
        return cls(named_metadata=named_metadata, relationships=relationships)

    @classmethod
    def from_dataframe(cls, dataframes: list[pd.DataFrame], names: list[str], metadata_from_dataloader_kwargs: None | dict=None, relationshipe_inspector: None | str | type[Inspector]='SubsetRelationshipInspector', relationships_inspector_kwargs: None | dict=None, relationships: None | list[Relationship]=None) -> 'MetadataCombiner':
        """
        Combine multiple dataframes with relationship.

        Args:
            dataframes (list[pd.DataFrame]): list of dataframes
            names (list[str]): list of names
            metadata_from_dataloader_kwargs (dict): kwargs for :func:`Metadata.from_dataloader`
            relationshipe_inspector (str | type[Inspector]): relationship inspector
            relationships_inspector_kwargs (dict): kwargs for :func:`InspectorManager.init`
            relationships (list[Relationship]): list of relationships
        """
        if not isinstance(dataframes, list):
            dataframes = [dataframes]
        if not isinstance(names, list):
            names = [names]
        metadata_from_dataloader_kwargs = metadata_from_dataloader_kwargs or {}
        if len(dataframes) != len(names):
            raise MetadataCombinerInitError('dataframes and names should have same length.')
        named_metadata = {n: Metadata.from_dataframe(d, **metadata_from_dataloader_kwargs) for n, d in zip(names, dataframes)}
        if relationships is None and relationshipe_inspector is not None:
            if relationships_inspector_kwargs is None:
                relationships_inspector_kwargs = {}
            inspector = InspectorManager().init(relationshipe_inspector, **relationships_inspector_kwargs)
            for n, d in zip(names, dataframes):
                inspector.fit(d, name=n, metadata=named_metadata[n])
            relationships = inspector.inspect()['relationships']
        return cls(named_metadata=named_metadata, relationships=relationships)

    def _dump_json(self):
        return self.model_dump_json()

    def save(self, save_dir: str | Path, metadata_subdir: str='metadata', relationship_subdir: str='relationship'):
        """
        Save metadata to json file.

        This will create several subdirectories for metadata and relationship.

        Args:
            save_dir (str | Path): directory to save
            metadata_subdir (str): subdirectory for metadata, default is "metadata"
            relationship_subdir (str): subdirectory for relationship, default is "relationship"
        """
        save_dir = Path(save_dir).expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        version_file = save_dir / 'version'
        version_file.write_text(self.version)
        metadata_subdir = save_dir / metadata_subdir
        relationship_subdir = save_dir / relationship_subdir
        metadata_subdir.mkdir(parents=True, exist_ok=True)
        for name, metadata in self.named_metadata.items():
            metadata.save(metadata_subdir / f'{name}.json')
        relationship_subdir.mkdir(parents=True, exist_ok=True)
        for relationship in self.relationships:
            relationship.save(relationship_subdir / f'{relationship.parent_table}_{relationship.child_table}.json')

    @classmethod
    def load(cls, save_dir: str | Path, metadata_subdir: str='metadata', relationship_subdir: str='relationship', version: None | str=None) -> 'MetadataCombiner':
        """
        Load metadata from json file.

        Args:
            save_dir (str | Path): directory to save
            metadata_subdir (str): subdirectory for metadata, default is "metadata"
            relationship_subdir (str): subdirectory for relationship, default is "relationship"
            version (str): Manual version, if not specified, try to load from version file
        """
        save_dir = Path(save_dir).expanduser().resolve()
        if not version:
            logger.debug('No version specified, try to load from version file.')
            version_file = save_dir / 'version'
            if version_file.exists():
                version = version_file.read_text().strip()
            else:
                logger.info('No version file found, assume version is 1.0')
                version = '1.0'
        named_metadata = {p.stem: Metadata.load(p) for p in (save_dir / metadata_subdir).glob('*')}
        relationships = [Relationship.load(p) for p in (save_dir / relationship_subdir).glob('*')]
        cls.upgrade(version, named_metadata, relationships)
        return cls(version=version, named_metadata=named_metadata, relationships=relationships)

    @classmethod
    def upgrade(cls, old_version: str, named_metadata: dict[str, Metadata], relationships: list[Relationship]) -> None:
        """
        Upgrade metadata from old version to new version

        :ref:`Metadata.upgrade` and :ref:`Relationship.upgrade` will try upgrade when loading.
        So here we just do Combiner's upgrade.
        """
        pass

    @property
    def fields(self) -> Iterable[str]:
        """
        Return all fields in MetadataCombiner.
        """
        return chain((k for k in self.model_fields if k.endswith('_columns')))

    def __eq__(self, other):
        if not isinstance(other, MetadataCombiner):
            return super().__eq__(other)
        return self.version == other.version and all((self.get(key) == other.get(key) for key in set(chain(self.fields, other.fields)))) and (set(self.fields) == set(other.fields))

def save(self, save_dir: str | Path, metadata_subdir: str='metadata', relationship_subdir: str='relationship'):
    """
        Save metadata to json file.

        This will create several subdirectories for metadata and relationship.

        Args:
            save_dir (str | Path): directory to save
            metadata_subdir (str): subdirectory for metadata, default is "metadata"
            relationship_subdir (str): subdirectory for relationship, default is "relationship"
        """
    save_dir = Path(save_dir).expanduser().resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    version_file = save_dir / 'version'
    version_file.write_text(self.version)
    metadata_subdir = save_dir / metadata_subdir
    relationship_subdir = save_dir / relationship_subdir
    metadata_subdir.mkdir(parents=True, exist_ok=True)
    for name, metadata in self.named_metadata.items():
        metadata.save(metadata_subdir / f'{name}.json')
    relationship_subdir.mkdir(parents=True, exist_ok=True)
    for relationship in self.relationships:
        relationship.save(relationship_subdir / f'{relationship.parent_table}_{relationship.child_table}.json')

@classmethod
def load(cls, save_dir: str | Path, metadata_subdir: str='metadata', relationship_subdir: str='relationship', version: None | str=None) -> 'MetadataCombiner':
    """
        Load metadata from json file.

        Args:
            save_dir (str | Path): directory to save
            metadata_subdir (str): subdirectory for metadata, default is "metadata"
            relationship_subdir (str): subdirectory for relationship, default is "relationship"
            version (str): Manual version, if not specified, try to load from version file
        """
    save_dir = Path(save_dir).expanduser().resolve()
    if not version:
        logger.debug('No version specified, try to load from version file.')
        version_file = save_dir / 'version'
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            logger.info('No version file found, assume version is 1.0')
            version = '1.0'
    named_metadata = {p.stem: Metadata.load(p) for p in (save_dir / metadata_subdir).glob('*')}
    relationships = [Relationship.load(p) for p in (save_dir / relationship_subdir).glob('*')]
    cls.upgrade(version, named_metadata, relationships)
    return cls(version=version, named_metadata=named_metadata, relationships=relationships)

class SynthesizerModel:
    use_dataloader: bool = False
    use_raw_data: bool = False

    def __init__(self, *args, **kwargs) -> None:
        if 'use_dataloader' in kwargs.keys():
            self.use_dataloader = kwargs['use_dataloader']
        if 'use_raw_data' in kwargs.keys():
            self.use_raw_data = kwargs['use_raw_data']

    def _check_access_type(self):
        if self.use_dataloader == self.use_raw_data == False:
            raise SynthesizerInitError('Data access type not specified, please use `use_raw_data: bool` or `use_dataloader: bool` to specify data access type.')
        elif self.use_dataloader == self.use_raw_data == True:
            raise SynthesizerInitError('Duplicate data access type found.')

    def fit(self, metadata: Metadata, dataloader: DataLoader, *args, **kwargs):
        """
        Fit the model using the given metadata and dataloader.

        Args:
            metadata (Metadata): The metadata to use.
            dataloader (DataLoader): The dataloader to use.
        """
        raise NotImplementedError

    def sample(self, count: int, *args, **kwargs) -> pd.DataFrame:
        """
        Sample data from the model.

        Args:
            count (int): The number of samples to generate.

        Returns:
            pd.DataFrame: The generated data.
        """
        raise NotImplementedError

    def save(self, save_dir: str | Path):
        """
        Dump model to file.

        Args:
            save_dir (str | Path): The directory to save the model.
        """
        raise NotImplementedError

    @classmethod
    def load(cls, save_dir: str | Path, **kwargs) -> 'SynthesizerModel':
        """
        Load model from file.

        Args:
            save_dir (str | Path): The directory to load the model from.
        """
        raise NotImplementedError

def _check_access_type(self):
    if self.use_dataloader == self.use_raw_data == False:
        raise SynthesizerInitError('Data access type not specified, please use `use_raw_data: bool` or `use_dataloader: bool` to specify data access type.')
    elif self.use_dataloader == self.use_raw_data == True:
        raise SynthesizerInitError('Duplicate data access type found.')

class CTGANSynthesizerModel(MLSynthesizerModel, BatchedSynthesizer):
    """
    Modified from ``sdgx.models.components.sdv_ctgan.synthesizers.ctgan.CTGANSynthesizer``.
    A CTGANSynthesizer but provided :ref:`SynthesizerModel` interface with chunked fit.

    This is the core class of the CTGAN project, where the different components
    are orchestrated together.
    For more details about the process, please check the [Modeling Tabular data using
    Conditional GAN](https://arxiv.org/abs/1907.00503) paper.


    Args:
        embedding_dim (int):
            Size of the random sample passed to the Generator. Defaults to 128.
        generator_dim (tuple or list of ints):
            Size of the output samples for each one of the Residuals. A Residual Layer
            will be created for each one of the values provided. Defaults to (256, 256).
        discriminator_dim (tuple or list of ints):
            Size of the output samples for each one of the Discriminator Layers. A Linear Layer
            will be created for each one of the values provided. Defaults to (256, 256).
        generator_lr (float):
            Learning rate for the generator. Defaults to 2e-4.
        generator_decay (float):
            Generator weight decay for the Adam Optimizer. Defaults to 1e-6.
        discriminator_lr (float):
            Learning rate for the discriminator. Defaults to 2e-4.
        discriminator_decay (float):
            Discriminator weight decay for the Adam Optimizer. Defaults to 1e-6.
        batch_size (int):
            Number of data samples to process in each step.
        discriminator_steps (int):
            Number of discriminator updates to do for each generator update.
            From the WGAN paper: https://arxiv.org/abs/1701.07875. WGAN paper
            default is 5. Default used is 1 to match original CTGAN implementation.
        log_frequency (boolean):
            Whether to use log frequency of categorical levels in conditional
            sampling. Defaults to ``True``.
        epochs (int):
            Number of training epochs. Defaults to 300.
        pac (int):
            Number of samples to group together when applying the discriminator.
            Defaults to 10.
        device (str):
            Device to run the training on. Preferred to be 'cuda' for GPU if available.
    """
    MODEL_SAVE_NAME = 'ctgan.pkl'

    def __init__(self, embedding_dim=128, generator_dim=(256, 256), discriminator_dim=(256, 256), generator_lr=0.0002, generator_decay=1e-06, discriminator_lr=0.0002, discriminator_decay=1e-06, batch_size=500, discriminator_steps=1, log_frequency=True, epochs=300, pac=10, device='cuda' if torch.cuda.is_available() else 'cpu'):
        assert batch_size % 2 == 0
        BatchedSynthesizer.__init__(self, batch_size=batch_size)
        self._embedding_dim = embedding_dim
        self._generator_dim = generator_dim
        self._discriminator_dim = discriminator_dim
        self._generator_lr = generator_lr
        self._generator_decay = generator_decay
        self._discriminator_lr = discriminator_lr
        self._discriminator_decay = discriminator_decay
        self._discriminator_steps = discriminator_steps
        self._log_frequency = log_frequency
        self._epochs = epochs
        self.pac = pac
        self._device = torch.device(device)
        self._transformer: Optional[DataTransformer] = None
        self._data_sampler: Optional[DataSampler] = None
        self._generator = None
        self._ndarry_loader: Optional[NDArrayLoader] = None
        self.data_dim: Optional[int] = None

    def fit(self, metadata: Metadata, dataloader: DataLoader, epochs=None, *args, **kwargs):
        discrete_columns = list(metadata.get('discrete_columns'))
        if epochs is not None:
            self._epochs = epochs
        self._pre_fit(dataloader, discrete_columns, metadata)
        if self.fit_data_empty:
            logger.info('CTGAN fit finished because of empty df detected.')
            return
        logger.info('CTGAN prefit finished, start CTGAN training.')
        self._fit(len(self._ndarry_loader))
        logger.info('CTGAN training finished.')

    def _pre_fit(self, dataloader: DataLoader, discrete_columns: list[str]=None, metadata: Metadata=None):
        if not discrete_columns:
            discrete_columns = []
        discrete_columns = self._filter_discrete_columns(dataloader.columns(), discrete_columns)
        if self.fit_data_empty:
            return
        self._transformer = DataTransformer(metadata=metadata)
        logger.info("Fitting model's transformer...")
        self._transformer.fit(dataloader, discrete_columns)
        logger.info('Transforming data...')
        self._ndarry_loader = self._transformer.transform(dataloader)
        logger.info('Sampling data.')
        self._data_sampler = DataSampler(self._ndarry_loader, self._transformer.output_info_list, self._log_frequency)
        logger.info('Initialize Generator.')
        self.data_dim = self._transformer.output_dimensions
        self._generator = Generator(self._embedding_dim + self._data_sampler.dim_cond_vec(), self._generator_dim, self.data_dim).to(self._device)

    @random_state
    def _fit(self, data_size: int):
        """Fit the CTGAN Synthesizer models to the training data."""
        logger.info(f'Fit using data_size:{data_size}, data_dim: {self.data_dim}.')
        epochs = self._epochs
        discriminator = Discriminator(self.data_dim + self._data_sampler.dim_cond_vec(), self._discriminator_dim, pac=self.pac).to(self._device)
        optimizerG = optim.Adam(self._generator.parameters(), lr=self._generator_lr, betas=(0.5, 0.9), weight_decay=self._generator_decay)
        optimizerD = optim.Adam(discriminator.parameters(), lr=self._discriminator_lr, betas=(0.5, 0.9), weight_decay=self._discriminator_decay)
        mean = torch.zeros(self._batch_size, self._embedding_dim, device=self._device)
        std = mean + 1
        logger.info('Starting model training, epochs: {}'.format(epochs))
        steps_per_epoch = max(data_size // self._batch_size, 1)
        for i in range(epochs):
            start_time = time.time()
            for id_ in tqdm.tqdm(range(steps_per_epoch), desc='Fitting batches', delay=3):
                for n in range(self._discriminator_steps):
                    fakez = torch.normal(mean=mean, std=std)
                    condvec = self._data_sampler.sample_condvec(self._batch_size)
                    if condvec is None:
                        c1, m1, col, opt = (None, None, None, None)
                        real = self._data_sampler.sample_data(self._batch_size, col, opt)
                    else:
                        c1, m1, col, opt = condvec
                        c1 = torch.from_numpy(c1).to(self._device)
                        m1 = torch.from_numpy(m1).to(self._device)
                        fakez = torch.cat([fakez, c1], dim=1)
                        perm = np.arange(self._batch_size)
                        np.random.shuffle(perm)
                        real = self._data_sampler.sample_data(self._batch_size, col[perm], opt[perm])
                        c2 = c1[perm]
                    fake = self._generator(fakez)
                    fakeact = self._apply_activate(fake)
                    real = torch.from_numpy(real.astype('float32')).to(self._device)
                    if c1 is not None:
                        fake_cat = torch.cat([fakeact, c1], dim=1)
                        real_cat = torch.cat([real, c2], dim=1)
                    else:
                        real_cat = real
                        fake_cat = fakeact
                    y_fake = discriminator(fake_cat)
                    y_real = discriminator(real_cat)
                    pen = discriminator.calc_gradient_penalty(real_cat, fake_cat, self._device, self.pac)
                    loss_d = -(torch.mean(y_real) - torch.mean(y_fake))
                    optimizerD.zero_grad()
                    pen.backward(retain_graph=True)
                    loss_d.backward()
                    optimizerD.step()
                fakez = torch.normal(mean=mean, std=std)
                condvec = self._data_sampler.sample_condvec(self._batch_size)
                if condvec is None:
                    c1, m1, col, opt = (None, None, None, None)
                else:
                    c1, m1, col, opt = condvec
                    c1 = torch.from_numpy(c1).to(self._device)
                    m1 = torch.from_numpy(m1).to(self._device)
                    fakez = torch.cat([fakez, c1], dim=1)
                fake = self._generator(fakez)
                fakeact = self._apply_activate(fake)
                if c1 is not None:
                    y_fake = discriminator(torch.cat([fakeact, c1], dim=1))
                else:
                    y_fake = discriminator(fakeact)
                if condvec is None:
                    cross_entropy = 0
                else:
                    cross_entropy = self._cond_loss(fake, c1, m1)
                loss_g = -torch.mean(y_fake) + cross_entropy
                optimizerG.zero_grad()
                loss_g.backward()
                optimizerG.step()
            logger.info(f'Epoch {i + 1}, Loss G: {loss_g.detach().cpu(): .4f}, Loss D: {loss_d.detach().cpu(): .4f}, Time: {time.time() - start_time: .4f}')

    def sample(self, count: int, *args, **kwargs) -> pd.DataFrame:
        if self.fit_data_empty:
            return pd.DataFrame(index=range(count))
        return self._sample(count, *args, **kwargs)

    @random_state
    def _sample(self, n, condition_column=None, condition_value=None, drop_more=True):
        """Sample data similar to the training data.

        Choosing a condition_column and condition_value will increase the probability of the
        discrete condition_value happening in the condition_column.

        Args:
            n (int):
                Number of rows to sample.
            condition_column (string):
                Name of a discrete column.
            condition_value (string):
                Name of the category in the condition_column which we wish to increase the
                probability of happening.

        Returns:
            numpy.ndarray or pandas.DataFrame
        """
        if condition_column is not None and condition_value is not None:
            condition_info = self._transformer.convert_column_name_value_to_id(condition_column, condition_value)
            global_condition_vec = self._data_sampler.generate_cond_from_condition_column_info(condition_info, self._batch_size)
        else:
            global_condition_vec = None
        steps = math.ceil(n / self._batch_size)
        data = []
        for _ in tqdm.tqdm(range(steps), desc='Sampling batches', delay=3):
            mean = torch.zeros(self._batch_size, self._embedding_dim)
            std = mean + 1
            fakez = torch.normal(mean=mean, std=std).to(self._device)
            if global_condition_vec is not None:
                condvec = global_condition_vec.copy()
            else:
                condvec = self._data_sampler.sample_original_condvec(self._batch_size)
            if condvec is None:
                pass
            else:
                c1 = condvec
                c1 = torch.from_numpy(c1).to(self._device)
                fakez = torch.cat([fakez, c1], dim=1)
            fake = self._generator(fakez)
            fakeact = self._apply_activate(fake)
            data.append(fakeact.detach().cpu().numpy())
        data = np.concatenate(data, axis=0)
        logger.info('CTGAN Generated {} raw samples.'.format(data.shape[0]))
        if drop_more:
            data = data[:n]
        return self._transformer.inverse_transform(data)

    def save(self, save_dir: str | Path):
        save_dir.mkdir(parents=True, exist_ok=True)
        return SDVBaseSynthesizer.save(self, save_dir / self.MODEL_SAVE_NAME)

    @classmethod
    def load(cls, save_dir: str | Path, device: str=None) -> 'CTGANSynthesizerModel':
        return SDVBaseSynthesizer.load(save_dir / cls.MODEL_SAVE_NAME, device)

    @staticmethod
    def _gumbel_softmax(logits, tau=1, hard=False, eps=1e-10, dim=-1):
        """Deals with the instability of the gumbel_softmax for older versions of torch.

        For more details about the issue:
        https://drive.google.com/file/d/1AA5wPfZ1kquaRtVruCd6BiYZGcDeNxyP/view?usp=sharing

        Args:
            logits […, num_features]:
                Unnormalized log probabilities
            tau:
                Non-negative scalar temperature
            hard (bool):
                If True, the returned samples will be discretized as one-hot vectors,
                but will be differentiated as if it is the soft sample in autograd
            dim (int):
                A dimension along which softmax will be computed. Default: -1.

        Returns:
            Sampled tensor of same shape as logits from the Gumbel-Softmax distribution.
        """
        if version.parse(torch.__version__) < version.parse('1.2.0'):
            for i in range(10):
                transformed = functional.gumbel_softmax(logits, tau=tau, hard=hard, eps=eps, dim=dim)
                if not torch.isnan(transformed).any():
                    return transformed
            raise ValueError('gumbel_softmax returning NaN.')
        return functional.gumbel_softmax(logits, tau=tau, hard=hard, eps=eps, dim=dim)

    def _apply_activate(self, data):
        """Apply proper activation function to the output of the generator."""
        data_t = []
        st = 0
        for column_info in self._transformer.output_info_list:
            for span_info in column_info:
                if span_info.activation_fn == 'tanh':
                    ed = st + span_info.dim
                    data_t.append(torch.tanh(data[:, st:ed]))
                    st = ed
                elif span_info.activation_fn == 'softmax':
                    ed = st + span_info.dim
                    transformed = self._gumbel_softmax(data[:, st:ed], tau=0.2)
                    data_t.append(transformed)
                    st = ed
                elif span_info.activation_fn == 'linear':
                    ed = st + span_info.dim
                    transformed = data[:, st:ed].clone()
                    data_t.append(transformed)
                    st = ed
                else:
                    raise ValueError(f'Unexpected activation function {span_info.activation_fn}.')
        return torch.cat(data_t, dim=1)

    def _cond_loss(self, data, c, m):
        """Compute the cross entropy loss on the fixed discrete column."""
        loss = []
        st = 0
        st_c = 0
        for column_info in self._transformer.output_info_list:
            for span_info in column_info:
                if len(column_info) != 1 or span_info.activation_fn != 'softmax':
                    st += span_info.dim
                else:
                    ed = st + span_info.dim
                    ed_c = st_c + span_info.dim
                    tmp = functional.cross_entropy(data[:, st:ed], torch.argmax(c[:, st_c:ed_c], dim=1), reduction='none')
                    loss.append(tmp)
                    st = ed
                    st_c = ed_c
        loss = torch.stack(loss, dim=1)
        return (loss * m).sum() / data.size()[0]

    def _filter_discrete_columns(self, train_data: List[str], discrete_columns: List[str]):
        """
        We filter PII Column here, which PII would only be discrete for now.
        As PII would be generating from PII Generator which not synthetic from model.

        Besides we need to figure it out when to stop model fitting:
        The original data consists entirely of discrete column data, and all of this discrete column data is PII.

        For `train_data`, there are three possibilities for the columns type.
         - train_data = valid_discrete + valid_continue
         - train_data = valid_continue
         - train_data = valid_discrete

        For `discrete_columns`, discrete_columns = invalid_discrete(PII) + valid_discrete

        Thus, valid_discrete = discrete_columns - invalid_discrete
                             = discrete_columns - Set.intersection(train_data, discrete_columns)

        Thus, original_data_is_all_PII: discrete_columns is not empty & train_data is empty
        """
        if len(discrete_columns) == 0:
            return discrete_columns
        if len(train_data) == 0:
            self.fit_data_empty = True
            return discrete_columns
        invalid_columns = set(discrete_columns) - set(train_data)
        return set(discrete_columns) - set(invalid_columns)

    def _validate_discrete_columns(self, train_data, discrete_columns):
        """Check whether ``discrete_columns`` exists in ``train_data``.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame or list):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        if isinstance(train_data, pd.DataFrame):
            invalid_columns = set(discrete_columns) - set(train_data.columns)
        elif isinstance(train_data, np.ndarray):
            invalid_columns = []
            for column in discrete_columns:
                if column < 0 or column >= train_data.shape[1]:
                    invalid_columns.append(column)
        elif isinstance(train_data, list):
            invalid_columns = set(discrete_columns) - set(train_data)
        else:
            raise TypeError('``train_data`` should be either pd.DataFrame or np.array.')
        if invalid_columns:
            raise ValueError(f'Invalid columns found: {invalid_columns}')

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU)."""
        self._device = device
        if self._generator is not None:
            self._generator.to(self._device)

def save(self, save_dir: str | Path):
    save_dir.mkdir(parents=True, exist_ok=True)
    return SDVBaseSynthesizer.save(self, save_dir / self.MODEL_SAVE_NAME)

@classmethod
def load(cls, save_dir: str | Path, device: str=None) -> 'CTGANSynthesizerModel':
    return SDVBaseSynthesizer.load(save_dir / cls.MODEL_SAVE_NAME, device)

class LLMBaseModel(SynthesizerModel):
    """
    This is a base class for generating synthetic data using LLM (Large Language Model).

    Note:
    - When using the data loader, the original data is transformed to pd.DataFrame format for subsequent processing.
    - It is not recommended to use this model with large data tables due to excessive token consumption in some expensive LLM service.
    - Generating data based on metadata is a potential way to generate data that cannot be made public and contains sensitive information.
    """
    use_raw_data = False
    '\n    By default, we use raw_data for data access.\n\n    When using the data loader, due to the need of randomization operation, we currently use the `.load_all()` to transform the original data to pd.DataFrame format for subsequent processing.\n\n    Due to the characteristics of the OpenAI GPT service, we do not recommend running this model with large data tables, which will consume your tokens excessively.\n    '
    use_metadata = False
    '\n    In this model, we accept a data generation paradigm that only provides metadata.\n\n    When only metadata is provided, sdgx will format the metadata of the data set into a message and transmit it to GPT, and GPT will generate similar data based on what it knows.\n\n    This is a potential way to generate data that cannot be made public and contains sensitive information.\n    '
    _metadata = None
    '\n    the metadata.\n    '
    off_table_features = []
    '\n    * Experimental Feature\n\n    Whether infer data columns that do not exist in the real data table, the effect may not be very good.\n    '
    prompts = {'message_prefix': 'Suppose you are the best data generating model in this world, we have some data samples with the following information:\n\n', 'message_suffix': '\nGenerate synthetic data samples based on the above information and your knowledge, each sample should be output on one line (do not output in multiple lines), the output format of the sample is the same as the example in this message, such as "column_name_1 is value_1", the count of the generated data samples is ', 'system_role_content': 'You are a powerful synthetic data generation model.'}
    '\n    Prompt words for generating data (preliminary version, improvements welcome).\n    '
    columns = []
    '\n    The columns of the data set.\n    '
    dataset_description = ''
    '\n    The description of the data set.\n    '
    _responses = []
    '\n    A list to store the responses received from the LLM.\n    '
    _message_list = []
    '\n    A list to store the messages used to ask LLM.\n    '

    def _check_access_type(self):
        """
        Checks the data access type.

        Raises:
            SynthesizerInitError: If data access type is not specified or if duplicate data access type is found.
        """
        if self.use_dataloader == self.use_raw_data == self.use_metadata == False:
            raise SynthesizerInitError('Data access type not specified, please use `use_raw_data: bool` or `use_dataloader: bool` to specify data access type.')
        if self.use_dataloader == self.use_raw_data == True:
            raise SynthesizerInitError('Duplicate data access type found.')

    def _form_columns_description(self):
        """
        We believe that giving information about a column helps improve data quality.

        Currently, we leave this function to Good First Issue until March 2024, if unclaimed we will implement it quickly.
        """
        raise NotImplementedError

    def _form_message_with_offtable_features(self):
        """
        This function forms a message with off-table features.

        If there are more off-table columns, additional processing is excuted here.
        """
        if self.off_table_features:
            logger.info(f'Use off_table_feature = {self.off_table_features}.')
            return f'Also, you should try to infer another {len(self.off_table_features)} columns based on your knowledge, the name of these columns are : {self.off_table_features}, attach these columns after the original table. \n'
        else:
            logger.info('No off_table_feature needed in current model.')
            return ''

    def _form_dataset_description(self):
        """
        This function is used to form the dataset description.

        Returns:
            str: The description of the generated table.
        """
        if self.dataset_description:
            logger.info(f'Use dataset_description = {self.dataset_description}.')
            return '\nThe description of the generated table is ' + self.dataset_description + '\n'
        else:
            logger.info('No dataset_description given in current model.')
            return ''

def _check_access_type(self):
    """
        Checks the data access type.

        Raises:
            SynthesizerInitError: If data access type is not specified or if duplicate data access type is found.
        """
    if self.use_dataloader == self.use_raw_data == self.use_metadata == False:
        raise SynthesizerInitError('Data access type not specified, please use `use_raw_data: bool` or `use_dataloader: bool` to specify data access type.')
    if self.use_dataloader == self.use_raw_data == True:
        raise SynthesizerInitError('Duplicate data access type found.')

class SingleTableGPTModel(LLMBaseModel):
    """
    This is a synthetic data generation model powered by OpenAI GPT, a state-of-the-art language model. This model is based on groundbreaking research presented in the ICLR paper titled "Language Models are Realistic Tabular Data Generators".

    Our model harnesses the power of GPT to generate synthetic tabular data that closely resembles real-world datasets. By utilizing the advanced capabilities of GPT, we aim to provide a reliable and efficient solution for generating simulated data that can be used for various purposes, such as testing, training, and analysis.

    With this synthetic data generation model, users can easily generate diverse and realistic tabular datasets, mimicking the characteristics and patterns found in real data.
    """
    openai_API_key = ''
    '\n    The API key required to access the OpenAI GPT model. Please provide your own API key for authentication.\n    '
    openai_API_url = 'https://api.openai.com/v1/'
    '\n    The URL endpoint for the OpenAI GPT API. Please specify the appropriate URL for accessing the API.\n    '
    max_tokens = 4000
    '\n    The maximum number of tokens allowed in the generated response. This parameter helps in limiting the length of the output text.\n    '
    temperature = 0.1
    '\n    A parameter that controls the randomness of the generated text. Lower values like 0.1 make the output more focused and deterministic, while higher values like 1.0 introduce more randomness.\n    '
    timeout = 90
    '\n    The maximum time (in seconds) to wait for a response from the OpenAI GPT API. If the response is not received within this time, the request will be timed out.\n    '
    gpt_model = 'gpt-3.5-turbo'
    '\n    The specific GPT model to be used for generating text. The default model is "gpt-3.5-turbo", which is known for its high performance and versatility.\n    '
    query_batch = 30
    '\n    This parameter is the number of samples submitted to GPT each time and the number of returned samples.\n\n    This size has a certain relationship with the max_token parameter.\n\n    We do not recommend setting too large a value, as this may cause potential problems or errors.\n    '
    _sample_lines = []
    '\n    A list to store the sample lines of generated data.\n    '
    _result_list = []
    '\n    A list to store the generated data samples.\n    '

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the class instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._get_openai_setting_from_env()

    def check(self):
        """
        Performs various checks.

        Raises:
            SynthesizerInitError: If data access type is not specified or if duplicate data access type is found.
        """
        self._check_openAI_setting()
        self._set_openAI()
        self._check_access_type()

    def set_openAI_settings(self, API_url='https://api.openai.com/v1/', API_key=''):
        """
        Sets the OpenAI settings.

        Args:
            API_url (str): The OpenAI API URL. Defaults to "https://api.openai.com/v1/".
            API_key (str): The OpenAI API key. Defaults to an empty string.
        """
        self.openai_API_url = API_url
        self.openai_API_key = API_key
        self._set_openAI()

    def _set_openAI(self):
        """
        Sets the OpenAI API key and base URL.
        """
        openai.api_key = self.openai_API_key
        openai.base_url = self.openai_API_url

    def _check_openAI_setting(self):
        """
        Checks if the OpenAI settings are properly initialized.

        Raises:
            InitializationError: If openai_API_url or openai_API_key is not found.
        """
        if not self.openai_API_url:
            raise InitializationError('openai_API_url NOT found.')
        if not self.openai_API_key:
            raise InitializationError('openai_API_key NOT found.')
        logger.debug('OpenAI setting check passed.')

    def _get_openai_setting_from_env(self):
        """
        Retrieves OpenAI settings from environment variables.
        """
        if os.getenv('OPENAI_KEY'):
            self.openai_API_key = os.getenv('OPENAI_KEY')
            logger.debug('Get OPENAI_KEY from ENV.')
        if os.getenv('OPENAI_URL'):
            self.openai_API_url = os.getenv('OPENAI_URL')
            logger.debug('Get OPENAI_URL from ENV.')

    def openai_client(self):
        """
        Generate a openai request client.
        """
        return openai.OpenAI(api_key=self.openai_API_key, base_url=self.openai_API_url)

    def ask_gpt(self, question, model=None):
        """
        Sends a question to the GPT model.

        Args:
            question (str): The question to ask.
            model (str): The GPT model to use. Defaults to None.

        Returns:
            str: The response from the GPT model.

        Raises:
            SynthesizerInitError: If the check method fails.
        """
        self.check()
        if model:
            model = model
        else:
            model = self.gpt_model
        client = self.openai_client()
        logger.info(f'Ask GPT with temperature = {self.temperature}.')
        response = client.chat.completions.create(model=model, messages=[{'role': 'user', 'content': question}], temperature=self.temperature, max_tokens=self.max_tokens, timeout=self.timeout)
        logger.info('Ask GPT Finished.')
        self._responses.append(response)
        return response.choices[0].message.content

    def fit(self, raw_data: pd.DataFrame | DataLoader=None, metadata: Metadata=None, *args, **kwargs):
        """
        Fits this model to the provided data.
        Please note that no actual algorithmic training is excuted here.

        Args:
            raw_data (pd.DataFrame | DataLoader): The raw data to fit the model to. It can be either a pandas DataFrame or a DataLoader object.
            metadata (Metadata): The metadata associated with the raw data.

        Returns:
            None

        Raises:
            InitializationError: If neither raw_data nor metadata is provided.
        """
        if raw_data is not None and type(raw_data) in [pd.DataFrame, DataLoader]:
            if metadata:
                self._metadata = metadata
            self._fit_with_data(raw_data)
            return
        if type(raw_data) is Metadata:
            self._fit_with_metadata(raw_data)
            return
        if metadata is not None and type(metadata) is Metadata:
            self._fit_with_metadata(metadata)
            return
        raise InitializationError('Ple1ase pass at least one valid parameter, train_data or metadata')

    def _fit_with_metadata(self, metadata):
        """
        Fit the model using metadata.

        Args:
            metadata: Metadata object.

        Returns:
            None
        """
        logger.info('Fitting model with metadata...')
        self.use_metadata = True
        self._metadata = metadata
        self.columns = list(metadata.column_list)
        logger.info('Fitting model with metadata... Finished.')

    def _fit_with_data(self, train_data):
        """
        Fit the model using data.

        Args:
            train_data: Training data.

        Returns:
            None
        """
        logger.info('Fitting model with raw data...')
        self.use_raw_data = True
        self.use_dataloader = False
        if type(train_data) is DataLoader:
            self.columns = list(train_data.columns())
            train_data = train_data.load_all()
        if not self.columns:
            self.columns = list(train_data.columns)
        if not self._metadata:
            self._metadata = Metadata.from_dataframe(train_data)
        sample_lines = []
        for _, row in train_data.iterrows():
            each_line = ''
            shuffled_columns = copy(self.columns)
            random.shuffle(shuffled_columns)
            for column in shuffled_columns:
                value = str(row[column])
                each_line += f'{column} is {value}, '
            each_line = each_line[:-2]
            each_line += '\n'
            sample_lines.append(each_line)
        self._sample_lines = sample_lines
        logger.info('Fitting model with raw data... Finished.')

    @staticmethod
    def _select_random_elements(input_list, cnt):
        """
        This function selects a random sample of elements from the input list.

        Args:
            input_list (list): The list from which elements will be selected.
            cnt (int): The number of elements to be selected.

        Returns:
            list: A list of randomly selected elements from the input list.

        Raises:
            ValueError: If cnt is greater than the length of the input list.
        """
        if cnt > len(input_list):
            raise ValueError('cnt should not be greater than the length of the list')
        return random.sample(input_list, cnt)

    def _form_message_with_data(self, sample_list, current_cnt):
        """
        This function forms a message with data.

        Args:
            sample_list (list): A list of samples.
            current_cnt (int): The current count of samples.

        Returns:
            str: The formed message with data.
        """
        sample_str = ''
        for i in range(current_cnt):
            each_sample = sample_list[i]
            each_str = f'sample {i}: ' + each_sample + '\n'
            sample_str += each_str
        message = self.prompts['message_prefix'] + sample_str
        message = message + self._form_dataset_description()
        message = message + self._form_message_with_offtable_features()
        message = message + f'Please note that the generated table has total {len(self.columns) + len(self.off_table_features)} columns of the generated data, the column names are {self.columns + self.off_table_features}, every column should not be missed when generating the data. \n'
        message = message + self.prompts['message_suffix'] + str(current_cnt) + '.'
        self._message_list.append(message)
        logger.debug('Message Generated.')
        return message

    def extract_samples_from_response(self, response_content):
        """
        Extracts samples from the response content.

        Args:
            response_content (dict): The response content as a dictionary.

        Returns:
            list: A list of extracted samples.
        """

        def dict_to_list(input_dict, header):
            """
            Converts a dictionary to a list based on the given header.

            Args:
                input_dict (dict): The input dictionary.
                header (list): The list of keys to extract from the dictionary.

            Returns:
                list: A list of values extracted from the dictionary based on the header.
            """
            res = []
            for each_col in header:
                each_value = input_dict.get(each_col, None)
                res.append(each_value)
            return res
        logger.info('Extracting samples from response ...')
        header = self.columns + self.off_table_features
        features = []
        for line in response_content.split('\n'):
            feature = {}
            for field in header:
                pattern = '\\b' + field + '\\s*(?:is|=)\\s*([^,\\n]+)'
                match = re.search(pattern, line)
                if match:
                    feature[field] = match.group(1).strip()
            if feature:
                features.append(dict_to_list(feature, header))
        logger.info(f'Extracting samples from response ... Finished, {len(features)} extracted.')
        return features

    def sample(self, count=50, dataset_desp='', *args, **kwargs):
        """
        This function samples data from either raw data or metadata based on the given parameters.

        Args:
            count (int): The number of samples to be generated. Default is 50.
            dataset_desp (str): The description of the dataset. Default is an empty string.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            res: The sampled data.
        """
        logger.info('Sampling use GPT model ...')
        self.dataset_description = dataset_desp
        if self.use_raw_data:
            res = self._sample_with_data(count, *args, **kwargs)
        elif self.use_metadata:
            res = self._sample_with_metadata(count, *args, **kwargs)
        logger.info('Sampling use GPT model ... Finished.')
        return res

    def _form_message_with_metadata(self, current_cnt):
        """
        This function forms a message with metadata for table data generation task.

        Args:
            current_cnt (int): The current count of the message.

        Returns:
            str: The formed message with metadata.
        """
        message = ''
        message = message + self.prompts['message_prefix']
        message = message + self._form_dataset_description()
        message = message + 'This table data generation task will only have metadata and no data samples. The header (columns infomation) of the tabular data is: '
        message = message + str(self.columns) + '. \n'
        message = message + self._form_message_with_offtable_features()
        message = message + f'Note that the generated table has total {len(self.columns) + len(self.off_table_features)} columns, the column names are {self.columns + self.off_table_features}, every column should NOT be missed in generated data.\n'
        message = message + self.prompts['message_suffix'] + str(current_cnt) + '.'
        self._message_list.append(message)
        return message

    def _sample_with_metadata(self, count, *args, **kwargs):
        """
        This method samples data with metadata.

        Args:
            count (int): The number of samples to be generated.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            int: The input count.

        """
        logger.info('Sampling with metadata.')
        result = []
        remaining_cnt = count
        while remaining_cnt > 0:
            if remaining_cnt - self.query_batch >= 0:
                current_cnt = self.query_batch
            else:
                current_cnt = remaining_cnt
            message = self._form_message_with_metadata(current_cnt)
            response = self.ask_gpt(message)
            generated_batch = self.extract_samples_from_response(response)
            result += generated_batch
            remaining_cnt = remaining_cnt - current_cnt
        self._result_list.append(result)
        final_columns = self.columns + self.off_table_features
        return pd.DataFrame(result, columns=final_columns)

    def _sample_with_data(self, count, *args, **kwargs):
        """
        This function samples data with a given count and returns a DataFrame with the sampled data.

        Args:
            count (int): The number of data samples to be generated.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            pd.DataFrame: A DataFrame containing the sampled data.

        """
        logger.info('Sampling with raw_data.')
        result = []
        remaining_cnt = count
        while remaining_cnt > 0:
            if remaining_cnt - self.query_batch >= 0:
                current_cnt = self.query_batch
            else:
                current_cnt = remaining_cnt
            sample_list = self._select_random_elements(self._sample_lines, current_cnt)
            message = self._form_message_with_data(sample_list, current_cnt)
            response = self.ask_gpt(message)
            generated_batch = self.extract_samples_from_response(response)
            result += generated_batch
            remaining_cnt = remaining_cnt - current_cnt
        self._result_list.append(result)
        final_columns = self.columns + self.off_table_features
        return pd.DataFrame(result, columns=final_columns)

def extract_samples_from_response(self, response_content):
    """
        Extracts samples from the response content.

        Args:
            response_content (dict): The response content as a dictionary.

        Returns:
            list: A list of extracted samples.
        """

    def dict_to_list(input_dict, header):
        """
            Converts a dictionary to a list based on the given header.

            Args:
                input_dict (dict): The input dictionary.
                header (list): The list of keys to extract from the dictionary.

            Returns:
                list: A list of values extracted from the dictionary based on the header.
            """
        res = []
        for each_col in header:
            each_value = input_dict.get(each_col, None)
            res.append(each_value)
        return res
    logger.info('Extracting samples from response ...')
    header = self.columns + self.off_table_features
    features = []
    for line in response_content.split('\n'):
        feature = {}
        for field in header:
            pattern = '\\b' + field + '\\s*(?:is|=)\\s*([^,\\n]+)'
            match = re.search(pattern, line)
            if match:
                feature[field] = match.group(1).strip()
        if feature:
            features.append(dict_to_list(feature, header))
    logger.info(f'Extracting samples from response ... Finished, {len(features)} extracted.')
    return features

class NDArrayLoader:
    """
    Cache ndarray in disk, allow slice and random access.

    Support for storing two-dimensional data by columns.
    """

    def __init__(self, cache_root: str | Path=DEFAULT_CACHE_ROOT, save_to_file=True) -> None:
        self.store_index = 0
        self.cache_root = Path(cache_root).expanduser().resolve()
        self.save_to_file = save_to_file
        if save_to_file:
            self.cache_root.mkdir(exist_ok=True, parents=True)
        else:
            self.ndarray_list = []

    @staticmethod
    def get_auto_save(raw_data) -> NDArrayLoader:
        save_to_file = True
        if isinstance(raw_data, pd.DataFrame) or (isinstance(raw_data, DataLoader) and isinstance(raw_data.data_connector, DataFrameConnector)):
            save_to_file = False
        return NDArrayLoader(save_to_file=save_to_file)

    @cached_property
    def subdir(self) -> str:
        """
        Prevent collision of cache files.
        """
        return uuid4().hex

    @cached_property
    def cache_dir(self) -> Path:
        """Cache directory for storing ndarray."""
        return self.cache_root / self.subdir

    def _get_cache_filename(self, index: int) -> Path:
        return self.cache_dir / f'{index}.npy'

    def store(self, ndarray: ndarray):
        """
        Spliting and storing columns of ndarry to disk, one by one.
        """
        if self.save_to_file:
            self.cache_dir.mkdir(exist_ok=True, parents=True)
            for ndarray in np.split(ndarray, indices_or_sections=ndarray.shape[1], axis=1):
                np.save(self._get_cache_filename(self.store_index), ndarray)
                self.store_index += 1
        else:
            for ndarray in np.split(ndarray, indices_or_sections=ndarray.shape[1], axis=1):
                self.ndarray_list.append(ndarray)
                self.store_index += 1

    def load(self, index: int) -> ndarray:
        """
        Load ndarray from disk by index of column.
        """
        if self.save_to_file:
            return np.load(self._get_cache_filename(int(index)))
        else:
            return self.ndarray_list[index]

    def cleanup(self):
        if self.save_to_file:
            try:
                shutil.rmtree(self.cache_dir, ignore_errors=True)
            except AttributeError:
                pass
        self.store_index = 0

    def iter(self) -> Generator[ndarray, None, None]:
        for i in range(self.store_index):
            yield self.load(i)

    def get_all(self) -> ndarray:
        return np.concatenate([array for array in self.iter()], axis=1)

    @cached_property
    def __shape_0(self):
        return self.load(0).shape[0]

    @property
    def shape(self) -> tuple[int, int]:
        return (self.__shape_0, self.store_index)

    def __len__(self):
        return self.shape[0]

    def __getitem__(self, key: int | slice | tuple[int | slice, int | slice]):
        if not isinstance(key, tuple):
            return np.concatenate([self.load(i)[key] for i in range(self.store_index)], axis=1)
        else:
            x_slice, y_slice = key
            if not isinstance(y_slice, slice):
                return self.load(y_slice)[x_slice].squeeze(axis=1)
            if not isinstance(x_slice, slice):
                return np.concatenate([self.load(i)[x_slice] for i in range(y_slice.start or 0, min(y_slice.stop or self.store_index, self.store_index), y_slice.step or 1)])
            else:
                return np.concatenate([self.load(i)[x_slice] for i in range(y_slice.start or 0, min(y_slice.stop or self.store_index, self.store_index), y_slice.step or 1)], axis=1)

    def __del__(self):
        self.cleanup()

def __init__(self, cache_root: str | Path=DEFAULT_CACHE_ROOT, save_to_file=True) -> None:
    self.store_index = 0
    self.cache_root = Path(cache_root).expanduser().resolve()
    self.save_to_file = save_to_file
    if save_to_file:
        self.cache_root.mkdir(exist_ok=True, parents=True)
    else:
        self.ndarray_list = []

def store(self, ndarray: ndarray):
    """
        Spliting and storing columns of ndarry to disk, one by one.
        """
    if self.save_to_file:
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        for ndarray in np.split(ndarray, indices_or_sections=ndarray.shape[1], axis=1):
            np.save(self._get_cache_filename(self.store_index), ndarray)
            self.store_index += 1
    else:
        for ndarray in np.split(ndarray, indices_or_sections=ndarray.shape[1], axis=1):
            self.ndarray_list.append(ndarray)
            self.store_index += 1

def load(self, index: int) -> ndarray:
    """
        Load ndarray from disk by index of column.
        """
    if self.save_to_file:
        return np.load(self._get_cache_filename(int(index)))
    else:
        return self.ndarray_list[index]

def cleanup(self):
    if self.save_to_file:
        try:
            shutil.rmtree(self.cache_dir, ignore_errors=True)
        except AttributeError:
            pass
    self.store_index = 0

def iter(self) -> Generator[ndarray, None, None]:
    for i in range(self.store_index):
        yield self.load(i)

@cached_property
def __shape_0(self):
    return self.load(0).shape[0]

class HyperTransformer:
    """HyperTransformer class.

    The ``HyperTransformer`` class contains a collection of ``transformers`` that can be
    used to transform and reverse transform one or more columns at once.

    Example:
        Create a simple ``HyperTransformer`` instance that will decide which transformers
        to use based on the fit data ``dtypes``.

        >>> ht = HyperTransformer()

        Create a ``HyperTransformer`` passing a dict mapping fields to sdtypes.

        >>> field_sdtypes = {
        ...     'a': 'categorical',
        ...     'b': 'numerical'
        ... }
        >>> ht = HyperTransformer(field_sdtypes=field_sdtypes)

        Create a ``HyperTransformer`` passing a ``field_transformers`` dict.
        (Note: The transformers used in this example may not exist and are just used
        to illustrate the different way that a transformer can be defined for a field).

        >>> field_transformers = {
        ...     'email': EmailTransformer(),
        ...     'email.domain': EmailDomainTransformer(),
        ... }
        >>> ht = HyperTransformer(field_transformers=field_transformers)

        Create a ``HyperTransformer`` passing a dict mapping sdtypes to transformers.
        >>> default_sdtype_transformers = {
        ...     'categorical': LabelEncoder(),
        ...     'numerical': FloatFormatter()
        ... }
        >>> ht = HyperTransformer(default_sdtype_transformers=default_sdtype_transformers)
    """
    _DTYPES_TO_SDTYPES = {'i': 'numerical', 'f': 'numerical', 'O': 'categorical', 'b': 'boolean', 'M': 'datetime'}
    _DEFAULT_OUTPUT_SDTYPES = ['numerical', 'float', 'integer']
    _REFIT_MESSAGE = "For this change to take effect, please refit your data using 'fit' or 'fit_transform'."
    _DETECT_CONFIG_MESSAGE = 'Nothing to update. Use the `detect_initial_config` method to pre-populate all the sdtypes and transformers from your dataset.'
    _NOT_FIT_MESSAGE = "The HyperTransformer is not ready to use. Please fit your data first using 'fit' or 'fit_transform'."

    @staticmethod
    def _user_message(text, prefix=None):
        """Print a text with an optional prefix to the user.

        Args:
            text (str):
                Text to print.
            prefix (str or None):
                A prefix to add to the front of the text before printing.
        """
        message = f'{prefix}: {text}' if prefix else text
        print(message)

    @staticmethod
    def _add_field_to_set(field, field_set):
        if isinstance(field, tuple):
            field_set.update(field)
        else:
            field_set.add(field)

    @staticmethod
    def _field_in_set(field, field_set):
        if isinstance(field, tuple):
            return all((column in field_set for column in field))
        return field in field_set

    @staticmethod
    def _subset(input_list, other_list, not_in=False):
        return [element for element in input_list if (element in other_list) ^ not_in]

    def _create_multi_column_fields(self):
        multi_column_fields = {}
        for field in list(self.field_sdtypes) + list(self.field_transformers):
            if isinstance(field, tuple):
                for column in field:
                    multi_column_fields[column] = field
        return multi_column_fields

    def _validate_field_transformers(self):
        for field in self.field_transformers:
            if self._field_in_set(field, self._specified_fields):
                raise ValueError(f'Multiple transformers specified for the field {field}. Each field can have at most one transformer defined in field_transformers.')
            self._add_field_to_set(field, self._specified_fields)

    def __init__(self):
        self._default_sdtype_transformers = {}
        self.field_sdtypes = {}
        self.field_transformers = {}
        self._specified_fields = set()
        self._validate_field_transformers()
        self._valid_output_sdtypes = self._DEFAULT_OUTPUT_SDTYPES
        self._multi_column_fields = self._create_multi_column_fields()
        self._transformers_sequence = []
        self._output_columns = []
        self._input_columns = []
        self._fitted_fields = set()
        self._fitted = False
        self._modified_config = False
        self._transformers_tree = defaultdict(dict)

    @staticmethod
    def _field_in_data(field, data):
        all_columns_in_data = isinstance(field, tuple) and all((col in data for col in field))
        return field in data or all_columns_in_data

    @staticmethod
    def _get_supported_sdtypes():
        get_transformers_by_type.cache_clear()
        return get_transformers_by_type().keys()

    def get_config(self):
        """Get the current ``HyperTransformer`` configuration.

        Returns:
            dict:
                A dictionary containing the following two dictionaries:
                - sdtypes: A dictionary mapping column names to their ``sdtypes``.
                - transformers: A dictionary mapping column names to their transformer instances.
        """
        return Config({'sdtypes': self.field_sdtypes, 'transformers': self.field_transformers})

    @staticmethod
    def _validate_transformers(column_name_to_transformer):
        """Validate the given transformers are valid.

        Args:
            column_name_to_transformer (dict):
                Dict mapping column names to transformers to be used for that column.

        Raises:
            Error:
                Raises an error if ``column_name_to_transformer`` contains one or more
                invalid transformers.
        """
        invalid_transformers_columns = []
        for column_name, transformer in column_name_to_transformer.items():
            if transformer is not None:
                try:
                    get_transformer_instance(transformer)
                except (ValueError, AttributeError):
                    invalid_transformers_columns.append(column_name)
        if invalid_transformers_columns:
            raise Error(f'Invalid transformers for columns: {invalid_transformers_columns}. Please assign an rdt transformer object to each column name.')

    @staticmethod
    def _validate_sdtypes(sdtypes):
        """Validate the given sdtypes are valid.

        Args:
            sdtypes (dict):
                Dict mapping column names to sdtypes to be used for that column.

        Raises:
            Error:
                Raises an error if ``sdtypes`` contains one or more invalid sdtype.
        """
        supported_sdtypes = HyperTransformer._get_supported_sdtypes()
        unsupported_sdtypes = []
        for sdtype in sdtypes.values():
            if sdtype not in supported_sdtypes:
                unsupported_sdtypes.append(sdtype)
        if unsupported_sdtypes:
            raise Error(f'Invalid sdtypes: {unsupported_sdtypes}. If you are trying to use a premium sdtype, contact info@sdv.dev about RDT Add-Ons.')

    @staticmethod
    def _validate_config(config):
        if set(config.keys()) != {'sdtypes', 'transformers'}:
            raise Error("Error: Invalid config. Please provide 2 dictionaries named 'sdtypes' and 'transformers'.")
        sdtypes = config['sdtypes']
        transformers = config['transformers']
        if set(sdtypes.keys()) != set(transformers.keys()):
            raise Error("The column names in the 'sdtypes' dictionary must match the column names in the 'transformers' dictionary.")
        HyperTransformer._validate_sdtypes(sdtypes)
        HyperTransformer._validate_transformers(transformers)
        mismatched_columns = []
        for column_name, transformer in transformers.items():
            if transformer is not None:
                input_sdtype = transformer.get_input_sdtype()
                sdtype = sdtypes.get(column_name)
                if input_sdtype != sdtype:
                    mismatched_columns.append(column_name)
        if mismatched_columns:
            raise Error(f"Some transformers you've assigned are not compatible with the sdtypes. Please change the following columns: {mismatched_columns}")

    def _validate_update_columns(self, update_columns):
        unknown_columns = self._subset(update_columns, self.field_sdtypes.keys(), not_in=True)
        if unknown_columns:
            raise Error(f"Invalid column names: {unknown_columns}. These columns do not exist in the config. Use 'set_config()' to write and set your entire config at once.")

    def set_config(self, config):
        """Set the ``HyperTransformer`` configuration.

        This method will only update the sdtypes/transformers passed. Other previously
        learned sdtypes/transformers will not be affected.

        Args:
            config (dict):
                A dictionary containing the following two dictionaries:
                - sdtypes: A dictionary mapping column names to their ``sdtypes``.
                - transformers: A dictionary mapping column names to their transformer instances.
        """
        self._validate_config(config)
        self.field_sdtypes.update(config['sdtypes'])
        self.field_transformers.update(config['transformers'])
        self._modified_config = True
        if self._fitted:
            warnings.warn(self._REFIT_MESSAGE)

    def update_transformers_by_sdtype(self, sdtype, transformer):
        """Update the transformers for the specified ``sdtype``.

        Given an ``sdtype`` and a ``transformer``, change all the fields of the ``sdtype``
        to use the given transformer.

        Args:
            sdtype (str):
                Semantic data type for the transformer.
            transformer (rdt.transformers.BaseTransformer):
                Transformer class or instance to be used for the given ``sdtype``.
        """
        if self._fitted:
            warnings.warn(self._REFIT_MESSAGE)
        if not self.field_sdtypes:
            raise Error('Nothing to update. Use the `detect_initial_config` method to pre-populate all the sdtypes and transformers from your dataset.')
        if sdtype not in self._get_supported_sdtypes():
            raise Error('Invalid sdtype. If you are trying to use a premium sdtype, contact info@sdv.dev about RDT Add-Ons.')
        if not isinstance(transformer, BaseTransformer) and transformer is not None:
            raise Error('Invalid transformer. Please input an rdt transformer object.')
        if transformer is not None and sdtype not in transformer.get_supported_sdtypes():
            raise Error("The transformer you've assigned is incompatible with the sdtype.")
        for field, field_sdtype in self.field_sdtypes.items():
            if field_sdtype == sdtype:
                self.field_transformers[field] = transformer
        self._modified_config = True

    def update_sdtypes(self, column_name_to_sdtype):
        """Update the ``sdtypes`` for each specified column name.

        Args:
            column_name_to_sdtype(dict):
                Dict mapping column names to ``sdtypes`` for that column.
        """
        if len(self.field_sdtypes) == 0:
            raise Error(self._DETECT_CONFIG_MESSAGE)
        update_columns = column_name_to_sdtype.keys()
        self._validate_update_columns(update_columns)
        self._validate_sdtypes(column_name_to_sdtype)
        transformers_to_update = {}
        for column, sdtype in column_name_to_sdtype.items():
            if self.field_sdtypes.get(column) != sdtype:
                current_transformer = self.field_transformers.get(column)
                if not current_transformer or current_transformer.get_input_sdtype() != sdtype:
                    transformers_to_update[column] = get_default_transformer(sdtype)
        self.field_sdtypes.update(column_name_to_sdtype)
        self.field_transformers.update(transformers_to_update)
        self._user_message("The transformers for these columns may change based on the new sdtype.\nUse 'get_config()' to verify the transformers.", 'Info')
        self._modified_config = True
        if self._fitted:
            warnings.warn(self._REFIT_MESSAGE)

    def update_transformers(self, column_name_to_transformer):
        """Update any of the transformers assigned to each of the column names.

        Args:
            column_name_to_transformer(dict):
                Dict mapping column names to transformers to be used for that column.
        """
        if self._fitted:
            warnings.warn(self._REFIT_MESSAGE)
        if len(self.field_transformers) == 0:
            raise Error(self._DETECT_CONFIG_MESSAGE)
        update_columns = column_name_to_transformer.keys()
        self._validate_update_columns(update_columns)
        self._validate_transformers(column_name_to_transformer)
        incompatible_sdtypes = []
        for column_name, transformer in column_name_to_transformer.items():
            if transformer is not None:
                current_sdtype = self.field_sdtypes.get(column_name)
                if current_sdtype and current_sdtype not in transformer.get_supported_sdtypes():
                    incompatible_sdtypes.append(column_name)
            self.field_transformers[column_name] = transformer
        if incompatible_sdtypes:
            warnings.warn(f"Some transformers you've assigned are not compatible with the sdtypes. Use 'update_sdtypes' to update: {incompatible_sdtypes}")
        self._modified_config = True

    def remove_transformers(self, column_names):
        """Remove transformers for given columns.

        This will remove the transformer for a given column name and this will not be
        transformed.

        Args:
            column_names (list):
                List of columns to remove the transformers for.
        """
        unknown_columns = []
        for column_name in column_names:
            if column_name not in self.field_transformers:
                unknown_columns.append(column_name)
        if unknown_columns:
            raise Error(f"Invalid column names: {unknown_columns}. These columns do not exist in the config. Use 'get_config()' to see the expected values.")
        for column_name in column_names:
            self.field_transformers[column_name] = None
        if self._fitted:
            warnings.warn(self._REFIT_MESSAGE)

    def remove_transformers_by_sdtype(self, sdtype):
        """Remove transformers for given ``sdtype``.

        This will remove the transformers for a given ``sdtype``  and those will not be
        transformed.

        Args:
            sdtype (str):
                Semantic data type for the transformers to be removed.
        """
        if sdtype not in self._get_supported_sdtypes():
            raise Error(f"Invalid sdtype '{sdtype}'. If you are trying to use a premium sdtype, contact info@sdv.dev about RDT Add-Ons.")
        for column_name, column_sdtype in self.field_sdtypes.items():
            if column_sdtype == sdtype:
                self.field_transformers[column_name] = None
        if self._fitted:
            warnings.warn(self._REFIT_MESSAGE)

    def _get_transformer(self, field):
        """Get the transformer instance used for a field.

        Args:
            field (str or tuple):
                String representing a column name or a tuple of multiple column names.

        Returns:
            Transformer:
                Transformer instance used on the specified field during ``transform``.
        """
        if not self._fitted:
            raise NotFittedError
        return self._transformers_tree[field].get('transformer', None)

    def _get_output_transformers(self, field):
        """Return dict mapping output columns of field to transformers used on them.

        Args:
            field (str or tuple):
                String representing a column name or a tuple of multiple column names.

        Returns:
            dict:
                Dictionary mapping the output names of the columns created after transforming the
                specified field, to the transformer instances used on them.
        """
        if not self._fitted:
            raise NotFittedError
        next_transformers = {}
        for output in self._transformers_tree[field].get('outputs', []):
            next_transformers[output] = self._transformers_tree[output].get('transformer', None)
        return next_transformers

    def _get_final_output_columns(self, field):
        """Return list of all final output columns related to a field.

        The ``HyperTransformer`` will figure out which transformers to use on a field during
        ``transform``. If the outputs are not of an acceptable sdtype, they will also go
        through transformations. This method finds all the output columns that are of an
        acceptable final sdtype that originated from the specified field.

        Args:
            field (str or tuple):
                String representing a column name or a tuple of multiple column names.

        Returns:
            list:
                List of output column names that were created as a by-product of the specified
                field.
        """
        if not self._fitted:
            raise NotFittedError
        final_outputs = []
        outputs = self._transformers_tree[field].get('outputs', []).copy()
        while len(outputs) > 0:
            output = outputs.pop()
            transformer = self._transformers_tree.get(output, {}).get('transformer')
            if output in self._transformers_tree and transformer:
                outputs.extend(self._transformers_tree[output].get('outputs', []))
            else:
                final_outputs.append(output)
        return sorted(final_outputs, reverse=True)

    def _get_transformer_tree_yaml(self):
        """Return yaml representation of transformers tree.

        After running ``fit``, a sequence of transformers is created to run each original column
        through. The sequence can be thought of as a tree, where each node is a field and the
        transformer used on it, and each neighbor is an output from that transformer. This method
        returns a YAML representation of this tree.

        Returns:
            string:
                YAML object representing the tree of transformers created during ``fit``. It has
                the following form:

                field1:
                    transformer: ExampleTransformer instance
                    outputs: [field1.out1, field1.out2]
                field1.out1:
                    transformer: FrequencyEncoder instance
                    outputs: [field1.out1.value]
                field1.out2:
                    transformer: FrequencyEncoder instance
                    outputs: [field1.out2.value]
        """
        modified_tree = deepcopy(self._transformers_tree)
        for field in modified_tree:
            class_name = modified_tree[field]['transformer'].__class__.__name__
            modified_tree[field]['transformer'] = class_name
        return yaml.safe_dump(dict(modified_tree))

    def _set_field_sdtype(self, data, field):
        clean_data = data[field].dropna()
        kind = clean_data.infer_objects().dtype.kind
        self.field_sdtypes[field] = self._DTYPES_TO_SDTYPES[kind]

    def _unfit(self):
        self._transformers_sequence = []
        self._input_columns = []
        self._output_columns = []
        self._fitted_fields.clear()
        self._fitted = False
        self._transformers_tree = defaultdict(dict)

    def _learn_config(self, data):
        """Unfit the HyperTransformer and learn the sdtypes and transformers of the data."""
        self._unfit()
        for field in data:
            if field not in self.field_sdtypes:
                self._set_field_sdtype(data, field)
            if field not in self.field_transformers:
                sdtype = self.field_sdtypes[field]
                if sdtype in self._default_sdtype_transformers:
                    self.field_transformers[field] = self._default_sdtype_transformers[sdtype]
                else:
                    self.field_transformers[field] = get_default_transformer(sdtype)

    def detect_initial_config(self, data):
        """Print the configuration of the data.

        This method detects the ``sdtype`` and transformer of each field in the data
        and then prints them as a json object.

        NOTE: This method completely resets the state of the ``HyperTransformer``.

        Args:
            data (pd.DataFrame):
                Data which will have its configuration detected.
        """
        self._default_sdtype_transformers = {}
        self.field_sdtypes = {}
        self.field_transformers = {}
        self._learn_config(data)
        self._user_message('Detecting a new config from the data ... SUCCESS')
        self._user_message('Setting the new config ... SUCCESS')
        config = Config({'sdtypes': self.field_sdtypes, 'transformers': self.field_transformers})
        self._user_message('Config:')
        self._user_message(config)

    def _get_next_transformer(self, output_field, output_sdtype, next_transformers):
        next_transformer = None
        if output_field in self.field_transformers:
            next_transformer = self.field_transformers[output_field]
        elif output_sdtype not in self._valid_output_sdtypes:
            if next_transformers is not None and output_field in next_transformers:
                next_transformer = next_transformers[output_field]
            else:
                next_transformer = get_default_transformer(output_sdtype)
        return next_transformer

    def _fit_field_transformer(self, data, field, transformer):
        """Fit a transformer to its corresponding field.

        This method fits a transformer to the specified field which can be a column
        name or tuple of column names. If the transformer outputs fields that aren't
        ML ready, then this method recursively fits transformers to their outputs until
        they are. This method keeps track of which fields are temporarily created by
        transformers as well as which fields will be part of the final output from ``transform``.

        Args:
            data (pandas.DataFrame):
                Data to fit the transformer to.
            field (str or tuple):
                Name of column or tuple of columns in data that will be transformed
                by the transformer.
            transformer (Transformer):
                Instance of transformer class that will fit the data.
        """
        if transformer is None:
            self._add_field_to_set(field, self._fitted_fields)
            self._transformers_tree[field]['transformer'] = None
            self._transformers_tree[field]['outputs'] = [field]
        else:
            transformer = get_transformer_instance(transformer)
            transformer.fit(data, field)
            self._add_field_to_set(field, self._fitted_fields)
            self._transformers_sequence.append(transformer)
            data = transformer.transform(data)
            output_sdtypes = transformer.get_output_sdtypes()
            next_transformers = transformer.get_next_transformers()
            self._transformers_tree[field]['transformer'] = transformer
            self._transformers_tree[field]['outputs'] = list(output_sdtypes)
            for output_name, output_sdtype in output_sdtypes.items():
                output_field = self._multi_column_fields.get(output_name, output_name)
                next_transformer = self._get_next_transformer(output_field, output_sdtype, next_transformers)
                if next_transformer:
                    if self._field_in_data(output_field, data):
                        self._fit_field_transformer(data, output_field, next_transformer)
        return data

    def _validate_all_fields_fitted(self):
        non_fitted_fields = self._specified_fields.difference(self._fitted_fields)
        if non_fitted_fields:
            warnings.warn(f'The following fields were specified in the input arguments but not found in the data: {non_fitted_fields}')

    def _sort_output_columns(self):
        """Sort ``_output_columns`` to follow the same order as the ``_input_columns``."""
        for input_column in self._input_columns:
            output_columns = self._get_final_output_columns(input_column)
            self._output_columns.extend(output_columns)

    def _validate_config_exists(self):
        if len(self.field_sdtypes) == 0 and len(self.field_transformers) == 0:
            raise Error("No config detected. Set the config using 'set_config' or pre-populate it automatically from your data using 'detect_initial_config' prior to fitting your data.")

    def _validate_detect_config_called(self, data):
        """Assert the ``detect_initial_config`` method is correcly called before fitting."""
        self._validate_config_exists()
        fields = list(self.field_sdtypes.keys())
        missing = any((column not in data.columns for column in fields))
        unknown_columns = self._subset(data.columns, fields, not_in=True)
        if unknown_columns or missing:
            unknown_text = f' (unknown columns: {unknown_columns})' if unknown_columns else ''
            raise Error(f"The data you are trying to fit has different columns than the original detected data{unknown_text}. Column names and their sdtypes must be the same. Use the method 'get_config()' to see the expected values.")

    def fit(self, data):
        """Fit the transformers to the data.

        Args:
            data (pandas.DataFrame):
                Data to fit the transformers to.
        """
        self._validate_detect_config_called(data)
        self._unfit()
        self._input_columns = list(data.columns)
        for field in self._input_columns:
            data = self._fit_field_transformer(data, field, self.field_transformers[field])
        self._validate_all_fields_fitted()
        self._fitted = True
        self._modified_config = False
        self._sort_output_columns()

    def _transform(self, data, prevent_subset):
        self._validate_config_exists()
        if not self._fitted or self._modified_config:
            raise NotFittedError(self._NOT_FIT_MESSAGE)
        unknown_columns = self._subset(data.columns, self._input_columns, not_in=True)
        if prevent_subset:
            contained = all((column in self._input_columns for column in data.columns))
            is_subset = contained and len(data.columns) < len(self._input_columns)
            if unknown_columns or is_subset:
                raise Error("The data you are trying to transform has different columns than the original data. Column names and their sdtypes must be the same. Use the method 'get_config()' to see the expected values.")
        elif unknown_columns:
            raise Error(f"Unexpected column names in the data you are trying to transform: {unknown_columns}. Use 'get_config()' to see the acceptable column names.")
        data = data.copy()
        for transformer in self._transformers_sequence:
            data = transformer.transform(data, drop=False)
        transformed_columns = self._subset(self._output_columns, data.columns)
        return data.reindex(columns=transformed_columns)

    def transform_subset(self, data):
        """Transform a subset of the fitted data's columns.

        Args:
            data (pandas.DataFrame):
                Data to transform.

        Returns:
            pandas.DataFrame:
                Transformed subset.
        """
        return self._transform(data, prevent_subset=False)

    def transform(self, data):
        """Transform the data.

        Args:
            data (pandas.DataFrame):
                Data to transform.

        Returns:
            pandas.DataFrame:
                Transformed data.
        """
        return self._transform(data, prevent_subset=True)

    def fit_transform(self, data):
        """Fit the transformers to the data and then transform it.

        Args:
            data (pandas.DataFrame):
                Data to transform.

        Returns:
            pandas.DataFrame:
                Transformed data.
        """
        self.fit(data)
        return self.transform(data)

    def _reverse_transform(self, data, prevent_subset):
        self._validate_config_exists()
        if not self._fitted or self._modified_config:
            raise NotFittedError(self._NOT_FIT_MESSAGE)
        unknown_columns = self._subset(data.columns, self._output_columns, not_in=True)
        if prevent_subset:
            contained = all((column in self._output_columns for column in data.columns))
            is_subset = contained and len(data.columns) < len(self._output_columns)
            if unknown_columns or is_subset:
                raise Error('There are unexpected columns in the data you are trying to transform. You must provide a transformed dataset with all the columns from the original data.')
        elif unknown_columns:
            raise Error(f'There are unexpected column names in the data you are trying to transform. A reverse transform is not defined for {unknown_columns}.')
        for transformer in reversed(self._transformers_sequence):
            data = transformer.reverse_transform(data, drop=False)
        reversed_columns = self._subset(self._input_columns, data.columns)
        return data.reindex(columns=reversed_columns)

    def reverse_transform_subset(self, data):
        """Revert the transformations for a subset of the fitted columns.

        Args:
            data (pandas.DataFrame):
                Data to revert.

        Returns:
            pandas.DataFrame:
                Reversed subset.
        """
        return self._reverse_transform(data, prevent_subset=False)

    def reverse_transform(self, data):
        """Revert the transformations back to the original values.

        Args:
            data (pandas.DataFrame):
                Data to revert.

        Returns:
            pandas.DataFrame:
                reversed data.
        """
        return self._reverse_transform(data, prevent_subset=True)

@staticmethod
def _user_message(text, prefix=None):
    """Print a text with an optional prefix to the user.

        Args:
            text (str):
                Text to print.
            prefix (str or None):
                A prefix to add to the front of the text before printing.
        """
    message = f'{prefix}: {text}' if prefix else text
    print(message)

class Univariate(object):
    """Univariate Distribution.

    Args:
        candidates (list[str or type or Univariate]):
            List of candidates to select the best univariate from.
            It can be a list of strings representing Univariate FQNs,
            or a list of Univariate subclasses or a list of instances.
        parametric (ParametricType):
            If not ``None``, only select subclasses of this type.
            Ignored if ``candidates`` is passed.
        bounded (BoundedType):
            If not ``None``, only select subclasses of this type.
            Ignored if ``candidates`` is passed.
        random_state (int or np.random.RandomState):
            Random seed or RandomState to use.
        selection_sample_size (int):
            Size of the subsample to use for candidate selection.
            If ``None``, all the data is used.
    """
    PARAMETRIC = ParametricType.NON_PARAMETRIC
    BOUNDED = BoundedType.UNBOUNDED
    fitted = False
    _constant_value = None
    _instance = None

    @classmethod
    def _select_candidates(cls, parametric=None, bounded=None):
        """Select which subclasses fulfill the specified constriants.

        Args:
            parametric (ParametricType):
                If not ``None``, only select subclasses of this type.
            bounded (BoundedType):
                If not ``None``, only select subclasses of this type.

        Returns:
            list:
                Selected subclasses.
        """
        candidates = []
        for subclass in cls.__subclasses__():
            candidates.extend(subclass._select_candidates(parametric, bounded))
            if ABC in subclass.__bases__:
                continue
            if parametric is not None and subclass.PARAMETRIC != parametric:
                continue
            if bounded is not None and subclass.BOUNDED != bounded:
                continue
            candidates.append(subclass)
        return candidates

    @store_args
    def __init__(self, candidates=None, parametric=None, bounded=None, random_state=None, selection_sample_size=None):
        self.candidates = candidates or self._select_candidates(parametric, bounded)
        self.random_state = validate_random_state(random_state)
        self.selection_sample_size = selection_sample_size

    @classmethod
    def __repr__(cls):
        """Return class name."""
        return cls.__name__

    def check_fit(self):
        """Check whether this model has already been fit to a random variable.

        Raise a ``NotFittedError`` if it has not.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        if not self.fitted:
            raise NotFittedError('This model is not fitted.')

    def _constant_sample(self, num_samples):
        """Sample values for a constant distribution.

        Args:
            num_samples (int):
                Number of rows to sample

        Returns:
            numpy.ndarray:
                Sampled values. Array of shape (num_samples,).
        """
        return np.full(num_samples, self._constant_value)

    def _constant_cumulative_distribution(self, X):
        """Cumulative distribution for the degenerate case of constant distribution.

        Note that the output of this method will be an array whose unique values are 0 and 1.
        More information can be found here: https://en.wikipedia.org/wiki/Degenerate_distribution

        Arguments:
            X (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.
        """
        result = np.ones(X.shape)
        result[np.nonzero(X < self._constant_value)] = 0
        return result

    def _constant_probability_density(self, X):
        """Probability density for the degenerate case of constant distribution.

        Note that the output of this method will be an array whose unique values are 0 and 1.
        More information can be found here: https://en.wikipedia.org/wiki/Degenerate_distribution

        Arguments:
            X (numpy.ndarray):
                Values for which the probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Probability density values for points in X.
        """
        result = np.zeros(X.shape)
        result[np.nonzero(X == self._constant_value)] = 1
        return result

    def _constant_percent_point(self, X):
        """Percent point for the degenerate case of constant distribution.

        Note that the output of this method will be an array whose unique values are `np.nan`
        and self._constant_value.
        More information can be found here: https://en.wikipedia.org/wiki/Degenerate_distribution

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.
        """
        return np.full(X.shape, self._constant_value)

    def _replace_constant_methods(self):
        """Replace conventional distribution methods by its constant counterparts."""
        self.cumulative_distribution = self._constant_cumulative_distribution
        self.percent_point = self._constant_percent_point
        self.probability_density = self._constant_probability_density
        self.sample = self._constant_sample

    def _set_constant_value(self, constant_value):
        """Set the distribution up to behave as a degenerate distribution.

        The constant value is stored as ``self._constant_value`` and all
        the methods are replaced by their degenerate counterparts.

        Args:
            constant_value (float):
                Value to set as the constant one.
        """
        self._constant_value = constant_value
        self._replace_constant_methods()

    def _check_constant_value(self, X):
        """Check if a Series or array contains only one unique value.

        If it contains only one value, set the instance up to behave accordingly.

        Args:
            X (numpy.ndarray):
                Data to analyze.

        Returns:
            float:
                Whether the input data had only one value or not.
        """
        uniques = np.unique(X)
        if len(uniques) == 1:
            self._set_constant_value(uniques[0])
            return True
        return False

    def fit(self, X):
        """Fit the model to a random variable.

        Arguments:
            X (numpy.ndarray):
                Values of the random variable. It must have shape (n, 1).
        """
        if self.selection_sample_size and self.selection_sample_size < len(X):
            selection_sample = np.random.choice(X, size=self.selection_sample_size)
        else:
            selection_sample = X
        self._instance = select_univariate(selection_sample, self.candidates)
        self._instance.fit(X)
        self.fitted = True

    def probability_density(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.probability_density(X)

    def log_probability_density(self, X):
        """Compute the log of the probability density for each point in X.

        It should be overridden with numerically stable variants whenever possible.

        Arguments:
            X (numpy.ndarray):
                Values for which the log probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Log probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        if self._instance:
            return self._instance.log_probability_density(X)
        return np.log(self.probability_density(X))

    def pdf(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Probability density values for points in X.
        """
        return self.probability_density(X)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.cumulative_distribution(X)

    def cdf(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.
        """
        return self.cumulative_distribution(X)

    def percent_point(self, U):
        """Compute the inverse cumulative distribution value for each point in U.

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.percent_point(U)

    def ppf(self, U):
        """Compute the inverse cumulative distribution value for each point in U.

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.
        """
        return self.percent_point(U)

    def set_random_state(self, random_state):
        """Set the random state.

        Args:
            random_state (int, np.random.RandomState, or None):
                Seed or RandomState for the random generator.
        """
        self.random_state = validate_random_state(random_state)

    def sample(self, n_samples=1):
        """Sample values from this model.

        Argument:
            n_samples (int):
                Number of values to sample

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, 1) with values randomly
                sampled from this model distribution.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.sample(n_samples)

    def _get_params(self):
        """Return attributes from self.model to serialize.

        Returns:
            dict:
                Parameters of the underlying distribution.
        """
        return self._instance._get_params()

    def _set_params(self, params):
        """Set the parameters of this univariate.

        Must be implemented in all the subclasses.

        Args:
            dict:
                Parameters to recreate this instance.
        """
        raise NotImplementedError()

    def to_dict(self):
        """Return the parameters of this model in a dict.

        Returns:
            dict:
                Dictionary containing the distribution type and all
                the parameters that define the distribution.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        params = self._get_params()
        if self.__class__ is Univariate:
            params['type'] = get_qualified_name(self._instance)
        else:
            params['type'] = get_qualified_name(self)
        return params

    @classmethod
    def from_dict(cls, params):
        """Build a distribution from its params dict.

        Args:
            params (dict):
                Dictionary containing the FQN of the distribution and the
                necessary parameters to rebuild it.
                The input format is exactly the same that is outputted by
                the distribution class ``to_dict`` method.

        Returns:
            Univariate:
                Distribution instance.
        """
        params = params.copy()
        distribution = get_instance(params.pop('type'))
        distribution._set_params(params)
        distribution.fitted = True
        return distribution

    def save(self, path):
        """Serialize this univariate instance using pickle.

        Args:
            path (str):
                Path to where this distribution will be serialized.
        """
        with open(path, 'wb') as pickle_file:
            pickle.dump(self, pickle_file)

    @classmethod
    def load(cls, path):
        """Load a Univariate instance from a pickle file.

        Args:
            path (str):
                Path to the pickle file where the distribution has been serialized.

        Returns:
            Univariate:
                Loaded instance.
        """
        with open(path, 'rb') as pickle_file:
            return pickle.load(pickle_file)

def save(self, path):
    """Serialize this univariate instance using pickle.

        Args:
            path (str):
                Path to where this distribution will be serialized.
        """
    with open(path, 'wb') as pickle_file:
        pickle.dump(self, pickle_file)

@classmethod
def load(cls, path):
    """Load a Univariate instance from a pickle file.

        Args:
            path (str):
                Path to the pickle file where the distribution has been serialized.

        Returns:
            Univariate:
                Loaded instance.
        """
    with open(path, 'rb') as pickle_file:
        return pickle.load(pickle_file)

class Multivariate(object):
    """Abstract class for a multi-variate copula object."""
    fitted = False

    def __init__(self, random_state=None):
        self.random_state = validate_random_state(random_state)

    def fit(self, X):
        """Fit the model to table with values from multiple random variables.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
        raise NotImplementedError

    def probability_density(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the probability density will be computed.

        Returns:
            numpy.ndarray:
                Probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        raise NotImplementedError

    def log_probability_density(self, X):
        """Compute the log of the probability density for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the log probability density will be computed.

        Returns:
            numpy.ndarray:
                Log probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        return np.log(self.probability_density(X))

    def pdf(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the probability density will be computed.

        Returns:
            numpy.ndarray:
                Probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        return self.probability_density(X)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the cumulative distribution will be computed.

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        raise NotImplementedError

    def cdf(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the cumulative distribution will be computed.

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        return self.cumulative_distribution(X)

    def set_random_state(self, random_state):
        """Set the random state.

        Args:
            random_state (int, np.random.RandomState, or None):
                Seed or RandomState for the random generator.
        """
        self.random_state = validate_random_state(random_state)

    def sample(self, num_rows=1):
        """Sample values from this model.

        Argument:
            num_rows (int):
                Number of rows to sample.

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, *) with values randomly
                sampled from this model distribution.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        raise NotImplementedError

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
        raise NotImplementedError

    @classmethod
    def from_dict(cls, params):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the distribution, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Multivariate:
                Instance of the distribution defined on the parameters.
        """
        multivariate_class = get_instance(params['type'])
        return multivariate_class.from_dict(params)

    @classmethod
    def load(cls, path):
        """Load a Multivariate instance from a pickle file.

        Args:
            path (str):
                Path to the pickle file where the distribution has been serialized.

        Returns:
            Multivariate:
                Loaded instance.
        """
        with open(path, 'rb') as pickle_file:
            return pickle.load(pickle_file)

    def save(self, path):
        """Serialize this multivariate instance using pickle.

        Args:
            path (str):
                Path to where this distribution will be serialized.
        """
        with open(path, 'wb') as pickle_file:
            pickle.dump(self, pickle_file)

    def check_fit(self):
        """Check whether this model has already been fit to a random variable.

        Raise a ``NotFittedError`` if it has not.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        if not self.fitted:
            raise NotFittedError('This model is not fitted.')

@classmethod
def load(cls, path):
    """Load a Multivariate instance from a pickle file.

        Args:
            path (str):
                Path to the pickle file where the distribution has been serialized.

        Returns:
            Multivariate:
                Loaded instance.
        """
    with open(path, 'rb') as pickle_file:
        return pickle.load(pickle_file)

def save(self, path):
    """Serialize this multivariate instance using pickle.

        Args:
            path (str):
                Path to where this distribution will be serialized.
        """
    with open(path, 'wb') as pickle_file:
        pickle.dump(self, pickle_file)

class Bivariate(object):
    """Base class for bivariate copulas.

    This class allows to instantiate all its subclasses and serves as a unique entry point for
    the bivariate copulas classes.

    >>> Bivariate(copula_type=CopulaTypes.FRANK).__class__
    copulas.bivariate.frank.Frank

    >>> Bivariate(copula_type='frank').__class__
    copulas.bivariate.frank.Frank


    Args:
        copula_type (Union[CopulaType, str]): Subtype of the copula.
        random_state (Union[int, np.random.RandomState, None]): Seed or RandomState
            for the random generator.

    Attributes:
        copula_type(CopulaTypes): Family of the copula a subclass belongs to.
        _subclasses(list[type]): List of declared subclasses.
        theta_interval(list[float]): Interval of valid thetas for the given copula family.
        invalid_thetas(list[float]): Values that, even though they belong to
            :attr:`theta_interval`, shouldn't be considered valid.
        tau (float): Kendall's tau for the data given at :meth:`fit`.
        theta(float): Parameter for the copula.

    """
    copula_type = None
    _subclasses = []
    theta_interval = []
    invalid_thetas = []
    theta = None
    tau = None

    @classmethod
    def _get_subclasses(cls):
        """Find recursively subclasses for the current class object.

        Returns:
            list[Bivariate]: List of subclass objects.

        """
        subclasses = []
        for subclass in cls.__subclasses__():
            subclasses.append(subclass)
            subclasses.extend(subclass._get_subclasses())
        return subclasses

    @classmethod
    def subclasses(cls):
        """Return a list of subclasses for the current class object.

        Returns:
            list[Bivariate]: Subclasses for given class.

        """
        if not cls._subclasses:
            cls._subclasses = cls._get_subclasses()
        return cls._subclasses

    def __new__(cls, *args, **kwargs):
        """Create and return a new object.

        Returns:
            Bivariate: New object.
        """
        copula_type = kwargs.get('copula_type', None)
        if copula_type is None:
            return super(Bivariate, cls).__new__(cls)
        if not isinstance(copula_type, CopulaTypes):
            if isinstance(copula_type, str) and copula_type.upper() in CopulaTypes.__members__:
                copula_type = CopulaTypes[copula_type.upper()]
            else:
                raise ValueError(f'Invalid copula type {copula_type}')
        for subclass in cls.subclasses():
            if subclass.copula_type is copula_type:
                return super(Bivariate, cls).__new__(subclass)

    def __init__(self, copula_type=None, random_state=None):
        """Initialize Bivariate object.

        Args:
            copula_type (CopulaType or str): Subtype of the copula.
            random_state (int, np.random.RandomState, or None): Seed or RandomState
                for the random generator.
        """
        self.random_state = validate_random_state(random_state)

    def check_theta(self):
        """Validate the computed theta against the copula specification.

        This method is used to assert the computed theta is in the valid range for the copula.

        Raises:
            ValueError: If theta is not in :attr:`theta_interval` or is in :attr:`invalid_thetas`,

        """
        lower, upper = self.theta_interval
        if not lower <= self.theta <= upper or self.theta in self.invalid_thetas:
            message = 'The computed theta value {} is out of limits for the given {} copula.'
            raise ValueError(message.format(self.theta, self.copula_type.name))

    def check_fit(self):
        """Assert that the model is fit and the computed `theta` is valid.

        Raises:
            NotFittedError: if the model is  not fitted.
            ValueError: if the computed theta is invalid.

        """
        if not self.theta:
            raise NotFittedError('This model is not fitted.')
        self.check_theta()

    def check_marginal(self, u):
        """Check that the marginals are uniformly distributed.

        Args:
            u(np.ndarray): Array of datapoints with shape (n,).

        Raises:
            ValueError: If the data does not appear uniformly distributed.
        """
        if min(u) < 0.0 or max(u) > 1.0:
            raise ValueError('Marginal value out of bounds.')
        emperical_cdf = np.sort(u)
        uniform_cdf = np.linspace(0.0, 1.0, num=len(u))
        ks_statistic = max(np.abs(emperical_cdf - uniform_cdf))
        if ks_statistic > 1.627 / np.sqrt(len(u)):
            warnings.warn('Data does not appear to be uniform.', category=RuntimeWarning)

    def _compute_theta(self):
        """Compute theta, validate it and assign it to self."""
        self.theta = self.compute_theta()
        self.check_theta()

    def fit(self, X):
        """Fit a model to the data updating the parameters.

        Args:
            X(np.ndarray): Array of datapoints with shape (n,2).

        Return:
            None
        """
        U, V = split_matrix(X)
        self.check_marginal(U)
        self.check_marginal(V)
        self.tau = stats.kendalltau(U, V)[0]
        if np.isnan(self.tau):
            if len(np.unique(U)) == 1 or len(np.unique(V)) == 1:
                raise ValueError('Constant column.')
            raise ValueError('Unable to compute tau.')
        self._compute_theta()

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict: Parameters of the copula.

        """
        return {'copula_type': self.copula_type.name, 'theta': self.theta, 'tau': self.tau}

    @classmethod
    def from_dict(cls, copula_dict):
        """Create a new instance from the given parameters.

        Args:
            copula_dict: `dict` with the parameters to replicate the copula.
              Like the output of `Bivariate.to_dict`

        Returns:
            Bivariate: Instance of the copula defined on the parameters.

        """
        instance = cls(copula_type=copula_dict['copula_type'])
        instance.theta = copula_dict['theta']
        instance.tau = copula_dict['tau']
        return instance

    def infer(self, X):
        """Take in subset of values and predicts the rest."""
        raise NotImplementedError

    def generator(self, t):
        """Compute the generator function for Archimedian copulas.

        The generator is a function
        :math:`\\psi: [0,1]\\times\\Theta \\rightarrow [0, \\infty)`  # noqa: JS101

        that given an Archimedian copula fulfills:
        .. math:: C(u,v) = \\psi^{-1}(\\psi(u) + \\psi(v))


        In a more generic way:

        .. math:: C(u_1, u_2, ..., u_n;\\theta) = \\psi^-1(\\sum_0^n{\\psi(u_i;\\theta)}; \\theta)

        """
        raise NotImplementedError

    def probability_density(self, X):
        """Compute probability density function for given copula family.

        The probability density(pdf) for a given copula is defined as:

        .. math:: c(U,V) = \\frac{\\partial^2 C(u,v)}{\\partial v \\partial u}

        Args:
            X(np.ndarray): Shape (n, 2).Datapoints to compute pdf.

        Returns:
            np.array: Probability density for the input values.

        """
        raise NotImplementedError

    def log_probability_density(self, X):
        """Return log probability density of model.

        The log probability should be overridden with numerically stable
        variants whenever possible.

        Arguments:
            X: `np.ndarray` of shape (n, 1).

        Returns:
            np.ndarray

        """
        return np.log(self.probability_density(X))

    def pdf(self, X):
        """Shortcut to :meth:`probability_density`."""
        return self.probability_density(X)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution function for the copula, :math:`C(u, v)`.

        Args:
            X(np.ndarray):

        Returns:
            numpy.array: cumulative probability

        """
        raise NotImplementedError

    def cdf(self, X):
        """Shortcut to :meth:`cumulative_distribution`."""
        return self.cumulative_distribution(X)

    def percent_point(self, y, V):
        """Compute the inverse of conditional cumulative distribution :math:`C(u|v)^{-1}`.

        Args:
            y: `np.ndarray` value of :math:`C(u|v)`.
            v: `np.ndarray` given value of v.
        """
        self.check_fit()
        result = []
        for _y, _v in zip(y, V):

            def f(u):
                return self.partial_derivative_scalar(u, _v) - _y
            minimum = brentq(f, EPSILON, 1.0)
            if isinstance(minimum, np.ndarray):
                minimum = minimum[0]
            result.append(minimum)
        return np.array(result)

    def ppf(self, y, V):
        """Shortcut to :meth:`percent_point`."""
        return self.percent_point(y, V)

    def partial_derivative(self, X):
        """Compute partial derivative of cumulative distribution.

        The partial derivative of the copula(CDF) is the conditional CDF.

         .. math:: F(v|u) = \\frac{\\partial C(u,v)}{\\partial u}

        The base class provides a finite difference approximation of the
        partial derivative of the CDF with respect to u.

        Args:
            X(np.ndarray)
            y(float)

        Returns:
            np.ndarray

        """
        delta = -2 * (X[:, 1] > 0.5) + 1
        delta = 0.0001 * delta
        X_prime = X.copy()
        X_prime[:, 1] += delta
        f = self.cumulative_distribution(X)
        f_prime = self.cumulative_distribution(X_prime)
        return (f_prime - f) / delta

    def partial_derivative_scalar(self, U, V):
        """Compute partial derivative :math:`C(u|v)` of cumulative density of single values."""
        self.check_fit()
        X = np.column_stack((U, V))
        return self.partial_derivative(X)

    def set_random_state(self, random_state):
        """Set the random state.

        Args:
            random_state (int, np.random.RandomState, or None): Seed or RandomState
                for the random generator.
        """
        self.random_state = validate_random_state(random_state)

    @random_state
    def sample(self, n_samples):
        """Generate specified `n_samples` of new data from model.

        The sampled are generated using the inverse transform method `v~U[0,1],v~C^-1(u|v)`

        Args:
            n_samples (int): amount of samples to create.

        Returns:
            np.ndarray: Array of length `n_samples` with generated data from the model.

        """
        if self.tau > 1 or self.tau < -1:
            raise ValueError('The range for correlation measure is [-1,1].')
        v = np.random.uniform(0, 1, n_samples)
        c = np.random.uniform(0, 1, n_samples)
        u = self.percent_point(c, v)
        return np.column_stack((u, v))

    def compute_theta(self):
        """Compute theta parameter using Kendall's tau."""
        raise NotImplementedError

    @classmethod
    def select_copula(cls, X):
        """Select best copula function based on likelihood.

        Given out candidate copulas the procedure proposed for selecting the one
        that best fit to a dataset of pairs :math:`\\{(u_j, v_j )\\}, j=1,2,...n` , is as follows:

        1. Estimate the most likely parameter :math:`\\theta` of each copula candidate for the given
           dataset.

        2. Construct :math:`R(z|\\theta)`. Calculate the area under the tail for each of the copula
           candidates.

        3. Compare the areas: :math:`a_u` achieved using empirical copula against the ones
           achieved for the copula candidates. Score the outcome of the comparison from 3 (best)
           down to 1 (worst).

        4. Proceed as in steps 2- 3 with the lower tail and function :math:`L`.

        5. Finally the sum of empirical upper and lower tail functions is compared against
           :math:`R + L`. Scores of the three comparisons are summed and the candidate with the
           highest value is selected.

        Args:
            X(np.ndarray): Matrix of shape (n,2).

        Returns:
            copula: Best copula that fits for it.

        """
        from sdgx.models.components.sdv_copulas.bivariate import select_copula
        warnings.warn('`Bivariate.select_copula` has been deprecated and will be removed in a later release. Please use `copulas.bivariate.select_copula` instead', DeprecationWarning)
        return select_copula(X)

    def save(self, filename):
        """Save the internal state of a copula in the specified filename.

        Args:
            filename(str): Path to save.

        Returns:
            None

        """
        content = self.to_dict()
        with open(filename, 'w') as f:
            json.dump(content, f)

    @classmethod
    def load(cls, copula_path):
        """Create a new instance from a file.

        Args:
            copula_path(str): Path to file with the serialized copula.

        Returns:
            Bivariate: Instance with the parameters stored in the file.

        """
        with open(copula_path) as f:
            copula_dict = json.load(f)
        return cls.from_dict(copula_dict)

def save(self, filename):
    """Save the internal state of a copula in the specified filename.

        Args:
            filename(str): Path to save.

        Returns:
            None

        """
    content = self.to_dict()
    with open(filename, 'w') as f:
        json.dump(content, f)

@classmethod
def load(cls, copula_path):
    """Create a new instance from a file.

        Args:
            copula_path(str): Path to file with the serialized copula.

        Returns:
            Bivariate: Instance with the parameters stored in the file.

        """
    with open(copula_path) as f:
        copula_dict = json.load(f)
    return cls.from_dict(copula_dict)

def read_csv(csv_filename, meta_filename=None, header=True, discrete=None):
    """Read a csv file."""
    data = pd.read_csv(csv_filename, header='infer' if header else None)
    if meta_filename:
        with open(meta_filename) as meta_file:
            metadata = json.load(meta_file)
        discrete_columns = [column['name'] for column in metadata['columns'] if column['type'] != 'continuous']
    elif discrete:
        discrete_columns = discrete.split(',')
        if not header:
            discrete_columns = [int(i) for i in discrete_columns]
    else:
        discrete_columns = []
    return (data, discrete_columns)

def read_tsv(data_filename, meta_filename):
    """Read a tsv file."""
    with open(meta_filename) as f:
        column_info = f.readlines()
    column_info_raw = [x.replace('{', ' ').replace('}', ' ').split() for x in column_info]
    discrete = []
    continuous = []
    column_info = []
    for idx, item in enumerate(column_info_raw):
        if item[0] == 'C':
            continuous.append(idx)
            column_info.append((float(item[1]), float(item[2])))
        else:
            assert item[0] == 'D'
            discrete.append(idx)
            column_info.append(item[1:])
    meta = {'continuous_columns': continuous, 'discrete_columns': discrete, 'column_info': column_info}
    with open(data_filename) as f:
        lines = f.readlines()
    data = []
    for row in lines:
        row_raw = row.split()
        row = []
        for idx, col in enumerate(row_raw):
            if idx in continuous:
                row.append(col)
            else:
                assert idx in discrete
                row.append(column_info[idx].index(col))
        data.append(row)
    return (np.asarray(data, dtype='float32'), meta['discrete_columns'])

def write_tsv(data, meta, output_filename):
    """Write to a tsv file."""
    with open(output_filename, 'w') as f:
        for row in data:
            for idx, col in enumerate(row):
                if idx in meta['continuous_columns']:
                    print(col, end=' ', file=f)
                else:
                    assert idx in meta['discrete_columns']
                    print(meta['column_info'][idx][int(col)], end=' ', file=f)
            print(file=f)

def main():
    """CLI."""
    args = _parse_args()
    if args.tsv:
        data, discrete_columns = read_tsv(args.data, args.metadata)
    else:
        data, discrete_columns = read_csv(args.data, args.metadata, args.header, args.discrete)
    if args.load:
        model = CTGAN.load(args.load)
    else:
        generator_dim = [int(x) for x in args.generator_dim.split(',')]
        discriminator_dim = [int(x) for x in args.discriminator_dim.split(',')]
        model = CTGAN(embedding_dim=args.embedding_dim, generator_dim=generator_dim, discriminator_dim=discriminator_dim, generator_lr=args.generator_lr, generator_decay=args.generator_decay, discriminator_lr=args.discriminator_lr, discriminator_decay=args.discriminator_decay, batch_size=args.batch_size, epochs=args.epochs)
    model.fit(data, discrete_columns)
    if args.save is not None:
        model.save(args.save)
    num_samples = args.num_samples or len(data)
    if args.sample_condition_column is not None:
        assert args.sample_condition_column_value is not None
    sampled = model.sample(num_samples, args.sample_condition_column, args.sample_condition_column_value)
    if args.tsv:
        write_tsv(sampled, args.metadata, args.output)
    else:
        sampled.to_csv(args.output, index=False)

class BaseSynthesizer:
    """Base class for all default synthesizers of ``CTGAN``.

    This should contain the save/load methods.
    """
    random_states = None

    def __getstate__(self):
        device_backup = self._device
        self.set_device(torch.device('cpu'))
        state = self.__dict__.copy()
        self.set_device(device_backup)
        random_states = self.random_states
        if isinstance(random_states, tuple) and isinstance(random_states[0], np.random.RandomState) and isinstance(random_states[1], torch.Generator):
            state['_numpy_random_state'] = random_states[0].get_state()
            state['_torch_random_state'] = random_states[1].get_state()
            del state['random_states']
        return state

    def __setstate__(self, state):
        np_state = state.pop('_numpy_random_state', None)
        torch_state = state.pop('_torch_random_state', None)
        if np_state is not None and torch_state is not None:
            current_torch_state = torch.Generator()
            current_torch_state.set_state(torch_state)
            current_numpy_state = np.random.RandomState()
            current_numpy_state.set_state(np_state)
            state['random_states'] = (current_numpy_state, current_torch_state)
        self.__dict__ = state

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU')."""
        self._device = device
        if self._generator is not None:
            self._generator.to(self._device)

    def save(self, path):
        """Save the model in the passed `path`."""
        device_backup = self._device
        self.set_device(torch.device('cpu'))
        with open(path, 'wb') as output:
            cloudpickle.dump(self, output)
        self.set_device(device_backup)

    @classmethod
    def load(cls, path: Union[str, Path], device: str='cuda' if torch.cuda.is_available() else 'cpu'):
        """Load the model stored in the passed arg `path`."""
        with open(path, 'rb') as f:
            model = cloudpickle.load(f)
        model.set_device(device)
        return model

    def set_random_state(self, random_state):
        """Set the random state.

        Args:
            random_state (int, tuple, or None):
                Either a tuple containing the (numpy.random.RandomState, torch.Generator)
                or an int representing the random seed to use for both random states.
        """
        if random_state is None:
            self.random_states = random_state
        elif isinstance(random_state, int):
            self.random_states = (np.random.RandomState(seed=random_state), torch.Generator().manual_seed(random_state))
        elif isinstance(random_state, tuple) and isinstance(random_state[0], np.random.RandomState) and isinstance(random_state[1], torch.Generator):
            self.random_states = random_state
        else:
            raise TypeError(f'`random_state` {random_state} expected to be an int or a tuple of (`np.random.RandomState`, `torch.Generator`)')

def save(self, path):
    """Save the model in the passed `path`."""
    device_backup = self._device
    self.set_device(torch.device('cpu'))
    with open(path, 'wb') as output:
        cloudpickle.dump(self, output)
    self.set_device(device_backup)

@click.option('--output_file', default=(_HERE / 'dataset/benchmark.csv').as_posix())
@click.option('--num_rows', default=1000000)
@click.option('--int_cols', default=15)
@click.option('--float_cols', default=15)
@click.option('--string_cols', default=10)
@click.option('--string_discrete_nums', default=50)
@click.option('--timestamp_cols', default=10)
@click.option('--datetime_cols', default=0)
@click.command()
def generate_dateset(output_file, num_rows, int_cols, float_cols, string_cols, string_discrete_nums, timestamp_cols, datetime_cols):
    headers = itertools.chain.from_iterable([(f'int_col{i}' for i in range(int_cols)), (f'float_col{i}' for i in range(float_cols)), (f'string_col{i}' for i in range(string_cols)), (f'timestamp_col{i}' for i in range(timestamp_cols)), (f'datetime_col{i}' for i in range(datetime_cols))])
    output_file = Path(output_file).expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    random_str_list = [random_string(25) for i in range(string_discrete_nums)]

    def _generate_one_line():
        return ','.join(map(str, itertools.chain((random_int() for _ in range(int_cols)), (random_float() for _ in range(float_cols)), (random.choice(random_str_list) for _ in range(string_cols)), (random_timestamp() for _ in range(timestamp_cols)), (random_datetime() for _ in range(datetime_cols)))))
    with output_file.open('w') as f:
        f.write(','.join(headers) + '\n')
        chunk_size = 1000
        for i in range(0, num_rows, chunk_size):
            f.write('\n'.join((_generate_one_line() for _ in range(chunk_size))))
            f.write('\n')

@pytest.fixture
def ctgan_synthesizer(demo_single_table_data_pos_neg_connector, demo_single_table_data_pos_neg_metadata):
    yield Synthesizer(metadata=demo_single_table_data_pos_neg_metadata, model=CTGANSynthesizerModel(epochs=1), data_connector=demo_single_table_data_pos_neg_connector)

class MockModel(SynthesizerModel):
    MODEL_SAVE_NAME = 'mockmoel.pth'

    def fit(self, metadata, dataloader, **kwargs):
        pass

    def sample(self, count, **kwargs) -> pd.DataFrame:
        return pd.DataFrame({'a': [i for i in range(count)], 'b': [i * 2 for i in range(count)]})

    def save(self, save_dir: str | Path):
        save_dir = Path(save_dir).expanduser().resolve()
        save_dir.mkdir(parents=True, exist_ok=True)
        save_dir.joinpath(self.MODEL_SAVE_NAME).touch()

    @classmethod
    def load(cls, save_dir: str | Path):
        save_dir = Path(save_dir).expanduser().resolve()
        if not save_dir.joinpath(cls.MODEL_SAVE_NAME).exists():
            raise FileNotFoundError
        return MockModel()

def save(self, save_dir: str | Path):
    save_dir = Path(save_dir).expanduser().resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    save_dir.joinpath(self.MODEL_SAVE_NAME).touch()

@classmethod
def load(cls, save_dir: str | Path):
    save_dir = Path(save_dir).expanduser().resolve()
    if not save_dir.joinpath(cls.MODEL_SAVE_NAME).exists():
        raise FileNotFoundError
    return MockModel()

@pytest.fixture
def metadata():
    yield Metadata()

@pytest.fixture
def synthesizer(cacher_kwargs):
    yield Synthesizer(MockModel(), data_connector=MockDataConnector(), raw_data_loaders_kwargs={'cacher_kwargs': cacher_kwargs}, data_processors=[MockDataProcessor()], processed_data_loaders_kwargs={'cacher_kwargs': cacher_kwargs}, metadata=Metadata())

@pytest.fixture
def save_dir(tmp_path):
    d = tmp_path / 'unittest-synthesizer'
    yield d
    shutil.rmtree(d, ignore_errors=True)

def test_save_and_load(synthesizer, save_dir):
    assert synthesizer.save(save_dir)
    assert (save_dir / synthesizer.METADATA_SAVE_NAME).exists()
    assert (save_dir / synthesizer.MODEL_SAVE_DIR).exists()
    synthesizer = Synthesizer.load(save_dir, model=MockModel)
    assert synthesizer

@pytest.fixture
def dummy_single_table_data_connector(dummy_single_table_path):
    yield CsvConnector(path=dummy_single_table_path)

@pytest.fixture
def dummy_single_table_data_loader(dummy_single_table_data_connector, cacher_kwargs):
    d = DataLoader(dummy_single_table_data_connector, cacher_kwargs=cacher_kwargs)
    yield d
    d.finalize()

@pytest.fixture
def dummy_single_table_metadata(dummy_single_table_data_loader):
    yield Metadata.from_dataloader(dummy_single_table_data_loader)

@pytest.fixture
def cacher_kwargs(tmp_path):
    cache_dir = tmp_path / 'cache'
    yield {'cache_dir': cache_dir.as_posix()}
    shutil.rmtree(cache_dir, ignore_errors=True)

@pytest.fixture
def demo_single_table_data_connector(demo_single_table_path):
    yield CsvConnector(path=demo_single_table_path)

@pytest.fixture
def demo_single_table_data_loader(demo_single_table_data_connector, cacher_kwargs):
    d = DataLoader(demo_single_table_data_connector, cacher_kwargs=cacher_kwargs)
    yield d
    d.finalize()

@pytest.fixture
def demo_single_table_metadata(demo_single_table_data_loader):
    yield Metadata.from_dataloader(demo_single_table_data_loader)

@pytest.fixture
def demo_multi_table_data_connector(demo_multi_table_path):
    connector_dict = {}
    for each_table in demo_multi_table_path.keys():
        each_path = demo_multi_table_path[each_table]
        connector_dict[each_table] = CsvConnector(path=each_path)
    yield connector_dict

@pytest.fixture
def demo_multi_table_data_loader(demo_multi_table_data_connector, cacher_kwargs):
    loader_dict = {}
    for each_table in demo_multi_table_data_connector.keys():
        each_connector = demo_multi_table_data_connector[each_table]
        each_d = DataLoader(each_connector, cacher_kwargs=cacher_kwargs)
        loader_dict[each_table] = each_d
    yield loader_dict
    for each_table in demo_multi_table_data_connector.keys():
        demo_multi_table_data_connector[each_table].finalize()

@pytest.fixture
def demo_multi_data_parent_matadata(demo_multi_table_data_loader):
    yield Metadata.from_dataloader(demo_multi_table_data_loader['store'])

@pytest.fixture
def demo_multi_data_child_matadata(demo_multi_table_data_loader):
    yield Metadata.from_dataloader(demo_multi_table_data_loader['train'])

@pytest.fixture
def demo_multi_data_relationship():
    yield Relationship.build(parent_table='store', child_table='train', foreign_keys=['Store'])

@pytest.mark.parametrize('json_output', [True, False])
@pytest.mark.parametrize('command', [list_cachers, list_data_connectors, list_data_processors, list_data_exporters, list_models])
def test_list_extension_api(command, json_output):
    runner = CliRunner()
    result = runner.invoke(command, ['--json_output', json_output])
    assert result.exit_code == 0
    if json_output:
        assert NormalMessage()._dump_json() in result.output
        assert NormalMessage()._dump_json() == result.output.strip().split('\n')[-1]
    else:
        assert NormalMessage()._dump_json() not in result.output

@pytest.mark.parametrize('model', ['CTGAN'])
@pytest.mark.parametrize('json_output', [True, False])
@pytest.mark.parametrize('torchrun', [False])
def test_fit_save_load_sample(model, demo_single_table_path, cacher_kwargs, json_output, torchrun, tmp_path):
    runner = CliRunner()
    save_dir = tmp_path / f'unittest-{model}'
    result = runner.invoke(fit, ['--save_dir', save_dir, '--model', model, '--model_kwargs', json.dumps({'epochs': 1}), '--data_connector', 'csvconnector', '--data_connector_kwargs', json.dumps({'path': demo_single_table_path}), '--raw_data_loaders_kwargs', json.dumps({'cacher_kwargs': cacher_kwargs}), '--processed_data_loaders_kwargs', json.dumps({'cacher_kwargs': cacher_kwargs}), '--json_output', json_output, '--torchrun', torchrun])
    assert result.exit_code == 0
    assert save_dir.exists()
    assert len(list(save_dir.iterdir())) > 0
    if json_output:
        assert json.loads(result.output.strip().split('\n')[-1])
    export_dst = tmp_path / 'exported.csv'
    result = runner.invoke(sample, ['--load_dir', save_dir, '--model', model, '--json_output', json_output, '--export_dst', export_dst.as_posix(), '--torchrun', torchrun])
    assert result.exit_code == 0
    assert export_dst.exists()
    if json_output:
        assert json.loads(result.output.strip().split('\n')[-1])

@pytest.fixture
def export_dst(tmp_path):
    filename = tmp_path / 'csv-exported.csv'
    filename.unlink(missing_ok=True)
    yield filename

@pytest.fixture
def manager():
    yield DataProcessorManager()

@pytest.fixture
def manager():
    yield ModelManager()

@pytest.fixture
def manager():
    yield DataConnectorManager()

@pytest.fixture
def manager():
    yield DataExporterManager()

@pytest.mark.parametrize('parent_table, parent_metadata, child_table, child_metadata, foreign_keys, exception', [('parent', parent_metadata, 'child', child_metadata, [KeyTuple('parent_id', 'parent_id')], None), ('parent', error_parent_metadata, 'child', child_metadata, [KeyTuple('parent_id', 'parent_id')], RelationshipInitError), ('parent', parent_metadata, 'child', error_child_metadata, [KeyTuple('parent_id', 'parent_id')], RelationshipInitError), ('parent', parent_metadata, 'parent', parent_metadata, [KeyTuple('parent_id', 'parent_id')], RelationshipInitError), ('parent', parent_metadata, 'parent', parent_metadata, [], RelationshipInitError), ('', parent_metadata, 'child', child_metadata, [KeyTuple('parent_id', 'parent_id')], RelationshipInitError), ('parent', parent_metadata, '', child_metadata, [KeyTuple('parent_id', 'parent_id')], RelationshipInitError), ('', parent_metadata, '', child_metadata, [KeyTuple('parent_id', 'parent_id')], RelationshipInitError), ('', parent_metadata, '', child_metadata, [], RelationshipInitError)])
def test_build(parent_table, parent_metadata, child_table, child_metadata, foreign_keys, exception):
    if exception:
        with pytest.raises(exception):
            Relationship.build(parent_table=parent_table, parent_metadata=parent_metadata, child_table=child_table, child_metadata=child_metadata, foreign_keys=foreign_keys)
    else:
        relationship = Relationship.build(parent_table=parent_table, parent_metadata=parent_metadata, child_table=child_table, child_metadata=child_metadata, foreign_keys=foreign_keys)
        assert relationship.parent_table == parent_table
        assert relationship.child_table == child_table
        assert relationship.foreign_keys == foreign_keys

def test_save_and_load(tmpdir):
    save_file = tmpdir / 'relationship.json'
    relationship = Relationship.build(parent_table='parent', parent_metadata=Metadata(primary_keys=['parent_id'], column_list=['parent_id'], id_columns={'parent_id'}), child_table='child', child_metadata=Metadata(primary_keys=['child_id'], column_list=['parent_id', 'child_id'], id_columns={'parent_id', 'child_id'}), foreign_keys=[KeyTuple('parent_id', 'parent_id')])
    relationship.save(save_file)
    assert save_file.exists()
    assert relationship == Relationship.load(save_file)

@pytest.fixture
def dataloader(demo_single_table_path, cacher_kwargs):
    d = DataLoader(CsvConnector(path=demo_single_table_path), cacher_kwargs=cacher_kwargs)
    yield d
    d.finalize(clear_cache=True)

@pytest.fixture
def metadata(dataloader):
    yield Metadata.from_dataloader(dataloader)

def test_metadata(metadata: Metadata):
    assert metadata.discrete_columns == metadata.get('discrete_columns')
    assert metadata.id_columns == metadata.get('id_columns')
    assert metadata.datetime_columns == metadata.get('datetime_columns')
    assert metadata.bool_columns == metadata.get('bool_columns')
    assert metadata.int_columns == metadata.get('int_columns')
    assert metadata.float_columns == metadata.get('float_columns')
    metadata.set('a', 'something')
    assert metadata.get('a') == {'something'}
    assert metadata._dump_json()

def test_metadata_save_load(metadata: Metadata, tmp_path: Path):
    test_path = tmp_path / 'metadata_path_test.json'
    metadata.save(test_path)
    new_meatadata = Metadata.load(test_path)
    assert metadata == new_meatadata

def test_metadata_primary_query_filed_tags():
    metadata = Metadata()
    metadata.set('id_columns', {'user_id'})
    metadata.set('int_columns', {'user_id', 'age'})
    results = metadata.query('user_id')
    results_list = list(results)
    print(results_list)
    assert 'id_columns' in results_list
    assert 'int_columns' in results_list

def test_from_dataloader(demo_relational_table_path, tmp_path):
    table_a_path, table_b_path, pairs = demo_relational_table_path
    dl_a = DataLoader(CsvConnector(path=table_a_path))
    dl_b = DataLoader(CsvConnector(path=table_b_path))
    relationship = Relationship.build(parent_table=dl_a.identity, parent_metadata=Metadata(primary_keys=['id'], column_list=['id'], id_columns={'id'}), child_table=dl_b.identity, child_metadata=Metadata(primary_keys=['child_id'], column_list=['child_id', 'foreign_id'], id_columns={'child_id', 'foreign_id'}), foreign_keys=pairs)
    combiner = MetadataCombiner.from_dataloader(dataloaders=[dl_a, dl_b], metadata_from_dataloader_kwargs={}, relationshipe_inspector=MockInspector, relationships_inspector_kwargs=dict(dummy_data=[relationship]))
    assert dl_a.identity in combiner.named_metadata
    assert dl_b.identity in combiner.named_metadata
    assert combiner.relationships == [relationship]
    save_dir = tmp_path / 'unittest-combinner'
    combiner.save(save_dir)
    assert save_dir.exists()
    loaded_combiner = MetadataCombiner.load(save_dir)
    assert combiner == loaded_combiner

def test_from_dataframe(demo_relational_table_path, tmp_path):
    table_a_path, table_b_path, pair = demo_relational_table_path
    relationship = Relationship.build(parent_table='table_a', parent_metadata=Metadata(primary_keys=['id'], column_list=['id'], id_columns={'id'}), child_table='table_b', child_metadata=Metadata(primary_keys=['child_id'], column_list=['child_id', 'foreign_id'], id_columns={'child_id', 'foreign_id'}), foreign_keys=pair)
    tb_a = pd.read_csv(table_a_path)
    tb_b = pd.read_csv(table_b_path)
    combiner = MetadataCombiner.from_dataframe(dataframes=[tb_a, tb_b], names=['table_a', 'table_b'], metadata_from_dataloader_kwargs={}, relationshipe_inspector=MockInspector, relationships_inspector_kwargs=dict(dummy_data=[relationship]))
    assert 'table_a' in combiner.named_metadata
    assert 'table_b' in combiner.named_metadata
    assert combiner.relationships == [relationship]
    save_dir = tmp_path / 'unittest-combinner'
    combiner.save(save_dir)
    assert save_dir.exists()
    loaded_combiner = MetadataCombiner.load(save_dir)
    assert combiner == loaded_combiner

def test_custom_build_from_dataloaders(demo_relational_table_path, tmp_path):
    table_a_path, table_b_path, pairs = demo_relational_table_path
    dl_a = DataLoader(CsvConnector(path=table_a_path))
    dl_b = DataLoader(CsvConnector(path=table_b_path))
    relationship = Relationship.build(parent_table=dl_a.identity, parent_metadata=Metadata(primary_keys=['id'], column_list=['id'], id_columns={'id'}), child_table=dl_b.identity, child_metadata=Metadata(primary_keys=['child_id'], column_list=['child_id', 'foreign_id'], id_columns={'child_id', 'foreign_id'}), foreign_keys=pairs)
    combiner = MetadataCombiner.from_dataloader(dataloaders=[dl_a, dl_b], metadata_from_dataloader_kwargs={}, relationshipe_inspector=MockInspector, relationships_inspector_kwargs=dict(dummy_data=Relationship.build(parent_table='balaP', parent_metadata=Metadata(primary_keys=['balabala'], column_list=['balabala'], id_columns={'balabala'}), child_table='balaC', child_metadata=Metadata(primary_keys=['child_id'], column_list=['balabala', 'child_id'], id_columns={'balabala', 'child_id'}), foreign_keys=['balabala'])), relationships=[relationship])
    assert dl_a.identity in combiner.named_metadata
    assert dl_b.identity in combiner.named_metadata
    assert combiner.relationships == [relationship]
    save_dir = tmp_path / 'unittest-combinner'
    combiner.save(save_dir)
    assert save_dir.exists()
    loaded_combiner = MetadataCombiner.load(save_dir)
    assert combiner == loaded_combiner

def test_custom_build_from_dataframe(demo_relational_table_path, tmp_path):
    table_a_path, table_b_path, pair = demo_relational_table_path
    relationship = Relationship.build(parent_table='table_a', parent_metadata=Metadata(primary_keys=['id'], column_list=['id'], id_columns={'id'}), child_table='table_b', child_metadata=Metadata(primary_keys=['child_id'], column_list=['child_id', 'foreign_id'], id_columns={'child_id', 'foreign_id'}), foreign_keys=pair)
    tb_a = pd.read_csv(table_a_path)
    tb_b = pd.read_csv(table_b_path)
    combiner = MetadataCombiner.from_dataframe(dataframes=[tb_a, tb_b], names=['table_a', 'table_b'], metadata_from_dataloader_kwargs={}, relationshipe_inspector=MockInspector, relationships_inspector_kwargs=dict(dummy_data=Relationship.build(parent_table='balaP', parent_metadata=Metadata(primary_keys=['balabala'], column_list=['balabala'], id_columns={'balabala'}), child_table='balaC', child_metadata=Metadata(primary_keys=['child_id'], column_list=['balabala', 'child_id'], id_columns={'balabala', 'child_id'}), foreign_keys=['balabala'])), relationships=[relationship])
    assert 'table_a' in combiner.named_metadata
    assert 'table_b' in combiner.named_metadata
    assert combiner.relationships == [relationship]
    save_dir = tmp_path / 'unittest-combinner'
    combiner.save(save_dir)
    assert save_dir.exists()
    loaded_combiner = MetadataCombiner.load(save_dir)
    assert combiner == loaded_combiner

@pytest.fixture
def dummy_relationship(demo_relational_table_path):
    _, _, pairs = demo_relational_table_path
    yield Relationship.build(parent_table='parent', child_table='child', foreign_keys=pairs)

@pytest.fixture
def csv_file(tmp_path):
    csv = tmp_path / 'test.csv'
    csv.write_text('index,a,b,c\n0,1,2,3\n1,4,5,6')
    yield csv
    csv.unlink()

@pytest.fixture
def csv_file(tmp_path):
    csv = tmp_path / 'test.csv'
    csv.write_text('index,a,b,c\n0,1,2,3\n1,4,5,6')
    yield csv
    csv.unlink()

@pytest.fixture
def csv_connector(csv_file):
    return CsvConnector(path=csv_file)

@pytest.fixture
def ctgan():
    yield CTGANSynthesizerModel(epochs=1)

@pytest.fixture
def save_model_dir(tmp_path):
    dirname = tmp_path / 'model'
    yield dirname
    shutil.rmtree(dirname, ignore_errors=True)

def test_ctgan(ctgan: CTGANSynthesizerModel, dummy_single_table_metadata, dummy_single_table_data_loader, save_model_dir):
    ctgan.fit(dummy_single_table_metadata, dummy_single_table_data_loader)
    sampled_data = ctgan.sample(10)
    assert_sampled_data(dummy_single_table_data_loader, sampled_data, 10)
    ctgan.save(save_model_dir)
    assert save_model_dir.exists()
    model = CTGANSynthesizerModel.load(save_model_dir)
    sampled_data = model.sample(10)
    assert_sampled_data(dummy_single_table_data_loader, sampled_data, 10)

