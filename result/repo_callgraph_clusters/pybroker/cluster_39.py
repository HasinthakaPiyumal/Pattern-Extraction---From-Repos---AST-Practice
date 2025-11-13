# Cluster 39

def _aroon_down(data: BarData):
    return vect.aroon_down(high=data.high, low=data.low, lookback=lookback)

