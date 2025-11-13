# Cluster 5

class PosSizeContext(BaseContext):
    """Holds data for a position size handler set with
    :meth:`pybroker.Strategy.set_pos_size_handler`. Used to set position sizes
    when placing orders from buy and sell signals.

    Attributes:
        sessions: ``dict`` used to store custom data for all symbols.
    """

    def __init__(self, config: StrategyConfig, portfolio: Portfolio, col_scope: ColumnScope, ind_scope: IndicatorScope, input_scope: ModelInputScope, pred_scope: PredictionScope, pending_order_scope: PendingOrderScope, models: Mapping[ModelSymbol, TrainedModel], sessions: Mapping[str, Mapping], sym_end_index: Mapping[str, int]):
        super().__init__(config=config, portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=models, sym_end_index=sym_end_index)
        self.sessions = sessions
        self._signal_shares: dict[int, Union[int, float, Decimal]] = {}
        self._buy_results: Optional[list[ExecResult]] = None
        self._sell_results: Optional[list[ExecResult]] = None
        self._max_long_positions = config.max_long_positions
        self._max_short_positions = config.max_short_positions

    def signals(self, signal_type: Optional[Literal['buy', 'sell']]=None) -> Iterator[ExecSignal]:
        """Returns :class:`Iterator` of :class:`.ExecSignal`\\ s containing
        data for buy and sell signals.
        """
        if signal_type is not None:
            if signal_type != 'buy' and signal_type != 'sell':
                raise ValueError(f'Unknown signal_type: {signal_type!r}.')
        if (signal_type is None or signal_type == 'buy') and self._buy_results is not None:
            for i, result in enumerate(self._buy_results):
                if result.buy_shares is None:
                    raise ValueError('buy_shares is None on a buy ExecResult.')
                yield ExecSignal(id=i, symbol=result.symbol, shares=result.buy_shares, score=result.score, bar_data=self._col_scope.bar_data_from_data_columns(result.symbol, self._sym_end_index[result.symbol]), type='buy')
                if self._max_long_positions is not None and i + 1 == self._max_long_positions:
                    break
        if (signal_type is None or signal_type == 'sell') and self._sell_results is not None:
            id_offset = len(self._buy_results) if self._buy_results is not None else 0
            for i, result in enumerate(self._sell_results):
                if result.sell_shares is None:
                    raise ValueError('sell_shares is None on a sell ExecResult.')
                yield ExecSignal(id=i + id_offset, symbol=result.symbol, shares=result.sell_shares, score=result.score, bar_data=self._col_scope.bar_data_from_data_columns(result.symbol, self._sym_end_index[result.symbol]), type='sell')
                if self._max_short_positions is not None and i + 1 == self._max_short_positions:
                    break

    def set_shares(self, signal: ExecSignal, shares: Union[int, float, Decimal]):
        """Sets the number of shares of an order for the buy or sell signal."""
        self._signal_shares[signal.id] = shares

def __init__(self, config: StrategyConfig, portfolio: Portfolio, col_scope: ColumnScope, ind_scope: IndicatorScope, input_scope: ModelInputScope, pred_scope: PredictionScope, pending_order_scope: PendingOrderScope, models: Mapping[ModelSymbol, TrainedModel], sessions: Mapping[str, Mapping], sym_end_index: Mapping[str, int]):
    super().__init__(config=config, portfolio=portfolio, col_scope=col_scope, ind_scope=ind_scope, input_scope=input_scope, pred_scope=pred_scope, pending_order_scope=pending_order_scope, models=models, sym_end_index=sym_end_index)
    self.sessions = sessions
    self._signal_shares: dict[int, Union[int, float, Decimal]] = {}
    self._buy_results: Optional[list[ExecResult]] = None
    self._sell_results: Optional[list[ExecResult]] = None
    self._max_long_positions = config.max_long_positions
    self._max_short_positions = config.max_short_positions

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

def __init__(self, api_key: str, api_secret: str):
    super().__init__()
    self._api = alpaca_stock.StockHistoricalDataClient(api_key, api_secret)

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

def __init__(self, api_key: str, api_secret: str):
    super().__init__()
    self._scope.register_custom_cols(self.TRADE_COUNT)
    self._api = alpaca_crypto.CryptoHistoricalDataClient(api_key, api_secret)

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

def register_columns(names: Union[str, Iterable[str]], *args):
    """Registers ``names`` of user-defined data columns."""
    StaticScope.instance().register_custom_cols(names, *args)

def unregister_columns(names: Union[str, Iterable[str]], *args):
    """Unregisters ``names`` of user-defined data columns."""
    StaticScope.instance().unregister_custom_cols(names, *args)

class ModelLoader(ModelSource):
    """Loads a pre-trained model.

    Args:
        name: Name of model.
        load_fn: ``Callable[[symbol: str, train_start_date: datetime,
            train_end_date: datetime, ...], DataFrame]`` used to load and
            return a pre-trained model. This is expected to
            return either a trained model instance, or a tuple containing a
            trained model instance and a :class:`Iterable` of column names to
            to be used as input for the model when making predictions.
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
        kwargs: ``dict`` of kwargs to pass to ``load_fn``.
    """

    def __init__(self, name: str, load_fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
        super().__init__(name, indicator_names, input_data_fn, predict_fn, kwargs)
        self._load_fn = functools.partial(load_fn, **kwargs)

    def __call__(self, symbol: str, train_start_date: datetime, train_end_date: datetime) -> Union[Any, tuple[Any, Iterable[str]]]:
        """Loads pre-trained model.

        Args:
            symbol: Ticker symbol for loading the pre-trained model.
            train_start_date: Start date of training window.
            train_end_date: End date of training window.

        Returns:
            Pre-trained model.
        """
        return self._load_fn(symbol, train_start_date, train_end_date)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'ModelLoader({self.name!r}, {self._kwargs})'

def __init__(self, name: str, load_fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
    super().__init__(name, indicator_names, input_data_fn, predict_fn, kwargs)
    self._load_fn = functools.partial(load_fn, **kwargs)

class ModelTrainer(ModelSource):
    """Trains a model.

    Args:
        name: Name of model.
        train_fn: ``Callable[[symbol: str, train_data: DataFrame,
            test_data: DataFrame, ...], DataFrame]`` used to train and return a
            model. This is expected to return either a trained model instance,
            or a tuple containing a trained model instance and a
            :class:`Iterable` of column names to to be used as input for the
            model when making predictions.
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
        kwargs: ``dict`` of kwargs to pass to ``train_fn``.
    """

    def __init__(self, name: str, train_fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
        super().__init__(name, indicator_names, input_data_fn, predict_fn, kwargs)
        self._train_fn = functools.partial(train_fn, **kwargs)

    def __call__(self, symbol: str, train_data: pd.DataFrame, test_data: pd.DataFrame) -> Union[Any, tuple[Any, Iterable[str]]]:
        """Trains model.

        Args:
            symbol: Ticker symbol of model (models are trained per symbol).
            train_data: Train data.
            test_data: Test data.

        Returns:
            Trained model.
        """
        return self._train_fn(symbol, train_data, test_data)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'ModelTrainer({self.name!r}, {self._kwargs})'

def __init__(self, name: str, train_fn: Callable[..., Union[Any, tuple[Any, Iterable[str]]]], indicator_names: Iterable[str], input_data_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]], predict_fn: Optional[Callable[[Any, pd.DataFrame], NDArray]], kwargs: dict[str, Any]):
    super().__init__(name, indicator_names, input_data_fn, predict_fn, kwargs)
    self._train_fn = functools.partial(train_fn, **kwargs)

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

def __init__(self, name: str, fn: Callable[..., NDArray[np.float64]], kwargs: dict[str, Any]):
    self.name = name
    self._fn = functools.partial(fn, **kwargs)
    self._kwargs = kwargs

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

def __init__(self, proxies: Optional[dict]=None):
    super().__init__()
    self.proxies = proxies

@pytest.fixture()
def setup_teardown(scope):
    scope.register_custom_cols('adj_close')
    yield
    scope.unregister_custom_cols('adj_close')

@pytest.mark.parametrize('field', ['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close'])
def test_fields(scope, ctx, field, end_index):
    scope.register_custom_cols('adj_close')
    assert len(getattr(ctx, field)) == end_index

def test_input(ctx, end_index):
    assert len(ctx.input(MODEL_NAME)['hhv']) == end_index

def test_preds(ctx, end_index):
    assert len(ctx.preds(MODEL_NAME)) == end_index

@pytest.mark.parametrize('col', ['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close'])
def test_foreign(ctx, col, foreign, data_source_df, end_index):
    df = data_source_df[data_source_df['symbol'] == foreign]
    assert (ctx.foreign(foreign, col) == df[col].values[:end_index]).all()
    df = data_source_df[data_source_df['symbol'] == foreign]
    assert (ctx.foreign(foreign, col) == df[col].values[:end_index]).all()

def test_foreign_with_custom_col(scope, ctx, foreign, data_source_df, end_index):
    scope.register_custom_cols('adj_close')
    df = data_source_df[data_source_df['symbol'] == foreign]
    assert (ctx.foreign(foreign, 'adj_close') == df['adj_close'].values[:end_index]).all()

def test_foreign_when_empty(ctx, foreign):
    assert ctx.foreign(foreign, 'foo') is None

def test_foreign_with_empty_col(scope, ctx, foreign, data_source_df, end_index):
    scope.register_custom_cols('adj_close')
    df = data_source_df[data_source_df['symbol'] == foreign]

    def verify_bar_data(bar_data):
        for col in ('date', 'open', 'high', 'low', 'close', 'volume', 'adj_close'):
            assert (getattr(bar_data, col) == df[col].values[:end_index]).all()
    verify_bar_data(ctx.foreign(foreign))
    verify_bar_data(ctx.foreign(foreign))

