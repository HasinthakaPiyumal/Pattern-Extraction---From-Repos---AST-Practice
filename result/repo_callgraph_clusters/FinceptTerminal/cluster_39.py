# Cluster 39

class DataValidator:
    """
    Comprehensive data validation and quality control system.
    """

    def __init__(self, strict_mode: bool=False):
        """
        Initialize data validator.

        Args:
            strict_mode: If True, raises exceptions for quality issues
        """
        self.strict_mode = strict_mode
        self.validation_rules = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default validation rules."""
        self.validation_rules = {'min_observations': 2, 'max_missing_ratio': 0.1, 'outlier_std_threshold': 3.0, 'min_numeric_ratio': 0.95, 'date_format_patterns': ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S']}

    def validate_financial_data(self, data: Union[pd.DataFrame, pd.Series, np.ndarray, List], data_type: str='general', data_name: str='data') -> Tuple[Any, DataQualityReport]:
        """
        Comprehensive validation of financial data.

        Args:
            data: Input data to validate
            data_type: Type of financial data ('returns', 'prices', 'rates', 'general')
            data_name: Name for reporting purposes

        Returns:
            Tuple of (cleaned_data, quality_report)
        """
        report = DataQualityReport(data_name)
        try:
            if isinstance(data, (list, tuple)):
                data = pd.Series(data)
            elif isinstance(data, np.ndarray):
                if data.ndim == 1:
                    data = pd.Series(data)
                else:
                    data = pd.DataFrame(data)
            cleaned_data = self._validate_structure(data, report)
            if data_type == 'returns':
                cleaned_data = self._validate_returns(cleaned_data, report)
            elif data_type == 'prices':
                cleaned_data = self._validate_prices(cleaned_data, report)
            elif data_type == 'rates':
                cleaned_data = self._validate_rates(cleaned_data, report)
            self._check_data_quality(cleaned_data, report)
            self._generate_recommendations(cleaned_data, report)
            return (cleaned_data, report)
        except Exception as e:
            report.add_issue('validation_error', f'Validation failed: {str(e)}', 'critical')
            if self.strict_mode:
                raise
            return (data, report)

    def _validate_structure(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate basic data structure."""
        if len(data) == 0:
            report.add_issue('empty_data', 'Dataset is empty', 'critical')
            if self.strict_mode:
                raise ValueError('Dataset is empty')
        if len(data) < self.validation_rules['min_observations']:
            report.add_issue('insufficient_data', f'Only {len(data)} observations, minimum {self.validation_rules['min_observations']} required', 'high')
        if isinstance(data, (pd.DataFrame, pd.Series)):
            if data.index.duplicated().any():
                report.add_warning('duplicate_index', 'Duplicate index values found')
                data = data.loc[~data.index.duplicated(keep='first')]
        report.statistics['total_observations'] = len(data)
        return data

    def _validate_returns(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate return data specifically."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
        else:
            numeric_data = data
        if isinstance(numeric_data, pd.DataFrame):
            for col in numeric_data.columns:
                extreme_returns = numeric_data[col].abs() > 1.0
                if extreme_returns.any():
                    count = extreme_returns.sum()
                    report.add_warning('extreme_returns', f'Column {col}: {count} returns > 100% found')
        else:
            extreme_returns = numeric_data.abs() > 1.0
            if extreme_returns.any():
                count = extreme_returns.sum()
                report.add_warning('extreme_returns', f'{count} returns > 100% found')
        self._check_return_patterns(numeric_data, report)
        return data

    def _validate_prices(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate price data specifically."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
        else:
            numeric_data = data
        if isinstance(numeric_data, pd.DataFrame):
            for col in numeric_data.columns:
                negative_prices = numeric_data[col] <= 0
                if negative_prices.any():
                    count = negative_prices.sum()
                    report.add_issue('negative_prices', f'Column {col}: {count} non-positive prices found', 'high')
        else:
            negative_prices = numeric_data <= 0
            if negative_prices.any():
                count = negative_prices.sum()
                report.add_issue('negative_prices', f'{count} non-positive prices found', 'high')
        self._check_price_jumps(numeric_data, report)
        return data

    def _validate_rates(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport) -> Union[pd.DataFrame, pd.Series]:
        """Validate interest rate data specifically."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
        else:
            numeric_data = data
        if isinstance(numeric_data, pd.DataFrame):
            for col in numeric_data.columns:
                high_rates = numeric_data[col] > 1.0
                if high_rates.any():
                    count = high_rates.sum()
                    report.add_warning('high_rates', f'Column {col}: {count} rates > 100% found')
        else:
            high_rates = numeric_data > 1.0
            if high_rates.any():
                count = high_rates.sum()
                report.add_warning('high_rates', f'{count} rates > 100% found')
        return data

    def _check_data_quality(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Perform general data quality checks."""
        self._analyze_missing_data(data, report)
        self._detect_outliers(data, report)
        self._check_data_types(data, report)
        self._generate_statistics(data, report)

    def _analyze_missing_data(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Analyze missing data patterns."""
        if isinstance(data, pd.DataFrame):
            total_cells = data.size
            missing_cells = data.isna().sum().sum()
            missing_ratio = missing_cells / total_cells if total_cells > 0 else 0
            missing_by_column = data.isna().sum()
            for col, missing_count in missing_by_column.items():
                if missing_count > 0:
                    col_ratio = missing_count / len(data)
                    if col_ratio > self.validation_rules['max_missing_ratio']:
                        report.add_issue('high_missing_data', f'Column {col}: {col_ratio:.1%} missing data', 'medium')
        else:
            missing_count = data.isna().sum()
            missing_ratio = missing_count / len(data) if len(data) > 0 else 0
            if missing_ratio > self.validation_rules['max_missing_ratio']:
                report.add_issue('high_missing_data', f'{missing_ratio:.1%} missing data', 'medium')
        report.statistics['missing_data_ratio'] = round(missing_ratio, 4)

    def _detect_outliers(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Detect statistical outliers."""

        def detect_outliers_series(series: pd.Series, name: str=''):
            if not pd.api.types.is_numeric_dtype(series):
                return
            clean_series = series.dropna()
            if len(clean_series) < 3:
                return
            z_scores = np.abs(stats.zscore(clean_series))
            outliers_zscore = z_scores > self.validation_rules['outlier_std_threshold']
            Q1 = clean_series.quantile(0.25)
            Q3 = clean_series.quantile(0.75)
            IQR = Q3 - Q1
            outliers_iqr = (clean_series < Q1 - 1.5 * IQR) | (clean_series > Q3 + 1.5 * IQR)
            outlier_count_z = outliers_zscore.sum()
            outlier_count_iqr = outliers_iqr.sum()
            if outlier_count_z > 0:
                report.add_warning('outliers_zscore', f'{name}Z-score outliers detected: {outlier_count_z}')
            if outlier_count_iqr > 0:
                report.add_warning('outliers_iqr', f'{name}IQR outliers detected: {outlier_count_iqr}')
        if isinstance(data, pd.DataFrame):
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                detect_outliers_series(data[col], f'Column {col}: ')
        else:
            detect_outliers_series(data)

    def _check_data_types(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Check data type consistency."""
        if isinstance(data, pd.DataFrame):
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            total_cols = len(data.columns)
            numeric_ratio = len(numeric_cols) / total_cols if total_cols > 0 else 0
            if numeric_ratio < self.validation_rules['min_numeric_ratio']:
                report.add_warning('low_numeric_ratio', f'Only {numeric_ratio:.1%} of columns are numeric')
            for col in data.columns:
                if data[col].dtype == 'object':
                    sample = data[col].dropna().head(100)
                    if self._looks_like_numeric(sample):
                        report.add_issue('type_mismatch', f'Column {col} contains numeric data stored as text', 'medium')
                    elif self._looks_like_date(sample):
                        report.add_issue('type_mismatch', f'Column {col} contains date data stored as text', 'medium')
        report.statistics['data_types'] = data.dtypes.astype(str).to_dict() if isinstance(data, pd.DataFrame) else str(data.dtype)

    def _looks_like_numeric(self, sample: pd.Series) -> bool:
        """Check if text data looks like it should be numeric."""
        if len(sample) == 0:
            return False
        numeric_pattern = re.compile('^-?\\d*\\.?\\d+([eE][+-]?\\d+)?')
        numeric_count = sample.astype(str).str.match(numeric_pattern).sum()
        return numeric_count / len(sample) > 0.8

    def _looks_like_date(self, sample: pd.Series) -> bool:
        """Check if text data looks like it should be dates."""
        if len(sample) == 0:
            return False
        date_patterns = ['\\d{4}-\\d{2}-\\d{2}', '\\d{2}/\\d{2}/\\d{4}', '\\d{2}-\\d{2}-\\d{4}']
        for pattern in date_patterns:
            matches = sample.astype(str).str.match(pattern).sum()
            if matches / len(sample) > 0.8:
                return True
        return False

    def _generate_statistics(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Generate comprehensive statistics for the data."""
        if isinstance(data, pd.DataFrame):
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                stats_dict = {'shape': data.shape, 'numeric_columns': len(numeric_data.columns), 'total_columns': len(data.columns), 'memory_usage_mb': round(data.memory_usage(deep=True).sum() / 1024 ** 2, 2)}
                desc_stats = numeric_data.describe()
                stats_dict['summary_statistics'] = desc_stats.to_dict()
        elif pd.api.types.is_numeric_dtype(data):
            clean_data = data.dropna()
            stats_dict = {'length': len(data), 'non_null_count': len(clean_data), 'mean': float(clean_data.mean()) if len(clean_data) > 0 else None, 'std': float(clean_data.std()) if len(clean_data) > 1 else None, 'min': float(clean_data.min()) if len(clean_data) > 0 else None, 'max': float(clean_data.max()) if len(clean_data) > 0 else None, 'skewness': float(clean_data.skew()) if len(clean_data) > 2 else None, 'kurtosis': float(clean_data.kurtosis()) if len(clean_data) > 3 else None}
        else:
            stats_dict = {'length': len(data), 'non_null_count': data.notna().sum(), 'unique_values': data.nunique(), 'data_type': str(data.dtype)}
        report.statistics.update(stats_dict)

    def _check_return_patterns(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Check for suspicious patterns in return data."""

        def check_series_patterns(series: pd.Series, name: str=''):
            clean_series = series.dropna()
            if len(clean_series) < 10:
                return
            zero_count = (clean_series == 0).sum()
            zero_ratio = zero_count / len(clean_series)
            if zero_ratio > 0.1:
                report.add_warning('high_zero_returns', f'{name}High proportion of zero returns: {zero_ratio:.1%}')
            if len(clean_series) > 20:
                for window in [5, 10]:
                    if len(clean_series) >= window * 3:
                        rolling_std = clean_series.rolling(window).std()
                        low_variance_periods = (rolling_std < 0.001).sum()
                        if low_variance_periods > len(clean_series) * 0.1:
                            report.add_warning('low_variance_periods', f'{name}Detected periods with suspiciously low variance')
            if len(clean_series) > 30:
                try:
                    jb_stat, jb_pvalue = stats.jarque_bera(clean_series)
                    if jb_pvalue < 0.01:
                        report.add_warning('non_normal_returns', f'{name}Returns significantly deviate from normal distribution')
                except:
                    pass
        if isinstance(data, pd.DataFrame):
            for col in data.select_dtypes(include=[np.number]).columns:
                check_series_patterns(data[col], f'Column {col}: ')
        else:
            check_series_patterns(data)

    def _check_price_jumps(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Check for suspicious price jumps."""

        def check_series_jumps(series: pd.Series, name: str=''):
            clean_series = series.dropna()
            if len(clean_series) < 2:
                return
            price_changes = clean_series.pct_change().dropna()
            large_jumps = price_changes.abs() > 0.5
            if large_jumps.any():
                jump_count = large_jumps.sum()
                report.add_warning('large_price_jumps', f'{name}{jump_count} large price jumps (>50%) detected')
            halving = (price_changes > -0.55) & (price_changes < -0.45)
            doubling = (price_changes > 0.95) & (price_changes < 1.05)
            if halving.any() or doubling.any():
                report.add_warning('potential_splits', f'{name}Potential stock splits/reverse splits detected')
        if isinstance(data, pd.DataFrame):
            for col in data.select_dtypes(include=[np.number]).columns:
                check_series_jumps(data[col], f'Column {col}: ')
        else:
            check_series_jumps(data)

    def _generate_recommendations(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
        """Generate data improvement recommendations."""
        issue_types = [issue['type'] for issue in report.issues]
        warning_types = [warning['type'] for warning in report.warnings]
        if 'high_missing_data' in issue_types:
            report.add_recommendation('Consider using interpolation or forward-fill for missing data')
            report.add_recommendation('Investigate the source of missing data - is it systematic?')
        if 'negative_prices' in issue_types:
            report.add_recommendation('Remove or correct negative price observations')
            report.add_recommendation('Verify data source and collection methodology')
        if 'extreme_returns' in warning_types:
            report.add_recommendation('Review extreme returns - may indicate data errors or corporate actions')
            report.add_recommendation('Consider winsorizing extreme values if confirmed as outliers')
        if 'outliers_zscore' in warning_types or 'outliers_iqr' in warning_types:
            report.add_recommendation('Investigate outliers - may be valid extreme events or data errors')
            report.add_recommendation('Consider robust statistical methods that are less sensitive to outliers')
        if 'type_mismatch' in issue_types:
            report.add_recommendation('Convert text columns to appropriate data types (numeric/datetime)')
            report.add_recommendation('Standardize data formats before importing')
        if 'insufficient_data' in issue_types:
            report.add_recommendation('Collect more historical data for reliable statistical analysis')
            report.add_recommendation('Consider using higher frequency data if available')
        if len(report.recommendations) == 0:
            report.add_recommendation('Data quality appears good - proceed with analysis')

    def clean_data(self, data: Union[pd.DataFrame, pd.Series], method: str='conservative', **kwargs) -> Union[pd.DataFrame, pd.Series]:
        """
        Clean data based on validation results.

        Args:
            data: Data to clean
            method: Cleaning method ('conservative', 'aggressive', 'custom')
            **kwargs: Additional parameters for cleaning

        Returns:
            Cleaned data
        """
        cleaned_data = data.copy()
        if method == 'conservative':
            if isinstance(cleaned_data, pd.DataFrame):
                cleaned_data = cleaned_data.dropna(how='all')
                numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if 'price' in col.lower():
                        cleaned_data = cleaned_data[cleaned_data[col] > 0]
            else:
                cleaned_data = cleaned_data.dropna()
        elif method == 'aggressive':
            if isinstance(cleaned_data, pd.DataFrame):
                missing_ratio = cleaned_data.isna().mean()
                cols_to_keep = missing_ratio[missing_ratio <= 0.5].index
                cleaned_data = cleaned_data[cols_to_keep]
                numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    Q1 = cleaned_data[col].quantile(0.25)
                    Q3 = cleaned_data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    cleaned_data = cleaned_data[(cleaned_data[col] >= lower_bound) & (cleaned_data[col] <= upper_bound)]
            else:
                Q1 = cleaned_data.quantile(0.25)
                Q3 = cleaned_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                cleaned_data = cleaned_data[(cleaned_data >= lower_bound) & (cleaned_data <= upper_bound)]
        return cleaned_data

    def validate_date_range(self, dates: Union[pd.DatetimeIndex, pd.Series, List], start_date: Optional[datetime]=None, end_date: Optional[datetime]=None) -> Tuple[bool, List[str]]:
        """
        Validate date range and continuity.

        Args:
            dates: Date data to validate
            start_date: Expected start date
            end_date: Expected end date

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        try:
            if isinstance(dates, list):
                dates = pd.to_datetime(dates)
            elif isinstance(dates, pd.Series):
                dates = pd.to_datetime(dates)
            if dates.duplicated().any():
                issues.append('Duplicate dates found')
            if not dates.is_monotonic_increasing:
                issues.append('Dates are not in chronological order')
            if start_date and dates.min() < start_date:
                issues.append(f'Data starts before expected date: {start_date}')
            if end_date and dates.max() > end_date:
                issues.append(f'Data ends after expected date: {end_date}')
            if len(dates) > 1:
                date_diffs = dates.to_series().diff().dropna()
                median_diff = date_diffs.median()
                large_gaps = date_diffs > median_diff * 5
                if large_gaps.any():
                    gap_count = large_gaps.sum()
                    issues.append(f'Found {gap_count} large gaps in date sequence')
            return (len(issues) == 0, issues)
        except Exception as e:
            issues.append(f'Date validation error: {str(e)}')
            return (False, issues)

    def validate_correlation_matrix(self, corr_matrix: pd.DataFrame, tolerance: float=1e-06) -> Tuple[bool, List[str]]:
        """
        Validate correlation matrix properties.

        Args:
            corr_matrix: Correlation matrix to validate
            tolerance: Numerical tolerance for validation

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        try:
            if corr_matrix.shape[0] != corr_matrix.shape[1]:
                issues.append('Correlation matrix is not square')
                return (False, issues)
            if not np.allclose(corr_matrix.values, corr_matrix.values.T, atol=tolerance):
                issues.append('Correlation matrix is not symmetric')
            diagonal = np.diag(corr_matrix.values)
            if not np.allclose(diagonal, 1.0, atol=tolerance):
                issues.append('Diagonal elements are not equal to 1')
            if (corr_matrix.values < -1 - tolerance).any() or (corr_matrix.values > 1 + tolerance).any():
                issues.append('Correlation values outside [-1, 1] range')
            off_diagonal = corr_matrix.values[~np.eye(corr_matrix.shape[0], dtype=bool)]
            perfect_corrs = np.abs(off_diagonal) > 1 - tolerance
            if perfect_corrs.any():
                issues.append('Perfect correlations detected (may indicate data issues)')
            eigenvals = np.linalg.eigvals(corr_matrix.values)
            if (eigenvals < -tolerance).any():
                issues.append('Correlation matrix is not positive semi-definite')
            return (len(issues) == 0, issues)
        except Exception as e:
            issues.append(f'Correlation matrix validation error: {str(e)}')
            return (False, issues)

    def validate_portfolio_weights(self, weights: Union[List, np.ndarray, pd.Series], tolerance: float=1e-06) -> Tuple[bool, List[str]]:
        """
        Validate portfolio weights.

        Args:
            weights: Portfolio weights to validate
            tolerance: Numerical tolerance

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        try:
            weights = np.array(weights)
            weights_sum = np.sum(weights)
            if not np.isclose(weights_sum, 1.0, atol=tolerance):
                issues.append(f'Weights sum to {weights_sum:.6f}, not 1.0')
            if (weights < -tolerance).any():
                negative_count = (weights < -tolerance).sum()
                issues.append(f'Found {negative_count} negative weights (short positions)')
            very_small = np.abs(weights) < tolerance
            if very_small.any():
                small_count = very_small.sum()
                issues.append(f'Found {small_count} very small weights (< {tolerance})')
            return (len(issues) == 0, issues)
        except Exception as e:
            issues.append(f'Portfolio weights validation error: {str(e)}')
            return (False, issues)

def _check_data_quality(self, data: Union[pd.DataFrame, pd.Series], report: DataQualityReport):
    """Perform general data quality checks."""
    self._analyze_missing_data(data, report)
    self._detect_outliers(data, report)
    self._check_data_types(data, report)
    self._generate_statistics(data, report)

