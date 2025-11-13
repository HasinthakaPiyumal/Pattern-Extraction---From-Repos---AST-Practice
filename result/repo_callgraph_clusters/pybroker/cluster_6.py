# Cluster 6

class Strategy(BacktestMixin, EvaluateMixin, IndicatorsMixin, ModelsMixin, WalkforwardMixin):
    """Class representing a trading strategy to backtest.

    Args:
        data_source: :class:`pybroker.data.DataSource` or
            :class:`pandas.DataFrame` of backtesting data.
        start_date: Starting date of the data to fetch from ``data_source``
            (inclusive).
        end_date: Ending date of the data to fetch from ``data_source``
            (inclusive).
        config: ``Optional`` :class:`pybroker.config.StrategyConfig`.
    """
    _execution_id: int = 0

    def __init__(self, data_source: Union[DataSource, pd.DataFrame], start_date: Union[str, datetime], end_date: Union[str, datetime], config: Optional[StrategyConfig]=None):
        self._verify_data_source(data_source)
        self._data_source = data_source
        self._start_date = to_datetime(start_date)
        self._end_date = to_datetime(end_date)
        verify_date_range(self._start_date, self._end_date)
        if config is not None:
            self._verify_config(config)
            self._config = config
        else:
            self._config = StrategyConfig()
        self._executions: set[Execution] = set()
        self._before_exec_fn: Optional[Callable[[Mapping[str, ExecContext]], None]] = None
        self._after_exec_fn: Optional[Callable[[Mapping[str, ExecContext]], None]] = None
        self._pos_size_handler: Optional[Callable[[PosSizeContext], None]] = None
        self._slippage_model: Optional[SlippageModel] = None
        self._scope = StaticScope.instance()
        self._logger = self._scope.logger

    def _verify_config(self, config: StrategyConfig):
        if config.initial_cash <= 0:
            raise ValueError('initial_cash must be greater than 0.')
        if config.max_long_positions is not None and config.max_long_positions <= 0:
            raise ValueError('max_long_positions must be greater than 0.')
        if config.max_short_positions is not None and config.max_short_positions <= 0:
            raise ValueError('max_short_positions must be greater than 0.')
        if config.buy_delay <= 0:
            raise ValueError('buy_delay must be greater than 0.')
        if config.sell_delay <= 0:
            raise ValueError('sell_delay must be greater than 0.')
        if config.bootstrap_samples <= 0:
            raise ValueError('bootstrap_samples must be greater than 0.')
        if config.bootstrap_sample_size <= 0:
            raise ValueError('bootstrap_sample_size must be greater than 0.')

    def _verify_data_source(self, data_source: Union[DataSource, pd.DataFrame]):
        if isinstance(data_source, pd.DataFrame):
            verify_data_source_columns(data_source)
        elif not isinstance(data_source, DataSource):
            raise TypeError(f'Invalid data_source type: {type(data_source)}')

    def set_slippage_model(self, slippage_model: Optional[SlippageModel]):
        """Sets :class:`pybroker.slippage.SlippageModel`."""
        self._slippage_model = slippage_model

    def add_execution(self, fn: Optional[Callable[[ExecContext], None]], symbols: Union[str, Iterable[str]], models: Optional[Union[ModelSource, Iterable[ModelSource]]]=None, indicators: Optional[Union[Indicator, Iterable[Indicator]]]=None):
        """Adds an execution to backtest.

        Args:
            fn: :class:`Callable` invoked on every bar of data during the
                backtest and passed an :class:`pybroker.context.ExecContext`
                for each ticker symbol in ``symbols``.
            symbols: Ticker symbols used to run ``fn``, where ``fn`` is called
                separately for each symbol.
            models: :class:`Iterable` of :class:`pybroker.model.ModelSource`\\ s
                to train/load for backtesting.
            indicators: :class:`Iterable` of
                :class:`pybroker.indicator.Indicator`\\ s to compute for
                backtesting.
        """
        symbols = frozenset((symbols,)) if isinstance(symbols, str) else frozenset(symbols)
        if not symbols:
            raise ValueError('symbols cannot be empty.')
        for sym in symbols:
            for exec in self._executions:
                if sym in exec.symbols:
                    raise ValueError(f'{sym} was already added to an execution.')
        if models is not None:
            for model in (models,) if isinstance(models, ModelSource) else models:
                if not self._scope.has_model_source(model.name):
                    raise ValueError(f'ModelSource {model.name!r} was not registered.')
                if model is not self._scope.get_model_source(model.name):
                    raise ValueError(f'ModelSource {model.name!r} does not match registered ModelSource.')
        model_names = (frozenset((models.name,)) if isinstance(models, ModelSource) else frozenset((model.name for model in models))) if models is not None else frozenset()
        if indicators is not None:
            for ind in (indicators,) if isinstance(indicators, Indicator) else indicators:
                if not self._scope.has_indicator(ind.name):
                    raise ValueError(f'Indicator {ind.name!r} was not registered.')
                if ind is not self._scope.get_indicator(ind.name):
                    raise ValueError(f'Indicator {ind.name!r} does not match registered Indicator.')
        ind_names = (frozenset((indicators.name,)) if isinstance(indicators, Indicator) else frozenset((ind.name for ind in indicators))) if indicators is not None else frozenset()
        self._execution_id += 1
        self._executions.add(Execution(id=self._execution_id, symbols=symbols, fn=fn, model_names=model_names, indicator_names=ind_names))

    def set_before_exec(self, fn: Optional[Callable[[Mapping[str, ExecContext]], None]]):
        """:class:`Callable[[Mapping[str, ExecContext]]` that runs before all
        execution functions.

        Args:
            fn: :class:`Callable` that takes a :class:`Mapping` of all ticker
                symbols to :class:`ExecContext`\\ s.
        """
        self._before_exec_fn = fn

    def set_after_exec(self, fn: Optional[Callable[[Mapping[str, ExecContext]], None]]):
        """:class:`Callable[[Mapping[str, ExecContext]]` that runs after all
        execution functions.

        Args:
            fn: :class:`Callable` that takes a :class:`Mapping` of all ticker
                symbols to :class:`ExecContext`\\ s.
        """
        self._after_exec_fn = fn

    def clear_executions(self):
        """Clears executions that were added with :meth:`.add_execution`."""
        self._executions.clear()

    def set_pos_size_handler(self, fn: Optional[Callable[[PosSizeContext], None]]):
        """Sets a :class:`Callable` that determines position sizes to use for
        buy and sell signals.

        Args:
            fn: :class:`Callable` invoked before placing orders for buy and
                sell signals, and is passed a
                :class:`pybroker.context.PosSizeContext`.
        """
        self._pos_size_handler = fn

    def backtest(self, start_date: Optional[Union[str, datetime]]=None, end_date: Optional[Union[str, datetime]]=None, timeframe: str='', between_time: Optional[tuple[str, str]]=None, days: Optional[Union[str, Day, Iterable[Union[str, Day]]]]=None, lookahead: int=1, train_size: float=0, shuffle: bool=False, calc_bootstrap: bool=False, disable_parallel: bool=False, warmup: Optional[int]=None, portfolio: Optional[Portfolio]=None, adjust: Optional[Any]=None) -> TestResult:
        """Backtests the trading strategy by running executions that were added
        with :meth:`.add_execution`.

        Args:
            start_date: Starting date of the backtest (inclusive). Must be
                within ``start_date`` and ``end_date`` range that was passed to
                :meth:`.__init__`.
            end_date: Ending date of the backtest (inclusive). Must be
                within ``start_date`` and ``end_date`` range that was passed to
                :meth:`.__init__`.
            timeframe: Formatted string that specifies the timeframe
                resolution of the backtesting data. The timeframe string
                supports the following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks

                An example timeframe string is ``1h 30m``.
            between_time: ``tuple[str, str]`` of times of day e.g.
                ('9:30', '16:00') used to filter the backtesting data
                (inclusive).
            days: Days (e.g. ``"mon"``, ``"tues"`` etc.) used to filter the
                backtesting data.
            lookahead: Number of bars in the future of the target prediction.
                For example, predicting returns for the next bar would have a
                ``lookahead`` of ``1``. This quantity is needed to prevent
                training data from leaking into the test boundary.
            train_size: Amount of :class:`pybroker.data.DataSource` data to use
                for training, where the max ``train_size`` is ``1``. For
                example, a ``train_size`` of ``0.9`` would result in 90% of
                data being used for training and the remaining 10% of data
                being used for testing.
            shuffle: Whether to randomly shuffle the data used for training.
                Defaults to ``False``. Disabled when model caching is enabled
                via :meth:`pybroker.cache.enable_model_cache`.
            calc_bootstrap: Whether to compute randomized bootstrap evaluation
                metrics. Defaults to ``False``.
            disable_parallel: If ``True``,
                :class:`pybroker.indicator.Indicator` data is computed
                serially. If ``False``, :class:`pybroker.indicator.Indicator`
                data is computed in parallel using multiple processes.
                Defaults to ``False``.
            warmup: Number of bars that need to pass before running the
                executions.
            portfolio: Custom :class:`pybroker.portfolio.Portfolio` to use for
                backtests.
            adjust: The type of adjustment to make to the
                :class:`pybroker.data.DataSource`.

        Returns:
            :class:`.TestResult` containing portfolio balances, order
            history, and evaluation metrics.
        """
        return self.walkforward(windows=1, lookahead=lookahead, start_date=start_date, end_date=end_date, timeframe=timeframe, between_time=between_time, days=days, train_size=train_size, shuffle=shuffle, calc_bootstrap=calc_bootstrap, disable_parallel=disable_parallel, warmup=warmup, portfolio=portfolio, adjust=adjust)

    def walkforward(self, windows: int, lookahead: int=1, start_date: Optional[Union[str, datetime]]=None, end_date: Optional[Union[str, datetime]]=None, timeframe: str='', between_time: Optional[tuple[str, str]]=None, days: Optional[Union[str, Day, Iterable[Union[str, Day]]]]=None, train_size: float=0.5, shuffle: bool=False, calc_bootstrap: bool=False, disable_parallel: bool=False, warmup: Optional[int]=None, portfolio: Optional[Portfolio]=None, adjust: Optional[Any]=None) -> TestResult:
        """Backtests the trading strategy using `Walkforward Analysis
        <https://www.pybroker.com/en/latest/notebooks/6.%20Training%20a%20Model.html#Walkforward-Analysis>`_.
        Backtesting data supplied by the :class:`pybroker.data.DataSource` is
        divided into ``windows`` number of equal sized time windows, with each
        window split into train and test data as specified by ``train_size``.
        The backtest "walks forward" in time through each window, running
        executions that were added with :meth:`.add_execution`.

        Args:
            windows: Number of walkforward time windows.
            start_date: Starting date of the Walkforward Analysis (inclusive).
                Must be within ``start_date`` and ``end_date`` range that was
                passed to :meth:`.__init__`.
            end_date: Ending date of the Walkforward Analysis (inclusive). Must
                be within ``start_date`` and ``end_date`` range that was passed
                to :meth:`.__init__`.
            timeframe: Formatted string that specifies the timeframe
                resolution of the backtesting data. The timeframe string
                supports the following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks

                An example timeframe string is ``1h 30m``.
            between_time: ``tuple[str, str]`` of times of day e.g.
                ('9:30', '16:00') used to filter the backtesting data
                (inclusive).
            days: Days (e.g. ``"mon"``, ``"tues"`` etc.) used to filter the
                backtesting data.
            lookahead: Number of bars in the future of the target prediction.
                For example, predicting returns for the next bar would have a
                ``lookahead`` of ``1``. This quantity is needed to prevent
                training data from leaking into the test boundary.
            train_size: Amount of :class:`pybroker.data.DataSource` data to use
                for training, where the max ``train_size`` is ``1``. For
                example, a ``train_size`` of ``0.9`` would result in 90% of
                data being used for training and the remaining 10% of data
                being used for testing.
            shuffle: Whether to randomly shuffle the data used for training.
                Defaults to ``False``. Disabled when model caching is enabled
                via :meth:`pybroker.cache.enable_model_cache`.
            calc_bootstrap: Whether to compute randomized bootstrap evaluation
                metrics. Defaults to ``False``.
            disable_parallel: If ``True``,
                :class:`pybroker.indicator.Indicator` data is computed
                serially. If ``False``, :class:`pybroker.indicator.Indicator`
                data is computed in parallel using multiple processes.
                Defaults to ``False``.
            warmup: Number of bars that need to pass before running the
                executions.
            portfolio: Custom :class:`pybroker.portfolio.Portfolio` to use for
                backtests.
            adjust: The type of adjustment to make to the
                :class:`pybroker.data.DataSource`.

        Returns:
            :class:`.TestResult` containing portfolio balances, order
            history, and evaluation metrics.
        """
        if warmup is not None and warmup < 1:
            raise ValueError('warmup must be > 0.')
        scope = StaticScope.instance()
        try:
            scope.freeze_data_cols()
            if not self._executions:
                raise ValueError('No executions were added.')
            start_dt = self._start_date if start_date is None else to_datetime(start_date)
            if start_dt < self._start_date or start_dt > self._end_date:
                raise ValueError(f'start_date must be between {self._start_date} and {self._end_date}.')
            end_dt = self._end_date if end_date is None else to_datetime(end_date)
            if end_dt < self._start_date or end_dt > self._end_date:
                raise ValueError(f'end_date must be between {self._start_date} and {self._end_date}.')
            if start_dt is not None and end_dt is not None:
                verify_date_range(start_dt, end_dt)
            self._logger.walkforward_start(start_dt, end_dt)
            df = self._fetch_data(timeframe, adjust)
            day_ids = self._to_day_ids(days)
            df = self._filter_dates(df=df, start_date=start_dt, end_date=end_dt, between_time=between_time, days=day_ids)
            tf_seconds = to_seconds(timeframe)
            indicator_data = self._fetch_indicators(df=df, cache_date_fields=CacheDateFields(start_date=start_dt, end_date=end_dt, tf_seconds=tf_seconds, between_time=between_time, days=day_ids), disable_parallel=disable_parallel)
            train_only = self._before_exec_fn is None and self._after_exec_fn is None and all(map(lambda e: e.fn is None, self._executions))
            if portfolio is None:
                portfolio = Portfolio(self._config.initial_cash, self._config.fee_mode, self._config.fee_amount, self._config.subtract_fees, self._fractional_shares_enabled(), self._config.position_mode, self._config.max_long_positions, self._config.max_short_positions, self._config.return_stops)
            signals = self._run_walkforward(portfolio=portfolio, df=df, indicator_data=indicator_data, tf_seconds=tf_seconds, between_time=between_time, days=day_ids, windows=windows, lookahead=lookahead, train_size=train_size, shuffle=shuffle, train_only=train_only, warmup=warmup)
            if train_only:
                self._logger.walkforward_completed()
            return self._to_test_result(start_dt, end_dt, portfolio, calc_bootstrap, train_only, signals if self._config.return_signals else None)
        finally:
            scope.unfreeze_data_cols()

    def _to_day_ids(self, days: Optional[Union[str, Day, Iterable[Union[str, Day]]]]) -> Optional[tuple[int]]:
        if days is None:
            return None
        days = (days,) if isinstance(days, str) or isinstance(days, Day) else days
        return tuple(sorted((day.value if isinstance(day, Day) else Day[day.upper()].value for day in set(days))))

    def _fractional_shares_enabled(self):
        return self._config.enable_fractional_shares or isinstance(self._data_source, AlpacaCrypto)

    def _run_walkforward(self, portfolio: Portfolio, df: pd.DataFrame, indicator_data: dict[IndicatorSymbol, pd.Series], tf_seconds: int, between_time: Optional[tuple[str, str]], days: Optional[tuple[int]], windows: int, lookahead: int, train_size: float, shuffle: bool, train_only: bool, warmup: Optional[int]) -> dict[str, pd.DataFrame]:
        sessions: dict[str, dict] = defaultdict(dict)
        exit_dates: dict[str, np.datetime64] = {}
        if self._config.exit_on_last_bar:
            for exec in self._executions:
                for sym in exec.symbols:
                    sym_dates = df[df[DataCol.SYMBOL.value] == sym][DataCol.DATE.value].values
                    if len(sym_dates):
                        sym_dates.sort()
                        exit_dates[sym] = sym_dates[-1]
        signals: dict[str, pd.DataFrame] = {}
        for train_idx, test_idx in self.walkforward_split(df=df, windows=windows, lookahead=lookahead, train_size=train_size, shuffle=shuffle):
            models: dict[ModelSymbol, TrainedModel] = {}
            train_data = df.loc[train_idx]
            test_data = df.loc[test_idx]
            if not train_data.empty:
                model_syms = {ModelSymbol(model_name, sym) for sym in train_data[DataCol.SYMBOL.value].unique() for execution in self._executions for model_name in execution.model_names if sym in execution.symbols}
                train_dates = get_unique_sorted_dates(train_data[DataCol.DATE.value])
                models = self.train_models(model_syms=model_syms, train_data=train_data, test_data=test_data, indicator_data=indicator_data, cache_date_fields=CacheDateFields(start_date=to_datetime(train_dates[0]), end_date=to_datetime(train_dates[-1]), tf_seconds=tf_seconds, between_time=between_time, days=days))
            if test_data.empty:
                return signals
            split_signals = self.backtest_executions(config=self._config, executions=self._executions, before_exec_fn=self._before_exec_fn, after_exec_fn=self._after_exec_fn, sessions=sessions, models=models, indicator_data=indicator_data, test_data=test_data, portfolio=portfolio, pos_size_handler=self._pos_size_handler, exit_dates=exit_dates, train_only=train_only, slippage_model=self._slippage_model, enable_fractional_shares=self._fractional_shares_enabled(), round_fill_price=self._config.round_fill_price, warmup=warmup)
            for sym, signals_df in split_signals.items():
                if sym in signals:
                    signals[sym] = pd.concat([signals[sym], signals_df])
                else:
                    signals[sym] = signals_df
        return signals

    def _filter_dates(self, df: pd.DataFrame, start_date: datetime, end_date: datetime, between_time: Optional[tuple[str, str]], days: Optional[tuple[int]]) -> pd.DataFrame:
        if start_date != self._start_date or end_date != self._end_date:
            df = _between(df, start_date, end_date).reset_index(drop=True)
        if df[DataCol.DATE.value].dt.tz is not None:
            df[DataCol.DATE.value] = df[DataCol.DATE.value].dt.tz_convert(None)
        is_time_range = between_time is not None or days is not None
        if is_time_range:
            df = df.reset_index(drop=True).set_index(DataCol.DATE.value)
        if days is not None:
            self._logger.info_walkforward_on_days(days)
            df = df[df.index.weekday.isin(frozenset(days))]
        if between_time is not None:
            if len(between_time) != 2:
                raise ValueError(f'between_time must be a tuple[str, str] of start time and end time, received {between_time!r}.')
            self._logger.info_walkforward_between_time(between_time)
            df = df.between_time(*between_time)
        if is_time_range:
            df = df.reset_index()
        return df

    def _fetch_indicators(self, df: pd.DataFrame, cache_date_fields: CacheDateFields, disable_parallel: bool) -> dict[IndicatorSymbol, pd.Series]:
        indicator_syms = set()
        for execution in self._executions:
            for sym in execution.symbols:
                for model_name in execution.model_names:
                    ind_names = self._scope.get_indicator_names(model_name)
                    for ind_name in ind_names:
                        indicator_syms.add(IndicatorSymbol(ind_name, sym))
                for ind_name in execution.indicator_names:
                    indicator_syms.add(IndicatorSymbol(ind_name, sym))
        return self.compute_indicators(df=df, indicator_syms=indicator_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)

    def _fetch_data(self, timeframe: str, adjust: Optional[Any]) -> pd.DataFrame:
        unique_syms = {sym for execution in self._executions for sym in execution.symbols}
        if isinstance(self._data_source, DataSource):
            df = self._data_source.query(unique_syms, self._start_date, self._end_date, timeframe, adjust)
        else:
            df = _between(self._data_source, self._start_date, self._end_date)
            df = df[df[DataCol.SYMBOL.value].isin(unique_syms)]
        if df.empty:
            raise ValueError('DataSource is empty.')
        return df.reset_index(drop=True)

    def _to_test_result(self, start_date: datetime, end_date: datetime, portfolio: Portfolio, calc_bootstrap: bool, train_only: bool, signals: Optional[dict[str, pd.DataFrame]]) -> TestResult:
        if train_only:
            return TestResult(start_date=start_date, end_date=end_date, portfolio=pd.DataFrame(), positions=pd.DataFrame(), orders=pd.DataFrame(), trades=pd.DataFrame(), metrics=EvalMetrics(), metrics_df=pd.DataFrame(), bootstrap=None, signals=signals, stops=None)
        pos_df = pd.DataFrame.from_records(portfolio.position_bars, columns=PositionBar._fields)
        for col in ('close', 'equity', 'market_value', 'margin', 'unrealized_pnl'):
            pos_df[col] = quantize(pos_df, col, self._config.round_test_result)
        pos_df.set_index(['symbol', 'date'], inplace=True)
        portfolio_df = pd.DataFrame.from_records(portfolio.bars, columns=PortfolioBar._fields, index='date')
        for col in ('cash', 'equity', 'margin', 'market_value', 'pnl', 'unrealized_pnl', 'fees'):
            portfolio_df[col] = quantize(portfolio_df, col, self._config.round_test_result)
        orders_df = pd.DataFrame.from_records(portfolio.orders, columns=Order._fields, index='id')
        for col in ('limit_price', 'fill_price', 'fees'):
            orders_df[col] = quantize(orders_df, col, self._config.round_test_result)
        trades_df = pd.DataFrame.from_records(portfolio.trades, columns=Trade._fields, index='id')
        trades_df['bars'] = trades_df['bars'].astype(int)
        for col in ('entry', 'exit', 'pnl', 'return_pct', 'agg_pnl', 'pnl_per_bar', 'mae', 'mfe'):
            trades_df[col] = quantize(trades_df, col, self._config.round_test_result)
        shares_type = float if self._fractional_shares_enabled() else int
        pos_df['long_shares'] = pos_df['long_shares'].astype(shares_type)
        pos_df['short_shares'] = pos_df['short_shares'].astype(shares_type)
        orders_df['shares'] = orders_df['shares'].astype(shares_type)
        trades_df['shares'] = trades_df['shares'].astype(shares_type)
        eval_result = self.evaluate(portfolio_df=portfolio_df, trades_df=trades_df, calc_bootstrap=calc_bootstrap, bootstrap_sample_size=self._config.bootstrap_sample_size, bootstrap_samples=self._config.bootstrap_samples, bars_per_year=self._config.bars_per_year)
        metrics = [(k, v) for k, v in dataclasses.asdict(eval_result.metrics).items() if v is not None]
        metrics_df = pd.DataFrame(metrics, columns=['name', 'value'])
        stops_df = None
        if self._config.return_stops:
            stops_df = pd.DataFrame.from_records(portfolio._stop_records, columns=StopRecord._fields)
        self._logger.walkforward_completed()
        return TestResult(start_date=start_date, end_date=end_date, portfolio=portfolio_df, positions=pos_df, orders=orders_df, trades=trades_df, metrics=eval_result.metrics, metrics_df=metrics_df, bootstrap=eval_result.bootstrap, signals=signals, stops=stops_df)

def add_execution(self, fn: Optional[Callable[[ExecContext], None]], symbols: Union[str, Iterable[str]], models: Optional[Union[ModelSource, Iterable[ModelSource]]]=None, indicators: Optional[Union[Indicator, Iterable[Indicator]]]=None):
    """Adds an execution to backtest.

        Args:
            fn: :class:`Callable` invoked on every bar of data during the
                backtest and passed an :class:`pybroker.context.ExecContext`
                for each ticker symbol in ``symbols``.
            symbols: Ticker symbols used to run ``fn``, where ``fn`` is called
                separately for each symbol.
            models: :class:`Iterable` of :class:`pybroker.model.ModelSource`\\ s
                to train/load for backtesting.
            indicators: :class:`Iterable` of
                :class:`pybroker.indicator.Indicator`\\ s to compute for
                backtesting.
        """
    symbols = frozenset((symbols,)) if isinstance(symbols, str) else frozenset(symbols)
    if not symbols:
        raise ValueError('symbols cannot be empty.')
    for sym in symbols:
        for exec in self._executions:
            if sym in exec.symbols:
                raise ValueError(f'{sym} was already added to an execution.')
    if models is not None:
        for model in (models,) if isinstance(models, ModelSource) else models:
            if not self._scope.has_model_source(model.name):
                raise ValueError(f'ModelSource {model.name!r} was not registered.')
            if model is not self._scope.get_model_source(model.name):
                raise ValueError(f'ModelSource {model.name!r} does not match registered ModelSource.')
    model_names = (frozenset((models.name,)) if isinstance(models, ModelSource) else frozenset((model.name for model in models))) if models is not None else frozenset()
    if indicators is not None:
        for ind in (indicators,) if isinstance(indicators, Indicator) else indicators:
            if not self._scope.has_indicator(ind.name):
                raise ValueError(f'Indicator {ind.name!r} was not registered.')
            if ind is not self._scope.get_indicator(ind.name):
                raise ValueError(f'Indicator {ind.name!r} does not match registered Indicator.')
    ind_names = (frozenset((indicators.name,)) if isinstance(indicators, Indicator) else frozenset((ind.name for ind in indicators))) if indicators is not None else frozenset()
    self._execution_id += 1
    self._executions.add(Execution(id=self._execution_id, symbols=symbols, fn=fn, model_names=model_names, indicator_names=ind_names))

def _run_walkforward(self, portfolio: Portfolio, df: pd.DataFrame, indicator_data: dict[IndicatorSymbol, pd.Series], tf_seconds: int, between_time: Optional[tuple[str, str]], days: Optional[tuple[int]], windows: int, lookahead: int, train_size: float, shuffle: bool, train_only: bool, warmup: Optional[int]) -> dict[str, pd.DataFrame]:
    sessions: dict[str, dict] = defaultdict(dict)
    exit_dates: dict[str, np.datetime64] = {}
    if self._config.exit_on_last_bar:
        for exec in self._executions:
            for sym in exec.symbols:
                sym_dates = df[df[DataCol.SYMBOL.value] == sym][DataCol.DATE.value].values
                if len(sym_dates):
                    sym_dates.sort()
                    exit_dates[sym] = sym_dates[-1]
    signals: dict[str, pd.DataFrame] = {}
    for train_idx, test_idx in self.walkforward_split(df=df, windows=windows, lookahead=lookahead, train_size=train_size, shuffle=shuffle):
        models: dict[ModelSymbol, TrainedModel] = {}
        train_data = df.loc[train_idx]
        test_data = df.loc[test_idx]
        if not train_data.empty:
            model_syms = {ModelSymbol(model_name, sym) for sym in train_data[DataCol.SYMBOL.value].unique() for execution in self._executions for model_name in execution.model_names if sym in execution.symbols}
            train_dates = get_unique_sorted_dates(train_data[DataCol.DATE.value])
            models = self.train_models(model_syms=model_syms, train_data=train_data, test_data=test_data, indicator_data=indicator_data, cache_date_fields=CacheDateFields(start_date=to_datetime(train_dates[0]), end_date=to_datetime(train_dates[-1]), tf_seconds=tf_seconds, between_time=between_time, days=days))
        if test_data.empty:
            return signals
        split_signals = self.backtest_executions(config=self._config, executions=self._executions, before_exec_fn=self._before_exec_fn, after_exec_fn=self._after_exec_fn, sessions=sessions, models=models, indicator_data=indicator_data, test_data=test_data, portfolio=portfolio, pos_size_handler=self._pos_size_handler, exit_dates=exit_dates, train_only=train_only, slippage_model=self._slippage_model, enable_fractional_shares=self._fractional_shares_enabled(), round_fill_price=self._config.round_fill_price, warmup=warmup)
        for sym, signals_df in split_signals.items():
            if sym in signals:
                signals[sym] = pd.concat([signals[sym], signals_df])
            else:
                signals[sym] = signals_df
    return signals

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

def _format_time(self, start_seconds: float) -> str:
    delta = time.time() - start_seconds
    return str(datetime.timedelta(seconds=round(delta)))

class StaticScope:
    """A static registry of data and object references.

    Attributes:
        logger: :class:`pybroker.log.Logger`
        data_source_cache: :class:`diskcache.Cache` that stores data retrieved
            from :class:`pybroker.data.DataSource`.
        data_source_cache_ns: Namespace set for  :attr:`.data_source_cache`.
        indicator_cache: :class:`diskcache.Cache` that stores
            :class:`pybroker.indicator.Indicator` data.
        indicator_cache_ns: Namespace set for :attr:`.indicator_cache`.
        model_cache: :class:`diskcache.Cache` that stores trained models.
        model_cache_ns: Namespace set for :attr:`.model_cache`.
        default_data_cols: Default data columns in :class:`pandas.DataFrame`
            retrieved from a :class:`pybroker.data.DataSource`.
        custom_data_cols: User-defined data columns in
            :class:`pandas.DataFrame` retrieved from a
            :class:`pybroker.data.DataSource`.
    """
    __instance = None

    def __init__(self):
        self.logger = Logger(self)
        self.data_source_cache: Optional[Cache] = None
        self.data_source_cache_ns: str = ''
        self.indicator_cache: Optional[Cache] = None
        self.indicator_cache_ns: str = ''
        self.model_cache: Optional[Cache] = None
        self.model_cache_ns: str = ''
        self._indicators = {}
        self._model_sources = {}
        self.default_data_cols = frozenset((DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value, DataCol.VWAP.value))
        self.custom_data_cols = set()
        self._cols_frozen: bool = False
        self._params: dict[str, Any] = {}

    def set_indicator(self, indicator):
        """Stores :class:`pybroker.indicator.Indicator` in static scope."""
        self._indicators[indicator.name] = indicator

    def has_indicator(self, name: str) -> bool:
        """Whether :class:`pybroker.indicator.Indicator` is stored in static
        scope.
        """
        return name in self._indicators

    def get_indicator(self, name: str):
        """Retrieves a :class:`pybroker.indicator.Indicator` from static
        scope."""
        if not self.has_indicator(name):
            raise ValueError(f'Indicator {name!r} does not exist.')
        return self._indicators[name]

    def get_indicator_names(self, model_name: str) -> tuple[str]:
        """Returns a ``tuple[str]`` of all
        :class:`pybroker.indicator.Indicator` names that are registered with
        :class:`pybroker.model.ModelSource` having ``model_name``.
        """
        return self._model_sources[model_name].indicators

    def set_model_source(self, source):
        """Stores :class:`pybroker.model.ModelSource` in static scope."""
        self._model_sources[source.name] = source

    def has_model_source(self, name: str) -> bool:
        """Whether :class:`pybroker.model.ModelSource` is stored in static
        scope.
        """
        return name in self._model_sources

    def get_model_source(self, name: str):
        """Retrieves a :class:`pybroker.model.ModelSource` from static
        scope.
        """
        if not self.has_model_source(name):
            raise ValueError(f'ModelSource {name!r} does not exist.')
        return self._model_sources[name]

    def register_custom_cols(self, names: Union[str, Iterable[str]], *args):
        """Registers user-defined column names."""
        self._verify_unfrozen_cols()
        if isinstance(names, str):
            names = (names, *args)
        else:
            names = (*names, *args)
        names = filter(lambda col: col not in self.default_data_cols, names)
        self.custom_data_cols.update(names)

    def unregister_custom_cols(self, names: Union[str, Iterable[str]], *args):
        """Unregisters user-defined column names."""
        self._verify_unfrozen_cols()
        if isinstance(names, str):
            names = (names, *args)
        else:
            names = (*names, *args)
        self.custom_data_cols.difference_update(names)

    @property
    def all_data_cols(self) -> frozenset[str]:
        """All registered data column names."""
        return self.default_data_cols | self.custom_data_cols

    def _verify_unfrozen_cols(self):
        if self._cols_frozen:
            raise ValueError('Cannot modify columns when strategy is running.')

    def freeze_data_cols(self):
        """Prevents additional data columns from being registered."""
        self._cols_frozen = True

    def unfreeze_data_cols(self):
        """Allows additional data columns to be registered if
        :func:`pybroker.scope.StaticScope.freeze_data_cols` was called.
        """
        self._cols_frozen = False

    def param(self, name: str, value: Optional[Any]=_EMPTY_PARAM) -> Optional[Any]:
        """Get or set a global parameter."""
        if value is _EMPTY_PARAM:
            return self._params.get(name, None)
        self._params[name] = value
        return value

    @classmethod
    def instance(cls) -> 'StaticScope':
        """Returns singleton instance."""
        if cls.__instance is None:
            cls.__instance = StaticScope()
        return cls.__instance

def get_indicator(self, name: str):
    """Retrieves a :class:`pybroker.indicator.Indicator` from static
        scope."""
    if not self.has_indicator(name):
        raise ValueError(f'Indicator {name!r} does not exist.')
    return self._indicators[name]

class ColumnScope:
    """Caches and retrieves column data queried from :class:`pandas.DataFrame`.

    Args:
        df: :class:`pandas.DataFrame` containing the column data.
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df.sort_index()
        self._symbols = frozenset(df.index.get_level_values(0).unique())
        self._sym_cols: dict[str, dict[str, Optional[NDArray]]] = defaultdict(dict)

    def fetch_dict(self, symbol: str, names: Iterable[str], end_index: Optional[int]=None) -> dict[str, Optional[NDArray]]:
        """Fetches a ``dict`` of column data for ``symbol``.

        Args:
            symbol: Ticker symbol to query.
            names: Names of columns to query.
            end_index: Truncates column values (exclusive). If ``None``, then
                column values are not truncated.

        Returns:
            ``dict`` mapping column names to :class:`numpy.ndarray`\\ s of
            column values.
        """
        result: dict[str, Optional[NDArray]] = {}
        if not names:
            return result
        sym_dfs: dict[str, pd.DataFrame] = {}
        for name in names:
            if symbol in self._sym_cols and name in self._sym_cols[symbol]:
                result[name] = self._sym_cols[symbol][name]
                if result[name] is not None:
                    result[name] = result[name][:end_index]
                continue
            if symbol in sym_dfs:
                sym_df = sym_dfs[symbol]
            else:
                if symbol not in self._symbols:
                    raise ValueError(f'Symbol not found: {symbol}.')
                sym_df = self._df.loc[pd.IndexSlice[symbol, :]].reset_index()
                sym_dfs[symbol] = sym_df
            if name not in sym_df.columns:
                self._sym_cols[symbol][name] = None
                result[name] = None
                continue
            array = sym_df[name].to_numpy()
            self._sym_cols[symbol][name] = array
            result[name] = array[:end_index]
        return result

    def fetch(self, symbol: str, name: str, end_index: Optional[int]=None) -> Optional[NDArray]:
        """Fetches a :class:`numpy.ndarray` of column data for ``symbol``.

        Args:
            symbol: Ticker symbol to query.
            name: Name of column to query.
            end_index: Truncates column values (exclusive). If ``None``, then
                column values are not truncated.

        Returns:
            :class:`numpy.ndarray` of column data for every bar until
            ``end_index`` (when specified).
        """
        result = self.fetch_dict(symbol, (name,), end_index)
        return result.get(name, None)

    def bar_data_from_data_columns(self, symbol: str, end_index: int) -> BarData:
        """Returns a new :class:`pybroker.common.BarData` instance containing
        column data of default and custom data columns registered with
        :class:`.StaticScope`.

        Args:
            symbol: Ticker symbol to query.
            end_index: Truncates column values (exclusive). If ``None``, then
                column values are not truncated.
        """
        static_scope = StaticScope.instance()
        default_col_data = self.fetch_dict(symbol, static_scope.default_data_cols, end_index)
        custom_col_data = self.fetch_dict(symbol, static_scope.custom_data_cols, end_index)
        return BarData(**default_col_data, **custom_col_data)

def __init__(self, df: pd.DataFrame):
    self._df = df.sort_index()
    self._symbols = frozenset(df.index.get_level_values(0).unique())
    self._sym_cols: dict[str, dict[str, Optional[NDArray]]] = defaultdict(dict)

class PendingOrderScope:
    """Stores :class:`.PendingOrder`\\ s"""
    _order_id: int = 0

    def __init__(self):
        self._orders: dict[int, PendingOrder] = {}
        self._sym_orders: dict[str, set[PendingOrder]] = defaultdict(set)

    def contains(self, order_id: int) -> bool:
        """Returns whether a :class:`.PendingOrder` exists with
        ``order_id``.
        """
        return order_id in self._orders

    def add(self, type: Literal['buy', 'sell'], symbol: str, created: np.datetime64, exec_date: np.datetime64, shares: Decimal, limit_price: Optional[Decimal], fill_price: Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]) -> int:
        """Creates a :class:`.PendingOrder`.

        Args:
            type: Type of order, either ``buy`` or ``sell``.
            symbol: Ticker symbol of the order.
            created: Date the order was created.
            exec_date: Date the order will be executed.
            shares: Number of shares to be bought or sold.
            limit_price: Limit price to use for the order.
            fill_price: Price that the order will be filled at.

        Returns:
            ID of the :class:`.PendingOrder`.
        """
        self._order_id += 1
        order = PendingOrder(id=self._order_id, type=type, symbol=symbol, created=created, exec_date=exec_date, shares=shares, limit_price=limit_price, fill_price=fill_price)
        self._orders[self._order_id] = order
        self._sym_orders[symbol].add(order)
        return order.id

    def remove(self, order_id: int) -> bool:
        """Removes a :class:`.PendingOrder` with ``order_id```."""
        if order_id in self._orders:
            order = self._orders[order_id]
            del self._orders[order_id]
            if order.symbol in self._sym_orders and order in self._sym_orders[order.symbol]:
                self._sym_orders[order.symbol].remove(order)
            return True
        return False

    def remove_all(self, symbol: Optional[str]=None):
        """Removes all :class:`.PendingOrder`\\ s."""
        if symbol is None:
            cancel_ids = tuple(self._orders.keys())
            for order_id in cancel_ids:
                self.remove(order_id)
        elif symbol in self._sym_orders:
            cancel_ids = tuple((order.id for order in self._sym_orders[symbol]))
            for order_id in cancel_ids:
                self.remove(order_id)

    def orders(self, symbol: Optional[str]=None) -> Iterable[PendingOrder]:
        """Returns an :class:`Iterable` of :class:`.PendingOrder`\\ s."""
        if symbol is None:
            return self._orders.values()
        else:
            if symbol not in self._sym_orders:
                return []
            return self._sym_orders[symbol]

def __init__(self):
    self._orders: dict[int, PendingOrder] = {}
    self._sym_orders: dict[str, set[PendingOrder]] = defaultdict(set)

def _decorate_indicator_fn(ind_name: str):
    fn = StaticScope.instance().get_indicator(ind_name).__call__

    def decorated_indicator_fn(symbol: str, ind_name: str, date: NDArray[np.datetime64], open: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: Optional[NDArray[np.float64]], vwap: Optional[NDArray[np.float64]], custom_col_data: Mapping[str, Optional[NDArray]]) -> tuple[IndicatorSymbol, pd.Series]:
        bar_data = BarData(date=date, open=open, high=high, low=low, close=close, volume=volume, vwap=vwap, **custom_col_data)
        series = fn(bar_data)
        return (IndicatorSymbol(ind_name, symbol), series)
    return decorated_indicator_fn

@njit
def max_drawdown_percent(returns: NDArray[np.float64]) -> tuple[float, Optional[int]]:
    """Computes maximum drawdown, measured in percentage loss.

    Args:
        returns: Array of returns centered at 0.

    Returns:
        - Maximum drawdown, measured in percentage loss.
        - Index of the maximum drawdown.
    """
    returns = returns + 1
    n = len(returns)
    if not n:
        return (0, None)
    cumulative = 1.0
    max_equity = 1.0
    dd = 0.0
    index = None
    for i, r in enumerate(returns):
        cumulative *= r
        if cumulative > max_equity:
            max_equity = cumulative
        elif max_equity > 0:
            loss = (cumulative / max_equity - 1) * 100
            if loss < dd:
                dd = loss
                index = i
    return (dd, index)

class TestStaticScope:

    def test_set_and_get_indicator(self, scope, hhv_ind):
        scope.set_indicator(hhv_ind)
        assert scope.has_indicator(hhv_ind.name)
        assert scope.get_indicator(hhv_ind.name) == hhv_ind

    def test_get_indicator_when_not_found_then_error(self, scope):
        with pytest.raises(ValueError, match=re.escape("Indicator 'foo' does not exist.")):
            scope.get_indicator('foo')

    def test_set_and_get_model_source(self, scope, model_source):
        scope.set_model_source(model_source)
        assert scope.has_model_source(model_source.name)
        assert scope.get_model_source(model_source.name) == model_source

    def test_get_model_source_when_not_found_then_error(self, scope):
        with pytest.raises(ValueError, match=re.escape("ModelSource 'foo' does not exist.")):
            scope.get_model_source('foo')

    def test_get_indicator_names(self, scope, model_source, ind_names):
        scope.set_model_source(model_source)
        assert set(scope.get_indicator_names(model_source.name)) == set(ind_names)

def test_set_and_get_indicator(self, scope, hhv_ind):
    scope.set_indicator(hhv_ind)
    assert scope.has_indicator(hhv_ind.name)
    assert scope.get_indicator(hhv_ind.name) == hhv_ind

class TestBacktestMixin:

    @pytest.mark.parametrize('pos_size_handler, expected_buy_shares, expected_sell_shares', [(None, 200, 100), (pos_size_handler, 1000, 2000)])
    def test_backtest_executions(self, data_source_df, pos_size_handler, expected_buy_shares, expected_sell_shares):

        def buy_exec_fn(ctx):
            ctx.buy_fill_price = PriceType.CLOSE
            ctx.buy_limit_price = 100
            ctx.buy_shares = 200

        def sell_exec_fn(ctx):
            ctx.sell_fill_price = PriceType.CLOSE
            ctx.sell_limit_price = 50.5
            ctx.sell_shares = 100
        buy_exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        sell_exec = Execution(id=2, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {buy_exec, sell_exec}
        mock_portfolio = Mock()
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=pos_size_handler, exit_dates={})
        buy_df = data_source_df[data_source_df['symbol'] == 'SPY']
        buy_dates = buy_df['date'].unique()[1:]
        assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
        for i, date in enumerate(buy_dates):
            _, kwargs = mock_portfolio.buy.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == 'SPY'
            assert kwargs['shares'] == expected_buy_shares
            assert kwargs['fill_price'] == Decimal(str(round(buy_df[buy_df['date'] == date]['close'].values[0], 2)))
            assert kwargs['limit_price'] == 100
        sell_df = data_source_df[data_source_df['symbol'] == 'AAPL']
        sell_dates = sell_df['date'].unique()[1:]
        assert len(mock_portfolio.sell.call_args_list) == len(sell_dates)
        for i, date in enumerate(sell_dates):
            _, kwargs = mock_portfolio.sell.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == 'AAPL'
            assert kwargs['shares'] == expected_sell_shares
            assert kwargs['fill_price'] == Decimal(str(round(sell_df[sell_df['date'] == date]['close'].values[0], 2)))
            assert kwargs['limit_price'] == 50.5

    def test_backtest_when_pos_size_handler_and_cover(self, data_source_df):

        def pos_size_handler(ctx):
            signals = tuple(ctx.signals())
            ctx.set_shares(signals[0], shares=10)
            ctx.set_shares(signals[1], shares=20)
            assert isinstance(ctx.sessions['SPY'], dict)
            assert isinstance(ctx.sessions['AAPL'], dict)

        def buy_exec_fn(ctx):
            ctx.cover_fill_price = 1
            ctx.cover_shares = 2

        def sell_exec_fn(ctx):
            ctx.sell_fill_price = 1
            ctx.sell_shares = 1
        buy_exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        sell_exec = Execution(id=2, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {buy_exec, sell_exec}
        portfolio = Portfolio(1000000)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=pos_size_handler, exit_dates={})
        buy_df = data_source_df[data_source_df['symbol'] == 'SPY']
        buy_dates = buy_df['date'].unique()[1:]
        sell_df = data_source_df[data_source_df['symbol'] == 'AAPL']
        sell_dates = sell_df['date'].unique()[1:]
        assert len(portfolio.orders) == len(buy_dates) + len(sell_dates)
        assert len(list(filter(lambda o: o.type == 'buy' and o.symbol == 'SPY' and (o.shares == 10), portfolio.orders))) == len(buy_dates)
        assert len(list(filter(lambda o: o.type == 'sell' and o.symbol == 'AAPL' and (o.shares == 20), portfolio.orders))) == len(sell_dates)

    def test_backtest_executions_when_buy_delay(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_fill_price = PriceType.CLOSE
            ctx.buy_limit_price = 100
            ctx.buy_shares = 200
        buy_exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {buy_exec}
        mock_portfolio = Mock()
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(buy_delay=2), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
        buy_df = data_source_df[data_source_df['symbol'] == 'SPY']
        buy_dates = buy_df['date'].unique()[2:]
        assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
        for i, date in enumerate(buy_dates):
            _, kwargs = mock_portfolio.buy.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == 'SPY'
            assert kwargs['shares'] == 200
            assert kwargs['fill_price'] == Decimal(str(round(buy_df[buy_df['date'] == date]['close'].values[0], 2)))
            assert kwargs['limit_price'] == 100

    def test_backtest_executions_when_sell_delay(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_fill_price = PriceType.CLOSE
            ctx.sell_limit_price = 50.5
            ctx.sell_shares = 100
        sell_exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {sell_exec}
        mock_portfolio = Mock()
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(sell_delay=2), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
        sell_df = data_source_df[data_source_df['symbol'] == 'AAPL']
        sell_dates = sell_df['date'].unique()[2:]
        assert len(mock_portfolio.sell.call_args_list) == len(sell_dates)
        for i, date in enumerate(sell_dates):
            _, kwargs = mock_portfolio.sell.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == 'AAPL'
            assert kwargs['shares'] == 100
            assert kwargs['fill_price'] == Decimal(str(round(sell_df[sell_df['date'] == date]['close'].values[0], 2)))
            assert kwargs['limit_price'] == 50.5

    def test_backtest_executions_when_invalid_buy_hold_bars_then_error(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_shares = 200
            ctx.hold_bars = 0
        buy_exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {buy_exec}
        mixin = BacktestMixin()
        with pytest.raises(ValueError, match=re.escape('hold_bars must be greater than 0.')):
            mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Mock(), pos_size_handler=None, exit_dates={})

    def test_backtest_executions_when_invalid_sell_hold_bars_then_error(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_shares = 100
            ctx.hold_bars = 0
        sell_exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {sell_exec}
        mixin = BacktestMixin()
        with pytest.raises(ValueError, match=re.escape('hold_bars must be greater than 0.')):
            mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Mock(), pos_size_handler=None, exit_dates={})

    def test_backtest_executions_when_no_fn(self, data_source_df):
        exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=None, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(100000)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert len(portfolio.bars) == len(data_source_df['date'].unique())
        assert not len(portfolio.position_bars)
        assert not len(portfolio.orders)
        assert not len(portfolio.trades)

    def test_backtest_executions_when_empty_symbols(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_shares = 200
        exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(100000)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df[data_source_df['symbol'] != 'AAPL'], portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert len(portfolio.bars) == len(data_source_df['date'].unique())
        assert not len(portfolio.position_bars)
        assert not len(portfolio.orders)
        assert not len(portfolio.trades)

    def test_backtest_executions_when_buy_delay_after_period(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_shares = 200
        exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(100000)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(buy_delay=1000), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert len(portfolio.bars) == len(data_source_df['date'].unique())
        assert not len(portfolio.position_bars)
        assert not len(portfolio.orders)
        assert not len(portfolio.trades)

    def test_backtest_executions_when_sell_delay_after_period(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_shares = 200
        exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(100000)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(sell_delay=1000), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert len(portfolio.bars)
        assert not len(portfolio.position_bars)
        assert not len(portfolio.orders)
        assert not len(portfolio.trades)

    def test_backtest_executions_when_buy_score(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_fill_price = PriceType.CLOSE
            ctx.buy_shares = 200
            if ctx.symbol == 'SPY':
                ctx.score = 1
            else:
                ctx.score = 0
        exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        mock_portfolio = Mock()
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(max_long_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
        df = data_source_df[data_source_df['symbol'].isin(['AAPL', 'SPY'])]
        buy_dates = sorted(df['date'].values)[2:]
        assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
        for i, date in enumerate(buy_dates):
            sym = 'SPY' if i % 2 == 0 else 'AAPL'
            _, kwargs = mock_portfolio.buy.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == sym
            assert kwargs['shares'] == 200
            assert kwargs['fill_price'] == Decimal(str(round(df[(df['date'] == date) & (df['symbol'] == sym)]['close'].values[0], 2)))
            assert kwargs['limit_price'] is None

    def test_backtest_executions_when_sell_score(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_fill_price = PriceType.CLOSE
            ctx.sell_shares = 200
            if ctx.symbol == 'AAPL':
                ctx.score = 1
            else:
                ctx.score = 0
        exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        mock_portfolio = Mock()
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(max_short_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
        df = data_source_df[data_source_df['symbol'].isin(['AAPL', 'SPY'])]
        sell_dates = sorted(df['date'].values)[2:]
        assert len(mock_portfolio.sell.call_args_list) == len(sell_dates)
        for i, date in enumerate(sell_dates):
            sym = 'AAPL' if i % 2 == 0 else 'SPY'
            _, kwargs = mock_portfolio.sell.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == sym
            assert kwargs['shares'] == 200
            assert kwargs['fill_price'] == Decimal(str(round(df[(df['date'] == date) & (df['symbol'] == sym)]['close'].values[0], 2)))
            assert kwargs['limit_price'] is None

    def test_backtest_executions_when_max_short_positions_and_cover(self, data_source_df):

        def sell_exec_fn(ctx):
            if ctx.symbol == 'AAPL':
                if ctx.bars == 1:
                    ctx.sell_shares = 200
                elif ctx.bars == 2:
                    ctx.cover_all_shares()
            elif ctx.bars == 2:
                ctx.sell_shares = 100
        exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(100000, max_short_positions=1)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(max_short_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert len(portfolio.short_positions) == 1
        assert not portfolio.long_positions
        assert len(portfolio.orders) == 3
        orders = portfolio.orders
        assert orders[0].symbol == 'AAPL'
        assert orders[0].shares == 200
        assert orders[0].type == 'sell'
        assert orders[1].symbol == 'AAPL'
        assert orders[1].shares == 200
        assert orders[1].type == 'buy'
        assert orders[2].symbol == 'SPY'
        assert orders[2].shares == 100
        assert orders[2].type == 'sell'
        trades = portfolio.trades
        assert len(trades) == 1
        assert trades[0].symbol == 'AAPL'
        assert trades[0].type == 'short'

    def test_backtest_executions_when_max_long_positions_and_cover(self, data_source_df):

        def cover_exec_fn(ctx):
            if ctx.symbol == 'AAPL':
                ctx.score = 2
            else:
                ctx.score = 1
            ctx.cover_shares = 100
            ctx.hold_bars = 1
        exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=cover_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(100000, max_long_positions=1)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(max_long_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        dates = data_source_df['date'].unique()[1:]
        orders = portfolio.orders
        assert len(list(filter(lambda o: o.symbol == 'AAPL', orders))) == len(dates) * 2 - 1
        trades = portfolio.trades
        assert len(list(filter(lambda t: t.symbol == 'AAPL', trades))) == len(dates) - 1

    @pytest.mark.parametrize('price_type, expected_fill_price', [(50, 50), (Decimal('111.1'), Decimal('111.1')), (lambda _symbol, _bar_data: 60, 60), (PriceType.OPEN, 200), (PriceType.HIGH, 400), (PriceType.LOW, 100), (PriceType.CLOSE, 300), (PriceType.MIDDLE, round(100 + (400 - 100) / 2.0, 2)), (PriceType.AVERAGE, round((200 + 100 + 400 + 300) / 4.0, 2))])
    def test_backtest_executions_get_price(self, price_type, expected_fill_price):
        dates = pd.date_range(start='1/1/2018', end='1/1/2019').tolist()
        df = pd.DataFrame({'date': dates, 'symbol': ['SPY'] * len(dates), 'open': np.repeat(200, len(dates)), 'high': np.repeat(400, len(dates)), 'low': np.repeat(100, len(dates)), 'close': np.repeat(300, len(dates))})

        def buy_exec_fn(ctx):
            ctx.buy_shares = 200
            ctx.buy_fill_price = price_type
            ctx.buy_limit_price = 101
        exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        mock_portfolio = Mock()
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
        buy_dates = dates[1:]
        assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
        for i, date in enumerate(buy_dates):
            _, kwargs = mock_portfolio.buy.call_args_list[i]
            assert kwargs['date'] == date
            assert kwargs['symbol'] == 'SPY'
            assert kwargs['shares'] == 200
            assert kwargs['fill_price'] == expected_fill_price
            assert kwargs['limit_price'] == 101

    def test_backtest_executions_get_price_when_invalid_price_then_error(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_shares = 200
            ctx.buy_fill_price = 'invalid'
        exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        mixin = BacktestMixin()
        with pytest.raises(ValueError, match='Unknown price: .*'):
            mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Portfolio(100000), pos_size_handler=None, exit_dates={})

    def test_backtest_executions_when_buy_limit_and_no_shares_then_error(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_limit_price = 100
        exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        mixin = BacktestMixin()
        with pytest.raises(ValueError, match=re.escape('buy_shares must be set when buy_limit_price is set.')):
            mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Portfolio(100000), pos_size_handler=None, exit_dates={})

    def test_backtest_executions_when_sell_limit_and_no_shares_then_error(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_limit_price = 100
        exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        mixin = BacktestMixin()
        with pytest.raises(ValueError, match=re.escape('sell_shares must be set when sell_limit_price is set.')):
            mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Portfolio(100000), pos_size_handler=None, exit_dates={})

    def test_backtest_executions_when_buy_order_not_filled(self, data_source_df):

        def buy_exec_fn(ctx):
            ctx.buy_fill_price = 100
            ctx.buy_shares = 100
        exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(1)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert not len(portfolio.orders)

    def test_backtest_executions_when_sell_order_not_filled(self, data_source_df):

        def sell_exec_fn(ctx):
            ctx.sell_fill_price = 100
            ctx.sell_limit_price = 200
            ctx.sell_shares = 100
        exec = Execution(id=1, symbols=frozenset(['SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
        execs = {exec}
        portfolio = Portfolio(1)
        mixin = BacktestMixin()
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
        assert not len(portfolio.orders)

@pytest.mark.parametrize('pos_size_handler, expected_buy_shares, expected_sell_shares', [(None, 200, 100), (pos_size_handler, 1000, 2000)])
def test_backtest_executions(self, data_source_df, pos_size_handler, expected_buy_shares, expected_sell_shares):

    def buy_exec_fn(ctx):
        ctx.buy_fill_price = PriceType.CLOSE
        ctx.buy_limit_price = 100
        ctx.buy_shares = 200

    def sell_exec_fn(ctx):
        ctx.sell_fill_price = PriceType.CLOSE
        ctx.sell_limit_price = 50.5
        ctx.sell_shares = 100
    buy_exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    sell_exec = Execution(id=2, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {buy_exec, sell_exec}
    mock_portfolio = Mock()
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=pos_size_handler, exit_dates={})
    buy_df = data_source_df[data_source_df['symbol'] == 'SPY']
    buy_dates = buy_df['date'].unique()[1:]
    assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
    for i, date in enumerate(buy_dates):
        _, kwargs = mock_portfolio.buy.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == 'SPY'
        assert kwargs['shares'] == expected_buy_shares
        assert kwargs['fill_price'] == Decimal(str(round(buy_df[buy_df['date'] == date]['close'].values[0], 2)))
        assert kwargs['limit_price'] == 100
    sell_df = data_source_df[data_source_df['symbol'] == 'AAPL']
    sell_dates = sell_df['date'].unique()[1:]
    assert len(mock_portfolio.sell.call_args_list) == len(sell_dates)
    for i, date in enumerate(sell_dates):
        _, kwargs = mock_portfolio.sell.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == 'AAPL'
        assert kwargs['shares'] == expected_sell_shares
        assert kwargs['fill_price'] == Decimal(str(round(sell_df[sell_df['date'] == date]['close'].values[0], 2)))
        assert kwargs['limit_price'] == 50.5

def test_backtest_when_pos_size_handler_and_cover(self, data_source_df):

    def pos_size_handler(ctx):
        signals = tuple(ctx.signals())
        ctx.set_shares(signals[0], shares=10)
        ctx.set_shares(signals[1], shares=20)
        assert isinstance(ctx.sessions['SPY'], dict)
        assert isinstance(ctx.sessions['AAPL'], dict)

    def buy_exec_fn(ctx):
        ctx.cover_fill_price = 1
        ctx.cover_shares = 2

    def sell_exec_fn(ctx):
        ctx.sell_fill_price = 1
        ctx.sell_shares = 1
    buy_exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    sell_exec = Execution(id=2, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {buy_exec, sell_exec}
    portfolio = Portfolio(1000000)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=pos_size_handler, exit_dates={})
    buy_df = data_source_df[data_source_df['symbol'] == 'SPY']
    buy_dates = buy_df['date'].unique()[1:]
    sell_df = data_source_df[data_source_df['symbol'] == 'AAPL']
    sell_dates = sell_df['date'].unique()[1:]
    assert len(portfolio.orders) == len(buy_dates) + len(sell_dates)
    assert len(list(filter(lambda o: o.type == 'buy' and o.symbol == 'SPY' and (o.shares == 10), portfolio.orders))) == len(buy_dates)
    assert len(list(filter(lambda o: o.type == 'sell' and o.symbol == 'AAPL' and (o.shares == 20), portfolio.orders))) == len(sell_dates)

def test_backtest_executions_when_buy_delay(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_fill_price = PriceType.CLOSE
        ctx.buy_limit_price = 100
        ctx.buy_shares = 200
    buy_exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {buy_exec}
    mock_portfolio = Mock()
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(buy_delay=2), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
    buy_df = data_source_df[data_source_df['symbol'] == 'SPY']
    buy_dates = buy_df['date'].unique()[2:]
    assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
    for i, date in enumerate(buy_dates):
        _, kwargs = mock_portfolio.buy.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == 'SPY'
        assert kwargs['shares'] == 200
        assert kwargs['fill_price'] == Decimal(str(round(buy_df[buy_df['date'] == date]['close'].values[0], 2)))
        assert kwargs['limit_price'] == 100

def test_backtest_executions_when_sell_delay(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_fill_price = PriceType.CLOSE
        ctx.sell_limit_price = 50.5
        ctx.sell_shares = 100
    sell_exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {sell_exec}
    mock_portfolio = Mock()
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(sell_delay=2), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
    sell_df = data_source_df[data_source_df['symbol'] == 'AAPL']
    sell_dates = sell_df['date'].unique()[2:]
    assert len(mock_portfolio.sell.call_args_list) == len(sell_dates)
    for i, date in enumerate(sell_dates):
        _, kwargs = mock_portfolio.sell.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == 'AAPL'
        assert kwargs['shares'] == 100
        assert kwargs['fill_price'] == Decimal(str(round(sell_df[sell_df['date'] == date]['close'].values[0], 2)))
        assert kwargs['limit_price'] == 50.5

def test_backtest_executions_when_invalid_buy_hold_bars_then_error(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_shares = 200
        ctx.hold_bars = 0
    buy_exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {buy_exec}
    mixin = BacktestMixin()
    with pytest.raises(ValueError, match=re.escape('hold_bars must be greater than 0.')):
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Mock(), pos_size_handler=None, exit_dates={})

def test_backtest_executions_when_invalid_sell_hold_bars_then_error(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_shares = 100
        ctx.hold_bars = 0
    sell_exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {sell_exec}
    mixin = BacktestMixin()
    with pytest.raises(ValueError, match=re.escape('hold_bars must be greater than 0.')):
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Mock(), pos_size_handler=None, exit_dates={})

def test_backtest_executions_when_no_fn(self, data_source_df):
    exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=None, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(100000)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert len(portfolio.bars) == len(data_source_df['date'].unique())
    assert not len(portfolio.position_bars)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

def test_backtest_executions_when_empty_symbols(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_shares = 200
    exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(100000)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df[data_source_df['symbol'] != 'AAPL'], portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert len(portfolio.bars) == len(data_source_df['date'].unique())
    assert not len(portfolio.position_bars)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

def test_backtest_executions_when_buy_delay_after_period(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_shares = 200
    exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(100000)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(buy_delay=1000), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert len(portfolio.bars) == len(data_source_df['date'].unique())
    assert not len(portfolio.position_bars)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

def test_backtest_executions_when_sell_delay_after_period(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_shares = 200
    exec = Execution(id=1, symbols=frozenset(['AAPL']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(100000)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(sell_delay=1000), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert len(portfolio.bars)
    assert not len(portfolio.position_bars)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

def test_backtest_executions_when_buy_score(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_fill_price = PriceType.CLOSE
        ctx.buy_shares = 200
        if ctx.symbol == 'SPY':
            ctx.score = 1
        else:
            ctx.score = 0
    exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    mock_portfolio = Mock()
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(max_long_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
    df = data_source_df[data_source_df['symbol'].isin(['AAPL', 'SPY'])]
    buy_dates = sorted(df['date'].values)[2:]
    assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
    for i, date in enumerate(buy_dates):
        sym = 'SPY' if i % 2 == 0 else 'AAPL'
        _, kwargs = mock_portfolio.buy.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == sym
        assert kwargs['shares'] == 200
        assert kwargs['fill_price'] == Decimal(str(round(df[(df['date'] == date) & (df['symbol'] == sym)]['close'].values[0], 2)))
        assert kwargs['limit_price'] is None

def test_backtest_executions_when_sell_score(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_fill_price = PriceType.CLOSE
        ctx.sell_shares = 200
        if ctx.symbol == 'AAPL':
            ctx.score = 1
        else:
            ctx.score = 0
    exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    mock_portfolio = Mock()
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(max_short_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
    df = data_source_df[data_source_df['symbol'].isin(['AAPL', 'SPY'])]
    sell_dates = sorted(df['date'].values)[2:]
    assert len(mock_portfolio.sell.call_args_list) == len(sell_dates)
    for i, date in enumerate(sell_dates):
        sym = 'AAPL' if i % 2 == 0 else 'SPY'
        _, kwargs = mock_portfolio.sell.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == sym
        assert kwargs['shares'] == 200
        assert kwargs['fill_price'] == Decimal(str(round(df[(df['date'] == date) & (df['symbol'] == sym)]['close'].values[0], 2)))
        assert kwargs['limit_price'] is None

def test_backtest_executions_when_max_short_positions_and_cover(self, data_source_df):

    def sell_exec_fn(ctx):
        if ctx.symbol == 'AAPL':
            if ctx.bars == 1:
                ctx.sell_shares = 200
            elif ctx.bars == 2:
                ctx.cover_all_shares()
        elif ctx.bars == 2:
            ctx.sell_shares = 100
    exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(100000, max_short_positions=1)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(max_short_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert len(portfolio.short_positions) == 1
    assert not portfolio.long_positions
    assert len(portfolio.orders) == 3
    orders = portfolio.orders
    assert orders[0].symbol == 'AAPL'
    assert orders[0].shares == 200
    assert orders[0].type == 'sell'
    assert orders[1].symbol == 'AAPL'
    assert orders[1].shares == 200
    assert orders[1].type == 'buy'
    assert orders[2].symbol == 'SPY'
    assert orders[2].shares == 100
    assert orders[2].type == 'sell'
    trades = portfolio.trades
    assert len(trades) == 1
    assert trades[0].symbol == 'AAPL'
    assert trades[0].type == 'short'

def test_backtest_executions_when_max_long_positions_and_cover(self, data_source_df):

    def cover_exec_fn(ctx):
        if ctx.symbol == 'AAPL':
            ctx.score = 2
        else:
            ctx.score = 1
        ctx.cover_shares = 100
        ctx.hold_bars = 1
    exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=cover_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(100000, max_long_positions=1)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(max_long_positions=1), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    dates = data_source_df['date'].unique()[1:]
    orders = portfolio.orders
    assert len(list(filter(lambda o: o.symbol == 'AAPL', orders))) == len(dates) * 2 - 1
    trades = portfolio.trades
    assert len(list(filter(lambda t: t.symbol == 'AAPL', trades))) == len(dates) - 1

@pytest.mark.parametrize('price_type, expected_fill_price', [(50, 50), (Decimal('111.1'), Decimal('111.1')), (lambda _symbol, _bar_data: 60, 60), (PriceType.OPEN, 200), (PriceType.HIGH, 400), (PriceType.LOW, 100), (PriceType.CLOSE, 300), (PriceType.MIDDLE, round(100 + (400 - 100) / 2.0, 2)), (PriceType.AVERAGE, round((200 + 100 + 400 + 300) / 4.0, 2))])
def test_backtest_executions_get_price(self, price_type, expected_fill_price):
    dates = pd.date_range(start='1/1/2018', end='1/1/2019').tolist()
    df = pd.DataFrame({'date': dates, 'symbol': ['SPY'] * len(dates), 'open': np.repeat(200, len(dates)), 'high': np.repeat(400, len(dates)), 'low': np.repeat(100, len(dates)), 'close': np.repeat(300, len(dates))})

    def buy_exec_fn(ctx):
        ctx.buy_shares = 200
        ctx.buy_fill_price = price_type
        ctx.buy_limit_price = 101
    exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    mock_portfolio = Mock()
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=df, portfolio=mock_portfolio, pos_size_handler=None, exit_dates={})
    buy_dates = dates[1:]
    assert len(mock_portfolio.buy.call_args_list) == len(buy_dates)
    for i, date in enumerate(buy_dates):
        _, kwargs = mock_portfolio.buy.call_args_list[i]
        assert kwargs['date'] == date
        assert kwargs['symbol'] == 'SPY'
        assert kwargs['shares'] == 200
        assert kwargs['fill_price'] == expected_fill_price
        assert kwargs['limit_price'] == 101

def test_backtest_executions_get_price_when_invalid_price_then_error(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_shares = 200
        ctx.buy_fill_price = 'invalid'
    exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    mixin = BacktestMixin()
    with pytest.raises(ValueError, match='Unknown price: .*'):
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Portfolio(100000), pos_size_handler=None, exit_dates={})

def test_backtest_executions_when_buy_limit_and_no_shares_then_error(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_limit_price = 100
    exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    mixin = BacktestMixin()
    with pytest.raises(ValueError, match=re.escape('buy_shares must be set when buy_limit_price is set.')):
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Portfolio(100000), pos_size_handler=None, exit_dates={})

def test_backtest_executions_when_sell_limit_and_no_shares_then_error(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_limit_price = 100
    exec = Execution(id=1, symbols=frozenset(['AAPL', 'SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    mixin = BacktestMixin()
    with pytest.raises(ValueError, match=re.escape('sell_shares must be set when sell_limit_price is set.')):
        mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=Portfolio(100000), pos_size_handler=None, exit_dates={})

def test_backtest_executions_when_buy_order_not_filled(self, data_source_df):

    def buy_exec_fn(ctx):
        ctx.buy_fill_price = 100
        ctx.buy_shares = 100
    exec = Execution(id=1, symbols=frozenset(['SPY']), fn=buy_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(1)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert not len(portfolio.orders)

def test_backtest_executions_when_sell_order_not_filled(self, data_source_df):

    def sell_exec_fn(ctx):
        ctx.sell_fill_price = 100
        ctx.sell_limit_price = 200
        ctx.sell_shares = 100
    exec = Execution(id=1, symbols=frozenset(['SPY']), fn=sell_exec_fn, model_names=frozenset(), indicator_names=frozenset())
    execs = {exec}
    portfolio = Portfolio(1)
    mixin = BacktestMixin()
    mixin.backtest_executions(config=StrategyConfig(), executions=execs, before_exec_fn=None, after_exec_fn=None, sessions=defaultdict(dict), models={}, indicator_data={}, test_data=data_source_df, portfolio=portfolio, pos_size_handler=None, exit_dates={})
    assert not len(portfolio.orders)

