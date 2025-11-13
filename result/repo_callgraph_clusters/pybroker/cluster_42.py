# Cluster 42

def _price_intensity(data: BarData):
    return vect.price_intensity(open=data.open, high=data.high, low=data.low, close=data.close, smoothing=smoothing, scale=scale)

