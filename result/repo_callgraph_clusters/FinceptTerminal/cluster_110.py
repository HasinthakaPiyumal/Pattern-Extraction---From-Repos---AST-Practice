# Cluster 110

class PriceMultiplesModel(BaseValuationModel):
    """Price-based multiple valuation model"""

    def __init__(self):
        super().__init__('Price Multiples', 'Price-based multiple valuation')
        self.valuation_method = ValuationMethod.MULTIPLES_PE

    def calculate_pe_ratio(self, price: float, eps: float) -> float:
        """Calculate Price-to-Earnings ratio"""
        if eps <= 0:
            raise ValidationError('Earnings per share must be positive for P/E calculation')
        return price / eps

    def calculate_pb_ratio(self, price: float, book_value_per_share: float) -> float:
        """Calculate Price-to-Book ratio"""
        if book_value_per_share <= 0:
            raise ValidationError('Book value per share must be positive for P/B calculation')
        return price / book_value_per_share

    def calculate_ps_ratio(self, price: float, sales_per_share: float) -> float:
        """Calculate Price-to-Sales ratio"""
        if sales_per_share <= 0:
            raise ValidationError('Sales per share must be positive for P/S calculation')
        return price / sales_per_share

    def calculate_peg_ratio(self, pe_ratio: float, growth_rate: float) -> float:
        """Calculate PEG ratio"""
        if growth_rate <= 0:
            raise ValidationError('Growth rate must be positive for PEG calculation')
        return pe_ratio / (growth_rate * 100)

    def calculate_dividend_yield(self, dividend_per_share: float, price: float) -> float:
        """Calculate dividend yield"""
        if price <= 0:
            raise ValidationError('Price must be positive for dividend yield calculation')
        return dividend_per_share / price

    def calculate_earnings_yield(self, eps: float, price: float) -> float:
        """Calculate earnings yield (E/P ratio)"""
        if price <= 0:
            raise ValidationError('Price must be positive for earnings yield calculation')
        return eps / price

    def normalize_earnings(self, earnings_history: List[float], method: str='average') -> float:
        """Normalize earnings using various methods"""
        if not earnings_history:
            raise ValidationError('Earnings history cannot be empty')
        positive_earnings = [e for e in earnings_history if e > 0]
        if method == 'average':
            return statistics.mean(earnings_history)
        elif method == 'median':
            return statistics.median(earnings_history)
        elif method == 'average_positive':
            return statistics.mean(positive_earnings) if positive_earnings else 0
        elif method == 'peak_earnings':
            return max(earnings_history)
        elif method == 'trough_earnings':
            return min(positive_earnings) if positive_earnings else 0
        else:
            raise ValidationError(f'Unknown normalization method: {method}')

    def calculate_justified_pe_from_fundamentals(self, payout_ratio: float, required_return: float, growth_rate: float, is_leading: bool=True) -> float:
        """Calculate justified P/E ratio from fundamentals"""
        justified_pe = CalculationEngine.pe_ratio_from_fundamentals(payout_ratio, required_return, growth_rate)
        if not is_leading:
            justified_pe = justified_pe / (1 + growth_rate)
        return justified_pe

    def calculate_justified_pb_from_fundamentals(self, roe: float, required_return: float, growth_rate: float) -> float:
        """Calculate justified P/B ratio from fundamentals"""
        if required_return <= growth_rate:
            raise ValidationError('Required return must be greater than growth rate')
        return (roe - growth_rate) / (required_return - growth_rate)

    def calculate_justified_ps_from_fundamentals(self, profit_margin: float, payout_ratio: float, required_return: float, growth_rate: float) -> float:
        """Calculate justified P/S ratio from fundamentals"""
        justified_pe = self.calculate_justified_pe_from_fundamentals(payout_ratio, required_return, growth_rate)
        return justified_pe * profit_margin

    def value_using_pe_multiple(self, comparable_pe: float, target_eps: float) -> float:
        """Value company using P/E multiple"""
        return comparable_pe * target_eps

    def value_using_pb_multiple(self, comparable_pb: float, target_bvps: float) -> float:
        """Value company using P/B multiple"""
        return comparable_pb * target_bvps

    def value_using_ps_multiple(self, comparable_ps: float, target_sps: float) -> float:
        """Value company using P/S multiple"""
        return comparable_ps * target_sps

def calculate_justified_ps_from_fundamentals(self, profit_margin: float, payout_ratio: float, required_return: float, growth_rate: float) -> float:
    """Calculate justified P/S ratio from fundamentals"""
    justified_pe = self.calculate_justified_pe_from_fundamentals(payout_ratio, required_return, growth_rate)
    return justified_pe * profit_margin

