# Cluster 28

@njit
def normalized_positive_volume_index(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, scale: float=0.5) -> NDArray[np.float64]:
    """Computes Normalized Positive Volume Index.

    Args:
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.5``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _normalized_volume_index(close, volume, lookback, scale, 'positive')

@njit
def normalized_negative_volume_index(close: NDArray[np.float64], volume: NDArray[np.float64], lookback: int, scale: float=0.5) -> NDArray[np.float64]:
    """Computes Normalized Negative Volume Index.

    Args:
        close: Close prices.
        volume: Trading volume.
        lookback: Number of lookback bars.
        scale: Increase > 1.0 for more compression of return values,
            decrease < 1.0 for less. Defaults to ``0.5``.

    Returns:
        :class:`numpy.ndarray` of computed values ranging [-50, 50].
    """
    return _normalized_volume_index(close, volume, lookback, scale, 'negative')

