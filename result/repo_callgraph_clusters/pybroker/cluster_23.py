# Cluster 23

def linear_trend(values: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int, atr_length: int, scale: float=1.0) -> NDArray[np.float64]:
    """Computes Linear Trend Strength.

    Args:
        values: :class:`numpy.ndarray` of input.
        high: High prices.
        low: Low prices.
        close: Close prices.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _trend(values, high, low, close, lookback, atr_length, scale, 'linear')

def quadratic_trend(values: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int, atr_length: int, scale: float=1.0) -> NDArray[np.float64]:
    """Computes Quadratic Trend Strength.

    Args:
        values: :class:`numpy.ndarray` of input.
        high: High prices.
        low: Low prices.
        close: Close prices.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _trend(values, high, low, close, lookback, atr_length, scale, 'quadratic')

def cubic_trend(values: NDArray[np.float64], high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], lookback: int, atr_length: int, scale: float=1.0) -> NDArray[np.float64]:
    """Computes Cubic Trend Strength.

    Args:
        values: :class:`numpy.ndarray` of input.
        high: High prices.
        low: Low prices.
        close: Close prices.
        lookback: Number of lookback bars.
        atr_length: Lookback length used for Average True Range (ATR)
            normalization.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``1.0``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _trend(values, high, low, close, lookback, atr_length, scale, 'cubic')

