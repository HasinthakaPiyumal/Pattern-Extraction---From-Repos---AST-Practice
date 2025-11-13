# Cluster 16

def _laguerre_rsi(data: BarData):
    return vect.laguerre_rsi(open=data.open, high=data.high, low=data.low, close=data.close, fe_length=fe_length)

