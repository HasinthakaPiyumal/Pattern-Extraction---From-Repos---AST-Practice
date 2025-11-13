# Cluster 26

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

