# Cluster 47

def _price_volume_fit(data: BarData):
    return vect.price_volume_fit(close=data.close, volume=data.volume, lookback=lookback, scale=scale)

