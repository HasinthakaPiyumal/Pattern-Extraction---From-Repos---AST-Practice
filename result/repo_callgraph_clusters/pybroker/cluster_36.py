# Cluster 36

def _stochastic(data: BarData):
    return vect.stochastic(high=data.high, low=data.low, close=data.close, lookback=lookback, smoothing=smoothing)

