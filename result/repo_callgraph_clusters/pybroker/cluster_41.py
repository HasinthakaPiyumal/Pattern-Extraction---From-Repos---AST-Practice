# Cluster 41

def _close_minus_ma(data: BarData):
    return vect.close_minus_ma(high=data.high, low=data.low, close=data.close, lookback=lookback, atr_length=atr_length, scale=scale)

