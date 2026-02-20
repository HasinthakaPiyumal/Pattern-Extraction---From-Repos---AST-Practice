# Cluster 41

def adjust_minimum_volume_by_trading_cap(deal_cap, min_volume):
    if min_volume < deal_cap.get_min_volume_cap():
        min_volume = -1
    return min_volume

# Node: get_min_volume_cap
