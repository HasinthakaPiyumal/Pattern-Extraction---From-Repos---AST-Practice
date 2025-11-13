# Cluster 160

def notify_system_status(component: str, status: str, details: str='', module: Optional[str]='main') -> bool:
    """Notify system status"""
    return notifier.system_status(component, status, details, module)

