# Cluster 12

class ExecContext(BaseContext):
    """Contains context data during the execution of a
    :class:`pybroker.strategy.Strategy`. Includes data about the current bar,
    portfolio positions, and other relevant context. This class is also used to
    set buy and sell signals for placing orders.

    The data contained in this class is for the latest bar that has already
    completed. Placing an order will be executed on a future bar specified by
    :attr:`pybroker.config.StrategyConfig.buy_delay` and
    :attr:`pybroker.config.StrategyConfig.sell_delay`.

    Attributes:
        symbol: Current ticker symbol of the execution.
        buy_fill_price: Fill price to use for a buy (long) order of
            ``symbol``.
        buy_shares: Number of shares to buy of ``symbol``.
        buy_limit_price: Limit price to use for a buy (long) order of
            ``symbol``.
        sell_fill_price: Fill price to use for a sell (short) order of
            ``symbol``.
        sell_shares: Number of shares to sell of ``symbol``.
        sell_limit_price: Limit price to use for a sell (short) order of
            ``symbol``.
        hold_bars: Number of bars to hold a long or short position for, after
            which the position is automatically liquidated.
        score: Score used to rank ``symbol`` when ranking buy and sell signals.
            Orders are placed for symbols with the highest scores, where the
            number of positions held at any time in the
            :class:`pybroker.portfolio.Portfolio` is specified by
            :attr:`pybroker.config.StrategyConfig.max_long_positions` and
            :attr:`pybroker.config.StrategyConfig.max_short_positions`
            respectively. Long and short signals are ranked separately by
            ``score``.
        session: ``dict`` used to store custom data that persists for each
            bar during the :class:`pybroker.strategy.Strategy`\\ 's execution.
        stop_loss: Sets stop loss on a new :class:`pybroker.portfolio.Entry`,
            where value is measured in points from entry price.
        stop_loss_pct: Sets stop loss on a new
            :class:`pybroker.portfolio.Entry`, where value is measured in
            percentage from entry price.
        stop_loss_limit: Limit price to use for the stop loss.
        stop_loss_exit_price: Exit :class:`pybroker.common.PriceType` to use
            for the stop loss exit. If set, the stop is checked against the
            ``exit_price`` and exits at the ``exit_price`` when triggered.
        stop_profit: Sets profit stop on a new
            :class:`pybroker.portfolio.Entry`, where value is measured in
            points from entry price.
        stop_profit_pct: Sets profit stop on a new
            :class:`pybroker.portfolio.Entry`, where value is measured in
            percentage from entry price.
        stop_profit_limit: Limit price to use for the profit stop.
        stop_profit_exit_price: Exit :class:`pybroker.common.PriceType` to use
            for the profit stop exit. If set, the stop is checked against the
            ``exit_price`` and exits at the ``exit_price`` when triggered.
        stop_trailing: Sets a trailing stop loss on a new
            :class:`pybroker.portfolio.Entry`, where value is measured in
            points from entry price.
        stop_trailing_pct: Sets a trailing stop loss on a new
            :class:`pybroker.portfolio.Entry`, where value is measured in
            percentage from entry price.
        stop_trailing_limit: Limit price to use for the trailing stop loss.
        stop_trailing_exit_price: Exit :class:`pybroker.common.PriceType` to
            use for the trailing stop exit. If set, the stop is checked against
            the ``exit_price`` and exits at the ``exit_price`` when triggered.
    """
    _stop_id: int = 0

    def __init__(self, symbol: str, config: StrategyConfig, portfolio: Portfolio, col_scope: ColumnScope, ind_scope: IndicatorScope, input_scope: ModelInputScope, pred_scope: PredictionScope, pending_order_scope: PendingOrderScope, models: Mapping[ModelSymbol, TrainedModel], sym_end_index: Mapping[str, int], session: MutableMapping):
        super().__init__(config=config, portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=models, sym_end_index=sym_end_index)
        self._scope = StaticScope.instance()
        self._curr_date: Optional[np.datetime64] = None
        self._dt: Optional[datetime] = None
        self._foreign: dict[str, pd.DataFrame] = {}
        self.symbol: str = symbol
        self.buy_fill_price: Optional[Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]] = None
        self.buy_shares: Optional[Union[int, float, Decimal]] = None
        self.buy_limit_price: Optional[Union[int, float, Decimal]] = None
        self.sell_fill_price: Optional[Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]] = None
        self.sell_shares: Optional[Union[int, float, Decimal]] = None
        self.sell_limit_price: Optional[Union[int, float, Decimal]] = None
        self.hold_bars: Optional[int] = None
        self.score: Optional[float] = None
        self.session = session
        self.stop_loss: Optional[Union[int, float, Decimal]] = None
        self.stop_loss_pct: Optional[Union[int, float, Decimal]] = None
        self.stop_loss_limit: Optional[Union[int, float, Decimal]] = None
        self.stop_loss_exit_price: Optional[PriceType] = None
        self.stop_profit: Optional[Union[int, float, Decimal]] = None
        self.stop_profit_pct: Optional[Union[int, float, Decimal]] = None
        self.stop_profit_limit: Optional[Union[int, float, Decimal]] = None
        self.stop_profit_exit_price: Optional[PriceType] = None
        self.stop_trailing: Optional[Union[int, float, Decimal]] = None
        self.stop_trailing_pct: Optional[Union[int, float, Decimal]] = None
        self.stop_trailing_limit: Optional[Union[int, float, Decimal]] = None
        self.stop_trailing_exit_price: Optional[PriceType] = None
        self._cover: bool = False
        self._exiting_pos: bool = False

    def _verify_symbol(self):
        if self.symbol is None:
            raise ValueError('symbol is not set.')

    @property
    def bars(self) -> int:
        """Number of bars of data that have completed."""
        return self._sym_end_index[self.symbol]

    @property
    def dt(self) -> datetime:
        """Current bar's date expressed as a ``datetime``."""
        if self._curr_date is None:
            raise ValueError('_curr_date is not set.')
        if self._dt is None:
            self._dt = to_datetime(self._curr_date)
        return self._dt

    @property
    def date(self) -> NDArray[np.datetime64]:
        """Current bar's date expressed as a ``numpy.datetime64``."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.DATE.value, self._sym_end_index[self.symbol])

    @property
    def open(self) -> NDArray[np.float64]:
        """Current bar's open price."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.OPEN.value, self._sym_end_index[self.symbol])

    @property
    def high(self) -> NDArray[np.float64]:
        """Current bar's high price."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.HIGH.value, self._sym_end_index[self.symbol])

    @property
    def low(self) -> NDArray[np.float64]:
        """Current bar's low price."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.LOW.value, self._sym_end_index[self.symbol])

    @property
    def close(self) -> NDArray[np.float64]:
        """Current bar's close price."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.CLOSE.value, self._sym_end_index[self.symbol])

    @property
    def volume(self) -> Optional[NDArray[np.float64]]:
        """Current bar's volume."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.VOLUME.value, self._sym_end_index[self.symbol])

    @property
    def vwap(self) -> Optional[NDArray[np.float64]]:
        """Current bar's volume-weighted average price (VWAP)."""
        self._verify_symbol()
        return self._col_scope.fetch(self.symbol, DataCol.VWAP.value, self._sym_end_index[self.symbol])

    @property
    def cover_fill_price(self) -> Optional[Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]]:
        """Alias for :attr:`.buy_fill_price`. When set, this causes the buy
        order to be placed before any sell orders.
        """
        return self.buy_fill_price

    @cover_fill_price.setter
    def cover_fill_price(self, fill_price: Optional[Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]]):
        self.buy_fill_price = fill_price
        self._cover = True

    @property
    def cover_shares(self) -> Optional[Union[int, float, Decimal]]:
        """Alias for :attr:`.buy_shares`. When set, this causes the buy
        order to be placed before any sell orders.
        """
        return self.buy_shares

    @cover_shares.setter
    def cover_shares(self, shares: Optional[Union[int, float, Decimal]]):
        self.buy_shares = shares
        self._cover = True

    @property
    def cover_limit_price(self) -> Optional[Union[int, float, Decimal]]:
        """Alias for :attr:`.buy_limit_price`. When set, this causes the buy
        order to be placed before any sell orders.
        """
        return self.buy_limit_price

    @cover_limit_price.setter
    def cover_limit_price(self, limit_price: Optional[Union[int, float, Decimal]]):
        self.buy_limit_price = limit_price
        self._cover = True

    def sell_all_shares(self):
        """Sells all long shares of :attr:`.ExecContext.symbol`."""
        pos = self.long_pos()
        if pos is None:
            raise ValueError(f'sell_all_shares failed: No long position for {self.symbol}')
        self.sell_shares = pos.shares
        self._portfolio.remove_stops(pos)
        self._exiting_pos = True

    def cover_all_shares(self):
        """Covers all short shares of :attr:`.ExecContext.symbol`."""
        pos = self.short_pos()
        if pos is None:
            raise ValueError(f'cover_all_shares failed: No short position for {self.symbol}')
        self.cover_shares = pos.shares
        self._portfolio.remove_stops(pos)
        self._exiting_pos = True

    def foreign(self, symbol: str, col: Optional[str]=None) -> Union[BarData, Optional[NDArray]]:
        """Retrieves bar data for another ticker symbol.

        Args:
            symbol: Ticker symbol of the bar data.
            col: Name of the data column to retrieve. If ``None``, all data
                columns are returned in :class:`pybroker.common.BarData`.

        Returns:
            If ``col`` is ``None``, a :class:`pybroker.common.BarData`
            instance containing data of all bars up to the current one.
            Otherwise, an :class:`numpy.ndarray` containing values of the
            column ``col``.
        """
        if symbol in self._foreign:
            return self._foreign[symbol]
        if symbol not in self._sym_end_index:
            raise ValueError(f'Symbol {symbol!r} not found.')
        end_index = self._sym_end_index[symbol]
        if col is None:
            bar_data = self._col_scope.bar_data_from_data_columns(symbol, end_index)
            self._foreign[symbol] = bar_data
            return bar_data
        else:
            return self._col_scope.fetch(symbol, col, end_index)

    def model(self, name: str, symbol: Optional[str]=None) -> Any:
        """Returns a trained model.

        Args:
            name: Name used to identify the model that was registered with
                :meth:`pybroker.model.model`.
            symbol: Ticker symbol of the data that was used to train the model.
                If ``None``, the ``ExecContext``\\ 's :attr:`.symbol` is used.

        Returns:
            Instance of the trained model.
        """
        symbol = self._get_symbol(symbol)
        return super().model(name, symbol)

    def indicator(self, name: str, symbol: Optional[str]=None) -> NDArray[np.float64]:
        """Returns indicator data.

        Args:
            name: Name used to identify the indicator, registered with
                :meth:`pybroker.indicator.indicator`.
            symbol: Ticker symbol that was used to generate the indicator data.
                If ``None``, the ``ExecContext``\\ 's :attr:`.symbol` is used.

        Returns:
            :class:`numpy.ndarray` of indicator values for all bars up to the
            current one, sorted in ascending chronological order.
        """
        symbol = self._get_symbol(symbol)
        return super().indicator(name, symbol)

    def input(self, model_name: str, symbol: Optional[str]=None) -> pd.DataFrame:
        """Returns model input data for making predictions.

        Args:
            model_name: Name of the model for the input data.
            symbol: Ticker symbol of the model for the input data. If ``None``,
                the ``ExecContext``\\ 's :attr:`.symbol` is used.

        Returns:
            :class:`pandas.DataFrame` containing the input data, where each row
            represents a bar in the sequence up to the current bar. The rows
            are sorted in ascending chronological order.
        """
        symbol = self._get_symbol(symbol)
        return super().input(model_name, symbol)

    def preds(self, model_name: str, symbol: Optional[str]=None) -> NDArray:
        """Returns model predictions.

        Args:
            model_name: Name of the model that made the predictions.
            symbol: Ticker symbol of the model that made the predictions. If
                ``None``, the ``ExecContext``\\ 's :attr:`.symbol` is used.

        Returns:
            :class:`numpy.ndarray` containing the sequence of model predictions
            up to the current bar. Sorted in ascending chronological order.
        """
        symbol = self._get_symbol(symbol)
        return super().preds(model_name, symbol)

    def long_pos(self, symbol: Optional[str]=None) -> Optional[Position]:
        """Retrieves a current long :class:`pybroker.portfolio.Position` for a
        ``symbol``.

        Args:
            symbol: Ticker symbol of the position to return. If ``None``,
                the ``ExecContext``\\ 's :attr:`.symbol` is used. Defaults to
                ``None``.

        Returns:
            :class:`pybroker.portfolio.Position` if one exists, otherwise
            ``None``.
        """
        symbol = self._get_symbol(symbol)
        return super().pos(symbol, 'long')

    def short_pos(self, symbol: Optional[str]=None) -> Optional[Position]:
        """Retrieves a current short :class:`pybroker.portfolio.Position` for
        a ``symbol``.

        Args:
            symbol: Ticker symbol of the position to return. If ``None``,
                the ``ExecContext``\\ 's :attr:`.symbol` is used. Defaults to
                ``None``.

        Returns:
            :class:`pybroker.portfolio.Position` if one exists, otherwise
            ``None``.
        """
        symbol = self._get_symbol(symbol)
        return super().pos(symbol, 'short')

    def calc_target_shares(self, target_size: float, price: Optional[float]=None, cash: Optional[float]=None) -> Union[Decimal, int]:
        """Calculates the number of shares given a ``target_size`` allocation
        and share ``price``.

        Args:
            target_size: Proportion of cash used to calculate the number of
                shares, where the max ``target_size`` is ``1``. For example, a
                ``target_size`` of ``0.1`` would represent 10% of cash.
            price: Share price used to calculate the number of shares. If
                ``None``, the share price of the ``ExecContext``\\ 's
                :attr:`.symbol` is used.
            cash: Cash used to calculate the number of number of shares. If
                ``None``, then the :class:`pybroker.portfolio.Portfolio` equity
                is used to calculate the number of shares.

        Returns:
            Number of shares given ``target_size`` and share ``price``. If
            :attr:`pybroker.config.StrategyConfig.enable_fractional_shares` is
            ``True``, then a Decimal is returned.
        """
        price = self.close[-1] if price is None else price
        return super().calc_target_shares(target_size, price, cash)

    def cancel_pending_order(self, order_id: int) -> bool:
        """Cancels a :class:`pybroker.scope.PendingOrder` with ``order_id``."""
        return self._pending_order_scope.remove(order_id)

    def cancel_all_pending_orders(self, symbol: Optional[str]=None):
        """Cancels all :class:`pybroker.scope.PendingOrder`\\ s for ``symbol``.
        When ``symbol`` is ``None``, all pending orders are canceled.
        """
        self._pending_order_scope.remove_all(symbol)

    def cancel_stop(self, stop_id: int) -> bool:
        """Cancels a :class:`pybroker.portfolio.Stop` with ``stop_id``."""
        return self._portfolio.remove_stop(stop_id)

    def cancel_stops(self, val: Union[str, Position, Entry], stop_type: Optional[StopType]=None):
        """Cancels :class:`pybroker.portfolio.Stop`\\ s.

        Args:
            val: Ticker symbol, :class:`pybroker.portfolio.Position`, or
                :class:`pybroker.portfolio.Entry` for which to cancel stops.
            stop_type: :class:`pybroker.common.StopType`.
        """
        self._portfolio.remove_stops(val, stop_type)

    def _get_symbol(self, symbol: Optional[str]=None) -> str:
        if symbol is not None:
            return symbol
        if self.symbol is None:
            raise ValueError('symbol is not set.')
        return self.symbol

    def _create_stop(self, stop_type: StopType, pos_type: Literal['long', 'short'], points: Optional[Union[int, float, Decimal]], percent: Optional[Union[int, float, Decimal]], bars: Optional[int], fill_price: Optional[Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]], limit_price: Optional[Union[int, float, Decimal]], exit_price: Optional[PriceType]):
        percent_dec, points_dec, limit_price_dec = (None, None, None)
        if stop_type != StopType.BAR:
            if percent is None and points is None:
                raise ValueError('Percent or points must be set.')
            if percent is not None:
                percent_dec = to_decimal(percent)
            elif points is not None:
                points_dec = to_decimal(points)
        if limit_price is not None:
            limit_price_dec = to_decimal(limit_price)
        if exit_price is not None and (not isinstance(exit_price, PriceType)):
            raise ValueError('Stop exit price must be a PriceType.')
        ExecContext._stop_id += 1
        return Stop(id=self._stop_id, symbol=self._get_symbol(), stop_type=stop_type, pos_type=pos_type, percent=percent_dec, points=points_dec, bars=bars, fill_price=fill_price, limit_price=limit_price_dec, exit_price=exit_price)

    def _get_stops(self) -> tuple[Optional[frozenset[Stop]], Optional[frozenset[Stop]]]:
        pos_type: Optional[Literal['long', 'short']] = None
        if self.buy_shares is not None:
            pos_type = 'long'
        elif self.sell_shares is not None:
            pos_type = 'short'
        if pos_type is None:
            return (None, None)
        stops: deque[Stop] = deque()
        if self.hold_bars is not None:
            if self.hold_bars <= 0:
                raise ValueError('hold_bars must be greater than 0.')
            if pos_type == 'long':
                fill_price = self.sell_fill_price if self.sell_fill_price is not None else PriceType.MIDDLE
            else:
                fill_price = self.buy_fill_price if self.buy_fill_price is not None else PriceType.MIDDLE
            stops.append(self._create_stop(stop_type=StopType.BAR, points=None, percent=None, bars=self.hold_bars, pos_type=pos_type, fill_price=fill_price, limit_price=None, exit_price=None))
        if self.stop_loss is not None and self.stop_loss_pct is not None:
            raise ValueError('Only one of stop_loss or stop_loss_pct can be set.')
        if self.stop_loss is not None:
            stops.append(self._create_stop(stop_type=StopType.LOSS, points=self.stop_loss, percent=None, bars=None, pos_type=pos_type, fill_price=None, limit_price=self.stop_loss_limit, exit_price=self.stop_loss_exit_price))
        elif self.stop_loss_pct is not None:
            stops.append(self._create_stop(stop_type=StopType.LOSS, points=None, percent=self.stop_loss_pct, bars=None, pos_type=pos_type, fill_price=None, limit_price=self.stop_loss_limit, exit_price=self.stop_loss_exit_price))
        if self.stop_profit is not None and self.stop_profit_pct is not None:
            raise ValueError('Only one of stop_profit or stop_profit_pct can be set.')
        if self.stop_profit is not None:
            stops.append(self._create_stop(stop_type=StopType.PROFIT, points=self.stop_profit, percent=None, bars=None, pos_type=pos_type, fill_price=None, limit_price=self.stop_profit_limit, exit_price=self.stop_profit_exit_price))
        elif self.stop_profit_pct is not None:
            stops.append(self._create_stop(stop_type=StopType.PROFIT, points=None, percent=self.stop_profit_pct, bars=None, pos_type=pos_type, fill_price=None, limit_price=self.stop_profit_limit, exit_price=self.stop_profit_exit_price))
        if self.stop_trailing is not None and self.stop_trailing_pct is not None:
            raise ValueError('Only one of stop_trailing or stop_trailing_pct can be set.')
        if self.stop_trailing is not None:
            stops.append(self._create_stop(stop_type=StopType.TRAILING, points=self.stop_trailing, percent=None, bars=None, pos_type=pos_type, fill_price=None, limit_price=self.stop_trailing_limit, exit_price=self.stop_trailing_exit_price))
        elif self.stop_trailing_pct is not None:
            stops.append(self._create_stop(stop_type=StopType.TRAILING, points=None, percent=self.stop_trailing_pct, bars=None, pos_type=pos_type, fill_price=None, limit_price=self.stop_trailing_limit, exit_price=self.stop_trailing_exit_price))
        if self.stop_loss_limit is not None and self.stop_loss is None and (self.stop_loss_pct is None):
            raise ValueError('Either stop_loss or stop_loss_pct must be set when stop_loss_limit is set.')
        if self.stop_loss_exit_price is not None and self.stop_loss is None and (self.stop_loss_pct is None):
            raise ValueError('Either stop_loss or stop_loss_pct must be set when stop_loss_exit_price is set.')
        if self.stop_profit_limit is not None and self.stop_profit is None and (self.stop_profit_pct is None):
            raise ValueError('Either stop_profit or stop_profit_pct must be set when stop_profit_limit is set.')
        if self.stop_profit_exit_price is not None and self.stop_profit is None and (self.stop_profit_pct is None):
            raise ValueError('Either stop_profit or stop_profit_pct must be set when stop_profit_exit_price is set.')
        if self.stop_trailing_limit is not None and self.stop_trailing is None and (self.stop_trailing_pct is None):
            raise ValueError('Either stop_trailing or stop_trailing_pct must be set when stop_trailing_limit is set.')
        if self.stop_trailing_exit_price is not None and self.stop_trailing is None and (self.stop_trailing_pct is None):
            raise ValueError('Either stop_trailing or stop_trailing_pct must be set when stop_trailing_exit_price is set.')
        if pos_type == 'long':
            return (frozenset(stops), None)
        else:
            return (None, frozenset(stops))

    def to_result(self) -> Optional[ExecResult]:
        """Creates an :class:`.ExecResult` from the data set on
        :class:`.ExecContext`.
        """
        if self._curr_date is None:
            raise ValueError('curr_date is not set.')
        if self.symbol is None:
            raise ValueError('symbol is not set.')
        if self.buy_shares is None:
            if self.buy_limit_price is not None:
                raise ValueError('buy_shares must be set when buy_limit_price is set.')
            if self.buy_fill_price is not None and self.hold_bars is None:
                raise ValueError('buy_shares or hold_bars must be set when buy_fill_price is set.')
        if self.sell_shares is None:
            if self.sell_limit_price is not None:
                raise ValueError('sell_shares must be set when sell_limit_price is set.')
            if self.sell_fill_price is not None and self.hold_bars is None:
                raise ValueError('sell_shares or hold_bars must be set when sell_fill_price is set.')
        if self.buy_shares is None and self.sell_shares is None:
            if self.stop_loss is not None or self.stop_loss_pct is not None or self.stop_loss_limit is not None or (self.stop_profit is not None) or (self.stop_profit_pct is not None) or (self.stop_profit_limit is not None) or (self.stop_trailing is not None) or (self.stop_trailing_pct is not None) or (self.stop_trailing_limit is not None):
                raise ValueError('Either buy_shares or sell_shares must be set when a stop is set.')
            if self.hold_bars is not None:
                raise ValueError('Either buy_shares or sell_shares must be set when hold_bars is set.')
        if self.buy_shares is not None and self.sell_shares is not None:
            raise ValueError('For each symbol, only one of buy_shares or sell_shares can be set per bar.')
        if not self.buy_shares and (not self.sell_shares):
            return None
        buy_fill_price = self.buy_fill_price if self.buy_fill_price is not None else PriceType.MIDDLE
        sell_fill_price = self.sell_fill_price if self.sell_fill_price is not None else PriceType.MIDDLE
        buy_shares = to_decimal(self.buy_shares) if self.buy_shares is not None else None
        buy_limit_price = to_decimal(self.buy_limit_price) if self.buy_limit_price is not None else None
        sell_limit_price = to_decimal(self.sell_limit_price) if self.sell_limit_price is not None else None
        sell_shares = to_decimal(self.sell_shares) if self.sell_shares is not None else None
        long_stops, short_stops = self._get_stops()
        return ExecResult(symbol=self.symbol, date=self._curr_date, buy_fill_price=buy_fill_price, sell_fill_price=sell_fill_price, score=self.score, hold_bars=self.hold_bars, buy_shares=buy_shares, buy_limit_price=buy_limit_price, sell_shares=sell_shares, sell_limit_price=sell_limit_price, long_stops=long_stops, short_stops=short_stops, cover=self._cover)

    def __getattr__(self, attr):
        if attr in self._scope.custom_data_cols:
            if self.symbol is None:
                raise ValueError('symbol is not set.')
            return self._col_scope.fetch(self.symbol, attr, self._sym_end_index[self.symbol])
        raise AttributeError(f'Attribute {attr!r} not found.')

def calc_target_shares(self, target_size: float, price: Optional[float]=None, cash: Optional[float]=None) -> Union[Decimal, int]:
    """Calculates the number of shares given a ``target_size`` allocation
        and share ``price``.

        Args:
            target_size: Proportion of cash used to calculate the number of
                shares, where the max ``target_size`` is ``1``. For example, a
                ``target_size`` of ``0.1`` would represent 10% of cash.
            price: Share price used to calculate the number of shares. If
                ``None``, the share price of the ``ExecContext``\\ 's
                :attr:`.symbol` is used.
            cash: Cash used to calculate the number of number of shares. If
                ``None``, then the :class:`pybroker.portfolio.Portfolio` equity
                is used to calculate the number of shares.

        Returns:
            Number of shares given ``target_size`` and share ``price``. If
            :attr:`pybroker.config.StrategyConfig.enable_fractional_shares` is
            ``True``, then a Decimal is returned.
        """
    price = self.close[-1] if price is None else price
    return super().calc_target_shares(target_size, price, cash)

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

def incr_bars(self):
    """Increments the number of bars held by every trade entry."""
    for pos in itertools.chain(self.long_positions.values(), self.short_positions.values()):
        pos.bars += 1
        for entry in pos.entries:
            entry.bars += 1

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

@pytest.fixture()
def ctx(col_scope, ind_scope, input_scope, pred_scope, pending_order_scope):
    return ExecContext(symbol='SPY', config=None, portfolio=None, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models={}, sym_end_index={}, session={})

@pytest.fixture()
def ind_scope(ind_data, dates):
    return IndicatorScope(ind_data, dates)

@pytest.fixture()
def input_scope(col_scope, ind_scope, trained_models):
    return ModelInputScope(col_scope, ind_scope, trained_models)

@pytest.fixture()
def pending_order_scope(pending_orders):
    scope = PendingOrderScope()
    for order in pending_orders:
        scope.add(type=order.type, symbol=order.symbol, created=order.created, exec_date=order.exec_date, shares=order.shares, limit_price=order.limit_price, fill_price=order.fill_price)
    return scope

@pytest.fixture()
def ctx(col_scope, ind_scope, input_scope, pred_scope, pending_order_scope, portfolio, trained_models, sym_end_index, session, symbol, date):
    ctx = ExecContext(symbol=symbol, config=StrategyConfig(max_long_positions=5), portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=trained_models, sym_end_index=sym_end_index, session=session)
    set_exec_ctx_data(ctx, date)
    return ctx

@pytest.fixture()
def ctx_with_pos(col_scope, ind_scope, input_scope, pred_scope, pending_order_scope, portfolio, trained_models, sym_end_index, session, symbol, symbols, date):
    portfolio.long_positions = {sym: Position(sym, 200, 'long') for sym in symbols}
    portfolio.short_positions = {sym: Position(sym, 100, 'short') for sym in symbols}
    ctx = ExecContext(symbol=symbol, config=StrategyConfig(max_long_positions=5), portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=trained_models, sym_end_index=sym_end_index, session=session)
    set_exec_ctx_data(ctx, date)
    return ctx

@pytest.fixture()
def ctx_with_orders(col_scope, ind_scope, input_scope, pred_scope, pending_order_scope, portfolio, trained_models, sym_end_index, session, symbol, date, orders, trades):
    portfolio.orders = deque(orders)
    portfolio.trades = deque(trades)
    portfolio.win_rate = 1
    portfolio.lose_rate = 0
    ctx = ExecContext(symbol=symbol, config=StrategyConfig(max_long_positions=5), portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=trained_models, sym_end_index=sym_end_index, session=session)
    set_exec_ctx_data(ctx, date)
    return ctx

def test_calc_target_shares(ctx):
    assert ctx.calc_target_shares(0.5, 33.5) == 50000 // 33.5

def test_calc_target_shares_when_enable_fractional_shares(col_scope, ind_scope, input_scope, pred_scope, pending_order_scope, portfolio, trained_models, sym_end_index, session, symbol):
    ctx = ExecContext(symbol=symbol, config=StrategyConfig(enable_fractional_shares=True), portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=trained_models, sym_end_index=sym_end_index, session=session)
    assert ctx.calc_target_shares(0.5, 33.5) == Decimal('50_000') / Decimal('33.5')

def test_calc_target_shares_with_cash(ctx):
    assert ctx.calc_target_shares(1 / 3, 20, 10000) == 166

def test_calc_target_shares_when_negative_then_zero(ctx):
    assert ctx.calc_target_shares(1, 20, -2000) == 0

def test_set_exec_ctx_data(ctx, sym_end_index):
    date = np.datetime64('2020-01-01')
    ctx._foreign = {'SPY': np.random.rand(100)}
    ctx._cover = True
    ctx._exiting_pos = True
    ctx.buy_fill_price = PriceType.AVERAGE
    ctx.buy_shares = 100
    ctx.buy_limit_price = 99
    ctx.sell_fill_price = PriceType.CLOSE
    ctx.sell_shares = 200
    ctx.sell_limit_price = 80
    ctx.hold_bars = 5
    ctx.score = 45.5
    ctx.stop_loss = 10
    ctx.stop_loss_pct = 20
    ctx.stop_loss_limit = 99
    ctx.stop_profit = 20
    ctx.stop_profit_pct = 30
    ctx.stop_profit_limit = 99.99
    ctx.stop_trailing = 100
    ctx.stop_trailing_pct = 15
    ctx.stop_trailing_limit = 80.8
    set_exec_ctx_data(ctx, date)
    assert ctx.dt == to_datetime(date)
    assert ctx.bars == sym_end_index[ctx.symbol]
    assert not ctx._foreign
    assert ctx._cover is False
    assert ctx._exiting_pos is False
    assert ctx.buy_fill_price is None
    assert ctx.buy_shares is None
    assert ctx.buy_limit_price is None
    assert ctx.sell_fill_price is None
    assert ctx.sell_shares is None
    assert ctx.sell_limit_price is None
    assert ctx.hold_bars is None
    assert ctx.score is None
    assert ctx.stop_loss is None
    assert ctx.stop_loss_pct is None
    assert ctx.stop_loss_limit is None
    assert ctx.stop_profit is None
    assert ctx.stop_profit_pct is None
    assert ctx.stop_profit_limit is None
    assert ctx.stop_trailing is None
    assert ctx.stop_trailing_pct is None
    assert ctx.stop_trailing_limit is None

