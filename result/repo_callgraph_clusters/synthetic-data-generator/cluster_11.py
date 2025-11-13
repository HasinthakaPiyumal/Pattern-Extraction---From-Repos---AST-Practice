# Cluster 11

class CsvExporter(DataExporter):

    def __init__(self, **kwargs):
        self.to_csv_kwargs = kwargs
        if 'header' in self.to_csv_kwargs:
            self.to_csv_kwargs.pop('header')
        if 'index' in self.to_csv_kwargs:
            self.to_csv_kwargs.pop('index')

    def write(self, dst: str | Path, data: pd.DataFrame | Generator[pd.DataFrame, None, None]) -> None:
        if isinstance(data, pd.DataFrame):
            data.to_csv(dst, index=False, **self.to_csv_kwargs)
        elif isinstance(data, Generator):
            with open(dst, 'a') as file:
                for df in data:
                    df.to_csv(file, header=file.tell() == 0, index=False, **self.to_csv_kwargs)
        else:
            raise CannotExportError(f'Cannot export data of type {type(data)} to csv')

def __init__(self, **kwargs):
    self.to_csv_kwargs = kwargs
    if 'header' in self.to_csv_kwargs:
        self.to_csv_kwargs.pop('header')
    if 'index' in self.to_csv_kwargs:
        self.to_csv_kwargs.pop('index')

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

def _covert_column_scale(self, column_name: str, column_data: pd.DataFrame):
    """
        Convert every numeric (include int and float) column using sklearn StandardScaler.
        """
    scaled_data = self.scalers[column_name].transform(column_data)
    return scaled_data

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

def _transform_continuous(self, column_transform_info, data):
    """Transform continuous column."""
    gm = column_transform_info.transform
    transformed = gm.transform(data)
    return transformed[f'{data.columns[0]}.normalized'].to_numpy().reshape(-1, 1)

def _transform_discrete(self, column_transform_info, data):
    """Transform discrete column using frequency encoding."""
    freq_encoder = column_transform_info.transform
    return freq_encoder.transform(data).to_numpy().reshape(-1, 1)

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

def generate_cond_from_condition_column_info(self, condition_info, batch):
    """Generate the condition vector."""
    vec = np.zeros((batch, self._n_categories), dtype='float32')
    id_ = self._onehot_column_matrix_st[condition_info['discrete_column_id']]
    id_ += condition_info['value_id']
    vec[:, id_] = 1
    return vec

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

def __setstate__(self, state):
    """Replace any ``null`` key by the actual ``np.nan`` instance."""
    intervals = state.get('intervals')
    if intervals:
        for key in list(intervals):
            if pd.isna(key):
                intervals[np.nan] = intervals.pop(key)
    self.__dict__ = state

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

def get_output_sdtypes(self):
    """Return the output sdtypes produced by this transformer.

        Returns:
            dict:
                Mapping from the transformed column names to the produced sdtypes.
        """
    output_sdtypes = {f'value{i}': 'float' for i in range(len(self.dummies))}
    return self._add_prefix(output_sdtypes)

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

def normalize_array_to_dict(arr):
    n = len(arr)
    digit = math.ceil(math.log10(n)) + 1
    self._round_digit = digit
    normalized_dict = {round(2 * i / (n - 1) - 1, digit): arr[i] for i in range(n)}
    return normalized_dict

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

def find_nearest_key(x):
    nearest_key = min(value_dict_keys, key=lambda k: abs(k - x))
    return value_dict[nearest_key]

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

def get_output_sdtypes(self):
    """Return the output sdtypes produced by this transformer.

        Returns:
            dict:
                Mapping from the transformed column names to the produced sdtypes.
        """
    return self._add_prefix(self.OUTPUT_SDTYPES)

def get_next_transformers(self):
    """Return the suggested next transformer to be used for each column.

        Returns:
            dict:
                Mapping from transformed column names to the transformers to apply to each column.
        """
    return self._add_prefix(self.NEXT_TRANSFORMERS)

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

def _in(options, max_repeat):
    generators = []
    sizes = []
    for option, args in options:
        generator, size = _GENERATORS[option](args, max_repeat)
        generators.append(generator)
        sizes.append(size)
    return ((value for generator in generators for value in generator), np.sum(sizes))

def strings_from_regex(regex, max_repeat=16):
    """Generate strings that match the given regular expression.

    The output is a generator that produces regular expressions that match
    the indicated regular expressions alongside an integer indicating the
    total length of the generator.

    WARNING: Subpatterns are currently not supported.

    Args:
        regex (str):
            String representing a valid python regular expression.
        max_repeat (int):
            Maximum number of repetitions to produce when the regular
            expression allows an infinte amount. Defaults to 16.

    Returns:
        tuple:
            * Generator that produces strings that match the given regex.
            * Total length of the generator.
    """
    parsed = sre_parse.parse(regex, flags=sre_parse.SRE_FLAG_UNICODE)
    generators = []
    sizes = []
    for option, args in reversed(parsed):
        if option != sre_parse.AT:
            generator, size = _GENERATORS[option](args, max_repeat)
            generators.append((generator, option, args))
            sizes.append(size)
    return (_from_generators(generators, max_repeat), np.prod(sizes))

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

class FloatFormatter(BaseTransformer):
    """Transformer for numerical data.

    This transformer replaces integer values with their float equivalent.
    Non null float values are not modified.

    Null values are replaced using a ``NullTransformer``.

    Args:
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
        learn_rounding_scheme (bool):
            Whether or not to learn what place to round to based on the data seen during ``fit``.
            If ``True``, the data returned by ``reverse_transform`` will be rounded to that place.
            Defaults to ``False``.
        enforce_min_max_values (bool):
            Whether or not to clip the data returned by ``reverse_transform`` to the min and
            max values seen during ``fit``. Defaults to ``False``.
        computer_representation (dtype):
            Accepts ``'Int8'``, ``'Int16'``, ``'Int32'``, ``'Int64'``, ``'UInt8'``, ``'UInt16'``,
            ``'UInt32'``, ``'UInt64'``, ``'Float'``.
            Defaults to ``'Float'``.
    """
    INPUT_SDTYPE = 'numerical'
    DETERMINISTIC_TRANSFORM = True
    DETERMINISTIC_REVERSE = True
    COMPOSITION_IS_IDENTITY = True
    null_transformer = None
    missing_value_replacement = None
    _dtype = None
    _rounding_digits = None
    _min_value = None
    _max_value = None

    def __init__(self, missing_value_replacement=None, model_missing_values=False, learn_rounding_scheme=False, enforce_min_max_values=False, computer_representation='Float'):
        self.missing_value_replacement = missing_value_replacement
        self.model_missing_values = model_missing_values
        self.learn_rounding_scheme = learn_rounding_scheme
        self.enforce_min_max_values = enforce_min_max_values
        self.computer_representation = computer_representation

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

    def is_composition_identity(self):
        """Return whether composition of transform and reverse transform produces the input data.

        Returns:
            bool:
                Whether or not transforming and then reverse transforming returns the input data.
        """
        if self.null_transformer and (not self.null_transformer.models_missing_values()):
            return False
        return self.COMPOSITION_IS_IDENTITY

    @staticmethod
    def _learn_rounding_digits(data):
        data = np.array(data)
        roundable_data = data[~(np.isinf(data) | pd.isna(data))]
        if (roundable_data % 1 != 0).any():
            if (roundable_data == roundable_data.round(MAX_DECIMALS)).all():
                for decimal in range(MAX_DECIMALS + 1):
                    if (roundable_data == roundable_data.round(decimal)).all():
                        return decimal
        return None

    def _raise_out_of_bounds_error(self, value, name, bound_type, min_bound, max_bound):
        raise ValueError(f"The {bound_type} value in column '{name}' is {value}. All values represented by '{self.computer_representation}' must be in the range [{min_bound}, {max_bound}].")

    def _validate_values_within_bounds(self, data):
        if self.computer_representation != 'Float':
            fractions = data[~data.isna() & data % 1 != 0]
            if not fractions.empty:
                raise ValueError(f"The column '{data.name}' contains float values {fractions.tolist()}. All values represented by '{self.computer_representation}' must be integers.")
            min_value = data.min()
            max_value = data.max()
            min_bound, max_bound = INTEGER_BOUNDS[self.computer_representation]
            if min_value < min_bound:
                self._raise_out_of_bounds_error(min_value, data.name, 'minimum', min_bound, max_bound)
            if max_value > max_bound:
                self._raise_out_of_bounds_error(max_value, data.name, 'maximum', min_bound, max_bound)

    def _fit(self, data):
        """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit.
        """
        self._validate_values_within_bounds(data)
        self._dtype = data.dtype
        if self.enforce_min_max_values:
            self._min_value = data.min()
            self._max_value = data.max()
        if self.learn_rounding_scheme:
            self._rounding_digits = self._learn_rounding_digits(data)
        self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
        self.null_transformer.fit(data)

    def _transform(self, data):
        """Transform numerical data.

        Integer values are replaced by their float equivalent. Non null float values
        are left unmodified.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        self._validate_values_within_bounds(data)
        data = data.astype(np.float64)
        return self.null_transformer.transform(data)

    def _reverse_transform(self, data):
        """Convert data back into the original format.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        if not isinstance(data, np.ndarray):
            data = data.to_numpy()
        if self.missing_value_replacement is not None:
            data = self.null_transformer.reverse_transform(data)
        if self.enforce_min_max_values:
            data = data.clip(self._min_value, self._max_value)
        elif self.computer_representation != 'Float':
            min_bound, max_bound = INTEGER_BOUNDS[self.computer_representation]
            data = data.clip(min_bound, max_bound)
        is_integer = np.dtype(self._dtype).kind == 'i'
        if self.learn_rounding_scheme or is_integer:
            data = data.round(self._rounding_digits or 0)
        if pd.isna(data).any() and is_integer:
            return data
        return data.astype(self._dtype)

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

def is_composition_identity(self):
    """Return whether composition of transform and reverse transform produces the input data.

        Returns:
            bool:
                Whether or not transforming and then reverse transforming returns the input data.
        """
    if self.null_transformer and (not self.null_transformer.models_missing_values()):
        return False
    return self.COMPOSITION_IS_IDENTITY

@staticmethod
def _learn_rounding_digits(data):
    data = np.array(data)
    roundable_data = data[~(np.isinf(data) | pd.isna(data))]
    if (roundable_data % 1 != 0).any():
        if (roundable_data == roundable_data.round(MAX_DECIMALS)).all():
            for decimal in range(MAX_DECIMALS + 1):
                if (roundable_data == roundable_data.round(decimal)).all():
                    return decimal
    return None

def _validate_values_within_bounds(self, data):
    if self.computer_representation != 'Float':
        fractions = data[~data.isna() & data % 1 != 0]
        if not fractions.empty:
            raise ValueError(f"The column '{data.name}' contains float values {fractions.tolist()}. All values represented by '{self.computer_representation}' must be integers.")
        min_value = data.min()
        max_value = data.max()
        min_bound, max_bound = INTEGER_BOUNDS[self.computer_representation]
        if min_value < min_bound:
            self._raise_out_of_bounds_error(min_value, data.name, 'minimum', min_bound, max_bound)
        if max_value > max_bound:
            self._raise_out_of_bounds_error(max_value, data.name, 'maximum', min_bound, max_bound)

def _fit(self, data):
    """Fit the transformer to the data.

        Args:
            data (pandas.Series):
                Data to fit.
        """
    self._validate_values_within_bounds(data)
    self._dtype = data.dtype
    if self.enforce_min_max_values:
        self._min_value = data.min()
        self._max_value = data.max()
    if self.learn_rounding_scheme:
        self._rounding_digits = self._learn_rounding_digits(data)
    self.null_transformer = NullTransformer(self.missing_value_replacement, self.model_missing_values)
    self.null_transformer.fit(data)

def _transform(self, data):
    """Transform numerical data.

        Integer values are replaced by their float equivalent. Non null float values
        are left unmodified.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
    self._validate_values_within_bounds(data)
    data = data.astype(np.float64)
    return self.null_transformer.transform(data)

def _reverse_transform(self, data):
    """Convert data back into the original format.

        Args:
            data (pd.Series or numpy.ndarray):
                Data to transform.

        Returns:
            numpy.ndarray
        """
    if not isinstance(data, np.ndarray):
        data = data.to_numpy()
    if self.missing_value_replacement is not None:
        data = self.null_transformer.reverse_transform(data)
    if self.enforce_min_max_values:
        data = data.clip(self._min_value, self._max_value)
    elif self.computer_representation != 'Float':
        min_bound, max_bound = INTEGER_BOUNDS[self.computer_representation]
        data = data.clip(min_bound, max_bound)
    is_integer = np.dtype(self._dtype).kind == 'i'
    if self.learn_rounding_scheme or is_integer:
        data = data.round(self._rounding_digits or 0)
    if pd.isna(data).any() and is_integer:
        return data
    return data.astype(self._dtype)

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

def _copula_transform(self, data):
    cdf = self._univariate.cdf(data)
    return scipy.stats.norm.ppf(cdf.clip(0 + EPSILON, 1 - EPSILON))

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

def _find_divider(self, transformed):
    self.divider = 1
    multipliers = [10] * 9 + [60, 60, 24]
    for multiplier in multipliers:
        candidate = self.divider * multiplier
        if (transformed % candidate).any():
            break
        self.divider = candidate

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

def _get_dataset_sizes(sdtype):
    """Get a list of (fit_size, transform_size) for each dataset generator.

    Based on the sdtype of the dataset generator, return the list of
    sizes to run performance tests on. Each element in this list is a tuple
    of (fit_size, transform_size).

    Args:
        sdtype (str):
            The type of data that the generator returns.

    Returns:
        sizes (list[tuple]):
            A list of (fit_size, transform_size) configs to run tests on.
    """
    sizes = [(s, s) for s in DATASET_SIZES]
    if sdtype == 'categorical':
        sizes = [(s, max(s, 1000)) for s in DATASET_SIZES if s <= 10000]
    return sizes

class RandomIntegerNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array of random integers with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(RandomIntegerGenerator.generate(num_rows).astype(float))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 5e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 1e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(RandomIntegerGenerator.generate(num_rows).astype(float))

class RandomStringNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array of random strings with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(RandomStringGenerator.generate(num_rows).astype('O'))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 1e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(RandomStringGenerator.generate(num_rows).astype('O'))

class RandomMixedGenerator(CategoricalGenerator):
    """Generator that creates an array of random mixed types.

    Mixed types include: int, float, bool, string, datetime.
    """

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        cat_size = 5
        categories = np.hstack([cat.astype('O') for cat in [RandomGapDatetimeGenerator.generate(cat_size), np.random.randint(0, 100, cat_size), np.random.uniform(0, 100, cat_size), np.arange(cat_size).astype(str), np.array([True, False])]])
        return np.random.choice(a=categories, size=num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 1e-05, 'memory': 2000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    cat_size = 5
    categories = np.hstack([cat.astype('O') for cat in [RandomGapDatetimeGenerator.generate(cat_size), np.random.randint(0, 100, cat_size), np.random.uniform(0, 100, cat_size), np.arange(cat_size).astype(str), np.array([True, False])]])
    return np.random.choice(a=categories, size=num_rows)

class SingleIntegerNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array with a single integer with some nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(SingleIntegerGenerator.generate(num_rows).astype(float))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 3e-05, 'memory': 400.0}, 'reverse_transform': {'time': 1e-05, 'memory': 500.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(SingleIntegerGenerator.generate(num_rows).astype(float))

class SingleStringNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array of a single string with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(SingleStringGenerator.generate(num_rows).astype('O'))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 400.0}, 'transform': {'time': 3e-05, 'memory': 400.0}, 'reverse_transform': {'time': 1e-05, 'memory': 500.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(SingleStringGenerator.generate(num_rows).astype('O'))

class UniqueIntegerGenerator(CategoricalGenerator):
    """Generator that creates an array of unique integers."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return np.arange(num_rows)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 2000.0}, 'transform': {'time': 0.0003, 'memory': 500000.0}, 'reverse_transform': {'time': 0.0004, 'memory': 1000000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return np.arange(num_rows)

class UniqueIntegerNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array of unique integers with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(UniqueIntegerGenerator.generate(num_rows))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 1000.0}, 'transform': {'time': 0.0002, 'memory': 1000000.0}, 'reverse_transform': {'time': 0.0002, 'memory': 1000000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(UniqueIntegerGenerator.generate(num_rows))

class UniqueStringGenerator(CategoricalGenerator):
    """Generator that creates an array of unique strings."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return np.arange(num_rows).astype(str)

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 2000.0}, 'transform': {'time': 0.0002, 'memory': 500000.0}, 'reverse_transform': {'time': 0.0004, 'memory': 1000000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return np.arange(num_rows).astype(str)

class UniqueStringNaNsGenerator(CategoricalGenerator):
    """Generator that creates an array of unique strings with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(UniqueStringGenerator.generate(num_rows).astype('O'))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 2e-05, 'memory': 1000.0}, 'transform': {'time': 0.0005, 'memory': 1000000.0}, 'reverse_transform': {'time': 0.0002, 'memory': 1000000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(UniqueStringGenerator.generate(num_rows).astype('O'))

class RandomStringNaNsGenerator(PIIGenerator):
    """Generator that creates an array of random strings with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(RandomStringGenerator.generate(num_rows).astype('O'))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 2e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(RandomStringGenerator.generate(num_rows).astype('O'))

class RandomIntegerNaNsGenerator(NumericalGenerator):
    """Generator that creates an array of random integers with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(RandomIntegerGenerator.generate(num_rows).astype(float))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 2500.0}, 'transform': {'time': 4e-05, 'memory': 400.0}, 'reverse_transform': {'time': 2e-05, 'memory': 300.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(RandomIntegerGenerator.generate(num_rows).astype(float))

class ConstantIntegerNaNsGenerator(NumericalGenerator):
    """Generator that creates a constant array with a random integer with some nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(ConstantIntegerGenerator.generate(num_rows).astype(float))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 600.0}, 'transform': {'time': 3e-05, 'memory': 400.0}, 'reverse_transform': {'time': 2e-05, 'memory': 300.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(ConstantIntegerGenerator.generate(num_rows).astype(float))

class AlmostConstantIntegerNaNsGenerator(NumericalGenerator):
    """Generator that creates an array with 2 only values, one of them repeated, and NaNs."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        ii32 = np.iinfo(np.int32)
        values = np.random.randint(ii32.min, ii32.max, size=2)
        additional_values = np.full(num_rows - 2, values[1]).astype(float)
        array = np.concatenate([values, add_nans(additional_values)])
        np.random.shuffle(array)
        return array

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 2500.0}, 'transform': {'time': 3e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 2e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    ii32 = np.iinfo(np.int32)
    values = np.random.randint(ii32.min, ii32.max, size=2)
    additional_values = np.full(num_rows - 2, values[1]).astype(float)
    array = np.concatenate([values, add_nans(additional_values)])
    np.random.shuffle(array)
    return array

class NormalNaNsGenerator(NumericalGenerator):
    """Generator that creates an array of normally distributed float values, with NaNs."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(NormalGenerator.generate(num_rows))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 2500.0}, 'transform': {'time': 4e-05, 'memory': 400.0}, 'reverse_transform': {'time': 5e-05, 'memory': 300.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(NormalGenerator.generate(num_rows))

class BigNormalNaNsGenerator(NumericalGenerator):
    """Generator that creates an array of normally distributed float values, with NaNs."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(BigNormalGenerator.generate(num_rows))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 0.001, 'memory': 2500.0}, 'transform': {'time': 3e-05, 'memory': 400.0}, 'reverse_transform': {'time': 2e-05, 'memory': 300.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(BigNormalGenerator.generate(num_rows))

class RandomStringNaNsGenerator(RegexGeneratorGenerator):
    """Generator that creates an array of random strings with nans."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        return add_nans(RandomStringGenerator.generate(num_rows).astype('O'))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 1e-05, 'memory': 400.0}, 'transform': {'time': 1e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 2e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    return add_nans(RandomStringGenerator.generate(num_rows).astype('O'))

class RandomGapDatetimeNaNsGenerator(DatetimeGenerator):
    """Generator that creates dates with random gaps and NaNs."""

    @staticmethod
    def generate(num_rows):
        """Generate a ``num_rows`` number of rows."""
        dates = RandomGapDatetimeGenerator.generate(num_rows)
        return add_nans(dates.astype('O'))

    @staticmethod
    def get_performance_thresholds():
        """Return the expected threseholds."""
        return {'fit': {'time': 5e-05, 'memory': 500.0}, 'transform': {'time': 5e-05, 'memory': 1000.0}, 'reverse_transform': {'time': 5e-05, 'memory': 1000.0}}

@staticmethod
def generate(num_rows):
    """Generate a ``num_rows`` number of rows."""
    dates = RandomGapDatetimeGenerator.generate(num_rows)
    return add_nans(dates.astype('O'))

def decorated(self, X, *args, **kwargs):
    if isinstance(X, pd.DataFrame):
        W = X.to_numpy()
    else:
        W = X
    if not len(W):
        raise ValueError('Your dataset is empty.')
    if not (np.issubdtype(W.dtype, np.floating) or np.issubdtype(W.dtype, np.integer)):
        raise ValueError('There are non-numerical values in your data.')
    if np.isnan(W).any().any():
        raise ValueError('There are nan values in your data.')
    return function(self, X, *args, **kwargs)

def bisect(f, xmin, xmax, tol=1e-08, maxiter=50):
    """Bisection method for finding roots.

    This method implements a simple vectorized routine for identifying
    the root (of a monotonically increasing function) given a bracketing
    interval.

    Arguments:
        f (Callable):
            A function which takes as input a vector x and returns a
            vector with the same number of dimensions.
        xmin (np.ndarray):
            The minimum value for x such that f(x) <= 0.
        xmax (np.ndarray):
            The maximum value for x such that f(x) >= 0.

    Returns:
        numpy.ndarray:
            The value of x such that f(x) is close to 0.
    """
    assert (f(xmin) <= 0.0).all()
    assert (f(xmax) >= 0.0).all()
    for _ in range(maxiter):
        guess = (xmin + xmax) / 2.0
        fguess = f(guess)
        xmin[fguess <= 0] = guess[fguess <= 0]
        xmax[fguess >= 0] = guess[fguess >= 0]
        if (xmax - xmin).max() < tol:
            break
    return (xmin + xmax) / 2.0

def chandrupatla(f, xmin, xmax, eps_m=None, eps_a=None, maxiter=50):
    """Chandrupatla's algorithm.

    This is adapted from [1] which implements Chandrupatla's algorithm [2]
    which starts from a bracketing interval and, conditionally, swaps between
    bisection and inverse quadratic interpolation.

    [1] https://github.com/scipy/scipy/issues/7242#issuecomment-290548427
    [2] https://books.google.com/books?id=cC-8BAAAQBAJ&pg=PA95

    Arguments:
        f (Callable):
            A function which takes as input a vector x and returns a
            vector with the same number of dimensions.
        xmin (np.ndarray):
            The minimum value for x such that f(x) <= 0.
        xmax (np.ndarray):
            The maximum value for x such that f(x) >= 0.

    Returns:
        numpy.ndarray:
            The value of x such that f(x) is close to 0.
    """
    a = xmax
    b = xmin
    fa = f(a)
    fb = f(b)
    shape = np.shape(fa)
    assert shape == np.shape(fb)
    fc = fa
    c = a
    assert (np.sign(fa) * np.sign(fb) <= 0).all()
    t = 0.5
    iqi = np.zeros(shape, dtype=bool)
    eps = np.finfo(float).eps
    if eps_m is None:
        eps_m = eps
    if eps_a is None:
        eps_a = 2 * eps
    iterations = 0
    terminate = False
    while maxiter > 0:
        maxiter -= 1
        xt = np.clip(a + t * (b - a), xmin, xmax)
        ft = f(xt)
        samesign = np.sign(ft) == np.sign(fa)
        c = np.choose(samesign, [b, a])
        b = np.choose(samesign, [a, b])
        fc = np.choose(samesign, [fb, fa])
        fb = np.choose(samesign, [fa, fb])
        a = xt
        fa = ft
        fa_is_smaller = np.abs(fa) < np.abs(fb)
        xm = np.choose(fa_is_smaller, [b, a])
        fm = np.choose(fa_is_smaller, [fb, fa])
        tol = 2 * eps_m * np.abs(xm) + eps_a
        tlim = tol / np.abs(b - c)
        terminate = np.logical_or(terminate, np.logical_or(fm == 0, tlim > 0.5))
        if np.all(terminate):
            break
        iterations += 1 - terminate
        xi = (a - b) / (c - b)
        phi = (fa - fb) / (fc - fb)
        iqi = np.logical_and(phi ** 2 < xi, (1 - phi) ** 2 < 1 - xi)
        if not shape:
            if iqi:
                eq1 = fa / (fb - fa) * fc / (fb - fc)
                eq2 = (c - a) / (b - a) * fa / (fc - fa) * fb / (fc - fb)
                t = eq1 + eq2
            else:
                t = 0.5
        else:
            t = np.full(shape, 0.5)
            a2, b2, c2, fa2, fb2, fc2 = (a[iqi], b[iqi], c[iqi], fa[iqi], fb[iqi], fc[iqi])
            t[iqi] = fa2 / (fb2 - fa2) * fc2 / (fb2 - fc2) + (c2 - a2) / (b2 - a2) * fa2 / (fc2 - fa2) * fb2 / (fc2 - fb2)
        t = np.minimum(1 - tlim, np.maximum(tlim, t))
    return xm

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

def _fit(self, X):
    loc = np.min(X)
    scale = np.max(X) - loc
    a, b, loc, scale = beta.fit(X, loc=loc, scale=scale)
    self._params = {'loc': loc, 'scale': scale, 'a': a, 'b': b}

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

def _get_bounds(self):
    X = self._params['dataset']
    lower = np.min(X) - 5 * np.std(X)
    upper = np.max(X) + 5 * np.std(X)
    return (lower, upper)

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

def _fit(self, X):
    self._params = {'loc': np.mean(X), 'scale': np.std(X)}

class UniformUnivariate(ScipyModel):
    """Uniform univariate model."""
    PARAMETRIC = ParametricType.PARAMETRIC
    BOUNDED = BoundedType.BOUNDED
    MODEL_CLASS = uniform

    def _fit_constant(self, X):
        self._params = {'loc': np.min(X), 'scale': np.max(X) - np.min(X)}

    def _fit(self, X):
        self._params = {'loc': np.min(X), 'scale': np.max(X) - np.min(X)}

    def _is_constant(self):
        return self._params['scale'] == 0

    def _extract_constant(self):
        return self._params['loc']

def _fit_constant(self, X):
    self._params = {'loc': np.min(X), 'scale': np.max(X) - np.min(X)}

def _fit(self, X):
    self._params = {'loc': np.min(X), 'scale': np.max(X) - np.min(X)}

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

def get_likelihood(self, uni_matrix):
    """Compute likelihood of the vine."""
    num_tree = len(self.trees)
    values = np.empty([1, num_tree])
    for i in range(num_tree):
        value, new_uni_matrix = self.trees[i].get_likelihood(uni_matrix)
        uni_matrix = new_uni_matrix
        values[0, i] = value
    return np.sum(values)

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

class Independence(Bivariate):
    """This class represent the copula for two independent variables."""
    copula_type = CopulaTypes.INDEPENDENCE

    def fit(self, X):
        """Fit the copula to the given data.

        Args:
            X (numpy.array): Probabilites in a matrix shaped (n, 2)

        Returns:
            None

        """

    def generator(self, t):
        """Compute the generator function for the Copula.

        The generator function is a function f(t), such that an archimedian copula can be
        defined as

        C(u1, ..., uN) = f(f^-1(u1), ..., f^-1(uN)).

        Args:
            t(numpy.array)

        Returns:
            np.array

        """
        return np.log(t)

    def probability_density(self, X):
        """Compute the probability density for the independence copula."""
        return np.all((0.0 <= X) & (X <= 1.0), axis=1).astype(float)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution of the independence bivariate copula is the product.

        Args:
            X(numpy.array): Matrix of shape (n,2), whose values are in [0, 1]

        Returns:
            numpy.array: Cumulative distribution values of given input.

        """
        U, V = split_matrix(X)
        return U * V

    def partial_derivative(self, X):
        """Compute the conditional probability of one event conditiones to the other.

        In the case of the independence copula, due to C(u,v) = u*v, we have that
        F(u|v) = dC/du = v.

        Args:
            X()

        """
        _, V = split_matrix(X)
        return V

    def percent_point(self, y, V):
        """Compute the inverse of conditional cumulative distribution :math:`F(u|v)^-1`.

        Args:
            y: `np.ndarray` value of :math:`F(u|v)`.
            v: `np.ndarray` given value of v.

        """
        self.check_fit()
        return y

def probability_density(self, X):
    """Compute the probability density for the independence copula."""
    return np.all((0.0 <= X) & (X <= 1.0), axis=1).astype(float)

def _compute_empirical(X):
    """Compute empirical distribution.

    Args:
        X(numpy.array): Shape (n,2); Datapoints to compute the empirical(frequentist) copula.

    Return:
        tuple(list):

    """
    z_left = []
    z_right = []
    L = []
    R = []
    U, V = split_matrix(X)
    N = len(U)
    base = np.linspace(EPSILON, 1.0 - EPSILON, COMPUTE_EMPIRICAL_STEPS)
    for k in range(COMPUTE_EMPIRICAL_STEPS):
        left = sum(np.logical_and(U <= base[k], V <= base[k])) / N
        right = sum(np.logical_and(U >= base[k], V >= base[k])) / N
        if left > 0:
            z_left.append(base[k])
            L.append(left / base[k] ** 2)
        if right > 0:
            z_right.append(base[k])
            R.append(right / (1 - z_right[k]) ** 2)
    return (z_left, L, z_right, R)

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

def generate_cond_from_condition_column_info(self, condition_info, batch):
    """Generate the condition vector."""
    vec = np.zeros((batch, self._n_categories), dtype='float32')
    id_ = self._discrete_column_matrix_st[condition_info['discrete_column_id']]
    id_ += condition_info['value_id']
    vec[:, id_] = 1
    return vec

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

def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
    length = self.df.shape[0]
    if offset >= length:
        return None
    limit = limit or length
    return self.df.iloc[offset:min(offset + limit, length)]

def generator() -> Generator[pd.DataFrame, None, None]:
    length = self.df.shape[0]
    if offset < length:
        current = offset
        while current < length:
            yield self.df.iloc[current:min(current + chunksize, length)]
            current += chunksize

def chunk_generator() -> Generator[pd.DataFrame, None, None]:
    for chunk in dataloader.iter():
        for d in data_processors:
            chunk = d.convert(chunk)
        assert not chunk.isna().any().any()
        assert not chunk.isnull().any().any()
        yield chunk

@pytest.fixture
def test_empty_data(raw_data: pd.DataFrame):
    raw_data['age'] = raw_data['age'].astype(float)
    raw_data['fnlwgt'] = raw_data['fnlwgt'].astype(float)
    raw_data['age'].values[:] = None
    raw_data['fnlwgt'].values[:] = None
    yield raw_data

def has_nan(df):
    """
    This function checks if there are any NaN values in the given DataFrame.

    Parameters:
    df (pandas.DataFrame): The DataFrame to check for NaN values.

    Returns:
    bool: True if there is any NaN value in the DataFrame, False otherwise.
    """
    return df.isnull().values.any()

def generate_uniform_credit_code():

    def generate():
        code = ''
        code += random.choice(string.digits + 'AHJNPQRTUWXY')
        code += random.choice(string.digits + 'AHJNPQRTUWXY')
        code += ''.join(random.choices(string.digits, k=6))
        code += ''.join(random.choices(string.digits, k=9))
        code += random.choice(string.digits + 'AHJNPQRTUWXY')
        return code
    code = generate()
    return code

@pytest.fixture
def test_empty_data(raw_data: pd.DataFrame):
    raw_data['age'] = raw_data['age'].astype(float)
    raw_data['fnlwgt'] = raw_data['fnlwgt'].astype(float)
    raw_data['age'].values[:] = None
    raw_data['fnlwgt'].values[:] = None
    yield raw_data

@pytest.fixture
def mi_sim_instance():
    return MISim()

def test_MISim_discrete(test_data_category, mi_sim_instance):
    metadata = {'role1': 'category', 'role2': 'category'}
    col_src = 'role1'
    col_tar = 'role2'
    result = mi_sim_instance.calculate(test_data_category[col_src], test_data_category[col_tar], metadata)
    result1 = mi_sim_instance.calculate(test_data_category[col_src], test_data_category[col_src], metadata)
    result2 = mi_sim_instance.calculate(test_data_category[col_tar], test_data_category[col_src], metadata)
    assert result >= 0
    assert result <= 1
    assert result1 == 1
    assert round(result2, 9) == round(result, 9)

def test_MISim_continuous(test_data_num, mi_sim_instance):
    metadata = {'feature_x': 'numerical', 'feature_y': 'numerical'}
    col_src = 'feature_x'
    col_tar = 'feature_y'
    result = mi_sim_instance.calculate(test_data_num[col_src], test_data_num[col_tar], metadata)
    result1 = mi_sim_instance.calculate(test_data_num[col_src], test_data_num[col_src], metadata)
    result2 = mi_sim_instance.calculate(test_data_num[col_tar], test_data_num[col_src], metadata)
    assert result >= 0
    assert result <= 1
    assert np.isclose(result1, 1, atol=1e-09)
    assert np.isclose(result, result2, atol=1e-09)

def test_MISim_time(test_data_time, mi_sim_instance):
    metadata = {'time_x': 'datetime', 'time_y': 'datetime'}
    col_src = 'time_x'
    col_tar = 'time_y'
    result = mi_sim_instance.calculate(test_data_time[col_src], test_data_time[col_tar], metadata)
    result1 = mi_sim_instance.calculate(test_data_time[col_src], test_data_time[col_src], metadata)
    result2 = mi_sim_instance.calculate(test_data_time[col_tar], test_data_time[col_src], metadata)
    assert result >= 0
    assert result <= 1
    assert np.isclose(result1, 1, atol=1e-09)
    assert np.isclose(result, result2, atol=1e-09)

def test_jsd_discrete(dummy_data, test_data, jsd_instance):
    cols = ['role']
    result = jsd_instance.calculate(dummy_data, test_data, cols, discrete=True)
    result1 = jsd_instance.calculate(dummy_data, dummy_data, cols, discrete=True)
    result2 = jsd_instance.calculate(test_data, dummy_data, cols, discrete=True)
    assert result >= 0
    assert result <= 1
    assert np.isclose(result1, 0, atol=1e-09)
    assert np.isclose(result, result2, atol=1e-09)

def test_jsd_continuous(dummy_data, test_data, jsd_instance):
    cols = ['feature_x']
    result = jsd_instance.calculate(dummy_data, test_data, cols, discrete=False)
    result1 = jsd_instance.calculate(dummy_data, dummy_data, cols, discrete=False)
    assert result >= 0
    assert result <= 1
    assert np.isclose(result1, 0, atol=1e-09)

