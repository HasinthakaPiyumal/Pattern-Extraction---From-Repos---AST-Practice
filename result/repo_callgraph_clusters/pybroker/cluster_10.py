# Cluster 10

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

def cancel_stops(self, val: Union[str, Position, Entry], stop_type: Optional[StopType]=None):
    """Cancels :class:`pybroker.portfolio.Stop`\\ s.

        Args:
            val: Ticker symbol, :class:`pybroker.portfolio.Position`, or
                :class:`pybroker.portfolio.Entry` for which to cancel stops.
            stop_type: :class:`pybroker.common.StopType`.
        """
    self._portfolio.remove_stops(val, stop_type)

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

def _add_trade(self, type: Literal['long', 'short'], symbol: str, entry_date: np.datetime64, exit_date: np.datetime64, entry_price: Decimal, exit_price: Decimal, shares: Decimal, pnl: Decimal, return_pct: Decimal, agg_pnl: Decimal, bars: int, pnl_per_bar: Decimal, stop_type: Optional[StopType], mae: Decimal, mfe: Decimal):
    self._trade_id += 1
    trade = Trade(id=self._trade_id, type=type, symbol=symbol, entry_date=entry_date, exit_date=exit_date, entry=entry_price, exit=exit_price, shares=shares, pnl=pnl, return_pct=return_pct, agg_pnl=agg_pnl, bars=bars, pnl_per_bar=pnl_per_bar, stop=None if stop_type is None else stop_type.value, mae=mae, mfe=mfe)
    self.trades.append(trade)
    if pnl > 0:
        self._wins += 1
    self.win_rate = self._wins / len(self.trades)
    self.loss_rate = 1 - self.win_rate

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

class RandomSlippageModel(SlippageModel):
    """Implements a simple random slippage model.

    Args:
        min_pct: Min percentage of slippage.
        max_pct: Max percentage of slippage.
    """

    def __init__(self, min_pct: float, max_pct: float):
        if min_pct < 0 or min_pct > 100:
            raise ValueError('min_pct must be between 0% and 100%.')
        if max_pct < 0 or max_pct > 100:
            raise ValueError('max_pct must be between 0% and 100%.')
        if min_pct >= max_pct:
            raise ValueError('min_pct must be < max_pct.')
        self.min_pct = min_pct / 100.0
        self.max_pct = max_pct / 100.0

    def apply_slippage(self, ctx: ExecContext, buy_shares: Optional[Decimal]=None, sell_shares: Optional[Decimal]=None):
        if buy_shares or sell_shares:
            slippage_pct = Decimal(random.uniform(self.min_pct, self.max_pct))
            if buy_shares:
                ctx.buy_shares = buy_shares - slippage_pct * buy_shares
            if sell_shares:
                ctx.sell_shares = sell_shares - slippage_pct * sell_shares

def apply_slippage(self, ctx: ExecContext, buy_shares: Optional[Decimal]=None, sell_shares: Optional[Decimal]=None):
    if buy_shares or sell_shares:
        slippage_pct = Decimal(random.uniform(self.min_pct, self.max_pct))
        if buy_shares:
            ctx.buy_shares = buy_shares - slippage_pct * buy_shares
        if sell_shares:
            ctx.sell_shares = sell_shares - slippage_pct * sell_shares

class IndicatorSet(IndicatorsMixin):
    """Computes data for multiple indicators."""

    def __init__(self):
        self._ind_names: set[str] = set()

    def add(self, indicators: Union[Indicator, Iterable[Indicator]], *args):
        """Adds indicators."""
        if isinstance(indicators, Indicator):
            indicators = (indicators, *args)
        else:
            indicators = (*indicators, *args)
        self._ind_names.update(map(op.attrgetter('name'), indicators))

    def remove(self, indicators: Union[Indicator, Iterable[Indicator]], *args):
        """Removes indicators."""
        if isinstance(indicators, Indicator):
            indicators = (indicators, *args)
        else:
            indicators = (*indicators, *args)
        self._ind_names.difference_update(map(op.attrgetter('name'), indicators))

    def clear(self):
        """Removes all indicators."""
        self._ind_names.clear()

    def __call__(self, df: pd.DataFrame, disable_parallel: bool=False) -> pd.DataFrame:
        """Computes indicator data.

        Args:
            df: :class:`pandas.DataFrame` of input data.
            disable_parallel: If ``True``, indicator data is computed serially.
                If ``False``, indicator data is computed in parallel using
                multiple processes. Defaults to ``False``.

        Returns:
            :class:`pandas.DataFrame` containing the computed indicator data.
        """
        if not self._ind_names:
            raise ValueError('No indicators were added.')
        if df.empty:
            return pd.DataFrame(columns=[DataCol.DATE.value, DataCol.SYMBOL.value] + list(self._ind_names))
        syms = df[DataCol.SYMBOL.value].unique()
        ind_syms = tuple(itertools.starmap(IndicatorSymbol, itertools.product(self._ind_names, syms)))
        ind_dict = self.compute_indicators(df=df, indicator_syms=ind_syms, cache_date_fields=None, disable_parallel=disable_parallel)
        sym_dict: dict[str, dict[str, pd.Series]] = defaultdict(dict)
        for ind_sym, series in ind_dict.items():
            sym_dict[ind_sym.symbol][ind_sym.ind_name] = series
        data: dict[str, list] = defaultdict(list)
        for sym, ind_series in sym_dict.items():
            dates = df[df[DataCol.SYMBOL.value] == sym][DataCol.DATE.value]
            data[DataCol.SYMBOL.value].extend(itertools.repeat(sym, len(dates)))
            data[DataCol.DATE.value].extend(dates)
            for ind_name, series in ind_series.items():
                data[ind_name].extend(series.values)
        return pd.DataFrame.from_dict(data)

def __init__(self):
    self._ind_names: set[str] = set()

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

def _calc_drawdown_conf(self, changes: NDArray[np.float64], returns: NDArray[np.float64], sample_size: int, samples: int) -> _DrawdownResult:
    metrics = drawdown_conf(changes, returns, sample_size, samples)
    df = pd.DataFrame(zip(('99.9%', '99%', '95%', '90%'), *metrics), columns=('conf', 'amount', 'percent'))
    df.set_index('conf', inplace=True)
    return _DrawdownResult(df=df, metrics=metrics)

class TestPriceScope:

    @pytest.mark.parametrize('price, round_fill_price, expected_price', [(50, True, 50), (111.1, True, Decimal('111.1')), (np.float32(99.98), True, Decimal('99.98')), (lambda _symbol, _bar_data: 60, True, 60), (PriceType.OPEN, True, 200), (PriceType.HIGH, True, 400), (PriceType.LOW, True, 100), (PriceType.CLOSE, True, 300), (PriceType.MIDDLE, True, round(100 + (400 - 100) / 2.0, 2)), (PriceType.MIDDLE, False, 100 + (400 - 100) / 2.0), (PriceType.AVERAGE, True, round((200 + 100 + 400 + 300) / 4.0, 2))])
    def test_fetch(self, price, round_fill_price, expected_price):
        df = pd.DataFrame({'date': [np.datetime64('2020-02-03'), np.datetime64('2020-02-04'), np.datetime64('2020-02-05')], 'symbol': ['SPY'] * 3, 'open': [100, 200, 300], 'high': [500, 400, 500], 'low': [200, 100, 200], 'close': [250, 300, 400]})
        col_scope = ColumnScope(df.set_index(['symbol', 'date']))
        price_scope = PriceScope(col_scope, {'SPY': 2}, round_fill_price)
        assert price_scope.fetch('SPY', price) == expected_price

@pytest.mark.parametrize('price, round_fill_price, expected_price', [(50, True, 50), (111.1, True, Decimal('111.1')), (np.float32(99.98), True, Decimal('99.98')), (lambda _symbol, _bar_data: 60, True, 60), (PriceType.OPEN, True, 200), (PriceType.HIGH, True, 400), (PriceType.LOW, True, 100), (PriceType.CLOSE, True, 300), (PriceType.MIDDLE, True, round(100 + (400 - 100) / 2.0, 2)), (PriceType.MIDDLE, False, 100 + (400 - 100) / 2.0), (PriceType.AVERAGE, True, round((200 + 100 + 400 + 300) / 4.0, 2))])
def test_fetch(self, price, round_fill_price, expected_price):
    df = pd.DataFrame({'date': [np.datetime64('2020-02-03'), np.datetime64('2020-02-04'), np.datetime64('2020-02-05')], 'symbol': ['SPY'] * 3, 'open': [100, 200, 300], 'high': [500, 400, 500], 'low': [200, 100, 200], 'close': [250, 300, 400]})
    col_scope = ColumnScope(df.set_index(['symbol', 'date']))
    price_scope = PriceScope(col_scope, {'SPY': 2}, round_fill_price)
    assert price_scope.fetch('SPY', price) == expected_price

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

@pytest.fixture()
def col_scope(data_source_df):
    return ColumnScope(data_source_df.set_index(['symbol', 'date']))

@pytest.fixture()
def trades(dates, symbols):
    return Trade(id=1, type='long', symbol=symbols[-1], entry_date=dates[0], exit_date=dates[1], entry=100, exit=101, shares=100, pnl=Decimal(100), return_pct=Decimal(5), agg_pnl=Decimal(100), bars=1, pnl_per_bar=Decimal(100), stop=None, mae=Decimal(-10), mfe=Decimal(10))

@pytest.mark.parametrize('fill_price, limit_price', [(100, 101), (100, 100), (100, None)])
def test_buy(fill_price, limit_price):
    portfolio = Portfolio(CASH)
    order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, fill_price, limit_price)
    assert_order(order=order, date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=limit_price, fill_price=fill_price, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH - SHARES_1 * fill_price, pnl=0, symbols={SYMBOL_1}, orders=[order], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=SHARES_1, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=fill_price, type='long')
    assert not portfolio.trades

def test_buy_when_partial_filled():
    shares = Decimal(SHARES_1 - 100)
    cash = 50 + FILL_PRICE_1 * shares
    portfolio = Portfolio(cash)
    order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    assert_order(order=order, date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_1, shares=shares, fees=0)
    assert_portfolio(portfolio=portfolio, cash=cash - shares * FILL_PRICE_1, pnl=0, symbols={SYMBOL_1}, orders=[order], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=shares, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=shares, price=FILL_PRICE_1, type='long')
    assert not portfolio.trades

def test_buy_when_existing_long_position():
    portfolio = Portfolio(CASH)
    order_1 = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    order_2 = portfolio.buy(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_2, LIMIT_PRICE_1)
    assert order_1 is not None
    assert_order(order=order_2, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_2, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH - (SHARES_1 * FILL_PRICE_1 + SHARES_2 * FILL_PRICE_2), pnl=0, symbols={SYMBOL_1}, orders=[order_1, order_2], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=SHARES_1 + SHARES_2, type='long', entries_len=2)
    entry_1 = pos.entries[0]
    assert_entry(entry=entry_1, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=FILL_PRICE_1, type='long')
    entry_2 = pos.entries[1]
    assert_entry(entry=entry_2, date=DATE_2, symbol=SYMBOL_1, shares=SHARES_2, price=FILL_PRICE_2, type='long')
    assert not portfolio.trades

def test_buy_when_multiple_positions():
    portfolio = Portfolio(CASH)
    order_1 = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    order_2 = portfolio.buy(DATE_2, SYMBOL_2, SHARES_2, FILL_PRICE_2, LIMIT_PRICE_2)
    assert order_1 is not None
    assert_order(order=order_2, date=DATE_2, symbol=SYMBOL_2, type='buy', limit_price=LIMIT_PRICE_2, fill_price=FILL_PRICE_2, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH - (SHARES_1 * FILL_PRICE_1 + SHARES_2 * FILL_PRICE_2), pnl=0, symbols={SYMBOL_1, SYMBOL_2}, orders=[order_1, order_2], short_positions_len=0, long_positions_len=2)
    pos_1 = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos_1, symbol=SYMBOL_1, shares=SHARES_1, type='long', entries_len=1)
    entry_1 = pos_1.entries[0]
    assert_entry(entry=entry_1, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=FILL_PRICE_1, type='long')
    pos_2 = portfolio.long_positions[SYMBOL_2]
    assert_position(pos=pos_2, symbol=SYMBOL_2, shares=SHARES_2, type='long', entries_len=1)
    entry_2 = pos_2.entries[0]
    assert_entry(entry=entry_2, date=DATE_2, symbol=SYMBOL_2, shares=SHARES_2, price=FILL_PRICE_2, type='long')
    assert not portfolio.trades

def test_buy_when_existing_short_position():
    portfolio = Portfolio(CASH)
    short_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_1, LIMIT_PRICE_1)
    expected_pnl = SHARES_1 * (FILL_PRICE_3 - FILL_PRICE_1)
    expected_shares = SHARES_2 - SHARES_1
    assert short_order is not None
    assert buy_order is not None
    assert_order(order=buy_order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_1, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH - (SHARES_2 - SHARES_1) * FILL_PRICE_1 + expected_pnl, pnl=expected_pnl, symbols={SYMBOL_1}, orders=[short_order, buy_order], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=expected_shares, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_2, symbol=SYMBOL_1, shares=expected_shares, price=FILL_PRICE_1, type='long')
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_3, exit=FILL_PRICE_1, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_buy_when_existing_short_and_not_enough_cash():
    portfolio = Portfolio(100)
    entry_price = Decimal(5)
    entry_limit = Decimal('4.9')
    exit_price = Decimal(200)
    exit_limit = Decimal(201)
    short_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, entry_limit)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_1, exit_price, exit_limit)
    expected_pnl = (entry_price - exit_price) * SHARES_1
    assert_order(order=short_order, date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=entry_limit, fill_price=5, shares=SHARES_1, fees=0)
    assert_order(order=buy_order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=exit_limit, fill_price=exit_price, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=100 + expected_pnl, pnl=expected_pnl, symbols=set(), orders=[short_order, buy_order], short_positions_len=0, long_positions_len=0)
    assert len(portfolio.trades) == 1
    expected_return_pct = (entry_price / exit_price - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=exit_price, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=entry_price - exit_price, mfe=0)

def test_buy_when_negative_cash():
    portfolio = Portfolio(-1000)
    order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    assert order is None
    assert portfolio.cash == -1000
    assert not len(portfolio.long_positions)
    assert not len(portfolio.short_positions)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

def test_buy_when_not_filled_max_positions():
    portfolio = Portfolio(CASH, max_long_positions=1)
    order_1 = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    assert order_1 is not None
    portfolio.incr_bars()
    order_2 = portfolio.buy(DATE_2, SYMBOL_2, SHARES_2, FILL_PRICE_2, LIMIT_PRICE_2)
    assert order_1 is not None
    assert order_2 is None
    assert_portfolio(portfolio=portfolio, cash=CASH - SHARES_1 * FILL_PRICE_1, pnl=0, symbols={SYMBOL_1}, orders=[order_1], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=SHARES_1, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=FILL_PRICE_1, type='long')
    assert not portfolio.trades

def test_buy_when_not_filled_limit():
    portfolio = Portfolio(CASH)
    order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, 100, 99)
    assert order is None
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols=set(), orders=[], short_positions_len=0, long_positions_len=0)
    assert not portfolio.trades

def test_buy_when_not_filled_cash():
    portfolio = Portfolio(1)
    order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    assert order is None
    assert portfolio.cash == 1
    assert not len(portfolio.long_positions)
    assert not len(portfolio.short_positions)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

def test_buy_when_zero_shares():
    portfolio = Portfolio(CASH)
    order = portfolio.buy(DATE_1, SYMBOL_1, 0, FILL_PRICE_1, LIMIT_PRICE_1)
    assert order is None
    assert portfolio.cash == CASH
    assert not len(portfolio.short_positions)
    assert not len(portfolio.long_positions)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

@pytest.mark.parametrize('fill_price, limit_price', [(101, 100), (101, 101), (101, None)])
def test_sell_when_all_shares(fill_price, limit_price):
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, fill_price, limit_price)
    expected_pnl = (fill_price - FILL_PRICE_1) * SHARES_1
    assert buy_order is not None
    assert_order(order=sell_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=limit_price, fill_price=fill_price, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), orders=[buy_order, sell_order], short_positions_len=0, long_positions_len=0)
    assert len(portfolio.trades) == 1
    expected_return_pct = (fill_price / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=fill_price - FILL_PRICE_1)

def test_sell_when_all_shares_and_multiple_bars():
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    expected_pnl = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_1
    assert buy_order is not None
    assert_order(order=sell_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_3, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), orders=[buy_order, sell_order], short_positions_len=0, long_positions_len=0)
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_3, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=2, pnl_per_bar=expected_pnl / 2, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_sell_when_all_shares_and_fractional():
    shares = Decimal('0.34')
    portfolio = Portfolio(CASH, enable_fractional_shares=True)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, shares, FILL_PRICE_1, LIMIT_PRICE_1)
    assert_order(buy_order, date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_1, shares=shares, fees=0)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=shares, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=shares, price=FILL_PRICE_1, type='long')
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, shares, FILL_PRICE_3, LIMIT_PRICE_3)
    expected_pnl = (FILL_PRICE_3 - FILL_PRICE_1) * shares
    assert_order(order=sell_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_3, shares=shares, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), orders=[buy_order, sell_order], short_positions_len=0, long_positions_len=0)
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_3, shares=shares, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def calc_fees(fee_info):
    assert fee_info.symbol == SYMBOL_1
    assert fee_info.shares == SHARES_1
    if fee_info.order_type == 'buy':
        assert fee_info.fill_price == FILL_PRICE_1
    else:
        assert fee_info.fill_price == FILL_PRICE_3
    return Decimal('9.99')

@pytest.mark.parametrize('fee_mode, expected_buy_fees, expected_sell_fees', [(FeeMode.ORDER_PERCENT, FILL_PRICE_1 * SHARES_1 * Decimal('0.01'), FILL_PRICE_3 * SHARES_1 * Decimal('0.01')), (FeeMode.PER_SHARE, SHARES_1, SHARES_1), (FeeMode.PER_ORDER, Decimal('1'), Decimal('1')), (calc_fees, Decimal('9.99'), Decimal('9.99'))])
def test_buy_and_sell_when_fees(fee_mode, expected_buy_fees, expected_sell_fees):
    portfolio = Portfolio(CASH, fee_mode, 1)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    assert_order(order=buy_order, date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_1, shares=SHARES_1, fees=expected_buy_fees)
    assert_order(order=sell_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_3, shares=SHARES_1, fees=expected_sell_fees)
    assert portfolio.fees == expected_buy_fees + expected_sell_fees

def test_subtract_fees():
    portfolio = Portfolio(3, FeeMode.PER_ORDER, fee_amount=1, subtract_fees=True)
    order = portfolio.buy(DATE_1, SYMBOL_1, shares=1, fill_price=1)
    assert_order(order=order, date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=1, shares=1, fees=1)
    assert portfolio.cash == 1
    order = portfolio.buy(DATE_2, SYMBOL_1, shares=1, fill_price=1)
    assert_order(order=order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=1, shares=1, fees=1)
    assert portfolio.cash == -1
    order = portfolio.buy(DATE_2, SYMBOL_1, shares=1, fill_price=1)
    assert order is None
    assert portfolio.cash == -1

def test_sell_when_partial_shares():
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_2, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    expected_pnl = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_1
    expected_shares = SHARES_2 - SHARES_1
    assert buy_order is not None
    assert_order(order=sell_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_3, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH - expected_shares * FILL_PRICE_1 + expected_pnl, pnl=expected_pnl, symbols={SYMBOL_1}, orders=[buy_order, sell_order], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=expected_shares, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=expected_shares, price=FILL_PRICE_1, type='long')
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_3, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_sell_when_multiple_entries():
    portfolio = Portfolio(CASH)
    buy_order_1 = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    buy_order_2 = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_3, LIMIT_PRICE_3)
    expected_order_pnl = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_2
    expected_shares = SHARES_1 * 2 - SHARES_2
    assert buy_order_1 is not None
    assert buy_order_2 is not None
    assert_order(order=sell_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_3, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH - expected_shares * FILL_PRICE_1 + expected_order_pnl, pnl=expected_order_pnl, symbols={SYMBOL_1}, orders=[buy_order_1, buy_order_2, sell_order], short_positions_len=0, long_positions_len=1)
    pos = portfolio.long_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=expected_shares, type='long', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=expected_shares, price=FILL_PRICE_1, type='long')
    assert len(portfolio.trades) == 2
    expected_trade_pnl_1 = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_3, shares=SHARES_1, pnl=expected_trade_pnl_1, return_pct=expected_return_pct, agg_pnl=expected_trade_pnl_1, bars=1, pnl_per_bar=expected_trade_pnl_1, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)
    expected_trade_pnl_2 = (FILL_PRICE_3 - FILL_PRICE_1) * (SHARES_2 - SHARES_1)
    assert_trade(trade=portfolio.trades[1], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_3, shares=SHARES_2 - SHARES_1, pnl=expected_trade_pnl_2, return_pct=expected_return_pct, agg_pnl=expected_trade_pnl_1 + expected_trade_pnl_2, bars=1, pnl_per_bar=expected_trade_pnl_2, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_sell_when_not_filled_limit():
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, 99, 100)
    assert buy_order is not None
    assert sell_order is None
    assert_portfolio(portfolio=portfolio, cash=CASH - FILL_PRICE_1 * SHARES_1, pnl=0, symbols={SYMBOL_1}, orders=[buy_order], short_positions_len=0, long_positions_len=1)
    assert not portfolio.trades

def test_sell_when_zero_shares():
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, 0, FILL_PRICE_3, LIMIT_PRICE_3)
    assert buy_order is not None
    assert sell_order is None
    assert portfolio.cash == CASH - FILL_PRICE_1 * SHARES_1
    assert len(portfolio.long_positions) == 1
    assert not len(portfolio.short_positions)
    assert portfolio.orders == deque([buy_order])
    assert not portfolio.trades

@pytest.mark.parametrize('fill_price, limit_price', [(100, 99), (100, 100), (100, None)])
def test_short(fill_price, limit_price):
    portfolio = Portfolio(CASH)
    order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, fill_price, limit_price)
    assert_order(order=order, date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=limit_price, fill_price=fill_price, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols={SYMBOL_1}, orders=[order], long_positions_len=0, short_positions_len=1)
    pos = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=SHARES_1, type='short', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=fill_price, type='short')
    assert not portfolio.trades

def test_short_when_existing_short_position():
    portfolio = Portfolio(CASH)
    order_1 = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    order_2 = portfolio.sell(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_4, LIMIT_PRICE_3)
    assert order_1 is not None
    assert_order(order=order_2, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_4, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols={SYMBOL_1}, orders=[order_1, order_2], short_positions_len=1, long_positions_len=0)
    pos = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=SHARES_1 + SHARES_2, type='short', entries_len=2)
    entry_1 = pos.entries[0]
    assert_entry(entry=entry_1, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=FILL_PRICE_3, type='short')
    entry_2 = pos.entries[1]
    assert_entry(entry=entry_2, date=DATE_2, symbol=SYMBOL_1, shares=SHARES_2, price=FILL_PRICE_4, type='short')
    assert not portfolio.trades

def test_short_when_multiple_positions():
    portfolio = Portfolio(CASH)
    order_1 = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_1)
    portfolio.incr_bars()
    order_2 = portfolio.sell(DATE_2, SYMBOL_2, SHARES_2, FILL_PRICE_4, LIMIT_PRICE_3)
    assert order_1 is not None
    assert_order(order=order_2, date=DATE_2, symbol=SYMBOL_2, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_4, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols={SYMBOL_1, SYMBOL_2}, orders=[order_1, order_2], short_positions_len=2, long_positions_len=0)
    pos_1 = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos_1, symbol=SYMBOL_1, shares=SHARES_1, type='short', entries_len=1)
    entry_1 = pos_1.entries[0]
    assert_entry(entry=entry_1, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=FILL_PRICE_3, type='short')
    pos_2 = portfolio.short_positions[SYMBOL_2]
    assert_position(pos=pos_2, symbol=SYMBOL_2, shares=SHARES_2, type='short', entries_len=1)
    entry_2 = pos_2.entries[0]
    assert_entry(entry=entry_2, date=DATE_2, symbol=SYMBOL_2, shares=SHARES_2, price=FILL_PRICE_4, type='short')
    assert not portfolio.trades

def test_short_when_existing_long_position():
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.incr_bars()
    short_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_3, LIMIT_PRICE_3)
    expected_pnl = SHARES_1 * (FILL_PRICE_3 - FILL_PRICE_1)
    expected_shares = SHARES_2 - SHARES_1
    assert buy_order is not None
    assert short_order is not None
    assert_order(order=short_order, date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=LIMIT_PRICE_3, fill_price=FILL_PRICE_3, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_1, pnl=expected_pnl, symbols={SYMBOL_1}, orders=[buy_order, short_order], short_positions_len=1, long_positions_len=0)
    pos = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=expected_shares, type='short', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_2, symbol=SYMBOL_1, shares=expected_shares, price=FILL_PRICE_3, type='short')
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_3, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_short_when_not_filled_max_positions():
    portfolio = Portfolio(CASH, max_short_positions=1)
    order_1 = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    order_2 = portfolio.sell(DATE_2, SYMBOL_2, SHARES_2, FILL_PRICE_4, LIMIT_PRICE_3)
    assert order_1 is not None
    assert order_2 is None
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols={SYMBOL_1}, orders=[order_1], short_positions_len=1, long_positions_len=0)
    pos = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=SHARES_1, type='short', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=SHARES_1, price=FILL_PRICE_3, type='short')
    assert not portfolio.trades

def test_short_when_not_filled_limit():
    portfolio = Portfolio(CASH)
    sell_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, 99, 100)
    assert sell_order is None
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols=set(), orders=[], short_positions_len=0, long_positions_len=0)
    assert not portfolio.trades

def test_short_when_zero_shares():
    portfolio = Portfolio(CASH)
    order = portfolio.sell(DATE_1, SYMBOL_1, 0, FILL_PRICE_3, LIMIT_PRICE_3)
    assert order is None
    assert portfolio.cash == CASH
    assert not len(portfolio.short_positions)
    assert not len(portfolio.long_positions)
    assert not len(portfolio.orders)
    assert not len(portfolio.trades)

@pytest.mark.parametrize('fill_price, limit_price', [(100, 101), (100, 100), (100, None)])
def test_cover_when_all_shares(fill_price, limit_price):
    portfolio = Portfolio(CASH)
    sell_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_1, fill_price, limit_price)
    expected_pnl = (FILL_PRICE_3 - fill_price) * SHARES_1
    assert sell_order is not None
    assert_order(order=buy_order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=limit_price, fill_price=fill_price, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), orders=[sell_order, buy_order], short_positions_len=0, long_positions_len=0)
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / fill_price - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_3, exit=fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_3 - fill_price)

def test_cover_when_partial_shares():
    portfolio = Portfolio(CASH)
    sell_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_2, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    expected_pnl = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_1
    expected_shares = SHARES_2 - SHARES_1
    assert sell_order is not None
    assert_order(order=buy_order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_1, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols={SYMBOL_1}, orders=[sell_order, buy_order], short_positions_len=1, long_positions_len=0)
    pos = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=expected_shares, type='short', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=expected_shares, price=FILL_PRICE_3, type='short')
    assert len(portfolio.trades) == 1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_3, exit=FILL_PRICE_1, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_cover_when_multiple_entries():
    portfolio = Portfolio(CASH)
    sell_order_1 = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    sell_order_2 = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_1, LIMIT_PRICE_1)
    expected_order_pnl = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_2
    expected_shares = SHARES_1 * 2 - SHARES_2
    assert sell_order_1 is not None
    assert sell_order_2 is not None
    assert_order(order=buy_order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=LIMIT_PRICE_1, fill_price=FILL_PRICE_1, shares=SHARES_2, fees=0)
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_order_pnl, pnl=expected_order_pnl, symbols={SYMBOL_1}, orders=[sell_order_1, sell_order_2, buy_order], short_positions_len=1, long_positions_len=0)
    pos = portfolio.short_positions[SYMBOL_1]
    assert_position(pos=pos, symbol=SYMBOL_1, shares=expected_shares, type='short', entries_len=1)
    entry = pos.entries[0]
    assert_entry(entry=entry, date=DATE_1, symbol=SYMBOL_1, shares=expected_shares, price=FILL_PRICE_3, type='short')
    assert len(portfolio.trades) == 2
    expected_trade_pnl_1 = (FILL_PRICE_3 - FILL_PRICE_1) * SHARES_1
    expected_return_pct = (FILL_PRICE_3 / FILL_PRICE_1 - 1) * 100
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_3, exit=FILL_PRICE_1, shares=SHARES_1, pnl=expected_trade_pnl_1, return_pct=expected_return_pct, agg_pnl=expected_trade_pnl_1, bars=1, pnl_per_bar=expected_trade_pnl_1, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)
    expected_trade_pnl_2 = (FILL_PRICE_3 - FILL_PRICE_1) * (SHARES_2 - SHARES_1)
    assert_trade(trade=portfolio.trades[1], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_3, exit=FILL_PRICE_1, shares=SHARES_2 - SHARES_1, pnl=expected_trade_pnl_2, return_pct=expected_return_pct, agg_pnl=expected_trade_pnl_1 + expected_trade_pnl_2, bars=1, pnl_per_bar=expected_trade_pnl_2, stop_type=None, mae=0, mfe=FILL_PRICE_3 - FILL_PRICE_1)

def test_cover_when_not_enough_cash():
    portfolio = Portfolio(100)
    sell_fill_price = 5
    sell_limit_price = Decimal('4.9')
    buy_fill_price = Decimal(1000)
    buy_limit_price = 1001
    short_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, sell_fill_price, sell_limit_price)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_1, buy_fill_price, buy_limit_price)
    expected_pnl = (sell_fill_price - buy_fill_price) * SHARES_1
    expected_return_pct = (sell_fill_price / buy_fill_price - 1) * 100
    assert_order(order=short_order, date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=sell_limit_price, fill_price=sell_fill_price, shares=SHARES_1, fees=0)
    assert_order(order=buy_order, date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=buy_limit_price, fill_price=buy_fill_price, shares=SHARES_1, fees=0)
    assert_portfolio(portfolio=portfolio, cash=100 + expected_pnl, pnl=expected_pnl, symbols=set(), orders=[short_order, buy_order], short_positions_len=0, long_positions_len=0)
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=sell_fill_price, exit=buy_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=expected_return_pct, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=None, mae=sell_fill_price - buy_fill_price, mfe=0)

def test_cover_when_not_filled_limit():
    portfolio = Portfolio(CASH)
    sell_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, SHARES_1, 100, 99)
    assert sell_order is not None
    assert buy_order is None
    assert_portfolio(portfolio=portfolio, cash=CASH, pnl=0, symbols={SYMBOL_1}, orders=[sell_order], short_positions_len=1, long_positions_len=0)
    assert not portfolio.trades

def test_cover_when_zero_shares():
    portfolio = Portfolio(CASH)
    sell_order = portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    portfolio.incr_bars()
    buy_order = portfolio.buy(DATE_2, SYMBOL_1, 0, FILL_PRICE_1, LIMIT_PRICE_1)
    assert sell_order is not None
    assert buy_order is None
    assert portfolio.cash == CASH
    assert len(portfolio.short_positions) == 1
    assert not len(portfolio.long_positions)
    assert portfolio.orders == deque([sell_order])
    assert not len(portfolio.trades)

def test_exit_position():
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.sell(DATE_1, SYMBOL_2, SHARES_2, FILL_PRICE_3, LIMIT_PRICE_3)
    assert len(portfolio.long_positions) == 1
    assert SYMBOL_1 in portfolio.long_positions
    assert len(portfolio.short_positions) == 1
    assert SYMBOL_2 in portfolio.short_positions
    portfolio.incr_bars()
    portfolio.exit_position(DATE_2, SYMBOL_1, buy_fill_price=0, sell_fill_price=FILL_PRICE_2)
    assert not portfolio.long_positions
    assert len(portfolio.short_positions) == 1
    assert SYMBOL_2 in portfolio.short_positions
    assert len(portfolio.trades) == 1
    long_pnl = (FILL_PRICE_2 - FILL_PRICE_1) * SHARES_1
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_1, exit=FILL_PRICE_2, shares=SHARES_1, pnl=long_pnl, return_pct=(FILL_PRICE_2 / FILL_PRICE_1 - 1) * 100, bars=1, pnl_per_bar=long_pnl, agg_pnl=long_pnl, stop_type=None, mae=0, mfe=FILL_PRICE_2 - FILL_PRICE_1)
    assert len(portfolio.orders) == 3
    assert_order(order=portfolio.orders[-1], date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=FILL_PRICE_2, shares=SHARES_1, fees=0)
    portfolio.exit_position(DATE_2, SYMBOL_2, buy_fill_price=FILL_PRICE_4, sell_fill_price=0)
    assert not portfolio.long_positions
    assert not portfolio.short_positions
    assert len(portfolio.trades) == 2
    short_pnl = (FILL_PRICE_3 - FILL_PRICE_4) * SHARES_2
    assert_trade(trade=portfolio.trades[-1], type='short', symbol=SYMBOL_2, entry_date=DATE_1, exit_date=DATE_2, entry=FILL_PRICE_3, exit=FILL_PRICE_4, shares=SHARES_2, pnl=short_pnl, return_pct=(FILL_PRICE_3 / FILL_PRICE_4 - 1) * 100, bars=1, pnl_per_bar=short_pnl, agg_pnl=short_pnl + long_pnl, stop_type=None, mae=FILL_PRICE_3 - FILL_PRICE_4, mfe=0)
    assert len(portfolio.orders) == 4
    assert_order(order=portfolio.orders[-1], date=DATE_2, symbol=SYMBOL_2, type='buy', limit_price=None, fill_price=FILL_PRICE_4, shares=SHARES_2, fees=0)

def test_trigger_long_bar_stop():
    expected_fill_price = Decimal(200)
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 100], [SYMBOL_1, DATE_2, expected_fill_price]], columns=['symbol', 'date', 'close'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.BAR, pos_type='long', percent=None, points=None, bars=1, fill_price=PriceType.CLOSE, limit_price=None, exit_price=None),)
    entry_price = Decimal(100)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    expected_pnl = (expected_fill_price - entry_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(expected_fill_price / entry_price - 1) * 100, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=StopType.BAR, mae=0, mfe=expected_fill_price - entry_price)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('percent, points, expected_fill_price', [(Decimal(20), None, Decimal(160)), (None, Decimal(10), Decimal(190))])
def test_trigger_long_loss_stop(percent, points, expected_fill_price):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 300], [SYMBOL_1, DATE_2, 100, 200]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=percent, points=points, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    entry_price = Decimal(200)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    expected_pnl = (expected_fill_price - entry_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(expected_fill_price / entry_price - 1) * 100, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=StopType.LOSS, mae=expected_fill_price - entry_price, mfe=0)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('percent, points, expected_fill_price', [(Decimal(20), None, Decimal(240)), (None, Decimal(10), Decimal(210))])
def test_trigger_long_profit_stop(percent, points, expected_fill_price):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 100, 200], [SYMBOL_1, DATE_2, 200, 300]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.PROFIT, pos_type='long', percent=percent, points=points, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    entry_price = Decimal(200)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    expected_pnl = (expected_fill_price - entry_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(expected_fill_price / entry_price - 1) * 100, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=StopType.PROFIT, mae=0, mfe=expected_fill_price - entry_price)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('percent, points, expected_fill_price', [(Decimal(20), None, Decimal(200)), (None, Decimal(20), Decimal(200))])
def test_trigger_long_trailing_stop(percent, points, expected_fill_price):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 75, 100], [SYMBOL_1, DATE_2, 250, 300], [SYMBOL_1, DATE_3, 290, 295], [SYMBOL_1, DATE_4, 200, 200]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.TRAILING, pos_type='long', percent=percent, points=points, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    entry_price = Decimal(100)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    expected_pnl = (expected_fill_price - entry_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_4, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(expected_fill_price / entry_price - 1) * 100, agg_pnl=expected_pnl, bars=3, pnl_per_bar=expected_pnl / 3, stop_type=StopType.TRAILING, mae=0, mfe=expected_fill_price - entry_price)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_4, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

def test_trigger_short_bar_stop():
    expected_fill_price = Decimal(200)
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 100], [SYMBOL_1, DATE_2, expected_fill_price]], columns=['symbol', 'date', 'close'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.BAR, pos_type='short', percent=None, points=None, bars=1, fill_price=PriceType.CLOSE, limit_price=None, exit_price=None),)
    entry_price = Decimal(100)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    expected_pnl = (entry_price - expected_fill_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(entry_price / expected_fill_price - 1) * 100, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=StopType.BAR, mae=entry_price - expected_fill_price, mfe=0)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('percent, points, expected_fill_price', [(Decimal(20), None, Decimal(240)), (None, Decimal(10), Decimal(210))])
def test_trigger_short_loss_stop(percent, points, expected_fill_price):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 100, 200], [SYMBOL_1, DATE_2, 200, 300]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='short', percent=percent, points=points, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    entry_price = Decimal(200)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    expected_pnl = (entry_price - expected_fill_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(entry_price / expected_fill_price - 1) * 100, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=StopType.LOSS, mae=entry_price - expected_fill_price, mfe=0)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('percent, points, expected_fill_price', [(Decimal(20), None, Decimal(160)), (None, Decimal(10), Decimal(190))])
def test_trigger_short_profit_stop(percent, points, expected_fill_price):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 300], [SYMBOL_1, DATE_2, 100, 200]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.PROFIT, pos_type='short', percent=percent, points=points, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    entry_price = Decimal(200)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    expected_pnl = (entry_price - expected_fill_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_2, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(entry_price / expected_fill_price - 1) * 100, agg_pnl=expected_pnl, bars=1, pnl_per_bar=expected_pnl, stop_type=StopType.PROFIT, mae=0, mfe=entry_price - expected_fill_price)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('percent, points, expected_fill_price', [(Decimal(20), None, Decimal(400)), (None, Decimal(20), Decimal(400))])
def test_trigger_short_trailing_stop(percent, points, expected_fill_price):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 350, 300], [SYMBOL_1, DATE_2, 230, 200], [SYMBOL_1, DATE_3, 215, 210], [SYMBOL_1, DATE_4, 400, 400]], columns=['symbol', 'date', 'high', 'low'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.TRAILING, pos_type='short', percent=percent, points=points, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    entry_price = Decimal(300)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    expected_pnl = (entry_price - expected_fill_price) * SHARES_1
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 1
    assert_trade(trade=portfolio.trades[0], type='short', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_4, entry=entry_price, exit=expected_fill_price, shares=SHARES_1, pnl=expected_pnl, return_pct=(entry_price / expected_fill_price - 1) * 100, agg_pnl=expected_pnl, bars=3, pnl_per_bar=expected_pnl / 3, stop_type=StopType.TRAILING, mae=entry_price - expected_fill_price, mfe=0)
    assert len(portfolio.orders) == 2
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=entry_price, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_4, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=expected_fill_price, shares=SHARES_1, fees=0)

@pytest.mark.parametrize('stop_type', [StopType.LOSS, StopType.PROFIT, StopType.TRAILING])
def test_long_stop_limit_price(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 75, 200, 100], [SYMBOL_1, DATE_2, 250, 400, 300], [SYMBOL_1, DATE_3, 290, 395, 295], [SYMBOL_1, DATE_4, 200, 300, 200]], columns=['symbol', 'date', 'low', 'high', 'close'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=stop_type, pos_type='long', percent=10, points=20, bars=None, fill_price=None, limit_price=500, exit_price=None),)
    entry_price = Decimal(100)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    assert portfolio.symbols == set(['SPY'])
    assert len(portfolio.long_positions) == 1
    assert not portfolio.short_positions
    assert not portfolio.trades
    assert len(portfolio.orders) == 1

@pytest.mark.parametrize('stop_type', [StopType.LOSS, StopType.PROFIT, StopType.TRAILING])
def test_long_stop_exit_price(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 75, 200, 100], [SYMBOL_1, DATE_2, 250, 400, 300], [SYMBOL_1, DATE_3, 290, 395, 295], [SYMBOL_1, DATE_4, 200, 300, 200]], columns=['symbol', 'date', 'open', 'high', 'close'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=stop_type, pos_type='long', percent=10, points=20, bars=None, fill_price=None, limit_price=500, exit_price=PriceType.OPEN),)
    entry_price = Decimal(100)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    assert portfolio.symbols == set(['SPY'])
    assert len(portfolio.long_positions) == 1
    assert not portfolio.short_positions
    assert not portfolio.trades
    assert len(portfolio.orders) == 1

@pytest.mark.parametrize('stop_type', [StopType.LOSS, StopType.PROFIT, StopType.TRAILING])
def test_short_stop_limit_price(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 350, 300], [SYMBOL_1, DATE_2, 100, 230, 200], [SYMBOL_1, DATE_3, 110, 215, 210], [SYMBOL_1, DATE_4, 300, 400, 400]], columns=['symbol', 'date', 'low', 'high', 'close'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=stop_type, pos_type='short', percent=20, points=None, bars=None, fill_price=None, limit_price=50, exit_price=None),)
    entry_price = Decimal(300)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    assert portfolio.symbols == set(['SPY'])
    assert not portfolio.long_positions
    assert len(portfolio.short_positions) == 1
    assert not portfolio.trades
    assert len(portfolio.orders) == 1

@pytest.mark.parametrize('stop_type', [StopType.LOSS, StopType.PROFIT, StopType.TRAILING])
def test_short_stop_exit_price(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 350, 300], [SYMBOL_1, DATE_2, 100, 230, 200], [SYMBOL_1, DATE_3, 110, 215, 210], [SYMBOL_1, DATE_4, 300, 400, 400]], columns=['symbol', 'date', 'low', 'open', 'close'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=stop_type, pos_type='short', percent=20, points=None, bars=None, fill_price=None, limit_price=50, exit_price=PriceType.OPEN),)
    entry_price = Decimal(300)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    assert portfolio.symbols == set(['SPY'])
    assert not portfolio.long_positions
    assert len(portfolio.short_positions) == 1
    assert not portfolio.trades
    assert len(portfolio.orders) == 1

def test_check_stops_when_multiple_entries():
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 300], [SYMBOL_1, DATE_2, 300, 400], [SYMBOL_1, DATE_3, 200, 300], [SYMBOL_1, DATE_4, 100, 200]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    entry_price_1 = Decimal(200)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price_1, limit_price=None, stops=(Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=100, bars=None, fill_price=None, limit_price=None, exit_price=None),))
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    entry_price_2 = Decimal(300)
    portfolio.buy(DATE_2, SYMBOL_1, SHARES_2, entry_price_2, limit_price=None, stops=(Stop(id=2, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=100, bars=None, fill_price=None, limit_price=None, exit_price=None),))
    portfolio.incr_bars()
    sym_end_index[SYMBOL_1] += 1
    portfolio.check_stops(DATE_3, price_scope)
    portfolio.incr_bars()
    sym_end_index[SYMBOL_1] += 1
    portfolio.check_stops(DATE_4, price_scope)
    expected_fill_price_1 = Decimal(100)
    expected_fill_price_2 = Decimal(200)
    expected_pnl_1 = (expected_fill_price_1 - entry_price_1) * SHARES_1
    expected_pnl_2 = (expected_fill_price_2 - entry_price_2) * SHARES_2
    expected_pnl = expected_pnl_1 + expected_pnl_2
    assert_portfolio(portfolio=portfolio, cash=CASH + expected_pnl, pnl=expected_pnl, symbols=set(), short_positions_len=0, long_positions_len=0, orders=portfolio.orders)
    assert len(portfolio.trades) == 2
    assert_trade(trade=portfolio.trades[0], type='long', symbol=SYMBOL_1, entry_date=DATE_2, exit_date=DATE_3, entry=entry_price_2, exit=expected_fill_price_2, shares=SHARES_2, pnl=expected_pnl_2, return_pct=(expected_fill_price_2 / entry_price_2 - 1) * 100, agg_pnl=expected_pnl_2, bars=1, pnl_per_bar=expected_pnl_2, stop_type=StopType.LOSS, mae=expected_fill_price_1 - entry_price_1, mfe=0)
    assert_trade(trade=portfolio.trades[1], type='long', symbol=SYMBOL_1, entry_date=DATE_1, exit_date=DATE_4, entry=entry_price_1, exit=expected_fill_price_1, shares=SHARES_1, pnl=expected_pnl_1, return_pct=(expected_fill_price_1 / entry_price_1 - 1) * 100, agg_pnl=expected_pnl, bars=3, pnl_per_bar=expected_pnl_1 / 3, stop_type=StopType.LOSS, mae=expected_fill_price_2 - entry_price_2, mfe=0)
    assert len(portfolio.orders) == 4
    assert_order(order=portfolio.orders[0], date=DATE_1, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=entry_price_1, shares=SHARES_1, fees=0)
    assert_order(order=portfolio.orders[1], date=DATE_2, symbol=SYMBOL_1, type='buy', limit_price=None, fill_price=entry_price_2, shares=SHARES_2, fees=0)
    assert_order(order=portfolio.orders[2], date=DATE_3, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=expected_fill_price_2, shares=SHARES_2, fees=0)
    assert_order(order=portfolio.orders[3], date=DATE_4, symbol=SYMBOL_1, type='sell', limit_price=None, fill_price=expected_fill_price_1, shares=SHARES_1, fees=0)

def test_check_stops_when_multiple_stops_hit():
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 300], [SYMBOL_1, DATE_2, 100, 200]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 3}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, Decimal(200), limit_price=None, stops=(Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=10, bars=None, fill_price=None, limit_price=None, exit_price=None), Stop(id=2, symbol=SYMBOL_1, stop_type=StopType.TRAILING, pos_type='long', percent=None, points=20, bars=None, fill_price=None, limit_price=None, exit_price=None)))
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    assert not portfolio.symbols
    assert not portfolio.long_positions
    assert not portfolio.short_positions
    assert len(portfolio.trades) == 1
    assert len(portfolio.orders) == 2

def test_remove_stop():
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200], [SYMBOL_1, DATE_2, 100]], columns=['symbol', 'date', 'low'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=10, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, Decimal(200), limit_price=None, stops=stops)
    assert portfolio.remove_stop(1)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    assert len(portfolio.long_positions) == 1
    assert portfolio.symbols == set([SYMBOL_1])
    assert not len(portfolio.trades)

@pytest.mark.parametrize('stop_type', [StopType.LOSS, None])
def test_remove_stops_when_symbol(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200], [SYMBOL_1, DATE_2, 100]], columns=['symbol', 'date', 'low'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=10, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, Decimal(200), limit_price=None, stops=stops)
    portfolio.remove_stops('SPY', stop_type)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    assert len(portfolio.long_positions) == 1
    pos = portfolio.long_positions[SYMBOL_1]
    assert len(pos.entries) == 1
    assert not pos.entries[0].stops
    assert portfolio.symbols == set([SYMBOL_1])
    assert not len(portfolio.trades)

@pytest.mark.parametrize('stop_type', [StopType.LOSS, None])
def test_remove_stops_when_position(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200], [SYMBOL_1, DATE_2, 100]], columns=['symbol', 'date', 'low'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=10, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, Decimal(200), limit_price=None, stops=stops)
    portfolio.remove_stops(portfolio.long_positions['SPY'], stop_type)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    assert len(portfolio.long_positions) == 1
    pos = portfolio.long_positions[SYMBOL_1]
    assert len(pos.entries) == 1
    assert not pos.entries[0].stops
    assert portfolio.symbols == set([SYMBOL_1])
    assert not len(portfolio.trades)

@pytest.mark.parametrize('stop_type', [StopType.LOSS, None])
def test_remove_stops_when_entry(stop_type):
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200], [SYMBOL_1, DATE_2, 100]], columns=['symbol', 'date', 'low'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=None, points=10, bars=None, fill_price=None, limit_price=None, exit_price=None),)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, Decimal(200), limit_price=None, stops=stops)
    portfolio.remove_stops(portfolio.long_positions['SPY'].entries[0], stop_type)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    assert len(portfolio.long_positions) == 1
    pos = portfolio.long_positions[SYMBOL_1]
    assert len(pos.entries) == 1
    assert not pos.entries[0].stops
    assert portfolio.symbols == set([SYMBOL_1])
    assert not len(portfolio.trades)

def test_long_stop_when_no_pos():
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 75, 200, 100], [SYMBOL_1, DATE_2, 250, 400, 300], [SYMBOL_1, DATE_3, 290, 395, 295], [SYMBOL_1, DATE_4, 200, 300, 200]], columns=['symbol', 'date', 'open', 'high', 'close'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=10, points=20, bars=None, fill_price=None, limit_price=500, exit_price=PriceType.OPEN),)
    entry_price = Decimal(100)
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    assert len(portfolio.orders) == 2

def test_short_stop_when_no_pos():
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 350, 300], [SYMBOL_1, DATE_2, 100, 230, 200], [SYMBOL_1, DATE_3, 110, 215, 210], [SYMBOL_1, DATE_4, 300, 400, 400]], columns=['symbol', 'date', 'low', 'open', 'close'])
    df = df.set_index(['symbol', 'date'])
    sym_end_index = {SYMBOL_1: 2}
    price_scope = PriceScope(ColumnScope(df), sym_end_index, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='short', percent=20, points=None, bars=None, fill_price=None, limit_price=50, exit_price=PriceType.OPEN),)
    entry_price = Decimal(300)
    portfolio = Portfolio(CASH)
    portfolio.sell(DATE_1, SYMBOL_1, SHARES_1, entry_price, limit_price=None, stops=stops)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, entry_price)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_3, price_scope)
    sym_end_index[SYMBOL_1] += 1
    portfolio.incr_bars()
    portfolio.check_stops(DATE_4, price_scope)
    assert len(portfolio.orders) == 2

def test_capture_stops():
    df = pd.DataFrame([[SYMBOL_1, DATE_1, 200, 300], [SYMBOL_1, DATE_2, 200, 300]], columns=['symbol', 'date', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    price_scope = PriceScope(ColumnScope(df), {SYMBOL_1: len(df)}, True)
    stops = (Stop(id=1, symbol=SYMBOL_1, stop_type=StopType.LOSS, pos_type='long', percent=5, points=None, bars=None, fill_price=None, limit_price=None, exit_price=None), Stop(id=2, symbol=SYMBOL_1, stop_type=StopType.TRAILING, pos_type='long', percent=None, points=5, bars=None, fill_price=None, limit_price=Decimal(200), exit_price=None), Stop(id=3, symbol=SYMBOL_1, stop_type=StopType.BAR, pos_type='long', percent=None, points=None, bars=5, fill_price=None, limit_price=None, exit_price=Decimal(200)), Stop(id=4, symbol=SYMBOL_1, stop_type=StopType.PROFIT, pos_type='long', percent=10, points=None, bars=None, fill_price=Decimal(210), limit_price=None, exit_price=None))
    portfolio = Portfolio(CASH, record_stops=True)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, fill_price=Decimal(200), limit_price=None, stops=stops)
    portfolio.incr_bars()
    portfolio.check_stops(DATE_2, price_scope)
    stops = {stop.stop_id: stop for stop in portfolio._stop_records}
    print(portfolio._stop_records)
    assert len(stops) == 4
    assert stops[1].date == DATE_2
    assert stops[1].symbol == SYMBOL_1
    assert stops[1].stop_type == StopType.LOSS.value
    assert stops[1].pos_type == 'long'
    assert stops[1].curr_value == 190
    assert stops[1].bars is None
    assert stops[1].limit_price is None
    assert stops[1].percent == 5
    assert stops[1].points is None
    assert stops[1].curr_bars is None
    assert stops[1].exit_price is None
    assert stops[1].fill_price is None
    assert stops[2].date == DATE_2
    assert stops[2].symbol == SYMBOL_1
    assert stops[2].stop_type == StopType.TRAILING.value
    assert stops[2].pos_type == 'long'
    assert stops[2].curr_value == 295
    assert stops[2].bars is None
    assert stops[2].limit_price == 200
    assert stops[2].percent is None
    assert stops[2].points == 5
    assert stops[2].curr_bars is None
    assert stops[2].exit_price is None
    assert stops[2].fill_price is None
    assert stops[3].date == DATE_2
    assert stops[3].symbol == SYMBOL_1
    assert stops[3].stop_type == StopType.BAR.value
    assert stops[3].pos_type == 'long'
    assert stops[3].curr_value is None
    assert stops[3].bars == 5
    assert stops[3].limit_price is None
    assert stops[3].percent is None
    assert stops[3].points is None
    assert stops[3].curr_bars == 1
    assert stops[3].exit_price == 200
    assert stops[3].fill_price is None
    assert stops[4].date == DATE_2
    assert stops[4].symbol == SYMBOL_1
    assert stops[4].stop_type == StopType.PROFIT.value
    assert stops[4].pos_type == 'long'
    assert stops[4].curr_value == 220
    assert stops[4].bars is None
    assert stops[4].limit_price is None
    assert stops[4].percent == 10
    assert stops[4].points is None
    assert stops[4].curr_bars is None
    assert stops[4].exit_price is None
    assert stops[4].fill_price == 220

def test_win_loss_rate():
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    portfolio.buy(DATE_1, SYMBOL_2, SHARES_1, FILL_PRICE_3, limit_price=None)
    portfolio.incr_bars()
    portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_2, limit_price=None)
    portfolio.sell(DATE_2, SYMBOL_2, SHARES_1, FILL_PRICE_2, LIMIT_PRICE_1)
    assert len(portfolio.trades) == 2
    assert portfolio.win_rate == Decimal('0.5')
    assert portfolio.loss_rate == Decimal('0.5')

def test_incr_ids():
    portfolio = Portfolio(CASH)
    buy_order = portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1, LIMIT_PRICE_1)
    assert buy_order.id == 1
    assert list(portfolio.long_positions.values())[0].entries[0].id == 1
    sell_order = portfolio.sell(DATE_2, SYMBOL_1, SHARES_1, FILL_PRICE_3, LIMIT_PRICE_3)
    assert sell_order.id == 2
    assert portfolio.trades[0].id == 1

def test_incr_bars():
    portfolio = Portfolio(CASH)
    portfolio.buy(DATE_1, SYMBOL_1, SHARES_1, FILL_PRICE_1)
    portfolio.incr_bars()
    portfolio.buy(DATE_2, SYMBOL_1, SHARES_2, FILL_PRICE_2)
    portfolio.sell(DATE_2, SYMBOL_2, SHARES_1, FILL_PRICE_3)
    portfolio.incr_bars()
    portfolio.incr_bars()
    assert len(portfolio.long_positions) == 1
    assert len(portfolio.short_positions) == 1
    long_pos = portfolio.long_positions[SYMBOL_1]
    assert long_pos.bars == 3
    assert len(long_pos.entries) == 2
    assert long_pos.entries[0].bars == 3
    assert long_pos.entries[1].bars == 2
    short_pos = portfolio.short_positions[SYMBOL_2]
    assert short_pos.bars == 2
    assert len(short_pos.entries) == 1
    assert short_pos.entries[0].bars == 2

def test_capture_bar_when_short_position():
    cash = 100000
    fill_price = Decimal('16.72')
    shares = 100
    close_price = Decimal('16.7')
    low_price = Decimal('15.00')
    high_price = Decimal('18.00')
    portfolio = Portfolio(cash)
    portfolio.sell(DATE_1, SYMBOL_1, shares, fill_price)
    df = pd.DataFrame([[SYMBOL_1, DATE_1, close_price, low_price, high_price]], columns=['symbol', 'date', 'close', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    portfolio.capture_bar(DATE_1, df)
    pos = portfolio.short_positions[SYMBOL_1]
    assert pos.pnl == (fill_price - close_price) * shares
    assert pos.equity == 0
    assert pos.margin == close_price * shares
    assert pos.market_value == pos.margin + pos.pnl
    assert pos.close == close_price
    assert pos.entries[0].mae == fill_price - high_price
    assert pos.entries[0].mfe == fill_price - low_price
    assert len(portfolio.bars) == 1
    bar = portfolio.bars[0]
    assert bar.date == DATE_1
    assert bar.cash == cash
    assert bar.equity == bar.cash
    assert bar.margin == close_price * shares
    assert bar.pnl == 0
    assert bar.unrealized_pnl == (fill_price - close_price) * shares
    assert bar.market_value == bar.equity + bar.unrealized_pnl
    assert bar.fees == 0
    assert len(portfolio.position_bars) == 1
    pos_bar = portfolio.position_bars[0]
    assert pos_bar.symbol == SYMBOL_1
    assert pos_bar.date == DATE_1
    assert pos_bar.long_shares == 0
    assert pos_bar.short_shares == shares
    assert pos_bar.close == close_price
    assert pos_bar.equity == 0
    assert pos_bar.margin == close_price * shares
    assert pos_bar.unrealized_pnl == (fill_price - close_price) * shares
    assert pos_bar.market_value == pos_bar.margin + pos_bar.unrealized_pnl

def test_capture_bar_when_long_position():
    cash = 100000
    fill_price = Decimal('16.72')
    shares = 100
    close_price = Decimal('16.7')
    low_price = Decimal('15.00')
    high_price = Decimal('18.00')
    portfolio = Portfolio(cash)
    portfolio.buy(DATE_1, SYMBOL_1, shares, fill_price)
    df = pd.DataFrame([[SYMBOL_1, DATE_1, close_price, low_price, high_price]], columns=['symbol', 'date', 'close', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    portfolio.capture_bar(DATE_1, df)
    pos = portfolio.long_positions[SYMBOL_1]
    assert pos.pnl == (close_price - fill_price) * shares
    assert pos.equity == close_price * shares
    assert pos.margin == 0
    assert pos.market_value == pos.equity
    assert pos.close == close_price
    assert pos.entries[0].mae == low_price - fill_price
    assert pos.entries[0].mfe == high_price - fill_price
    assert len(portfolio.bars) == 1
    bar = portfolio.bars[0]
    assert bar.date == DATE_1
    assert bar.cash == cash - shares * fill_price
    assert bar.equity == cash + bar.pnl
    assert bar.margin == 0
    assert bar.pnl == (close_price - fill_price) * shares
    assert bar.market_value == bar.equity
    assert bar.fees == 0
    assert len(portfolio.position_bars) == 1
    pos_bar = portfolio.position_bars[0]
    assert pos_bar.symbol == SYMBOL_1
    assert pos_bar.date == DATE_1
    assert pos_bar.long_shares == shares
    assert pos_bar.short_shares == 0
    assert pos_bar.close == close_price
    assert pos_bar.equity == shares * close_price
    assert pos_bar.margin == 0
    assert pos_bar.unrealized_pnl == (close_price - fill_price) * shares
    assert pos_bar.market_value == pos_bar.equity

def test_mae_mfe_when_short_position():
    cash = 100000
    fill_price = Decimal('16.72')
    shares = 100
    close_price = Decimal('16.7')
    low_price = Decimal('15.00')
    high_price = Decimal('18.00')
    portfolio = Portfolio(cash)
    portfolio.sell(DATE_1, SYMBOL_1, shares, fill_price)
    df = pd.DataFrame([[SYMBOL_1, DATE_1, close_price, low_price, high_price]], columns=['symbol', 'date', 'close', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    portfolio.capture_bar(DATE_1, df)
    portfolio.buy(DATE_1, SYMBOL_1, shares, fill_price)
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0].mae == fill_price - high_price
    assert portfolio.trades[0].mfe == fill_price - low_price

def test_mae_mfe_when_long_position():
    cash = 100000
    fill_price = Decimal('16.72')
    shares = 100
    close_price = Decimal('16.7')
    low_price = Decimal('15.00')
    high_price = Decimal('18.00')
    portfolio = Portfolio(cash)
    portfolio.buy(DATE_1, SYMBOL_1, shares, fill_price)
    df = pd.DataFrame([[SYMBOL_1, DATE_1, close_price, low_price, high_price]], columns=['symbol', 'date', 'close', 'low', 'high'])
    df = df.set_index(['symbol', 'date'])
    portfolio.capture_bar(DATE_1, df)
    portfolio.sell(DATE_1, SYMBOL_1, shares, fill_price)
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0].mae == low_price - fill_price
    assert portfolio.trades[0].mfe == high_price - fill_price

def test_long_only_mode():
    cash = 100000
    portfolio = Portfolio(cash, position_mode=PositionMode.LONG_ONLY)
    portfolio.buy(DATE_1, SYMBOL_1, 100, FILL_PRICE_1)
    portfolio.sell(DATE_2, SYMBOL_1, 200, FILL_PRICE_1)
    assert not portfolio.long_positions
    assert not portfolio.short_positions
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0].shares == 100

def test_short_only_mode():
    cash = 100000
    portfolio = Portfolio(cash, position_mode=PositionMode.SHORT_ONLY)
    portfolio.sell(DATE_1, SYMBOL_1, 100, FILL_PRICE_1)
    portfolio.buy(DATE_2, SYMBOL_1, 200, FILL_PRICE_1)
    assert not portfolio.long_positions
    assert not portfolio.short_positions
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0].shares == 100

