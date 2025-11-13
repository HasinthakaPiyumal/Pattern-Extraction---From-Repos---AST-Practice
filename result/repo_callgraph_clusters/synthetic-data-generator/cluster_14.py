# Cluster 14

class Singleton(type):
    """
    metaclass for singleton, thread-safe.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def __call__(cls, *args, **kwargs):
    if cls not in cls._instances:
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    return cls._instances[cls]

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

def __init__(self):
    super().__init__()
    self.fixed_combinations: dict[str, set[str]] = {}
    self.simplified_fixed_combinations: dict[str, set[str]] = {}
    self.column_mappings: dict[(str, str), dict[str, str]] = {}
    self.is_been_specified = False

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._int_rate = 0.9
    self.df_length = 0

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fixed_combinations: dict[str, set[str]] = {}
    '\n        A dictionary mapping column names to sets of column names that have fixed relationships with them.\n        '
    self._inspect_level: int = 70
    '\n        The inspection level for this inspector, set to 70. This attribute indicates the priority or depth of inspection that this inspector performs relative to other inspectors.\n        '

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.bool_columns: set[str] = set()

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.discrete_columns: set[str] = set()

class Inspector:
    """
    Base Inspector class

    Inspector is used to inspect data and generate metadata automatically.

    Parameters:
        ready (bool): Ready to inspect, maybe all fields are fitted, or indicate if there is more data, inspector will be more precise.
    """
    pii = False
    '\n    PII refers if a column contains private or sensitive information.\n    '
    _inspect_level: int = 10
    "\n    Private variable used to store property inspect_level's value.\n    "
    ready: bool = False
    '\n    Indicates whether the inspector has completed its inference.\n\n    When completed, ready == True.\n    '

    @property
    def inspect_level(self):
        """
        Inspected level is a concept newly introduced in version 0.1.6. Since a single column in the table may be marked by different inspectors at the same time (for example: the email column may be recognized as email, but it may also be recognized as the id column, and it may also be recognized by different inspectors at the same time identified as a discrete column, which will cause confusion in subsequent processing), the inspect_leve is used when determining the specific type of a column.

        We will preset different inspector levels for different inspectors, usually more specific inspectors will get higher levels, and general inspectors (like discrete) will have inspect_level.

        The value of the variable inspect_level is limited to 1-100. In baseclass and bool, discrete and numeric types, the inspect_level is set to 10. For datetime and id types, the inspect_level is set to 20.

        Current inspect_level value will make it easier for developers to insert a custom inspector from the middle.
        """
        return self._inspect_level

    @inspect_level.setter
    def inspect_level(self, value: int):
        if value > 0 and value <= 100:
            self._inspect_level = value
        else:
            raise InspectorInitError('The inspect_level should be set in [1, 100].')

    def __init__(self, inspect_level=None, *args, **kwargs):
        self.ready: bool = False
        if inspect_level:
            self.inspect_level = inspect_level

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        return

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""

@inspect_level.setter
def inspect_level(self, value: int):
    if value > 0 and value <= 100:
        self._inspect_level = value
    else:
        raise InspectorInitError('The inspect_level should be set in [1, 100].')

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.maybe_related_columns: dict[str, dict[str, pd.Series]] = {}

class EmptyInspector(Inspector):
    """
    The EmptyInspector class is designed to identify columns in a DataFrame that have a high rate of missing values.

    Columns taged empty will be removed during the training process and reinserted into their original positions after the model sampling process is complete.

    Attributes:
        empty_rate_threshold (float): The threshold for the rate of missing values above which a column is considered empty, default = 0.9.
        empty_columns (set[str]): A set of column names that have missing values above the threshold.

    Methods:
        __init__(self, *args, **kwargs): Initializes the EmptyInspector instance, optionally setting the empty_rate_threshold.
        fit(self, raw_data: pd.DataFrame, *args, **kwargs): Fits the inspector to the raw data, identifying columns with missing values above the threshold.
        inspect(self, *args, **kwargs) -> dict[str, Any]: Returns a dictionary containing the list of columns identified as empty.
    """
    empty_rate_threshold = 0.9
    '\n    float: The threshold for the rate of missing values above which a column is considered empty.\n    Default is 0.9, meaning if a column has more than 90% of its values missing, it will be considered empty.\n    '
    empty_columns: set[str] = set()
    '\n    set[str]: A set of column names that have missing values above the empty_rate_threshold.\n    These columns are identified as empty and will be handled accordingly during the data processing.\n    '
    _inspect_level = 90
    '\n    int: The inspection level for the EmptyInspector, set to a quite high value (90) to prioritize the identification and handling of empty columns.\n    This high value is chosen because empty columns contain no information and should not be considered for any other type of inspection or processing.\n    They are typically removed during model training as they cannot be understood by many models and may cause errors.\n    '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'empty_rate_threshold' in kwargs:
            self.empty_rate_threshold = kwargs['empty_rate_threshold']

    def fit(self, raw_data: pd.DataFrame, *args, **kwargs):
        """Fit the inspector.

        Gets the list of empty columns from the raw data.

        Args:
            raw_data (pd.DataFrame): Raw data
        """
        empty_rate = raw_data.isnull().mean()
        self.empty_columns = set(empty_rate[empty_rate >= self.empty_rate_threshold].index)
        self.ready = True

    def inspect(self, *args, **kwargs) -> dict[str, Any]:
        """Inspect raw data and generate metadata."""
        return {'empty_columns': list(self.empty_columns)}

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if 'empty_rate_threshold' in kwargs:
        self.empty_rate_threshold = kwargs['empty_rate_threshold']

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

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.ID_columns: set[str] = set()

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

def __init__(self, user_formats: list[str]=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.datetime_columns: set[str] = set()
    self.user_defined_formats = user_formats if user_formats else []
    self.column_formats: dict[str, str] = {}

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

class SinTabMISim(SingleTableMetric):
    """MISim : Mutual Information Similarity

    This class is used to calculate the Mutual Information Similarity between the target columns of real data and synthetic data.

    Currently, we support discrete and continuous(need to be discretized) columns as inputs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.lower_bound = 0
        self.upper_bound = 1
        self.metric_name = 'mutual_information_similarity'
        self.numerical_bins = 50

    @classmethod
    def calculate(real_data: pd.DataFrame, synthetic_data: pd.DataFrame, metadata) -> pd.DataFrame:
        """
        Calculate the Mutual Information Similarity between a real column and a synthetic column.
        Args:
            real_data (pd.DataFrame): The real data.
            synthetic_data (pd.DataFrame): The synthetic data.
            metadata(dict): The metadata that describes the data type of each column
        Returns:
            MI_similarity (float): The metric value.
        """
        columns = synthetic_data.columns
        n = len(columns)
        mi_sim_instance = MISim()
        nMI_sim = np.zeros((n, n))
        for i in range(len(columns)):
            for j in range(len(columns)):
                syn_data = pd.concat([synthetic_data[columns[i]], synthetic_data[columns[j]]], axis=1)
                real_data = pd.concat([real_data[columns[i]], real_data[columns[j]]], axis=1)
                nMI_sim[i][j] = mi_sim_instance.calculate(real_data, syn_data, metadata)
        MI_sim = np.sum(nMI_sim) / n / n
        MISim.check_output(MI_sim)
        return MI_sim

    @classmethod
    def check_output(cls, raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the Mutual Information Similarity.
        """
        instance = cls()
        if raw_metric_value < instance.lower_bound or raw_metric_value > instance.upper_bound:
            raise ValueError

def __init__(self) -> None:
    super().__init__()
    self.lower_bound = 0
    self.upper_bound = 1
    self.metric_name = 'mutual_information_similarity'
    self.numerical_bins = 50

class JSD(ColumnMetric):
    """JSD : Jensen Shannon Divergence

    This class is used to calculate the Jensen Shannon divergence value betweenthe target columns of real data and synthetic data.

    Currently, we support discrete and continuous columns as inputs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.lower_bound = 0
        self.upper_bound = 1
        self.metric_name = 'jensen_shannon_divergence'

    @classmethod
    def calculate(cls, real_data: pd.DataFrame, synthetic_data: pd.DataFrame, cols: list[str] | None, discrete: bool=True) -> pd.DataFrame:
        """
        Calculate the JSD value between a real column and a synthetic column.

        Args:
            real_data (pd.DataFrame): The real data.

            synthetic_data (pd.DataFrame): The synthetic data.

            cols (list[str]): The target column to calculat JSD metric.

            discrete (bool): Whether this column is a discrete column.

        Returns:
            JSD_val (float): The meteic value.
        """
        if discrete:
            JSD.check_input(real_data, synthetic_data)
            joint_pd_real = real_data.groupby(cols, dropna=False).size() / len(real_data)
            joint_pd_syn = synthetic_data.groupby(cols, dropna=False).size() / len(synthetic_data)
            joint_pdf_values_real, joint_pdf_values_syn = joint_pd_real.align(joint_pd_syn, fill_value=0)
        else:
            real_data_T = real_data[cols].values.T
            syn_data_T = synthetic_data[cols].values.T
            kde_joint_real = gaussian_kde(real_data_T)
            kde_joint_syn = gaussian_kde(syn_data_T)
            variables_range = [np.linspace(min(col), max(col), 100) for col in real_data_T]
            grid_points = np.meshgrid(*variables_range)
            grid_points_flat = np.vstack([item.ravel() for item in grid_points])
            joint_pdf_values_real = kde_joint_real(grid_points_flat).reshape(grid_points[0].shape).ravel()
            joint_pdf_values_syn = kde_joint_syn(grid_points_flat).reshape(grid_points[0].shape).ravel()
        JSD_val = JSD.jensen_shannon_divergence(joint_pdf_values_real, joint_pdf_values_syn)
        JSD.check_output(JSD_val)
        return JSD_val

    @classmethod
    def check_output(cls, raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the JSD metric.
        """
        instance = cls()
        if raw_metric_value < instance.lower_bound or raw_metric_value > instance.upper_bound:
            raise ValueError

    @classmethod
    def jensen_shannon_divergence(cls, p: float, q: float):
        """Calculate the jensen_shannon_divergence of p and q.

        Args:
            p (float): the input parameter p.

            q (float): the input parameter q.
        """
        m = 0.5 * (p + q)
        kl_p = entropy(p, m, base=2)
        kl_q = entropy(q, m, base=2)
        js_divergence = 0.5 * (kl_p + kl_q)
        return js_divergence

def __init__(self) -> None:
    super().__init__()
    self.lower_bound = 0
    self.upper_bound = 1
    self.metric_name = 'jensen_shannon_divergence'

class MISim(PairMetric):
    """MISim : Mutual Information Similarity

    This class is used to calculate the Mutual Information Similarity between the target columns of real data and synthetic data.

    Currently, we support discrete and continuous(need to be discretized) columns as inputs.
    """

    def __init__(instance) -> None:
        super().__init__()
        instance.lower_bound = 0
        instance.upper_bound = 1
        instance.metric_name = 'mutual_information_similarity'
        instance.numerical_bins = 50

    @classmethod
    def calculate(cls, src_col: pd.Series, tar_col: pd.Series, metadata: dict) -> float:
        """
        Calculate the MI similarity for the source data colum and the target data column.
        Args:
            src_data(pd.Series ): the source data column.
            tar_data(pd.Series): the target data column .
            metadata(dict): The metadata that describes the data type of each columns
        Returns:
            MI_similarity (float): The metric value.
        """
        instance = cls()
        col_name = src_col.name
        data_type = metadata[col_name]
        if data_type == 'numerical':
            x = np.array(src_col.array)
            src_col = pd.cut(x, instance.numerical_bins, labels=range(instance.numerical_bins))
            x = np.array(tar_col.array)
            tar_col = pd.cut(x, instance.numerical_bins, labels=range(instance.numerical_bins))
            src_col = src_col.to_numpy()
            tar_col = tar_col.to_numpy()
        elif data_type == 'category':
            le = LabelEncoder()
            src_list = list(set(src_col.array))
            tar_list = list(set(tar_col.array))
            fit_list = tar_list + src_list
            le.fit(fit_list)
            src_col = le.transform(np.array(src_col.array))
            tar_col = le.transform(np.array(tar_col.array))
        elif data_type == 'datetime':
            src_col = src_col.apply(time2int)
            tar_col = tar_col.apply(time2int)
            src_col = pd.cut(src_col, bins=instance.numerical_bins, labels=range(instance.numerical_bins))
            tar_col = pd.cut(tar_col, bins=instance.numerical_bins, labels=range(instance.numerical_bins))
            src_col = src_col.to_numpy()
            tar_col = tar_col.to_numpy()
        MI_sim = normalized_mutual_info_score(src_col, tar_col)
        return MI_sim

    @classmethod
    def check_output(cls, raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the MI similarity.
        """
        pass

def __init__(instance) -> None:
    super().__init__()
    instance.lower_bound = 0
    instance.upper_bound = 1
    instance.metric_name = 'mutual_information_similarity'
    instance.numerical_bins = 50

class MISim(MultiTableMetric):
    """MISim : Mutual Information Similarity

    This class is used to calculate the Mutual Information Similarity between the target columns of real data and synthetic data.

    Currently, we support discrete and continuous(need to be discretized) columns as inputs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.lower_bound = 0
        self.upper_bound = 1
        self.metric_name = 'mutual_information_similarity'
        self.numerical_bins = 50

    @classmethod
    def calculate(real_data: pd.DataFrame, synthetic_data: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        Calculate the Mutual Information Similarity between a real column and a synthetic column.
        Args:
            real_data (pd.DataFrame): The real data.
            synthetic_data (pd.DataFrame): The synthetic data.
            metadata(dict): The metadata that describes the data type of each column

        Returns:
            MI_similarity (float): The metric value.
        """
        columns = synthetic_data.columns
        n = len(columns)
        mi_sim_instance = MISim()
        nMI_sim = np.zeros((n, n))
        for i in range(len(columns)):
            for j in range(len(columns)):
                syn_data = pd.concat([synthetic_data[columns[i]], synthetic_data[columns[j]]], axis=1)
                real_data = pd.concat([real_data[columns[i]], real_data[columns[j]]], axis=1)
                nMI_sim[i][j] = mi_sim_instance.calculate(real_data, syn_data, metadata)
        MI_sim = np.sum(nMI_sim) / n / n
        MISim.check_output(MI_sim)
        return MI_sim

    @classmethod
    def check_output(cls, raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the Mutual Information Similarity.
        """
        instance = cls()
        if raw_metric_value < instance.lower_bound or raw_metric_value > instance.upper_bound:
            raise ValueError

def __init__(self) -> None:
    super().__init__()
    self.lower_bound = 0
    self.upper_bound = 1
    self.metric_name = 'mutual_information_similarity'
    self.numerical_bins = 50

class Discriminator(Module):
    """Discriminator for the CTGAN."""

    def __init__(self, input_dim, discriminator_dim, pac=10):
        super(Discriminator, self).__init__()
        dim = input_dim * pac
        self.pac = pac
        self.pacdim = dim
        seq = []
        for item in list(discriminator_dim):
            seq += [Linear(dim, item), LeakyReLU(0.2), Dropout(0.5)]
            dim = item
        seq += [Linear(dim, 1)]
        self.seq = Sequential(*seq)

    def calc_gradient_penalty(self, real_data, fake_data, device='cpu', pac=10, lambda_=10):
        """Compute the gradient penalty."""
        alpha = torch.rand(real_data.size(0) // pac, 1, 1, device=device)
        alpha = alpha.repeat(1, pac, real_data.size(1))
        alpha = alpha.view(-1, real_data.size(1))
        interpolates = alpha * real_data + (1 - alpha) * fake_data
        disc_interpolates = self(interpolates)
        gradients = torch.autograd.grad(outputs=disc_interpolates, inputs=interpolates, grad_outputs=torch.ones(disc_interpolates.size(), device=device), create_graph=True, retain_graph=True, only_inputs=True)[0]
        gradients_view = gradients.view(-1, pac * real_data.size(1)).norm(2, dim=1) - 1
        gradient_penalty = (gradients_view ** 2).mean() * lambda_
        return gradient_penalty

    def forward(self, input_):
        """Apply the Discriminator to the `input_`."""
        assert input_.size()[0] % self.pac == 0
        return self.seq(input_.view(-1, self.pacdim))

def __init__(self, input_dim, discriminator_dim, pac=10):
    super(Discriminator, self).__init__()
    dim = input_dim * pac
    self.pac = pac
    self.pacdim = dim
    seq = []
    for item in list(discriminator_dim):
        seq += [Linear(dim, item), LeakyReLU(0.2), Dropout(0.5)]
        dim = item
    seq += [Linear(dim, 1)]
    self.seq = Sequential(*seq)

class Residual(Module):
    """Residual layer for the CTGAN."""

    def __init__(self, i, o):
        super(Residual, self).__init__()
        self.fc = Linear(i, o)
        self.bn = BatchNorm1d(o)
        self.relu = ReLU()

    def forward(self, input_):
        """Apply the Residual layer to the `input_`."""
        out = self.fc(input_)
        out = self.bn(out)
        out = self.relu(out)
        return torch.cat([out, input_], dim=1)

def __init__(self, i, o):
    super(Residual, self).__init__()
    self.fc = Linear(i, o)
    self.bn = BatchNorm1d(o)
    self.relu = ReLU()

class Generator(Module):
    """Generator for the CTGAN."""

    def __init__(self, embedding_dim, generator_dim, data_dim):
        super(Generator, self).__init__()
        dim = embedding_dim
        seq = []
        for item in list(generator_dim):
            seq += [Residual(dim, item)]
            dim += item
        seq.append(Linear(dim, data_dim))
        self.seq = Sequential(*seq)

    def forward(self, input_):
        """Apply the Generator to the `input_`."""
        data = self.seq(input_)
        return data

def __init__(self, embedding_dim, generator_dim, data_dim):
    super(Generator, self).__init__()
    dim = embedding_dim
    seq = []
    for item in list(generator_dim):
        seq += [Residual(dim, item)]
        dim += item
    seq.append(Linear(dim, data_dim))
    self.seq = Sequential(*seq)

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

def __init__(self, *args, **kwargs) -> None:
    """
        Initializes the class instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
    super().__init__(*args, **kwargs)
    self._get_openai_setting_from_env()

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

@property
def value(self):
    return str(super().value)

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

def __init__(self, order_by=None):
    super().__init__(False, order_by)
    self._round_digit = None

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

def __init__(self, order, add_noise=False):
    self.order = pd.Series(order).fillna(np.nan)
    super().__init__(add_noise=add_noise)

class NormalizedFrequencyEncoder(FrequencyEncoder):
    """Same to FrequencyEncoder except the transform result is in [-1, 1] instead of [0, 1]"""

    def _fit(self, data):
        """Fit the transformer to the data.

        Compute the intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        self.dtype = data.dtype
        self.intervals, self.means, self.starts = self._get_intervals(data, normalized=True)

    def _reverse_transform(self, data):
        return super()._reverse_transform(data, True)

def _reverse_transform(self, data):
    return super()._reverse_transform(data, True)

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

def __init__(self, model_missing_values=False, learn_rounding_scheme=False, enforce_min_max_values=False, distribution='truncated_gaussian'):
    super().__init__(missing_value_replacement='mean', model_missing_values=model_missing_values, learn_rounding_scheme=learn_rounding_scheme, enforce_min_max_values=enforce_min_max_values)
    self.distribution = distribution
    self._distributions = self._get_distributions()
    if isinstance(distribution, str):
        distribution = self._distributions[distribution]
    self._distribution = distribution

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

def __init__(self, model_missing_values=False, learn_rounding_scheme=False, enforce_min_max_values=False, max_clusters=10, weight_threshold=0.005):
    super().__init__(missing_value_replacement='mean', model_missing_values=model_missing_values, learn_rounding_scheme=learn_rounding_scheme, enforce_min_max_values=enforce_min_max_values)
    self.max_clusters = max_clusters
    self.weight_threshold = weight_threshold

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

class OptimizedTimestampEncoder(UnixTimestampEncoder):
    """Optimized transformer for datetime data.

    This transformer replaces datetime values with an integer timestamp transformed to float.
    It optimizes the output values by finding the smallest time unit that is not zero on
    the training datetimes and dividing the generated numerical values by the value of the next
    smallest time unit. This, apart from reducing the orders of magnitude of the transformed
    values, ensures that reverted values always are zero on the lower time units.

    Null values are replaced using a ``NullTransformer``.

    This class behaves exactly as the ``UnixTimestampEncoder`` except with the optimization.

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
    divider = None

    def __init__(self, missing_value_replacement=None, model_missing_values=False, datetime_format=None):
        super().__init__(missing_value_replacement=missing_value_replacement, model_missing_values=model_missing_values, datetime_format=datetime_format)

    def _find_divider(self, transformed):
        self.divider = 1
        multipliers = [10] * 9 + [60, 60, 24]
        for multiplier in multipliers:
            candidate = self.divider * multiplier
            if (transformed % candidate).any():
                break
            self.divider = candidate

    def _transform_helper(self, data):
        """Transform datetime values to integer."""
        data = super()._transform_helper(data)
        self._find_divider(data)
        return data // self.divider

    def _reverse_transform_helper(self, data):
        """Transform integer values back into datetimes."""
        data = super()._reverse_transform_helper(data)
        return data * self.divider

def __init__(self, missing_value_replacement=None, model_missing_values=False, datetime_format=None):
    super().__init__(missing_value_replacement=missing_value_replacement, model_missing_values=model_missing_values, datetime_format=datetime_format)

def _transform_helper(self, data):
    """Transform datetime values to integer."""
    data = super()._transform_helper(data)
    self._find_divider(data)
    return data // self.divider

def _reverse_transform_helper(self, data):
    """Transform integer values back into datetimes."""
    data = super()._reverse_transform_helper(data)
    return data * self.divider

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

def __init__(self, provider_name=None, function_name=None, function_kwargs=None, locales=None):
    super().__init__(provider_name=provider_name, function_name=function_name, function_kwargs=function_kwargs, locales=locales)
    self._mapping_dict = {}
    self._reverse_mapping_dict = {}

@contextlib.contextmanager
def set_random_state(random_state, set_model_random_state):
    """Context manager for managing the random state.

    Args:
        random_state (int or np.random.RandomState):
            The random seed or RandomState.
        set_model_random_state (function):
            Function to set the random state on the model.
    """
    original_state = np.random.get_state()
    np.random.set_state(random_state.get_state())
    try:
        yield
    finally:
        current_random_state = np.random.RandomState()
        current_random_state.set_state(np.random.get_state())
        set_model_random_state(current_random_state)
        np.random.set_state(original_state)

def validate_random_state(random_state):
    """Validate random state argument.

    Args:
        random_state (int, numpy.random.RandomState, tuple, or None):
            Seed or RandomState for the random generator.

    Output:
        numpy.random.RandomState
    """
    if random_state is None:
        return None
    if isinstance(random_state, int):
        return np.random.RandomState(seed=random_state)
    elif isinstance(random_state, np.random.RandomState):
        return random_state
    else:
        raise TypeError(f'`random_state` {random_state} expected to be an int or `np.random.RandomState` object.')

@contextlib.contextmanager
def set_random_states(random_state, set_model_random_state):
    """Context manager for managing the random state.

    Args:
        random_state (int or tuple):
            The random seed or a tuple of (numpy.random.RandomState, torch.Generator).
        set_model_random_state (function):
            Function to set the random state on the model.
    """
    original_np_state = np.random.get_state()
    original_torch_state = torch.get_rng_state()
    random_np_state, random_torch_state = random_state
    np.random.set_state(random_np_state.get_state())
    torch.set_rng_state(random_torch_state.get_state())
    try:
        yield
    finally:
        current_np_state = np.random.RandomState()
        current_np_state.set_state(np.random.get_state())
        current_torch_state = torch.Generator()
        current_torch_state.set_state(torch.get_rng_state())
        set_model_random_state((current_np_state, current_torch_state))
        np.random.set_state(original_np_state)
        torch.set_rng_state(original_torch_state)

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

class BatchedSynthesizer(BaseSynthesizer):

    def __init__(self, batch_size, **kwargs):
        self._batch_size = batch_size
        super().__init__(**kwargs)

    def get_batch_size(self):
        return self._batch_size

    def set_batch_size(self, b: int):
        warnings.warn('Reset batch_size may caused unintentional behavior.')
        self._batch_size = b

def __init__(self, batch_size, **kwargs):
    self._batch_size = batch_size
    super().__init__(**kwargs)

class Encoder(Module):
    """Encoder for the TVAE.

    Args:
        data_dim (int):
            Dimensions of the data.
        compress_dims (tuple or list of ints):
            Size of each hidden layer.
        embedding_dim (int):
            Size of the output vector.
    """

    def __init__(self, data_dim, compress_dims, embedding_dim):
        super(Encoder, self).__init__()
        dim = data_dim
        seq = []
        for item in list(compress_dims):
            seq += [Linear(dim, item), ReLU()]
            dim = item
        self.seq = Sequential(*seq)
        self.fc1 = Linear(dim, embedding_dim)
        self.fc2 = Linear(dim, embedding_dim)

    def forward(self, input_):
        """Encode the passed `input_`."""
        feature = self.seq(input_)
        mu = self.fc1(feature)
        logvar = self.fc2(feature)
        std = torch.exp(0.5 * logvar)
        return (mu, std, logvar)

def __init__(self, data_dim, compress_dims, embedding_dim):
    super(Encoder, self).__init__()
    dim = data_dim
    seq = []
    for item in list(compress_dims):
        seq += [Linear(dim, item), ReLU()]
        dim = item
    self.seq = Sequential(*seq)
    self.fc1 = Linear(dim, embedding_dim)
    self.fc2 = Linear(dim, embedding_dim)

class Decoder(Module):
    """Decoder for the TVAE.

    Args:
        embedding_dim (int):
            Size of the input vector.
        decompress_dims (tuple or list of ints):
            Size of each hidden layer.
        data_dim (int):
            Dimensions of the data.
    """

    def __init__(self, embedding_dim, decompress_dims, data_dim):
        super(Decoder, self).__init__()
        dim = embedding_dim
        seq = []
        for item in list(decompress_dims):
            seq += [Linear(dim, item), ReLU()]
            dim = item
        seq.append(Linear(dim, data_dim))
        self.seq = Sequential(*seq)
        self.sigma = Parameter(torch.ones(data_dim) * 0.1)

    def forward(self, input_):
        """Decode the passed `input_`."""
        return (self.seq(input_), self.sigma)

def __init__(self, embedding_dim, decompress_dims, data_dim):
    super(Decoder, self).__init__()
    dim = embedding_dim
    seq = []
    for item in list(decompress_dims):
        seq += [Linear(dim, item), ReLU()]
        dim = item
    seq.append(Linear(dim, data_dim))
    self.seq = Sequential(*seq)
    self.sigma = Parameter(torch.ones(data_dim) * 0.1)

class TVAE(BatchedSynthesizer):
    """TVAE."""

    def __init__(self, embedding_dim=128, compress_dims=(128, 128), decompress_dims=(128, 128), l2scale=1e-05, batch_size=500, epochs=300, loss_factor=2, cuda=True):
        super().__init__(batch_size)
        self.embedding_dim = embedding_dim
        self.compress_dims = compress_dims
        self.decompress_dims = decompress_dims
        self.l2scale = l2scale
        self.loss_factor = loss_factor
        self.epochs = epochs
        if not cuda or not torch.cuda.is_available():
            device = 'cpu'
        elif isinstance(cuda, str):
            device = cuda
        else:
            device = 'cuda'
        self._device = torch.device(device)

    @random_state
    def fit(self, train_data, discrete_columns=()):
        """Fit the TVAE Synthesizer models to the training data.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        self.transformer = DataTransformer()
        self.transformer.fit(train_data, discrete_columns)
        train_data = self.transformer.transform(train_data)
        dataset = TensorDataset(torch.from_numpy(train_data.astype('float32')).to(self._device))
        loader = DataLoader(dataset, batch_size=self._batch_size, shuffle=True, drop_last=False)
        data_dim = self.transformer.output_dimensions
        encoder = Encoder(data_dim, self.compress_dims, self.embedding_dim).to(self._device)
        self.decoder = Decoder(self.embedding_dim, self.decompress_dims, data_dim).to(self._device)
        optimizerAE = Adam(list(encoder.parameters()) + list(self.decoder.parameters()), weight_decay=self.l2scale)
        for i in range(self.epochs):
            for id_, data in enumerate(loader):
                optimizerAE.zero_grad()
                real = data[0].to(self._device)
                mu, std, logvar = encoder(real)
                eps = torch.randn_like(std)
                emb = eps * std + mu
                rec, sigmas = self.decoder(emb)
                loss_1, loss_2 = _loss_function(rec, real, sigmas, mu, logvar, self.transformer.output_info_list, self.loss_factor)
                loss = loss_1 + loss_2
                loss.backward()
                optimizerAE.step()
                self.decoder.sigma.data.clamp_(0.01, 1.0)

    @random_state
    def sample(self, samples):
        """Sample data similar to the training data.

        Args:
            samples (int):
                Number of rows to sample.

        Returns:
            numpy.ndarray or pandas.DataFrame
        """
        self.decoder.eval()
        steps = samples // self._batch_size + 1
        data = []
        for _ in range(steps):
            mean = torch.zeros(self._batch_size, self.embedding_dim)
            std = mean + 1
            noise = torch.normal(mean=mean, std=std).to(self._device)
            fake, sigmas = self.decoder(noise)
            fake = torch.tanh(fake)
            data.append(fake.detach().cpu().numpy())
        data = np.concatenate(data, axis=0)
        data = data[:samples]
        return self.transformer.inverse_transform(data, sigmas.detach().cpu().numpy())

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU)."""
        self._device = device
        self.decoder.to(self._device)

def __init__(self, embedding_dim=128, compress_dims=(128, 128), decompress_dims=(128, 128), l2scale=1e-05, batch_size=500, epochs=300, loss_factor=2, cuda=True):
    super().__init__(batch_size)
    self.embedding_dim = embedding_dim
    self.compress_dims = compress_dims
    self.decompress_dims = decompress_dims
    self.l2scale = l2scale
    self.loss_factor = loss_factor
    self.epochs = epochs
    if not cuda or not torch.cuda.is_available():
        device = 'cpu'
    elif isinstance(cuda, str):
        device = cuda
    else:
        device = 'cuda'
    self._device = torch.device(device)

class Discriminator(Module):
    """Discriminator for the CTGAN."""

    def __init__(self, input_dim, discriminator_dim, pac=10):
        super(Discriminator, self).__init__()
        dim = input_dim * pac
        self.pac = pac
        self.pacdim = dim
        seq = []
        for item in list(discriminator_dim):
            seq += [Linear(dim, item), LeakyReLU(0.2), Dropout(0.5)]
            dim = item
        seq += [Linear(dim, 1)]
        self.seq = Sequential(*seq)

    def calc_gradient_penalty(self, real_data, fake_data, device='cpu', pac=10, lambda_=10):
        """Compute the gradient penalty."""
        alpha = torch.rand(real_data.size(0) // pac, 1, 1, device=device)
        alpha = alpha.repeat(1, pac, real_data.size(1))
        alpha = alpha.view(-1, real_data.size(1))
        interpolates = alpha * real_data + (1 - alpha) * fake_data
        disc_interpolates = self(interpolates)
        gradients = torch.autograd.grad(outputs=disc_interpolates, inputs=interpolates, grad_outputs=torch.ones(disc_interpolates.size(), device=device), create_graph=True, retain_graph=True, only_inputs=True)[0]
        gradients_view = gradients.view(-1, pac * real_data.size(1)).norm(2, dim=1) - 1
        gradient_penalty = (gradients_view ** 2).mean() * lambda_
        return gradient_penalty

    def forward(self, input_):
        """Apply the Discriminator to the `input_`."""
        assert input_.size()[0] % self.pac == 0
        return self.seq(input_.view(-1, self.pacdim))

def __init__(self, input_dim, discriminator_dim, pac=10):
    super(Discriminator, self).__init__()
    dim = input_dim * pac
    self.pac = pac
    self.pacdim = dim
    seq = []
    for item in list(discriminator_dim):
        seq += [Linear(dim, item), LeakyReLU(0.2), Dropout(0.5)]
        dim = item
    seq += [Linear(dim, 1)]
    self.seq = Sequential(*seq)

class Residual(Module):
    """Residual layer for the CTGAN."""

    def __init__(self, i, o):
        super(Residual, self).__init__()
        self.fc = Linear(i, o)
        self.bn = BatchNorm1d(o)
        self.relu = ReLU()

    def forward(self, input_):
        """Apply the Residual layer to the `input_`."""
        out = self.fc(input_)
        out = self.bn(out)
        out = self.relu(out)
        return torch.cat([out, input_], dim=1)

def __init__(self, i, o):
    super(Residual, self).__init__()
    self.fc = Linear(i, o)
    self.bn = BatchNorm1d(o)
    self.relu = ReLU()

class Generator(Module):
    """Generator for the CTGAN."""

    def __init__(self, embedding_dim, generator_dim, data_dim):
        super(Generator, self).__init__()
        dim = embedding_dim
        seq = []
        for item in list(generator_dim):
            seq += [Residual(dim, item)]
            dim += item
        seq.append(Linear(dim, data_dim))
        self.seq = Sequential(*seq)

    def forward(self, input_):
        """Apply the Generator to the `input_`."""
        data = self.seq(input_)
        return data

def __init__(self, embedding_dim, generator_dim, data_dim):
    super(Generator, self).__init__()
    dim = embedding_dim
    seq = []
    for item in list(generator_dim):
        seq += [Residual(dim, item)]
        dim += item
    seq.append(Linear(dim, data_dim))
    self.seq = Sequential(*seq)

class CTGAN(BatchedSynthesizer):
    """Conditional Table GAN Synthesizer.

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
        verbose (boolean):
            Whether to have print statements for progress results. Defaults to ``False``.
        epochs (int):
            Number of training epochs. Defaults to 300.
        pac (int):
            Number of samples to group together when applying the discriminator.
            Defaults to 10.
        cuda (bool):
            Whether to attempt to use cuda for GPU computation.
            If this is False or CUDA is not available, CPU will be used.
            Defaults to ``True``.
    """

    def __init__(self, embedding_dim=128, generator_dim=(256, 256), discriminator_dim=(256, 256), generator_lr=0.0002, generator_decay=1e-06, discriminator_lr=0.0002, discriminator_decay=1e-06, batch_size=500, discriminator_steps=1, log_frequency=True, verbose=False, epochs=300, pac=10, cuda=True):
        assert batch_size % 2 == 0
        super().__init__(batch_size)
        self._embedding_dim = embedding_dim
        self._generator_dim = generator_dim
        self._discriminator_dim = discriminator_dim
        self._generator_lr = generator_lr
        self._generator_decay = generator_decay
        self._discriminator_lr = discriminator_lr
        self._discriminator_decay = discriminator_decay
        self._discriminator_steps = discriminator_steps
        self._log_frequency = log_frequency
        self._verbose = verbose
        self._epochs = epochs
        self.pac = pac
        if not cuda or not torch.cuda.is_available():
            device = 'cpu'
        elif isinstance(cuda, str):
            device = cuda
        else:
            device = 'cuda'
        self._device = torch.device(device)
        self._transformer = None
        self._data_sampler = None
        self._generator = None

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

    def _validate_discrete_columns(self, train_data, discrete_columns):
        """Check whether ``discrete_columns`` exists in ``train_data``.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
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
        else:
            raise TypeError('``train_data`` should be either pd.DataFrame or np.array.')
        if invalid_columns:
            raise ValueError(f'Invalid columns found: {invalid_columns}')

    @random_state
    def fit(self, train_data, discrete_columns=(), epochs=None):
        """Fit the CTGAN Synthesizer models to the training data.

        Args:
            train_data (numpy.ndarray or pandas.DataFrame):
                Training Data. It must be a 2-dimensional numpy array or a pandas.DataFrame.
            discrete_columns (list-like):
                List of discrete columns to be used to generate the Conditional
                Vector. If ``train_data`` is a Numpy array, this list should
                contain the integer indices of the columns. Otherwise, if it is
                a ``pandas.DataFrame``, this list should contain the column names.
        """
        self._validate_discrete_columns(train_data, discrete_columns)
        if epochs is None:
            epochs = self._epochs
        else:
            warnings.warn('`epochs` argument in `fit` method has been deprecated and will be removed in a future version. Please pass `epochs` to the constructor instead', DeprecationWarning)
        self._transformer = DataTransformer()
        self._transformer.fit(train_data, discrete_columns)
        train_data = self._transformer.transform(train_data)
        self._data_sampler = DataSampler(train_data, self._transformer.output_info_list, self._log_frequency)
        data_dim = self._transformer.output_dimensions
        self._generator = Generator(self._embedding_dim + self._data_sampler.dim_cond_vec(), self._generator_dim, data_dim).to(self._device)
        discriminator = Discriminator(data_dim + self._data_sampler.dim_cond_vec(), self._discriminator_dim, pac=self.pac).to(self._device)
        optimizerG = optim.Adam(self._generator.parameters(), lr=self._generator_lr, betas=(0.5, 0.9), weight_decay=self._generator_decay)
        optimizerD = optim.Adam(discriminator.parameters(), lr=self._discriminator_lr, betas=(0.5, 0.9), weight_decay=self._discriminator_decay)
        mean = torch.zeros(self._batch_size, self._embedding_dim, device=self._device)
        std = mean + 1
        steps_per_epoch = max(len(train_data) // self._batch_size, 1)
        for i in range(epochs):
            for id_ in range(steps_per_epoch):
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
            if self._verbose:
                print(f'Epoch {i + 1}, Loss G: {loss_g.detach().cpu(): .4f},Loss D: {loss_d.detach().cpu(): .4f}', flush=True)

    @random_state
    def sample(self, n, condition_column=None, condition_value=None):
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
        steps = n // self._batch_size + 1
        data = []
        for i in range(steps):
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
        data = data[:n]
        return self._transformer.inverse_transform(data)

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU)."""
        self._device = device
        if self._generator is not None:
            self._generator.to(self._device)

def __init__(self, embedding_dim=128, generator_dim=(256, 256), discriminator_dim=(256, 256), generator_lr=0.0002, generator_decay=1e-06, discriminator_lr=0.0002, discriminator_decay=1e-06, batch_size=500, discriminator_steps=1, log_frequency=True, verbose=False, epochs=300, pac=10, cuda=True):
    assert batch_size % 2 == 0
    super().__init__(batch_size)
    self._embedding_dim = embedding_dim
    self._generator_dim = generator_dim
    self._discriminator_dim = discriminator_dim
    self._generator_lr = generator_lr
    self._generator_decay = generator_decay
    self._discriminator_lr = discriminator_lr
    self._discriminator_decay = discriminator_decay
    self._discriminator_steps = discriminator_steps
    self._log_frequency = log_frequency
    self._verbose = verbose
    self._epochs = epochs
    self.pac = pac
    if not cuda or not torch.cuda.is_available():
        device = 'cpu'
    elif isinstance(cuda, str):
        device = cuda
    else:
        device = 'cuda'
    self._device = torch.device(device)
    self._transformer = None
    self._data_sampler = None
    self._generator = None

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

def __init__(self, metadata_combiner: MetadataCombiner, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.metadata_combiner = metadata_combiner
    self._calculate_parent_and_child_map()
    self.check()

class StatisticSynthesizerModel(SynthesizerModel):
    random_states = None

    def __init__(self, transformer=None, sampler=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._generator = None
        self.model = None
        self.status = 'UNFINED'
        self.model_type = 'MODEL_TYPE_UNDEFINED'
        self._device = 'CPU'

    def fit(self, metadata: Metadata, dataloader: DataLoader, *args, **kwargs):
        raise NotImplementedError

    def set_device(self, device):
        """Set the `device` to be used ('GPU' or 'CPU')."""
        self._device = device
        if self._generator is not None:
            self._generator.to(self._device)

    def __getstate__(self):
        device_backup = self._device
        self.set_device(torch.device('cpu'))
        state = self.__dict__.copy()
        self.set_device(device_backup)
        if isinstance(self.random_states, tuple) and isinstance(self.random_states[0], np.random.RandomState) and isinstance(self.random_states[1], torch.Generator):
            state['_numpy_random_state'] = self.random_states[0].get_state()
            state['_torch_random_state'] = self.random_states[1].get_state()
            state.pop('random_states')
        return state

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
        if not os.getenv('SDG_FORCE_LOAD_CPU'):
            device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
            self.set_device(device)

    def save(self, path):
        device_backup = self._device
        self.set_device(torch.device('cpu'))
        torch.save(self, path)
        self.set_device(device_backup)

    @classmethod
    def load(cls, path):
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        model = torch.load(path)
        model.set_device(device)
        return model

    def set_random_state(self, random_state):
        if random_state is None:
            self.random_states = random_state
        elif isinstance(random_state, int):
            self.random_states = (np.random.RandomState(seed=random_state), torch.Generator().manual_seed(random_state))
        elif isinstance(random_state, tuple) and isinstance(random_state[0], np.random.RandomState) and isinstance(random_state[1], torch.Generator):
            self.random_states = random_state
        else:
            raise TypeError(f'`random_state` {random_state} expected to be an int or a tuple of (`np.random.RandomState`, `torch.Generator`)')

def __init__(self, transformer=None, sampler=None, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self._generator = None
    self.model = None
    self.status = 'UNFINED'
    self.model_type = 'MODEL_TYPE_UNDEFINED'
    self._device = 'CPU'

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
    if not os.getenv('SDG_FORCE_LOAD_CPU'):
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.set_device(device)

def save(self, path):
    device_backup = self._device
    self.set_device(torch.device('cpu'))
    torch.save(self, path)
    self.set_device(device_backup)

@classmethod
def load(cls, path):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = torch.load(path)
    model.set_device(device)
    return model

def set_random_state(self, random_state):
    if random_state is None:
        self.random_states = random_state
    elif isinstance(random_state, int):
        self.random_states = (np.random.RandomState(seed=random_state), torch.Generator().manual_seed(random_state))
    elif isinstance(random_state, tuple) and isinstance(random_state[0], np.random.RandomState) and isinstance(random_state[1], torch.Generator):
        self.random_states = random_state
    else:
        raise TypeError(f'`random_state` {random_state} expected to be an int or a tuple of (`np.random.RandomState`, `torch.Generator`)')

class DataFrameConnector(DataConnector):
    """
    Directly Wraps DataFrame into :ref:`DataConnector`, for small dataset can be loaded all in memory.

    Args:
        df (pd.DataFrame): DataFrame to be wrapped.

    Example:

        .. code-block:: python
            from sdgx.data_connectors.dataframe_connector import DataFrameConnector
            connector = DataFrameConnector(
                df=pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}),
            )
            df = connector.read()


    """

    def __init__(self, df: pd.DataFrame, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.df: pd.DataFrame = df

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        length = self.df.shape[0]
        if offset >= length:
            return None
        limit = limit or length
        return self.df.iloc[offset:min(offset + limit, length)]

    def _columns(self) -> list[str]:
        return list(self.df.columns)

    def _iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:

        def generator() -> Generator[pd.DataFrame, None, None]:
            length = self.df.shape[0]
            if offset < length:
                current = offset
                while current < length:
                    yield self.df.iloc[current:min(current + chunksize, length)]
                    current += chunksize
        return generator()

def __init__(self, df: pd.DataFrame, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.df: pd.DataFrame = df

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

def __init__(self, generator_caller: Callable[[], Generator[pd.DataFrame, None, None]], *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.generator_caller = generator_caller
    self._generator = self.generator_caller()

class MockDataConnector(GeneratorConnector):

    def __init__(self, *args, **kwargs):
        super().__init__(generator_data, *args, **kwargs)

def __init__(self, *args, **kwargs):
    super().__init__(generator_data, *args, **kwargs)

class MockInspector(RelationshipInspector):

    def __init__(self, dummy_data: list[Relationship], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tables = set()
        self.dummy_data = dummy_data

    def _build_relationship(self) -> list[Relationship]:
        return self.dummy_data

def __init__(self, dummy_data: list[Relationship], *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.tables = set()
    self.dummy_data = dummy_data

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

def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._readed = False

