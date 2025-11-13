# Cluster 178

def create_default_aqr_signal():
    return AQRSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', factor_exposures={'value': 0.5, 'momentum': 0.5, 'quality': 0.5, 'low_volatility': 0.5, 'profitability': 0.5, 'combined_factor_score': 0.5})

