# Cluster 33

class CallableBondInstrument(BondInstrument):
    """Callable bond instrument with embedded call option"""

    def __init__(self, callable_bond: CallableBond):
        super().__init__(callable_bond)
        self.callable_bond = callable_bond

    def is_callable_on_date(self, check_date: date) -> bool:
        """Check if bond is callable on a specific date"""
        for call_feature in self.callable_bond.call_schedule:
            if call_feature.call_date == check_date:
                return True
        return False

    def get_call_price(self, call_date: date) -> Optional[Decimal]:
        """Get call price for a specific date"""
        for call_feature in self.callable_bond.call_schedule:
            if call_feature.call_date == call_date:
                return call_feature.call_price
        return None

    def next_call_date(self, from_date: Optional[date]=None) -> Optional[date]:
        """Get next call date after specified date"""
        if from_date is None:
            from_date = date.today()
        next_call = None
        for call_feature in self.callable_bond.call_schedule:
            if call_feature.call_date > from_date:
                if next_call is None or call_feature.call_date < next_call:
                    next_call = call_feature.call_date
        return next_call

    def effective_maturity(self, yield_to_call: Decimal, yield_to_maturity: Decimal) -> date:
        """Determine effective maturity based on yield comparison"""
        next_call = self.next_call_date()
        if next_call and yield_to_call < yield_to_maturity:
            return next_call
        else:
            return self.bond.maturity_date

def effective_maturity(self, yield_to_call: Decimal, yield_to_maturity: Decimal) -> date:
    """Determine effective maturity based on yield comparison"""
    next_call = self.next_call_date()
    if next_call and yield_to_call < yield_to_maturity:
        return next_call
    else:
        return self.bond.maturity_date

