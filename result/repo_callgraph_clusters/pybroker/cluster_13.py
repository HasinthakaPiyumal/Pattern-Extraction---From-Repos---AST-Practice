# Cluster 13

class BacktestMixin:
    """Mixin implementing backtesting functionality."""

    def backtest_executions(self, config: StrategyConfig, executions: set[Execution], before_exec_fn: Optional[Callable[[Mapping[str, ExecContext]], None]], after_exec_fn: Optional[Callable[[Mapping[str, ExecContext]], None]], sessions: Mapping[str, MutableMapping], models: Mapping[ModelSymbol, TrainedModel], indicator_data: Mapping[IndicatorSymbol, pd.Series], test_data: pd.DataFrame, portfolio: Portfolio, pos_size_handler: Optional[Callable[[PosSizeContext], None]], exit_dates: Mapping[str, np.datetime64], train_only: bool=False, slippage_model: Optional[SlippageModel]=None, enable_fractional_shares: bool=False, round_fill_price: bool=True, warmup: Optional[int]=None) -> dict[str, pd.DataFrame]:
        """Backtests a ``set`` of :class:`.Execution`\\ s that implement
        trading logic.

        Args:
            config: :class:`pybroker.config.StrategyConfig`.
            executions: :class:`.Execution`\\ s to run.
            sessions: :class:`Mapping` of symbols to :class:`Mapping` of custom
                data that persists for every bar during the
                :class:`.Execution`.
            models: :class:`Mapping` of :class:`pybroker.common.ModelSymbol`
                pairs to :class:`pybroker.common.TrainedModel`\\ s.
            indicator_data: :class:`Mapping` of
                :class:`pybroker.common.IndicatorSymbol` pairs to
                :class:`pandas.Series` of :class:`pybroker.indicator.Indicator`
                values.
            test_data: :class:`pandas.DataFrame` of test data.
            portfolio: :class:`pybroker.portfolio.Portfolio`.
            pos_size_handler: :class:`Callable` that sets position sizes when
                placing orders for buy and sell signals.
            exit_dates: :class:`Mapping` of symbols to exit dates.
            train_only: Whether the backtest is run with trading rules or
                only trains models.
            enable_fractional_shares: Whether to enable trading fractional
                shares.
            round_fill_price: Whether to round fill prices to the nearest cent.
            warmup: Number of bars that need to pass before running the
                executions.

        Returns:
            Dictionary of :class:`pandas.DataFrame`\\ s containing bar data,
            indicator data, and model predictions for each symbol when
            :attr:`pybroker.config.StrategyConfig.return_signals` is ``True``.
        """
        test_dates = get_unique_sorted_dates(test_data[DataCol.DATE.value])
        test_syms = sorted(test_data[DataCol.SYMBOL.value].unique())
        test_data = test_data.reset_index(drop=True).set_index([DataCol.SYMBOL.value, DataCol.DATE.value]).sort_index()
        col_scope = ColumnScope(test_data)
        ind_scope = IndicatorScope(indicator_data, test_dates)
        input_scope = ModelInputScope(col_scope, ind_scope, models)
        pred_scope = PredictionScope(models, input_scope)
        if train_only:
            if config.return_signals:
                return get_signals(test_syms, col_scope, ind_scope, pred_scope)
            return {}
        sym_end_index: dict[str, int] = defaultdict(int)
        price_scope = PriceScope(col_scope, sym_end_index, round_fill_price)
        pending_order_scope = PendingOrderScope()
        exec_ctxs: dict[str, ExecContext] = {}
        exec_fns: dict[str, Callable[[ExecContext], None]] = {}
        for sym in test_syms:
            for exec in executions:
                if sym not in exec.symbols:
                    continue
                exec_ctxs[sym] = ExecContext(symbol=sym, config=config, portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=models, sym_end_index=sym_end_index, session=sessions[sym])
                if exec.fn is not None:
                    exec_fns[sym] = exec.fn
        sym_exec_dates = {sym: frozenset(test_data.loc[pd.IndexSlice[sym, :]].index.values) for sym in exec_ctxs.keys()}
        cover_sched: dict[np.datetime64, list[ExecResult]] = defaultdict(list)
        buy_sched: dict[np.datetime64, list[ExecResult]] = defaultdict(list)
        sell_sched: dict[np.datetime64, list[ExecResult]] = defaultdict(list)
        if pos_size_handler is not None:
            pos_ctx = PosSizeContext(config=config, portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=models, sessions=sessions, sym_end_index=sym_end_index)
        logger = StaticScope.instance().logger
        logger.backtest_executions_start(test_dates)
        cover_results: deque[ExecResult] = deque()
        buy_results: deque[ExecResult] = deque()
        sell_results: deque[ExecResult] = deque()
        exit_ctxs: deque[ExecContext] = deque()
        active_ctxs: dict[str, ExecContext] = {}
        for i, date in enumerate(test_dates):
            active_ctxs.clear()
            for sym, ctx in exec_ctxs.items():
                if date not in sym_exec_dates[sym]:
                    continue
                sym_end_index[sym] += 1
                if warmup and sym_end_index[sym] <= warmup:
                    continue
                active_ctxs[sym] = ctx
                set_exec_ctx_data(ctx, date)
                if exit_dates and sym in exit_dates and (date == exit_dates[sym]):
                    exit_ctxs.append(ctx)
            is_cover_sched = date in cover_sched
            is_buy_sched = date in buy_sched
            is_sell_sched = date in sell_sched
            if config.max_long_positions is not None or pos_size_handler is not None:
                if is_cover_sched:
                    cover_sched[date].sort(key=_sort_by_score, reverse=True)
                elif is_buy_sched:
                    buy_sched[date].sort(key=_sort_by_score, reverse=True)
            if is_sell_sched and (config.max_short_positions is not None or pos_size_handler is not None):
                sell_sched[date].sort(key=_sort_by_score, reverse=True)
            if pos_size_handler is not None and (is_cover_sched or is_buy_sched or is_sell_sched):
                pos_size_buy_results = None
                if is_cover_sched:
                    pos_size_buy_results = cover_sched[date]
                elif is_buy_sched:
                    pos_size_buy_results = buy_sched[date]
                self._set_pos_sizes(pos_size_handler=pos_size_handler, pos_ctx=pos_ctx, buy_results=pos_size_buy_results, sell_results=sell_sched[date] if is_sell_sched else None)
            portfolio.check_stops(date, price_scope)
            if is_cover_sched:
                self._place_buy_orders(date=date, price_scope=price_scope, pending_order_scope=pending_order_scope, buy_sched=cover_sched, portfolio=portfolio, enable_fractional_shares=enable_fractional_shares)
            if is_sell_sched:
                self._place_sell_orders(date=date, price_scope=price_scope, pending_order_scope=pending_order_scope, sell_sched=sell_sched, portfolio=portfolio, enable_fractional_shares=enable_fractional_shares)
            if is_buy_sched:
                self._place_buy_orders(date=date, price_scope=price_scope, pending_order_scope=pending_order_scope, buy_sched=buy_sched, portfolio=portfolio, enable_fractional_shares=enable_fractional_shares)
            portfolio.capture_bar(date, test_data)
            if before_exec_fn is not None and active_ctxs:
                before_exec_fn(active_ctxs)
            for sym, ctx in active_ctxs.items():
                if sym in exec_fns:
                    exec_fns[sym](ctx)
            if after_exec_fn is not None and active_ctxs:
                after_exec_fn(active_ctxs)
            for ctx in active_ctxs.values():
                if slippage_model and (not ctx._exiting_pos) and (ctx.buy_shares or ctx.sell_shares):
                    self._apply_slippage(slippage_model, ctx)
                result = ctx.to_result()
                if result is None:
                    continue
                if result.buy_shares is not None:
                    if result.cover:
                        cover_results.append(result)
                    else:
                        buy_results.append(result)
                if result.sell_shares is not None:
                    sell_results.append(result)
            while cover_results:
                self._schedule_order(result=cover_results.popleft(), created=date, sym_end_index=sym_end_index, delay=config.buy_delay, sched=cover_sched, col_scope=col_scope, pending_order_scope=pending_order_scope)
            while buy_results:
                self._schedule_order(result=buy_results.popleft(), created=date, sym_end_index=sym_end_index, delay=config.buy_delay, sched=buy_sched, col_scope=col_scope, pending_order_scope=pending_order_scope)
            while sell_results:
                self._schedule_order(result=sell_results.popleft(), created=date, sym_end_index=sym_end_index, delay=config.sell_delay, sched=sell_sched, col_scope=col_scope, pending_order_scope=pending_order_scope)
            while exit_ctxs:
                self._exit_position(portfolio=portfolio, date=date, ctx=exit_ctxs.popleft(), exit_cover_fill_price=config.exit_cover_fill_price, exit_sell_fill_price=config.exit_sell_fill_price, price_scope=price_scope)
            portfolio.incr_bars()
            if i % 10 == 0 or i == len(test_dates) - 1:
                logger.backtest_executions_loading(i + 1)
        return get_signals(test_syms, col_scope, ind_scope, pred_scope) if config.return_signals else {}

    def _apply_slippage(self, slippage_model: SlippageModel, ctx: ExecContext):
        buy_shares = to_decimal(ctx.buy_shares) if ctx.buy_shares else None
        sell_shares = to_decimal(ctx.sell_shares) if ctx.sell_shares else None
        slippage_model.apply_slippage(ctx, buy_shares=buy_shares, sell_shares=sell_shares)

    def _exit_position(self, portfolio: Portfolio, date: np.datetime64, ctx: ExecContext, exit_cover_fill_price: Union[PriceType, Callable[[str, BarData], Union[int, float, Decimal]]], exit_sell_fill_price: Union[PriceType, Callable[[str, BarData], Union[int, float, Decimal]]], price_scope: PriceScope):
        buy_fill_price = price_scope.fetch(ctx.symbol, exit_cover_fill_price)
        sell_fill_price = price_scope.fetch(ctx.symbol, exit_sell_fill_price)
        portfolio.exit_position(date, ctx.symbol, buy_fill_price=buy_fill_price, sell_fill_price=sell_fill_price)

    def _set_pos_sizes(self, pos_size_handler: Callable[[PosSizeContext], None], pos_ctx: PosSizeContext, buy_results: Optional[list[ExecResult]], sell_results: Optional[list[ExecResult]]):
        set_pos_size_ctx_data(ctx=pos_ctx, buy_results=buy_results, sell_results=sell_results)
        pos_size_handler(pos_ctx)
        for id, shares in pos_ctx._signal_shares.items():
            if id < 0:
                raise ValueError(f'Invalid ExecSignal id: {id}')
            if buy_results is not None and sell_results is not None:
                if id >= len(buy_results) + len(sell_results):
                    raise ValueError(f'Invalid ExecSignal id: {id}')
                if id < len(buy_results):
                    buy_results[id].buy_shares = to_decimal(shares)
                else:
                    sell_results[id - len(buy_results)].sell_shares = to_decimal(shares)
            elif buy_results is not None:
                if id >= len(buy_results):
                    raise ValueError(f'Invalid ExecSignal id: {id}')
                buy_results[id].buy_shares = to_decimal(shares)
            elif sell_results is not None:
                if id >= len(sell_results):
                    raise ValueError(f'Invalid ExecSignal id: {id}')
                sell_results[id].sell_shares = to_decimal(shares)
            else:
                raise ValueError('buy_results and sell_results cannot both be None.')

    def _schedule_order(self, result: ExecResult, created: np.datetime64, sym_end_index: Mapping[str, int], delay: int, sched: Mapping[np.datetime64, list[ExecResult]], col_scope: ColumnScope, pending_order_scope: PendingOrderScope):
        date_loc = sym_end_index[result.symbol] - 1
        dates = col_scope.fetch(result.symbol, DataCol.DATE.value)
        if dates is None:
            raise ValueError('Dates not found.')
        logger = StaticScope.instance().logger
        if date_loc + delay < len(dates):
            date = dates[date_loc + delay]
            order_type: Literal['buy', 'sell']
            if result.buy_shares is not None:
                order_type = 'buy'
                shares = result.buy_shares
                limit_price = result.buy_limit_price
                fill_price = result.buy_fill_price
            elif result.sell_shares is not None:
                order_type = 'sell'
                shares = result.sell_shares
                limit_price = result.sell_limit_price
                fill_price = result.sell_fill_price
            else:
                raise ValueError('buy_shares or sell_shares needs to be set.')
            result.pending_order_id = pending_order_scope.add(type=order_type, symbol=result.symbol, created=created, exec_date=date, shares=shares, limit_price=limit_price, fill_price=fill_price)
            sched[date].append(result)
            logger.debug_schedule_order(date, result)
        else:
            logger.debug_unscheduled_order(result)

    def _place_buy_orders(self, date: np.datetime64, price_scope: PriceScope, pending_order_scope: PendingOrderScope, buy_sched: dict[np.datetime64, list[ExecResult]], portfolio: Portfolio, enable_fractional_shares: bool):
        buy_results = buy_sched[date]
        for result in buy_results:
            if result.buy_shares is None:
                continue
            if result.pending_order_id is None or not pending_order_scope.contains(result.pending_order_id):
                continue
            pending_order_scope.remove(result.pending_order_id)
            buy_shares = self._get_shares(result.buy_shares, enable_fractional_shares)
            fill_price = price_scope.fetch(result.symbol, result.buy_fill_price)
            order = portfolio.buy(date=date, symbol=result.symbol, shares=buy_shares, fill_price=fill_price, limit_price=result.buy_limit_price, stops=result.long_stops)
            logger = StaticScope.instance().logger
            if order is None:
                logger.debug_unfilled_buy_order(date=date, symbol=result.symbol, shares=buy_shares, fill_price=fill_price, limit_price=result.buy_limit_price)
            else:
                logger.debug_filled_buy_order(date=date, symbol=result.symbol, shares=buy_shares, fill_price=fill_price, limit_price=result.buy_limit_price)
        del buy_sched[date]

    def _place_sell_orders(self, date: np.datetime64, price_scope: PriceScope, pending_order_scope: PendingOrderScope, sell_sched: dict[np.datetime64, list[ExecResult]], portfolio: Portfolio, enable_fractional_shares: bool):
        sell_results = sell_sched[date]
        for result in sell_results:
            if result.sell_shares is None:
                continue
            if result.pending_order_id is None or not pending_order_scope.contains(result.pending_order_id):
                continue
            pending_order_scope.remove(result.pending_order_id)
            sell_shares = self._get_shares(result.sell_shares, enable_fractional_shares)
            fill_price = price_scope.fetch(result.symbol, result.sell_fill_price)
            order = portfolio.sell(date=date, symbol=result.symbol, shares=sell_shares, fill_price=fill_price, limit_price=result.sell_limit_price, stops=result.short_stops)
            logger = StaticScope.instance().logger
            if order is None:
                logger.debug_unfilled_sell_order(date=date, symbol=result.symbol, shares=sell_shares, fill_price=fill_price, limit_price=result.sell_limit_price)
            else:
                logger.debug_filled_sell_order(date=date, symbol=result.symbol, shares=sell_shares, fill_price=fill_price, limit_price=result.sell_limit_price)
        del sell_sched[date]

    def _get_shares(self, shares: Union[int, float, Decimal], enable_fractional_shares: bool) -> Decimal:
        if enable_fractional_shares:
            return to_decimal(shares)
        else:
            return to_decimal(int(shares))

def _apply_slippage(self, slippage_model: SlippageModel, ctx: ExecContext):
    buy_shares = to_decimal(ctx.buy_shares) if ctx.buy_shares else None
    sell_shares = to_decimal(ctx.sell_shares) if ctx.sell_shares else None
    slippage_model.apply_slippage(ctx, buy_shares=buy_shares, sell_shares=sell_shares)

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

class DataSourceCacheMixin:
    """Mixin that implements fetching and storing cached :class:`.DataSource`
    data.
    """

    def get_cached(self, symbols: Iterable[str], timeframe: str, start_date: Union[str, datetime, pd.Timestamp, np.datetime64], end_date: Union[str, datetime, pd.Timestamp, np.datetime64], adjust: Optional[Any]) -> tuple[pd.DataFrame, Iterable[str]]:
        """Retrieves cached data from disk when caching is enabled with
        :meth:`pybroker.cache.enable_data_source_cache`.

        Args:
            symbols: :class:`Iterable` of symbols for fetching cached data.
            timeframe: Formatted string that specifies the timeframe
                resolution of the cached data. The timeframe string supports
                the following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks


                An example timeframe string is ``1h 30m``.
            start_date: Starting date of the cached data (inclusive).
            end_date: Ending date of the cached data (inclusive).
            adjust: The type of adjustment to make.

        Returns:
            ``tuple[pandas.DataFrame, Iterable[str]]`` containing a
            :class:`pandas.DataFrame` with the cached data, and an
            ``Iterable[str]`` of symbols for which no cached data was
            found.
        """
        df = pd.DataFrame()
        scope = StaticScope.instance()
        cache = scope.data_source_cache
        if cache is None:
            return (df, symbols)
        start_date = to_datetime(start_date)
        end_date = to_datetime(end_date)
        tf_seconds = to_seconds(timeframe)
        uncached_syms = []
        cached_syms = []
        for sym in symbols:
            cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=tf_seconds, start_date=start_date, end_date=end_date, adjust=adjust)
            cached = cache.get(repr(cache_key))
            scope.logger.debug_get_data_source_cache(cache_key)
            if cached is None:
                uncached_syms.append(sym)
            else:
                cached_syms.append(sym)
                df = pd.concat([df, cached])
        if not uncached_syms:
            scope.logger.loaded_bar_data()
        scope.logger.info_loaded_bar_data(symbols=cached_syms, timeframe=timeframe, start_date=start_date, end_date=end_date)
        return (df, uncached_syms)

    def set_cached(self, timeframe: str, start_date: Union[str, datetime, pd.Timestamp, np.datetime64], end_date: Union[str, datetime, pd.Timestamp, np.datetime64], adjust: Optional[Any], data: pd.DataFrame):
        """Stores data to disk cache when caching is enabled with
        :meth:`pybroker.cache.enable_data_source_cache`.

        Args:
            timeframe: Formatted string that specifies the timeframe
                resolution of the data to cache. The timeframe string supports
                the following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks

                An example timeframe string would be ``1h 30m``.
            start_date: Starting date of the data to cache (inclusive).
            end_date: Ending date of the data to cache (inclusive).
            adjust: The type of adjustment to make.
            data: :class:`pandas.DataFrame` containing the data to cache.
        """
        if data.empty:
            return
        scope = StaticScope.instance()
        cache = scope.data_source_cache
        if cache is None:
            return
        start_date = to_datetime(start_date)
        end_date = to_datetime(end_date)
        tf_seconds = to_seconds(timeframe)
        for sym in data[DataCol.SYMBOL.value].unique():
            df = data[data[DataCol.SYMBOL.value] == sym]
            cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=tf_seconds, start_date=start_date, end_date=end_date, adjust=adjust)
            cache.set(repr(cache_key), df)
            scope.logger.debug_set_data_source_cache(cache_key)

def get_cached(self, symbols: Iterable[str], timeframe: str, start_date: Union[str, datetime, pd.Timestamp, np.datetime64], end_date: Union[str, datetime, pd.Timestamp, np.datetime64], adjust: Optional[Any]) -> tuple[pd.DataFrame, Iterable[str]]:
    """Retrieves cached data from disk when caching is enabled with
        :meth:`pybroker.cache.enable_data_source_cache`.

        Args:
            symbols: :class:`Iterable` of symbols for fetching cached data.
            timeframe: Formatted string that specifies the timeframe
                resolution of the cached data. The timeframe string supports
                the following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks


                An example timeframe string is ``1h 30m``.
            start_date: Starting date of the cached data (inclusive).
            end_date: Ending date of the cached data (inclusive).
            adjust: The type of adjustment to make.

        Returns:
            ``tuple[pandas.DataFrame, Iterable[str]]`` containing a
            :class:`pandas.DataFrame` with the cached data, and an
            ``Iterable[str]`` of symbols for which no cached data was
            found.
        """
    df = pd.DataFrame()
    scope = StaticScope.instance()
    cache = scope.data_source_cache
    if cache is None:
        return (df, symbols)
    start_date = to_datetime(start_date)
    end_date = to_datetime(end_date)
    tf_seconds = to_seconds(timeframe)
    uncached_syms = []
    cached_syms = []
    for sym in symbols:
        cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=tf_seconds, start_date=start_date, end_date=end_date, adjust=adjust)
        cached = cache.get(repr(cache_key))
        scope.logger.debug_get_data_source_cache(cache_key)
        if cached is None:
            uncached_syms.append(sym)
        else:
            cached_syms.append(sym)
            df = pd.concat([df, cached])
    if not uncached_syms:
        scope.logger.loaded_bar_data()
    scope.logger.info_loaded_bar_data(symbols=cached_syms, timeframe=timeframe, start_date=start_date, end_date=end_date)
    return (df, uncached_syms)

def set_cached(self, timeframe: str, start_date: Union[str, datetime, pd.Timestamp, np.datetime64], end_date: Union[str, datetime, pd.Timestamp, np.datetime64], adjust: Optional[Any], data: pd.DataFrame):
    """Stores data to disk cache when caching is enabled with
        :meth:`pybroker.cache.enable_data_source_cache`.

        Args:
            timeframe: Formatted string that specifies the timeframe
                resolution of the data to cache. The timeframe string supports
                the following units:

                - ``"s"``/``"sec"``: seconds
                - ``"m"``/``"min"``: minutes
                - ``"h"``/``"hour"``: hours
                - ``"d"``/``"day"``: days
                - ``"w"``/``"week"``: weeks

                An example timeframe string would be ``1h 30m``.
            start_date: Starting date of the data to cache (inclusive).
            end_date: Ending date of the data to cache (inclusive).
            adjust: The type of adjustment to make.
            data: :class:`pandas.DataFrame` containing the data to cache.
        """
    if data.empty:
        return
    scope = StaticScope.instance()
    cache = scope.data_source_cache
    if cache is None:
        return
    start_date = to_datetime(start_date)
    end_date = to_datetime(end_date)
    tf_seconds = to_seconds(timeframe)
    for sym in data[DataCol.SYMBOL.value].unique():
        df = data[data[DataCol.SYMBOL.value] == sym]
        cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=tf_seconds, start_date=start_date, end_date=end_date, adjust=adjust)
        cache.set(repr(cache_key), df)
        scope.logger.debug_set_data_source_cache(cache_key)

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

def parse_timeframe(timeframe: str) -> list[tuple[int, str]]:
    """Parses timeframe string with the following units:

    - ``"s"``/``"sec"``: seconds
    - ``"m"``/``"min"``: minutes
    - ``"h"``/``"hour"``: hours
    - ``"d"``/``"day"``: days
    - ``"w"``/``"week"``: weeks

    An example timeframe string is ``1h 30m``.

    Returns:
        ``list`` of ``tuple[int, str]``, where each tuple contains an ``int``
        value and ``str`` unit of one of the following: ``sec``, ``min``,
        ``hour``, ``day``, ``week``.
    """
    parts = _tf_pattern.findall(timeframe)
    if not parts or len(parts) != len(timeframe.split()):
        raise ValueError('Invalid timeframe format.')
    result = []
    units = frozenset(_tf_abbr.values())
    seen_units = set()
    for part in parts:
        unit = part[1].lower()
        if unit in _tf_abbr:
            unit = _tf_abbr[unit]
        if unit not in units:
            raise ValueError('Invalid timeframe format.')
        if unit in seen_units:
            raise ValueError('Invalid timeframe format.')
        result.append((int(part[0]), unit))
        seen_units.add(unit)
    return result

def model(name: str, fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicators: Optional[Iterable[Indicator]]=None, input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]]=None, predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]]=None, pretrained: bool=False, **kwargs) -> ModelSource:
    """Creates a :class:`.ModelSource` instance and registers it globally with
    ``name``.

    Args:
        name: Name for referencing the model globally.
        fn: :class:`Callable` used to either train or load a model instance. If
            for training, then ``fn`` has signature ``Callable[[symbol: str,
            train_data: DataFrame, test_data: DataFrame, ...], DataFrame]``.
            If for loading, then ``fn`` has signature
            ``Callable[[symbol: str, train_start_date: datetime,
            train_end_date: datetime, ...], DataFrame]``. This is expected to
            return either a trained model instance, or a tuple containing a
            trained model instance and a :class:`Iterable` of column names to
            to be used as input for the model when making predictions.
        indicators: :class:`Iterable` of
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
        pretrained: If ``True``, then ``fn`` is used to load and return a
            pre-trained model. If ``False``, ``fn`` is used to train and return
            a new model. Defaults to ``False``.
        \\**kwargs: Additional arguments to pass to ``fn``.

    Returns:
        :class:`.ModelSource` instance.
    """
    scope = StaticScope.instance()
    indicator_names = tuple(sorted(set((ind.name for ind in indicators)))) if indicators is not None else tuple()
    if pretrained:
        loader = ModelLoader(name=name, load_fn=fn, indicator_names=indicator_names, input_data_fn=input_data_fn, predict_fn=predict_fn, kwargs=kwargs)
        scope.set_model_source(loader)
        return loader
    else:
        trainer = ModelTrainer(name=name, train_fn=fn, indicator_names=indicator_names, input_data_fn=input_data_fn, predict_fn=predict_fn, kwargs=kwargs)
        scope.set_model_source(trainer)
        return trainer

class ModelsMixin:
    """Mixin implementing model related functionality."""

    def train_models(self, model_syms: Iterable[ModelSymbol], train_data: pd.DataFrame, test_data: pd.DataFrame, indicator_data: Mapping[IndicatorSymbol, pd.Series], cache_date_fields: CacheDateFields) -> dict[ModelSymbol, TrainedModel]:
        """Trains models for the provided :class:`pybroker.common.ModelSymbol`
        pairs.

        Args:
            model_syms: ``Iterable`` of
                :class:`pybroker.common.ModelSymbol` pairs of models to train.
            train_data: :class:`pandas.DataFrame` of training data.
            test_data: :class:`pandas.DataFrame` of test data.
            indicator_data: ``Mapping`` of
                :class:`pybroker.common.IndicatorSymbol` pairs to
                ``pandas.Series`` of :class:`pybroker.indicator.Indicator`
                values.
            cache_date_fields: Date fields used to key cache data.

        Returns:
            ``dict`` mapping each :class:`pybroker.common.ModelSymbol` pair
            to a :class:`pybroker.common.TrainedModel`.
        """
        if train_data.empty or not model_syms:
            return {}
        scope = StaticScope.instance()
        train_dates = get_unique_sorted_dates(train_data[DataCol.DATE.value])
        test_dates = get_unique_sorted_dates(test_data[DataCol.DATE.value])
        scope.logger.train_split_start(train_dates)
        scope.logger.info_train_split_start(model_syms)
        models, uncached_model_syms = self._get_cached_models(model_syms, cache_date_fields)
        if not uncached_model_syms:
            scope.logger.loaded_models()
            scope.logger.info_loaded_models(model_syms)
            return models
        if models:
            scope.logger.info_loaded_models(models.keys())
        start_date = to_datetime(train_dates[0])
        end_date = to_datetime(train_dates[-1])
        for model_sym in uncached_model_syms:
            if model_sym in models:
                continue
            model_name, sym = model_sym
            source = scope.get_model_source(model_name)
            if isinstance(source, ModelTrainer):
                sym_train_data = self._slice_by_symbol(sym, train_data)
                sym_test_data = self._slice_by_symbol(sym, test_data)
                for ind_name in source.indicators:
                    ind_series = indicator_data[IndicatorSymbol(ind_name, sym)]
                    if not sym_train_data.empty:
                        sym_train_data[ind_name] = ind_series[ind_series.index.isin(train_dates)].values
                    if not sym_test_data.empty:
                        sym_test_data[ind_name] = ind_series[ind_series.index.isin(test_dates)].values
                scope.logger.info_train_model_start(model_sym)
                model_result = source(sym, sym_train_data, sym_test_data)
                scope.logger.info_train_model_completed(model_sym)
            elif isinstance(source, ModelLoader):
                model_result = source(sym, start_date, end_date)
                scope.logger.info_loaded_model(model_sym)
            else:
                raise TypeError(f'Invalid ModelSource type: {type(source)}')
            input_cols: Optional[tuple[str]] = None
            if isinstance(model_result, tuple):
                model = model_result[0]
                input_cols = tuple(model_result[1])
            else:
                model = model_result
            models[model_sym] = TrainedModel(name=model_name, instance=model, predict_fn=source._predict_fn, input_cols=input_cols)
            self._set_cached_model(model, input_cols, model_sym, cache_date_fields)
        scope.logger.train_split_completed()
        return models

    def _slice_by_symbol(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        return df.loc[df[DataCol.SYMBOL.value] == symbol].drop(columns=DataCol.SYMBOL.value).sort_values(DataCol.DATE.value)

    def _get_cached_models(self, model_syms: Iterable[ModelSymbol], cache_date_fields: CacheDateFields) -> tuple[dict[ModelSymbol, TrainedModel], list[ModelSymbol]]:
        model_syms = sorted(model_syms)
        models: dict[ModelSymbol, TrainedModel] = {}
        scope = StaticScope.instance()
        if scope.model_cache is None:
            return (models, model_syms)
        uncached_model_syms = []
        for model_sym in model_syms:
            cache_key = ModelCacheKey(symbol=model_sym.symbol, model_name=model_sym.model_name, **asdict(cache_date_fields))
            scope.logger.debug_get_model_cache(cache_key)
            cached_data = scope.model_cache.get(repr(cache_key))
            if cached_data is not None:
                input_cols = None
                if isinstance(cached_data, CachedModel):
                    model = cached_data.model
                    input_cols = cached_data.input_cols
                else:
                    model = cached_data
                source = scope.get_model_source(model_sym.model_name)
                models[model_sym] = TrainedModel(name=model_sym.model_name, instance=model, predict_fn=source._predict_fn, input_cols=input_cols)
            else:
                uncached_model_syms.append(model_sym)
        return (models, uncached_model_syms)

    def _set_cached_model(self, model: Any, input_cols: Optional[tuple[str]], model_sym: ModelSymbol, cache_date_fields: CacheDateFields):
        scope = StaticScope.instance()
        if scope.model_cache is None:
            return
        cache_key = ModelCacheKey(symbol=model_sym.symbol, model_name=model_sym.model_name, **asdict(cache_date_fields))
        cached_model = CachedModel(model, input_cols)
        scope.logger.debug_set_model_cache(cache_key)
        scope.model_cache.set(repr(cache_key), cached_model)

def _slice_by_symbol(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df[DataCol.SYMBOL.value] == symbol].drop(columns=DataCol.SYMBOL.value).sort_values(DataCol.DATE.value)

class AKShare(DataSource):
    """Retrieves data from `AKShare <https://akshare.akfamily.xyz/>`_."""
    _tf_to_period = {'': 'daily', '1day': 'daily', '1week': 'weekly'}

    def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[str]) -> pd.DataFrame:
        """:meta private:"""
        start_date_str = to_datetime(start_date).strftime('%Y%m%d')
        end_date_str = to_datetime(end_date).strftime('%Y%m%d')
        symbols_list = list(symbols)
        symbols_simple = [item.split('.')[0] for item in symbols_list]
        result = pd.DataFrame()
        formatted_tf = self._format_timeframe(timeframe)
        if formatted_tf in AKShare._tf_to_period:
            period = AKShare._tf_to_period[formatted_tf]
            for i in range(len(symbols_list)):
                temp_df = akshare.stock_zh_a_hist(symbol=symbols_simple[i], start_date=start_date_str, end_date=end_date_str, period=period, adjust=adjust if adjust is not None else '')
                if not temp_df.columns.empty:
                    temp_df['symbol'] = symbols_list[i]
                result = pd.concat([result, temp_df], ignore_index=True)
        if result.columns.empty:
            return pd.DataFrame(columns=[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value])
        if result.empty:
            return result
        result.rename(columns={'日期': DataCol.DATE.value, '开盘': DataCol.OPEN.value, '收盘': DataCol.CLOSE.value, '最高': DataCol.HIGH.value, '最低': DataCol.LOW.value, '成交量': DataCol.VOLUME.value}, inplace=True)
        result['date'] = pd.to_datetime(result['date'])
        result = result[[DataCol.DATE.value, DataCol.SYMBOL.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value]]
        return result

def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[str]) -> pd.DataFrame:
    """:meta private:"""
    start_date_str = to_datetime(start_date).strftime('%Y%m%d')
    end_date_str = to_datetime(end_date).strftime('%Y%m%d')
    symbols_list = list(symbols)
    symbols_simple = [item.split('.')[0] for item in symbols_list]
    result = pd.DataFrame()
    formatted_tf = self._format_timeframe(timeframe)
    if formatted_tf in AKShare._tf_to_period:
        period = AKShare._tf_to_period[formatted_tf]
        for i in range(len(symbols_list)):
            temp_df = akshare.stock_zh_a_hist(symbol=symbols_simple[i], start_date=start_date_str, end_date=end_date_str, period=period, adjust=adjust if adjust is not None else '')
            if not temp_df.columns.empty:
                temp_df['symbol'] = symbols_list[i]
            result = pd.concat([result, temp_df], ignore_index=True)
    if result.columns.empty:
        return pd.DataFrame(columns=[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value])
    if result.empty:
        return result
    result.rename(columns={'日期': DataCol.DATE.value, '开盘': DataCol.OPEN.value, '收盘': DataCol.CLOSE.value, '最高': DataCol.HIGH.value, '最低': DataCol.LOW.value, '成交量': DataCol.VOLUME.value}, inplace=True)
    result['date'] = pd.to_datetime(result['date'])
    result = result[[DataCol.DATE.value, DataCol.SYMBOL.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value]]
    return result

class YQuery(DataSource):
    """Retrieves data from Yahoo Finance using
    `Yahooquery <https://github.com/dpguthrie/yahooquery>`_\\ ."""
    _tf_to_period = {'': '1d', '1hour': '1h', '1day': '1d', '5day': '5d', '1week': '1wk'}

    def __init__(self, proxies: Optional[dict]=None):
        super().__init__()
        self.proxies = proxies

    def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[bool]) -> pd.DataFrame:
        """:meta private:"""
        show_yf_progress_bar = not self._logger._disabled and (not self._logger._progress_bar_disabled)
        ticker = Ticker(symbols, asynchronous=True, progress=show_yf_progress_bar, proxies=self.proxies)
        timeframe = self._format_timeframe(timeframe)
        if timeframe not in self._tf_to_period:
            raise ValueError(f"Unsupported timeframe: '{timeframe}'.\nSupported timeframes: {list(self._tf_to_period.keys())}.")
        df = ticker.history(start=start_date, end=end_date, interval=self._tf_to_period[timeframe], adj_ohlc=adjust)
        if df.columns.empty:
            return pd.DataFrame(columns=[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value])
        if df.empty:
            return df
        df = df.reset_index()
        df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
        df = df[[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value]]
        return df

def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, timeframe: Optional[str], adjust: Optional[bool]) -> pd.DataFrame:
    """:meta private:"""
    show_yf_progress_bar = not self._logger._disabled and (not self._logger._progress_bar_disabled)
    ticker = Ticker(symbols, asynchronous=True, progress=show_yf_progress_bar, proxies=self.proxies)
    timeframe = self._format_timeframe(timeframe)
    if timeframe not in self._tf_to_period:
        raise ValueError(f"Unsupported timeframe: '{timeframe}'.\nSupported timeframes: {list(self._tf_to_period.keys())}.")
    df = ticker.history(start=start_date, end=end_date, interval=self._tf_to_period[timeframe], adj_ohlc=adjust)
    if df.columns.empty:
        return pd.DataFrame(columns=[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value])
    if df.empty:
        return df
    df = df.reset_index()
    df[DataCol.DATE.value] = pd.to_datetime(df[DataCol.DATE.value])
    df = df[[DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value]]
    return df

@pytest.mark.parametrize('tf, expected', [('1day 2h 3min', 24 * 60 * 60 + 2 * 60 * 60 + 3 * 60), ('10week', 10 * 7 * 24 * 60 * 60), ('3d 20m', 3 * 24 * 60 * 60 + 20 * 60), ('30s', 30), (None, 0)])
def test_to_seconds(tf, expected):
    assert to_seconds(tf) == expected

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

def test_repr(self, hhv_ind):
    assert repr(hhv_ind) == "Indicator('hhv', {'n': 5})"

@pytest.mark.usefixtures('setup_teardown')
class TestIndicatorsMixin:

    def _assert_indicators(self, ind_data, ind_syms, data_source_df):
        assert set(ind_data.keys()) == set(ind_syms)
        for ind_sym, series in ind_data.items():
            df = data_source_df[data_source_df['symbol'] == ind_sym.symbol]
            assert len(series) == df.shape[0]

    @pytest.mark.usefixtures('setup_ind_cache')
    def test_compute_indicators(self, ind_syms, data_source_df, cache_date_fields, disable_parallel):
        mixin = IndicatorsMixin()
        ind_data = mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
        self._assert_indicators(ind_data, ind_syms, data_source_df)

    @pytest.mark.usefixtures('setup_ind_cache')
    def test_compute_indicators_when_empty_data(self, ind_syms, cache_date_fields, disable_parallel):
        mixin = IndicatorsMixin()
        ind_data = mixin.compute_indicators(df=pd.DataFrame(columns=[col.value for col in DataCol]), indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
        assert len(ind_data) == 0

    @pytest.mark.usefixtures('setup_enabled_ind_cache')
    def test_compute_indicators_data_when_cached(self, ind_syms, cache_date_fields, data_source_df, disable_parallel):
        mixin = IndicatorsMixin()
        mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
        ind_data = mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
        self._assert_indicators(ind_data, ind_syms, data_source_df)

    @pytest.mark.usefixtures('setup_enabled_ind_cache')
    def test_compute_indicators_when_partial_cached(self, ind_syms, cache_date_fields, data_source_df, disable_parallel):
        mixin = IndicatorsMixin()
        mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms[:1], cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
        ind_data = mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
        self._assert_indicators(ind_data, ind_syms, data_source_df)

@pytest.mark.usefixtures('setup_ind_cache')
def test_compute_indicators(self, ind_syms, data_source_df, cache_date_fields, disable_parallel):
    mixin = IndicatorsMixin()
    ind_data = mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
    self._assert_indicators(ind_data, ind_syms, data_source_df)

@pytest.mark.usefixtures('setup_ind_cache')
def test_compute_indicators_when_empty_data(self, ind_syms, cache_date_fields, disable_parallel):
    mixin = IndicatorsMixin()
    ind_data = mixin.compute_indicators(df=pd.DataFrame(columns=[col.value for col in DataCol]), indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
    assert len(ind_data) == 0

@pytest.mark.usefixtures('setup_enabled_ind_cache')
def test_compute_indicators_data_when_cached(self, ind_syms, cache_date_fields, data_source_df, disable_parallel):
    mixin = IndicatorsMixin()
    mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
    ind_data = mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
    self._assert_indicators(ind_data, ind_syms, data_source_df)

@pytest.mark.usefixtures('setup_enabled_ind_cache')
def test_compute_indicators_when_partial_cached(self, ind_syms, cache_date_fields, data_source_df, disable_parallel):
    mixin = IndicatorsMixin()
    mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms[:1], cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
    ind_data = mixin.compute_indicators(df=data_source_df, indicator_syms=ind_syms, cache_date_fields=cache_date_fields, disable_parallel=disable_parallel)
    self._assert_indicators(ind_data, ind_syms, data_source_df)

class TestIndicatorSet:

    def test_add_and_remove(self, hhv_ind, llv_ind, sumv_ind):
        ind_set = IndicatorSet()
        ind_set.add(hhv_ind)
        ind_set.add([llv_ind, sumv_ind], hhv_ind)
        assert ind_set._ind_names == set(['llv', 'hhv', 'sumv'])
        ind_set.remove(llv_ind)
        assert ind_set._ind_names == set(['hhv', 'sumv'])
        ind_set.remove(hhv_ind, sumv_ind)
        assert not ind_set._ind_names

    def test_clear(self, hhv_ind, llv_ind, sumv_ind):
        ind_set = IndicatorSet()
        ind_set.add(llv_ind, sumv_ind, hhv_ind)
        assert ind_set._ind_names == set(['llv', 'hhv', 'sumv'])
        ind_set.clear()
        assert not ind_set._ind_names

    def test_call_when_indicators_empty_then_error(self, data_source_df):
        ind_set = IndicatorSet()
        with pytest.raises(ValueError, match='No indicators were added.'):
            ind_set(data_source_df)

    @pytest.mark.parametrize('df', [pd.DataFrame(), LazyFixture('data_source_df')])
    def test_call(self, df, hhv_ind, llv_ind, disable_parallel, request):
        df = get_fixture(request, df)
        ind_set = IndicatorSet()
        ind_set.add([hhv_ind, llv_ind])
        result = ind_set(df, disable_parallel)
        assert len(result) == len(df)
        assert set(result.columns) == set(['date', 'symbol', 'hhv', 'llv'])

def test_add_and_remove(self, hhv_ind, llv_ind, sumv_ind):
    ind_set = IndicatorSet()
    ind_set.add(hhv_ind)
    ind_set.add([llv_ind, sumv_ind], hhv_ind)
    assert ind_set._ind_names == set(['llv', 'hhv', 'sumv'])
    ind_set.remove(llv_ind)
    assert ind_set._ind_names == set(['hhv', 'sumv'])
    ind_set.remove(hhv_ind, sumv_ind)
    assert not ind_set._ind_names

def test_clear(self, hhv_ind, llv_ind, sumv_ind):
    ind_set = IndicatorSet()
    ind_set.add(llv_ind, sumv_ind, hhv_ind)
    assert ind_set._ind_names == set(['llv', 'hhv', 'sumv'])
    ind_set.clear()
    assert not ind_set._ind_names

def test_call_when_indicators_empty_then_error(self, data_source_df):
    ind_set = IndicatorSet()
    with pytest.raises(ValueError, match='No indicators were added.'):
        ind_set(data_source_df)

@pytest.mark.parametrize('df', [pd.DataFrame(), LazyFixture('data_source_df')])
def test_call(self, df, hhv_ind, llv_ind, disable_parallel, request):
    df = get_fixture(request, df)
    ind_set = IndicatorSet()
    ind_set.add([hhv_ind, llv_ind])
    result = ind_set(df, disable_parallel)
    assert len(result) == len(df)
    assert set(result.columns) == set(['date', 'symbol', 'hhv', 'llv'])

def test_enable_logging(mock_logger):
    enable_logging()
    mock_logger.enable.assert_called_once()

def test_disable_logging(mock_logger):
    disable_logging()
    mock_logger.disable.assert_called_once()

class TestDataSourceCacheMixin:

    @pytest.mark.usefixtures('scope')
    def test_set_cached(self, alpaca_df, symbols, mock_cache):
        cache_mixin = DataSourceCacheMixin()
        cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, alpaca_df)
        assert len(mock_cache.set.call_args_list) == len(symbols)
        for i, sym in enumerate(symbols):
            expected_cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=to_seconds(TIMEFRAME), start_date=START_DATE, end_date=END_DATE, adjust=ADJUST)
            cache_key, sym_df = mock_cache.set.call_args_list[i].args
            assert cache_key == repr(expected_cache_key)
            assert sym_df.equals(alpaca_df[alpaca_df['symbol'] == sym])

    @pytest.mark.usefixtures('scope')
    @pytest.mark.parametrize('query_symbols', [[], LazyFixture('symbols')])
    def test_get_cached_when_empty(self, mock_cache, query_symbols, request):
        query_symbols = get_fixture(request, query_symbols)
        cache_mixin = DataSourceCacheMixin()
        df, uncached_syms = cache_mixin.get_cached(query_symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
        assert df.empty
        assert uncached_syms == query_symbols
        assert len(mock_cache.get.call_args_list) == len(query_symbols)
        for i, sym in enumerate(query_symbols):
            expected_cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=to_seconds(TIMEFRAME), start_date=START_DATE, end_date=END_DATE, adjust=ADJUST)
            cache_key = mock_cache.get.call_args_list[i].args[0]
            assert cache_key == repr(expected_cache_key)

    @pytest.mark.usefixtures('setup_enabled_ds_cache')
    def test_set_and_get_cached(self, alpaca_df, symbols):
        cache_mixin = DataSourceCacheMixin()
        cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, alpaca_df)
        df, uncached_syms = cache_mixin.get_cached(symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
        assert df.equals(alpaca_df)
        assert not len(uncached_syms)

    @pytest.mark.usefixtures('setup_enabled_ds_cache')
    def test_set_and_get_cached_when_partial(self, alpaca_df, symbols):
        cache_mixin = DataSourceCacheMixin()
        cached_df = alpaca_df[alpaca_df['symbol'].isin(symbols[:2])]
        cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, cached_df)
        df, uncached_syms = cache_mixin.get_cached(symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
        assert df.equals(cached_df)
        assert uncached_syms == symbols[2:]

    @pytest.mark.usefixtures('mock_cache')
    @pytest.mark.parametrize('timeframe, start_date, end_date, error', [('dffdfdf', datetime.strptime('2022-02-02', '%Y-%m-%d'), datetime.strptime('2021-02-02', '%Y-%m-%d'), ValueError), ('1m', 'sdfdfdfg', datetime.strptime('2022-02-02', '%Y-%m-%d'), Exception), ('1m', datetime.strptime('2021-02-02', '%Y-%m-%d'), 'sdfsdf', Exception)])
    def test_set_and_get_cached_when_invalid_times_then_error(self, alpaca_df, symbols, timeframe, start_date, end_date, error):
        cache_mixin = DataSourceCacheMixin()
        with pytest.raises(error):
            cache_mixin.set_cached(timeframe, start_date, end_date, ADJUST, alpaca_df)
        with pytest.raises(error):
            cache_mixin.get_cached(symbols, timeframe, start_date, end_date, ADJUST)

    def test_set_and_get_cached_when_cache_disabled(self, alpaca_df, symbols):
        cache_mixin = DataSourceCacheMixin()
        cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, alpaca_df)
        df, uncached_syms = cache_mixin.get_cached(symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
        assert df.empty
        assert uncached_syms == symbols

@pytest.mark.usefixtures('scope')
def test_set_cached(self, alpaca_df, symbols, mock_cache):
    cache_mixin = DataSourceCacheMixin()
    cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, alpaca_df)
    assert len(mock_cache.set.call_args_list) == len(symbols)
    for i, sym in enumerate(symbols):
        expected_cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=to_seconds(TIMEFRAME), start_date=START_DATE, end_date=END_DATE, adjust=ADJUST)
        cache_key, sym_df = mock_cache.set.call_args_list[i].args
        assert cache_key == repr(expected_cache_key)
        assert sym_df.equals(alpaca_df[alpaca_df['symbol'] == sym])

@pytest.mark.usefixtures('scope')
@pytest.mark.parametrize('query_symbols', [[], LazyFixture('symbols')])
def test_get_cached_when_empty(self, mock_cache, query_symbols, request):
    query_symbols = get_fixture(request, query_symbols)
    cache_mixin = DataSourceCacheMixin()
    df, uncached_syms = cache_mixin.get_cached(query_symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
    assert df.empty
    assert uncached_syms == query_symbols
    assert len(mock_cache.get.call_args_list) == len(query_symbols)
    for i, sym in enumerate(query_symbols):
        expected_cache_key = DataSourceCacheKey(symbol=sym, tf_seconds=to_seconds(TIMEFRAME), start_date=START_DATE, end_date=END_DATE, adjust=ADJUST)
        cache_key = mock_cache.get.call_args_list[i].args[0]
        assert cache_key == repr(expected_cache_key)

@pytest.mark.usefixtures('setup_enabled_ds_cache')
def test_set_and_get_cached(self, alpaca_df, symbols):
    cache_mixin = DataSourceCacheMixin()
    cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, alpaca_df)
    df, uncached_syms = cache_mixin.get_cached(symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
    assert df.equals(alpaca_df)
    assert not len(uncached_syms)

@pytest.mark.usefixtures('setup_enabled_ds_cache')
def test_set_and_get_cached_when_partial(self, alpaca_df, symbols):
    cache_mixin = DataSourceCacheMixin()
    cached_df = alpaca_df[alpaca_df['symbol'].isin(symbols[:2])]
    cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, cached_df)
    df, uncached_syms = cache_mixin.get_cached(symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
    assert df.equals(cached_df)
    assert uncached_syms == symbols[2:]

@pytest.mark.usefixtures('mock_cache')
@pytest.mark.parametrize('timeframe, start_date, end_date, error', [('dffdfdf', datetime.strptime('2022-02-02', '%Y-%m-%d'), datetime.strptime('2021-02-02', '%Y-%m-%d'), ValueError), ('1m', 'sdfdfdfg', datetime.strptime('2022-02-02', '%Y-%m-%d'), Exception), ('1m', datetime.strptime('2021-02-02', '%Y-%m-%d'), 'sdfsdf', Exception)])
def test_set_and_get_cached_when_invalid_times_then_error(self, alpaca_df, symbols, timeframe, start_date, end_date, error):
    cache_mixin = DataSourceCacheMixin()
    with pytest.raises(error):
        cache_mixin.set_cached(timeframe, start_date, end_date, ADJUST, alpaca_df)
    with pytest.raises(error):
        cache_mixin.get_cached(symbols, timeframe, start_date, end_date, ADJUST)

def test_set_and_get_cached_when_cache_disabled(self, alpaca_df, symbols):
    cache_mixin = DataSourceCacheMixin()
    cache_mixin.set_cached(TIMEFRAME, START_DATE, END_DATE, ADJUST, alpaca_df)
    df, uncached_syms = cache_mixin.get_cached(symbols, TIMEFRAME, START_DATE, END_DATE, ADJUST)
    assert df.empty
    assert uncached_syms == symbols

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

def test_query_when_null_timeframe_then_error(self, symbols):
    alpaca = Alpaca(API_KEY, API_SECRET)
    with pytest.raises(ValueError, match=re.escape('Timeframe needs to be specified for Alpaca.')):
        alpaca.query(symbols, START_DATE, END_DATE, timeframe=None)

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

def test_query_when_null_timeframe_then_error(self, symbols):
    crypto = Alpaca(API_KEY, API_SECRET)
    with pytest.raises(ValueError, match=re.escape('Timeframe needs to be specified for Alpaca.')):
        crypto.query(symbols, START_DATE, END_DATE, timeframe=None)

class TestYFinance:

    @pytest.mark.parametrize('param_symbols, expected_df, expected_rows', [(LazyFixture('symbols'), LazyFixture('yfinance_df'), 2020), (['SPY'], LazyFixture('yfinance_single_df'), 505)])
    @pytest.mark.usefixtures('setup_ds_cache')
    @pytest.mark.parametrize('auto_adjust', [True, False])
    def test_query(self, param_symbols, expected_df, expected_rows, request, auto_adjust):
        param_symbols = get_fixture(request, param_symbols)
        expected_df = get_fixture(request, expected_df)
        if auto_adjust:
            expected_df = expected_df.drop(columns=['Adj Close'])
        yf = YFinance(auto_adjust=auto_adjust)
        with mock.patch.object(yfinance, 'download', return_value=expected_df):
            df = yf.query(param_symbols, START_DATE, END_DATE)
        expected_columns = {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
        if not auto_adjust:
            expected_columns.add('adj_close')
        assert set(df.columns) == expected_columns
        assert df.shape[0] == expected_rows
        assert set(df['symbol'].unique()) == set(param_symbols)
        assert (df['date'].unique() == expected_df.index.unique()).all()

    @pytest.mark.usefixtures('setup_ds_cache')
    @pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'adj_close']])
    @pytest.mark.parametrize('auto_adjust', [True, False])
    def test_query_when_empty_result(self, symbols, columns, auto_adjust):
        yf = YFinance(auto_adjust=auto_adjust)
        if auto_adjust and 'adj_close' in columns:
            columns = [col for col in columns if col != 'adj_close']
        with mock.patch.object(yfinance, 'download', return_value=pd.DataFrame(columns=columns)):
            df = yf.query(symbols, START_DATE, END_DATE)
        assert df.empty
        expected_columns = {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
        if not auto_adjust:
            expected_columns.add('adj_close')
        assert set(df.columns) == expected_columns

@pytest.mark.parametrize('param_symbols, expected_df, expected_rows', [(LazyFixture('symbols'), LazyFixture('yfinance_df'), 2020), (['SPY'], LazyFixture('yfinance_single_df'), 505)])
@pytest.mark.usefixtures('setup_ds_cache')
@pytest.mark.parametrize('auto_adjust', [True, False])
def test_query(self, param_symbols, expected_df, expected_rows, request, auto_adjust):
    param_symbols = get_fixture(request, param_symbols)
    expected_df = get_fixture(request, expected_df)
    if auto_adjust:
        expected_df = expected_df.drop(columns=['Adj Close'])
    yf = YFinance(auto_adjust=auto_adjust)
    with mock.patch.object(yfinance, 'download', return_value=expected_df):
        df = yf.query(param_symbols, START_DATE, END_DATE)
    expected_columns = {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
    if not auto_adjust:
        expected_columns.add('adj_close')
    assert set(df.columns) == expected_columns
    assert df.shape[0] == expected_rows
    assert set(df['symbol'].unique()) == set(param_symbols)
    assert (df['date'].unique() == expected_df.index.unique()).all()

@pytest.mark.usefixtures('setup_ds_cache')
@pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'adj_close']])
@pytest.mark.parametrize('auto_adjust', [True, False])
def test_query_when_empty_result(self, symbols, columns, auto_adjust):
    yf = YFinance(auto_adjust=auto_adjust)
    if auto_adjust and 'adj_close' in columns:
        columns = [col for col in columns if col != 'adj_close']
    with mock.patch.object(yfinance, 'download', return_value=pd.DataFrame(columns=columns)):
        df = yf.query(symbols, START_DATE, END_DATE)
    assert df.empty
    expected_columns = {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
    if not auto_adjust:
        expected_columns.add('adj_close')
    assert set(df.columns) == expected_columns

class TestAKShare:

    @pytest.mark.usefixtures('setup_ds_cache')
    @pytest.mark.parametrize('timeframe', [None, '', '1d', '1w'])
    def test_query(self, timeframe):
        symbols = ['A']
        ak = AKShare()
        expected_df = pd.DataFrame({'日期': [END_DATE], '开盘': [1], '收盘': [2], '最高': [3], '最低': [4], '成交量': [5], 'symbol': symbols})
        with mock.patch.object(akshare, 'stock_zh_a_hist', return_value=expected_df):
            df = ak.query(symbols, START_DATE, END_DATE, timeframe)
        assert set(df.columns) == {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
        assert df.shape[0] == expected_df.shape[0]
        assert set(df['symbol'].unique()) == set(symbols)
        assert (df['date'].unique() == expected_df['日期'].unique()).all()

    @pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']])
    @pytest.mark.usefixtures('setup_ds_cache')
    def test_query_when_empty_result(self, columns):
        ak = AKShare()
        with mock.patch.object(akshare, 'stock_zh_a_hist', return_value=pd.DataFrame(columns=columns)):
            df = ak.query(['A'], START_DATE, END_DATE)
        assert df.empty
        assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol'))

    @pytest.mark.usefixtures('setup_ds_cache')
    def test_query_when_unsupported_timeframe_then_empty(self):
        symbols = ['A']
        ak = AKShare()
        expected_df = pd.DataFrame({'日期': [END_DATE], '开盘': [1], '收盘': [2], '最高': [3], '最低': [4], '成交量': [5], 'symbol': symbols})
        with mock.patch.object(akshare, 'stock_zh_a_hist', return_value=expected_df):
            df = ak.query(symbols, START_DATE, END_DATE, '2d')
        assert df.empty
        assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol'))

@pytest.mark.usefixtures('setup_ds_cache')
@pytest.mark.parametrize('timeframe', [None, '', '1d', '1w'])
def test_query(self, timeframe):
    symbols = ['A']
    ak = AKShare()
    expected_df = pd.DataFrame({'日期': [END_DATE], '开盘': [1], '收盘': [2], '最高': [3], '最低': [4], '成交量': [5], 'symbol': symbols})
    with mock.patch.object(akshare, 'stock_zh_a_hist', return_value=expected_df):
        df = ak.query(symbols, START_DATE, END_DATE, timeframe)
    assert set(df.columns) == {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
    assert df.shape[0] == expected_df.shape[0]
    assert set(df['symbol'].unique()) == set(symbols)
    assert (df['date'].unique() == expected_df['日期'].unique()).all()

@pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']])
@pytest.mark.usefixtures('setup_ds_cache')
def test_query_when_empty_result(self, columns):
    ak = AKShare()
    with mock.patch.object(akshare, 'stock_zh_a_hist', return_value=pd.DataFrame(columns=columns)):
        df = ak.query(['A'], START_DATE, END_DATE)
    assert df.empty
    assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol'))

@pytest.mark.usefixtures('setup_ds_cache')
def test_query_when_unsupported_timeframe_then_empty(self):
    symbols = ['A']
    ak = AKShare()
    expected_df = pd.DataFrame({'日期': [END_DATE], '开盘': [1], '收盘': [2], '最高': [3], '最低': [4], '成交量': [5], 'symbol': symbols})
    with mock.patch.object(akshare, 'stock_zh_a_hist', return_value=expected_df):
        df = ak.query(symbols, START_DATE, END_DATE, '2d')
    assert df.empty
    assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol'))

class TestYQuery:

    @pytest.mark.usefixtures('setup_ds_cache')
    @pytest.mark.parametrize('timeframe', [None, '', '1h', '1d', '5d', '1w'])
    def test_query(self, timeframe):
        yq = YQuery()
        symbols = ['A']
        expected_df = pd.DataFrame({'date': [END_DATE], 'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5], 'symbol': symbols})
        with mock.patch.object(Ticker, 'history', return_value=expected_df):
            df = yq.query(symbols, START_DATE, END_DATE, timeframe)
        assert set(df.columns) == {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
        assert df.shape[0] == expected_df.shape[0]
        assert set(df['symbol'].unique()) == set(symbols)
        assert (df['date'].unique() == expected_df['date'].unique()).all()

    @pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']])
    @pytest.mark.usefixtures('setup_ds_cache')
    def test_query_when_empty_result(self, columns):
        yq = YQuery()
        with mock.patch.object(Ticker, 'history', return_value=pd.DataFrame(columns=columns)):
            df = yq.query(['A'], START_DATE, END_DATE)
        assert df.empty
        assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol'))

    @pytest.mark.usefixtures('setup_ds_cache')
    def test_query_when_unsupported_timeframe_then_error(self):
        yq = YQuery()
        symbols = ['A']
        expected_df = pd.DataFrame({'date': [END_DATE], 'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5], 'symbol': symbols})
        with pytest.raises(ValueError, match=re.escape("Unsupported timeframe: '90min'.\nSupported timeframes: ['', '1hour', '1day', '5day', '1week'].")):
            with mock.patch.object(Ticker, 'history', return_value=expected_df):
                yq.query(symbols, START_DATE, END_DATE, '90m')

@pytest.mark.usefixtures('setup_ds_cache')
@pytest.mark.parametrize('timeframe', [None, '', '1h', '1d', '5d', '1w'])
def test_query(self, timeframe):
    yq = YQuery()
    symbols = ['A']
    expected_df = pd.DataFrame({'date': [END_DATE], 'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5], 'symbol': symbols})
    with mock.patch.object(Ticker, 'history', return_value=expected_df):
        df = yq.query(symbols, START_DATE, END_DATE, timeframe)
    assert set(df.columns) == {'date', 'open', 'high', 'low', 'close', 'volume', 'symbol'}
    assert df.shape[0] == expected_df.shape[0]
    assert set(df['symbol'].unique()) == set(symbols)
    assert (df['date'].unique() == expected_df['date'].unique()).all()

@pytest.mark.parametrize('columns', [[], ['date', 'open', 'high', 'low', 'close', 'volume', 'symbol']])
@pytest.mark.usefixtures('setup_ds_cache')
def test_query_when_empty_result(self, columns):
    yq = YQuery()
    with mock.patch.object(Ticker, 'history', return_value=pd.DataFrame(columns=columns)):
        df = yq.query(['A'], START_DATE, END_DATE)
    assert df.empty
    assert set(df.columns) == set(('date', 'open', 'high', 'low', 'close', 'volume', 'symbol'))

@pytest.mark.usefixtures('setup_ds_cache')
def test_query_when_unsupported_timeframe_then_error(self):
    yq = YQuery()
    symbols = ['A']
    expected_df = pd.DataFrame({'date': [END_DATE], 'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5], 'symbol': symbols})
    with pytest.raises(ValueError, match=re.escape("Unsupported timeframe: '90min'.\nSupported timeframes: ['', '1hour', '1day', '5day', '1week'].")):
        with mock.patch.object(Ticker, 'history', return_value=expected_df):
            yq.query(symbols, START_DATE, END_DATE, '90m')

@pytest.mark.usefixtures('setup_teardown')
@pytest.mark.parametrize('enable_fn, disable_fn, cache_attr', [(enable_data_source_cache, disable_data_source_cache, 'data_source_cache'), (enable_indicator_cache, disable_indicator_cache, 'indicator_cache'), (enable_model_cache, disable_model_cache, 'model_cache')])
def test_enable_and_disable_cache(scope, enable_fn, disable_fn, cache_attr, cache_dir, cache_path):
    cache = enable_fn('test', cache_dir)
    assert cache is not None
    assert cache.directory
    assert len(list(cache_path.iterdir())) == 1
    assert isinstance(getattr(scope, cache_attr), Cache)
    assert getattr(scope, f'{cache_attr}_ns') == 'test'
    disable_fn()
    assert getattr(scope, cache_attr) is None
    assert getattr(scope, f'{cache_attr}_ns') == ''

@pytest.mark.usefixtures('setup_teardown')
@pytest.mark.parametrize('enable_fn, clear_fn, cache_attr', [(enable_data_source_cache, clear_data_source_cache, 'data_source_cache'), (enable_indicator_cache, clear_indicator_cache, 'indicator_cache'), (enable_model_cache, clear_model_cache, 'model_cache')])
def test_clear_cache_when_enabled_then_success(scope, enable_fn, clear_fn, cache_attr, cache_dir):
    enable_fn('test', cache_dir)
    with mock.patch.object(scope, cache_attr) as cache:
        clear_fn()
        cache.clear.assert_called_once()

@pytest.mark.usefixtures('setup_teardown')
def test_enable_and_disable_all_caches(scope, cache_dir, cache_path):
    enable_caches('test', cache_dir)
    assert len(list(cache_path.iterdir())) == 1
    assert isinstance(scope.data_source_cache, Cache)
    assert isinstance(scope.indicator_cache, Cache)
    assert isinstance(scope.model_cache, Cache)
    assert scope.data_source_cache_ns == 'test'
    assert scope.indicator_cache_ns == 'test'
    assert scope.model_cache_ns == 'test'
    disable_caches()
    assert scope.data_source_cache is None
    assert scope.indicator_cache is None
    assert scope.model_cache is None
    assert scope.data_source_cache_ns == ''
    assert scope.indicator_cache_ns == ''
    assert scope.model_cache_ns == ''

@pytest.mark.usefixtures('setup_teardown')
def test_clear_all_caches(scope, cache_dir):
    enable_caches('test', cache_dir)
    with mock.patch.object(scope, 'data_source_cache') as data_source_cache, mock.patch.object(scope, 'indicator_cache') as ind_cache, mock.patch.object(scope, 'model_cache') as model_cache:
        clear_caches()
        data_source_cache.clear.assert_called_once()
        ind_cache.clear.assert_called_once()
        model_cache.clear.assert_called_once()

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

class TestModelsMixin:

    def _assert_models(self, models, expected_model_syms):
        assert set(models.keys()) == set(expected_model_syms)
        for model_sym in expected_model_syms:
            model = models[model_sym]
            assert isinstance(model, TrainedModel)
            assert model.name == model_sym.model_name
            assert model.instance.symbol == model_sym.symbol

    @pytest.mark.usefixtures('setup_model_cache')
    @pytest.mark.parametrize('param_test_data', [pd.DataFrame(columns=['symbol', 'date']), LazyFixture('test_data')])
    def test_train_models(self, model_syms, train_data, param_test_data, ind_data, cache_date_fields, request):
        param_test_data = get_fixture(request, param_test_data)
        mixin = ModelsMixin()
        models = mixin.train_models(model_syms, train_data, param_test_data, ind_data, cache_date_fields)
        self._assert_models(models, model_syms)

    @pytest.mark.usefixtures('setup_model_cache')
    def test_train_models_when_empty_train_data(self, model_syms, test_data, ind_data, cache_date_fields):
        mixin = ModelsMixin()
        models = mixin.train_models(model_syms, pd.DataFrame(), test_data, ind_data, cache_date_fields)
        assert len(models) == 0

    @pytest.mark.usefixtures('setup_enabled_model_cache')
    def test_train_models_when_cached(self, model_syms, train_data, test_data, ind_data, cache_date_fields):
        mixin = ModelsMixin()
        mixin.train_models(model_syms, train_data, test_data, ind_data, cache_date_fields)
        models = mixin.train_models(model_syms, train_data, test_data, ind_data, cache_date_fields)
        self._assert_models(models, model_syms)

    @pytest.mark.usefixtures('setup_enabled_model_cache')
    def test_train_models_when_partial_cached(self, model_syms, train_data, test_data, ind_data, cache_date_fields):
        mixin = ModelsMixin()
        mixin.train_models(model_syms[:1], train_data, test_data, ind_data, cache_date_fields)
        models = mixin.train_models(model_syms, train_data, test_data, ind_data, cache_date_fields)
        self._assert_models(models, model_syms)

@pytest.mark.usefixtures('setup_model_cache')
@pytest.mark.parametrize('param_test_data', [pd.DataFrame(columns=['symbol', 'date']), LazyFixture('test_data')])
def test_train_models(self, model_syms, train_data, param_test_data, ind_data, cache_date_fields, request):
    param_test_data = get_fixture(request, param_test_data)
    mixin = ModelsMixin()
    models = mixin.train_models(model_syms, train_data, param_test_data, ind_data, cache_date_fields)
    self._assert_models(models, model_syms)

@pytest.mark.usefixtures('setup_model_cache')
def test_train_models_when_empty_train_data(self, model_syms, test_data, ind_data, cache_date_fields):
    mixin = ModelsMixin()
    models = mixin.train_models(model_syms, pd.DataFrame(), test_data, ind_data, cache_date_fields)
    assert len(models) == 0

@pytest.mark.usefixtures('setup_enabled_model_cache')
def test_train_models_when_cached(self, model_syms, train_data, test_data, ind_data, cache_date_fields):
    mixin = ModelsMixin()
    mixin.train_models(model_syms, train_data, test_data, ind_data, cache_date_fields)
    models = mixin.train_models(model_syms, train_data, test_data, ind_data, cache_date_fields)
    self._assert_models(models, model_syms)

@pytest.mark.usefixtures('setup_enabled_model_cache')
def test_train_models_when_partial_cached(self, model_syms, train_data, test_data, ind_data, cache_date_fields):
    mixin = ModelsMixin()
    mixin.train_models(model_syms[:1], train_data, test_data, ind_data, cache_date_fields)
    models = mixin.train_models(model_syms, train_data, test_data, ind_data, cache_date_fields)
    self._assert_models(models, model_syms)

