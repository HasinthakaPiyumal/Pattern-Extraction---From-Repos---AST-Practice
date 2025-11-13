# Cluster 45

def _money_flow(data: BarData):
    return vect.money_flow(high=data.high, low=data.low, close=data.close, volume=data.volume, lookback=lookback, smoothing=smoothing)

