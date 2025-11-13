# Cluster 8

def time2int(datetime, form='%Y-%m-%d %H:%M:%S'):
    time_array = time.strptime(str(datetime), form)
    time_stamp = int(time.mktime(time_array))
    return time_stamp

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

def reverse_convert(self, processed_data: pd.DataFrame) -> pd.DataFrame:
    if not self.email_columns_list:
        return processed_data
    df_length = processed_data.shape[0]
    for each_col_name in self.email_columns_list:
        each_email_col = [fake.ascii_company_email() for _ in range(df_length)]
        each_email_df = pd.DataFrame({each_col_name: each_email_col})
        processed_data = self.attach_columns(processed_data, each_email_df)
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

def replace_row(row):
    base_val = row[base_col]
    if base_val in mapping:
        new_related_val = mapping[base_val]
        return pd.Series({base_col: base_val, related_col: new_related_val})
    else:
        new_base_val = random.choice(list(mapping.keys()))
        new_related_val = mapping[new_base_val]
        return pd.Series({base_col: new_base_val, related_col: new_related_val})

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

def convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return self.int_outlier_fill_value

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

def column_timestamp_formatter(each_stamp: int, timestamp_format: str) -> str:
    try:
        each_str = datetime.fromtimestamp(each_stamp).strftime(timestamp_format)
    except Exception as e:
        logger.debug(f'An error occured when convert timestamp to str {e}.')
        each_str = 'No Datetime'
    return each_str

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    return {'bool_columns': list(self.bool_columns)}

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    return {'discrete_columns': list(self.discrete_columns)}

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    return {'empty_columns': list(self.empty_columns)}

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    return {'id_columns': list(self.ID_columns)}

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    return {'datetime_columns': list(self.datetime_columns), 'datetime_formats': self.column_formats}

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

def inspect(self, *args, **kwargs) -> dict[str, Any]:
    """Inspect raw data and generate metadata."""
    return {self.data_type_name + '_columns': list(self.regex_columns)}

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

def sample(self, count: int, *args, **kwargs) -> pd.DataFrame:
    if self.fit_data_empty:
        return pd.DataFrame(index=range(count))
    return self._sample(count, *args, **kwargs)

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

def __str__(self):
    return str(self.values)

def flatten_array(nested, prefix=''):
    """Flatten an array as a dict.

    Args:
        nested (list, numpy.array):
            Iterable to flatten.
        prefix (str):
            Name to append to the array indices. Defaults to ``''``.

    Returns:
        dict:
            Flattened array.
    """
    result = {}
    for index in range(len(nested)):
        prefix_key = '__'.join([prefix, str(index)]) if len(prefix) else str(index)
        value = nested[index]
        if isinstance(value, (list, np.ndarray)):
            result.update(flatten_array(value, prefix=prefix_key))
        elif isinstance(value, dict):
            result.update(flatten_dict(value, prefix=prefix_key))
        else:
            result[prefix_key] = value
    return result

def flatten_dict(nested, prefix=''):
    """Flatten a dictionary.

    This method returns a flatten version of a dictionary, concatenating key names with
    double underscores.

    Args:
        nested (dict):
            Original dictionary to flatten.
        prefix (str):
            Prefix to append to key name. Defaults to ``''``.

    Returns:
        dict:
            Flattened dictionary.
    """
    result = {}
    for key, value in nested.items():
        prefix_key = '__'.join([prefix, str(key)]) if len(prefix) else key
        if key in IGNORED_DICT_KEYS and (not isinstance(value, (dict, list))):
            continue
        elif isinstance(value, dict):
            result.update(flatten_dict(value, prefix_key))
        elif isinstance(value, (np.ndarray, list)):
            result.update(flatten_array(value, prefix_key))
        else:
            result[prefix_key] = value
    return result

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

def get_demo(num_rows=5):
    """Generate demo data with multiple sdtypes.

    The first five rows are hard coded. The rest are randomly generated
    using ``np.random.seed(42)``.

    Args:
        num_rows (int):
            Number of data rows to generate. Defaults to 5.

    Returns:
        pd.DataFrame
    """
    login_dates = ['2021-06-26', '2021-02-10', 'NAT', '2020-09-26', '2020-12-22']
    last_login = [np.datetime64(i) for i in login_dates]
    email_optin = pd.Series([False, False, False, True, np.nan], dtype='object')
    credit_card = ['VISA', 'VISA', 'AMEX', np.nan, 'DISCOVER']
    age = [29, 18, 21, 45, 32]
    dollars_spent = [99.99, np.nan, 2.5, 25.0, 19.99]
    data = pd.DataFrame({'last_login': last_login, 'email_optin': email_optin, 'credit_card': credit_card, 'age': age, 'dollars_spent': dollars_spent})
    if num_rows <= 5:
        return data.iloc[:num_rows]
    random_state = np.random.get_state()
    np.random.set_state(np.random.RandomState(RANDOM_SEED).get_state())
    try:
        num_rows -= 5
        login_dates = np.array([np.datetime64('2000-01-01') + np.timedelta64(np.random.randint(0, 10000), 'D') for _ in range(num_rows)])
        login_dates[np.random.random(size=num_rows) > 0.8] = np.datetime64('NaT')
        email_optin = pd.Series([True, False, np.nan], dtype='object').sample(num_rows, replace=True)
        credit_card = np.random.choice(['VISA', 'AMEX', np.nan, 'DISCOVER'], size=num_rows)
        age = np.random.randint(18, 100, size=num_rows)
        dollars_spent = np.around(np.random.uniform(0, 100, size=num_rows), decimals=2)
        dollars_spent[np.random.random(size=num_rows) > 0.8] = np.nan
    finally:
        np.random.set_state(random_state)
    return data.append(pd.DataFrame({'last_login': login_dates, 'email_optin': email_optin, 'credit_card': credit_card, 'age': age, 'dollars_spent': dollars_spent}), ignore_index=True)

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

def get_output_columns(self):
    """Return list of column names created in ``transform``.

        Returns:
            list:
                Names of columns created during ``transform``.
        """
    return list(self.get_output_sdtypes())

def _build_output_columns(self, data):
    self.column_prefix = '#'.join(self.columns)
    self.output_columns = list(self.get_output_sdtypes().keys())
    data_columns = set(data.columns)
    while data_columns & set(self.output_columns):
        self.column_prefix += '#'
        self.output_columns = list(self.get_output_sdtypes().keys())

def _max_repeat(options, max_repeat):
    min_, max_, options = options
    if max_ == sre_parse.MAXREPEAT:
        max_ = max_repeat
    option, args = options[0]
    _, size = _GENERATORS[option](args, max_repeat)
    generators = []
    sizes = []
    for repeat in range(min_, max_ + 1):
        if repeat:
            sizes.append(size ** repeat)
            repeat_generators = [(_GENERATORS[option](args, max_repeat)[0], option, args) for _ in range(repeat)]
            generators.append(_from_generators(repeat_generators, max_repeat))
    return ((value for generator in generators for value in generator), np.sum(sizes) + int(min_ == 0))

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

class RandomIntegerGenerator(CategoricalGenerator):
    """Generator that creates an array of random integers."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        categories = [1, 2, 3, 4, 5]
        return np.random.choice(a=categories, size=num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 5e-05, 'memory': 400.0}, 'reverse_transform': {'time': 1e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    categories = [1, 2, 3, 4, 5]
    return np.random.choice(a=categories, size=num_rows)

class RandomStringGenerator(CategoricalGenerator):
    """Generator that creates an array of random strings."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        categories = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
        return np.random.choice(a=categories, size=num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 500.0}, 'transform': {'time': 1e-05, 'memory': 500.0}, 'reverse_transform': {'time': 1e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    categories = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
    return np.random.choice(a=categories, size=num_rows)

class RandomMixedNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array of random mixed types with nans.

    Mixed types include: int, float, bool, string, datetime.
    """

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        array = RandomMixedGenerator.generate(num_rows)
        length = len(array)
        num_nulls = np.random.randint(1, length)
        nulls_idx = np.random.choice(range(length), num_nulls)
        nulls = np.random.choice([np.nan, float('nan'), None], num_nulls)
        array[nulls_idx] = nulls
        return array

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 2000.0}, 'reverse_transform': {'time': 1e-05, 'memory': 2000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    array = RandomMixedGenerator.generate(num_rows)
    length = len(array)
    num_nulls = np.random.randint(1, length)
    nulls_idx = np.random.choice(range(length), num_nulls)
    nulls = np.random.choice([np.nan, float('nan'), None], num_nulls)
    array[nulls_idx] = nulls
    return array

def add_nans(array):
    """Add a random amount of NaN values to the given array.

    Args:
        array (np.array):
            1 dimensional numpy array.

    Returns:
        np.array:
            The same array with some values replaced by NaNs.
    """
    if array.dtype.kind == 'i':
        array = array.astype(float)
    length = len(array)
    num_nulls = np.random.randint(1, length)
    nulls = np.random.choice(range(length), num_nulls)
    array[nulls] = np.nan
    return array

class RandomStringGenerator(PIIGenerator):
    """Generator that creates an array of random strings."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        categories = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
        return np.random.choice(a=categories, size=num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 500.0}, 'transform': {'time': 1e-05, 'memory': 500.0}, 'reverse_transform': {'time': 2e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    categories = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
    return np.random.choice(a=categories, size=num_rows)

class RandomIntegerGenerator(NumericalGenerator):
    """Generator that creates an array of random integers."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        ii32 = np.iinfo(np.int32)
        return np.random.randint(ii32.min, ii32.max, num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 2500.0}, 'transform': {'time': 5e-05, 'memory': 400.0}, 'reverse_transform': {'time': 5e-05, 'memory': 400.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    ii32 = np.iinfo(np.int32)
    return np.random.randint(ii32.min, ii32.max, num_rows)

class ConstantIntegerGenerator(NumericalGenerator):
    """Generator that creates a constant array with a random integer."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        ii32 = np.iinfo(np.int32)
        constant = np.random.randint(ii32.min, ii32.max)
        return np.full(num_rows, constant)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 400.0}, 'reverse_transform': {'time': 5e-05, 'memory': 400.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    ii32 = np.iinfo(np.int32)
    constant = np.random.randint(ii32.min, ii32.max)
    return np.full(num_rows, constant)

class RandomStringGenerator(RegexGeneratorGenerator):
    """Generator that creates an array of random strings."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        categories = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
        return np.random.choice(a=categories, size=num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 500.0}, 'transform': {'time': 1e-05, 'memory': 500.0}, 'reverse_transform': {'time': 2e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    categories = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
    return np.random.choice(a=categories, size=num_rows)

class RandomGapDatetimeGenerator(DatetimeGenerator):
    """Generator that creates dates with random gaps between them."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        today = datetime.datetime.today()
        delta = datetime.timedelta(days=1)
        dates = [np.random.random() * delta + today for i in range(num_rows)]
        return np.array(dates, dtype='datetime64')

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 5e-05, 'memory': 500.0}, 'transform': {'time': 5e-05, 'memory': 300.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    today = datetime.datetime.today()
    delta = datetime.timedelta(days=1)
    dates = [np.random.random() * delta + today for i in range(num_rows)]
    return np.array(dates, dtype='datetime64')

class RandomGapSecondsDatetimeGenerator(DatetimeGenerator):
    """Generator that creates dates with random gaps of seconds between them."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        today = datetime.datetime.today()
        delta = datetime.timedelta(seconds=1)
        dates = [np.random.random() * delta + today for i in range(num_rows)]
        return np.array(dates, dtype='datetime64')

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 5e-05, 'memory': 500.0}, 'transform': {'time': 5e-05, 'memory': 300.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    today = datetime.datetime.today()
    delta = datetime.timedelta(seconds=1)
    dates = [np.random.random() * delta + today for i in range(num_rows)]
    return np.array(dates, dtype='datetime64')

class EqualGapHoursDatetimeGenerator(DatetimeGenerator):
    """Generator that creates dates with hour gaps between them."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        today = datetime.datetime.today()
        delta = datetime.timedelta
        dates = [delta(hours=i) + today for i in range(num_rows)]
        return np.array(dates, dtype='datetime64')

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 5e-05, 'memory': 500.0}, 'transform': {'time': 5e-05, 'memory': 300.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    today = datetime.datetime.today()
    delta = datetime.timedelta
    dates = [delta(hours=i) + today for i in range(num_rows)]
    return np.array(dates, dtype='datetime64')

class EqualGapDaysDatetimeGenerator(DatetimeGenerator):
    """Generator that creates dates with 1 day gaps between them."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        today = datetime.datetime.today()
        delta = datetime.timedelta
        today = min(datetime.datetime.today(), pd.Timestamp.max - delta(num_rows))
        dates = [delta(i) + today for i in range(num_rows)]
        return np.array(dates, dtype='datetime64')

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 5e-05, 'memory': 500.0}, 'transform': {'time': 5e-05, 'memory': 300.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    today = datetime.datetime.today()
    delta = datetime.timedelta
    today = min(datetime.datetime.today(), pd.Timestamp.max - delta(num_rows))
    dates = [delta(i) + today for i in range(num_rows)]
    return np.array(dates, dtype='datetime64')

class EqualGapWeeksDatetimeGenerator(DatetimeGenerator):
    """Generator that creates dates with 1 week gaps between them."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        today = datetime.datetime.today()
        delta = datetime.timedelta
        today = datetime.datetime.today()
        dates = [min(delta(weeks=i) + today, pd.Timestamp.max) for i in range(num_rows)]
        return np.array(dates, dtype='datetime64')

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 5e-05, 'memory': 500.0}, 'transform': {'time': 5e-05, 'memory': 300.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    today = datetime.datetime.today()
    delta = datetime.timedelta
    today = datetime.datetime.today()
    dates = [min(delta(weeks=i) + today, pd.Timestamp.max) for i in range(num_rows)]
    return np.array(dates, dtype='datetime64')

class RandomBooleanGenerator(BooleanGenerator):
    """Generator that creates dataset of random booleans."""

    @staticmethod
    def generate(num_rows):
        """Generate an array of random booleans.

        Args:
            num_rows (int):
                Number of rows of booleans to generate.

        Returns:
            numpy.ndarray of size ``num_rows`` containing random booleans.
        """
        return np.random.choice(a=[True, False], size=num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 400.0}, 'reverse_transform': {'time': 5e-05, 'memory': 500.0}}

@staticmethod
def generate(num_rows):
    """Generate an array of random booleans.

        Args:
            num_rows (int):
                Number of rows of booleans to generate.

        Returns:
            numpy.ndarray of size ``num_rows`` containing random booleans.
        """
    return np.random.choice(a=[True, False], size=num_rows)

class RandomBooleanNaNsGenerator(BooleanGenerator):
    """Generator that creates an array of random booleans with nulls."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        percent_null = np.random.randint(MIN_PERCENT, MAX_PERCENT_NULL)
        percent_true = (100 - percent_null) / 2
        percent_false = 100 - percent_true - percent_null
        return np.random.choice(a=[True, False, None], size=num_rows, p=[percent_true / 100, percent_false / 100, percent_null / 100])

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    percent_null = np.random.randint(MIN_PERCENT, MAX_PERCENT_NULL)
    percent_true = (100 - percent_null) / 2
    percent_false = 100 - percent_true - percent_null
    return np.random.choice(a=[True, False, None], size=num_rows, p=[percent_true / 100, percent_false / 100, percent_null / 100])

class RandomSkewedBooleanGenerator(BooleanGenerator):
    """Generator that creates dataset of random booleans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        percent_true = np.random.randint(MIN_PERCENT, 100 - MIN_PERCENT)
        return np.random.choice(a=[True, False], size=num_rows, p=[percent_true / 100, (100 - percent_true) / 100])

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 400.0}, 'reverse_transform': {'time': 5e-05, 'memory': 500.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    percent_true = np.random.randint(MIN_PERCENT, 100 - MIN_PERCENT)
    return np.random.choice(a=[True, False], size=num_rows, p=[percent_true / 100, (100 - percent_true) / 100])

class RandomSkewedBooleanNaNsGenerator(BooleanGenerator):
    """Generator that creates an array of random booleans with nulls."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        percent_null = np.random.randint(MIN_PERCENT, MAX_PERCENT_NULL)
        percent_true = np.random.randint(MIN_PERCENT, 100 - percent_null - MIN_PERCENT)
        percent_false = 100 - percent_null - percent_true
        return np.random.choice(a=[True, False, None], size=num_rows, p=[percent_true / 100, percent_false / 100, percent_null / 100])

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    percent_null = np.random.randint(MIN_PERCENT, MAX_PERCENT_NULL)
    percent_true = np.random.randint(MIN_PERCENT, 100 - percent_null - MIN_PERCENT)
    percent_false = 100 - percent_null - percent_true
    return np.random.choice(a=[True, False, None], size=num_rows, p=[percent_true / 100, percent_false / 100, percent_null / 100])

class ConstantBooleanNaNsGenerator(BooleanGenerator):
    """Generator that creates a constant array with either True or False with some nulls."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        constant = np.random.choice([True, False])
        percent_null = np.random.randint(MIN_PERCENT, MAX_PERCENT_NULL)
        return np.random.choice(a=[constant, None], size=num_rows, p=[(100 - percent_null) / 100, percent_null / 100])

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    constant = np.random.choice([True, False])
    percent_null = np.random.randint(MIN_PERCENT, MAX_PERCENT_NULL)
    return np.random.choice(a=[constant, None], size=num_rows, p=[(100 - percent_null) / 100, percent_null / 100])

def sample_bivariate_age_income(size=1000, seed=42):
    """Sample from a bivariate toy dataset.

    This dataset contains two columns which correspond to the simulated age and
    income which are positively correlated with outliers.

    Args:
        size (int):
            Amount of samples to generate. Defaults to 1000.
        seed (int):
            Random seed to use. Defaults to 42.

    Returns:
        pandas.DataFrame:
            DataFrame with two columns, ``age`` and ``income``.
    """
    with set_random_state(validate_random_state(seed), _dummy_fn):
        age = stats.beta.rvs(a=2.0, b=6.0, loc=18, scale=100, size=size)
        income = np.log(age) * 100
        income += np.random.normal(loc=np.log(age) / 100, scale=10, size=size)
        income[np.random.randint(0, 10, size=size) == 0] /= 1000
    return pd.DataFrame({'age': age, 'income': income})

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
def _deserialize_previous_tree(cls, tree_dict, previous):
    if tree_dict['level'] == 1:
        return np.array(tree_dict['previous_tree'])
    return previous

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

def split_matrix(X):
    """Split an (n,2) numpy.array into two vectors.

    Args:
        X(numpy.array): Matrix of shape (n,2)

    Returns:
        tuple[numpy.array]: Both of shape (n,)

    """
    if len(X):
        return (X[:, 0], X[:, 1])
    return (np.array([]), np.array([]))

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

def _columns(self) -> list[str]:
    return list(self.df.columns)

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

def _columns(self) -> list[str]:
    for df in self._iter():
        return list(df.columns)

def random_string(length):
    return ''.join((random.choice(string.ascii_lowercase) for i in range(length)))

def random_float():
    return random.random() * 1000

def random_int():
    return random.randint(0, 1000)

def random_timestamp():
    current_timestamp = datetime.datetime.now().timestamp()
    return current_timestamp + random_int()

def random_datetime():
    return datetime.datetime.fromtimestamp(random_timestamp())

def _generate_one_line():
    return ','.join(map(str, itertools.chain((random_int() for _ in range(int_cols)), (random_float() for _ in range(float_cols)), (random.choice(random_str_list) for _ in range(string_cols)), (random_timestamp() for _ in range(timestamp_cols)), (random_datetime() for _ in range(datetime_cols)))))

@pytest.fixture
def demo_single_table_data_pos_neg():
    row_cnt = 1000
    np.random.seed(42)
    faker.Faker.seed(42)
    fake = faker.Faker()
    X = {'int_id': list(range(row_cnt)), 'pos_int': np.random.randint(1, 100, size=row_cnt), 'neg_int': np.random.randint(-100, 0, size=row_cnt), 'pos_float': np.random.uniform(0, 100, size=row_cnt), 'neg_float': np.random.uniform(-100, 0, size=row_cnt), 'mixed_int': np.random.randint(-50, 50, size=row_cnt), 'mixed_float': np.random.uniform(-50, 50, size=row_cnt), 'cat_onehot': [str(i) for i in range(row_cnt)], 'cat_label': [str(i) for i in range(row_cnt)], 'cat_date': [fake.date() for _ in range(row_cnt)], 'cat_freq': [str(i) for i in range(row_cnt)], 'cat_thres_freq': [str(i) for i in range(100)] * (row_cnt // 100), 'cat_thres_label': [str(i) for i in range(200)] * (row_cnt // 200)}
    header = X.keys()
    yield pd.DataFrame(X, columns=list(header))

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

def sample(self, count, **kwargs) -> pd.DataFrame:
    return pd.DataFrame({'a': [i for i in range(count)], 'b': [i * 2 for i in range(count)]})

def generator_data() -> pd.DataFrame:
    for i in range(10):
        yield pd.DataFrame({'a': [i], 'b': [i * 2]})

def ramdon_str():
    return ''.join((random.choice(string.ascii_letters) for _ in range(10)))

@pytest.fixture
def dummy_single_table_path(tmp_path):
    dummy_size = 10
    role_set = ['admin', 'user', 'guest']
    df = pd.DataFrame({'role': [random.choice(role_set) for _ in range(dummy_size)], 'name': [ramdon_str() for _ in range(dummy_size)], 'feature_x': [random.random() for _ in range(dummy_size)], 'feature_y': [random.random() for _ in range(dummy_size)], 'feature_z': [random.random() for _ in range(dummy_size)]})
    save_path = tmp_path / 'dummy.csv'
    df.to_csv(save_path, index=False, header=True)
    yield save_path
    save_path.unlink()

@pytest.fixture
def demo_relational_table_path(tmp_path):
    dummy_size = 10
    role_set = ['admin', 'user', 'guest']
    df = pd.DataFrame({'id': list(range(dummy_size)), 'role': [random.choice(role_set) for _ in range(dummy_size)], 'name': [ramdon_str() for _ in range(dummy_size)], 'feature_x': [random.random() for _ in range(dummy_size)], 'feature_y': [random.random() for _ in range(dummy_size)], 'feature_z': [random.random() for _ in range(dummy_size)]})
    save_path_a = tmp_path / 'dummy_relation_A.csv'
    df.to_csv(save_path_a, index=False, header=True)
    sub_size = 5
    assert dummy_size >= sub_size
    df = pd.DataFrame({'foreign_id': list(range(sub_size)), 'feature_i': [random.random() for _ in range(sub_size)], 'feature_j': [random.random() for _ in range(sub_size)], 'feature_k': [random.random() for _ in range(sub_size)]})
    save_path_b = tmp_path / 'dummy_relation_B.csv'
    df.to_csv(save_path_b, index=False, header=True)
    return (save_path_a, save_path_b, [('id', 'foreign_id')])

@pytest.fixture
def ndarray_list():
    """
    1, 4, 7
    2, 5, 8
    3, 6, 9
    """
    yield [np.array([[1], [2], [3]]), np.array([[4], [5], [6]]), np.array([[7], [8], [9]])]

@pytest.fixture
def datetime_test_df():
    total_row = 150
    ff = faker.Faker()
    df = pd.DataFrame([ff.date() for i in range(total_row)], columns=['date'])
    return df

def preparing_data():
    fake = faker.Faker()
    data = [(i, random.choice('abcdefg'), (random.random() - 0.5) * 1000, fake.name(), fake.date_between(start_date='today', end_date='+1y'), (random.random() - 0.5) * 1000, fake.sentence(nb_words=3)) for i in range(1000)]
    df = pd.DataFrame(data, columns=['id', 'grade', 'num2', 'author', 'date', 'num', 'title'])

    def gen_func():
        yield df.copy()
    connector = GeneratorConnector(gen_func)
    data_metadata = Metadata.from_dataframe(df)
    dl = DataLoader(connector)
    data_metadata.datetime_format = {key: '%Y/%m/%d' for key in data_metadata.datetime_columns}
    transformer = DataTransformer()
    transformer.fit(dl, data_metadata.discrete_columns)
    return (transformer, dl)

def test_parallel_transform_fixed_not_columns_switching():
    transformer, data_loader = preparing_data()
    ndarry_loader = transformer._parallel_transform(data_loader, transformer._column_transform_info_list)
    find_not_matching_column_type_onehot(ndarry_loader, transformer._column_transform_info_list)

def generator():
    yield pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    yield pd.DataFrame({'a': [7, 8, 9], 'b': [10, 11, 12]})

def test_attach_columns(single_demo_data_df: pd.DataFrame, attach_demo_data_df: pd.DataFrame, base_data_processor: DataProcessor):
    assert 'occupation' in single_demo_data_df.columns
    assert 'workclass' in single_demo_data_df.columns
    assert 'age' in single_demo_data_df.columns
    assert 'education' not in single_demo_data_df.columns
    assert 'capital-gain' not in single_demo_data_df.columns
    assert 'education' in attach_demo_data_df.columns
    assert 'capital-gain' in attach_demo_data_df.columns
    attached_df = base_data_processor.attach_columns(single_demo_data_df, attach_demo_data_df)
    assert 'occupation' in attached_df.columns
    assert 'workclass' in attached_df.columns
    assert 'age' in attached_df.columns
    assert 'education' in attached_df.columns
    assert 'capital-gain' in attached_df

@pytest.fixture
def chn_personal_test_df():
    row_cnt = 1000
    today = datetime.datetime.today()
    X = []
    header = ['ssn_sfz', 'chn_name', 'eng_name', 'gender', 'birth_date', 'age', 'email', 'mobile_phone_no', 'chn_address', 'postcode', 'job', 'company_name']
    for _ in range(row_cnt):
        each_gender = random.choice(['male', 'female'])
        if each_gender == 'male':
            each_name = fake.last_name() + fake.name_male()
        else:
            each_name = fake.last_name() + fake.name_female()
        each_eng_name = fake_en.name()
        each_birth_date = fake.date()
        each_age = today.year - int(each_birth_date[:4])
        each_email = fake.email()
        each_phone = fake.phone_number()
        each_sfz = fake.ssn()
        each_address = fake.address()
        each_job = fake.job()
        each_corp = fake.company()
        each_postcode = fake.postcode()
        each_x = [each_sfz, each_name, each_eng_name, each_gender, each_birth_date, each_age, each_email, each_phone, each_address, each_postcode, each_job, each_corp]
        X.append(each_x)
    yield pd.DataFrame(X, columns=header)

@pytest.fixture
def chn_personal_test_df():
    row_cnt = 1000
    today = datetime.datetime.today()
    X = []
    header = ['ssn_sfz', 'chn_name', 'eng_name', 'gender', 'birth_date', 'age', 'email', 'mobile_phone_no', 'chn_address', 'postcode', 'job', 'company_name']
    for _ in range(row_cnt):
        each_gender = random.choice(['male', 'female'])
        if each_gender == 'male':
            each_name = fake.last_name() + fake.name_male()
        else:
            each_name = fake.last_name() + fake.name_female()
        each_eng_name = fake_en.name()
        each_birth_date = fake.date()
        each_age = today.year - int(each_birth_date[:4])
        each_email = fake.email()
        each_phone = fake.phone_number()
        each_sfz = fake.ssn()
        each_address = fake.address()
        each_job = fake.job()
        each_corp = fake.company()
        each_postcode = fake.postcode()
        each_x = [each_sfz, each_name, each_eng_name, each_gender, each_birth_date, each_age, each_email, each_phone, each_address, each_postcode, each_job, each_corp]
        X.append(each_x)
    yield pd.DataFrame(X, columns=header)

@pytest.fixture
def pos_neg_test_df():
    row_cnt = 1000
    header = ['int_id', 'pos_int', 'neg_int', 'pos_float', 'neg_float', 'mixed_int', 'mixed_float']
    np.random.seed(42)
    int_id = list(range(row_cnt))
    pos_int = np.random.randint(1, 100, size=row_cnt)
    neg_int = np.random.randint(-100, 0, size=row_cnt)
    pos_float = np.random.uniform(0, 100, size=row_cnt)
    neg_float = np.random.uniform(-100, 0, size=row_cnt)
    mixed_int = np.random.randint(-50, 50, size=row_cnt)
    mixed_float = np.random.uniform(-50, 50, size=row_cnt)
    X = [[int_id[i], pos_int[i], neg_int[i], pos_float[i], neg_float[i], mixed_int[i], mixed_float[i]] for i in range(row_cnt)]
    yield pd.DataFrame(X, columns=header)

@pytest.fixture
def train_data():
    return pd.DataFrame({'price_usd': [100, 200, 300], 'price_cny': [700, 1400, 2100], 'price_eur': [90, 180, 270], 'size_cm': [10, 20, 30], 'size_inch': [3.94, 7.87, 11.81], 'size_m': [0.1, 0.2, 0.3]})

@pytest.fixture
def test_data():
    return pd.DataFrame({'price_usd': [200, 200, 100], 'price_cny': [1400, 1400, 2100], 'price_eur': [90, 270, 270], 'size_cm': [10, 20, 20], 'size_inch': [3.94, 7.87, 11.81], 'size_m': [0.1, 0.3, 0.3]})

@pytest.fixture
def expected_data():
    return pd.DataFrame({'price_usd': [200, 200, 300], 'price_cny': [1400, 1400, 2100], 'price_eur': [180, 180, 270], 'size_cm': [10, 20, 30], 'size_inch': [3.94, 7.87, 11.81], 'size_m': [0.1, 0.2, 0.3]})

@pytest.fixture
def df_data():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'int_random', 'bool_random', 'float_random']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    bool_random = int_random < 50
    float_random = np.random.randn(row_cnt)
    X = [[int_id[i], str_id[i], int_random[i], bool_random[i], float_random[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    yield df

@pytest.fixture
def test_fixed_combination_data():
    data = {'A': [1, 2, 3, 4, 5], 'B': [2, 4, 6, 8, 10], 'C': [5, 5, 5, 5, 5], 'D': [1, 3, 5, 7, 9], 'E': [2, 4, 6, 8, 10], 'categorical_one': ['co1', 'co3', 'co2', 'co9', 'co1'], 'categorical_two': ['ct1', 'ct3', 'ct2', 'ct9', 'ct1']}
    df = pd.DataFrame(data)
    yield df

@pytest.fixture
def df_data():
    row_cnt = 100
    header = ['int_id', 'str_id', 'int_random', 'bool_random', 'float_random']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    bool_random = int_random < 50
    float_random = np.random.randn(row_cnt)
    X = [[int_id[i], str_id[i], int_random[i], bool_random[i], float_random[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    yield df

@pytest.fixture
def df_data_processed():
    """
    A synthetic dataframe after being processed by other processor / model.
    """
    row_cnt = 100
    header = ['int_random', 'int_id', 'float_random_2', 'bool_random', 'float_random', 'bool_random_2', 'str_id']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    bool_random = int_random < 50
    bool_random_2 = int_random < 40
    float_random = np.random.randn(row_cnt)
    float_random_2 = np.random.randn(row_cnt)
    X = [[int_random[i], int_id[i], float_random_2[i], bool_random[i], float_random[i], bool_random_2[i], str_id[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    yield df

@pytest.fixture
def outlier_test_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'int_random', 'float_random']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    float_random = np.random.uniform(0, 100, size=row_cnt)
    X = [[int_id[i], str_id[i], int_random[i], float_random[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    outlier_indices = np.random.choice(row_cnt, size=int(row_cnt * 0.1), replace=False)
    for idx in outlier_indices:
        df.iat[idx, 2] = 'not_number_outlier'
        df.iat[idx, 3] = 'not_number_outlier'
    yield df

@pytest.fixture
def nan_test_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'int_random', 'bool_random']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    bool_random = int_random < 50
    X = [[int_id[i], str_id[i], int_random[i], bool_random[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    nan_indices = np.random.choice(row_cnt, size=int(row_cnt * 0.1), replace=False)
    for idx in nan_indices:
        col_idx = np.random.randint(0, len(header))
        df.iat[idx, col_idx] = np.nan
    yield df

@pytest.fixture
def df_data():
    row_cnt = 1000
    header = ['int_id', 'discrete_val', 'int_random', 'bool_random', 'float_random']
    int_id = list(range(row_cnt))
    discrete_val = list((random.choice(['a', 'b', 'c']) for _ in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    bool_random = int_random < 50
    float_random = np.random.randn(row_cnt)
    X = [[int_id[i], discrete_val[i], int_random[i], bool_random[i], float_random[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    yield df

def int_formatter_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'int_random', 'float_random']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    float_random = np.random.randn(row_cnt)
    X = [[int_id[i], str_id[i], int_random[i], float_random[i]] for i in range(row_cnt)]
    df = pd.DataFrame(X, columns=header)
    return df

@pytest.fixture
def datetime_test_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'not_int_id', 'not_str_id', 'simple_datetime', 'simple_datetime_2', 'date_with_time']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    not_int_id = list(range(int(row_cnt / 2))) + list(range(int(row_cnt / 2)))
    not_str_id = list(('id_' + str(i) for i in range(int(row_cnt / 2)))) + list(('id_' + str(i) for i in range(int(row_cnt / 2))))
    simple_datetime = pd.date_range(start='2023-12-27', periods=row_cnt)
    simple_datetime_2 = [datetime.datetime.strftime(x, '%d %b %Y') for x in simple_datetime]
    simple_datetime_str = [datetime.datetime.strftime(x, '%Y-%m-%d') for x in simple_datetime]
    h = np.random.randint(0, 24, size=row_cnt)
    m = np.random.randint(0, 59, size=row_cnt)
    s = np.random.randint(0, 59, size=row_cnt)
    date_with_time = [simple_datetime[i] + pd.Timedelta(hours=h[i], minutes=m[i], seconds=s[i]) for i in range(row_cnt)]
    datetime_test_df = [[int_id[i], str_id[i], not_int_id[i], not_str_id[i], simple_datetime_str[i], simple_datetime_2[i], date_with_time[i]] for i in range(row_cnt)]
    yield pd.DataFrame(datetime_test_df, columns=header)

def generate():
    code = ''
    code += random.choice(string.digits + 'AHJNPQRTUWXY')
    code += random.choice(string.digits + 'AHJNPQRTUWXY')
    code += ''.join(random.choices(string.digits, k=6))
    code += ''.join(random.choices(string.digits, k=9))
    code += random.choice(string.digits + 'AHJNPQRTUWXY')
    return code

@pytest.fixture
def chn_personal_test_df():
    row_cnt = 1000
    today = datetime.datetime.today()
    X = []
    header = ['ssn_sfz', 'chn_name', 'eng_name', 'gender', 'birth_date', 'age', 'email', 'mobile_phone_no', 'chn_address', 'postcode', 'job', 'company_name', 'uscc']
    for _ in range(row_cnt):
        each_gender = random.choice(['male', 'female'])
        if each_gender == 'male':
            each_name = fake.last_name() + fake.name_male()
        else:
            each_name = fake.last_name() + fake.name_female()
        each_eng_name = fake_en.name()
        each_birth_date = fake.date()
        each_age = today.year - int(each_birth_date[:4])
        each_email = fake.email()
        each_phone = fake.phone_number()
        each_sfz = fake.ssn()
        each_address = fake.address()
        each_job = fake.job()
        each_corp = fake.company()
        each_postcode = fake.postcode()
        each_uscc = generate_uniform_credit_code()
        each_x = [each_sfz, each_name, each_eng_name, each_gender, each_birth_date, each_age, each_email, each_phone, each_address, each_postcode, each_job, each_corp, each_uscc]
        X.append(each_x)
    yield pd.DataFrame(X, columns=header)

@pytest.fixture
def datetime_test_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'not_int_id', 'not_str_id', 'simple_datetime', 'simple_datetime_2', 'date_with_time']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    not_int_id = list(range(int(row_cnt / 2))) + list(range(int(row_cnt / 2)))
    not_str_id = list(('id_' + str(i) for i in range(int(row_cnt / 2)))) + list(('id_' + str(i) for i in range(int(row_cnt / 2))))
    simple_datetime = pd.date_range(start='2023-12-27', periods=row_cnt)
    simple_datetime_2 = [datetime.datetime.strftime(x, '%d %b %Y') for x in simple_datetime]
    h = np.random.randint(0, 24, size=row_cnt)
    m = np.random.randint(0, 59, size=row_cnt)
    s = np.random.randint(0, 59, size=row_cnt)
    date_with_time = [simple_datetime[i] + pd.Timedelta(hours=h[i], minutes=m[i], seconds=s[i]) for i in range(row_cnt)]
    X = [[int_id[i], str_id[i], not_int_id[i], not_str_id[i], simple_datetime[i], simple_datetime_2[i], date_with_time[i]] for i in range(row_cnt)]
    yield pd.DataFrame(X, columns=header)

@pytest.fixture
def test_fixed_combination_data():
    data = {'A': [1, 2, 3, 4, 5], 'B': [2, 4, 6, 8, 10], 'C': [5, 5, 5, 5, 5], 'D': [1, 3, 5, 7, 9], 'E': [2, 4, 6, 8, 10], 'categorical_1': ['apple', 'banana', 'apple', 'banana', 'cherry'], 'categorical_2': ['red', 'yellow', 'red', 'yellow', 'pink'], 'categorical_3': [1, 2, 1, 2, 3], 'categorical_4': ['one', 'two', 'one', 'two', 'three'], 'categorical_5': [0.1, 0.5, 0.1, 0.5, 1.0], 'categorical_6': ['light', 'medium', 'light', 'medium', 'heavy']}
    df = pd.DataFrame(data)
    yield df

@pytest.fixture
def bool_test_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'int_random', 'bool_random']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    int_random = np.random.randint(100, size=row_cnt)
    bool_random = int_random < 5
    X = [[int_id[i], str_id[i], int_random[i], bool_random[i]] for i in range(row_cnt)]
    yield pd.DataFrame(X, columns=header)

@pytest.fixture
def id_test_df():
    row_cnt = 1000
    header = ['int_id', 'str_id', 'not_int_id', 'not_str_id']
    int_id = list(range(row_cnt))
    str_id = list(('id_' + str(i) for i in range(row_cnt)))
    not_int_id = list(range(int(row_cnt / 2))) + list(range(int(row_cnt / 2)))
    not_str_id = list(('id_' + str(i) for i in range(int(row_cnt / 2)))) + list(('id_' + str(i) for i in range(int(row_cnt / 2))))
    X = [[int_id[i], str_id[i], not_int_id[i], not_str_id[i]] for i in range(row_cnt)]
    yield pd.DataFrame(X, columns=header)

def generator_caller():
    yield pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    yield pd.DataFrame({'a': [7, 8, 9], 'b': [10, 11, 12]})
    yield pd.DataFrame({'a': [13, 14, 15], 'b': [16, 17, 18]})

def generator_caller():
    yield pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    yield pd.DataFrame({'a': [7, 8, 9], 'b': [10, 11, 12]})
    yield pd.DataFrame({'a': [13, 14, 15], 'b': [16, 17, 18]})

@pytest.fixture
def data_for_test():
    return pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

def generate_random_time(start_date, end_date):
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    random_time_delta = random.randint(0, int((end_datetime - start_datetime).total_seconds()))
    random_datetime = start_datetime + timedelta(seconds=random_time_delta)
    return random_datetime

@pytest.fixture
def test_data_time():
    start_date = '1900-01-01'
    end_date = '2023-12-31'
    df = pd.DataFrame({'time_x': [generate_random_time(start_date, end_date) for _ in range(10)], 'time_y': [generate_random_time(start_date, end_date) for _ in range(10)]})
    return df

@pytest.fixture
def test_data_category():
    role_set = ['admin', 'user', 'guest']
    df = pd.DataFrame({'role1': [random.choice(role_set) for _ in range(10)], 'role2': [random.choice(role_set) for _ in range(10)]})
    return df

@pytest.fixture
def test_data_num():
    df = pd.DataFrame({'feature_x': [random.random() for _ in range(10)], 'feature_y': [random.random() for _ in range(10)]})
    return df

@pytest.fixture
def test_data():
    role_set = ['admin', 'user', 'guest']
    df = pd.DataFrame({'role': [random.choice(role_set) for _ in range(10)], 'feature_x': [random.random() for _ in range(10)]})
    return df

@pytest.fixture(scope='module')
def data_test():
    return pd.DataFrame({'x': [str(i) for i in range(100)], 'y': [str(-i) for i in range(50)] * 2, 'z': [str(i) for i in range(25)] * 4}, columns=['x', 'y', 'z'])

@pytest.mark.parametrize('response_index', range(len(gpt_response_list)))
def test_feature_extraction_data(response_index: int, single_table_gpt_model: SingleTableGPTModel, raw_data: pd.DataFrame):
    single_table_gpt_model.fit(raw_data)
    response_content = gpt_response_list[response_index]
    res = single_table_gpt_model.extract_samples_from_response(response_content)
    assert type(res) is list
    assert len(res) == gpt_response_sample_count[response_index]
    assert len(res[0]) == len(single_table_gpt_model.columns)
    res_df = pd.DataFrame(res, columns=single_table_gpt_model.columns + single_table_gpt_model.off_table_features)
    assert res_df.shape == (gpt_response_sample_count[response_index], len(single_table_gpt_model.columns))
    sample_list = single_table_gpt_model._sample_lines
    message = single_table_gpt_model._form_message_with_data(sample_list, 20)
    assert type(message) is str
    for each_col in raw_data.columns:
        assert each_col in message
    assert type(sample_list) is list
    assert len(sample_list) == len(raw_data)
    fake_openAI_KEY = 'sk-qXCXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    occur_error = False
    try:
        single_table_gpt_model.check()
        occur_error = False
    except Exception as e:
        occur_error = True
        assert type(e) is InitializationError
    assert occur_error is True
    single_table_gpt_model.set_openAI_settings('https://api.openai.com/v1/', fake_openAI_KEY)
    single_table_gpt_model.check()

@pytest.mark.parametrize('response_index', range(len(gpt_response_list)))
def test_feature_extraction_metadata(response_index: int, single_table_gpt_model: SingleTableGPTModel, demo_single_table_metadata: Metadata):
    single_table_gpt_model.fit(demo_single_table_metadata)
    single_table_gpt_model.off_table_features = ['has_car']
    response_content = gpt_response_list[response_index]
    res = single_table_gpt_model.extract_samples_from_response(response_content)
    assert len(res) == gpt_response_sample_count[response_index]
    assert len(res[0]) == len(single_table_gpt_model.columns) + len(single_table_gpt_model.off_table_features)
    res_df = pd.DataFrame(res, columns=single_table_gpt_model.columns + single_table_gpt_model.off_table_features)
    assert res_df.shape == (gpt_response_sample_count[response_index], len(single_table_gpt_model.columns) + len(single_table_gpt_model.off_table_features))
    message = single_table_gpt_model._form_message_with_metadata(20)
    for each_col in demo_single_table_metadata.column_list:
        assert each_col in message
    assert type(message) is str
    single_table_gpt_model.fit(metadata=demo_single_table_metadata)

@pytest.fixture(scope='module')
def data_test():
    return pd.DataFrame({'x': [str(i) for i in range(100)], 'y': [str(-i) for i in range(50)] * 2, 'z': [str(i) for i in range(25)] * 4}, columns=['x', 'y', 'z'])

