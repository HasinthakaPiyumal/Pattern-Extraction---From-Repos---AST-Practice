# Cluster 37

def _adx(data: BarData):
    return vect.adx(high=data.high, low=data.low, close=data.close, lookback=lookback)

