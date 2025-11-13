# Cluster 38

def _aroon_up(data: BarData):
    return vect.aroon_up(high=data.high, low=data.low, lookback=lookback)

