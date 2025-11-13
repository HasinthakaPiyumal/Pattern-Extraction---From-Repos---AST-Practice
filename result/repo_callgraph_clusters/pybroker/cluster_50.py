# Cluster 50

def _delta_on_balance_volume(data: BarData):
    return vect.delta_on_balance_volume(close=data.close, volume=data.volume, lookback=lookback, delta_length=delta_length, scale=scale)

