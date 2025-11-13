# Cluster 43

def _price_change_oscillator(data: BarData):
    return vect.price_change_oscillator(high=data.high, low=data.low, close=data.close, short_length=short_length, multiplier=multiplier, scale=scale)

