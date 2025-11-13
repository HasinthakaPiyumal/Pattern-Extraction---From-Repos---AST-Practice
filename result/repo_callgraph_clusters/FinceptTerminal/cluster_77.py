# Cluster 77

def calculate_gdp_growth(gdp_data, method='solow'):
    """Quick GDP growth decomposition"""
    analyzer = GrowthAnalyzer()
    return analyzer.decompose_growth(gdp_data, method)

