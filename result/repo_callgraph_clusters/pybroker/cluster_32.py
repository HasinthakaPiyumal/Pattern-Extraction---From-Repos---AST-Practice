# Cluster 32

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

