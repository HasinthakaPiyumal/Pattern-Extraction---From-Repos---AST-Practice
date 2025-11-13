# Cluster 5

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

def chunk_generator() -> Generator[pd.DataFrame, None, None]:
    for chunk in self.dataloader.iter():
        for d in self.data_processors:
            chunk = d.convert(chunk)
        yield chunk

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

def iter(self) -> Generator[pd.DataFrame, None, None]:
    """
        Load data from cache in chunk.
        """
    for d in self.cacher.iter(self.chunksize, self.data_connector):
        yield d

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

class Cacher:
    """
    Base class for cachers

    Cacher is used to cache raw data and processed data to prevent repeat read or process.

    You can treat Cacher as a warrper of :ref:`DataConnector`
    """

    def __init__(self, blocksize, *args, **kwargs) -> None:
        self.blocksize = blocksize

    def is_cached(self, offset: int) -> bool:
        """
        Check if the data is cached
        """
        raise NotImplementedError

    def load(self, offset: int, chunksize: int, data_connector: DataConnector) -> pd.DataFrame:
        """
        Load data from data_connector or cache
        """
        raise NotImplementedError

    def load_all(self, data_connector: DataConnector) -> pd.DataFrame:
        """
        Load all data from data_connector or cache
        """
        return pd.concat(self.iter(chunksize=self.blocksize, data_connector=data_connector), ignore_index=True)

    def clear_cache(self):
        """
        Clear all cache
        """
        return

    def clear_invalid_cache(self):
        """
        Clear invalid cache.

        It's useful when data source has been changed.
        Subclass can try to inspect cache and only clear invalid cache.
        Also, it may clear all cache when not sure or not support.
        """
        return

    def iter(self, chunksize: int, data_connector: DataConnector) -> Generator[pd.DataFrame, None, None]:
        """
        Load data from data_connector or cache in chunk
        """
        raise NotImplementedError

def load_all(self, data_connector: DataConnector) -> pd.DataFrame:
    """
        Load all data from data_connector or cache
        """
    return pd.concat(self.iter(chunksize=self.blocksize, data_connector=data_connector), ignore_index=True)

class NoCache(Cacher):
    """
    No cache means to proxy data_connector
    """

    def is_cached(self, offset: int) -> bool:
        """
        Always return False
        """
        return False

    def load(self, offset: int, chunksize: int, data_connector: DataConnector) -> pd.DataFrame:
        """
        Proxy to data_connector.read
        """
        return data_connector.read(offset=offset, limit=chunksize)

    def load_all(self, data_connector: DataConnector) -> pd.DataFrame:
        """
        Proxy to data_connector.read
        """
        return data_connector.read(offset=0, limit=None)

    def iter(self, chunksize: int, data_connector: DataConnector) -> Generator[pd.DataFrame, None, None]:
        """
        Proxy to data_connector.iter
        """
        for d in data_connector.iter(chunksize=chunksize):
            yield d

def load(self, offset: int, chunksize: int, data_connector: DataConnector) -> pd.DataFrame:
    """
        Proxy to data_connector.read
        """
    return data_connector.read(offset=offset, limit=chunksize)

def load_all(self, data_connector: DataConnector) -> pd.DataFrame:
    """
        Proxy to data_connector.read
        """
    return data_connector.read(offset=0, limit=None)

def iter(self, chunksize: int, data_connector: DataConnector) -> Generator[pd.DataFrame, None, None]:
    """
        Proxy to data_connector.iter
        """
    for d in data_connector.iter(chunksize=chunksize):
        yield d

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

class DataProcessor:
    """
    Base class for data processors.
    """
    fitted = False

    def check_fitted(self):
        """Check if the processor is fitted.

        Raises:
            SynthesizerProcessorError: If the processor is not fitted.
        """
        if not self.fitted:
            raise SynthesizerProcessorError('Processor NOT fitted.')

    def fit(self, metadata: Metadata | None=None, **kwargs: Dict[str, Any]):
        self._fit(metadata, **kwargs)
        self.fitted = True

    def _fit(self, metadata: Metadata | None=None, **kwargs: Dict[str, Any]):
        """Fit the data processor.

        Called before ``convert`` and ``reverse_convert``.

        Args:
            metadata (Metadata, optional): Metadata. Defaults to None.
        """
        return

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Convert raw data into processed data.

        Args:
            raw_data (pd.DataFrame): Raw data

        Returns:
            pd.DataFrame: Processed data
        """
        return raw_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """Convert processed data into raw data.

        Args:
            processed_data (pd.DataFrame): Processed data

        Returns:
            pd.DataFrame: Raw data
        """
        return processed_data

    @staticmethod
    def remove_columns(tabular_data: pd.DataFrame, column_name_to_remove: list) -> pd.DataFrame:
        """
        Remove specified columns from the input tabular data.

        Args:
            - tabular_data (pd.DataFrame): Processed tabular data
            - column_name_to_remove (list): List of column names to be removed

        Returns:
            - result_data (pd.DataFrame): Tabular data with specified columns removed
        """
        result_data = tabular_data.copy()
        try:
            result_data = result_data.drop(columns=column_name_to_remove)
        except KeyError:
            logger.warning('Duplicate column removal occurred, which might lead to unintended consequences.')
        return result_data

    @staticmethod
    def attach_columns(tabular_data: pd.DataFrame, new_columns: pd.DataFrame) -> pd.DataFrame:
        """
        Attach additional columns to an existing DataFrame.

        Args:
            - tabular_data (pd.DataFrame): The original DataFrame.
            - new_columns (pd.DataFrame): The DataFrame containing additional columns to be attached.

        Returns:
            - result_data (pd.DataFrame): The DataFrame with new_columns attached.

        Raises:
            - ValueError: If the number of rows in tabular_data and new_columns are not the same.
        """
        if tabular_data.shape[0] != new_columns.shape[0]:
            raise ValueError('Number of rows in tabular_data and new_columns must be the same.')
        result_data = pd.concat([tabular_data, new_columns], axis=1)
        return result_data

@staticmethod
def remove_columns(tabular_data: pd.DataFrame, column_name_to_remove: list) -> pd.DataFrame:
    """
        Remove specified columns from the input tabular data.

        Args:
            - tabular_data (pd.DataFrame): Processed tabular data
            - column_name_to_remove (list): List of column names to be removed

        Returns:
            - result_data (pd.DataFrame): Tabular data with specified columns removed
        """
    result_data = tabular_data.copy()
    try:
        result_data = result_data.drop(columns=column_name_to_remove)
    except KeyError:
        logger.warning('Duplicate column removal occurred, which might lead to unintended consequences.')
    return result_data

@staticmethod
def attach_columns(tabular_data: pd.DataFrame, new_columns: pd.DataFrame) -> pd.DataFrame:
    """
        Attach additional columns to an existing DataFrame.

        Args:
            - tabular_data (pd.DataFrame): The original DataFrame.
            - new_columns (pd.DataFrame): The DataFrame containing additional columns to be attached.

        Returns:
            - result_data (pd.DataFrame): The DataFrame with new_columns attached.

        Raises:
            - ValueError: If the number of rows in tabular_data and new_columns are not the same.
        """
    if tabular_data.shape[0] != new_columns.shape[0]:
        raise ValueError('Number of rows in tabular_data and new_columns must be the same.')
    result_data = pd.concat([tabular_data, new_columns], axis=1)
    return result_data

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

class DiscreteTransformer(Transformer):
    """
    A transformer class for handling discrete values in the input data.

    This class uses one-hot encoding to convert discrete values into a format that can be used by machine learning models.

    Attributes:
        discrete_columns (list): A list of column names that are of discrete type.
        one_hot_warning_cnt (int): The warning count for one-hot encoding. If the number of new columns after one-hot encoding exceeds this count, a warning message will be issued.
        one_hot_encoders (dict): A dictionary that stores the OneHotEncoder objects for each discrete column. The keys are the column names, and the values are the corresponding OneHotEncoder objects.
        one_hot_column_names (dict): A dictionary that stores the new column names after one-hot encoding for each discrete column. The keys are the column names, and the values are lists of new column names.
        onehot_encoder_handle_unknown (str): The parameter to handle unknown categories in the OneHotEncoder. If set to 'ignore', new categories will be ignored. If set to 'error', an error will be raised when new categories are encountered.

    Methods:
        fit(metadata: Metadata, tabular_data: DataLoader | pd.DataFrame): Fit the transformer to the input data.
        _fit_column(column_name: str, column_data: pd.DataFrame): Fit a single discrete column.
        convert(raw_data: pd.DataFrame) -> pd.DataFrame: Convert the input data using one-hot encoding.
        reverse_convert(processed_data: pd.DataFrame) -> pd.DataFrame: Reverse the one-hot encoding process to get the original data.
    """
    discrete_columns: list
    '\n    Record which columns are of discrete type.\n    '
    one_hot_warning_cnt: int
    '\n    The warning count for one-hot encoding.\n    If the number of new columns after one-hot encoding exceeds this count, a warning message will be issued.\n    '
    one_hot_encoders: dict
    '\n    A dictionary that stores the OneHotEncoder objects for each discrete column.\n    The keys are the column names, and the values are the corresponding OneHotEncoder objects.\n    '
    one_hot_column_names: dict
    '\n    A dictionary that stores the new column names after one-hot encoding for each discrete column.\n    The keys are the column names, and the values are lists of new column names.\n    '
    onehot_encoder_handle_unknown: str
    "\n    The parameter to handle unknown categories in the OneHotEncoder.\n    If set to 'ignore', new categories will be ignored.\n    If set to 'error', an error will be raised when new categories are encountered.\n    "

    def __init__(self):
        self.discrete_columns = []
        self.one_hot_warning_cnt = 512
        self.one_hot_encoders = {}
        self.one_hot_column_names = {}
        self.onehot_encoder_handle_unknown = 'ignore'

    def fit(self, metadata: Metadata, tabular_data: DataLoader | pd.DataFrame):
        """
        Fit method for the DiscreteTransformer.
        """
        logger.info('Fitting using DiscreteTransformer...')
        self.discrete_columns = metadata.get('discrete_columns')
        datetime_columns = metadata.get('datetime_columns')
        if len(self.discrete_columns) == 0:
            logger.info('Fitting using DiscreteTransformer... Finished (No Columns).')
            return
        for each_datgetime_col in datetime_columns:
            if each_datgetime_col in self.discrete_columns:
                self.discrete_columns.remove(each_datgetime_col)
                logger.info(f'Datetime column {each_datgetime_col} removed from discrete column.')
        for each_col in self.discrete_columns:
            self._fit_column(each_col, tabular_data[[each_col]])
        logger.info('Fitting using DiscreteTransformer... Finished.')
        self.fitted = True
        return

    def _fit_column(self, column_name: str, column_data: pd.DataFrame):
        """
        Fit every discrete column in `_fit_column`.

        Args:
            - column_data (pd.DataFrame): A dataframe containing a column.
            - column_name: str: column name.
        """
        self.one_hot_encoders[column_name] = OneHotEncoder(handle_unknown=self.onehot_encoder_handle_unknown, sparse_output=False)
        self.one_hot_encoders[column_name].fit(column_data)
        logger.debug(f'Discrete column {column_name} fitted.')

    def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Convert method to handle discrete values in the input data.
        """
        logger.info('Converting data using DiscreteTransformer...')
        if len(self.discrete_columns) == 0:
            logger.info('Converting data using DiscreteTransformer... Finished (No column).')
            return
        processed_data = raw_data.copy()
        for each_col in self.discrete_columns:
            new_onehot_columns = self.one_hot_encoders[each_col].transform(raw_data[[each_col]])
            new_onehot_column_names = self.one_hot_encoders[each_col].get_feature_names_out()
            self.one_hot_column_names[each_col] = new_onehot_column_names
            if len(new_onehot_column_names) > self.one_hot_warning_cnt:
                logger.warning(f'Column {each_col} has too many discrete values ({len(new_onehot_column_names)} values), may consider as a continous column?')
            processed_data = self.attach_columns(processed_data, pd.DataFrame(new_onehot_columns, columns=new_onehot_column_names))
            logger.debug(f'Column {each_col} converted.')
        logger.info(f'Processed data shape: {processed_data.shape}.')
        logger.info('Converting data using DiscreteTransformer... Finished.')
        processed_data = self.remove_columns(processed_data, self.discrete_columns)
        return processed_data

    def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
        Reverse_convert method for the transformer.

        Args:
            - processed_data (pd.DataFrame): A dataframe containing onehot encoded columns.

        Returns:
            - pd.DataFrame: inverse transformed processed data.
        """
        reversed_data = processed_data.copy()
        for each_col in self.discrete_columns:
            one_hot_column_set = processed_data[self.one_hot_column_names[each_col]]
            res_column_data = self.one_hot_encoders[each_col].inverse_transform(pd.DataFrame(one_hot_column_set, columns=self.one_hot_column_names[each_col]))
            reversed_data = self.attach_columns(reversed_data, pd.DataFrame(res_column_data, columns=[each_col]))
            reversed_data = self.remove_columns(reversed_data, self.one_hot_column_names[each_col])
        logger.info('Data inverse-converted by DiscreteTransformer.')
        return reversed_data
    pass

def convert(self, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
        Convert method to handle discrete values in the input data.
        """
    logger.info('Converting data using DiscreteTransformer...')
    if len(self.discrete_columns) == 0:
        logger.info('Converting data using DiscreteTransformer... Finished (No column).')
        return
    processed_data = raw_data.copy()
    for each_col in self.discrete_columns:
        new_onehot_columns = self.one_hot_encoders[each_col].transform(raw_data[[each_col]])
        new_onehot_column_names = self.one_hot_encoders[each_col].get_feature_names_out()
        self.one_hot_column_names[each_col] = new_onehot_column_names
        if len(new_onehot_column_names) > self.one_hot_warning_cnt:
            logger.warning(f'Column {each_col} has too many discrete values ({len(new_onehot_column_names)} values), may consider as a continous column?')
        processed_data = self.attach_columns(processed_data, pd.DataFrame(new_onehot_columns, columns=new_onehot_column_names))
        logger.debug(f'Column {each_col} converted.')
    logger.info(f'Processed data shape: {processed_data.shape}.')
    logger.info('Converting data using DiscreteTransformer... Finished.')
    processed_data = self.remove_columns(processed_data, self.discrete_columns)
    return processed_data

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

class ConstInspector(Inspector):
    """
    ConstInspector is a class designed to identify columns in a DataFrame that contain constant values.
    It extends the base Inspector class and is used to fit the data and inspect it for constant columns.

    Attributes:
        const_columns (set[str]): A set of column names that contain constant values.
        const_values (dict[Any]): A dictionary mapping column names to their constant values.
        _inspect_level (int): The inspection level for this inspector, set to 80.
    """
    const_columns: set[str] = set()
    '\n    A set of column names that contain constant values. This attribute is populated during the fit method by identifying columns in the DataFrame where all values are the same.\n    '
    const_values: dict[Any] = {}
    '\n    A dictionary mapping column names to their constant values. This attribute is populated during the fit method by storing the unique value found in each constant column.\n    '
    _inspect_level = 80
    '\n    The inspection level for this inspector, set to 80. This attribute indicates the priority or depth of inspection that this inspector performs relative to other inspectors.\n    '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """
        Fit the inspector to the raw data.

        This method identifies columns in the DataFrame that contain constant values. It populates the `const_columns` set with the names of these columns and the `const_values` dictionary with the constant values found in each column.

        Args:
            raw_data (pd.DataFrame): The raw data to be inspected.

        Returns:
            None
        """
        self.const_columns = set()
        for column in raw_data.columns:
            if len(raw_data[column].value_counts(normalize=True)) == 1:
                self.const_columns.add(column)
        self.ready = True

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'const_columns': self.const_columns}

def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
    """
        Fit the inspector to the raw data.

        This method identifies columns in the DataFrame that contain constant values. It populates the `const_columns` set with the names of these columns and the `const_values` dictionary with the constant values found in each column.

        Args:
            raw_data (pd.DataFrame): The raw data to be inspected.

        Returns:
            None
        """
    self.const_columns = set()
    for column in raw_data.columns:
        if len(raw_data[column].value_counts(normalize=True)) == 1:
            self.const_columns.add(column)
    self.ready = True

class SubsetRelationshipInspector(RelationshipInspector):
    """
    Inspecting relationships by comparing two columns is subset or not. So it needs to inspect all data for prev
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maybe_related_columns: dict[str, dict[str, pd.Series]] = {}

    def _is_related(self, p: pd.Series, c: pd.Series) -> bool:
        """
        If child is subset of parent, assume related
        """
        return c.isin(p).all()

    def _build_relationship(self) -> list[Relationship]:
        r = []
        for parent, p_m_related in self.maybe_related_columns.items():
            for child, c_m_related in self.maybe_related_columns.items():
                if parent == child:
                    continue
                related_pairs = []
                for p_col, p_df in p_m_related.items():
                    for c_col, c_df in c_m_related.items():
                        if self._is_related(p_df, c_df):
                            related_pairs.append((p_col, c_col) if p_col != c_col else p_col)
                if related_pairs:
                    r.append(Relationship.build(parent, child, related_pairs))
        return r

    def fit(self, raw_data: pd.DataFrame, name: str | None=None, metadata: 'Metadata' | None=None, *args, **kwargs):
        columns = set((n for n in chain(metadata.id_columns, metadata.primary_keys)))
        for c in columns:
            cur_map = self.maybe_related_columns.setdefault(name, dict())
            cur_map[c] = pd.concat((cur_map.get(c, pd.Series()), raw_data[[c]].squeeze()), ignore_index=True)

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'relationships': self._build_relationship()}

def _is_related(self, p: pd.Series, c: pd.Series) -> bool:
    """
        If child is subset of parent, assume related
        """
    return c.isin(p).all()

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

def _is_series_fit_format(parsed_series, match_rate):
    length = len(parsed_series)
    false_num = len(list((i for i in parsed_series if i is False)))
    false_rate = false_num / length
    return false_rate >= match_rate

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

class ChinaMainlandUnifiedSocialCreditCode(RegexInspector):
    pattern = '^[0-9A-HJ-NPQRTUWXY]{2}\\d{6}[0-9A-HJ-NPQRTUWXY]{10}$'
    data_type_name = 'unified_social_credit_code'
    _inspect_level = 30
    pii = True
    pattern_ID = '^[1-9]\\d{5}(18|19|20)\\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\\d{3}[0-9Xx]$'
    p_id = re.compile(pattern_ID)

    def domain_verification(self, each_sample):
        if re.match(self.p_id, each_sample):
            return False
        return True

def domain_verification(self, each_sample):
    if re.match(self.p_id, each_sample):
        return False
    return True

class ChineseNameInspector(RegexInspector):
    pattern = chn_last_names[:600] + '][\\u4e00-\\u9fa5]{1,3}$'
    data_type_name = 'chinese_name'
    _inspect_level = 40
    pii = True

    def domain_verification(self, each_sample):

        def has_symbols(s):
            return bool(re.search('[^\\w\\s]', s))

        def has_english(s):
            return bool(re.search('[a-zA-Z]', s))

        def has_number(s):
            for char in s:
                if char.isdigit():
                    return True
            return False
        if has_number(each_sample):
            return False
        if has_english(each_sample):
            return False
        if has_symbols(each_sample):
            return False
        return True

def domain_verification(self, each_sample):

    def has_symbols(s):
        return bool(re.search('[^\\w\\s]', s))

    def has_english(s):
        return bool(re.search('[a-zA-Z]', s))

    def has_number(s):
        for char in s:
            if char.isdigit():
                return True
        return False
    if has_number(each_sample):
        return False
    if has_english(each_sample):
        return False
    if has_symbols(each_sample):
        return False
    return True

class EnglishNameInspector(RegexInspector):
    pattern = "^([a-zA-Z]{2,}\\s[a-zA-Z]{1,}'?-?[a-zA-Z]{2,}\\s?([a-zA-Z]{1,})?)"
    data_type_name = 'english_name'
    _inspect_level = 40
    pii = True
    name_min_length = 5
    '\n    The min length of the name.\n\n    GPT-4: The shortest full name in English could be something like "Ed Li" or "Al Lu", with just four characters including a space.\n    '
    name_max_length = 70
    '\n    The max length of the name.\n\n    UK Government Data Standards Catalogue suggests 35 characters for each of Given Name and Family Name, or 70 characters for a single field to hold the Full Name.\n    '

    def domain_verification(self, each_sample):

        def has_number(s):
            for char in s:
                if char.isdigit():
                    return True
            return False
        if len(each_sample) > self.name_max_length:
            return False
        if len(each_sample) < self.name_min_length:
            return False
        if has_number(each_sample):
            return False
        return True

def domain_verification(self, each_sample):

    def has_number(s):
        for char in s:
            if char.isdigit():
                return True
        return False
    if len(each_sample) > self.name_max_length:
        return False
    if len(each_sample) < self.name_min_length:
        return False
    if has_number(each_sample):
        return False
    return True

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

def get_all(self) -> ndarray:
    return np.concatenate([array for array in self.iter()], axis=1)

class DataSampler(object):
    """DataSampler samples the conditional vector and corresponding data for CTGAN."""

    def __init__(self, data: NDArrayLoader | np.ndarray, output_info: List[List[SpanInfo]], log_frequency: bool):
        self._data: NDArrayLoader | np.ndarray = data

        def is_onehot_encoding_column(column_info: List[SpanInfo]):
            return len(column_info) == 1 and column_info[0].activation_fn == 'softmax'
        n_onehot_columns = sum([1 for column_info in output_info if is_onehot_encoding_column(column_info)])
        self._onehot_column_matrix_st = np.zeros(n_onehot_columns, dtype='int32')
        self._rid_by_cat_cols = []
        st = 0
        for column_info in output_info:
            if is_onehot_encoding_column(column_info):
                span_info = column_info[0]
                ed = st + span_info.dim
                rid_by_cat = []
                for j in range(span_info.dim):
                    rid_by_cat.append(np.nonzero(data[:, st + j])[0])
                self._rid_by_cat_cols.append(rid_by_cat)
                st = ed
            else:
                st += sum([span_info.dim for span_info in column_info])
        assert st == data.shape[1]
        max_category = max([column_info[0].dim for column_info in output_info if is_onehot_encoding_column(column_info)], default=0)
        self._onehot_column_cond_st = np.zeros(n_onehot_columns, dtype='int32')
        self._onehot_column_n_category = np.zeros(n_onehot_columns, dtype='int32')
        self._onehot_column_category_prob = np.zeros((n_onehot_columns, max_category))
        self._n_onehot_columns = n_onehot_columns
        self._n_categories = sum([column_info[0].dim for column_info in output_info if is_onehot_encoding_column(column_info)])
        st = 0
        current_id = 0
        current_cond_st = 0
        for column_info in output_info:
            if is_onehot_encoding_column(column_info):
                span_info = column_info[0]
                ed = st + span_info.dim
                category_freq = np.sum(data[:, st:ed], axis=0)
                if log_frequency:
                    category_freq = np.log(category_freq + 1)
                category_prob = category_freq / np.sum(category_freq)
                self._onehot_column_category_prob[current_id, :span_info.dim] = category_prob
                self._onehot_column_cond_st[current_id] = current_cond_st
                self._onehot_column_n_category[current_id] = span_info.dim
                current_cond_st += span_info.dim
                current_id += 1
                st = ed
            else:
                st += sum([span_info.dim for span_info in column_info])
        assert st == data.shape[1]

    def _random_choice_prob_index(self, discrete_column_id):
        probs = self._onehot_column_category_prob[discrete_column_id]
        r = np.expand_dims(np.random.rand(probs.shape[0]), axis=1)
        return (probs.cumsum(axis=1) > r).argmax(axis=1)

    def sample_condvec(self, batch):
        """Generate the conditional vector for training.

        Returns:
            cond (batch x #categories):
                The conditional vector.
            mask (batch x #discrete columns):
                A one-hot vector indicating the selected discrete column.
            discrete column id (batch):
                Integer representation of mask.
            category_id_in_col (batch):
                Selected category in the selected discrete column.
        """
        if self._n_onehot_columns == 0:
            return None
        onehot_column_id = np.random.choice(np.arange(self._n_onehot_columns), batch)
        cond = np.zeros((batch, self._n_categories), dtype='float32')
        mask = np.zeros((batch, self._n_onehot_columns), dtype='float32')
        mask[np.arange(batch), onehot_column_id] = 1
        category_id_in_col = self._random_choice_prob_index(onehot_column_id)
        category_id = self._onehot_column_cond_st[onehot_column_id] + category_id_in_col
        cond[np.arange(batch), category_id] = 1
        return (cond, mask, onehot_column_id, category_id_in_col)

    def sample_original_condvec(self, batch):
        """Generate the conditional vector for generation use original frequency."""
        if self._n_onehot_columns == 0:
            return None
        cond = np.zeros((batch, self._n_categories), dtype='float32')
        for i in tqdm.tqdm(range(batch), desc='Sampling in batch', delay=3, leave=False):
            row_idx = np.random.randint(0, len(self._data))
            col_idx = np.random.randint(0, self._n_onehot_columns)
            matrix_st = self._onehot_column_matrix_st[col_idx]
            matrix_ed = matrix_st + self._onehot_column_n_category[col_idx]
            pick = np.argmax(self._data[row_idx, matrix_st:matrix_ed])
            cond[i, pick + self._onehot_column_cond_st[col_idx]] = 1
        return cond

    def sample_data(self, n, col, opt):
        """Sample data from original training data satisfying the sampled conditional vector.

        Returns:
            n rows of matrix data.
        """
        if col is None:
            idx = np.random.randint(len(self._data), size=n)
            return self._data[idx]
        idx = []
        for c, o in zip(col, opt):
            idx.append(np.random.choice(self._rid_by_cat_cols[c][o]))
        return self._data[idx]

    def dim_cond_vec(self):
        """Return the total number of categories."""
        return self._n_categories

    def generate_cond_from_condition_column_info(self, condition_info, batch):
        """Generate the condition vector."""
        vec = np.zeros((batch, self._n_categories), dtype='float32')
        id_ = self._onehot_column_matrix_st[condition_info['discrete_column_id']]
        id_ += condition_info['value_id']
        vec[:, id_] = 1
        return vec

def is_onehot_encoding_column(column_info: List[SpanInfo]):
    return len(column_info) == 1 and column_info[0].activation_fn == 'softmax'

class FrequencyEncoder(BaseTransformer):
    """Transformer for categorical data.

    This transformer computes a float representative for each one of the categories
    found in the fit data, and then replaces the instances of these categories with
    the corresponding representative.

    The representatives are decided by sorting the categorical values by their relative
    frequency, then dividing the ``[0, 1]`` interval by these relative frequencies, and
    finally assigning the middle point of each interval to the corresponding category.

    When the transformation is reverted, each value is assigned the category that
    corresponds to the interval it falls in.

    Null values are considered just another category.

    Args:
        add_noise (bool):
            Whether to generate gaussian noise around the class representative of each interval
            or just use the mean for all the replaced values. Defaults to ``False``.
    """
    INPUT_SDTYPE = 'categorical'
    SUPPORTED_SDTYPES = ['categorical', 'boolean']
    OUTPUT_SDTYPES = {'value': 'float'}
    DETERMINISTIC_REVERSE = True
    COMPOSITION_IS_IDENTITY = True
    mapping = None
    intervals = None
    starts = None
    means = None
    dtype = None

    def __setstate__(self, state):
        """Replace any ``null`` key by the actual ``np.nan`` instance."""
        intervals = state.get('intervals')
        if intervals:
            for key in list(intervals):
                if pd.isna(key):
                    intervals[np.nan] = intervals.pop(key)
        self.__dict__ = state

    def __init__(self, add_noise=False):
        self.add_noise = add_noise

    def is_transform_deterministic(self):
        """Return whether the transform is deterministic.

        Returns:
            bool:
                Whether or not the transform is deterministic.
        """
        return not self.add_noise

    @staticmethod
    def _get_intervals(data, normalized=False):
        """Compute intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to analyze.

        Returns:
            dict:
                intervals for each categorical value (start, end).
        """
        data = data.fillna(np.nan)
        frequencies = data.value_counts(dropna=False)
        start = -1.0 if normalized else 0.0
        end = 0.0
        elements = len(data)
        probes = frequencies / (elements / 2.0) if normalized else frequencies / elements
        intervals = {}
        means = []
        starts = []
        for value, prob in probes.items():
            end = start + prob
            mean = start + prob / 2
            std = prob / 6
            if pd.isna(value):
                value = np.nan
            intervals[value] = (start, end, mean, std)
            means.append(mean)
            starts.append((value, start))
            start = end
        means = pd.Series(means, index=list(frequencies.keys()))
        starts = pd.DataFrame(starts, columns=['category', 'start']).set_index('start')
        return (intervals, means, starts)

    def _fit(self, data):
        """Fit the transformer to the data.

        Compute the intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        self.dtype = data.dtype
        self.intervals, self.means, self.starts = self._get_intervals(data)

    @staticmethod
    def _clip_noised_transform(result, start, end):
        """Clip transformed values.

        Used to ensure the noise added to transformed values doesn't make it
        go out of the bounds of a given category.

        The upper bound must be slightly lower than ``end``
        so it doesn't get treated as the next category.
        """
        return np.clip(result, start, end - 1e-09)

    def _transform_by_category(self, data):
        """Transform the data by iterating over the different categories."""
        result = np.empty(shape=(len(data),), dtype=float)
        for category, values in self.intervals.items():
            start, end, mean, std = values
            if category is np.nan:
                mask = data.isna()
            else:
                mask = data.to_numpy() == category
            if self.add_noise:
                result[mask] = norm.rvs(mean, std, size=mask.sum())
                result[mask] = self._clip_noised_transform(result[mask], start, end)
            else:
                result[mask] = mean
        return result

    def _get_value(self, category):
        """Get the value that represents this category."""
        if pd.isna(category):
            category = np.nan
        start, end, mean, std = self.intervals[category]
        if self.add_noise:
            result = norm.rvs(mean, std)
            return self._clip_noised_transform(result, start, end)
        return mean

    def _transform_by_row(self, data):
        """Transform the data row by row."""
        return data.fillna(np.nan).apply(self._get_value).to_numpy()

    def _transform(self, data):
        """Transform the categorical values to float representatives.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        fit_categories = pd.Series(self.intervals.keys())
        has_nan = pd.isna(fit_categories).any()
        unseen_indexes = ~(data.isin(fit_categories) | pd.isna(data) & has_nan)
        if unseen_indexes.any():
            unseen_categories = set(data[unseen_indexes][:5])
            warnings.warn(f'The data contains {unseen_indexes.sum()} new categories that were not seen in the original data (examples: {unseen_categories}). Assigning them random values. If you want to model new categories, please fit the transformer again with the new data.')
        data[unseen_indexes] = np.random.choice(fit_categories, size=unseen_indexes.size)
        if len(self.means) < len(data):
            return self._transform_by_category(data)
        return self._transform_by_row(data)

    def _reverse_transform_by_matrix(self, data):
        """Reverse transform the data with matrix operations."""
        num_rows = len(data)
        num_categories = len(self.starts)
        data = np.broadcast_to(data, (num_categories, num_rows)).T
        starts = np.broadcast_to(self.starts.index, (num_rows, num_categories))
        is_data_greater_than_starts = (data >= starts)[:, ::-1]
        interval_indexes = num_categories - np.argmax(is_data_greater_than_starts, axis=1) - 1
        get_category_from_index = list(self.starts['category']).__getitem__
        return pd.Series(interval_indexes).apply(get_category_from_index).astype(self.dtype)

    def _reverse_transform_by_category(self, data):
        """Reverse transform the data by iterating over all the categories."""
        result = np.empty(shape=(len(data),), dtype=self.dtype)
        for category, values in self.intervals.items():
            start = values[0]
            mask = start <= data.to_numpy()
            result[mask] = category
        return pd.Series(result, index=data.index, dtype=self.dtype)

    def _get_category_from_start(self, value):
        lower = self.starts.loc[:value]
        return lower.iloc[-1].category

    def _reverse_transform_by_row(self, data):
        """Reverse transform the data by iterating over each row."""
        return data.apply(self._get_category_from_start).astype(self.dtype)

    def _reverse_transform(self, data, normalize=False):
        """Convert float values back to the original categorical values.

        Args:
            data (pd.Series):
                Data to revert.

        Returns:
            pandas.Series
        """
        data = data.clip(-1 if normalize else 0, 1)
        num_rows = len(data)
        num_categories = len(self.means)
        needed_memory = num_rows * num_categories * 8 * 3
        available_memory = psutil.virtual_memory().available
        if available_memory > needed_memory:
            return self._reverse_transform_by_matrix(data)
        if num_rows > num_categories:
            return self._reverse_transform_by_category(data)
        return self._reverse_transform_by_row(data)

@staticmethod
def _get_intervals(data, normalized=False):
    """Compute intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to analyze.

        Returns:
            dict:
                intervals for each categorical value (start, end).
        """
    data = data.fillna(np.nan)
    frequencies = data.value_counts(dropna=False)
    start = -1.0 if normalized else 0.0
    end = 0.0
    elements = len(data)
    probes = frequencies / (elements / 2.0) if normalized else frequencies / elements
    intervals = {}
    means = []
    starts = []
    for value, prob in probes.items():
        end = start + prob
        mean = start + prob / 2
        std = prob / 6
        if pd.isna(value):
            value = np.nan
        intervals[value] = (start, end, mean, std)
        means.append(mean)
        starts.append((value, start))
        start = end
    means = pd.Series(means, index=list(frequencies.keys()))
    starts = pd.DataFrame(starts, columns=['category', 'start']).set_index('start')
    return (intervals, means, starts)

def _transform_by_row(self, data):
    """Transform the data row by row."""
    return data.fillna(np.nan).apply(self._get_value).to_numpy()

def _reverse_transform_by_row(self, data):
    """Reverse transform the data by iterating over each row."""
    return data.apply(self._get_category_from_start).astype(self.dtype)

class OneHotEncoder(BaseTransformer):
    """OneHotEncoding for categorical data.

    This transformer replaces a single vector with N unique categories in it
    with N vectors which have 1s on the rows where the corresponding category
    is found and 0s on the rest.

    Null values are considered just another category.
    """
    INPUT_SDTYPE = 'categorical'
    SUPPORTED_SDTYPES = ['categorical', 'boolean']
    DETERMINISTIC_TRANSFORM = True
    DETERMINISTIC_REVERSE = True
    dummies = None
    _dummy_na = None
    _num_dummies = None
    _dummy_encoded = False
    _indexer = None
    _uniques = None

    @staticmethod
    def _prepare_data(data):
        """Transform data to appropriate format.

        If data is a valid list or a list of lists, transforms it into an np.array,
        otherwise returns it.

        Args:
            data (pandas.Series or pandas.DataFrame):
                Data to prepare.

        Returns:
            pandas.Series or numpy.ndarray
        """
        if isinstance(data, list):
            data = np.array(data)
        if len(data.shape) > 2:
            raise ValueError('Unexpected format.')
        if len(data.shape) == 2:
            if data.shape[1] != 1:
                raise ValueError('Unexpected format.')
            data = data[:, 0]
        return data

    def get_output_sdtypes(self):
        """Return the output sdtypes produced by this transformer.

        Returns:
            dict:
                Mapping from the transformed column names to the produced sdtypes.
        """
        output_sdtypes = {f'value{i}': 'float' for i in range(len(self.dummies))}
        return self._add_prefix(output_sdtypes)

    def _fit(self, data):
        """Fit the transformer to the data.

        Get the pandas `dummies` which will be used later on for OneHotEncoding.

        Args:
            data (pandas.Series or pandas.DataFrame):
                Data to fit the transformer to.
        """
        data = self._prepare_data(data)
        null = pd.isna(data)
        self._uniques = list(pd.unique(data[~null]))
        self._dummy_na = null.any()
        self._num_dummies = len(self._uniques)
        self._indexer = list(range(self._num_dummies))
        self.dummies = self._uniques.copy()
        if not np.issubdtype(data.dtype, np.number):
            self._dummy_encoded = True
        if self._dummy_na:
            self.dummies.append(np.nan)

    def _transform_helper(self, data):
        if self._dummy_encoded:
            coder = self._indexer
            codes = pd.Categorical(data, categories=self._uniques).codes
        else:
            coder = self._uniques
            codes = data
        rows = len(data)
        dummies = np.broadcast_to(coder, (rows, self._num_dummies))
        coded = np.broadcast_to(codes, (self._num_dummies, rows)).T
        array = (coded == dummies).astype(int)
        if self._dummy_na:
            null = np.zeros((rows, 1), dtype=int)
            null[pd.isna(data)] = 1
            array = np.append(array, null, axis=1)
        return array

    def _transform(self, data):
        """Replace each category with the OneHot vectors.

        Args:
            data (pandas.Series, list or list of lists):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        data = self._prepare_data(data)
        unique_data = {np.nan if pd.isna(x) else x for x in pd.unique(data)}
        unseen_categories = unique_data - set(self.dummies)
        if unseen_categories:
            examples_unseen_categories = set(list(unseen_categories)[:5])
            warnings.warn(f'The data contains {len(unseen_categories)} new categories that were not seen in the original data (examples: {examples_unseen_categories}). Creating a vector of all 0s. If you want to model new categories, please fit the transformer again with the new data.')
        return self._transform_helper(data)

    def _reverse_transform(self, data):
        """Convert float values back to the original categorical values.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to revert.

        Returns:
            pandas.Series
        """
        if not isinstance(data, np.ndarray):
            data = data.to_numpy()
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        indices = np.argmax(data, axis=1)
        return pd.Series(indices).map(self.dummies.__getitem__)

def _transform(self, data):
    """Replace each category with the OneHot vectors.

        Args:
            data (pandas.Series, list or list of lists):
                Data to transform.

        Returns:
            numpy.ndarray
        """
    data = self._prepare_data(data)
    unique_data = {np.nan if pd.isna(x) else x for x in pd.unique(data)}
    unseen_categories = unique_data - set(self.dummies)
    if unseen_categories:
        examples_unseen_categories = set(list(unseen_categories)[:5])
        warnings.warn(f'The data contains {len(unseen_categories)} new categories that were not seen in the original data (examples: {examples_unseen_categories}). Creating a vector of all 0s. If you want to model new categories, please fit the transformer again with the new data.')
    return self._transform_helper(data)

class LabelEncoder(BaseTransformer):
    """LabelEncoding for categorical data.

    This transformer generates a unique integer representation for each category
    and simply replaces each category with its integer value.

    Null values are considered just another category.

    Attributes:
        values_to_categories (dict):
            Dictionary that maps each integer value for its category.
        categories_to_values (dict):
            Dictionary that maps each category with the corresponding
            integer value.

    Args:
        add_noise (bool):
            Whether to generate uniform noise around the label for each category.
            Defaults to ``False``.
        order_by (None or str):
            A string defining how to order the categories before assigning them labels. Defaults to
            ``None``. Options include:
            - ``'numerical_value'``: Order the categories by numerical value.
            - ``'alphabetical'``: Order the categories alphabetically.
            - ``None``: Use the order that the categories appear in when fitting.
    """
    INPUT_SDTYPE = 'categorical'
    SUPPORTED_SDTYPES = ['categorical', 'boolean']
    OUTPUT_SDTYPES = {'value': 'float'}
    DETERMINISTIC_TRANSFORM = True
    DETERMINISTIC_REVERSE = True
    COMPOSITION_IS_IDENTITY = True
    values_to_categories = None
    categories_to_values = None

    def __init__(self, add_noise=False, order_by=None):
        self.add_noise = add_noise
        if order_by not in [None, 'alphabetical', 'numerical_value']:
            raise Error("order_by must be one of the following values: None, 'numerical_value' or 'alphabetical'")
        self.order_by = order_by

    def _order_categories(self, unique_data):
        if self.order_by == 'alphabetical':
            if unique_data.dtype.type not in [np.str_, np.object_]:
                raise Error("The data must be of type string if order_by is 'alphabetical'.")
        elif self.order_by == 'numerical_value':
            if not np.issubdtype(unique_data.dtype.type, np.number):
                raise Error("The data must be numerical if order_by is 'numerical_value'.")
        if self.order_by is not None:
            nans = pd.isna(unique_data)
            unique_data = np.sort(unique_data[~nans])
            if nans.any():
                unique_data = np.append(unique_data, [np.nan])
        return unique_data

    def _fit(self, data):
        """Fit the transformer to the data.

        Generate a unique integer representation for each category and
        store them in the ``categories_to_values`` dict and its reverse
        ``values_to_categories``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        unique_data = pd.unique(data.fillna(np.nan))
        unique_data = self._order_categories(unique_data)
        self.values_to_categories = dict(enumerate(unique_data))
        self.categories_to_values = {category: value for value, category in self.values_to_categories.items()}

    def _transform(self, data):
        """Replace each category with its corresponding integer value.

        If a category has not been seen before, a random value is assigned.

        If ``add_noise`` is True, the integer values will be replaced by a
        random number between the value and the value + 1.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            pd.Series
        """
        mapped = data.fillna(np.nan).map(self.categories_to_values)
        is_null = mapped.isna()
        if is_null.any():
            unseen_categories = set(data[is_null][:5])
            warnings.warn(f'The data contains {is_null.sum()} new categories that were not seen in the original data (examples: {unseen_categories}). Assigning them random values. If you want to model new categories, please fit the transformer again with the new data.')
        mapped[is_null] = np.random.randint(len(self.categories_to_values), size=is_null.sum())
        if self.add_noise:
            mapped = np.random.uniform(mapped, mapped + 1)
        return mapped

    def _reverse_transform(self, data):
        """Convert float values back to the original categorical values.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to revert.

        Returns:
            pandas.Series
        """
        if self.add_noise:
            data = np.floor(data)
        data = data.clip(min(self.values_to_categories), max(self.values_to_categories))
        return data.round().map(self.values_to_categories)

def _fit(self, data):
    """Fit the transformer to the data.

        Generate a unique integer representation for each category and
        store them in the ``categories_to_values`` dict and its reverse
        ``values_to_categories``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
    unique_data = pd.unique(data.fillna(np.nan))
    unique_data = self._order_categories(unique_data)
    self.values_to_categories = dict(enumerate(unique_data))
    self.categories_to_values = {category: value for value, category in self.values_to_categories.items()}

class NormalizedLabelEncoder(LabelEncoder):
    """Same to the LabelEncoder except the transform result will be [-1, 1] instead of positive integer."""

    def __init__(self, order_by=None):
        super().__init__(False, order_by)
        self._round_digit = None

    def _order_categories(self, unique_data):
        if self.order_by == 'alphabetical':
            if unique_data.dtype.type not in [np.str_, np.object_]:
                pass
        elif self.order_by == 'numerical_value':
            if not np.issubdtype(unique_data.dtype.type, np.number):
                pass
        if self.order_by is not None:
            nans = pd.isna(unique_data)
            unique_data = np.sort(unique_data[~nans])
            if nans.any():
                unique_data = np.append(unique_data, [np.nan])
        return unique_data

    def _fit(self, data):
        """Fit the transformer to the data.

        Generate a unique integer representation for each category and
        store them in the ``categories_to_values`` dict and its reverse
        ``values_to_categories``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        unique_data = pd.unique(data.fillna(np.nan))
        unique_data = self._order_categories(unique_data)

        def normalize_array_to_dict(arr):
            n = len(arr)
            digit = math.ceil(math.log10(n)) + 1
            self._round_digit = digit
            normalized_dict = {round(2 * i / (n - 1) - 1, digit): arr[i] for i in range(n)}
            return normalized_dict
        self.values_to_categories = normalize_array_to_dict(unique_data)
        self.categories_to_values = {category: value for value, category in self.values_to_categories.items()}

    def _reverse_transform(self, data):
        """Convert float values back to the original categorical values.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to revert.

        Returns:
            pandas.Series
        """
        value_dict_keys = self.values_to_categories.keys()
        value_dict = self.values_to_categories

        def find_nearest_key(x):
            nearest_key = min(value_dict_keys, key=lambda k: abs(k - x))
            return value_dict[nearest_key]
        data: pd.Series = data.clip(min(self.values_to_categories), max(self.values_to_categories))
        return data.apply(find_nearest_key)

def _fit(self, data):
    """Fit the transformer to the data.

        Generate a unique integer representation for each category and
        store them in the ``categories_to_values`` dict and its reverse
        ``values_to_categories``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
    unique_data = pd.unique(data.fillna(np.nan))
    unique_data = self._order_categories(unique_data)

    def normalize_array_to_dict(arr):
        n = len(arr)
        digit = math.ceil(math.log10(n)) + 1
        self._round_digit = digit
        normalized_dict = {round(2 * i / (n - 1) - 1, digit): arr[i] for i in range(n)}
        return normalized_dict
    self.values_to_categories = normalize_array_to_dict(unique_data)
    self.categories_to_values = {category: value for value, category in self.values_to_categories.items()}

class CustomLabelEncoder(LabelEncoder):
    """Custom label encoder for categorical data.

    This class works very similarly to the ``LabelEncoder``, except that it requires the ordering
    for the labels to be provided.

    Null values are considered just another category.

    Args:
        order (list):
            A list of all the unique categories for the data. The order of the list determines the
            label that each category will get.
        add_noise (bool):
            Whether to generate uniform noise around the label for each category.
            Defaults to ``False``.
    """

    def __init__(self, order, add_noise=False):
        self.order = pd.Series(order).fillna(np.nan)
        super().__init__(add_noise=add_noise)

    def _fit(self, data):
        """Fit the transformer to the data.

        Generate a unique integer representation for each category and
        store them in the ``categories_to_values`` dict and its reverse
        ``values_to_categories``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        data = data.fillna(np.nan)
        missing = list(data[~data.isin(self.order)].unique())
        if len(missing) > 0:
            raise Error(f"Unknown categories '{missing}'. All possible categories must be defined in the 'order' parameter.")
        self.values_to_categories = dict(enumerate(self.order))
        self.categories_to_values = {category: value for value, category in self.values_to_categories.items()}

def _fit(self, data):
    """Fit the transformer to the data.

        Generate a unique integer representation for each category and
        store them in the ``categories_to_values`` dict and its reverse
        ``values_to_categories``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
    data = data.fillna(np.nan)
    missing = list(data[~data.isin(self.order)].unique())
    if len(missing) > 0:
        raise Error(f"Unknown categories '{missing}'. All possible categories must be defined in the 'order' parameter.")
    self.values_to_categories = dict(enumerate(self.order))
    self.categories_to_values = {category: value for value, category in self.values_to_categories.items()}

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

def _literal(character, max_repeat):
    del max_repeat
    return (iter([chr(character)]), 1)

def _range(options, max_repeat):
    del max_repeat
    min_value, max_value = options
    max_value += 1
    return ((chr(value) for value in range(min_value, max_value)), max_value - min_value)

def _any(options, max_repeat):
    del options
    del max_repeat
    return (iter(string.printable), len(string.printable))

def _category_chars(regex):
    return [char for char in string.printable if regex.match(char)]

def _category(category, max_repeat):
    del max_repeat
    characters = _CATEGORIES[category]
    return (iter(characters), len(characters))

class NullTransformer:
    """Transformer for data that contains Null values.

    Args:
        missing_value_replacement (object or None):
            Indicate what to do with the null values. If an integer, float or string is given,
            replace them with the given value. If the strings ``'mean'`` or ``'mode'`` are given,
            replace them with the corresponding aggregation (``'mean'`` only works for numerical
            values). If ``None`` is given, do not replace them. Defaults to ``None``.
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
    """
    nulls = None
    _model_missing_values = None
    _missing_value_replacement = None
    _null_percentage = None

    def __init__(self, missing_value_replacement=None, model_missing_values=False):
        self._missing_value_replacement = missing_value_replacement
        self._model_missing_values = model_missing_values

    def models_missing_values(self):
        """Indicate whether this transformer creates a null column on transform.

        Returns:
            bool:
                Whether a null column is created on transform.
        """
        return self._model_missing_values

    def _get_missing_value_replacement(self, data):
        """Get the fill value to use for the given data.

        Args:
            data (pd.Series):
                The data that is being transformed.

        Return:
            object:
                The fill value that needs to be used.
        """
        if self._missing_value_replacement is None:
            return None
        if self._missing_value_replacement == 'mean':
            return data.mean()
        if self._missing_value_replacement == 'mode':
            return data.mode(dropna=True)[0]
        return self._missing_value_replacement

    def fit(self, data):
        """Fit the transformer to the data.

        Evaluate if the transformer has to create the null column or not.

        Args:
            data (pandas.Series):
                Data to transform.
        """
        null_values = data.isna().to_numpy()
        self.nulls = null_values.any()
        self._missing_value_replacement = self._get_missing_value_replacement(data)
        if not self.nulls and self._model_missing_values:
            self._model_missing_values = False
            guidance_message = f'Guidance: There are no missing values in column {data.name}. Extra column not created.'
            LOGGER.info(guidance_message)
        if not self._model_missing_values:
            self._null_percentage = null_values.sum() / len(data)

    def transform(self, data):
        """Replace null values with the indicated ``missing_value_replacement``.

        If required, create the null indicator column.

        Args:
            data (pandas.Series or numpy.ndarray):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        isna = data.isna()
        if isna.any() and self._missing_value_replacement is not None:
            data = data.fillna(self._missing_value_replacement)
        if self._model_missing_values:
            return pd.concat([data, isna.astype(np.float64)], axis=1).to_numpy()
        return data.to_numpy()

    def reverse_transform(self, data):
        """Restore null values to the data.

        If a null indicator column was created during fit, use it as a reference.
        Otherwise, randomly replace values with ``np.nan``. The percentage of values
        that will be replaced is the percentage of null values seen in the fitted data.

        Args:
            data (numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series
        """
        data = data.copy()
        if self._model_missing_values:
            if self.nulls:
                isna = data[:, 1] > 0.5
            data = data[:, 0]
        elif self.nulls:
            isna = np.random.random((len(data),)) < self._null_percentage
        data = pd.Series(data)
        if self.nulls and isna.any():
            data.loc[isna] = np.nan
        return data

def transform(self, data):
    """Replace null values with the indicated ``missing_value_replacement``.

        If required, create the null indicator column.

        Args:
            data (pandas.Series or numpy.ndarray):
                Data to transform.

        Returns:
            numpy.ndarray
        """
    isna = data.isna()
    if isna.any() and self._missing_value_replacement is not None:
        data = data.fillna(self._missing_value_replacement)
    if self._model_missing_values:
        return pd.concat([data, isna.astype(np.float64)], axis=1).to_numpy()
    return data.to_numpy()

def reverse_transform(self, data):
    """Restore null values to the data.

        If a null indicator column was created during fit, use it as a reference.
        Otherwise, randomly replace values with ``np.nan``. The percentage of values
        that will be replaced is the percentage of null values seen in the fitted data.

        Args:
            data (numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series
        """
    data = data.copy()
    if self._model_missing_values:
        if self.nulls:
            isna = data[:, 1] > 0.5
        data = data[:, 0]
    elif self.nulls:
        isna = np.random.random((len(data),)) < self._null_percentage
    data = pd.Series(data)
    if self.nulls and isna.any():
        data.loc[isna] = np.nan
    return data

def evaluate_transformer_performance(transformer, dataset_generator, verbose=False):
    """Evaluate the given transformer's performance against the given dataset generator.

    Args:
        transformer (rdt.transformers.BaseTransformer):
            The transformer to evaluate.
        dataset_generator (rdt.tests.datasets.BaseDatasetGenerator):
            The dataset generator to performance test against.
        verbose (bool):
            Whether or not to add extra columns about the dataset and transformer,
            and return data for all dataset sizes. If false, it will only return
            the max performance values of all the dataset sizes used.

    Returns:
        pandas.DataFrame:
            The performance test results.
    """
    transformer_args = TRANSFORMER_ARGS.get(transformer.__name__, {})
    transformer_instance = transformer(**transformer_args)
    sizes = _get_dataset_sizes(dataset_generator.SDTYPE)
    out = []
    for fit_size, transform_size in sizes:
        performance = profile_transformer(transformer=transformer_instance, dataset_generator=dataset_generator, fit_size=fit_size, transform_size=transform_size)
        size = np.array([fit_size, transform_size, transform_size] * 2)
        performance = performance / size
        if verbose:
            performance = performance.rename(lambda x: x + ' (s)' if 'Time' in x else x + ' (B)')
            performance['Number of fit rows'] = fit_size
            performance['Number of transform rows'] = transform_size
            performance['Dataset'] = dataset_generator.__name__
            performance['Transformer'] = f'{transformer.__module__}.{transformer.__name__}'
        out.append(performance)
    summary = pd.DataFrame(out)
    if verbose:
        return summary
    return summary.max(axis=0)

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

class ScipyModel(Univariate, ABC):
    """Wrapper for scipy models.

    This class makes the probability_density, cumulative_distribution,
    percent_point and sample point at the underlying pdf, cdf, ppd and rvs
    methods respectively.

    fit, _get_params and _set_params must be implemented by the subclasses.
    """
    MODEL_CLASS = None
    _params = None

    def __init__(self, random_state=None):
        """Initialize Scipy model.

        Overwrite Univariate __init__ to skip candidate initialization.

        Args:
            random_state (int, np.random.RandomState, or None): seed
                or RandomState for random generator.
        """
        self.random_state = validate_random_state(random_state)

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
        return self.MODEL_CLASS.pdf(X, **self._params)

    def log_probability_density(self, X):
        """Compute the log of the probability density for each point in X.

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
        if hasattr(self.MODEL_CLASS, 'logpdf'):
            return self.MODEL_CLASS.logpdf(X, **self._params)
        return np.log(self.probability_density(X))

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
        return self.MODEL_CLASS.cdf(X, **self._params)

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
        return self.MODEL_CLASS.ppf(U, **self._params)

    @random_state
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
        return self.MODEL_CLASS.rvs(size=n_samples, **self._params)

    def _fit(self, X):
        """Fit the model to a non-constant random variable.

        Must be implemented in all the subclasses.

        Arguments:
            X (numpy.ndarray):
                Values of the random variable. It must have shape (n, 1).
        """
        raise NotImplementedError()

    def fit(self, X):
        """Fit the model to a random variable.

        Arguments:
            X (numpy.ndarray):
                Values of the random variable. It must have shape (n, 1).
        """
        if self._check_constant_value(X):
            self._fit_constant(X)
        else:
            self._fit(X)
        self.fitted = True

    def _get_params(self):
        """Return attributes from self._model to serialize.

        Must be implemented in all the subclasses.

        Returns:
            dict:
                Parameters to recreate self._model in its current fit status.
        """
        return self._params.copy()

    def _set_params(self, params):
        """Set the parameters of this univariate.

        Args:
            params (dict):
                Parameters to recreate this instance.
        """
        self._params = params.copy()
        if self._is_constant():
            constant = self._extract_constant()
            self._set_constant_value(constant)

def _get_params(self):
    """Return attributes from self._model to serialize.

        Must be implemented in all the subclasses.

        Returns:
            dict:
                Parameters to recreate self._model in its current fit status.
        """
    return self._params.copy()

def _set_params(self, params):
    """Set the parameters of this univariate.

        Args:
            params (dict):
                Parameters to recreate this instance.
        """
    self._params = params.copy()
    if self._is_constant():
        constant = self._extract_constant()
        self._set_constant_value(constant)

class BetaUnivariate(ScipyModel):
    """Wrapper around scipy.stats.beta.

    Documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html
    """
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.BOUNDED
    MODEL_CLASS = beta

    def _fit_constant(self, X):
        self._params = {'a': 1.0, 'b': 1.0, 'loc': np.unique(X)[0], 'scale': 0.0}

    def _fit(self, X):
        loc = np.min(X)
        scale = np.max(X) - loc
        a, b, loc, scale = beta.fit(X, loc=loc, scale=scale)
        self._params = {'loc': loc, 'scale': scale, 'a': a, 'b': b}

    def _is_constant(self):
        return self._params['scale'] == 0

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    self._params = {'a': 1.0, 'b': 1.0, 'loc': np.unique(X)[0], 'scale': 0.0}

class TruncatedGaussian(ScipyModel):
    """Wrapper around scipy.stats.truncnorm.

    Documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.truncnorm.html
    """
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.BOUNDED
    MODEL_CLASS = truncnorm

    @store_args
    def __init__(self, minimum=None, maximum=None, random_state=None):
        self.random_state = validate_random_state(random_state)
        self.min = minimum
        self.max = maximum

    def _fit_constant(self, X):
        constant = np.unique(X)[0]
        self._params = {'a': constant, 'b': constant, 'loc': constant, 'scale': 0.0}

    def _fit(self, X):
        if self.min is None:
            self.min = X.min() - EPSILON
        if self.max is None:
            self.max = X.max() + EPSILON

        def nnlf(params):
            loc, scale = params
            a = (self.min - loc) / scale
            b = (self.max - loc) / scale
            return truncnorm.nnlf((a, b, loc, scale), X)
        initial_params = (X.mean(), X.std())
        optimal = fmin_slsqp(nnlf, initial_params, iprint=False, bounds=[(self.min, self.max), (0.0, (self.max - self.min) ** 2)])
        loc, scale = optimal
        a = (self.min - loc) / scale
        b = (self.max - loc) / scale
        self._params = {'a': a, 'b': b, 'loc': loc, 'scale': scale}

    def _is_constant(self):
        return self._params['a'] == self._params['b']

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    constant = np.unique(X)[0]
    self._params = {'a': constant, 'b': constant, 'loc': constant, 'scale': 0.0}

class GaussianKDE(ScipyModel):
    """A wrapper for gaussian Kernel density estimation.

    It was implemented in scipy.stats toolbox. gaussian_kde is slower than statsmodels
    but allows more flexibility.

    When a sample_size is provided the fit method will sample the
    data, and mask the real information. Also, ensure the number of
    entries will be always the value of sample_size.

    Args:
        sample_size(int): amount of parameters to sample
    """
    PARAMETRIC = ParametricType.NON_PARAMETRIC
    BOUNDED = BoundedType.UNBOUNDED
    MODEL_CLASS = gaussian_kde

    @store_args
    def __init__(self, sample_size=None, random_state=None, bw_method=None, weights=None):
        self.random_state = validate_random_state(random_state)
        self._sample_size = sample_size
        self.bw_method = bw_method
        self.weights = weights

    def _get_model(self):
        dataset = self._params['dataset']
        self._sample_size = self._sample_size or len(dataset)
        return gaussian_kde(dataset, bw_method=self.bw_method, weights=self.weights)

    def _get_bounds(self):
        X = self._params['dataset']
        lower = np.min(X) - 5 * np.std(X)
        upper = np.max(X) + 5 * np.std(X)
        return (lower, upper)

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
        return self._model.evaluate(X)

    @random_state
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
        return self._model.resample(size=n_samples)[0]

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
        X = np.array(X)
        stdev = np.sqrt(self._model.covariance[0, 0])
        lower = ndtr((self._get_bounds()[0] - self._model.dataset) / stdev)[0]
        uppers = ndtr((X[:, None] - self._model.dataset) / stdev)
        return (uppers - lower).dot(self._model.weights)

    def percent_point(self, U, method='chandrupatla'):
        """Compute the inverse cumulative distribution value for each point in U.

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].
            method (str):
                Whether to use the `chandrupatla` or `bisect` solver.

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        if len(U.shape) > 1:
            raise ValueError(f'Expected 1d array, got {(U,)}.')
        if np.any(U > 1.0) or np.any(U < 0.0):
            raise ValueError('Expected values in range [0.0, 1.0].')
        is_one = U >= 1.0 - EPSILON
        is_zero = U <= EPSILON
        is_valid = ~(is_zero | is_one)
        lower, upper = self._get_bounds()

        def _f(X):
            return self.cumulative_distribution(X) - U[is_valid]
        X = np.zeros(U.shape)
        X[is_one] = float('inf')
        X[is_zero] = float('-inf')
        if is_valid.any():
            lower = np.full(U[is_valid].shape, lower)
            upper = np.full(U[is_valid].shape, upper)
            if method == 'bisect':
                X[is_valid] = bisect(_f, lower, upper)
            else:
                X[is_valid] = chandrupatla(_f, lower, upper)
        return X

    def _fit_constant(self, X):
        sample_size = self._sample_size or len(X)
        constant = np.unique(X)[0]
        self._params = {'dataset': [constant] * sample_size}

    def _fit(self, X):
        if self._sample_size:
            X = gaussian_kde(X, bw_method=self.bw_method, weights=self.weights).resample(self._sample_size)
        self._params = {'dataset': X.tolist()}
        self._model = self._get_model()

    def _is_constant(self):
        return len(np.unique(self._params['dataset'])) == 1

    def _extract_constant(self):
        return self._params['dataset'][0]

    def _set_params(self, params):
        """Set the parameters of this univariate.

        Args:
            params (dict):
                Parameters to recreate this instance.
        """
        self._params = params.copy()
        if self._is_constant():
            constant = self._extract_constant()
            self._set_constant_value(constant)
        else:
            self._model = self._get_model()

def _get_model(self):
    dataset = self._params['dataset']
    self._sample_size = self._sample_size or len(dataset)
    return gaussian_kde(dataset, bw_method=self.bw_method, weights=self.weights)

@random_state
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
    return self._model.resample(size=n_samples)[0]

def _fit_constant(self, X):
    sample_size = self._sample_size or len(X)
    constant = np.unique(X)[0]
    self._params = {'dataset': [constant] * sample_size}

def _fit(self, X):
    if self._sample_size:
        X = gaussian_kde(X, bw_method=self.bw_method, weights=self.weights).resample(self._sample_size)
    self._params = {'dataset': X.tolist()}
    self._model = self._get_model()

def _is_constant(self):
    return len(np.unique(self._params['dataset'])) == 1

def _set_params(self, params):
    """Set the parameters of this univariate.

        Args:
            params (dict):
                Parameters to recreate this instance.
        """
    self._params = params.copy()
    if self._is_constant():
        constant = self._extract_constant()
        self._set_constant_value(constant)
    else:
        self._model = self._get_model()

class GaussianUnivariate(ScipyModel):
    """Gaussian univariate model."""
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.UNBOUNDED
    MODEL_CLASS = norm

    def _fit_constant(self, X):
        self._params = {'loc': np.unique(X)[0], 'scale': 0}

    def _fit(self, X):
        self._params = {'loc': np.mean(X), 'scale': np.std(X)}

    def _is_constant(self):
        return self._params['scale'] == 0

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    self._params = {'loc': np.unique(X)[0], 'scale': 0}

class GammaUnivariate(ScipyModel):
    """Wrapper around scipy.stats.gamma.

    Documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.gamma.html
    """
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.SEMI_BOUNDED
    MODEL_CLASS = gamma

    def _fit_constant(self, X):
        self._params = {'a': 0.0, 'loc': np.unique(X)[0], 'scale': 0.0}

    def _fit(self, X):
        a, loc, scale = gamma.fit(X)
        self._params = {'a': a, 'loc': loc, 'scale': scale}

    def _is_constant(self):
        return self._params['scale'] == 0

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    self._params = {'a': 0.0, 'loc': np.unique(X)[0], 'scale': 0.0}

class LogLaplace(ScipyModel):
    """Wrapper around scipy.stats.loglaplace.

    Documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.loglaplace.html
    """
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.SEMI_BOUNDED
    MODEL_CLASS = loglaplace

    def _fit_constant(self, X):
        self._params = {'c': 2.0, 'loc': np.unique(X)[0], 'scale': 0.0}

    def _fit(self, X):
        c, loc, scale = loglaplace.fit(X)
        self._params = {'c': c, 'loc': loc, 'scale': scale}

    def _is_constant(self):
        return self._params['scale'] == 0

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    self._params = {'c': 2.0, 'loc': np.unique(X)[0], 'scale': 0.0}

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

def _get_constraints(self):
    """Get neighboring edges for each edge in the edges."""
    num_edges = len(self.edges)
    for k in range(num_edges):
        for i in range(num_edges):
            if k != i and self.edges[k].is_adjacent(self.edges[i]):
                self.edges[k].neighbors.append(i)

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

class DataSampler(object):
    """DataSampler samples the conditional vector and corresponding data for CTGAN."""

    def __init__(self, data, output_info, log_frequency):
        self._data = data

        def is_discrete_column(column_info):
            return len(column_info) == 1 and column_info[0].activation_fn == 'softmax'
        n_discrete_columns = sum([1 for column_info in output_info if is_discrete_column(column_info)])
        self._discrete_column_matrix_st = np.zeros(n_discrete_columns, dtype='int32')
        self._rid_by_cat_cols = []
        st = 0
        for column_info in output_info:
            if is_discrete_column(column_info):
                span_info = column_info[0]
                ed = st + span_info.dim
                rid_by_cat = []
                for j in range(span_info.dim):
                    rid_by_cat.append(np.nonzero(data[:, st + j])[0])
                self._rid_by_cat_cols.append(rid_by_cat)
                st = ed
            else:
                st += sum([span_info.dim for span_info in column_info])
        assert st == data.shape[1]
        max_category = max([column_info[0].dim for column_info in output_info if is_discrete_column(column_info)], default=0)
        self._discrete_column_cond_st = np.zeros(n_discrete_columns, dtype='int32')
        self._discrete_column_n_category = np.zeros(n_discrete_columns, dtype='int32')
        self._discrete_column_category_prob = np.zeros((n_discrete_columns, max_category))
        self._n_discrete_columns = n_discrete_columns
        self._n_categories = sum([column_info[0].dim for column_info in output_info if is_discrete_column(column_info)])
        st = 0
        current_id = 0
        current_cond_st = 0
        for column_info in output_info:
            if is_discrete_column(column_info):
                span_info = column_info[0]
                ed = st + span_info.dim
                category_freq = np.sum(data[:, st:ed], axis=0)
                if log_frequency:
                    category_freq = np.log(category_freq + 1)
                category_prob = category_freq / np.sum(category_freq)
                self._discrete_column_category_prob[current_id, :span_info.dim] = category_prob
                self._discrete_column_cond_st[current_id] = current_cond_st
                self._discrete_column_n_category[current_id] = span_info.dim
                current_cond_st += span_info.dim
                current_id += 1
                st = ed
            else:
                st += sum([span_info.dim for span_info in column_info])

    def _random_choice_prob_index(self, discrete_column_id):
        probs = self._discrete_column_category_prob[discrete_column_id]
        r = np.expand_dims(np.random.rand(probs.shape[0]), axis=1)
        return (probs.cumsum(axis=1) > r).argmax(axis=1)

    def sample_condvec(self, batch):
        """Generate the conditional vector for training.

        Returns:
            cond (batch x #categories):
                The conditional vector.
            mask (batch x #discrete columns):
                A one-hot vector indicating the selected discrete column.
            discrete column id (batch):
                Integer representation of mask.
            category_id_in_col (batch):
                Selected category in the selected discrete column.
        """
        if self._n_discrete_columns == 0:
            return None
        discrete_column_id = np.random.choice(np.arange(self._n_discrete_columns), batch)
        cond = np.zeros((batch, self._n_categories), dtype='float32')
        mask = np.zeros((batch, self._n_discrete_columns), dtype='float32')
        mask[np.arange(batch), discrete_column_id] = 1
        category_id_in_col = self._random_choice_prob_index(discrete_column_id)
        category_id = self._discrete_column_cond_st[discrete_column_id] + category_id_in_col
        cond[np.arange(batch), category_id] = 1
        return (cond, mask, discrete_column_id, category_id_in_col)

    def sample_original_condvec(self, batch):
        """Generate the conditional vector for generation use original frequency."""
        if self._n_discrete_columns == 0:
            return None
        cond = np.zeros((batch, self._n_categories), dtype='float32')
        for i in range(batch):
            row_idx = np.random.randint(0, len(self._data))
            col_idx = np.random.randint(0, self._n_discrete_columns)
            matrix_st = self._discrete_column_matrix_st[col_idx]
            matrix_ed = matrix_st + self._discrete_column_n_category[col_idx]
            pick = np.argmax(self._data[row_idx, matrix_st:matrix_ed])
            cond[i, pick + self._discrete_column_cond_st[col_idx]] = 1
        return cond

    def sample_data(self, n, col, opt):
        """Sample data from original training data satisfying the sampled conditional vector.

        Returns:
            n rows of matrix data.
        """
        if col is None:
            idx = np.random.randint(len(self._data), size=n)
            return self._data[idx]
        idx = []
        for c, o in zip(col, opt):
            idx.append(np.random.choice(self._rid_by_cat_cols[c][o]))
        return self._data[idx]

    def dim_cond_vec(self):
        """Return the total number of categories."""
        return self._n_categories

    def generate_cond_from_condition_column_info(self, condition_info, batch):
        """Generate the condition vector."""
        vec = np.zeros((batch, self._n_categories), dtype='float32')
        id_ = self._discrete_column_matrix_st[condition_info['discrete_column_id']]
        id_ += condition_info['value_id']
        vec[:, id_] = 1
        return vec

def is_discrete_column(column_info):
    return len(column_info) == 1 and column_info[0].activation_fn == 'softmax'

class GaussianCopulaSynthesizerModel(StatisticSynthesizerModel):
    """Model wrapping ``copulas.multivariate.GaussianMultivariate`` copula.

    Args:
        metadata (sdgx.data_models.metadata.Metadata):
            Metadata of the input table.
        enforce_min_max_values (bool):
            Specify whether or not to clip the data returned by ``reverse_transform`` of
            the numerical transformer, ``FloatFormatter``, to the min and max values seen
            during ``fit``. Defaults to ``True``.
        enforce_rounding (bool):
            Define rounding scheme for ``numerical`` columns. If ``True``, the data returned
            by ``reverse_transform`` will be rounded as in the original data. Defaults to ``True``.
        locales (list or str):
            The default locale(s) to use for AnonymizedFaker transformers. Defaults to ``None``.
        numerical_distributions (dict):
            Dictionary that maps field names from the table that is being modeled with
            the distribution that needs to be used. The distributions can be passed as either
            a ``copulas.univariate`` instance or as one of the following values:

                * ``norm``: Use a norm distribution.
                * ``beta``: Use a Beta distribution.
                * ``truncnorm``: Use a truncnorm distribution.
                * ``uniform``: Use a uniform distribution.
                * ``gamma``: Use a Gamma distribution.
                * ``gaussian_kde``: Use a GaussianKDE distribution. This model is non-parametric,
                  so using this will make ``get_parameters`` unusable.

        default_distribution (str):
            Copulas univariate distribution to use by default. Valid options are:

                * ``norm``: Use a norm distribution.
                * ``beta``: Use a Beta distribution.
                * ``truncnorm``: Use a Truncated Gaussian distribution.
                * ``uniform``: Use a uniform distribution.
                * ``gamma``: Use a Gamma distribution.
                * ``gaussian_kde``: Use a GaussianKDE distribution. This model is non-parametric,
                  so using this will make ``get_parameters`` unusable.
             Defaults to ``beta``.
    """
    _DISTRIBUTIONS = {'norm': copulas.univariate.GaussianUnivariate, 'beta': copulas.univariate.BetaUnivariate, 'truncnorm': copulas.univariate.TruncatedGaussian, 'gamma': copulas.univariate.GammaUnivariate, 'uniform': copulas.univariate.UniformUnivariate, 'gaussian_kde': copulas.univariate.GaussianKDE}
    _model = None

    @classmethod
    def get_distribution_class(cls, distribution):
        """Return the corresponding distribution class from ``copulas.univariate``.

        Args:
            distribution (str):
                A string representing a copulas univariate distribution.

        Returns:
            copulas.univariate:
                A copulas univariate class that corresponds to the distribution.
        """
        if not isinstance(distribution, str) or distribution not in cls._DISTRIBUTIONS:
            error_message = f"Invalid distribution specification '{distribution}'."
            raise ValueError(error_message)
        return cls._DISTRIBUTIONS[distribution]

    def __init__(self, metadata: Metadata=None, enforce_min_max_values=True, enforce_rounding=True, locales=None, numerical_distributions=None, default_distribution=None):
        self.metadata = metadata
        self.enforce_min_max_values = (enforce_min_max_values,)
        self.enforce_rounding = (enforce_rounding,)
        self.locales = (locales,)
        if isinstance(self.metadata, Metadata):
            self.discrete_cols = self.metadata.discrete_columns
        else:
            self.discrete_cols = None
        validate_numerical_distributions(numerical_distributions, self.metadata)
        self.numerical_distributions = numerical_distributions or {}
        self.default_distribution = default_distribution or 'beta'
        self._default_distribution = self.get_distribution_class(self.default_distribution)
        self._numerical_distributions = {field: self.get_distribution_class(distribution) for field, distribution in self.numerical_distributions.items()}
        self._num_rows = None
        self._transformer = None

    def fit(self, metadata: Metadata, dataloader: DataLoader, *args, **kwargs):
        processed_data: pd.DataFrame = dataloader.load_all()
        self.discrete_cols = list(metadata.get('discrete_columns'))
        self.metadata = metadata
        self._transformer = StatisticDataTransformer()
        self._transformer.fit(processed_data, self.discrete_cols)
        processed_data = pd.DataFrame(self._transformer.transform(processed_data))
        '\n        log_numerical_distributions_error(\n            self.numerical_distributions, processed_data.columns, LOGGER\n        )\n        '
        self._num_rows = len(processed_data)
        numerical_distributions = deepcopy(self._numerical_distributions)
        for column in processed_data.columns:
            if column not in numerical_distributions:
                numerical_distributions[column] = self._numerical_distributions.get(column, self._default_distribution)
        self._model = multivariate.GaussianMultivariate(distribution=numerical_distributions)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', module='scipy')
            self._model.fit(processed_data)

    def sample(self, num_rows, conditions=None):
        """Sample the indicated number of rows from the model.

        Args:
            num_rows (int):
                Amount of rows to sample.
            conditions (dict):
                If specified, this dictionary maps column names to the column
                value. Then, this method generates ``num_rows`` samples, all of
                which are conditioned on the given variables.

        Returns:
            pandas.DataFrame:
                Sampled data.
        """
        return self._transformer.inverse_transform(self._model.sample(num_rows, conditions=conditions).to_numpy())

    def _get_valid_columns_from_metadata(self, columns):
        valid_columns = []
        for column in columns:
            for valid_column in self.metadata.column_list:
                if column.startswith(valid_column):
                    valid_columns.append(column)
                    break
        return valid_columns

    def get_learned_distributions(self):
        """Get the marginal distributions used by the ``GaussianCopula``.

        Return a dictionary mapping the column names with the distribution name and the learned
        parameters for those.

        Returns:
            dict:
                Dictionary containing the distributions used or detected for each column and the
                learned parameters for those.
        """
        if not self._fitted:
            raise ValueError("Distributions have not been learned yet. Please fit your model first using 'fit'.")
        parameters = self._model.to_dict()
        columns = parameters['columns']
        univariates = deepcopy(parameters['univariates'])
        learned_distributions = {}
        valid_columns = self._get_valid_columns_from_metadata(columns)
        for column, learned_params in zip(columns, univariates):
            if column in valid_columns:
                distribution = self.numerical_distributions.get(column, self.default_distribution)
                learned_params.pop('type')
                learned_distributions[column] = {'distribution': distribution, 'learned_parameters': learned_params}
        return learned_distributions

    def _get_parameters(self):
        """Get copula model parameters.

        Compute model ``correlation`` and ``distribution.std``
        before it returns the flatten dict.

        Returns:
            dict:
                Copula parameters.

        Raises:
            NonParametricError:
                If a non-parametric distribution has been used.
        """
        for univariate in self._model.univariates:
            univariate_type = type(univariate)
            if univariate_type is copulas.univariate.Univariate:
                univariate = univariate._instance
            if univariate.PARAMETRIC == copulas.univariate.ParametricType.NON_PARAMETRIC:
                raise NonParametricError('This GaussianCopula uses non parametric distributions')
        params = self._model.to_dict()
        correlation = []
        for index, row in enumerate(params['correlation'][1:]):
            correlation.append(row[:index + 1])
        params['correlation'] = correlation
        params['univariates'] = dict(zip(params.pop('columns'), params['univariates']))
        params['num_rows'] = self._num_rows
        return flatten_dict(params)

    @staticmethod
    def _get_nearest_correlation_matrix(matrix):
        """Find the nearest correlation matrix.

        If the given matrix is not Positive Semi-definite, which means
        that any of its eigenvalues is negative, find the nearest PSD matrix
        by setting the negative eigenvalues to 0 and rebuilding the matrix
        from the same eigenvectors and the modified eigenvalues.

        After this, the matrix will be PSD but may not have 1s in the diagonal,
        so the diagonal is replaced by 1s and then the PSD condition of the
        matrix is validated again, repeating the process until the built matrix
        contains 1s in all the diagonal and is PSD.

        After 10 iterations, the last step is skipped and the current PSD matrix
        is returned even if it does not have all 1s in the diagonal.

        Insipired by: https://stackoverflow.com/a/63131250
        """
        eigenvalues, eigenvectors = scipy.linalg.eigh(matrix)
        negative = eigenvalues < 0
        identity = np.identity(len(matrix))
        iterations = 0
        while np.any(negative):
            eigenvalues[negative] = 0
            matrix = eigenvectors.dot(np.diag(eigenvalues)).dot(eigenvectors.T)
            if iterations >= 10:
                break
            matrix = matrix - matrix * identity + identity
            max_value = np.abs(np.abs(matrix).max())
            if max_value > 1:
                matrix /= max_value
            eigenvalues, eigenvectors = scipy.linalg.eigh(matrix)
            negative = eigenvalues < 0
            iterations += 1
        return matrix

    @classmethod
    def _rebuild_correlation_matrix(cls, triangular_correlation):
        """Rebuild a valid correlation matrix from its lower half triangle.

        The input of this function is a list of lists of floats of size 1, 2, 3...n-1:

           [[c_{2,1}], [c_{3,1}, c_{3,2}], ..., [c_{n,1},...,c_{n,n-1}]]

        Corresponding to the values from the lower half of the original correlation matrix,
        **excluding** the diagonal.

        The output is the complete correlation matrix reconstructed using the given values
        and scaled to the :math:`[-1, 1]` range if necessary.

        Args:
            triangle_correlation (list[list[float]]):
                A list that contains lists of floats of size 1, 2, 3... up to ``n-1``,
                where ``n`` is the size of the target correlation matrix.

        Returns:
            numpy.ndarray:
                rebuilt correlation matrix.
        """
        zero = [0.0]
        size = len(triangular_correlation) + 1
        left = np.zeros((size, size))
        right = np.zeros((size, size))
        for idx, values in enumerate(triangular_correlation):
            values = values + zero * (size - idx - 1)
            left[idx + 1, :] = values
            right[:, idx + 1] = values
        correlation = left + right
        max_value = np.abs(correlation).max()
        if max_value > 1:
            correlation /= max_value
        correlation += np.identity(size)
        return cls._get_nearest_correlation_matrix(correlation).tolist()

    def _rebuild_gaussian_copula(self, model_parameters):
        """Rebuild the model params to recreate a Gaussian Multivariate instance.

        Args:
            model_parameters (dict):
                Sampled and reestructured model parameters.

        Returns:
            dict:
                Model parameters ready to recreate the model.
        """
        columns = []
        univariates = []
        for column, univariate in model_parameters['univariates'].items():
            columns.append(column)
            univariate['type'] = self.get_distribution_class(self._numerical_distributions.get(column, self.default_distribution))
            if 'scale' in univariate:
                univariate['scale'] = max(0, univariate['scale'])
            univariates.append(univariate)
        model_parameters['univariates'] = univariates
        model_parameters['columns'] = columns
        correlation = model_parameters.get('correlation')
        if correlation:
            model_parameters['correlation'] = self._rebuild_correlation_matrix(correlation)
        else:
            model_parameters['correlation'] = [[1.0]]
        return model_parameters

    def _get_likelihood(self, table_rows):
        return self._model.probability_density(table_rows)

    def _set_parameters(self, parameters):
        """Set copula model parameters.

        Args:
            dict:
                Copula flatten parameters.
        """
        parameters = unflatten_dict(parameters)
        if 'num_rows' in parameters:
            num_rows = parameters.pop('num_rows')
            self._num_rows = 0 if pd.isna(num_rows) else max(0, int(round(num_rows)))
        if parameters:
            parameters = self._rebuild_gaussian_copula(parameters)
            self._model = multivariate.GaussianMultivariate.from_dict(parameters)

def fit(self, metadata: Metadata, dataloader: DataLoader, *args, **kwargs):
    processed_data: pd.DataFrame = dataloader.load_all()
    self.discrete_cols = list(metadata.get('discrete_columns'))
    self.metadata = metadata
    self._transformer = StatisticDataTransformer()
    self._transformer.fit(processed_data, self.discrete_cols)
    processed_data = pd.DataFrame(self._transformer.transform(processed_data))
    '\n        log_numerical_distributions_error(\n            self.numerical_distributions, processed_data.columns, LOGGER\n        )\n        '
    self._num_rows = len(processed_data)
    numerical_distributions = deepcopy(self._numerical_distributions)
    for column in processed_data.columns:
        if column not in numerical_distributions:
            numerical_distributions[column] = self._numerical_distributions.get(column, self._default_distribution)
    self._model = multivariate.GaussianMultivariate(distribution=numerical_distributions)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', module='scipy')
        self._model.fit(processed_data)

class DataConnector:
    """
    DataConnector warps data source into ``pd.DataFrame``.

    For different data source, implement a specific subclass.
    """
    identity = None
    '\n    Identity of data source, e.g. table name, hash of content\n    '

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None | None:
        """
        Subclass must implement this for reading data.

        See ``read`` for more details.
        """
        raise NotImplementedError

    def _columns(self) -> list[str]:
        """
        Subclass should implement this for reading columns if there is an efficient way for peaking columns.

        See ``column`` for more details.
        """
        raise NotImplementedError

    def _iter(self, offset: int=0, chunksize: int=0) -> Generator[pd.DataFrame, None, None]:
        """
        Subclass should implement this for reading data in chunk.

        See ``iter`` for more details.
        """
        raise NotImplementedError

    def iter(self, offset: int=0, chunksize: int=0) -> Generator[pd.DataFrame, None, None]:
        """
        Interface for reading data in chunk.

        Args:
            offset (int, optional): Offset for reading. Defaults to 0.
            chunksize (int, optional): Chunksize for reading. Defaults to 0.

        Returns:
            typing.Generator[pd.DataFrame, None, None]: Generator/Iterator for readed dataframe
        """
        return self._iter(offset, chunksize)

    def read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        """
        Interface for reading data.

        Args:
            offset (int, optional): Offset for reading. Defaults to 0.
            limit (int, optional): Limit for reading. Defaults to None.
                None is for reading all data and 0 is for reading no data(only header).

        Returns:
            pd.DataFrame: Readed dataframe
        """
        return self._read(offset, limit)

    def columns(self) -> list[str]:
        """
        Interface for peaking columns.
        """
        try:
            return self._columns()
        except NotImplementedError:
            return self.read(0, 1).columns.tolist()

    def keys(self) -> list[str]:
        """
        Same as ``columns``.
        """
        return self.columns()

    def finalize(self):
        """
        Finalize the data connector.
        """
        pass

def keys(self) -> list[str]:
    """
        Same as ``columns``.
        """
    return self.columns()

class CsvConnector(DataConnector):
    """
    Wraps csv file into :ref:`DataConnector`

    Args:
        path (str): Path to csv file
        sep (str, optional): Separator. Defaults to ','.
        header (str, optional): Header. Defaults to 'infer'.
        read_csv_kwargs (dict, optional): kwargs for pd.read_csv, please refer to https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

    Example:

        .. code-block:: python

            from sdgx.data_connectors.csv_connector import CsvConnector
            connector = CsvConnector(
                path="data.csv",
            )
            df = connector.read()


    """

    @cached_property
    def identity(self):
        """
        Identity of the data source is the sha256 of the file
        """
        with open(self.path, 'rb') as f:
            return f'csvfile-{hashlib.sha256(f.read()).hexdigest()}'

    def __init__(self, path, sep=',', header='infer', **read_csv_kwargs):
        self.path = path
        self.sep = sep
        self.header = header
        self.read_csv_kwargs = read_csv_kwargs

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        return pd.read_csv(self.path, sep=self.sep, header=self.header, skiprows=range(1, offset + 1), nrows=limit, **self.read_csv_kwargs)

    def _columns(self) -> list[str]:
        d = pd.read_csv(self.path, sep=self.sep, header=self.header, nrows=0, **self.read_csv_kwargs).columns.tolist()
        return d

    def _iter(self, offset: int=0, chunksize: int=1000) -> Generator[pd.DataFrame, None, None]:
        if chunksize is None:
            yield self._read(offset=offset)
            return
        for d in pd.read_csv(self.path, sep=self.sep, header=self.header, skiprows=range(1, offset + 1), chunksize=chunksize, **self.read_csv_kwargs):
            yield d

@cached_property
def identity(self):
    """
        Identity of the data source is the sha256 of the file
        """
    with open(self.path, 'rb') as f:
        return f'csvfile-{hashlib.sha256(f.read()).hexdigest()}'

@pytest.fixture
def demo_single_table_data_pos_neg_metadata(demo_single_table_data_pos_neg):
    metadata = Metadata.from_dataframe(demo_single_table_data_pos_neg.copy(), check=True)
    metadata.categorical_encoder = {'cat_onehot': 'onehot', 'cat_label': 'label', 'cat_freq': 'frequency'}
    metadata.datetime_format = {'cat_date': '%Y-%m-%d'}
    metadata.categorical_threshold = {99: 'frequency', 199: 'label'}
    yield metadata

def test_sample(synthesizer):
    assert len(synthesizer.sample(10)) == 10
    for df in synthesizer.sample(10, chunksize=5):
        assert len(df) == 5

def gen_func():
    yield df.copy()

class MockCsvConnector(CsvConnector):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._readed = False

    @property
    def is_readed(self):
        return self._readed

    def reset(self):
        self._readed = False

    def _read(self, offset=0, limit=0) -> pd.DataFrame:
        self._readed = True
        try:
            return super()._read(offset, limit)
        except Exception:
            self._readed = False
            raise

    def _columns(self) -> list[str]:
        self._readed = True
        try:
            return super()._columns()
        except Exception:
            self._readed = False
            raise

    def iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:
        self._readed = True
        try:
            return super().iter(offset, chunksize)
        except Exception:
            self._readed = False
            raise

def iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:
    self._readed = True
    try:
        return super().iter(offset, chunksize)
    except Exception:
        self._readed = False
        raise

@pytest.mark.parametrize('cacher_cls', [NoCache, DiskCache])
@pytest.mark.parametrize('blocksize', [1])
@pytest.mark.parametrize('chunksize', [1])
def test_cacher(cacher_cls, cacher_kwargs, blocksize, chunksize, data_connector):
    cacher: Cacher = cacher_cls(blocksize=blocksize, **cacher_kwargs)
    for d in cacher.iter(chunksize, data_connector):
        assert len(d) == chunksize
    if isinstance(cacher, NoCache):
        assert not cacher.is_cached(0)
    else:
        assert cacher.is_cached(0)
        data_connector.reset()
        cacher.load(0, chunksize, data_connector)
        assert not data_connector.is_readed
    assert not cacher.load_all(data_connector).empty

@pytest.mark.parametrize('cacher', ['NoCache', 'DiskCache'])
def test_demo_dataloader(dataloader_builder: DataLoader, cacher, demo_single_table_data_connector):
    d: DataLoader = dataloader_builder(data_connector=demo_single_table_data_connector, cacher=cacher)
    assert len(d) == 48842
    assert sorted(d.columns()) == sorted(d.keys()) == sorted(['age', 'workclass', 'fnlwgt', 'education', 'educational-num', 'marital-status', 'occupation', 'relationship', 'race', 'gender', 'capital-gain', 'capital-loss', 'hours-per-week', 'native-country', 'income'])
    assert d.shape == (48842, 15)
    assert d.load_all().shape == (48842, 15)
    assert d[:].shape == d.shape
    assert d[:100].shape == (100, 15)
    assert d[100:].shape == (48842 - 100, 15)
    assert d[100:10000].shape == (10000 - 100, 15)
    assert d[100:10000:2].shape == ((10000 - 100) // 2, 15)
    assert d[['age', 'workclass']].shape == (48842, 2)
    for df in d.iter():
        assert len(df) == d.chunksize
        break

@pytest.mark.parametrize('cacher', ['NoCache', 'DiskCache'])
def test_loader_with_generator_connector(dataloader_builder, cacher, generator_connector):
    if cacher == 'NoCache':
        with pytest.raises(DataLoaderInitError):
            d: DataLoader = dataloader_builder(data_connector=generator_connector, cacher=cacher)
        return
    d: DataLoader = dataloader_builder(data_connector=generator_connector, cacher=cacher)
    df_all = pd.concat(generator_caller(), ignore_index=True)
    pd.testing.assert_frame_equal(d.load_all(), df_all)
    pd.testing.assert_frame_equal(d[:], df_all[:])
    pd.testing.assert_frame_equal(d[1:], df_all[1:])
    pd.testing.assert_frame_equal(d[:3], df_all[:3])
    pd.testing.assert_frame_equal(d[['a']], df_all[['a']])

def test_read(csv_connector: CsvConnector):
    df = csv_connector.read()
    assert len(df) == 2
    df = csv_connector.read(offset=1)
    assert len(df) == 1
    df = csv_connector.read(limit=1)
    assert len(df) == 1
    df = csv_connector.read(offset=1, limit=1)
    assert len(df) == 1
    df = csv_connector.read(offset=1, limit=2)
    assert len(df) == 1
    df = csv_connector.read(offset=100)
    assert len(df) == 0

def test_columns(csv_connector: CsvConnector):
    columns = csv_connector.columns()
    assert isinstance(columns, list)
    assert len(columns) == 4

def assert_sampled_data(dummy_single_table_data_loader, sampled_data, count):
    assert len(sampled_data) == count
    assert sampled_data.columns.tolist() == dummy_single_table_data_loader.columns()

def test_encoder(data_test: pd.DataFrame):
    for col in ['x', 'y', 'z']:
        nlabel_encoder = NormalizedLabelEncoder()
        nlabel_encoder.fit(data_test, col)
        td = nlabel_encoder.transform(data_test.copy())
        rd = nlabel_encoder.reverse_transform(td.copy())
        td.rename(columns={f'{col}.value': f'{col}'}, inplace=True)
        assert (rd[col].sort_values().values == data_test[col].sort_values().values).all()
        assert (td[col] >= -1).all()
        assert (td[col] <= 1).all()
        assert td[col].shape == data_test[col].shape
        assert len(td[col].unique()) == len(data_test[col].unique())

def test_gaussian_copula(dummy_single_table_metadata, dummy_single_table_data_loader):
    model = GaussianCopulaSynthesizerModel()
    model.fit(dummy_single_table_metadata, dummy_single_table_data_loader)
    sampled_data = model.sample(10)
    original_data = dummy_single_table_data_loader.load_all()
    assert len(sampled_data) == 10
    assert sampled_data.columns.tolist() == original_data.columns.tolist()

def test_encoder(data_test: pd.DataFrame):
    for col in ['x', 'y', 'z']:
        nlabel_encoder = NormalizedFrequencyEncoder()
        nlabel_encoder.fit(data_test, col)
        td = nlabel_encoder.transform(data_test.copy())
        rd = nlabel_encoder.reverse_transform(td.copy())
        td.rename(columns={f'{col}.value': f'{col}'}, inplace=True)
        assert (rd[col].sort_values().values == data_test[col].sort_values().values).all()
        assert (td[col] >= -1).all()
        assert (td[col] <= 1).all()
        assert td[col].shape == data_test[col].shape
        assert len(td[col].unique()) == len(data_test[col].unique())

