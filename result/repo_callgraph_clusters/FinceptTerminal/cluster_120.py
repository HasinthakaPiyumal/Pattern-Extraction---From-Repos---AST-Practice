# Cluster 120

def calculate_justified_pb_ratio(roe: float, required_return: float, growth_rate: float) -> float:
    """Quick justified P/B ratio calculation"""
    analyzer = ResidualIncomeAnalyzer()
    return analyzer.calculate_fundamental_pb_ratio(roe, required_return, growth_rate)

