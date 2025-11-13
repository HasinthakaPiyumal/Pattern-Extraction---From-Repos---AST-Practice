# Cluster 156

def notify_trade_executed(symbol: str, action: str, quantity: int, price: float, module: Optional[str]='trading') -> bool:
    """Notify trade execution"""
    return notifier.trade_executed(symbol, action, quantity, price, module)

