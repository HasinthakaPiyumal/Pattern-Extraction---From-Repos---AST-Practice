# Cluster 32

class BondInstrument:
    """Base bond instrument class with core functionality"""

    def __init__(self, bond: Bond):
        self.bond = bond
        self._cash_flows = None

    def generate_cash_flows(self, settlement_date: Optional[date]=None) -> List[CashFlow]:
        """Generate bond cash flows from settlement date to maturity"""
        if settlement_date is None:
            settlement_date = date.today()
        cash_flows = []
        if self.bond.is_zero_coupon:
            cash_flows.append(CashFlow(date=self.bond.maturity_date, amount=self.bond.face_value, type='principal'))
            return cash_flows
        coupon_dates = self._generate_coupon_dates(settlement_date)
        coupon_amount = self._calculate_coupon_amount()
        for coupon_date in coupon_dates:
            if coupon_date > settlement_date:
                cash_flows.append(CashFlow(date=coupon_date, amount=coupon_amount, type='coupon'))
        if cash_flows:
            cash_flows[-1].amount += self.bond.face_value
            cash_flows[-1].type = 'coupon_and_principal'
        else:
            cash_flows.append(CashFlow(date=self.bond.maturity_date, amount=self.bond.face_value, type='principal'))
        self._cash_flows = cash_flows
        return cash_flows

    def _generate_coupon_dates(self, start_date: date) -> List[date]:
        """Generate coupon payment dates"""
        dates = []
        frequency = self.bond.coupon_frequency.value
        if frequency == 0:
            frequency = 1
        months_between = 12 // frequency
        current_date = self.bond.maturity_date
        while current_date > self.bond.issue_date:
            dates.append(current_date)
            if current_date.month <= months_between:
                new_month = 12 + current_date.month - months_between
                new_year = current_date.year - 1
            else:
                new_month = current_date.month - months_between
                new_year = current_date.year
            try:
                current_date = current_date.replace(year=new_year, month=new_month)
            except ValueError:
                if new_month == 2 and current_date.day > 28:
                    current_date = current_date.replace(year=new_year, month=new_month, day=28)
                else:
                    current_date = current_date.replace(year=new_year, month=new_month, day=1)
                    current_date = current_date.replace(day=min(current_date.day, self._days_in_month(new_year, new_month)))
        dates.reverse()
        return dates

    def _days_in_month(self, year: int, month: int) -> int:
        """Get number of days in a month"""
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        this_month = date(year, month, 1)
        return (next_month - this_month).days

    def _calculate_coupon_amount(self) -> Decimal:
        """Calculate coupon payment amount"""
        annual_coupon = self.bond.face_value * self.bond.coupon_rate
        frequency = self.bond.coupon_frequency.value
        if frequency == 0:
            return annual_coupon
        return annual_coupon / Decimal(frequency)

    def accrued_interest(self, settlement_date: date) -> Decimal:
        """Calculate accrued interest from last coupon date"""
        if self.bond.is_zero_coupon:
            return Decimal('0')
        coupon_dates = self._generate_coupon_dates(self.bond.issue_date)
        last_coupon_date = self.bond.issue_date
        for coupon_date in coupon_dates:
            if coupon_date <= settlement_date:
                last_coupon_date = coupon_date
            else:
                break
        days_accrued = self._calculate_days(last_coupon_date, settlement_date)
        days_in_period = self._calculate_days_in_coupon_period(last_coupon_date)
        coupon_amount = self._calculate_coupon_amount()
        return coupon_amount * (Decimal(days_accrued) / Decimal(days_in_period))

    def _calculate_days(self, start_date: date, end_date: date) -> int:
        """Calculate days between dates based on day count convention"""
        if self.bond.day_count_convention == DayCountConvention.ACTUAL_360:
            return (end_date - start_date).days
        elif self.bond.day_count_convention == DayCountConvention.ACTUAL_365:
            return (end_date - start_date).days
        elif self.bond.day_count_convention == DayCountConvention.ACTUAL_ACTUAL:
            return (end_date - start_date).days
        elif self.bond.day_count_convention == DayCountConvention.THIRTY_360:
            return self._thirty_360_days(start_date, end_date)
        else:
            return (end_date - start_date).days

    def _thirty_360_days(self, start_date: date, end_date: date) -> int:
        """Calculate days using 30/360 convention"""
        d1 = min(start_date.day, 30)
        d2 = min(end_date.day, 30) if d1 == 30 else end_date.day
        return 360 * (end_date.year - start_date.year) + 30 * (end_date.month - start_date.month) + (d2 - d1)

    def _calculate_days_in_coupon_period(self, coupon_date: date) -> int:
        """Calculate days in coupon period"""
        frequency = self.bond.coupon_frequency.value
        if frequency == 0:
            frequency = 1
        if self.bond.day_count_convention == DayCountConvention.THIRTY_360:
            return 360 // frequency
        else:
            return 365 // frequency

    def time_to_maturity(self, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate time to maturity in years"""
        if settlement_date is None:
            settlement_date = date.today()
        days = (self.bond.maturity_date - settlement_date).days
        if self.bond.day_count_convention == DayCountConvention.ACTUAL_365:
            return Decimal(days) / Decimal('365')
        elif self.bond.day_count_convention == DayCountConvention.ACTUAL_360:
            return Decimal(days) / Decimal('360')
        else:
            return Decimal(days) / Decimal('365.25')

def _calculate_days(self, start_date: date, end_date: date) -> int:
    """Calculate days between dates based on day count convention"""
    if self.bond.day_count_convention == DayCountConvention.ACTUAL_360:
        return (end_date - start_date).days
    elif self.bond.day_count_convention == DayCountConvention.ACTUAL_365:
        return (end_date - start_date).days
    elif self.bond.day_count_convention == DayCountConvention.ACTUAL_ACTUAL:
        return (end_date - start_date).days
    elif self.bond.day_count_convention == DayCountConvention.THIRTY_360:
        return self._thirty_360_days(start_date, end_date)
    else:
        return (end_date - start_date).days

