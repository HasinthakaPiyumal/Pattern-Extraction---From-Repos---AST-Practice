# Cluster 52

class ConstraintsAnalysis:
    """Investment constraints analysis and management"""

    @staticmethod
    def analyze_liquidity_constraints(client_profile: InvestorProfile, cash_flow_data: Dict) -> Dict:
        """Analyze liquidity requirements and constraints"""
        liquidity_needs = ConstraintsAnalysis._calculate_liquidity_needs(client_profile, cash_flow_data)
        liquidity_sources = ConstraintsAnalysis._assess_liquidity_sources(cash_flow_data)
        liquidity_constraints = ConstraintsAnalysis._set_liquidity_constraints(liquidity_needs, liquidity_sources)
        return {'liquidity_needs': liquidity_needs, 'liquidity_sources': liquidity_sources, 'liquidity_constraints': liquidity_constraints, 'emergency_fund_requirement': ConstraintsAnalysis._calculate_emergency_fund(client_profile, cash_flow_data)}

    @staticmethod
    def analyze_time_horizon_constraints(client_profile: InvestorProfile) -> Dict:
        """Analyze time horizon constraints"""
        primary_horizon = client_profile.time_horizon
        sub_periods = ConstraintsAnalysis._identify_sub_periods(client_profile)
        allocation_implications = ConstraintsAnalysis._time_horizon_allocation_implications(primary_horizon, sub_periods)
        return {'primary_time_horizon': primary_horizon, 'horizon_category': 'Long' if primary_horizon > 10 else 'Medium' if primary_horizon > 5 else 'Short', 'sub_periods': sub_periods, 'allocation_implications': allocation_implications, 'glide_path_considerations': ConstraintsAnalysis._assess_glide_path_needs(primary_horizon, sub_periods)}

    @staticmethod
    def analyze_tax_constraints(client_profile: InvestorProfile) -> Dict:
        """Analyze tax considerations and constraints"""
        tax_situation = client_profile.tax_situation
        tax_strategies = ConstraintsAnalysis._identify_tax_strategies(tax_situation)
        account_recommendations = ConstraintsAnalysis._recommend_account_types(tax_situation, client_profile)
        asset_location = ConstraintsAnalysis._develop_asset_location_strategy(tax_situation)
        return {'tax_situation_analysis': tax_situation, 'tax_efficiency_strategies': tax_strategies, 'account_recommendations': account_recommendations, 'asset_location_strategy': asset_location, 'tax_loss_harvesting': ConstraintsAnalysis._assess_tax_loss_harvesting(tax_situation)}

    @staticmethod
    def analyze_legal_regulatory_constraints(client_profile: InvestorProfile) -> Dict:
        """Analyze legal and regulatory constraints"""
        applicable_regulations = ConstraintsAnalysis._identify_applicable_regulations(client_profile)
        compliance_requirements = ConstraintsAnalysis._assess_compliance_requirements(applicable_regulations, client_profile)
        prohibited_investments = ConstraintsAnalysis._identify_prohibited_investments(applicable_regulations, client_profile)
        return {'applicable_regulations': applicable_regulations, 'compliance_requirements': compliance_requirements, 'prohibited_investments': prohibited_investments, 'reporting_obligations': ConstraintsAnalysis._identify_reporting_obligations(applicable_regulations)}

    @staticmethod
    def _calculate_liquidity_needs(client_profile: InvestorProfile, cash_flow_data: Dict) -> Dict:
        """Calculate specific liquidity needs"""
        annual_expenses = cash_flow_data.get('annual_expenses', 50000)
        irregular_expenses = cash_flow_data.get('irregular_expenses', [])
        emergency_fund = annual_expenses * 0.5
        planned_expenses = sum((expense.get('amount', 0) for expense in irregular_expenses))
        total_liquidity = emergency_fund + planned_expenses
        return {'emergency_fund_need': emergency_fund, 'planned_expenses': planned_expenses, 'total_liquidity_need': total_liquidity, 'liquidity_percentage': client_profile.liquidity_needs, 'liquidity_timeline': ConstraintsAnalysis._create_liquidity_timeline(irregular_expenses)}

    @staticmethod
    def _identify_sub_periods(client_profile: InvestorProfile) -> List[Dict]:
        """Identify investment sub-periods with different characteristics"""
        sub_periods = []
        if client_profile.investor_type == InvestorType.INDIVIDUAL:
            if hasattr(client_profile, 'age'):
                age = client_profile.age
                if age < 45:
                    sub_periods.append({'period': 'Accumulation phase', 'years': max(1, 45 - age), 'characteristics': 'High risk tolerance, growth focus'})
                if 45 <= age < 65:
                    sub_periods.append({'period': 'Consolidation phase', 'years': max(1, 65 - age), 'characteristics': 'Moderate risk, balanced approach'})
                if age >= 55:
                    sub_periods.append({'period': 'Pre-retirement', 'years': max(1, 65 - age), 'characteristics': 'Risk reduction, income focus'})
        return sub_periods

@staticmethod
def analyze_time_horizon_constraints(client_profile: InvestorProfile) -> Dict:
    """Analyze time horizon constraints"""
    primary_horizon = client_profile.time_horizon
    sub_periods = ConstraintsAnalysis._identify_sub_periods(client_profile)
    allocation_implications = ConstraintsAnalysis._time_horizon_allocation_implications(primary_horizon, sub_periods)
    return {'primary_time_horizon': primary_horizon, 'horizon_category': 'Long' if primary_horizon > 10 else 'Medium' if primary_horizon > 5 else 'Short', 'sub_periods': sub_periods, 'allocation_implications': allocation_implications, 'glide_path_considerations': ConstraintsAnalysis._assess_glide_path_needs(primary_horizon, sub_periods)}

