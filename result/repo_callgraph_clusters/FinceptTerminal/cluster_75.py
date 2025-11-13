# Cluster 75

class CreditCycleAnalyzer(EconomicsBase):
    """Credit cycle analysis and financial stability assessment"""

    def analyze_credit_cycle(self, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current credit cycle phase and characteristics"""
        credit_growth = self.to_decimal(credit_data.get('credit_growth_rate', 0))
        loan_standards = credit_data.get('lending_standards', 'neutral')
        credit_spreads = self.to_decimal(credit_data.get('credit_spreads_bps', 0))
        default_rates = self.to_decimal(credit_data.get('default_rate', 0))
        leverage_ratio = self.to_decimal(credit_data.get('leverage_ratio', 0))
        asset_prices = self.to_decimal(credit_data.get('asset_price_growth', 0))
        cycle_phase = self._determine_credit_phase(credit_growth, loan_standards, credit_spreads, default_rates)
        return {'credit_cycle_phase': cycle_phase, 'phase_characteristics': self._get_credit_phase_characteristics(cycle_phase), 'risk_assessment': self._assess_credit_risks(credit_growth, leverage_ratio, default_rates, asset_prices), 'financial_stability_indicators': self._analyze_financial_stability(credit_data), 'investment_implications': self._credit_cycle_investment_implications(cycle_phase), 'policy_implications': self._credit_cycle_policy_implications(cycle_phase, credit_data)}

    def _determine_credit_phase(self, credit_growth: Decimal, standards: str, spreads: Decimal, defaults: Decimal) -> str:
        """Determine current credit cycle phase"""
        if credit_growth > self.to_decimal(5) and standards == 'loose' and (spreads < self.to_decimal(200)):
            return 'expansion'
        elif credit_growth > self.to_decimal(8) and spreads < self.to_decimal(150) and (defaults < self.to_decimal(2)):
            return 'peak'
        elif credit_growth < self.to_decimal(0) and standards == 'tight' and (spreads > self.to_decimal(300)):
            return 'contraction'
        elif credit_growth < self.to_decimal(2) and defaults > self.to_decimal(5) and (spreads > self.to_decimal(400)):
            return 'trough'
        else:
            return 'transition'

    def _get_credit_phase_characteristics(self, phase: str) -> Dict[str, Any]:
        """Get characteristics of each credit cycle phase"""
        characteristics = {'expansion': {'credit_growth': 'Accelerating', 'lending_standards': 'Loosening', 'credit_spreads': 'Tightening', 'default_rates': 'Low and declining', 'asset_prices': 'Rising', 'risk_appetite': 'Increasing', 'typical_duration': '3-7 years'}, 'peak': {'credit_growth': 'Very high but potentially slowing', 'lending_standards': 'Very loose', 'credit_spreads': 'Very tight', 'default_rates': 'Near cyclical lows', 'asset_prices': 'Near peaks, potential bubbles', 'risk_appetite': 'Excessive', 'typical_duration': '6-18 months'}, 'contraction': {'credit_growth': 'Negative', 'lending_standards': 'Tightening rapidly', 'credit_spreads': 'Widening', 'default_rates': 'Rising sharply', 'asset_prices': 'Declining', 'risk_appetite': 'Risk aversion', 'typical_duration': '1-3 years'}, 'trough': {'credit_growth': 'Negative but stabilizing', 'lending_standards': 'Very tight', 'credit_spreads': 'Wide but stabilizing', 'default_rates': 'High but peaking', 'asset_prices': 'Depressed but stabilizing', 'risk_appetite': 'Extremely low', 'typical_duration': '6-18 months'}}
        return characteristics.get(phase, {})

    def _assess_credit_risks(self, credit_growth: Decimal, leverage: Decimal, defaults: Decimal, asset_prices: Decimal) -> Dict[str, Any]:
        """Assess systemic credit risks"""
        risk_score = self.to_decimal(0)
        risk_factors = []
        if credit_growth > self.to_decimal(10):
            risk_score += self.to_decimal(25)
            risk_factors.append('Excessive credit growth')
        if leverage > self.to_decimal(8):
            risk_score += self.to_decimal(25)
            risk_factors.append('High leverage ratios')
        if defaults > self.to_decimal(4):
            risk_score += self.to_decimal(20)
            risk_factors.append('Rising default rates')
        if asset_prices > self.to_decimal(15):
            risk_score += self.to_decimal(20)
            risk_factors.append('Asset price bubbles')
        if risk_score > self.to_decimal(60):
            risk_level = 'High'
        elif risk_score > self.to_decimal(30):
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        return {'overall_risk_score': risk_score, 'risk_level': risk_level, 'key_risk_factors': risk_factors, 'systemic_risk_probability': self._calculate_systemic_risk_probability(risk_score)}

    def _calculate_systemic_risk_probability(self, risk_score: Decimal) -> str:
        """Calculate probability of systemic financial crisis"""
        if risk_score > self.to_decimal(70):
            return 'High (>30% in next 2 years)'
        elif risk_score > self.to_decimal(50):
            return 'Moderate (10-30% in next 2 years)'
        elif risk_score > self.to_decimal(30):
            return 'Low (5-10% in next 2 years)'
        else:
            return 'Very Low (<5% in next 2 years)'

    def _analyze_financial_stability(self, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial stability indicators"""
        return {'banking_sector_health': {'capital_adequacy': credit_data.get('bank_capital_ratio', 'N/A'), 'loan_loss_provisions': credit_data.get('loan_loss_provisions', 'N/A'), 'profitability': credit_data.get('bank_roe', 'N/A'), 'asset_quality': credit_data.get('npl_ratio', 'N/A')}, 'household_sector': {'debt_to_income': credit_data.get('household_debt_ratio', 'N/A'), 'mortgage_defaults': credit_data.get('mortgage_default_rate', 'N/A'), 'savings_rate': credit_data.get('household_savings_rate', 'N/A')}, 'corporate_sector': {'corporate_debt_ratio': credit_data.get('corporate_debt_gdp', 'N/A'), 'interest_coverage': credit_data.get('interest_coverage_ratio', 'N/A'), 'bankruptcy_rate': credit_data.get('corporate_bankruptcy_rate', 'N/A')}, 'government_sector': {'debt_to_gdp': credit_data.get('government_debt_gdp', 'N/A'), 'deficit_ratio': credit_data.get('budget_deficit_gdp', 'N/A')}}

    def _credit_cycle_investment_implications(self, phase: str) -> Dict[str, Any]:
        """Investment implications for each credit cycle phase"""
        implications = {'expansion': {'credit_sensitive_sectors': 'Favor banks, real estate, consumer finance', 'fixed_income': 'Corporate bonds outperform, credit spreads tighten', 'equity_strategy': 'Growth and cyclical stocks perform well', 'risk_management': 'Monitor leverage, prepare for cycle turn'}, 'peak': {'credit_sensitive_sectors': 'Begin reducing exposure to credit cyclicals', 'fixed_income': 'Lock in credit spreads, extend duration', 'equity_strategy': 'Rotate to defensive sectors', 'risk_management': 'Reduce overall risk exposure'}, 'contraction': {'credit_sensitive_sectors': 'Avoid banks, real estate, high-yield bonds', 'fixed_income': 'Government bonds, high-grade corporates', 'equity_strategy': 'Defensive sectors, dividend stocks', 'risk_management': 'Capital preservation focus'}, 'trough': {'credit_sensitive_sectors': 'Prepare for opportunistic investments', 'fixed_income': 'Distressed debt opportunities', 'equity_strategy': 'Value opportunities in beaten-down sectors', 'risk_management': 'Begin rebuilding risk exposure'}}
        return implications.get(phase, {})

    def _credit_cycle_policy_implications(self, phase: str, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Policy implications for each credit cycle phase"""
        base_implications = {'expansion': {'monetary_policy': 'Consider gradual tightening to prevent bubbles', 'macroprudential': 'Implement countercyclical capital buffers', 'regulatory': 'Monitor systemic risk buildup'}, 'peak': {'monetary_policy': 'Careful balancing to prevent hard landing', 'macroprudential': 'Activate countercyclical buffers', 'regulatory': 'Stress test financial institutions'}, 'contraction': {'monetary_policy': 'Aggressive easing to support credit flow', 'macroprudential': 'Release countercyclical buffers', 'regulatory': 'Temporary forbearance measures'}, 'trough': {'monetary_policy': 'Maintain accommodative stance', 'macroprudential': 'Gradual rebuilding of buffers', 'regulatory': 'Support credit intermediation'}}
        return base_implications.get(phase, {})

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Calculate credit cycle analysis"""
        return self.analyze_credit_cycle(kwargs['credit_data'])

def calculate(self, **kwargs) -> Dict[str, Any]:
    """Calculate credit cycle analysis"""
    return self.analyze_credit_cycle(kwargs['credit_data'])

