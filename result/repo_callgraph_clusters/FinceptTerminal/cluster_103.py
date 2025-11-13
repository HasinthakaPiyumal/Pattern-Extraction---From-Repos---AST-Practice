# Cluster 103

class PortfolioRiskAnalyzer:
    """
    Portfolio-level risk analysis across multiple alternative investments
    CFA Standards: Portfolio risk management and optimization
    """

    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()

    def portfolio_var_analysis(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Calculate portfolio VaR considering correlations
        CFA Standard: Portfolio VaR with correlation matrix
        """
        if not asset_returns or not portfolio_weights:
            return {'error': 'Asset returns and weights required'}
        total_weight = sum(portfolio_weights.values())
        if abs(total_weight - Decimal('1')) > Decimal('0.01'):
            return {'error': f'Weights sum to {total_weight}, should be 1.0'}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        if not portfolio_returns:
            return {'error': 'Cannot calculate portfolio returns'}
        portfolio_var = self.risk_analyzer.value_at_risk_analysis(portfolio_returns)
        component_var = self._calculate_component_var(asset_returns, portfolio_weights)
        return {'portfolio_var': portfolio_var, 'component_var': component_var, 'portfolio_statistics': {'mean_return': float(sum(portfolio_returns) / len(portfolio_returns)), 'volatility': float(self.risk_analyzer._calculate_volatility(portfolio_returns)), 'number_of_assets': len(portfolio_weights)}}

    def risk_budget_analysis(self, asset_returns: Dict[str, List[Decimal]], target_risk_budgets: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Analyze risk budgeting and contribution
        CFA Standard: Risk budgeting framework
        """
        risk_analysis = {}
        asset_volatilities = {}
        for asset, returns in asset_returns.items():
            vol = self.risk_analyzer._calculate_volatility(returns)
            asset_volatilities[asset] = vol
        correlation_matrix = self.risk_analyzer._calculate_correlation_matrix(asset_returns)
        risk_contributions = self._calculate_risk_contributions_detailed(asset_volatilities, correlation_matrix, target_risk_budgets)
        risk_analysis['risk_contributions'] = risk_contributions
        risk_analysis['target_risk_budgets'] = {k: float(v) for k, v in target_risk_budgets.items()}
        risk_analysis['asset_volatilities'] = {k: float(v) for k, v in asset_volatilities.items()}
        return risk_analysis

    def portfolio_stress_testing(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal], stress_scenarios: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """
        Comprehensive portfolio stress testing
        CFA Standard: Portfolio stress testing across scenarios
        """
        stress_results = {}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        baseline_metrics = {'mean_return': float(sum(portfolio_returns) / len(portfolio_returns)), 'volatility': float(self.risk_analyzer._calculate_volatility(portfolio_returns))}
        stress_results['baseline_metrics'] = baseline_metrics
        scenario_impacts = {}
        for scenario_name, scenario_shocks in stress_scenarios.items():
            scenario_impact = self._apply_portfolio_stress_scenario(asset_returns, portfolio_weights, scenario_shocks)
            scenario_impacts[scenario_name] = scenario_impact
        stress_results['scenario_impacts'] = scenario_impacts
        worst_case = self._identify_worst_case_scenario(scenario_impacts)
        stress_results['worst_case_scenario'] = worst_case
        return stress_results

    def liquidity_risk_portfolio(self, asset_liquidity_scores: Dict[str, float], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Analyze portfolio-level liquidity risk
        CFA Standard: Portfolio liquidity management
        """
        liquidity_analysis = {}
        weighted_liquidity = Decimal('0')
        for asset, weight in portfolio_weights.items():
            if asset in asset_liquidity_scores:
                liquidity_score = Decimal(str(asset_liquidity_scores[asset]))
                weighted_liquidity += weight * liquidity_score
        liquidity_analysis['weighted_average_liquidity'] = float(weighted_liquidity)
        liquidity_buckets = {'high': Decimal('0'), 'medium': Decimal('0'), 'low': Decimal('0')}
        for asset, weight in portfolio_weights.items():
            if asset in asset_liquidity_scores:
                score = asset_liquidity_scores[asset]
                if score >= 70:
                    liquidity_buckets['high'] += weight
                elif score >= 40:
                    liquidity_buckets['medium'] += weight
                else:
                    liquidity_buckets['low'] += weight
        liquidity_analysis['liquidity_buckets'] = {k: float(v) for k, v in liquidity_buckets.items()}
        if weighted_liquidity >= 70:
            risk_level = 'Low'
        elif weighted_liquidity >= 50:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
        liquidity_analysis['portfolio_liquidity_risk'] = risk_level
        return liquidity_analysis

    def concentration_risk_analysis(self, portfolio_weights: Dict[str, Decimal], asset_classifications: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze concentration risk across multiple dimensions
        CFA Standard: Concentration risk management
        """
        concentration_analysis = {}
        max_weight = max(portfolio_weights.values())
        concentration_analysis['maximum_single_asset_weight'] = float(max_weight)
        asset_class_weights = {}
        for asset, weight in portfolio_weights.items():
            if asset in asset_classifications:
                asset_class = asset_classifications[asset].get('asset_class', 'unknown')
                if asset_class not in asset_class_weights:
                    asset_class_weights[asset_class] = Decimal('0')
                asset_class_weights[asset_class] += weight
        concentration_analysis['asset_class_concentration'] = {k: float(v) for k, v in asset_class_weights.items()}
        geographic_weights = {}
        for asset, weight in portfolio_weights.items():
            if asset in asset_classifications:
                geography = asset_classifications[asset].get('geography', 'unknown')
                if geography not in geographic_weights:
                    geographic_weights[geography] = Decimal('0')
                geographic_weights[geography] += weight
        concentration_analysis['geographic_concentration'] = {k: float(v) for k, v in geographic_weights.items()}
        concentration_score = self._calculate_concentration_score(max_weight, asset_class_weights, geographic_weights)
        concentration_analysis['concentration_risk_score'] = concentration_score
        return concentration_analysis

    def _calculate_portfolio_returns(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> List[Decimal]:
        """Calculate portfolio returns given weights"""
        min_length = min((len(returns) for returns in asset_returns.values() if returns))
        if min_length == 0:
            return []
        portfolio_returns = []
        for i in range(min_length):
            period_return = Decimal('0')
            for asset, weight in portfolio_weights.items():
                if asset in asset_returns and i < len(asset_returns[asset]):
                    period_return += weight * asset_returns[asset][i]
            portfolio_returns.append(period_return)
        return portfolio_returns

    def _calculate_component_var(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate component VaR for each asset"""
        component_vars = {}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        if not portfolio_returns:
            return component_vars
        portfolio_var_95 = self.risk_analyzer.math.var_historical(portfolio_returns, Decimal('0.05'))
        for asset, weight in portfolio_weights.items():
            if asset in asset_returns:
                asset_return_series = asset_returns[asset][:len(portfolio_returns)]
                if asset_return_series:
                    correlation = self.risk_analyzer._calculate_correlation(asset_return_series, portfolio_returns)
                    asset_vol = self.risk_analyzer._calculate_volatility(asset_return_series)
                    portfolio_vol = self.risk_analyzer._calculate_volatility(portfolio_returns)
                    if portfolio_vol > 0:
                        component_var = weight * correlation * (asset_vol / portfolio_vol) * portfolio_var_95
                        component_vars[asset] = float(component_var)
        return component_vars

    def _calculate_risk_contributions_detailed(self, asset_volatilities: Dict[str, Decimal], correlation_matrix: Dict[str, Dict[str, float]], target_risk_budgets: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate detailed risk contributions"""
        risk_contributions = {}
        assets = list(asset_volatilities.keys())
        for asset in assets:
            asset_vol = asset_volatilities[asset]
            correlations = []
            for other_asset in assets:
                if other_asset != asset and other_asset in correlation_matrix.get(asset, {}):
                    correlations.append(correlation_matrix[asset][other_asset])
            avg_correlation = sum(correlations) / len(correlations) if correlations else 0
            target_budget = target_risk_budgets.get(asset, Decimal('0'))
            risk_contribution = float(asset_vol * target_budget * Decimal(str(avg_correlation)))
            risk_contributions[asset] = {'risk_contribution': risk_contribution, 'target_budget': float(target_budget), 'asset_volatility': float(asset_vol), 'average_correlation': avg_correlation}
        return risk_contributions

    def _apply_portfolio_stress_scenario(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal], scenario_shocks: Dict[str, Decimal]) -> Dict[str, Any]:
        """Apply stress scenario to portfolio"""
        scenario_impact = {}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        baseline_return = sum(portfolio_returns) / len(portfolio_returns) if portfolio_returns else Decimal('0')
        stressed_return = Decimal('0')
        for asset, weight in portfolio_weights.items():
            asset_shock = scenario_shocks.get(asset, Decimal('0'))
            if asset in asset_returns and asset_returns[asset]:
                asset_baseline = sum(asset_returns[asset]) / len(asset_returns[asset])
                stressed_asset_return = asset_baseline + asset_shock
            else:
                stressed_asset_return = asset_shock
            stressed_return += weight * stressed_asset_return
        impact = stressed_return - baseline_return
        scenario_impact['baseline_return'] = float(baseline_return)
        scenario_impact['stressed_return'] = float(stressed_return)
        scenario_impact['impact'] = float(impact)
        scenario_impact['impact_percentage'] = float(impact / baseline_return * 100) if baseline_return != 0 else 0
        return scenario_impact

    def _identify_worst_case_scenario(self, scenario_impacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Identify worst case scenario from stress testing"""
        worst_case = {}
        worst_impact = 0
        worst_scenario = None
        for scenario_name, impact_data in scenario_impacts.items():
            if isinstance(impact_data, dict) and 'impact' in impact_data:
                impact = impact_data['impact']
                if impact < worst_impact:
                    worst_impact = impact
                    worst_scenario = scenario_name
        if worst_scenario:
            worst_case['worst_scenario_name'] = worst_scenario
            worst_case['worst_impact'] = worst_impact
            worst_case['worst_scenario_details'] = scenario_impacts[worst_scenario]
        return worst_case

    def _calculate_concentration_score(self, max_single_weight: Decimal, asset_class_weights: Dict[str, Decimal], geographic_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate concentration risk score"""
        score_components = {}
        single_asset_score = float(max_single_weight * 100)
        score_components['single_asset_concentration'] = single_asset_score
        if asset_class_weights:
            hhi_asset_class = sum((weight ** 2 for weight in asset_class_weights.values()))
            asset_class_score = float(hhi_asset_class * 100)
            score_components['asset_class_concentration'] = asset_class_score
        if geographic_weights:
            hhi_geographic = sum((weight ** 2 for weight in geographic_weights.values()))
            geographic_score = float(hhi_geographic * 100)
            score_components['geographic_concentration'] = geographic_score
        scores = list(score_components.values())
        composite_score = sum(scores) / len(scores) if scores else 0
        if composite_score < 30:
            risk_level = 'Low'
        elif composite_score < 60:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
        return {'composite_concentration_score': composite_score, 'concentration_risk_level': risk_level, 'score_components': score_components}

def __init__(self):
    self.risk_analyzer = RiskAnalyzer()

