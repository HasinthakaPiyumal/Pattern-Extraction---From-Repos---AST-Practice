# Cluster 119

class EconomicValueAddedModel(BaseValuationModel):
    """Economic Value Added (EVA) Model"""

    def __init__(self):
        super().__init__('EVA Model', 'Economic Value Added valuation')
        self.valuation_method = ValuationMethod.RESIDUAL_INCOME

    def calculate_eva(self, nopat: float, invested_capital: float, wacc: float) -> float:
        """Calculate Economic Value Added"""
        return CalculationEngine.economic_value_added(nopat, invested_capital, wacc)

    def calculate_nopat(self, ebit: float, tax_rate: float) -> float:
        """Calculate Net Operating Profit After Tax"""
        return ebit * (1 - tax_rate)

    def calculate_invested_capital(self, total_assets: float, non_interest_bearing_liabilities: float) -> float:
        """Calculate invested capital"""
        return total_assets - non_interest_bearing_liabilities

    def calculate_eva_from_components(self, ebit: float, tax_rate: float, total_assets: float, non_interest_bearing_liabilities: float, wacc: float) -> float:
        """Calculate EVA from financial statement components"""
        nopat = self.calculate_nopat(ebit, tax_rate)
        invested_capital = self.calculate_invested_capital(total_assets, non_interest_bearing_liabilities)
        return self.calculate_eva(nopat, invested_capital, wacc)

    def calculate_market_value_added(self, market_value: float, invested_capital: float) -> float:
        """Calculate Market Value Added (MVA)"""
        return market_value - invested_capital

    def eva_valuation(self, current_invested_capital: float, projected_evas: List[float], wacc: float, terminal_eva: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate firm value using EVA approach"""
        pv_evas = 0
        for year, eva in enumerate(projected_evas, 1):
            pv_eva = CalculationEngine.present_value(eva, wacc, year)
            pv_evas += pv_eva
        if terminal_eva is not None:
            if terminal_growth is None:
                terminal_growth = 0
            if terminal_growth >= wacc:
                raise ValidationError('Terminal growth must be less than WACC for EVA terminal value')
            next_eva = terminal_eva * (1 + terminal_growth)
            terminal_value = next_eva / (wacc - terminal_growth)
            pv_terminal = CalculationEngine.present_value(terminal_value, wacc, len(projected_evas))
        else:
            pv_terminal = 0
        firm_value = current_invested_capital + pv_evas + pv_terminal
        return {'current_invested_capital': current_invested_capital, 'pv_projected_evas': pv_evas, 'pv_terminal_evas': pv_terminal, 'total_firm_value': firm_value}

def calculate_eva_from_components(self, ebit: float, tax_rate: float, total_assets: float, non_interest_bearing_liabilities: float, wacc: float) -> float:
    """Calculate EVA from financial statement components"""
    nopat = self.calculate_nopat(ebit, tax_rate)
    invested_capital = self.calculate_invested_capital(total_assets, non_interest_bearing_liabilities)
    return self.calculate_eva(nopat, invested_capital, wacc)

