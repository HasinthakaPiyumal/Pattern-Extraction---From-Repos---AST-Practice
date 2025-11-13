# Cluster 31

class DateUtils:
    """Date utility functions for fixed income calculations"""

    @staticmethod
    def add_business_days(start_date: date, business_days: int, convention: BusinessDayConvention=BusinessDayConvention.FOLLOWING) -> date:
        """Add business days to a date"""
        current_date = start_date
        days_added = 0
        while days_added < business_days:
            current_date += timedelta(days=1)
            if DateUtils.is_business_day(current_date):
                days_added += 1
        return DateUtils.adjust_for_business_day(current_date, convention)

    @staticmethod
    def is_business_day(check_date: date) -> bool:
        """Check if date is a business day (Monday-Friday, no holidays)"""
        return check_date.weekday() < 5

    @staticmethod
    def adjust_for_business_day(check_date: date, convention: BusinessDayConvention) -> date:
        """Adjust date according to business day convention"""
        if DateUtils.is_business_day(check_date):
            return check_date
        if convention == BusinessDayConvention.FOLLOWING:
            while not DateUtils.is_business_day(check_date):
                check_date += timedelta(days=1)
        elif convention == BusinessDayConvention.PRECEDING:
            while not DateUtils.is_business_day(check_date):
                check_date -= timedelta(days=1)
        elif convention == BusinessDayConvention.MODIFIED_FOLLOWING:
            original_month = check_date.month
            while not DateUtils.is_business_day(check_date):
                check_date += timedelta(days=1)
            if check_date.month != original_month:
                check_date = DateUtils.adjust_for_business_day(check_date.replace(day=1) - timedelta(days=1), BusinessDayConvention.PRECEDING)
        elif convention == BusinessDayConvention.MODIFIED_PRECEDING:
            original_month = check_date.month
            while not DateUtils.is_business_day(check_date):
                check_date -= timedelta(days=1)
            if check_date.month != original_month:
                check_date = DateUtils.adjust_for_business_day(check_date.replace(day=1), BusinessDayConvention.FOLLOWING)
        return check_date

    @staticmethod
    def calculate_day_count_fraction(start_date: date, end_date: date, convention: DayCountConvention) -> Decimal:
        """Calculate day count fraction between two dates"""
        if start_date >= end_date:
            return Decimal('0')
        if convention == DayCountConvention.ACTUAL_360:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('360')
        elif convention == DayCountConvention.ACTUAL_365:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('365')
        elif convention == DayCountConvention.ACTUAL_365_FIXED:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('365')
        elif convention == DayCountConvention.ACTUAL_ACTUAL:
            days = (end_date - start_date).days
            year_start = date(start_date.year, 1, 1)
            year_end = date(start_date.year + 1, 1, 1)
            days_in_year = (year_end - year_start).days
            return Decimal(days) / Decimal(days_in_year)
        elif convention == DayCountConvention.THIRTY_360:
            return DateUtils._thirty_360_fraction(start_date, end_date)
        elif convention == DayCountConvention.THIRTY_360_EUROPEAN:
            return DateUtils._thirty_360_european_fraction(start_date, end_date)
        else:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('365')

    @staticmethod
    def _thirty_360_fraction(start_date: date, end_date: date) -> Decimal:
        """Calculate 30/360 day count fraction (US/NASD convention)"""
        d1 = start_date.day
        d2 = end_date.day
        m1 = start_date.month
        m2 = end_date.month
        y1 = start_date.year
        y2 = end_date.year
        if d1 == 31:
            d1 = 30
        if d1 == 30 and d2 == 31:
            d2 = 30
        days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
        return Decimal(days) / Decimal('360')

    @staticmethod
    def _thirty_360_european_fraction(start_date: date, end_date: date) -> Decimal:
        """Calculate 30E/360 day count fraction (European convention)"""
        d1 = min(start_date.day, 30)
        d2 = min(end_date.day, 30)
        m1 = start_date.month
        m2 = end_date.month
        y1 = start_date.year
        y2 = end_date.year
        days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
        return Decimal(days) / Decimal('360')

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Check if year is a leap year"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    @staticmethod
    def days_in_year(year: int) -> int:
        """Get number of days in a year"""
        return 366 if DateUtils.is_leap_year(year) else 365

    @staticmethod
    def end_of_month(input_date: date) -> date:
        """Get last day of month for given date"""
        if input_date.month == 12:
            next_month = date(input_date.year + 1, 1, 1)
        else:
            next_month = date(input_date.year, input_date.month + 1, 1)
        return next_month - timedelta(days=1)

    @staticmethod
    def generate_schedule(start_date: date, end_date: date, frequency: CompoundingFrequency, convention: BusinessDayConvention=BusinessDayConvention.MODIFIED_FOLLOWING) -> List[date]:
        """Generate payment schedule between two dates"""
        if frequency == CompoundingFrequency.CONTINUOUS:
            return [end_date]
        schedule = []
        freq_value = frequency.value
        months_between = 12 // freq_value
        current_date = end_date
        while current_date > start_date:
            schedule.append(DateUtils.adjust_for_business_day(current_date, convention))
            if current_date.month <= months_between:
                new_month = 12 + current_date.month - months_between
                new_year = current_date.year - 1
            else:
                new_month = current_date.month - months_between
                new_year = current_date.year
            try:
                current_date = current_date.replace(year=new_year, month=new_month)
            except ValueError:
                current_date = DateUtils.end_of_month(date(new_year, new_month, 1))
        schedule.reverse()
        return schedule

@staticmethod
def days_in_year(year: int) -> int:
    """Get number of days in a year"""
    return 366 if DateUtils.is_leap_year(year) else 365

