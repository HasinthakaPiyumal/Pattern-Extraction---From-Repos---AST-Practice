# Cluster 8

def _volume_momentum(data: BarData):
    return vect.volume_momentum(volume=data.volume, short_length=short_length, multiplier=multiplier, scale=scale)

