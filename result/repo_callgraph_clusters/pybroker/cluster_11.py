# Cluster 11

@njit
def cross(a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.bool_]:
    """Checks for crossover of ``a`` above ``b``.

    Args:
        a: :class:`numpy.ndarray` of data.
        b: :class:`numpy.ndarray` of data.

    Returns:
        :class:`numpy.ndarray` containing values of ``1`` when ``a`` crosses
        above ``b``, otherwise values of ``0``.
    """
    assert len(a), 'a cannot be empty.'
    assert len(b), 'b cannot be empty.'
    assert len(a) == len(b), 'a and b must be same length.'
    assert len(a) >= 2, 'a and b must have length >= 2.'
    crossed = np.where(a > b, 1, 0)
    return (sumv(crossed > 0, 2) == 1) * crossed

def get_signals(symbols: Iterable[str], col_scope: ColumnScope, ind_scope: IndicatorScope, pred_scope: PredictionScope) -> dict[str, pd.DataFrame]:
    """Retrieves dictionary of :class:`pandas.DataFrame`\\ s
    containing bar data, indicator data, and model predictions for each symbol.
    """
    static_scope = StaticScope.instance()
    cols = static_scope.all_data_cols
    inds = static_scope._indicators.keys()
    models = static_scope._model_sources.keys()
    dates = col_scope._df.index.get_level_values(1)
    dfs: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        data = {DataCol.DATE.value: dates}
        for col in cols:
            data[col] = col_scope.fetch(sym, col)
        for ind in inds:
            try:
                data[ind] = ind_scope.fetch(sym, ind)
            except ValueError:
                continue
        for model in models:
            try:
                data[f'{model}_pred'] = pred_scope.fetch(sym, model)
            except ValueError:
                continue
        dfs[sym] = pd.DataFrame(data)
    return dfs

def _highest(data: BarData):
    values = getattr(data, field)
    return highv(values, period)

def highest(name: str, field: str, period: int) -> Indicator:
    """Creates a rolling high :class:`.Indicator`.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field for computing the rolling
            high.
        period: Lookback period.

    Returns:
        Rolling high :class:`.Indicator`.
    """

    def _highest(data: BarData):
        values = getattr(data, field)
        return highv(values, period)
    return indicator(name, _highest)

def _lowest(data: BarData):
    values = getattr(data, field)
    return lowv(values, period)

def lowest(name: str, field: str, period: int) -> Indicator:
    """Creates a rolling low :class:`.Indicator`.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field for computing the rolling
            low.
        period: Lookback period.

    Returns:
        Rolling low :class:`.Indicator`.
    """

    def _lowest(data: BarData):
        values = getattr(data, field)
        return lowv(values, period)
    return indicator(name, _lowest)

def _returns(data: BarData):
    values = getattr(data, field)
    return returnv(values, period)

def returns(name: str, field: str, period: int=1) -> Indicator:
    """Creates a rolling returns :class:`.Indicator`.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field for computing the rolling
            returns.
        period: Returns period. Defaults to 1.

    Returns:
        Rolling returns :class:`.Indicator`.
    """

    def _returns(data: BarData):
        values = getattr(data, field)
        return returnv(values, period)
    return indicator(name, _returns)

def _detrended_rsi(data: BarData):
    values = getattr(data, field)
    return vect.detrended_rsi(values, short_length=short_length, long_length=long_length, reg_length=reg_length)

def detrended_rsi(name: str, field: str, short_length: int, long_length: int, reg_length: int) -> Indicator:
    """Detrended Relative Strength Index (RSI).

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        short_length: Lookback for the short-term RSI.
        long_length: Lookback for the long-term RSI.
        reg_length: Number of bars used for linear regressions.

    Returns:
        Detrended RSI :class:`.Indicator`.
    """

    def _detrended_rsi(data: BarData):
        values = getattr(data, field)
        return vect.detrended_rsi(values, short_length=short_length, long_length=long_length, reg_length=reg_length)
    return indicator(name, _detrended_rsi)

def macd(name: str, short_length: int, long_length: int, smoothing: float=0.0, scale: float=1.0) -> Indicator:
    """Moving Average Convergence Divergence.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        short_length: Short-term lookback.
        long_length: Long-term lookback.
        smoothing: Compute MACD minus smoothed if >= 2.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        Moving Average Convergence Divergence :class:`.Indicator`.
    """

    def _macd(data: BarData):
        return vect.macd(high=data.high, low=data.low, close=data.close, short_length=short_length, long_length=long_length, smoothing=smoothing, scale=scale)
    return indicator(name, _macd)

def stochastic(name: str, lookback: int, smoothing: int=0) -> Indicator:
    """Stochastic.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        smoothing: Number of times the raw stochastic is smoothed, either 0,
            1, or 2 times. Defaults to ``0``.

    Returns:
        Stochastic :class:`.Indicator`.
    """

    def _stochastic(data: BarData):
        return vect.stochastic(high=data.high, low=data.low, close=data.close, lookback=lookback, smoothing=smoothing)
    return indicator(name, _stochastic)

def _stochastic_rsi(data: BarData):
    values = getattr(data, field)
    return vect.stochastic_rsi(values, rsi_lookback=rsi_lookback, sto_lookback=sto_lookback, smoothing=smoothing)

def stochastic_rsi(name: str, field: str, rsi_lookback: int, sto_lookback: int, smoothing: float=0.0) -> Indicator:
    """Stochastic Relative Strength Index (RSI).

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        rsi_lookback: Lookback length for RSI calculation.
        sto_lookback: Lookback length for Stochastic calculation.
        smoothing: Amount of smoothing; <= 1 for none. Defaults to ``0``.

    Returns:
        Stochastic RSI :class:`.Indicator`.
    """

    def _stochastic_rsi(data: BarData):
        values = getattr(data, field)
        return vect.stochastic_rsi(values, rsi_lookback=rsi_lookback, sto_lookback=sto_lookback, smoothing=smoothing)
    return indicator(name, _stochastic_rsi)

def _linear_trend(data: BarData):
    values = getattr(data, field)
    return vect.linear_trend(values, high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)

def linear_trend(name: str, field: str, lookback: int, atr_length: int, scale: float=1.0) -> Indicator:
    """Linear Trend Strength.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        Linear Trend Strength :class:`.Indicator`.
    """

    def _linear_trend(data: BarData):
        values = getattr(data, field)
        return vect.linear_trend(values, high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)
    return indicator(name, _linear_trend)

def _quadratic_trend(data: BarData):
    values = getattr(data, field)
    return vect.quadratic_trend(values, high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)

def quadratic_trend(name: str, field: str, lookback: int, atr_length: int, scale: float=1.0) -> Indicator:
    """Quadratic Trend Strength.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        Quadratic Trend Strength :class:`.Indicator`.
    """

    def _quadratic_trend(data: BarData):
        values = getattr(data, field)
        return vect.quadratic_trend(values, high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)
    return indicator(name, _quadratic_trend)

def _cubic_trend(data: BarData):
    values = getattr(data, field)
    return vect.cubic_trend(values, high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)

def cubic_trend(name: str, field: str, lookback: int, atr_length: int, scale: float=1.0) -> Indicator:
    """Cubic Trend Strength.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        Cubic Trend Strength :class:`.Indicator`.
    """

    def _cubic_trend(data: BarData):
        values = getattr(data, field)
        return vect.cubic_trend(values, high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)
    return indicator(name, _cubic_trend)

def adx(name: str, lookback: int) -> Indicator:
    """Average Directional Movement Index.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.

    Returns:
        Average Directional Movement Index :class:`.Indicator`.
    """

    def _adx(data: BarData):
        return vect.adx(high=data.high, low=data.low, close=data.close, lookback=lookback)
    return indicator(name, _adx)

def aroon_up(name: str, lookback: int) -> Indicator:
    """Aroon Upward Trend.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.

    Returns:
        Aroon Upward Trend :class:`.Indicator`.
    """

    def _aroon_up(data: BarData):
        return vect.aroon_up(high=data.high, low=data.low, lookback=lookback)
    return indicator(name, _aroon_up)

def aroon_down(name: str, lookback: int) -> Indicator:
    """Aroon Downward Trend.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.

    Returns:
        Aroon Downward Trend :class:`.Indicator`.
    """

    def _aroon_down(data: BarData):
        return vect.aroon_down(high=data.high, low=data.low, lookback=lookback)
    return indicator(name, _aroon_down)

def aroon_diff(name: str, lookback: int) -> Indicator:
    """Aroon Upward Trend minus Aroon Downward Trend.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.

    Returns:
        Aroon Upward Trend minus Aroon Downward Trend :class:`.Indicator`.
    """

    def _aroon_diff(data: BarData):
        return vect.aroon_diff(high=data.high, low=data.low, lookback=lookback)
    return indicator(name, _aroon_diff)

def close_minus_ma(name: str, lookback: int, atr_length: int, scale: float=1.0) -> Indicator:
    """Close Minus Moving Average.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        Close Minus Moving Average :class:`.Indicator`.
    """

    def _close_minus_ma(data: BarData):
        return vect.close_minus_ma(high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)
    return indicator(name, _close_minus_ma)

def _linear_deviation(data: BarData):
    values = getattr(data, field)
    return vect.linear_deviation(values, lookback=lookback, scale=scale)

def linear_deviation(name: str, field: str, lookback: int, scale: float=0.6) -> Indicator:
    """Deviation from Linear Trend.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        Deviation from Linear Trend :class:`.Indicator`.
    """

    def _linear_deviation(data: BarData):
        values = getattr(data, field)
        return vect.linear_deviation(values, lookback=lookback, scale=scale)
    return indicator(name, _linear_deviation)

def _quadratic_deviation(data: BarData):
    values = getattr(data, field)
    return vect.quadratic_deviation(values, lookback=lookback, scale=scale)

def quadratic_deviation(name: str, field: str, lookback: int, scale: float=0.6) -> Indicator:
    """Deviation from Quadratic Trend.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        Deviation from Quadratic Trend :class:`.Indicator`.
    """

    def _quadratic_deviation(data: BarData):
        values = getattr(data, field)
        return vect.quadratic_deviation(values, lookback=lookback, scale=scale)
    return indicator(name, _quadratic_deviation)

def _cubic_deviation(data: BarData):
    values = getattr(data, field)
    return vect.cubic_deviation(values, lookback=lookback, scale=scale)

def cubic_deviation(name: str, field: str, lookback: int, scale: float=0.6) -> Indicator:
    """Deviation from Cubic Trend.

    Args:
        name: Indicator name.
        field: :class:`pybroker.common.BarData` field name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        Deviation from Cubic Trend :class:`.Indicator`.
    """

    def _cubic_deviation(data: BarData):
        values = getattr(data, field)
        return vect.cubic_deviation(values, lookback=lookback, scale=scale)
    return indicator(name, _cubic_deviation)

def price_intensity(name: str, smoothing: float=0.0, scale: float=0.8) -> Indicator:
    """Price Intensity.

    Args:
        name: Indicator name.
        smoothing: Amount of smoothing. Defaults to ``0``.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.8``.

    Returns:
        Price Intensity :class:`.Indicator`.
    """

    def _price_intensity(data: BarData):
        return vect.price_intensity(open=data.open, high=data.high, low=data.low, close=data.close, smoothing=smoothing, scale=scale)
    return indicator(name, _price_intensity)

def price_change_oscillator(name: str, short_length: int, multiplier: int, scale: float=4.0) -> Indicator:
    """Price Change Oscillator.

    Args:
        name: Indicator name.
        short_length: Number of short lookback bars.
        multiplier: Multiplier used to compute number of long lookback bars =
            ``multiplier * short_length``.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``4.0``.

    Returns:
        Price Change Oscillator :class:`.Indicator`.
    """

    def _price_change_oscillator(data: BarData):
        return vect.price_change_oscillator(high=data.high, low=data.low, close=data.close, short_length=short_length, multiplier=multiplier, scale=scale)
    return indicator(name, _price_change_oscillator)

def intraday_intensity(name: str, lookback: int, smoothing: float=0.0) -> Indicator:
    """Intraday Intensity.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        smoothing: Amount of smoothing; <= 1 for none. Defaults to ``0``.

    Returns:
        Intraday Intensity :class:`.Indicator`.
    """

    def _intraday_intensity(data: BarData):
        return vect.intraday_intensity(high=data.high, low=data.low, close=data.close, volume=data.volume, lookback=lookback, smoothing=smoothing)
    return indicator(name, _intraday_intensity)

def money_flow(name: str, lookback: int, smoothing: float=0.0) -> Indicator:
    """Chaikin's Money Flow.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        smoothing: Amount of smoothing; <= 1 for none. Defaults to ``0``.

    Returns:
        Chaikin's Money Flow :class:`.Indicator`.
    """

    def _money_flow(data: BarData):
        return vect.money_flow(high=data.high, low=data.low, close=data.close, volume=data.volume, lookback=lookback, smoothing=smoothing)
    return indicator(name, _money_flow)

def reactivity(name: str, lookback: int, smoothing: float=0.0, scale: float=0.6) -> Indicator:
    """Reactivity.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        smoothing: Smoothing multiplier.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        Reactivity :class:`.Indicator`.
    """

    def _reactivity(data: BarData):
        return vect.reactivity(high=data.high, low=data.low, close=data.close, volume=data.volume, lookback=lookback, smoothing=smoothing, scale=scale)
    return indicator(name, _reactivity)

def price_volume_fit(name: str, lookback: int, scale: float=9.0) -> Indicator:
    """Price Volume Fit.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``9.0``.

    Returns:
        Price Volume Fit :class:`.Indicator`.
    """

    def _price_volume_fit(data: BarData):
        return vect.price_volume_fit(close=data.close, volume=data.volume, lookback=lookback, scale=scale)
    return indicator(name, _price_volume_fit)

def volume_weighted_ma_ratio(name: str, lookback: int, scale: float=1.0) -> Indicator:
    """Volume-Weighted Moving Average Ratio.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        Volume-Weighted Moving Average Ratio :class:`.Indicator`.
    """

    def _volume_weighted_ma_ratio(data: BarData):
        return vect.volume_weighted_ma_ratio(close=data.close, volume=data.volume, lookback=lookback, scale=scale)
    return indicator(name, _volume_weighted_ma_ratio)

def normalized_on_balance_volume(name: str, lookback: int, scale: float=0.6) -> Indicator:
    """Normalized On-Balance Volume.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        Normalized On-Balance Volume :class:`.Indicator`.
    """

    def _normalized_on_balance_volume(data: BarData):
        return vect.normalized_on_balance_volume(close=data.close, volume=data.volume, lookback=lookback, scale=scale)
    return indicator(name, _normalized_on_balance_volume)

def delta_on_balance_volume(name: str, lookback: int, delta_length: int=0, scale: float=0.6) -> Indicator:
    """Delta On-Balance Volume.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        delta_length: Lag for differencing.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        Delta On-Balance Volume :class:`.Indicator`.
    """

    def _delta_on_balance_volume(data: BarData):
        return vect.delta_on_balance_volume(close=data.close, volume=data.volume, lookback=lookback, delta_length=delta_length, scale=scale)
    return indicator(name, _delta_on_balance_volume)

def normalized_positive_volume_index(name: str, lookback: int, scale: float=0.5) -> Indicator:
    """Normalized Positive Volume Index.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.5``.

    Returns:
        Normalized Positive Volume Index :class:`.Indicator`.
    """

    def _normalized_positive_volume_index(data: BarData):
        return vect.normalized_positive_volume_index(close=data.close, volume=data.volume, lookback=lookback, scale=scale)
    return indicator(name, _normalized_positive_volume_index)

def normalized_negative_volume_index(name: str, lookback: int, scale: float=0.5) -> Indicator:
    """Normalized Negative Volume Index.

    Args:
        name: Indicator name.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.5``.

    Returns:
        Normalized Negative Volume Index :class:`.Indicator`.
    """

    def _normalized_negative_volume_index(data: BarData):
        return vect.normalized_negative_volume_index(close=data.close, volume=data.volume, lookback=lookback, scale=scale)
    return indicator(name, _normalized_negative_volume_index)

def volume_momentum(name: str, short_length: int, multiplier: int=2, scale: float=3.0) -> Indicator:
    """Volume Momentum.

    Args:
        name: Indicator name.
        short_length: Number of short lookback bars.
        multiplier: Lookback multiplier. Defaults to ``2``.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``3.0``.

    Returns:
        Volume Momentum :class:`.Indicator`.
    """

    def _volume_momentum(data: BarData):
        return vect.volume_momentum(volume=data.volume, short_length=short_length, multiplier=multiplier, scale=scale)
    return indicator(name, _volume_momentum)

def laguerre_rsi(name: str, fe_length: int=13) -> Indicator:
    """Laguerre Relative Strength Index (RSI).

    Args:
        name: Indicator name.
        fe_length: Fractal Energy length. Defaults to ``13``.

    Returns:
        Laguerre RSI :class:`.Indicator`.
    """

    def _laguerre_rsi(data: BarData):
        return vect.laguerre_rsi(open=data.open, high=data.high, low=data.low, close=data.close, fe_length=fe_length)
    return indicator(name, _laguerre_rsi)

@pytest.fixture()
def hhv_ind(scope):
    return indicator('hhv', lambda bar_data, n: highv(bar_data.close, n), n=5)

@pytest.fixture()
def llv_ind(scope):
    return indicator('llv', lambda bar_data, n: lowv(bar_data.close, n), n=3)

@pytest.fixture()
def sumv_ind(scope):
    return indicator('sumv', lambda bar_data, n: sumv(bar_data.close, n), n=2)

@pytest.mark.parametrize('field, port_field', [('total_equity', 'equity'), ('cash', 'cash'), ('total_margin', 'margin'), ('total_market_value', 'market_value')])
def test_portfolio_field(ctx, portfolio, field, port_field):
    assert getattr(ctx, field) == getattr(portfolio, port_field)

def test_indicator(ctx, end_index):
    assert len(ctx.indicator('hhv')) == end_index

@pytest.mark.parametrize('pos_type', ['long', 'short'])
def test_position(ctx_with_pos, pos_type, portfolio, symbol):
    assert getattr(ctx_with_pos, f'{pos_type}_pos')() == getattr(portfolio, f'{pos_type}_positions')[symbol]

@pytest.mark.parametrize('pos_fn', ['long_pos', 'short_pos'])
def test_position_when_empty(ctx, pos_fn):
    assert getattr(ctx, pos_fn)() is None

@pytest.mark.parametrize('pos_type', ['long', 'short'])
def test_position_with_foreign_when_empty(ctx, pos_type, foreign):
    assert getattr(ctx, f'{pos_type}_pos')(foreign) is None

class TestEvaluateMixin:

    @pytest.mark.parametrize('bars_per_year, expected_sharpe, expected_sortino', [(None, 0.026013464180574847, 0.02727734785007549), (252, 0.026013464180574847 * np.sqrt(252), 0.02727734785007549 * np.sqrt(252))])
    @pytest.mark.parametrize('bootstrap_sample_size, bootstrap_samples', [(10, 100), (100000, 100)])
    def test_evaluate(self, bootstrap_sample_size, bootstrap_samples, portfolio_df, trades_df, calc_bootstrap, bars_per_year, expected_sharpe, expected_sortino):
        mixin = EvaluateMixin()
        result = mixin.evaluate(portfolio_df, trades_df, calc_bootstrap, bootstrap_sample_size=bootstrap_sample_size, bootstrap_samples=bootstrap_samples, bars_per_year=bars_per_year)
        assert result.metrics is not None
        if not calc_bootstrap:
            assert result.bootstrap is None
        else:
            assert result.bootstrap is not None
            assert result.bootstrap.conf_intervals is not None
            assert result.bootstrap.drawdown_conf is not None
            assert result.bootstrap.profit_factor is not None
            assert result.bootstrap.sharpe is not None
            assert result.bootstrap.drawdown is not None
            ci = result.bootstrap.conf_intervals
            assert ci.columns.tolist() == ['lower', 'upper']
            names = ci.index.get_level_values(0).unique().tolist()
            assert names == ['Profit Factor', 'Sharpe Ratio']
            for name in names:
                df = ci[ci.index.get_level_values(0) == name]
                confs = df.index.get_level_values(1).tolist()
                assert confs == ['97.5%', '95%', '90%']
            dd = result.bootstrap.drawdown_conf
            assert dd.columns.tolist() == ['amount', 'percent']
            conf = dd.index.get_level_values(0).tolist()
            assert conf == ['99.9%', '99%', '95%', '90%']
        metrics = result.metrics
        assert metrics.initial_market_value == 500000
        assert metrics.end_market_value == 693111.87
        assert metrics.total_pnl == 165740.2
        assert metrics.unrealized_pnl == metrics.end_market_value - metrics.initial_market_value - metrics.total_pnl
        assert metrics.total_return_pct == 33.14804
        assert metrics.total_profit == 403511.07999999996
        assert metrics.total_loss == -237770.88
        assert metrics.max_drawdown == -56721.59999999998
        assert metrics.max_drawdown_pct == -7.908428778116649
        assert metrics.max_drawdown_date == datetime(2022, 1, 25, 5, 0)
        assert metrics.win_rate == 52.57731958762887
        assert metrics.loss_rate == 47.42268041237113
        assert metrics.winning_trades == 204
        assert metrics.losing_trades == 184
        assert metrics.avg_pnl == 427.1654639175258
        assert metrics.avg_return_pct == 0.279639175257732
        assert metrics.avg_trade_bars == 2.4149484536082473
        assert metrics.avg_profit == 1977.9954901960782
        assert metrics.avg_profit_pct == 3.1687745098039217
        assert metrics.avg_winning_trade_bars == 2.465686274509804
        assert metrics.avg_loss == -1292.233043478261
        assert metrics.avg_loss_pct == -2.9235326086956523
        assert metrics.avg_losing_trade_bars == 2.358695652173913
        assert metrics.largest_win == 21069.63
        assert metrics.largest_win_pct == 14.49
        assert metrics.largest_win_bars == 3
        assert metrics.largest_loss == -11487.43
        assert metrics.largest_loss_pct == -6.49
        assert metrics.largest_loss_bars == 3
        assert metrics.max_wins == 7
        assert metrics.max_losses == 7
        assert metrics.sharpe == expected_sharpe
        assert metrics.sortino == expected_sortino
        assert metrics.profit_factor == 1.0759385033768167
        assert metrics.ulcer_index == 1.898347959437099
        assert metrics.upi == 0.01844528848501509
        assert metrics.equity_r2 == 0.8979045919638434
        assert metrics.std_error == 69646.36129687089
        assert metrics.total_fees == 0
        if bars_per_year is not None:
            assert metrics.calmar == 1.1557170701224246
            assert truncate(metrics.annual_return_pct, 6) == truncate(5.897743691129764, 6)
            assert metrics.annual_std_error == 1105601.710272446
            assert metrics.annual_volatility_pct == 21.36797425126505
        else:
            assert metrics.calmar is None
            assert metrics.annual_return_pct is None
            assert metrics.annual_std_error is None
            assert metrics.annual_volatility_pct is None

    def test_evaluate_when_portfolio_empty(self, trades_df, calc_bootstrap):
        mixin = EvaluateMixin()
        result = mixin.evaluate(pd.DataFrame(columns=['market_value', 'fees']), trades_df, calc_bootstrap, bootstrap_sample_size=10, bootstrap_samples=100, bars_per_year=None)
        assert result.metrics is not None
        for field in get_type_hints(EvalMetrics):
            if field in ('calmar', 'annual_return_pct', 'annual_std_error', 'annual_volatility_pct', 'max_drawdown_date'):
                assert getattr(result.metrics, field) is None
            else:
                assert getattr(result.metrics, field) == 0
        assert result.bootstrap is None

    def test_evaluate_when_single_market_value(self, trades_df, calc_bootstrap):
        mixin = EvaluateMixin()
        result = mixin.evaluate(pd.DataFrame([[1000, 0]], columns=['market_value', 'fees'], index=[pd.Timestamp('2023-04-12 00:00:00')]), trades_df, calc_bootstrap, bootstrap_sample_size=10, bootstrap_samples=100, bars_per_year=None)
        assert result.metrics is not None
        for field in get_type_hints(EvalMetrics):
            if field in ('calmar', 'annual_return_pct', 'annual_std_error', 'annual_volatility_pct', 'max_drawdown_date'):
                assert getattr(result.metrics, field) is None
            else:
                assert getattr(result.metrics, field) == 0
        assert result.bootstrap is None

    def test_evaluate_when_trades_empty(self, portfolio_df, calc_bootstrap):
        mixin = EvaluateMixin()
        result = mixin.evaluate(portfolio_df, pd.DataFrame(columns=['pnl', 'return_pct', 'bars']), calc_bootstrap, bootstrap_sample_size=10, bootstrap_samples=100, bars_per_year=None)
        metrics = result.metrics
        assert metrics is not None
        assert metrics.total_pnl == 0
        assert metrics.total_return_pct == 0
        assert metrics.total_profit == 0
        assert metrics.total_loss == 0
        assert metrics.win_rate == 0
        assert metrics.loss_rate == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0
        assert metrics.avg_pnl == 0
        assert metrics.avg_return_pct == 0
        assert metrics.avg_trade_bars == 0
        assert metrics.avg_profit == 0
        assert metrics.avg_profit_pct == 0
        assert metrics.avg_winning_trade_bars == 0
        assert metrics.avg_loss == 0
        assert metrics.avg_loss_pct == 0
        assert metrics.avg_losing_trade_bars == 0
        assert metrics.largest_win == 0
        assert metrics.largest_win_pct == 0
        assert metrics.largest_win_bars == 0
        assert metrics.largest_loss == 0
        assert metrics.largest_loss_pct == 0
        assert metrics.largest_loss_bars == 0
        assert metrics.max_wins == 0
        assert metrics.max_losses == 0
        assert metrics.total_fees == 0
        if calc_bootstrap:
            assert result.bootstrap is not None
            assert result.bootstrap.conf_intervals is not None
            assert result.bootstrap.drawdown_conf is not None
            assert result.bootstrap.profit_factor is not None
            assert result.bootstrap.sharpe is not None
            assert result.bootstrap.drawdown is not None
        else:
            assert result.bootstrap is None

@pytest.mark.parametrize('bars_per_year, expected_sharpe, expected_sortino', [(None, 0.026013464180574847, 0.02727734785007549), (252, 0.026013464180574847 * np.sqrt(252), 0.02727734785007549 * np.sqrt(252))])
@pytest.mark.parametrize('bootstrap_sample_size, bootstrap_samples', [(10, 100), (100000, 100)])
def test_evaluate(self, bootstrap_sample_size, bootstrap_samples, portfolio_df, trades_df, calc_bootstrap, bars_per_year, expected_sharpe, expected_sortino):
    mixin = EvaluateMixin()
    result = mixin.evaluate(portfolio_df, trades_df, calc_bootstrap, bootstrap_sample_size=bootstrap_sample_size, bootstrap_samples=bootstrap_samples, bars_per_year=bars_per_year)
    assert result.metrics is not None
    if not calc_bootstrap:
        assert result.bootstrap is None
    else:
        assert result.bootstrap is not None
        assert result.bootstrap.conf_intervals is not None
        assert result.bootstrap.drawdown_conf is not None
        assert result.bootstrap.profit_factor is not None
        assert result.bootstrap.sharpe is not None
        assert result.bootstrap.drawdown is not None
        ci = result.bootstrap.conf_intervals
        assert ci.columns.tolist() == ['lower', 'upper']
        names = ci.index.get_level_values(0).unique().tolist()
        assert names == ['Profit Factor', 'Sharpe Ratio']
        for name in names:
            df = ci[ci.index.get_level_values(0) == name]
            confs = df.index.get_level_values(1).tolist()
            assert confs == ['97.5%', '95%', '90%']
        dd = result.bootstrap.drawdown_conf
        assert dd.columns.tolist() == ['amount', 'percent']
        conf = dd.index.get_level_values(0).tolist()
        assert conf == ['99.9%', '99%', '95%', '90%']
    metrics = result.metrics
    assert metrics.initial_market_value == 500000
    assert metrics.end_market_value == 693111.87
    assert metrics.total_pnl == 165740.2
    assert metrics.unrealized_pnl == metrics.end_market_value - metrics.initial_market_value - metrics.total_pnl
    assert metrics.total_return_pct == 33.14804
    assert metrics.total_profit == 403511.07999999996
    assert metrics.total_loss == -237770.88
    assert metrics.max_drawdown == -56721.59999999998
    assert metrics.max_drawdown_pct == -7.908428778116649
    assert metrics.max_drawdown_date == datetime(2022, 1, 25, 5, 0)
    assert metrics.win_rate == 52.57731958762887
    assert metrics.loss_rate == 47.42268041237113
    assert metrics.winning_trades == 204
    assert metrics.losing_trades == 184
    assert metrics.avg_pnl == 427.1654639175258
    assert metrics.avg_return_pct == 0.279639175257732
    assert metrics.avg_trade_bars == 2.4149484536082473
    assert metrics.avg_profit == 1977.9954901960782
    assert metrics.avg_profit_pct == 3.1687745098039217
    assert metrics.avg_winning_trade_bars == 2.465686274509804
    assert metrics.avg_loss == -1292.233043478261
    assert metrics.avg_loss_pct == -2.9235326086956523
    assert metrics.avg_losing_trade_bars == 2.358695652173913
    assert metrics.largest_win == 21069.63
    assert metrics.largest_win_pct == 14.49
    assert metrics.largest_win_bars == 3
    assert metrics.largest_loss == -11487.43
    assert metrics.largest_loss_pct == -6.49
    assert metrics.largest_loss_bars == 3
    assert metrics.max_wins == 7
    assert metrics.max_losses == 7
    assert metrics.sharpe == expected_sharpe
    assert metrics.sortino == expected_sortino
    assert metrics.profit_factor == 1.0759385033768167
    assert metrics.ulcer_index == 1.898347959437099
    assert metrics.upi == 0.01844528848501509
    assert metrics.equity_r2 == 0.8979045919638434
    assert metrics.std_error == 69646.36129687089
    assert metrics.total_fees == 0
    if bars_per_year is not None:
        assert metrics.calmar == 1.1557170701224246
        assert truncate(metrics.annual_return_pct, 6) == truncate(5.897743691129764, 6)
        assert metrics.annual_std_error == 1105601.710272446
        assert metrics.annual_volatility_pct == 21.36797425126505
    else:
        assert metrics.calmar is None
        assert metrics.annual_return_pct is None
        assert metrics.annual_std_error is None
        assert metrics.annual_volatility_pct is None

def test_evaluate_when_portfolio_empty(self, trades_df, calc_bootstrap):
    mixin = EvaluateMixin()
    result = mixin.evaluate(pd.DataFrame(columns=['market_value', 'fees']), trades_df, calc_bootstrap, bootstrap_sample_size=10, bootstrap_samples=100, bars_per_year=None)
    assert result.metrics is not None
    for field in get_type_hints(EvalMetrics):
        if field in ('calmar', 'annual_return_pct', 'annual_std_error', 'annual_volatility_pct', 'max_drawdown_date'):
            assert getattr(result.metrics, field) is None
        else:
            assert getattr(result.metrics, field) == 0
    assert result.bootstrap is None

def test_evaluate_when_single_market_value(self, trades_df, calc_bootstrap):
    mixin = EvaluateMixin()
    result = mixin.evaluate(pd.DataFrame([[1000, 0]], columns=['market_value', 'fees'], index=[pd.Timestamp('2023-04-12 00:00:00')]), trades_df, calc_bootstrap, bootstrap_sample_size=10, bootstrap_samples=100, bars_per_year=None)
    assert result.metrics is not None
    for field in get_type_hints(EvalMetrics):
        if field in ('calmar', 'annual_return_pct', 'annual_std_error', 'annual_volatility_pct', 'max_drawdown_date'):
            assert getattr(result.metrics, field) is None
        else:
            assert getattr(result.metrics, field) == 0
    assert result.bootstrap is None

def test_evaluate_when_trades_empty(self, portfolio_df, calc_bootstrap):
    mixin = EvaluateMixin()
    result = mixin.evaluate(portfolio_df, pd.DataFrame(columns=['pnl', 'return_pct', 'bars']), calc_bootstrap, bootstrap_sample_size=10, bootstrap_samples=100, bars_per_year=None)
    metrics = result.metrics
    assert metrics is not None
    assert metrics.total_pnl == 0
    assert metrics.total_return_pct == 0
    assert metrics.total_profit == 0
    assert metrics.total_loss == 0
    assert metrics.win_rate == 0
    assert metrics.loss_rate == 0
    assert metrics.winning_trades == 0
    assert metrics.losing_trades == 0
    assert metrics.avg_pnl == 0
    assert metrics.avg_return_pct == 0
    assert metrics.avg_trade_bars == 0
    assert metrics.avg_profit == 0
    assert metrics.avg_profit_pct == 0
    assert metrics.avg_winning_trade_bars == 0
    assert metrics.avg_loss == 0
    assert metrics.avg_loss_pct == 0
    assert metrics.avg_losing_trade_bars == 0
    assert metrics.largest_win == 0
    assert metrics.largest_win_pct == 0
    assert metrics.largest_win_bars == 0
    assert metrics.largest_loss == 0
    assert metrics.largest_loss_pct == 0
    assert metrics.largest_loss_bars == 0
    assert metrics.max_wins == 0
    assert metrics.max_losses == 0
    assert metrics.total_fees == 0
    if calc_bootstrap:
        assert result.bootstrap is not None
        assert result.bootstrap.conf_intervals is not None
        assert result.bootstrap.drawdown_conf is not None
        assert result.bootstrap.profit_factor is not None
        assert result.bootstrap.sharpe is not None
        assert result.bootstrap.drawdown is not None
    else:
        assert result.bootstrap is None

