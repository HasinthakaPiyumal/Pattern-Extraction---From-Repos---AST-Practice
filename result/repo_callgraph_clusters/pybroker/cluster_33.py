# Cluster 33

class ModelLoader(ModelSource):
    """Loads a pre-trained model.

    Args:
        name: Name of model.
        load_fn: ``Callable[[symbol: str, train_start_date: datetime,
            train_end_date: datetime, ...], DataFrame]`` used to load and
            return a pre-trained model. This is expected to
            return either a trained model instance, or a tuple containing a
            trained model instance and a :class:`Iterable` of column names to
            to be used as input for the model when making predictions.
        indicator_names: :class:`Iterable` of names of
            :class:`pybroker.indicator.Indicator`\\ s used as features of the
            model.
        input_data_fn: :class:`Callable[[DataFrame], DataFrame]` for
            preprocessing input data passed to the model when making
            predictions. If set, ``input_data_fn`` will be called with a
            :class:`pandas.DataFrame` containing all test data.
        predict_fn: :class:`Callable[[Model, DataFrame], ndarray]` that
            overrides calling the model's default ``predict`` function. If set,
            ``predict_fn`` will be called with the trained model and a
            :class:`pandas.DataFrame` containing all test data.
        kwargs: ``dict`` of kwargs to pass to ``load_fn``.
    """

    def __init__(self, name: str, load_fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
        super().__init__(name, indicator_names, input_data_fn, predict_fn, kwargs)
        self._load_fn = functools.partial(load_fn, **kwargs)

    def __call__(self, symbol: str, train_start_date: datetime, train_end_date: datetime) -> Union[Any, tuple[Any, Iterable[str]]]:
        """Loads pre-trained model.

        Args:
            symbol: Ticker symbol for loading the pre-trained model.
            train_start_date: Start date of training window.
            train_end_date: End date of training window.

        Returns:
            Pre-trained model.
        """
        return self._load_fn(symbol, train_start_date, train_end_date)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'ModelLoader({self.name!r}, {self._kwargs})'

def __repr__(self):
    return self.__str__()

class ModelTrainer(ModelSource):
    """Trains a model.

    Args:
        name: Name of model.
        train_fn: ``Callable[[symbol: str, train_data: DataFrame,
            test_data: DataFrame, ...], DataFrame]`` used to train and return a
            model. This is expected to return either a trained model instance,
            or a tuple containing a trained model instance and a
            :class:`Iterable` of column names to to be used as input for the
            model when making predictions.
        indicator_names: :class:`Iterable` of names of
            :class:`pybroker.indicator.Indicator`\\ s used as features of the
            model.
        input_data_fn: :class:`Callable[[DataFrame], DataFrame]` for
            preprocessing input data passed to the model when making
            predictions. If set, ``input_data_fn`` will be called with a
            :class:`pandas.DataFrame` containing all test data.
        predict_fn: :class:`Callable[[Model, DataFrame], ndarray]` that
            overrides calling the model's default ``predict`` function. If set,
            ``predict_fn`` will be called with the trained model and a
            :class:`pandas.DataFrame` containing all test data.
        kwargs: ``dict`` of kwargs to pass to ``train_fn``.
    """

    def __init__(self, name: str, train_fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
        super().__init__(name, indicator_names, input_data_fn, predict_fn, kwargs)
        self._train_fn = functools.partial(train_fn, **kwargs)

    def __call__(self, symbol: str, train_data: pd.DataFrame, test_data: pd.DataFrame) -> Union[Any, tuple[Any, Iterable[str]]]:
        """Trains model.

        Args:
            symbol: Ticker symbol of model (models are trained per symbol).
            train_data: Train data.
            test_data: Test data.

        Returns:
            Trained model.
        """
        return self._train_fn(symbol, train_data, test_data)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'ModelTrainer({self.name!r}, {self._kwargs})'

def __repr__(self):
    return self.__str__()

class Indicator:
    """Class representing an indicator.

    Args:
        name: Name of indicator.
        fn: :class:`Callable` used to compute the series of indicator values.
        kwargs: ``dict`` of kwargs to pass to ``fn``.
    """

    def __init__(self, name: str, fn: Callable[..., NDArray[np.float64]], kwargs: dict[str, Any]):
        self.name = name
        self._fn = functools.partial(fn, **kwargs)
        self._kwargs = kwargs

    def relative_entropy(self, data: Union[BarData, pd.DataFrame]) -> float:
        """Generates indicator data with ``data`` and computes its relative
        `entropy
        <https://en.wikipedia.org/wiki/Entropy_(information_theory)>`_.
        """
        return relative_entropy(self(data).values)

    def iqr(self, data: Union[BarData, pd.DataFrame]) -> float:
        """Generates indicator data with ``data`` and computes its
        `interquartile range (IQR)
        <https://en.wikipedia.org/wiki/Interquartile_range>`_.
        """
        return iqr(self(data).values)

    def __call__(self, data: Union[BarData, pd.DataFrame]) -> pd.Series:
        """Computes indicator values."""
        if isinstance(data, pd.DataFrame):
            data = _to_bar_data(data)
        values = self._fn(data)
        if isinstance(values, pd.Series):
            values = values.to_numpy()
        if len(values.shape) != 1:
            raise ValueError(f'Indicator {self.name} must return a one-dimensional array.')
        return pd.Series(values, index=data.date)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Indicator({self.name!r}, {self._kwargs})'

def __repr__(self):
    return self.__str__()

