# Cluster 158

def notify_connection_status(service: str, status: str, module: Optional[str]='api') -> bool:
    """Notify connection status"""
    return notifier.connection_status(service, status, module)

