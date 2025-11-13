# Cluster 76

class FiscalPolicyAnalyzer(EconomicsBase):
    """Fiscal policy analysis and impact assessment"""

    def compare_fiscal_monetary(self) -> Dict[str, Any]:
        """Compare fiscal and monetary policy characteristics"""
        return {'fiscal_policy': {'authority': 'Government (legislative/executive)', 'tools': ['Government spending', 'Taxation', 'Transfer payments'], 'targets': ['Economic growth', 'Employment', 'Income distribution'], 'transmission': 'Direct impact on aggregate demand', 'lag_time': 'Long (6-18 months)', 'political_influence': 'High', 'flexibility': 'Low (requires legislative approval)'}, 'monetary_policy': {'authority': 'Central bank', 'tools': ['Interest rates', 'Money supply', 'Reserve requirements'], 'targets': ['Price stability', 'Economic growth', 'Financial stability'], 'transmission': 'Indirect through financial markets', 'lag_time': 'Medium (3-12 months)', 'political_influence': 'Low (independent)', 'flexibility': 'High (quick implementation)'}, 'interaction_effects': {'complementary': 'Both expansionary during recession', 'conflicting': 'Fiscal expansion with monetary tightening', 'coordination_importance': 'Critical for policy effectiveness'}}

    def analyze_fiscal_tools(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fiscal policy tools and their effects"""
        tools_analysis = {'government_spending': {'multiplier_effect': self._calculate_spending_multiplier(policy_data), 'advantages': ['Direct job creation', 'Infrastructure investment', 'Quick stimulus'], 'disadvantages': ['Crowding out private investment', 'Debt accumulation', 'Political interference'], 'effectiveness': 'High during recessions, moderate during expansions'}, 'taxation': {'multiplier_effect': self._calculate_tax_multiplier(policy_data), 'advantages': ['Broad-based impact', 'Revenue generation', 'Incentive alignment'], 'disadvantages': ['Lagged response', 'Political constraints', 'Distortionary effects'], 'effectiveness': 'Moderate, depends on tax type and economic conditions'}, 'transfer_payments': {'multiplier_effect': self._calculate_transfer_multiplier(policy_data), 'advantages': ['Targeted support', 'Automatic stabilizers', 'Social safety net'], 'disadvantages': ['Potential dependency', 'Fiscal burden', 'Limited growth impact'], 'effectiveness': 'High for consumption support, moderate for growth'}}
        return {'tools_analysis': tools_analysis, 'implementation_challenges': self._assess_implementation_challenges(), 'policy_recommendation': self._recommend_fiscal_mix(policy_data)}

    def assess_debt_sustainability(self, debt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess whether national debt relative to GDP matters"""
        debt_gdp = self.to_decimal(debt_data.get('debt_to_gdp_ratio', 0))
        gdp_growth = self.to_decimal(debt_data.get('gdp_growth_rate', 0))
        interest_rate = self.to_decimal(debt_data.get('avg_interest_rate', 0))
        primary_balance = self.to_decimal(debt_data.get('primary_balance_gdp', 0))
        sustainability_gap = interest_rate - gdp_growth - primary_balance
        if debt_gdp > self.to_decimal(100):
            risk_level = 'Very High'
        elif debt_gdp > self.to_decimal(60):
            risk_level = 'High'
        elif debt_gdp > self.to_decimal(40):
            risk_level = 'Moderate'
        else:
            risk_level = 'Low'
        return {'debt_to_gdp': debt_gdp, 'sustainability_gap': sustainability_gap, 'sustainable': sustainability_gap < self.to_decimal(0), 'risk_level': risk_level, 'debt_dynamics': {'interest_burden': interest_rate * debt_gdp / self.to_decimal(100), 'growth_benefit': gdp_growth * debt_gdp / self.to_decimal(100), 'primary_contribution': primary_balance}, 'implications': self._get_debt_implications(debt_gdp, sustainability_gap)}

    def identify_policy_stance(self, fiscal_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Identify if fiscal policy is expansionary or contractionary"""
        spending_change = self.to_decimal(fiscal_indicators.get('spending_change_percent', 0))
        tax_change = self.to_decimal(fiscal_indicators.get('tax_change_percent', 0))
        deficit_change = self.to_decimal(fiscal_indicators.get('deficit_change_gdp', 0))
        fiscal_impulse = spending_change - tax_change
        if fiscal_impulse > self.to_decimal(1):
            stance = 'Expansionary'
            description = 'Government increasing spending more than taxes'
        elif fiscal_impulse < self.to_decimal(-1):
            stance = 'Contractionary'
            description = 'Government reducing spending or increasing taxes significantly'
        else:
            stance = 'Neutral'
            description = 'Minimal net fiscal impact'
        return {'fiscal_stance': stance, 'fiscal_impulse': fiscal_impulse, 'description': description, 'stance_indicators': {'spending_change': spending_change, 'tax_change': tax_change, 'deficit_change': deficit_change}, 'economic_impact': self._assess_stance_impact(stance, fiscal_impulse)}

    def _calculate_spending_multiplier(self, data: Dict[str, Any]) -> Decimal:
        """Calculate government spending multiplier"""
        mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
        return self.to_decimal(1) / (self.to_decimal(1) - mpc)

    def _calculate_tax_multiplier(self, data: Dict[str, Any]) -> Decimal:
        """Calculate tax multiplier"""
        mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
        return -mpc / (self.to_decimal(1) - mpc)

    def _calculate_transfer_multiplier(self, data: Dict[str, Any]) -> Decimal:
        """Calculate transfer payment multiplier"""
        mpc = self.to_decimal(data.get('marginal_propensity_consume', 0.8))
        return mpc / (self.to_decimal(1) - mpc)

    def _assess_implementation_challenges(self) -> List[str]:
        """Assess fiscal policy implementation difficulties"""
        return ['Recognition lag: Time to identify economic problems', 'Legislative lag: Time for political approval', 'Implementation lag: Time to execute policy', 'Political constraints: Electoral and partisan considerations', 'Crowding out: Government borrowing affects private investment', 'Ricardian equivalence: Tax cuts offset by expected future taxes']

    def _recommend_fiscal_mix(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Recommend optimal fiscal policy mix"""
        unemployment = self.to_decimal(data.get('unemployment_rate', 0))
        inflation = self.to_decimal(data.get('inflation_rate', 0))
        if unemployment > self.to_decimal(7):
            return {'recommendation': 'Expansionary', 'focus': 'Job creation and demand stimulus'}
        elif inflation > self.to_decimal(4):
            return {'recommendation': 'Contractionary', 'focus': 'Reduce demand pressures'}
        else:
            return {'recommendation': 'Neutral', 'focus': 'Maintain fiscal balance'}

    def _get_debt_implications(self, debt_gdp: Decimal, gap: Decimal) -> Dict[str, str]:
        """Get implications of debt sustainability analysis"""
        if gap > self.to_decimal(2):
            return {'fiscal_space': 'Limited', 'interest_burden': 'High and rising', 'policy_flexibility': 'Constrained', 'investor_confidence': 'At risk'}
        else:
            return {'fiscal_space': 'Adequate', 'interest_burden': 'Manageable', 'policy_flexibility': 'Available', 'investor_confidence': 'Stable'}

    def _assess_stance_impact(self, stance: str, impulse: Decimal) -> Dict[str, str]:
        """Assess economic impact of fiscal stance"""
        impacts = {'Expansionary': {'gdp_impact': 'Positive stimulus to growth', 'employment_impact': 'Job creation likely', 'inflation_risk': 'Potential upward pressure', 'debt_impact': 'Increased deficit spending'}, 'Contractionary': {'gdp_impact': 'Negative drag on growth', 'employment_impact': 'Potential job losses', 'inflation_risk': 'Reduced price pressures', 'debt_impact': 'Deficit reduction'}, 'Neutral': {'gdp_impact': 'Minimal direct impact', 'employment_impact': 'Status quo maintained', 'inflation_risk': 'No significant pressure', 'debt_impact': 'Stable debt dynamics'}}
        return impacts.get(stance, {})

    def calculate(self, analysis_type: str='tools_analysis', **kwargs) -> Dict[str, Any]:
        """Main fiscal policy calculation dispatcher"""
        analyses = {'compare_policies': self.compare_fiscal_monetary, 'tools_analysis': lambda: self.analyze_fiscal_tools(kwargs.get('policy_data', {})), 'debt_sustainability': lambda: self.assess_debt_sustainability(kwargs.get('debt_data', {})), 'policy_stance': lambda: self.identify_policy_stance(kwargs.get('fiscal_indicators', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def analyze_fiscal_tools(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze fiscal policy tools and their effects"""
    tools_analysis = {'government_spending': {'multiplier_effect': self._calculate_spending_multiplier(policy_data), 'advantages': ['Direct job creation', 'Infrastructure investment', 'Quick stimulus'], 'disadvantages': ['Crowding out private investment', 'Debt accumulation', 'Political interference'], 'effectiveness': 'High during recessions, moderate during expansions'}, 'taxation': {'multiplier_effect': self._calculate_tax_multiplier(policy_data), 'advantages': ['Broad-based impact', 'Revenue generation', 'Incentive alignment'], 'disadvantages': ['Lagged response', 'Political constraints', 'Distortionary effects'], 'effectiveness': 'Moderate, depends on tax type and economic conditions'}, 'transfer_payments': {'multiplier_effect': self._calculate_transfer_multiplier(policy_data), 'advantages': ['Targeted support', 'Automatic stabilizers', 'Social safety net'], 'disadvantages': ['Potential dependency', 'Fiscal burden', 'Limited growth impact'], 'effectiveness': 'High for consumption support, moderate for growth'}}
    return {'tools_analysis': tools_analysis, 'implementation_challenges': self._assess_implementation_challenges(), 'policy_recommendation': self._recommend_fiscal_mix(policy_data)}

