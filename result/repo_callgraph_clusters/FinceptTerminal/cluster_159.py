# Cluster 159

def notify_data_update(data_type: str, count: int, module: Optional[str]='market') -> bool:
    """Notify data update"""
    return notifier.data_update(data_type, count, module)

