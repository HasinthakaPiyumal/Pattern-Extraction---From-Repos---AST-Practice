# Cluster 129

def competitive_position_analysis(company_data: CompanyData) -> Dict[str, Any]:
    """Quick competitive position analysis"""
    analyzer = CompetitivePositionAnalyzer()
    return analyzer.analyze_competitive_position(company_data)

