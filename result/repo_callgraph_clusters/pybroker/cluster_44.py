# Cluster 44

def _intraday_intensity(data: BarData):
    return vect.intraday_intensity(high=data.high, low=data.low, close=data.close, volume=data.volume, lookback=lookback, smoothing=smoothing)

