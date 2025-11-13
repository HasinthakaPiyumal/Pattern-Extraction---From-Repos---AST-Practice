# Cluster 7

class Logger:
    """Class for logging information about triggered events.

    Args:
        scope: :class:`pybroker.scope.StaticScope`.
    """

    def __init__(self, scope):
        self._scope = scope
        self._progress_bar: Optional[ProgressBar] = None
        self._download_start_time: Optional[float] = None
        self._train_split_start_time: Optional[float] = None
        self._train_model_start_time: Optional[float] = None
        self._walkforward_start_time: Optional[float] = None
        self._bootstrap_start_time: Optional[float] = None
        self._progress_bar_disabled = False
        self._disabled = False

    def _start_progress_bar(self, message: str, total_count: int):
        if self._disabled:
            return
        if self._progress_bar_disabled:
            print(message, flush=True)
            return
        self._progress_bar = ProgressBar(max_value=total_count)
        self._out(message)
        self._progress_bar.update(0)

    def _update_progress_bar(self, count: int):
        if self._progress_bar is None or self._disabled or self._progress_bar_disabled:
            return
        self._progress_bar.update(count)
        if count == self._progress_bar.max_value:
            self._progress_bar.finish()
            self._progress_bar = None
            self._out('')

    def disable(self):
        """Disables logging."""
        self._disabled = True

    def enable(self):
        """Enables logging."""
        self._disabled = False

    def disable_progress_bar(self):
        """Disables logging a progress bar."""
        self._progress_bar_disabled = True

    def enable_progress_bar(self):
        """Enables logging a progress bar."""
        self._progress_bar_disabled = False

    def download_bar_data_start(self):
        self._out('Loading bar data...')
        self._download_start_time = time.time()

    def info_download_bar_data_start(self, symbols: Iterable[str], start_date: datetime.datetime, end_date: datetime.datetime, timeframe: str):
        self._info(f'Loading:\n{start_date} to {end_date}\ntimeframe: {timeframe}\n{sorted(symbols)}')

    def loaded_bar_data(self):
        self._out('Loaded cached bar data.\n')

    def info_loaded_bar_data(self, symbols: Iterable[str], start_date: datetime.datetime, end_date: datetime.datetime, timeframe: str):
        self._info(f'Loaded:\nnamespace={self._scope.data_source_cache_ns}\n{start_date} to {end_date}\n', f'timeframe: {timeframe}\n', f'{sorted(symbols)}')

    def info_invalidate_data_source_cache(self):
        self._info(f'Mismatched columns in data source cache:\nnamespace={self._scope.data_source_cache_ns}\nInvalidating cache...')

    def debug_get_data_source_cache(self, cache_key):
        self._debug(f'Fetched data source cache:\n{cache_key}')

    def debug_set_data_source_cache(self, cache_key):
        self._debug(f'Set data source cache:\n{cache_key}')

    def download_bar_data_completed(self):
        if self._download_start_time is None:
            return
        self._out('Loaded bar data:', self._format_time(self._download_start_time), '\n')
        self._download_start_time = None

    def indicator_data_start(self, ind_syms: Sized):
        self._start_progress_bar('Computing indicators...', len(ind_syms))

    def info_indicator_data_start(self, ind_syms: Iterable[IndicatorSymbol]):
        self._info(f'Indicators: {sorted(ind_syms)}')

    def loaded_indicator_data(self):
        self._out('Loaded cached indicator data.\n')

    def info_loaded_indicator_data(self, ind_syms: Iterable[IndicatorSymbol]):
        self._info(f'Loaded:\nnamespace={self._scope.indicator_cache_ns}\n{sorted(ind_syms)}')

    def indicator_data_loading(self, count: int):
        self._update_progress_bar(count)

    def debug_get_indicator_cache(self, cache_key):
        self._debug(f'Fetched indicator cache:\n{cache_key}')

    def debug_set_indicator_cache(self, cache_key):
        self._debug(f'Set indicator cache:\n{cache_key}')

    def debug_compute_indicators(self, is_parallel: bool):
        self._debug('Computing indicators in parallel.' if is_parallel else 'Computing indicators in serial.')

    def train_split_start(self, train_dates: Sequence[np.datetime64]):
        start_date = to_datetime(train_dates[0])
        end_date = to_datetime(train_dates[-1])
        self._out(f'Train split: {start_date} to {end_date}')
        self._train_split_start_time = time.time()

    def info_train_split_start(self, model_syms: Iterable[ModelSymbol]):
        self._info(f'Models: {sorted(model_syms)}')

    def loaded_models(self):
        self._out('Loaded cached models.\n')

    def info_loaded_models(self, model_syms: Iterable[ModelSymbol]):
        self._info(f'Loaded:\nnamespace={self._scope.model_cache_ns}\n{sorted(model_syms)}')

    def info_train_model_start(self, model_sym: ModelSymbol):
        self._info(f'Training model: {model_sym}')
        self._train_model_start_time = time.time()

    def info_train_model_completed(self, model_sym: ModelSymbol):
        if self._train_model_start_time is None:
            return
        self._info(f'Finished training model {model_sym}:', self._format_time(self._train_model_start_time))
        self._train_model_start_time = None

    def info_loaded_model(self, model_sym: ModelSymbol):
        self._info(f'Loaded model: {model_sym}')

    def debug_get_model_cache(self, cache_key):
        self._debug(f'Fetched model cache:\n{cache_key}')

    def debug_set_model_cache(self, cache_key):
        self._debug(f'Set model cache:\n{cache_key}')

    def train_split_completed(self):
        if self._train_split_start_time is None:
            return
        self._out('Finished training models:', self._format_time(self._train_split_start_time), '\n')
        self._train_split_start_time = None

    def backtest_executions_start(self, test_dates: Sequence[np.datetime64]):
        if not len(test_dates):
            return
        start_date = to_datetime(test_dates[0])
        end_date = to_datetime(test_dates[-1])
        self._start_progress_bar(f'Test split: {start_date} to {end_date}', len(test_dates))

    def backtest_executions_loading(self, count: int):
        self._update_progress_bar(count)

    def walkforward_start(self, start_date: datetime.datetime, end_date: datetime.datetime):
        self._out(f'Backtesting: {start_date} to {end_date}\n')
        self._walkforward_start_time = time.time()

    def info_walkforward_between_time(self, between_time: tuple[str, str]):
        self._info(f'Backtest between times: {between_time}')

    def info_walkforward_on_days(self, days: tuple[int]):
        self._info(f'Backtest on days: {map(lambda d: Day(d).name, days)}')

    def walkforward_completed(self):
        if self._walkforward_start_time is None:
            return
        self._out('Finished backtest:', self._format_time(self._walkforward_start_time))
        self._walkforward_start_time = None

    def calc_bootstrap_metrics_start(self, samples, sample_size):
        self._out(f'Calculating bootstrap metrics: sample_size={sample_size}, samples={samples}...')
        self._bootstrap_start_time = time.time()

    def calc_bootstrap_metrics_completed(self):
        if self._bootstrap_start_time is None:
            return
        self._out('Calculated bootstrap metrics:', self._format_time(self._bootstrap_start_time), '\n')
        self._bootstrap_start_time = None

    def debug_place_buy_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Placing buy order:\n{order}')

    def debug_buy_shares_exceed_cash(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal], cash: Decimal, clamped_shares: Decimal):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Buy order amount exceeds available cash={cash}:\n{order}\nSetting buy_shares={clamped_shares}.')

    def debug_filled_buy_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Filled buy order:\n{order}')

    def debug_unfilled_buy_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Unfilled buy order:\n{order}')

    def debug_place_sell_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Placing sell order:\n{order}')

    def debug_filled_sell_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Filled sell order:\n{order}')

    def debug_unfilled_sell_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        order = self._format_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        self._debug(f'Unfilled sell order:\n{order}')

    def debug_schedule_order(self, date: np.datetime64, exec_result):
        self._debug(f'Scheduling order: {date}\n{exec_result}')

    def debug_unscheduled_order(self, exec_result):
        self._debug(f'Unscheduled order:\n{exec_result}')

    def warn_bootstrap_sample_size(self, n: int, sample_size: int):
        self._warn(f'Returns length {n} < sample size {sample_size}.\nSetting number of bootstraps to 1.')

    def debug_enable_data_source_cache(self, ns: str, cache_dir: str):
        self._debug(f'Enabled data source cache:\nnamespace={ns}\ndir={cache_dir}')

    def debug_disable_data_source_cache(self):
        self._debug('Disabled data source cache.')

    def debug_clear_data_source_cache(self, cache_dir: str):
        self._debug(f'Cleared data source cache: {cache_dir}')

    def debug_enable_indicator_cache(self, ns: str, cache_dir: str):
        self._debug(f'Enabled indicator cache:\nnamespace={ns}\ndir={cache_dir}')

    def debug_disable_indicator_cache(self):
        self._debug('Disabled indicator cache.')

    def debug_clear_indicator_cache(self, cache_dir: str):
        self._debug(f'Cleared indicator cache: {cache_dir}')

    def debug_enable_model_cache(self, ns: str, cache_dir: str):
        self._debug(f'Enabled model cache:\nnamespace={ns}\ndir={cache_dir}')

    def debug_disable_model_cache(self):
        self._debug('Disabled model cache.')

    def debug_clear_model_cache(self, cache_dir: str):
        self._debug(f'Cleared model cache: {cache_dir}')

    def _out(self, msg: str, *args):
        if self._disabled:
            return
        print(msg, *args, flush=True)

    def _info(self, msg: str, *args):
        if self._disabled:
            return
        logging.info(msg, *args)

    def _debug(self, msg: str, *args):
        if self._disabled:
            return
        logging.debug(msg, *args)

    def _warn(self, msg: str, *args):
        if self._disabled:
            return
        logging.warning(msg, *args)

    def _format_order(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]):
        return f'date={to_datetime(date)}\nsymbol={symbol}\nshares={shares}\nfill_price={fill_price}\nlimit_price={limit_price}\n'

    def _format_time(self, start_seconds: float) -> str:
        delta = time.time() - start_seconds
        return str(datetime.timedelta(seconds=round(delta)))

def indicator_data_start(self, ind_syms: Sized):
    self._start_progress_bar('Computing indicators...', len(ind_syms))

def backtest_executions_start(self, test_dates: Sequence[np.datetime64]):
    if not len(test_dates):
        return
    start_date = to_datetime(test_dates[0])
    end_date = to_datetime(test_dates[-1])
    self._start_progress_bar(f'Test split: {start_date} to {end_date}', len(test_dates))

@njit
def _verify_input(array: NDArray[np.float64], n: int):
    assert n > 0, 'n needs to be >= 1.'
    assert n <= len(array), 'n is greater than array length.'

def get_unique_sorted_dates(col: pd.Series) -> Sequence[np.datetime64]:
    """Returns sorted unique values from a DataFrame column of dates.
    Guarantees compatability between Pandas 1 and 2.
    """
    result = col.unique()
    if hasattr(result, 'to_numpy'):
        result = result.to_numpy()
    result.sort()
    return result

@njit
def max_drawdown(changes: NDArray[np.float64]) -> float:
    """Computes maximum drawdown, measured in cash.

    Args:
        changes: Array of differences between each bar and the previous bar.
    """
    n = len(changes)
    if not n:
        return 0
    cumulative = 0
    max_equity = 0
    dd = 0
    for change in changes:
        cumulative += change
        if cumulative > max_equity:
            max_equity = cumulative
        else:
            loss = max_equity - cumulative
            if loss > dd:
                dd = loss
    return -dd

@njit
def _dd_confs(boot: NDArray[np.float64]) -> DrawdownConfs:
    boot.sort()
    boot = boot[::-1]
    return DrawdownConfs(_dd_conf(0.999, boot), _dd_conf(0.99, boot), _dd_conf(0.95, boot), _dd_conf(0.9, boot))

def iqr(values: NDArray[np.float64]) -> float:
    """Computes the `interquartile range (IQR)
    <https://en.wikipedia.org/wiki/Interquartile_range>`_ of ``values``."""
    x = values[~np.isnan(values)]
    if not len(x):
        return 0
    percentiles: NDArray[np.float64] = np.percentile(x, [75, 25], method='midpoint')
    q75: float = float(percentiles[0])
    q25: float = float(percentiles[1])
    return q75 - q25

def win_loss_rate(pnls: NDArray[np.float64]) -> tuple[float, float]:
    """Computes the win rate and loss rate as percentages.

    Args:
        pnls: Array of profits and losses (PnLs) per trade.

    Returns:
        ``tuple[float, float]`` of win rate and loss rate.
    """
    pnls = pnls[pnls != 0]
    n = len(pnls)
    if not n:
        return (0, 0)
    win_rate = len(pnls[pnls > 0]) / n * 100
    loss_rate = len(pnls[pnls < 0]) / n * 100
    return (win_rate, loss_rate)

def winning_losing_trades(pnls: NDArray[np.float64]) -> tuple[int, int]:
    """Returns the number of winning and losing trades.

    Args:
        pnls: Array of profits and losses (PnLs) per trade.

    Returns:
        ``tuple[int, int]`` containing numbers of winning and losing trades.
    """
    pnls = pnls[pnls != 0]
    if not len(pnls):
        return (0, 0)
    return (len(pnls[pnls > 0]), len(pnls[pnls < 0]))

@pytest.mark.parametrize('date, expected', [('2022-02-02', datetime.strptime('2022-02-02', '%Y-%m-%d')), (datetime.strptime('2021-05-05', '%Y-%m-%d'), datetime.strptime('2021-05-05', '%Y-%m-%d')), (np.datetime64('2019-03-03'), datetime.strptime('2019-03-03', '%Y-%m-%d')), (pd.Timestamp('2020-03-03'), datetime.strptime('2020-03-03', '%Y-%m-%d'))])
def test_to_datetime(date, expected):
    dt = to_datetime(date)
    assert isinstance(dt, datetime)
    assert dt == expected

class TestColumnScope:

    def _assert_length(self, values, end_index, data_source_df, sym):
        df = data_source_df[data_source_df['symbol'] == sym]
        expected = df.shape[0] if end_index is None else end_index
        assert len(values) == expected

    def test_fetch_dict(self, col_scope, data_source_df, symbols, end_index):
        cols = ['date', 'close']
        result = col_scope.fetch_dict(symbols[0], cols, end_index)
        assert set(result.keys()) == set(cols)
        for value in result.values():
            self._assert_length(value, end_index, data_source_df, symbols[0])

    def test_fetch(self, col_scope, data_source_df, symbols, end_index):
        values = col_scope.fetch(symbols[0], 'close', end_index)
        assert isinstance(values, np.ndarray)
        self._assert_length(values, end_index, data_source_df, symbols[0])

    def test_fetch_when_cached(self, col_scope, data_source_df, symbols):
        col_scope.fetch(symbols[0], 'close', 1)
        values = col_scope.fetch(symbols[0], 'close', 2)
        assert isinstance(values, np.ndarray)
        self._assert_length(values, 2, data_source_df, symbols[0])

    def test_fetch_dict_when_empty_names(self, col_scope, symbols, end_index):
        result = col_scope.fetch_dict(symbols[0], [], end_index)
        assert not len(result)

    def test_fetch_dict_when_name_not_found(self, col_scope, symbols, end_index):
        result = col_scope.fetch_dict(symbols[0], ['foo'], end_index)
        assert result['foo'] is None

    def test_fetch_when_name_not_found(self, col_scope, symbols, end_index):
        assert col_scope.fetch(symbols[0], 'foo', end_index) is None

    def test_fetch_when_symbol_not_found_then_error(self, col_scope, end_index):
        with pytest.raises(ValueError, match=re.escape('Symbol not found: FOO.')):
            col_scope.fetch('FOO', 'close', end_index)

    def test_fetch_dict_when_symbol_not_found_then_error(self, col_scope, end_index):
        with pytest.raises(ValueError, match=re.escape('Symbol not found: FOO.')):
            col_scope.fetch_dict('FOO', ['close'], end_index)

    def test_fetch_dict_when_cached(self, col_scope, data_source_df, symbols, end_index):
        cols = ['date', 'close']
        col_scope.fetch_dict(symbols[0], cols, end_index)
        result = col_scope.fetch_dict(symbols[0], cols, end_index)
        assert set(result.keys()) == set(cols)
        for value in result.values():
            self._assert_length(value, end_index, data_source_df, symbols[0])

    def test_bar_data_from_data_columns(self, col_scope, data_source_df, symbols, end_index):
        register_columns('adj_close')
        bar_data = col_scope.bar_data_from_data_columns(symbols[0], end_index)
        sym_df = data_source_df[data_source_df['symbol'] == symbols[0]]
        for col in ('open', 'high', 'low', 'close', 'volume', 'adj_close'):
            assert (getattr(bar_data, col) == sym_df[col].to_numpy()[:end_index]).all()
        unregister_columns('adj_close')

def _assert_length(self, values, end_index, data_source_df, sym):
    df = data_source_df[data_source_df['symbol'] == sym]
    expected = df.shape[0] if end_index is None else end_index
    assert len(values) == expected

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

def _data_frame(self, dates, dates_length):
    dates = dates[:dates_length]
    return pd.DataFrame({'date': dates, 'close': np.random.rand(len(dates))})

class TestStrategy:

    @pytest.mark.parametrize('data_source', [FakeDataSource(), LazyFixture('data_source_df')])
    @pytest.mark.parametrize('executions', [LazyFixture('executions_train_only'), LazyFixture('executions_only'), LazyFixture('executions_with_indicators'), LazyFixture('executions_with_models'), LazyFixture('executions_with_models_and_indicators')])
    def test_walkforward(self, data_source, executions, date_range, days, between_time, calc_bootstrap, disable_parallel, request):
        data_source = get_fixture(request, data_source)
        executions = get_fixture(request, executions)
        config = StrategyConfig(bootstrap_samples=100, bootstrap_sample_size=10)
        strategy = Strategy(data_source, START_DATE, END_DATE, config)
        for exec in executions:
            strategy.add_execution(**exec)
        result = strategy.walkforward(start_date=date_range[0], end_date=date_range[1], windows=3, lookahead=1, timeframe='1d', days=days, between_time=between_time, calc_bootstrap=calc_bootstrap, disable_parallel=disable_parallel, adjust='adjustment')
        if date_range[0] is None:
            expected_start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
        else:
            expected_start_date = pd.to_datetime(date_range[0])
        if date_range[1] is None:
            expected_end_date = datetime.strptime(END_DATE, '%Y-%m-%d')
        else:
            expected_end_date = pd.to_datetime(date_range[1])
        if all(map(lambda e: not e['fn'], executions)):
            assert result.start_date == expected_start_date
            assert result.end_date == expected_end_date
            assert result.portfolio.empty
            assert result.positions.empty
            assert result.orders.empty
            assert result.trades.empty
            assert result.metrics == EvalMetrics()
            assert result.bootstrap is None
            assert result.signals is None
            return
        assert isinstance(result, TestResult)
        assert result.metrics is not None
        assert isinstance(result.metrics_df, pd.DataFrame)
        assert not result.metrics_df.empty
        assert result.start_date == expected_start_date
        assert result.end_date == expected_end_date
        assert isinstance(result.portfolio, pd.DataFrame)
        assert not result.portfolio.empty
        assert isinstance(result.positions, pd.DataFrame)
        assert isinstance(result.orders, pd.DataFrame)
        if calc_bootstrap:
            assert not result.bootstrap.conf_intervals.empty
            assert not result.bootstrap.drawdown_conf.empty
        else:
            assert result.bootstrap is None

    @pytest.mark.parametrize('return_signals', [True, False])
    @pytest.mark.parametrize('return_stops', [True, False])
    def test_walkforward_results(self, data_source_df, return_signals, return_stops):

        def exec_fn(ctx):
            if not ctx.long_pos():
                ctx.buy_shares = 100
                ctx.stop_trailing = 100
                ctx.stop_profit_pct = 100
        data_source_df = data_source_df[data_source_df['date'] <= to_datetime(END_DATE)]
        config = StrategyConfig(return_signals=return_signals, return_stops=return_stops)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.add_execution(exec_fn, ['AAPL', 'SPY'])
        result = strategy.walkforward(windows=3, calc_bootstrap=False)
        dates = set()
        for _, test_idx in strategy.walkforward_split(data_source_df, windows=3, lookahead=1, train_size=0.5):
            df = data_source_df.loc[test_idx]
            df = df[df['symbol'].isin(['AAPL', 'SPY'])]
            dates.update(df['date'].values)
        assert result.start_date == to_datetime(START_DATE)
        assert result.end_date == to_datetime(END_DATE)
        dates_list = list(dates)
        dates_list.sort()
        assert np.array_equal(result.portfolio.index, dates_list)
        assert len(result.positions) == 2 * len(dates) - 2
        assert np.array_equal(result.positions.index.get_level_values(1).unique(), dates_list[1:])
        assert len(result.orders) == 2
        assert not len(result.trades)
        if return_signals:
            assert len(result.signals) == 2
            assert not result.signals['AAPL'].empty
            assert not result.signals['SPY'].empty
        else:
            assert result.signals is None
        if return_stops:
            assert not result.stops.empty
            assert set(result.stops.columns) == {'date', 'symbol', 'stop_id', 'stop_type', 'pos_type', 'curr_value', 'curr_bars', 'percent', 'points', 'bars', 'fill_price', 'limit_price', 'exit_price'}
        else:
            assert result.stops is None

    def test_walkforward_when_no_executions_then_error(self, data_source_df):
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        with pytest.raises(ValueError, match=re.escape('No executions were added.')):
            strategy.walkforward(windows=3, lookahead=1)

    def test_walkforward_when_empty_data_source_then_error(self):
        df = pd.DataFrame(columns=[col.value for col in DataCol])
        strategy = Strategy(df, START_DATE, END_DATE)
        strategy.add_execution(None, 'SPY')
        with pytest.raises(ValueError, match=re.escape('DataSource is empty.')):
            strategy.walkforward(windows=3, lookahead=1)

    @pytest.mark.parametrize('start_date_1, end_date_1, start_date_2, end_date_2, expected_msg', [('2020-03-01', '2020-02-20', None, None, 'start_date (.*) must be on or before end_date (.*)\\.'), ('2020-03-01', '2020-09-30', '2020-01-01', None, 'start_date must be between .* and .*\\.'), ('2020-03-01', '2020-09-30', '2020-10-01', None, 'start_date must be between .* and .*\\.'), ('2020-03-01', '2020-09-30', None, '2020-02-01', 'end_date must be between .* and .*\\.'), ('2020-03-01', '2020-09-30', None, '2020-10-31', 'end_date must be between .* and .*\\.'), ('2020-03-01', '2020-09-30', '2020-05-01', '2020-04-01', 'start_date (.*) must be on or before end_date (.*)\\.')])
    def test_walkforward_when_invalid_dates_then_error(self, executions_only, data_source_df, start_date_1, end_date_1, start_date_2, end_date_2, expected_msg):
        with pytest.raises(ValueError, match=expected_msg):
            strategy = Strategy(data_source_df, start_date_1, end_date_1)
            for exec in executions_only:
                strategy.add_execution(**exec)
            strategy.walkforward(windows=3, lookahead=1, start_date=start_date_2, end_date=end_date_2)

    def test_backtest(self, executions_only, data_source_df):
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        for exec in executions_only:
            strategy.add_execution(**exec)
        result = strategy.backtest(calc_bootstrap=True)
        assert isinstance(result, TestResult)
        assert result.start_date == datetime.strptime(START_DATE, '%Y-%m-%d')
        assert result.end_date == datetime.strptime(END_DATE, '%Y-%m-%d')
        assert not result.portfolio.empty
        assert not result.bootstrap.conf_intervals.empty
        assert not result.bootstrap.drawdown_conf.empty

    @pytest.mark.parametrize('tz', ['UTC', None])
    @pytest.mark.parametrize('between_time, expected_hour', [(None, None), (('10:00', '1:00'), (10, 13))])
    @pytest.mark.parametrize('days, expected_days', [(None, None), ('tues', {1}), (['weds', 'fri'], {2, 4})])
    def test_filter_dates(self, tz, between_time, expected_hour, days, expected_days, data_source_df):
        data_source_df['date'] = data_source_df['date'].dt.tz_localize(tz)
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        start_date = pd.to_datetime('1/1/2021').to_pydatetime()
        end_date = pd.to_datetime('12/1/2021').to_pydatetime()
        df = strategy._filter_dates(data_source_df, start_date, end_date, between_time=between_time, days=strategy._to_day_ids(days))
        assert df.iloc[0]['date'] >= start_date
        assert df.iloc[-1]['date'] <= end_date
        row_days = set()
        for _, row in df.iterrows():
            if between_time is not None:
                assert row['date'].hour >= expected_hour[0]
                assert row['date'].hour <= expected_hour[1]
            row_days.add(row['date'].weekday())
        if expected_days is not None:
            assert row_days == expected_days

    def test_filter_dates_when_empty(self, data_source_df):
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        start_date = pd.to_datetime('1/1/2021').to_pydatetime()
        end_date = pd.to_datetime('12/1/2021').to_pydatetime()
        df = strategy._filter_dates(data_source_df, start_date, end_date, between_time=('9:00', '10:00'), days=strategy._to_day_ids('tues'))
        assert df.empty

    def test_filter_dates_when_invalid_between_time_then_error(self, data_source_df):
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        start_date = pd.to_datetime('1/1/2021').to_pydatetime()
        end_date = pd.to_datetime('12/1/2021').to_pydatetime()
        with pytest.raises(ValueError, match=re.escape("between_time must be a tuple[str, str] of start time and end time, received '9:00'.")):
            strategy._filter_dates(data_source_df, start_date, end_date, days=None, between_time='9:00')

    def test_add_execution_when_empty_symbols_then_error(self, data_source_df):
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        with pytest.raises(ValueError, match=re.escape('symbols cannot be empty.')):
            strategy.add_execution(None, [])

    def test_add_execution_when_duplicate_symbol_then_error(self, data_source_df):

        def exec_fn_1(ctx):
            ctx.buy_shares = 100

        def exec_fn_2(ctx):
            ctx.sell_shares = 100
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn_1, ['AAPL', 'SPY'])
        with pytest.raises(ValueError, match=re.escape('AAPL was already added to an execution.')):
            strategy.add_execution(exec_fn_2, 'AAPL')

    @pytest.mark.parametrize('initial_cash, max_long_positions, max_short_positions, buy_delay,sell_delay, bootstrap_samples, bootstrap_sample_size, expected_msg', [(-1, None, None, 1, 1, 100, 10, 'initial_cash must be greater than 0.'), (10000, 0, None, 1, 1, 100, 10, 'max_long_positions must be greater than 0.'), (10000, None, 0, 1, 1, 100, 10, 'max_short_positions must be greater than 0.'), (10000, None, None, 0, 1, 100, 10, 'buy_delay must be greater than 0.'), (10000, None, None, 1, 0, 100, 10, 'sell_delay must be greater than 0.'), (10000, None, None, 1, 1, 0, 10, 'bootstrap_samples must be greater than 0.'), (10000, None, None, 1, 1, 100, 0, 'bootstrap_sample_size must be greater than 0.')])
    def test_when_invalid_config_then_error(self, data_source_df, initial_cash, max_long_positions, max_short_positions, buy_delay, sell_delay, bootstrap_samples, bootstrap_sample_size, expected_msg):
        config = StrategyConfig(initial_cash=initial_cash, max_long_positions=max_long_positions, max_short_positions=max_short_positions, buy_delay=buy_delay, sell_delay=sell_delay, bootstrap_samples=bootstrap_samples, bootstrap_sample_size=bootstrap_sample_size)
        with pytest.raises(ValueError, match=re.escape(expected_msg)):
            Strategy(data_source_df, START_DATE, END_DATE, config)

    def test_when_data_source_missing_columns_then_error(self):
        values = np.repeat(1, 100)
        df = pd.DataFrame({'symbol': ['SPY'] * 100, 'open': values, 'high': values, 'low': values, 'close': values})
        with pytest.raises(ValueError, match=re.escape("DataFrame is missing required columns: ['date']")):
            Strategy(df, START_DATE, END_DATE)

    def test_when_invalid_data_source_type_then_error(self):
        with pytest.raises(TypeError, match='Invalid data_source type: .*'):
            Strategy({}, START_DATE, END_DATE)

    def test_clear_executions(self):
        df = pd.DataFrame(columns=[col.value for col in DataCol])
        strategy = Strategy(df, START_DATE, END_DATE)
        strategy.add_execution(None, 'SPY')
        strategy.clear_executions()
        assert not strategy._executions

    @pytest.mark.parametrize('enable_fractional_shares, expected_shares_type,expected_short_shares, expected_long_shares', [(True, np.float64, 0.1, 3.14), (False, np.int_, 0, 3)])
    def test_to_test_result_when_fractional_shares(self, data_source_df, enable_fractional_shares, expected_shares_type, expected_long_shares, expected_short_shares):
        portfolio = Portfolio(100000)
        portfolio.bars = deque((PortfolioBar(date=np.datetime64(START_DATE), cash=Decimal(100000), equity=Decimal(100000), margin=Decimal(), market_value=Decimal(100000), pnl=Decimal(1000), unrealized_pnl=Decimal(), fees=Decimal()),))
        portfolio.position_bars = deque((PositionBar(symbol='SPY', date=np.datetime64(START_DATE), long_shares=Decimal('3.14'), short_shares=Decimal('0.1'), close=Decimal(100), equity=Decimal(100000), market_value=Decimal(100000), margin=Decimal(), unrealized_pnl=Decimal(100)),))
        portfolio.orders = deque((Order(id=1, type='buy', symbol='SPY', date=np.datetime64(START_DATE), shares=Decimal('3.14'), limit_price=Decimal(100), fill_price=Decimal(99), fees=Decimal()),))
        portfolio.trades = deque((Trade(id=1, type='long', symbol='SPY', entry_date=np.datetime64(START_DATE), exit_date=np.datetime64(END_DATE), entry=Decimal(100), exit=Decimal(101), shares=Decimal('3.14'), pnl=Decimal(1000), return_pct=Decimal('10.3'), agg_pnl=Decimal(1000), bars=2, pnl_per_bar=Decimal(500), stop=None, mae=Decimal(-10), mfe=Decimal(10)),))
        config = StrategyConfig(enable_fractional_shares=enable_fractional_shares)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        result = strategy._to_test_result(START_DATE, END_DATE, portfolio, calc_bootstrap=False, train_only=False, signals=None)
        assert np.issubdtype(result.positions['long_shares'].dtype, expected_shares_type)
        assert np.issubdtype(result.positions['short_shares'].dtype, expected_shares_type)
        assert np.issubdtype(result.orders['shares'].dtype, expected_shares_type)
        assert np.issubdtype(result.trades['shares'].dtype, expected_shares_type)
        assert result.positions['long_shares'].values[0] == expected_long_shares
        assert result.positions['short_shares'].values[0] == expected_short_shares
        assert result.orders['shares'].values[0] == expected_long_shares
        assert result.trades['shares'].values[0] == expected_long_shares

    def test_to_result_when_round_test_result_is_false(self, data_source_df):
        portfolio = Portfolio(100000)
        portfolio.bars = deque((PortfolioBar(date=np.datetime64(START_DATE), cash=Decimal(100000), equity=Decimal(100000), margin=Decimal(), market_value=Decimal(100000), pnl=Decimal('1000.111'), unrealized_pnl=Decimal(), fees=Decimal()),))
        portfolio.position_bars = deque((PositionBar(symbol='SPY', date=np.datetime64(START_DATE), long_shares=Decimal('3.144'), short_shares=Decimal('0.111'), close=Decimal(100), equity=Decimal(100000), market_value=Decimal(100000), margin=Decimal(), unrealized_pnl=Decimal(100)),))
        portfolio.orders = deque((Order(id=1, type='buy', symbol='SPY', date=np.datetime64(START_DATE), shares=Decimal('3.144'), limit_price=Decimal(100), fill_price=Decimal(99), fees=Decimal()),))
        portfolio.trades = deque((Trade(id=1, type='long', symbol='SPY', entry_date=np.datetime64(START_DATE), exit_date=np.datetime64(END_DATE), entry=Decimal(100), exit=Decimal(101), shares=Decimal('3.144'), pnl=Decimal(1000), return_pct=Decimal('10.33'), agg_pnl=Decimal(1000), bars=2, pnl_per_bar=Decimal(500), stop=None, mae=Decimal(-10), mfe=Decimal(10)),))
        config = StrategyConfig(enable_fractional_shares=True, round_test_result=False)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        result = strategy._to_test_result(START_DATE, END_DATE, portfolio, calc_bootstrap=False, train_only=False, signals=None)
        assert result.positions['long_shares'].values[0] == 3.144
        assert result.positions['short_shares'].values[0] == 0.111
        assert result.portfolio['pnl'].values[0] == 1000.111
        assert result.orders['shares'].values[0] == 3.144
        assert result.trades['shares'].values[0] == 3.144

    def test_to_test_result_when_empty(self, data_source_df):
        portfolio = Portfolio(100000)
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        result = strategy._to_test_result(START_DATE, END_DATE, portfolio, calc_bootstrap=False, train_only=False, signals=None)
        assert result.portfolio.empty
        assert result.positions.empty
        assert result.orders.empty
        assert result.trades.empty
        assert result.signals is None

    def test_backtest_when_exit_long_on_last_bar(self, data_source_df):

        def buy_exec_fn(ctx):
            if not ctx.long_pos():
                ctx.buy_shares = 100
                ctx.buy_fill_price = 150

        def sell_fill_price(_symbol, _bar_data):
            return 199.99
        config = StrategyConfig(exit_on_last_bar=True, exit_sell_fill_price=sell_fill_price)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.add_execution(buy_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        assert len(result.trades) == 1
        trade = result.trades.iloc[0]
        assert trade['type'] == 'long'
        assert trade['symbol'] == 'SPY'
        assert trade['entry_date'] == dates[1]
        assert trade['exit_date'] == dates[-1]
        assert trade['entry'] == 150
        assert trade['exit'] == 199.99
        assert trade['shares'] == 100

    def test_backtest_when_exit_short_on_last_bar(self, data_source_df):

        def sell_exec_fn(ctx):
            if not ctx.short_pos():
                ctx.sell_shares = 100
                ctx.sell_fill_price = 200

        def buy_fill_price(_symbol, _bar_data):
            return 99.99
        config = StrategyConfig(exit_on_last_bar=True, exit_cover_fill_price=buy_fill_price)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.add_execution(sell_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        assert len(result.trades) == 1
        trade = result.trades.iloc[0]
        assert trade['type'] == 'short'
        assert trade['symbol'] == 'SPY'
        assert trade['entry_date'] == dates[1]
        assert trade['exit_date'] == dates[-1]
        assert trade['entry'] == 200
        assert trade['exit'] == 99.99
        assert trade['shares'] == 100

    def test_backtest_when_buy_shares_and_sell_shares_then_error(self, data_source_df):

        def exec_fn(ctx):
            ctx.buy_shares = 100
            ctx.sell_shares = 100
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, ['AAPL', 'SPY'])
        with pytest.raises(ValueError, match=re.escape('For each symbol, only one of buy_shares or sell_shares can be set per bar.')):
            strategy.backtest()

    def test_backtest_pending_orders(self, data_source_df):
        buy_delay = 2
        dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]

        def buy_exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
            elif ctx.bars == 2:
                orders = tuple(ctx.pending_orders())
                assert len(orders) == 1
                assert orders[0] == PendingOrder(id=1, type='buy', symbol='SPY', created=ctx.date[0], exec_date=dates[buy_delay], shares=100, limit_price=None, fill_price=PriceType.MIDDLE)
            else:
                assert not tuple(ctx.pending_orders())
        config = StrategyConfig(buy_delay=buy_delay)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.add_execution(buy_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.orders) == 1
        order = result.orders.iloc[0]
        assert order['type'] == 'buy'
        assert order['symbol'] == 'SPY'
        assert order['date'] == dates[2]
        assert np.isnan(order['limit_price'])
        assert order['shares'] == 100

    def test_backtest_when_pending_orders_canceled(self, data_source_df):
        dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        buy_delay = 10
        sell_delay = 5

        def exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
                ctx.buy_limit_price = 99
            elif ctx.bars == 2:
                ctx.sell_shares = 200
                ctx.sell_limit_price = 100
            elif ctx.bars == 3:
                orders = tuple(ctx.pending_orders())
                assert len(orders) == 2
                assert orders[0] == PendingOrder(id=1, type='buy', symbol='SPY', created=ctx.date[0], exec_date=dates[buy_delay], shares=100, limit_price=99, fill_price=PriceType.MIDDLE)
                assert orders[1] == PendingOrder(id=2, type='sell', symbol='SPY', created=ctx.date[1], exec_date=dates[1 + sell_delay], shares=200, limit_price=100, fill_price=PriceType.MIDDLE)
                ctx.cancel_all_pending_orders()
            else:
                assert not tuple(ctx.pending_orders())
        config = StrategyConfig(buy_delay=buy_delay, sell_delay=sell_delay)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.add_execution(exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        assert not len(result.orders)

    def test_backtest_when_buy_hold_bars(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_fill_price = PriceType.CLOSE
            ctx.sell_fill_price = PriceType.OPEN
            ctx.buy_shares = 100
            ctx.hold_bars = 2
        df = data_source_df[data_source_df['symbol'] == 'SPY']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        buy_dates = dates[1:]
        sell_dates = dates[3:]
        config = StrategyConfig(initial_cash=500000)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.add_execution(buy_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        orders = result.orders
        buy_orders = orders[orders['type'] == 'buy']
        assert len(buy_orders) == len(buy_dates)
        for buy_date in buy_dates:
            row = buy_orders[buy_orders['date'] == buy_date]
            assert row['symbol'].item() == 'SPY'
            assert row['shares'].item() == 100
            assert np.isnan(row['limit_price'].item())
            assert row['fill_price'].item() == round(df[df['date'] == buy_date]['close'].item(), 2)
            assert row['fees'].item() == 0
        sell_orders = orders[orders['type'] == 'sell']
        assert len(sell_orders) == len(sell_dates)
        for sell_date in sell_dates:
            row = sell_orders[sell_orders['date'] == sell_date]
            assert row['symbol'].item() == 'SPY'
            assert row['shares'].item() == 100
            assert np.isnan(row['limit_price'].item())
            assert row['fill_price'].item() == round(df[df['date'] == sell_date]['open'].item(), 2)
            assert row['fees'].item() == 0
        assert (result.trades['stop'] == 'bar').all()

    def test_backtest_when_sell_hold_bars(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_fill_price = PriceType.OPEN
            ctx.buy_fill_price = PriceType.CLOSE
            ctx.sell_shares = 100
            ctx.hold_bars = 1
        df = data_source_df[data_source_df['symbol'] == 'SPY']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        buy_dates = dates[2:]
        sell_dates = dates[1:]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(sell_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        orders = result.orders
        sell_orders = orders[orders['type'] == 'sell']
        assert len(sell_orders) == len(sell_dates)
        for sell_date in sell_dates:
            row = sell_orders[sell_orders['date'] == sell_date]
            assert row['symbol'].item() == 'SPY'
            assert row['shares'].item() == 100
            assert np.isnan(row['limit_price'].item())
            assert row['fill_price'].item() == round(df[df['date'] == sell_date]['open'].item(), 2)
            assert row['fees'].item() == 0
        buy_orders = orders[orders['type'] == 'buy']
        assert len(buy_orders) == len(buy_dates)
        for buy_date in buy_dates:
            row = buy_orders[buy_orders['date'] == buy_date]
            assert row['symbol'].item() == 'SPY'
            assert row['shares'].item() == 100
            assert np.isnan(row['limit_price'].item())
            assert row['fill_price'].item() == round(df[df['date'] == buy_date]['close'].item(), 2)
            assert row['fees'].item() == 0
        assert len(result.trades) == len(buy_orders)
        assert (result.trades['stop'] == 'bar').all()

    def test_backtest_when_slippage(self, data_source_df):

        class FakeSlippageModel(SlippageModel):

            def apply_slippage(self, ctx: ExecContext, buy_shares, sell_shares):
                ctx.buy_shares = 99

        def buy_exec_fn(ctx):
            ctx.buy_fill_price = PriceType.CLOSE
            ctx.sell_fill_price = PriceType.OPEN
            ctx.buy_shares = 100
            ctx.hold_bars = 2
        df = data_source_df[data_source_df['symbol'] == 'SPY']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        buy_dates = dates[1:]
        sell_dates = dates[3:]
        config = StrategyConfig(initial_cash=500000)
        strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
        strategy.set_slippage_model(FakeSlippageModel())
        strategy.add_execution(buy_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        orders = result.orders
        buy_orders = orders[orders['type'] == 'buy']
        assert len(buy_orders) == len(buy_dates)
        for buy_date in buy_dates:
            row = buy_orders[buy_orders['date'] == buy_date]
            assert row['symbol'].item() == 'SPY'
            assert row['shares'].item() == 99
            assert np.isnan(row['limit_price'].item())
            assert row['fill_price'].item() == round(df[df['date'] == buy_date]['close'].item(), 2)
            assert row['fees'].item() == 0
        sell_orders = orders[orders['type'] == 'sell']
        assert len(sell_orders) == len(sell_dates)
        for sell_date in sell_dates:
            row = sell_orders[sell_orders['date'] == sell_date]
            assert row['symbol'].item() == 'SPY'
            assert row['shares'].item() == 99
            assert np.isnan(row['limit_price'].item())
            assert row['fill_price'].item() == round(df[df['date'] == sell_date]['open'].item(), 2)
            assert row['fees'].item() == 0
        assert (result.trades['stop'] == 'bar').all()

    def test_backtest_when_slippage_and_sell_all_shares(self, data_source_df):

        class FakeSlippageModel(SlippageModel):

            def apply_slippage(self, ctx: ExecContext, buy_shares, sell_shares):
                if sell_shares:
                    ctx.sell_shares = 90

        def buy_exec_fn(ctx):
            if not ctx.long_pos():
                ctx.buy_shares = 100
            elif ctx.bars == 2:
                ctx.sell_all_shares()
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.set_slippage_model(FakeSlippageModel())
        strategy.add_execution(buy_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        orders = result.orders
        sell_orders = orders[orders['type'] == 'sell']
        assert len(sell_orders) == 1
        assert sell_orders.iloc[0]['shares'] == 100

    def test_backtest_when_slippage_and_cover_all_shares(self, data_source_df):

        class FakeSlippageModel(SlippageModel):

            def apply_slippage(self, ctx: ExecContext, buy_shares, sell_shares):
                if buy_shares:
                    ctx.buy_shares = 90

        def buy_exec_fn(ctx):
            if not ctx.short_pos():
                ctx.sell_shares = 100
            elif ctx.bars == 2:
                ctx.cover_all_shares()
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.set_slippage_model(FakeSlippageModel())
        strategy.add_execution(buy_exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        orders = result.orders
        buy_orders = orders[orders['type'] == 'buy']
        assert len(buy_orders) == 1
        assert buy_orders.iloc[0]['shares'] == 100

    def test_backtest_when_stop_loss(self, data_source_df):

        def exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
                ctx.stop_loss = 10
        df = data_source_df[data_source_df['symbol'].isin(['SPY', 'AAPL'])]
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, ['SPY', 'AAPL'])
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.trades) == 2
        trade = result.trades.iloc[0]
        assert trade['type'] == 'long'
        assert trade['symbol'] == 'SPY'
        assert trade['entry_date'] == dates[1]
        assert trade['exit'] == trade['entry'] - 10
        assert trade['shares'] == 100
        assert trade['pnl'] == -1000
        assert trade['agg_pnl'] == -1000
        assert trade['pnl_per_bar'] == round(-1000 / trade['bars'], 2)
        assert trade['stop'] == 'loss'
        trade = result.trades.iloc[1]
        assert trade['type'] == 'long'
        assert trade['symbol'] == 'AAPL'
        assert trade['entry_date'] == dates[1]
        assert trade['exit'] == trade['entry'] - 10
        assert trade['shares'] == 100
        assert trade['pnl'] == -1000
        assert trade['agg_pnl'] == -2000
        assert trade['pnl_per_bar'] == round(-1000 / trade['bars'], 2)
        assert trade['stop'] == 'loss'
        assert len(result.orders) == 4
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'AAPL'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 100
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0
        buy_order = result.orders.iloc[1]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'SPY'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 100
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0
        sell_order = result.orders.iloc[2]
        assert sell_order['type'] == 'sell'
        assert sell_order['symbol'] == 'SPY'
        assert sell_order['shares'] == 100
        assert np.isnan(sell_order['limit_price'])
        assert sell_order['fees'] == 0
        sell_order = result.orders.iloc[3]
        assert sell_order['type'] == 'sell'
        assert sell_order['symbol'] == 'AAPL'
        assert sell_order['shares'] == 100
        assert np.isnan(sell_order['limit_price'])
        assert sell_order['fees'] == 0

    def test_backtest_when_sell_before_stop_loss(self, data_source_df):

        def exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
                ctx.stop_loss = 10
            elif ctx.bars == 10:
                ctx.sell_all_shares()
        df = data_source_df[data_source_df['symbol'] == 'SPY']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.trades) == 1
        trade = result.trades.iloc[0]
        assert trade['type'] == 'long'
        assert trade['symbol'] == 'SPY'
        assert trade['entry_date'] == dates[1]
        assert trade['exit_date'] == dates[10]
        assert trade['shares'] == 100
        assert trade['stop'] is None
        assert len(result.orders) == 2
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'SPY'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 100
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0
        sell_order = result.orders.iloc[1]
        assert sell_order['type'] == 'sell'
        assert sell_order['symbol'] == 'SPY'
        assert sell_order['date'] == dates[10]
        assert sell_order['shares'] == 100
        assert np.isnan(sell_order['limit_price'])
        assert sell_order['fees'] == 0

    def test_backtest_when_cancel_stop(self, data_source_df):

        def exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
                ctx.stop_loss = 10
            elif ctx.bars == 10:
                entry = tuple(ctx.long_pos().entries)[0]
                stop = next(iter(entry.stops))
                assert ctx.cancel_stop(stop_id=stop.id)
        df = data_source_df[data_source_df['symbol'] == 'SPY']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        assert not len(result.trades)
        assert len(result.orders) == 1
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'SPY'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 100
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0

    def test_backtest_when_cancel_stops(self, data_source_df):

        def exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
                ctx.stop_loss = 10
                ctx.stop_trailing = 10
            elif ctx.bars == 10:
                ctx.cancel_stops('SPY')
        df = data_source_df[data_source_df['symbol'] == 'SPY']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        assert not len(result.trades)
        assert len(result.orders) == 1
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'SPY'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 100
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0

    def test_backtest_when_pos_size_handler_zero_shares(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_shares = 100

        def sell_exec_fn(ctx):
            ctx.sell_shares = 100

        def pos_size_handler(ctx):
            signals = tuple(ctx.signals())
            ctx.set_shares(signals[0], shares=0)
            ctx.set_shares(signals[1], shares=0)
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(buy_exec_fn, 'SPY')
        strategy.add_execution(sell_exec_fn, 'AAPL')
        strategy.set_pos_size_handler(pos_size_handler)
        result = strategy.backtest(calc_bootstrap=False)
        assert not len(result.orders)

    def test_backtest_when_no_stops(self, data_source_df):

        def exec_fn(ctx):
            if ctx.bars == 1:
                ctx.buy_shares = 100
            elif ctx.long_pos() and ctx.bars > 30:
                ctx.sell_all_shares()
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, 'SPY')
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.trades) == 1
        assert result.trades.iloc[0]['stop'] is None

    def test_backtest_when_before_exec(self, data_source_df):

        def before_exec_fn(ctxs):
            assert len(ctxs) == 2
            assert isinstance(ctxs['SPY'], ExecContext)
            assert isinstance(ctxs['AAPL'], ExecContext)
            ctxs['SPY'].session['foo'] = 'bar'

        def exec_fn(ctx):
            if ctx.symbol == 'AAPL' and (not ctx.long_pos()):
                ctx.buy_shares = 200
            if ctx.symbol == 'SPY':
                assert ctx.session['foo'] == 'bar'
        df = data_source_df[data_source_df['symbol'] == 'AAPL']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, ['SPY', 'AAPL'])
        strategy.set_before_exec(before_exec_fn)
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.orders) == 1
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'AAPL'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 200
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0

    def test_backtest_when_before_exec_and_no_executions(self, data_source_df):

        def before_exec_fn(ctxs):
            assert len(ctxs) == 2
            assert isinstance(ctxs['SPY'], ExecContext)
            assert isinstance(ctxs['AAPL'], ExecContext)
            if not ctxs['AAPL'].long_pos():
                ctxs['AAPL'].buy_shares = 200
        df = data_source_df[data_source_df['symbol'] == 'AAPL']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(None, ['SPY', 'AAPL'])
        strategy.set_before_exec(before_exec_fn)
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.orders) == 1
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'AAPL'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 200
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0

    def test_backtest_when_after_exec(self, data_source_df):

        def after_exec_fn(ctxs):
            assert len(ctxs) == 2
            assert isinstance(ctxs['SPY'], ExecContext)
            assert isinstance(ctxs['AAPL'], ExecContext)
            if not ctxs['AAPL'].long_pos():
                ctxs['AAPL'].buy_shares = 300

        def exec_fn(ctx):
            if ctx.symbol == 'AAPL' and (not ctx.long_pos()):
                ctx.buy_shares = 200
        df = data_source_df[data_source_df['symbol'] == 'AAPL']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, ['SPY', 'AAPL'])
        strategy.set_after_exec(after_exec_fn)
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.orders) == 1
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'AAPL'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 300
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0

    def test_backtest_when_after_exec_and_no_executions(self, data_source_df):

        def after_exec_fn(ctxs):
            assert len(ctxs) == 2
            assert isinstance(ctxs['SPY'], ExecContext)
            assert isinstance(ctxs['AAPL'], ExecContext)
            if not ctxs['AAPL'].long_pos():
                ctxs['AAPL'].buy_shares = 200
        df = data_source_df[data_source_df['symbol'] == 'AAPL']
        dates = df['date'].unique()
        dates = dates[dates <= np.datetime64(END_DATE)]
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(None, ['SPY', 'AAPL'])
        strategy.set_after_exec(after_exec_fn)
        result = strategy.backtest(calc_bootstrap=False)
        assert len(result.orders) == 1
        buy_order = result.orders.iloc[0]
        assert buy_order['type'] == 'buy'
        assert buy_order['symbol'] == 'AAPL'
        assert buy_order['date'] == dates[1]
        assert buy_order['shares'] == 200
        assert np.isnan(buy_order['limit_price'])
        assert buy_order['fees'] == 0

    def test_backtest_when_warmup(self, data_source_df):

        def exec_fn(ctx):
            if ctx.bars <= 10:
                raise AssertionError('Warmup failed.')
            elif not ctx.long_pos():
                ctx.buy_shares = 100
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, 'SPY')
        result = strategy.backtest(warmup=10)
        assert len(result.orders) == 1

    def test_backtest_when_warmup_invalid_then_error(self, data_source_df):

        def exec_fn(ctx):
            pass
        strategy = Strategy(data_source_df, START_DATE, END_DATE)
        strategy.add_execution(exec_fn, 'SPY')
        with pytest.raises(ValueError, match=re.escape('warmup must be > 0.')):
            strategy.backtest(warmup=-1)

@pytest.mark.parametrize('return_signals', [True, False])
@pytest.mark.parametrize('return_stops', [True, False])
def test_walkforward_results(self, data_source_df, return_signals, return_stops):

    def exec_fn(ctx):
        if not ctx.long_pos():
            ctx.buy_shares = 100
            ctx.stop_trailing = 100
            ctx.stop_profit_pct = 100
    data_source_df = data_source_df[data_source_df['date'] <= to_datetime(END_DATE)]
    config = StrategyConfig(return_signals=return_signals, return_stops=return_stops)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.add_execution(exec_fn, ['AAPL', 'SPY'])
    result = strategy.walkforward(windows=3, calc_bootstrap=False)
    dates = set()
    for _, test_idx in strategy.walkforward_split(data_source_df, windows=3, lookahead=1, train_size=0.5):
        df = data_source_df.loc[test_idx]
        df = df[df['symbol'].isin(['AAPL', 'SPY'])]
        dates.update(df['date'].values)
    assert result.start_date == to_datetime(START_DATE)
    assert result.end_date == to_datetime(END_DATE)
    dates_list = list(dates)
    dates_list.sort()
    assert np.array_equal(result.portfolio.index, dates_list)
    assert len(result.positions) == 2 * len(dates) - 2
    assert np.array_equal(result.positions.index.get_level_values(1).unique(), dates_list[1:])
    assert len(result.orders) == 2
    assert not len(result.trades)
    if return_signals:
        assert len(result.signals) == 2
        assert not result.signals['AAPL'].empty
        assert not result.signals['SPY'].empty
    else:
        assert result.signals is None
    if return_stops:
        assert not result.stops.empty
        assert set(result.stops.columns) == {'date', 'symbol', 'stop_id', 'stop_type', 'pos_type', 'curr_value', 'curr_bars', 'percent', 'points', 'bars', 'fill_price', 'limit_price', 'exit_price'}
    else:
        assert result.stops is None

def test_backtest(self, executions_only, data_source_df):
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    for exec in executions_only:
        strategy.add_execution(**exec)
    result = strategy.backtest(calc_bootstrap=True)
    assert isinstance(result, TestResult)
    assert result.start_date == datetime.strptime(START_DATE, '%Y-%m-%d')
    assert result.end_date == datetime.strptime(END_DATE, '%Y-%m-%d')
    assert not result.portfolio.empty
    assert not result.bootstrap.conf_intervals.empty
    assert not result.bootstrap.drawdown_conf.empty

def test_add_execution_when_empty_symbols_then_error(self, data_source_df):
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    with pytest.raises(ValueError, match=re.escape('symbols cannot be empty.')):
        strategy.add_execution(None, [])

def test_add_execution_when_duplicate_symbol_then_error(self, data_source_df):

    def exec_fn_1(ctx):
        ctx.buy_shares = 100

    def exec_fn_2(ctx):
        ctx.sell_shares = 100
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn_1, ['AAPL', 'SPY'])
    with pytest.raises(ValueError, match=re.escape('AAPL was already added to an execution.')):
        strategy.add_execution(exec_fn_2, 'AAPL')

def test_when_invalid_data_source_type_then_error(self):
    with pytest.raises(TypeError, match='Invalid data_source type: .*'):
        Strategy({}, START_DATE, END_DATE)

def test_clear_executions(self):
    df = pd.DataFrame(columns=[col.value for col in DataCol])
    strategy = Strategy(df, START_DATE, END_DATE)
    strategy.add_execution(None, 'SPY')
    strategy.clear_executions()
    assert not strategy._executions

def test_backtest_when_exit_long_on_last_bar(self, data_source_df):

    def buy_exec_fn(ctx):
        if not ctx.long_pos():
            ctx.buy_shares = 100
            ctx.buy_fill_price = 150

    def sell_fill_price(_symbol, _bar_data):
        return 199.99
    config = StrategyConfig(exit_on_last_bar=True, exit_sell_fill_price=sell_fill_price)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.add_execution(buy_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    assert len(result.trades) == 1
    trade = result.trades.iloc[0]
    assert trade['type'] == 'long'
    assert trade['symbol'] == 'SPY'
    assert trade['entry_date'] == dates[1]
    assert trade['exit_date'] == dates[-1]
    assert trade['entry'] == 150
    assert trade['exit'] == 199.99
    assert trade['shares'] == 100

def test_backtest_when_exit_short_on_last_bar(self, data_source_df):

    def sell_exec_fn(ctx):
        if not ctx.short_pos():
            ctx.sell_shares = 100
            ctx.sell_fill_price = 200

    def buy_fill_price(_symbol, _bar_data):
        return 99.99
    config = StrategyConfig(exit_on_last_bar=True, exit_cover_fill_price=buy_fill_price)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.add_execution(sell_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    assert len(result.trades) == 1
    trade = result.trades.iloc[0]
    assert trade['type'] == 'short'
    assert trade['symbol'] == 'SPY'
    assert trade['entry_date'] == dates[1]
    assert trade['exit_date'] == dates[-1]
    assert trade['entry'] == 200
    assert trade['exit'] == 99.99
    assert trade['shares'] == 100

def test_backtest_when_buy_shares_and_sell_shares_then_error(self, data_source_df):

    def exec_fn(ctx):
        ctx.buy_shares = 100
        ctx.sell_shares = 100
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, ['AAPL', 'SPY'])
    with pytest.raises(ValueError, match=re.escape('For each symbol, only one of buy_shares or sell_shares can be set per bar.')):
        strategy.backtest()

def test_backtest_pending_orders(self, data_source_df):
    buy_delay = 2
    dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]

    def buy_exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
        elif ctx.bars == 2:
            orders = tuple(ctx.pending_orders())
            assert len(orders) == 1
            assert orders[0] == PendingOrder(id=1, type='buy', symbol='SPY', created=ctx.date[0], exec_date=dates[buy_delay], shares=100, limit_price=None, fill_price=PriceType.MIDDLE)
        else:
            assert not tuple(ctx.pending_orders())
    config = StrategyConfig(buy_delay=buy_delay)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.add_execution(buy_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.orders) == 1
    order = result.orders.iloc[0]
    assert order['type'] == 'buy'
    assert order['symbol'] == 'SPY'
    assert order['date'] == dates[2]
    assert np.isnan(order['limit_price'])
    assert order['shares'] == 100

def test_backtest_when_pending_orders_canceled(self, data_source_df):
    dates = data_source_df[data_source_df['symbol'] == 'SPY']['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    buy_delay = 10
    sell_delay = 5

    def exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
            ctx.buy_limit_price = 99
        elif ctx.bars == 2:
            ctx.sell_shares = 200
            ctx.sell_limit_price = 100
        elif ctx.bars == 3:
            orders = tuple(ctx.pending_orders())
            assert len(orders) == 2
            assert orders[0] == PendingOrder(id=1, type='buy', symbol='SPY', created=ctx.date[0], exec_date=dates[buy_delay], shares=100, limit_price=99, fill_price=PriceType.MIDDLE)
            assert orders[1] == PendingOrder(id=2, type='sell', symbol='SPY', created=ctx.date[1], exec_date=dates[1 + sell_delay], shares=200, limit_price=100, fill_price=PriceType.MIDDLE)
            ctx.cancel_all_pending_orders()
        else:
            assert not tuple(ctx.pending_orders())
    config = StrategyConfig(buy_delay=buy_delay, sell_delay=sell_delay)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.add_execution(exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    assert not len(result.orders)

def test_backtest_when_buy_hold_bars(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_fill_price = PriceType.CLOSE
        ctx.sell_fill_price = PriceType.OPEN
        ctx.buy_shares = 100
        ctx.hold_bars = 2
    df = data_source_df[data_source_df['symbol'] == 'SPY']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    buy_dates = dates[1:]
    sell_dates = dates[3:]
    config = StrategyConfig(initial_cash=500000)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.add_execution(buy_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    orders = result.orders
    buy_orders = orders[orders['type'] == 'buy']
    assert len(buy_orders) == len(buy_dates)
    for buy_date in buy_dates:
        row = buy_orders[buy_orders['date'] == buy_date]
        assert row['symbol'].item() == 'SPY'
        assert row['shares'].item() == 100
        assert np.isnan(row['limit_price'].item())
        assert row['fill_price'].item() == round(df[df['date'] == buy_date]['close'].item(), 2)
        assert row['fees'].item() == 0
    sell_orders = orders[orders['type'] == 'sell']
    assert len(sell_orders) == len(sell_dates)
    for sell_date in sell_dates:
        row = sell_orders[sell_orders['date'] == sell_date]
        assert row['symbol'].item() == 'SPY'
        assert row['shares'].item() == 100
        assert np.isnan(row['limit_price'].item())
        assert row['fill_price'].item() == round(df[df['date'] == sell_date]['open'].item(), 2)
        assert row['fees'].item() == 0
    assert (result.trades['stop'] == 'bar').all()

def test_backtest_when_sell_hold_bars(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_fill_price = PriceType.OPEN
        ctx.buy_fill_price = PriceType.CLOSE
        ctx.sell_shares = 100
        ctx.hold_bars = 1
    df = data_source_df[data_source_df['symbol'] == 'SPY']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    buy_dates = dates[2:]
    sell_dates = dates[1:]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(sell_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    orders = result.orders
    sell_orders = orders[orders['type'] == 'sell']
    assert len(sell_orders) == len(sell_dates)
    for sell_date in sell_dates:
        row = sell_orders[sell_orders['date'] == sell_date]
        assert row['symbol'].item() == 'SPY'
        assert row['shares'].item() == 100
        assert np.isnan(row['limit_price'].item())
        assert row['fill_price'].item() == round(df[df['date'] == sell_date]['open'].item(), 2)
        assert row['fees'].item() == 0
    buy_orders = orders[orders['type'] == 'buy']
    assert len(buy_orders) == len(buy_dates)
    for buy_date in buy_dates:
        row = buy_orders[buy_orders['date'] == buy_date]
        assert row['symbol'].item() == 'SPY'
        assert row['shares'].item() == 100
        assert np.isnan(row['limit_price'].item())
        assert row['fill_price'].item() == round(df[df['date'] == buy_date]['close'].item(), 2)
        assert row['fees'].item() == 0
    assert len(result.trades) == len(buy_orders)
    assert (result.trades['stop'] == 'bar').all()

def test_backtest_when_slippage(self, data_source_df):

    class FakeSlippageModel(SlippageModel):

        def apply_slippage(self, ctx: ExecContext, buy_shares, sell_shares):
            ctx.buy_shares = 99

    def buy_exec_fn(ctx):
        ctx.buy_fill_price = PriceType.CLOSE
        ctx.sell_fill_price = PriceType.OPEN
        ctx.buy_shares = 100
        ctx.hold_bars = 2
    df = data_source_df[data_source_df['symbol'] == 'SPY']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    buy_dates = dates[1:]
    sell_dates = dates[3:]
    config = StrategyConfig(initial_cash=500000)
    strategy = Strategy(data_source_df, START_DATE, END_DATE, config)
    strategy.set_slippage_model(FakeSlippageModel())
    strategy.add_execution(buy_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    orders = result.orders
    buy_orders = orders[orders['type'] == 'buy']
    assert len(buy_orders) == len(buy_dates)
    for buy_date in buy_dates:
        row = buy_orders[buy_orders['date'] == buy_date]
        assert row['symbol'].item() == 'SPY'
        assert row['shares'].item() == 99
        assert np.isnan(row['limit_price'].item())
        assert row['fill_price'].item() == round(df[df['date'] == buy_date]['close'].item(), 2)
        assert row['fees'].item() == 0
    sell_orders = orders[orders['type'] == 'sell']
    assert len(sell_orders) == len(sell_dates)
    for sell_date in sell_dates:
        row = sell_orders[sell_orders['date'] == sell_date]
        assert row['symbol'].item() == 'SPY'
        assert row['shares'].item() == 99
        assert np.isnan(row['limit_price'].item())
        assert row['fill_price'].item() == round(df[df['date'] == sell_date]['open'].item(), 2)
        assert row['fees'].item() == 0
    assert (result.trades['stop'] == 'bar').all()

def test_backtest_when_slippage_and_sell_all_shares(self, data_source_df):

    class FakeSlippageModel(SlippageModel):

        def apply_slippage(self, ctx: ExecContext, buy_shares, sell_shares):
            if sell_shares:
                ctx.sell_shares = 90

    def buy_exec_fn(ctx):
        if not ctx.long_pos():
            ctx.buy_shares = 100
        elif ctx.bars == 2:
            ctx.sell_all_shares()
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.set_slippage_model(FakeSlippageModel())
    strategy.add_execution(buy_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    orders = result.orders
    sell_orders = orders[orders['type'] == 'sell']
    assert len(sell_orders) == 1
    assert sell_orders.iloc[0]['shares'] == 100

def test_backtest_when_slippage_and_cover_all_shares(self, data_source_df):

    class FakeSlippageModel(SlippageModel):

        def apply_slippage(self, ctx: ExecContext, buy_shares, sell_shares):
            if buy_shares:
                ctx.buy_shares = 90

    def buy_exec_fn(ctx):
        if not ctx.short_pos():
            ctx.sell_shares = 100
        elif ctx.bars == 2:
            ctx.cover_all_shares()
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.set_slippage_model(FakeSlippageModel())
    strategy.add_execution(buy_exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    orders = result.orders
    buy_orders = orders[orders['type'] == 'buy']
    assert len(buy_orders) == 1
    assert buy_orders.iloc[0]['shares'] == 100

def test_backtest_when_stop_loss(self, data_source_df):

    def exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
            ctx.stop_loss = 10
    df = data_source_df[data_source_df['symbol'].isin(['SPY', 'AAPL'])]
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, ['SPY', 'AAPL'])
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.trades) == 2
    trade = result.trades.iloc[0]
    assert trade['type'] == 'long'
    assert trade['symbol'] == 'SPY'
    assert trade['entry_date'] == dates[1]
    assert trade['exit'] == trade['entry'] - 10
    assert trade['shares'] == 100
    assert trade['pnl'] == -1000
    assert trade['agg_pnl'] == -1000
    assert trade['pnl_per_bar'] == round(-1000 / trade['bars'], 2)
    assert trade['stop'] == 'loss'
    trade = result.trades.iloc[1]
    assert trade['type'] == 'long'
    assert trade['symbol'] == 'AAPL'
    assert trade['entry_date'] == dates[1]
    assert trade['exit'] == trade['entry'] - 10
    assert trade['shares'] == 100
    assert trade['pnl'] == -1000
    assert trade['agg_pnl'] == -2000
    assert trade['pnl_per_bar'] == round(-1000 / trade['bars'], 2)
    assert trade['stop'] == 'loss'
    assert len(result.orders) == 4
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'AAPL'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 100
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0
    buy_order = result.orders.iloc[1]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'SPY'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 100
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0
    sell_order = result.orders.iloc[2]
    assert sell_order['type'] == 'sell'
    assert sell_order['symbol'] == 'SPY'
    assert sell_order['shares'] == 100
    assert np.isnan(sell_order['limit_price'])
    assert sell_order['fees'] == 0
    sell_order = result.orders.iloc[3]
    assert sell_order['type'] == 'sell'
    assert sell_order['symbol'] == 'AAPL'
    assert sell_order['shares'] == 100
    assert np.isnan(sell_order['limit_price'])
    assert sell_order['fees'] == 0

def test_backtest_when_sell_before_stop_loss(self, data_source_df):

    def exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
            ctx.stop_loss = 10
        elif ctx.bars == 10:
            ctx.sell_all_shares()
    df = data_source_df[data_source_df['symbol'] == 'SPY']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.trades) == 1
    trade = result.trades.iloc[0]
    assert trade['type'] == 'long'
    assert trade['symbol'] == 'SPY'
    assert trade['entry_date'] == dates[1]
    assert trade['exit_date'] == dates[10]
    assert trade['shares'] == 100
    assert trade['stop'] is None
    assert len(result.orders) == 2
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'SPY'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 100
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0
    sell_order = result.orders.iloc[1]
    assert sell_order['type'] == 'sell'
    assert sell_order['symbol'] == 'SPY'
    assert sell_order['date'] == dates[10]
    assert sell_order['shares'] == 100
    assert np.isnan(sell_order['limit_price'])
    assert sell_order['fees'] == 0

def test_backtest_when_cancel_stop(self, data_source_df):

    def exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
            ctx.stop_loss = 10
        elif ctx.bars == 10:
            entry = tuple(ctx.long_pos().entries)[0]
            stop = next(iter(entry.stops))
            assert ctx.cancel_stop(stop_id=stop.id)
    df = data_source_df[data_source_df['symbol'] == 'SPY']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    assert not len(result.trades)
    assert len(result.orders) == 1
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'SPY'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 100
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0

def test_backtest_when_cancel_stops(self, data_source_df):

    def exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
            ctx.stop_loss = 10
            ctx.stop_trailing = 10
        elif ctx.bars == 10:
            ctx.cancel_stops('SPY')
    df = data_source_df[data_source_df['symbol'] == 'SPY']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    assert not len(result.trades)
    assert len(result.orders) == 1
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'SPY'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 100
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0

def test_backtest_when_pos_size_handler_zero_shares(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_shares = 100

    def sell_exec_fn(ctx):
        ctx.sell_shares = 100

    def pos_size_handler(ctx):
        signals = tuple(ctx.signals())
        ctx.set_shares(signals[0], shares=0)
        ctx.set_shares(signals[1], shares=0)
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(buy_exec_fn, 'SPY')
    strategy.add_execution(sell_exec_fn, 'AAPL')
    strategy.set_pos_size_handler(pos_size_handler)
    result = strategy.backtest(calc_bootstrap=False)
    assert not len(result.orders)

def test_backtest_when_no_stops(self, data_source_df):

    def exec_fn(ctx):
        if ctx.bars == 1:
            ctx.buy_shares = 100
        elif ctx.long_pos() and ctx.bars > 30:
            ctx.sell_all_shares()
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, 'SPY')
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.trades) == 1
    assert result.trades.iloc[0]['stop'] is None

def test_backtest_when_before_exec(self, data_source_df):

    def before_exec_fn(ctxs):
        assert len(ctxs) == 2
        assert isinstance(ctxs['SPY'], ExecContext)
        assert isinstance(ctxs['AAPL'], ExecContext)
        ctxs['SPY'].session['foo'] = 'bar'

    def exec_fn(ctx):
        if ctx.symbol == 'AAPL' and (not ctx.long_pos()):
            ctx.buy_shares = 200
        if ctx.symbol == 'SPY':
            assert ctx.session['foo'] == 'bar'
    df = data_source_df[data_source_df['symbol'] == 'AAPL']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, ['SPY', 'AAPL'])
    strategy.set_before_exec(before_exec_fn)
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.orders) == 1
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'AAPL'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 200
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0

def test_backtest_when_before_exec_and_no_executions(self, data_source_df):

    def before_exec_fn(ctxs):
        assert len(ctxs) == 2
        assert isinstance(ctxs['SPY'], ExecContext)
        assert isinstance(ctxs['AAPL'], ExecContext)
        if not ctxs['AAPL'].long_pos():
            ctxs['AAPL'].buy_shares = 200
    df = data_source_df[data_source_df['symbol'] == 'AAPL']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(None, ['SPY', 'AAPL'])
    strategy.set_before_exec(before_exec_fn)
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.orders) == 1
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'AAPL'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 200
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0

def test_backtest_when_after_exec(self, data_source_df):

    def after_exec_fn(ctxs):
        assert len(ctxs) == 2
        assert isinstance(ctxs['SPY'], ExecContext)
        assert isinstance(ctxs['AAPL'], ExecContext)
        if not ctxs['AAPL'].long_pos():
            ctxs['AAPL'].buy_shares = 300

    def exec_fn(ctx):
        if ctx.symbol == 'AAPL' and (not ctx.long_pos()):
            ctx.buy_shares = 200
    df = data_source_df[data_source_df['symbol'] == 'AAPL']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, ['SPY', 'AAPL'])
    strategy.set_after_exec(after_exec_fn)
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.orders) == 1
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'AAPL'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 300
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0

def test_backtest_when_after_exec_and_no_executions(self, data_source_df):

    def after_exec_fn(ctxs):
        assert len(ctxs) == 2
        assert isinstance(ctxs['SPY'], ExecContext)
        assert isinstance(ctxs['AAPL'], ExecContext)
        if not ctxs['AAPL'].long_pos():
            ctxs['AAPL'].buy_shares = 200
    df = data_source_df[data_source_df['symbol'] == 'AAPL']
    dates = df['date'].unique()
    dates = dates[dates <= np.datetime64(END_DATE)]
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(None, ['SPY', 'AAPL'])
    strategy.set_after_exec(after_exec_fn)
    result = strategy.backtest(calc_bootstrap=False)
    assert len(result.orders) == 1
    buy_order = result.orders.iloc[0]
    assert buy_order['type'] == 'buy'
    assert buy_order['symbol'] == 'AAPL'
    assert buy_order['date'] == dates[1]
    assert buy_order['shares'] == 200
    assert np.isnan(buy_order['limit_price'])
    assert buy_order['fees'] == 0

def test_backtest_when_warmup(self, data_source_df):

    def exec_fn(ctx):
        if ctx.bars <= 10:
            raise AssertionError('Warmup failed.')
        elif not ctx.long_pos():
            ctx.buy_shares = 100
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, 'SPY')
    result = strategy.backtest(warmup=10)
    assert len(result.orders) == 1

def test_backtest_when_warmup_invalid_then_error(self, data_source_df):

    def exec_fn(ctx):
        pass
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    strategy.add_execution(exec_fn, 'SPY')
    with pytest.raises(ValueError, match=re.escape('warmup must be > 0.')):
        strategy.backtest(warmup=-1)

def assert_portfolio(portfolio, cash, pnl, symbols, orders, short_positions_len, long_positions_len):
    assert portfolio.cash == cash
    assert portfolio.pnl == pnl
    assert portfolio.symbols == symbols
    assert portfolio.orders == deque(orders)
    assert len(portfolio.short_positions) == short_positions_len
    assert len(portfolio.long_positions) == long_positions_len

def assert_position(pos, symbol, shares, type, entries_len):
    assert pos.symbol == symbol
    assert pos.shares == shares
    assert pos.type == type
    assert len(pos.entries) == entries_len

