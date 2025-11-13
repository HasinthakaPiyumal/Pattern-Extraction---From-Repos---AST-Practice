# Cluster 52

def _normalized_negative_volume_index(data: BarData):
    return vect.normalized_negative_volume_index(close=data.close, volume=data.volume, lookback=lookback, scale=scale)

