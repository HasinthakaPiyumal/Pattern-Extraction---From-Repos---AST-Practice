# Cluster 6

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

def add_log_file_handler():
    logger.add('sdgx-{time}.log', rotation='10 MB')

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

def keys(self) -> list:
    """
        Same as ``columns``
        """
    return self.data_connector.keys()

class DataExporterManager(Manager):
    register_type = DataExporter
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_exporters(self):
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(data_exporters)

    def init_exporter(self, exporter_name, **kwargs: dict[str, Any]) -> DataExporter:
        return self.init(exporter_name, **kwargs)

def init_exporter(self, exporter_name, **kwargs: dict[str, Any]) -> DataExporter:
    return self.init(exporter_name, **kwargs)

class CacherManager(Manager):
    register_type = Cacher
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_cachers(self):
        """
        redirect to registed_cls
        """
        return self.registed_cls

    def load_all_local_model(self):
        """
        Load all local model. Currently only ``sdgx.cachers``.
        """
        self._load_dir(cachers)

    def init_cacher(self, cacher_name, **kwargs: dict[str, Any]) -> Cacher:
        """
        redirect to init
        """
        return self.init(cacher_name, **kwargs)

def init_cacher(self, cacher_name, **kwargs: dict[str, Any]) -> Cacher:
    """
        redirect to init
        """
    return self.init(cacher_name, **kwargs)

class DataProcessorManager(Manager):
    """
    This is a plugin management class for data processing components.

    Properties:
        - register_type: Specifies the type of data processors to register.
        - project_name: Stores the project name from the extension module.
        - hookspecs_model: Stores the hook specifications model from the extension module.
        - preset_default_processors: Stores a list of default processor names in lowercase.
        - registed_data_processors: Property that returns the registered data processors.
        - registed_default_processor_list: Property that returns the registered default data processors.

    Methods:
        - load_all_local_model: Loads all local models for formatters, generators, samplers, and transformers.
        - init_data_processor: Initializes a data processor with the given name and keyword arguments.
        - init_all_processors: Initializes all registered data processors with optional keyword arguments.
        - init_default_processors: Initializes default processors that are both registered and preset.

    """
    register_type = DataProcessor
    '\n    Specifies the type of data processors to register.'
    project_name = PROJECT_NAME
    '\n    Stores the project name from the extension module.\n    '
    hookspecs_model = extension
    '\n    The hook specifications model from the extension module.\n    '
    preset_defalut_processors = [p.lower() for p in ['SpecificCombinationTransformer', 'FixedCombinationTransformer', 'NonValueTransformer', 'OutlierTransformer', 'EmailGenerator', 'ChnPiiGenerator', 'IntValueFormatter', 'DatetimeFormatter']] + ['ConstValueTransformer'.lower(), 'PositiveNegativeFilter'.lower(), 'EmptyTransformer'.lower(), 'ColumnOrderTransformer'.lower()]
    '\n    preset_defalut_processors list stores the lowercase names of the transformers loaded by default. When using the synthesizer, they will be loaded by default to facilitate user operations.\n\n    Keep ColumnOrderTransformer always at the last one.\n    '

    @property
    def registed_data_processors(self):
        """
        This property returns all registered data processors
        """
        return self.registed_cls

    @property
    def registed_default_processor_list(self):
        """
        This property returns all registered default data processors
        """
        registed_processor_list = self.registed_data_processors.keys()
        default_processors = []
        for each_processor in self.preset_defalut_processors:
            if each_processor in registed_processor_list:
                default_processors.append(each_processor)
        return default_processors

    def load_all_local_model(self):
        """
        loads all local models
        """
        self._load_dir(data_processors.formatters)
        self._load_dir(data_processors.generators)
        self._load_dir(data_processors.samplers)
        self._load_dir(data_processors.transformers)
        self._load_dir(data_processors.filter)

    def init_data_processor(self, processor_name, **kwargs: dict[str, Any]) -> DataProcessor:
        """
        Initializes a data processor with the given name and parameters
        """
        return self.init(processor_name, **kwargs)

    def init_all_processors(self, **kwargs: Any) -> list[DataProcessor]:
        """
        Initializes all registered data processors
        """
        return [self.init(processor_name, **kwargs) for processor_name in self.registed_data_processors.keys()]

    def init_default_processors(self, **kwargs: Any) -> list[DataProcessor]:
        """
        Initializes all default data processors
        """
        return [self.init(processor_name, **kwargs) for processor_name in self.registed_default_processor_list]

@property
def registed_default_processor_list(self):
    """
        This property returns all registered default data processors
        """
    registed_processor_list = self.registed_data_processors.keys()
    default_processors = []
    for each_processor in self.preset_defalut_processors:
        if each_processor in registed_processor_list:
            default_processors.append(each_processor)
    return default_processors

def init_data_processor(self, processor_name, **kwargs: dict[str, Any]) -> DataProcessor:
    """
        Initializes a data processor with the given name and parameters
        """
    return self.init(processor_name, **kwargs)

def init_all_processors(self, **kwargs: Any) -> list[DataProcessor]:
    """
        Initializes all registered data processors
        """
    return [self.init(processor_name, **kwargs) for processor_name in self.registed_data_processors.keys()]

def init_default_processors(self, **kwargs: Any) -> list[DataProcessor]:
    """
        Initializes all default data processors
        """
    return [self.init(processor_name, **kwargs) for processor_name in self.registed_default_processor_list]

class EmailGenerator(PIIGenerator):
    """
    A class for generating and reversing the conversion of email addresses in a pd.DataFrame.

    This class is a subclass of `PIIGenerator` and is designed to handle the conversion and
    reversal of email addresses in a pd.DataFrame. It uses the `email_columns_list` to identify
    which columns in the pd.DataFrame contain email addresses.

    Attributes:
        email_columns_list (list): A list of column names in the pd.DataFrame that contain email addresses.

    Methods:
        fit(metadata: Metadata | None = None): Fits the generator to the metadata.
        convert(raw_data: pd.DataFrame) -> pd.DataFrame: Converts the email addresses in the pd.DataFrame.
        reverse_convert(processed_data: pd.DataFrame) -> pd.DataFrame: Reverses the conversion of the email addresses in the pd.DataFrame.
    """
    email_columns_list: list
    fitted: bool

    def __init__(self):
        self.email_columns_list = []
        self.fitted = False

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        self.email_columns_list = list(metadata.get('email_columns'))
        self.fitted = True

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        if not self.email_columns_list:
            return raw_data
        processed_data = raw_data
        for each_col in self.email_columns_list:
            processed_data = self.remove_columns(processed_data, each_col)
        return processed_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        if not self.email_columns_list:
            return processed_data
        df_length = processed_data.shape[0]
        for each_col_name in self.email_columns_list:
            each_email_col = [fake.ascii_company_email() for _ in range(df_length)]
            each_email_df = pd.DataFrame({each_col_name: each_email_col})
            processed_data = self.attach_columns(processed_data, each_email_df)
        return processed_data

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    if not self.email_columns_list:
        return raw_data
    processed_data = raw_data
    for each_col in self.email_columns_list:
        processed_data = self.remove_columns(processed_data, each_col)
    return processed_data

class ChnPiiGenerator(PIIGenerator):
    """ """
    chn_id_columns_list: list
    chn_phone_columns_list: list
    chn_name_columns_list: list
    chn_company_name_list: list
    fitted: bool

    def __init__(self):
        self.chn_id_columns_list = []
        self.chn_phone_columns_list = []
        self.chn_name_columns_list = []
        self.chn_company_name_list = []
        self.fitted = False

    @property
    def chn_pii_columns(self):
        return self.chn_id_columns_list + self.chn_name_columns_list + self.chn_phone_columns_list + self.chn_company_name_list

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        for each_col in metadata.column_list:
            data_type = metadata.get_column_data_type(each_col)
            if data_type == 'chinese_name':
                self.chn_name_columns_list.append(each_col)
                continue
            if data_type == 'china_mainland_mobile_phone':
                self.chn_phone_columns_list.append(each_col)
                continue
            if data_type == 'china_mainland_id':
                self.chn_id_columns_list.append(each_col)
                continue
            if data_type == 'chinese_company_name':
                self.chn_company_name_list.append(each_col)
        self.fitted = True

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        if not self.chn_pii_columns:
            return raw_data
        processed_data = raw_data
        for each_col in self.chn_pii_columns:
            processed_data = self.remove_columns(processed_data, each_col)
        return processed_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        if not self.chn_pii_columns:
            return processed_data
        df_length = processed_data.shape[0]
        for each_col_name in self.chn_id_columns_list:
            each_email_col = [fake.ssn() for _ in range(df_length)]
            each_email_df = pd.DataFrame({each_col_name: each_email_col})
            processed_data = self.attach_columns(processed_data, each_email_df)
        for each_col_name in self.chn_phone_columns_list:
            each_email_col = [fake.phone_number() for _ in range(df_length)]
            each_email_df = pd.DataFrame({each_col_name: each_email_col})
            processed_data = self.attach_columns(processed_data, each_email_df)
        for each_col_name in self.chn_name_columns_list:
            each_email_col = [fake.name() for _ in range(df_length)]
            each_email_df = pd.DataFrame({each_col_name: each_email_col})
            processed_data = self.attach_columns(processed_data, each_email_df)
        for each_col_name in self.chn_company_name_list:
            each_company_col = [fake.company() for _ in range(df_length)]
            each_company_df = pd.DataFrame({each_col_name: each_company_col})
            processed_data = self.attach_columns(processed_data, each_company_df)
        return processed_data

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    for each_col in metadata.column_list:
        data_type = metadata.get_column_data_type(each_col)
        if data_type == 'chinese_name':
            self.chn_name_columns_list.append(each_col)
            continue
        if data_type == 'china_mainland_mobile_phone':
            self.chn_phone_columns_list.append(each_col)
            continue
        if data_type == 'china_mainland_id':
            self.chn_id_columns_list.append(each_col)
            continue
        if data_type == 'chinese_company_name':
            self.chn_company_name_list.append(each_col)
    self.fitted = True

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    if not self.chn_pii_columns:
        return raw_data
    processed_data = raw_data
    for each_col in self.chn_pii_columns:
        processed_data = self.remove_columns(processed_data, each_col)
    return processed_data

class PositiveNegativeFilter(Filter):
    """
    A data processor for filtering positive and negative values.

    This filter is used to ensure that values in specific columns remain positive or negative.
    During the reverse conversion process, rows that do not meet the expected positivity or
    negativity will be removed.

    Attributes:
        int_columns (set): A set of column names containing integer values.
        float_columns (set): A set of column names containing float values.
        positive_columns (set): A set of column names that should contain positive values.
        negative_columns (set): A set of column names that should contain negative values.
    """
    int_columns: set
    '\n    A set of column names that contain integer values.\n    '
    float_columns: set
    '\n    A set of column names that contain float values.\n    '
    positive_columns: set
    '\n    A set of column names that are identified as containing positive numeric values.\n    '
    negative_columns: set
    '\n    A set of column names that are identified as containing negative numeric values.\n    '

    def __init__(self):
        self.int_columns = set()
        self.float_columns = set()
        self.positive_columns = set()
        self.negative_columns = set()

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the data filter.
        """
        logger.info('PositiveNegativeFilter Fitted.')
        self.int_columns = metadata.int_columns
        self.float_columns = metadata.float_columns
        self.positive_columns = set(metadata.numeric_format['positive'])
        self.negative_columns = set(metadata.numeric_format['negative'])
        self.fitted = True

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert method for data filter (No Action).
        """
        logger.info('Converting data using PositiveNegativeFilter... Finished (No Action)')
        return raw_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse_convert method for the pos_neg data filter.

        Iterate through each row of data, check if there are negative values in positive_columns,
        or positive values in negative_columns. If the conditions are not met, discard the row.
        """
        logger.info(f'Data reverse-converted by PositiveNegativeFilter Start with Shape: {processed_data.shape}.')
        mask = pd.Series(True, index=processed_data.index)
        for col in self.positive_columns:
            if col in processed_data.columns and pd.api.types.is_numeric_dtype(processed_data[col]):
                mask &= processed_data[col] >= 0
        for col in self.negative_columns:
            if col in processed_data.columns and pd.api.types.is_numeric_dtype(processed_data[col]):
                mask &= processed_data[col] <= 0
        filtered_data = processed_data[mask]
        logger.info(f'Data reverse-converted by PositiveNegativeFilter with Output Shape: {filtered_data.shape}.')
        return filtered_data

def __init__(self):
    self.int_columns = set()
    self.float_columns = set()
    self.positive_columns = set()
    self.negative_columns = set()

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the data filter.
        """
    logger.info('PositiveNegativeFilter Fitted.')
    self.int_columns = metadata.int_columns
    self.float_columns = metadata.float_columns
    self.positive_columns = set(metadata.numeric_format['positive'])
    self.negative_columns = set(metadata.numeric_format['negative'])
    self.fitted = True

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Convert method for data filter (No Action).
        """
    logger.info('Converting data using PositiveNegativeFilter... Finished (No Action)')
    return raw_data

class NumericValueTransformer(Transformer):
    """
    A transformer class for numeric data.

    This class is used to transform numeric data by scaling it using the StandardScaler from sklearn.

    Attributes:
        standard_scale (bool): A flag indicating whether to scale the data using StandardScaler.
        int_columns (Set): A set of column names that are of integer type.
        float_columns (Set): A set of column names that are of float type.
        scalers (Dict): A dictionary of scalers for each numeric column.
    """
    standard_scale: bool = True
    '\n    A flag indicating whether to scale the data using StandardScaler.\n    If True, the data will be scaled using StandardScaler.\n    If False, the data will not be scaled.\n    '
    int_columns: Set
    '\n    A set of column names that are of integer type.\n    These columns will be considered for scaling if `standard_scale` is True.\n    '
    float_columns: Set
    '\n    A set of column names that are of float type.\n    These columns will be considered for scaling if `standard_scale` is True.\n    '
    scalers: Dict
    '\n    A dictionary of scalers for each numeric column.\n    The keys are the column names and the values are the corresponding scalers.\n    '

    def __init__(self):
        self.int_columns = set()
        self.float_columns = set()
        self.scalers = {}

    def fit(self, metadata: Metadata | None=None, tabular_data: DataLoader | pd.DataFrame=None, **kwargs: dict[str, Any]):
        """
        The fit method.

        Data columns of int and float types need to be recorded here (Get data from metadata).
        """
        for each_col in metadata.int_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'int':
                self.int_columns.add(each_col)
                continue
            if metadata.get_column_data_type(each_col) == 'id':
                self.int_columns.add(each_col)
        for each_col in metadata.float_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'float':
                self.float_columns.add(each_col)
        if len(self.int_columns) == 0 and len(self.float_columns) == 0:
            logger.info('NumericValueTransformer Fitted (No numeric columns).')
            return
        for each_col in list(self.int_columns) + list(self.float_columns):
            self._fit_column(each_col, tabular_data[[each_col]])
        self.fitted = True
        logger.info('NumericValueTransformer Fitted.')

    def _fit_column(self, column_name: str, column_data: pd.DataFrame) -> np.ndarray:
        """
        Fit every numeric (include int and float) column in `_fit_column`.
        """
        if self.standard_scale:
            self._fit_column_scale(column_name, column_data)
            return
        return

    def _fit_column_scale(self, column_name: str, column_data: pd.DataFrame) -> np.ndarray:
        """
        Fit every numeric (include int and float) column using sklearn StandardScaler.
        """
        self.scalers[column_name] = StandardScaler()
        self.scalers[column_name].fit(column_data)

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert method to handle missing values in the input data.
        """
        logger.info('Converting data using NumericValueTransformer...')
        if len(self.int_columns) == 0 and len(self.float_columns) == 0:
            logger.info('Converting data using NumericValueTransformer... Finished (No column).')
            return
        processed_data = raw_data.copy()
        for each_col in list(self.int_columns) + list(self.float_columns):
            processed_col = self._covert_column(each_col, processed_data[[each_col]])
            processed_data[each_col] = processed_col
        logger.info('Converting data using NumericValueTransformer... Finished.')
        return processed_data

    def _covert_column(self, column_name: str, column_data: pd.DataFrame):
        """
        Convert every numeric (include int and float) column.
        """
        if self.standard_scale:
            return self._covert_column_scale(column_name=column_name, column_data=column_data)
        pass

    def _covert_column_scale(self, column_name: str, column_data: pd.DataFrame):
        """
        Convert every numeric (include int and float) column using sklearn StandardScaler.
        """
        scaled_data = self.scalers[column_name].transform(column_data)
        return scaled_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse convert method, convert generated data into processed data.
        """
        for each_col in list(self.int_columns) + list(self.float_columns):
            processed_col = self._reverse_convert_column(each_col, processed_data[[each_col]])
            processed_data[each_col] = processed_col
        logger.info('Data reverse-converted by NumericValueTransformer (No Action).')
        return processed_data

    def _reverse_convert_column(self, column_name: str, column_data: pd.DataFrame):
        """
        Reverse convert method for each column.
        """
        if self.standard_scale:
            return self._reverse_convert_column_scale(column_name=column_name, column_data=column_data)
        return

    def _reverse_convert_column_scale(self, column_name: str, column_data: pd.DataFrame):
        """
        Reverse convert method for input column using scale method.
        """
        reverse_converted_data = self.scalers[column_name].inverse_transform(column_data)
        return reverse_converted_data
    pass

def __init__(self):
    self.int_columns = set()
    self.float_columns = set()
    self.scalers = {}

def fit(self, metadata: Metadata | None=None, tabular_data: DataLoader | pd.DataFrame=None, **kwargs: dict[str, Any]):
    """
        The fit method.

        Data columns of int and float types need to be recorded here (Get data from metadata).
        """
    for each_col in metadata.int_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'int':
            self.int_columns.add(each_col)
            continue
        if metadata.get_column_data_type(each_col) == 'id':
            self.int_columns.add(each_col)
    for each_col in metadata.float_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'float':
            self.float_columns.add(each_col)
    if len(self.int_columns) == 0 and len(self.float_columns) == 0:
        logger.info('NumericValueTransformer Fitted (No numeric columns).')
        return
    for each_col in list(self.int_columns) + list(self.float_columns):
        self._fit_column(each_col, tabular_data[[each_col]])
    self.fitted = True
    logger.info('NumericValueTransformer Fitted.')

def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
    """
        Reverse convert method, convert generated data into processed data.
        """
    for each_col in list(self.int_columns) + list(self.float_columns):
        processed_col = self._reverse_convert_column(each_col, processed_data[[each_col]])
        processed_data[each_col] = processed_col
    logger.info('Data reverse-converted by NumericValueTransformer (No Action).')
    return processed_data

class ConstValueTransformer(Transformer):
    """
    A transformer that replaces the input with a constant value.

    This class is used to transform any input data into a predefined constant value.
    It is particularly useful in scenarios where a consistent output is required regardless of the input.

    Attributes:
        const_value (dict[Any]): The constant value that will be returned.
    """
    const_columns: list
    const_values: dict[Any, Any]

    def __init__(self):
        self.const_columns = []
        self.const_values = {}

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the transformer.

        This method processes the metadata to identify columns that should be replaced with a constant value.
        It updates the internal state of the transformer with the columns and their corresponding constant values.

        Args:
            metadata (Metadata | None): The metadata object containing information about the columns and their data types.
            **kwargs (dict[str, Any]): Additional keyword arguments.

        Returns:
            None
        """
        for each_col in metadata.column_list:
            if metadata.get_column_data_type(each_col) == 'const':
                self.const_columns.append(each_col)
        logger.info('ConstValueTransformer Fitted.')
        self.fitted = True

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert method to handle missing values in the input data by replacing specified columns with constant values.

        This method iterates over the columns identified for replacement with constant values and removes them from the input DataFrame.
        The removal is based on the columns specified during the fitting process.

        Args:
            raw_data (pd.DataFrame): The input DataFrame containing the data to be processed.

        Returns:
            pd.DataFrame: A DataFrame with the specified columns removed.
        """
        processed_data = copy.deepcopy(raw_data)
        logger.info('Converting data using ConstValueTransformer...')
        for each_col in self.const_columns:
            if each_col not in self.const_values.keys():
                self.const_values[each_col] = processed_data[each_col].unique()[0]
            processed_data = self.remove_columns(processed_data, [each_col])
        logger.info('Converting data using ConstValueTransformer... Finished.')
        return processed_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse_convert method for the transformer.

        This method restores the original columns that were replaced with constant values during the conversion process.
        It iterates over the columns identified for replacement with constant values and adds them back to the DataFrame
        with the predefined constant values.

        Args:
            processed_data (pd.DataFrame): The input DataFrame containing the processed data.

        Returns:
            pd.DataFrame: A DataFrame with the original columns restored, filled with their corresponding constant values.
        """
        df_length = processed_data.shape[0]
        for each_col_name in self.const_columns:
            each_value = self.const_values[each_col_name]
            each_const_col = [each_value for _ in range(df_length)]
            each_const_df = pd.DataFrame({each_col_name: each_const_col})
            processed_data = self.attach_columns(processed_data, each_const_df)
        logger.info('Data reverse-converted by ConstValueTransformer.')
        return processed_data

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the transformer.

        This method processes the metadata to identify columns that should be replaced with a constant value.
        It updates the internal state of the transformer with the columns and their corresponding constant values.

        Args:
            metadata (Metadata | None): The metadata object containing information about the columns and their data types.
            **kwargs (dict[str, Any]): Additional keyword arguments.

        Returns:
            None
        """
    for each_col in metadata.column_list:
        if metadata.get_column_data_type(each_col) == 'const':
            self.const_columns.append(each_col)
    logger.info('ConstValueTransformer Fitted.')
    self.fitted = True

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Convert method to handle missing values in the input data by replacing specified columns with constant values.

        This method iterates over the columns identified for replacement with constant values and removes them from the input DataFrame.
        The removal is based on the columns specified during the fitting process.

        Args:
            raw_data (pd.DataFrame): The input DataFrame containing the data to be processed.

        Returns:
            pd.DataFrame: A DataFrame with the specified columns removed.
        """
    processed_data = copy.deepcopy(raw_data)
    logger.info('Converting data using ConstValueTransformer...')
    for each_col in self.const_columns:
        if each_col not in self.const_values.keys():
            self.const_values[each_col] = processed_data[each_col].unique()[0]
        processed_data = self.remove_columns(processed_data, [each_col])
    logger.info('Converting data using ConstValueTransformer... Finished.')
    return processed_data

class FixedCombinationTransformer(Transformer):
    """
    A transformer that handles columns with fixed combinations in a DataFrame.

    This transformer goal to auto identifies and processes columns that have fixed relationships (high covariance) in
    a given DataFrame.

    The relationships between columns include:
      - Numerical function relationships: assess them based on covariance between the columns.
      - Categorical mapping relationships: check for duplicate values for each column.

    Note that we support one-to-one mappings between columns now, and each corresponding relationship will not
    include duplicate columns.

    For example:
    we detect that,
    1 numerical relationship: (key1, Value1, Value2)
    3 one-to-one relationships: (key1, Key2) , (Category1, Category2)

    | Key1 | Key2 | Category1 | Category2 | Value1 | Value2 |
    | :--: | :--: | :-------: | :-------: | :----: | :----: |
    |  1   |  A   |   1001   |   Apple   |   10   |   20   |
    |  2   |  B   |   1002   | Broccoli  |   15   |   30   |
    |  2   |  B   |   1001   |  Apple   |   20   |   20   |
    """
    fixed_combinations: dict[str, set[str]]
    '\n    A dictionary mapping column names to sets of column names that have fixed relationships with them.\n    '
    simplified_fixed_combinations: dict[str, set[str]]
    '\n    A dictionary mapping column names to sets of column names that have fixed relationships with them.\n    '
    column_mappings: dict[(str, str), dict[str, str]]
    '\n    A dictionary mapping tuples of column names to dictionaries of value mappings.\n    '
    is_been_specified: bool
    "\n    A boolean that flag if exist specific combinations by user.\n    If true, needn't running this auto detect transform.\n    "

    def __init__(self):
        super().__init__()
        self.fixed_combinations: dict[str, set[str]] = {}
        self.simplified_fixed_combinations: dict[str, set[str]] = {}
        self.column_mappings: dict[(str, str), dict[str, str]] = {}
        self.is_been_specified = False

    @property
    def is_exist_fixed_combinations(self) -> bool:
        """
        A boolean that flag if inspector have inspected some fixed combinations.
        If False, needn't running this auto detect transform.
        """
        return bool(self.fixed_combinations)

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """Fit the transformer and save the relationships between columns.

        Args:
            metadata (Metadata): Metadata object
        """
        if metadata.get('specific_combinations'):
            logger.info('Fit data using FixedCombinationTransformer(been specified)... Finished (No action).')
            self.is_been_specified = True
            self.fitted = True
            return
        self.fixed_combinations = metadata.get('fixed_combinations') or dict()
        if not self.is_exist_fixed_combinations:
            logger.info('Fit data using FixedCombinationTransformer(not existed)... Finished (No action).')
            self.fitted = True
            return
        simplified_fixed_combinations = {}
        seen = set()
        if not isinstance(self.fixed_combinations, dict):
            raise TypeError('fixed_combinations should be a dict, rather than {}'.format(type(self.fixed_combinations).__name__))
        for base_col, related_cols in self.fixed_combinations.items():
            combination = frozenset([base_col]) | frozenset(related_cols)
            if combination not in seen:
                simplified_fixed_combinations[base_col] = related_cols
                seen.add(combination)
        self.simplified_fixed_combinations = simplified_fixed_combinations
        self.has_column_mappings = False
        self.fitted = True

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Convert the input DataFrame by identifying and storing fixed column relationships.

        This method analyzes the relationships between columns specified in simplified_fixed_combinations
        and stores their value mappings. The mappings are only computed once for the first batch of data
        to optimize performance.

        NOTE:
            TODO-Enhance-Refactor Inspector by chain-of-responsibility, base one-to-one on Identified discrete_columns.
            The current implementation has space for optimization:
            - The column_mappings definition depends on the first batch of data from the DataLoader
            - This might miss some edge cases where column relationships are very comprehensive
              (e.g., some column correspondences might only appear in later batches)
            - While processing each batch separately could avoid this issue, it would incur
              significant performance overhead
            - The current function is sufficient for most scenarios
            - In the future, we may introduce parameters to control these strategies

        Args:
            raw_data (pd.DataFrame): The input DataFrame to be processed

        Returns:
            pd.DataFrame: The processed DataFrame (unchanged in this implementation)
        """
        if self.is_been_specified:
            logger.info('Converting data using FixedCombinationTransformer(been specified)... Finished (No action).')
            return raw_data
        if not self.is_exist_fixed_combinations:
            logger.info('Converting data using FixedCombinationTransformer(not existed)... Finished (No action).')
            return raw_data
        if self.has_column_mappings:
            logger.info('Converting data using FixedCombinationTransformer... Finished (No action).')
            return raw_data
        logger.info('Converting data using FixedCombinationTransformer... ')
        for base_col, related_cols in self.simplified_fixed_combinations.items():
            if base_col not in raw_data.columns:
                continue
            base_values = raw_data[base_col].unique()
            for related_col in related_cols:
                if related_col not in raw_data.columns:
                    continue
                value_mapping = {}
                for base_val in base_values:
                    related_vals = raw_data[raw_data[base_col] == base_val][related_col].unique()
                    if len(related_vals) == 1:
                        value_mapping[base_val] = related_vals[0]
                if value_mapping and (not any((pd.isna(v) for v in value_mapping.values()))):
                    self.column_mappings[base_col, related_col] = value_mapping
                    logger.debug(f'Saved mapping relationship between {base_col} and {related_col}')
        logger.info('Converting data using FixedCombinationTransformer... Finished.')
        self.has_column_mappings = True
        return raw_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverses the conversion process applied by the FixedCombinationTransformer.

        This method takes the processed DataFrame and uses the saved column mappings
        to restore the original values based on the relationships defined during the
        conversion process. If a base value does not have a corresponding related value,
        a random base value is selected to ensure that the DataFrame remains consistent.

        Args:
            processed_data (pd.DataFrame): The input DataFrame containing the processed data.

        Returns:
            pd.DataFrame: The DataFrame with original values restored based on the defined mappings.
        """
        if self.is_been_specified:
            logger.info('Reverse converting data using FixedCombinationTransformer(been specified)... Finished (No action).')
            return processed_data
        if not self.is_exist_fixed_combinations:
            logger.info('Reverse converting data using FixedCombinationTransformer(not existed)... Finished (No action).')
            return processed_data
        result_df = processed_data.copy()
        logger.info('Reverse converting data using FixedCombinationTransformer...')
        for (base_col, related_col), mapping in self.column_mappings.items():
            if base_col not in result_df.columns or related_col not in result_df.columns:
                continue

            def replace_row(row):
                base_val = row[base_col]
                if base_val in mapping:
                    new_related_val = mapping[base_val]
                    return pd.Series({base_col: base_val, related_col: new_related_val})
                else:
                    new_base_val = random.choice(list(mapping.keys()))
                    new_related_val = mapping[new_base_val]
                    return pd.Series({base_col: new_base_val, related_col: new_related_val})
            replaced = result_df.apply(replace_row, axis=1)
            result_df[base_col] = replaced[base_col]
            result_df[related_col] = replaced[related_col]
        logger.info('Reverse converting data using FixedCombinationTransformer... Finished.')
        return result_df

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """Fit the transformer and save the relationships between columns.

        Args:
            metadata (Metadata): Metadata object
        """
    if metadata.get('specific_combinations'):
        logger.info('Fit data using FixedCombinationTransformer(been specified)... Finished (No action).')
        self.is_been_specified = True
        self.fitted = True
        return
    self.fixed_combinations = metadata.get('fixed_combinations') or dict()
    if not self.is_exist_fixed_combinations:
        logger.info('Fit data using FixedCombinationTransformer(not existed)... Finished (No action).')
        self.fitted = True
        return
    simplified_fixed_combinations = {}
    seen = set()
    if not isinstance(self.fixed_combinations, dict):
        raise TypeError('fixed_combinations should be a dict, rather than {}'.format(type(self.fixed_combinations).__name__))
    for base_col, related_cols in self.fixed_combinations.items():
        combination = frozenset([base_col]) | frozenset(related_cols)
        if combination not in seen:
            simplified_fixed_combinations[base_col] = related_cols
            seen.add(combination)
    self.simplified_fixed_combinations = simplified_fixed_combinations
    self.has_column_mappings = False
    self.fitted = True

class SpecificCombinationTransformer(Transformer):
    """
    A transformer used to handle specific combinations of columns in tabular data.

    The relationships between columns can be quite complex. Currently, we introduced `FixedCombinationTransformer`
    is not capable of comprehensive automatic detection. This transformer allows users to manually specify the
    mapping relationships between columns, specifically for multiple corresponding relationships. Users can define
    multiple groups, with each group supporting multiple columns. The transformer will record the combination values
    of each column, and in the `reverse_convert()`, it will restore any mismatched combinations from the recorded
    relationships.

    For example:

    | Category A | Category B | Category C | Category D | Category E |
    | :--------: | :--------: | :--------: | :--------: | :--------: |
    |     A1     |     B1     |     C1     |     D1     |     E1     |
    |     A1     |     B1     |     C2     |     D2     |     E2     |
    |     A2     |     B2     |     C1     |     D1     |     E3     |

    Here user can specific combination like (Category A, Category B), (Category C, Category D, Category E).

    For now, the `specific_combinations` passing by `Metadata`

    """
    column_groups: List[Set[str]]
    '\n    Define a list where each element is a set containing string type column names\n    '
    mappings: Dict[frozenset, pd.DataFrame]
    '\n    Define a dictionary variable `mappings` where the keys are frozensets and the values are pandas DataFrame objects\n    '
    specified: bool
    '\n    Define a boolean that flag if user specified the combination, if true, that handle the `specific_combinations`\n    '

    def __init__(self):
        self.column_groups: List[Set[str]] = []
        self.mappings: Dict[frozenset, pd.DataFrame] = {}
        self.specified = False

    def fit(self, metadata: Metadata | None=None, tabular_data: DataLoader | pd.DataFrame=None):
        """
        Study the combination relationships and value mapping of columns.

        Args:
            metadata: Metadata containing information about specific column combinations.
            tabular_data: The tabular data to be fitted, can be a DataLoader object or a pandas DataFrame.
        """
        specific_combinations = metadata.get('specific_combinations')
        if specific_combinations is None or len(specific_combinations) == 0:
            logger.info('Fit data using SpecificCombinationTransformer(No specified)... Finished (No action).')
            self.fitted = True
            return
        df = tabular_data
        self.column_groups = [set(cols) for cols in specific_combinations]
        for group in self.column_groups:
            group_df = df[list(group)].drop_duplicates()
            self.mappings[frozenset(group)] = group_df
        self.fitted = True
        self.specified = True
        logger.info('SpecificCombinationTransformer Fitted.')

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert the raw data based on the learned mapping relationships.

        Args:
           raw_data: The raw data to be converted.

        Returns:
           The converted data.
        """
        if not self.specified:
            logger.info('Converting data using SpecificCombinationTransformer(No specified)... Finished (No action).')
            return super().convert(raw_data)
        logger.info('SpecificCombinationTransformer convert doing nothing...')
        return super().convert(raw_data)

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse convert the processed data to ensure it conforms to the original format.

        Args:
            processed_data: The processed data to be reverse converted.

        Returns:
            The reverse converted data.
        """
        if not self.specified:
            logger.info('Reverse converting data using SpecificCombinationTransformer(No specified)... Finished (No action).')
            return processed_data
        result_df = processed_data.copy()
        n_rows = len(result_df)
        for group in self.column_groups:
            group_mapping = self.mappings[frozenset(group)]
            group_cols = list(group)
            random_indices = np.random.choice(len(group_mapping), size=n_rows)
            random_mappings = group_mapping.iloc[random_indices]
            result_df[group_cols] = random_mappings[group_cols].values
        return result_df

def fit(self, metadata: Metadata | None=None, tabular_data: DataLoader | pd.DataFrame=None):
    """
        Study the combination relationships and value mapping of columns.

        Args:
            metadata: Metadata containing information about specific column combinations.
            tabular_data: The tabular data to be fitted, can be a DataLoader object or a pandas DataFrame.
        """
    specific_combinations = metadata.get('specific_combinations')
    if specific_combinations is None or len(specific_combinations) == 0:
        logger.info('Fit data using SpecificCombinationTransformer(No specified)... Finished (No action).')
        self.fitted = True
        return
    df = tabular_data
    self.column_groups = [set(cols) for cols in specific_combinations]
    for group in self.column_groups:
        group_df = df[list(group)].drop_duplicates()
        self.mappings[frozenset(group)] = group_df
    self.fitted = True
    self.specified = True
    logger.info('SpecificCombinationTransformer Fitted.')

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Convert the raw data based on the learned mapping relationships.

        Args:
           raw_data: The raw data to be converted.

        Returns:
           The converted data.
        """
    if not self.specified:
        logger.info('Converting data using SpecificCombinationTransformer(No specified)... Finished (No action).')
        return super().convert(raw_data)
    logger.info('SpecificCombinationTransformer convert doing nothing...')
    return super().convert(raw_data)

def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
    """
        Reverse convert the processed data to ensure it conforms to the original format.

        Args:
            processed_data: The processed data to be reverse converted.

        Returns:
            The reverse converted data.
        """
    if not self.specified:
        logger.info('Reverse converting data using SpecificCombinationTransformer(No specified)... Finished (No action).')
        return processed_data
    result_df = processed_data.copy()
    n_rows = len(result_df)
    for group in self.column_groups:
        group_mapping = self.mappings[frozenset(group)]
        group_cols = list(group)
        random_indices = np.random.choice(len(group_mapping), size=n_rows)
        random_mappings = group_mapping.iloc[random_indices]
        result_df[group_cols] = random_mappings[group_cols].values
    return result_df

class OutlierTransformer(Transformer):
    """
    A transformer class to handle outliers in the data by converting them to specified fill values.

    Attributes:
        int_columns (set): A set of column names that contain integer values.
        int_outlier_fill_value (int): The value to fill in for outliers in integer columns. Default is 0.
        float_columns (set): A set of column names that contain float values.
        float_outlier_fill_value (float): The value to fill in for outliers in float columns. Default is 0.
    """
    int_columns: set
    '\n    set: A set of column names that contain integer values. These columns will have their outliers replaced by `int_outlier_fill_value`.\n    '
    int_outlier_fill_value: int
    '\n    int: The value to fill in for outliers in integer columns. Default is 0.\n    '
    float_columns: set
    '\n    set: A set of column names that contain float values. These columns will have their outliers replaced by `float_outlier_fill_value`.\n    '
    float_outlier_fill_value: float
    '\n    float: The value to fill in for outliers in float columns. Default is 0.\n    '

    def __init__(self):
        self.int_columns = set()
        self.int_outlier_fill_value = 0
        self.float_columns = set()
        self.float_outlier_fill_value = float(0)

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the transformer.

        Records the names of integer and float columns from the metadata.

        Args:
            metadata (Metadata | None): The metadata object containing column type information.
            **kwargs: Additional keyword arguments.
        """
        for each_col in metadata.int_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'int':
                self.int_columns.add(each_col)
        for each_col in metadata.float_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'float':
                self.float_columns.add(each_col)
        self.fitted = True
        logger.info('OutlierTransformer Fitted.')

    def convert(self, raw_data: DataFrame) -> DataFrame:
        """
        Convert method to handle outliers in the input data by replacing them with specified fill values.

        Args:
            raw_data (DataFrame): The input DataFrame containing the data to be processed.

        Returns:
            DataFrame: The processed DataFrame with outliers replaced by fill values.
        """
        res = raw_data
        logger.info('Converting data using OutlierTransformer...')

        def convert_to_int(value):
            try:
                return int(value)
            except ValueError:
                return self.int_outlier_fill_value
        for each_col in self.int_columns:
            res[each_col] = res[each_col].apply(convert_to_int)

        def convert_to_float(value):
            try:
                return float(value)
            except ValueError:
                return self.float_outlier_fill_value
        for each_col in self.float_columns:
            res[each_col] = res[each_col].apply(convert_to_float)
        logger.info('Converting data using OutlierTransformer... Finished.')
        return res

    def reverse_convert(self, processed_data: DataFrame) -> DataFrame:
        """
        Reverse_convert method for the transformer (No action for OutlierTransformer).

        Args:
            processed_data (DataFrame): The processed DataFrame.

        Returns:
            DataFrame: The same processed DataFrame.
        """
        logger.info('Data reverse-converted by OutlierTransformer (No Action).')
        return processed_data

def __init__(self):
    self.int_columns = set()
    self.int_outlier_fill_value = 0
    self.float_columns = set()
    self.float_outlier_fill_value = float(0)

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the transformer.

        Records the names of integer and float columns from the metadata.

        Args:
            metadata (Metadata | None): The metadata object containing column type information.
            **kwargs: Additional keyword arguments.
        """
    for each_col in metadata.int_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'int':
            self.int_columns.add(each_col)
    for each_col in metadata.float_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'float':
            self.float_columns.add(each_col)
    self.fitted = True
    logger.info('OutlierTransformer Fitted.')

def convert_to_float(value):
    try:
        return float(value)
    except ValueError:
        return self.float_outlier_fill_value

def reverse_convert(self, processed_data: DataFrame) -> DataFrame:
    """
        Reverse_convert method for the transformer (No action for OutlierTransformer).

        Args:
            processed_data (DataFrame): The processed DataFrame.

        Returns:
            DataFrame: The same processed DataFrame.
        """
    logger.info('Data reverse-converted by OutlierTransformer (No Action).')
    return processed_data

class NonValueTransformer(Transformer):
    """
    A transformer class designed to handle missing values in a DataFrame. It can either drop rows with missing values or fill them with specified values.

    Attributes:
        int_columns (set): A set of column names that contain integer values.
        float_columns (set): A set of column names that contain float values.
        column_list (list): A list of all column names in the DataFrame.
        fill_na_value_int (int): The value to fill missing integer values with. Default is 0.
        fill_na_value_float (float): The value to fill missing float values with. Default is 0.0.
        fill_na_value_default (str): The value to fill missing values for non-numeric columns with. Default is 'NAN_VALUE'.
        drop_na (bool): A flag indicating whether to drop rows with missing values. If True, rows with missing values are dropped. If False, missing values are filled with specified values. Default is False.
    """
    int_columns: set
    '\n    A set of column names that contain integer values.\n    '
    float_columns: set
    '\n    A set of column names that contain float values.\n    '
    column_list: list
    '\n    A list of all column names in the DataFrame.\n    '
    fill_na_value_int: int
    '\n    The value to fill missing integer values with. Default is 0.\n    '
    fill_na_value_float: float
    '\n    The value to fill missing float values with. Default is 0.0.\n    '
    fill_na_value_default: str
    "\n    The value to fill missing values for non-numeric columns with. Default is 'NAN_VALUE'.\n    "
    drop_na: bool
    '\n    A boolean flag indicating whether to drop rows with missing values or fill them with `fill_na_value`.\n\n    If `True`, rows with missing values will be dropped.\n    If `False`, missing values will be filled with `fill_na_value`.\n\n    Currently, the default setting is False, which means rows with missing values are not dropped.\n    '

    def __init__(self):
        self.int_columns = set()
        self.float_columns = set()
        self.column_list = []
        self.fill_na_value_int = 0
        self.fill_na_value_float = 0.0
        self.fill_na_value_default = 'NAN_VALUE'
        self.drop_na = False

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the transformer.
        """
        logger.info('NonValueTransformer Fitted.')
        for key, value in kwargs.items():
            if key == 'drop_na':
                if not isinstance(value, str):
                    raise ValueError('fill_na_value must be of type <str>')
                self.drop_na = value
        for each_col in metadata.int_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'int':
                self.int_columns.add(each_col)
        logger.info(f'NonValueTransformer get int columns: {self.int_columns}.')
        for each_col in metadata.float_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'float':
                self.float_columns.add(each_col)
        logger.info(f'NonValueTransformer get float columns: {self.float_columns}.')
        self.column_list = metadata.column_list
        logger.info(f'NonValueTransformer get column list from metadata: {self.column_list}.')
        self.fitted = True

    def convert(self, raw_data: DataFrame) -> DataFrame:
        """
        Convert method to handle missing values in the input data.
        """
        logger.info('Converting data using NonValueTransformer...')
        if self.drop_na:
            logger.info('Converting data using NonValueTransformer... Finished (Drop NA).')
            return raw_data.dropna()
        res = raw_data
        for each_col in self.int_columns:
            res[each_col] = res[each_col].fillna(self.fill_na_value_int)
        for each_col in self.float_columns:
            res[each_col] = res[each_col].fillna(self.fill_na_value_float)
        for each_col in self.column_list:
            if each_col in self.int_columns or each_col in self.float_columns:
                continue
            res[each_col] = res[each_col].fillna(self.fill_na_value_default)
        logger.info('Converting data using NonValueTransformer... Finished.')
        return res

    def reverse_convert(self, processed_data: DataFrame) -> DataFrame:
        """
        Reverse_convert method for the transformer.

        Does not require any action.
        """

        def replace_nan_value(df):
            """
            Scans all rows and columns in the DataFrame and replaces all cells with the value "NAN_VALUE", which is self.fill_na_value_default, with an empty string.

            Parameters:
            df (pd.DataFrame): The input DataFrame.

            Returns:
            pd.DataFrame: The DataFrame after replacement.
            """
            df_replaced = df.replace(self.fill_na_value_default, '')
            return df_replaced
        logger.info('Data reverse-converted by NonValueTransformer.')
        return replace_nan_value(processed_data)
    pass

def __init__(self):
    self.int_columns = set()
    self.float_columns = set()
    self.column_list = []
    self.fill_na_value_int = 0
    self.fill_na_value_float = 0.0
    self.fill_na_value_default = 'NAN_VALUE'
    self.drop_na = False

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the transformer.
        """
    logger.info('NonValueTransformer Fitted.')
    for key, value in kwargs.items():
        if key == 'drop_na':
            if not isinstance(value, str):
                raise ValueError('fill_na_value must be of type <str>')
            self.drop_na = value
    for each_col in metadata.int_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'int':
            self.int_columns.add(each_col)
    logger.info(f'NonValueTransformer get int columns: {self.int_columns}.')
    for each_col in metadata.float_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'float':
            self.float_columns.add(each_col)
    logger.info(f'NonValueTransformer get float columns: {self.float_columns}.')
    self.column_list = metadata.column_list
    logger.info(f'NonValueTransformer get column list from metadata: {self.column_list}.')
    self.fitted = True

def reverse_convert(self, processed_data: DataFrame) -> DataFrame:
    """
        Reverse_convert method for the transformer.

        Does not require any action.
        """

    def replace_nan_value(df):
        """
            Scans all rows and columns in the DataFrame and replaces all cells with the value "NAN_VALUE", which is self.fill_na_value_default, with an empty string.

            Parameters:
            df (pd.DataFrame): The input DataFrame.

            Returns:
            pd.DataFrame: The DataFrame after replacement.
            """
        df_replaced = df.replace(self.fill_na_value_default, '')
        return df_replaced
    logger.info('Data reverse-converted by NonValueTransformer.')
    return replace_nan_value(processed_data)

class EmptyTransformer(Transformer):
    """
    A transformer that handles empty columns in a DataFrame.

    This transformer identifies and processes columns that contain no data (empty columns) in a given DataFrame.
    It can remove these columns during the conversion process and restore them during the reverse conversion process.

    Attributes:
        empty_columns (list): A list of column names that are identified as empty.

    Methods:
        fit(metadata: Metadata | None = None, **kwargs: dict[str, Any]):
            Fits the transformer to the data by identifying empty columns based on provided metadata.
        convert(raw_data: pd.DataFrame) -> pd.DataFrame:
            Converts the raw data by removing the identified empty columns.
        reverse_convert(processed_data: pd.DataFrame) -> pd.DataFrame:
            Reverses the conversion by restoring the previously removed empty columns.
    """
    empty_columns: set
    '\n    Set of column names that are identified as empty. This attribute is populated during the fitting process\n    and is used to remove these columns during the conversion process and restore them during the reverse conversion process.\n    '

    def __init__(self):
        self.empty_columns = set()

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the transformer.
        Remember the empty_columns from all columns.

        Args:
            metadata (Metadata | None): The metadata containing information about the data, including empty columns.
            **kwargs (dict[str, Any]): Additional keyword arguments.

        Returns:
            None
        """
        for each_col in metadata.get('empty_columns'):
            if metadata.get_column_data_type(each_col) == 'empty':
                self.empty_columns.add(each_col)
        logger.info('EmptyTransformer Fitted.')
        self.fitted = True
        return

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the raw data by removing the identified empty columns.

        Args:
            raw_data (pd.DataFrame): The input DataFrame containing the raw data.

        Returns:
            pd.DataFrame: The processed DataFrame with empty columns removed.
        """
        processed_data = raw_data
        logger.info('Converting data using EmptyTransformer...')
        for each_col in self.empty_columns:
            processed_data = self.remove_columns(processed_data, [each_col])
        logger.info('Converting data using EmptyTransformer... Finished (No action).')
        return processed_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverses the conversion by restoring the previously removed empty columns.

        Args:
            processed_data (pd.DataFrame): The input DataFrame containing the processed data.

        Returns:
            pd.DataFrame: The DataFrame with previously removed empty columns restored.
        """
        if not self.fitted or not self.empty_columns:
            return processed_data
        for col_name in self.empty_columns:
            empty_df = pd.DataFrame({col_name: [None] * len(processed_data)})
            processed_data = self.attach_columns(processed_data, empty_df)
        return processed_data

def __init__(self):
    self.empty_columns = set()

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the transformer.
        Remember the empty_columns from all columns.

        Args:
            metadata (Metadata | None): The metadata containing information about the data, including empty columns.
            **kwargs (dict[str, Any]): Additional keyword arguments.

        Returns:
            None
        """
    for each_col in metadata.get('empty_columns'):
        if metadata.get_column_data_type(each_col) == 'empty':
            self.empty_columns.add(each_col)
    logger.info('EmptyTransformer Fitted.')
    self.fitted = True
    return

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Converts the raw data by removing the identified empty columns.

        Args:
            raw_data (pd.DataFrame): The input DataFrame containing the raw data.

        Returns:
            pd.DataFrame: The processed DataFrame with empty columns removed.
        """
    processed_data = raw_data
    logger.info('Converting data using EmptyTransformer...')
    for each_col in self.empty_columns:
        processed_data = self.remove_columns(processed_data, [each_col])
    logger.info('Converting data using EmptyTransformer... Finished (No action).')
    return processed_data

class ColumnOrderTransformer(Transformer):
    """
    A transformer that rearranges the columns of a DataFrame to a specified order.

    Attributes:
        column_list (list): The list of column names in the desired order.

    Methods:
        fit(metadata: Metadata | None = None, **kwargs: dict[str, Any]): Fits the transformer by remembering the order of the columns.
        convert(raw_data: pd.DataFrame) -> pd.DataFrame: Converts the input DataFrame by rearranging its columns.
        reverse_convert(processed_data: pd.DataFrame) -> pd.DataFrame: Reverse-converts the processed DataFrame by rearranging its columns back to their original order.
        rearrange_columns(column_list, processed_data): Rearranges the columns of a DataFrame according to the provided column list.
    """
    column_list: list
    "\n    The list of tabular data's columns.\n    "

    def __init__(self):
        self.column_list = None

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the transformer.

        Remember the order of the columns.
        """
        self.column_list = list(metadata.column_list)
        logger.info('ColumnOrderTransformer Fitted.')
        self.fitted = True
        return

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert method to handle missing values in the input data.
        """
        logger.info('Converting data using ColumnOrderTransformer...')
        logger.info('Converting data using ColumnOrderTransformer... Finished (No action).')
        return raw_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse_convert method for the transformer.
        """
        res = self.rearrange_columns(self.column_list, processed_data)
        logger.info('Data reverse-converted by ColumnOrderTransformer.')
        return res

    @staticmethod
    def rearrange_columns(column_list, processed_data):
        """
        This method rearranges the columns of a given DataFrame according to the provided column list.

        Any columns in the DataFrame that are not in the column list are dropped.

        Args:
            - column_list (list): A list of column names in the order they should appear in the output DataFrame.
            - processed_data (pd.DataFrame): The DataFrame to be rearranged.

        Returns:
            - result_data (pd.DataFrame): The rearranged DataFrame.
        """
        result_data = processed_data.reindex(columns=column_list)
        return result_data

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the transformer.

        Remember the order of the columns.
        """
    self.column_list = list(metadata.column_list)
    logger.info('ColumnOrderTransformer Fitted.')
    self.fitted = True
    return

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Convert method to handle missing values in the input data.
        """
    logger.info('Converting data using ColumnOrderTransformer...')
    logger.info('Converting data using ColumnOrderTransformer... Finished (No action).')
    return raw_data

def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
    """
        Reverse_convert method for the transformer.
        """
    res = self.rearrange_columns(self.column_list, processed_data)
    logger.info('Data reverse-converted by ColumnOrderTransformer.')
    return res

class DatetimeFormatter(Formatter):
    """
    A class for formatting datetime columns in a pandas DataFrame.

    DatetimeFormatter is designed to handle the conversion of datetime columns to timestamp format and vice versa.
    It uses metadata to identify datetime columns and their corresponding datetime formats.

    Attributes:
        datetime_columns (list): List of column names that are of datetime type.
        datetime_formats (dict): Dictionary with column names as keys and datetime formats as values.
        dead_columns (list): List of column names that are no longer needed or to be removed.
        fitted (bool): Indicates whether the formatter has been fitted.

    Methods:
        fit(metadata: Metadata | None = None, **kwargs: dict[str, Any]): Fits the formatter by recording the datetime columns and their formats.
        convert(raw_data: pd.DataFrame) -> pd.DataFrame: Converts datetime columns in raw_data to timestamp format.
        reverse_convert(processed_data: pd.DataFrame) -> pd.DataFrame: Converts timestamp columns in processed_data back to datetime format.
    """
    datetime_columns: list
    '\n    List to store the columns that are of datetime type.\n    '
    datetime_formats: Dict
    '\n    Dictionary to store the datetime formats for each column, with default value as an empty string.\n    '
    dead_columns: list
    '\n    List to store columns that are no longer needed or to be removed.\n    '

    def __init__(self):
        self.fitted = False
        self.datetime_columns = []
        self.datetime_formats = defaultdict(str)
        self.dead_columns = []

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for datetime formatter, the datetime column and datetime format need to be recorded.

        If there is a column without format, the default format will be used for output (this may cause some problems).

        Formatter need to use metadata to record which columns belong to datetime type, and convert timestamp back to datetime type during post-processing.
        """
        self.datetime_formats = metadata.get('datetime_format')
        datetime_columns = []
        dead_columns = []
        meta_datetime_columns = metadata.get('datetime_columns')
        for each_col in meta_datetime_columns:
            if each_col in self.datetime_formats.keys():
                datetime_columns.append(each_col)
            else:
                dead_columns.append(each_col)
                logger.warning(f'Column {each_col} has no datetime_format, DatetimeFormatter will REMOVE this column！')
        if not set(datetime_columns) - set(metadata.discrete_columns):
            metadata.change_column_type(datetime_columns, 'discrete', 'datetime')
        metadata.remove_column(dead_columns)
        self.datetime_columns = datetime_columns
        self.dead_columns = dead_columns
        logger.info('DatetimeFormatter Fitted.')
        self.fitted = True
        return

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert method to convert datetime samples into timestamp.

        Args:
            - raw_data (pd.DataFrame): Unprocessed table data
        """
        if len(self.datetime_columns) == 0:
            logger.info('Converting data using DatetimeFormatter... Finished (No datetime columns).')
            return raw_data
        for each_col in self.dead_columns:
            raw_data = self.remove_columns(raw_data, [each_col])
            logger.warning(f'Column {each_col} was removed because lack of format info.')
        logger.info('Converting data using DatetimeFormatter...')
        res_data = self.convert_datetime_columns(self.datetime_columns, self.datetime_formats, raw_data)
        logger.info('Converting data using DatetimeFormatter... Finished.')
        return res_data

    @staticmethod
    def convert_datetime_columns(datetime_column_list, datetime_formats, processed_data):
        """
        Convert datetime columns in processed_data from string to timestamp (int)

        Args:
            - datetime_column_list (list): List of columns that are date time type
            - processed_data (pd.DataFrame): Processed table data

        Returns:
            - result_data (pd.DataFrame): Processed table data with datetime columns converted to timestamp
        """

        def datetime_formatter(each_value, datetime_format):
            """
            convert each single column datetime string to timestamp int value.
            """
            try:
                datetime_obj = datetime.strptime(str(each_value), datetime_format)
                each_stamp = datetime.timestamp(datetime_obj)
            except Exception as e:
                logger.warning(f'An error occured when convert str to timestamp {e}, we set as mean.')
                logger.warning(f'Input parameters: ({str(each_value)}, {datetime_format})')
                logger.warning(f'Input type: ({type(each_value)}, {type(datetime_format)})')
                each_stamp = np.nan
            return each_stamp
        result_data: pd.DataFrame = processed_data.copy()
        for column in datetime_column_list:
            result_data[column] = result_data[column].apply(datetime_formatter, datetime_format=datetime_formats[column])
            result_data[column].fillna(result_data[column].mean(), inplace=True)
        return result_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        reverse_convert method for datetime formatter.

        Does not require any action.
        """
        if len(self.datetime_columns) == 0:
            logger.info('Data reverse-converted by DatetimeFormatter (No datetime columns).')
            return processed_data
        logger.info('Data reverse-converting by DatetimeFormatter...')
        logger.info(f'parameters : {self.datetime_columns}, {self.datetime_formats}')
        result_data = self.convert_timestamp_to_datetime(self.datetime_columns, self.datetime_formats, processed_data)
        logger.info('Data reverse-converted by DatetimeFormatter... Finished.')
        return result_data

    @staticmethod
    def convert_timestamp_to_datetime(timestamp_column_list, format_dict, processed_data):
        """
        Convert timestamp columns to datetime format in a DataFrame.

        Parameters:
            - timestamp_column_list (list): List of column names in the DataFrame which are of timestamp type.
            - datetime_column_dict (dict): Dictionary with column names as keys and datetime format as values.
            - processed_data (pd.DataFrame): DataFrame containing the processed data.

        Returns:
            - result_data (pd.DataFrame): DataFrame with timestamp columns converted to datetime format.

        TODO:
            if the value <0, the result will be `No Datetime`, try to fix it.
        """

        def column_timestamp_formatter(each_stamp: int, timestamp_format: str) -> str:
            try:
                each_str = datetime.fromtimestamp(each_stamp).strftime(timestamp_format)
            except Exception as e:
                logger.debug(f'An error occured when convert timestamp to str {e}.')
                each_str = 'No Datetime'
            return each_str
        result_data = processed_data.copy()
        for column in timestamp_column_list:
            if column in result_data.columns:
                result_data[column] = result_data[column].apply(column_timestamp_formatter, timestamp_format=format_dict[column])
            else:
                logger.error(f"Column {column} not in processed data's column list!")
        return result_data

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for datetime formatter, the datetime column and datetime format need to be recorded.

        If there is a column without format, the default format will be used for output (this may cause some problems).

        Formatter need to use metadata to record which columns belong to datetime type, and convert timestamp back to datetime type during post-processing.
        """
    self.datetime_formats = metadata.get('datetime_format')
    datetime_columns = []
    dead_columns = []
    meta_datetime_columns = metadata.get('datetime_columns')
    for each_col in meta_datetime_columns:
        if each_col in self.datetime_formats.keys():
            datetime_columns.append(each_col)
        else:
            dead_columns.append(each_col)
            logger.warning(f'Column {each_col} has no datetime_format, DatetimeFormatter will REMOVE this column！')
    if not set(datetime_columns) - set(metadata.discrete_columns):
        metadata.change_column_type(datetime_columns, 'discrete', 'datetime')
    metadata.remove_column(dead_columns)
    self.datetime_columns = datetime_columns
    self.dead_columns = dead_columns
    logger.info('DatetimeFormatter Fitted.')
    self.fitted = True
    return

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Convert method to convert datetime samples into timestamp.

        Args:
            - raw_data (pd.DataFrame): Unprocessed table data
        """
    if len(self.datetime_columns) == 0:
        logger.info('Converting data using DatetimeFormatter... Finished (No datetime columns).')
        return raw_data
    for each_col in self.dead_columns:
        raw_data = self.remove_columns(raw_data, [each_col])
        logger.warning(f'Column {each_col} was removed because lack of format info.')
    logger.info('Converting data using DatetimeFormatter...')
    res_data = self.convert_datetime_columns(self.datetime_columns, self.datetime_formats, raw_data)
    logger.info('Converting data using DatetimeFormatter... Finished.')
    return res_data

def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
    """
        reverse_convert method for datetime formatter.

        Does not require any action.
        """
    if len(self.datetime_columns) == 0:
        logger.info('Data reverse-converted by DatetimeFormatter (No datetime columns).')
        return processed_data
    logger.info('Data reverse-converting by DatetimeFormatter...')
    logger.info(f'parameters : {self.datetime_columns}, {self.datetime_formats}')
    result_data = self.convert_timestamp_to_datetime(self.datetime_columns, self.datetime_formats, processed_data)
    logger.info('Data reverse-converted by DatetimeFormatter... Finished.')
    return result_data

class IntValueFormatter(Formatter):
    """
    Formatter class for handling Int values in pd.DataFrame.
    """
    int_columns: set
    '\n    List of column names that are of type int, populated by the fit method using metadata.\n    '

    def __init__(self):
        self.int_columns = set()

    def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
        """
        Fit method for the formatter.

        Formatter need to use metadata to record which columns belong to the int type, and convert them back to the int type during post-processing.
        """
        for each_col in metadata.int_columns:
            if each_col not in metadata.column_list:
                continue
            if metadata.get_column_data_type(each_col) == 'int':
                self.int_columns.add(each_col)
                continue
            if metadata.get_column_data_type(each_col) == 'id':
                self.int_columns.add(each_col)
        logger.info('IntValueFormatter Fitted.')
        self.fitted = True
        return

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        No action for convert.
        """
        logger.info('Converting data using IntValueFormatter... Finished  (No Action).')
        return raw_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        reverse_convert method for the formatter.

        Do format conversion for int columns.
        """
        for col in self.int_columns:
            if col in processed_data.columns:
                processed_data[col] = processed_data[col].astype(int)
            else:
                logger.error('Column {} not found in processed_data.'.format(col))
        logger.info('Data reverse-converted by IntValueFormatter.')
        return processed_data

def __init__(self):
    self.int_columns = set()

def fit(self, metadata: Metadata | None=None, **kwargs: dict[str, Any]):
    """
        Fit method for the formatter.

        Formatter need to use metadata to record which columns belong to the int type, and convert them back to the int type during post-processing.
        """
    for each_col in metadata.int_columns:
        if each_col not in metadata.column_list:
            continue
        if metadata.get_column_data_type(each_col) == 'int':
            self.int_columns.add(each_col)
            continue
        if metadata.get_column_data_type(each_col) == 'id':
            self.int_columns.add(each_col)
    logger.info('IntValueFormatter Fitted.')
    self.fitted = True
    return

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        No action for convert.
        """
    logger.info('Converting data using IntValueFormatter... Finished  (No Action).')
    return raw_data

def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
    """
        reverse_convert method for the formatter.

        Do format conversion for int columns.
        """
    for col in self.int_columns:
        if col in processed_data.columns:
            processed_data[col] = processed_data[col].astype(int)
        else:
            logger.error('Column {} not found in processed_data.'.format(col))
    logger.info('Data reverse-converted by IntValueFormatter.')
    return processed_data

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

@field_validator('column_list')
@classmethod
def check_column_list(cls, value) -> Any:
    if len(value) == len(set(value)):
        return value
    raise MetadataInitError('column_list has duplicate element!')

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

def update(self, attributes: dict[str, Any]):
    """
        Update tags.
        """
    for k, v in attributes.items():
        self.add(k, v)
    return self

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

class NumericInspector(Inspector):
    """
    A class for inspecting numeric data.

    This class is a subclass of `Inspector` and is designed to provide methods for inspecting
    and analyzing numeric data. It includes methods for detecting int or float data type.

    In August 2024, we introduced a new feature that will continue to judge the positivity or
    negativity after determining the type, thereby effectively improving the quality of synthetic
    data in subsequent processing.
    """
    int_columns: set = set()
    '\n    A set of column names that contain integer values.\n    '
    float_columns: set = set()
    '\n    A set of column names that contain float values.\n    '
    positive_columns: set = set()
    '\n    A set of column names that contain only positive numeric values.\n    '
    negative_columns: set = set()
    '\n    A set of column names that contain only negative numeric values.\n    '
    pos_threshold: float = 0.95
    '\n    The threshold proportion of positive values in a column to consider it as a positive column.\n    '
    negative_threshold: float = 0.95
    '\n    The threshold proportion of negative values in a column to consider it as a negative column.\n    '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._int_rate = 0.9
        self.df_length = 0

    def _is_int_column(self, col_series: pd.Series) -> bool:
        """
        Determine if a column contains predominantly integer values.

        This method checks if the proportion of integer values in the given column
        exceeds a predefined threshold.

        Args:
            col_series (pd.Series): The column series to be inspected.

        Returns:
            bool: True if the column is predominantly integer, False otherwise.
        """
        numeric_values = pd.to_numeric(col_series, errors='coerce').dropna()
        if len(numeric_values) == 0:
            return False
        int_cnt = (numeric_values == numeric_values.astype(int)).sum()
        int_rate = int_cnt / len(numeric_values)
        return int_rate > self._int_rate

    def _is_positive_or_negative_column(self, col_series: pd.Series, threshold: float, comparison_func) -> bool:
        """
        Determine if a column contains predominantly positive or negative values.

        This method checks if the proportion of values that satisfy a given comparison
        function exceeds a predefined threshold.

        Args:
            col_series (pd.Series): The column series to be inspected.
            threshold (float): The proportion threshold for considering the column as positive or negative.
            comparison_func (function): A function that takes a numeric value and returns a boolean.

        Returns:
            bool: True if the column satisfies the condition, False otherwise.
        """
        numeric_values = pd.to_numeric(col_series, errors='coerce').dropna()
        if len(numeric_values) == 0:
            return False
        count = comparison_func(numeric_values).sum()
        proportion = count / len(numeric_values)
        return proportion >= threshold

    def _is_positive_column(self, col_series: pd.Series) -> bool:
        """
        Determine if a column contains predominantly positive values.

        This method checks if the proportion of positive values in the given column
        exceeds a predefined threshold.

        Args:
            col_series (pd.Series): The column series to be inspected.

        Returns:
            bool: True if the column is predominantly positive, False otherwise.
        """
        return self._is_positive_or_negative_column(col_series, self.pos_threshold, lambda x: x > 0)

    def _is_negative_column(self, col_series: pd.Series) -> bool:
        """
        Determine if a column contains predominantly negative values.

        This method checks if the proportion of negative values in the given column
        exceeds a predefined threshold.

        Args:
            col_series (pd.Series): The column series to be inspected.

        Returns:
            bool: True if the column is predominantly negative, False otherwise.
        """
        return self._is_positive_or_negative_column(col_series, self.negative_threshold, lambda x: x < 0)

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        self.int_columns = set()
        self.float_columns = set()
        self.positive_columns = set()
        self.negative_columns = set()
        self.df_length = len(raw_data)
        for col in raw_data.columns:
            if pd.api.types.is_integer_dtype(raw_data[col].dtype) or pd.api.types.is_float_dtype(raw_data[col].dtype):
                if self._is_int_column(raw_data[col]):
                    self.int_columns.add(col)
                else:
                    self.float_columns.add(col)
                if self._is_positive_column(raw_data[col]):
                    self.positive_columns.add(col)
                elif self._is_negative_column(raw_data[col]):
                    self.negative_columns.add(col)
        self.ready = True

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        numeric_format: dict = {}
        numeric_format['positive'] = sorted(list(self.positive_columns))
        numeric_format['negative'] = sorted(list(self.negative_columns))
        return {'int_columns': list(self.int_columns), 'float_columns': list(self.float_columns), 'numeric_format': numeric_format}

def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
    """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
    self.int_columns = set()
    self.float_columns = set()
    self.positive_columns = set()
    self.negative_columns = set()
    self.df_length = len(raw_data)
    for col in raw_data.columns:
        if pd.api.types.is_integer_dtype(raw_data[col].dtype) or pd.api.types.is_float_dtype(raw_data[col].dtype):
            if self._is_int_column(raw_data[col]):
                self.int_columns.add(col)
            else:
                self.float_columns.add(col)
            if self._is_positive_column(raw_data[col]):
                self.positive_columns.add(col)
            elif self._is_negative_column(raw_data[col]):
                self.negative_columns.add(col)
    self.ready = True

class FixedCombinationInspector(Inspector):
    """
    FixedCombinationInspector is designed to identify columns in a DataFrame that have fixed relationships based on covariance.

    Attributes:
        fixed_combinations (dict[str, set[str]]): A dictionary mapping column names to sets of column names that have fixed relationships with them.
        _inspect_level (int): The inspection level for this inspector, set to 70.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fixed_combinations: dict[str, set[str]] = {}
        '\n        A dictionary mapping column names to sets of column names that have fixed relationships with them.\n        '
        self._inspect_level: int = 70
        '\n        The inspection level for this inspector, set to 70. This attribute indicates the priority or depth of inspection that this inspector performs relative to other inspectors.\n        '

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """
        Fit the inspector to the raw data.
            Process fixed combinations of numerical and string columns:
            Numerical Columns: Calculate correlation using the covariance matrix.
            String Columns: Determine relationships based on one-to-one value mapping.
        """
        self.fixed_combinations = {}
        self._fit_numeric_relationships(raw_data)
        self._fit_one_to_one_relationships(raw_data)
        self.ready = True

    def _fit_numeric_relationships(self, raw_data: pd.DataFrame) -> None:
        """
        Calculate correlation using the covariance matrix.
        """
        numeric_columns = raw_data.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_columns) > 0:
            covariance_matrix = raw_data[numeric_columns].dropna().cov()
            for column in covariance_matrix.columns:
                related_columns = set(covariance_matrix.index[covariance_matrix[column].abs() > 0.9])
                related_columns.discard(column)
                if related_columns:
                    self.fixed_combinations[column] = related_columns

    def _fit_one_to_one_relationships(self, raw_data: pd.DataFrame) -> None:
        """
        Determine relationships based on one-to-one value mapping.
        """
        string_columns = raw_data.columns
        if len(string_columns) > 0:
            matched_columns = set()
            unique_counts = raw_data[string_columns].nunique(dropna=True)
            filter_condition = (unique_counts < raw_data.shape[0] * 0.9) & (unique_counts != 0)
            unique_counts = unique_counts[filter_condition]
            sorted_columns = unique_counts.sort_values().index.tolist()
            for i, col1 in enumerate(sorted_columns):
                if col1 in matched_columns:
                    continue
                for col2 in sorted_columns[i + 1:]:
                    if col2 in matched_columns:
                        continue
                    if unique_counts[col1] != unique_counts[col2]:
                        continue
                    pairs = raw_data[[col1, col2]].dropna()
                    mapping_from_col = pairs.drop_duplicates(subset=[col1, col2])
                    duplicates_in_col1 = mapping_from_col.duplicated(subset=col1, keep=False)
                    duplicates_in_col2 = mapping_from_col.duplicated(subset=col2, keep=False)
                    if not duplicates_in_col1.any() and (not duplicates_in_col2.any()):
                        if col1 not in self.fixed_combinations:
                            self.fixed_combinations[col1] = set()
                        self.fixed_combinations[col1].add(col2)
                        matched_columns.add(col1)
                        matched_columns.add(col2)
                        break

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'fixed_combinations': self.fixed_combinations}

def _fit_numeric_relationships(self, raw_data: pd.DataFrame) -> None:
    """
        Calculate correlation using the covariance matrix.
        """
    numeric_columns = raw_data.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_columns) > 0:
        covariance_matrix = raw_data[numeric_columns].dropna().cov()
        for column in covariance_matrix.columns:
            related_columns = set(covariance_matrix.index[covariance_matrix[column].abs() > 0.9])
            related_columns.discard(column)
            if related_columns:
                self.fixed_combinations[column] = related_columns

def _fit_one_to_one_relationships(self, raw_data: pd.DataFrame) -> None:
    """
        Determine relationships based on one-to-one value mapping.
        """
    string_columns = raw_data.columns
    if len(string_columns) > 0:
        matched_columns = set()
        unique_counts = raw_data[string_columns].nunique(dropna=True)
        filter_condition = (unique_counts < raw_data.shape[0] * 0.9) & (unique_counts != 0)
        unique_counts = unique_counts[filter_condition]
        sorted_columns = unique_counts.sort_values().index.tolist()
        for i, col1 in enumerate(sorted_columns):
            if col1 in matched_columns:
                continue
            for col2 in sorted_columns[i + 1:]:
                if col2 in matched_columns:
                    continue
                if unique_counts[col1] != unique_counts[col2]:
                    continue
                pairs = raw_data[[col1, col2]].dropna()
                mapping_from_col = pairs.drop_duplicates(subset=[col1, col2])
                duplicates_in_col1 = mapping_from_col.duplicated(subset=col1, keep=False)
                duplicates_in_col2 = mapping_from_col.duplicated(subset=col2, keep=False)
                if not duplicates_in_col1.any() and (not duplicates_in_col2.any()):
                    if col1 not in self.fixed_combinations:
                        self.fixed_combinations[col1] = set()
                    self.fixed_combinations[col1].add(col2)
                    matched_columns.add(col1)
                    matched_columns.add(col2)
                    break

class BoolInspector(Inspector):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bool_columns: set[str] = set()

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        self.bool_columns = set()
        self.bool_columns = self.bool_columns.union(set(raw_data.infer_objects().select_dtypes(include=['bool']).columns))
        self.ready = True

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'bool_columns': list(self.bool_columns)}

def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
    """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
    self.bool_columns = set()
    self.bool_columns = self.bool_columns.union(set(raw_data.infer_objects().select_dtypes(include=['bool']).columns))
    self.ready = True

class DiscreteInspector(Inspector):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.discrete_columns: set[str] = set()

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        self.discrete_columns = set()
        self.discrete_columns = self.discrete_columns.union(set(raw_data.select_dtypes(include='object').columns))
        self.ready = True

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'discrete_columns': list(self.discrete_columns)}

def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
    """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
    self.discrete_columns = set()
    self.discrete_columns = self.discrete_columns.union(set(raw_data.select_dtypes(include='object').columns))
    self.ready = True

class IDInspector(Inspector):
    _inspect_level = 20
    '\n    The inspect_level of IDInspector is higher than NumericInspector.\n\n    Often, some column, especially int type id column can also be recognized as numeric types by NumericInspector, causing the column to be marked repeatedly.\n    '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ID_columns: set[str] = set()

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        self.ID_columns = set()
        df_length = len(raw_data)
        candidate_columns = set(raw_data.select_dtypes(include=['object', 'int64']).columns)
        for each_col_name in candidate_columns:
            target_col = raw_data[each_col_name]
            col_set_length = len(set(target_col))
            if col_set_length == df_length:
                self.ID_columns.add(each_col_name)
        self.ready = True

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'id_columns': list(self.ID_columns)}

def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
    """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
    self.ID_columns = set()
    df_length = len(raw_data)
    candidate_columns = set(raw_data.select_dtypes(include=['object', 'int64']).columns)
    for each_col_name in candidate_columns:
        target_col = raw_data[each_col_name]
        col_set_length = len(set(target_col))
        if col_set_length == df_length:
            self.ID_columns.add(each_col_name)
    self.ready = True

class InspectorManager(Manager):
    register_type = Inspector
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_inspectors(self):
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(inspectors)

    def init_all_inspectors(self, **kwargs: Any) -> list[Inspector]:
        return [self.init(inspector_name, **kwargs) for inspector_name in self.registed_inspectors.keys()]

    def init_inspcetors(self, includes: Iterable[str] | None=None, excludes: Iterable[str] | None=None, **kwargs: Any) -> list[Inspector]:
        includes = includes or self.registed_inspectors.keys()
        if excludes:
            includes = list(set(includes) - set(excludes))
        return [self.init(inspector_name, **kwargs) for inspector_name in includes]

def init_all_inspectors(self, **kwargs: Any) -> list[Inspector]:
    return [self.init(inspector_name, **kwargs) for inspector_name in self.registed_inspectors.keys()]

def init_inspcetors(self, includes: Iterable[str] | None=None, excludes: Iterable[str] | None=None, **kwargs: Any) -> list[Inspector]:
    includes = includes or self.registed_inspectors.keys()
    if excludes:
        includes = list(set(includes) - set(excludes))
    return [self.init(inspector_name, **kwargs) for inspector_name in includes]

class DatetimeInspector(Inspector):
    _inspect_level = 20
    '\n    The inspect_level of DatetimeInspector is higher than DiscreteInspector.\n\n    Often, difficult-to-recognize date or datetime objects are also recognized as descrete types by DatetimeInspector, causing the column to be marked repeatedly.\n    '
    _format_match_rate = 0.9
    '\n    When specifically check the datatime format, problems caused by missing values and incorrect values will inevitably occur.\n    To fix this, we discard the .any()  method and use the `match_rate` to increase the robustness of this inspector.\n    '
    PRESET_FORMAT_STRINGS = ['%Y-%m-%d', '%d %b %Y', '%b-%Y', '%Y/%m/%d']

    def __init__(self, user_formats: list[str]=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datetime_columns: set[str] = set()
        self.user_defined_formats = user_formats if user_formats else []
        self.column_formats: dict[str, str] = {}

    @classmethod
    @ignore_warnings(category=UserWarning)
    def can_convert_to_datetime(cls, input_col: pd.Series):
        """Whether a df column can be converted to datetime.

        Args:
            input_col(pd.Series): A column of a dataframe.
        """
        try:
            pd.to_datetime(input_col)
            return True
        except DateParseError:
            return False
        except:
            return False

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        self.datetime_columns = set()
        self.datetime_columns = self.datetime_columns.union(set(raw_data.infer_objects().select_dtypes(include=['datetime64']).columns))
        candidate_columns = set(raw_data.select_dtypes(include=['object']).columns)
        for col_name in candidate_columns:
            each_col = raw_data[col_name]
            if DatetimeInspector.can_convert_to_datetime(each_col):
                self.datetime_columns.add(col_name)
        for col_name in self.datetime_columns:
            each_col = raw_data[col_name]
            datetime_format = self.detect_datetime_format(each_col)
            if datetime_format:
                self.column_formats[col_name] = datetime_format
        self.ready = True

    def detect_datetime_format(self, series: pd.Series):
        """Detects the datetime format of a pandas Series.

        This method iterates over a list of user-defined and preset datetime formats,
        and attempts to parse each date in the series using each format.
        If all dates in the series can be successfully parsed with a format,
        that format is returned. If no format can parse all dates, an empty string is returned.

        Args:
            series (pd.Series): The pandas Series to detect the datetime format of.

        Returns:
               str: The datetime format that can parse all dates in the series, or None if no such format is found.
        """

        def _is_series_fit_format(parsed_series, match_rate):
            length = len(parsed_series)
            false_num = len(list((i for i in parsed_series if i is False)))
            false_rate = false_num / length
            return false_rate >= match_rate
        for fmt in self.user_defined_formats + self.PRESET_FORMAT_STRINGS:
            try:
                parsed_series = series.apply(lambda x: pd.to_datetime(x, format=fmt, errors='coerce'))
                if _is_series_fit_format(parsed_series.isnull(), self._format_match_rate):
                    return fmt
            except ValueError:
                continue

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'datetime_columns': list(self.datetime_columns), 'datetime_formats': self.column_formats}

def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
    """Fit the inspector.

        Gets the list of discrete columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
    self.datetime_columns = set()
    self.datetime_columns = self.datetime_columns.union(set(raw_data.infer_objects().select_dtypes(include=['datetime64']).columns))
    candidate_columns = set(raw_data.select_dtypes(include=['object']).columns)
    for col_name in candidate_columns:
        each_col = raw_data[col_name]
        if DatetimeInspector.can_convert_to_datetime(each_col):
            self.datetime_columns.add(col_name)
    for col_name in self.datetime_columns:
        each_col = raw_data[col_name]
        datetime_format = self.detect_datetime_format(each_col)
        if datetime_format:
            self.column_formats[col_name] = datetime_format
    self.ready = True

class RegexInspector(Inspector):
    """RegexInspector
    RegexInspector is a sdgx inspector that uses regular expression rules to detect column data types. It can be initialized with a custom expression, or it can be inherited and applied to specific data types,such as email, US address, HKID etc.

    By default, we will not directly register the RegexInspector to the Inspector Manager. Instead, use it as a baseclass or user-defined regex, then put it into the Inspector Manager or use it alone
    """
    pattern: str = None
    '\n    pattern is the regular expression string of current inspector.\n    '
    data_type_name: str = None
    '\n    data_type_name is the name of the data type, such as email, US address, HKID etc.\n    '
    _match_percentage: float = 0.8
    "\n    Private variable used to store property match_percentage's value.\n    "

    @property
    def match_percentage(self):
        """
        The match_percentage shoud > 0.5 and < 1.

        Due to the existence of empty data, wrong data, etc., the match_percentage is the proportion of the current regular expression compound. When the number of compound regular expressions is higher than this ratio, the column can be considered fit the current data type.
        """
        return self._match_percentage

    @match_percentage.setter
    def match_percentage(self, value):
        if value > 0.5 and value <= 1:
            self._match_percentage = value
        else:
            raise InspectorInitError('The match_percentage should be set in (0.5, 1].')

    def __init__(self, pattern: str=None, data_type_name: str=None, match_percentage: float=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex_columns: set[str] = set()
        if pattern:
            self.pattern = pattern
        if self.pattern is None:
            raise InspectorInitError('Regular expression NOT found.')
        self.p = re.compile(self.pattern)
        if data_type_name:
            if data_type_name.endswith('_columns'):
                self.data_type_name = data_type_name[:-8]
            else:
                self.data_type_name = data_type_name
        elif not self.data_type_name:
            self.data_type_name = f'regex_{self.pattern}_columns'
        if self.data_type_name is None:
            raise InspectorInitError("Inspector's data type undefined.")
        if match_percentage:
            self.match_percentage = match_percentage

    def fit(self, input_raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Finds the list of regex columns from the tabular data (in pd.DataFrame).

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        for each_col in input_raw_data.columns:
            each_match_rate = self._fit_column(input_raw_data[each_col])
            if each_match_rate > self.match_percentage:
                self.regex_columns.add(each_col)
        self.ready = True

    def domain_verification(self, each_sample: str):
        """
        The function domain_verification is used to add custom domain verification logic. When a sample matches a regular expression, the domain_verification function is executed for further verification.

        Additional logic checks can be performed beyond regular expressions, making it more flexible. For example, in a company name, there may be address information. When determining the type of address, if the sample ends with "Company", domain_verification can return False to avoid misclassification, thus improving the accuracy of the inspector.

        This function has the power to veto. When the function outputs False, the sample will be classified as not matching the corresponding data type of the inspector.

        If this function is not overwritten, domain_verification will default to return True.

        Args:
            each_sample (str): string of each sample.
        """
        return True

    def _fit_column(self, column_data: pd.Series):
        """
        Regular expression matching for a single column, returning the matching ratio.

        Args:
             column_data (pd.Series): the column data.
        """
        length = len(column_data)
        unmatch_cnt = 0
        match_cnt = 0
        for i in column_data:
            m = re.match(self.p, str(i))
            d = self.domain_verification(str(i))
            if m and d:
                match_cnt += 1
            else:
                unmatch_cnt += 1
                if unmatch_cnt > length * (1 - self.match_percentage) + 1:
                    break
        return match_cnt / length

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {self.data_type_name + '_columns': list(self.regex_columns)}

def fit(self, input_raw_data: pd.DataFrame, *args, **kwargs):
    """Fit the inspector.

        Finds the list of regex columns from the tabular data (in pd.DataFrame).

        Args:
            raw_data (pd.DataFrame): Raw data
        """
    for each_col in input_raw_data.columns:
        each_match_rate = self._fit_column(input_raw_data[each_col])
        if each_match_rate > self.match_percentage:
            self.regex_columns.add(each_col)
    self.ready = True

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

def __init__(self, *args, **kwargs) -> None:
    if 'use_dataloader' in kwargs.keys():
        self.use_dataloader = kwargs['use_dataloader']
    if 'use_raw_data' in kwargs.keys():
        self.use_raw_data = kwargs['use_raw_data']

class ModelManager(Manager):
    register_type = SynthesizerModel
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_models(self):
        """
        redirect to registed_cls
        """
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(ml.single_table)
        self._load_dir(ml.multi_tables)
        self._load_dir(statistics.single_table)
        self._load_dir(statistics.multi_tables)

    def init_model(self, model_name, **kwargs: dict[str, Any]) -> SynthesizerModel:
        """
        redirect to init
        """
        return self.init(model_name, **kwargs)

    def load(self, model: type[SynthesizerModel] | str, model_path, **kwargs) -> SynthesizerModel:
        if not (isinstance(model, type) or isinstance(model, str)):
            raise ManagerLoadModelError('model must be type of SynthesizerModel or str for model_name')
        if isinstance(model, str):
            model = self._normalize_name(model)
        if isinstance(model, str) and model not in self.registed_models:
            raise ManagerLoadModelError(f'{model} is not registered.')
        model = model if isinstance(model, type) else self.registed_models[model]
        try:
            return model.load(model_path, **kwargs)
        except Exception as e:
            raise ManagerLoadModelError(e)

def init_model(self, model_name, **kwargs: dict[str, Any]) -> SynthesizerModel:
    """
        redirect to init
        """
    return self.init(model_name, **kwargs)

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

class StrValuedEnumMeta(EnumMeta):

    def __str__(self):
        return str(self.values)
    __repr__ = __str__

    def __contains__(cls, item):
        if isinstance(item, str):
            return item in cls.values
        elif isinstance(item, Iterable):
            a = np.array(list(item)).astype(str)
            if len(a.shape) == 0 or a.shape[0] == 0:
                return True
            values = set(a)
            return values.issubset(set(cls.values))
        else:
            super().__contains__(item)

def __contains__(cls, item):
    if isinstance(item, str):
        return item in cls.values
    elif isinstance(item, Iterable):
        a = np.array(list(item)).astype(str)
        if len(a.shape) == 0 or a.shape[0] == 0:
            return True
        values = set(a)
        return values.issubset(set(cls.values))
    else:
        super().__contains__(item)

def log_numerical_distributions_error(numerical_distributions, processed_data_columns, logger):
    """Log error when numerical distributions columns don't exist anymore."""
    unseen_columns = numerical_distributions.keys() - set(processed_data_columns)
    for column in unseen_columns:
        logger.info(f"Requested distribution '{numerical_distributions[column]}' cannot be applied to column '{column}' because it no longer exists after preprocessing.")

class DataTransformer(object):
    """Data Transformer.

    Model continuous columns with a BayesianGMM and normalized to a scalar [0, 1] and a vector.
    Discrete columns are encoded using a scikit-learn OneHotEncoder.
    """

    def __init__(self, max_clusters=10, weight_threshold=0.005, metadata=None):
        """Create a data transformer.

        Args:
            max_clusters (int):
                Maximum number of Gaussian distributions in Bayesian GMM.
            weight_threshold (float):
                Weight threshold for a Gaussian distribution to be kept.
        """
        self.metadata: Metadata = metadata
        self._max_clusters = max_clusters
        self._weight_threshold = weight_threshold

    def _fit_categorical_encoder(self, column_name: str, data: pd.DataFrame, encoder_type: CategoricalEncoderType) -> Tuple[CategoricalEncoderInstanceType, int, ActivationFuncType]:
        if encoder_type not in CategoricalEncoderMapper.keys():
            raise ValueError('Unsupported encoder type {0}.'.format(encoder_type))
        p: CategoricalEncoderParams = CategoricalEncoderMapper[encoder_type]
        encoder = p.encoder()
        encoder.fit(data, column_name)
        num_categories = p.categories_caculator(encoder)
        activate_fn = p.activate_fn
        return (encoder, num_categories, activate_fn)

    def _fit_continuous(self, data):
        """Train Bayesian GMM for continuous columns.

        Args:
            data (pd.DataFrame):
                A dataframe containing a column.

        Returns:
            namedtuple:
                A ``ColumnTransformInfo`` object.
        """
        column_name = data.columns[0]
        gm = ClusterBasedNormalizer(model_missing_values=True, max_clusters=min(len(data), 10))
        gm.fit(data, column_name)
        num_components = sum(gm.valid_component_indicator)
        return ColumnTransformInfo(column_name=column_name, column_type='continuous', transform=gm, output_info=[SpanInfo(1, 'tanh'), SpanInfo(num_components, 'softmax')], output_dimensions=1 + num_components)

    def _fit_discrete(self, data, encoder_type: CategoricalEncoderType=None):
        """Fit one hot encoder for discrete column.

        Args:
            data (pd.DataFrame):
                A dataframe containing a column.

        Returns:
            namedtuple:
                A ``ColumnTransformInfo`` object.
        """
        encoder, activate_fn, selected_encoder_type = (None, None, None)
        column_name = data.columns[0]
        if encoder_type is None and self.metadata:
            selected_encoder_type = encoder_type = self.metadata.get_column_encoder_by_name(column_name)
        if encoder_type is None:
            encoder_type = 'onehot'
        num_categories = -1
        if encoder_type == 'onehot':
            encoder, num_categories, activate_fn = self._fit_categorical_encoder(column_name, data, encoder_type)
        if not selected_encoder_type and self.metadata and (num_categories != -1):
            encoder_type = self.metadata.get_column_encoder_by_categorical_threshold(num_categories) or encoder_type
        if encoder_type == 'onehot':
            pass
        else:
            encoder, num_categories, activate_fn = self._fit_categorical_encoder(column_name, data, encoder_type)
        assert encoder and activate_fn
        return ColumnTransformInfo(column_name=column_name, column_type='discrete', transform=encoder, output_info=[SpanInfo(num_categories, activate_fn)], output_dimensions=num_categories)

    def fit(self, data_loader: DataLoader, discrete_columns=()):
        """Fit the ``DataTransformer``.

        Fits a ``ClusterBasedNormalizer`` for continuous columns and a
        ``OneHotEncoder`` for discrete columns.

        This step also counts the #columns in matrix data and span information.
        """
        self.output_info_list: List[List[SpanInfo]] = []
        self.output_dimensions: int = 0
        self.dataframe: bool = True
        self._column_raw_dtypes = data_loader[:data_loader.chunksize].infer_objects().dtypes
        self._column_transform_info_list: List[ColumnTransformInfo] = []
        for column_name in tqdm.tqdm(data_loader.columns(), desc='Preparing data', delay=3):
            if column_name in discrete_columns:
                logger.debug(f'Fitting discrete column {column_name}...')
                column_transform_info = self._fit_discrete(data_loader[[column_name]])
            else:
                logger.debug(f'Fitting continuous column {column_name}...')
                column_transform_info = self._fit_continuous(data_loader[[column_name]])
            self.output_info_list.append(column_transform_info.output_info)
            self.output_dimensions += column_transform_info.output_dimensions
            self._column_transform_info_list.append(column_transform_info)

    def _transform_continuous(self, column_transform_info, data):
        logger.debug(f'Transforming continuous column {column_transform_info.column_name}...')
        column_name = data.columns[0]
        data[column_name] = data[column_name].to_numpy().flatten()
        gm = column_transform_info.transform
        transformed = gm.transform(data)
        output = np.zeros((len(transformed), column_transform_info.output_dimensions))
        output[:, 0] = transformed[f'{column_name}.normalized'].to_numpy()
        index = transformed[f'{column_name}.component'].to_numpy().astype(int)
        output[np.arange(index.size), index + 1] = 1.0
        return output

    def _transform_discrete(self, column_transform_info, data):
        logger.debug(f'Transforming discrete column {column_transform_info.column_name}...')
        encoder = column_transform_info.transform
        return encoder.transform(data).to_numpy()

    def _synchronous_transform(self, raw_data, column_transform_info_list) -> NDArrayLoader:
        """Take a Pandas DataFrame and transform columns synchronous.

        Outputs a list with Numpy arrays.
        """
        loader = NDArrayLoader.get_auto_save(raw_data)
        for column_transform_info in column_transform_info_list:
            column_name = column_transform_info.column_name
            data = raw_data[[column_name]]
            if column_transform_info.column_type == 'continuous':
                loader.store(self._transform_continuous(column_transform_info, data).astype(float))
            else:
                loader.store(self._transform_discrete(column_transform_info, data).astype(float))
        return loader

    def _parallel_transform(self, raw_data, column_transform_info_list) -> NDArrayLoader:
        """Take a Pandas DataFrame and transform columns in parallel.

        Outputs a list with Numpy arrays.
        """
        processes = []
        for column_transform_info in column_transform_info_list:
            column_name = column_transform_info.column_name
            data = raw_data[[column_name]]
            process = None
            if column_transform_info.column_type == 'continuous':
                process = delayed(self._transform_continuous)(column_transform_info, data)
            else:
                process = delayed(self._transform_discrete)(column_transform_info, data)
            processes.append(process)
        p = Parallel(n_jobs=-1, return_as='generator')
        loader = NDArrayLoader.get_auto_save(raw_data)
        for ndarray in tqdm.tqdm(p(processes), desc='Transforming data', total=len(processes), delay=3):
            loader.store(ndarray.astype(float))
        return loader

    def transform(self, dataloader: DataLoader) -> NDArrayLoader:
        """Take raw data and output a matrix data."""
        if dataloader.shape[0] < 500:
            loader = self._synchronous_transform(dataloader, self._column_transform_info_list)
        else:
            loader = self._parallel_transform(dataloader, self._column_transform_info_list)
        return loader

    def _inverse_transform_continuous(self, column_transform_info, column_data, sigmas, st):
        gm = column_transform_info.transform
        data = pd.DataFrame(column_data[:, :2], columns=list(gm.get_output_sdtypes()))
        data = data.astype(float)
        data.iloc[:, 1] = np.argmax(column_data[:, 1:], axis=1)
        if sigmas is not None:
            selected_normalized_value = np.random.normal(data.iloc[:, 0], sigmas[st])
            data.iloc[:, 0] = selected_normalized_value
        return gm.reverse_transform(data)

    def _inverse_transform_discrete(self, column_transform_info, column_data):
        ohe = column_transform_info.transform
        data = pd.DataFrame(column_data, columns=list(ohe.get_output_sdtypes()))
        return ohe.reverse_transform(data)[column_transform_info.column_name]

    def inverse_transform(self, data, sigmas=None):
        """Take matrix data and output raw data.

        Output uses the same type as input to the transform function.
        Either np array or pd dataframe.
        """
        st = 0
        recovered_column_data_list = []
        column_names = []
        for column_transform_info in tqdm.tqdm(self._column_transform_info_list, desc='Inverse transforming', delay=3):
            dim = column_transform_info.output_dimensions
            column_data = data[:, st:st + dim]
            if column_transform_info.column_type == 'continuous':
                recovered_column_data = self._inverse_transform_continuous(column_transform_info, column_data, sigmas, st)
            else:
                recovered_column_data = self._inverse_transform_discrete(column_transform_info, column_data)
            recovered_column_data_list.append(recovered_column_data)
            column_names.append(column_transform_info.column_name)
            st += dim
        recovered_data = np.column_stack(recovered_column_data_list)
        recovered_data = pd.DataFrame(recovered_data, columns=column_names).astype(self._column_raw_dtypes)
        if not self.dataframe:
            recovered_data = recovered_data.to_numpy()
        return recovered_data

    def convert_column_name_value_to_id(self, column_name, value):
        """Get the ids of the given `column_name`."""
        discrete_counter = 0
        column_id = 0
        for column_transform_info in self._column_transform_info_list:
            if column_transform_info.column_name == column_name:
                break
            if column_transform_info.column_type == 'discrete':
                discrete_counter += 1
            column_id += 1
        else:
            raise ValueError(f"The column_name `{column_name}` doesn't exist in the data.")
        ohe = column_transform_info.transform
        data = pd.DataFrame([value], columns=[column_transform_info.column_name])
        one_hot = ohe.transform(data).to_numpy()[0]
        if sum(one_hot) == 0:
            raise ValueError(f"The value `{value}` doesn't exist in the column `{column_name}`.")
        return {'discrete_column_id': discrete_counter, 'column_id': column_id, 'value_id': np.argmax(one_hot)}

def _fit_categorical_encoder(self, column_name: str, data: pd.DataFrame, encoder_type: CategoricalEncoderType) -> Tuple[CategoricalEncoderInstanceType, int, ActivationFuncType]:
    if encoder_type not in CategoricalEncoderMapper.keys():
        raise ValueError('Unsupported encoder type {0}.'.format(encoder_type))
    p: CategoricalEncoderParams = CategoricalEncoderMapper[encoder_type]
    encoder = p.encoder()
    encoder.fit(data, column_name)
    num_categories = p.categories_caculator(encoder)
    activate_fn = p.activate_fn
    return (encoder, num_categories, activate_fn)

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
def _get_supported_sdtypes():
    get_transformers_by_type.cache_clear()
    return get_transformers_by_type().keys()

def _set_field_sdtype(self, data, field):
    clean_data = data[field].dropna()
    kind = clean_data.infer_objects().dtype.kind
    self.field_sdtypes[field] = self._DTYPES_TO_SDTYPES[kind]

class BaseTransformer:
    """Base class for all transformers.

    The ``BaseTransformer`` class contains methods that must be implemented
    in order to create a new transformer. The ``_fit`` method is optional,
    and ``fit_transform`` method is already implemented.
    """
    INPUT_SDTYPE = None
    SUPPORTED_SDTYPES = None
    OUTPUT_SDTYPES = None
    DETERMINISTIC_TRANSFORM = None
    DETERMINISTIC_REVERSE = None
    COMPOSITION_IS_IDENTITY = None
    NEXT_TRANSFORMERS = None
    columns = None
    column_prefix = None
    output_columns = None

    @classmethod
    def get_subclasses(cls):
        """Recursively find subclasses of this Baseline.

        Returns:
            list:
                List of all subclasses of this class.
        """
        subclasses = []
        for subclass in cls.__subclasses__():
            if abc.ABC not in subclass.__bases__:
                subclasses.append(subclass)
            subclasses += subclass.get_subclasses()
        return subclasses

    @classmethod
    def get_input_sdtype(cls):
        """Return the input sdtype supported by the transformer.

        Returns:
            string:
                Accepted input sdtype of the transformer.
        """
        return cls.INPUT_SDTYPE

    @classmethod
    def get_supported_sdtypes(cls):
        """Return the supported sdtypes by the transformer.

        Returns:
            list:
                Accepted input sdtypes of the transformer.
        """
        return cls.SUPPORTED_SDTYPES or [cls.INPUT_SDTYPE]

    def _add_prefix(self, dictionary):
        if not dictionary:
            return {}
        output = {}
        for output_columns, output_sdtype in dictionary.items():
            output[f'{self.column_prefix}.{output_columns}'] = output_sdtype
        return output

    def get_output_sdtypes(self):
        """Return the output sdtypes produced by this transformer.

        Returns:
            dict:
                Mapping from the transformed column names to the produced sdtypes.
        """
        return self._add_prefix(self.OUTPUT_SDTYPES)

    def is_transform_deterministic(self):
        """Return whether the transform is deterministic.

        Returns:
            bool:
                Whether or not the transform is deterministic.
        """
        return self.DETERMINISTIC_TRANSFORM

    def is_reverse_deterministic(self):
        """Return whether the reverse transform is deterministic.

        Returns:
            bool:
                Whether or not the reverse transform is deterministic.
        """
        return self.DETERMINISTIC_REVERSE

    def is_composition_identity(self):
        """Return whether composition of transform and reverse transform produces the input data.

        Returns:
            bool:
                Whether or not transforming and then reverse transforming returns the input data.
        """
        return self.COMPOSITION_IS_IDENTITY

    def get_next_transformers(self):
        """Return the suggested next transformer to be used for each column.

        Returns:
            dict:
                Mapping from transformed column names to the transformers to apply to each column.
        """
        return self._add_prefix(self.NEXT_TRANSFORMERS)

    def get_input_column(self):
        """Return input column name for transformer.

        Returns:
            str:
                Input column name.
        """
        return self.columns[0]

    def get_output_columns(self):
        """Return list of column names created in ``transform``.

        Returns:
            list:
                Names of columns created during ``transform``.
        """
        return list(self.get_output_sdtypes())

    def _store_columns(self, columns, data):
        if isinstance(columns, tuple) and columns not in data:
            columns = list(columns)
        elif not isinstance(columns, list):
            columns = [columns]
        missing = set(columns) - set(data.columns)
        if missing:
            raise KeyError(f'Columns {missing} were not present in the data.')
        self.columns = columns

    @staticmethod
    def _get_columns_data(data, columns):
        if len(columns) == 1:
            columns = columns[0]
        return data[columns].copy()

    @staticmethod
    def _add_columns_to_data(data, columns, column_names):
        """Add new columns to a ``pandas.DataFrame``.

        Args:
            - data (pd.DataFrame):
                The ``pandas.DataFrame`` to which the new columns have to be added.
            - columns (pd.DataFrame, pd.Series, np.ndarray):
                The data of the new columns to be added.
            - column_names (list, np.ndarray):
                The names of the new columns to be added.

        Returns:
            ``pandas.DataFrame`` with the new columns added.
        """
        if columns is not None:
            if isinstance(columns, (pd.DataFrame, pd.Series)):
                columns.index = data.index
            if len(columns.shape) == 1:
                data[column_names[0]] = columns
            else:
                new_data = pd.DataFrame(columns, columns=column_names)
                data = pd.concat([data, new_data.set_index(data.index)], axis=1)
        return data

    def _build_output_columns(self, data):
        self.column_prefix = '#'.join(self.columns)
        self.output_columns = list(self.get_output_sdtypes().keys())
        data_columns = set(data.columns)
        while data_columns & set(self.output_columns):
            self.column_prefix += '#'
            self.output_columns = list(self.get_output_sdtypes().keys())

    def __repr__(self):
        """Represent initialization of transformer as text.

        Returns:
            str:
                The name of the transformer followed by any non-default parameters.
        """
        class_name = self.__class__.__name__
        custom_args = []
        args = inspect.getfullargspec(self.__init__)
        keys = args.args[1:]
        defaults = args.defaults or []
        defaults = dict(zip(keys, defaults))
        instanced = {key: getattr(self, key) for key in keys}
        if defaults == instanced:
            return f'{class_name}()'
        for arg, value in instanced.items():
            if defaults[arg] != value:
                custom_args.append(f'{arg}={repr(value)}')
        args_string = ', '.join(custom_args)
        return f'{class_name}({args_string})'

    def _fit(self, columns_data):
        """Fit the transformer to the data.

        Args:
            columns_data (pandas.DataFrame or pandas.Series):
                Data to transform.
        """
        raise NotImplementedError()

    def fit(self, data, column):
        """Fit the transformer to a ``column`` of the ``data``.

        Args:
            data (pandas.DataFrame):
                The entire table.
            column (str):
                Column name. Must be present in the data.
        """
        self._store_columns(column, data)
        columns_data = self._get_columns_data(data, self.columns)
        self._fit(columns_data)
        self._build_output_columns(data)

    def _transform(self, columns_data):
        """Transform the data.

        Args:
            columns_data (pandas.DataFrame or pandas.Series):
                Data to transform.

        Returns:
            pandas.DataFrame or pandas.Series:
                Transformed data.
        """
        raise NotImplementedError()

    def transform(self, data, drop=True):
        """Transform the `self.columns` of the `data`.

        Args:
            data (pandas.DataFrame):
                The entire table.
            drop (bool):
                Whether or not to drop original columns.

        Returns:
            pd.DataFrame:
                The entire table, containing the transformed data.
        """
        if any((column not in data.columns for column in self.columns)):
            return data
        data = data.copy()
        columns_data = self._get_columns_data(data, self.columns)
        transformed_data = self._transform(columns_data)
        data = self._add_columns_to_data(data, transformed_data, self.output_columns)
        if drop:
            data = data.drop(self.columns, axis=1)
        return data

    def fit_transform(self, data, column):
        """Fit the transformer to a `column` of the `data` and then transform it.

        Args:
            data (pandas.DataFrame):
                The entire table.
            column (str):
                A column name.

        Returns:
            pd.DataFrame:
                The entire table, containing the transformed data.
        """
        self.fit(data, column)
        return self.transform(data)

    def _reverse_transform(self, columns_data):
        """Revert the transformations to the original values.

        Args:
            columns_data (pandas.DataFrame or pandas.Series):
                Data to revert.

        Returns:
            pandas.DataFrame or pandas.Series:
                Reverted data.
        """
        raise NotImplementedError()

    def reverse_transform(self, data, drop=True):
        """Revert the transformations to the original values.

        Args:
            data (pandas.DataFrame):
                The entire table.
            drop (bool):
                Whether or not to drop derived columns.

        Returns:
            pandas.DataFrame:
                The entire table, containing the reverted data.
        """
        if any((column not in data.columns for column in self.output_columns)):
            return data
        data = data.copy()
        columns_data = self._get_columns_data(data, self.output_columns)
        reversed_data = self._reverse_transform(columns_data)
        data = self._add_columns_to_data(data, reversed_data, self.columns)
        if drop:
            data = data.drop(self.output_columns, axis=1)
        return data

def _store_columns(self, columns, data):
    if isinstance(columns, tuple) and columns not in data:
        columns = list(columns)
    elif not isinstance(columns, list):
        columns = [columns]
    missing = set(columns) - set(data.columns)
    if missing:
        raise KeyError(f'Columns {missing} were not present in the data.')
    self.columns = columns

class Tree(Multivariate):
    """Helper class to instantiate a single tree in the vine model."""
    tree_type = None
    fitted = False

    def fit(self, index, n_nodes, tau_matrix, previous_tree, edges=None):
        """Fit this tree object.

        Args:
            index (int):
                index of the tree.
            n_nodes (int):
                number of nodes in the tree.
            tau_matrix (numpy.array):
                kendall's tau matrix of the data, shape (n_nodes, n_nodes).
            previous_tree (Tree):
                tree object of previous level.
        """
        self.level = index + 1
        self.n_nodes = n_nodes
        self.tau_matrix = tau_matrix
        self.previous_tree = previous_tree
        self.edges = edges or []
        if not self.edges:
            if self.level == 1:
                self.u_matrix = previous_tree
                self._build_first_tree()
            else:
                self._build_kth_tree()
            self.prepare_next_tree()
        self.fitted = True

    def _check_constraint(self, edge1, edge2):
        """Check if two edges satisfy vine constraint.

        Args:
            edge1 (Edge):
                edge object representing edge1
            edge2 (Edge):
                edge object representing edge2

        Returns:
            bool:
                True if the two edges satisfy vine constraints
        """
        full_node = {edge1.L, edge1.R, edge2.L, edge2.R}
        full_node.update(edge1.D)
        full_node.update(edge2.D)
        return len(full_node) == self.level + 1

    def _get_constraints(self):
        """Get neighboring edges for each edge in the edges."""
        num_edges = len(self.edges)
        for k in range(num_edges):
            for i in range(num_edges):
                if k != i and self.edges[k].is_adjacent(self.edges[i]):
                    self.edges[k].neighbors.append(i)

    def _sort_tau_by_y(self, y):
        """Sort tau matrix by dependece with variable y.

        Args:
            y (int):
                index of variable of intrest

        Returns:
            numpy.ndarray:
                sorted tau matrix.
        """
        tau_y = self.tau_matrix[:, y]
        tau_y[y] = np.NaN
        temp = np.empty([self.n_nodes, 3])
        temp[:, 0] = np.arange(self.n_nodes)
        temp[:, 1] = tau_y
        temp[:, 2] = abs(tau_y)
        temp[np.isnan(temp)] = -10
        sort_temp = temp[:, 2].argsort()[::-1]
        tau_sorted = temp[sort_temp]
        return tau_sorted

    def get_tau_matrix(self):
        """Get tau matrix for adjacent pairs.

        Returns:
            tau (numpy.ndarray):
                tau matrix for the current tree
        """
        num_edges = len(self.edges)
        tau = np.empty([num_edges, num_edges])
        for i in range(num_edges):
            edge = self.edges[i]
            for j in edge.neighbors:
                if self.level == 1:
                    left_u = self.u_matrix[:, edge.L]
                    right_u = self.u_matrix[:, edge.R]
                else:
                    left_parent, right_parent = edge.parents
                    left_u, right_u = Edge.get_conditional_uni(left_parent, right_parent)
                tau[i, j], pvalue = scipy.stats.kendalltau(left_u, right_u)
        return tau

    def get_adjacent_matrix(self):
        """Get adjacency matrix.

        Returns:
            numpy.ndarray:
                adjacency matrix
        """
        edges = self.edges
        num_edges = len(edges) + 1
        adj = np.zeros([num_edges, num_edges])
        for k in range(num_edges - 1):
            adj[edges[k].L, edges[k].R] = 1
            adj[edges[k].R, edges[k].L] = 1
        return adj

    def prepare_next_tree(self):
        """Prepare conditional U matrix for next tree."""
        for edge in self.edges:
            copula_theta = edge.theta
            if self.level == 1:
                left_u = self.u_matrix[:, edge.L]
                right_u = self.u_matrix[:, edge.R]
            else:
                left_parent, right_parent = edge.parents
                left_u, right_u = Edge.get_conditional_uni(left_parent, right_parent)
            left_u = [x for x in left_u if x is not None]
            right_u = [x for x in right_u if x is not None]
            X_left_right = np.array([[x, y] for x, y in zip(left_u, right_u)])
            X_right_left = np.array([[x, y] for x, y in zip(right_u, left_u)])
            copula = Bivariate(copula_type=edge.name)
            copula.theta = copula_theta
            left_given_right = copula.partial_derivative(X_left_right)
            right_given_left = copula.partial_derivative(X_right_left)
            left_given_right[left_given_right == 0] = EPSILON
            right_given_left[right_given_left == 0] = EPSILON
            left_given_right[left_given_right == 1] = 1 - EPSILON
            right_given_left[right_given_left == 1] = 1 - EPSILON
            edge.U = np.array([left_given_right, right_given_left])

    def get_likelihood(self, uni_matrix):
        """Compute likelihood of the tree given an U matrix.

        Args:
            uni_matrix (numpy.array):
                univariate matrix to evaluate likelihood on.

        Returns:
            tuple[float, numpy.array]:
                likelihood of the current tree, next level conditional univariate matrix
        """
        uni_dim = uni_matrix.shape[1]
        num_edge = len(self.edges)
        values = np.zeros([1, num_edge])
        new_uni_matrix = np.empty([uni_dim, uni_dim])
        for i in range(num_edge):
            edge = self.edges[i]
            value, left_u, right_u = edge.get_likelihood(uni_matrix)
            new_uni_matrix[edge.L, edge.R] = left_u
            new_uni_matrix[edge.R, edge.L] = right_u
            values[0, i] = np.log(value)
        return (np.sum(values), new_uni_matrix)

    def __str__(self):
        """Produce printable representation of the class."""
        template = 'L:{} R:{} D:{} Copula:{} Theta:{}'
        return '\n'.join([template.format(edge.L, edge.R, edge.D, edge.name, edge.theta) for edge in self.edges])

    def _serialize_previous_tree(self):
        if self.level == 1:
            return self.previous_tree.tolist()
        return None

    @classmethod
    def _deserialize_previous_tree(cls, tree_dict, previous):
        if tree_dict['level'] == 1:
            return np.array(tree_dict['previous_tree'])
        return previous

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this Tree.

        Returns:
            dict:
                Parameters of this Tree.
        """
        fitted = self.fitted
        result = {'tree_type': self.tree_type, 'type': get_qualified_name(self), 'fitted': fitted}
        if not fitted:
            return result
        result.update({'level': self.level, 'n_nodes': self.n_nodes, 'tau_matrix': self.tau_matrix.tolist(), 'previous_tree': self._serialize_previous_tree(), 'edges': [edge.to_dict() for edge in self.edges]})
        return result

    @classmethod
    def from_dict(cls, tree_dict, previous=None):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the Tree, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Tree:
                Instance of the tree defined on the parameters.
        """
        instance = get_tree(tree_dict['tree_type'])
        fitted = tree_dict['fitted']
        instance.fitted = fitted
        if fitted:
            instance.level = tree_dict['level']
            instance.n_nodes = tree_dict['n_nodes']
            instance.tau_matrix = np.array(tree_dict['tau_matrix'])
            instance.previous_tree = cls._deserialize_previous_tree(tree_dict, previous)
            instance.edges = [Edge.from_dict(edge) for edge in tree_dict['edges']]
        return instance

def __str__(self):
    """Produce printable representation of the class."""
    template = 'L:{} R:{} D:{} Copula:{} Theta:{}'
    return '\n'.join([template.format(edge.L, edge.R, edge.D, edge.name, edge.theta) for edge in self.edges])

class Edge(object):
    """Represents an edge in the copula."""

    def __init__(self, index, left, right, copula_name, copula_theta):
        """Initialize an Edge object.

        Args:
            left (int):
                left_node index (smaller)
            right (int):
                right_node index (larger)
            copula_name (str):
                name of the fitted copula class
            copula_theta (float):
                parameters of the fitted copula class
        """
        self.index = index
        self.L = left
        self.R = right
        self.D = set()
        self.parents = None
        self.neighbors = []
        self.name = copula_name
        self.theta = copula_theta
        self.tau = None
        self.U = None
        self.likelihood = None

    @staticmethod
    def _identify_eds_ing(first, second):
        """Find nodes connecting adjacent edges.

        Args:
            first (Edge):
                Edge object representing the first edge.
            second (Edge):
                Edge object representing the second edge.

        Returns:
            tuple[int, int, set[int]]:
                The first two values represent left and right node
                indicies of the new edge. The third value is the new dependence set.
        """
        A = {first.L, first.R}
        A.update(first.D)
        B = {second.L, second.R}
        B.update(second.D)
        depend_set = A & B
        left, right = sorted(A ^ B)
        return (left, right, depend_set)

    def is_adjacent(self, another_edge):
        """Check if two edges are adjacent.

        Args:
            another_edge (Edge):
                edge object of another edge

        Returns:
            bool:
                True if the two edges are adjacent.
        """
        return self.L == another_edge.L or self.L == another_edge.R or self.R == another_edge.L or (self.R == another_edge.R)

    @staticmethod
    def sort_edge(edges):
        """Sort iterable of edges first by left node indices then right.

        Args:
            edges (list[Edge]):
                List of edges to be sorted.

        Returns:
            list[Edge]:
                Sorted list by left and right node indices.
        """
        return sorted(edges, key=lambda x: (x.L, x.R))

    @classmethod
    def get_conditional_uni(cls, left_parent, right_parent):
        """Identify pair univariate value from parents.

        Args:
            left_parent (Edge):
                left parent
            right_parent (Edge):
                right parent

        Returns:
            tuple[np.ndarray, np.ndarray]:
                left and right parents univariate.
        """
        left, right, _ = cls._identify_eds_ing(left_parent, right_parent)
        left_u = left_parent.U[0] if left_parent.L == left else left_parent.U[1]
        right_u = right_parent.U[0] if right_parent.L == right else right_parent.U[1]
        return (left_u, right_u)

    @classmethod
    def get_child_edge(cls, index, left_parent, right_parent):
        """Construct a child edge from two parent edges.

        Args:
            index (int):
                Index of the new Edge.
            left_parent (Edge):
                Left parent
            right_parent (Edge):
                Right parent

        Returns:
            Edge:
                The new child edge.
        """
        [ed1, ed2, depend_set] = cls._identify_eds_ing(left_parent, right_parent)
        left_u, right_u = cls.get_conditional_uni(left_parent, right_parent)
        X = np.array([[x, y] for x, y in zip(left_u, right_u)])
        copula = Bivariate.select_copula(X)
        name, theta = (copula.copula_type, copula.theta)
        new_edge = Edge(index, ed1, ed2, name, theta)
        new_edge.D = depend_set
        new_edge.parents = [left_parent, right_parent]
        return new_edge

    def get_likelihood(self, uni_matrix):
        """Compute likelihood given a U matrix.

        Args:
            uni_matrix (numpy.array):
                Matrix to compute the likelihood.

        Return:
            tuple (np.ndarray, np.ndarray, np.array):
                likelihood and conditional values.
        """
        if self.parents is None:
            left_u = uni_matrix[:, self.L]
            right_u = uni_matrix[:, self.R]
        else:
            left_ing = list(self.D - self.parents[0].D)[0]
            right_ing = list(self.D - self.parents[1].D)[0]
            left_u = uni_matrix[self.L, left_ing]
            right_u = uni_matrix[self.R, right_ing]
        copula = Bivariate(copula_type=self.name)
        copula.theta = self.theta
        X_left_right = np.array([[left_u, right_u]])
        X_right_left = np.array([[right_u, left_u]])
        value = np.sum(copula.probability_density(X_left_right))
        left_given_right = copula.partial_derivative(X_left_right)
        right_given_left = copula.partial_derivative(X_right_left)
        return (value, left_given_right, right_given_left)

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this Edge.

        Returns:
            dict:
                Parameters of this Edge.
        """
        parents = None
        if self.parents:
            parents = [parent.to_dict() for parent in self.parents]
        U = None
        if self.U is not None:
            U = self.U.tolist()
        return {'index': self.index, 'L': self.L, 'R': self.R, 'D': self.D, 'parents': parents, 'neighbors': self.neighbors, 'name': self.name, 'theta': self.theta, 'tau': self.tau, 'U': U, 'likelihood': self.likelihood}

    @classmethod
    def from_dict(cls, edge_dict):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the Edge, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Edge:
                Instance of the edge defined on the parameters.
        """
        instance = cls(edge_dict['index'], edge_dict['L'], edge_dict['R'], edge_dict['name'], edge_dict['theta'])
        instance.U = np.array(edge_dict['U'])
        parents = edge_dict['parents']
        if parents:
            instance.parents = []
            for parent in parents:
                edge = Edge.from_dict(parent)
                instance.parents.append(edge)
        regular_attributes = ['D', 'tau', 'likelihood', 'neighbors']
        for key in regular_attributes:
            setattr(instance, key, edge_dict[key])
        return instance

def __init__(self, index, left, right, copula_name, copula_theta):
    """Initialize an Edge object.

        Args:
            left (int):
                left_node index (smaller)
            right (int):
                right_node index (larger)
            copula_name (str):
                name of the fitted copula class
            copula_theta (float):
                parameters of the fitted copula class
        """
    self.index = index
    self.L = left
    self.R = right
    self.D = set()
    self.parents = None
    self.neighbors = []
    self.name = copula_name
    self.theta = copula_theta
    self.tau = None
    self.U = None
    self.likelihood = None

class VineCopula(Multivariate):
    """Vine copula model.

    A :math:`vine` is a graphical representation of one factorization of the n-variate probability
    distribution in terms of :math:`n(n − 1)/2` bivariate copulas by means of the chain rule.

    It consists of a sequence of levels and as many levels as variables. Each level consists of
    a tree (no isolated nodes and no loops) satisfying that if it has :math:`n` nodes there must
    be :math:`n − 1` edges.

    Each node in tree :math:`T_1` is a variable and edges are couplings of variables constructed
    with bivariate copulas.

    Each node in tree :math:`T_{k+1}` is a coupling in :math:`T_{k}`, expressed by the copula
    of the variables; while edges are couplings between two vertices that must have one variable
    in common, becoming a conditioning variable in the bivariate copula. Thus, every level has
    one node less than the former. Once all the trees are drawn, the factorization is the product
    of all the nodes.

    Args:
        vine_type (str):
            type of the vine copula, could be 'center','direct','regular'
        random_state (int or np.random.RandomState):
            Random seed or RandomState to use.


    Attributes:
        model (copulas.univariate.Univariate):
            Distribution to compute univariates.
        u_matrix (numpy.array):
            Univariates.
        n_sample (int):
            Number of samples.
        n_var (int):
            Number of variables.
        columns (pandas.Series):
            Names of the variables.
        tau_mat (numpy.array):
            Kendall correlation parameters for data.
        truncated (int):
            Max level used to build the vine.
        depth (int):
            Vine depth.
        trees (list[Tree]):
            List of trees used by this vine.
        ppfs (list[callable]):
            percent point functions from the univariates used by this vine.
    """

    @store_args
    def __init__(self, vine_type, random_state=None):
        if sys.version_info > (3, 8):
            warnings.warn('Vines have not been fully tested on Python 3.8 and might produce wrong results. Please use Python 3.5, 3.6 or 3.7')
        self.random_state = validate_random_state(random_state)
        self.vine_type = vine_type
        self.u_matrix = None
        self.model = GaussianKDE

    @classmethod
    def _deserialize_trees(cls, tree_list):
        previous = Tree.from_dict(tree_list[0])
        trees = [previous]
        for tree_dict in tree_list[1:]:
            tree = Tree.from_dict(tree_dict, previous)
            trees.append(tree)
            previous = tree
        return trees

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this Vine.

        Returns:
            dict:
                Parameters of this Vine.
        """
        result = {'type': get_qualified_name(self), 'vine_type': self.vine_type, 'fitted': self.fitted}
        if not self.fitted:
            return result
        result.update({'n_sample': self.n_sample, 'n_var': self.n_var, 'depth': self.depth, 'truncated': self.truncated, 'trees': [tree.to_dict() for tree in self.trees], 'tau_mat': self.tau_mat.tolist(), 'u_matrix': self.u_matrix.tolist(), 'unis': [distribution.to_dict() for distribution in self.unis], 'columns': self.columns})
        return result

    @classmethod
    def from_dict(cls, vine_dict):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the Vine, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Vine:
                Instance of the Vine defined on the parameters.
        """
        instance = cls(vine_dict['vine_type'])
        fitted = vine_dict['fitted']
        if fitted:
            instance.fitted = fitted
            instance.n_sample = vine_dict['n_sample']
            instance.n_var = vine_dict['n_var']
            instance.truncated = vine_dict['truncated']
            instance.depth = vine_dict['depth']
            instance.trees = cls._deserialize_trees(vine_dict['trees'])
            instance.unis = [GaussianKDE.from_dict(uni) for uni in vine_dict['unis']]
            instance.ppfs = [uni.percent_point for uni in instance.unis]
            instance.columns = vine_dict['columns']
            instance.tau_mat = np.array(vine_dict['tau_mat'])
            instance.u_matrix = np.array(vine_dict['u_matrix'])
        return instance

    @check_valid_values
    def fit(self, X, truncated=3):
        """Fit a vine model to the data.

        1. Transform all the variables by means of their marginals.
        In other words, compute

        .. math:: u_i = F_i(x_i), i = 1, ..., n

        and compose the matrix :math:`u = u_1, ..., u_n,` where :math:`u_i` are their columns.

        Args:
            X (numpy.ndarray):
                Data to be fitted to.
            truncated (int):
                Max level to build the vine.
        """
        LOGGER.info('Fitting VineCopula("%s")', self.vine_type)
        self.n_sample, self.n_var = X.shape
        self.columns = X.columns
        self.tau_mat = X.corr(method='kendall').to_numpy()
        self.u_matrix = np.empty([self.n_sample, self.n_var])
        self.truncated = truncated
        self.depth = self.n_var - 1
        self.trees = []
        self.unis, self.ppfs = ([], [])
        for i, col in enumerate(X):
            uni = self.model()
            uni.fit(X[col])
            self.u_matrix[:, i] = uni.cumulative_distribution(X[col])
            self.unis.append(uni)
            self.ppfs.append(uni.percent_point)
        self.train_vine(self.vine_type)
        self.fitted = True

    def train_vine(self, tree_type):
        """Build the vine.

        1. For the construction of the first tree :math:`T_1`, assign one node to each variable
           and then couple them by maximizing the measure of association considered.
           Different vines impose different constraints on this construction. When those are
           applied different trees are achieved at this level.

        2. Select the copula that best fits to the pair of variables coupled by each edge in
           :math:`T_1`.

        3. Let :math:`C_{ij}(u_i , u_j )` be the copula for a given edge :math:`(u_i, u_j)`
           in :math:`T_1`. Then for every edge in :math:`T_1`, compute either

           .. math:: {v^1}_{j|i} = \\\\frac{\\\\partial C_{ij}(u_i, u_j)}{\\\\partial u_j}

           or similarly :math:`{v^1}_{i|j}`, which are conditional cdfs. When finished with
           all the edges, construct the new matrix with :math:`v^1` that has one less column u.

        4. Set k = 2.

        5. Assign one node of :math:`T_k` to each edge of :math:`T_ {k−1}`. The structure of
           :math:`T_{k−1}` imposes a set of constraints on which edges of :math:`T_k` are
           realizable. Hence the next step is to get a linked list of the accesible nodes for
           every node in :math:`T_k`.

        6. As in step 1, nodes of :math:`T_k` are coupled maximizing the measure of association
           considered and satisfying the constraints impose by the kind of vine employed plus the
           set of constraints imposed by tree :math:`T_{k−1}`.

        7. Select the copula that best fit to each edge created in :math:`T_k`.

        8. Recompute matrix :math:`v_k` as in step 4, but taking :math:`T_k` and :math:`vk−1`
           instead of :math:`T_1` and u.

        9. Set :math:`k = k + 1` and repeat from (5) until all the trees are constructed.

        Args:
            tree_type (str or TreeTypes):
                Type of trees to use.
        """
        LOGGER.debug('start building tree : 0')
        tree_1 = get_tree(tree_type)
        tree_1.fit(0, self.n_var, self.tau_mat, self.u_matrix)
        self.trees.append(tree_1)
        LOGGER.debug('finish building tree : 0')
        for k in range(1, min(self.n_var - 1, self.truncated)):
            self.trees[k - 1]._get_constraints()
            tau = self.trees[k - 1].get_tau_matrix()
            LOGGER.debug(f'start building tree: {k}')
            tree_k = get_tree(tree_type)
            tree_k.fit(k, self.n_var - k, tau, self.trees[k - 1])
            self.trees.append(tree_k)
            LOGGER.debug(f'finish building tree: {k}')

    def get_likelihood(self, uni_matrix):
        """Compute likelihood of the vine."""
        num_tree = len(self.trees)
        values = np.empty([1, num_tree])
        for i in range(num_tree):
            value, new_uni_matrix = self.trees[i].get_likelihood(uni_matrix)
            uni_matrix = new_uni_matrix
            values[0, i] = value
        return np.sum(values)

    def _sample_row(self):
        """Generate a single sampled row from vine model.

        Returns:
            numpy.ndarray
        """
        unis = np.random.uniform(0, 1, self.n_var)
        first_ind = np.random.randint(0, self.n_var)
        adj = self.trees[0].get_adjacent_matrix()
        visited = []
        explore = [first_ind]
        sampled = np.zeros(self.n_var)
        itr = 0
        while explore:
            current = explore.pop(0)
            adj_is_one = adj[current, :] == 1
            neighbors = np.where(adj_is_one)[0].tolist()
            if itr == 0:
                new_x = self.ppfs[current](unis[current])
            else:
                for i in range(itr - 1, -1, -1):
                    current_ind = -1
                    if i >= self.truncated:
                        continue
                    current_tree = self.trees[i].edges
                    for edge in current_tree:
                        if i == 0:
                            if edge.L == current and edge.R == visited[0] or (edge.R == current and edge.L == visited[0]):
                                current_ind = edge.index
                                break
                        elif edge.L == current or edge.R == current:
                            condition = set(edge.D)
                            condition.add(edge.L)
                            condition.add(edge.R)
                            visit_set = set(visited)
                            visit_set.add(current)
                            if condition.issubset(visit_set):
                                current_ind = edge.index
                            break
                    if current_ind != -1:
                        copula_type = current_tree[current_ind].name
                        copula = Bivariate(copula_type=CopulaTypes(copula_type))
                        copula.theta = current_tree[current_ind].theta
                        U = np.array([unis[visited[0]]])
                        if i == itr - 1:
                            tmp = copula.percent_point(np.array([unis[current]]), U)[0]
                        else:
                            tmp = copula.percent_point(np.array([tmp]), U)[0]
                        tmp = min(max(tmp, EPSILON), 0.99)
                new_x = self.ppfs[current](np.array([tmp]))
            sampled[current] = new_x
            for s in neighbors:
                if s not in visited:
                    explore.insert(0, s)
            itr += 1
            visited.insert(0, current)
        return sampled

    @random_state
    def sample(self, num_rows):
        """Sample new rows.

        Args:
            num_rows (int):
                Number of rows to sample

        Returns:
            pandas.DataFrame:
                sampled rows.
        """
        sampled_values = []
        for i in range(num_rows):
            sampled_values.append(self._sample_row())
        return pd.DataFrame(sampled_values, columns=self.columns)

def _sample_row(self):
    """Generate a single sampled row from vine model.

        Returns:
            numpy.ndarray
        """
    unis = np.random.uniform(0, 1, self.n_var)
    first_ind = np.random.randint(0, self.n_var)
    adj = self.trees[0].get_adjacent_matrix()
    visited = []
    explore = [first_ind]
    sampled = np.zeros(self.n_var)
    itr = 0
    while explore:
        current = explore.pop(0)
        adj_is_one = adj[current, :] == 1
        neighbors = np.where(adj_is_one)[0].tolist()
        if itr == 0:
            new_x = self.ppfs[current](unis[current])
        else:
            for i in range(itr - 1, -1, -1):
                current_ind = -1
                if i >= self.truncated:
                    continue
                current_tree = self.trees[i].edges
                for edge in current_tree:
                    if i == 0:
                        if edge.L == current and edge.R == visited[0] or (edge.R == current and edge.L == visited[0]):
                            current_ind = edge.index
                            break
                    elif edge.L == current or edge.R == current:
                        condition = set(edge.D)
                        condition.add(edge.L)
                        condition.add(edge.R)
                        visit_set = set(visited)
                        visit_set.add(current)
                        if condition.issubset(visit_set):
                            current_ind = edge.index
                        break
                if current_ind != -1:
                    copula_type = current_tree[current_ind].name
                    copula = Bivariate(copula_type=CopulaTypes(copula_type))
                    copula.theta = current_tree[current_ind].theta
                    U = np.array([unis[visited[0]]])
                    if i == itr - 1:
                        tmp = copula.percent_point(np.array([unis[current]]), U)[0]
                    else:
                        tmp = copula.percent_point(np.array([tmp]), U)[0]
                    tmp = min(max(tmp, EPSILON), 0.99)
            new_x = self.ppfs[current](np.array([tmp]))
        sampled[current] = new_x
        for s in neighbors:
            if s not in visited:
                explore.insert(0, s)
        itr += 1
        visited.insert(0, current)
    return sampled

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

class DataConnectorManager(Manager):
    register_type = DataConnector
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_data_connectors(self):
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(data_connectors)

    def init_data_connector(self, connector_name, **kwargs: dict[str, Any]) -> DataConnector:
        return self.init(connector_name, **kwargs)

def init_data_connector(self, connector_name, **kwargs: dict[str, Any]) -> DataConnector:
    return self.init(connector_name, **kwargs)

def test_remove_columns(single_demo_data_df: pd.DataFrame, base_data_processor: DataProcessor):
    assert 'occupation' in single_demo_data_df.columns
    assert 'workclass' in single_demo_data_df.columns
    assert 'age' in single_demo_data_df.columns
    result_df = base_data_processor.remove_columns(single_demo_data_df, ['workclass', 'occupation'])
    assert 'occupation' not in result_df.columns
    assert 'workclass' not in result_df.columns
    assert 'age' in result_df.columns

def test_change_metadata(metadata: Metadata):
    metadata = metadata.model_copy()
    col = 'age'
    assert col in metadata.int_columns
    assert col not in metadata.datetime_columns
    metadata.change_column_type(col, 'int', 'datetime')
    assert col in metadata.datetime_columns
    assert col not in metadata.int_columns
    metadata.change_column_type(col, 'datetime', 'int')
    assert col in metadata.int_columns
    assert col not in metadata.datetime_columns

def test_remove_metadata(metadata: Metadata):
    metadata = metadata.model_copy()
    col = 'age'
    assert col in metadata.int_columns
    metadata.remove_column([col])
    assert col not in metadata.int_columns

def test_metadata_primary_key(metadata: Metadata):
    metadata.add('id_columns', 'fnlwgt')
    metadata.update_primary_key(['fnlwgt'])
    assert metadata.primary_keys == {'fnlwgt'}

def test_metadata_check(metadata: Metadata):
    metadata.update_primary_key([])
    metadata.check()

def test_demo_multi_table_data_metadata_parent(demo_multi_data_parent_matadata):
    demo_multi_data_parent_matadata.check()
    assert demo_multi_data_parent_matadata.get_column_data_type('Store') == 'id'
    assert demo_multi_data_parent_matadata.get_column_data_type('StoreType') == 'discrete'
    assert demo_multi_data_parent_matadata.get_column_data_type('Assortment') == 'discrete'
    assert demo_multi_data_parent_matadata.get_column_data_type('CompetitionDistance') == 'int'
    assert demo_multi_data_parent_matadata.get_column_data_type('CompetitionOpenSinceMonth') == 'int'
    assert demo_multi_data_parent_matadata.get_column_data_type('Promo2') == 'int'
    assert demo_multi_data_parent_matadata.get_column_data_type('Promo2SinceWeek') == 'int'
    assert demo_multi_data_parent_matadata.get_column_data_type('Promo2SinceYear') == 'int'
    assert demo_multi_data_parent_matadata.get_column_data_type('PromoInterval') == 'discrete'
    for each_col in demo_multi_data_parent_matadata.column_list:
        assert demo_multi_data_parent_matadata.get_column_pii(each_col) is False
    assert len(demo_multi_data_parent_matadata.pii_columns) is 0
    assert 'column_data_type' in demo_multi_data_parent_matadata.dump().keys()

def test_demo_multi_table_data_metadata_child(demo_multi_data_child_matadata):
    demo_multi_data_child_matadata.check()
    assert demo_multi_data_child_matadata.get_column_data_type('Store') == 'int'
    assert demo_multi_data_child_matadata.get_column_data_type('Date') == 'datetime'
    assert demo_multi_data_child_matadata.get_column_data_type('Customers') == 'int'
    assert demo_multi_data_child_matadata.get_column_data_type('StateHoliday') == 'const'
    assert demo_multi_data_child_matadata.get_column_data_type('Sales') == 'int'
    assert demo_multi_data_child_matadata.get_column_data_type('Promo') == 'int'
    assert demo_multi_data_child_matadata.get_column_data_type('DayOfWeek') == 'int'
    assert demo_multi_data_child_matadata.get_column_data_type('Open') == 'int'
    assert demo_multi_data_child_matadata.get_column_data_type('SchoolHoliday') == 'int'
    for each_col in demo_multi_data_child_matadata.column_list:
        assert demo_multi_data_child_matadata.get_column_pii(each_col) is False
    assert len(demo_multi_data_child_matadata.pii_columns) is 0
    assert 'column_data_type' in demo_multi_data_child_matadata.dump().keys()

def test_meta_encoder(metadata: Metadata):
    metadata = metadata.model_copy()
    metadata.categorical_threshold = {1: 'aaa'}
    with pytest.raises(MetadataInvalidError):
        metadata.check()
    metadata.categorical_threshold[1] = CategoricalEncoderType.ONEHOT
    metadata.check()
    metadata.categorical_threshold['1'] = CategoricalEncoderType.ONEHOT
    with pytest.raises(MetadataInvalidError):
        metadata.check()
    del metadata.categorical_threshold['1']
    assert 'education' in metadata.discrete_columns
    metadata.categorical_encoder = {'education': CategoricalEncoderType.ONEHOT}
    metadata.check()
    metadata.categorical_encoder['1'] = CategoricalEncoderType.ONEHOT
    with pytest.raises(MetadataInvalidError):
        metadata.check()
    del metadata.categorical_encoder['1']
    metadata.categorical_encoder['1'] = 'a'
    with pytest.raises(MetadataInvalidError):
        metadata.check()

def test_keys(csv_connector: CsvConnector):
    keys = csv_connector.keys()
    assert isinstance(keys, list)
    assert len(keys) == 4

def test_singletable_gpt_model_openapi_setting(single_table_gpt_model: SingleTableGPTModel):
    open_ai_key = 'sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    open_ai_base = 'https://api.mock.openai.base.com'
    open_ai_model = 'gpt-4o-mini'
    single_table_gpt_model.set_openAI_settings(open_ai_base, open_ai_key)
    single_table_gpt_model.gpt_model = open_ai_model
    client = single_table_gpt_model.openai_client()
    assert client.base_url == open_ai_base
    assert client.api_key == open_ai_key
    assert single_table_gpt_model.gpt_model == open_ai_model

