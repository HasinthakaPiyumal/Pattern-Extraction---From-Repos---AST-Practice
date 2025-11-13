# Cluster 34

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

