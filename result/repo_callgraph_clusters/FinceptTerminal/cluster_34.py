# Cluster 34

@dataclass
class Bond:
    """Base bond data model"""
    isin: str
    cusip: Optional[str] = None
    ticker: Optional[str] = None
    issue_date: date
    maturity_date: date
    face_value: Decimal = Decimal('100')
    currency: Currency = Currency.USD
    coupon_rate: Decimal = Decimal('0')
    coupon_frequency: CompoundingFrequency = CompoundingFrequency.SEMI_ANNUAL
    day_count_convention: DayCountConvention = DayCountConvention.THIRTY_360
    issuer_name: str = ''
    issuer_rating: Optional[CreditRating] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    current_price: Optional[Decimal] = None
    current_yield: Optional[Decimal] = None
    bond_type: BondType = BondType.FIXED_RATE
    callable: bool = False
    putable: bool = False
    settlement_days: int = 3
    business_day_convention: BusinessDayConvention = BusinessDayConvention.MODIFIED_FOLLOWING

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate bond parameters"""
        if self.maturity_date <= self.issue_date:
            raise ValidationError('Maturity date must be after issue date')
        if self.coupon_rate < VALIDATION_RULES['min_coupon_rate']:
            raise ValidationError('Coupon rate below minimum')
        if self.coupon_rate > VALIDATION_RULES['max_coupon_rate']:
            raise ValidationError('Coupon rate above maximum')
        if self.current_price and (self.current_price < VALIDATION_RULES['min_price'] or self.current_price > VALIDATION_RULES['max_price']):
            raise ValidationError('Bond price outside valid range')

    @property
    def time_to_maturity(self) -> Decimal:
        """Calculate time to maturity in years"""
        today = date.today()
        days_to_maturity = (self.maturity_date - today).days
        return Decimal(days_to_maturity) / Decimal('365.25')

    @property
    def is_zero_coupon(self) -> bool:
        """Check if bond is zero coupon"""
        return self.coupon_rate == 0 or self.bond_type == BondType.ZERO_COUPON

def __post_init__(self):
    self._validate()

