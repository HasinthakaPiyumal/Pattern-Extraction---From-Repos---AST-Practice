# Cluster 46

def _reactivity(data: BarData):
    return vect.reactivity(high=data.high, low=data.low, close=data.close, volume=data.volume, lookback=lookback, smoothing=smoothing, scale=scale)

