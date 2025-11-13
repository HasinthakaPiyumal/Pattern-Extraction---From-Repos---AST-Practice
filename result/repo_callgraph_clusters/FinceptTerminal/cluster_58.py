# Cluster 58

class PortfolioPlanning:
    """Main portfolio planning and construction interface"""

    def __init__(self):
        self.ips_framework = IPSFramework()
        self.objectives_framework = ObjectivesFramework()
        self.constraints_analysis = ConstraintsAnalysis()
        self.asset_allocation_framework = AssetAllocationFramework()
        self.construction_principles = PortfolioConstructionPrinciples()
        self.esg_integration = ESGIntegration()

    def create_comprehensive_ips(self, client_profile: InvestorProfile, financial_data: Dict, esg_preferences: Optional[Dict]=None) -> InvestmentPolicyStatement:
        """Create comprehensive Investment Policy Statement"""
        return_objectives = self.objectives_framework.analyze_return_objectives(client_profile, financial_data)
        risk_objectives = self.objectives_framework.analyze_risk_objectives(client_profile, return_objectives)
        liquidity_constraints = self.constraints_analysis.analyze_liquidity_constraints(client_profile, financial_data)
        time_horizon_constraints = self.constraints_analysis.analyze_time_horizon_constraints(client_profile)
        tax_constraints = self.constraints_analysis.analyze_tax_constraints(client_profile)
        legal_constraints = self.constraints_analysis.analyze_legal_regulatory_constraints(client_profile)
        asset_classes = self.asset_allocation_framework.define_asset_classes()
        strategic_allocation = self.asset_allocation_framework.strategic_asset_allocation(client_profile, {'return_objectives': return_objectives, 'risk_objectives': risk_objectives}, {'liquidity': liquidity_constraints, 'time_horizon': time_horizon_constraints, 'tax': tax_constraints, 'legal': legal_constraints}, asset_classes)
        esg_policy = None
        if esg_preferences:
            esg_policy = self.esg_integration.develop_esg_policy(client_profile, esg_preferences)
        ips = InvestmentPolicyStatement(client_information=self._compile_client_information(client_profile, financial_data), investment_objectives={'return_objectives': return_objectives, 'risk_objectives': risk_objectives}, investment_constraints={'liquidity': liquidity_constraints, 'time_horizon': time_horizon_constraints, 'tax': tax_constraints, 'legal_regulatory': legal_constraints, 'unique_circumstances': self._analyze_unique_circumstances(client_profile)}, investment_guidelines=self._develop_investment_guidelines(strategic_allocation, client_profile), strategic_asset_allocation=strategic_allocation, rebalancing_policy=self._develop_rebalancing_policy(strategic_allocation), performance_measurement=self._develop_performance_measurement_framework(return_objectives, strategic_allocation), responsibilities=self._define_responsibilities(), review_schedule=self._establish_review_schedule(client_profile), esg_policy=esg_policy)
        return ips

    def validate_and_optimize_ips(self, ips: InvestmentPolicyStatement) -> Dict:
        """Validate and provide optimization recommendations for IPS"""
        validation_results = self.ips_framework.validate_ips(ips)
        optimization_recommendations = self._generate_optimization_recommendations(ips)
        stress_test_results = self._stress_test_ips(ips)
        return {'validation_results': validation_results, 'optimization_recommendations': optimization_recommendations, 'stress_test_results': stress_test_results, 'implementation_roadmap': self._create_implementation_roadmap(ips)}

    def portfolio_construction_analysis(self, ips: InvestmentPolicyStatement, market_conditions: Dict) -> Dict:
        """Comprehensive portfolio construction analysis"""
        construction_framework = self.construction_principles.construction_framework()
        risk_budget_analysis = self.construction_principles.risk_budgeting_approach(ips.investment_objectives['risk_objectives']['overall_risk_tolerance']['overall_risk_tolerance'], ips.strategic_asset_allocation['strategic_allocation'])
        implementation_analysis = self._analyze_implementation_considerations(ips, market_conditions)
        monitoring_framework = self._develop_monitoring_framework(ips)
        return {'construction_framework': construction_framework, 'risk_budget_analysis': risk_budget_analysis, 'implementation_analysis': implementation_analysis, 'monitoring_framework': monitoring_framework, 'success_metrics': self._define_success_metrics(ips)}

    def _compile_client_information(self, client_profile: InvestorProfile, financial_data: Dict) -> Dict:
        """Compile comprehensive client information"""
        return {'client_type': client_profile.investor_type.value, 'investment_objective': client_profile.investment_objective.value, 'risk_tolerance': client_profile.risk_tolerance, 'time_horizon': client_profile.time_horizon, 'liquidity_needs': client_profile.liquidity_needs, 'financial_situation': {'current_assets': financial_data.get('current_portfolio_value', 0), 'annual_income': financial_data.get('annual_income', 0), 'annual_expenses': financial_data.get('annual_expenses', 0), 'net_worth': financial_data.get('net_worth', 0)}, 'tax_situation': client_profile.tax_situation, 'unique_circumstances': client_profile.unique_circumstances}

    def _analyze_unique_circumstances(self, client_profile: InvestorProfile) -> Dict:
        """Analyze unique circumstances affecting portfolio"""
        unique_analysis = {'circumstances': client_profile.unique_circumstances, 'portfolio_implications': [], 'special_considerations': []}
        for circumstance in client_profile.unique_circumstances:
            if 'concentrated position' in circumstance.lower():
                unique_analysis['portfolio_implications'].append('Diversification challenge due to concentrated position')
                unique_analysis['special_considerations'].append('Consider gradual diversification strategy')
            elif 'business ownership' in circumstance.lower():
                unique_analysis['portfolio_implications'].append('High correlation between human capital and financial capital')
                unique_analysis['special_considerations'].append('Emphasize diversification away from business sector')
            elif 'inheritance' in circumstance.lower():
                unique_analysis['special_considerations'].append('Consider step-up in basis for tax planning')
        return unique_analysis

    def _develop_investment_guidelines(self, strategic_allocation: Dict, client_profile: InvestorProfile) -> Dict:
        """Develop comprehensive investment guidelines"""
        return {'asset_allocation_guidelines': {'strategic_targets': strategic_allocation['strategic_allocation'], 'rebalancing_bands': strategic_allocation['rebalancing_bands'], 'tactical_ranges': self._set_tactical_ranges(strategic_allocation)}, 'security_selection_guidelines': {'quality_requirements': self._define_quality_requirements(client_profile), 'diversification_requirements': self._define_diversification_requirements(), 'liquidity_requirements': self._define_liquidity_requirements(client_profile), 'cost_guidelines': self._define_cost_guidelines()}, 'risk_management_guidelines': {'maximum_position_sizes': self._set_position_limits(), 'prohibited_investments': self._identify_prohibited_investments(client_profile), 'derivative_usage': self._define_derivative_usage_policy(client_profile)}}

    def _develop_rebalancing_policy(self, strategic_allocation: Dict) -> Dict:
        """Develop rebalancing policy"""
        return {'rebalancing_method': 'Threshold-based with calendar review', 'rebalancing_bands': strategic_allocation['rebalancing_bands'], 'rebalancing_frequency': {'calendar_review': 'Quarterly', 'threshold_monitoring': 'Monthly', 'emergency_rebalancing': 'As needed for major market events'}, 'rebalancing_priorities': ['Bring severely out-of-range allocations back to target', 'Consider tax implications of rebalancing transactions', 'Use cash flows to rebalance when possible', 'Minimize transaction costs'], 'implementation_guidelines': {'minimum_trade_size': '1% of portfolio value', 'tax_loss_harvesting': 'Incorporate when beneficial', 'cash_flow_utilization': 'Use contributions/withdrawals for rebalancing'}}

    def _develop_performance_measurement_framework(self, return_objectives: Dict, strategic_allocation: Dict) -> Dict:
        """Develop performance measurement framework"""
        return {'primary_benchmark': self._select_primary_benchmark(strategic_allocation), 'secondary_benchmarks': self._select_secondary_benchmarks(strategic_allocation), 'performance_metrics': ['Total return vs. benchmark', 'Risk-adjusted returns (Sharpe ratio)', 'Maximum drawdown', 'Tracking error vs. benchmark'], 'evaluation_periods': {'short_term': '1 year', 'medium_term': '3 years', 'long_term': '5+ years'}, 'performance_attribution': {'asset_allocation_effect': 'Contribution from strategic allocation decisions', 'security_selection_effect': 'Contribution from security selection', 'interaction_effect': 'Interaction between allocation and selection'}, 'reporting_schedule': {'monthly': 'Portfolio value and basic performance metrics', 'quarterly': 'Comprehensive performance report with attribution', 'annual': 'Full performance review with recommendations'}}

    def _define_responsibilities(self) -> Dict:
        """Define roles and responsibilities"""
        return {'client_responsibilities': ['Provide accurate and complete financial information', 'Communicate changes in circumstances promptly', 'Review and approve Investment Policy Statement', 'Make timely decisions on recommended changes'], 'advisor_responsibilities': ['Develop and maintain Investment Policy Statement', 'Implement investment strategy according to IPS', 'Monitor portfolio performance and risk', 'Provide regular reporting and communication', 'Recommend changes when appropriate'], 'third_party_responsibilities': ['Custodian: Safekeeping of assets and transaction settlement', 'Portfolio managers: Investment management within guidelines', 'Other service providers: Specific services as contracted']}

    def _establish_review_schedule(self, client_profile: InvestorProfile) -> Dict:
        """Establish IPS and portfolio review schedule"""
        if client_profile.investor_type == InvestorType.INDIVIDUAL:
            review_frequency = 'Annual'
            interim_reviews = 'As circumstances change'
        else:
            review_frequency = 'Annual or as required by governance'
            interim_reviews = 'Quarterly committee reviews'
        return {'formal_review_frequency': review_frequency, 'interim_review_triggers': ['Significant changes in client circumstances', 'Major market events or economic changes', 'Performance significantly off-track', 'Changes in investment objectives or constraints'], 'review_process': {'preparation': 'Gather performance data and market analysis', 'review_meeting': 'Discuss performance, circumstances, and changes', 'documentation': 'Update IPS if changes are made', 'implementation': 'Execute any approved changes'}, 'update_procedures': ['Document reasons for any IPS changes', 'Obtain client approval for material changes', 'Communicate changes to all relevant parties', 'Update systems and processes accordingly']}

    def _generate_optimization_recommendations(self, ips: InvestmentPolicyStatement) -> List[str]:
        """Generate IPS optimization recommendations"""
        recommendations = []
        allocation = ips.strategic_asset_allocation.get('strategic_allocation', {})
        if len(allocation) < 4:
            recommendations.append('Consider additional asset classes for better diversification')
        if not ips.rebalancing_policy.get('rebalancing_bands'):
            recommendations.append('Establish clear rebalancing bands to maintain strategic allocation')
        if not ips.performance_measurement.get('primary_benchmark'):
            recommendations.append('Define clear performance benchmarks for evaluation')
        if not ips.esg_policy and 'esg' in str(ips.client_information.get('unique_circumstances', [])).lower():
            recommendations.append('Consider developing ESG policy based on client preferences')
        return recommendations

    def _stress_test_ips(self, ips: InvestmentPolicyStatement) -> Dict:
        """Stress test the IPS under various scenarios"""
        allocation = ips.strategic_asset_allocation.get('strategic_allocation', {})
        scenarios = {'market_crash': {'equity_shock': -0.3, 'bond_shock': 0.05}, 'inflation_spike': {'equity_shock': -0.1, 'bond_shock': -0.15}, 'recession': {'equity_shock': -0.2, 'bond_shock': 0.1}}
        stress_results = {}
        for scenario_name, shocks in scenarios.items():
            portfolio_impact = 0
            for asset_class, weight in allocation.items():
                if 'equity' in asset_class:
                    portfolio_impact += weight * shocks['equity_shock']
                elif 'bond' in asset_class:
                    portfolio_impact += weight * shocks['bond_shock']
            stress_results[scenario_name] = {'portfolio_impact': portfolio_impact, 'severity': 'High' if abs(portfolio_impact) > 0.15 else 'Moderate' if abs(portfolio_impact) > 0.1 else 'Low'}
        return {'scenario_analysis': stress_results, 'overall_resilience': 'Good' if all((abs(result['portfolio_impact']) < 0.2 for result in stress_results.values())) else 'Moderate', 'recommendations': self._generate_stress_test_recommendations(stress_results)}

    def _create_implementation_roadmap(self, ips: InvestmentPolicyStatement) -> Dict:
        """Create implementation roadmap for IPS"""
        return {'phase_1_immediate': {'timeframe': '0-30 days', 'tasks': ['Finalize and approve IPS', 'Set up custodial and administrative accounts', 'Implement core strategic allocation']}, 'phase_2_buildup': {'timeframe': '30-90 days', 'tasks': ['Complete portfolio construction', 'Implement security selection', 'Establish monitoring and reporting systems']}, 'phase_3_optimization': {'timeframe': '90+ days', 'tasks': ['Fine-tune allocation based on performance', 'Optimize tax efficiency', 'Conduct first quarterly review']}}

    def _analyze_implementation_considerations(self, ips: InvestmentPolicyStatement, market_conditions: Dict) -> Dict:
        """Analyze implementation considerations"""
        return {'market_timing_considerations': {'current_valuations': market_conditions.get('market_valuations', 'neutral'), 'volatility_environment': market_conditions.get('volatility', 'normal'), 'implementation_approach': 'Dollar-cost averaging for large allocations'}, 'cost_analysis': {'estimated_implementation_costs': '0.10% - 0.25% of assets', 'ongoing_management_fees': '0.50% - 1.50% annually', 'transaction_cost_minimization': 'Use low-cost index funds where appropriate'}, 'tax_optimization': {'account_type_utilization': 'Maximize tax-advantaged account usage', 'asset_location': 'Place tax-inefficient assets in tax-advantaged accounts', 'transition_management': 'Consider tax implications of portfolio transitions'}}

    def _develop_monitoring_framework(self, ips: InvestmentPolicyStatement) -> Dict:
        """Develop comprehensive monitoring framework"""
        return {'daily_monitoring': ['Portfolio value and performance', 'Cash flows and liquidity', 'Market risk exposures'], 'monthly_monitoring': ['Asset allocation drift', 'Performance vs. benchmarks', 'Risk metrics and attribution'], 'quarterly_monitoring': ['Comprehensive performance review', 'Rebalancing needs assessment', 'Strategy effectiveness evaluation'], 'alert_systems': {'allocation_alerts': 'Trigger when allocation exceeds bands', 'performance_alerts': 'Trigger on significant underperformance', 'risk_alerts': 'Trigger on excessive risk measures'}}

    def _define_success_metrics(self, ips: InvestmentPolicyStatement) -> Dict:
        """Define success metrics for portfolio"""
        return_target = ips.investment_objectives['return_objectives']['return_targets']['primary_return_target']
        return {'primary_success_metrics': {'return_achievement': f'Achieve {return_target:.1%} annual return over long term', 'risk_control': 'Stay within defined risk parameters', 'objective_fulfillment': 'Meet stated investment objectives'}, 'secondary_success_metrics': {'cost_efficiency': 'Minimize total investment costs', 'tax_efficiency': 'Optimize after-tax returns', 'implementation_efficiency': 'Minimize tracking error to strategic allocation'}, 'measurement_timeframes': {'short_term': '1-year rolling periods', 'medium_term': '3-year rolling periods', 'long_term': '5+ year periods'}}

    def _set_tactical_ranges(self, strategic_allocation: Dict) -> Dict:
        """Set tactical allocation ranges"""
        tactical_ranges = {}
        for asset_class, target in strategic_allocation['strategic_allocation'].items():
            deviation = target * 0.25
            tactical_ranges[asset_class] = {'minimum': max(0, target - deviation), 'maximum': min(1, target + deviation)}
        return tactical_ranges

    def _define_quality_requirements(self, client_profile: InvestorProfile) -> List[str]:
        """Define security quality requirements"""
        requirements = ['Minimum investment grade rating for fixed income']
        if client_profile.risk_tolerance == 'conservative':
            requirements.extend(['Large-cap equity bias', 'Minimum market capitalization of $2 billion for individual stocks'])
        return requirements

    def _define_diversification_requirements(self) -> List[str]:
        """Define diversification requirements"""
        return ['Maximum 5% in any single security', 'Maximum 25% in any single sector', 'Minimum 20 individual securities in equity allocation']

    def _define_liquidity_requirements(self, client_profile: InvestorProfile) -> List[str]:
        """Define liquidity requirements"""
        requirements = ['Minimum daily trading volume of $1 million for individual securities']
        if client_profile.liquidity_needs > 0.2:
            requirements.append('Maximum 10% in illiquid investments')
        else:
            requirements.append('Maximum 20% in illiquid investments')
        return requirements

    def _define_cost_guidelines(self) -> List[str]:
        """Define cost guidelines"""
        return ['Target expense ratios below 0.75% for actively managed funds', 'Target expense ratios below 0.25% for index funds', 'Minimize portfolio turnover to reduce transaction costs']

    def _set_position_limits(self) -> Dict[str, float]:
        """Set maximum position size limits"""
        return {'individual_security': 0.05, 'sector_concentration': 0.25, 'geographic_concentration': 0.6, 'currency_exposure': 0.3}

    def _identify_prohibited_investments(self, client_profile: InvestorProfile) -> List[str]:
        """Identify prohibited investments"""
        prohibited = ['Penny stocks', 'Highly leveraged ETFs (>2x)']
        for circumstance in client_profile.unique_circumstances:
            if 'no tobacco' in circumstance.lower():
                prohibited.append('Tobacco companies')
            if 'no weapons' in circumstance.lower():
                prohibited.append('Defense/weapons manufacturers')
        return prohibited

    def _define_derivative_usage_policy(self, client_profile: InvestorProfile) -> Dict:
        """Define derivative usage policy"""
        if client_profile.risk_tolerance == 'conservative':
            return {'permitted_derivatives': ['Currency hedging forwards'], 'prohibited_derivatives': ['Options', 'Futures', 'Swaps'], 'usage_purpose': 'Hedging only'}
        else:
            return {'permitted_derivatives': ['Options', 'Futures', 'Currency hedging'], 'usage_purpose': 'Hedging and limited tactical positioning', 'maximum_notional': '10% of portfolio value'}

    def _select_primary_benchmark(self, strategic_allocation: Dict) -> str:
        """Select primary benchmark based on allocation"""
        allocation = strategic_allocation['strategic_allocation']
        equity_weight = sum((weight for asset, weight in allocation.items() if 'equity' in asset))
        if equity_weight > 0.7:
            return 'MSCI All Country World Index'
        elif equity_weight > 0.4:
            return '60/40 Stock/Bond Composite'
        else:
            return 'Bloomberg Aggregate Bond Index'

    def _select_secondary_benchmarks(self, strategic_allocation: Dict) -> List[str]:
        """Select secondary benchmarks"""
        allocation = strategic_allocation['strategic_allocation']
        benchmarks = []
        if 'domestic_equity' in allocation:
            benchmarks.append('S&P 500 Index')
        if 'international_equity' in allocation:
            benchmarks.append('MSCI EAFE Index')
        if 'domestic_bonds' in allocation:
            benchmarks.append('Bloomberg US Aggregate Bond Index')
        if 'real_estate' in allocation:
            benchmarks.append('FTSE NAREIT All REITs Index')
        return benchmarks

    def _generate_stress_test_recommendations(self, stress_results: Dict) -> List[str]:
        """Generate recommendations based on stress test results"""
        recommendations = []
        high_impact_scenarios = [scenario for scenario, result in stress_results.items() if result['severity'] == 'High']
        if high_impact_scenarios:
            recommendations.append('Consider reducing portfolio risk through increased diversification')
        if 'market_crash' in high_impact_scenarios:
            recommendations.append('Consider adding defensive assets or hedge fund strategies')
        if 'inflation_spike' in high_impact_scenarios:
            recommendations.append('Consider adding inflation-protected securities or commodities')
        return recommendations

def __init__(self):
    self.ips_framework = IPSFramework()
    self.objectives_framework = ObjectivesFramework()
    self.constraints_analysis = ConstraintsAnalysis()
    self.asset_allocation_framework = AssetAllocationFramework()
    self.construction_principles = PortfolioConstructionPrinciples()
    self.esg_integration = ESGIntegration()

