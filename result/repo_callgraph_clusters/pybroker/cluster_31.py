# Cluster 31

class BaseContext:
    """Base context class.

    Attributes:
        config: :class:`pybroker.config.StrategyConfig`.
    """

    def __init__(self, config: StrategyConfig, portfolio: Portfolio, col_scope: ColumnScope, ind_scope: IndicatorScope, input_scope: ModelInputScope, pred_scope: PredictionScope, pending_order_scope: PendingOrderScope, models: Mapping[ModelSymbol, TrainedModel], sym_end_index: Mapping[str, int]):
        self.config = config
        self._portfolio = portfolio
        self._col_scope = col_scope
        self._ind_scope = ind_scope
        self._input_scope = input_scope
        self._pred_scope = pred_scope
        self._models = models
        self._sym_end_index = sym_end_index
        self._pending_order_scope = pending_order_scope

    @property
    def total_equity(self) -> Decimal:
        """Total equity currently held in the
        :class:`pybroker.portfolio.Portfolio`.
        """
        return self._portfolio.equity

    @property
    def cash(self) -> Decimal:
        """Total cash currently held in the
        :class:`pybroker.portfolio.Portfolio`.
        """
        return self._portfolio.cash

    @property
    def total_margin(self) -> Decimal:
        """Total amount of margin currently held in the
        :class:`pybroker.portfolio.Portfolio`.
        """
        return self._portfolio.margin

    @property
    def total_market_value(self) -> Decimal:
        """Total market value currently held in the
        :class:`pybroker.portfolio.Portfolio`. The market value is defined as
        the amount of equity held in cash and long positions added together
        with the unrealized PnL of all open short positions.
        """
        return self._portfolio.market_value

    @property
    def win_rate(self) -> Decimal:
        """Running win rate of trades."""
        return self._portfolio.win_rate

    @property
    def loss_rate(self) -> Decimal:
        """Running loss rate of trades."""
        return self._portfolio.loss_rate

    def orders(self) -> Iterator[Order]:
        """:class:`Iterator` of all :class:`pybroker.portfolio.Order`\\ s that
        have been placed and filled.
        """
        for order in self._portfolio.orders:
            yield order

    def pending_orders(self, symbol: Optional[str]=None) -> Iterator[PendingOrder]:
        for order in self._pending_order_scope.orders(symbol):
            yield order

    def trades(self) -> Iterator[Trade]:
        """:class:`Iterator` of all :class:`pybroker.portfolio.Trade`\\ s that
        have been completed.
        """
        for trade in self._portfolio.trades:
            yield trade

    def pos(self, symbol: str, pos_type: Literal['long', 'short']) -> Optional[Position]:
        """Retrieves a current long or short
        :class:`pybroker.portfolio.Position` for a ``symbol``.

        Args:
            symbol: Ticker symbol of the position to return.
            pos_type: Specifies whether to return a ``long`` or ``short``
                position.

        Returns:
            :class:`pybroker.portfolio.Position` if one exists, otherwise
            ``None``.
        """
        self._verify_pos_type(pos_type)
        if pos_type == 'long' and symbol in self._portfolio.long_positions:
            return self._portfolio.long_positions[symbol]
        elif pos_type == 'short' and symbol in self._portfolio.short_positions:
            return self._portfolio.short_positions[symbol]
        return None

    def positions(self, symbol: Optional[str]=None, pos_type: Optional[Literal['long', 'short']]=None) -> Iterator[Position]:
        """Retrieves all current positions.

        Args:
            symbol: Ticker symbol used to filter positions. If ``None``,
                positions for all symbols are returned. Defaults to ``None``.
            pos_type: Type of positions to return. If ``None``, both ``long``
                and ``short`` positions are returned.

        Returns:
            :class:`Iterator` of currently held
            :class:`pybroker.portfolio.Position` \\s.
        """
        if pos_type is not None:
            self._verify_pos_type(pos_type)
        if symbol is None:
            if pos_type != 'short':
                for pos in self._portfolio.long_positions.values():
                    yield pos
            if pos_type != 'long':
                for pos in self._portfolio.short_positions.values():
                    yield pos
        else:
            if pos_type != 'short' and symbol in self._portfolio.long_positions:
                yield self._portfolio.long_positions[symbol]
            if pos_type != 'long' and symbol in self._portfolio.short_positions:
                yield self._portfolio.short_positions[symbol]

    def long_positions(self, symbol: Optional[str]=None) -> Iterator[Position]:
        """Retrieves all current long positions.

        Args:
            symbol: Ticker symbol used to filter positions. If ``None``,
                long positions for all symbols are returned. Defaults to
                ``None``.

        Returns:
            :class:`Iterator` of currently held long
            :class:`pybroker.portfolio.Position` \\s.
        """
        return self.positions(symbol, 'long')

    def short_positions(self, symbol: Optional[str]=None) -> Iterator[Position]:
        """Retrieves all current short positions.

        Args:
            symbol: Ticker symbol used to filter positions. If ``None``,
                short positions for all symbols are returned. Defaults to
                ``None``.

        Returns:
            :class:`Iterator` of currently held short
            :class:`pybroker.portfolio.Position` \\s.
        """
        return self.positions(symbol, 'short')

    def _verify_pos_type(self, pos_type: str):
        if pos_type != 'short' and pos_type != 'long':
            raise ValueError(f'Unknown pos_type: {pos_type!r}.')

    def calc_target_shares(self, target_size: float, price: float, cash: Optional[float]=None) -> Union[Decimal, int]:
        """Calculates the number of shares given a ``target_size`` allocation
        and share ``price``.

        Args:
            target_size: Proportion of cash used to calculate the number of
                shares, where the max ``target_size`` is ``1``. For example, a
                ``target_size`` of ``0.1`` would represent 10% of cash.
            price: Share price used to calculate the number of shares.
            cash: Cash used to calculate the number of shares. If
                ``None``, then the :class:`pybroker.portfolio.Portfolio` equity
                is used to calculate the number of shares.

        Returns:
            Number of shares given ``target_size`` and share ``price``. If
            :attr:`pybroker.config.StrategyConfig.enable_fractional_shares` is
            ``True``, then a Decimal is returned.
        """
        shares = (to_decimal(cash) if cash is not None else self._portfolio.equity) * to_decimal(target_size) / to_decimal(price)
        if self.config.enable_fractional_shares:
            return shares.max(0)
        return max(int(shares), 0)

    def model(self, name: str, symbol: str) -> Any:
        """Returns a trained model.

        Args:
            name: Name used to identify the model that was registered with
                :meth:`pybroker.model.model`.
            symbol: Ticker symbol of the data that was used to train the model.

        Returns:
            Instance of the trained model.
        """
        model_sym = ModelSymbol(name, symbol)
        if model_sym not in self._models:
            raise ValueError(f'Model {name!r} not found for {symbol}.')
        return self._models[model_sym].instance

    def indicator(self, name: str, symbol: str) -> NDArray[np.float64]:
        """Returns indicator data.

        Args:
            name: Name used to identify the indicator that was registered with
                :meth:`pybroker.indicator.indicator`.
            symbol: Ticker symbol that was used to generate the indicator data.

        Returns:
            :class:`numpy.ndarray` of indicator data for all bars up to the
            current one, sorted in ascending chronological order.
        """
        end_index = self._sym_end_index[symbol]
        return self._ind_scope.fetch(symbol, name, end_index)

    def input(self, model_name: str, symbol: str) -> pd.DataFrame:
        """Returns model input data for making predictions.

        Args:
            model_name: Name of the model for the input data.
            symbol: Ticker symbol of the model for the input data.

        Returns:
            :class:`pandas.DataFrame` containing the input data, where each row
            represents a bar in the sequence up to the current bar. The rows
            are sorted in ascending chronological order.
        """
        end_index = self._sym_end_index[symbol]
        return self._input_scope.fetch(symbol, model_name, end_index)

    def preds(self, model_name: str, symbol: str) -> NDArray:
        """Returns model predictions.

        Args:
            model_name: Name of the model that made the predictions.
            symbol: Ticker symbol of the model that made the predictions.

        Returns:
            :class:`numpy.ndarray` containing the sequence of model predictions
            up to the current bar. Sorted in ascending chronological order.
        """
        end_index = self._sym_end_index[symbol]
        return self._pred_scope.fetch(symbol, model_name, end_index)

def long_positions(self, symbol: Optional[str]=None) -> Iterator[Position]:
    """Retrieves all current long positions.

        Args:
            symbol: Ticker symbol used to filter positions. If ``None``,
                long positions for all symbols are returned. Defaults to
                ``None``.

        Returns:
            :class:`Iterator` of currently held long
            :class:`pybroker.portfolio.Position` \\s.
        """
    return self.positions(symbol, 'long')

def short_positions(self, symbol: Optional[str]=None) -> Iterator[Position]:
    """Retrieves all current short positions.

        Args:
            symbol: Ticker symbol used to filter positions. If ``None``,
                short positions for all symbols are returned. Defaults to
                ``None``.

        Returns:
            :class:`Iterator` of currently held short
            :class:`pybroker.portfolio.Position` \\s.
        """
    return self.positions(symbol, 'short')

def _between(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    if df.empty:
        return df
    return df[(df[DataCol.DATE.value].dt.tz_localize(None) >= start_date) & (df[DataCol.DATE.value].dt.tz_localize(None) <= end_date)]

class Alpaca(DataSource):
    """Retrieves stock data from `Alpaca <https://alpaca.markets/>`_."""
    __EST: Final = 'US/Eastern'

    def __init__(self, api_key: str, api_secret: str):
        super().__init__()
        self._api = alpaca_stock.StockHistoricalDataClient(api_key, api_secret)

    def query(self, symbols: Union[str, Iterable[str]], start_date: Union[str, datetime], end_date: Union[str, datetime], timeframe: Optional[str]='1d', adjust: Optional[Any]=None) -> pd.DataFrame:
        _parse_alpaca_timeframe(timeframe)
        return super().query(symbols, start_date, end_date, timeframe, adjust)

    def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[Any]) -> pd.DataFrame:
        """:meta private:"""
        amount, unit = _parse_alpaca_timeframe(timeframe)
        adj_enum = None
        if adjust is not None:
            for member in Adjustment:
                if member.value == adjust:
                    adj_enum = member
                    break
            if adj_enum is None:
                raise ValueError(f'Unknown adjustment: {adjust}.')
        request = StockBarsRequest(symbol_or_symbols=list(symbols), start=start_date, end=end_date, timeframe=TimeFrame(amount, unit), limit=None, adjustment=adj_enum, feed=None)
        df = self._api.get_stock_bars(request).df
        if df.columns.empty:
            return pd.DataFrame(columns=[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value, DataCol.VWAP.value])
        if df.empty:
            return df
        df = df.reset_index()
        df.rename(columns={'timestamp': DataCol.DATE.value}, inplace=True)
        df = df[[col.value for col in DataCol]]
        df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
        df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(self.__EST)
        return df

def query(self, symbols: Union[str, Iterable[str]], start_date: Union[str, datetime], end_date: Union[str, datetime], timeframe: Optional[str]='1d', adjust: Optional[Any]=None) -> pd.DataFrame:
    _parse_alpaca_timeframe(timeframe)
    return super().query(symbols, start_date, end_date, timeframe, adjust)

def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[Any]) -> pd.DataFrame:
    """:meta private:"""
    amount, unit = _parse_alpaca_timeframe(timeframe)
    adj_enum = None
    if adjust is not None:
        for member in Adjustment:
            if member.value == adjust:
                adj_enum = member
                break
        if adj_enum is None:
            raise ValueError(f'Unknown adjustment: {adjust}.')
    request = StockBarsRequest(symbol_or_symbols=list(symbols), start=start_date, end=end_date, timeframe=TimeFrame(amount, unit), limit=None, adjustment=adj_enum, feed=None)
    df = self._api.get_stock_bars(request).df
    if df.columns.empty:
        return pd.DataFrame(columns=[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value, DataCol.VWAP.value])
    if df.empty:
        return df
    df = df.reset_index()
    df.rename(columns={'timestamp': DataCol.DATE.value}, inplace=True)
    df = df[[col.value for col in DataCol]]
    df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
    df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(self.__EST)
    return df

class AlpacaCrypto(DataSource):
    """Retrieves crypto data from `Alpaca <https://alpaca.markets/>`_.

    Args:
        api_key: Alpaca API key.
        api_secret: Alpaca API secret.
    """
    TRADE_COUNT: Final = 'trade_count'
    COLUMNS: Final = (DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value, DataCol.VWAP.value, TRADE_COUNT)
    __EST: Final = 'US/Eastern'

    def __init__(self, api_key: str, api_secret: str):
        super().__init__()
        self._scope.register_custom_cols(self.TRADE_COUNT)
        self._api = alpaca_crypto.CryptoHistoricalDataClient(api_key, api_secret)

    def query(self, symbols: Union[str, Iterable[str]], start_date: Union[str, datetime], end_date: Union[str, datetime], timeframe: Optional[str]='1d', _adjust: Optional[str]=None) -> pd.DataFrame:
        _parse_alpaca_timeframe(timeframe)
        return super().query(symbols, start_date, end_date, timeframe, _adjust)

    def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], _adjust: Optional[str]) -> pd.DataFrame:
        """:meta private:"""
        amount, unit = _parse_alpaca_timeframe(timeframe)
        request = CryptoBarsRequest(symbol_or_symbols=list(symbols), start=start_date, end=end_date, timeframe=TimeFrame(amount, unit), limit=None)
        df = self._api.get_crypto_bars(request).df
        if df.columns.empty:
            return pd.DataFrame(columns=self.COLUMNS)
        if df.empty:
            return df
        df = df.reset_index()
        df.rename(columns={'timestamp': DataCol.DATE.value}, inplace=True)
        df = df[[col for col in self.COLUMNS]]
        df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
        df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(self.__EST)
        return df

def query(self, symbols: Union[str, Iterable[str]], start_date: Union[str, datetime], end_date: Union[str, datetime], timeframe: Optional[str]='1d', _adjust: Optional[str]=None) -> pd.DataFrame:
    _parse_alpaca_timeframe(timeframe)
    return super().query(symbols, start_date, end_date, timeframe, _adjust)

def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], _adjust: Optional[str]) -> pd.DataFrame:
    """:meta private:"""
    amount, unit = _parse_alpaca_timeframe(timeframe)
    request = CryptoBarsRequest(symbol_or_symbols=list(symbols), start=start_date, end=end_date, timeframe=TimeFrame(amount, unit), limit=None)
    df = self._api.get_crypto_bars(request).df
    if df.columns.empty:
        return pd.DataFrame(columns=self.COLUMNS)
    if df.empty:
        return df
    df = df.reset_index()
    df.rename(columns={'timestamp': DataCol.DATE.value}, inplace=True)
    df = df[[col for col in self.COLUMNS]]
    df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
    df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(self.__EST)
    return df

def enable_caches(namespace, cache_dir: Optional[str]=None):
    """Enables all caches.

    Args:
        namespace: Namespace shared by cached data.
        cache_dir: Directory used to store cached data.
    """
    enable_data_source_cache(namespace, cache_dir)
    enable_indicator_cache(namespace, cache_dir)
    enable_model_cache(namespace, cache_dir)

def disable_caches():
    """Disables all caches."""
    disable_data_source_cache()
    disable_indicator_cache()
    disable_model_cache()

def clear_caches():
    """Clears cached data from all caches. :meth:`enable_caches` must be
    called first before clearing."""
    clear_data_source_cache()
    clear_indicator_cache()
    clear_model_cache()

def test_bar_data_get_custom_data():
    date = np.full(10, np.datetime64('2022-02-02'))
    open_ = np.full(10, 1)
    high = np.full(10, 2)
    low = np.full(10, 3)
    close = np.full(10, 4)
    foo = np.full(10, 5)
    bar = np.full(10, 6)
    custom_data = {'foo': foo, 'bar': bar}
    bar_data = BarData(date=date, open=open_, high=high, low=low, close=close, volume=None, vwap=None, **custom_data)
    assert bar_data.foo is foo
    assert bar_data.bar is bar

@pytest.fixture(params=[True, False])
def disable_parallel(request):
    return request.param

@pytest.mark.usefixtures('setup_teardown')
class TestIndicator:

    def test_call_with_kwargs(self, hhv_ind, data_source_df):
        data = hhv_ind(data_source_df)
        assert len(data) == len(data_source_df['date'])
        assert isinstance(data.index[0], pd.Timestamp)

    def test_call_when_invalid_shape_then_error(self, data_source_df):

        def invalid_shape(_data):
            return np.array([[1, 2, 3], [4, 5, 6]])
        ind_invalid_shape = indicator('invalid_shape', invalid_shape)
        with pytest.raises(ValueError, match=re.escape('Indicator invalid_shape must return a one-dimensional array.')):
            ind_invalid_shape(data_source_df)

    def test_iqr(self, hhv_ind, data_source_df):
        assert isinstance(hhv_ind.iqr(data_source_df), float)

    def test_relative_entropy(self, hhv_ind, data_source_df):
        assert isinstance(hhv_ind.relative_entropy(data_source_df), float)

    def test_repr(self, hhv_ind):
        assert repr(hhv_ind) == "Indicator('hhv', {'n': 5})"

def test_call_with_kwargs(self, hhv_ind, data_source_df):
    data = hhv_ind(data_source_df)
    assert len(data) == len(data_source_df['date'])
    assert isinstance(data.index[0], pd.Timestamp)

@pytest.fixture(params=[10, None])
def end_index(request):
    return request.param

@pytest.fixture()
def mock_logger(scope):
    logger, scope.logger = (scope.logger, Mock())
    yield scope.logger
    scope.logger = logger

class TestModelInputScope:

    def test_fetch(self, input_scope, model_source, symbol, data_source_df, end_index):
        df = data_source_df[data_source_df['symbol'] == symbol]
        result = input_scope.fetch(symbol, model_source.name, end_index)
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == set(model_source.indicators)
        assert result.shape[0] == df.shape[0] if end_index is None else end_index

    def test_fetch_when_input_fn(self, scope, indicators, input_scope, symbol, data_source_df, end_index, trained_model):
        scope.custom_data_cols = set()
        expected_cols = {'hhv', 'llv', 'sumv'}

        def input_fn(df):
            assert set(df.columns) == expected_cols
            df['foo'] = np.ones(len(df['hhv']))
            return df
        model_source = model(trained_model.name, lambda *_: trained_model, indicators, input_data_fn=input_fn)
        df = data_source_df[data_source_df['symbol'] == symbol]
        result = input_scope.fetch(symbol, model_source.name, end_index)
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == {'foo'} | expected_cols
        assert result.shape[0] == df.shape[0] if end_index is None else end_index

    def test_fetch_when_cached(self, input_scope, model_source, symbol, data_source_df, end_index):
        input_scope.fetch(symbol, model_source.name, end_index)
        result = input_scope.fetch(symbol, model_source.name, end_index)
        df = data_source_df[data_source_df['symbol'] == symbol]
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == set(model_source.indicators)
        assert result.shape[0] == df.shape[0] if end_index is None else end_index

    @pytest.mark.parametrize('sym, name, expected_msg', [('FOO', MODEL_NAME, 'Symbol not found: FOO'), ('SPY', 'foo', "Model 'foo' not found.")])
    def test_fetch_when_not_found_then_error(self, input_scope, sym, name, expected_msg):
        with pytest.raises(ValueError, match=re.escape(expected_msg)):
            input_scope.fetch(sym, name)

def input_fn(df):
    assert set(df.columns) == expected_cols
    df['foo'] = np.ones(len(df['hhv']))
    return df

@pytest.fixture(params=[200, 202])
def dates_length(request):
    return request.param

@pytest.fixture(params=[1, 2, 3])
def lookahead(request):
    return request.param

@pytest.fixture()
def dates():
    dates = pd.date_range(start='1/1/2018', end='1/1/2019').tolist()
    return sorted(dates + dates.copy())

@pytest.fixture(params=list(range(1, 6)))
def windows(request):
    return request.param

@pytest.fixture(params=np.arange(0, 1.05, 0.05).tolist())
def train_size(request):
    return request.param

@pytest.fixture(params=[True, False])
def shuffle(request):
    return request.param

class TestWalkforwardMixin:

    def test_walkforward_split_1(self, dates, dates_length, windows, lookahead, train_size, shuffle):
        self._verify_windows(dates, dates_length, windows, lookahead, train_size, shuffle)

    @pytest.mark.parametrize('dates_length, windows, lookahead', [(22, 5, 1), (20, 5, 1), (22, 2, 2), (20, 2, 2)])
    def test_walkforward_split_2(self, dates, dates_length, windows, lookahead, train_size, shuffle):
        self._verify_windows(dates, dates_length, windows, lookahead, train_size, shuffle)

    def _verify_windows(self, dates, dates_length, windows, lookahead, train_size, shuffle):
        df = self._data_frame(dates, dates_length)
        mixin = WalkforwardMixin()
        results = list(mixin.walkforward_split(df, windows, lookahead, train_size, shuffle))
        dates = sorted(dates)
        assert len(results) == windows
        for i, (train_idx, test_idx) in enumerate(results):
            assert len(dates) - (len(train_idx) + len(test_idx) * windows) >= 0
            assert not set(train_idx) & set(test_idx)
            assert len(train_idx) or len(test_idx)
            if len(train_idx) and len(test_idx):
                train_end_index = sorted(train_idx)[-1] + lookahead * 2
                test_start_index = sorted(test_idx)[0]
                assert dates[train_end_index] == dates[test_start_index]
                assert dates[train_end_index - 2] != dates[test_start_index]
            if train_size == 0.5:
                assert len(train_idx) == len(test_idx)
            if len(test_idx) and i == len(results) - 1:
                assert dates[dates_length - 1] == dates[sorted(test_idx)[-1]]

    @pytest.mark.parametrize('dates_length, windows, lookahead, train_size', [(11, -1, 1, 0.5), (11, 5, 0, 0.5), (11, 5, 1, -1), (0, 2, 1, 0.5), (12, 7, 2, 0.5), (1, 1, 2, 0.5), (1, 1, 10, 0.5), (1, 2, 1, 0.5), (10, 2, 11, 0.5)])
    def test_walkforward_split_when_invalid_params_then_error(self, dates, dates_length, windows, lookahead, train_size):
        df = self._data_frame(dates, dates_length)
        mixin = WalkforwardMixin()
        with pytest.raises(ValueError):
            list(mixin.walkforward_split(df, windows, lookahead, train_size))

    def _data_frame(self, dates, dates_length):
        dates = dates[:dates_length]
        return pd.DataFrame({'date': dates, 'close': np.random.rand(len(dates))})

def _verify_windows(self, dates, dates_length, windows, lookahead, train_size, shuffle):
    df = self._data_frame(dates, dates_length)
    mixin = WalkforwardMixin()
    results = list(mixin.walkforward_split(df, windows, lookahead, train_size, shuffle))
    dates = sorted(dates)
    assert len(results) == windows
    for i, (train_idx, test_idx) in enumerate(results):
        assert len(dates) - (len(train_idx) + len(test_idx) * windows) >= 0
        assert not set(train_idx) & set(test_idx)
        assert len(train_idx) or len(test_idx)
        if len(train_idx) and len(test_idx):
            train_end_index = sorted(train_idx)[-1] + lookahead * 2
            test_start_index = sorted(test_idx)[0]
            assert dates[train_end_index] == dates[test_start_index]
            assert dates[train_end_index - 2] != dates[test_start_index]
        if train_size == 0.5:
            assert len(train_idx) == len(test_idx)
        if len(test_idx) and i == len(results) - 1:
            assert dates[dates_length - 1] == dates[sorted(test_idx)[-1]]

@pytest.mark.parametrize('dates_length, windows, lookahead, train_size', [(11, -1, 1, 0.5), (11, 5, 0, 0.5), (11, 5, 1, -1), (0, 2, 1, 0.5), (12, 7, 2, 0.5), (1, 1, 2, 0.5), (1, 1, 10, 0.5), (1, 2, 1, 0.5), (10, 2, 11, 0.5)])
def test_walkforward_split_when_invalid_params_then_error(self, dates, dates_length, windows, lookahead, train_size):
    df = self._data_frame(dates, dates_length)
    mixin = WalkforwardMixin()
    with pytest.raises(ValueError):
        list(mixin.walkforward_split(df, windows, lookahead, train_size))

@pytest.fixture()
def executions_train_only():
    return [{'fn': None, 'symbols': ['AAPL', 'MSFT'], 'models': None, 'indicators': None}, {'fn': None, 'symbols': 'SPY', 'models': None, 'indicators': None}, {'fn': None, 'symbols': 'QQQ', 'models': None, 'indicators': None}]

@pytest.fixture()
def executions_only(executions_train_only):

    def exec_fn_1(ctx):
        if ctx.long_pos():
            ctx.sell_all_shares()
        else:
            ctx.buy_shares = 100

    def exec_fn_2(ctx):
        ctx.sell_fill_price = PriceType.AVERAGE
        ctx.sell_shares = 10
        ctx.hold_bars = 1
    executions_train_only[0]['fn'] = exec_fn_1
    executions_train_only[1]['fn'] = exec_fn_2
    executions_train_only[2]['fn'] = exec_fn_2
    return executions_train_only

@pytest.fixture()
def executions_with_indicators(executions_only, hhv_ind, llv_ind):

    def exec_fn_1(ctx):
        assert len(ctx.indicator(hhv_ind.name))

    def exec_fn_2(ctx):
        assert len(ctx.indicator(hhv_ind.name))
        assert len(ctx.indicator(llv_ind.name))
    executions_only[0]['indicators'] = hhv_ind
    executions_only[0]['fn'] = exec_fn_1
    executions_only[1]['indicators'] = (hhv_ind, llv_ind)
    executions_only[1]['fn'] = exec_fn_2
    return executions_only

@pytest.fixture()
def exec_model_source(scope, data_source_df, indicators):
    return model(MODEL_NAME, lambda sym, *_: FakeModel(sym, np.full(data_source_df[data_source_df['symbol'] == sym].shape[0], 100)), indicators, pretrained=False)

@pytest.fixture()
def executions_with_models(executions_only, exec_model_source):

    def exec_fn(ctx):
        assert isinstance(ctx.model(exec_model_source.name), FakeModel)
    executions_only[0]['models'] = exec_model_source
    executions_only[0]['fn'] = exec_fn
    return executions_only

@pytest.fixture()
def executions_with_models_and_indicators(executions_only, exec_model_source, hhv_ind, llv_ind):

    def exec_fn_1(ctx):
        assert len(ctx.indicator(llv_ind.name))
    executions_only[0]['indicators'] = llv_ind
    executions_only[0]['fn'] = exec_fn_1

    def exec_fn_2(ctx):
        assert len(ctx.indicator(hhv_ind.name))
        assert isinstance(ctx.model(exec_model_source.name), FakeModel)
    executions_only[1]['indicators'] = hhv_ind
    executions_only[1]['models'] = exec_model_source
    executions_only[1]['fn'] = exec_fn_2
    return executions_only

@pytest.fixture(params=[(None, None), ('2020/06/01', None), (None, '2021-10-31'), ('1/1/2021', '2021-09-01')])
def date_range(request):
    return request.param

@pytest.fixture(params=[True, False])
def calc_bootstrap(request):
    return request.param

@pytest.fixture(params=[True, False])
def disable_parallel(request):
    return request.param

@pytest.fixture(params=[None, 'weds', ('mon', 'fri')])
def days(request):
    return request.param

@pytest.fixture(params=[None, ('10:00', '1:00')])
def between_time(request):
    return request.param

class FakeDataSource(DataSource):

    def _fetch_data(self, symbols, start_date, end_date, timeframe, adjustment):
        return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/daily_1.pkl'))

def _fetch_data(self, symbols, start_date, end_date, timeframe, adjustment):
    return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/daily_1.pkl'))

@pytest.fixture()
def alpaca_df():
    df = pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/daily_1.pkl'))
    df['date'] = df['date'].dt.tz_localize('US/Eastern')
    return df.assign(vwap=1)[ALPACA_COLS]

@pytest.fixture()
def alpaca_crypto_df():
    df = pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/daily_1.pkl'))
    df['date'] = df['date'].dt.tz_localize('US/Eastern')
    return df.assign(vwap=1, trade_count=1)[ALPACA_CRYPTO_COLS]

@pytest.fixture()
def bars_df(alpaca_df):
    return alpaca_df.rename(columns={'date': 'timestamp'})

@pytest.fixture()
def crypto_bars_df(alpaca_crypto_df):
    return alpaca_crypto_df.rename(columns={'date': 'timestamp'})

@pytest.fixture()
def yfinance_df():
    return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/yfinance.pkl'))

@pytest.fixture()
def yfinance_single_df():
    return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/yfinance_single.pkl'))

@pytest.fixture()
def symbols(alpaca_df):
    return list(alpaca_df['symbol'].unique())

@pytest.fixture()
def mock_cache(scope):
    with mock.patch.object(scope, 'data_source_cache') as cache, mock.patch.object(cache, 'get', return_value=None):
        yield cache

@pytest.fixture()
def mock_alpaca():
    with mock.patch('alpaca.data.historical.stock.StockHistoricalDataClient') as client:
        yield client

@pytest.fixture()
def mock_alpaca_crypto():
    with mock.patch('alpaca.data.historical.crypto.CryptoHistoricalDataClient') as client:
        yield client

@pytest.fixture()
def data_source_df():
    return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/daily_1.pkl'))

@pytest.fixture()
def symbols(data_source_df):
    return list(data_source_df['symbol'].unique())

@pytest.fixture()
def symbol(symbols):
    return symbols[0]

@pytest.fixture()
def dates(data_source_df):
    return list(data_source_df['date'].unique())

@pytest.fixture()
def indicators(hhv_ind, llv_ind, sumv_ind):
    return [hhv_ind, llv_ind, sumv_ind]

@pytest.fixture()
def ind_name(ind_names):
    return ind_names[0]

@pytest.fixture()
def ind_df(data_source_df, hhv_ind, llv_ind, sumv_ind):
    return pd.DataFrame({hhv_ind.name: hhv_ind(data_source_df), llv_ind.name: llv_ind(data_source_df), sumv_ind.name: sumv_ind(data_source_df)})

@pytest.fixture(params=[True, False])
def model_source(scope, data_source_df, indicators, request):
    return model(MODEL_NAME, lambda sym, *_: FakeModel(sym, np.full(data_source_df[data_source_df['symbol'] == sym].shape[0], 100)), indicators, pretrained=request.param)

@pytest.fixture()
def preds(symbols, data_source_df):
    return {sym: np.random.random(data_source_df[data_source_df['symbol'] == sym].shape[0]) for sym in symbols}

@pytest.fixture()
def pred_scope(trained_models, input_scope):
    return PredictionScope(trained_models, input_scope)

@pytest.fixture()
def setup_enabled_model_cache(tmp_path):
    enable_model_cache('test', tmp_path)
    yield
    clear_model_cache()
    disable_model_cache()

@pytest.fixture(params=[True, False])
def setup_model_cache(tmp_path, request):
    if request.param:
        enable_model_cache('test', tmp_path)
    else:
        disable_model_cache()
    yield
    if request.param:
        clear_model_cache()
    disable_model_cache()

@pytest.fixture()
def setup_enabled_ds_cache(tmp_path):
    enable_data_source_cache('test', tmp_path)
    yield
    clear_data_source_cache()
    disable_data_source_cache()

@pytest.fixture(params=[True, False])
def setup_ds_cache(tmp_path, request):
    if request.param:
        enable_data_source_cache('test', tmp_path)
    else:
        disable_data_source_cache()
    yield
    if request.param:
        clear_data_source_cache()
    disable_data_source_cache()

@pytest.fixture()
def setup_enabled_ind_cache(tmp_path):
    enable_indicator_cache('test', tmp_path)
    yield
    clear_indicator_cache()
    disable_indicator_cache()

@pytest.fixture(params=[True, False])
def setup_ind_cache(tmp_path, request):
    if request.param:
        enable_indicator_cache('test', tmp_path)
    else:
        disable_indicator_cache()
    yield
    if request.param:
        clear_indicator_cache()
    disable_indicator_cache()

@pytest.fixture()
def portfolio():
    return Portfolio(100000)

@pytest.fixture()
def end_index():
    return 100

@pytest.fixture()
def sym_end_index(symbols, end_index):
    return {sym: end_index for sym in symbols}

@pytest.fixture()
def session():
    return {'foo': 1, 'bar': 2}

@pytest.fixture()
def foreign(symbols):
    return list(symbols)[-1]

@pytest.fixture()
def date(dates, end_index):
    return list(dates)[end_index - 1]

@pytest.fixture()
def orders(dates, symbols):
    return (Order(id=1, date=dates[0], symbol=symbols[1], type='buy', limit_price=None, fill_price=10, shares=200, fees=0), Order(id=2, date=dates[1], symbol=symbols[2], type='sell', limit_price=100, fill_price=101.1, shares=100, fees=0))

@pytest.mark.parametrize('pos_type', ['long', 'short', None])
def test_positions_when_empty(ctx, pos_type):
    assert not len(list(ctx.positions(None, pos_type)))

@pytest.mark.parametrize('pos_type', ['long', 'short', None])
def test_positions_with_symbol(ctx_with_pos, pos_type, foreign):
    positions = list(ctx_with_pos.positions(foreign, pos_type))
    if pos_type is None:
        assert len(positions) == 2
        assert positions[0].symbol == foreign
        assert positions[1].symbol == foreign
    else:
        assert len(positions) == 1
        assert positions[0].symbol == foreign

@pytest.mark.parametrize('pos_type', ['long', 'short', None])
def test_positions_with_symbol_when_empty(ctx, pos_type, foreign):
    assert not len(list(ctx.positions(foreign, pos_type)))

def test_trades(ctx_with_orders, trades):
    assert tuple(ctx_with_orders.trades()) == trades

def test_trades_when_empty(ctx):
    assert not len(list(ctx.trades()))

@pytest.fixture(params=[0, 1, 2])
def value_type(request):
    return request.param

@pytest.fixture(params=[0, 1, 2, 10, 1000])
def rand_values(value_type, request):
    if not request.param:
        return np.empty(0)
    if value_type == 0:
        return np.zeros(request.param)
    elif value_type == 1:
        return np.ones(request.param)
    return np.random.rand(request.param)

@pytest.fixture(params=[True, False])
def calc_bootstrap(request):
    return request.param

@pytest.fixture()
def portfolio_df():
    return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/portfolio_df.pkl'))

@pytest.fixture()
def trades_df():
    return pd.read_pickle(os.path.join(os.path.dirname(__file__), 'testdata/trades_df.pkl'))

@pytest.fixture()
def setup_teardown(scope, tmp_path):
    with mock.patch.object(os, 'getcwd', return_value=tmp_path):
        yield
    scope.data_source_cache = None
    scope.data_source_cache_ns = None
    scope.indicator_cache = None
    scope.indicator_cache_ns = None
    scope.model_cache = None
    scope.model_cache_ns = None

@pytest.fixture(params=['cache', None])
def cache_dir(request, tmp_path):
    return tmp_path / request.param if request.param is not None else None

@pytest.fixture()
def cache_path(tmp_path, cache_dir):
    return tmp_path / '.pybrokercache' if cache_dir is None else cache_dir

@pytest.fixture()
def train_data(data_source_df):
    return data_source_df.iloc[:data_source_df.shape[0] // 2]

@pytest.fixture()
def test_data(data_source_df):
    return data_source_df.iloc[data_source_df.shape[0] // 2:]

@pytest.fixture()
def model_loader():
    return model('loader', lambda symbol, train_start_date, train_end_date: FakeModel(symbol=symbol, preds=[]), [], pretrained=True)

