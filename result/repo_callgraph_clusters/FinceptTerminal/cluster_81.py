# Cluster 81

class CapitalFlowAnalyzer(EconomicsBase):
    """Capital flows analysis and balance of payments impact"""

    def analyze_capital_flow_types(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze different types of capital flows and their characteristics"""
        return {'foreign_direct_investment': {'definition': 'Long-term investment for control or significant influence (>10% ownership)', 'characteristics': ['Long-term commitment and stability', 'Technology and knowledge transfer', 'Management expertise and best practices', 'Difficult to reverse quickly'], 'economic_impact': {'positive': 'Productivity gains, employment creation, export growth', 'negative': 'Potential crowding out of domestic investment', 'volatility': 'Low - stable funding source'}, 'current_flows': self._analyze_fdi_flows(flow_data), 'policy_implications': 'Generally welcomed, policies focus on attraction and retention'}, 'portfolio_investment': {'definition': 'Investment in securities without control (<10% ownership)', 'characteristics': ['Liquid and easily reversible', 'Driven by return differentials and risk appetite', 'Sensitive to market sentiment', 'Includes equity and debt securities'], 'economic_impact': {'positive': 'Capital market development, financing access', 'negative': 'Volatility and sudden stops risk', 'volatility': 'High - subject to rapid reversals'}, 'current_flows': self._analyze_portfolio_flows(flow_data), 'policy_implications': 'Requires robust regulatory framework and macroprudential policies'}, 'other_investment': {'definition': 'Bank lending, trade credits, and other financial flows', 'characteristics': ['Includes bank loans and deposits', 'Trade finance and short-term credits', 'Interbank and intercompany lending', 'Often procyclical'], 'economic_impact': {'positive': 'Trade finance facilitation, liquidity provision', 'negative': 'Banking sector vulnerabilities, sudden stops', 'volatility': 'Medium to High - depends on banking conditions'}, 'current_flows': self._analyze_other_flows(flow_data), 'policy_implications': 'Banking supervision and capital flow management'}, 'official_flows': {'definition': 'Central bank and government transactions', 'characteristics': ['Reserve accumulation/depletion', 'Official development assistance', 'Bilateral government lending', 'IMF and multilateral lending'], 'economic_impact': {'positive': 'Crisis support, development financing', 'negative': 'May create moral hazard', 'volatility': 'Low to Medium - policy driven'}, 'policy_implications': 'Part of macroeconomic management and development strategy'}, 'flow_determinants': self._analyze_flow_determinants(flow_data), 'volatility_comparison': self._compare_flow_volatility(), 'crisis_behavior': self._analyze_crisis_behavior()}

    def analyze_balance_of_payments_impact(self, bop_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how BOP flows affect exchange rates"""
        return {'current_account_impact': {'trade_balance': {'surplus_effect': 'Creates demand for domestic currency', 'deficit_effect': 'Creates supply of domestic currency', 'elasticity_considerations': 'J-curve effect in short run', 'current_balance': self._assess_trade_balance_impact(bop_data)}, 'income_flows': {'investment_income': 'Returns on foreign investments affect currency demand', 'compensation': 'Worker remittances and cross-border wages', 'impact_assessment': self._assess_income_flows_impact(bop_data)}, 'transfers': {'remittances': 'Significant for many developing countries', 'official_transfers': 'Aid and government transfers', 'impact_assessment': self._assess_transfer_impact(bop_data)}}, 'capital_account_impact': {'direct_investment': {'fx_impact': 'Usually strengthens recipient currency', 'timing': 'Gradual impact as investments are made', 'sustainability': 'Most stable form of capital flow'}, 'portfolio_investment': {'fx_impact': 'Can cause rapid currency movements', 'timing': 'Immediate impact on exchange rates', 'volatility': 'High sensitivity to sentiment changes'}, 'financial_derivatives': {'fx_impact': 'Complex, depends on underlying positions', 'hedging_flows': 'May offset other capital flows'}, 'reserve_changes': {'intervention_impact': 'Central bank buying/selling affects rates', 'signaling_effect': 'Indicates policy stance and credibility'}}, 'bop_equilibrium_analysis': self._analyze_bop_equilibrium(bop_data), 'sustainability_assessment': self._assess_bop_sustainability(bop_data), 'policy_responses': self._recommend_bop_policies(bop_data)}

    def assess_capital_restrictions(self, restriction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze government capital restrictions and their objectives"""
        return {'restriction_types': {'inflow_controls': {'objectives': ['Prevent asset bubbles from hot money', 'Maintain monetary policy independence', 'Reduce financial stability risks', 'Prevent real exchange rate appreciation'], 'instruments': ['Unremunerated reserve requirements', 'Taxes on foreign investment', 'Minimum holding periods', 'Limits on foreign ownership'], 'effectiveness': self._assess_inflow_control_effectiveness(restriction_data)}, 'outflow_controls': {'objectives': ['Prevent capital flight during crises', 'Preserve foreign exchange reserves', 'Maintain exchange rate stability', 'Support domestic financing needs'], 'instruments': ['Approval requirements for foreign investment', 'Limits on foreign currency holdings', 'Restrictions on overseas deposits', 'Export surrender requirements'], 'effectiveness': self._assess_outflow_control_effectiveness(restriction_data)}}, 'common_objectives': {'macroeconomic_stability': 'Maintain stable exchange rates and inflation', 'financial_stability': 'Prevent excessive risk-taking and bubbles', 'monetary_independence': 'Preserve domestic monetary policy effectiveness', 'development_goals': 'Channel capital toward productive investments', 'crisis_prevention': 'Reduce vulnerability to sudden stops'}, 'effectiveness_factors': {'comprehensiveness': 'Controls must cover all relevant channels', 'enforceability': 'Administrative capacity and compliance monitoring', 'market_development': 'May hinder financial market development', 'evasion_potential': 'Sophisticated investors can often circumvent controls', 'international_coordination': 'Effectiveness increases with coordination'}, 'costs_and_benefits': self._analyze_restriction_costs_benefits(), 'optimal_design_principles': self._recommend_optimal_design(), 'current_trends': self._analyze_current_restriction_trends()}

    def _analyze_fdi_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FDI flow characteristics"""
        fdi_inflows = self.to_decimal(data.get('fdi_inflows_gdp', 0))
        fdi_outflows = self.to_decimal(data.get('fdi_outflows_gdp', 0))
        return {'inflow_level': f'{fdi_inflows:.1f}% of GDP', 'outflow_level': f'{fdi_outflows:.1f}% of GDP', 'net_position': f'{fdi_inflows - fdi_outflows:.1f}% of GDP', 'assessment': self._assess_fdi_level(fdi_inflows), 'sectoral_distribution': data.get('fdi_sectors', 'Mixed across sectors')}

    def _analyze_portfolio_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio flow characteristics"""
        portfolio_flows = self.to_decimal(data.get('portfolio_flows_gdp', 0))
        volatility = data.get('portfolio_volatility', 'High')
        return {'flow_level': f'{portfolio_flows:.1f}% of GDP', 'volatility_assessment': volatility, 'composition': data.get('portfolio_composition', 'Mixed equity and debt'), 'vulnerability_indicator': self._assess_portfolio_vulnerability(portfolio_flows)}

    def _analyze_other_flows(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze other investment flows"""
        other_flows = self.to_decimal(data.get('other_investment_gdp', 0))
        return {'flow_level': f'{other_flows:.1f}% of GDP', 'banking_component': data.get('banking_flows_share', 'Significant'), 'trade_finance_component': data.get('trade_finance_share', 'Moderate'), 'stability_assessment': self._assess_other_flow_stability(other_flows)}

    def _analyze_flow_determinants(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze determinants of capital flows"""
        return {'push_factors': ['Global risk appetite and liquidity conditions', 'Advanced economy interest rates', 'Global growth and commodity prices', 'Investor risk tolerance'], 'pull_factors': ['Domestic economic fundamentals', 'Interest rate differentials', 'Exchange rate expectations', 'Political and institutional quality', 'Market development and accessibility'], 'structural_factors': ['Trade openness and integration', 'Financial market development', 'Capital account openness', 'Institutional quality and governance']}

    def _compare_flow_volatility(self) -> Dict[str, str]:
        """Compare volatility across flow types"""
        return {'most_volatile': 'Portfolio investment (especially equity)', 'moderately_volatile': 'Other investment (banking flows)', 'least_volatile': 'Foreign direct investment', 'crisis_behavior': 'Portfolio flows show strongest sudden stop tendency'}

    def _analyze_crisis_behavior(self) -> Dict[str, str]:
        """Analyze capital flow behavior during crises"""
        return {'sudden_stops': 'Rapid reversal of portfolio and banking flows', 'flight_to_quality': 'Shift from emerging to developed markets', 'fdi_resilience': 'FDI typically more stable during crises', 'contagion_channels': 'Capital flows can transmit crises across countries'}

    def _assess_trade_balance_impact(self, data: Dict[str, Any]) -> str:
        """Assess trade balance impact on exchange rates"""
        trade_balance = self.to_decimal(data.get('trade_balance_gdp', 0))
        if trade_balance > self.to_decimal(2):
            return 'Large surplus likely supporting currency'
        elif trade_balance < self.to_decimal(-5):
            return 'Large deficit creating downward pressure on currency'
        else:
            return 'Moderate trade balance with limited FX impact'

    def _assess_income_flows_impact(self, data: Dict[str, Any]) -> str:
        """Assess income flows impact"""
        income_balance = self.to_decimal(data.get('income_balance_gdp', 0))
        if income_balance > self.to_decimal(1):
            return 'Positive income flows supporting currency'
        elif income_balance < self.to_decimal(-2):
            return 'Negative income flows pressuring currency'
        else:
            return 'Income flows have moderate impact'

    def _assess_transfer_impact(self, data: Dict[str, Any]) -> str:
        """Assess transfer impact on currency"""
        transfers = self.to_decimal(data.get('transfers_gdp', 0))
        if transfers > self.to_decimal(3):
            return 'Significant remittances providing currency support'
        else:
            return 'Transfers have limited currency impact'

    def _analyze_bop_equilibrium(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze balance of payments equilibrium"""
        current_account = self.to_decimal(data.get('current_account_gdp', 0))
        capital_account = self.to_decimal(data.get('capital_account_gdp', 0))
        return {'current_account_balance': f'{current_account:.1f}% of GDP', 'capital_account_balance': f'{capital_account:.1f}% of GDP', 'overall_balance': f'{current_account + capital_account:.1f}% of GDP', 'equilibrium_assessment': self._assess_bop_equilibrium_status(current_account, capital_account), 'reserve_implications': self._assess_reserve_implications(current_account + capital_account)}

    def _assess_bop_sustainability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess BOP sustainability"""
        current_account = self.to_decimal(data.get('current_account_gdp', 0))
        foreign_debt = self.to_decimal(data.get('foreign_debt_gdp', 0))
        return {'current_account_sustainability': self._assess_ca_sustainability(current_account), 'external_debt_sustainability': self._assess_debt_sustainability(foreign_debt), 'vulnerability_indicators': self._identify_vulnerability_indicators(data), 'early_warning_signals': self._identify_early_warning_signals(data)}

    def _recommend_bop_policies(self, data: Dict[str, Any]) -> List[str]:
        """Recommend BOP adjustment policies"""
        current_account = self.to_decimal(data.get('current_account_gdp', 0))
        if current_account < self.to_decimal(-5):
            return ['Fiscal consolidation to reduce domestic absorption', 'Structural reforms to improve competitiveness', 'Exchange rate adjustment if overvalued', 'Capital flow management measures if needed']
        elif current_account > self.to_decimal(5):
            return ['Fiscal expansion to increase domestic demand', 'Infrastructure investment to utilize surplus', 'Currency appreciation to restore balance', 'Gradual capital account liberalization']
        else:
            return ['Maintain current policy stance', 'Monitor for emerging imbalances', 'Strengthen economic fundamentals']

    def _assess_inflow_control_effectiveness(self, data: Dict[str, Any]) -> str:
        """Assess effectiveness of capital inflow controls"""
        control_intensity = data.get('inflow_control_index', 0.5)
        if control_intensity > 0.7:
            return 'Comprehensive controls - moderately effective but may reduce efficiency'
        elif control_intensity > 0.3:
            return 'Selective controls - limited effectiveness, some circumvention'
        else:
            return 'Minimal controls - market-based allocation but potential volatility'

    def _assess_outflow_control_effectiveness(self, data: Dict[str, Any]) -> str:
        """Assess effectiveness of capital outflow controls"""
        control_intensity = data.get('outflow_control_index', 0.5)
        if control_intensity > 0.7:
            return 'Strict controls - effective short-term but high economic costs'
        elif control_intensity > 0.3:
            return 'Moderate controls - some effectiveness with manageable costs'
        else:
            return 'Light controls - limited effectiveness but preserves market efficiency'

    def _analyze_restriction_costs_benefits(self) -> Dict[str, Dict[str, List[str]]]:
        """Analyze costs and benefits of capital restrictions"""
        return {'benefits': {'macroeconomic': ['Exchange rate stability', 'Monetary policy independence', 'Reduced volatility'], 'financial': ['Reduced systemic risk', 'Prevented asset bubbles', 'Banking stability'], 'developmental': ['Capital allocated to development priorities', 'Reduced inequality']}, 'costs': {'efficiency': ['Reduced capital allocation efficiency', 'Higher cost of capital', 'Innovation constraints'], 'market_development': ['Slower financial market development', 'Reduced competition', 'Limited diversification'], 'administrative': ['High enforcement costs', 'Bureaucratic burden', 'Corruption risks']}}

    def _recommend_optimal_design(self) -> List[str]:
        """Recommend optimal design principles for capital controls"""
        return ['Targeted rather than blanket restrictions', 'Temporary rather than permanent measures', 'Price-based rather than quantity-based controls', 'Comprehensive coverage to prevent evasion', 'Regular review and adjustment of measures', 'Clear communication of objectives and duration']

    def _analyze_current_restriction_trends(self) -> Dict[str, str]:
        """Analyze current trends in capital restrictions"""
        return {'developing_countries': 'Increased use of macroprudential measures', 'developed_countries': 'Generally maintain open capital accounts', 'crisis_response': 'Temporary restrictions during financial stress', 'international_coordination': 'Growing recognition of spillover effects', 'institutional_view': 'IMF more accepting of capital flow management'}

    def _assess_fdi_level(self, fdi_inflows: Decimal) -> str:
        """Assess FDI inflow level"""
        if fdi_inflows > self.to_decimal(5):
            return 'High FDI inflows indicating strong investment climate'
        elif fdi_inflows > self.to_decimal(2):
            return 'Moderate FDI inflows'
        else:
            return 'Low FDI inflows, may indicate investment barriers'

    def _assess_portfolio_vulnerability(self, flows: Decimal) -> str:
        """Assess portfolio flow vulnerability"""
        if abs(flows) > self.to_decimal(5):
            return 'High vulnerability to sudden stops'
        elif abs(flows) > self.to_decimal(2):
            return 'Moderate vulnerability'
        else:
            return 'Low vulnerability to portfolio flow reversals'

    def _assess_other_flow_stability(self, flows: Decimal) -> str:
        """Assess other investment flow stability"""
        if abs(flows) > self.to_decimal(3):
            return 'Volatile other investment flows'
        else:
            return 'Relatively stable other investment flows'

    def _assess_bop_equilibrium_status(self, ca: Decimal, ka: Decimal) -> str:
        """Assess BOP equilibrium status"""
        overall = ca + ka
        if abs(overall) < self.to_decimal(1):
            return 'Balanced position'
        elif overall > self.to_decimal(2):
            return 'Surplus position - reserve accumulation'
        else:
            return 'Deficit position - reserve depletion or borrowing'

    def _assess_reserve_implications(self, balance: Decimal) -> str:
        """Assess reserve implications of BOP position"""
        if balance > self.to_decimal(2):
            return 'Reserve accumulation, potential sterilization needs'
        elif balance < self.to_decimal(-2):
            return 'Reserve depletion, potential sustainability concerns'
        else:
            return 'Stable reserve position'

    def _assess_ca_sustainability(self, ca: Decimal) -> str:
        """Assess current account sustainability"""
        if ca < self.to_decimal(-5):
            return 'Large deficit raises sustainability concerns'
        elif ca < self.to_decimal(-3):
            return 'Moderate deficit requires monitoring'
        else:
            return 'Sustainable current account position'

    def _assess_debt_sustainability(self, debt: Decimal) -> str:
        """Assess external debt sustainability"""
        if debt > self.to_decimal(60):
            return 'High external debt raises sustainability concerns'
        elif debt > self.to_decimal(40):
            return 'Moderate external debt requires monitoring'
        else:
            return 'Manageable external debt level'

    def _identify_vulnerability_indicators(self, data: Dict[str, Any]) -> List[str]:
        """Identify BOP vulnerability indicators"""
        return ['Current account deficit > 5% of GDP', 'Short-term external debt > reserves', 'High dependence on volatile capital flows', 'Real exchange rate overvaluation', 'Rapid credit growth and asset price increases']

    def _identify_early_warning_signals(self, data: Dict[str, Any]) -> List[str]:
        """Identify early warning signals of BOP crisis"""
        return ['Sudden stop in capital inflows', 'Rapid reserve depletion', 'Currency under pressure', 'Rising sovereign risk premiums', 'Bank deposit outflows']

    def calculate(self, analysis_type: str='capital_flows', **kwargs) -> Dict[str, Any]:
        """Main capital flows calculation dispatcher"""
        analyses = {'capital_flows': lambda: self.analyze_capital_flow_types(kwargs.get('flow_data', {})), 'bop_impact': lambda: self.analyze_balance_of_payments_impact(kwargs.get('bop_data', {})), 'capital_restrictions': lambda: self.assess_capital_restrictions(kwargs.get('restriction_data', {}))}
        if analysis_type not in analyses:
            raise ValidationError(f'Unknown analysis type: {analysis_type}')
        result = analyses[analysis_type]()
        result['metadata'] = self.get_metadata()
        return result

def analyze_balance_of_payments_impact(self, bop_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze how BOP flows affect exchange rates"""
    return {'current_account_impact': {'trade_balance': {'surplus_effect': 'Creates demand for domestic currency', 'deficit_effect': 'Creates supply of domestic currency', 'elasticity_considerations': 'J-curve effect in short run', 'current_balance': self._assess_trade_balance_impact(bop_data)}, 'income_flows': {'investment_income': 'Returns on foreign investments affect currency demand', 'compensation': 'Worker remittances and cross-border wages', 'impact_assessment': self._assess_income_flows_impact(bop_data)}, 'transfers': {'remittances': 'Significant for many developing countries', 'official_transfers': 'Aid and government transfers', 'impact_assessment': self._assess_transfer_impact(bop_data)}}, 'capital_account_impact': {'direct_investment': {'fx_impact': 'Usually strengthens recipient currency', 'timing': 'Gradual impact as investments are made', 'sustainability': 'Most stable form of capital flow'}, 'portfolio_investment': {'fx_impact': 'Can cause rapid currency movements', 'timing': 'Immediate impact on exchange rates', 'volatility': 'High sensitivity to sentiment changes'}, 'financial_derivatives': {'fx_impact': 'Complex, depends on underlying positions', 'hedging_flows': 'May offset other capital flows'}, 'reserve_changes': {'intervention_impact': 'Central bank buying/selling affects rates', 'signaling_effect': 'Indicates policy stance and credibility'}}, 'bop_equilibrium_analysis': self._analyze_bop_equilibrium(bop_data), 'sustainability_assessment': self._assess_bop_sustainability(bop_data), 'policy_responses': self._recommend_bop_policies(bop_data)}

