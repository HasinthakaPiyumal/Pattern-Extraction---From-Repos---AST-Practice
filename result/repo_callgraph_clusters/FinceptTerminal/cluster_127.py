# Cluster 127

def quick_industry_analysis(company_data: CompanyData) -> Dict[str, Any]:
    """Quick industry analysis"""
    analyzer = IndustryAnalyzer()
    return analyzer.analyze_company(company_data)

