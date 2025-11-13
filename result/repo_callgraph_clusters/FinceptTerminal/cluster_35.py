# Cluster 35

class ForwardCurve:
    """Forward rate curve implementation"""

    def __init__(self, spot_curve: SpotCurve):
        self.spot_curve = spot_curve
        self.curve_date = spot_curve.curve.curve_date
        self.currency = spot_curve.curve.currency

    @cache_calculation
    def get_forward_rate(self, start_time: Decimal, end_time: Decimal) -> Decimal:
        """Calculate forward rate between two time points"""
        return self.spot_curve.forward_rate(start_time, end_time)

    def build_forward_curve(self, start_maturity: Decimal, end_maturities: List[Decimal]) -> YieldCurve:
        """Build forward curve from start maturity to various end maturities"""
        forward_rates = []
        for end_maturity in end_maturities:
            if end_maturity <= start_maturity:
                raise ValueError(f'End maturity {end_maturity} must be greater than start maturity {start_maturity}')
            forward_rate = self.get_forward_rate(start_maturity, end_maturity)
            forward_rates.append(forward_rate)
        return YieldCurve(curve_date=self.curve_date, maturities=end_maturities, rates=forward_rates, currency=self.currency, curve_type='forward')

    def instantaneous_forward_rate(self, maturity: Decimal, delta: Decimal=Decimal('0.001')) -> Decimal:
        """Calculate instantaneous forward rate at given maturity"""
        if maturity <= delta:
            return self.spot_curve.get_rate(delta)
        r1 = self.spot_curve.get_rate(maturity - delta / 2)
        r2 = self.spot_curve.get_rate(maturity + delta / 2)
        return r2 + maturity * (r2 - r1) / delta

@cache_calculation
def get_forward_rate(self, start_time: Decimal, end_time: Decimal) -> Decimal:
    """Calculate forward rate between two time points"""
    return self.spot_curve.forward_rate(start_time, end_time)

