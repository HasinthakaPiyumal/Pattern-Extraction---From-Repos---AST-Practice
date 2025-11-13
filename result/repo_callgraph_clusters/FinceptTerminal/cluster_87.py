# Cluster 87

class ConvergenceAnalyzer(EconomicsBase):
    """Economic convergence hypotheses analysis"""

    def test_convergence_hypotheses(self, country_data: List[Dict[str, Any]], convergence_type: str='beta') -> Dict[str, Any]:
        """Test convergence hypotheses (beta and sigma convergence)"""
        if convergence_type not in ['beta', 'sigma', 'both']:
            raise ValidationError("Convergence type must be 'beta', 'sigma', or 'both'")
        results = {}
        if convergence_type in ['beta', 'both']:
            results['beta_convergence'] = self._test_beta_convergence(country_data)
        if convergence_type in ['sigma', 'both']:
            results['sigma_convergence'] = self._test_sigma_convergence(country_data)
        results['convergence_theories'] = self._explain_convergence_theories()
        return results

    def _test_beta_convergence(self, country_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test beta convergence (catch-up effect)"""
        initial_gdp = []
        growth_rates = []
        for country in country_data:
            initial_gdp.append(self.to_decimal(country['initial_gdp_per_capita']))
            growth_rates.append(self.to_decimal(country['avg_growth_rate']))
        if len(initial_gdp) < 3:
            raise ValidationError('At least 3 countries required for convergence analysis')
        correlation = self._calculate_correlation(initial_gdp, growth_rates)
        convergence_speed = -correlation * self.to_decimal(0.02)
        half_life = self.to_decimal(0.693) / abs(convergence_speed) if convergence_speed != 0 else None
        return {'correlation_coefficient': correlation, 'convergence_exists': correlation < self.to_decimal(-0.3), 'convergence_speed': convergence_speed, 'half_life_years': half_life, 'interpretation': self._interpret_beta_convergence(correlation), 'countries_analyzed': len(country_data)}

    def _test_sigma_convergence(self, country_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test sigma convergence (dispersion reduction)"""
        time_periods = {}
        for country in country_data:
            for year, gdp in country.get('gdp_time_series', {}).items():
                if year not in time_periods:
                    time_periods[year] = []
                time_periods[year].append(self.to_decimal(gdp))
        dispersions = {}
        for year, gdp_values in time_periods.items():
            if len(gdp_values) > 1:
                mean_gdp = sum(gdp_values) / self.to_decimal(len(gdp_values))
                variance = sum(((x - mean_gdp) ** 2 for x in gdp_values)) / self.to_decimal(len(gdp_values) - 1)
                dispersions[year] = variance.sqrt()
        years = sorted(dispersions.keys())
        if len(years) < 2:
            raise ValidationError('At least 2 time periods required for sigma convergence')
        initial_dispersion = dispersions[years[0]]
        final_dispersion = dispersions[years[-1]]
        dispersion_change = (final_dispersion - initial_dispersion) / initial_dispersion
        return {'initial_dispersion': initial_dispersion, 'final_dispersion': final_dispersion, 'dispersion_change_percent': dispersion_change * self.to_decimal(100), 'sigma_convergence_exists': final_dispersion < initial_dispersion, 'time_periods_analyzed': len(years), 'dispersion_trend': 'Decreasing' if final_dispersion < initial_dispersion else 'Increasing'}

    def _calculate_correlation(self, x_values: List[Decimal], y_values: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient"""
        n = len(x_values)
        if n != len(y_values) or n < 2:
            return self.to_decimal(0)
        mean_x = sum(x_values) / self.to_decimal(n)
        mean_y = sum(y_values) / self.to_decimal(n)
        numerator = sum(((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n)))
        sum_sq_x = sum(((x - mean_x) ** 2 for x in x_values))
        sum_sq_y = sum(((y - mean_y) ** 2 for y in y_values))
        denominator = (sum_sq_x * sum_sq_y).sqrt()
        return numerator / denominator if denominator != 0 else self.to_decimal(0)

    def _interpret_beta_convergence(self, correlation: Decimal) -> str:
        """Interpret beta convergence results"""
        if correlation < self.to_decimal(-0.5):
            return 'Strong beta convergence: Poor countries growing significantly faster'
        elif correlation < self.to_decimal(-0.3):
            return 'Moderate beta convergence: Some catch-up effect observed'
        elif correlation < self.to_decimal(-0.1):
            return 'Weak beta convergence: Limited catch-up effect'
        else:
            return 'No beta convergence: No systematic catch-up by poor countries'

    def _explain_convergence_theories(self) -> Dict[str, Any]:
        """Explain convergence theories"""
        return {'neoclassical_theory': {'prediction': 'Unconditional convergence due to diminishing returns', 'mechanism': 'Poor countries have higher marginal returns to capital', 'assumptions': 'Same technology, preferences, institutions', 'reality': 'Limited empirical support for unconditional convergence'}, 'conditional_convergence': {'prediction': 'Convergence to country-specific steady states', 'mechanism': 'Countries converge to own equilibrium based on fundamentals', 'factors': 'Savings rates, population growth, technology, institutions', 'evidence': 'Stronger empirical support'}, 'endogenous_growth': {'prediction': 'Divergence possible due to increasing returns', 'mechanism': 'Knowledge spillovers, human capital externalities', 'implications': 'Rich countries may grow faster permanently', 'policy': 'Government intervention may be needed'}}

    def calculate(self, convergence_type: str='both', **kwargs) -> Dict[str, Any]:
        """Calculate convergence analysis"""
        return self.test_convergence_hypotheses(kwargs['country_data'], convergence_type)

def calculate(self, convergence_type: str='both', **kwargs) -> Dict[str, Any]:
    """Calculate convergence analysis"""
    return self.test_convergence_hypotheses(kwargs['country_data'], convergence_type)

