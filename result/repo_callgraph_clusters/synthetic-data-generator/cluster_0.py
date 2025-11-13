# Cluster 0

@hookimpl
def register(manager):
    manager.register('MyOwnExporter', MyOwnExporter)

@hookimpl
def register(manager):
    manager.register('DummyModel', MyOwnModel)

@hookimpl
def register(manager):
    manager.register('DummyDataConnector', MyOwnDataConnector)

@hookimpl
def register(manager):
    manager.register('DummyCache', MyOwnCache)

@pytest.fixture
def manager():
    yield CacherManager()

@hookimpl
def register(manager):
    manager.register('DummyInspector', MyOwnInspector)

@hookimpl
def register(manager):
    manager.register('DummyDataProcessor', MyOwnDataProcessor)

@functools.wraps(func)
def wrapper(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=category)
        return func(*args, **kwargs)

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

class Manager(metaclass=Singleton):
    """
    Base class for all manager.

    Manager is a singleton class for preventing multiple initialization.

    Define following attributes in subclass:
        * register_type: Base class for registered class
        * project_name: Name of entry-point for extensio
        * hookspecs_model: Hook specification model(where @hookspec is defined)

    For available managers, please refer to :ref:`Plugin-supported modules`

    """
    register_type: type = object
    '\n    Base class for registered class\n    '
    project_name: str = ''
    '\n    Name of entry-point for extension\n    '
    hookspecs_model = None
    '\n    Hook specification model(where @hookspec is defined)\n    '

    def __init__(self):
        self.pm = pluggy.PluginManager(self.project_name)
        self.pm.add_hookspecs(self.hookspecs_model)
        self._registed_cls: dict[str, type[self.register_type]] = {}
        self.pm.load_setuptools_entrypoints(self.project_name)
        self.load_all_local_model()

    def load_all_local_model(self):
        """
        Implement this function to load all local model
        """
        return

    @property
    def registed_cls(self) -> dict[str, type]:
        """
        Access all registed class.

        Lazy load, only load once.
        """
        if self._registed_cls:
            return self._registed_cls
        for f in self.pm.hook.register(manager=self):
            try:
                f()
            except Exception as e:
                logger.exception(RegisterError(e))
                continue
        return self._registed_cls

    def _load_dir(self, module):
        """
        Import all python files in a submodule.
        """
        modules = glob.glob(join(dirname(module.__file__), '*.py'))
        sub_packages = (basename(f)[:-3] for f in modules if isfile(f) and (not f.endswith('__init__.py')))
        packages = (str(module.__package__) + '.' + i for i in sub_packages)
        for p in packages:
            self.pm.register(importlib.import_module(p))

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    def register(self, cls_name, cls: type):
        """
        Register a new model, if the model is already registed, skip it.
        """
        cls_name = self._normalize_name(cls_name)
        logger.debug(f'Register for new model: {cls_name}')
        if cls in self._registed_cls.values():
            logger.error(f'SKIP: {cls_name} is already registed')
            return
        if not issubclass(cls, self.register_type):
            logger.error(f'SKIP: {cls_name} is not a subclass of {self.register_type}')
            return
        self._registed_cls[cls_name] = cls

    def init(self, c, **kwargs: dict[str, Any]):
        """
        Init a new subclass of self.register_type.

        Raises:
            NotFoundError: if cls_name is not registered
            InitializationError: if failed to initialize
        """
        if isinstance(c, self.register_type):
            return c
        if isinstance(c, type):
            cls_type = c
        else:
            c = self._normalize_name(c)
            if not c in self.registed_cls:
                raise NotFoundError
            cls_type = self.registed_cls[c]
        try:
            instance = cls_type(**kwargs)
            if not isinstance(instance, self.register_type):
                raise InitializationError(f'{c} is not a subclass of {self.register_type}.')
            return instance
        except Exception as e:
            raise InitializationError(e)

@property
def registed_cls(self) -> dict[str, type]:
    """
        Access all registed class.

        Lazy load, only load once.
        """
    if self._registed_cls:
        return self._registed_cls
    for f in self.pm.hook.register(manager=self):
        try:
            f()
        except Exception as e:
            logger.exception(RegisterError(e))
            continue
    return self._registed_cls

@click.option('--torchrun', type=bool, default=False, help='Use `torchrun` to run cli.')
@click.option('--torchrun_kwargs', type=str, default='{}', help='[Json String] torchrun kwargs.')
@wraps(func)
def wrapper(torchrun, torchrun_kwargs, *args, **kwargs):
    if not torchrun:
        func(*args, **kwargs)
    else:
        torchrun_kwargs = json.loads(torchrun_kwargs)
        torchrun_kwargs.setdefault('master_port', find_free_port())
        origin_args = copy.deepcopy(sys.argv)
        sys.argv = [re.sub('(-script\\.pyw|\\.exe)?$', '', sys.argv[0])]
        for k, v in torchrun_kwargs.items():
            sys.argv.extend([f'--{k}', str(v)])
        if '--torchrun' in origin_args:
            i = origin_args.index('--torchrun')
            if i + 1 < len(origin_args) and origin_args[i + 1] == 'true':
                origin_args.pop(i)
                origin_args.pop(i)
        if '--torchrun=true' in origin_args:
            origin_args.remove('--torchrun=true')
        sys.argv.extend(origin_args)
        sys.exit(load_entry_point('torch', 'console_scripts', 'torchrun')())

@click.command()
@cli_wrapper
def list_cachers():
    for model_name, model_cls in CacherManager().registed_cachers.items():
        print(f'{model_name} is registed as class: {model_cls}.')

@hookimpl
def register(manager):
    manager.register('CsvExporter', CsvExporter)

@hookimpl
def register(manager):
    manager.register('NoCache', NoCache)

@hookimpl
def register(manager):
    manager.register('DiskCache', DiskCache)

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

def fit(self, metadata: Metadata | None=None, **kwargs: Dict[str, Any]):
    self._fit(metadata, **kwargs)
    self.fitted = True

@hookimpl
def register(manager):
    manager.register('EmailGenerator', EmailGenerator)

@hookimpl
def register(manager):
    manager.register('chnpiigenerator', ChnPiiGenerator)

@hookimpl
def register(manager):
    manager.register('PositiveNegativeFilter', PositiveNegativeFilter)

@hookimpl
def register(manager):
    manager.register('NumericValueTransformer', NumericValueTransformer)

@hookimpl
def register(manager):
    manager.register('ConstValueTransformer', ConstValueTransformer)

@hookimpl
def register(manager):
    manager.register('FixedCombinationTransformer', FixedCombinationTransformer)

@hookimpl
def register(manager):
    manager.register('SpecificCombinationTransformer', SpecificCombinationTransformer)

@hookimpl
def register(manager):
    """
    Register the OutlierTransformer with the manager.

    Args:
        manager: The manager object responsible for registering transformers.
    """
    manager.register('OutlierTransformer', OutlierTransformer)

@hookimpl
def register(manager):
    manager.register('NonValueTransformer', NonValueTransformer)

@hookimpl
def register(manager):
    manager.register('EmptyTransformer', EmptyTransformer)

@hookimpl
def register(manager):
    manager.register('ColumnOrderTransformer', ColumnOrderTransformer)

@hookimpl
def register(manager):
    manager.register('DatetimeFormatter', DatetimeFormatter)

@hookimpl
def register(manager):
    manager.register('IntValueFormatter', IntValueFormatter)

@hookimpl
def register(manager):
    manager.register('NumericInspector', NumericInspector)

@hookimpl
def register(manager):
    manager.register('ConstInspector', ConstInspector)

@hookimpl
def register(manager):
    manager.register('FixCombinationInspector', FixedCombinationInspector)

@hookimpl
def register(manager):
    manager.register('BoolInspector', BoolInspector)

@hookimpl
def register(manager):
    manager.register('DiscreteInspector', DiscreteInspector)

@hookimpl
def register(manager):
    manager.register('SubsetRelationshipInspector', SubsetRelationshipInspector)

@hookimpl
def register(manager):
    manager.register('EmptyInspector', EmptyInspector)

@hookimpl
def register(manager):
    manager.register('IDInspector', IDInspector)

@hookimpl
def register(manager):
    manager.register('DatetimeInspector', DatetimeInspector)

@hookimpl
def register(manager):
    manager.register('EmailInspector', EmailInspector)
    manager.register('ChinaMainlandIDInspector', ChinaMainlandIDInspector)
    manager.register('ChinaMainlandMobilePhoneInspector', ChinaMainlandMobilePhoneInspector)
    manager.register('ChinaMainlandPostCode', ChinaMainlandPostCode)
    manager.register('ChinaMainlandUnifiedSocialCreditCode', ChinaMainlandUnifiedSocialCreditCode)
    manager.register('ChinaMainlandAddressInspector', ChinaMainlandAddressInspector)
    manager.register('ChineseNameInspector', ChineseNameInspector)
    manager.register('EnglishNameInspector', EnglishNameInspector)
    manager.register('ChineseCompanyNameInspector', ChineseCompanyNameInspector)

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

@hookimpl
def register(manager):
    manager.register('CTGAN', CTGANSynthesizerModel)

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

class GaussianNormalizer(FloatFormatter):
    """Transformer for numerical data based on copulas transformation.

    Transformation consists on bringing the input data to a standard normal space
    by using a combination of *cdf* and *inverse cdf* transformations:

    Given a variable :math:`x`:

    - Find the best possible marginal or use user specified one, :math:`P(x)`.
    - do :math:`u = \\phi (x)` where :math:`\\phi` is cumulative density function,
      given :math:`P(x)`.
    - do :math:`z = \\phi_{N(0,1)}^{-1}(u)`, where :math:`\\phi_{N(0,1)}^{-1}` is
      the *inverse cdf* of a *standard normal* distribution.

    The reverse transform will do the inverse of the steps above and go from :math:`z`
    to :math:`u` and then to :math:`x`.

    Args:
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
        learn_rounding_scheme (bool):
            Whether or not to learn what place to round to based on the data seen during ``fit``.
            If ``True``, the data returned by ``reverse_transform`` will be rounded to that place.
            Defaults to ``False``.
        enforce_min_max_values (bool):
            Whether or not to clip the data returned by ``reverse_transform`` to the min and
            max values seen during ``fit``. Defaults to ``False``.
        distribution (copulas.univariate.Univariate or str):
            Copulas univariate distribution to use. Defaults to ``truncated_gaussian``.
            Options include:

                * ``gaussian``: Use a Gaussian distribution.
                * ``gamma``: Use a Gamma distribution.
                * ``beta``: Use a Beta distribution.
                * ``student_t``: Use a Student T distribution.
                * ``gussian_kde``: Use a GaussianKDE distribution. This model is non-parametric,
                  so using this will make ``get_parameters`` unusable.
                * ``truncated_gaussian``: Use a Truncated Gaussian distribution.
    """
    _univariate = None
    COMPOSITION_IS_IDENTITY = False

    def __init__(self, model_missing_values=False, learn_rounding_scheme=False, enforce_min_max_values=False, distribution='truncated_gaussian'):
        super().__init__(missing_value_replacement='mean', model_missing_values=model_missing_values, learn_rounding_scheme=learn_rounding_scheme, enforce_min_max_values=enforce_min_max_values)
        self.distribution = distribution
        self._distributions = self._get_distributions()
        if isinstance(distribution, str):
            distribution = self._distributions[distribution]
        self._distribution = distribution

    @staticmethod
    def _get_distributions():
        try:
            from sdgx.models.components.sdv_copulas import univariate
        except ImportError as error:
            error.msg += '\n\nIt seems like `copulas` is not installed.\nPlease install it using:\n\n    pip install rdt[copulas]'
            raise
        return {'gaussian': univariate.GaussianUnivariate, 'gamma': univariate.GammaUnivariate, 'beta': univariate.BetaUnivariate, 'student_t': univariate.StudentTUnivariate, 'gaussian_kde': univariate.GaussianKDE, 'truncated_gaussian': univariate.TruncatedGaussian}

    def _get_univariate(self):
        distribution = self._distribution
        if any((isinstance(distribution, dist) for dist in self._distributions.values())):
            return copy.deepcopy(distribution)
        if isinstance(distribution, tuple):
            return distribution[0](**distribution[1])
        if isinstance(distribution, type) and distribution in self._distributions.values():
            return distribution()
        raise TypeError(f'Invalid distribution: {distribution}')

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
        self._univariate = self._get_univariate()
        super()._fit(data)
        data = super()._transform(data)
        if data.ndim > 1:
            data = data[:, 0]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self._univariate.fit(data)

    def _copula_transform(self, data):
        cdf = self._univariate.cdf(data)
        return scipy.stats.norm.ppf(cdf.clip(0 + EPSILON, 1 - EPSILON))

    def _transform(self, data):
        """Transform numerical data.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        transformed = super()._transform(data)
        if transformed.ndim > 1:
            transformed[:, 0] = self._copula_transform(transformed[:, 0])
        else:
            transformed = self._copula_transform(transformed)
        return transformed

    def _reverse_transform(self, data):
        """Convert data back into the original format.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series
        """
        if not isinstance(data, np.ndarray):
            data = data.to_numpy()
        if data.ndim > 1:
            data[:, 0] = self._univariate.ppf(scipy.stats.norm.cdf(data[:, 0]))
        else:
            data = self._univariate.ppf(scipy.stats.norm.cdf(data))
        return super()._reverse_transform(data)

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
    self._univariate = self._get_univariate()
    super()._fit(data)
    data = super()._transform(data)
    if data.ndim > 1:
        data = data[:, 0]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        self._univariate.fit(data)

def _transform(self, data):
    """Transform numerical data.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
    transformed = super()._transform(data)
    if transformed.ndim > 1:
        transformed[:, 0] = self._copula_transform(transformed[:, 0])
    else:
        transformed = self._copula_transform(transformed)
    return transformed

class ClusterBasedNormalizer(FloatFormatter):
    """Transformer for numerical data using a Bayesian Gaussian Mixture Model.

    This transformation takes a numerical value and transforms it using a Bayesian GMM
    model. It generates two outputs, a discrete value which indicates the selected
    'component' of the GMM and a continuous value which represents the normalized value
    based on the mean and std of the selected component.

    Args:
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
        learn_rounding_scheme (bool):
            Whether or not to learn what place to round to based on the data seen during ``fit``.
            If ``True``, the data returned by ``reverse_transform`` will be rounded to that place.
            Defaults to ``False``.
        enforce_min_max_values (bool):
            Whether or not to clip the data returned by ``reverse_transform`` to the min and
            max values seen during ``fit``. Defaults to ``False``.
        max_clusters (int):
            The maximum number of mixture components. Depending on the data, the model may select
            fewer components (based on the ``weight_threshold``).
            Defaults to 10.
        weight_threshold (int, float):
            The minimum value a component weight can take to be considered a valid component.
            ``weights_`` under this value will be ignored.
            Defaults to 0.005.

    Attributes:
        _bgm_transformer:
            An instance of sklearn`s ``BayesianGaussianMixture`` class.
        valid_component_indicator:
            An array indicating the valid components. If the weight of a component is greater
            than the ``weight_threshold``, it's indicated with True, otherwise it's set to False.
    """
    STD_MULTIPLIER = 4
    DETERMINISTIC_TRANSFORM = False
    DETERMINISTIC_REVERSE = True
    COMPOSITION_IS_IDENTITY = False
    _bgm_transformer = None
    valid_component_indicator = None

    def __init__(self, model_missing_values=False, learn_rounding_scheme=False, enforce_min_max_values=False, max_clusters=10, weight_threshold=0.005):
        super().__init__(missing_value_replacement='mean', model_missing_values=model_missing_values, learn_rounding_scheme=learn_rounding_scheme, enforce_min_max_values=enforce_min_max_values)
        self.max_clusters = max_clusters
        self.weight_threshold = weight_threshold

    def get_output_sdtypes(self):
        """Return the output sdtypes supported by the transformer.

        Returns:
            dict:
                Mapping from the transformed column names to supported sdtypes.
        """
        output_sdtypes = {'normalized': 'float', 'component': 'categorical'}
        if self.null_transformer and self.null_transformer.models_missing_values():
            output_sdtypes['is_null'] = 'float'
        return self._add_prefix(output_sdtypes)

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
        self._bgm_transformer = BayesianGaussianMixture(n_components=self.max_clusters, weight_concentration_prior_type='dirichlet_process', weight_concentration_prior=0.001, n_init=1)
        super()._fit(data)
        data = super()._transform(data)
        if data.ndim > 1:
            data = data[:, 0]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self._bgm_transformer.fit(data.reshape(-1, 1))
        self.valid_component_indicator = self._bgm_transformer.weights_ > self.weight_threshold

    def _transform(self, data):
        """Transform the numerical data.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray.
        """
        data = super()._transform(data)
        if data.ndim > 1:
            data, model_missing_values = (data[:, 0], data[:, 1])
        data = data.reshape((len(data), 1))
        means = self._bgm_transformer.means_.reshape((1, self.max_clusters))
        stds = np.sqrt(self._bgm_transformer.covariances_).reshape((1, self.max_clusters))
        normalized_values = (data - means) / (self.STD_MULTIPLIER * stds)
        normalized_values = normalized_values[:, self.valid_component_indicator]
        component_probs = self._bgm_transformer.predict_proba(data)
        component_probs = component_probs[:, self.valid_component_indicator]
        selected_component = np.zeros(len(data), dtype='int')
        for i in range(len(data)):
            component_prob_t = component_probs[i] + 1e-06
            component_prob_t = component_prob_t / component_prob_t.sum()
            selected_component[i] = np.random.choice(np.arange(self.valid_component_indicator.sum()), p=component_prob_t)
        aranged = np.arange(len(data))
        normalized = normalized_values[aranged, selected_component].reshape([-1, 1])
        normalized = np.clip(normalized, -0.99, 0.99)
        normalized = normalized[:, 0]
        rows = [normalized, selected_component]
        if self.null_transformer and self.null_transformer.models_missing_values():
            rows.append(model_missing_values)
        return np.stack(rows, axis=1)

    def _reverse_transform_helper(self, data):
        normalized = np.clip(data[:, 0], -1, 1)
        means = self._bgm_transformer.means_.reshape([-1])
        stds = np.sqrt(self._bgm_transformer.covariances_).reshape([-1])
        selected_component = data[:, 1].astype(int)
        std_t = stds[self.valid_component_indicator][selected_component]
        mean_t = means[self.valid_component_indicator][selected_component]
        reversed_data = normalized * self.STD_MULTIPLIER * std_t + mean_t
        return reversed_data

    def _reverse_transform(self, data):
        """Convert data back into the original format.

        Args:
            data (pd.DataFrame or numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series.
        """
        if not isinstance(data, np.ndarray):
            data = data.to_numpy()
        recovered_data = self._reverse_transform_helper(data)
        if self.null_transformer and self.null_transformer.models_missing_values():
            data = np.stack([recovered_data, data[:, -1]], axis=1)
        else:
            data = recovered_data
        return super()._reverse_transform(data)

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
    self._bgm_transformer = BayesianGaussianMixture(n_components=self.max_clusters, weight_concentration_prior_type='dirichlet_process', weight_concentration_prior=0.001, n_init=1)
    super()._fit(data)
    data = super()._transform(data)
    if data.ndim > 1:
        data = data[:, 0]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        self._bgm_transformer.fit(data.reshape(-1, 1))
    self.valid_component_indicator = self._bgm_transformer.weights_ > self.weight_threshold

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

class StudentTUnivariate(ScipyModel):
    """Wrapper around scipy.stats.t.

    Documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html
    """
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.UNBOUNDED
    MODEL_CLASS = t

    def _fit_constant(self, X):
        self._fit(X)
        self._params['scale'] = 0

    def _fit(self, X):
        dataframe, loc, scale = t.fit(X)
        self._params = {'df': dataframe, 'loc': loc, 'scale': scale}

    def _is_constant(self):
        return self._params['scale'] == 0

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    self._fit(X)
    self._params['scale'] = 0

@hookimpl
def register(manager):
    manager.register('DataFrameConnector', DataFrameConnector)

@hookimpl
def register(manager):
    manager.register('CsvConnector', CsvConnector)

class GeneratorConnector(DataConnector):
    """
    A virtual data connector that wrap
    `Generator <https://docs.python.org/3/glossary.html#term-generator>`_
    into a DataConnector.

    Passing ``offset=0`` to ``read`` will reset the generator.

    Warning:
        ``offset`` and ``limit`` are ignored as ``Generator`` not supporting random access.
        But we can use :ref:`Cacher` to support it. See :ref:`Data Loader` for more details.

    Note:
        This connector is not been registered by default.
        So only be used with the library way.
    """

    @cached_property
    def identity(self) -> str:
        return f'generator-{os.getpid()}-{id(self.generator_caller)}'

    def __init__(self, generator_caller: Callable[[], Generator[pd.DataFrame, None, None]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generator_caller = generator_caller
        self._generator = self.generator_caller()

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        """
        Ingore limit and allow sequential reading.
        """
        if offset == 0:
            self._generator = self.generator_caller()
        try:
            return next(self._generator)
        except StopIteration:
            return None

    def _columns(self) -> list[str]:
        for df in self._iter():
            return list(df.columns)

    def _iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:
        """
        Subclass should implement this for reading data in chunk.

        See ``iter`` for more details.
        """
        return self.generator_caller()

@cached_property
def identity(self) -> str:
    return f'generator-{os.getpid()}-{id(self.generator_caller)}'

@pytest.fixture
def manager():
    yield CacherManager()

