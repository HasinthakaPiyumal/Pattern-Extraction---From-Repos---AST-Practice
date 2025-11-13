# Cluster 0

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

def pending_orders(self, symbol: Optional[str]=None) -> Iterator[PendingOrder]:
    for order in self._pending_order_scope.orders(symbol):
        yield order

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

def cancel_pending_order(self, order_id: int) -> bool:
    """Cancels a :class:`pybroker.scope.PendingOrder` with ``order_id``."""
    return self._pending_order_scope.remove(order_id)

def cancel_all_pending_orders(self, symbol: Optional[str]=None):
    """Cancels all :class:`pybroker.scope.PendingOrder`\\ s for ``symbol``.
        When ``symbol`` is ``None``, all pending orders are canceled.
        """
    self._pending_order_scope.remove_all(symbol)

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

def _to_day_ids(self, days: Optional[Union[str, Day, Iterable[Union[str, Day]]]]) -> Optional[tuple[int]]:
    if days is None:
        return None
    days = (days,) if isinstance(days, str) or isinstance(days, Day) else days
    return tuple(sorted((day.value if isinstance(day, Day) else Day[day.upper()].value for day in set(days))))

class YFinance(DataSource):
    """Retrieves data from `Yahoo Finance <https://finance.yahoo.com/>`_\\ .

    Args:
        auto_adjust: Whether to auto adjust close prices. If ``True``, then
            adjusted close prices are stored in the ``close`` column. Defaults
            to ``False``.

    Attributes:
        ADJ_CLOSE: Column name of adjusted close prices.
    """
    ADJ_CLOSE: Final = 'adj_close'
    __TIMEFRAME: Final = '1d'

    def __init__(self, auto_adjust: bool=False):
        super().__init__()
        self.auto_adjust = auto_adjust
        self._scope.register_custom_cols(self.ADJ_CLOSE)

    def query(self, symbols: Union[str, Iterable[str]], start_date: Union[str, datetime], end_date: Union[str, datetime], _timeframe: Optional[str]='', _adjust: Optional[Any]=None) -> pd.DataFrame:
        """Queries data from `Yahoo Finance <https://finance.yahoo.com/>`_\\ .
        The timeframe of the data is limited to per day only.

        Args:
            symbols: Ticker symbols of the data to query.
            start_date: Start date of the data to query (inclusive).
            end_date: End date of the data to query (inclusive).

        Returns:
            :class:`pandas.DataFrame` containing the queried data.
        """
        return super().query(symbols, start_date, end_date, self.__TIMEFRAME, _adjust)

    def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, _timeframe: Optional[str], _adjust: Optional[Any]) -> pd.DataFrame:
        """:meta private:"""
        show_yf_progress_bar = not self._logger._disabled and (not self._logger._progress_bar_disabled)
        df = yfinance.download(list(symbols), start=start_date, end=end_date, progress=show_yf_progress_bar, auto_adjust=self.auto_adjust)
        if df.columns.empty:
            columns = [DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value]
            if not self.auto_adjust:
                columns.append(self.ADJ_CLOSE)
            return pd.DataFrame(columns=columns)
        if df.empty:
            return df
        df = df.reset_index()
        result = pd.DataFrame()
        if len(symbols) == 1:
            result[DataCol.DATE.value] = df['Date'].values
            result[DataCol.SYMBOL.value] = tuple(itertools.repeat(next(iter(symbols)), len(df['Close'].values)))
            result[DataCol.OPEN.value] = df['Open'].values
            result[DataCol.HIGH.value] = df['High'].values
            result[DataCol.LOW.value] = df['Low'].values
            result[DataCol.CLOSE.value] = df['Close'].values
            result[DataCol.VOLUME.value] = df['Volume'].values
            if not self.auto_adjust:
                result[self.ADJ_CLOSE] = df['Adj Close'].values
        else:
            df.columns = df.columns.to_flat_index()
            for sym in symbols:
                sym_df = pd.DataFrame()
                sym_df[DataCol.DATE.value] = df['Date', ''].values
                sym_df[DataCol.SYMBOL.value] = tuple(itertools.repeat(sym, len(df['Close', sym].values)))
                sym_df[DataCol.OPEN.value] = df['Open', sym].values
                sym_df[DataCol.HIGH.value] = df['High', sym].values
                sym_df[DataCol.LOW.value] = df['Low', sym].values
                sym_df[DataCol.CLOSE.value] = df['Close', sym].values
                sym_df[DataCol.VOLUME.value] = df['Volume', sym].values
                if not self.auto_adjust:
                    sym_df[self.ADJ_CLOSE] = df['Adj Close', sym].values
                result = pd.concat((result, sym_df))
        return result

def _fetch_data(self, symbols: frozenset[str], start_date: datetime, end_date: datetime, _timeframe: Optional[str], _adjust: Optional[Any]) -> pd.DataFrame:
    """:meta private:"""
    show_yf_progress_bar = not self._logger._disabled and (not self._logger._progress_bar_disabled)
    df = yfinance.download(list(symbols), start=start_date, end=end_date, progress=show_yf_progress_bar, auto_adjust=self.auto_adjust)
    if df.columns.empty:
        columns = [DataCol.SYMBOL.value, DataCol.DATE.value, DataCol.OPEN.value, DataCol.HIGH.value, DataCol.LOW.value, DataCol.CLOSE.value, DataCol.VOLUME.value]
        if not self.auto_adjust:
            columns.append(self.ADJ_CLOSE)
        return pd.DataFrame(columns=columns)
    if df.empty:
        return df
    df = df.reset_index()
    result = pd.DataFrame()
    if len(symbols) == 1:
        result[DataCol.DATE.value] = df['Date'].values
        result[DataCol.SYMBOL.value] = tuple(itertools.repeat(next(iter(symbols)), len(df['Close'].values)))
        result[DataCol.OPEN.value] = df['Open'].values
        result[DataCol.HIGH.value] = df['High'].values
        result[DataCol.LOW.value] = df['Low'].values
        result[DataCol.CLOSE.value] = df['Close'].values
        result[DataCol.VOLUME.value] = df['Volume'].values
        if not self.auto_adjust:
            result[self.ADJ_CLOSE] = df['Adj Close'].values
    else:
        df.columns = df.columns.to_flat_index()
        for sym in symbols:
            sym_df = pd.DataFrame()
            sym_df[DataCol.DATE.value] = df['Date', ''].values
            sym_df[DataCol.SYMBOL.value] = tuple(itertools.repeat(sym, len(df['Close', sym].values)))
            sym_df[DataCol.OPEN.value] = df['Open', sym].values
            sym_df[DataCol.HIGH.value] = df['High', sym].values
            sym_df[DataCol.LOW.value] = df['Low', sym].values
            sym_df[DataCol.CLOSE.value] = df['Close', sym].values
            sym_df[DataCol.VOLUME.value] = df['Volume', sym].values
            if not self.auto_adjust:
                sym_df[self.ADJ_CLOSE] = df['Adj Close', sym].values
            result = pd.concat((result, sym_df))
    return result

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

def remove_stop(self, stop_id: int) -> bool:
    """Removes a :class:`.Stop` with ``stop_id``."""
    if stop_id in self._stop_data:
        stop_data = self._stop_data[stop_id]
        del self._stop_data[stop_id]
        if stop_data.stop in stop_data.entry.stops:
            stop_data.entry.stops.remove(stop_data.stop)
        return True
    return False

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

class ModelSource:
    """Base class of a model source. A model source provides a model instance
    either by training one or by loading a pre-trained model.

    Args:
        name: Name of model.
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
        kwargs: ``dict`` of additional kwargs.
    """

    def __init__(self, name: str, indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
        self.name = name
        self.indicators = tuple(indicator_names)
        self._input_data_fn = input_data_fn
        self._predict_fn = predict_fn
        self._kwargs = kwargs

    def prepare_input_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepares a :class:`pandas.DataFrame` of input data for passing to a
        model when making predictions. If set, the ``input_data_fn``
        is used to preprocess the input data. If ``False``, then indicator
        columns in ``df`` are used as input features.
        """
        if df.empty:
            return df
        if self._input_data_fn is None:
            df_cols = frozenset(df.columns)
            for ind_name in self.indicators:
                if ind_name not in df_cols:
                    raise ValueError(f'Indicator {ind_name!r} not found in DataFrame.')
            return df[[*self.indicators]]
        return self._input_data_fn(df)

def __init__(self, name: str, indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
    self.name = name
    self.indicators = tuple(indicator_names)
    self._input_data_fn = input_data_fn
    self._predict_fn = predict_fn
    self._kwargs = kwargs

class TestPendingOrderScope:

    def test_remove(self, pending_orders, pending_order_scope):
        assert pending_order_scope.remove(pending_orders[0].id)
        orders = tuple(pending_order_scope.orders())
        assert len(orders) == 1
        assert orders[0] == pending_orders[1]
        assert not pending_order_scope.contains(1)
        assert pending_order_scope.contains(2)

    def test_remove_all(self, pending_order_scope):
        pending_order_scope.remove_all()
        assert not tuple(pending_order_scope.orders())
        assert not pending_order_scope.contains(1)
        assert not pending_order_scope.contains(2)

    def test_remove_all_when_symbol(self, pending_orders, pending_order_scope):
        pending_order_scope.remove_all('AAPL')
        orders = tuple(pending_order_scope.orders())
        assert len(orders) == 1
        assert orders[0] == pending_orders[0]
        assert not pending_order_scope.contains(2)
        assert pending_order_scope.contains(1)

    def test_contains(self, pending_order_scope):
        assert pending_order_scope.contains(1)
        assert not pending_order_scope.contains(3)

    def test_orders(self, pending_orders, pending_order_scope):
        assert tuple(pending_order_scope.orders()) == pending_orders
        assert tuple(pending_order_scope.orders('SPY')) == tuple([pending_orders[0]])
        assert not tuple(pending_order_scope.orders('FOO'))

def test_remove(self, pending_orders, pending_order_scope):
    assert pending_order_scope.remove(pending_orders[0].id)
    orders = tuple(pending_order_scope.orders())
    assert len(orders) == 1
    assert orders[0] == pending_orders[1]
    assert not pending_order_scope.contains(1)
    assert pending_order_scope.contains(2)

def test_remove_all(self, pending_order_scope):
    pending_order_scope.remove_all()
    assert not tuple(pending_order_scope.orders())
    assert not pending_order_scope.contains(1)
    assert not pending_order_scope.contains(2)

def test_remove_all_when_symbol(self, pending_orders, pending_order_scope):
    pending_order_scope.remove_all('AAPL')
    orders = tuple(pending_order_scope.orders())
    assert len(orders) == 1
    assert orders[0] == pending_orders[0]
    assert not pending_order_scope.contains(2)
    assert pending_order_scope.contains(1)

def test_contains(self, pending_order_scope):
    assert pending_order_scope.contains(1)
    assert not pending_order_scope.contains(3)

def test_orders(self, pending_orders, pending_order_scope):
    assert tuple(pending_order_scope.orders()) == pending_orders
    assert tuple(pending_order_scope.orders('SPY')) == tuple([pending_orders[0]])
    assert not tuple(pending_order_scope.orders('FOO'))

def pos_size_handler(ctx):
    signals = tuple(ctx.signals())
    ctx.set_shares(signals[0], shares=1000)
    ctx.set_shares(signals[1], shares=2000)
    assert isinstance(ctx.sessions['SPY'], dict)
    assert isinstance(ctx.sessions['AAPL'], dict)

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

def pos_size_handler(ctx):
    signals = tuple(ctx.signals())
    ctx.set_shares(signals[0], shares=10)
    ctx.set_shares(signals[1], shares=20)
    assert isinstance(ctx.sessions['SPY'], dict)
    assert isinstance(ctx.sessions['AAPL'], dict)

def sell_exec_fn(ctx):
    ctx.sell_fill_price = 100
    ctx.sell_limit_price = 200
    ctx.sell_shares = 100

def exec_fn_1(ctx):
    assert len(ctx.indicator(llv_ind.name))

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

def exec_fn(ctx):
    pass

def buy_exec_fn(ctx):
    ctx.buy_shares = 100

def sell_exec_fn(ctx):
    ctx.sell_shares = 100

def pos_size_handler(ctx):
    signals = tuple(ctx.signals())
    ctx.set_shares(signals[0], shares=0)
    ctx.set_shares(signals[1], shares=0)

def before_exec_fn(ctxs):
    assert len(ctxs) == 2
    assert isinstance(ctxs['SPY'], ExecContext)
    assert isinstance(ctxs['AAPL'], ExecContext)
    if not ctxs['AAPL'].long_pos():
        ctxs['AAPL'].buy_shares = 200

def after_exec_fn(ctxs):
    assert len(ctxs) == 2
    assert isinstance(ctxs['SPY'], ExecContext)
    assert isinstance(ctxs['AAPL'], ExecContext)
    if not ctxs['AAPL'].long_pos():
        ctxs['AAPL'].buy_shares = 200

@pytest.fixture()
def pending_orders():
    return (PendingOrder(id=1, type='buy', symbol='SPY', created=np.datetime64('2020-01-05'), exec_date=np.datetime64('2020-01-10'), shares=Decimal(100), limit_price=None, fill_price=PriceType.MIDDLE), PendingOrder(id=2, type='sell', symbol='AAPL', created=np.datetime64('2020-01-06'), exec_date=np.datetime64('2020-01-08'), shares=Decimal(200), limit_price=Decimal(99), fill_price=PriceType.AVERAGE))

def test_sell_all_shares(ctx_with_pos):
    ctx_with_pos.sell_all_shares()
    assert ctx_with_pos.sell_shares == 200
    assert ctx_with_pos._exiting_pos is True

def test_cover_all_shares(ctx_with_pos):
    ctx_with_pos.cover_all_shares()
    assert ctx_with_pos.buy_shares == 100
    assert ctx_with_pos._exiting_pos is True

def test_long_positions(ctx_with_pos, symbol):
    positions = tuple(ctx_with_pos.long_positions(symbol))
    assert len(positions) == 1
    assert positions[0] == Position(symbol, 200, 'long')

def test_long_positions_when_empty(ctx, symbol):
    assert not len(tuple(ctx.long_positions(symbol)))

def test_short_positions(ctx_with_pos, symbol):
    positions = tuple(ctx_with_pos.short_positions(symbol))
    assert len(positions) == 1
    assert positions[0] == Position(symbol, 100, 'short')

def test_short_positions_when_empty(ctx, symbol):
    assert not len(tuple(ctx.short_positions(symbol)))

def test_to_result_when_buy(ctx, symbol, date):
    ctx.buy_fill_price = PriceType.AVERAGE
    ctx.sell_fill_price = PriceType.HIGH
    ctx.buy_shares = 20
    ctx.buy_limit_price = 99.99
    ctx.hold_bars = 2
    ctx.score = 7
    result = ctx.to_result()
    assert result.symbol == symbol
    assert result.date == date
    assert result.buy_fill_price == PriceType.AVERAGE
    assert result.buy_shares == 20
    assert result.buy_limit_price == Decimal('99.99')
    assert result.hold_bars == 2
    assert result.score == 7
    assert len(result.long_stops) == 1
    assert result.short_stops is None
    stop = next(iter(result.long_stops))
    assert stop.symbol == symbol
    assert stop.stop_type == StopType.BAR
    assert stop.pos_type == 'long'
    assert stop.percent is None
    assert stop.points is None
    assert stop.bars == 2
    assert stop.fill_price == PriceType.HIGH
    assert stop.limit_price is None

def test_to_result_when_sell(ctx, symbol, date):
    ctx.buy_fill_price = PriceType.AVERAGE
    ctx.sell_fill_price = PriceType.HIGH
    ctx.sell_shares = 20
    ctx.sell_limit_price = 110.11
    ctx.hold_bars = 2
    ctx.score = 7
    result = ctx.to_result()
    assert result.symbol == symbol
    assert result.date == date
    assert result.sell_fill_price == PriceType.HIGH
    assert result.sell_shares == 20
    assert result.sell_limit_price == Decimal('110.11')
    assert result.hold_bars == 2
    assert result.score == 7
    assert len(result.short_stops) == 1
    assert result.long_stops is None
    stop = next(iter(result.short_stops))
    assert stop.symbol == symbol
    assert stop.stop_type == StopType.BAR
    assert stop.pos_type == 'short'
    assert stop.percent is None
    assert stop.points is None
    assert stop.bars == 2
    assert stop.fill_price == PriceType.AVERAGE
    assert stop.limit_price is None

def test_orders(ctx_with_orders, orders):
    assert tuple(ctx_with_orders.orders()) == orders

def test_orders_when_empty(ctx):
    assert not len(list(ctx.orders()))

def test_cancel_pending_order(ctx, pending_orders):
    assert ctx.cancel_pending_order(pending_orders[0].id)
    orders = tuple(ctx.pending_orders())
    assert orders == tuple([pending_orders[1]])

def test_cancel_all_pending_orders(ctx):
    ctx.cancel_all_pending_orders()
    assert not tuple(ctx.pending_orders())

def test_cancel_all_pending_orders_when_symbol(ctx, pending_orders):
    ctx.cancel_all_pending_orders('SPY')
    assert tuple(ctx.pending_orders()) == tuple([pending_orders[1]])

def test_pending_orders(ctx, pending_orders):
    assert tuple(ctx.pending_orders()) == pending_orders
    assert tuple(ctx.pending_orders('AAPL')) == tuple([pending_orders[1]])

