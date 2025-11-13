# Cluster 27

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

