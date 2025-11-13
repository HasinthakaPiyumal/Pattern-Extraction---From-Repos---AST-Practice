# Cluster 25

@njit
def linear_deviation(values: NDArray[np.float64], lookback: int, scale: float=0.6) -> NDArray[np.float64]:
    """Computes Deviation from Linear Trend.

    Args:
        values: :class:`numpy.ndarray` of input.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _deviation(values, lookback, scale, 'linear')

@njit
def quadratic_deviation(values: NDArray[np.float64], lookback: int, scale: float=0.6) -> NDArray[np.float64]:
    """Computes Deviation from Quadratic Trend.

    Args:
        values: :class:`numpy.ndarray` of input.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _deviation(values, lookback, scale, 'quadratic')

@njit
def cubic_deviation(values: NDArray[np.float64], lookback: int, scale: float=0.6) -> NDArray[np.float64]:
    """Computes Deviation from Cubic Trend.

    Args:
        values: :class:`numpy.ndarray` of input.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _deviation(values, lookback, scale, 'cubic')

