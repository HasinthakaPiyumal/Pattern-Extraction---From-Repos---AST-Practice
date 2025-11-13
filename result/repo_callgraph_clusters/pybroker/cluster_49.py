# Cluster 49

def _normalized_on_balance_volume(data: BarData):
    return vect.normalized_on_balance_volume(close=data.close, volume=data.volume, lookback=lookback, scale=scale)

