# Cluster 40

def _aroon_diff(data: BarData):
    return vect.aroon_diff(high=data.high, low=data.low, lookback=lookback)

