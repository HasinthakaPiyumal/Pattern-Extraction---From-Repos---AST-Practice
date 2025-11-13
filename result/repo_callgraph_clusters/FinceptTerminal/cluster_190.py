# Cluster 190

def create_default_two_sigma_signal():
    return TwoSigmaSignal(signal='neutral', confidence=0.0, reasoning='Analysis error, defaulting to neutral', ml_model_predictions={'ensemble_prediction': 0.5, 'model_confidence': 0.0, 'random_forest': 0.5, 'gradient_boosting': 0.5, 'neural_network': 0.5, 'lstm': 0.5})

