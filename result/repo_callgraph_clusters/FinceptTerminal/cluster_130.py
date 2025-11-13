# Cluster 130

class ForwardCommitmentPricingEngine(PricingEngine):
    """Unified pricing engine for forward commitments"""

    def __init__(self):
        self.carry_calculator = CarryArbitrageCalculator()

    def price(self, instrument: ForwardCommitment, market_data: MarketData) -> PricingResult:
        """Price forward commitment based on type"""
        if not self.validate_inputs(instrument, market_data):
            raise ValidationError('Invalid inputs for forward commitment pricing')
        if isinstance(instrument, EquityForward):
            return instrument.fair_value(market_data)
        elif isinstance(instrument, InterestRateForward):
            return instrument.fair_value(market_data)
        elif isinstance(instrument, FixedIncomeForward):
            return instrument.fair_value(market_data)
        else:
            raise ValueError(f'Unsupported forward commitment type: {type(instrument)}')

    def validate_inputs(self, instrument: ForwardCommitment, market_data: MarketData) -> bool:
        """Validate inputs for forward commitment pricing"""
        try:
            ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
            ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
            ModelValidator.validate_non_negative(market_data.dividend_yield, 'dividend_yield')
            if instrument.is_expired():
                logger.warning('Forward commitment has expired')
                return False
            return True
        except ValidationError:
            return False

def __init__(self):
    self.carry_calculator = CarryArbitrageCalculator()

