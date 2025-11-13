# Cluster 79

def detect_business_cycle_phase(economic_indicators):
    """Quick business cycle phase detection"""
    analyzer = BusinessCycleAnalyzer()
    return analyzer.detect_phase(economic_indicators)

