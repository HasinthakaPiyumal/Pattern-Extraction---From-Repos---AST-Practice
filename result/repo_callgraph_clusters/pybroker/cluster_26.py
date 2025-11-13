# Cluster 26

@njit
def intraday_intensity(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, smoothing: float=0.0) -> NDArray[np.float64]:
    """Computes Intraday Intensity.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        smoothing: Amount of smoothing; <= 1 for none. Defaults to ``0``.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    return _flow(high, low, close, volume, lookback, smoothing, 'intraday')

@njit
def money_flow(high: NDArray[np.float64], low: NDArray[np.float64], close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, smoothing: float=0.0) -> NDArray[np.float64]:
    """Computes Chaikin's Money Flow.

    Args:
        high: High prices.
        low: Low prices.
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        smoothing: Amount of smoothing; <= 1 for none. Defaults to ``0``.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    return _flow(high, low, close, volume, lookback, smoothing, 'money_flow')

