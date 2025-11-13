# Cluster 1

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

def __getattr__(self, attr):
    if attr in self._scope.custom_data_cols:
        if self.symbol is None:
            raise ValueError('symbol is not set.')
        return self._col_scope.fetch(self.symbol, attr, self._sym_end_index[self.symbol])
    raise AttributeError(f'Attribute {attr!r} not found.')

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

def _exit_position(self, portfolio: Portfolio, date: np.datetime64, ctx: ExecContext, exit_cover_fill_price: Union[PriceType, Callable[[str, BarData], Union[int, float, Decimal]]], exit_sell_fill_price: Union[PriceType, Callable[[str, BarData], Union[int, float, Decimal]]], price_scope: PriceScope):
    buy_fill_price = price_scope.fetch(ctx.symbol, exit_cover_fill_price)
    sell_fill_price = price_scope.fetch(ctx.symbol, exit_sell_fill_price)
    portfolio.exit_position(date, ctx.symbol, buy_fill_price=buy_fill_price, sell_fill_price=sell_fill_price)

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

def _verify_data_source(self, data_source: Union[DataSource, pd.DataFrame]):
    if isinstance(data_source, pd.DataFrame):
        verify_data_source_columns(data_source)
    elif not isinstance(data_source, DataSource):
        raise TypeError(f'Invalid data_source type: {type(data_source)}')

def _fractional_shares_enabled(self):
    return self._config.enable_fractional_shares or isinstance(self._data_source, AlpacaCrypto)

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

def info_walkforward_on_days(self, days: tuple[int]):
    self._info(f'Backtest on days: {map(lambda d: Day(d).name, days)}')

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

def _trigger_bar_stop(self, stop: Stop, price_scope: PriceScope, entry: Entry) -> Optional[Decimal]:
    if stop.bars is None:
        raise ValueError('Bars not set on bar stop.')
    if entry.bars >= stop.bars:
        return price_scope.fetch(stop.symbol, PriceType.MIDDLE if stop.fill_price is None else stop.fill_price)
    return None

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

class IndicatorScope:
    """Caches and retrieves :class:`pybroker.indicator.Indicator` data.

    Args:
        indicator_data: :class:`Mapping` of
            :class:`pybroker.common.IndicatorSymbol` pairs to ``pandas.Series``
            of :class:`pybroker.indicator.Indicator` values.
        filter_dates: Filters :class:`pybroker.indicator.Indicator` data on
            :class:`Sequence` of dates.
    """

    def __init__(self, indicator_data: Mapping[IndicatorSymbol, pd.Series], filter_dates: Sequence[np.datetime64]):
        self._indicator_data = indicator_data
        self._filter_dates = filter_dates
        self._sym_inds: dict[IndicatorSymbol, NDArray[np.float64]] = {}

    def fetch(self, symbol: str, name: str, end_index: Optional[int]=None) -> NDArray[np.float64]:
        """Fetches :class:`pybroker.indicator.Indicator` data.

        Args:
            symbol: Ticker symbol to query.
            name: Name of :class:`pybroker.indicator.Indicator` to query.
            end_index: Truncates the array of
                :class:`pybroker.indicator.Indicator` data returned
                (exclusive). If ``None``, then indicator data is not truncated.

        Returns:
            :class:`numpy.ndarray` of :class:`pybroker.indicator.Indicator`
            data for every bar until ``end_index`` (when specified).
        """
        ind_sym = IndicatorSymbol(name, symbol)
        if ind_sym in self._sym_inds:
            return self._sym_inds[ind_sym][:end_index]
        if ind_sym not in self._indicator_data:
            raise ValueError(f'Indicator {name!r} not found for {symbol}.')
        ind_series = self._indicator_data[ind_sym]
        ind_data = ind_series[ind_series.index.isin(self._filter_dates)].values
        self._sym_inds[ind_sym] = ind_data
        return ind_data[:end_index]

def fetch(self, symbol: str, name: str, end_index: Optional[int]=None) -> NDArray[np.float64]:
    """Fetches :class:`pybroker.indicator.Indicator` data.

        Args:
            symbol: Ticker symbol to query.
            name: Name of :class:`pybroker.indicator.Indicator` to query.
            end_index: Truncates the array of
                :class:`pybroker.indicator.Indicator` data returned
                (exclusive). If ``None``, then indicator data is not truncated.

        Returns:
            :class:`numpy.ndarray` of :class:`pybroker.indicator.Indicator`
            data for every bar until ``end_index`` (when specified).
        """
    ind_sym = IndicatorSymbol(name, symbol)
    if ind_sym in self._sym_inds:
        return self._sym_inds[ind_sym][:end_index]
    if ind_sym not in self._indicator_data:
        raise ValueError(f'Indicator {name!r} not found for {symbol}.')
    ind_series = self._indicator_data[ind_sym]
    ind_data = ind_series[ind_series.index.isin(self._filter_dates)].values
    self._sym_inds[ind_sym] = ind_data
    return ind_data[:end_index]

class PriceScope:
    """Retrieves most recent prices."""

    def __init__(self, col_scope: ColumnScope, sym_end_index: Mapping[str, int], round_fill_price: bool):
        self._col_scope = col_scope
        self._sym_end_index = sym_end_index
        self._round_fill_price = round_fill_price

    def fetch(self, symbol: str, price: Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]) -> Decimal:
        end_index = self._sym_end_index[symbol]
        price_type = type(price)
        fill_price = None
        if price_type == PriceType:
            if price == PriceType.OPEN:
                open_ = self._col_scope.fetch(symbol, DataCol.OPEN.value, end_index)
                if open_ is None:
                    raise ValueError('Open price not found.')
                fill_price = open_[-1]
            elif price == PriceType.HIGH:
                high = self._col_scope.fetch(symbol, DataCol.HIGH.value, end_index)
                if high is None:
                    raise ValueError('High price not found.')
                fill_price = high[-1]
            elif price == PriceType.LOW:
                low = self._col_scope.fetch(symbol, DataCol.LOW.value, end_index)
                if low is None:
                    raise ValueError('Low price not found.')
                fill_price = low[-1]
            elif price == PriceType.CLOSE:
                close = self._col_scope.fetch(symbol, DataCol.CLOSE.value, end_index)
                if close is None:
                    raise ValueError('Close price not found.')
                fill_price = close[-1]
            elif price == PriceType.MIDDLE:
                low = self._col_scope.fetch(symbol, DataCol.LOW.value, end_index)
                if low is None:
                    raise ValueError('Low price not found.')
                high = self._col_scope.fetch(symbol, DataCol.HIGH.value, end_index)
                if high is None:
                    raise ValueError('High price not found.')
                fill_price = low[-1] + (high[-1] - low[-1]) / 2.0
            elif price == PriceType.AVERAGE:
                open_ = self._col_scope.fetch(symbol, DataCol.OPEN.value, end_index)
                if open_ is None:
                    raise ValueError('Open price not found.')
                high = self._col_scope.fetch(symbol, DataCol.HIGH.value, end_index)
                if high is None:
                    raise ValueError('High price not found.')
                low = self._col_scope.fetch(symbol, DataCol.LOW.value, end_index)
                if low is None:
                    raise ValueError('Low price not found.')
                close = self._col_scope.fetch(symbol, DataCol.CLOSE.value, end_index)
                if close is None:
                    raise ValueError('Close price not found.')
                fill_price = (open_[-1] + low[-1] + high[-1] + close[-1]) / 4.0
            else:
                raise ValueError(f'Unknown price: {price_type}')
        elif price_type is float or price_type is int or isinstance(price, np.floating) or isinstance(price, Decimal):
            fill_price = price
        elif callable(price):
            bar_data = self._col_scope.bar_data_from_data_columns(symbol, self._sym_end_index[symbol])
            fill_price = price(symbol, bar_data)
        else:
            raise ValueError(f'Unknown price: {price_type}')
        if self._round_fill_price:
            fill_price = round(cast(float, fill_price), 2)
        return to_decimal(cast(float, fill_price))

def fetch(self, symbol: str, price: Union[int, float, np.floating, Decimal, PriceType, Callable[[str, BarData], Union[int, float, Decimal]]]) -> Decimal:
    end_index = self._sym_end_index[symbol]
    price_type = type(price)
    fill_price = None
    if price_type == PriceType:
        if price == PriceType.OPEN:
            open_ = self._col_scope.fetch(symbol, DataCol.OPEN.value, end_index)
            if open_ is None:
                raise ValueError('Open price not found.')
            fill_price = open_[-1]
        elif price == PriceType.HIGH:
            high = self._col_scope.fetch(symbol, DataCol.HIGH.value, end_index)
            if high is None:
                raise ValueError('High price not found.')
            fill_price = high[-1]
        elif price == PriceType.LOW:
            low = self._col_scope.fetch(symbol, DataCol.LOW.value, end_index)
            if low is None:
                raise ValueError('Low price not found.')
            fill_price = low[-1]
        elif price == PriceType.CLOSE:
            close = self._col_scope.fetch(symbol, DataCol.CLOSE.value, end_index)
            if close is None:
                raise ValueError('Close price not found.')
            fill_price = close[-1]
        elif price == PriceType.MIDDLE:
            low = self._col_scope.fetch(symbol, DataCol.LOW.value, end_index)
            if low is None:
                raise ValueError('Low price not found.')
            high = self._col_scope.fetch(symbol, DataCol.HIGH.value, end_index)
            if high is None:
                raise ValueError('High price not found.')
            fill_price = low[-1] + (high[-1] - low[-1]) / 2.0
        elif price == PriceType.AVERAGE:
            open_ = self._col_scope.fetch(symbol, DataCol.OPEN.value, end_index)
            if open_ is None:
                raise ValueError('Open price not found.')
            high = self._col_scope.fetch(symbol, DataCol.HIGH.value, end_index)
            if high is None:
                raise ValueError('High price not found.')
            low = self._col_scope.fetch(symbol, DataCol.LOW.value, end_index)
            if low is None:
                raise ValueError('Low price not found.')
            close = self._col_scope.fetch(symbol, DataCol.CLOSE.value, end_index)
            if close is None:
                raise ValueError('Close price not found.')
            fill_price = (open_[-1] + low[-1] + high[-1] + close[-1]) / 4.0
        else:
            raise ValueError(f'Unknown price: {price_type}')
    elif price_type is float or price_type is int or isinstance(price, np.floating) or isinstance(price, Decimal):
        fill_price = price
    elif callable(price):
        bar_data = self._col_scope.bar_data_from_data_columns(symbol, self._sym_end_index[symbol])
        fill_price = price(symbol, bar_data)
    else:
        raise ValueError(f'Unknown price: {price_type}')
    if self._round_fill_price:
        fill_price = round(cast(float, fill_price), 2)
    return to_decimal(cast(float, fill_price))

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

def orders(self, symbol: Optional[str]=None) -> Iterable[PendingOrder]:
    """Returns an :class:`Iterable` of :class:`.PendingOrder`\\ s."""
    if symbol is None:
        return self._orders.values()
    else:
        if symbol not in self._sym_orders:
            return []
        return self._sym_orders[symbol]

class BarData:
    """Contains data for a series of bars. Each field is a
    :class:`numpy.ndarray` that contains bar values in the series. The values
    are sorted in ascending chronological order.

    Args:
        date: Timestamps of each bar.
        open: Open prices.
        high: High prices.
        low: Low prices.
        close: Close prices.
        volume: Trading volumes.
        vwap: Volume-weighted average prices (VWAP).
        \\**kwargs: Custom data fields.
    """

    def __init__(self, date: NDArray[np.datetime64], open: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: Optional[NDArray[np.float64]], vwap: Optional[NDArray[np.float64]], **kwargs):
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.vwap = vwap
        self._custom_col_data = kwargs

    def __getattr__(self, attr):
        if self._custom_col_data and attr in self._custom_col_data:
            return self._custom_col_data[attr]
        raise AttributeError(f'Attribute {attr!r} not found.')

def __getattr__(self, attr):
    if self._custom_col_data and attr in self._custom_col_data:
        return self._custom_col_data[attr]
    raise AttributeError(f'Attribute {attr!r} not found.')

def to_datetime(date: Union[str, datetime, np.datetime64, pd.Timestamp]) -> datetime:
    """Converts ``date`` to :class:`datetime`."""
    if isinstance(date, pd.Timestamp):
        return date.to_pydatetime()
    elif isinstance(date, datetime):
        return date
    elif isinstance(date, str):
        return pd.to_datetime(date).to_pydatetime()
    elif isinstance(date, np.datetime64):
        return pd.Timestamp(date).to_pydatetime()
    else:
        raise TypeError(f'Unsupported date type: {type(date)}')

def to_decimal(value: Union[int, float, Decimal]) -> Decimal:
    """Converts ``value`` to :class:`Decimal`."""
    value_type = type(value)
    if value_type == Decimal:
        return value
    elif value_type is int:
        return Decimal(value)
    return Decimal(str(value))

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

class Indicator:
    """Class representing an indicator.

    Args:
        name: Name of indicator.
        fn: :class:`Callable` used to compute the series of indicator values.
        kwargs: ``dict`` of kwargs to pass to ``fn``.
    """

    def __init__(self, name: str, fn: Callable[..., NDArray[np.float64]], kwargs: dict[str, Any]):
        self.name = name
        self._fn = functools.partial(fn, **kwargs)
        self._kwargs = kwargs

    def relative_entropy(self, data: Union[BarData, pd.DataFrame]) -> float:
        """Generates indicator data with ``data`` and computes its relative
        `entropy
        <https://en.wikipedia.org/wiki/Entropy_(information_theory)>`_.
        """
        return relative_entropy(self(data).values)

    def iqr(self, data: Union[BarData, pd.DataFrame]) -> float:
        """Generates indicator data with ``data`` and computes its
        `interquartile range (IQR)
        <https://en.wikipedia.org/wiki/Interquartile_range>`_.
        """
        return iqr(self(data).values)

    def __call__(self, data: Union[BarData, pd.DataFrame]) -> pd.Series:
        """Computes indicator values."""
        if isinstance(data, pd.DataFrame):
            data = _to_bar_data(data)
        values = self._fn(data)
        if isinstance(values, pd.Series):
            values = values.to_numpy()
        if len(values.shape) != 1:
            raise ValueError(f'Indicator {self.name} must return a one-dimensional array.')
        return pd.Series(values, index=data.date)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Indicator({self.name!r}, {self._kwargs})'

def relative_entropy(self, data: Union[BarData, pd.DataFrame]) -> float:
    """Generates indicator data with ``data`` and computes its relative
        `entropy
        <https://en.wikipedia.org/wiki/Entropy_(information_theory)>`_.
        """
    return relative_entropy(self(data).values)

def iqr(self, data: Union[BarData, pd.DataFrame]) -> float:
    """Generates indicator data with ``data`` and computes its
        `interquartile range (IQR)
        <https://en.wikipedia.org/wiki/Interquartile_range>`_.
        """
    return iqr(self(data).values)

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

def test_verify_data_source_columns():
    df = pd.DataFrame(columns=['symbol', 'date', 'open', 'high', 'low', 'close'])
    verify_data_source_columns(df)
    assert True

@pytest.fixture()
def ind_syms(hhv_ind, llv_ind, sumv_ind, symbols):
    return [IndicatorSymbol(ind.name, sym) for sym in symbols for ind in (hhv_ind, llv_ind, sumv_ind)]

@pytest.mark.usefixtures('setup_teardown')
def test_indicator():
    ind = indicator('llv', lowv)
    assert isinstance(ind, Indicator)
    assert ind.name == 'llv'

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

def test_iqr(self, hhv_ind, data_source_df):
    assert isinstance(hhv_ind.iqr(data_source_df), float)

def test_relative_entropy(self, hhv_ind, data_source_df):
    assert isinstance(hhv_ind.relative_entropy(data_source_df), float)

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

def test_fetch_dict_when_cached(self, col_scope, data_source_df, symbols, end_index):
    cols = ['date', 'close']
    col_scope.fetch_dict(symbols[0], cols, end_index)
    result = col_scope.fetch_dict(symbols[0], cols, end_index)
    assert set(result.keys()) == set(cols)
    for value in result.values():
        self._assert_length(value, end_index, data_source_df, symbols[0])

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

def test_fetch(self, ind_scope, symbol, ind_data, ind_name, end_index):
    result = ind_scope.fetch(symbol, ind_name, end_index)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, ind_data[IndicatorSymbol(ind_name, symbol)].values[:end_index], equal_nan=True)

def test_fetch_when_cached(self, ind_scope, symbol, ind_data, ind_name, end_index):
    ind_scope.fetch(symbol, ind_name, end_index)
    result = ind_scope.fetch(symbol, ind_name, end_index)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, ind_data[IndicatorSymbol(ind_name, symbol)].values[:end_index], equal_nan=True)

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

def test_get_signals(symbols, scope, col_scope, ind_scope, pred_scope, data_source_df, ind_data, preds):
    dfs = get_signals(symbols, col_scope, ind_scope, pred_scope)
    assert set(dfs.keys()) == set(symbols)
    for sym in symbols:
        for col in scope.all_data_cols:
            if col not in data_source_df.columns:
                continue
            assert np.array_equal(dfs[sym][col].values, data_source_df[data_source_df['symbol'] == sym][col].values)
        assert np.array_equal(dfs[sym][f'{MODEL_NAME}_pred'].values, preds[sym], equal_nan=True)
    for ind_name, sym in ind_data:
        assert np.array_equal(dfs[sym][ind_name].values, ind_data[IndicatorSymbol(ind_name, sym)].values, equal_nan=True)

def exec_fn_2(ctx):
    assert len(ctx.indicator(hhv_ind.name))
    assert isinstance(ctx.model(exec_model_source.name), FakeModel)

def exec_fn(ctx):
    assert isinstance(ctx.model(exec_model_source.name), FakeModel)

def get_fixture(request, param):
    if isinstance(param, LazyFixture):
        return request.getfixturevalue(param.name)
    return param

@pytest.fixture()
def ind_data(data_source_df, symbols, hhv_ind, llv_ind, sumv_ind):
    return {**{IndicatorSymbol(ind.name, sym): ind(data_source_df[data_source_df['symbol'] == sym]) for sym in symbols for ind in [hhv_ind, llv_ind, sumv_ind]}}

@pytest.fixture()
def ind_names(indicators):
    return list(map(lambda x: x.name, indicators))

@pytest.fixture()
def trained_model(trained_models):
    return list(trained_models.values())[0]

def test_model(ctx, trained_models, symbol):
    assert ctx.model(MODEL_NAME) == trained_models[MODEL_NAME, symbol].instance

@pytest.mark.parametrize('pos_type', ['long', 'short', None])
def test_positions(ctx_with_pos, pos_type, portfolio):
    positions = ctx_with_pos.positions(None, pos_type)
    if pos_type is None:
        expected_positions = set(portfolio.long_positions.keys()) | set(portfolio.short_positions.keys())
    else:
        expected_positions = set(getattr(portfolio, f'{pos_type}_positions').keys())
    assert set(map(lambda p: p.symbol, positions)) == expected_positions

@pytest.mark.parametrize('pretrained, input_cols', [(True, False), (True, False)])
def test_model(indicators, pretrained, input_cols):

    def input_data_fn(df):
        pass

    def predict_fn(model, df):
        pass
    name = f'pretrained={pretrained}'
    source = model(name, lambda x: (x, ['hhv', 'llv']) if input_cols else x, indicators, input_data_fn=input_data_fn, predict_fn=predict_fn, pretrained=pretrained)
    assert isinstance(source, ModelLoader if pretrained else ModelTrainer)
    assert source.name == name
    assert source.indicators == ('hhv', 'llv', 'sumv')
    assert source._input_data_fn is input_data_fn
    assert source._predict_fn is predict_fn

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

def _assert_models(self, models, expected_model_syms):
    assert set(models.keys()) == set(expected_model_syms)
    for model_sym in expected_model_syms:
        model = models[model_sym]
        assert isinstance(model, TrainedModel)
        assert model.name == model_sym.model_name
        assert model.instance.symbol == model_sym.symbol

