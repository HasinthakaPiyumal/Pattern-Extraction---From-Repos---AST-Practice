# Cluster 101

class RiskAnalyzer:
    """
    Comprehensive risk analysis for alternative investments
    CFA Standards: Risk measurement, stress testing, scenario analysis
    """

    def __init__(self):
        self.math = FinancialMath()
        self.config = Config()

    def value_at_risk_analysis(self, returns: List[Decimal], confidence_levels: List[Decimal]=None) -> Dict[str, Any]:
        """
        Comprehensive Value at Risk analysis
        CFA Standard: Historical simulation, parametric, and Monte Carlo VaR
        """
        if not returns:
            return {'error': 'No return data provided'}
        if confidence_levels is None:
            confidence_levels = [Decimal('0.01'), Decimal('0.05'), Decimal('0.10')]
        var_analysis = {}
        historical_var = {}
        for confidence in confidence_levels:
            var_value = self.math.var_historical(returns, confidence)
            confidence_pct = int((1 - confidence) * 100)
            historical_var[f'var_{confidence_pct}'] = float(var_value)
        var_analysis['historical_var'] = historical_var
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        parametric_var = {}
        for confidence in confidence_levels:
            z_scores = {Decimal('0.01'): Decimal('-2.326'), Decimal('0.05'): Decimal('-1.645'), Decimal('0.10'): Decimal('-1.282')}
            z_score = z_scores.get(confidence, Decimal('-1.645'))
            var_value = mean_return + z_score * volatility
            confidence_pct = int((1 - confidence) * 100)
            parametric_var[f'var_{confidence_pct}'] = float(abs(var_value))
        var_analysis['parametric_var'] = parametric_var
        conditional_var = {}
        for confidence in confidence_levels:
            cvar_value = self._calculate_conditional_var(returns, confidence)
            confidence_pct = int((1 - confidence) * 100)
            conditional_var[f'cvar_{confidence_pct}'] = float(cvar_value)
        var_analysis['conditional_var'] = conditional_var
        var_analysis['model_comparison'] = self._compare_var_models(historical_var, parametric_var, returns)
        return var_analysis

    def stress_testing(self, returns: List[Decimal], asset_class: AssetClass=None) -> Dict[str, Any]:
        """
        Comprehensive stress testing framework
        CFA Standard: Scenario analysis and stress testing
        """
        if not returns:
            return {'error': 'No return data provided'}
        stress_results = {}
        historical_scenarios = self._historical_stress_scenarios(returns)
        stress_results['historical_scenarios'] = historical_scenarios
        hypothetical_scenarios = self._hypothetical_stress_scenarios(returns, asset_class)
        stress_results['hypothetical_scenarios'] = hypothetical_scenarios
        monte_carlo_scenarios = self._monte_carlo_stress_testing(returns)
        stress_results['monte_carlo_scenarios'] = monte_carlo_scenarios
        tail_risk = self._analyze_tail_risk(returns)
        stress_results['tail_risk_analysis'] = tail_risk
        return stress_results

    def correlation_analysis(self, asset_returns: Dict[str, List[Decimal]], rolling_window: int=60) -> Dict[str, Any]:
        """
        Dynamic correlation analysis across asset classes
        CFA Standard: Correlation analysis and diversification benefits
        """
        if len(asset_returns) < 2:
            return {'error': 'Need at least 2 asset return series'}
        correlation_analysis = {}
        static_correlations = self._calculate_correlation_matrix(asset_returns)
        correlation_analysis['static_correlations'] = static_correlations
        rolling_correlations = self._calculate_rolling_correlations(asset_returns, rolling_window)
        correlation_analysis['rolling_correlations'] = rolling_correlations
        correlation_breakdown = self._analyze_correlation_breakdown(asset_returns)
        correlation_analysis['correlation_breakdown'] = correlation_breakdown
        diversification_metrics = self._calculate_diversification_metrics(static_correlations)
        correlation_analysis['diversification_metrics'] = diversification_metrics
        return correlation_analysis

    def liquidity_risk_assessment(self, trading_volumes: List[Decimal], market_caps: List[Decimal]=None, bid_ask_spreads: List[Decimal]=None) -> Dict[str, Any]:
        """
        Comprehensive liquidity risk assessment
        CFA Standard: Liquidity risk measurement and management
        """
        liquidity_assessment = {}
        if not trading_volumes:
            return {'error': 'Trading volume data required'}
        volume_metrics = self._analyze_volume_patterns(trading_volumes)
        liquidity_assessment['volume_metrics'] = volume_metrics
        if market_caps:
            market_impact = self._estimate_market_impact(trading_volumes, market_caps)
            liquidity_assessment['market_impact'] = market_impact
        if bid_ask_spreads:
            spread_analysis = self._analyze_bid_ask_spreads(bid_ask_spreads)
            liquidity_assessment['spread_analysis'] = spread_analysis
        liquidity_score = self._calculate_liquidity_score(volume_metrics, market_caps, bid_ask_spreads)
        liquidity_assessment['liquidity_score'] = liquidity_score
        return liquidity_assessment

    def drawdown_analysis(self, price_series: List[Decimal]) -> Dict[str, Any]:
        """
        Comprehensive drawdown analysis
        CFA Standard: Drawdown measurement and recovery analysis
        """
        if len(price_series) < 2:
            return {'error': 'Insufficient price data'}
        drawdown_results = {}
        drawdowns = self._calculate_drawdown_series(price_series)
        max_dd, peak_idx, trough_idx = self.math.maximum_drawdown(price_series)
        drawdown_results['maximum_drawdown'] = float(max_dd)
        drawdown_results['peak_to_trough_periods'] = trough_idx - peak_idx
        dd_stats = self._calculate_drawdown_statistics(drawdowns)
        drawdown_results['drawdown_statistics'] = dd_stats
        recovery_analysis = self._analyze_recovery_patterns(price_series, drawdowns)
        drawdown_results['recovery_analysis'] = recovery_analysis
        ulcer_index = self._calculate_ulcer_index(drawdowns)
        drawdown_results['ulcer_index'] = float(ulcer_index)
        return drawdown_results

    def risk_attribution(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """
        Risk attribution analysis using factor models
        CFA Standard: Risk factor decomposition
        """
        if not portfolio_returns or not factor_returns:
            return {'error': 'Portfolio returns and factor returns required'}
        attribution_results = {}
        factor_exposures = self._calculate_factor_exposures(portfolio_returns, factor_returns)
        attribution_results['factor_exposures'] = factor_exposures
        risk_contributions = self._calculate_risk_contributions(portfolio_returns, factor_returns, factor_exposures)
        attribution_results['risk_contributions'] = risk_contributions
        idiosyncratic_risk = self._calculate_idiosyncratic_risk(portfolio_returns, factor_returns, factor_exposures)
        attribution_results['idiosyncratic_risk'] = float(idiosyncratic_risk)
        return attribution_results

    def scenario_analysis(self, base_returns: List[Decimal], scenarios: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """
        Comprehensive scenario analysis
        CFA Standard: Scenario planning and sensitivity analysis
        """
        scenario_results = {}
        for scenario_name, scenario_params in scenarios.items():
            scenario_impact = self._calculate_scenario_impact(base_returns, scenario_params)
            scenario_results[scenario_name] = scenario_impact
        scenario_summary = self._summarize_scenario_outcomes(scenario_results)
        scenario_results['scenario_summary'] = scenario_summary
        return scenario_results

    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate standard deviation of returns"""
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        return variance.sqrt()

    def _calculate_conditional_var(self, returns: List[Decimal], confidence: Decimal) -> Decimal:
        """Calculate Conditional VaR (Expected Shortfall)"""
        if not returns:
            return Decimal('0')
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * confidence)
        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1
        tail_returns = sorted_returns[:var_index + 1]
        if not tail_returns:
            return Decimal('0')
        cvar = sum(tail_returns) / len(tail_returns)
        return abs(cvar)

    def _compare_var_models(self, historical_var: Dict, parametric_var: Dict, returns: List[Decimal]) -> Dict[str, Any]:
        """Compare different VaR model approaches"""
        comparison = {}
        for confidence_key in historical_var.keys():
            hist_var = historical_var[confidence_key]
            param_var = parametric_var[confidence_key]
            difference = abs(hist_var - param_var)
            relative_difference = difference / hist_var if hist_var != 0 else 0
            comparison[confidence_key] = {'historical_var': hist_var, 'parametric_var': param_var, 'absolute_difference': difference, 'relative_difference': relative_difference}
        avg_relative_diff = sum((comp['relative_difference'] for comp in comparison.values())) / len(comparison)
        if avg_relative_diff < 0.1:
            comparison['recommended_model'] = 'Either (similar results)'
        elif len(returns) < 100:
            comparison['recommended_model'] = 'Parametric (limited history)'
        else:
            comparison['recommended_model'] = 'Historical (sufficient data)'
        return comparison

    def _historical_stress_scenarios(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze historical stress periods"""
        if len(returns) < 20:
            return {'insufficient_data': True}
        worst_returns = sorted(returns)[:10]
        scenarios = {}
        scenarios['worst_single_period'] = {'return': float(worst_returns[0]), 'impact': f'{float(worst_returns[0] * 100):.2f}%'}
        worst_consecutive = self._find_worst_consecutive_periods(returns, 5)
        scenarios['worst_5_period_sequence'] = {'cumulative_return': float(worst_consecutive), 'impact': f'{float(worst_consecutive * 100):.2f}%'}
        return scenarios

    def _hypothetical_stress_scenarios(self, returns: List[Decimal], asset_class: AssetClass=None) -> Dict[str, Any]:
        """Generate hypothetical stress scenarios"""
        scenarios = {}
        current_vol = self._calculate_volatility(returns)
        two_sigma_shock = current_vol * Decimal('2')
        scenarios['two_sigma_shock'] = {'negative_shock': float(-two_sigma_shock), 'positive_shock': float(two_sigma_shock)}
        if asset_class:
            asset_scenarios = self._get_asset_class_scenarios(asset_class)
            scenarios.update(asset_scenarios)
        return scenarios

    def _monte_carlo_stress_testing(self, returns: List[Decimal], num_simulations: int=1000) -> Dict[str, Any]:
        """Monte Carlo stress testing"""
        if len(returns) < 10:
            return {'insufficient_data': True}
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        simulated_outcomes = []
        try:
            import random
            random.seed(42)
            for _ in range(num_simulations):
                z = Decimal(str(random.gauss(0, 1)))
                simulated_return = mean_return + volatility * z
                simulated_outcomes.append(simulated_return)
        except ImportError:
            for i in range(num_simulations):
                z = Decimal(str((i - num_simulations / 2) / (num_simulations / 4)))
                simulated_return = mean_return + volatility * z
                simulated_outcomes.append(simulated_return)
        sorted_outcomes = sorted(simulated_outcomes)
        return {'worst_1_percent': float(sorted_outcomes[int(0.01 * len(sorted_outcomes))]), 'worst_5_percent': float(sorted_outcomes[int(0.05 * len(sorted_outcomes))]), 'best_5_percent': float(sorted_outcomes[int(0.95 * len(sorted_outcomes))]), 'median_outcome': float(sorted_outcomes[len(sorted_outcomes) // 2]), 'simulations_run': num_simulations}

    def _analyze_tail_risk(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze tail risk characteristics"""
        if len(returns) < 20:
            return {'insufficient_data': True}
        sorted_returns = sorted(returns)
        left_tail_10pct = sorted_returns[:len(returns) // 10]
        right_tail_10pct = sorted_returns[-len(returns) // 10:]
        left_tail_mean = sum(left_tail_10pct) / len(left_tail_10pct) if left_tail_10pct else Decimal('0')
        right_tail_mean = sum(right_tail_10pct) / len(right_tail_10pct) if right_tail_10pct else Decimal('0')
        return {'left_tail_mean': float(left_tail_mean), 'right_tail_mean': float(right_tail_mean), 'tail_ratio': float(abs(left_tail_mean / right_tail_mean)) if right_tail_mean != 0 else 0, 'skewness_indicator': 'negative_skew' if abs(left_tail_mean) > right_tail_mean else 'positive_skew'}

    def _calculate_correlation_matrix(self, asset_returns: Dict[str, List[Decimal]]) -> Dict[str, Dict[str, float]]:
        """Calculate static correlation matrix"""
        assets = list(asset_returns.keys())
        correlation_matrix = {}
        for asset1 in assets:
            correlation_matrix[asset1] = {}
            for asset2 in assets:
                if asset1 == asset2:
                    correlation_matrix[asset1][asset2] = 1.0
                else:
                    returns1 = asset_returns[asset1]
                    returns2 = asset_returns[asset2]
                    if len(returns1) == len(returns2) and len(returns1) > 1:
                        correlation = self._calculate_correlation(returns1, returns2)
                        correlation_matrix[asset1][asset2] = float(correlation)
                    else:
                        correlation_matrix[asset1][asset2] = 0.0
        return correlation_matrix

    def _calculate_rolling_correlations(self, asset_returns: Dict[str, List[Decimal]], window: int) -> Dict[str, List[float]]:
        """Calculate rolling correlations between assets"""
        rolling_correlations = {}
        assets = list(asset_returns.keys())
        if len(assets) < 2:
            return rolling_correlations
        asset1, asset2 = (assets[0], assets[1])
        returns1 = asset_returns[asset1]
        returns2 = asset_returns[asset2]
        if len(returns1) != len(returns2) or len(returns1) < window:
            return rolling_correlations
        correlations = []
        for i in range(window, len(returns1)):
            window_returns1 = returns1[i - window:i]
            window_returns2 = returns2[i - window:i]
            correlation = self._calculate_correlation(window_returns1, window_returns2)
            correlations.append(float(correlation))
        rolling_correlations[f'{asset1}_vs_{asset2}'] = correlations
        return rolling_correlations

    def _calculate_correlation(self, returns1: List[Decimal], returns2: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient"""
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return Decimal('0')
        mean1 = sum(returns1) / len(returns1)
        mean2 = sum(returns2) / len(returns2)
        numerator = sum(((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2)))
        sum_sq1 = sum(((r1 - mean1) ** 2 for r1 in returns1))
        sum_sq2 = sum(((r2 - mean2) ** 2 for r2 in returns2))
        denominator = (sum_sq1 * sum_sq2).sqrt()
        if denominator == 0:
            return Decimal('0')
        return numerator / denominator

    def _analyze_correlation_breakdown(self, asset_returns: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """Analyze correlation breakdown during stress periods"""
        breakdown_analysis = {}
        assets = list(asset_returns.keys())
        if len(assets) < 2:
            return breakdown_analysis
        all_correlations = []
        correlation_matrix = self._calculate_correlation_matrix(asset_returns)
        for asset1 in assets:
            for asset2 in assets:
                if asset1 != asset2:
                    corr = correlation_matrix[asset1][asset2]
                    all_correlations.append(corr)
        if all_correlations:
            avg_correlation = sum(all_correlations) / len(all_correlations)
            breakdown_analysis['average_correlation'] = avg_correlation
            if avg_correlation > 0.7:
                breakdown_analysis['diversification_benefit'] = 'Low'
            elif avg_correlation > 0.4:
                breakdown_analysis['diversification_benefit'] = 'Medium'
            else:
                breakdown_analysis['diversification_benefit'] = 'High'
        return breakdown_analysis

    def _calculate_diversification_metrics(self, correlation_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Calculate diversification effectiveness metrics"""
        assets = list(correlation_matrix.keys())
        if len(assets) < 2:
            return {}
        all_correlations = []
        for asset1 in assets:
            for asset2 in assets:
                if asset1 != asset2:
                    all_correlations.append(correlation_matrix[asset1][asset2])
        avg_correlation = sum(all_correlations) / len(all_correlations) if all_correlations else 0
        diversification_effectiveness = 1 - abs(avg_correlation)
        return {'average_correlation': avg_correlation, 'diversification_effectiveness': diversification_effectiveness, 'number_of_assets': len(assets)}

    def _analyze_volume_patterns(self, volumes: List[Decimal]) -> Dict[str, Any]:
        """Analyze trading volume patterns for liquidity assessment"""
        if not volumes:
            return {}
        avg_volume = sum(volumes) / len(volumes)
        volume_volatility = self._calculate_volatility(volumes)
        volume_stability = 1 - volume_volatility / avg_volume if avg_volume > 0 else 0
        return {'average_volume': float(avg_volume), 'volume_volatility': float(volume_volatility), 'volume_stability': float(volume_stability)}

    def _estimate_market_impact(self, volumes: List[Decimal], market_caps: List[Decimal]) -> Dict[str, Any]:
        """Estimate market impact for liquidity assessment"""
        if len(volumes) != len(market_caps):
            return {}
        volume_ratios = []
        for vol, mcap in zip(volumes, market_caps):
            if mcap > 0:
                ratio = vol / mcap
                volume_ratios.append(ratio)
        if not volume_ratios:
            return {}
        avg_volume_ratio = sum(volume_ratios) / len(volume_ratios)
        if avg_volume_ratio > Decimal('0.1'):
            impact_assessment = 'Low'
        elif avg_volume_ratio > Decimal('0.01'):
            impact_assessment = 'Medium'
        else:
            impact_assessment = 'High'
        return {'average_volume_to_mcap': float(avg_volume_ratio), 'market_impact_assessment': impact_assessment}

    def _analyze_bid_ask_spreads(self, spreads: List[Decimal]) -> Dict[str, Any]:
        """Analyze bid-ask spreads for liquidity assessment"""
        if not spreads:
            return {}
        avg_spread = sum(spreads) / len(spreads)
        spread_volatility = self._calculate_volatility(spreads)
        return {'average_spread': float(avg_spread), 'spread_volatility': float(spread_volatility), 'spread_stability': float(1 - spread_volatility / avg_spread) if avg_spread > 0 else 0}

    def _calculate_liquidity_score(self, volume_metrics: Dict, market_caps: List[Decimal], bid_ask_spreads: List[Decimal]) -> Dict[str, Any]:
        """Calculate composite liquidity score"""
        score_components = {}
        total_score = 0
        components_count = 0
        if volume_metrics and 'volume_stability' in volume_metrics:
            volume_score = volume_metrics['volume_stability'] * 100
            score_components['volume_score'] = volume_score
            total_score += volume_score
            components_count += 1
        if market_caps:
            avg_mcap = sum(market_caps) / len(market_caps)
            mcap_score = min(100, float(avg_mcap) / 1000000)
            score_components['market_cap_score'] = mcap_score
            total_score += mcap_score
            components_count += 1
        if bid_ask_spreads:
            avg_spread = sum(bid_ask_spreads) / len(bid_ask_spreads)
            spread_score = max(0, 100 - float(avg_spread * 10000))
            score_components['spread_score'] = spread_score
            total_score += spread_score
            components_count += 1
        composite_score = total_score / components_count if components_count > 0 else 0
        return {'composite_liquidity_score': composite_score, 'score_components': score_components, 'liquidity_rating': self._get_liquidity_rating(composite_score)}

    def _get_liquidity_rating(self, score: float) -> str:
        """Convert liquidity score to rating"""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        elif score >= 20:
            return 'Poor'
        else:
            return 'Very Poor'

    def _calculate_drawdown_series(self, price_series: List[Decimal]) -> List[Decimal]:
        """Calculate drawdown series from price series"""
        if not price_series:
            return []
        drawdowns = []
        peak = price_series[0]
        for price in price_series:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            drawdowns.append(drawdown)
        return drawdowns

    def _calculate_drawdown_statistics(self, drawdowns: List[Decimal]) -> Dict[str, Any]:
        """Calculate comprehensive drawdown statistics"""
        if not drawdowns:
            return {}
        max_dd = max(drawdowns)
        avg_dd = sum(drawdowns) / len(drawdowns)
        periods_in_drawdown = sum((1 for dd in drawdowns if dd > 0))
        drawdown_frequency = periods_in_drawdown / len(drawdowns)
        return {'maximum_drawdown': float(max_dd), 'average_drawdown': float(avg_dd), 'drawdown_frequency': float(drawdown_frequency), 'periods_in_drawdown': periods_in_drawdown, 'total_periods': len(drawdowns)}

    def _analyze_recovery_patterns(self, price_series: List[Decimal], drawdowns: List[Decimal]) -> Dict[str, Any]:
        """Analyze recovery patterns from drawdowns"""
        if len(price_series) != len(drawdowns):
            return {}
        recovery_periods = []
        in_drawdown = False
        drawdown_start = 0
        for i, dd in enumerate(drawdowns):
            if dd > 0 and (not in_drawdown):
                in_drawdown = True
                drawdown_start = i
            elif dd == 0 and in_drawdown:
                recovery_period = i - drawdown_start
                recovery_periods.append(recovery_period)
                in_drawdown = False
        if not recovery_periods:
            return {'no_complete_recoveries': True}
        avg_recovery_period = sum(recovery_periods) / len(recovery_periods)
        max_recovery_period = max(recovery_periods)
        return {'average_recovery_period': avg_recovery_period, 'maximum_recovery_period': max_recovery_period, 'number_of_recoveries': len(recovery_periods)}

    def _calculate_ulcer_index(self, drawdowns: List[Decimal]) -> Decimal:
        """Calculate Ulcer Index (alternative drawdown measure)"""
        if not drawdowns:
            return Decimal('0')
        squared_drawdowns = [dd ** 2 for dd in drawdowns]
        mean_squared_dd = sum(squared_drawdowns) / len(squared_drawdowns)
        return mean_squared_dd.sqrt()

    def _calculate_factor_exposures(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, float]:
        """Calculate factor exposures using regression"""
        try:
            y = [float(r) for r in portfolio_returns]
            factors = []
            factor_names = []
            for factor_name, returns in factor_returns.items():
                if len(returns) == len(portfolio_returns):
                    factors.append([float(r) for r in returns])
                    factor_names.append(factor_name)
            if not factors:
                return {}
            try:
                import numpy as np
                X = np.array(factors).T
                X = np.column_stack([np.ones(len(y)), X])
                coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
                exposures = {'alpha': float(coefficients[0])}
                for i, factor_name in enumerate(factor_names):
                    exposures[f'{factor_name}_beta'] = float(coefficients[i + 1])
                y_pred = X @ coefficients
                ss_res = np.sum((np.array(y) - y_pred) ** 2)
                ss_tot = np.sum((np.array(y) - np.mean(y)) ** 2)
                r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0
                exposures['r_squared'] = float(r_squared)
                return exposures
            except ImportError:
                exposures = {}
                for factor_name, factor_rets in zip(factor_names, factors):
                    if len(factor_rets) == len(portfolio_returns):
                        correlation = self._calculate_correlation(portfolio_returns, [Decimal(str(r)) for r in factor_rets])
                        exposures[f'{factor_name}_beta'] = float(correlation)
                return exposures
        except Exception as e:
            logger.error(f'Error calculating factor exposures: {str(e)}')
            return {}

    def _calculate_risk_contributions(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]], factor_exposures: Dict[str, float]) -> Dict[str, float]:
        """Calculate risk contribution by factor"""
        risk_contributions = {}
        portfolio_variance = float(self._calculate_volatility(portfolio_returns) ** 2)
        for factor_name, factor_rets in factor_returns.items():
            beta_key = f'{factor_name}_beta'
            if beta_key in factor_exposures and len(factor_rets) == len(portfolio_returns):
                factor_beta = Decimal(str(factor_exposures[beta_key]))
                factor_variance = self._calculate_volatility([Decimal(str(r)) for r in factor_rets]) ** 2
                if portfolio_variance > 0:
                    risk_contrib = float(factor_beta ** 2 * factor_variance / Decimal(str(portfolio_variance)))
                    risk_contributions[factor_name] = risk_contrib
        return risk_contributions

    def _calculate_idiosyncratic_risk(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]], factor_exposures: Dict[str, float]) -> Decimal:
        """Calculate idiosyncratic (specific) risk"""
        try:
            total_variance = self._calculate_volatility(portfolio_returns) ** 2
            explained_variance = Decimal('0')
            for factor_name, factor_rets in factor_returns.items():
                beta_key = f'{factor_name}_beta'
                if beta_key in factor_exposures and len(factor_rets) == len(portfolio_returns):
                    factor_beta = Decimal(str(factor_exposures[beta_key]))
                    factor_variance = self._calculate_volatility([Decimal(str(r)) for r in factor_rets]) ** 2
                    explained_variance += factor_beta ** 2 * factor_variance
            idiosyncratic_variance = max(Decimal('0'), total_variance - explained_variance)
            return idiosyncratic_variance.sqrt()
        except Exception:
            return Decimal('0')

    def _calculate_scenario_impact(self, base_returns: List[Decimal], scenario_params: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate impact of specific scenario"""
        scenario_impact = {}
        shock_magnitude = scenario_params.get('shock_magnitude', Decimal('0'))
        shock_probability = scenario_params.get('probability', Decimal('1'))
        base_mean = sum(base_returns) / len(base_returns) if base_returns else Decimal('0')
        scenario_return = base_mean + shock_magnitude
        scenario_impact['scenario_return'] = float(scenario_return)
        scenario_impact['shock_magnitude'] = float(shock_magnitude)
        scenario_impact['probability'] = float(shock_probability)
        expected_impact = scenario_return * shock_probability
        scenario_impact['expected_impact'] = float(expected_impact)
        return scenario_impact

    def _summarize_scenario_outcomes(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize scenario analysis outcomes"""
        summary = {}
        scenario_returns = []
        expected_impacts = []
        for scenario_name, scenario_data in scenario_results.items():
            if isinstance(scenario_data, dict) and 'scenario_return' in scenario_data:
                scenario_returns.append(scenario_data['scenario_return'])
                if 'expected_impact' in scenario_data:
                    expected_impacts.append(scenario_data['expected_impact'])
        if scenario_returns:
            summary['best_case_return'] = max(scenario_returns)
            summary['worst_case_return'] = min(scenario_returns)
            summary['scenario_range'] = max(scenario_returns) - min(scenario_returns)
        if expected_impacts:
            summary['expected_scenario_impact'] = sum(expected_impacts) / len(expected_impacts)
        return summary

    def _find_worst_consecutive_periods(self, returns: List[Decimal], num_periods: int) -> Decimal:
        """Find worst consecutive period returns"""
        if len(returns) < num_periods:
            return Decimal('0')
        worst_cumulative = Decimal('0')
        for i in range(len(returns) - num_periods + 1):
            cumulative_return = Decimal('1')
            for j in range(i, i + num_periods):
                cumulative_return *= Decimal('1') + returns[j]
            period_return = cumulative_return - Decimal('1')
            if period_return < worst_cumulative:
                worst_cumulative = period_return
        return worst_cumulative

    def _get_asset_class_scenarios(self, asset_class: AssetClass) -> Dict[str, Any]:
        """Get asset class specific stress scenarios"""
        scenarios = {}
        if asset_class == AssetClass.PRIVATE_EQUITY:
            scenarios.update({'recession_scenario': {'description': 'Economic recession impact', 'expected_impact': -0.3, 'recovery_time': '24_months'}, 'credit_crunch': {'description': 'Limited exit opportunities', 'expected_impact': -0.25, 'recovery_time': '18_months'}})
        elif asset_class == AssetClass.REAL_ESTATE:
            scenarios.update({'interest_rate_shock': {'description': '300bp rate increase', 'expected_impact': -0.2, 'recovery_time': '12_months'}, 'property_market_crash': {'description': 'Property values decline', 'expected_impact': -0.35, 'recovery_time': '36_months'}})
        elif asset_class == AssetClass.COMMODITIES:
            scenarios.update({'demand_shock': {'description': 'Global demand reduction', 'expected_impact': -0.4, 'recovery_time': '6_months'}, 'supply_disruption': {'description': 'Supply chain disruption', 'expected_impact': 0.25, 'recovery_time': '12_months'}})
        elif asset_class == AssetClass.HEDGE_FUND:
            scenarios.update({'market_volatility_spike': {'description': 'VIX above 40', 'expected_impact': -0.15, 'recovery_time': '3_months'}, 'liquidity_crisis': {'description': 'Redemption pressure', 'expected_impact': -0.2, 'recovery_time': '6_months'}})
        elif asset_class == AssetClass.DIGITAL_ASSETS:
            scenarios.update({'regulatory_crackdown': {'description': 'Major regulatory restrictions', 'expected_impact': -0.5, 'recovery_time': '12_months'}, 'crypto_winter': {'description': 'Extended bear market', 'expected_impact': -0.7, 'recovery_time': '24_months'}})
        return scenarios

def stress_testing(self, returns: List[Decimal], asset_class: AssetClass=None) -> Dict[str, Any]:
    """
        Comprehensive stress testing framework
        CFA Standard: Scenario analysis and stress testing
        """
    if not returns:
        return {'error': 'No return data provided'}
    stress_results = {}
    historical_scenarios = self._historical_stress_scenarios(returns)
    stress_results['historical_scenarios'] = historical_scenarios
    hypothetical_scenarios = self._hypothetical_stress_scenarios(returns, asset_class)
    stress_results['hypothetical_scenarios'] = hypothetical_scenarios
    monte_carlo_scenarios = self._monte_carlo_stress_testing(returns)
    stress_results['monte_carlo_scenarios'] = monte_carlo_scenarios
    tail_risk = self._analyze_tail_risk(returns)
    stress_results['tail_risk_analysis'] = tail_risk
    return stress_results

