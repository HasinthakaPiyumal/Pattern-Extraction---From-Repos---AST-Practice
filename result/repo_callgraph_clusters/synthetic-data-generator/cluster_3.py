# Cluster 3

@pytest.fixture
def manager():
    yield InspectorManager()

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

def cleanup(self):
    """
        Cleanup resources. This will cause model unavailable and clear the cache.

        It useful when Synthesizer object is no longer needed and may hold large resources like GPUs.
        """
    if self.dataloader:
        self.dataloader.finalize(clear_cache=True)
    if hasattr(self, 'model'):
        del self.model

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

def _fit_column_scale(self, column_name: str, column_data: pd.DataFrame) -> np.ndarray:
    """
        Fit every numeric (include int and float) column using sklearn StandardScaler.
        """
    self.scalers[column_name] = StandardScaler()
    self.scalers[column_name].fit(column_data)

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    numeric_format: dict = {}
    numeric_format['positive'] = sorted(list(self.positive_columns))
    numeric_format['negative'] = sorted(list(self.negative_columns))
    return {'int_columns': list(self.int_columns), 'float_columns': list(self.float_columns), 'numeric_format': numeric_format}

class StrValuedBaseEnum(Enum, metaclass=StrValuedEnumMeta):

    def __hash__(self):
        return hash(self.value)

    @property
    def value(self):
        return str(super().value)

    @classmethod
    @property
    def values(cls) -> set:
        if not hasattr(cls, '__VALUES'):
            cls.__VALUES = {i.value for i in cls}
        return cls.__VALUES

    def __eq__(self, other) -> bool:
        if isinstance(other, type(self)):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        else:
            return False

    def __str__(self):
        return self.value

@classmethod
@property
def values(cls) -> set:
    if not hasattr(cls, '__VALUES'):
        cls.__VALUES = {i.value for i in cls}
    return cls.__VALUES

class StatisticDataTransformer(DataTransformer):
    """Data Transformer for statistical models like Gaussian Copula."""

    def _fit_continuous(self, data):
        """Train ClusterBasedNormalizer for continuous columns."""
        column_name = data.columns[0]
        gm = ClusterBasedNormalizer(model_missing_values=True, max_clusters=1)
        gm.fit(data, column_name)
        return ColumnTransformInfo(column_name=column_name, column_type='continuous', transform=gm, output_info=[SpanInfo(1, 'tanh')], output_dimensions=1)

    def _transform_continuous(self, column_transform_info, data):
        """Transform continuous column."""
        gm = column_transform_info.transform
        transformed = gm.transform(data)
        return transformed[f'{data.columns[0]}.normalized'].to_numpy().reshape(-1, 1)

    def _inverse_transform_continuous(self, column_transform_info, column_data, sigmas, st):
        """Inverse transform continuous column."""
        gm = column_transform_info.transform
        column_name = column_transform_info.column_name
        data = pd.DataFrame({f'{column_name}.normalized': column_data.flatten(), f'{column_name}.component': [0] * len(column_data)})
        if sigmas is not None:
            data[f'{column_name}.normalized'] = np.random.normal(data[f'{column_name}.normalized'], sigmas[st])
        result = gm.reverse_transform(data)
        if column_name in result.columns:
            return result[column_name]
        else:
            return result.iloc[:, 0]

    def _fit_discrete(self, data):
        """Fit frequency encoder for discrete column."""
        column_name = data.columns[0]
        freq_encoder = FrequencyEncoder()
        freq_encoder.fit(data, column_name)
        self._discrete_values = {column_name: data[column_name].unique().tolist()} if not hasattr(self, '_discrete_values') else {**self._discrete_values, column_name: data[column_name].unique().tolist()}
        return ColumnTransformInfo(column_name=column_name, column_type='discrete', transform=freq_encoder, output_info=[SpanInfo(1, 'tanh')], output_dimensions=1)

    def _transform_discrete(self, column_transform_info, data):
        """Transform discrete column using frequency encoding."""
        freq_encoder = column_transform_info.transform
        return freq_encoder.transform(data).to_numpy().reshape(-1, 1)

    def _inverse_transform_discrete(self, column_transform_info, column_data):
        """Inverse transform discrete column from frequency encoding."""
        freq_encoder = column_transform_info.transform
        column_name = column_transform_info.column_name
        data = pd.DataFrame({column_name: column_data.flatten()})
        categories = freq_encoder.starts['category'].values
        result = []
        for val in data[column_name]:
            starts = freq_encoder.starts.index.values
            idx = np.abs(starts - val).argmin()
            result.append(categories[idx])
        return pd.Series(result, index=data.index, dtype=freq_encoder.dtype)

def _fit_continuous(self, data):
    """Train ClusterBasedNormalizer for continuous columns."""
    column_name = data.columns[0]
    gm = ClusterBasedNormalizer(model_missing_values=True, max_clusters=1)
    gm.fit(data, column_name)
    return ColumnTransformInfo(column_name=column_name, column_type='continuous', transform=gm, output_info=[SpanInfo(1, 'tanh')], output_dimensions=1)

def _fit_discrete(self, data):
    """Fit frequency encoder for discrete column."""
    column_name = data.columns[0]
    freq_encoder = FrequencyEncoder()
    freq_encoder.fit(data, column_name)
    self._discrete_values = {column_name: data[column_name].unique().tolist()} if not hasattr(self, '_discrete_values') else {**self._discrete_values, column_name: data[column_name].unique().tolist()}
    return ColumnTransformInfo(column_name=column_name, column_type='discrete', transform=freq_encoder, output_info=[SpanInfo(1, 'tanh')], output_dimensions=1)

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
def _add_field_to_set(field, field_set):
    if isinstance(field, tuple):
        field_set.update(field)
    else:
        field_set.add(field)

class RegexGenerator(BaseTransformer):
    """RegexGenerator transformer.

    This transformer will drop a column and regenerate it with the previously specified
    ``regex`` format. The transformer will also be able to handle nulls and regenerate null values
    if specified.

    Args:
        regex (str):
            String representing the regex function.
        missing_value_replacement (object or None):
            Indicate what to do with the null values. If an integer or float is given,
            replace them with the given value. If the strings ``'mean'`` or ``'mode'`` are
            given, replace them with the corresponding aggregation. If ``None`` is given,
            do not replace them. Defaults to ``None``.
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
    """
    DETERMINISTIC_TRANSFORM = False
    DETERMINISTIC_REVERSE = False
    INPUT_SDTYPE = 'text'
    null_transformer = None

    def __init__(self, regex_format='[A-Za-z]{5}', missing_value_replacement=None, model_missing_values=False):
        self.missing_value_replacement = missing_value_replacement
        self.model_missing_values = model_missing_values
        self.regex_format = regex_format
        self.data_length = None

    def get_output_sdtypes(self):
        """Return the output sdtypes supported by the transformer.

        Returns:
            dict:
                Mapping from the transformed column names to supported sdtypes.
        """
        output_sdtypes = {}
        if self.null_transformer and self.null_transformer.models_missing_values():
            output_sdtypes['is_null'] = 'float'
        return self._add_prefix(output_sdtypes)

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
        self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
        self.null_transformer.fit(data)
        self.data_length = len(data)

    def _transform(self, data):
        """Return ``null`` column if ``models_missing_values``.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            (numpy.ndarray or None):
                If ``self.model_missing_values`` is ``True`` then will return a ``numpy.ndarray``
                indicating which values should be ``nan``, else will return ``None``. In both
                scenarios the original column is being dropped.
        """
        if self.null_transformer and self.null_transformer.models_missing_values():
            return self.null_transformer.transform(data)[:, 1].astype(float)
        return None

    def _reverse_transform(self, data):
        """Generate new data using the provided ``regex_format``.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series
        """
        if data is not None and len(data):
            sample_size = len(data)
        else:
            sample_size = self.data_length
        generator, size = strings_from_regex(self.regex_format)
        if sample_size > size:
            warnings.warn(f"The data has {sample_size} rows but the regex for '{self.get_input_column()}' can only create {size} unique values. Some values in '{self.get_input_column()}' may be repeated.")
        if size > sample_size:
            reverse_transformed = np.array([next(generator) for _ in range(sample_size)], dtype=object)
        else:
            generated_values = list(generator)
            reverse_transformed = []
            while len(reverse_transformed) < sample_size:
                remaining = sample_size - len(reverse_transformed)
                reverse_transformed.extend(generated_values[:remaining])
            reverse_transformed = np.array(reverse_transformed, dtype=object)
        if self.null_transformer.models_missing_values():
            reverse_transformed = np.column_stack((reverse_transformed, data))
        return self.null_transformer.reverse_transform(reverse_transformed)

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
    self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
    self.null_transformer.fit(data)
    self.data_length = len(data)

class UnixTimestampEncoder(BaseTransformer):
    """Transformer for datetime data.

    This transformer replaces datetime values with an integer timestamp
    transformed to float.

    Null values are replaced using a ``NullTransformer``.

    Args:
        missing_value_replacement (object or None):
            Indicate what to do with the null values. If an object is given, replace them
            with the given value. If the strings ``'mean'`` or ``'mode'`` are given, replace
            them with the corresponding aggregation. If ``None`` is given, do not replace them.
            Defaults to ``None``.
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
        datetime_format (str):
            The strftime to use for parsing time. For more information, see
            https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior.
    """
    INPUT_SDTYPE = 'datetime'
    DETERMINISTIC_TRANSFORM = True
    DETERMINISTIC_REVERSE = True
    COMPOSITION_IS_IDENTITY = True
    null_transformer = None

    def __init__(self, missing_value_replacement=None, model_missing_values=False, datetime_format=None):
        self.missing_value_replacement = missing_value_replacement
        self.model_missing_values = model_missing_values
        self.datetime_format = datetime_format
        self._dtype = None

    def is_composition_identity(self):
        """Return whether composition of transform and reverse transform produces the input data.

        Returns:
            bool:
                Whether or not transforming and then reverse transforming returns the input data.
        """
        if self.null_transformer and (not self.null_transformer.models_missing_values()):
            return False
        return self.COMPOSITION_IS_IDENTITY

    def get_output_sdtypes(self):
        """Return the output sdtypes supported by the transformer.

        Returns:
            dict:
                Mapping from the transformed column names to supported sdtypes.
        """
        output_sdtypes = {'value': 'float'}
        if self.null_transformer and self.null_transformer.models_missing_values():
            output_sdtypes['is_null'] = 'float'
        return self._add_prefix(output_sdtypes)

    def _convert_to_datetime(self, data):
        if data.dtype == 'object':
            try:
                pandas_datetime_format = None
                if self.datetime_format:
                    pandas_datetime_format = self.datetime_format.replace('%-', '%')
                data = pd.to_datetime(data, format=pandas_datetime_format)
            except ValueError as error:
                if 'Unknown string format:' in str(error):
                    message = 'Data must be of dtype datetime, or castable to datetime.'
                    raise TypeError(message) from None
                raise ValueError('Data does not match specified datetime format.') from None
        return data

    def _transform_helper(self, datetimes):
        """Transform datetime values to integer."""
        datetimes = self._convert_to_datetime(datetimes)
        nulls = datetimes.isna()
        integers = pd.to_numeric(datetimes, errors='coerce').to_numpy().astype(np.float64)
        integers[nulls] = np.nan
        transformed = pd.Series(integers)
        return transformed

    def _reverse_transform_helper(self, data):
        """Transform integer values back into datetimes."""
        if not isinstance(data, np.ndarray):
            data = data.to_numpy()
        if self.model_missing_values or self.missing_value_replacement is not None:
            data = self.null_transformer.reverse_transform(data)
        data = np.round(data.astype(np.float64))
        return data

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        self._dtype = data.dtype
        if self.datetime_format is None:
            datetime_array = data.astype(str).to_numpy()
            self.datetime_format = _guess_datetime_format_for_array(datetime_array)
        transformed = self._transform_helper(data)
        self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
        self.null_transformer.fit(transformed)

    def _transform(self, data):
        """Transform datetime values to float values.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        data = self._transform_helper(data)
        return self.null_transformer.transform(data)

    def _reverse_transform(self, data):
        """Convert float values back to datetimes.

        Args:
            data (pandas.Series or numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series
        """
        data = self._reverse_transform_helper(data)
        datetime_data = pd.to_datetime(data)
        if not isinstance(datetime_data, pd.Series):
            datetime_data = pd.Series(datetime_data)
        if self.datetime_format:
            if self._dtype == 'object':
                datetime_data = datetime_data.dt.strftime(self.datetime_format)
            elif is_datetime64_dtype(self._dtype) and '.%f' not in self.datetime_format:
                datetime_data = pd.to_datetime(datetime_data.dt.strftime(self.datetime_format))
        return datetime_data

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
    self._dtype = data.dtype
    if self.datetime_format is None:
        datetime_array = data.astype(str).to_numpy()
        self.datetime_format = _guess_datetime_format_for_array(datetime_array)
    transformed = self._transform_helper(data)
    self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
    self.null_transformer.fit(transformed)

class BinaryEncoder(BaseTransformer):
    """Transformer for boolean data.

    This transformer replaces boolean values with their integer representation
    transformed to float.

    Null values are replaced using a ``NullTransformer``.

    Args:
        missing_value_replacement (object or None):
            Indicate what to do with the null values. If an object is given, replace them
            with the given value. If the string ``'mode'`` is given, replace them with the
            most common value. If ``None`` is given, do not replace them.
            Defaults to ``None``.
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
    """
    INPUT_SDTYPE = 'boolean'
    DETERMINISTIC_TRANSFORM = True
    DETERMINISTIC_REVERSE = True
    null_transformer = None

    def __init__(self, missing_value_replacement=None, model_missing_values=False):
        self.missing_value_replacement = missing_value_replacement
        self.model_missing_values = model_missing_values

    def get_output_sdtypes(self):
        """Return the output sdtypes returned by this transformer.

        Returns:
            dict:
                Mapping from the transformed column names to the produced sdtypes.
        """
        output_sdtypes = {'value': 'float'}
        if self.null_transformer and self.null_transformer.models_missing_values():
            output_sdtypes['is_null'] = 'float'
        return self._add_prefix(output_sdtypes)

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
        self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
        self.null_transformer.fit(data)

    def _transform(self, data):
        """Transform boolean to float.

        The boolean values will be replaced by the corresponding integer
        representations as float values.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns
            pandas.DataFrame or pandas.Series
        """
        data = pd.to_numeric(data, errors='coerce')
        return self.null_transformer.transform(data).astype(float)

    def _reverse_transform(self, data):
        """Transform float values back to the original boolean values.

        Args:
            data (pandas.DataFrame or pandas.Series):
                Data to revert.

        Returns:
            pandas.Series:
                Reverted data.
        """
        if not isinstance(data, np.ndarray):
            data = data.to_numpy()
        if self.missing_value_replacement is not None:
            data = self.null_transformer.reverse_transform(data)
        if isinstance(data, np.ndarray):
            if data.ndim == 2:
                data = data[:, 0]
            data = pd.Series(data)
        isna = data.isna()
        data = np.round(data).clip(0, 1).astype('boolean').astype('object')
        data[isna] = np.nan
        return data

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
    self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
    self.null_transformer.fit(data)

class AnonymizedFaker(BaseTransformer):
    """Personal Identifiable Information Anonymizer using Faker.

    This transformer will drop a column and regenerate it with the previously specified
    ``Faker`` provider and ``function``. The transformer will also be able to handle nulls
    and regenerate null values if specified.

    Args:
        provider_name (str):
            The name of the provider in ``Faker``. If ``None`` the ``BaseProvider`` is used.
            Defaults to ``None``.
        function_name (str):
            The name of the function to use within the ``faker.provider``. Defaults to
            ``lexify``.
        function_kwargs (dict):
            Keyword args to pass into the ``function_name`` when being called.
        locales (list):
            List of localized providers to use instead of the global provider.
        missing_value_replacement (object or None):
            Indicate what to do with the null values. If an integer or float is given,
            replace them with the given value. If the strings ``'mean'`` or ``'mode'`` are
            given, replace them with the corresponding aggregation. If ``None`` is given,
            do not replace them. Defaults to ``None``.
        model_missing_values (bool):
            Whether to create a new column to indicate which values were null or not. The column
            will be created only if there are null values. If ``True``, create the new column if
            there are null values. If ``False``, do not create the new column even if there
            are null values. Defaults to ``False``.
    """
    DETERMINISTIC_TRANSFORM = False
    DETERMINISTIC_REVERSE = False
    INPUT_SDTYPE = 'pii'
    OUTPUT_SDTYPES = {}
    null_transformer = None

    @staticmethod
    def check_provider_function(provider_name, function_name):
        """Check that the provider and the function exist.

        Attempt to get the provider from ``faker.providers`` and then get the ``function``
        from the provider object. If one of them fails, it will raise an ``AttributeError``.

        Raises:
            ``AttributeError`` if the provider or the function is not found.
        """
        try:
            module = getattr(faker.providers, provider_name)
            if provider_name.lower() == 'baseprovider':
                getattr(module, function_name)
            else:
                provider = getattr(module, 'Provider')
                getattr(provider, function_name)
        except AttributeError as exception:
            raise Error(f"The '{provider_name}' module does not contain a function named '{function_name}'.\nRefer to the Faker docs to find the correct function: https://faker.readthedocs.io/en/master/providers.html") from exception

    def _check_locales(self):
        """Check if the locales exist for the provided provider."""
        locales = self.locales if isinstance(self.locales, list) else [self.locales]
        missed_locales = []
        for locale in locales:
            spec = importlib.util.find_spec(f'faker.providers.{self.provider_name}.{locale}')
            if spec is None:
                missed_locales.append(locale)
        if missed_locales:
            warnings.warn(f"Locales {missed_locales} do not support provider '{self.provider_name}' and function '{self.function_name}'.\nIn place of these locales, 'en_US' will be used instead. Please refer to the localized provider docs for more information: https://faker.readthedocs.io/en/master/locales.html")

    def __init__(self, provider_name=None, function_name=None, function_kwargs=None, locales=None, missing_value_replacement=None, model_missing_values=False):
        self.data_length = None
        self.provider_name = provider_name if provider_name else 'BaseProvider'
        if self.provider_name != 'BaseProvider' and function_name is None:
            raise Error(f"Please specify the function name to use from the '{self.provider_name}' provider.")
        self.function_name = function_name if function_name else 'lexify'
        self.function_kwargs = deepcopy(function_kwargs) if function_kwargs else {}
        self.check_provider_function(self.provider_name, self.function_name)
        self.missing_value_replacement = missing_value_replacement
        self.model_missing_values = model_missing_values
        self.locales = locales
        self.faker = faker.Faker(locales)
        if self.locales:
            self._check_locales()

    def _function(self):
        """Return a callable ``faker`` function."""
        return getattr(self.faker, self.function_name)(**self.function_kwargs)

    def get_output_sdtypes(self):
        """Return the output sdtypes supported by the transformer.

        Returns:
            dict:
                Mapping from the transformed column names to supported sdtypes.
        """
        output_sdtypes = self.OUTPUT_SDTYPES
        if self.null_transformer and self.null_transformer.models_missing_values():
            output_sdtypes['is_null'] = 'float'
        return self._add_prefix(output_sdtypes)

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
        self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
        self.null_transformer.fit(data)
        self.data_length = len(data)

    def _transform(self, data):
        """Return ``null`` column if ``models_missing_values``.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            (numpy.ndarray or None):
                If ``self.model_missing_values`` is ``True`` then will return a ``numpy.ndarray``
                indicating which values should be ``nan``, else will return ``None``. In both
                scenarios the original column is being dropped.
        """
        if self.null_transformer and self.null_transformer.models_missing_values():
            return self.null_transformer.transform(data)[:, 1].astype(float)
        return None

    def _reverse_transform(self, data):
        """Generate new anonymized data using a ``faker.provider.function``.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to transform.

        Returns:
            pandas.Series
        """
        if data is not None and len(data):
            sample_size = len(data)
        else:
            sample_size = self.data_length
        reverse_transformed = np.array([self._function() for _ in range(sample_size)], dtype=object)
        if self.null_transformer.models_missing_values():
            reverse_transformed = np.column_stack((reverse_transformed, data))
        return self.null_transformer.reverse_transform(reverse_transformed)

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
        defaults = dict(zip(keys, args.defaults))
        instanced = {key: getattr(self, key) for key in keys}
        defaults['function_name'] = None
        for arg, value in instanced.items():
            if value and defaults[arg] != value and (value != 'BaseProvider'):
                value = f"'{value}'" if isinstance(value, str) else value
                custom_args.append(f'{arg}={value}')
        args_string = ', '.join(custom_args)
        return f'{class_name}({args_string})'

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit to.
        """
    self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
    self.null_transformer.fit(data)
    self.data_length = len(data)

def get_qualified_name(_object):
    """Return the Fully Qualified Name from an instance or class."""
    module = _object.__module__
    if hasattr(_object, '__name__'):
        _class = _object.__name__
    else:
        _class = _object.__class__.__name__
    return module + '.' + _class

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

def _fit(self, X):
    dataframe, loc, scale = t.fit(X)
    self._params = {'df': dataframe, 'loc': loc, 'scale': scale}

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

def _fit(self, X):
    a, loc, scale = gamma.fit(X)
    self._params = {'a': a, 'loc': loc, 'scale': scale}

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

def _fit(self, X):
    c, loc, scale = loglaplace.fit(X)
    self._params = {'c': c, 'loc': loc, 'scale': scale}

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

class DataTransformer(object):
    """Data Transformer.

    Model continuous columns with a BayesianGMM and normalized to a scalar [0, 1] and a vector.
    Discrete columns are encoded using a scikit-learn OneHotEncoder.
    """

    def __init__(self, max_clusters=10, weight_threshold=0.005):
        """Create a data transformer.

        Args:
            max_clusters (int):
                Maximum number of Gaussian distributions in Bayesian GMM.
            weight_threshold (float):
                Weight threshold for a Gaussian distribution to be kept.
        """
        self._max_clusters = max_clusters
        self._weight_threshold = weight_threshold

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

    def _fit_discrete(self, data):
        """Fit one hot encoder for discrete column.

        Args:
            data (pd.DataFrame):
                A dataframe containing a column.

        Returns:
            namedtuple:
                A ``ColumnTransformInfo`` object.
        """
        column_name = data.columns[0]
        ohe = OneHotEncoder()
        ohe.fit(data, column_name)
        num_categories = len(ohe.dummies)
        return ColumnTransformInfo(column_name=column_name, column_type='discrete', transform=ohe, output_info=[SpanInfo(num_categories, 'softmax')], output_dimensions=num_categories)

    def fit(self, raw_data, discrete_columns=()):
        """Fit the ``DataTransformer``.

        Fits a ``ClusterBasedNormalizer`` for continuous columns and a
        ``OneHotEncoder`` for discrete columns.

        This step also counts the #columns in matrix data and span information.
        """
        self.output_info_list = []
        self.output_dimensions = 0
        self.dataframe = True
        if not isinstance(raw_data, pd.DataFrame):
            self.dataframe = False
            discrete_columns = [str(column) for column in discrete_columns]
            column_names = [str(num) for num in range(raw_data.shape[1])]
            raw_data = pd.DataFrame(raw_data, columns=column_names)
        self._column_raw_dtypes = raw_data.infer_objects().dtypes
        self._column_transform_info_list = []
        for column_name in raw_data.columns:
            if column_name in discrete_columns:
                column_transform_info = self._fit_discrete(raw_data[[column_name]])
            else:
                column_transform_info = self._fit_continuous(raw_data[[column_name]])
            self.output_info_list.append(column_transform_info.output_info)
            self.output_dimensions += column_transform_info.output_dimensions
            self._column_transform_info_list.append(column_transform_info)

    def _transform_continuous(self, column_transform_info, data):
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
        ohe = column_transform_info.transform
        return ohe.transform(data).to_numpy()

    def _synchronous_transform(self, raw_data, column_transform_info_list):
        """Take a Pandas DataFrame and transform columns synchronous.

        Outputs a list with Numpy arrays.
        """
        column_data_list = []
        for column_transform_info in column_transform_info_list:
            column_name = column_transform_info.column_name
            data = raw_data[[column_name]]
            if column_transform_info.column_type == 'continuous':
                column_data_list.append(self._transform_continuous(column_transform_info, data))
            else:
                column_data_list.append(self._transform_discrete(column_transform_info, data))
        return column_data_list

    def _parallel_transform(self, raw_data, column_transform_info_list):
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
        return Parallel(n_jobs=-1)(processes)

    def transform(self, raw_data):
        """Take raw data and output a matrix data."""
        if not isinstance(raw_data, pd.DataFrame):
            column_names = [str(num) for num in range(raw_data.shape[1])]
            raw_data = pd.DataFrame(raw_data, columns=column_names)
        if raw_data.shape[0] < 500:
            column_data_list = self._synchronous_transform(raw_data, self._column_transform_info_list)
        else:
            column_data_list = self._parallel_transform(raw_data, self._column_transform_info_list)
        return np.concatenate(column_data_list, axis=1).astype(float)

    def _inverse_transform_continuous(self, column_transform_info, column_data, sigmas, st):
        gm = column_transform_info.transform
        data = pd.DataFrame(column_data[:, :2], columns=list(gm.get_output_sdtypes()))
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
        for column_transform_info in self._column_transform_info_list:
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

def _fit_discrete(self, data):
    """Fit one hot encoder for discrete column.

        Args:
            data (pd.DataFrame):
                A dataframe containing a column.

        Returns:
            namedtuple:
                A ``ColumnTransformInfo`` object.
        """
    column_name = data.columns[0]
    ohe = OneHotEncoder()
    ohe.fit(data, column_name)
    num_categories = len(ohe.dummies)
    return ColumnTransformInfo(column_name=column_name, column_type='discrete', transform=ohe, output_info=[SpanInfo(num_categories, 'softmax')], output_dimensions=num_categories)

def test_fit(synthesizer):
    synthesizer.fit()

def test_datetime_formatter_test_df(datetime_test_df: pd.DataFrame):

    def df_generator():
        yield datetime_test_df
    data_processors = [DatetimeFormatter()]
    dataconnector = GeneratorConnector(df_generator)
    dataloader = DataLoader(dataconnector, chunksize=CHUNK_SIZE)
    metadata = Metadata.from_dataloader(dataloader)
    metadata.datetime_columns = ['date']
    metadata.discrete_columns = []
    metadata.datetime_format = {'date': '%Y-%m-%d'}
    for d in data_processors:
        d.fit(metadata=metadata, tabular_data=dataloader)

    def chunk_generator() -> Generator[pd.DataFrame, None, None]:
        for chunk in dataloader.iter():
            for d in data_processors:
                chunk = d.convert(chunk)
            assert not chunk.isna().any().any()
            assert not chunk.isnull().any().any()
            yield chunk
    processed_dataloader = DataLoader(GeneratorConnector(chunk_generator), identity=dataloader.identity)
    df = processed_dataloader.load_all()
    assert not df.isna().any().any()
    assert not df.isnull().any().any()
    reverse_converted_df = df
    for d in data_processors:
        reverse_converted_df = d.reverse_convert(df)
    assert reverse_converted_df.eq(datetime_test_df).all().all()

def test_email_generator(chn_personal_test_df: pd.DataFrame):
    assert 'email' in chn_personal_test_df.columns
    metadata_df = Metadata.from_dataframe(chn_personal_test_df)
    email_generator = EmailGenerator()
    assert not email_generator.fitted
    email_generator.fit(metadata_df)
    assert email_generator.fitted
    assert email_generator.email_columns_list == ['email']
    converted_df = email_generator.convert(chn_personal_test_df)
    assert len(converted_df) == len(chn_personal_test_df)
    assert converted_df.shape[1] != chn_personal_test_df.shape[1]
    assert converted_df.shape[1] == chn_personal_test_df.shape[1] - len(email_generator.email_columns_list)
    assert 'email' not in converted_df.columns
    reverse_converted_df = email_generator.reverse_convert(converted_df)
    assert len(reverse_converted_df) == len(chn_personal_test_df)
    assert 'email' in reverse_converted_df.columns
    for each_value in chn_personal_test_df['email'].values:
        assert EmailCheckModel(email=each_value)

def test_chn_pii_generator(chn_personal_test_df: pd.DataFrame):
    assert 'chn_name' in chn_personal_test_df.columns
    assert 'mobile_phone_no' in chn_personal_test_df.columns
    assert 'ssn_sfz' in chn_personal_test_df.columns
    assert 'company_name' in chn_personal_test_df.columns
    metadata_df = Metadata.from_dataframe(chn_personal_test_df)
    pii_generator = ChnPiiGenerator()
    assert not pii_generator.fitted
    pii_generator.fit(metadata_df)
    assert pii_generator.fitted
    assert pii_generator.chn_name_columns_list == ['chn_name']
    assert pii_generator.chn_phone_columns_list == ['mobile_phone_no']
    assert pii_generator.chn_id_columns_list == ['ssn_sfz']
    assert pii_generator.chn_company_name_list == ['company_name']
    converted_df = pii_generator.convert(chn_personal_test_df)
    assert len(converted_df) == len(chn_personal_test_df)
    assert converted_df.shape[1] != chn_personal_test_df.shape[1]
    assert converted_df.shape[1] == chn_personal_test_df.shape[1] - len(pii_generator.chn_pii_columns)
    assert 'chn_name' not in converted_df.columns
    assert 'mobile_phone_no' not in converted_df.columns
    assert 'ssn_sfz' not in converted_df.columns
    assert 'company_name' not in converted_df.columns
    reverse_converted_df = pii_generator.reverse_convert(converted_df)
    assert len(reverse_converted_df) == len(chn_personal_test_df)
    assert 'chn_name' in reverse_converted_df.columns
    assert 'mobile_phone_no' in reverse_converted_df.columns
    assert 'ssn_sfz' in reverse_converted_df.columns
    assert 'company_name' in reverse_converted_df.columns
    for each_value in chn_personal_test_df['ssn_sfz'].values:
        assert len(each_value) == 18
        pattern = '^\\d{17}[0-9X]$'
        assert bool(re.match(pattern, each_value))
    for each_value in chn_personal_test_df['chn_name'].values:
        pattern = '^[\\u4e00-\\u9fa5]{2,5}$'
        assert len(each_value) >= 2 and len(each_value) <= 5
        assert bool(re.match(pattern, each_value))
    for each_value in chn_personal_test_df['mobile_phone_no'].values:
        assert each_value.startswith('1')
        assert len(each_value) == 11
        pattern = '^1[3-9]\\d{9}$'
        assert bool(re.match(pattern, each_value))
    for each_value in chn_personal_test_df['company_name'].values:
        pattern = '.*?公司.*?'
        assert bool(re.match(pattern, each_value))

def test_positive_negative_filter(pos_neg_test_df: pd.DataFrame):
    metadata_df = Metadata.from_dataframe(pos_neg_test_df)
    pos_neg_filter = PositiveNegativeFilter()
    assert not pos_neg_filter.fitted
    pos_neg_filter.fit(metadata_df)
    assert pos_neg_filter.fitted
    assert pos_neg_filter.positive_columns == {'int_id', 'pos_int', 'pos_float'}
    assert pos_neg_filter.negative_columns == {'neg_int', 'neg_float'}
    converted_df = pos_neg_filter.convert(pos_neg_test_df)
    assert converted_df.shape == pos_neg_test_df.shape
    assert (converted_df['pos_int'] >= 0).all()
    assert (converted_df['pos_float'] >= 0).all()
    assert (converted_df['neg_int'] <= 0).all()
    assert (converted_df['neg_float'] <= 0).all()
    reverse_converted_df = pos_neg_filter.reverse_convert(converted_df)
    assert reverse_converted_df.shape[1] == converted_df.shape[1]
    assert (reverse_converted_df['pos_int'] >= 0).all()
    assert (reverse_converted_df['pos_float'] >= 0).all()
    assert (reverse_converted_df['neg_int'] <= 0).all()
    assert (reverse_converted_df['neg_float'] <= 0).all()
    pd.testing.assert_series_equal(pos_neg_test_df['mixed_int'], reverse_converted_df['mixed_int'])
    pd.testing.assert_series_equal(pos_neg_test_df['mixed_float'], reverse_converted_df['mixed_float'])
    assert reverse_converted_df.shape[0] <= pos_neg_test_df.shape[0]

def test_specific_combination_transformer(train_data, test_data):
    transformer = SpecificCombinationTransformer()
    metadata = Metadata.from_dataframe(train_data)
    combinations = {('price_usd', 'price_cny', 'price_eur'), ('size_cm', 'size_inch', 'size_m')}
    metadata.update({'specific_combinations': combinations})
    transformer.fit(metadata=metadata, tabular_data=train_data)
    result = transformer.reverse_convert(test_data)
    for cols in combinations:
        result_rows = result[list(cols)].values.tolist()
        train_rows = train_data[list(cols)].values.tolist()
        assert all((row in train_rows for row in result_rows)), f'Combination {cols} contains some invalid value in original train data.'

def test_numeric_transformer_fit_test_df(df_data: pd.DataFrame):
    """ """
    metadata_df = Metadata.from_dataframe(df_data)
    transformer = NumericValueTransformer()
    transformer.fit(metadata_df, df_data)
    assert transformer.int_columns == {'int_random', 'int_id'}
    assert transformer.float_columns == {'float_random'}

def test_numeric_transformer_convert_test_df(df_data: pd.DataFrame):
    """ """
    metadata_df = Metadata.from_dataframe(df_data)
    transformer = NumericValueTransformer()
    transformer.fit(metadata_df, df_data)
    converted_df = transformer.convert(df_data)
    numerical_columns = list(transformer.int_columns) + list(transformer.float_columns)
    converted_status = calculate_mean_and_variance(converted_df, numerical_columns)
    assert type(converted_df) == pd.DataFrame
    assert converted_df.shape == df_data.shape
    assert np.isclose(converted_status['int_id']['mean'], 0.0)
    assert np.isclose(converted_status['int_random']['mean'], 0.0)
    assert np.isclose(converted_status['float_random']['mean'], 0.0)
    assert np.isclose(converted_status['int_id']['variance'], 1, atol=0.001)
    assert np.isclose(converted_status['int_random']['variance'], 1, atol=0.001)
    assert np.isclose(converted_status['float_random']['variance'], 1, atol=0.001)

def test_numeric_transformer_reverse_convert_test_df(df_data: pd.DataFrame):
    """ """
    transformer = NumericValueTransformer()
    transformer.fit(Metadata.from_dataframe(df_data), df_data)
    numerical_columns = list(transformer.int_columns) + list(transformer.float_columns)
    converted_df = transformer.convert(df_data)
    reverse_converted_df = transformer.reverse_convert(converted_df)
    reverse_converted_status = calculate_mean_and_variance(reverse_converted_df, numerical_columns)
    original_status = calculate_mean_and_variance(df_data, numerical_columns)
    assert type(reverse_converted_df) == pd.DataFrame
    assert reverse_converted_df.shape == df_data.shape
    assert np.isclose(reverse_converted_status['int_id']['mean'], original_status['int_id']['mean'])
    assert np.isclose(reverse_converted_status['int_random']['mean'], original_status['int_random']['mean'])
    assert np.isclose(reverse_converted_status['float_random']['mean'], original_status['float_random']['mean'])
    assert np.isclose(reverse_converted_status['int_id']['variance'], original_status['int_id']['variance'])
    assert np.isclose(reverse_converted_status['int_random']['variance'], original_status['int_random']['variance'])
    assert np.isclose(reverse_converted_status['float_random']['variance'], original_status['float_random']['variance'])

def test_empty_handling_test_df(test_empty_data: pd.DataFrame):
    """
    Test the handling of empty columns in a DataFrame.
    This function tests the behavior of a DataFrame when it contains empty columns.
    It is designed to be used in a testing environment, where the DataFrame is passed as an argument.

    Parameters:
    test_empty_data (pd.DataFrame): The DataFrame to test.

    Returns:
    None

    Raises:
    AssertionError: If the DataFrame does not handle empty columns as expected.
    """
    metadata = Metadata.from_dataframe(test_empty_data)
    empty_transformer = EmptyTransformer()
    assert empty_transformer.fitted is False
    empty_transformer.fit(metadata)
    assert empty_transformer.fitted
    assert sorted(empty_transformer.empty_columns) == ['age', 'fnlwgt']
    transformed_df = empty_transformer.convert(test_empty_data)
    processed_metadata = Metadata.from_dataframe(transformed_df)
    assert not processed_metadata.get('empty_columns')
    reverse_converted_df = empty_transformer.reverse_convert(transformed_df)
    reverse_converted_metadata = Metadata.from_dataframe(reverse_converted_df)
    assert reverse_converted_metadata.get('empty_columns') == {'age', 'fnlwgt'}

def test_fixed_combination_handling_test_df(test_fixed_combination_data: pd.DataFrame):
    """
    Test the handling of fixed combination columns in a DataFrame.
    This function tests the behavior of a DataFrame when it contains fixed combination columns.
    It is designed to be used in a testing environment, where the DataFrame is passed as an argument.

    Parameters:
    test_fixed_combination_data (pd.DataFrame): The DataFrame to test.

    Returns:
    None

    Raises:
    AssertionError: If the DataFrame does not handle fixed combination columns as expected.
    """
    metadata = Metadata.from_dataframe(test_fixed_combination_data)
    fixed_combinations = metadata.get('fixed_combinations')
    assert fixed_combinations == {'A': {'E', 'D', 'B'}, 'B': {'A', 'E', 'D'}, 'D': {'A', 'E', 'B'}, 'E': {'A', 'D', 'B'}, 'categorical_one': {'categorical_two'}}
    fixed_combination_transformer = FixedCombinationTransformer()
    assert fixed_combination_transformer.fitted is False
    fixed_combination_transformer.fit(metadata)
    assert fixed_combination_transformer.fitted
    assert fixed_combination_transformer.fixed_combinations == {'A': {'E', 'D', 'B'}, 'B': {'A', 'E', 'D'}, 'D': {'A', 'E', 'B'}, 'E': {'A', 'D', 'B'}, 'categorical_one': {'categorical_two'}}
    transformed_df = fixed_combination_transformer.convert(test_fixed_combination_data)
    for column in test_fixed_combination_data.columns:
        assert column in transformed_df.columns, f'Column {column} should be retained in the transformed data.'
    assert transformed_df.shape == test_fixed_combination_data.shape

def test_categorical_fixed_combinations(test_fixed_combination_data):
    """Test the fixed combination relationship of categorical variables"""
    metadata = Metadata.from_dataframe(test_fixed_combination_data)
    transformer = FixedCombinationTransformer()
    transformer.fit(metadata)
    assert 'categorical_one' in transformer.fixed_combinations
    assert 'categorical_two' in transformer.fixed_combinations['categorical_one']
    transformed_df = transformer.convert(test_fixed_combination_data)
    assert all(transformed_df['categorical_one'].map(dict(zip(test_fixed_combination_data['categorical_one'], test_fixed_combination_data['categorical_two']))) == transformed_df['categorical_two'])

def test_numeric_transformer_fit_test_df(df_data: pd.DataFrame, df_data_processed: pd.DataFrame):
    """
    Test the functionality of the ColumnOrderTransformer class.

    This function tests the following:
    1. The correctness of the input dataframes' columns and shapes.
    2. The correctness of the metadata extraction from the input dataframe.
    3. The correctness of the fitting of the ColumnOrderTransformer.
    4. The correctness of the conversion of the input dataframe using the ColumnOrderTransformer.
    5. The correctness of the reverse conversion of the processed dataframe using the ColumnOrderTransformer.

    Parameters:
    df_data (pd.DataFrame): The input dataframe to be transformed.
    df_data_processed (pd.DataFrame): The processed dataframe to be reversely transformed.

    Returns:
    None
    """
    assert df_data.columns.to_list() == ['int_id', 'str_id', 'int_random', 'bool_random', 'float_random']
    assert df_data_processed.columns.to_list() == ['int_random', 'int_id', 'float_random_2', 'bool_random', 'float_random', 'bool_random_2', 'str_id']
    assert df_data.shape == (100, 5)
    assert df_data_processed.shape == (100, 7)
    metadata_df = Metadata.from_dataframe(df_data)
    transformer = ColumnOrderTransformer()
    transformer.fit(metadata_df)
    assert transformer.column_list == ['int_id', 'str_id', 'int_random', 'bool_random', 'float_random']
    transformed_df = transformer.convert(df_data)
    assert transformed_df.columns.to_list() == df_data.columns.to_list()
    assert transformed_df.shape == (100, 5)
    assert df_data.equals(transformed_df)
    convert_transformed_df = transformer.reverse_convert(df_data_processed)
    assert df_data.columns.to_list() == convert_transformed_df.columns.to_list()
    assert convert_transformed_df.shape == (100, 5)
    assert convert_transformed_df.columns.to_list() == transformer.column_list

@pytest.mark.skip(reason='success in local, failed in GitHub Action')
def test_outlier_handling_test_df(outlier_test_df: pd.DataFrame):
    """
    Test the handling of outliers in a DataFrame.
    This function tests the behavior of a DataFrame when it contains outliers.
    It is designed to be used in a testing environment, where the DataFrame is passed as an argument.

    Parameters:
        outlier_test_df (pd.DataFrame): The DataFrame to test.

    Returns:
        None

    Raises:
        AssertionError: If the DataFrame does not handle outliers as expected.
    """
    assert 'not_number_outlier' in outlier_test_df['int_random'].to_list()
    assert 'not_number_outlier' in outlier_test_df['float_random'].to_list()
    outlier_transformer = OutlierTransformer()
    assert outlier_transformer.fitted is False
    metadata_outlier = Metadata.from_dataframe(outlier_test_df)
    metadata_outlier.column_list = ['int_id', 'str_id', 'int_random', 'float_random']
    metadata_outlier.int_columns = set(['int_id', 'int_random'])
    metadata_outlier.float_columns = set(['float_random'])
    outlier_transformer.fit(metadata=metadata_outlier)
    assert outlier_transformer.fitted
    transformed_df = outlier_transformer.convert(outlier_test_df)
    assert not 'not_number_outlier' in transformed_df['int_random'].to_list()
    assert not 'not_number_outlier' in transformed_df['float_random'].to_list()
    assert 0 in transformed_df['int_random'].to_list()
    assert 0.0 in transformed_df['float_random'].to_list()

@pytest.mark.skip(reason='success in local, failed in GitHub Action')
def test_nan_handling_test_df(nan_test_df: pd.DataFrame):
    """
    Test the handling of NaN values in a DataFrame.
    This function tests the behavior of a DataFrame when it contains NaN values.
    It is designed to be used in a testing environment, where the DataFrame is passed as an argument.

    Parameters:
    nan_test_df (pd.DataFrame): The DataFrame to test.

    Returns:
    None

    Raises:
    AssertionError: If the DataFrame does not handle NaN values as expected.
    """
    assert has_nan(nan_test_df), 'NaN values were not removed from the DataFrame.'
    nan_transformer = NonValueTransformer()
    assert nan_transformer.fitted is False
    nan_csv_metadata = Metadata.from_dataframe(nan_test_df)
    nan_csv_metadata.column_list = ['int_id', 'str_id', 'int_random', 'bool_random']
    nan_transformer.fit(nan_csv_metadata)
    assert nan_transformer.fitted
    transformed_df = nan_transformer.convert(nan_test_df)
    assert not has_nan(transformed_df)

def test_discrete_transformer_fit_test_df(df_data: pd.DataFrame):
    """
    Test the fit and convert methods of the DiscreteTransformer class.

    This function tests the following:
    1. The fit method of the DiscreteTransformer class.
    2. The convert method of the DiscreteTransformer class.
    3. The reverse_convert method of the DiscreteTransformer class.
    4. The equality of the original dataframe and the reversely converted dataframe.

    Parameters:
    df_data (pd.DataFrame): The input dataframe to be tested.

    Returns:
    None
    """
    metadata_df = Metadata.from_dataframe(df_data)
    order_transformer = ColumnOrderTransformer()
    order_transformer.fit(metadata_df)
    transformer = DiscreteTransformer()
    assert not transformer.fitted
    transformer.fit(metadata_df, df_data)
    assert transformer.fitted
    assert transformer.discrete_columns == {'discrete_val'}
    converted_df = transformer.convert(df_data)
    assert isinstance(converted_df, pd.DataFrame)
    assert is_an_integer_list(converted_df['discrete_val_a'].to_list())
    assert is_an_integer_list(converted_df['discrete_val_b'].to_list())
    assert is_an_integer_list(converted_df['discrete_val_c'].to_list())
    reverse_converted_df = transformer.reverse_convert(converted_df)
    reverse_converted_df = order_transformer.reverse_convert(reverse_converted_df)
    assert isinstance(reverse_converted_df, pd.DataFrame)
    assert is_a_string_list(reverse_converted_df['discrete_val'].to_list())
    assert reverse_converted_df.eq(df_data).all().all()

def test_const_handling_test_df(test_const_data: pd.DataFrame):
    """
    Test the handling of const columns in a DataFrame.
    This function tests the behavior of a DataFrame when it contains const columns.
    It is designed to be used in a testing environment, where the DataFrame is passed as an argument.

    Parameters:
    test_const_data (pd.DataFrame): The DataFrame to test.

    Returns:
    None

    Raises:
    AssertionError: If the DataFrame does not handle const columns as expected.
    """
    metadata = Metadata.from_dataframe(test_const_data)
    const_transformer = ConstValueTransformer()
    assert const_transformer.fitted is False
    const_transformer.fit(metadata)
    assert const_transformer.fitted
    assert sorted(const_transformer.const_columns) == ['age', 'fnlwgt', 'workclass']
    transformed_df = const_transformer.convert(test_const_data)
    assert 'age' not in transformed_df.columns
    assert 'fnlwgt' not in transformed_df.columns
    assert 'workclass' not in transformed_df.columns
    reverse_converted_df = const_transformer.reverse_convert(transformed_df)
    assert 'age' in reverse_converted_df.columns
    assert 'fnlwgt' in reverse_converted_df.columns
    assert 'workclass' in reverse_converted_df.columns
    assert reverse_converted_df['age'][0] == 100
    assert reverse_converted_df['fnlwgt'][0] == 1.41421
    assert reverse_converted_df['workclass'][0] == 'President'
    assert len(reverse_converted_df['age'].unique()) == 1
    assert len(reverse_converted_df['fnlwgt'].unique()) == 1
    assert len(reverse_converted_df['workclass'].unique()) == 1

@pytest.mark.skip(reason='success in local, failed in GitHub Action')
def test_int_formatter_fit_test_df():
    """
    Test the functionality of the IntValueFormatter class.

    This function tests the following:
    1. The fit method of the IntValueFormatter class.
    2. The addition of a new column to the formatter.
    3. The reverse conversion of the DataFrame.
    4. The checking of integer values in the DataFrame columns.

    Parameters:
    df_data (pd.DataFrame): The DataFrame to be tested.

    Returns:
    None

    Raises:
    AssertionError: If any of the assertions fail.
    """
    df = int_formatter_df()
    metadata_df = Metadata.from_dataframe(df)
    formatter = IntValueFormatter()
    formatter.fit(metadata_df)
    metadata_df.column_list = ['int_id', 'str_id', 'int_random', 'float_random']
    assert sorted(metadata_df.column_list) == sorted(['int_id', 'str_id', 'int_random', 'float_random'])
    assert 'int_random' in formatter.int_columns
    assert 'int_id' in formatter.int_columns
    reverse_df = formatter.reverse_convert(df)
    assert is_an_integer_list(reverse_df['int_id'].tolist())
    assert not is_an_integer_list(reverse_df['str_id'].tolist())
    assert is_an_integer_list(reverse_df['int_random'].tolist())

def test_datetime_formatter_test_df_dead_column(datetime_test_df: pd.DataFrame):
    """
    Test the DatetimeFormatter class with a DataFrame that has datetime columns.

    Parameters:
    datetime_test_df (pd.DataFrame): The DataFrame to test.

    Returns:
    None

    Raises:
    AssertionError: If any of the assertions fail.
    """
    assert datetime_test_df.shape == (1000, 7)
    metadata_df = Metadata.from_dataframe(datetime_test_df)
    assert metadata_df.datetime_columns == {'simple_datetime_2', 'date_with_time', 'simple_datetime'}
    metadata_df.datetime_format = {}
    transformer = DatetimeFormatter()
    transformer.fit(metadata=metadata_df)
    assert transformer.datetime_columns == []
    assert set(transformer.dead_columns) == {'simple_datetime_2', 'date_with_time', 'simple_datetime'}

def test_datetime_formatter_test_df(datetime_test_df: pd.DataFrame):
    """
    Test function for the DatetimeFormatter class.

    This function tests the functionality of the DatetimeFormatter class by creating a test DataFrame,
    setting the datetime format for the columns, fitting the transformer, converting the DataFrame,
    reversing the conversion, and checking if the reversed DataFrame is equal to the original one.

    Args:
        datetime_test_df (pd.DataFrame): The test DataFrame to be used for testing.

    Returns:
        None

    Raises:
        AssertionError: If any of the assertions fail.
    """
    assert datetime_test_df.shape == (1000, 7)
    metadata_df = Metadata.from_dataframe(datetime_test_df)
    assert metadata_df.datetime_columns == {'simple_datetime_2', 'date_with_time', 'simple_datetime'}
    datetime_format = {}
    datetime_format['simple_datetime'] = '%Y-%m-%d'
    datetime_format['simple_datetime_2'] = '%d %b %Y'
    datetime_format['date_with_time'] = '%Y-%m-%d %H:%M:%S'
    metadata_df.datetime_format = datetime_format
    transformer = DatetimeFormatter()
    assert not transformer.fitted
    transformer.fit(metadata=metadata_df)
    assert transformer.fitted
    assert transformer.dead_columns == []
    assert set(transformer.datetime_columns) == {'simple_datetime_2', 'date_with_time', 'simple_datetime'}
    converted_df = transformer.convert(datetime_test_df)
    assert is_an_integer_list(converted_df['date_with_time'].to_list())
    assert is_an_integer_list(converted_df['simple_datetime_2'].to_list())
    assert is_an_integer_list(converted_df['simple_datetime'].to_list())
    reverse_converte_df = transformer.reverse_convert(converted_df)
    assert is_a_string_list(reverse_converte_df['simple_datetime'].to_list())
    assert is_a_string_list(reverse_converte_df['date_with_time'].to_list())
    assert is_a_string_list(reverse_converte_df['simple_datetime_2'].to_list())
    assert reverse_converte_df.eq(datetime_test_df).all().all()

@pytest.fixture
def manager():
    yield InspectorManager()

@pytest.mark.parametrize('inspector_name', list(InspectorManager().registed_inspectors.keys()))
def test_inspector(inspector_name, manager: InspectorManager, raw_data: pd.DataFrame):
    each_inspector = manager.init(inspector_name)
    assert 'sdgx.data_models.inspectors' in str(type(each_inspector))
    assert each_inspector.ready is False
    if not 'relationship' in inspector_name:
        each_inspector.fit(raw_data)
        assert each_inspector.ready is True
    assert each_inspector.inspect_level <= 100 and each_inspector.inspect_level > 0
    each_inspector.inspect_level = 66
    assert each_inspector.inspect_level == 66
    each_inspector.inspect_level = 88
    assert each_inspector.inspect_level == 88
    each_inspector.inspect_level = 100
    assert each_inspector.inspect_level == 100
    each_inspector.inspect_level = 10
    assert each_inspector.inspect_level == 10
    has_error = False
    try:
        each_inspector.inspect_level = 101
    except Exception as e:
        has_error = True
        assert type(e) == InspectorInitError
    assert has_error is True
    has_error = False
    try:
        each_inspector.inspect_level = 0
    except Exception as e:
        has_error = True
        assert type(e) == InspectorInitError
    assert has_error is True

def test_const_inspector(test_const_data: pd.DataFrame):
    inspector = ConstInspector()
    inspector.fit(test_const_data)
    assert inspector.ready
    assert inspector.const_columns
    assert sorted(inspector.inspect()['const_columns']) == sorted(['age', 'fnlwgt', 'workclass'])
    assert inspector.inspect_level == 80

def test_inspector(inspector: DiscreteInspector, raw_data):
    inspector.fit(raw_data)
    assert inspector.ready
    assert inspector.discrete_columns
    assert sorted(inspector.inspect()['discrete_columns']) == sorted(['workclass', 'education', 'marital-status', 'occupation', 'relationship', 'race', 'gender', 'native-country', 'income'])
    assert inspector.inspect_level == 10

def test_email_inspector_demo_data(raw_data):
    inspector_Email = EmailInspector()
    inspector_Email.fit(raw_data)
    assert not inspector_Email.regex_columns
    assert sorted(inspector_Email.inspect()['email_columns']) == sorted([])
    assert inspector_Email.inspect_level == 30
    assert inspector_Email.pii is True

def test_email_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_Email = EmailInspector()
    inspector_Email.fit(chn_personal_test_df)
    assert inspector_Email.regex_columns
    assert sorted(inspector_Email.inspect()['email_columns']) == sorted(['email'])
    assert inspector_Email.inspect_level == 30
    assert inspector_Email.pii is True

def test_chn_phone_inspector_demo_data(raw_data):
    inspector_Phone = ChinaMainlandMobilePhoneInspector()
    inspector_Phone.fit(raw_data)
    assert not inspector_Phone.regex_columns
    assert sorted(inspector_Phone.inspect()['china_mainland_mobile_phone_columns']) == sorted([])
    assert inspector_Phone.inspect_level == 30
    assert inspector_Phone.pii is True

def test_chn_phone_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_Phone = ChinaMainlandMobilePhoneInspector()
    inspector_Phone.fit(chn_personal_test_df)
    assert inspector_Phone.regex_columns
    assert sorted(inspector_Phone.inspect()['china_mainland_mobile_phone_columns']) == sorted(['mobile_phone_no'])
    assert inspector_Phone.inspect_level == 30
    assert inspector_Phone.pii is True

def test_chn_ID_inspector_demo_data(raw_data):
    inspector_ID = ChinaMainlandIDInspector()
    inspector_ID.fit(raw_data)
    assert not inspector_ID.regex_columns
    assert sorted(inspector_ID.inspect()['china_mainland_id_columns']) == sorted([])
    assert inspector_ID.inspect_level == 30
    assert inspector_ID.pii is True

def test_chn_ID_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_ID = ChinaMainlandIDInspector()
    inspector_ID.fit(chn_personal_test_df)
    assert inspector_ID.regex_columns
    assert sorted(inspector_ID.inspect()['china_mainland_id_columns']) == sorted(['ssn_sfz'])
    assert inspector_ID.inspect_level == 30
    assert inspector_ID.pii is True

def test_chn_postcode_inspector_demo_data(raw_data):
    inspector_PostCode = ChinaMainlandPostCode()
    inspector_PostCode.fit(raw_data)
    assert not inspector_PostCode.regex_columns
    assert sorted(inspector_PostCode.inspect()['china_mainland_postcode_columns']) == sorted([])
    assert inspector_PostCode.inspect_level == 20
    assert inspector_PostCode.pii is False

def test_chn_postcode_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_PostCode = ChinaMainlandPostCode()
    inspector_PostCode.fit(chn_personal_test_df)
    assert inspector_PostCode.regex_columns
    assert sorted(inspector_PostCode.inspect()['china_mainland_postcode_columns']) == sorted(['postcode'])
    assert inspector_PostCode.inspect_level == 20
    assert inspector_PostCode.pii is False

def test_chn_uscc_inspector_demo_data(raw_data):
    inspector_USCC = ChinaMainlandUnifiedSocialCreditCode()
    inspector_USCC.fit(raw_data)
    assert not inspector_USCC.regex_columns
    assert sorted(inspector_USCC.inspect()['unified_social_credit_code_columns']) == sorted([])
    assert inspector_USCC.inspect_level == 30
    assert inspector_USCC.pii is True

def test_chn_uscc_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_USCC = ChinaMainlandUnifiedSocialCreditCode()
    inspector_USCC.fit(chn_personal_test_df)
    assert inspector_USCC.regex_columns
    assert sorted(inspector_USCC.inspect()['unified_social_credit_code_columns']) == sorted(['uscc'])
    assert inspector_USCC.inspect_level == 30
    assert inspector_USCC.pii is True

def test_chn_address_inspector_demo_data(raw_data):
    inspector_CHN_Address = ChinaMainlandAddressInspector()
    inspector_CHN_Address.fit(raw_data)
    assert not inspector_CHN_Address.regex_columns
    assert sorted(inspector_CHN_Address.inspect()['china_mainland_address_columns']) == sorted([])
    assert inspector_CHN_Address.inspect_level == 30
    assert inspector_CHN_Address.pii is True

def test_chn_address_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_CHN_Address = ChinaMainlandAddressInspector()
    inspector_CHN_Address.fit(chn_personal_test_df)
    assert inspector_CHN_Address.regex_columns
    assert sorted(inspector_CHN_Address.inspect()['china_mainland_address_columns']) == sorted(['chn_address'])
    assert inspector_CHN_Address.inspect_level == 30
    assert inspector_CHN_Address.pii is True

def test_chn_name_inspector_demo_data(raw_data):
    inspector_CHN_name = ChineseNameInspector()
    inspector_CHN_name.fit(raw_data)
    assert not inspector_CHN_name.regex_columns
    assert sorted(inspector_CHN_name.inspect()['chinese_name_columns']) == sorted([])
    assert inspector_CHN_name.inspect_level == 40
    assert inspector_CHN_name.pii is True

def test_chn_name_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_CHN_name = ChineseNameInspector()
    inspector_CHN_name.fit(chn_personal_test_df)
    assert inspector_CHN_name.regex_columns
    assert sorted(inspector_CHN_name.inspect()['chinese_name_columns']) == sorted(['chn_name'])
    assert inspector_CHN_name.inspect_level == 40
    assert inspector_CHN_name.pii is True

def test_eng_name_inspector_demo_data(raw_data):
    inspector_ENG_name = EnglishNameInspector()
    inspector_ENG_name.fit(raw_data)
    assert not inspector_ENG_name.regex_columns
    assert sorted(inspector_ENG_name.inspect()['english_name_columns']) == sorted([])
    assert inspector_ENG_name.inspect_level == 40
    assert inspector_ENG_name.pii is True

def test_eng_name_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_ENG_name = EnglishNameInspector()
    inspector_ENG_name.fit(chn_personal_test_df)
    assert inspector_ENG_name.regex_columns
    assert sorted(inspector_ENG_name.inspect()['english_name_columns']) == sorted(['eng_name'])
    assert inspector_ENG_name.inspect_level == 40
    assert inspector_ENG_name.pii is True

def test_chn_company_inspector_demo_data(raw_data):
    inspector_PostCode = ChineseCompanyNameInspector()
    inspector_PostCode.fit(raw_data)
    assert not inspector_PostCode.regex_columns
    assert sorted(inspector_PostCode.inspect()['chinese_company_name_columns']) == sorted([])
    assert inspector_PostCode.inspect_level == 40
    assert inspector_PostCode.pii is False

def test_chn_company_inspector_generated_data(chn_personal_test_df: pd.DataFrame):
    inspector_PostCode = ChineseCompanyNameInspector()
    inspector_PostCode.fit(chn_personal_test_df)
    assert inspector_PostCode.regex_columns
    assert sorted(inspector_PostCode.inspect()['chinese_company_name_columns']) == sorted(['company_name'])
    assert inspector_PostCode.inspect_level == 40
    assert inspector_PostCode.pii is False

def test_inspector(inspector: NumericInspector, raw_data):
    inspector.fit(raw_data)
    assert inspector.ready
    assert inspector.int_columns
    assert sorted(inspector.inspect()['int_columns']) == sorted(['educational-num', 'fnlwgt', 'hours-per-week', 'age', 'capital-gain', 'capital-loss'])
    assert not inspector.float_columns
    assert inspector.inspect_level == 10
    assert inspector.negative_columns == set()
    assert inspector.positive_columns == {'age', 'hours-per-week', 'fnlwgt', 'educational-num'}
    assert set(inspector.inspect().keys()) == {'int_columns', 'float_columns', 'numeric_format'}

@pytest.fixture
def inspector():
    yield DatetimeInspector()

def test_inspector_demo_data(inspector: DatetimeInspector, raw_data):
    inspector.fit(raw_data)
    assert inspector.ready
    assert not inspector.datetime_columns
    assert sorted(inspector.inspect()['datetime_columns']) == sorted([])
    assert inspector.inspect_level == 20

def test_inspector_generated_data(inspector: DatetimeInspector, datetime_test_df: pd.DataFrame):
    inspector.fit(datetime_test_df)
    assert inspector.datetime_columns
    assert sorted(inspector.inspect()['datetime_columns']) == sorted(['simple_datetime', 'simple_datetime_2', 'date_with_time'])
    assert inspector.inspect_level == 20

def test_custom_format_detection(datetime_test_df: pd.DataFrame):
    inspector = DatetimeInspector(user_formats=['%Y-%m-%d %H:%M:%S'])
    inspector.fit(datetime_test_df)
    result = inspector.inspect()
    assert result['datetime_formats']['simple_datetime'] == '%Y-%m-%d %H:%M:%S'
    assert result['datetime_formats']['simple_datetime_2'] == '%d %b %Y'
    assert result['datetime_formats']['date_with_time'] == '%Y-%m-%d %H:%M:%S'
    assert inspector.inspect_level == 20

def test_inspector(dummy_data, dummy_relationship, inspector: SubsetRelationshipInspector):
    for raw_data, name, metadata in dummy_data:
        inspector.fit(raw_data, name=name, metadata=metadata)
    relationships = inspector.inspect()['relationships']
    assert relationships
    assert relationships == [dummy_relationship]

def test_fixed_combination_inspector(test_fixed_combination_data: pd.DataFrame):
    inspector = FixedCombinationInspector()
    inspector.fit(test_fixed_combination_data)
    assert inspector.ready
    assert inspector.fixed_combinations
    expected_combinations = {'A': {'categorical_3', 'D', 'E', 'B'}, 'B': {'categorical_3', 'D', 'E', 'A'}, 'D': {'categorical_3', 'E', 'A', 'B'}, 'E': {'categorical_3', 'D', 'A', 'B'}, 'categorical_3': {'categorical_4', 'D', 'E', 'A', 'B'}, 'categorical_1': {'categorical_2'}, 'categorical_5': {'categorical_6'}}
    assert inspector.fixed_combinations == expected_combinations
    assert inspector.inspect_level == 70

def test_inspector(inspector: EmptyInspector, test_empty_data):
    inspector.fit(test_empty_data)
    assert inspector.ready
    assert inspector.empty_columns
    assert sorted(inspector.inspect()['empty_columns']) == sorted(['age', 'fnlwgt'])
    assert inspector.inspect_level == 90

def test_int_regex_inspector_demo_data(int_inspector: RegexInspector, raw_data: pd.DataFrame):
    int_inspector.fit(raw_data)
    assert int_inspector.ready
    assert int_inspector.regex_columns
    assert sorted(int_inspector.inspect()['int_columns']) == sorted(['age', 'capital-gain', 'capital-loss', 'educational-num', 'fnlwgt', 'hours-per-week'])
    assert int_inspector.inspect_level == 10

def test_empty_regex_inspector_demo_data(empty_inspector: RegexInspector, raw_data: pd.DataFrame):
    empty_inspector.fit(raw_data)
    assert empty_inspector.ready
    assert not empty_inspector.regex_columns
    assert sorted(empty_inspector.inspect()['empty_columns']) == sorted([])
    assert empty_inspector.inspect_level == 10

def test_inspector_demo_data(inspector: BoolInspector, raw_data):
    inspector.fit(raw_data)
    assert inspector.ready
    assert not inspector.bool_columns
    assert sorted(inspector.inspect()['bool_columns']) == sorted([])
    assert inspector.inspect_level == 10

def test_inspector_generated_data(inspector: BoolInspector, bool_test_df: pd.DataFrame):
    inspector.fit(bool_test_df)
    assert inspector.bool_columns
    assert sorted(inspector.inspect()['bool_columns']) == sorted(['bool_random'])

def test_inspector_demo_data(inspector: IDInspector, raw_data):
    inspector.fit(raw_data)
    assert inspector.ready
    assert not inspector.ID_columns
    assert sorted(inspector.inspect()['id_columns']) == sorted([])
    assert inspector.inspect_level == 20

def test_inspector_generated_data(inspector: IDInspector, id_test_df: pd.DataFrame):
    inspector.fit(id_test_df)
    assert inspector.ID_columns
    assert sorted(inspector.inspect()['id_columns']) == sorted(['int_id', 'str_id'])

