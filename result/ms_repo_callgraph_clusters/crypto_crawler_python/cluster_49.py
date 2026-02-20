# Cluster 49

def adjust_maximum_volume_by_trading_cap(deal_cap, volume):
    if deal_cap.get_max_volume_cap() == NO_MAX_CAP_LIMIT:
        return volume
    if volume > deal_cap.get_max_volume_cap():
        return deal_cap.get_max_volume_cap()
    return volume

# Node: get_max_volume_cap
