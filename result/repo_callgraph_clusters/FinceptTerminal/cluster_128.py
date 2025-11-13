# Cluster 128

def porters_five_forces(company_data: CompanyData) -> PortersFiveForcesAnalysis:
    """Quick Porter's Five Forces analysis"""
    analyzer = PortersFiveForcesAnalyzer()
    return analyzer.analyze_five_forces(company_data)

