# Cluster 51

def _normalized_positive_volume_index(data: BarData):
    return vect.normalized_positive_volume_index(close=data.close, volume=data.volume, lookback=lookback, scale=scale)

