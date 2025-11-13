# Cluster 191

def create_default_citadel_signal():
    return CitadelSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', strategy_allocation={'equity_long_short': 0.4, 'quantitative': 0.25, 'global_macro': 0.15, 'market_making': 0.1, 'convertible_arbitrage': 0.1})

