# Cluster 14

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

class DataSource(ABC, DataSourceCacheMixin):
    """Base class for querying data from an external source. Extend this class
    and override :meth:`._fetch_data` to implement a custom
    :class:`.DataSource` that can be used with
    :class:`pybroker.strategy.Strategy`.
    """

    def __init__(self):
        self._scope = StaticScope.instance()
        self._logger = self._scope.logger

    def query(self, symbols: Union[str, Iterable[str]], start_date: Union[str, datetime], end_date: Union[str, datetime], timeframe: Optional[str]='', adjust: Optional[Any]=None) -> pd.DataFrame:
        """Queries data. Cached data is returned if caching is enabled by
        calling :meth:`pybroker.cache.enable_data_source_cache`.

        Args:
            symbols: Symbols of the data to query.
            start_date: Start date of the data to query (inclusive).
            end_date: End date of the data to query (inclusive).
            timeframe: Formatted string that specifies the timeframe
                resolution to query. The timeframe string supports the
                following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks

                An example timeframe string is ``1h 30m``.
            adjust: The type of adjustment to make.

        Returns:
            :class:`pandas.DataFrame` containing the queried data.
        """
        start_date = to_datetime(start_date)
        end_date = to_datetime(end_date)
        verify_date_range(start_date, end_date)
        if isinstance(symbols, str) and (not symbols):
            raise ValueError('Symbols cannot be empty.')
        unique_syms = frozenset((symbols,)) if isinstance(symbols, str) else frozenset(symbols)
        if not unique_syms:
            raise ValueError('Symbols cannot be empty.')
        timeframe = self._format_timeframe(timeframe)
        cached_df, uncached_syms = self.get_cached(symbols=unique_syms, timeframe=timeframe, start_date=start_date, end_date=end_date, adjust=adjust)
        if not uncached_syms:
            return cached_df
        self._logger.download_bar_data_start()
        self._logger.info_download_bar_data_start(symbols=uncached_syms, timeframe=timeframe, start_date=start_date, end_date=end_date)
        df = self._fetch_data(frozenset(uncached_syms), start_date, end_date, timeframe, adjust)
        if self._scope.data_source_cache is not None and (not cached_df.columns.empty) and (set(cached_df.columns) != set(df.columns)):
            self._logger.info_invalidate_data_source_cache()
            self._scope.data_source_cache.clear()
            return self.query(symbols, start_date, end_date, timeframe)
        verify_data_source_columns(df)
        self.set_cached(timeframe, start_date, end_date, adjust, df)
        df = pd.concat((cached_df, df))
        if not df.empty:
            df = df.sort_values(by=[DataCol.DATE.value, DataCol.SYMBOL.value])
        self._logger.download_bar_data_completed()
        return df.reset_index(drop=True)

    @abstractmethod
    def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[Any]) -> pd.DataFrame:
        """:meta public:
        Override this method to return data from a custom
        source. The returned :class:`pandas.DataFrame` must contain the
        following columns: ``symbol``, ``date``, ``open``, ``high``, ``low``,
        and ``close``.

        Args:
            symbols: Ticker symbols of the data to query.
            start_date: Start date of the data to query (inclusive).
            end_date: End date of the data to query (inclusive).
            timeframe: Formatted string that specifies the timeframe
                resolution to query. The timeframe string supports the
                following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks

                An example timeframe string is ``1h 30m``.
            adjust: The type of adjustment to make.

        Returns:
            :class:`pandas.DataFrame` containing the queried data.
        """

    def _format_timeframe(self, timeframe: Optional[str]) -> str:
        if not timeframe:
            return ''
        return ' '.join((f'{part[0]}{part[1]}' for part in parse_timeframe(timeframe)))

def _format_timeframe(self, timeframe: Optional[str]) -> str:
    if not timeframe:
        return ''
    return ' '.join((f'{part[0]}{part[1]}' for part in parse_timeframe(timeframe)))

def _parse_alpaca_timeframe(timeframe: Optional[str]) -> tuple[int, TimeFrameUnit]:
    if timeframe is None:
        raise ValueError('Timeframe needs to be specified for Alpaca.')
    parts = parse_timeframe(timeframe)
    if len(parts) != 1:
        raise ValueError(f'Invalid Alpaca timeframe: {timeframe}')
    tf = parts[0]
    if tf[1] == 'min':
        unit = TimeFrameUnit.Minute
    elif tf[1] == 'hour':
        unit = TimeFrameUnit.Hour
    elif tf[1] == 'day':
        unit = TimeFrameUnit.Day
    elif tf[1] == 'week':
        unit = TimeFrameUnit.Week
    else:
        raise ValueError(f'Invalid Alpaca timeframe: {timeframe}')
    return (tf[0], unit)

@njit
def sumv(array: NDArray[np.float64], n: int) -> NDArray[np.float64]:
    """Calculates the sums for every ``n`` period in ``array``.

    Args:
        array: :class:`numpy.ndarray` of data.
        n: Length of period.

    Returns:
        :class:`numpy.ndarray` of the sums for every ``n`` period in ``array``.
    """
    if not len(array):
        return np.array(tuple())
    _verify_input(array, n)
    out_len = len(array)
    out = np.array([np.nan for _ in range(out_len)])
    for i in range(n, out_len + 1):
        out[i - 1] = np.sum(array[i - n:i])
    return out

def to_seconds(timeframe: Optional[str]) -> int:
    """Converts a timeframe string to seconds, where ``timeframe`` supports the
    following units:

    - ``"s"``/``"sec"``: seconds
    - ``"m"``/``"min"``: minutes
    - ``"h"``/``"hour"``: hours
    - ``"d"``/``"day"``: days
    - ``"w"``/``"week"``: weeks

    An example timeframe string is ``1h 30m``.

    Returns:
        The converted number of seconds.
    """
    if not timeframe:
        return 0
    seconds = {'sec': 1, 'min': 60, 'hour': 60 * 60, 'day': 24 * 60 * 60, 'week': 7 * 24 * 60 * 60}
    return sum((part[0] * seconds[part[1]] for part in parse_timeframe(timeframe)))

def decorated_indicator_fn(symbol: str, ind_name: str, date: NDArray[np.datetime64], open: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: Optional[NDArray[np.float64]], vwap: Optional[NDArray[np.float64]], custom_col_data: Mapping[str, Optional[NDArray]]) -> tuple[IndicatorSymbol, pd.Series]:
    bar_data = BarData(date=date, open=open, high=high, low=low, close=close, volume=volume, vwap=vwap, **custom_col_data)
    series = fn(bar_data)
    return (IndicatorSymbol(ind_name, symbol), series)

@njit
def profit_factor(changes: NDArray[np.float64], use_log: bool=False) -> np.floating:
    """Computes the profit factor, which is the ratio of gross profit to gross
    loss.

    Args:
        changes: Array of differences between each bar and the previous bar.
        use_log: Whether to log transform the profit factor. Defaults to False.
    """
    wins = changes[changes > 0]
    losses = changes[changes < 0]
    if not len(wins) and (not len(losses)):
        return np.float64(0)
    numer = denom = 1e-10
    numer += np.sum(wins)
    denom -= np.sum(losses)
    if use_log:
        return np.log(numer / denom)
    else:
        return np.divide(numer, denom)

@njit
def log_profit_factor(changes: NDArray[np.float64]) -> np.floating:
    """Computes the log transformed profit factor, which is the ratio of gross
    profit to gross loss.

    Args:
        changes: Array of differences between each bar and the previous bar.
    """
    return profit_factor(changes, use_log=True)

@njit
def sharpe_ratio(returns: NDArray[np.float64], obs: Optional[int]=None, downside_only: bool=False) -> np.floating:
    """Computes the
    `Sharpe Ratio <https://en.wikipedia.org/wiki/Sharpe_ratio>`_.

    Args:
        returns: Array of returns centered at 0.
        obs: Number of observations used to annualize the Sharpe Ratio. For
            example, a value of ``252`` would be used to annualize daily
            returns.
    """
    std_changes = returns[returns < 0] if downside_only else returns
    if not len(std_changes):
        return np.float64(0)
    std = np.std(std_changes)
    if std == 0:
        return np.float64(0)
    sr = np.mean(returns) / std
    if obs is not None:
        sr *= np.sqrt(obs)
    return sr

def sortino_ratio(returns: NDArray[np.float64], obs: Optional[int]=None) -> float:
    """Computes the
    `Sortino Ratio <https://en.wikipedia.org/wiki/Sortino_ratio>`_.

    Args:
        returns: Array of returns centered at 0.
        obs: Number of observations used to annualize the Sortino Ratio. For
            example, a value of ``252`` would be used to annualize daily
            returns.
    """
    return float(sharpe_ratio(returns, obs, downside_only=True))

def calmar_ratio(returns: NDArray[np.float64], bars_per_year: int) -> float:
    """Computes the Calmar Ratio.

    Args:
        returns: Array of returns centered at 0.
        bars_per_year: Number of bars per annum.
    """
    if not len(returns):
        return 0
    max_dd = np.abs(max_drawdown(returns))
    if max_dd == 0:
        return 0
    return np.mean(returns) * bars_per_year / max_dd

@njit
def upi(values: NDArray[np.float64], period: int=14, ui: Optional[float]=None) -> float:
    """Computes the `Ulcer Performance Index
    <https://en.wikipedia.org/wiki/Ulcer_index>`_ of ``values``.
    """
    if len(values) <= 1:
        return 0
    if ui is None:
        ui = ulcer_index(values, period)
    if ui == 0:
        return 0
    r = np.zeros(len(values) - 1)
    for i in range(len(r)):
        r[i] = (values[i + 1] - values[i]) / values[i] * 100
    return float(np.mean(r) / ui)

def total_profit_loss(pnls: NDArray[np.float64]) -> tuple[float, float]:
    """Computes total profit and loss.

    Args:
        pnls: Array of profits and losses (PnLs) per trade.

    Returns:
        ``tuple[float, float]`` of total profit and total loss.
    """
    profits = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    return (np.sum(profits) if len(profits) else 0, np.sum(losses) if len(losses) else 0)

def avg_profit_loss(pnls: NDArray[np.float64]) -> tuple[float, float]:
    """Computes the average profit and average loss per trade.

    Args:
        pnls: Array of profits and losses (PnLs) per trade.

    Returns:
        ``tuple[float, float]`` of average profit and average loss.
    """
    profits = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    return (float(np.mean(profits)) if len(profits) else 0, float(np.mean(losses)) if len(losses) else 0)

def r_squared(values: NDArray[np.float64]) -> float:
    """Computes R-squared of ``values``."""
    n = len(values)
    if not n:
        return 0
    x = np.arange(n)
    try:
        coeffs = np.polyfit(x, values, 1)
        pred = np.poly1d(coeffs)(x)
        y_hat = np.mean(values)
        ssres = float(np.sum((values - pred) ** 2))
        sstot = float(np.sum((values - y_hat) ** 2))
        if sstot == 0:
            return 0
        return 1 - ssres / sstot
    except Exception:
        return 0

class EvaluateMixin:
    """Mixin for computing evaluation metrics."""

    def evaluate(self, portfolio_df: pd.DataFrame, trades_df: pd.DataFrame, calc_bootstrap: bool, bootstrap_sample_size: int, bootstrap_samples: int, bars_per_year: Optional[int]) -> EvalResult:
        """Computes evaluation metrics.

        Args:
            portfolio_df: :class:`pandas.DataFrame` of portfolio market values
                per bar.
            trades_df: :class:`pandas.DataFrame` of trades.
            calc_bootstrap: ``True`` to calculate randomized bootstrap metrics.
            bootstrap_sample_size: Size of each random bootstrap sample.
            bootstrap_samples: Number of random bootstrap samples to use.
            bars_per_year: Number of observations per years that will be used
                to annualize evaluation metrics. For example, a value of
                ``252`` would be used to annualize the Sharpe Ratio for daily
                returns.

        Returns:
            :class:`.EvalResult` containing evaluation metrics.
        """
        market_values = portfolio_df['market_value'].to_numpy()
        fees = portfolio_df['fees'].to_numpy()
        bar_returns = self._calc_bar_returns(portfolio_df)
        bar_return_dates = bar_returns.index.to_series().reset_index(drop=True)
        bar_returns = bar_returns.to_numpy()
        bar_changes = self._calc_bar_changes(portfolio_df)
        if not len(market_values) or not len(bar_returns) or (not len(bar_changes)):
            return EvalResult(EvalMetrics(), None)
        pnls = trades_df['pnl'].to_numpy()
        return_pcts = trades_df['return_pct'].to_numpy()
        bars = trades_df['bars'].to_numpy()
        winning_trades = trades_df[trades_df['pnl'] > 0]
        winning_bars = winning_trades['bars'].to_numpy()
        losing_trades = trades_df[trades_df['pnl'] < 0]
        losing_bars = losing_trades['bars'].to_numpy()
        largest_win = winning_trades[winning_trades['pnl'] == winning_trades['pnl'].max()]
        largest_win_pct = 0 if largest_win.empty else largest_win['return_pct'].values[0]
        largest_win_bars = 0 if largest_win.empty else largest_win['bars'].values[0]
        largest_loss = losing_trades[losing_trades['pnl'] == losing_trades['pnl'].min()]
        largest_loss_pct = 0 if largest_loss.empty else largest_loss['return_pct'].values[0]
        largest_loss_bars = 0 if largest_loss.empty else largest_loss['bars'].values[0]
        metrics = self._calc_eval_metrics(market_values, bar_changes, bar_returns, bar_return_dates, pnls, return_pcts, bars=bars, winning_bars=winning_bars, losing_bars=losing_bars, largest_win_num_bars=largest_win_bars, largest_win_pct=largest_win_pct, largest_loss_num_bars=largest_loss_bars, largest_loss_pct=largest_loss_pct, fees=fees, bars_per_year=bars_per_year)
        logger = StaticScope.instance().logger
        if not calc_bootstrap:
            return EvalResult(metrics, None)
        if len(bar_returns) <= bootstrap_sample_size:
            logger.warn_bootstrap_sample_size(len(bar_returns), bootstrap_sample_size)
        logger.calc_bootstrap_metrics_start(samples=bootstrap_samples, sample_size=bootstrap_sample_size)
        confs_result = self._calc_conf_intervals(changes=bar_changes, returns=bar_returns, sample_size=bootstrap_sample_size, samples=bootstrap_samples, bars_per_year=bars_per_year)
        dd_result = self._calc_drawdown_conf(changes=bar_changes, returns=bar_returns, sample_size=bootstrap_sample_size, samples=bootstrap_samples)
        bootstrap = BootstrapResult(conf_intervals=confs_result.df, drawdown_conf=dd_result.df, profit_factor=confs_result.profit_factor, sharpe=confs_result.sharpe, drawdown=dd_result.metrics)
        logger.calc_bootstrap_metrics_completed()
        return EvalResult(metrics, bootstrap)

    def _calc_bar_returns(self, df: pd.DataFrame) -> pd.Series:
        prev_market_value = df['market_value'].shift(1)
        returns = (df['market_value'] - prev_market_value) / prev_market_value
        return returns.dropna()

    def _calc_bar_changes(self, df: pd.DataFrame) -> NDArray[np.float64]:
        changes = df['market_value'] - df['market_value'].shift(1)
        return changes.dropna().to_numpy()

    def _calc_eval_metrics(self, market_values: NDArray[np.float64], bar_changes: NDArray[np.float64], bar_returns: NDArray[np.float64], bar_return_dates: pd.Series, pnls: NDArray[np.float64], return_pcts: NDArray[np.float64], bars: NDArray[np.int_], winning_bars: NDArray[np.int_], losing_bars: NDArray[np.int_], largest_win_num_bars: int, largest_win_pct: float, largest_loss_num_bars: int, largest_loss_pct: float, fees: NDArray[np.float64], bars_per_year: Optional[int]) -> EvalMetrics:
        total_fees = fees[-1] if len(fees) else 0
        max_dd = max_drawdown(bar_changes)
        max_dd_pct, max_dd_index = max_drawdown_percent(bar_returns)
        max_dd_date = bar_return_dates.iloc[max_dd_index].to_pydatetime() if max_dd_index else None
        sharpe = sharpe_ratio(bar_returns, bars_per_year)
        sortino = sortino_ratio(bar_returns, bars_per_year)
        pf = profit_factor(bar_changes)
        r2 = r_squared(market_values)
        ui = ulcer_index(market_values)
        upi_ = upi(market_values, ui=ui)
        std_error = float(np.std(market_values))
        largest_win = 0.0
        largest_loss = 0.0
        win_rate = 0.0
        loss_rate = 0.0
        winning_trades = 0
        losing_trades = 0
        avg_pnl = 0.0
        avg_return_pct = 0.0
        avg_trade_bars = 0.0
        avg_profit = 0.0
        avg_loss = 0.0
        avg_profit_pct = 0.0
        avg_loss_pct = 0.0
        avg_winning_trade_bars = 0.0
        avg_losing_trade_bars = 0.0
        total_profit = 0.0
        total_loss = 0.0
        total_pnl = 0.0
        unrealized_pnl = 0.0
        max_wins = 0
        max_losses = 0
        if len(pnls):
            largest_win, largest_loss = largest_win_loss(pnls)
            win_rate, loss_rate = win_loss_rate(pnls)
            winning_trades, losing_trades = winning_losing_trades(pnls)
            avg_profit, avg_loss = avg_profit_loss(pnls)
            avg_profit_pct, avg_loss_pct = avg_profit_loss(return_pcts)
            total_profit, total_loss = total_profit_loss(pnls)
            max_wins, max_losses = max_wins_losses(pnls)
            total_pnl = float(np.sum(pnls))
            if len(pnls):
                avg_pnl = float(np.mean(pnls))
            if len(return_pcts):
                avg_return_pct = float(np.mean(return_pcts))
            if len(bars):
                avg_trade_bars = float(np.mean(bars))
            if len(winning_bars):
                avg_winning_trade_bars = float(np.mean(winning_bars))
            if len(losing_bars):
                avg_losing_trade_bars = float(np.mean(losing_bars))
        total_return_pct = total_return_percent(initial_value=market_values[0], pnl=total_pnl)
        unrealized_pnl = market_values[-1] - market_values[0] - total_pnl
        annual_return_pct = None
        annual_std_error = None
        annual_volatility_pct = None
        calmar = None
        if bars_per_year is not None:
            annual_return_pct = annual_total_return_percent(initial_value=market_values[0], pnl=total_pnl, bars_per_year=bars_per_year, total_bars=len(market_values))
            annual_std_error = std_error * np.sqrt(bars_per_year)
            annual_volatility_pct = float(np.std(bar_returns * 100) * np.sqrt(bars_per_year))
            calmar = calmar_ratio(bar_returns, bars_per_year)
        return EvalMetrics(trade_count=len(pnls), initial_market_value=market_values[0], end_market_value=market_values[-1], max_drawdown=max_dd, max_drawdown_pct=max_dd_pct, max_drawdown_date=max_dd_date, largest_win=largest_win, largest_win_pct=largest_win_pct, largest_win_bars=largest_win_num_bars, largest_loss=largest_loss, largest_loss_pct=largest_loss_pct, largest_loss_bars=largest_loss_num_bars, max_wins=max_wins, max_losses=max_losses, win_rate=win_rate, loss_rate=loss_rate, winning_trades=winning_trades, losing_trades=losing_trades, avg_pnl=avg_pnl, avg_return_pct=avg_return_pct, avg_trade_bars=avg_trade_bars, avg_profit=avg_profit, avg_profit_pct=avg_profit_pct, avg_winning_trade_bars=avg_winning_trade_bars, avg_loss=avg_loss, avg_loss_pct=avg_loss_pct, avg_losing_trade_bars=avg_losing_trade_bars, total_profit=total_profit, total_loss=total_loss, total_pnl=total_pnl, unrealized_pnl=unrealized_pnl, total_return_pct=total_return_pct, annual_return_pct=annual_return_pct, total_fees=total_fees, sharpe=sharpe, sortino=sortino, calmar=calmar, profit_factor=pf, equity_r2=r2, ulcer_index=ui, upi=upi_, std_error=std_error, annual_std_error=annual_std_error, annual_volatility_pct=annual_volatility_pct)

    def _calc_conf_intervals(self, changes: NDArray[np.float64], returns: NDArray[np.float64], sample_size: int, samples: int, bars_per_year: Optional[int]) -> _ConfsResult:
        pf_intervals = conf_profit_factor(changes, sample_size, samples)
        pf_conf = self._to_conf_intervals('Profit Factor', pf_intervals)
        sr_intervals = conf_sharpe_ratio(returns, sample_size, samples, bars_per_year)
        sharpe_conf = self._to_conf_intervals('Sharpe Ratio', sr_intervals)
        df = pd.DataFrame.from_records(pf_conf + sharpe_conf, columns=ConfInterval._fields)
        df.set_index(['name', 'conf'], inplace=True)
        return _ConfsResult(df=df, profit_factor=pf_intervals, sharpe=sr_intervals)

    def _to_conf_intervals(self, name: str, conf: BootConfIntervals) -> deque[ConfInterval]:
        results: deque[ConfInterval] = deque()
        results.append(ConfInterval(name, '97.5%', conf.low_2p5, conf.high_2p5))
        results.append(ConfInterval(name, '95%', conf.low_5, conf.high_5))
        results.append(ConfInterval(name, '90%', conf.low_10, conf.high_10))
        return results

    def _calc_drawdown_conf(self, changes: NDArray[np.float64], returns: NDArray[np.float64], sample_size: int, samples: int) -> _DrawdownResult:
        metrics = drawdown_conf(changes, returns, sample_size, samples)
        df = pd.DataFrame(zip(('99.9%', '99%', '95%', '90%'), *metrics), columns=('conf', 'amount', 'percent'))
        df.set_index('conf', inplace=True)
        return _DrawdownResult(df=df, metrics=metrics)

def _calc_eval_metrics(self, market_values: NDArray[np.float64], bar_changes: NDArray[np.float64], bar_returns: NDArray[np.float64], bar_return_dates: pd.Series, pnls: NDArray[np.float64], return_pcts: NDArray[np.float64], bars: NDArray[np.int_], winning_bars: NDArray[np.int_], losing_bars: NDArray[np.int_], largest_win_num_bars: int, largest_win_pct: float, largest_loss_num_bars: int, largest_loss_pct: float, fees: NDArray[np.float64], bars_per_year: Optional[int]) -> EvalMetrics:
    total_fees = fees[-1] if len(fees) else 0
    max_dd = max_drawdown(bar_changes)
    max_dd_pct, max_dd_index = max_drawdown_percent(bar_returns)
    max_dd_date = bar_return_dates.iloc[max_dd_index].to_pydatetime() if max_dd_index else None
    sharpe = sharpe_ratio(bar_returns, bars_per_year)
    sortino = sortino_ratio(bar_returns, bars_per_year)
    pf = profit_factor(bar_changes)
    r2 = r_squared(market_values)
    ui = ulcer_index(market_values)
    upi_ = upi(market_values, ui=ui)
    std_error = float(np.std(market_values))
    largest_win = 0.0
    largest_loss = 0.0
    win_rate = 0.0
    loss_rate = 0.0
    winning_trades = 0
    losing_trades = 0
    avg_pnl = 0.0
    avg_return_pct = 0.0
    avg_trade_bars = 0.0
    avg_profit = 0.0
    avg_loss = 0.0
    avg_profit_pct = 0.0
    avg_loss_pct = 0.0
    avg_winning_trade_bars = 0.0
    avg_losing_trade_bars = 0.0
    total_profit = 0.0
    total_loss = 0.0
    total_pnl = 0.0
    unrealized_pnl = 0.0
    max_wins = 0
    max_losses = 0
    if len(pnls):
        largest_win, largest_loss = largest_win_loss(pnls)
        win_rate, loss_rate = win_loss_rate(pnls)
        winning_trades, losing_trades = winning_losing_trades(pnls)
        avg_profit, avg_loss = avg_profit_loss(pnls)
        avg_profit_pct, avg_loss_pct = avg_profit_loss(return_pcts)
        total_profit, total_loss = total_profit_loss(pnls)
        max_wins, max_losses = max_wins_losses(pnls)
        total_pnl = float(np.sum(pnls))
        if len(pnls):
            avg_pnl = float(np.mean(pnls))
        if len(return_pcts):
            avg_return_pct = float(np.mean(return_pcts))
        if len(bars):
            avg_trade_bars = float(np.mean(bars))
        if len(winning_bars):
            avg_winning_trade_bars = float(np.mean(winning_bars))
        if len(losing_bars):
            avg_losing_trade_bars = float(np.mean(losing_bars))
    total_return_pct = total_return_percent(initial_value=market_values[0], pnl=total_pnl)
    unrealized_pnl = market_values[-1] - market_values[0] - total_pnl
    annual_return_pct = None
    annual_std_error = None
    annual_volatility_pct = None
    calmar = None
    if bars_per_year is not None:
        annual_return_pct = annual_total_return_percent(initial_value=market_values[0], pnl=total_pnl, bars_per_year=bars_per_year, total_bars=len(market_values))
        annual_std_error = std_error * np.sqrt(bars_per_year)
        annual_volatility_pct = float(np.std(bar_returns * 100) * np.sqrt(bars_per_year))
        calmar = calmar_ratio(bar_returns, bars_per_year)
    return EvalMetrics(trade_count=len(pnls), initial_market_value=market_values[0], end_market_value=market_values[-1], max_drawdown=max_dd, max_drawdown_pct=max_dd_pct, max_drawdown_date=max_dd_date, largest_win=largest_win, largest_win_pct=largest_win_pct, largest_win_bars=largest_win_num_bars, largest_loss=largest_loss, largest_loss_pct=largest_loss_pct, largest_loss_bars=largest_loss_num_bars, max_wins=max_wins, max_losses=max_losses, win_rate=win_rate, loss_rate=loss_rate, winning_trades=winning_trades, losing_trades=losing_trades, avg_pnl=avg_pnl, avg_return_pct=avg_return_pct, avg_trade_bars=avg_trade_bars, avg_profit=avg_profit, avg_profit_pct=avg_profit_pct, avg_winning_trade_bars=avg_winning_trade_bars, avg_loss=avg_loss, avg_loss_pct=avg_loss_pct, avg_losing_trade_bars=avg_losing_trade_bars, total_profit=total_profit, total_loss=total_loss, total_pnl=total_pnl, unrealized_pnl=unrealized_pnl, total_return_pct=total_return_pct, annual_return_pct=annual_return_pct, total_fees=total_fees, sharpe=sharpe, sortino=sortino, calmar=calmar, profit_factor=pf, equity_r2=r2, ulcer_index=ui, upi=upi_, std_error=std_error, annual_std_error=annual_std_error, annual_volatility_pct=annual_volatility_pct)

@pytest.mark.parametrize('array, n, expected', [([3, 3, 4, 2, 5, 6, 1, 3], 3, [np.nan, np.nan, 3, 2, 2, 2, 1, 1]), ([3, 3, 4, 2, 5, 6, 1, 3], 1, [3, 3, 4, 2, 5, 6, 1, 3]), ([4, 3, 2, 1], 4, [np.nan, np.nan, np.nan, 1]), ([1], 1, [1]), ([], 5, [])])
def test_lowv(array, n, expected):
    assert np.array_equal(lowv(np.array(array), n), expected, equal_nan=True)

@pytest.mark.parametrize('array, n, expected', [([3, 3, 4, 2, 5, 6, 1, 3], 3, [np.nan, np.nan, 4, 4, 5, 6, 6, 6]), ([3, 3, 4, 2, 5, 6, 1, 3], 1, [3, 3, 4, 2, 5, 6, 1, 3]), ([4, 3, 2, 1], 4, [np.nan, np.nan, np.nan, 4]), ([1], 1, [1]), ([], 5, [])])
def test_highv(array, n, expected):
    assert np.array_equal(highv(np.array(array), n), expected, equal_nan=True)

@pytest.mark.parametrize('array, n, expected', [([3, 3, 4, 2, 5, 6, 1, 3], 3, [np.nan, np.nan, 10, 9, 11, 13, 12, 10]), ([3, 3, 4, 2, 5, 6, 1, 3], 1, [3, 3, 4, 2, 5, 6, 1, 3]), ([4, 3, 2, 1], 4, [np.nan, np.nan, np.nan, 10]), ([1], 1, [1]), ([], 5, [])])
def test_sumv(array, n, expected):
    assert np.array_equal(sumv(np.array(array), n), expected, equal_nan=True)

@pytest.mark.parametrize('array, n, expected', [([1, 1.5, 1.7, 1.3, 1.2, 1.4], 1, [np.nan, 0.5, 0.13333333, -0.23529412, -0.07692308, 0.16666667]), ([1, 1.5, 1.7, 1.3, 1.2, 1.4], 2, [np.nan, np.nan, 0.7, -0.133333, -0.294118, 0.076923]), ([1], 1, [np.nan]), ([], 5, [])])
def test_returnv(array, n, expected):
    assert np.array_equal(np.round(returnv(np.array(array), n), 6), np.round(expected, 6), equal_nan=True)

@pytest.mark.parametrize('fnv', [lowv, highv, sumv, returnv])
@pytest.mark.parametrize('array, n, expected_msg', [([1, 2, 3], 10, 'n is greater than array length.'), ([1, 2, 3], 0, 'n needs to be >= 1.'), ([1, 2, 3], -1, 'n needs to be >= 1.')])
def test_when_n_invalid_then_error(fnv, array, n, expected_msg):
    with pytest.raises(AssertionError, match=re.escape(expected_msg)):
        fnv(np.array(array), n)

@pytest.mark.parametrize('a, b, expected', [([3, 3, 4, 2, 5, 6, 1, 3], [3, 3, 3, 3, 3, 3, 3, 3], [0, 0, 1, 0, 1, 0, 0, 0]), ([3, 3, 3, 3, 3, 3, 3, 3], [3, 3, 4, 2, 5, 6, 1, 3], [0, 0, 0, 1, 0, 0, 1, 0]), ([1, 1], [1, 1], [0, 0])])
def test_cross(a, b, expected):
    assert np.array_equal(cross(np.array(a), np.array(b)), expected, equal_nan=True)

@pytest.mark.parametrize('a, b, expected_msg', [([1, 2, 3], [3, 3, 3, 3], 'a and b must be same length.'), ([3, 3, 3, 3], [1, 2, 3], 'a and b must be same length.'), ([1, 2, 3], [], 'b cannot be empty.'), ([], [1, 2, 3], 'a cannot be empty.'), ([1], [1], 'a and b must have length >= 2.')])
def test_cross_when_invalid_input_then_error(a, b, expected_msg):
    with pytest.raises(AssertionError, match=re.escape(expected_msg)):
        cross(np.array(a), np.array(b))

@pytest.mark.parametrize('fn, args, expected_length', [(detrended_rsi, {'values': np.random.rand(1000), 'short_length': 2, 'long_length': 4, 'reg_length': 30}, 1000), (detrended_rsi, {'values': np.array([]), 'short_length': 2, 'long_length': 4, 'reg_length': 30}, 0), (detrended_rsi, {'values': np.random.rand(10), 'short_length': 2, 'long_length': 4, 'reg_length': 30}, 10), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 4, 'smoothing': 0.1}, 1000), (macd, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'short_length': 2, 'long_length': 4, 'smoothing': 0.1}, 0), (macd, {'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'short_length': 2, 'long_length': 50, 'smoothing': 0.1}, 10), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 5, 'smoothing': 0}, 1000), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 5, 'smoothing': 1}, 1000), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 5, 'smoothing': 2}, 1000), (stochastic, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'lookback': 5, 'smoothing': 0}, 0), (stochastic, {'high': np.array([1.0]), 'low': np.array([1.0]), 'close': np.array([1.0]), 'lookback': 5, 'smoothing': 0}, 1), (stochastic_rsi, {'values': np.random.rand(1000), 'rsi_lookback': 5, 'sto_lookback': 5}, 1000), (stochastic_rsi, {'values': np.random.rand(1000), 'rsi_lookback': 5, 'sto_lookback': 5, 'smoothing': 0.5}, 1000), (stochastic_rsi, {'values': np.array([]), 'rsi_lookback': 5, 'sto_lookback': 5}, 0), (stochastic_rsi, {'values': np.random.rand(10), 'rsi_lookback': 5, 'sto_lookback': 20}, 10), (stochastic_rsi, {'values': np.random.rand(10), 'rsi_lookback': 20, 'sto_lookback': 5}, 10), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}, 1000), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0.5}, 1000), (linear_trend, {'values': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'lookback': 20, 'atr_length': 10}, 0), (linear_trend, {'values': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}, 10), (linear_trend, {'values': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 10, 'atr_length': 20}, 10), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}, 1000), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0.5}, 1000), (quadratic_trend, {'values': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'lookback': 20, 'atr_length': 10}, 0), (quadratic_trend, {'values': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}, 10), (quadratic_trend, {'values': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 10, 'atr_length': 20}, 10), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}, 1000), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0.5}, 1000), (cubic_trend, {'values': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'lookback': 20, 'atr_length': 10}, 0), (cubic_trend, {'values': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}, 10), (cubic_trend, {'values': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 10, 'atr_length': 20}, 10), (adx, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 10}, 1000), (adx, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'lookback': 10}, 0), (adx, {'high': np.array([1.0]), 'low': np.array([1.0]), 'close': np.array([1.0]), 'lookback': 10}, 1), (aroon_up, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'lookback': 10}, 1000), (aroon_up, {'high': np.array([]), 'low': np.array([]), 'lookback': 10}, 0), (aroon_up, {'high': np.array([1.0]), 'low': np.array([1.0]), 'lookback': 10}, 1), (aroon_down, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'lookback': 10}, 1000), (aroon_down, {'high': np.array([]), 'low': np.array([]), 'lookback': 10}, 0), (aroon_down, {'high': np.array([1.0]), 'low': np.array([1.0]), 'lookback': 10}, 1), (aroon_diff, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'lookback': 10}, 1000), (aroon_diff, {'high': np.array([]), 'low': np.array([]), 'lookback': 10}, 0), (aroon_diff, {'high': np.array([1.0]), 'low': np.array([1.0]), 'lookback': 10}, 1), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}, 1000), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0.5}, 1000), (close_minus_ma, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'lookback': 20, 'atr_length': 10}, 0), (close_minus_ma, {'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}, 10), (close_minus_ma, {'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10), 'lookback': 10, 'atr_length': 20}, 10), (linear_deviation, {'values': np.random.rand(1000), 'lookback': 10}, 1000), (linear_deviation, {'values': np.random.rand(1000), 'lookback': 10, 'scale': 1.0}, 1000), (linear_deviation, {'values': np.array([]), 'lookback': 10}, 0), (linear_deviation, {'values': np.array([1.0]), 'lookback': 10}, 1), (quadratic_deviation, {'values': np.random.rand(1000), 'lookback': 10}, 1000), (quadratic_deviation, {'values': np.random.rand(1000), 'lookback': 10, 'scale': 1.0}, 1000), (quadratic_deviation, {'values': np.array([]), 'lookback': 10}, 0), (quadratic_deviation, {'values': np.array([1.0]), 'lookback': 10}, 1), (cubic_deviation, {'values': np.random.rand(1000), 'lookback': 10}, 1000), (cubic_deviation, {'values': np.random.rand(1000), 'lookback': 10, 'scale': 1.0}, 1000), (cubic_deviation, {'values': np.array([]), 'lookback': 10}, 0), (cubic_deviation, {'values': np.array([1.0]), 'lookback': 10}, 1), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000)}, 1000), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'smoothing': 0.1}, 1000), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'scale': 0.5}, 1000), (price_intensity, {'open': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([])}, 0), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 5, 'multiplier': 2}, 1000), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 5, 'multiplier': 2, 'scale': 1.0}, 1000), (price_change_oscillator, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'short_length': 5, 'multiplier': 2}, 0), (price_change_oscillator, {'high': np.array([1.0]), 'low': np.array([1.0]), 'close': np.array([1.0]), 'short_length': 5, 'multiplier': 2}, 1), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'smoothing': 1.1}, 1000), (intraday_intensity, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (intraday_intensity, {'high': np.array([1.0]), 'low': np.array([1.0]), 'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'smoothing': 1.1}, 1000), (money_flow, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (money_flow, {'high': np.array([1.0]), 'low': np.array([1.0]), 'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'smoothing': 2.0}, 1000), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.0}, 1000), (reactivity, {'high': np.array([]), 'low': np.array([]), 'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (reactivity, {'high': np.array([1.0]), 'low': np.array([1.0]), 'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (price_volume_fit, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (price_volume_fit, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.5}, 1000), (price_volume_fit, {'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (price_volume_fit, {'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (volume_weighted_ma_ratio, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (volume_weighted_ma_ratio, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.5}, 1000), (volume_weighted_ma_ratio, {'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (volume_weighted_ma_ratio, {'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (normalized_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (normalized_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.5}, 1000), (normalized_on_balance_volume, {'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (normalized_on_balance_volume, {'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'delta_length': 10}, 1000), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.0}, 1000), (delta_on_balance_volume, {'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (delta_on_balance_volume, {'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (normalized_positive_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (normalized_positive_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.5}, 1000), (normalized_positive_volume_index, {'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (normalized_positive_volume_index, {'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (normalized_negative_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}, 1000), (normalized_negative_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 1.5}, 1000), (normalized_negative_volume_index, {'close': np.array([]), 'volume': np.array([]), 'lookback': 5}, 0), (normalized_negative_volume_index, {'close': np.array([1.0]), 'volume': np.array([1.0]), 'lookback': 5}, 1), (volume_momentum, {'volume': np.random.rand(1000), 'short_length': 5}, 1000), (volume_momentum, {'volume': np.random.rand(1000), 'short_length': 5, 'multiplier': 3}, 1000), (volume_momentum, {'volume': np.random.rand(1000), 'short_length': 5, 'scale': 1.0}, 1000), (volume_momentum, {'volume': np.array([1.0]), 'short_length': 5}, 1), (volume_momentum, {'volume': np.array([]), 'short_length': 5}, 0), (laguerre_rsi, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000)}, 1000), (laguerre_rsi, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'fe_length': 20}, 1000), (laguerre_rsi, {'open': np.random.rand(10), 'high': np.random.rand(10), 'low': np.random.rand(10), 'close': np.random.rand(10)}, 10), (laguerre_rsi, {'open': np.array([]), 'high': np.array([]), 'low': np.array([]), 'close': np.array([])}, 0)])
def test_indicators(fn, args, expected_length):
    assert len(fn(**args)) == expected_length

@pytest.mark.parametrize('fn, args', [(detrended_rsi, {'values': np.random.rand(100), 'short_length': 1, 'long_length': 4, 'reg_length': 30}), (detrended_rsi, {'values': np.random.rand(100), 'short_length': 1, 'long_length': 1, 'reg_length': 30}), (detrended_rsi, {'values': np.random.rand(100), 'short_length': 5, 'long_length': 4, 'reg_length': 30}), (detrended_rsi, {'values': np.random.rand(100), 'short_length': 2, 'long_length': 4, 'reg_length': 0}), (macd, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 4}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 4}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'short_length': 2, 'long_length': 4}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 0, 'long_length': 4}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 0}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 1}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 4, 'smoothing': -0.1}), (macd, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 2, 'long_length': 4, 'scale': 0}), (stochastic, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 5, 'smoothing': 0}), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'lookback': 5, 'smoothing': 0}), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'lookback': 5, 'smoothing': 0}), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 0, 'smoothing': 0}), (stochastic, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 5, 'smoothing': 3}), (stochastic_rsi, {'values': np.random.rand(1000), 'rsi_lookback': 0, 'sto_lookback': 5}), (stochastic_rsi, {'values': np.random.rand(1000), 'rsi_lookback': 5, 'sto_lookback': 0}), (stochastic_rsi, {'values': np.random.rand(1000), 'rsi_lookback': 5, 'sto_lookback': 5, 'smoothing': -0.1}), (linear_trend, {'values': np.random.rand(10), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 0, 'atr_length': 10}), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 0}), (linear_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0}), (quadratic_trend, {'values': np.random.rand(10), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 0, 'atr_length': 10}), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 0}), (quadratic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0}), (cubic_trend, {'values': np.random.rand(10), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 0, 'atr_length': 10}), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 0}), (cubic_trend, {'values': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0}), (adx, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 10}), (adx, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'lookback': 10}), (adx, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'lookback': 10}), (adx, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 0}), (aroon_up, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'lookback': 10}), (aroon_up, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'lookback': 10}), (aroon_up, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'lookback': 0}), (aroon_down, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'lookback': 10}), (aroon_down, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'lookback': 10}), (aroon_down, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'lookback': 0}), (aroon_diff, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'lookback': 10}), (aroon_diff, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'lookback': 10}), (aroon_diff, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'lookback': 0}), (close_minus_ma, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10}), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'lookback': 20, 'atr_length': 10}), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 0, 'atr_length': 10}), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 0}), (close_minus_ma, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'lookback': 20, 'atr_length': 10, 'scale': 0}), (linear_deviation, {'values': np.random.rand(1000), 'lookback': 0}), (quadratic_deviation, {'values': np.random.rand(1000), 'lookback': 0}), (cubic_deviation, {'values': np.random.rand(1000), 'lookback': 0}), (price_intensity, {'open': np.random.rand(10), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000)}), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000)}), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000)}), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10)}), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'smoothing': -1}), (price_intensity, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'scale': 0}), (price_change_oscillator, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 5, 'multiplier': 2}), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'short_length': 5, 'multiplier': 2}), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'short_length': 5, 'multiplier': 2}), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 0, 'multiplier': 2}), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 5, 'multiplier': 0}), (price_change_oscillator, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'short_length': 5, 'multiplier': 2, 'scale': 0}), (intraday_intensity, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (intraday_intensity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'smoothing': -1}), (money_flow, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (money_flow, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'smoothing': -1}), (reactivity, {'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5}), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'smoothing': -1}), (reactivity, {'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 0}), (price_volume_fit, {'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (price_volume_fit, {'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (price_volume_fit, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (volume_weighted_ma_ratio, {'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (volume_weighted_ma_ratio, {'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (volume_weighted_ma_ratio, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (normalized_on_balance_volume, {'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (normalized_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (normalized_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (normalized_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 0}), (delta_on_balance_volume, {'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 0}), (delta_on_balance_volume, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'delta_length': -1}), (normalized_positive_volume_index, {'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (normalized_positive_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (normalized_positive_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (normalized_positive_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 0}), (normalized_negative_volume_index, {'close': np.random.rand(10), 'volume': np.random.rand(1000), 'lookback': 5}), (normalized_negative_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(10), 'lookback': 5}), (normalized_negative_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 0}), (normalized_negative_volume_index, {'close': np.random.rand(1000), 'volume': np.random.rand(1000), 'lookback': 5, 'scale': 0}), (volume_momentum, {'volume': np.random.rand(1000), 'short_length': 0}), (volume_momentum, {'volume': np.random.rand(1000), 'short_length': 5, 'multiplier': 0}), (volume_momentum, {'volume': np.random.rand(1000), 'short_length': 5, 'scale': 0}), (laguerre_rsi, {'open': np.random.rand(10), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000)}), (laguerre_rsi, {'open': np.random.rand(1000), 'high': np.random.rand(10), 'low': np.random.rand(1000), 'close': np.random.rand(1000)}), (laguerre_rsi, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(10), 'close': np.random.rand(1000)}), (laguerre_rsi, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(10)}), (laguerre_rsi, {'open': np.random.rand(1000), 'high': np.random.rand(1000), 'low': np.random.rand(1000), 'close': np.random.rand(1000), 'fe_length': 0})])
def test_indicators_when_assertion_error(fn, args):
    with pytest.raises(AssertionError):
        fn(**args)

def test_bar_data_get_custom_data_when_no_attr_then_error():
    date = np.full(10, np.datetime64('2022-02-02'))
    open_ = np.full(10, 1)
    high = np.full(10, 2)
    low = np.full(10, 3)
    close = np.full(10, 4)
    bar_data = BarData(date=date, open=open_, high=high, low=low, close=close, volume=None, vwap=None)
    with pytest.raises(AttributeError, match=re.escape("Attribute 'foo' not found.")):
        bar_data.foo

@pytest.mark.parametrize('tf, expected', [('1day 2h 3min', [(1, 'day'), (2, 'hour'), (3, 'min')]), ('10week', [(10, 'week')]), ('3d 20m', [(3, 'day'), (20, 'min')]), ('30s', [(30, 'sec')])])
def test_parse_timeframe_success(tf, expected):
    assert parse_timeframe(tf) == expected

@pytest.mark.parametrize('tf', ['10foo', '20days', '10d 5 m', '1w 2w 3w 5min', 'dd ff cc', 'w d m', '1d5m', '1d 5mm', ''])
def test_parse_timeframe_invalid(tf):
    with pytest.raises(ValueError, match=re.escape('Invalid timeframe format.')):
        parse_timeframe(tf)

def test_quantize_when_column_not_found_then_error():
    df = pd.DataFrame([[Decimal('0.9999'), Decimal('1.22222')], [Decimal('0.1'), Decimal('0.22')], [Decimal('0.33'), Decimal('0.2222')], [Decimal(1), Decimal('0.1')]], columns=['a', 'b'])
    with pytest.raises(ValueError, match=re.escape("Column 'c' not found in DataFrame.")):
        quantize(df, 'c', True)

def test_verify_data_source_columns_when_missing_then_error():
    df = pd.DataFrame(columns=['symbol', 'date', 'open', 'high', 'low'])
    with pytest.raises(ValueError, match=re.escape("DataFrame is missing required columns: ['close']")):
        verify_data_source_columns(df)

class TestRandomSlippageModel:

    def test_init_when_invalid_min_pct_then_error(self):
        with pytest.raises(ValueError, match=re.escape('min_pct must be between 0% and 100%.')):
            RandomSlippageModel(min_pct=-1, max_pct=100)

    def test_init_when_invalid_max_pct_then_error(self):
        with pytest.raises(ValueError, match=re.escape('max_pct must be between 0% and 100%.')):
            RandomSlippageModel(min_pct=0, max_pct=101)

    def test_init_when_min_gte_max_pct_then_error(self):
        with pytest.raises(ValueError, match=re.escape('min_pct must be < max_pct.')):
            RandomSlippageModel(min_pct=5, max_pct=1)

    def test_slip_when_buy_shares(self, ctx):
        model = RandomSlippageModel(min_pct=1, max_pct=2)
        with patch.object(random, 'uniform', return_value='0.01'):
            model.apply_slippage(ctx, buy_shares=100, sell_shares=None)
            assert ctx.buy_shares == Decimal(99)
            assert ctx.sell_shares is None

    def test_slip_when_sell_shares(self, ctx):
        model = RandomSlippageModel(min_pct=1, max_pct=2)
        with patch.object(random, 'uniform', return_value='0.01'):
            model.apply_slippage(ctx, buy_shares=None, sell_shares=100)
            assert ctx.sell_shares == Decimal(99)
            assert ctx.buy_shares is None

def test_init_when_invalid_min_pct_then_error(self):
    with pytest.raises(ValueError, match=re.escape('min_pct must be between 0% and 100%.')):
        RandomSlippageModel(min_pct=-1, max_pct=100)

def test_init_when_invalid_max_pct_then_error(self):
    with pytest.raises(ValueError, match=re.escape('max_pct must be between 0% and 100%.')):
        RandomSlippageModel(min_pct=0, max_pct=101)

def test_init_when_min_gte_max_pct_then_error(self):
    with pytest.raises(ValueError, match=re.escape('min_pct must be < max_pct.')):
        RandomSlippageModel(min_pct=5, max_pct=1)

@pytest.mark.parametrize('drop_col', ['date', 'open', 'high', 'low', 'close'])
def test_to_bar_data_when_missing_cols_then_error(drop_col, data_source_df):
    with pytest.raises(ValueError, match=f'DataFrame is missing required column: {drop_col}'):
        _to_bar_data(data_source_df.drop(columns=drop_col))

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

def invalid_shape(_data):
    return np.array([[1, 2, 3], [4, 5, 6]])

def test_call_when_invalid_shape_then_error(self, data_source_df):

    def invalid_shape(_data):
        return np.array([[1, 2, 3], [4, 5, 6]])
    ind_invalid_shape = indicator('invalid_shape', invalid_shape)
    with pytest.raises(ValueError, match=re.escape('Indicator invalid_shape must return a one-dimensional array.')):
        ind_invalid_shape(data_source_df)

@pytest.mark.parametrize('fn, values, period, expected', [(highest, [3, 3, 4, 2, 5, 6, 1, 3], 3, [np.nan, np.nan, 4, 4, 5, 6, 6, 6]), (highest, [3, 3, 4, 2, 5, 6, 1, 3], 1, [3, 3, 4, 2, 5, 6, 1, 3]), (highest, [4, 3, 2, 1], 4, [np.nan, np.nan, np.nan, 4]), (highest, [1], 1, [1]), (lowest, [3, 3, 4, 2, 5, 6, 1, 3], 3, [np.nan, np.nan, 3, 2, 2, 2, 1, 1]), (lowest, [3, 3, 4, 2, 5, 6, 1, 3], 1, [3, 3, 4, 2, 5, 6, 1, 3]), (lowest, [4, 3, 2, 1], 4, [np.nan, np.nan, np.nan, 1]), (lowest, [1], 1, [1]), (returns, [1, 1.5, 1.7, 1.3, 1.2, 1.4], 1, [np.nan, 0.5, 0.13333333, -0.23529412, -0.07692308, 0.16666667]), (returns, [1, 1.5, 1.7, 1.3, 1.2, 1.4], 2, [np.nan, np.nan, 0.7, -0.133333, -0.294118, 0.076923]), (returns, [1], 1, [np.nan]), (returns, [], 5, [])])
def test_wrappers(fn, values, period, expected):
    n = len(values)
    dates = pd.date_range(start='1/1/2018', end='1/1/2019').to_numpy()[:n]
    bar_data = BarData(date=dates, open=np.zeros(n), high=np.zeros(n), low=np.zeros(n), close=np.array(values), volume=None, vwap=None)
    indicator = fn('my_indicator', 'close', period)
    assert isinstance(indicator, Indicator)
    assert indicator.name == 'my_indicator'
    series = indicator(bar_data)
    assert np.array_equal(series.index.to_numpy(), dates)
    assert np.array_equal(np.round(series.values, 6), np.round(expected, 6), equal_nan=True)

@pytest.mark.parametrize('fn, args', [(detrended_rsi, {'field': 'close', 'short_length': 5, 'long_length': 10, 'reg_length': 20}), (macd, {'short_length': 5, 'long_length': 10, 'smoothing': 2.0}), (stochastic, {'lookback': 10, 'smoothing': 2}), (stochastic_rsi, {'field': 'close', 'rsi_lookback': 10, 'sto_lookback': 10, 'smoothing': 2.0}), (linear_trend, {'field': 'close', 'lookback': 10, 'atr_length': 20, 'scale': 0.5}), (quadratic_trend, {'field': 'close', 'lookback': 10, 'atr_length': 20, 'scale': 0.5}), (cubic_trend, {'field': 'close', 'lookback': 10, 'atr_length': 20, 'scale': 0.5}), (adx, {'lookback': 10}), (aroon_up, {'lookback': 10}), (aroon_down, {'lookback': 10}), (aroon_diff, {'lookback': 10}), (close_minus_ma, {'lookback': 10, 'atr_length': 20, 'scale': 0.5}), (linear_deviation, {'field': 'close', 'lookback': 10, 'scale': 0.5}), (quadratic_deviation, {'field': 'close', 'lookback': 10, 'scale': 0.5}), (cubic_deviation, {'field': 'close', 'lookback': 10, 'scale': 0.5}), (price_intensity, {'smoothing': 1.0, 'scale': 0.5}), (price_change_oscillator, {'short_length': 5, 'multiplier': 3, 'scale': 0.5}), (intraday_intensity, {'lookback': 10, 'smoothing': 1.0}), (money_flow, {'lookback': 10, 'smoothing': 1.0}), (reactivity, {'lookback': 10, 'smoothing': 1.0, 'scale': 0.5}), (price_volume_fit, {'lookback': 10, 'scale': 0.5}), (volume_weighted_ma_ratio, {'lookback': 10, 'scale': 0.5}), (normalized_on_balance_volume, {'lookback': 10, 'scale': 0.5}), (delta_on_balance_volume, {'lookback': 10, 'delta_length': 5, 'scale': 0.5}), (normalized_positive_volume_index, {'lookback': 10, 'scale': 0.5}), (normalized_negative_volume_index, {'lookback': 10, 'scale': 0.5}), (volume_momentum, {'short_length': 5, 'multiplier': 2, 'scale': 2.0}), (laguerre_rsi, {'fe_length': 20})])
def test_indicators(fn, args):
    dates = pd.date_range(start='1/1/2018', end='1/1/2019').to_numpy()
    n = len(dates)
    bar_data = BarData(date=dates, open=np.random.rand(n), high=np.random.rand(n), low=np.random.rand(n), close=np.random.rand(n), volume=np.random.rand(n), vwap=None)
    indicator = fn(fn.__name__, **args)
    assert isinstance(indicator, Indicator)
    assert indicator.name == fn.__name__
    series = indicator(bar_data)
    assert len(series) == n
    assert np.array_equal(series.index.to_numpy(), dates)

def test_register_columns_when_frozen_then_error(scope):
    scope.freeze_data_cols()
    with pytest.raises(ValueError, match=re.escape('Cannot modify columns when strategy is running.')):
        register_columns('a')
    scope.unfreeze_data_cols()

def test_unregister_columns_when_frozen_then_error(scope):
    scope.freeze_data_cols()
    with pytest.raises(ValueError, match=re.escape('Cannot modify columns when strategy is running.')):
        unregister_columns('a')
    scope.unfreeze_data_cols()

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

def test_get_indicator_when_not_found_then_error(self, scope):
    with pytest.raises(ValueError, match=re.escape("Indicator 'foo' does not exist.")):
        scope.get_indicator('foo')

def test_get_model_source_when_not_found_then_error(self, scope):
    with pytest.raises(ValueError, match=re.escape("ModelSource 'foo' does not exist.")):
        scope.get_model_source('foo')

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

def test_fetch_when_symbol_not_found_then_error(self, col_scope, end_index):
    with pytest.raises(ValueError, match=re.escape('Symbol not found: FOO.')):
        col_scope.fetch('FOO', 'close', end_index)

def test_fetch_dict_when_symbol_not_found_then_error(self, col_scope, end_index):
    with pytest.raises(ValueError, match=re.escape('Symbol not found: FOO.')):
        col_scope.fetch_dict('FOO', ['close'], end_index)

class TestIndicatorScope:

    def test_fetch(self, ind_scope, symbol, ind_data, ind_name, end_index):
        result = ind_scope.fetch(symbol, ind_name, end_index)
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, ind_data[IndicatorSymbol(ind_name, symbol)].values[:end_index], equal_nan=True)

    def test_fetch_when_cached(self, ind_scope, symbol, ind_data, ind_name, end_index):
        ind_scope.fetch(symbol, ind_name, end_index)
        result = ind_scope.fetch(symbol, ind_name, end_index)
        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, ind_data[IndicatorSymbol(ind_name, symbol)].values[:end_index], equal_nan=True)

    @pytest.mark.parametrize('sym, name', [('FOO', 'hhv'), ('SPY', 'foo')])
    def test_fetch_when_not_found_then_error(self, ind_scope, sym, name):
        with pytest.raises(ValueError, match=re.escape(f'Indicator {name!r} not found for {sym}.')):
            ind_scope.fetch(sym, name)

@pytest.mark.parametrize('sym, name', [('FOO', 'hhv'), ('SPY', 'foo')])
def test_fetch_when_not_found_then_error(self, ind_scope, sym, name):
    with pytest.raises(ValueError, match=re.escape(f'Indicator {name!r} not found for {sym}.')):
        ind_scope.fetch(sym, name)

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

@pytest.mark.parametrize('sym, name, expected_msg', [('FOO', MODEL_NAME, 'Symbol not found: FOO'), ('SPY', 'foo', "Model 'foo' not found.")])
def test_fetch_when_not_found_then_error(self, input_scope, sym, name, expected_msg):
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        input_scope.fetch(sym, name)

class TestPredictionScope:

    def test_fetch(self, pred_scope, preds, trained_model, symbol, data_source_df, end_index):
        values = pred_scope.fetch(symbol, trained_model.name, end_index)
        assert isinstance(values, np.ndarray)
        expected = preds[symbol] if end_index is None else preds[symbol][:end_index]
        assert np.array_equal(values, expected, equal_nan=True)
        df = data_source_df[data_source_df['symbol'] == symbol]
        assert len(values) == df.shape[0] if end_index is None else end_index

    def test_fetch_when_cached(self, pred_scope, preds, trained_model, symbol, data_source_df, end_index):
        pred_scope.fetch(symbol, trained_model.name, end_index)
        values = pred_scope.fetch(symbol, trained_model.name, end_index)
        assert isinstance(values, np.ndarray)
        expected = preds[symbol] if end_index is None else preds[symbol][:end_index]
        assert np.array_equal(values, expected, equal_nan=True)
        df = data_source_df[data_source_df['symbol'] == symbol]
        assert len(values) == df.shape[0] if end_index is None else end_index

    @pytest.mark.parametrize('sym, name, expected_msg', [('FOO', MODEL_NAME, 'Symbol not found: FOO'), ('SPY', 'foo', "Model 'foo' not found.")])
    def test_fetch_when_not_found_then_error(self, pred_scope, sym, name, expected_msg):
        with pytest.raises(ValueError, match=re.escape(expected_msg)):
            pred_scope.fetch(sym, name)

    def test_fetch_when_predict_not_defined_then_error(self, input_scope):
        model = TrainedModel(name=MODEL_NAME, instance={}, predict_fn=None, input_cols=None)
        pred_scope = PredictionScope(models={ModelSymbol(MODEL_NAME, 'SPY'): model}, input_scope=input_scope)
        with pytest.raises(ValueError, match=re.escape(f'Model instance trained for {MODEL_NAME!r} does not define a predict function. Please pass a predict_fn to pybroker.model().')):
            pred_scope.fetch('SPY', MODEL_NAME)

    def test_fetch_when_input_data_empty_then_error(self, col_scope):
        model_name = 'no_input_data'
        ind_scope = IndicatorScope({}, [])
        pybroker.model(model_name, lambda sym, train, test: {})
        model = TrainedModel(name=model_name, instance={}, predict_fn=None, input_cols=None)
        models = {ModelSymbol(model_name, 'SPY'): model}
        input_scope = ModelInputScope(col_scope, ind_scope, models)
        pred_scope = PredictionScope(models, input_scope)
        with pytest.raises(ValueError, match=re.escape(f'No input data found for model {model_name!r}. Consider passing input_data_fn to pybroker#model() if custom columns were registered.')):
            pred_scope.fetch('SPY', model_name)

@pytest.mark.parametrize('sym, name, expected_msg', [('FOO', MODEL_NAME, 'Symbol not found: FOO'), ('SPY', 'foo', "Model 'foo' not found.")])
def test_fetch_when_not_found_then_error(self, pred_scope, sym, name, expected_msg):
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        pred_scope.fetch(sym, name)

def test_fetch_when_predict_not_defined_then_error(self, input_scope):
    model = TrainedModel(name=MODEL_NAME, instance={}, predict_fn=None, input_cols=None)
    pred_scope = PredictionScope(models={ModelSymbol(MODEL_NAME, 'SPY'): model}, input_scope=input_scope)
    with pytest.raises(ValueError, match=re.escape(f'Model instance trained for {MODEL_NAME!r} does not define a predict function. Please pass a predict_fn to pybroker.model().')):
        pred_scope.fetch('SPY', MODEL_NAME)

def test_fetch_when_input_data_empty_then_error(self, col_scope):
    model_name = 'no_input_data'
    ind_scope = IndicatorScope({}, [])
    pybroker.model(model_name, lambda sym, train, test: {})
    model = TrainedModel(name=model_name, instance={}, predict_fn=None, input_cols=None)
    models = {ModelSymbol(model_name, 'SPY'): model}
    input_scope = ModelInputScope(col_scope, ind_scope, models)
    pred_scope = PredictionScope(models, input_scope)
    with pytest.raises(ValueError, match=re.escape(f'No input data found for model {model_name!r}. Consider passing input_data_fn to pybroker#model() if custom columns were registered.')):
        pred_scope.fetch('SPY', model_name)

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

def test_walkforward_split_1(self, dates, dates_length, windows, lookahead, train_size, shuffle):
    self._verify_windows(dates, dates_length, windows, lookahead, train_size, shuffle)

@pytest.mark.parametrize('dates_length, windows, lookahead', [(22, 5, 1), (20, 5, 1), (22, 2, 2), (20, 2, 2)])
def test_walkforward_split_2(self, dates, dates_length, windows, lookahead, train_size, shuffle):
    self._verify_windows(dates, dates_length, windows, lookahead, train_size, shuffle)

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

def test_filter_dates_when_invalid_between_time_then_error(self, data_source_df):
    strategy = Strategy(data_source_df, START_DATE, END_DATE)
    start_date = pd.to_datetime('1/1/2021').to_pydatetime()
    end_date = pd.to_datetime('12/1/2021').to_pydatetime()
    with pytest.raises(ValueError, match=re.escape("between_time must be a tuple[str, str] of start time and end time, received '9:00'.")):
        strategy._filter_dates(data_source_df, start_date, end_date, days=None, between_time='9:00')

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

class TestAlpaca:

    def test_init(self, mock_alpaca):
        Alpaca(API_KEY, API_SECRET)
        mock_alpaca.assert_called_once_with(API_KEY, API_SECRET)

    @pytest.mark.usefixtures('setup_ds_cache', 'mock_alpaca')
    def test_query_when_empty_cache(self, alpaca_df, bars_df, symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        mock_bars = mock.Mock()
        mock_bars.df = bars_df
        with mock.patch.object(alpaca._api, 'get_stock_bars', return_value=mock_bars):
            df = alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME, adjust='all')
            df = df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            expected = alpaca_df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            assert df.equals(expected)

    def test_query_when_invalid_adj_then_error(self, symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        with pytest.raises(ValueError, match=re.escape('Unknown adjustment: foo')):
            alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME, adjust='foo')

    @pytest.mark.usefixtures('setup_enabled_ds_cache', 'mock_alpaca', 'tmp_path')
    def test_query_when_partial_cache(self, alpaca_df, bars_df, symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        cached_df = alpaca_df[alpaca_df['symbol'].isin(symbols[-1:])]
        alpaca.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, cached_df)
        mock_bars = mock.Mock()
        mock_bars.df = bars_df[bars_df['symbol'].isin(symbols[:-1])]
        with mock.patch.object(alpaca._api, 'get_stock_bars', return_value=mock_bars):
            df = alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME, ADJUST)
            df = df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            expected = alpaca_df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            assert df.equals(expected)

    @pytest.mark.usefixtures('setup_enabled_ds_cache', 'mock_alpaca', 'tmp_path')
    def test_query_when_cache_mismatch(self, alpaca_df, bars_df, symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        cached_df = alpaca_df[alpaca_df['symbol'].isin(symbols[-1:])]
        cached_df = cached_df.drop(columns=['vwap'])
        alpaca.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, cached_df)
        mock_bars = mock.Mock()
        mock_bars.df = bars_df[bars_df['symbol'].isin(symbols[:-1])]
        with mock.patch.object(alpaca._api, 'get_stock_bars', return_value=mock_bars):
            df = alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME, ADJUST)
            assert not df.empty
            assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'vwap'))

    @pytest.mark.usefixtures('setup_ds_cache', 'mock_alpaca')
    def test_query_when_cached(self, alpaca_df, bars_df, symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        mock_bars = mock.Mock()
        mock_bars.df = bars_df
        with mock.patch.object(alpaca._api, 'get_stock_bars', return_value=mock_bars):
            alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME)
            df = alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME)
            df = df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            expected = alpaca_df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            assert df.equals(expected)

    @pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'vwap']])
    @pytest.mark.usefixtures('setup_ds_cache', 'mock_alpaca')
    def test_query_when_empty_result(self, symbols, columns):
        alpaca = Alpaca(API_KEY, API_SECRET)
        mock_bars = mock.Mock()
        mock_bars.df = pd.DataFrame(columns=columns)
        with mock.patch.object(alpaca._api, 'get_stock_bars', return_value=mock_bars):
            df = alpaca.query(symbols, START_DATE, END_DATE, TIMEFRAME)
            assert df.empty
            assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'vwap'))

    @pytest.mark.parametrize('empty_symbols', ['', []])
    @pytest.mark.usefixtures('setup_ds_cache', 'mock_alpaca')
    def test_query_when_symbols_empty(self, empty_symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        with pytest.raises(ValueError, match=re.escape('Symbols cannot be empty.')):
            alpaca.query(empty_symbols, START_DATE, END_DATE, TIMEFRAME)

    @pytest.mark.parametrize('timeframe', ['1w 2d', '30s'])
    def test_query_when_invalid_timeframe_then_error(self, symbols, timeframe):
        alpaca = Alpaca(API_KEY, API_SECRET)
        with pytest.raises(ValueError, match=re.escape(f'Invalid Alpaca timeframe: {timeframe}')):
            alpaca.query(symbols, START_DATE, END_DATE, timeframe)

    def test_query_when_null_timeframe_then_error(self, symbols):
        alpaca = Alpaca(API_KEY, API_SECRET)
        with pytest.raises(ValueError, match=re.escape('Timeframe needs to be specified for Alpaca.')):
            alpaca.query(symbols, START_DATE, END_DATE, timeframe=None)

@pytest.mark.parametrize('timeframe', ['1w 2d', '30s'])
def test_query_when_invalid_timeframe_then_error(self, symbols, timeframe):
    alpaca = Alpaca(API_KEY, API_SECRET)
    with pytest.raises(ValueError, match=re.escape(f'Invalid Alpaca timeframe: {timeframe}')):
        alpaca.query(symbols, START_DATE, END_DATE, timeframe)

class TestAlpacaCrypto:

    def test_init(self, mock_alpaca_crypto):
        AlpacaCrypto(API_KEY, API_SECRET)
        mock_alpaca_crypto.assert_called_once_with(API_KEY, API_SECRET)

    @pytest.mark.usefixtures('setup_ds_cache', 'mock_alpaca')
    def test_query(self, alpaca_crypto_df, crypto_bars_df, symbols):
        crypto = AlpacaCrypto(API_KEY, API_SECRET)
        mock_bars = mock.Mock()
        mock_bars.df = crypto_bars_df
        with mock.patch.object(crypto._api, 'get_crypto_bars', return_value=mock_bars):
            df = crypto.query(symbols, START_DATE, END_DATE, TIMEFRAME)
            df = df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            expected = alpaca_crypto_df.sort_values(['symbol', 'date']).reset_index(drop=True).sort_index(axis=1)
            assert df.equals(expected)

    @pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'vwap', 'trade_count']])
    @pytest.mark.usefixtures('setup_ds_cache', 'mock_alpaca')
    def test_query_when_empty_result(self, symbols, columns):
        crypto = AlpacaCrypto(API_KEY, API_SECRET)
        mock_bars = mock.Mock()
        mock_bars.df = pd.DataFrame(columns=columns)
        with mock.patch.object(crypto._api, 'get_crypto_bars', return_value=mock_bars):
            df = crypto.query(symbols, START_DATE, END_DATE, TIMEFRAME)
            assert df.empty
            assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'vwap', 'trade_count'))

    @pytest.mark.parametrize('timeframe', ['1w 2d', '30s'])
    def test_query_when_invalid_timeframe_then_error(self, symbols, timeframe):
        crypto = AlpacaCrypto(API_KEY, API_SECRET)
        with pytest.raises(ValueError, match=re.escape(f'Invalid Alpaca timeframe: {timeframe}')):
            crypto.query(symbols, START_DATE, END_DATE, timeframe)

    def test_query_when_null_timeframe_then_error(self, symbols):
        crypto = Alpaca(API_KEY, API_SECRET)
        with pytest.raises(ValueError, match=re.escape('Timeframe needs to be specified for Alpaca.')):
            crypto.query(symbols, START_DATE, END_DATE, timeframe=None)

@pytest.mark.parametrize('timeframe', ['1w 2d', '30s'])
def test_query_when_invalid_timeframe_then_error(self, symbols, timeframe):
    crypto = AlpacaCrypto(API_KEY, API_SECRET)
    with pytest.raises(ValueError, match=re.escape(f'Invalid Alpaca timeframe: {timeframe}')):
        crypto.query(symbols, START_DATE, END_DATE, timeframe)

def test_field_not_found_then_error(ctx):
    with pytest.raises(AttributeError, match=re.escape("Attribute 'foo' not found.")):
        ctx.foo

def test_sell_all_shares_when_no_position(ctx):
    with pytest.raises(ValueError, match=re.escape('sell_all_shares failed: No long position for SPY')):
        ctx.sell_all_shares()

def test_cover_all_shares_when_no_position(ctx):
    with pytest.raises(ValueError, match=re.escape('cover_all_shares failed: No short position for SPY')):
        ctx.cover_all_shares()

def test_model_when_not_found_then_error(ctx, symbol):
    with pytest.raises(ValueError, match=re.escape(f"Model 'undefined_model' not found for {symbol}.")):
        ctx.model('undefined_model')

def test_indicator_when_not_found_then_error(ctx, symbol):
    with pytest.raises(ValueError, match=re.escape(f"Indicator 'undefined_indicator' not found for {symbol}.")):
        ctx.indicator('undefined_indicator')

def test_input_when_not_found_then_error(ctx):
    with pytest.raises(ValueError, match=re.escape("Model 'undefined_model' not found.")):
        ctx.input('undefined_model')

def test_preds_when_not_found_then_error(ctx):
    with pytest.raises(ValueError, match=re.escape("Model 'undefined_model' not found.")):
        ctx.preds('undefined_model')

def test_position_when_invalid_pos_type_then_error(ctx, symbol):
    with pytest.raises(ValueError, match=re.escape("Unknown pos_type: 'invalid'.")):
        ctx.pos(symbol, 'invalid')

def test_foreign_when_symbol_not_found_then_error(ctx):
    with pytest.raises(ValueError, match=re.escape("Symbol 'FOO' not found.")):
        ctx.foreign('FOO', 'close')

def test_to_result_when_buy_shares_and_sell_shares_then_error(ctx):
    ctx.buy_shares = 100
    ctx.sell_shares = 100
    with pytest.raises(ValueError, match=re.escape('For each symbol, only one of buy_shares or sell_shares can be set per bar.')):
        ctx.to_result()

@pytest.mark.parametrize('attr, value, error', [('buy_limit_price', 100, 'buy_shares must be set when buy_limit_price is set.'), ('buy_fill_price', PriceType.CLOSE, 'buy_shares or hold_bars must be set when buy_fill_price is set.')])
def test_to_result_when_not_buy_shares_then_error(ctx, attr, value, error):
    ctx.sell_shares = 100
    setattr(ctx, attr, value)
    with pytest.raises(ValueError, match=re.escape(error)):
        ctx.to_result()

@pytest.mark.parametrize('attr, value, error', [('sell_limit_price', 100, 'sell_shares must be set when sell_limit_price is set.'), ('sell_fill_price', PriceType.CLOSE, 'sell_shares or hold_bars must be set when sell_fill_price is set.')])
def test_to_result_when_not_sell_shares_then_error(ctx, attr, value, error):
    ctx.buy_shares = 100
    setattr(ctx, attr, value)
    with pytest.raises(ValueError, match=re.escape(error)):
        ctx.to_result()

@pytest.mark.parametrize('attr, value, error', [('hold_bars', 2, 'Either buy_shares or sell_shares must be set when hold_bars is set.')])
def test_to_result_not_buy_shares_and_not_sell_shares_then_error(ctx, attr, value, error):
    setattr(ctx, attr, value)
    with pytest.raises(ValueError, match=re.escape(error)):
        ctx.to_result()

@pytest.mark.parametrize('attr', ['stop_loss', 'stop_loss_pct', 'stop_loss_limit', 'stop_profit', 'stop_profit_pct', 'stop_profit_limit', 'stop_trailing', 'stop_trailing_pct', 'stop_trailing_limit'])
def test_to_result_not_buy_shares_and_not_sell_shares_and_stop_then_error(ctx, attr):
    setattr(ctx, attr, 10)
    with pytest.raises(ValueError, match=re.escape('Either buy_shares or sell_shares must be set when a stop is set.')):
        ctx.to_result()

def test_result_when_not_buy_shares_and_not_sell_shares_then_return_none(ctx):
    assert ctx.to_result() is None

def test_result_when_default_buy_fill_price(ctx):
    ctx.buy_shares = 100
    result = ctx.to_result()
    assert result.buy_fill_price == PriceType.MIDDLE

def test_result_when_default_sell_fill_price(ctx):
    ctx.sell_shares = 100
    result = ctx.to_result()
    assert result.sell_fill_price == PriceType.MIDDLE

@pytest.mark.parametrize('pos_type', ['long', 'short'])
@pytest.mark.parametrize('stop_attr, expected_stop_type', [('stop_loss', StopType.LOSS), ('stop_loss_pct', StopType.LOSS), ('stop_profit', StopType.PROFIT), ('stop_profit_pct', StopType.PROFIT), ('stop_trailing', StopType.TRAILING), ('stop_trailing_pct', StopType.TRAILING)])
def test_to_result_when_stop(ctx, symbol, date, pos_type, stop_attr, expected_stop_type):
    stop_limit = 200
    stop_amount = 20
    exit_price = PriceType.OPEN
    percent = None
    points = None
    if stop_attr.endswith('_pct'):
        percent = stop_amount
    else:
        points = stop_amount
    buy_shares = None
    sell_shares = None
    if pos_type == 'long':
        buy_shares = 100
    else:
        sell_shares = 100
    ctx.buy_shares = buy_shares
    ctx.sell_shares = sell_shares
    setattr(ctx, stop_attr, stop_amount)
    setattr(ctx, f'{stop_attr.replace('_pct', '')}_limit', stop_limit)
    setattr(ctx, f'{stop_attr.replace('_pct', '')}_exit_price', exit_price)
    result = ctx.to_result()
    assert result.symbol == symbol
    assert result.date == date
    assert result.buy_fill_price == PriceType.MIDDLE
    assert result.buy_limit_price is None
    assert result.sell_fill_price == PriceType.MIDDLE
    assert result.sell_limit_price is None
    assert result.hold_bars is None
    assert result.score is None
    if pos_type == 'long':
        assert result.buy_shares == 100
        assert result.sell_shares is None
        assert len(result.long_stops) == 1
        assert result.short_stops is None
        stop = next(iter(result.long_stops))
    else:
        assert result.sell_shares == 100
        assert result.buy_shares is None
        assert len(result.short_stops) == 1
        assert result.long_stops is None
        stop = next(iter(result.short_stops))
    assert stop.symbol == symbol
    assert stop.stop_type == expected_stop_type
    assert stop.pos_type == pos_type
    assert stop.percent == percent
    assert stop.points == points
    assert stop.bars is None
    assert stop.fill_price is None
    assert stop.limit_price == stop_limit
    assert stop.exit_price == exit_price

@pytest.mark.parametrize('stop_attr', ['stop_loss', 'stop_profit', 'stop_trailing'])
def test_to_result_when_stop_pct_and_points_then_error(ctx, stop_attr):
    ctx.buy_shares = 100
    with pytest.raises(ValueError, match=re.escape(f'Only one of {stop_attr} or {stop_attr}_pct can be set.')):
        setattr(ctx, stop_attr, 20)
        setattr(ctx, f'{stop_attr}_pct', 20)
        ctx.to_result()

@pytest.mark.parametrize('stop_attr', ['stop_loss', 'stop_profit', 'stop_trailing'])
def test_to_result_when_stop_limit_and_not_stop_then_error(ctx, stop_attr):
    ctx.buy_shares = 100
    with pytest.raises(ValueError, match=re.escape(f'Either {stop_attr} or {stop_attr}_pct must be set when {stop_attr}_limit is set.')):
        setattr(ctx, f'{stop_attr}_limit', 20)
        ctx.to_result()

@pytest.mark.parametrize('stop_attr', ['stop_loss', 'stop_profit', 'stop_trailing'])
def test_to_result_when_stop_exit_price_and_not_stop_then_error(ctx, stop_attr):
    ctx.buy_shares = 100
    with pytest.raises(ValueError, match=re.escape(f'Either {stop_attr} or {stop_attr}_pct must be set when {stop_attr}_exit_price is set.')):
        setattr(ctx, f'{stop_attr}_exit_price', PriceType.CLOSE)
        ctx.to_result()

@pytest.mark.parametrize('stop_attr', ['stop_loss', 'stop_profit', 'stop_trailing'])
def test_to_result_when_stop_exit_not_valid_then_error(ctx, stop_attr):
    ctx.buy_shares = 100
    with pytest.raises(ValueError, match=re.escape('Stop exit price must be a PriceType.')):
        setattr(ctx, f'{stop_attr}_pct', 10)
        setattr(ctx, f'{stop_attr}_exit_price', 20)
        ctx.to_result()

@pytest.mark.parametrize('cover_attr, buy_attr', [('cover_fill_price', 'buy_fill_price'), ('cover_shares', 'buy_shares'), ('cover_limit_price', 'buy_limit_price')])
def test_cover(ctx, cover_attr, buy_attr):
    setattr(ctx, cover_attr, 99)
    assert getattr(ctx, cover_attr) == 99
    assert getattr(ctx, cover_attr) == getattr(ctx, buy_attr)
    assert ctx._cover is True

@pytest.mark.parametrize('n, n_boot, expected_msg', [(0, 100, 'Bootstrap sample size must be greater than 0.'), (-1, 100, 'Bootstrap sample size must be greater than 0.'), (10, 0, 'Number of boostrap samples must be greater than 0.'), (10, -1, 'Number of boostrap samples must be greater than 0.')])
def test_bca_boot_conf_when_invalid_params_then_error(n, n_boot, expected_msg):
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        bca_boot_conf(np.random.rand(100), n, n_boot, profit_factor)

@pytest.mark.parametrize('n, n_boot', [(1, 100), (1, 1), (10, 100), (10, 1)])
def test_drawdown_conf(n, n_boot, rand_values):
    dd, dd_pct = drawdown_conf(rand_values * 1000, rand_values, n, n_boot)
    assert len(dd) == 4
    assert len(dd_pct) == 4

@pytest.mark.parametrize('n, n_boot, expected_msg', [(0, 100, 'Bootstrap sample size must be greater than 0.'), (-1, 100, 'Bootstrap sample size must be greater than 0.'), (10, 0, 'Number of boostrap samples must be greater than 0.'), (10, -1, 'Number of boostrap samples must be greater than 0.')])
def test_drawdown_conf_when_invalid_params_then_error(n, n_boot, expected_msg):
    values = np.random.rand(100)
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        drawdown_conf(values, values, n, n_boot)

def test_drawdown_conf_when_length_mismatch_then_error():
    with pytest.raises(ValueError, match=re.escape('Param changes length does not match returns length.')):
        drawdown_conf(np.random.rand(100), np.random.rand(101), 10, 100)

@pytest.mark.parametrize('values, expected_pf', [([0.1, -0.2, 0.3, 0, -0.4, 0.5], 1.499999), ([1, 1, 1, 1], 40000000001), ([1], 10000000001), ([-1], 0), ([0, 0, 0, 0], 0), ([], 0)])
def test_profit_factor(values, expected_pf):
    pf = profit_factor(np.array(values))
    assert truncate(pf, 6) == truncate(expected_pf, 6)

@pytest.mark.parametrize('values, obs, expected_sharpe', [([0.1, -0.2, 0.3, 0, -0.4, 0.5], None, 0.167443), ([0.1, -0.2, 0.3, 0, -0.4, 0.5], 252, 0.16744367165578425 * np.sqrt(252)), ([1, 1, 1, 1], None, 0), ([1], None, 0), ([], None, 0)])
def test_sharpe_ratio(values, obs, expected_sharpe):
    sharpe = sharpe_ratio(np.array(values), obs)
    assert truncate(sharpe, 6) == truncate(expected_sharpe, 6)

@pytest.mark.parametrize('values, obs, expected_sortino', [([0.1, -0.2, 0.3, 0, -0.4, 0.5], None, 0.499999), ([0.1, -0.2, 0.3, 0, -0.4, 0.5], 252, 0.4999999999999999 * np.sqrt(252)), ([1, 1, 1, 1], None, 0), ([1], None, 0), ([], None, 0)])
def test_sortino_ratio(values, obs, expected_sortino):
    sortino = sortino_ratio(np.array(values), obs)
    assert truncate(sortino, 6) == truncate(expected_sortino, 6)

@pytest.mark.parametrize('values, expected_dd', [([0.1, 0.15, -0.05, 0.1, -0.25, -0.15, 0], -0.4), ([0.1, -0.4], -0.4), ([-0.1], -0.1), ([1, 1, 1, 1], 0), ([1], 0), ([], 0)])
def test_max_drawdown(values, expected_dd):
    changes = np.array(values)
    assert max_drawdown(changes) == expected_dd

@pytest.mark.parametrize('values, bars_per_year, expected_calmar', [([0.1, 0.15, -0.05, 0.1, -0.25, -0.15, 0], 252, -9), ([0.1, -0.4], 252, -94.5), ([1, 1, 1, 1], 252, 0), ([1], 252, 0), ([], 252, 0)])
def test_calmar_ratio(values, bars_per_year, expected_calmar):
    calmar = calmar_ratio(np.array(values), bars_per_year)
    assert truncate(calmar, 6) == expected_calmar

@pytest.mark.parametrize('values, expected_dd, expected_index', [([0, 0.1, 0.15, -0.05, 0.1, -0.25, -0.15, 0], -36.25, 6), ([0, -0.2], -20, 1), ([-0.1], -10, 0), ([0, 0, 0, 0], 0, None), ([0], 0, None), ([], 0, None)])
def test_max_drawdown_percent(values, expected_dd, expected_index):
    returns = np.array(values)
    dd, index = max_drawdown_percent(returns)
    assert round(dd, 2) == expected_dd
    if expected_index is None:
        assert index is None
    else:
        assert index == expected_index

@pytest.mark.parametrize('values, expected_iqr', [([1, 3, 5, 7, 8, 10, 11, 13], 6.5), ([1], 0), ([1, 2], 0), ([1, 1, 1, 1, 1], 0), ([], 0)])
def test_iqr(values, expected_iqr):
    assert iqr(np.array(values)) == expected_iqr

@pytest.mark.parametrize('values, expected_entropy', [([0.1, 0.2, 0.3, -0.2, 0.11, -0.3, -0.4, 0, 0.1, 0.2, 0.2], 0.782775), ([1, 1, 1, 1], 0), ([1], 0), ([], 0)])
def test_relative_entropy(values, expected_entropy):
    entropy = relative_entropy(np.array(values))
    assert truncate(entropy, 6) == expected_entropy

@pytest.mark.parametrize('values, period, expected_ui', [([100, 101, 102, 100, 99, 103, 103, 102], 2, 0.909259), ([100, 101, 102, 100, 99, 103, 103, 102], 1, 0), ([0, 0, 0, 0, 0], 2, 0), ([1, 1, 1, 1, 1], 2, 0), ([100], 14, 0), ([100], 1, 0), ([], 2, 0)])
def test_ulcer_index(values, period, expected_ui):
    assert truncate(ulcer_index(np.array(values), period), 6) == expected_ui

@pytest.mark.parametrize('values, period', [([100, 101, 102], 0), ([100, 101, 102], -1)])
def test_ulcer_index_when_invalid_period_then_error(values, period):
    with pytest.raises(AssertionError, match=re.escape('n needs to be >= 1.')):
        ulcer_index(np.array(values), period)

@pytest.mark.parametrize('values, period, ui, expected_upi', [([100, 101, 102, 100, 99, 103, 103, 102], 2, None, 0.329757), ([100, 101, 102, 100, 99, 103, 103, 102], 2, 0, 0), ([100, 101, 102, 100, 99, 103, 103, 102], 2, 1, 0.299834), ([100, 101, 102, 100, 99, 103, 103, 102], 1, None, 0), ([0, 0, 0, 0, 0], 2, None, 0), ([1, 1, 1, 1, 1], 2, None, 0), ([100], 14, None, 0), ([100], 1, None, 0), ([], 2, None, 0), ([], 14, None, 0), ([], 14, 0, 0), ([], 14, 1.5, 0), ([100], 14, None, 0), ([100], 14, 0, 0), ([100], 14, 1.5, 0), ([100], 1, None, 0), ([100, 101], 14, None, 0), ([100, 101], 14, 0, 0), ([100, 101, 102], 2, 0, 0)])
def test_upi(values, period, ui, expected_upi):
    upi_ = upi(np.array(values), period=period, ui=ui)
    assert truncate(upi_, 6) == expected_upi

@pytest.mark.parametrize('values, period', [([100, 101, 102], 0), ([100, 101, 102], -1)])
def test_upi_when_invalid_period_then_error(values, period):
    with pytest.raises(AssertionError, match=re.escape('n needs to be >= 1.')):
        upi(np.array(values), period)

@pytest.mark.parametrize('values, expected_win_rate, expected_loss_rate', [([0.1, 0.2, 0.3, -0.2, 0.11, -0.3, -0.4, 0, 0.1, 0.2, 0.2], 70, 30), ([0.1], 100, 0), ([-0.1], 0, 100), ([0, 0, 0, 0, 0], 0, 0), ([], 0, 0)])
def test_win_loss_rate(values, expected_win_rate, expected_loss_rate):
    pnls = np.array(values)
    win_rate, loss_rate = win_loss_rate(pnls)
    assert win_rate == expected_win_rate
    assert loss_rate == expected_loss_rate

@pytest.mark.parametrize('values, expected_winning_trades, expected_losing_trades', [([0.1, 0.2, 0.3, -0.2, 0.11, -0.3, -0.4, 0, 0.1, 0.2, 0.2], 7, 3), ([0.1], 1, 0), ([-0.1], 0, 1), ([0, 0, 0, 0, 0], 0, 0), ([], 0, 0)])
def test_winning_losing_trades(values, expected_winning_trades, expected_losing_trades):
    pnls = np.array(values)
    winning_trades, losing_trades = winning_losing_trades(pnls)
    assert winning_trades == expected_winning_trades
    assert losing_trades == expected_losing_trades

@pytest.mark.parametrize('values, expected_profit, expected_loss', [([0.1, -0.2, 0.3, 0, -0.4, 0.5], 0.9, -0.6), ([0, 0, 0, 0, 0], 0, 0), ([0.1], 0.1, 0), ([-0.1], 0, -0.1), ([], 0, 0)])
def test_total_profit_loss(values, expected_profit, expected_loss):
    pnls = np.array(values)
    profit, loss = total_profit_loss(pnls)
    assert profit == expected_profit
    assert round(loss, 2) == expected_loss

@pytest.mark.parametrize('values, expected_profit, expected_loss', [([0.1, -0.2, 0.3, 0, -0.4, 0.5], 0.3, -0.3), ([1, 1, 1, 1, 1], 1, 0), ([-1, -1, -1, -1, -1], 0, -1), ([0, 0, 0, 0, 0], 0, 0), ([], 0, 0)])
def test_avg_profit_loss(values, expected_profit, expected_loss):
    pnls = np.array(values)
    profit, loss = avg_profit_loss(pnls)
    assert profit == expected_profit
    assert round(loss, 2) == expected_loss

@pytest.mark.parametrize('values, expected_win, expected_loss', [([0.1, 0.2, 0.3, -0.2, 0.11, -0.3, -0.4, 0, 0.1, 0.2, 0.2], 0.3, -0.4), ([1, 1, 1, 1, 1], 1, 0), ([-1, -1, -1, -1, -1], 0, -1), ([0, 0, 0, 0, 0], 0, 0), ([], 0, 0)])
def test_largest_win_loss(values, expected_win, expected_loss):
    pnls = np.array(values)
    win, loss = largest_win_loss(pnls)
    assert win == expected_win
    assert loss == expected_loss

@pytest.mark.parametrize('values, expected_wins, expected_losses', [([0.1, 0.2, 0.3, -0.2, 0.11, -0.3, -0.4, 0, 0.1, 0.2, 0.2], 3, 2), ([1, 1, 1, 1, 1], 5, 0), ([-1, -1, -1, -1, -1], 0, 5), ([0, 0, 0, 0, 0], 0, 0), ([], 0, 0)])
def test_max_wins_losses(values, expected_wins, expected_losses):
    pnls = np.array(values)
    wins, losses = max_wins_losses(pnls)
    assert wins == expected_wins
    assert losses == expected_losses

@pytest.mark.parametrize('values, expected_r2', [([1, 3, 5, 7, 8, 10, 11, 13], 0.992907), ([1], 0), ([-1], 0), ([1, 1, 1, 1, 1], 0), ([0, 0, 0, 0, 0], 0), ([], 0)])
def test_r_squared(values, expected_r2):
    r2 = r_squared(np.array(values))
    assert truncate(r2, 6) == expected_r2

@pytest.mark.parametrize('initial_value, pnl, expected_return', [(100, 10, 10), (0, 10, 0)])
def test_total_return_percent(initial_value, pnl, expected_return):
    return_pct = total_return_percent(initial_value, pnl)
    assert truncate(return_pct, 2) == expected_return

@pytest.mark.parametrize('initial_value, pnl, bars_per_year, total_bars, expected_return', [(100, 10, 252, 756, 3.22), (0, 10, 252, 756, 0), (100, 10, 252, 0, 0)])
def test_annual_total_return_percent(initial_value, pnl, bars_per_year, total_bars, expected_return):
    return_pct = annual_total_return_percent(initial_value, pnl, bars_per_year, total_bars)
    assert truncate(return_pct, 2) == expected_return

@pytest.mark.usefixtures('setup_teardown')
@pytest.mark.parametrize('clear_fn, expected_msg', [(clear_data_source_cache, 'Data source cache needs to be enabled before clearing.'), (clear_indicator_cache, 'Indicator cache needs to be enabled before clearing.'), (clear_model_cache, 'Model cache needs to be enabled before clearing.')])
def test_clear_cache_when_not_enabled_then_error(clear_fn, expected_msg):
    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        clear_fn()

@pytest.mark.usefixtures('setup_teardown')
@pytest.mark.parametrize('enable_fn', [enable_data_source_cache, enable_indicator_cache, enable_model_cache, enable_caches])
def test_enable_cache_when_namespace_empty_then_error(enable_fn):
    with pytest.raises(ValueError, match=re.escape('Cache namespace cannot be empty.')):
        enable_fn('')

class TestModelSource:

    @pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
    def test_model_prepare_input_fn(self, data_source_df, clazz):
        prepare_fn = Mock()
        source = clazz('model_source', lambda x: x, [], prepare_fn, None, {})
        source.prepare_input_data(data_source_df)
        prepare_fn.assert_called_once_with(data_source_df)

    @pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
    def test_model_prepare_input_fn_when_empty_data(self, clazz):
        source = clazz('model_source', lambda x: x, [], None, None, {})
        df = source.prepare_input_data(pd.DataFrame())
        assert df.empty

    @pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
    def test_model_prepare_input_fn_when_fn_none(self, ind_df, ind_names, clazz):
        source = clazz('model_source', lambda x: x, ind_names, None, None, {})
        df = source.prepare_input_data(ind_df)
        assert df.equals(ind_df)

    @pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
    def test_model_prepare_input_fn_when_indicators_not_found_then_error(self, ind_df, clazz):
        source = clazz('model_source', lambda x: x, ['foo'], None, None, {})
        with pytest.raises(ValueError, match=re.escape("Indicator 'foo' not found in DataFrame.")):
            source.prepare_input_data(ind_df)

    def test_model_loader_call_with_kwargs(self, start_date, end_date):
        load_fn = Mock()
        kwargs = {'a': 1, 'b': 2}
        ModelLoader('loader', load_fn, [], None, None, kwargs)('SPY', start_date, end_date)
        load_fn.assert_called_once_with('SPY', start_date, end_date, **kwargs)

    def test_model_trainer_call_with_kwargs(self, train_data, test_data):
        train_fn = Mock()
        kwargs = {'a': 1, 'b': 2}
        ModelTrainer('trainer', train_fn, [], None, None, kwargs)('SPY', train_data, test_data)
        train_fn.assert_called_once_with('SPY', train_data, test_data, **kwargs)

    def test_model_trainer_repr(self):
        trainer = ModelTrainer('trainer', lambda x: x, [], None, None, {'a': 1})
        assert repr(trainer) == "ModelTrainer('trainer', {'a': 1})"

    def test_model_loader_repr(self):
        trainer = ModelLoader('loader', lambda x: x, [], None, None, {'a': 1})
        assert repr(trainer) == "ModelLoader('loader', {'a': 1})"

@pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
def test_model_prepare_input_fn(self, data_source_df, clazz):
    prepare_fn = Mock()
    source = clazz('model_source', lambda x: x, [], prepare_fn, None, {})
    source.prepare_input_data(data_source_df)
    prepare_fn.assert_called_once_with(data_source_df)

@pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
def test_model_prepare_input_fn_when_empty_data(self, clazz):
    source = clazz('model_source', lambda x: x, [], None, None, {})
    df = source.prepare_input_data(pd.DataFrame())
    assert df.empty

@pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
def test_model_prepare_input_fn_when_fn_none(self, ind_df, ind_names, clazz):
    source = clazz('model_source', lambda x: x, ind_names, None, None, {})
    df = source.prepare_input_data(ind_df)
    assert df.equals(ind_df)

@pytest.mark.parametrize('clazz', [ModelLoader, ModelTrainer])
def test_model_prepare_input_fn_when_indicators_not_found_then_error(self, ind_df, clazz):
    source = clazz('model_source', lambda x: x, ['foo'], None, None, {})
    with pytest.raises(ValueError, match=re.escape("Indicator 'foo' not found in DataFrame.")):
        source.prepare_input_data(ind_df)

@pytest.mark.parametrize('shares, fill_price, limit_price, expected_msg', [(-1, FILL_PRICE_1, LIMIT_PRICE_1, 'Shares cannot be negative: -1'), (SHARES_1, -1, LIMIT_PRICE_1, 'Fill price must be > 0: -1'), (SHARES_1, FILL_PRICE_1, -1, 'Limit price must be > 0: -1')])
def test_buy_when_invalid_input_then_error(shares, fill_price, limit_price, expected_msg):
    portfolio = Portfolio(CASH)
    with pytest.raises(ValueError, match=expected_msg):
        portfolio.buy(DATE_1, SYMBOL_1, shares, fill_price, limit_price)

@pytest.mark.parametrize('shares, fill_price, limit_price, expected_msg', [(-1, FILL_PRICE_3, LIMIT_PRICE_3, 'Shares cannot be negative: -1'), (SHARES_1, -1, LIMIT_PRICE_3, 'Fill price must be > 0: -1'), (SHARES_1, FILL_PRICE_3, -1, 'Limit price must be > 0: -1')])
def test_sell_when_invalid_input_then_error(shares, fill_price, limit_price, expected_msg):
    portfolio = Portfolio(CASH)
    with pytest.raises(ValueError, match=expected_msg):
        portfolio.sell(DATE_1, SYMBOL_1, shares, fill_price, limit_price)

