# Cluster 30

class ConvexityMeasures:
    """Convexity calculations for fixed income securities"""

    @staticmethod
    @cache_calculation
    def effective_convexity(bond: Bond, base_curve: SpotCurve, yield_shift: Decimal=Decimal('0.0001')) -> Decimal:
        """Calculate Effective convexity using curve shifts"""
        ValidationUtils.validate_positive(yield_shift, 'Yield shift')
        up_curve = base_curve.shift_curve(yield_shift, 'parallel')
        down_curve = base_curve.shift_curve(-yield_shift, 'parallel')
        base_price = BondValuation.present_value_with_curve(bond, base_curve)
        up_price = BondValuation.present_value_with_curve(bond, up_curve)
        down_price = BondValuation.present_value_with_curve(bond, down_curve)
        if base_price == 0:
            return Decimal('0')
        numerator = up_price + down_price - Decimal('2') * base_price
        denominator = base_price * yield_shift ** 2
        return numerator / denominator

    @staticmethod
    def convexity_adjustment(duration: Decimal, convexity: Decimal, yield_change: Decimal) -> Decimal:
        """Calculate convexity adjustment to duration-based price change"""
        return Decimal('0.5') * convexity * yield_change ** 2

    @staticmethod
    def approximate_price_change(duration: Decimal, convexity: Decimal, yield_change: Decimal) -> Decimal:
        """Approximate percentage price change using duration and convexity"""
        duration_effect = -duration * yield_change
        convexity_effect = ConvexityMeasures.convexity_adjustment(duration, convexity, yield_change)
        return duration_effect + convexity_effect

@staticmethod
def approximate_price_change(duration: Decimal, convexity: Decimal, yield_change: Decimal) -> Decimal:
    """Approximate percentage price change using duration and convexity"""
    duration_effect = -duration * yield_change
    convexity_effect = ConvexityMeasures.convexity_adjustment(duration, convexity, yield_change)
    return duration_effect + convexity_effect

