# Cluster 35

def _macd(data: BarData):
    return vect.macd(high=data.high, low=data.low, close=data.close, short_length=short_length, long_length=long_length, smoothing=smoothing, scale=scale)

