# Cluster 112

class FCFFModel(BaseValuationModel):
    """Free Cash Flow to Firm Model"""

    def __init__(self):
        super().__init__('FCFF Model', 'Free Cash Flow to Firm valuation')
        self.valuation_method = ValuationMethod.DCF_FCFF

    def validate_inputs(self, wacc: float, fcff_projections: List[float], terminal_growth: float=None) -> bool:
        """Validate FCFF model inputs"""
        ModelValidator.validate_percentage(wacc, 'WACC')
        if not fcff_projections or len(fcff_projections) == 0:
            raise ValidationError('FCFF projections cannot be empty')
        if terminal_growth is not None:
            ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
            ModelValidator.validate_growth_vs_required_return(terminal_growth, wacc)
        return True

    def calculate_fcff_from_components(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF from financial statement components"""
        return CalculationEngine.free_cash_flow_to_firm(ebit, tax_rate, depreciation, capex, working_capital_change)

    def calculate_fcff_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF starting from EBITDA"""
        ebit = ebitda - depreciation
        return self.calculate_fcff_from_components(ebit, tax_rate, depreciation, capex, working_capital_change)

    def calculate_fcff_from_net_income(self, net_income: float, interest_expense: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF starting from net income"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        unlevered_net_income = net_income + after_tax_interest
        return unlevered_net_income + depreciation - capex - working_capital_change

    def calculate_fcff_from_cfo(self, cfo: float, interest_expense: float, tax_rate: float, capex: float) -> float:
        """Calculate FCFF from Cash Flow from Operations"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        return cfo + after_tax_interest - capex

    def calculate_terminal_value(self, final_fcff: float, terminal_growth: float, wacc: float) -> float:
        """Calculate terminal value using Gordon Growth"""
        if terminal_growth >= wacc:
            raise ValidationError('Terminal growth rate must be less than WACC')
        terminal_fcff = final_fcff * (1 + terminal_growth)
        return terminal_fcff / (wacc - terminal_growth)

    def calculate_enterprise_value(self, fcff_projections: List[float], wacc: float, terminal_growth: float=None, terminal_value: float=None) -> Dict[str, float]:
        """Calculate enterprise value from FCFF projections"""
        pv_fcff = 0
        pv_details = []
        for year, fcff in enumerate(fcff_projections, 1):
            pv = CalculationEngine.present_value(fcff, wacc, year)
            pv_fcff += pv
            pv_details.append({'year': year, 'fcff': fcff, 'pv': pv})
        if terminal_value is None:
            if terminal_growth is None:
                raise ValidationError('Either terminal_growth or terminal_value must be provided')
            terminal_value = self.calculate_terminal_value(fcff_projections[-1], terminal_growth, wacc)
        pv_terminal = CalculationEngine.present_value(terminal_value, wacc, len(fcff_projections))
        enterprise_value = pv_fcff + pv_terminal
        return {'pv_fcff': pv_fcff, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'enterprise_value': enterprise_value, 'pv_details': pv_details}

    def calculate_equity_value(self, enterprise_value: float, cash: float, total_debt: float, preferred_stock: float=0) -> float:
        """Calculate equity value from enterprise value"""
        return enterprise_value + cash - total_debt - preferred_stock

    def calculate(self, fcff_projections: List[float], wacc: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, cash: float=0, total_debt: float=0, preferred_stock: float=0, current_price: float=None) -> ValuationResult:
        """Calculate valuation using FCFF model"""
        self.validate_inputs(wacc, fcff_projections, terminal_growth)
        ev_components = self.calculate_enterprise_value(fcff_projections, wacc, terminal_growth, terminal_value)
        equity_value = self.calculate_equity_value(ev_components['enterprise_value'], cash, total_debt, preferred_stock)
        intrinsic_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'wacc': wacc, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcff_projections), 'terminal_value_multiple': ev_components['pv_terminal'] / ev_components['enterprise_value'] * 100, 'cash': cash, 'total_debt': total_debt, 'preferred_stock': preferred_stock, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFF DCF Model'}
        calculation_details = {'fcff_projections': fcff_projections, 'pv_fcff': ev_components['pv_fcff'], 'terminal_value': ev_components['terminal_value'], 'pv_terminal': ev_components['pv_terminal'], 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ev_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate_fcff_from_components(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
    """Calculate FCFF from financial statement components"""
    return CalculationEngine.free_cash_flow_to_firm(ebit, tax_rate, depreciation, capex, working_capital_change)

