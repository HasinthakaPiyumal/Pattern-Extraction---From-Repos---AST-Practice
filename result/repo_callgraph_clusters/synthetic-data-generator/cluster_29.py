# Cluster 29

class SingleTableMetric:
    """SingleTableMetric

    Metrics used to evaluate the quality of single table synthetic data.
    """
    upper_bound = None
    lower_bound = None
    metric_name = None
    metadata = None

    def __init__(self, metadata: dict) -> None:
        """Initialization

        Args:
            metadata(dict): This parameter accepts a metadata description dict, which is used to describe the column description information of the table.
        """
        self.metadata = metadata
        pass

    @classmethod
    def check_input(cls, real_data: pd.DataFrame, synthetic_data: pd.DataFrame):
        """Input check for single table input.

        Args:
            real_data(pd.DataFrame): the real (original) data table.

            synthetic_data(pd.DataFrame): the synthetic (generated) data table.
        """
        if real_data is None or synthetic_data is None:
            raise TypeError('Input contains None.')
        if type(real_data) is not type(synthetic_data):
            raise TypeError('Data type of real_data and synthetic data should be the same.')
        if isinstance(real_data, pd.DataFrame):
            return (real_data, synthetic_data)
        try:
            real_data = pd.DataFrame(real_data)
            synthetic_data = pd.DataFrame(synthetic_data)
            return (real_data, synthetic_data)
        except Exception as e:
            logger.error(f'An error occurred while converting to pd.DataFrame: {e}')
        return (None, None)

    def calculate(cls, real_data: pd.DataFrame, synthetic_data: pd.DataFrame):
        """Calculate the metric value between a real table and a synthetic table.

        Args:
            real_data(pd.DataFrame): the real (original) data table.

            synthetic_data(pd.DataFrame): the synthetic (generated) data table.
        """
        raise NotImplementedError()

    @classmethod
    def check_output(raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the Mutual Information Similarity.
        """
        raise NotImplementedError()
    pass

def calculate(cls, real_data: pd.DataFrame, synthetic_data: pd.DataFrame):
    """Calculate the metric value between a real table and a synthetic table.

        Args:
            real_data(pd.DataFrame): the real (original) data table.

            synthetic_data(pd.DataFrame): the synthetic (generated) data table.
        """
    raise NotImplementedError()

@classmethod
def check_output(raw_metric_value: float):
    """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the Mutual Information Similarity.
        """
    raise NotImplementedError()

class ColumnMetric(object):
    """ColumnMetric

    Metrics used to evaluate the quality of synthetic data columns.
    """
    upper_bound = None
    lower_bound = None
    metric_name = 'Accuracy'

    def __init__(self) -> None:
        pass

    @classmethod
    def check_input(cls, real_data: pd.Series | pd.DataFrame, synthetic_data: pd.Series | pd.DataFrame):
        """Input check for column or table input.

        Args:
            real_data(pd.DataFrame or pd.Series): the real (original) data table / column.

            synthetic_data(pd.DataFrame or pd.Series): the synthetic (generated) data table / column.
        """
        if real_data is None or synthetic_data is None:
            raise TypeError('Input contains None.')
        if type(real_data) is not type(synthetic_data):
            raise TypeError('Data type of real_data and synthetic data should be the same.')
        if type(real_data) in [int, float, str]:
            raise TypeError("real_data's type must not be None, int, float or str")
        if isinstance(real_data, pd.Series) or isinstance(real_data, pd.DataFrame):
            return (real_data, synthetic_data)
        try:
            real_data = pd.Series(real_data)
            synthetic_data = pd.Series(synthetic_data)
            return (real_data, synthetic_data)
        except Exception as e:
            logger.error(f'An error occurred while converting to pd.Series: {e}')
        return (None, None)

    @classmethod
    def calculate(cls, real_data: pd.Series | pd.DataFrame, synthetic_data: pd.Series | pd.DataFrame):
        """Calculate the metric value between columns between real table and synthetic table.
        Args:
            real_data(pd.DataFrame or pd.Series): the real (original) data table / column.
            synthetic_data(pd.DataFrame or pd.Series): the synthetic (generated) data table / column.
        """
        real_data, synthetic_data = ColumnMetric.check_input(real_data, synthetic_data)
        raise NotImplementedError()

    @classmethod
    def check_output(cls, raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the JSD metric.
        """
        raise NotImplementedError()
    pass

@classmethod
def calculate(cls, real_data: pd.Series | pd.DataFrame, synthetic_data: pd.Series | pd.DataFrame):
    """Calculate the metric value between columns between real table and synthetic table.
        Args:
            real_data(pd.DataFrame or pd.Series): the real (original) data table / column.
            synthetic_data(pd.DataFrame or pd.Series): the synthetic (generated) data table / column.
        """
    real_data, synthetic_data = ColumnMetric.check_input(real_data, synthetic_data)
    raise NotImplementedError()

@classmethod
def check_output(cls, raw_metric_value: float):
    """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the JSD metric.
        """
    raise NotImplementedError()

class PairMetric(object):
    """PairMetric
    Metrics used to evaluate the quality of synthetic data columns.
    """
    upper_bound = None
    lower_bound = None
    metric_name = 'Correlation'

    def __init__(self) -> None:
        pass

    @classmethod
    def check_input(cls, src_col: pd.Series, tar_col: pd.Series, metadata: dict):
        """Input check for table input.
        Args:
            src_data(pd.Series ): the source data column.
            tar_data(pd.Series): the target data column .
            metadata(dict): The metadata that describes the data type of each column
        """
        if real_data is None or synthetic_data is None:
            raise TypeError('Input contains None.')
        tar_name = tar_col.name
        src_name = src_col.name
        if metadata[tar_name] != metadata[src_name]:
            raise TypeError('Type of Pair is Conflicting.')
        if isinstance(real_data, pd.Series):
            return (src_col, tar_col)
        try:
            src_col = pd.Series(src_col)
            tar_col = pd.Series(tar_col)
            return (src_col, tar_col)
        except Exception as e:
            logger.error(f'An error occurred while converting to pd.Series: {e}')
        return (None, None)

    @classmethod
    def calculate(cls, src_col: pd.Series, tar_col: pd.Series, metadata):
        """Calculate the metric value between pair-columns between real table and synthetic table.

        Args:
            src_data(pd.Series ): the source data column.
            tar_data(pd.Series): the target data column .
            metadata(dict): The metadata that describes the data type of each column
        """
        real_data, synthetic_data = PairMetric.check_input(src_col, tar_col)
        raise NotImplementedError()

    @classmethod
    def check_output(cls, raw_metric_value: float):
        """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the Mutual Information.
        """
        raise NotImplementedError()
    pass

@classmethod
def calculate(cls, src_col: pd.Series, tar_col: pd.Series, metadata):
    """Calculate the metric value between pair-columns between real table and synthetic table.

        Args:
            src_data(pd.Series ): the source data column.
            tar_data(pd.Series): the target data column .
            metadata(dict): The metadata that describes the data type of each column
        """
    real_data, synthetic_data = PairMetric.check_input(src_col, tar_col)
    raise NotImplementedError()

@classmethod
def check_output(cls, raw_metric_value: float):
    """Check the output value.

        Args:
            raw_metric_value (float):  the calculated raw value of the Mutual Information.
        """
    raise NotImplementedError()

class MultiTableMetric:
    """MultiTableMetric

    Metrics used to evaluate the quality of synthetic multi-table data.
    """
    upper_bound = None
    lower_bound = None
    metric_name = None
    metadata = None
    table_list = []

    def __init__(self, metadata: dict) -> None:
        """Initialization

        Args:
            metadata(dict): This parameter accepts a metadata description dict, which is used to describe the table relations and column description information for each table.
        """
        self.metadata = metadata

    @classmethod
    def check_input(cls, real_data: dict, synthetic_data: dict):
        """Format check for single table input.

        The `real_data` and `synthetic_data` should be dict, which contains tables (in pd.DataFrame).

        Args:
            real_data(dict): the real (original) data table.

            synthetic_data(dict): the synthetic (generated) data table.
        """
        if real_data is None or synthetic_data is None:
            raise TypeError('Input contains None.')
        if type(real_data) is not type(synthetic_data):
            raise TypeError('Data type of real_data and synthetic data should be the same.')
        if isinstance(real_data, dict) and len(real_data.keys()) > 0 and (len(synthetic_data.keys()) > 0):
            return (real_data, synthetic_data)
        logger.error('An error occurred while checking the input.')
        return (None, None)

    def calculate(self, real_data: dict, synthetic_data: dict):
        """Calculate the metric value between real tables and synthetic tables.

        Args:

            real_data(dict): the real (original) data table.

            synthetic_data(dict): the synthetic (generated) data table.
        """
        raise NotImplementedError()

    @classmethod
    def check_output(raw_metric_value: float):
        """Check the output value.
        Args:

            raw_metric_value (float):  the calculated raw value of the Mutual Information Similarity.
        """
        raise NotImplementedError()
    pass

def calculate(self, real_data: dict, synthetic_data: dict):
    """Calculate the metric value between real tables and synthetic tables.

        Args:

            real_data(dict): the real (original) data table.

            synthetic_data(dict): the synthetic (generated) data table.
        """
    raise NotImplementedError()

@classmethod
def check_output(raw_metric_value: float):
    """Check the output value.
        Args:

            raw_metric_value (float):  the calculated raw value of the Mutual Information Similarity.
        """
    raise NotImplementedError()

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

def _fit(self, columns_data):
    """Fit the transformer to the data.

        Args:
            columns_data (pandas.DataFrame or pandas.Series):
                Data to transform.
        """
    raise NotImplementedError()

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

@staticmethod
@abstractmethod
def get_performance_thresholds():
    """Return the expected threseholds."""
    raise NotImplementedError()

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

def _set_params(self, params):
    """Set the parameters of this univariate.

        Must be implemented in all the subclasses.

        Args:
            dict:
                Parameters to recreate this instance.
        """
    raise NotImplementedError()

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

def _fit(self, X):
    """Fit the model to a non-constant random variable.

        Must be implemented in all the subclasses.

        Arguments:
            X (numpy.ndarray):
                Values of the random variable. It must have shape (n, 1).
        """
    raise NotImplementedError()

