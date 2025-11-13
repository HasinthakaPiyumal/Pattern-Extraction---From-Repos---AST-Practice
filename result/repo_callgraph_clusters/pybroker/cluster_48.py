# Cluster 48

def _volume_weighted_ma_ratio(data: BarData):
    return vect.volume_weighted_ma_ratio(close=data.close, volume=data.volume, lookback=lookback, scale=scale)

