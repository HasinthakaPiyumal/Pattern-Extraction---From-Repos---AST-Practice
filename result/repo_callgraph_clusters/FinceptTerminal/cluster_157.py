# Cluster 157

def notify_price_alert(symbol: str, current_price: float, target_price: float, condition: str, module: Optional[str]='alerts') -> bool:
    """Notify price alert"""
    return notifier.price_alert(symbol, current_price, target_price, condition, module)

