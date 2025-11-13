# Cluster 38

def get_anonymizer_engine() -> AnonymizerEngine:
    """Get or create singleton AnonymizerEngine instance."""
    global _anonymizer_engine
    if _anonymizer_engine is None:
        _anonymizer_engine = AnonymizerEngine()
        _anonymizer_engine.add_anonymizer(InstanceCounterAnonymizer)
    return _anonymizer_engine

