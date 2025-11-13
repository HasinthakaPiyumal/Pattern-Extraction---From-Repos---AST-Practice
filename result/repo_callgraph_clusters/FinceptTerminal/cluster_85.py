# Cluster 85

class GrowthAnalyzer(EconomicsBase):
    """Main economic growth analysis coordinator"""

    def __init__(self, precision: int=8, base_currency: str='USD'):
        super().__init__(precision, base_currency)
        self.productivity = ProductivityAnalyzer(precision, base_currency)
        self.convergence = ConvergenceAnalyzer(precision, base_currency)
        self.demographic = DemographicAnalyzer(precision, base_currency)

    def compare_growth_factors(self, country_type: str, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare factors favoring and limiting growth in developed vs developing economies"""
        if country_type.lower() not in ['developed', 'developing']:
            raise ValidationError("Country type must be 'developed' or 'developing'")
        if country_type.lower() == 'developed':
            return self._analyze_developed_economy_factors(economic_data)
        else:
            return self._analyze_developing_economy_factors(economic_data)

    def _analyze_developed_economy_factors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth factors for developed economies"""
        gdp_per_capita = self.to_decimal(data.get('gdp_per_capita', 0))
        rd_spending = self.to_decimal(data.get('rd_spending_percent_gdp', 0))
        education_index = self.to_decimal(data.get('education_index', 0))
        infrastructure_quality = self.to_decimal(data.get('infrastructure_quality', 0))
        population_growth = self.to_decimal(data.get('population_growth_rate', 0))
        aging_ratio = self.to_decimal(data.get('old_age_dependency_ratio', 0))
        favoring_factors = {'technological_innovation': {'score': rd_spending * self.to_decimal(10), 'description': 'High R&D spending drives innovation-led growth', 'weight': self.to_decimal(0.25)}, 'human_capital': {'score': education_index * self.to_decimal(100), 'description': 'Skilled workforce enables productivity gains', 'weight': self.to_decimal(0.2)}, 'institutional_quality': {'score': infrastructure_quality, 'description': 'Strong institutions support efficient markets', 'weight': self.to_decimal(0.2)}, 'capital_deepening': {'score': self.to_decimal(85), 'description': 'Existing capital stock supports productivity', 'weight': self.to_decimal(0.15)}}
        limiting_factors = {'demographic_constraints': {'score': aging_ratio, 'description': 'Aging population reduces labor force growth', 'weight': self.to_decimal(0.3)}, 'diminishing_returns': {'score': gdp_per_capita / self.to_decimal(1000), 'description': 'High income levels face diminishing marginal returns', 'weight': self.to_decimal(0.25)}, 'low_population_growth': {'score': max(self.to_decimal(0), self.to_decimal(2) - population_growth) * self.to_decimal(50), 'description': 'Low population growth limits labor force expansion', 'weight': self.to_decimal(0.2)}, 'mature_economy_constraints': {'score': self.to_decimal(70), 'description': 'Limited catch-up growth opportunities', 'weight': self.to_decimal(0.25)}}
        favoring_score = sum((factor['score'] * factor['weight'] for factor in favoring_factors.values()))
        limiting_score = sum((factor['score'] * factor['weight'] for factor in limiting_factors.values()))
        return {'country_type': 'developed', 'favoring_factors': favoring_factors, 'limiting_factors': limiting_factors, 'composite_favoring_score': favoring_score, 'composite_limiting_score': limiting_score, 'net_growth_potential': favoring_score - limiting_score, 'primary_growth_drivers': ['technological_innovation', 'human_capital'], 'main_constraints': ['demographic_constraints', 'diminishing_returns']}

    def _analyze_developing_economy_factors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth factors for developing economies"""
        gdp_per_capita = self.to_decimal(data.get('gdp_per_capita', 0))
        savings_rate = self.to_decimal(data.get('savings_rate', 0))
        fdi_inflows = self.to_decimal(data.get('fdi_percent_gdp', 0))
        population_growth = self.to_decimal(data.get('population_growth_rate', 0))
        institutional_quality = self.to_decimal(data.get('institutional_quality_index', 0))
        education_enrollment = self.to_decimal(data.get('secondary_education_enrollment', 0))
        favoring_factors = {'catch_up_potential': {'score': max(self.to_decimal(0), self.to_decimal(50) - gdp_per_capita / self.to_decimal(1000)), 'description': 'Low income levels allow rapid catch-up growth', 'weight': self.to_decimal(0.25)}, 'demographic_dividend': {'score': min(population_growth * self.to_decimal(25), self.to_decimal(100)), 'description': 'Young population provides growing workforce', 'weight': self.to_decimal(0.2)}, 'capital_accumulation': {'score': savings_rate * self.to_decimal(2), 'description': 'High savings enable capital investment', 'weight': self.to_decimal(0.2)}, 'technology_transfer': {'score': fdi_inflows * self.to_decimal(10), 'description': 'FDI brings advanced technology and knowledge', 'weight': self.to_decimal(0.15)}, 'education_expansion': {'score': education_enrollment, 'description': 'Growing human capital base', 'weight': self.to_decimal(0.2)}}
        limiting_factors = {'institutional_weaknesses': {'score': self.to_decimal(100) - institutional_quality, 'description': 'Weak institutions hinder efficient resource allocation', 'weight': self.to_decimal(0.3)}, 'infrastructure_gaps': {'score': self.to_decimal(80), 'description': 'Inadequate infrastructure limits productivity', 'weight': self.to_decimal(0.25)}, 'human_capital_deficits': {'score': self.to_decimal(100) - education_enrollment, 'description': 'Limited education reduces productivity potential', 'weight': self.to_decimal(0.2)}, 'external_dependence': {'score': self.to_decimal(60), 'description': 'Dependence on external financing and technology', 'weight': self.to_decimal(0.25)}}
        favoring_score = sum((factor['score'] * factor['weight'] for factor in favoring_factors.values()))
        limiting_score = sum((factor['score'] * factor['weight'] for factor in limiting_factors.values()))
        return {'country_type': 'developing', 'favoring_factors': favoring_factors, 'limiting_factors': limiting_factors, 'composite_favoring_score': favoring_score, 'composite_limiting_score': limiting_score, 'net_growth_potential': favoring_score - limiting_score, 'primary_growth_drivers': ['catch_up_potential', 'demographic_dividend'], 'main_constraints': ['institutional_weaknesses', 'infrastructure_gaps']}

    def analyze_stock_market_growth_relationship(self, market_data: Dict[str, Any], economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationship between stock market appreciation and sustainable growth rate"""
        stock_returns = [self.to_decimal(r) for r in market_data.get('annual_returns', [])]
        dividend_yield = self.to_decimal(market_data.get('dividend_yield', 0))
        pe_ratio = self.to_decimal(market_data.get('pe_ratio', 0))
        gdp_growth = self.to_decimal(economic_data.get('gdp_growth_rate', 0))
        productivity_growth = self.to_decimal(economic_data.get('productivity_growth', 0))
        employment_growth = self.to_decimal(economic_data.get('employment_growth', 0))
        if not stock_returns:
            raise ValidationError('Stock returns data is required')
        avg_stock_return = sum(stock_returns) / self.to_decimal(len(stock_returns))
        sustainable_growth = gdp_growth
        earnings_growth_component = gdp_growth
        dividend_component = dividend_yield
        valuation_change_component = avg_stock_return - earnings_growth_component - dividend_component
        excess_return = avg_stock_return - sustainable_growth
        return {'average_stock_return': avg_stock_return, 'sustainable_growth_rate': sustainable_growth, 'excess_return': excess_return, 'return_decomposition': {'earnings_growth': earnings_growth_component, 'dividend_yield': dividend_component, 'valuation_change': valuation_change_component}, 'long_run_relationship': {'description': 'In long run, stock returns should converge to sustainable growth + dividend yield', 'theoretical_return': sustainable_growth + dividend_yield, 'current_deviation': avg_stock_return - (sustainable_growth + dividend_yield), 'sustainable': abs(excess_return) < self.to_decimal(2)}, 'implications_for_investors': self._generate_stock_growth_implications(excess_return, pe_ratio)}

    def _generate_stock_growth_implications(self, excess_return: Decimal, pe_ratio: Decimal) -> Dict[str, str]:
        """Generate investment implications from stock-growth relationship"""
        implications = {}
        if excess_return > self.to_decimal(3):
            implications['valuation'] = 'Market may be overvalued relative to economic fundamentals'
            implications['future_returns'] = 'Expected returns may be below historical average'
            implications['risk'] = 'Higher risk of market correction'
        elif excess_return < self.to_decimal(-3):
            implications['valuation'] = 'Market may be undervalued relative to economic fundamentals'
            implications['future_returns'] = 'Expected returns may be above historical average'
            implications['risk'] = 'Potential opportunity for higher returns'
        else:
            implications['valuation'] = 'Market appears fairly valued relative to economic growth'
            implications['future_returns'] = 'Expected returns align with sustainable growth'
            implications['risk'] = 'Balanced risk-return profile'
        if pe_ratio > self.to_decimal(25):
            implications['pe_signal'] = 'High PE suggests expensive market'
        elif pe_ratio < self.to_decimal(12):
            implications['pe_signal'] = 'Low PE suggests attractive valuations'
        else:
            implications['pe_signal'] = 'PE ratio within normal range'
        return implications

    def potential_gdp_importance(self, gdp_data: Dict[str, Any], investor_type: str) -> Dict[str, Any]:
        """Explain importance of potential GDP for equity and fixed income investors"""
        potential_gdp = self.to_decimal(gdp_data.get('potential_gdp', 0))
        actual_gdp = self.to_decimal(gdp_data.get('actual_gdp', 0))
        potential_growth = self.to_decimal(gdp_data.get('potential_growth_rate', 0))
        output_gap = (actual_gdp - potential_gdp) / potential_gdp * self.to_decimal(100)
        if investor_type.lower() == 'equity':
            return self._equity_investor_implications(output_gap, potential_growth, gdp_data)
        elif investor_type.lower() == 'fixed_income':
            return self._fixed_income_implications(output_gap, potential_growth, gdp_data)
        else:
            return {'equity_implications': self._equity_investor_implications(output_gap, potential_growth, gdp_data), 'fixed_income_implications': self._fixed_income_implications(output_gap, potential_growth, gdp_data), 'output_gap': output_gap, 'potential_growth_rate': potential_growth}

    def _equity_investor_implications(self, output_gap: Decimal, potential_growth: Decimal, gdp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implications of potential GDP for equity investors"""
        return {'earnings_growth_potential': {'description': 'Potential GDP growth sets upper bound for long-term earnings growth', 'implication': f'Long-term earnings growth limited to ~{potential_growth:.1f}% annually', 'current_position': 'Above potential' if output_gap > 0 else 'Below potential'}, 'cyclical_positioning': {'output_gap': output_gap, 'interpretation': self._interpret_output_gap_equity(output_gap), 'strategy': self._equity_strategy_from_gap(output_gap)}, 'sector_implications': {'cyclical_sectors': 'Sensitive to output gap fluctuations', 'defensive_sectors': 'Less sensitive, focus on long-term potential growth', 'growth_sectors': 'Beneficiaries of productivity improvements driving potential growth'}, 'valuation_framework': {'sustainable_pe': f'Long-term PE ratios should reflect potential growth of {potential_growth:.1f}%', 'cyclical_adjustment': 'Adjust for temporary deviations from potential'}}

    def _fixed_income_implications(self, output_gap: Decimal, potential_growth: Decimal, gdp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implications of potential GDP for fixed income investors"""
        inflation_rate = self.to_decimal(gdp_data.get('inflation_rate', 0))
        return {'monetary_policy_stance': {'output_gap': output_gap, 'policy_implication': self._monetary_policy_from_gap(output_gap), 'interest_rate_direction': self._interest_rate_direction(output_gap)}, 'inflation_expectations': {'gap_pressure': 'Positive gap = inflationary pressure' if output_gap > 0 else 'Negative gap = disinflationary pressure', 'long_term_anchor': f'Long-term inflation should align with potential growth of {potential_growth:.1f}%', 'current_risk': 'Inflation risk elevated' if output_gap > self.to_decimal(2) else 'Inflation risk contained'}, 'yield_curve_implications': {'short_end': 'Driven by central bank response to output gap', 'long_end': 'Anchored by potential growth and inflation expectations', 'curve_shape': self._yield_curve_shape(output_gap)}, 'credit_risk_assessment': {'corporate_earnings': 'Tied to actual vs potential GDP performance', 'default_risk': 'Lower when economy operates near potential', 'recovery_rates': 'Higher potential growth supports better recovery values'}}

    def _interpret_output_gap_equity(self, gap: Decimal) -> str:
        """Interpret output gap for equity investors"""
        if gap > self.to_decimal(2):
            return 'Economy overheating - potential for policy tightening and earnings pressure'
        elif gap > self.to_decimal(0):
            return 'Economy above potential - supporting earnings but watch for inflation'
        elif gap > self.to_decimal(-2):
            return 'Economy near potential - balanced growth environment'
        else:
            return 'Economy below potential - room for growth but current earnings pressure'

    def _equity_strategy_from_gap(self, gap: Decimal) -> str:
        """Suggest equity strategy based on output gap"""
        if gap > self.to_decimal(2):
            return 'Consider defensive positioning, watch for policy tightening'
        elif gap > self.to_decimal(0):
            return 'Balanced approach, favor quality cyclicals'
        else:
            return 'Growth opportunities available, consider cyclical exposure'

    def _monetary_policy_from_gap(self, gap: Decimal) -> str:
        """Predict monetary policy stance from output gap"""
        if gap > self.to_decimal(1):
            return 'Likely tightening bias'
        elif gap > self.to_decimal(-1):
            return 'Neutral stance'
        else:
            return 'Likely easing bias'

    def _interest_rate_direction(self, gap: Decimal) -> str:
        """Predict interest rate direction"""
        if gap > self.to_decimal(1):
            return 'Upward pressure'
        elif gap > self.to_decimal(-1):
            return 'Stable'
        else:
            return 'Downward pressure'

    def _yield_curve_shape(self, gap: Decimal) -> str:
        """Predict yield curve shape"""
        if gap > self.to_decimal(2):
            return 'Flattening risk (short rates rising faster)'
        elif gap < self.to_decimal(-2):
            return 'Steepening (short rates falling faster)'
        else:
            return 'Stable shape'

    def forecast_potential_gdp(self, historical_data: Dict[str, Any], forecast_assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast potential GDP using growth accounting relations"""
        labor_force_growth = [self.to_decimal(x) for x in historical_data.get('labor_force_growth', [])]
        productivity_growth = [self.to_decimal(x) for x in historical_data.get('productivity_growth', [])]
        capital_growth = [self.to_decimal(x) for x in historical_data.get('capital_growth', [])]
        forecast_periods = int(forecast_assumptions.get('periods', 5))
        labor_growth_forecast = self.to_decimal(forecast_assumptions.get('labor_growth_rate', 0))
        productivity_growth_forecast = self.to_decimal(forecast_assumptions.get('productivity_growth_rate', 0))
        capital_growth_forecast = self.to_decimal(forecast_assumptions.get('capital_growth_rate', 0))
        alpha = self.to_decimal(forecast_assumptions.get('capital_share', 0.3))
        historical_potential = []
        min_length = min(len(labor_force_growth), len(productivity_growth), len(capital_growth))
        for i in range(min_length):
            potential_growth = productivity_growth[i] + alpha * capital_growth[i] + (self.to_decimal(1) - alpha) * labor_force_growth[i]
            historical_potential.append(potential_growth)
        forecast_potential_growth = productivity_growth_forecast + alpha * capital_growth_forecast + (self.to_decimal(1) - alpha) * labor_growth_forecast
        trend_productivity = sum(productivity_growth) / self.to_decimal(len(productivity_growth)) if productivity_growth else self.to_decimal(0)
        trend_labor = sum(labor_force_growth) / self.to_decimal(len(labor_force_growth)) if labor_force_growth else self.to_decimal(0)
        trend_capital = sum(capital_growth) / self.to_decimal(len(capital_growth)) if capital_growth else self.to_decimal(0)
        return {'growth_accounting_framework': {'formula': 'GDP Growth = Productivity Growth + α×Capital Growth + (1-α)×Labor Growth', 'capital_share_alpha': alpha, 'labor_share': self.to_decimal(1) - alpha}, 'historical_analysis': {'historical_potential_growth': historical_potential, 'average_historical_potential': sum(historical_potential) / self.to_decimal(len(historical_potential)) if historical_potential else self.to_decimal(0), 'trend_components': {'productivity': trend_productivity, 'labor_force': trend_labor, 'capital_stock': trend_capital}}, 'forecast': {'periods': forecast_periods, 'potential_gdp_growth': forecast_potential_growth, 'components': {'productivity_contribution': productivity_growth_forecast, 'capital_contribution': alpha * capital_growth_forecast, 'labor_contribution': (self.to_decimal(1) - alpha) * labor_growth_forecast}, 'assumptions': forecast_assumptions}, 'sensitivity_analysis': self._sensitivity_analysis_potential_gdp(alpha, productivity_growth_forecast, capital_growth_forecast, labor_growth_forecast)}

    def _sensitivity_analysis_potential_gdp(self, alpha: Decimal, prod_growth: Decimal, cap_growth: Decimal, lab_growth: Decimal) -> Dict[str, Any]:
        """Sensitivity analysis for potential GDP forecast"""
        base_growth = prod_growth + alpha * cap_growth + (self.to_decimal(1) - alpha) * lab_growth
        scenarios = {'productivity_high': prod_growth + self.to_decimal(0.005), 'productivity_low': prod_growth - self.to_decimal(0.005), 'capital_high': cap_growth + self.to_decimal(0.01), 'capital_low': cap_growth - self.to_decimal(0.01), 'labor_high': lab_growth + self.to_decimal(0.005), 'labor_low': lab_growth - self.to_decimal(0.005)}
        sensitivity_results = {}
        for scenario, value in scenarios.items():
            if 'productivity' in scenario:
                new_growth = value + alpha * cap_growth + (self.to_decimal(1) - alpha) * lab_growth
            elif 'capital' in scenario:
                new_growth = prod_growth + alpha * value + (self.to_decimal(1) - alpha) * lab_growth
            else:
                new_growth = prod_growth + alpha * cap_growth + (self.to_decimal(1) - alpha) * value
            sensitivity_results[scenario] = {'growth_rate': new_growth, 'change_from_base': new_growth - base_growth}
        return {'base_case': base_growth, 'scenarios': sensitivity_results, 'most_sensitive_to': max(sensitivity_results.items(), key=lambda x: abs(x[1]['change_from_base']))[0]}

    def calculate(self, analysis_type: str, **kwargs) -> Dict[str, Any]:
        """Main calculation dispatcher"""
        calculations = {'growth_factors': lambda: self.compare_growth_factors(kwargs['country_type'], kwargs['economic_data']), 'stock_growth_relationship': lambda: self.analyze_stock_market_growth_relationship(kwargs['market_data'], kwargs['economic_data']), 'potential_gdp_importance': lambda: self.potential_gdp_importance(kwargs['gdp_data'], kwargs.get('investor_type', 'both')), 'forecast_potential_gdp': lambda: self.forecast_potential_gdp(kwargs['historical_data'], kwargs['forecast_assumptions'])}
        if analysis_type not in calculations:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = calculations[analysis_type]()
        result['metadata'] = self.get_metadata()
        result['analysis_type'] = analysis_type
        return result

def _equity_investor_implications(self, output_gap: Decimal, potential_growth: Decimal, gdp_data: Dict[str, Any]) -> Dict[str, Any]:
    """Implications of potential GDP for equity investors"""
    return {'earnings_growth_potential': {'description': 'Potential GDP growth sets upper bound for long-term earnings growth', 'implication': f'Long-term earnings growth limited to ~{potential_growth:.1f}% annually', 'current_position': 'Above potential' if output_gap > 0 else 'Below potential'}, 'cyclical_positioning': {'output_gap': output_gap, 'interpretation': self._interpret_output_gap_equity(output_gap), 'strategy': self._equity_strategy_from_gap(output_gap)}, 'sector_implications': {'cyclical_sectors': 'Sensitive to output gap fluctuations', 'defensive_sectors': 'Less sensitive, focus on long-term potential growth', 'growth_sectors': 'Beneficiaries of productivity improvements driving potential growth'}, 'valuation_framework': {'sustainable_pe': f'Long-term PE ratios should reflect potential growth of {potential_growth:.1f}%', 'cyclical_adjustment': 'Adjust for temporary deviations from potential'}}

