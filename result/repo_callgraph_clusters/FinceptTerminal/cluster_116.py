# Cluster 116

class ResidualIncomeModel(BaseValuationModel):
    """Single-stage and Multi-stage Residual Income Model"""

    def __init__(self):
        super().__init__('Residual Income Model', 'Residual income valuation')
        self.valuation_method = ValuationMethod.RESIDUAL_INCOME

    def calculate_residual_income(self, net_income: float, beginning_book_value: float, required_return: float) -> float:
        """Calculate residual income for a single period"""
        return CalculationEngine.residual_income(net_income, beginning_book_value, required_return)

    def calculate_continuing_residual_income(self, final_ri: float, required_return: float, growth_rate: float) -> float:
        """Calculate continuing residual income value"""
        if growth_rate >= required_return:
            raise ValidationError('Growth rate must be less than required return for continuing RI')
        next_ri = final_ri * (1 + growth_rate)
        return next_ri / (required_return - growth_rate)

    def calculate_single_stage_ri_value(self, current_book_value: float, roe: float, required_return: float, growth_rate: float=0) -> float:
        """Calculate single-stage constant growth RI value"""
        if growth_rate >= required_return:
            raise ValidationError('Growth rate must be less than required return')
        next_net_income = current_book_value * roe * (1 + growth_rate)
        next_book_value = current_book_value * (1 + growth_rate)
        next_ri = self.calculate_residual_income(next_net_income, current_book_value, required_return)
        if growth_rate == 0:
            pv_future_ris = next_ri / required_return
        else:
            pv_future_ris = next_ri / (required_return - growth_rate)
        return current_book_value + pv_future_ris

    def calculate_multistage_ri_value(self, current_book_value: float, projected_ris: List[float], required_return: float, terminal_ri: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate multi-stage RI value"""
        pv_projected_ris = 0
        pv_details = []
        for year, ri in enumerate(projected_ris, 1):
            pv_ri = CalculationEngine.present_value(ri, required_return, year)
            pv_projected_ris += pv_ri
            pv_details.append({'year': year, 'ri': ri, 'pv_ri': pv_ri})
        if terminal_ri is not None:
            if terminal_growth is None:
                terminal_growth = 0
            continuing_ri_value = self.calculate_continuing_residual_income(terminal_ri, required_return, terminal_growth)
            pv_terminal = CalculationEngine.present_value(continuing_ri_value, required_return, len(projected_ris))
        else:
            pv_terminal = 0
        total_value = current_book_value + pv_projected_ris + pv_terminal
        return {'current_book_value': current_book_value, 'pv_projected_ris': pv_projected_ris, 'pv_terminal': pv_terminal, 'total_value': total_value, 'pv_details': pv_details}

    def calculate_intrinsic_value(self, company_data: CompanyData, market_data: MarketData) -> float:
        """Calculate intrinsic value using RI model"""
        financial_data = company_data.financial_data
        book_value_total = financial_data.get('book_value', 0) * company_data.shares_outstanding
        roe = financial_data.get('roe', 0)
        required_return = market_data.required_return
        growth_rate = market_data.growth_rate
        total_value = self.calculate_single_stage_ri_value(book_value_total, roe, required_return, growth_rate)
        return total_value / company_data.shares_outstanding if company_data.shares_outstanding > 0 else 0

    def calculate(self, current_book_value: float, projected_ris: List[float], required_return: float, shares_outstanding: float, terminal_ri: float=None, terminal_growth: float=None, current_price: float=None) -> ValuationResult:
        """Calculate valuation using Residual Income model"""
        ModelValidator.validate_positive_number(current_book_value, 'Current book value')
        ModelValidator.validate_percentage(required_return, 'Required return')
        if terminal_growth is not None:
            ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
        ri_components = self.calculate_multistage_ri_value(current_book_value, projected_ris, required_return, terminal_ri, terminal_growth)
        intrinsic_value = ri_components['total_value'] / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'current_book_value': current_book_value, 'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_periods': len(projected_ris), 'book_value_percentage': current_book_value / ri_components['total_value'] * 100, 'terminal_value_percentage': ri_components['pv_terminal'] / ri_components['total_value'] * 100, 'model_type': 'Multi-stage Residual Income Model'}
        calculation_details = {'projected_ris': projected_ris, 'pv_projected_ris': ri_components['pv_projected_ris'], 'pv_terminal': ri_components['pv_terminal'], 'total_value': ri_components['total_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ri_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate_residual_income(self, net_income: float, beginning_book_value: float, required_return: float) -> float:
    """Calculate residual income for a single period"""
    return CalculationEngine.residual_income(net_income, beginning_book_value, required_return)

