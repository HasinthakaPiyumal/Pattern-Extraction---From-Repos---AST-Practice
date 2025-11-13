# Cluster 12

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

def __del__(self):
    self.cleanup()

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

def __init__(self):
    self.fitted = False
    self.datetime_columns = []
    self.datetime_formats = defaultdict(str)
    self.dead_columns = []

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

def has_number(s):
    for char in s:
        if char.isdigit():
            return True
    return False

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

def has_number(s):
    for char in s:
        if char.isdigit():
            return True
    return False

def _key_order(key_value):
    parts = []
    for part in key_value[0].split('__'):
        if part.isdigit():
            part = int(part)
        parts.append(part)
    return parts

def unflatten_dict(flat):
    """Transform a flattened dict into its original form.

    Args:
        flat (dict):
            Flattened dict.

    Returns:
        dict:
            Nested dict (if corresponds)
    """
    unflattened = {}
    for key, value in sorted(flat.items(), key=_key_order):
        if '__' in key:
            key, subkey = key.split('__', 1)
            subkey, name = subkey.rsplit('__', 1)
            if name.isdigit():
                column_index = int(name)
                row_index = int(subkey)
                array = unflattened.setdefault(key, [])
                if len(array) == row_index:
                    row = []
                    array.append(row)
                elif len(array) == row_index + 1:
                    row = array[row_index]
                else:
                    raise ValueError('There was an error unflattening the extension.')
                if len(row) == column_index:
                    row.append(value)
                else:
                    raise ValueError('There was an error unflattening the extension.')
            else:
                subdict = unflattened.setdefault(key, {})
                if subkey.isdigit():
                    subkey = int(subkey)
                inner = subdict.setdefault(subkey, {})
                inner[name] = value
        else:
            unflattened[key] = value
    return unflattened

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

@staticmethod
def get_auto_save(raw_data) -> NDArrayLoader:
    save_to_file = True
    if isinstance(raw_data, pd.DataFrame) or (isinstance(raw_data, DataLoader) and isinstance(raw_data.data_connector, DataFrameConnector)):
        save_to_file = False
    return NDArrayLoader(save_to_file=save_to_file)

def __del__(self):
    self.cleanup()

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

class Config(dict):
    """Config dict for ``HyperTransformer`` with a better representation."""

    def __repr__(self):
        """Pretty print the dictionary."""
        config = {'sdtypes': self['sdtypes'], 'transformers': {k: repr(v) for k, v in self['transformers'].items()}}
        printed = json.dumps(config, indent=4)
        for transformer in self['transformers'].values():
            quoted_transformer = f'"{transformer}"'
            if quoted_transformer in printed:
                printed = printed.replace(quoted_transformer, repr(transformer))
        return printed

def __repr__(self):
    """Pretty print the dictionary."""
    config = {'sdtypes': self['sdtypes'], 'transformers': {k: repr(v) for k, v in self['transformers'].items()}}
    printed = json.dumps(config, indent=4)
    for transformer in self['transformers'].values():
        quoted_transformer = f'"{transformer}"'
        if quoted_transformer in printed:
            printed = printed.replace(quoted_transformer, repr(transformer))
    return printed

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

def _reverse_transform_by_category(self, data):
    """Reverse transform the data by iterating over all the categories."""
    result = np.empty(shape=(len(data),), dtype=self.dtype)
    for category, values in self.intervals.items():
        start = values[0]
        mask = start <= data.to_numpy()
        result[mask] = category
    return pd.Series(result, index=data.index, dtype=self.dtype)

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

def __init__(self, add_noise=False, order_by=None):
    self.add_noise = add_noise
    if order_by not in [None, 'alphabetical', 'numerical_value']:
        raise Error("order_by must be one of the following values: None, 'numerical_value' or 'alphabetical'")
    self.order_by = order_by

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

def _add_prefix(self, dictionary):
    if not dictionary:
        return {}
    output = {}
    for output_columns, output_sdtype in dictionary.items():
        output[f'{self.column_prefix}.{output_columns}'] = output_sdtype
    return output

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

def _from_generators(generators, max_repeat):
    previous = [None] + [next(generator) for generator, _, _ in generators[1:]]
    remaining = True
    while remaining:
        generated = []
        for index, (generator, option, args) in enumerate(generators):
            remaining = True
            try:
                value = next(generator)
                generated.append(value)
                previous[index] = value
                generated.extend(previous[index + 1:])
                break
            except StopIteration:
                generator = _GENERATORS[option](args, max_repeat)[0]
                generators[index] = (generator, option, args)
                value = next(generator)
                previous[index] = value
                generated.append(value)
                remaining = False
        if remaining:
            yield ''.join(reversed(generated))

@lru_cache()
def get_transformers_by_type():
    """Build a ``dict`` mapping sdtypes to valid existing transformers for that sdtype.

    Returns:
        dict:
            Mapping of sdtypes to a list of existing transformers that take that
            sdtype as an input.
    """
    sdtype_transformers = defaultdict(list)
    transformer_classes = BaseTransformer.get_subclasses()
    for transformer in transformer_classes:
        input_sdtype = transformer.get_input_sdtype()
        sdtype_transformers[input_sdtype].append(transformer)
    return sdtype_transformers

@lru_cache()
def get_default_transformers():
    """Build a ``dict`` mapping sdtypes to a default transformer for that sdtype.

    Returns:
        dict:
            Mapping of sdtypes to a transformer.
    """
    transformers_by_type = get_transformers_by_type()
    defaults = deepcopy(DEFAULT_TRANSFORMERS)
    for sdtype, transformers in transformers_by_type.items():
        if sdtype not in defaults:
            defaults[sdtype] = transformers[0]()
    return defaults

@lru_cache()
def get_default_transformer(sdtype):
    """Get default transformer for a sdtype.

    Returns:
        Transformer:
            Default transformer for sdtype.
    """
    default_transformers = get_default_transformers()
    return default_transformers[sdtype]

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

class PseudoAnonymizedFaker(AnonymizedFaker):
    """Pseudo-anonymization Transformer using Faker.

    This transformer anonymizes values that can be traced back to the original input by using
    a mapping. The transformer will generate a mapping with the previously specified
    ``Faker`` provider and ``function``.

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
    """
    OUTPUT_SDTYPES = {'value': 'categorical'}
    NEXT_TRANSFORMER = {'value': LabelEncoder(add_noise=True)}

    def __getstate__(self):
        """Return a dictionary representation of the instance and warn the user when pickling."""
        warnings.warn('You are saving the mapping information, which includes the original data. Sharing this object with others will also give them access to the original data used with this transformer.')
        return self.__dict__

    def __init__(self, provider_name=None, function_name=None, function_kwargs=None, locales=None):
        super().__init__(provider_name=provider_name, function_name=function_name, function_kwargs=function_kwargs, locales=locales)
        self._mapping_dict = {}
        self._reverse_mapping_dict = {}

    def _function(self):
        """Return a callable ``faker`` function."""
        return getattr(self.faker.unique, self.function_name)(**self.function_kwargs)

    def get_mapping(self):
        """Return the mapping dictionary."""
        return deepcopy(self._mapping_dict)

    def _fit(self, columns_data):
        """Fit the transformer to the data.

        Generate a ``_mapping_dict`` and a ``_reverse_mapping_dict`` for each
        value in the provided ``columns_data`` using the ``Faker`` provider and
        ``function``.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        unique_values = columns_data[columns_data.notna()].unique()
        unique_data_length = len(unique_values)
        try:
            generated_values = [self._function() for _ in range(unique_data_length)]
        except faker.exceptions.UniquenessException as exception:
            raise Error(f'The Faker function you specified is not able to generate {unique_data_length} unique values. Please use a different Faker function for this column.') from exception
        generated_values = list(set(generated_values))
        self._mapping_dict = dict(zip(unique_values, generated_values))
        self._reverse_mapping_dict = dict(zip(generated_values, unique_values))

    def _transform(self, columns_data):
        """Replace each category with a numerical representation.

        Map the input ``columns_data`` using the previously generated values for each one.
        If the  ``columns_data`` contain unknown values, a ``Error`` will be raised with the
        unknown categories.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            pd.Series
        """
        unique_values = columns_data[columns_data.notna()].unique()
        new_values = list(set(unique_values) - set(self._mapping_dict))
        if new_values:
            new_values = [str(value) for value in new_values]
            if len(new_values) < 5:
                new_values = ', '.join(new_values)
                error_msg = f'The data you are transforming has new, unexpected values ({new_values}). Please fit the transformer again using this new data.'
            else:
                diff = len(new_values) - 5
                new_values = ', '.join(new_values[:5])
                error_msg = f'The data you are transforming has new, unexpected values ({new_values} and {diff} more). Please fit the transformer again using this new data.'
            raise Error(error_msg)
        mapped_data = columns_data.map(self._mapping_dict)
        return mapped_data

    def _reverse_transform(self, columns_data):
        """Return the input data.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to revert.

        Returns:
            pandas.Series
        """
        return columns_data

def __getstate__(self):
    """Return a dictionary representation of the instance and warn the user when pickling."""
    warnings.warn('You are saving the mapping information, which includes the original data. Sharing this object with others will also give them access to the original data used with this transformer.')
    return self.__dict__

class BaseDatasetGenerator(ABC):
    """Parent class for all the Dataset Generators."""
    SDTYPE = None

    @staticmethod
    @abstractmethod
    def generate(num_rows):
        """Return array of data. This method serves as a template for dataset generators.

        Args:
            num_rows (int):
                Number of rows to generate.

        Returns:
            numpy.ndarray of size ``num_rows``
        """
        raise NotImplementedError()

    @classmethod
    def get_subclasses(cls):
        """Recursively find subclasses of this Baseline.

        Returns:
            list:
                List of all subclasses of this class.
        """
        subclasses = []
        for subclass in cls.__subclasses__():
            if ABC not in subclass.__bases__:
                subclasses.append(subclass)
            subclasses += subclass.get_subclasses()
        return subclasses

    @staticmethod
    @abstractmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        raise NotImplementedError()

@classmethod
def get_subclasses(cls):
    """Recursively find subclasses of this Baseline.

        Returns:
            list:
                List of all subclasses of this class.
        """
    subclasses = []
    for subclass in cls.__subclasses__():
        if ABC not in subclass.__bases__:
            subclasses.append(subclass)
        subclasses += subclass.get_subclasses()
    return subclasses

def get_dataset_generators_by_type():
    """Build a ``dict`` mapping sdtypes to dataset generators.

    Returns:
        dict:
            Mapping of sdtype to a list of dataset generators that produce
            data of that sdtype.
    """
    dataset_generators = defaultdict(list)
    for dataset_generator in BaseDatasetGenerator.get_subclasses():
        dataset_generators[dataset_generator.SDTYPE].append(dataset_generator)
    return dataset_generators

def select_univariate(X, candidates):
    """Select the best univariate class for this data.

    Args:
        X (pandas.DataFrame):
            Data for which be best univariate must be found.
        candidates (list[Univariate]):
            List of Univariate subclasses (or instances of those) to choose from.

    Returns:
        Univariate:
            Instance of the selected candidate.
    """
    best_ks = np.inf
    best_model = None
    for model in candidates:
        try:
            instance = get_instance(model)
            instance.fit(X)
            ks, _ = kstest(X, instance.cdf)
            if ks < best_ks:
                best_ks = ks
                best_model = model
        except Exception:
            pass
    return get_instance(best_model)

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

def check_fit(self):
    """Check whether this model has already been fit to a random variable.

        Raise a ``NotFittedError`` if it has not.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
    if not self.fitted:
        raise NotFittedError('This model is not fitted.')

class GaussianMultivariate(Multivariate):
    """Class for a multivariate distribution that uses the Gaussian copula.

    Args:
        distribution (str or dict):
            Fully qualified name of the class to be used for modeling the marginal
            distributions or a dictionary mapping column names to the fully qualified
            distribution names.
    """
    covariance = None
    columns = None
    univariates = None

    @store_args
    def __init__(self, distribution=DEFAULT_DISTRIBUTION, random_state=None):
        self.random_state = validate_random_state(random_state)
        self.distribution = distribution

    def __repr__(self):
        """Produce printable representation of the object."""
        if self.distribution == DEFAULT_DISTRIBUTION:
            distribution = ''
        elif isinstance(self.distribution, type):
            distribution = f'distribution="{self.distribution.__name__}"'
        else:
            distribution = f'distribution="{self.distribution}"'
        return f'GaussianMultivariate({distribution})'

    def _transform_to_normal(self, X):
        if isinstance(X, pd.Series):
            X = X.to_frame().T
        elif not isinstance(X, pd.DataFrame):
            if len(X.shape) == 1:
                X = [X]
            X = pd.DataFrame(X, columns=self.columns)
        U = []
        for column_name, univariate in zip(self.columns, self.univariates):
            if column_name in X:
                column = X[column_name]
                U.append(univariate.cdf(column.to_numpy()).clip(EPSILON, 1 - EPSILON))
        return stats.norm.ppf(np.column_stack(U))

    def _get_covariance(self, X):
        """Compute covariance matrix with transformed data.

        Args:
            X (numpy.ndarray):
                Data for which the covariance needs to be computed.

        Returns:
            numpy.ndarray:
                computed covariance matrix.
        """
        result = self._transform_to_normal(X)
        covariance = pd.DataFrame(data=result).corr().to_numpy()
        covariance = np.nan_to_num(covariance, nan=0.0)
        if np.linalg.cond(covariance) > 1.0 / sys.float_info.epsilon:
            covariance = covariance + np.identity(covariance.shape[0]) * EPSILON
        return pd.DataFrame(covariance, index=self.columns, columns=self.columns)

    @check_valid_values
    def fit(self, X):
        """Compute the distribution for each variable and then its covariance matrix.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
        LOGGER.info('Fitting %s', self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        columns = []
        univariates = []
        for column_name, column in X.items():
            if isinstance(self.distribution, dict):
                distribution = self.distribution.get(column_name, DEFAULT_DISTRIBUTION)
            else:
                distribution = self.distribution
            LOGGER.debug('Fitting column %s to %s', column_name, distribution)
            univariate = get_instance(distribution)
            try:
                univariate.fit(column)
            except BaseException:
                warning_message = f'Unable to fit to a {distribution} distribution for column {column_name}. Using a Gaussian distribution instead.'
                warnings.warn(warning_message)
                univariate = GaussianUnivariate()
                univariate.fit(column)
            columns.append(column_name)
            univariates.append(univariate)
        self.columns = columns
        self.univariates = univariates
        LOGGER.debug('Computing covariance')
        self.covariance = self._get_covariance(X)
        self.fitted = True
        LOGGER.debug('GaussianMultivariate fitted successfully')

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
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.pdf(transformed, cov=self.covariance)

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
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.cdf(transformed, cov=self.covariance)

    def _get_conditional_distribution(self, conditions):
        """Compute the parameters of a conditional multivariate normal distribution.

        The parameters of the conditioned distribution are computed as specified here:
        https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Conditional_distributions

        Args:
            conditions (pandas.Series):
                Mapping of the column names and column values to condition on.
                The input values have already been transformed to their normal distribution.

        Returns:
            tuple:
                * means (numpy.array):
                    mean values to use for the conditioned multivariate normal.
                * covariance (numpy.array):
                    covariance matrix to use for the conditioned
                  multivariate normal.
                * columns (list):
                    names of the columns that will be sampled conditionally.
        """
        columns2 = conditions.index
        columns1 = self.covariance.columns.difference(columns2)
        sigma11 = self.covariance.loc[columns1, columns1].to_numpy()
        sigma12 = self.covariance.loc[columns1, columns2].to_numpy()
        sigma21 = self.covariance.loc[columns2, columns1].to_numpy()
        sigma22 = self.covariance.loc[columns2, columns2].to_numpy()
        mu1 = np.zeros(len(columns1))
        mu2 = np.zeros(len(columns2))
        sigma12sigma22inv = sigma12 @ np.linalg.inv(sigma22)
        mu_bar = mu1 + sigma12sigma22inv @ (conditions - mu2)
        sigma_bar = sigma11 - sigma12sigma22inv @ sigma21
        return (mu_bar, sigma_bar, columns1)

    def _get_normal_samples(self, num_rows, conditions):
        """Get random rows in the standard normal space.

        If no conditions are given, the values are sampled from a standard normal
        multivariate.

        If conditions are given, they are transformed to their equivalent standard
        normal values using their marginals and then the values are sampled from
        a standard normal multivariate conditioned on the given condition values.
        """
        if conditions is None:
            covariance = self.covariance
            columns = self.columns
            means = np.zeros(len(columns))
        else:
            conditions = pd.Series(conditions)
            normal_conditions = self._transform_to_normal(conditions)[0]
            normal_conditions = pd.Series(normal_conditions, index=conditions.index)
            means, covariance, columns = self._get_conditional_distribution(normal_conditions)
        samples = np.random.multivariate_normal(means, covariance, size=num_rows)
        return pd.DataFrame(samples, columns=columns)

    @random_state
    def sample(self, num_rows=1, conditions=None):
        """Sample values from this model.

        Argument:
            num_rows (int):
                Number of rows to sample.
            conditions (dict or pd.Series):
                Mapping of the column names and column values to condition on.

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, *) with values randomly
                sampled from this model distribution. If conditions have been
                given, the output array also contains the corresponding columns
                populated with the given values.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        samples = self._get_normal_samples(num_rows, conditions)
        output = {}
        for column_name, univariate in zip(self.columns, self.univariates):
            if conditions and column_name in conditions:
                output[column_name] = np.full(num_rows, conditions[column_name])
            else:
                cdf = stats.norm.cdf(samples[column_name])
                output[column_name] = univariate.percent_point(cdf)
        return pd.DataFrame(data=output)

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
        self.check_fit()
        univariates = [univariate.to_dict() for univariate in self.univariates]
        warnings.warn('`covariance` will be renamed to `correlation` in v0.4.0', DeprecationWarning)
        return {'covariance': self.covariance.to_numpy().tolist(), 'univariates': univariates, 'columns': self.columns, 'type': get_qualified_name(self)}

    @classmethod
    def from_dict(cls, copula_dict):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the distribution, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Multivariate:
                Instance of the distribution defined on the parameters.
        """
        instance = cls()
        instance.univariates = []
        columns = copula_dict['columns']
        instance.columns = columns
        for parameters in copula_dict['univariates']:
            instance.univariates.append(Univariate.from_dict(parameters))
        covariance = copula_dict['covariance']
        instance.covariance = pd.DataFrame(covariance, index=columns, columns=columns)
        instance.fitted = True
        warnings.warn('`covariance` will be renamed to `correlation` in v0.4.0', DeprecationWarning)
        return instance

@check_valid_values
def fit(self, X):
    """Compute the distribution for each variable and then its covariance matrix.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
    LOGGER.info('Fitting %s', self)
    if not isinstance(X, pd.DataFrame):
        X = pd.DataFrame(X)
    columns = []
    univariates = []
    for column_name, column in X.items():
        if isinstance(self.distribution, dict):
            distribution = self.distribution.get(column_name, DEFAULT_DISTRIBUTION)
        else:
            distribution = self.distribution
        LOGGER.debug('Fitting column %s to %s', column_name, distribution)
        univariate = get_instance(distribution)
        try:
            univariate.fit(column)
        except BaseException:
            warning_message = f'Unable to fit to a {distribution} distribution for column {column_name}. Using a Gaussian distribution instead.'
            warnings.warn(warning_message)
            univariate = GaussianUnivariate()
            univariate.fit(column)
        columns.append(column_name)
        univariates.append(univariate)
    self.columns = columns
    self.univariates = univariates
    LOGGER.debug('Computing covariance')
    self.covariance = self._get_covariance(X)
    self.fitted = True
    LOGGER.debug('GaussianMultivariate fitted successfully')

@classmethod
def from_dict(cls, copula_dict):
    """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the distribution, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Multivariate:
                Instance of the distribution defined on the parameters.
        """
    instance = cls()
    instance.univariates = []
    columns = copula_dict['columns']
    instance.columns = columns
    for parameters in copula_dict['univariates']:
        instance.univariates.append(Univariate.from_dict(parameters))
    covariance = copula_dict['covariance']
    instance.covariance = pd.DataFrame(covariance, index=columns, columns=columns)
    instance.fitted = True
    warnings.warn('`covariance` will be renamed to `correlation` in v0.4.0', DeprecationWarning)
    return instance

class CenterTree(Tree):
    """Tree for a C-vine copula."""
    tree_type = TreeTypes.CENTER

    def _build_first_tree(self):
        """Build first level tree."""
        tau_sorted = self._sort_tau_by_y(0)
        for itr in range(self.n_nodes - 1):
            ind = int(tau_sorted[itr, 0])
            copula = Bivariate.select_copula(self.u_matrix[:, (0, ind)])
            name, theta = (copula.copula_type, copula.theta)
            new_edge = Edge(itr, 0, ind, name, theta)
            new_edge.tau = self.tau_matrix[0, ind]
            self.edges.append(new_edge)

    def _build_kth_tree(self):
        """Build k-th level tree."""
        anchor = self.get_anchor()
        aux_sorted = self._sort_tau_by_y(anchor)
        edges = self.previous_tree.edges
        for itr in range(self.n_nodes - 1):
            right = int(aux_sorted[itr, 0])
            left_parent, right_parent = Edge.sort_edge([edges[anchor], edges[right]])
            new_edge = Edge.get_child_edge(itr, left_parent, right_parent)
            new_edge.tau = aux_sorted[itr, 1]
            self.edges.append(new_edge)

    def get_anchor(self):
        """Find anchor variable with highest sum of dependence with the rest.

        Returns:
            int:
                Anchor variable.
        """
        temp = np.empty([self.n_nodes, 2])
        temp[:, 0] = np.arange(self.n_nodes, dtype=int)
        temp[:, 1] = np.sum(abs(self.tau_matrix), 1)
        anchor = int(temp[0, 0])
        return anchor

def _build_first_tree(self):
    """Build first level tree."""
    tau_sorted = self._sort_tau_by_y(0)
    for itr in range(self.n_nodes - 1):
        ind = int(tau_sorted[itr, 0])
        copula = Bivariate.select_copula(self.u_matrix[:, (0, ind)])
        name, theta = (copula.copula_type, copula.theta)
        new_edge = Edge(itr, 0, ind, name, theta)
        new_edge.tau = self.tau_matrix[0, ind]
        self.edges.append(new_edge)

def _build_kth_tree(self):
    """Build k-th level tree."""
    anchor = self.get_anchor()
    aux_sorted = self._sort_tau_by_y(anchor)
    edges = self.previous_tree.edges
    for itr in range(self.n_nodes - 1):
        right = int(aux_sorted[itr, 0])
        left_parent, right_parent = Edge.sort_edge([edges[anchor], edges[right]])
        new_edge = Edge.get_child_edge(itr, left_parent, right_parent)
        new_edge.tau = aux_sorted[itr, 1]
        self.edges.append(new_edge)

class DirectTree(Tree):
    """DirectTree class."""
    tree_type = TreeTypes.DIRECT

    def _build_first_tree(self):
        tau_matrix = self.tau_matrix
        tau_sorted = self._sort_tau_by_y(0)
        left_ind = tau_sorted[0, 0]
        right_ind = tau_sorted[1, 0]
        T1 = np.array([left_ind, 0, right_ind]).astype(int)
        tau_T1 = tau_sorted[:2, 1]
        tau_matrix[:, [T1]] = -10
        for k in range(2, self.n_nodes - 1):
            left = np.argmax(tau_matrix[T1[0], :])
            right = np.argmax(tau_matrix[T1[-1], :])
            valL = np.max(tau_matrix[T1[0], :])
            valR = np.max(tau_matrix[T1[-1], :])
            if valL > valR:
                T1 = np.append(int(left), T1)
                tau_T1 = np.append(valL, tau_T1)
                tau_matrix[:, left] = -10
            else:
                T1 = np.append(T1, int(right))
                tau_T1 = np.append(tau_T1, valR)
                tau_matrix[:, right] = -10
        for k in range(self.n_nodes - 1):
            copula = Bivariate.select_copula(self.u_matrix[:, (T1[k], T1[k + 1])])
            name, theta = (copula.copula_type, copula.theta)
            left, right = sorted([T1[k], T1[k + 1]])
            new_edge = Edge(k, left, right, name, theta)
            new_edge.tau = tau_T1[k]
            self.edges.append(new_edge)

    def _build_kth_tree(self):
        edges = self.previous_tree.edges
        for k in range(self.n_nodes - 1):
            left_parent, right_parent = Edge.sort_edge([edges[k], edges[k + 1]])
            new_edge = Edge.get_child_edge(k, left_parent, right_parent)
            new_edge.tau = self.tau_matrix[k, k + 1]
            self.edges.append(new_edge)

def _build_first_tree(self):
    tau_matrix = self.tau_matrix
    tau_sorted = self._sort_tau_by_y(0)
    left_ind = tau_sorted[0, 0]
    right_ind = tau_sorted[1, 0]
    T1 = np.array([left_ind, 0, right_ind]).astype(int)
    tau_T1 = tau_sorted[:2, 1]
    tau_matrix[:, [T1]] = -10
    for k in range(2, self.n_nodes - 1):
        left = np.argmax(tau_matrix[T1[0], :])
        right = np.argmax(tau_matrix[T1[-1], :])
        valL = np.max(tau_matrix[T1[0], :])
        valR = np.max(tau_matrix[T1[-1], :])
        if valL > valR:
            T1 = np.append(int(left), T1)
            tau_T1 = np.append(valL, tau_T1)
            tau_matrix[:, left] = -10
        else:
            T1 = np.append(T1, int(right))
            tau_T1 = np.append(tau_T1, valR)
            tau_matrix[:, right] = -10
    for k in range(self.n_nodes - 1):
        copula = Bivariate.select_copula(self.u_matrix[:, (T1[k], T1[k + 1])])
        name, theta = (copula.copula_type, copula.theta)
        left, right = sorted([T1[k], T1[k + 1]])
        new_edge = Edge(k, left, right, name, theta)
        new_edge.tau = tau_T1[k]
        self.edges.append(new_edge)

def _build_kth_tree(self):
    edges = self.previous_tree.edges
    for k in range(self.n_nodes - 1):
        left_parent, right_parent = Edge.sort_edge([edges[k], edges[k + 1]])
        new_edge = Edge.get_child_edge(k, left_parent, right_parent)
        new_edge.tau = self.tau_matrix[k, k + 1]
        self.edges.append(new_edge)

class RegularTree(Tree):
    """RegularTree class."""
    tree_type = TreeTypes.REGULAR

    def _build_first_tree(self):
        """Build the first tree with n-1 variable."""
        neg_tau = -1.0 * abs(self.tau_matrix)
        X = {0}
        while len(X) != self.n_nodes:
            adj_set = set()
            for x in X:
                for k in range(self.n_nodes):
                    if k not in X and k != x:
                        adj_set.add((x, k))
            edge = sorted(adj_set, key=lambda e: neg_tau[e[0]][e[1]])[0]
            copula = Bivariate.select_copula(self.u_matrix[:, (edge[0], edge[1])])
            name, theta = (copula.copula_type, copula.theta)
            left, right = sorted([edge[0], edge[1]])
            new_edge = Edge(len(X) - 1, left, right, name, theta)
            new_edge.tau = self.tau_matrix[edge[0], edge[1]]
            self.edges.append(new_edge)
            X.add(edge[1])

    def _build_kth_tree(self):
        """Build tree for level k."""
        neg_tau = -1.0 * abs(self.tau_matrix)
        edges = self.previous_tree.edges
        visited = {0}
        unvisited = set(range(self.n_nodes))
        while len(visited) != self.n_nodes:
            adj_set = set()
            for x in visited:
                for k in range(self.n_nodes):
                    if k not in visited and k != x and self._check_constraint(edges[x], edges[k]):
                        adj_set.add((x, k))
            if len(adj_set) == 0:
                visited.add(list(unvisited)[0])
                continue
            pairs = sorted(adj_set, key=lambda e: neg_tau[e[0]][e[1]])[0]
            left_parent, right_parent = Edge.sort_edge([edges[pairs[0]], edges[pairs[1]]])
            new_edge = Edge.get_child_edge(len(visited) - 1, left_parent, right_parent)
            new_edge.tau = self.tau_matrix[pairs[0], pairs[1]]
            self.edges.append(new_edge)
            visited.add(pairs[1])
            unvisited.remove(pairs[1])

def _build_first_tree(self):
    """Build the first tree with n-1 variable."""
    neg_tau = -1.0 * abs(self.tau_matrix)
    X = {0}
    while len(X) != self.n_nodes:
        adj_set = set()
        for x in X:
            for k in range(self.n_nodes):
                if k not in X and k != x:
                    adj_set.add((x, k))
        edge = sorted(adj_set, key=lambda e: neg_tau[e[0]][e[1]])[0]
        copula = Bivariate.select_copula(self.u_matrix[:, (edge[0], edge[1])])
        name, theta = (copula.copula_type, copula.theta)
        left, right = sorted([edge[0], edge[1]])
        new_edge = Edge(len(X) - 1, left, right, name, theta)
        new_edge.tau = self.tau_matrix[edge[0], edge[1]]
        self.edges.append(new_edge)
        X.add(edge[1])

def _build_kth_tree(self):
    """Build tree for level k."""
    neg_tau = -1.0 * abs(self.tau_matrix)
    edges = self.previous_tree.edges
    visited = {0}
    unvisited = set(range(self.n_nodes))
    while len(visited) != self.n_nodes:
        adj_set = set()
        for x in visited:
            for k in range(self.n_nodes):
                if k not in visited and k != x and self._check_constraint(edges[x], edges[k]):
                    adj_set.add((x, k))
        if len(adj_set) == 0:
            visited.add(list(unvisited)[0])
            continue
        pairs = sorted(adj_set, key=lambda e: neg_tau[e[0]][e[1]])[0]
        left_parent, right_parent = Edge.sort_edge([edges[pairs[0]], edges[pairs[1]]])
        new_edge = Edge.get_child_edge(len(visited) - 1, left_parent, right_parent)
        new_edge.tau = self.tau_matrix[pairs[0], pairs[1]]
        self.edges.append(new_edge)
        visited.add(pairs[1])
        unvisited.remove(pairs[1])

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

def check_fit(self):
    """Assert that the model is fit and the computed `theta` is valid.

        Raises:
            NotFittedError: if the model is  not fitted.
            ValueError: if the computed theta is invalid.

        """
    if not self.theta:
        raise NotFittedError('This model is not fitted.')
    self.check_theta()

def _compute_theta(self):
    """Compute theta, validate it and assign it to self."""
    self.theta = self.compute_theta()
    self.check_theta()

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

def select_copula(X):
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
    frank = Frank()
    frank.fit(X)
    if frank.tau <= 0:
        return frank
    copula_candidates = [frank]
    for copula_class in [Clayton, Gumbel]:
        try:
            copula = copula_class()
            copula.tau = frank.tau
            copula._compute_theta()
            copula_candidates.append(copula)
        except ValueError:
            pass
    left_tail, empirical_left_aut, right_tail, empirical_right_aut = _compute_empirical(X)
    candidate_left_auts, candidate_right_auts = _compute_candidates(copula_candidates, left_tail, right_tail)
    empirical_aut = np.concatenate((empirical_left_aut, empirical_right_aut))
    candidate_auts = [np.concatenate((left, right)) for left, right in zip(candidate_left_auts, candidate_right_auts)]
    diff_left = [np.sum((empirical_left_aut - left) ** 2) for left in candidate_left_auts]
    diff_right = [np.sum((empirical_right_aut - right) ** 2) for right in candidate_right_auts]
    diff_both = [np.sum((empirical_aut - candidate) ** 2) for candidate in candidate_auts]
    score_left = pd.Series(diff_left).rank(ascending=False)
    score_right = pd.Series(diff_right).rank(ascending=False)
    score_both = pd.Series(diff_both).rank(ascending=False)
    score = score_left + score_right + score_both
    selected_copula = np.argmax(score.to_numpy())
    return copula_candidates[selected_copula]

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

class BatchedSynthesizer(BaseSynthesizer):

    def __init__(self, batch_size, **kwargs):
        self._batch_size = batch_size
        super().__init__(**kwargs)

    def get_batch_size(self):
        return self._batch_size

    def set_batch_size(self, b: int):
        warnings.warn('Reset batch_size may caused unintentional behavior.')
        self._batch_size = b

def set_batch_size(self, b: int):
    warnings.warn('Reset batch_size may caused unintentional behavior.')
    self._batch_size = b

class MultiTableSynthesizerModel(SynthesizerModel):
    """MultiTableSynthesizerModel

    The base model of multi-table statistic models.
    """
    metadata_combiner: MetadataCombiner = None
    "\n    metadata_combiner is a sdgx builtin class, it stores all tables' metadata and relationships.\n\n    This parameter must be specified when initializing the multi-table class.\n    "
    tables_data_frame: Dict[str, Any] = defaultdict()
    "\n    tables_data_frame is a dict contains every table's csv data frame.\n    For a small amount of data, this scheme can be used.\n    "
    tables_data_loader: Dict[str, Any] = defaultdict()
    "\n    tables_data_loader is a dict contains every table's data loader.\n    "
    _parent_id: List = []
    "\n    _parent_id is used to store all parent table's parimary keys in list.\n    "
    _table_synthesizers: Dict[str, Any] = {}
    '\n    _table_synthesizers is a dict to store model for each table.\n    '
    parent_map: Dict = defaultdict()
    '\n    The mapping from all child tables to their parent table.\n    '
    child_map: Dict = defaultdict()
    '\n    The mapping from all parent tabels to their child table.\n    '

    def __init__(self, metadata_combiner: MetadataCombiner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata_combiner = metadata_combiner
        self._calculate_parent_and_child_map()
        self.check()

    def _calculate_parent_and_child_map(self):
        """Get the mapping from all parent tables to self._parent_map
        - key(str) is a child map;
        - value(str) is the parent map.
        """
        relationships = self.metadata_combiner.relationships
        for each_relationship in relationships:
            parent_table = each_relationship.parent_table
            child_table = each_relationship.child_table
            self.parent_map[child_table] = parent_table
            self.child_map[parent_table] = child_table

    def _get_foreign_keys(self, parent_table, child_table):
        """Get the foreign key list from a relationship"""
        relationships = self.metadata_combiner.relationships
        for each_relationship in relationships:
            if each_relationship.parent_table == parent_table and each_relationship.child_table == child_table:
                return each_relationship.foreign_keys
        return []

    def _get_all_foreign_keys(self, child_table):
        """Given a child table, return ALL foreign keys from metadata."""
        all_foreign_keys = []
        relationships = self.metadata_combiner.relationships
        for each_relationship in relationships:
            if each_relationship.child_table == child_table:
                all_foreign_keys.append(each_relationship.foreign_keys)
        return all_foreign_keys

    def _finalize(self):
        """Finalize the"""
        raise NotImplementedError

    def check(self, check_circular=True):
        """Excute necessary checks

        - check access type
        - check metadata_combiner
        - check relationship
        - check each metadata
        - validate circular relationships
        - validate child map_circular relationship
        - validate all tables connect relationship
        - validate column relationships foreign keys
        """
        self._check_access_type()
        if not isinstance(self.metadata_combiner, MetadataCombiner):
            raise SynthesizerInitError('Wrong Metadata Combiner found.')
        pass

    def fit(self, dataloader: Dict[str, DataLoader], raw_data: Dict[str, pd.DataFrame], *args, **kwargs):
        """
        Fit the model using the given metadata and dataloader.

        Args:
            dataloader (Dict[str, DataLoader]): The dataloader to use to fit the model.
            raw_data (Dict[str, pd.DataFrame]): The raw pd.DataFrame to use to fit the model.
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
        pass

    @classmethod
    def load(target_path: str | Path):
        pass
    pass

def _get_all_foreign_keys(self, child_table):
    """Given a child table, return ALL foreign keys from metadata."""
    all_foreign_keys = []
    relationships = self.metadata_combiner.relationships
    for each_relationship in relationships:
        if each_relationship.child_table == child_table:
            all_foreign_keys.append(each_relationship.foreign_keys)
    return all_foreign_keys

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

class GaussianMultivariate(Multivariate):
    """Class for a multivariate distribution that uses the Gaussian copula.

    Args:
        distribution (str or dict):
            Fully qualified name of the class to be used for modeling the marginal
            distributions or a dictionary mapping column names to the fully qualified
            distribution names.
    """
    correlation = None
    columns = None
    univariates = None

    @store_args
    def __init__(self, distribution=DEFAULT_DISTRIBUTION, random_state=None):
        self.random_state = validate_random_state(random_state)
        self.distribution = distribution

    def __repr__(self):
        """Produce printable representation of the object."""
        if self.distribution == DEFAULT_DISTRIBUTION:
            distribution = ''
        elif isinstance(self.distribution, type):
            distribution = f'distribution="{self.distribution.__name__}"'
        else:
            distribution = f'distribution="{self.distribution}"'
        return f'GaussianMultivariate({distribution})'

    def _transform_to_normal(self, X):
        if isinstance(X, pd.Series):
            X = X.to_frame().T
        elif not isinstance(X, pd.DataFrame):
            if len(X.shape) == 1:
                X = [X]
            X = pd.DataFrame(X, columns=self.columns)
        U = []
        for column_name, univariate in zip(self.columns, self.univariates):
            if column_name in X:
                column = X[column_name]
                U.append(univariate.cdf(column.to_numpy()).clip(EPSILON, 1 - EPSILON))
        return stats.norm.ppf(np.column_stack(U))

    def _get_correlation(self, X):
        """Compute correlation matrix with transformed data.

        Args:
            X (numpy.ndarray):
                Data for which the correlation needs to be computed.

        Returns:
            numpy.ndarray:
                computed correlation matrix.
        """
        result = self._transform_to_normal(X)
        correlation = pd.DataFrame(data=result).corr().to_numpy()
        correlation = np.nan_to_num(correlation, nan=0.0)
        if np.linalg.cond(correlation) > 1.0 / sys.float_info.epsilon:
            correlation = correlation + np.identity(correlation.shape[0]) * EPSILON
        return pd.DataFrame(correlation, index=self.columns, columns=self.columns)

    @check_valid_values
    def fit(self, X):
        """Compute the distribution for each variable and then its correlation matrix.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
        LOGGER.info('Fitting %s', self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        columns = []
        univariates = []
        for column_name, column in X.items():
            if isinstance(self.distribution, dict):
                distribution = self.distribution.get(column_name, DEFAULT_DISTRIBUTION)
            else:
                distribution = self.distribution
            LOGGER.debug('Fitting column %s to %s', column_name, distribution)
            univariate = get_instance(distribution)
            try:
                univariate.fit(column)
            except BaseException:
                warning_message = f'Unable to fit to a {distribution} distribution for column {column_name}. Using a Gaussian distribution instead.'
                warnings.warn(warning_message)
                univariate = GaussianUnivariate()
                univariate.fit(column)
            columns.append(column_name)
            univariates.append(univariate)
        self.columns = columns
        self.univariates = univariates
        LOGGER.debug('Computing correlation')
        self.correlation = self._get_correlation(X)
        self.fitted = True
        LOGGER.debug('GaussianMultivariate fitted successfully')

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
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.pdf(transformed, cov=self.correlation)

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
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.cdf(transformed, cov=self.correlation)

    def _get_conditional_distribution(self, conditions):
        """Compute the parameters of a conditional multivariate normal distribution.

        The parameters of the conditioned distribution are computed as specified here:
        https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Conditional_distributions

        Args:
            conditions (pandas.Series):
                Mapping of the column names and column values to condition on.
                The input values have already been transformed to their normal distribution.

        Returns:
            tuple:
                * means (numpy.array):
                    mean values to use for the conditioned multivariate normal.
                * covariance (numpy.array):
                    covariance matrix to use for the conditioned
                  multivariate normal.
                * columns (list):
                    names of the columns that will be sampled conditionally.
        """
        columns2 = conditions.index
        columns1 = self.correlation.columns.difference(columns2)
        sigma11 = self.correlation.loc[columns1, columns1].to_numpy()
        sigma12 = self.correlation.loc[columns1, columns2].to_numpy()
        sigma21 = self.correlation.loc[columns2, columns1].to_numpy()
        sigma22 = self.correlation.loc[columns2, columns2].to_numpy()
        mu1 = np.zeros(len(columns1))
        mu2 = np.zeros(len(columns2))
        sigma12sigma22inv = sigma12 @ np.linalg.inv(sigma22)
        mu_bar = mu1 + sigma12sigma22inv @ (conditions - mu2)
        sigma_bar = sigma11 - sigma12sigma22inv @ sigma21
        return (mu_bar, sigma_bar, columns1)

    def _get_normal_samples(self, num_rows, conditions):
        """Get random rows in the standard normal space.

        If no conditions are given, the values are sampled from a standard normal
        multivariate.

        If conditions are given, they are transformed to their equivalent standard
        normal values using their marginals and then the values are sampled from
        a standard normal multivariate conditioned on the given condition values.
        """
        if conditions is None:
            covariance = self.correlation
            columns = self.columns
            means = np.zeros(len(columns))
        else:
            conditions = pd.Series(conditions)
            normal_conditions = self._transform_to_normal(conditions)[0]
            normal_conditions = pd.Series(normal_conditions, index=conditions.index)
            means, covariance, columns = self._get_conditional_distribution(normal_conditions)
        samples = np.random.multivariate_normal(means, covariance, size=num_rows)
        return pd.DataFrame(samples, columns=columns)

    @random_state
    def sample(self, num_rows=1, conditions=None):
        """Sample values from this model.

        Argument:
            num_rows (int):
                Number of rows to sample.
            conditions (dict or pd.Series):
                Mapping of the column names and column values to condition on.

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, *) with values randomly
                sampled from this model distribution. If conditions have been
                given, the output array also contains the corresponding columns
                populated with the given values.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        samples = self._get_normal_samples(num_rows, conditions)
        output = {}
        for column_name, univariate in zip(self.columns, self.univariates):
            if conditions and column_name in conditions:
                output[column_name] = np.full(num_rows, conditions[column_name])
            else:
                cdf = stats.norm.cdf(samples[column_name])
                output[column_name] = univariate.percent_point(cdf)
        return pd.DataFrame(data=output)

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
        self.check_fit()
        univariates = [univariate.to_dict() for univariate in self.univariates]
        return {'correlation': self.correlation.to_numpy().tolist(), 'univariates': univariates, 'columns': self.columns, 'type': get_qualified_name(self)}

    @classmethod
    def from_dict(cls, copula_dict):
        instance = cls()
        instance.univariates = []
        columns = copula_dict['columns']
        instance.columns = columns
        for parameters in copula_dict['univariates']:
            instance.univariates.append(Univariate.from_dict(parameters))
        correlation = copula_dict['correlation']
        instance.correlation = pd.DataFrame(correlation, index=columns, columns=columns)
        instance.fitted = True
        return instance

@check_valid_values
def fit(self, X):
    """Compute the distribution for each variable and then its correlation matrix.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
    LOGGER.info('Fitting %s', self)
    if not isinstance(X, pd.DataFrame):
        X = pd.DataFrame(X)
    columns = []
    univariates = []
    for column_name, column in X.items():
        if isinstance(self.distribution, dict):
            distribution = self.distribution.get(column_name, DEFAULT_DISTRIBUTION)
        else:
            distribution = self.distribution
        LOGGER.debug('Fitting column %s to %s', column_name, distribution)
        univariate = get_instance(distribution)
        try:
            univariate.fit(column)
        except BaseException:
            warning_message = f'Unable to fit to a {distribution} distribution for column {column_name}. Using a Gaussian distribution instead.'
            warnings.warn(warning_message)
            univariate = GaussianUnivariate()
            univariate.fit(column)
        columns.append(column_name)
        univariates.append(univariate)
    self.columns = columns
    self.univariates = univariates
    LOGGER.debug('Computing correlation')
    self.correlation = self._get_correlation(X)
    self.fitted = True
    LOGGER.debug('GaussianMultivariate fitted successfully')

@classmethod
def from_dict(cls, copula_dict):
    instance = cls()
    instance.univariates = []
    columns = copula_dict['columns']
    instance.columns = columns
    for parameters in copula_dict['univariates']:
        instance.univariates.append(Univariate.from_dict(parameters))
    correlation = copula_dict['correlation']
    instance.correlation = pd.DataFrame(correlation, index=columns, columns=columns)
    instance.fitted = True
    return instance

def generator():
    cache_dir = tmp_path / 'ndarrycache'
    for save in [True, False]:
        loader = NDArrayLoader(cache_root=cache_dir, save_to_file=save)
        for ndarray in ndarray_list:
            loader.store(ndarray)
        yield loader
        loader.cleanup()

@pytest.mark.parametrize('return_val', [0, '123', [1, 2, 3], {'a': 1, 'b': 2}])
def test_normal_message(return_val):
    NormalMessage.from_return_val(return_val)._dump_json == json.dumps({'code': 0, 'msg': 'Success', 'payload': return_val if isinstance(return_val, dict) else {'return_val': return_val}})

def test_base_multi_table_synthesizer(demo_base_multi_table_synthesizer):
    KeyTuple = namedtuple('KeyTuple', ['parent', 'child'])
    assert demo_base_multi_table_synthesizer.parent_map == defaultdict(None, {'train': 'store'})
    assert demo_base_multi_table_synthesizer.child_map == defaultdict(None, {'store': 'train'})
    assert demo_base_multi_table_synthesizer._get_all_foreign_keys('train')[0][0] == KeyTuple(parent='Store', child='Store')

