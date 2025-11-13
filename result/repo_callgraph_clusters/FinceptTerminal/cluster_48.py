# Cluster 48

class RiskManagement:
    """Main risk management interface"""

    def __init__(self, parameters: RiskParameters=DEFAULT_RISK_PARAMS):
        self.parameters = parameters
        self.governance = RiskGovernance()
        self.risk_budgeting = None

    def comprehensive_risk_analysis(self, returns_data: Union[np.ndarray, Dict[str, np.ndarray]], weights: Optional[np.ndarray]=None, portfolio_value: float=1000000) -> Dict:
        """Perform comprehensive risk analysis"""
        if isinstance(returns_data, dict):
            returns_matrix = np.array([returns_data[asset] for asset in returns_data.keys()]).T
            if weights is None:
                weights = np.ones(len(returns_data)) / len(returns_data)
            portfolio_returns = np.dot(returns_matrix, weights)
            asset_names = list(returns_data.keys())
        else:
            portfolio_returns = np.array(returns_data)
            returns_matrix = portfolio_returns.reshape(-1, 1)
            weights = np.array([1.0])
            asset_names = ['Portfolio']
        results = {'basic_risk_metrics': self._calculate_basic_risk_metrics(portfolio_returns), 'var_analysis': self._comprehensive_var_analysis(portfolio_returns), 'stress_testing': self._perform_stress_testing(portfolio_returns), 'risk_decomposition': None}
        if len(asset_names) > 1:
            results['risk_decomposition'] = VaRCalculations.component_var(portfolio_returns, returns_matrix, weights)
        results['dollar_metrics'] = self._convert_to_dollar_metrics(results, portfolio_value)
        return results

    def _calculate_basic_risk_metrics(self, returns: np.ndarray) -> Dict:
        """Calculate basic risk metrics"""
        return {'volatility_daily': np.std(returns, ddof=1), 'volatility_annual': np.std(returns, ddof=1) * np.sqrt(MathConstants.TRADING_DAYS_YEAR), 'downside_deviation': StatisticalCalculations.calculate_downside_deviation(returns), 'max_drawdown': self._calculate_max_drawdown(returns), 'skewness': stats.skew(returns), 'kurtosis': stats.kurtosis(returns, fisher=False), 'jarque_bera_test': stats.jarque_bera(returns)}

    def _comprehensive_var_analysis(self, returns: np.ndarray) -> Dict:
        """Comprehensive VaR analysis with multiple methods"""
        var_results = {}
        for confidence_level in self.parameters.var_confidence_levels:
            var_results[f'var_{int(confidence_level * 100)}'] = {'parametric_normal': VaRCalculations.parametric_var(returns, confidence_level, distribution='normal'), 'parametric_t': VaRCalculations.parametric_var(returns, confidence_level, distribution='t_distribution'), 'historical': {'var': RiskCalculations.value_at_risk_historical(returns, confidence_level), 'cvar': RiskCalculations.conditional_value_at_risk(returns, confidence_level)}, 'monte_carlo': VaRCalculations.monte_carlo_var(returns, confidence_level, num_simulations=self.parameters.monte_carlo_simulations)}
        return var_results

    def _perform_stress_testing(self, returns: np.ndarray) -> Dict:
        """Perform comprehensive stress testing"""
        return ScenarioAnalysis.stress_testing(returns, self.parameters.stress_scenarios)

    def _calculate_max_drawdown(self, returns: np.ndarray) -> Dict:
        """Calculate maximum drawdown statistics"""
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)
        peak_idx = np.argmax(running_max[:max_dd_idx + 1]) if max_dd_idx > 0 else 0
        return {'max_drawdown': max_dd, 'peak_to_trough_days': max_dd_idx - peak_idx, 'drawdown_series': drawdown}

    def _convert_to_dollar_metrics(self, results: Dict, portfolio_value: float) -> Dict:
        """Convert percentage metrics to dollar amounts"""
        dollar_metrics = {}
        if 'var_analysis' in results:
            for var_level, var_data in results['var_analysis'].items():
                dollar_metrics[var_level] = {}
                if 'historical' in var_data:
                    dollar_metrics[var_level]['historical_var'] = var_data['historical']['var'] * portfolio_value
                    dollar_metrics[var_level]['historical_cvar'] = var_data['historical']['cvar'] * portfolio_value
                if 'parametric_normal' in var_data:
                    dollar_metrics[var_level]['parametric_var'] = var_data['parametric_normal']['var'] * portfolio_value
        return dollar_metrics

def __init__(self, parameters: RiskParameters=DEFAULT_RISK_PARAMS):
    self.parameters = parameters
    self.governance = RiskGovernance()
    self.risk_budgeting = None

