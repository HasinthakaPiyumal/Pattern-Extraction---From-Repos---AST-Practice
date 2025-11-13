# Cluster 2

def test_registed_exporter(manager: DataExporterManager):
    assert manager._normalize_name('MyOwnExporter') in manager.registed_exporters

def test_registed_model(manager: ModelManager):
    assert manager._normalize_name('DummyModel') in manager.registed_models

def test_registed_data_connector(manager: DataConnectorManager):
    assert manager._normalize_name('DummyDataConnector') in manager.registed_data_connectors

def test_registed_cacher(manager: CacherManager):
    assert manager._normalize_name('DummyCache') in manager.registed_cachers

def test_registed_cacher(manager: InspectorManager):
    assert manager._normalize_name('DummyInspector') in manager.registed_inspectors

def test_registed_data_processor(manager: DataProcessorManager):
    assert manager._normalize_name('DummyDataProcessor') in manager.registed_data_processors

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

@pytest.mark.parametrize('exception_caller', [unknown_exception, sdgx_exception])
def test_exception_message(exception_caller):
    try:
        exception_caller()
    except Exception as e:
        msg = ExceptionMessage.from_exception(e)
        assert msg._dump_json()
        assert msg.code != 0
        assert msg.payload
        assert 'details' in msg.payload

@pytest.mark.parametrize('supported_data_processor', [])
def test_manager(supported_data_processor, manager: DataProcessorManager):
    assert manager._normalize_name(supported_data_processor) in manager.registed_data_processors

@pytest.mark.parametrize('supported_model', ['ctgan'])
def test_manager(supported_model, manager: ModelManager):
    assert manager._normalize_name(supported_model) in manager.registed_models
    manager.init_model(supported_model, epochs=1)

@pytest.mark.parametrize('basic_inspector', ['DiscreteInspector', 'NumericInspector', 'IDInspector', 'BoolInspector', 'DatetimeInspector'])
def test_manager(basic_inspector, manager: InspectorManager):
    assert manager._normalize_name(basic_inspector) in manager.registed_inspectors

@pytest.mark.parametrize('supportd_cacher', ['NoCache', 'DiskCache'])
def test_manager(supportd_cacher, manager: CacherManager):
    assert manager._normalize_name(supportd_cacher) in manager.registed_cachers

@pytest.mark.parametrize('supported_data_connector', ['CsvConnector'])
def test_manager(supported_data_connector, manager: DataConnectorManager):
    assert manager._normalize_name(supported_data_connector) in manager.registed_data_connectors

@pytest.mark.parametrize('supportd_exporter', ['CsvExporter'])
def test_manager(supportd_exporter, manager: DataExporterManager):
    assert manager._normalize_name(supportd_exporter) in manager.registed_exporters

