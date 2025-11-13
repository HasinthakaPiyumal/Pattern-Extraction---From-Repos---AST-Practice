# Cluster 24

@njit
def aroon_up(high: NDArray[np.float64], low: NDArray[np.float64], lookback: int) -> NDArray[np.float64]:
    """Computes Aroon Upward Trend.

    Args:
        high: High prices.
        low: Low prices.
        lookback: Number of lookback bars.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    return _aroon(high, low, lookback, 'up')

@njit
def aroon_down(high: NDArray[np.float64], low: NDArray[np.float64], lookback: int) -> NDArray[np.float64]:
    """Computes Aroon Downward Trend.

    Args:
        high: High prices.
        low: Low prices.
        lookback: Number of lookback bars.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    return _aroon(high, low, lookback, 'down')

@njit
def aroon_diff(high: NDArray[np.float64], low: NDArray[np.float64], lookback: int) -> NDArray[np.float64]:
    """Computes Aroon Upward Trend minus Aroon Downward Trend.

    Args:
        high: High prices.
        low: Low prices.
        lookback: Number of lookback bars.

    Returns:
        :class:`numpy.ndarray` of computed values.
    """
    return _aroon(high, low, lookback, 'diff')

