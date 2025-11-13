# Cluster 115

class FCFEModel(BaseValuationModel):
    """Free Cash Flow to Equity Model"""

    def __init__(self):
        super().__init__('FCFE Model', 'Free Cash Flow to Equity valuation')
        self.valuation_method = ValuationMethod.DCF_FCFE

    def validate_inputs(self, required_return: float, fcfe_projections: List[float], terminal_growth: float=None) -> bool:
        """Validate FCFE model inputs"""
        ModelValidator.validate_percentage(required_return, 'Required return on equity')
        if not fcfe_projections or len(fcfe_projections) == 0:
            raise ValidationError('FCFE projections cannot be empty')
        if terminal_growth is not None:
            ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
            ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
        return True

    def calculate_fcfe_from_components(self, net_income: float, depreciation: float, capex: float, working_capital_change: float, net_borrowing: float) -> float:
        """Calculate FCFE from financial statement components"""
        return CalculationEngine.free_cash_flow_to_equity(net_income, depreciation, capex, working_capital_change, net_borrowing)

    def calculate_fcfe_from_fcff(self, fcff: float, interest_expense: float, tax_rate: float, net_borrowing: float) -> float:
        """Calculate FCFE from FCFF"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        return fcff - after_tax_interest + net_borrowing

    def calculate_fcfe_from_ebit(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
        """Calculate FCFE starting from EBIT"""
        ebt = ebit - interest_expense
        net_income = ebt * (1 - tax_rate)
        return self.calculate_fcfe_from_components(net_income, depreciation, capex, working_capital_change, net_borrowing)

    def calculate_fcfe_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
        """Calculate FCFE starting from EBITDA"""
        ebit = ebitda - depreciation
        return self.calculate_fcfe_from_ebit(ebit, tax_rate, depreciation, capex, working_capital_change, interest_expense, net_borrowing)

    def calculate_fcfe_from_cfo(self, cfo: float, capex: float, net_borrowing: float) -> float:
        """Calculate FCFE from Cash Flow from Operations"""
        return cfo - capex + net_borrowing

    def calculate_terminal_value(self, final_fcfe: float, terminal_growth: float, required_return: float) -> float:
        """Calculate terminal value using Gordon Growth"""
        if terminal_growth >= required_return:
            raise ValidationError('Terminal growth rate must be less than required return')
        terminal_fcfe = final_fcfe * (1 + terminal_growth)
        return terminal_fcfe / (required_return - terminal_growth)

    def calculate_equity_value(self, fcfe_projections: List[float], required_return: float, terminal_growth: float=None, terminal_value: float=None) -> Dict[str, float]:
        """Calculate equity value from FCFE projections"""
        pv_fcfe = 0
        pv_details = []
        for year, fcfe in enumerate(fcfe_projections, 1):
            pv = CalculationEngine.present_value(fcfe, required_return, year)
            pv_fcfe += pv
            pv_details.append({'year': year, 'fcfe': fcfe, 'pv': pv})
        if terminal_value is None:
            if terminal_growth is None:
                raise ValidationError('Either terminal_growth or terminal_value must be provided')
            terminal_value = self.calculate_terminal_value(fcfe_projections[-1], terminal_growth, required_return)
        pv_terminal = CalculationEngine.present_value(terminal_value, required_return, len(fcfe_projections))
        equity_value = pv_fcfe + pv_terminal
        return {'pv_fcfe': pv_fcfe, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'equity_value': equity_value, 'pv_details': pv_details}

    def calculate(self, fcfe_projections: List[float], required_return: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, current_price: float=None) -> ValuationResult:
        """Calculate valuation using FCFE model"""
        self.validate_inputs(required_return, fcfe_projections, terminal_growth)
        equity_components = self.calculate_equity_value(fcfe_projections, required_return, terminal_growth, terminal_value)
        intrinsic_value = equity_components['equity_value'] / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcfe_projections), 'terminal_value_multiple': equity_components['pv_terminal'] / equity_components['equity_value'] * 100, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFE DCF Model'}
        calculation_details = {'fcfe_projections': fcfe_projections, 'pv_fcfe': equity_components['pv_fcfe'], 'terminal_value': equity_components['terminal_value'], 'pv_terminal': equity_components['pv_terminal'], 'equity_value': equity_components['equity_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': equity_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate_fcfe_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
    """Calculate FCFE starting from EBITDA"""
    ebit = ebitda - depreciation
    return self.calculate_fcfe_from_ebit(ebit, tax_rate, depreciation, capex, working_capital_change, interest_expense, net_borrowing)

