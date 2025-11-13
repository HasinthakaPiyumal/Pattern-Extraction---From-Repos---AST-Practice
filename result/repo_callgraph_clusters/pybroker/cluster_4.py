# Cluster 4

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

def _get_shares(self, shares: Union[int, float, Decimal], enable_fractional_shares: bool) -> Decimal:
    if enable_fractional_shares:
        return to_decimal(shares)
    else:
        return to_decimal(int(shares))

class Portfolio:
    """Class representing a portfolio of holdings. The portfolio contains
    information about open positions and balances, and is also used to place
    buy and sell orders.

    Args:
        cash: Starting cash balance.
        fee_mode: Brokerage fee mode.
        fee_amount: Brokerage fee amount.
        subtract_fees: Whether to subtract fees from the cash balance after an
            order is filled.
        enable_fractional_shares: Whether to enable trading fractional shares.
        position_mode: Position mode for :class:`.Portfolio`.
        max_long_positions: Maximum number of long :class:`.Position`\\ s that
            can be held at a time. If ``None``, then unlimited.
        max_short_positions: Maximum number of short :class:`.Position`\\ s that
            can be held at a time. If ``None``, then unlimited.
        record_stops: Whether to record stop data per-bar.

    Attributes:
        cash: Current cash balance.
        equity: Current amount of equity.
        market_value: Current market value. The market value is defined as
            the amount of equity held in cash and long positions added together
            with the unrealized PnL of all open short positions.
        fees: Current brokerage fees.
        fee_amount: Brokerage fee amount.
        subtract_fees: Whether to subtract fees from the cash balance.
        enable_fractional_shares: Whether to enable trading fractional shares.
        orders: ``deque`` of all filled orders, sorted in ascending
            chronological order.
        margin: Current amount of margin held in open positions.
        pnl: Realized profit and loss (PnL).
        long_positions: ``dict`` mapping ticker symbols to open long
            :class:`.Position`\\ s.
        short_positions: ``dict`` mapping ticker symbols to open short
            :class:`.Position`\\ s.
        symbols: Ticker symbols of all currently open positions.
        bars: ``deque`` of snapshots of :class:`.Portfolio` state on every bar,
            sorted in ascending chronological order.
        position_bars: ``deque`` of snapshots of :class:`.Position` states on
            every bar, sorted in ascending chronological order.
        win_rate: Running win rate of trades.
        loss_rate: Running loss rate of trades.
    """

    def __init__(self, cash: float, fee_mode: Optional[Union[FeeMode, Callable[[FeeInfo], Decimal], None]]=None, fee_amount: Optional[float]=None, subtract_fees: bool=False, enable_fractional_shares: bool=False, position_mode: PositionMode=PositionMode.DEFAULT, max_long_positions: Optional[int]=None, max_short_positions: Optional[int]=None, record_stops: Optional[bool]=False):
        self.cash: Decimal = to_decimal(cash)
        self._initial_market_value = self.cash
        self._fee_mode = fee_mode
        self._fee_amount: Optional[Decimal] = None if fee_amount is None else to_decimal(fee_amount)
        self._subtract_fees = subtract_fees
        self._enable_fractional_shares = enable_fractional_shares
        self._position_mode = position_mode
        self.equity: Decimal = self.cash
        self.market_value: Decimal = self.cash
        self.fees = Decimal()
        self._max_long_positions = max_long_positions
        self._max_short_positions = max_short_positions
        self._record_stops = record_stops
        self.orders: deque[Order] = deque()
        self.trades: deque[Trade] = deque()
        self.margin: Decimal = Decimal()
        self.pnl: Decimal = Decimal()
        self.long_positions: dict[str, Position] = {}
        self.short_positions: dict[str, Position] = {}
        self.symbols: set[str] = set()
        self.bars: deque[PortfolioBar] = deque()
        self.position_bars: deque[PositionBar] = deque()
        self.win_rate: Decimal = Decimal()
        self.loss_rate: Decimal = Decimal()
        self._wins: Decimal = Decimal()
        self._logger = StaticScope.instance().logger
        self._stop_data: dict[int, _StopData] = {}
        self._order_id: int = 0
        self._entry_id: int = 0
        self._trade_id: int = 0
        self._stop_records: list[StopRecord] = []

    def _calculate_fees(self, symbol: str, fill_price: Decimal, shares: Decimal, order_type: Literal['buy', 'sell']) -> Decimal:
        fees = Decimal()
        if self._fee_mode is None or self._fee_amount is None:
            return fees
        if callable(self._fee_mode):
            fees = to_decimal(self._fee_mode(FeeInfo(symbol=symbol, shares=shares, fill_price=fill_price, order_type=order_type)))
        elif self._fee_mode == FeeMode.ORDER_PERCENT:
            fees = self._fee_amount / _DECIMAL_100 * fill_price * shares
        elif self._fee_mode == FeeMode.PER_ORDER:
            fees = self._fee_amount
        elif self._fee_mode == FeeMode.PER_SHARE:
            fees = self._fee_amount * shares
        else:
            raise ValueError(f'Unknown FeeMode: {self._fee_mode!r}')
        return fees

    def _verify_input(self, shares: Union[int, float, Decimal], fill_price: Decimal, limit_price: Optional[Decimal]):
        if shares < 0:
            raise ValueError(f'Shares cannot be negative: {shares}')
        if fill_price <= 0:
            raise ValueError(f'Fill price must be > 0: {fill_price}')
        if limit_price is not None and limit_price <= 0:
            raise ValueError(f'Limit price must be > 0: {limit_price}')

    def _add_entry(self, date: np.datetime64, symbol: str, shares: Decimal, price: Decimal, type: Literal['long', 'short'], pos: Position) -> Entry:
        self._entry_id += 1
        entry = Entry(id=self._entry_id, symbol=symbol, shares=shares, price=price, date=date, type=type)
        pos.entries.append(entry)
        return entry

    def _add_order(self, date: np.datetime64, symbol: str, type: Literal['buy', 'sell'], limit_price: Optional[Decimal], fill_price: Decimal, shares: Decimal) -> Order:
        self._order_id += 1
        fees = self._calculate_fees(symbol, fill_price, shares, type)
        order = Order(id=self._order_id, date=date, symbol=symbol, type=type, limit_price=limit_price, fill_price=fill_price, shares=shares, fees=fees)
        self.orders.append(order)
        self.fees += fees
        if self._subtract_fees:
            self.cash -= fees
        return order

    def _add_trade(self, type: Literal['long', 'short'], symbol: str, entry_date: np.datetime64, exit_date: np.datetime64, entry_price: Decimal, exit_price: Decimal, shares: Decimal, pnl: Decimal, return_pct: Decimal, agg_pnl: Decimal, bars: int, pnl_per_bar: Decimal, stop_type: Optional[StopType], mae: Decimal, mfe: Decimal):
        self._trade_id += 1
        trade = Trade(id=self._trade_id, type=type, symbol=symbol, entry_date=entry_date, exit_date=exit_date, entry=entry_price, exit=exit_price, shares=shares, pnl=pnl, return_pct=return_pct, agg_pnl=agg_pnl, bars=bars, pnl_per_bar=pnl_per_bar, stop=None if stop_type is None else stop_type.value, mae=mae, mfe=mfe)
        self.trades.append(trade)
        if pnl > 0:
            self._wins += 1
        self.win_rate = self._wins / len(self.trades)
        self.loss_rate = 1 - self.win_rate

    def _get_stop_amount(self, stop: Stop, price: Decimal) -> Decimal:
        if stop.percent is not None:
            return price * stop.percent / 100
        elif stop.points is not None:
            return stop.points
        else:
            raise ValueError('Stop amount not set.')

    def _add_stops(self, entry: Entry, stops: Iterable[Stop]):
        for stop in stops:
            if stop.id in self._stop_data:
                raise ValueError(f'Duplicate stop ID: {stop.id}')
            entry.stops.append(stop)
            if stop.stop_type == StopType.BAR:
                continue
            amount = self._get_stop_amount(stop, entry.price)
            if stop.pos_type == 'long' and stop.stop_type == StopType.PROFIT or (stop.pos_type == 'short' and (stop.stop_type == StopType.LOSS or stop.stop_type == StopType.TRAILING)):
                stop_value = entry.price + amount
            else:
                stop_value = entry.price - amount
            self._stop_data[stop.id] = _StopData(value=stop_value, stop=stop, entry=entry)

    def _remove_stop_data(self, entry: Entry):
        for stop in entry.stops:
            if stop.id in self._stop_data:
                del self._stop_data[stop.id]

    def _clamp_shares(self, fill_price: Decimal, shares: Decimal) -> Decimal:
        if self.cash < 0:
            return Decimal()
        max_shares = Decimal(self.cash / fill_price) if self._enable_fractional_shares else Decimal(self.cash // fill_price)
        return min(shares, max_shares)

    def buy(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]=None, stops: Optional[Iterable[Stop]]=None) -> Optional[Order]:
        """Places a buy order.

        Args:
            date: Date when the :class:`.Order` is placed.
            symbol: Ticker symbol to buy.
            shares: Number of shares to buy.
            fill_price: If filled, the price used to fill the :class:`.Order`.
            limit_price: Limit price of the :class:`.Order`.
            stops: :class:`.Stop`\\ s to set on the :class:`.Entry` created from
                the :class:`.Order`, if filled.

        Returns:
            :class:`.Order` if the order was filled, otherwise ``None``.
        """
        self._verify_input(shares, fill_price, limit_price)
        self._logger.debug_place_buy_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        if limit_price is not None and limit_price < fill_price:
            return None
        if shares == 0:
            return None
        covered = self._cover(date, symbol, shares, fill_price)
        bought_shares = self._long(date, symbol, covered.rem_shares, fill_price, limit_price, stops)
        if not covered.filled_shares and (not bought_shares):
            return None
        order = self._add_order(date=date, symbol=symbol, type='buy', limit_price=limit_price, fill_price=fill_price, shares=covered.filled_shares + bought_shares)
        return order

    def _cover(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal) -> _OrderResult:
        if symbol not in self.short_positions:
            return _OrderResult(Decimal(), shares)
        rem_shares = shares
        if rem_shares <= 0:
            return _OrderResult(Decimal(), shares)
        pos = self.short_positions[symbol]
        while pos.entries:
            entry = pos.entries[0]
            if rem_shares >= entry.shares:
                rem_shares -= entry.shares
                self._exit_short(date, pos, entry, entry.shares, fill_price, stop_type=None)
                self._remove_stop_data(entry)
                pos.entries.popleft()
            else:
                self._exit_short(date, pos, entry, rem_shares, fill_price, stop_type=None)
                rem_shares = Decimal()
                break
        self._update_position(pos)
        return _OrderResult(shares - rem_shares, rem_shares)

    def _exit_short(self, date: np.datetime64, pos: Position, entry: Entry, shares: Decimal, fill_price: Decimal, stop_type: Optional[StopType]):
        order_amount = shares * fill_price
        entry_amount = shares * entry.price
        entry_pnl = entry_amount - order_amount
        self.pnl += entry_pnl
        self.cash += entry_pnl
        pos.shares -= shares
        entry.shares -= shares
        pnl_per_bar = entry_pnl if not entry.bars else entry_pnl / entry.bars
        return_pct = (entry.price / fill_price - 1) * 100
        pnl = entry.price - fill_price
        mae = pnl if pnl < 0 and pnl < entry.mae else entry.mae
        mfe = pnl if pnl > 0 and pnl > entry.mfe else entry.mfe
        self._add_trade(type=entry.type, symbol=entry.symbol, entry_date=entry.date, exit_date=date, entry_price=entry.price, exit_price=fill_price, shares=shares, pnl=entry_pnl, return_pct=return_pct, agg_pnl=self.pnl, bars=entry.bars, pnl_per_bar=pnl_per_bar, stop_type=stop_type, mae=mae, mfe=mfe)

    def _long(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal], stops: Optional[Iterable[Stop]]) -> Decimal:
        if self._position_mode == PositionMode.SHORT_ONLY:
            return Decimal()
        clamped_shares = self._clamp_shares(fill_price, shares)
        if clamped_shares < shares:
            self._logger.debug_buy_shares_exceed_cash(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price, cash=self.cash, clamped_shares=clamped_shares)
            shares = clamped_shares
        if shares <= 0:
            return Decimal()
        if self._max_long_positions is not None and symbol not in self.long_positions and (len(self.long_positions) == self._max_long_positions):
            return Decimal()
        order_amount = shares * fill_price
        self.cash -= order_amount
        if symbol not in self.long_positions:
            self.symbols.add(symbol)
            pos = Position(symbol=symbol, shares=shares, type='long')
            self.long_positions[symbol] = pos
        else:
            pos = self.long_positions[symbol]
            pos.shares += shares
        entry = self._add_entry(date=date, symbol=symbol, shares=shares, price=fill_price, type='long', pos=pos)
        if stops is not None:
            self._add_stops(entry, stops)
        return shares

    def sell(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]=None, stops: Optional[Iterable[Stop]]=None) -> Optional[Order]:
        """Places a sell order.

        Args:
            date: Date when the :class:`.Order` is placed.
            symbol: Ticker symbol to sell.
            shares: Number of shares to sell.
            fill_price: If filled, the price used to fill the :class:`.Order`.
            limit_price: Limit price of the :class:`.Order`.
            stops: :class:`.Stop`\\ s to set on the :class:`.Entry` created from
                the :class:`.Order`, if filled.

        Returns:
            :class:`.Order` if the order was filled, otherwise ``None``.
        """
        self._verify_input(shares, fill_price, limit_price)
        self._logger.debug_place_sell_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
        if limit_price is not None and limit_price > fill_price:
            return None
        if shares == 0:
            return None
        sold = self._sell_existing(date, symbol, shares, fill_price)
        short_shares = self._short(date, symbol, sold.rem_shares, fill_price, stops)
        if not sold.filled_shares and (not short_shares):
            return None
        order = self._add_order(date=date, symbol=symbol, type='sell', limit_price=limit_price, fill_price=fill_price, shares=sold.filled_shares + short_shares)
        return order

    def _sell_existing(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal) -> _OrderResult:
        if symbol not in self.long_positions:
            return _OrderResult(Decimal(), shares)
        rem_shares = shares
        pos = self.long_positions[symbol]
        while pos.entries:
            entry = pos.entries[0]
            if rem_shares >= entry.shares:
                rem_shares -= entry.shares
                self._exit_long(date, pos, entry, entry.shares, fill_price, stop_type=None)
                self._remove_stop_data(entry)
                pos.entries.popleft()
            else:
                self._exit_long(date, pos, entry, rem_shares, fill_price, stop_type=None)
                rem_shares = Decimal()
                break
        self._update_position(pos)
        return _OrderResult(shares - rem_shares, rem_shares)

    def _exit_long(self, date: np.datetime64, pos: Position, entry: Entry, shares: Decimal, fill_price: Decimal, stop_type: Optional[StopType]):
        order_amount = shares * fill_price
        entry_amount = shares * entry.price
        entry_pnl = order_amount - entry_amount
        self.pnl += entry_pnl
        self.cash += order_amount
        pos.shares -= shares
        entry.shares -= shares
        pnl_per_bar = entry_pnl if not entry.bars else entry_pnl / entry.bars
        return_pct = (fill_price / entry.price - 1) * 100
        pnl = fill_price - entry.price
        mae = pnl if pnl < 0 and pnl < entry.mae else entry.mae
        mfe = pnl if pnl > 0 and pnl > entry.mfe else entry.mfe
        self._add_trade(type=entry.type, symbol=entry.symbol, entry_date=entry.date, exit_date=date, entry_price=entry.price, exit_price=fill_price, shares=shares, pnl=entry_pnl, return_pct=return_pct, agg_pnl=self.pnl, bars=entry.bars, pnl_per_bar=pnl_per_bar, stop_type=stop_type, mae=mae, mfe=mfe)

    def _update_position(self, pos: Position):
        if pos.entries:
            return
        if pos.type == 'long':
            if pos.symbol in self.long_positions:
                del self.long_positions[pos.symbol]
        elif pos.symbol in self.short_positions:
            del self.short_positions[pos.symbol]
        if pos.symbol in self.symbols and pos.symbol not in self.long_positions and (pos.symbol not in self.short_positions):
            self.symbols.remove(pos.symbol)

    def _short(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, stops: Optional[Iterable[Stop]]) -> Decimal:
        if shares <= 0:
            return Decimal()
        if self._max_short_positions is not None and symbol not in self.short_positions and (len(self.short_positions) == self._max_short_positions):
            return Decimal()
        if self._position_mode == PositionMode.LONG_ONLY:
            return Decimal()
        if symbol not in self.short_positions:
            self.symbols.add(symbol)
            pos = Position(symbol=symbol, shares=shares, type='short')
            self.short_positions[symbol] = pos
        else:
            pos = self.short_positions[symbol]
            pos.shares += shares
        entry = self._add_entry(date=date, symbol=symbol, shares=shares, price=fill_price, type='short', pos=pos)
        if stops is not None:
            self._add_stops(entry, stops)
        return shares

    def exit_position(self, date: np.datetime64, symbol: str, buy_fill_price: Decimal, sell_fill_price: Decimal):
        """Exits any long and short positions for ``symbol`` at
        ``buy_fill_price`` and ``sell_fill_price``.
        """
        if symbol in self.long_positions:
            self.sell(date=date, symbol=symbol, shares=self.long_positions[symbol].shares, fill_price=sell_fill_price)
        if symbol in self.short_positions:
            self.buy(date=date, symbol=symbol, shares=self.short_positions[symbol].shares, fill_price=buy_fill_price)

    def capture_bar(self, date: np.datetime64, df: pd.DataFrame):
        """Captures portfolio state of the current bar.

        Args:
            date: Date of current bar.
            df: :class:`pandas.DataFrame` containing close prices.
        """
        total_equity = self.cash
        total_market_value = total_equity
        total_margin = Decimal()
        for sym in self.symbols:
            index = (sym, date)
            close = None
            low = None
            high = None
            if index in df.index:
                df_row = df.loc[index].squeeze()
                if isinstance(df_row, pd.core.frame.DataFrame):
                    raise ValueError('df has the same index. index:' + str(index))
                close = to_decimal(df_row[DataCol.CLOSE.value])
                low = to_decimal(df_row[DataCol.LOW.value])
                high = to_decimal(df_row[DataCol.HIGH.value])
            pos_long_shares = Decimal()
            pos_short_shares = Decimal()
            pos_equity = Decimal()
            pos_market_value = Decimal()
            pos_margin = Decimal()
            pos_pnl = Decimal()
            if sym in self.long_positions:
                pos = self.long_positions[sym]
                if close is not None:
                    _calculate_pnl_mae_mfe(pos, close=close, low=low, high=high)
                    pos.equity = pos.shares * close
                    pos.market_value = pos.equity
                    pos.close = close
                    pos_long_shares += pos.shares
                    pos_equity += pos.equity
                    pos_market_value += pos.market_value
                    pos_pnl += pos.pnl
                total_equity += pos.equity
                total_market_value += pos.equity
            if sym in self.short_positions:
                pos = self.short_positions[sym]
                if close is not None:
                    _calculate_pnl_mae_mfe(pos, close=close, low=low, high=high)
                    pos.close = close
                    pos.margin = close * pos.shares
                    pos.market_value = pos.margin + pos.pnl
                    pos_margin += pos.margin
                    pos_short_shares += pos.shares
                    pos_market_value += pos.market_value
                    pos_pnl += pos.pnl
                total_margin += pos.margin
                total_market_value += pos.pnl
            if close is not None:
                self.position_bars.append(PositionBar(symbol=sym, date=date, long_shares=pos_long_shares, short_shares=pos_short_shares, close=close, equity=pos_equity, market_value=pos_market_value, margin=pos_margin, unrealized_pnl=pos_pnl))
        self.equity = total_equity
        self.market_value = total_market_value
        self.margin = total_margin
        self.bars.append(PortfolioBar(date=date, cash=self.cash, equity=self.equity, market_value=self.market_value, margin=self.margin, pnl=self.equity - self._initial_market_value, unrealized_pnl=self.market_value - self.equity, fees=self.fees))

    def incr_bars(self):
        """Increments the number of bars held by every trade entry."""
        for pos in itertools.chain(self.long_positions.values(), self.short_positions.values()):
            pos.bars += 1
            for entry in pos.entries:
                entry.bars += 1

    def remove_stop(self, stop_id: int) -> bool:
        """Removes a :class:`.Stop` with ``stop_id``."""
        if stop_id in self._stop_data:
            stop_data = self._stop_data[stop_id]
            del self._stop_data[stop_id]
            if stop_data.stop in stop_data.entry.stops:
                stop_data.entry.stops.remove(stop_data.stop)
            return True
        return False

    def remove_stops(self, val: Union[str, Position, Entry], stop_type: Optional[StopType]=None):
        """Removes :class:`.Stop`\\ s.

        Args:
            val: Ticker symbol, :class:`.Position`, or :class:`.Entry` for
                which to cancel stops.
            stop_type: :class:`pybroker.common.StopType`.
        """
        if isinstance(val, str):
            if val in self.long_positions:
                self._remove_position_stops(self.long_positions[val], stop_type)
            if val in self.short_positions:
                self._remove_position_stops(self.short_positions[val], stop_type)
        elif isinstance(val, Position):
            self._remove_position_stops(val, stop_type)
        elif isinstance(val, Entry):
            self._remove_entry_stops(val, stop_type)

    def _remove_position_stops(self, pos: Position, stop_type: Optional[StopType]):
        for entry in pos.entries:
            self._remove_entry_stops(entry, stop_type)

    def _remove_entry_stops(self, entry: Entry, stop_type: Optional[StopType]):
        if stop_type is None:
            self._remove_stop_data(entry)
            entry.stops.clear()
        else:
            stop_id = None
            for stop in entry.stops:
                if stop.stop_type == stop_type:
                    stop_id = stop.id
                    break
            if stop_id is not None:
                self.remove_stop(stop_id)

    def check_stops(self, date: np.datetime64, price_scope: PriceScope):
        """Checks whether stops are triggered."""
        executed: deque[tuple[Position, Entry]] = deque()
        for pos in itertools.chain(self.long_positions.values(), self.short_positions.values()):
            for entry in pos.entries:
                for stop in entry.stops:
                    triggered, fill_price = self._trigger_stop(date, price_scope, pos, entry, stop)
                    if self._record_stops:
                        self._capture_stop(date, entry, stop, fill_price)
                    if triggered:
                        executed.append((pos, entry))
                        break
        for pos, entry in executed:
            pos.entries.remove(entry)
            self._remove_stop_data(entry)
            self._update_position(pos)

    def _capture_stop(self, date: np.datetime64, entry: Entry, stop: Stop, fill_price: Optional[Decimal]):
        stop_record = StopRecord(date=date, stop_id=stop.id, symbol=stop.symbol, stop_type=stop.stop_type.value, pos_type=stop.pos_type, curr_value=self._stop_data[stop.id].value if stop.id in self._stop_data else None, curr_bars=entry.bars if stop.stop_type == StopType.BAR else None, bars=stop.bars, percent=stop.percent, points=stop.points, limit_price=stop.limit_price, exit_price=stop.exit_price, fill_price=fill_price)
        self._stop_records.append(stop_record)

    def _trigger_stop(self, date: np.datetime64, price_scope: PriceScope, pos: Position, entry: Entry, stop: Stop) -> tuple[bool, Optional[Decimal]]:
        fill_price = None
        if stop.pos_type == 'long' and stop.symbol not in self.long_positions:
            return (False, fill_price)
        if stop.pos_type == 'short' and stop.symbol not in self.short_positions:
            return (False, fill_price)
        if stop.stop_type == StopType.BAR:
            fill_price = self._trigger_bar_stop(stop, price_scope, entry)
        elif stop.stop_type == StopType.LOSS or stop.stop_type == StopType.PROFIT:
            fill_price = self._trigger_profit_or_loss_stop(stop, price_scope)
        elif stop.stop_type == StopType.TRAILING:
            fill_price = self._trigger_trailing_stop(stop, price_scope)
        else:
            raise ValueError(f'Unknown stop type: {stop.stop_type}')
        if fill_price is None:
            return (False, fill_price)
        order_type: Literal['buy', 'sell']
        stop_shares = entry.shares
        if stop.pos_type == 'long':
            if stop.limit_price is not None and fill_price < stop.limit_price:
                return (False, fill_price)
            self._exit_long(date, pos, entry, entry.shares, fill_price, stop.stop_type)
            order_type = 'sell'
        elif stop.pos_type == 'short':
            if stop.limit_price is not None and fill_price > stop.limit_price:
                return (False, fill_price)
            self._exit_short(date, pos, entry, entry.shares, fill_price, stop.stop_type)
            order_type = 'buy'
        else:
            raise ValueError(f'Unknown pos_type: {stop.pos_type}')
        self._add_order(date=date, symbol=pos.symbol, type=order_type, limit_price=stop.limit_price, fill_price=fill_price, shares=stop_shares)
        return (True, fill_price)

    def _trigger_bar_stop(self, stop: Stop, price_scope: PriceScope, entry: Entry) -> Optional[Decimal]:
        if stop.bars is None:
            raise ValueError('Bars not set on bar stop.')
        if entry.bars >= stop.bars:
            return price_scope.fetch(stop.symbol, PriceType.MIDDLE if stop.fill_price is None else stop.fill_price)
        return None

    def _trigger_profit_or_loss_stop(self, stop: Stop, price_scope: PriceScope) -> Optional[Decimal]:
        if stop.pos_type == 'long' and (stop.stop_type == StopType.LOSS or stop.stop_type == StopType.TRAILING) or (stop.pos_type == 'short' and stop.stop_type == StopType.PROFIT):
            if stop.exit_price is not None:
                exit_price = price_scope.fetch(stop.symbol, stop.exit_price)
                if exit_price <= self._stop_data[stop.id].value:
                    return exit_price
            else:
                low = price_scope.fetch(stop.symbol, PriceType.LOW)
                if low <= self._stop_data[stop.id].value:
                    high = price_scope.fetch(stop.symbol, PriceType.HIGH)
                    return min(self._stop_data[stop.id].value, high)
        elif stop.pos_type == 'long' and stop.stop_type == StopType.PROFIT or (stop.pos_type == 'short' and (stop.stop_type == StopType.LOSS or stop.stop_type == StopType.TRAILING)):
            if stop.exit_price is not None:
                exit_price = price_scope.fetch(stop.symbol, stop.exit_price)
                if exit_price >= self._stop_data[stop.id].value:
                    return exit_price
            else:
                high = price_scope.fetch(stop.symbol, PriceType.HIGH)
                if high >= self._stop_data[stop.id].value:
                    low = price_scope.fetch(stop.symbol, PriceType.LOW)
                    return max(self._stop_data[stop.id].value, low)
        return None

    def _trigger_trailing_stop(self, stop: Stop, price_scope: PriceScope) -> Optional[Decimal]:
        fill_price = self._trigger_profit_or_loss_stop(stop, price_scope)
        if fill_price is not None:
            return fill_price
        if stop.pos_type == 'long':
            high = price_scope.fetch(stop.symbol, PriceType.HIGH)
            amount = self._get_stop_amount(stop, high)
            self._stop_data[stop.id].value = max(high - amount, self._stop_data[stop.id].value)
        else:
            low = price_scope.fetch(stop.symbol, PriceType.LOW)
            amount = self._get_stop_amount(stop, low)
            self._stop_data[stop.id].value = min(low + amount, self._stop_data[stop.id].value)
        return None

def _clamp_shares(self, fill_price: Decimal, shares: Decimal) -> Decimal:
    if self.cash < 0:
        return Decimal()
    max_shares = Decimal(self.cash / fill_price) if self._enable_fractional_shares else Decimal(self.cash // fill_price)
    return min(shares, max_shares)

def buy(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]=None, stops: Optional[Iterable[Stop]]=None) -> Optional[Order]:
    """Places a buy order.

        Args:
            date: Date when the :class:`.Order` is placed.
            symbol: Ticker symbol to buy.
            shares: Number of shares to buy.
            fill_price: If filled, the price used to fill the :class:`.Order`.
            limit_price: Limit price of the :class:`.Order`.
            stops: :class:`.Stop`\\ s to set on the :class:`.Entry` created from
                the :class:`.Order`, if filled.

        Returns:
            :class:`.Order` if the order was filled, otherwise ``None``.
        """
    self._verify_input(shares, fill_price, limit_price)
    self._logger.debug_place_buy_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
    if limit_price is not None and limit_price < fill_price:
        return None
    if shares == 0:
        return None
    covered = self._cover(date, symbol, shares, fill_price)
    bought_shares = self._long(date, symbol, covered.rem_shares, fill_price, limit_price, stops)
    if not covered.filled_shares and (not bought_shares):
        return None
    order = self._add_order(date=date, symbol=symbol, type='buy', limit_price=limit_price, fill_price=fill_price, shares=covered.filled_shares + bought_shares)
    return order

def sell(self, date: np.datetime64, symbol: str, shares: Decimal, fill_price: Decimal, limit_price: Optional[Decimal]=None, stops: Optional[Iterable[Stop]]=None) -> Optional[Order]:
    """Places a sell order.

        Args:
            date: Date when the :class:`.Order` is placed.
            symbol: Ticker symbol to sell.
            shares: Number of shares to sell.
            fill_price: If filled, the price used to fill the :class:`.Order`.
            limit_price: Limit price of the :class:`.Order`.
            stops: :class:`.Stop`\\ s to set on the :class:`.Entry` created from
                the :class:`.Order`, if filled.

        Returns:
            :class:`.Order` if the order was filled, otherwise ``None``.
        """
    self._verify_input(shares, fill_price, limit_price)
    self._logger.debug_place_sell_order(date=date, symbol=symbol, shares=shares, fill_price=fill_price, limit_price=limit_price)
    if limit_price is not None and limit_price > fill_price:
        return None
    if shares == 0:
        return None
    sold = self._sell_existing(date, symbol, shares, fill_price)
    short_shares = self._short(date, symbol, sold.rem_shares, fill_price, stops)
    if not sold.filled_shares and (not short_shares):
        return None
    order = self._add_order(date=date, symbol=symbol, type='sell', limit_price=limit_price, fill_price=fill_price, shares=sold.filled_shares + short_shares)
    return order

def _trigger_profit_or_loss_stop(self, stop: Stop, price_scope: PriceScope) -> Optional[Decimal]:
    if stop.pos_type == 'long' and (stop.stop_type == StopType.LOSS or stop.stop_type == StopType.TRAILING) or (stop.pos_type == 'short' and stop.stop_type == StopType.PROFIT):
        if stop.exit_price is not None:
            exit_price = price_scope.fetch(stop.symbol, stop.exit_price)
            if exit_price <= self._stop_data[stop.id].value:
                return exit_price
        else:
            low = price_scope.fetch(stop.symbol, PriceType.LOW)
            if low <= self._stop_data[stop.id].value:
                high = price_scope.fetch(stop.symbol, PriceType.HIGH)
                return min(self._stop_data[stop.id].value, high)
    elif stop.pos_type == 'long' and stop.stop_type == StopType.PROFIT or (stop.pos_type == 'short' and (stop.stop_type == StopType.LOSS or stop.stop_type == StopType.TRAILING)):
        if stop.exit_price is not None:
            exit_price = price_scope.fetch(stop.symbol, stop.exit_price)
            if exit_price >= self._stop_data[stop.id].value:
                return exit_price
        else:
            high = price_scope.fetch(stop.symbol, PriceType.HIGH)
            if high >= self._stop_data[stop.id].value:
                low = price_scope.fetch(stop.symbol, PriceType.LOW)
                return max(self._stop_data[stop.id].value, low)
    return None

def _trigger_trailing_stop(self, stop: Stop, price_scope: PriceScope) -> Optional[Decimal]:
    fill_price = self._trigger_profit_or_loss_stop(stop, price_scope)
    if fill_price is not None:
        return fill_price
    if stop.pos_type == 'long':
        high = price_scope.fetch(stop.symbol, PriceType.HIGH)
        amount = self._get_stop_amount(stop, high)
        self._stop_data[stop.id].value = max(high - amount, self._stop_data[stop.id].value)
    else:
        low = price_scope.fetch(stop.symbol, PriceType.LOW)
        amount = self._get_stop_amount(stop, low)
        self._stop_data[stop.id].value = min(low + amount, self._stop_data[stop.id].value)
    return None

@njit
def lowv(array: NDArray[np.float64], n: int) -> NDArray[np.float64]:
    """Calculates the lowest values for every ``n`` period in ``array``.

    Args:
        array: :class:`numpy.ndarray` of data.
        n: Length of period.

    Returns:
        :class:`numpy.ndarray` of the lowest values for every ``n`` period in
        ``array``.
    """
    if not len(array):
        return np.array(tuple())
    _verify_input(array, n)
    out_len = len(array)
    out = np.array([np.nan for _ in range(out_len)])
    for i in range(n, out_len + 1):
        out[i - 1] = np.min(array[i - n:i])
    return out

@njit
def highv(array: NDArray[np.float64], n: int) -> NDArray[np.float64]:
    """Calculates the highest values for every ``n`` period in ``array``.

    Args:
        array: :class:`numpy.ndarray` of data.
        n: Length of period.

    Returns:
        :class:`numpy.ndarray` of the highest values for every ``n`` period in
        ``array``.
    """
    if not len(array):
        return np.array(tuple())
    _verify_input(array, n)
    out_len = len(array)
    out = np.array([np.nan for _ in range(out_len)])
    for i in range(n, out_len + 1):
        out[i - 1] = np.max(array[i - n:i])
    return out

@njit
def returnv(array: NDArray[np.float64], n: int=1) -> NDArray[np.float64]:
    """Calculates returns.

    Args:
        n: Return period. Defaults to 1.

    Returns:
        :class:`numpy.ndarray` of returns.
    """
    if not len(array):
        return np.array(tuple())
    _verify_input(array, n)
    out_len = len(array)
    out = np.array([np.nan for _ in range(out_len)])
    for i in range(n, out_len):
        out[i] = (array[i] - array[i - n]) / array[i - n]
    return out

@njit
def normal_cdf(z: float) -> float:
    """Computes the CDF of the standard normal distribution."""
    zz = np.fabs(z)
    pdf = np.exp(-0.5 * zz * zz) / np.sqrt(2 * np.pi)
    t = 1 / (1 + zz * 0.2316419)
    poly = ((((1.330274429 * t - 1.821255978) * t + 1.781477937) * t - 0.356563782) * t + 0.31938153) * t
    return 1 - pdf * poly if z > 0 else pdf * poly

@njit
def inverse_normal_cdf(p: float) -> float:
    """Computes the inverse CDF of the standard normal distribution."""
    pp = p if p <= 0.5 else 1 - p
    if pp == 0:
        pp = 1e-10
    t = np.sqrt(np.log(1 / (pp * pp)))
    numer = (0.010328 * t + 0.802853) * t + 2.515517
    denom = ((0.001308 * t + 0.189269) * t + 1.432788) * t + 1
    x = t - numer / denom
    return -x if p <= 0.5 else x

@njit
def _atr(last_bar: int, lookback: int, high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], use_log: bool=False) -> float:
    """Computes Average True Range.

    Args:
        last_bar: Index of last bar for ATR calculation.
        lookback: Number of lookback bars.
        high: High prices.
        low: Low prices.
        close: Close prices.
        use_log: Whether to log transform. Defaults to ``False``.

    Returns:
        The computed ATR.
    """
    assert last_bar >= lookback
    if lookback == 0:
        if use_log:
            return np.log(high[last_bar] / low[last_bar])
        else:
            return high[last_bar] - low[last_bar]
    total = 0.0
    for i in range(last_bar - lookback + 1, last_bar + 1):
        if use_log:
            term = high[i] / low[i]
            if high[i] / close[i - 1] > term:
                term = high[i] / close[i - 1]
            if close[i - 1] / low[i] > term:
                term = close[i - 1] / low[i]
            total += np.log(term)
        else:
            term = high[i] - low[i]
            if high[i] - close[i - 1] > term:
                term = high[i] - close[i - 1]
            if close[i - 1] - low[i] > term:
                term = close[i - 1] - low[i]
            total += term
    return total / lookback

@njit
def _variance(use_change: bool, last_bar: int, length: int, prices: NDArray[np.float64]) -> float:
    if use_change:
        assert last_bar >= length
    else:
        assert last_bar >= length - 1
    total = 0.0
    for i in range(last_bar - length + 1, last_bar + 1):
        if use_change:
            term = np.log(prices[i] / prices[i - 1])
        else:
            term = np.log(prices[i])
        total += term
    mean = total / length
    total = 0.0
    for i in range(last_bar - length + 1, last_bar + 1):
        if use_change:
            term = np.log(prices[i] / prices[i - 1]) - mean
        else:
            term = np.log(prices[i]) - mean
        total += term * term
    return total / length

@njit
def detrended_rsi(values: NDArray[np.float64], short_length: int, long_length: int, reg_length: int) -> NDArray[np.float64]:
    """Computes Detrended Relative Strength Index (RSI).

    Args:
        values: :class:`numpy.ndarray` of input.
        short_length: Lookback for the short-term RSI.
        long_length: Lookback for the long-term RSI.
        reg_length: Number of bars used for linear regressions.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    assert short_length > 0
    assert short_length <= long_length
    assert short_length > 1
    assert long_length > 1
    assert reg_length >= 1
    n = len(values)
    front_bad = long_length + reg_length - 1
    output = np.zeros(n)
    if front_bad >= n:
        return output
    work1 = np.zeros(n)
    for i in range(short_length):
        work1[i] = 1e+90
    up_sum = dn_sum = 1e-60
    for i in range(1, short_length):
        diff = values[i] - values[i - 1]
        if diff > 0.0:
            up_sum += diff
        else:
            dn_sum -= diff
    up_sum /= short_length - 1
    dn_sum /= short_length - 1
    for i in range(short_length, n):
        diff = values[i] - values[i - 1]
        if diff > 0:
            up_sum = ((short_length - 1.0) * up_sum + diff) / short_length
            dn_sum *= (short_length - 1.0) / short_length
        else:
            dn_sum = ((short_length - 1.0) * dn_sum - diff) / short_length
            up_sum *= (short_length - 1.0) / short_length
        work1[i] = 100.0 * up_sum / (up_sum + dn_sum)
        if short_length == 2:
            work1[i] = -10.0 * np.log(2.0 / (1 + 0.00999 * (2 * work1[i] - 100)) - 1)
    work2 = np.zeros(n)
    for i in range(long_length):
        work2[i] = -1e+90
    up_sum = dn_sum = 1e-60
    for i in range(1, long_length):
        diff = values[i] - values[i - 1]
        if diff > 0.0:
            up_sum += diff
        else:
            dn_sum -= diff
    up_sum /= long_length - 1
    dn_sum /= long_length - 1
    for i in range(long_length, n):
        diff = values[i] - values[i - 1]
        if diff > 0.0:
            up_sum = ((long_length - 1.0) * up_sum + diff) / long_length
            dn_sum *= (long_length - 1.0) / long_length
        else:
            dn_sum = ((long_length - 1.0) * dn_sum - diff) / long_length
            up_sum *= (long_length - 1.0) / long_length
        work2[i] = 100.0 * up_sum / (up_sum + dn_sum)
    for i in range(front_bad, n):
        x_mean = y_mean = 0.0
        for j in range(reg_length):
            k = i - j
            x_mean += work2[k]
            y_mean += work1[k]
        x_mean /= reg_length
        y_mean /= reg_length
        xss = xy = 0.0
        for j in range(reg_length):
            k = i - j
            x_diff = work2[k] - x_mean
            y_diff = work1[k] - y_mean
            xss += x_diff * x_diff
            xy += x_diff * y_diff
        coef = xy / (xss + 1e-60)
        x_diff = work2[i] - x_mean
        y_diff = work1[i] - y_mean
        output[i] = y_diff - coef * x_diff
    return output

@njit
def macd(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], short_length: int, long_length: int, smoothing: float=0.0, scale: float=1.0) -> NDArray[np.float64]:
    """Computes Moving Average Convergence Divergence.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        short_length: Short-term lookback.
        long_length: Long-term lookback.
        smoothing: Compute MACD minus smoothed if >= 2.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(high) == len(low) and len(high) == len(close)
    assert short_length > 0
    assert short_length <= long_length
    assert smoothing >= 0
    assert scale > 0
    n = len(close)
    output = np.zeros(n)
    long_alpha = 2.0 / (long_length + 1.0)
    short_alpha = 2.0 / (short_length + 1.0)
    long_sum = short_sum = close[0]
    for i in range(1, n):
        long_sum = long_alpha * close[i] + (1.0 - long_alpha) * long_sum
        short_sum = short_alpha * close[i] + (1.0 - short_alpha) * short_sum
        diff = 0.5 * (long_length - 1.0)
        diff -= 0.5 * (short_length - 1.0)
        denom = np.sqrt(np.fabs(diff))
        k = long_length + smoothing
        if k > i:
            k = i
        denom *= _atr(i, k, high, low, close, False)
        output[i] = (short_sum - long_sum) / (denom + 1e-15)
        output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
    if smoothing > 1:
        alpha = 2.0 / (smoothing + 1.0)
        smoothed = output[0]
        for i in range(1, n):
            smoothed = alpha * output[i] + (1.0 - alpha) * smoothed
            output[i] -= smoothed
    return output

@njit
def stochastic(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int, smoothing: int=0) -> NDArray[np.float64]:
    """Computes Stochastic.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        lookback: Number of lookback bars.
        smoothing: Number of times the raw stochastic is smoothed, either 0,
            1, or 2 times. Defaults to ``0``.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    assert len(high) == len(low) and len(high) == len(close)
    assert lookback > 0
    assert smoothing == 0 or smoothing == 1 or smoothing == 2
    n = len(close)
    front_bad = lookback - 1
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        min_val = 1e+60
        max_val = -1e+60
        for j in range(lookback):
            if high[i - j] > max_val:
                max_val = high[i - j]
            if low[i - j] < min_val:
                min_val = low[i - j]
        sto_0 = (close[i] - min_val) / (max_val - min_val + 1e-60)
        if smoothing == 0:
            output[i] = 100.0 * sto_0 - 50
        elif i == front_bad:
            sto_1 = sto_0
            output[i] = 100.0 * sto_0 - 50
        else:
            sto_1 = 0.33333333 * sto_0 + 0.66666667 * sto_1
            if smoothing == 1:
                output[i] = 100.0 * sto_1 - 50
            elif i == front_bad + 1:
                sto_2 = sto_1
                output[i] = 100.0 * sto_1 - 50
            else:
                sto_2 = 0.33333333 * sto_1 + 0.66666667 * sto_2
                output[i] = 100.0 * sto_2 - 50
    return output

@njit
def stochastic_rsi(values: NDArray[np.float64], rsi_lookback: int, sto_lookback: int, smoothing: float=0.0) -> NDArray[np.float64]:
    """Computes Stochastic Relative Strength Index (RSI).

    Args:
        values: :class:`numpy.ndarray` of input.
        rsi_lookback: Lookback length for RSI calculation.
        sto_lookback: Lookback length for Stochastic calculation.
        smoothing: Amount of smoothing; <= 1 for none. Defaults to ``0``.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    assert rsi_lookback > 0
    assert sto_lookback > 0
    assert smoothing >= 0
    n = len(values)
    front_bad = rsi_lookback + sto_lookback - 1
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    if rsi_lookback >= n:
        return output
    for i in range(front_bad):
        output[i] = 0
    up_sum = dn_sum = 1e-60
    for i in range(1, rsi_lookback):
        diff = values[i] - values[i - 1]
        if diff > 0.0:
            up_sum += diff
        else:
            dn_sum -= diff
    up_sum /= rsi_lookback - 1
    dn_sum /= rsi_lookback - 1
    work1 = np.zeros(n)
    for i in range(rsi_lookback, n):
        diff = values[i] - values[i - 1]
        if diff > 0.0:
            up_sum = ((rsi_lookback - 1) * up_sum + diff) / rsi_lookback
            dn_sum *= (rsi_lookback - 1.0) / rsi_lookback
        else:
            dn_sum = ((rsi_lookback - 1) * dn_sum - diff) / rsi_lookback
            up_sum *= (rsi_lookback - 1.0) / rsi_lookback
        work1[i] = 100.0 * up_sum / (up_sum + dn_sum)
    for i in range(front_bad, n):
        min_val = 1e+60
        max_val = -1e+60
        for j in range(sto_lookback):
            if work1[i - j] > max_val:
                max_val = work1[i - j]
            if work1[i - j] < min_val:
                min_val = work1[i - j]
        output[i] = 100.0 * (work1[i] - min_val) / (max_val - min_val + 1e-60) - 50.0
    if smoothing > 1:
        alpha = 2.0 / (smoothing + 1.0)
        smoothed = output[front_bad]
        for i in range(front_bad + 1, n):
            smoothed = alpha * output[i] + (1.0 - alpha) * smoothed
            output[i] = smoothed
    return output

@njit
def _legendre_1(n: int) -> NDArray[np.float64]:
    c1 = np.zeros(n)
    total = 0.0
    for i in range(n):
        c1[i] = 2.0 * i / (n - 1.0) - 1.0
        total += c1[i] * c1[i]
    total = np.sqrt(total)
    for i in range(n):
        c1[i] /= total
    return c1

@njit
def _legendre_2(n: int) -> tuple[NDArray, NDArray]:
    c1 = _legendre_1(n)
    c2 = np.zeros(n)
    total = 0.0
    for i in range(n):
        c2[i] = c1[i] * c1[i]
        total += c2[i]
    mean = total / n
    total = 0.0
    for i in range(n):
        c2[i] -= mean
        total += c2[i] * c2[i]
    total = np.sqrt(total)
    for i in range(n):
        c2[i] /= total
    return (c1, c2)

@njit
def _legendre_3(n: int) -> tuple[NDArray, NDArray, NDArray]:
    """Computes the first three Legendre polynomials.

    The first polynomial measures linear trend, the second measures the
    quadratic trend, and the third measures the cubic trend.

    Args:
        n: Length of result.

    Returns:
        Tuple of first three Legendre polynomials.
    """
    c1, c2 = _legendre_2(n)
    c3 = np.zeros(n)
    total = 0.0
    for i in range(n):
        c3[i] = c1[i] * c1[i] * c1[i]
        total += c3[i]
    mean = total / n
    total = 0.0
    for i in range(n):
        c3[i] -= mean
        total += c3[i] * c3[i]
    total = np.sqrt(total)
    for i in range(n):
        c3[i] /= total
    proj = 0.0
    for i in range(n):
        proj += c1[i] * c3[i]
    total = 0.0
    for i in range(n):
        c3[i] -= proj * c1[i]
        total += c3[i] * c3[i]
    total = np.sqrt(total)
    for i in range(n):
        c3[i] /= total
    return (c1, c2, c3)

@njit
def _trend(values: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int, atr_length: int, scale: float, trend_type: Literal['linear', 'quadratic', 'cubic']) -> NDArray[np.float64]:
    assert len(values) == len(high) and len(values) == len(low) and (len(values) == len(close))
    assert lookback > 0
    assert atr_length > 0
    assert scale > 0
    n = len(values)
    front_bad = lookback - 1 if lookback - 1 > atr_length else atr_length
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    dptr = None
    for i in range(front_bad, n):
        if trend_type == 'linear':
            dptr = _legendre_1(lookback)
        elif trend_type == 'quadratic':
            _, dptr = _legendre_2(lookback)
        else:
            _, _, dptr = _legendre_3(lookback)
        dptr_i = 0
        dot_prod = 0.0
        mean = 0.0
        for j in range(i - lookback + 1, i + 1):
            price = np.log(values[j])
            mean += price
            dot_prod += price * dptr[dptr_i]
            dptr_i += 1
        mean /= lookback
        dptr_i -= lookback
        k = lookback - 1
        if lookback == 2:
            k = 2
        denom = _atr(i, atr_length, high, low, close, True) * k
        output[i] = dot_prod * 2.0 / (denom + 1e-60)
        yss = rsq = 0.0
        for j in range(i - lookback + 1, i + 1):
            price = np.log(values[j])
            diff = price - mean
            yss += diff * diff
            pred = dot_prod * dptr[dptr_i]
            dptr_i += 1
            diff = diff - pred
            rsq += diff * diff
        rsq = 1 - rsq / (yss + 1e-60)
        if rsq < 0:
            rsq = 0
        output[i] *= rsq
        output[i] = 100 * normal_cdf(scale * output[i]) - 50
    return output

@njit
def adx(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int) -> NDArray[np.float64]:
    """Computes Average Directional Movement Index.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        lookback: Number of lookback bars.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    assert len(high) == len(low) and len(high) == len(close)
    assert lookback > 0
    n = len(close)
    output = np.zeros(n)
    if n <= 2 * lookback:
        return output
    output[0] = 0
    dms_plus = dms_minus = atr_ = 0.0
    for i in range(1, lookback + 1):
        dm_plus = high[i] - high[i - 1]
        dm_minus = low[i - 1] - low[i]
        if dm_plus >= dm_minus:
            dm_minus = 0.0
        else:
            dm_plus = 0.0
        if dm_plus < 0.0:
            dm_plus = 0.0
        if dm_minus < 0.0:
            dm_minus = 0.0
        dms_plus += dm_plus
        dms_minus += dm_minus
        term = high[i] - low[i]
        if high[i] - close[i - 1] > term:
            term = high[i] - close[i - 1]
        if close[i - 1] - low[i] > term:
            term = close[i - 1] - low[i]
        atr_ += term
        di_plus = dms_plus / (atr_ + 1e-10)
        di_minus = dms_minus / (atr_ + 1e-10)
        adx_ = np.fabs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        output[i] = 100 * adx_
    for i in range(lookback + 1, 2 * lookback):
        dm_plus = high[i] - high[i - 1]
        dm_minus = low[i - 1] - low[i]
        if dm_plus >= dm_minus:
            dm_minus = 0.0
        else:
            dm_plus = 0.0
        if dm_plus < 0.0:
            dm_plus = 0.0
        if dm_minus < 0.0:
            dm_minus = 0.0
        dms_plus = (lookback - 1.0) / lookback * dms_plus + dm_plus
        dms_minus = (lookback - 1.0) / lookback * dms_minus + dm_minus
        term = high[i] - low[i]
        if high[i] - close[i - 1] > term:
            term = high[i] - close[i - 1]
        if close[i - 1] - low[i] > term:
            term = close[i - 1] - low[i]
        atr_ = (lookback - 1.0) / lookback * atr_ + term
        di_plus = dms_plus / (atr_ + 1e-10)
        di_minus = dms_minus / (atr_ + 1e-10)
        adx_ += np.fabs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        output[i] = 100 * adx_ / (i - lookback + 1)
    adx_ /= lookback
    for i in range(2 * lookback, n):
        dm_plus = high[i] - high[i - 1]
        dm_minus = low[i - 1] - low[i]
        if dm_plus >= dm_minus:
            dm_minus = 0.0
        else:
            dm_plus = 0.0
        if dm_plus < 0.0:
            dm_plus = 0.0
        if dm_minus < 0.0:
            dm_minus = 0.0
        dms_plus = (lookback - 1.0) / lookback * dms_plus + dm_plus
        dms_minus = (lookback - 1.0) / lookback * dms_minus + dm_minus
        term = high[i] - low[i]
        if high[i] - close[i - 1] > term:
            term = high[i] - close[i - 1]
        if close[i - 1] - low[i] > term:
            term = close[i - 1] - low[i]
        atr_ = (lookback - 1.0) / lookback * atr_ + term
        di_plus = dms_plus / (atr_ + 1e-10)
        di_minus = dms_minus / (atr_ + 1e-10)
        term = np.fabs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        adx_ = (lookback - 1.0) / lookback * adx_ + term / lookback
        output[i] = 100 * adx_
    return output

@njit
def _aroon(high: NDArray[np.float64], low: NDArray[np.float64], lookback: int, aroon_type: Literal['up', 'down', 'diff']) -> NDArray[np.float64]:
    assert len(high) == len(low)
    assert lookback > 0
    n = len(high)
    output = np.zeros(n)
    if aroon_type == 'up' or aroon_type == 'down':
        output[0] = 50
    elif aroon_type == 'diff':
        output[0] = 0
    for i in range(1, n):
        if aroon_type == 'up' or aroon_type == 'diff':
            i_max = i
            x_max = high[i]
            for i in range(i - 1, i - lookback - 1, -1):
                if i < 0:
                    break
                if high[i] > x_max:
                    x_max = high[i]
                    i_max = i
        if aroon_type == 'down' or aroon_type == 'diff':
            i_min = i
            x_min = low[i]
            for i in range(i - 1, i - lookback - 1, -1):
                if i < 0:
                    break
                if low[i] < x_min:
                    x_min = low[i]
                    i_min = i
        if aroon_type == 'up':
            output[i] = 100 * (lookback - (i - i_max)) / lookback
        elif aroon_type == 'down':
            output[i] = 100 * (lookback - (i - i_min)) / lookback
        else:
            max_val = 100 * (lookback - (i - i_max)) / lookback
            min_val = 100 * (lookback - (i - i_min)) / lookback
            output[i] = max_val - min_val
    return output

@njit
def close_minus_ma(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int, atr_length: int, scale: float=1.0) -> NDArray[np.float64]:
    """Computes Close Minus Moving Average.

    Args:
        close: Close prices.
        high: High prices.
        low: Low prices.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(high) == len(low) and len(high) == len(close)
    assert lookback > 0
    assert atr_length > 0
    assert scale > 0
    n = len(close)
    front_bad = max(lookback, atr_length)
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        total = 0.0
        for j in range(i - lookback, i):
            total += np.log(close[j])
        total /= lookback
        denom = _atr(i, atr_length, high, low, close, True)
        if denom > 0.0:
            denom *= np.sqrt(lookback + 1.0)
            output[i] = (np.log(close[i]) - total) / denom
            output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
        else:
            output[i] = 0.0
    return output

@njit
def _deviation(values: NDArray[np.float64], lookback: int, scale: float, dev_type: Literal['linear', 'quadratic', 'cubic']) -> NDArray[np.float64]:
    assert lookback > 0
    assert scale > 0
    n = len(values)
    if dev_type == 'linear' and lookback < 3:
        lookback = 3
    if dev_type == 'quadratic' and lookback < 4:
        lookback = 4
    if dev_type == 'cubic' and lookback < 5:
        lookback = 5
    front_bad = lookback - 1
    if front_bad > n:
        front_bad = n
    if dev_type == 'quadratic' or dev_type == 'cubic':
        work1, work2, work3 = _legendre_3(lookback)
    else:
        work1 = _legendre_1(lookback)
    output = np.zeros(n)
    for i in range(front_bad, n):
        c0 = c1 = c2 = c3 = 0.0
        dptr = work1
        dptr_i = 0
        for j in range(i - lookback + 1, i + 1):
            price = np.log(values[j])
            c0 += price
            c1 += price * dptr[dptr_i]
            dptr_i += 1
        c0 /= lookback
        if dev_type == 'quadratic' or dev_type == 'cubic':
            dptr = work2
            dptr_i = 0
            for j in range(i - lookback + 1, i + 1):
                price = np.log(values[j])
                c2 += price * dptr[dptr_i]
                dptr_i += 1
        if dev_type == 'cubic':
            dptr = work3
            dptr_i = 0
            for j in range(i - lookback + 1, i + 1):
                price = np.log(values[j])
                c3 += price * dptr[dptr_i]
                dptr_i += 1
        j = 0
        total = 0.0
        for k in range(i - lookback + 1, i + 1):
            pred = c0 + c1 * work1[j]
            if dev_type == 'quadratic' or dev_type == 'cubic':
                pred += c2 * work2[j]
            if dev_type == 'cubic':
                pred += c3 * work3[j]
            diff = np.log(values[k]) - pred
            total += diff * diff
            j += 1
        denom = np.sqrt(total / lookback)
        if denom > 0.0:
            pred = c0 + c1 * work1[lookback - 1]
            if dev_type == 'quadratic' or dev_type == 'cubic':
                pred += c2 * work2[lookback - 1]
            if dev_type == 'cubic':
                pred += c3 * work3[lookback - 1]
            output[i] = (np.log(values[i]) - pred) / denom
            output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
        else:
            output[i] = 0.0
    return output

@njit
def price_intensity(open: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], smoothing: float=0.0, scale: float=0.8) -> NDArray[np.float64]:
    """Computes Price Intensity.

    Args:
        open: Open prices.
        high: High prices.
        low: Low prices.
        close: Close prices.
        smoothing: Amount of smoothing. Defaults to ``0``.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.8``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(open) == len(high) and len(open) == len(low) and (len(open) == len(close))
    assert smoothing >= 0
    assert scale > 0
    n = len(close)
    if smoothing < 1:
        smoothing = 1
    output = np.zeros(n)
    denom = high[0] - low[0]
    if denom < 1e-60:
        denom = 1e-60
    output[0] = (close[0] - open[0]) / denom
    for i in range(1, n):
        denom = high[i] - low[i]
        if high[i] - close[i - 1] > denom:
            denom = high[i] - close[i - 1]
        if close[i - 1] - low[i] > denom:
            denom = close[i - 1] - low[i]
        if denom < 1e-60:
            denom = 1e-60
        output[i] = (close[i] - open[i]) / denom
    if smoothing > 1:
        alpha = 2.0 / (smoothing + 1.0)
        smoothed = output[0]
        for i in range(1, n):
            smoothed = alpha * output[i] + (1.0 - alpha) * smoothed
            output[i] = smoothed
    for i in range(n):
        output[i] = 100.0 * normal_cdf(scale * np.sqrt(smoothing) * output[i]) - 50.0
    return output

@njit
def price_change_oscillator(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], short_length: int, multiplier: int, scale: float=4.0) -> NDArray[np.float64]:
    """Computes Price Change Oscillator.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        short_length: Number of short lookback bars.
        multiplier: Multiplier used to compute number of long lookback bars =
            ``multiplier * short_length``.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``4.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(high) == len(low) and len(high) == len(close)
    assert short_length > 0
    assert multiplier > 0
    assert scale > 0
    n = len(close)
    if multiplier < 2:
        multiplier = 2
    long_length = short_length * multiplier
    front_bad = long_length
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        short_sum = 0.0
        for j in range(i - short_length - 1, i + 1):
            short_sum += np.fabs(np.log(close[j] / close[j - 1]))
        long_sum = short_sum
        for j in range(i - long_length + 1, i - short_length + 1):
            long_sum += np.fabs(np.log(close[j] / close[j - 1]))
        short_sum /= short_length
        long_sum /= long_length
        denom = 0.36 + 1.0 / short_length
        v = np.log(0.5 * multiplier) / 1.609
        denom += 0.7 * v
        denom *= _atr(i, long_length, high, low, close, True)
        if denom > 1e-20:
            output[i] = (short_sum - long_sum) / denom
            output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
        else:
            output[i] = 0.0
    return output

@njit
def _flow(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, smoothing: float, flow_type: Literal['intraday', 'money_flow']) -> NDArray[np.float64]:
    assert len(high) == len(low) and len(high) == len(close) and (len(high) == len(volume))
    assert lookback > 0
    assert smoothing >= 0
    n = len(close)
    front_bad = lookback - 1
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(first_volume, n):
        if high[i] > low[i]:
            output[i] = 100.0 * (2.0 * close[i] - high[i] - low[i]) / (high[i] - low[i]) * volume[i]
        else:
            output[i] = 0.0
    if lookback > 1:
        for i in range(n - 1, front_bad - 1, -1):
            total = 0.0
            for j in range(lookback):
                total += output[i - j]
            output[i] = total / lookback
    if flow_type == 'money_flow':
        for i in range(front_bad, n):
            total = 0.0
            for j in range(lookback):
                total += volume[i - j]
            total /= lookback
            if total > 0.0:
                output[i] /= total
            else:
                output[i] = 0.0
    elif smoothing > 1:
        alpha = 2.0 / (smoothing + 1.0)
        smoothed = volume[first_volume]
        for i in range(first_volume, n):
            smoothed = alpha * volume[i] + (1.0 - alpha) * smoothed
            if smoothed > 0.0:
                output[i] /= smoothed
            else:
                output[i] = 0.0
    for i in range(front_bad):
        output[i] = 0.0
    return output

@njit
def reactivity(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, smoothing: float=0.0, scale: float=0.6) -> NDArray[np.float64]:
    """Computes Reactivity.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        smoothing: Smoothing multiplier.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(high) == len(low) and len(high) == len(close) and (len(high) == len(volume))
    assert lookback > 0
    assert smoothing >= 0
    assert scale > 0
    n = len(close)
    front_bad = lookback
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad):
        output[i] = 0.0
    alpha = 2.0 / (lookback * smoothing + 1)
    lowest = low[first_volume]
    highest = high[first_volume]
    smoothed_range = highest - lowest
    smoothed_volume = volume[first_volume]
    if smoothed_range == 0:
        return output
    if first_volume + 1 >= n or first_volume + lookback >= n:
        return output
    for i in range(first_volume + 1, first_volume + lookback):
        if high[i] > highest:
            highest = high[i]
        if low[i] < lowest:
            lowest = low[i]
        smoothed_range = alpha * (highest - lowest) + (1.0 - alpha) * smoothed_range
        smoothed_volume = alpha * volume[i] + (1.0 - alpha) * smoothed_volume
    for i in range(front_bad, n):
        lowest = low[i]
        highest = high[i]
        for j in range(1, lookback + 1):
            if high[i - j] > highest:
                highest = high[i - j]
            if low[i - j] < lowest:
                lowest = low[i - j]
        smoothed_range = alpha * (highest - lowest) + (1.0 - alpha) * smoothed_range
        smoothed_volume = alpha * volume[i] + (1.0 - alpha) * smoothed_volume
        aspect_ratio = (highest - lowest) / smoothed_range
        if volume[i] > 0.0 and smoothed_volume > 0.0:
            aspect_ratio /= volume[i] / smoothed_volume
        else:
            aspect_ratio = 1.0
        output[i] = aspect_ratio * (close[i] - close[i - lookback])
        output[i] /= smoothed_range
        output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
    return output

@njit
def price_volume_fit(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, scale: float=9.0) -> NDArray[np.float64]:
    """Computes Price Volume Fit.

    Args:
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``9.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(close) == len(volume)
    assert lookback > 0
    assert scale > 0
    n = len(close)
    front_bad = lookback - 1
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        x_mean = y_mean = 0.0
        for j in range(lookback):
            k = i - j
            x_mean += np.log(volume[k] + 1.0)
            y_mean += np.log(close[k])
        x_mean /= lookback
        y_mean /= lookback
        xss = xy = 0.0
        for j in range(lookback):
            k = i - j
            x_diff = np.log(volume[k] + 1.0) - x_mean
            y_diff = np.log(close[k]) - y_mean
            xss += x_diff * x_diff
            xy += x_diff * y_diff
        coef = xy / (xss + 1e-30)
        output[i] = 100.0 * normal_cdf(scale * coef) - 50.0
    return output

@njit
def volume_weighted_ma_ratio(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, scale: float=1.0) -> NDArray[np.float64]:
    """Computes Volume-Weighted Moving Average Ratio.

    Args:
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert len(close) == len(volume)
    assert lookback > 0
    assert scale > 0
    n = len(close)
    front_bad = lookback - 1
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        total = numer = denom = 0.0
        for j in range(i - lookback + 1, i + 1):
            numer += volume[j] * close[j]
            denom += close[j]
            total += volume[j]
        if total > 0.0:
            output[i] = 1000.0 * np.log(lookback * numer / (total * denom)) / np.sqrt(lookback)
            output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
        else:
            output[i] = 0.0
    return output

@njit
def _on_balance_volume(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, delta_length: int, scale: float, volume_type: Literal['normalized', 'delta']) -> NDArray[np.float64]:
    assert len(close) == len(volume)
    assert lookback > 0
    assert delta_length >= 0
    assert scale > 0
    n = len(close)
    front_bad = lookback
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        signed_volume = total_volume = 0.0
        for j in range(lookback):
            if close[i - j] > close[i - j - 1]:
                signed_volume += volume[i - j]
            elif close[i - j] < close[i - j - 1]:
                signed_volume -= volume[i - j]
            total_volume += volume[i - j]
        if total_volume <= 0.0:
            output[i] = 0.0
            continue
        value = signed_volume / total_volume
        value *= np.sqrt(lookback)
        output[i] = 100.0 * normal_cdf(scale * value) - 50.0
    if volume_type == 'delta':
        if delta_length < 1:
            delta_length = 1
        front_bad += delta_length
        if front_bad > n:
            front_bad = n
        for i in range(n - 1, front_bad - 1, -1):
            output[i] -= output[i - delta_length]
    return output

@njit
def _normalized_volume_index(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, scale: float, volume_type: Literal['positive', 'negative']) -> NDArray[np.float64]:
    assert len(close) == len(volume)
    assert lookback > 0
    assert scale > 0
    n = len(close)
    volatility_length = 2 * lookback
    if volatility_length < 250:
        volatility_length = 250
    front_bad = volatility_length
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    for i in range(front_bad, n):
        total = 0.0
        if volume_type == 'positive':
            for j in range(lookback):
                if volume[i - j] > volume[i - j - 1]:
                    total += np.log(close[i - j] / close[i - j - 1])
        else:
            for j in range(lookback):
                if volume[i - j] < volume[i - j - 1]:
                    total += np.log(close[i - j] / close[i - j - 1])
        total /= np.sqrt(lookback)
        denom = np.sqrt(_variance(True, i, volatility_length, close))
        if denom > 0.0:
            total /= denom
            output[i] = 100.0 * normal_cdf(scale * total) - 50.0
        else:
            output[i] = 0.0
    return output

@njit
def volume_momentum(volume: NDArray[np.float64], short_length: int, multiplier: int=2, scale: float=3.0) -> NDArray[np.float64]:
    """Computes Volume Momentum.

    Args:
        volume: Trading volume.
        short_length: Number of short lookback bars.
        multiplier: Lookback multiplier. Defaults to ``2``.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``3.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    assert short_length > 0
    assert multiplier >= 1
    assert scale > 0
    n = len(volume)
    if multiplier < 2:
        multiplier = 2
    long_length = short_length * multiplier
    front_bad = long_length - 1
    for first_volume in range(n):
        if volume[first_volume] > 0:
            break
    front_bad += first_volume
    if front_bad > n:
        front_bad = n
    output = np.zeros(n)
    denom = np.exp(np.log(multiplier) / 3.0)
    for i in range(front_bad, n):
        short_sum = 0.0
        for j in range(i - short_length + 1, i + 1):
            short_sum += volume[j]
        long_sum = short_sum
        for j in range(i - long_length + 1, i - short_length + 1):
            long_sum += volume[j]
        short_sum /= short_length
        long_sum /= long_length
        if long_sum > 0.0 and short_sum > 0.0:
            output[i] = np.log(short_sum / long_sum) / denom
            output[i] = 100.0 * normal_cdf(scale * output[i]) - 50.0
        else:
            output[i] = 0.0
    return output

@njit
def laguerre_rsi(open: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], fe_length: int=13) -> NDArray[np.float64]:
    """Computes Laguerre Relative Strength Index (RSI).

    Args:
        open: Open prices.
        high: High prices.
        low: Low prices.
        close: Close prices.
        fe_length: Fractal Energy length. Defaults to ``13``.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    assert len(open) == len(high) and len(open) == len(low) and (len(open) == len(close))
    assert fe_length > 0
    n = len(close)
    output = np.zeros(n)
    if n <= fe_length:
        return output
    alpha = np.zeros(n)
    L0_1, L1_1, L2_1, L3_1 = (0.0, 0.0, 0.0, 0.0)
    for i in range(fe_length, n):
        OC = (open[i] + close[i - 1]) / 2.0
        HC = max(high[i], close[i - 1])
        LC = min(low[i], close[i - 1])
        fe_src = (OC + HC + LC + close[i]) / 4.0
        highest = max(high[i + 1 - fe_length:i + 1])
        lowest = min(low[i + 1 - fe_length:i + 1])
        denom = highest - lowest
        if denom == 0:
            output[i] = alpha[i] = 0
            continue
        s = 0
        for i in range(fe_length):
            diff = max(high[i - i], close[i - i - 1]) - min(low[i - i], close[i - i - 1])
            s += diff / denom
        fe_alpha = np.log(s) / np.log(fe_length)
        alpha[i] = fe_alpha * 100
        L0 = fe_alpha * fe_src + (1 - fe_alpha) * L0_1
        L1 = -(1 - fe_alpha) * L0 + L0_1 + (1 - fe_alpha) * L1_1
        L2 = -(1 - fe_alpha) * L1 + L1_1 + (1 - fe_alpha) * L2_1
        L3 = -(1 - fe_alpha) * L2 + L2_1 + (1 - fe_alpha) * L3_1
        CU = (L0 - L1 if L0 >= L1 else 0) + (L1 - L2 if L1 >= L2 else 0) + (L2 - L3 if L2 >= L3 else 0)
        CD = (0 if L0 >= L1 else L1 - L0) + (0 if L1 >= L2 else L2 - L1) + (0 if L2 >= L3 else L3 - L2)
        lrsi = CU / (CU + CD) if CU + CD != 0 else 0
        output[i] = lrsi * 100
        L0_1, L1_1, L2_1, L3_1 = (L0, L1, L2, L3)
    return output

@njit
def bca_boot_conf(x: NDArray[np.float64], n: int, n_boot: int, fn: Callable[[NDArray[np.float64]], float]) -> BootConfIntervals:
    """Computes confidence intervals for a user-defined parameter using the
    `bias corrected and accelerated (BCa) bootstrap method.
    <https://blogs.sas.com/content/iml/2017/07/12/bootstrap-bca-interval.html>`_

    Args:
        x: :class:`numpy.ndarray` containing the data for the randomized
            bootstrap sampling.
        n: Number of elements in each random bootstrap sample.
        n_boot: Number of random bootstrap samples to use.
        fn: :class:`Callable` for computing the parameter used for the
            confidence intervals.

    Returns:
        :class:`.BootConfIntervals` containing the computed confidence
        intervals.
    """
    if n <= 0:
        raise ValueError('Bootstrap sample size must be greater than 0.')
    if n_boot <= 0:
        raise ValueError('Number of boostrap samples must be greater than 0.')
    n_x = len(x)
    if not n_x:
        return BootConfIntervals(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    if n_x <= n:
        n = n_x
        n_boot = 1

    def clamp(k: int):
        return min(max(k, 0), n_boot - 1)
    x_buff = np.zeros(n)
    boot = np.zeros(n_boot)
    theta_hat = fn(x[:n])
    z0_count = 0
    for i in range(n_boot):
        for j in range(n):
            k = np.random.choice(n_x)
            x_buff[j] = x[k]
        param = fn(x_buff)
        boot[i] = param
        if param < theta_hat:
            z0_count += 1
    z0_count = min(z0_count, n_boot - 1)
    z0_count = max(z0_count, 1)
    z0 = inverse_normal_cdf(z0_count / n_boot)
    theta_dot = 0.0
    for i in range(n):
        x_temp, x[i] = (x[i], x[n - 1])
        param = fn(x[:n - 1])
        theta_dot += param
        x_buff[i] = param
        x[i] = x_temp
    theta_dot /= n
    numer = denom = 0
    for i in range(n):
        diff = theta_dot - x_buff[i]
        diff_sq = diff ** 2
        denom += diff_sq
        numer += diff_sq * diff
    denom = np.power(np.sqrt(denom), 3)
    accel = numer / (6 * denom + 1e-60)
    boot.sort()
    zlo = inverse_normal_cdf(0.025)
    zhi = inverse_normal_cdf(0.975)
    alo = normal_cdf(z0 + (z0 + zlo) / (1 - accel * (z0 + zlo)))
    ahi = normal_cdf(z0 + (z0 + zhi) / (1 - accel * (z0 + zhi)))
    k = int(alo * (n_boot + 1)) - 1
    k = clamp(k)
    low_2p5 = boot[k]
    k = int((1 - ahi) * (n_boot + 1)) - 1
    k = clamp(k)
    high_2p5 = boot[n_boot - 1 - k]
    zlo = inverse_normal_cdf(0.05)
    zhi = inverse_normal_cdf(0.95)
    alo = normal_cdf(z0 + (z0 + zlo) / (1 - accel * (z0 + zlo)))
    ahi = normal_cdf(z0 + (z0 + zhi) / (1 - accel * (z0 + zhi)))
    k = int(alo * (n_boot + 1)) - 1
    k = clamp(k)
    low_5 = boot[k]
    k = int((1 - ahi) * (n_boot + 1)) - 1
    k = clamp(k)
    high_5 = boot[n_boot - 1 - k]
    zlo = inverse_normal_cdf(0.1)
    zhi = inverse_normal_cdf(0.9)
    alo = normal_cdf(z0 + (z0 + zlo) / (1 - accel * (z0 + zlo)))
    ahi = normal_cdf(z0 + (z0 + zhi) / (1 - accel * (z0 + zhi)))
    k = int(alo * (n_boot + 1)) - 1
    k = clamp(k)
    low_10 = boot[k]
    k = int((1 - ahi) * (n_boot + 1)) - 1
    k = clamp(k)
    high_10 = boot[n_boot - 1 - k]
    return BootConfIntervals(low_2p5, high_2p5, low_5, high_5, low_10, high_10)

def clamp(k: int):
    return min(max(k, 0), n_boot - 1)

def conf_profit_factor(x: NDArray[np.float64], n: int, n_boot: int) -> BootConfIntervals:
    """Computes confidence intervals for :func:`.profit_factor`."""
    intervals = bca_boot_conf(x, n, n_boot, log_profit_factor)
    return BootConfIntervals(low_2p5=np.exp(intervals.low_2p5), high_2p5=np.exp(intervals.high_2p5), low_5=np.exp(intervals.low_5), high_5=np.exp(intervals.high_5), low_10=np.exp(intervals.low_10), high_10=np.exp(intervals.high_10))

def conf_sharpe_ratio(x: NDArray[np.float64], n: int, n_boot: int, obs: Optional[int]=None) -> BootConfIntervals:
    """Computes confidence intervals for :func:`.sharpe_ratio`."""
    intervals = bca_boot_conf(x, n, n_boot, sharpe_ratio)
    if obs is not None:
        factor = np.sqrt(obs)
        intervals = BootConfIntervals(low_2p5=intervals.low_2p5 * factor, high_2p5=intervals.high_2p5 * factor, low_5=intervals.low_5 * factor, high_5=intervals.high_5 * factor, low_10=intervals.low_10 * factor, high_10=intervals.high_10 * factor)
    return intervals

@njit
def _dd_conf(q: float, boot: NDArray[np.float64]) -> float:
    k = int(q * (len(boot) + 1) - 1)
    k = max(k, 0)
    return boot[k]

@njit
def drawdown_conf(changes: NDArray[np.float64], returns: NDArray[np.float64], n: int, n_boot: int) -> DrawdownMetrics:
    """Computes upper bounds of confidence intervals for maximum drawdown using
    the bootstrap method.

    Args:
        changes: Array of differences between each bar and the previous bar.
        returns: Array of returns centered at 0.
        n: Number of elements in each random bootstrap sample.
        n_boot: Number of random bootstrap samples to use.

    Returns:
        :class:`.DrawdownMetrics` containing the confidence bounds.
    """
    if n <= 0:
        raise ValueError('Bootstrap sample size must be greater than 0.')
    if n_boot <= 0:
        raise ValueError('Number of boostrap samples must be greater than 0.')
    n_changes = len(changes)
    if n_changes != len(returns):
        raise ValueError('Param changes length does not match returns length.')
    if n_changes <= n:
        n = n_changes
        n_boot = 1
    changes_sample = np.zeros(n)
    returns_sample = np.zeros(n)
    boot_dd = np.zeros(n_boot)
    boot_dd_pct = np.zeros(n_boot)
    for i in range(n_boot):
        for j in range(n):
            k = np.random.choice(n_changes)
            changes_sample[j] = changes[k]
            returns_sample[j] = returns[k]
        boot_dd[i] = max_drawdown(changes_sample)
        boot_dd_pct[i], _ = max_drawdown_percent(returns_sample)
    return DrawdownMetrics(_dd_confs(boot_dd), _dd_confs(boot_dd_pct))

@njit
def relative_entropy(values: NDArray[np.float64]) -> float:
    """Computes the relative `entropy
    <https://en.wikipedia.org/wiki/Entropy_(information_theory)>`_.
    """
    x = values[~np.isnan(values)]
    n = len(x)
    if not n:
        return 0
    n_bins = 3
    if n >= 10000:
        n_bins = 20
    elif n >= 1000:
        n_bins = 10
    elif n >= 100:
        n_bins = 5
    min_val = float(np.min(x))
    max_val = float(np.max(x))
    factor = (n_bins - 1e-10) / (max_val - min_val + 1e-60)
    count = np.zeros(n_bins)
    for v in x:
        k = int(factor * (v - min_val))
        count[k] += 1
    sum_ = 0
    for c in count:
        if c == 0:
            continue
        p = c / n
        sum_ += p * np.log(p)
    return -sum_ / np.log(n_bins)

@njit
def ulcer_index(values: NDArray[np.float64], period: int=14) -> float:
    """Computes the
    `Ulcer Index <https://en.wikipedia.org/wiki/Ulcer_index>`_ of ``values``.
    """
    n = len(values)
    if n <= period:
        return 0
    start = period - 1
    dd = np.zeros(n - start)
    max_values = highv(values, period)
    for i in range(start, n):
        if max_values[i] == 0:
            dd[i - start] = 0
            continue
        dd[i - start] = (values[i] - max_values[i]) / max_values[i] * 100
    return np.sqrt(np.mean(np.square(dd)))

def largest_win_loss(pnls: NDArray[np.float64]) -> tuple[float, float]:
    """Computes the largest profit and largest loss of all trades.

    Args:
        pnls: Array of profits and losses (PnLs) per trade.

    Returns:
        ``tuple[float, float]`` of largest profit and largest loss.
    """
    profits = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    return (np.max(profits) if len(profits) else 0, np.min(losses) if len(losses) else 0)

@njit
def max_wins_losses(pnls: NDArray[np.float64]) -> tuple[int, int]:
    """Computes the max consecutive wins and max consecutive losses.

    Args:
        pnls: Array of profits and losses (PnLs) per trade.

    Returns:
        ``tuple[int, int]`` of max consecutive wins and max consecutive losses.
    """
    max_wins = max_losses = wins = losses = 0
    for pnl in pnls:
        if pnl > 0:
            wins += 1
            max_wins = max(max_wins, wins)
        else:
            wins = 0
        if pnl < 0:
            losses += 1
            max_losses = max(max_losses, losses)
        else:
            losses = 0
    return (max_wins, max_losses)

def annual_total_return_percent(initial_value: float, pnl: float, bars_per_year: int, total_bars: int) -> float:
    """Computes annualized total return as percentage.

    Args:
        initial_value: Initial value.
        pnl: Total profit and loss (PnL).
        bars_per_year: Number of bars per annum.
        total_bars: Total number of bars of the return.
    """
    if initial_value == 0 or total_bars == 0:
        return 0
    return (np.power((pnl + initial_value) / initial_value, bars_per_year / total_bars) - 1) * 100

@pytest.mark.parametrize('value, expected', [(1.22222, Decimal('1.22222')), (1, Decimal(1)), (30.33, Decimal('30.33')), (Decimal('10.1'), Decimal('10.1'))])
def test_to_decimal(value, expected):
    assert to_decimal(value) == expected

