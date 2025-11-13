# Cluster 27

@njit
def normalized_on_balance_volume(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, scale: float=0.6) -> NDArray[np.float64]:
    """Computes Normalized On-Balance Volume.

    Args:
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _on_balance_volume(close, volume, lookback, 0, scale, 'normalized')

@njit
def delta_on_balance_volume(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, delta_length: int=0, scale: float=0.6) -> NDArray[np.float64]:
    """Computes Delta On-Balance Volume.

    Args:
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        delta_length: Lag for differencing.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.6``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _on_balance_volume(close, volume, lookback, delta_length, scale, 'delta')

