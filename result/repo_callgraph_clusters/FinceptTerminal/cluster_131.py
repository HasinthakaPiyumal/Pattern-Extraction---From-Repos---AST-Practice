# Cluster 131

class BusinessDayCalculator:
    """Business day calculations with holiday support"""

    def __init__(self, country: str='US'):
        self.country = country
        self.holidays = self._load_holidays()

    def _load_holidays(self) -> List[Holiday]:
        """Load holidays for specified country"""
        current_year = datetime.now().year
        holidays = []
        for year in range(current_year - 1, current_year + 5):
            holidays.append(Holiday("New Year's Day", datetime(year, 1, 1)))
            holidays.append(Holiday('Independence Day', datetime(year, 7, 4)))
            holidays.append(Holiday('Christmas Day', datetime(year, 12, 25)))
            jan_1 = datetime(year, 1, 1)
            days_to_monday = (7 - jan_1.weekday()) % 7
            first_monday = jan_1 + timedelta(days=days_to_monday)
            mlk_day = first_monday + timedelta(days=14)
            holidays.append(Holiday('MLK Day', mlk_day))
            feb_1 = datetime(year, 2, 1)
            days_to_monday = (7 - feb_1.weekday()) % 7
            first_monday = feb_1 + timedelta(days=days_to_monday)
            presidents_day = first_monday + timedelta(days=14)
            holidays.append(Holiday('Presidents Day', presidents_day))
            sep_1 = datetime(year, 9, 1)
            days_to_monday = (7 - sep_1.weekday()) % 7
            labor_day = sep_1 + timedelta(days=days_to_monday)
            holidays.append(Holiday('Labor Day', labor_day))
            nov_1 = datetime(year, 11, 1)
            days_to_thursday = (3 - nov_1.weekday()) % 7
            first_thursday = nov_1 + timedelta(days=days_to_thursday)
            thanksgiving = first_thursday + timedelta(days=21)
            holidays.append(Holiday('Thanksgiving', thanksgiving))
        return holidays

    def is_business_day(self, date_input: Union[datetime, date]) -> bool:
        """Check if date is a business day"""
        if isinstance(date_input, date):
            date_input = datetime.combine(date_input, datetime.min.time())
        if date_input.weekday() >= 5:
            return False
        for holiday in self.holidays:
            if date_input.date() == holiday.date.date() and holiday.country == self.country:
                return False
        return True

    def add_business_days(self, start_date: Union[datetime, date], days: int) -> datetime:
        """Add business days to a date"""
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        current_date = start_date
        days_added = 0
        while days_added < days:
            current_date += timedelta(days=1)
            if self.is_business_day(current_date):
                days_added += 1
        return current_date

    def business_days_between(self, start_date: Union[datetime, date], end_date: Union[datetime, date]) -> int:
        """Count business days between two dates"""
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date):
            end_date = datetime.combine(end_date, datetime.min.time())
        if start_date >= end_date:
            return 0
        business_days = 0
        current_date = start_date
        while current_date < end_date:
            current_date += timedelta(days=1)
            if self.is_business_day(current_date):
                business_days += 1
        return business_days

def __init__(self, country: str='US'):
    self.country = country
    self.holidays = self._load_holidays()

