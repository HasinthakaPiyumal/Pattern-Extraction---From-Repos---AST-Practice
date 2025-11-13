# Cluster 188

def create_default_bridgewater_signal():
    return BridgewaterSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', all_weather_allocation={'rising_growth_weight': 0.25, 'falling_growth_weight': 0.25, 'rising_inflation_weight': 0.25, 'falling_inflation_weight': 0.25})

