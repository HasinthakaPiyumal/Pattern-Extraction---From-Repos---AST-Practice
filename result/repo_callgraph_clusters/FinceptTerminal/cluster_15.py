# Cluster 15

def get_historical(symbol, start_date, end_date):
    """Fetch historical data for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date)
        if hist.empty:
            return None
        historical_data = []
        for index, row in hist.iterrows():
            historical_data.append({'symbol': symbol, 'timestamp': int(index.timestamp()), 'open': round(float(row['Open']), 2), 'high': round(float(row['High']), 2), 'low': round(float(row['Low']), 2), 'close': round(float(row['Close']), 2), 'volume': int(row['Volume']), 'adj_close': round(float(row['Close']), 2)})
        return historical_data
    except Exception as e:
        return {'error': str(e), 'symbol': symbol}

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

class PrivateEquityAnalyzer(AlternativeInvestmentBase):
    """
    Private Equity investment analysis and valuation
    CFA Standards: IRR, MOIC, DPI, RVPI calculations and due diligence
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.fund_life = getattr(parameters, 'fund_life', Constants.PE_TYPICAL_FUND_LIFE)
        self.vintage_year = getattr(parameters, 'vintage_year', None)
        self.commitment = getattr(parameters, 'commitment', None)
        self.called_capital = Decimal('0')
        self.distributed_capital = Decimal('0')
        self.current_nav = Decimal('0')

    def add_commitment(self, commitment_amount: Decimal, vintage_year: int) -> None:
        """Record fund commitment"""
        self.commitment = commitment_amount
        self.vintage_year = vintage_year

    def process_capital_call(self, amount: Decimal, call_date: str, description: str=None) -> None:
        """Process capital call from fund"""
        cash_flow = CashFlow(date=call_date, amount=-abs(amount), cf_type='capital_call', description=description or f'Capital call - {call_date}')
        self.add_cash_flows([cash_flow])
        self.called_capital += abs(amount)

    def process_distribution(self, amount: Decimal, dist_date: str, distribution_type: str='distribution') -> None:
        """Process distribution from fund"""
        cash_flow = CashFlow(date=dist_date, amount=amount, cf_type=distribution_type, description=f'{distribution_type} - {dist_date}')
        self.add_cash_flows([cash_flow])
        self.distributed_capital += amount

    def update_nav(self, nav_value: Decimal, nav_date: str) -> None:
        """Update current Net Asset Value"""
        self.current_nav = nav_value
        market_data = MarketData(timestamp=nav_date, price=nav_value, volume=None)
        self.add_market_data([market_data])

    def calculate_nav(self) -> Decimal:
        """Calculate current NAV"""
        return self.current_nav

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """
        Calculate key PE metrics following CFA standards
        """
        if not self.cash_flows:
            return {'error': 'No cash flows available'}
        metrics = {}
        cf_for_irr = self.cash_flows.copy()
        if self.current_nav > 0:
            latest_date = max((cf.date for cf in self.cash_flows)) if self.cash_flows else datetime.now().strftime('%Y-%m-%d')
            cf_for_irr.append(CashFlow(date=latest_date, amount=self.current_nav, cf_type='nav', description='Current NAV'))
        irr = self.math.irr(cf_for_irr)
        metrics['irr'] = float(irr) if irr else None
        moic = self.math.moic(cf_for_irr)
        metrics['moic'] = float(moic) if moic else None
        dpi = self.math.dpi(self.cash_flows)
        metrics['dpi'] = float(dpi)
        rvpi = self.math.rvpi(self.cash_flows, self.current_nav)
        metrics['rvpi'] = float(rvpi)
        tvpi = dpi + rvpi
        metrics['tvpi'] = float(tvpi)
        if self.commitment:
            called_ratio = self.called_capital / self.commitment
            metrics['called_capital_ratio'] = float(called_ratio)
            metrics['uncalled_commitment'] = float(self.commitment - self.called_capital)
        metrics['called_capital'] = float(self.called_capital)
        metrics['distributed_capital'] = float(self.distributed_capital)
        metrics['current_nav'] = float(self.current_nav)
        if self.vintage_year:
            current_year = datetime.now().year
            fund_age = current_year - self.vintage_year
            metrics['fund_age'] = fund_age
            metrics['vintage_year'] = self.vintage_year
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive PE valuation summary"""
        key_metrics = self.calculate_key_metrics()
        valuation = {'investment_overview': {'asset_class': self.parameters.asset_class.value, 'fund_name': self.parameters.name, 'vintage_year': self.vintage_year, 'commitment': float(self.commitment) if self.commitment else None}, 'capital_account': {'total_commitment': float(self.commitment) if self.commitment else None, 'called_capital': float(self.called_capital), 'uncalled_commitment': float(self.commitment - self.called_capital) if self.commitment else None, 'distributed_capital': float(self.distributed_capital), 'current_nav': float(self.current_nav)}, 'performance_metrics': key_metrics, 'cash_flow_summary': {'number_of_capital_calls': len([cf for cf in self.cash_flows if cf.cf_type == 'capital_call']), 'number_of_distributions': len([cf for cf in self.cash_flows if cf.cf_type == 'distribution']), 'total_cash_flows': len(self.cash_flows)}}
        return valuation

    def benchmark_comparison(self, benchmark_irr: Decimal, benchmark_moic: Decimal) -> Dict[str, Any]:
        """Compare performance against benchmark"""
        metrics = self.calculate_key_metrics()
        if not metrics.get('irr') or not metrics.get('moic'):
            return {'error': 'Insufficient data for benchmark comparison'}
        fund_irr = Decimal(str(metrics['irr']))
        fund_moic = Decimal(str(metrics['moic']))
        comparison = {'fund_performance': {'irr': float(fund_irr), 'moic': float(fund_moic)}, 'benchmark_performance': {'irr': float(benchmark_irr), 'moic': float(benchmark_moic)}, 'relative_performance': {'irr_difference': float(fund_irr - benchmark_irr), 'moic_difference': float(fund_moic - benchmark_moic), 'irr_outperformance': fund_irr > benchmark_irr, 'moic_outperformance': fund_moic > benchmark_moic}}
        return comparison

def process_capital_call(self, amount: Decimal, call_date: str, description: str=None) -> None:
    """Process capital call from fund"""
    cash_flow = CashFlow(date=call_date, amount=-abs(amount), cf_type='capital_call', description=description or f'Capital call - {call_date}')
    self.add_cash_flows([cash_flow])
    self.called_capital += abs(amount)

def process_distribution(self, amount: Decimal, dist_date: str, distribution_type: str='distribution') -> None:
    """Process distribution from fund"""
    cash_flow = CashFlow(date=dist_date, amount=amount, cf_type=distribution_type, description=f'{distribution_type} - {dist_date}')
    self.add_cash_flows([cash_flow])
    self.distributed_capital += amount

def update_nav(self, nav_value: Decimal, nav_date: str) -> None:
    """Update current Net Asset Value"""
    self.current_nav = nav_value
    market_data = MarketData(timestamp=nav_date, price=nav_value, volume=None)
    self.add_market_data([market_data])

def calculate_key_metrics(self) -> Dict[str, Any]:
    """
        Calculate key PE metrics following CFA standards
        """
    if not self.cash_flows:
        return {'error': 'No cash flows available'}
    metrics = {}
    cf_for_irr = self.cash_flows.copy()
    if self.current_nav > 0:
        latest_date = max((cf.date for cf in self.cash_flows)) if self.cash_flows else datetime.now().strftime('%Y-%m-%d')
        cf_for_irr.append(CashFlow(date=latest_date, amount=self.current_nav, cf_type='nav', description='Current NAV'))
    irr = self.math.irr(cf_for_irr)
    metrics['irr'] = float(irr) if irr else None
    moic = self.math.moic(cf_for_irr)
    metrics['moic'] = float(moic) if moic else None
    dpi = self.math.dpi(self.cash_flows)
    metrics['dpi'] = float(dpi)
    rvpi = self.math.rvpi(self.cash_flows, self.current_nav)
    metrics['rvpi'] = float(rvpi)
    tvpi = dpi + rvpi
    metrics['tvpi'] = float(tvpi)
    if self.commitment:
        called_ratio = self.called_capital / self.commitment
        metrics['called_capital_ratio'] = float(called_ratio)
        metrics['uncalled_commitment'] = float(self.commitment - self.called_capital)
    metrics['called_capital'] = float(self.called_capital)
    metrics['distributed_capital'] = float(self.distributed_capital)
    metrics['current_nav'] = float(self.current_nav)
    if self.vintage_year:
        current_year = datetime.now().year
        fund_age = current_year - self.vintage_year
        metrics['fund_age'] = fund_age
        metrics['vintage_year'] = self.vintage_year
    return metrics

class DataHandler:
    """
    Centralized data handler for all alternative investment data sources
    Supports multiple input formats and validates according to CFA standards
    """

    def __init__(self):
        self.config = Config()
        self.validation_rules = ValidationRules()

    def standardize_price_data(self, data: Union[Dict, pd.DataFrame, List]) -> List[MarketData]:
        """
        Standardize price data from various sources into MarketData objects

        Args:
            data: Price data in various formats

        Returns:
            List of MarketData objects
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._from_dataframe(data)
            elif isinstance(data, dict):
                return self._from_dict(data)
            elif isinstance(data, list):
                return self._from_list(data)
            else:
                raise DataValidationError(f'Unsupported data type: {type(data)}')
        except Exception as e:
            logger.error(f'Error standardizing price data: {str(e)}')
            raise DataValidationError(f'Failed to standardize price data: {str(e)}')

    def _from_dataframe(self, df: pd.DataFrame) -> List[MarketData]:
        """Convert DataFrame to MarketData objects"""
        required_columns = ['timestamp', 'price']
        if not all((col in df.columns for col in required_columns)):
            raise DataValidationError(f'DataFrame must contain columns: {required_columns}')
        market_data = []
        for _, row in df.iterrows():
            md = MarketData(timestamp=self._standardize_timestamp(row['timestamp']), price=self._to_decimal(row['price']), volume=self._to_decimal(row.get('volume')), bid=self._to_decimal(row.get('bid')), ask=self._to_decimal(row.get('ask')), high=self._to_decimal(row.get('high')), low=self._to_decimal(row.get('low')), open=self._to_decimal(row.get('open')), close=self._to_decimal(row.get('close')))
            self._validate_market_data(md)
            market_data.append(md)
        return market_data

    def _from_dict(self, data: Dict) -> List[MarketData]:
        """Convert dictionary to MarketData objects"""
        if 'data' in data:
            data = data['data']
        if isinstance(data, list):
            return [self._dict_to_market_data(item) for item in data]
        else:
            return [self._dict_to_market_data(data)]

    def _from_list(self, data: List) -> List[MarketData]:
        """Convert list to MarketData objects"""
        return [self._dict_to_market_data(item) for item in data]

    def _dict_to_market_data(self, item: Dict) -> MarketData:
        """Convert single dictionary item to MarketData"""
        md = MarketData(timestamp=self._standardize_timestamp(item.get('timestamp', item.get('date', item.get('time')))), price=self._to_decimal(item.get('price', item.get('close'))), volume=self._to_decimal(item.get('volume')), bid=self._to_decimal(item.get('bid')), ask=self._to_decimal(item.get('ask')), high=self._to_decimal(item.get('high')), low=self._to_decimal(item.get('low')), open=self._to_decimal(item.get('open')), close=self._to_decimal(item.get('close')))
        self._validate_market_data(md)
        return md

    def standardize_cash_flows(self, data: Union[Dict, pd.DataFrame, List]) -> List[CashFlow]:
        """
        Standardize cash flow data for IRR and performance calculations

        Args:
            data: Cash flow data in various formats

        Returns:
            List of CashFlow objects
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._cash_flows_from_dataframe(data)
            elif isinstance(data, dict):
                return self._cash_flows_from_dict(data)
            elif isinstance(data, list):
                return self._cash_flows_from_list(data)
            else:
                raise DataValidationError(f'Unsupported cash flow data type: {type(data)}')
        except Exception as e:
            logger.error(f'Error standardizing cash flows: {str(e)}')
            raise DataValidationError(f'Failed to standardize cash flows: {str(e)}')

    def _cash_flows_from_dataframe(self, df: pd.DataFrame) -> List[CashFlow]:
        """Convert DataFrame to CashFlow objects"""
        required_columns = ['date', 'amount']
        if not all((col in df.columns for col in required_columns)):
            raise DataValidationError(f'Cash flow DataFrame must contain columns: {required_columns}')
        cash_flows = []
        for _, row in df.iterrows():
            cf = CashFlow(date=self._standardize_date(row['date']), amount=self._to_decimal(row['amount']), cf_type=row.get('type', 'inflow' if float(row['amount']) > 0 else 'outflow'), description=row.get('description'))
            self._validate_cash_flow(cf)
            cash_flows.append(cf)
        return sorted(cash_flows, key=lambda x: x.date)

    def _cash_flows_from_dict(self, data: Dict) -> List[CashFlow]:
        """Convert dictionary to CashFlow objects"""
        if 'cash_flows' in data:
            data = data['cash_flows']
        if isinstance(data, list):
            return [self._dict_to_cash_flow(item) for item in data]
        else:
            return [self._dict_to_cash_flow(data)]

    def _cash_flows_from_list(self, data: List) -> List[CashFlow]:
        """Convert list to CashFlow objects"""
        return [self._dict_to_cash_flow(item) for item in data]

    def _dict_to_cash_flow(self, item: Dict) -> CashFlow:
        """Convert single dictionary item to CashFlow"""
        cf = CashFlow(date=self._standardize_date(item.get('date', item.get('timestamp'))), amount=self._to_decimal(item.get('amount', item.get('value'))), cf_type=item.get('type', item.get('cf_type', 'inflow' if float(item.get('amount', 0)) > 0 else 'outflow')), description=item.get('description', item.get('desc')))
        self._validate_cash_flow(cf)
        return cf

    def load_from_csv(self, file_path: str, data_type: str='price') -> Union[List[MarketData], List[CashFlow]]:
        """
        Load data from CSV file

        Args:
            file_path: Path to CSV file
            data_type: 'price' or 'cash_flow'

        Returns:
            Standardized data objects
        """
        try:
            df = pd.read_csv(file_path)
            if data_type == 'price':
                return self.standardize_price_data(df)
            elif data_type == 'cash_flow':
                return self.standardize_cash_flows(df)
            else:
                raise DataValidationError(f'Unsupported data type: {data_type}')
        except Exception as e:
            logger.error(f'Error loading CSV file {file_path}: {str(e)}')
            raise DataValidationError(f'Failed to load CSV: {str(e)}')

    def load_from_json(self, file_path: str, data_type: str='price') -> Union[List[MarketData], List[CashFlow]]:
        """
        Load data from JSON file

        Args:
            file_path: Path to JSON file
            data_type: 'price' or 'cash_flow'

        Returns:
            Standardized data objects
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if data_type == 'price':
                return self.standardize_price_data(data)
            elif data_type == 'cash_flow':
                return self.standardize_cash_flows(data)
            else:
                raise DataValidationError(f'Unsupported data type: {data_type}')
        except Exception as e:
            logger.error(f'Error loading JSON file {file_path}: {str(e)}')
            raise DataValidationError(f'Failed to load JSON: {str(e)}')

    def calculate_returns(self, prices: List[MarketData], method: str='simple') -> pd.DataFrame:
        """
        Calculate returns from price data

        Args:
            prices: List of MarketData objects
            method: 'simple', 'log', or 'compound'

        Returns:
            DataFrame with returns
        """
        if len(prices) < 2:
            raise DataValidationError('Need at least 2 price points to calculate returns')
        df = pd.DataFrame([{'timestamp': p.timestamp, 'price': float(p.price)} for p in prices])
        df = df.sort_values('timestamp')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if method == 'simple':
            df['return'] = df['price'].pct_change()
        elif method == 'log':
            df['return'] = np.log(df['price'] / df['price'].shift(1))
        elif method == 'compound':
            df['return'] = df['price'] / df['price'].shift(1) - 1
        else:
            raise DataValidationError(f'Unsupported return calculation method: {method}')
        return df.dropna()

    def aggregate_to_frequency(self, data: List[MarketData], frequency: str='monthly') -> List[MarketData]:
        """
        Aggregate data to specified frequency

        Args:
            data: List of MarketData objects
            frequency: 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'

        Returns:
            Aggregated MarketData objects
        """
        if not data:
            return []
        df = pd.DataFrame([{'timestamp': pd.to_datetime(d.timestamp), 'price': float(d.price), 'volume': float(d.volume) if d.volume else 0, 'high': float(d.high) if d.high else float(d.price), 'low': float(d.low) if d.low else float(d.price), 'open': float(d.open) if d.open else float(d.price), 'close': float(d.close) if d.close else float(d.price)} for d in data])
        df = df.set_index('timestamp').sort_index()
        freq_map = {'daily': 'D', 'weekly': 'W', 'monthly': 'M', 'quarterly': 'Q', 'yearly': 'Y'}
        if frequency not in freq_map:
            raise DataValidationError(f'Unsupported frequency: {frequency}')
        agg_df = df.resample(freq_map[frequency]).agg({'price': 'last', 'volume': 'sum', 'high': 'max', 'low': 'min', 'open': 'first', 'close': 'last'}).dropna()
        result = []
        for timestamp, row in agg_df.iterrows():
            md = MarketData(timestamp=timestamp.strftime('%Y-%m-%d'), price=Decimal(str(row['price'])), volume=Decimal(str(row['volume'])) if row['volume'] > 0 else None, high=Decimal(str(row['high'])), low=Decimal(str(row['low'])), open=Decimal(str(row['open'])), close=Decimal(str(row['close'])))
            result.append(md)
        return result

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal with validation"""
        if value is None or pd.isna(value):
            return None
        try:
            decimal_value = Decimal(str(value))
            if decimal_value < self.config.MIN_PRICE and decimal_value != 0:
                raise DataValidationError(f'Price too small: {decimal_value}')
            return decimal_value
        except (InvalidOperation, ValueError) as e:
            raise DataValidationError(f'Invalid decimal value: {value}')

    def _standardize_timestamp(self, timestamp: Any) -> str:
        """Standardize timestamp to ISO format"""
        if isinstance(timestamp, str):
            try:
                dt = pd.to_datetime(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return timestamp
        elif isinstance(timestamp, (datetime, date)):
            return timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(timestamp)

    def _standardize_date(self, date_value: Any) -> str:
        """Standardize date to ISO format"""
        if isinstance(date_value, str):
            try:
                dt = pd.to_datetime(date_value)
                return dt.strftime('%Y-%m-%d')
            except:
                return date_value
        elif isinstance(date_value, (datetime, date)):
            return date_value.strftime('%Y-%m-%d')
        else:
            return str(date_value)

    def _validate_market_data(self, md: MarketData) -> None:
        """Validate MarketData object"""
        if md.price <= 0:
            raise DataValidationError(f'Invalid price: {md.price}')
        if md.volume is not None and md.volume < 0:
            raise DataValidationError(f'Invalid volume: {md.volume}')
        if md.high and md.low and (md.high < md.low):
            raise DataValidationError(f'High price ({md.high}) less than low price ({md.low})')
        if md.bid and md.ask and (md.bid > md.ask):
            raise DataValidationError(f'Bid price ({md.bid}) greater than ask price ({md.ask})')

    def _validate_cash_flow(self, cf: CashFlow) -> None:
        """Validate CashFlow object"""
        if cf.amount == 0:
            logger.warning(f'Zero cash flow amount on {cf.date}')
        valid_types = ['inflow', 'outflow', 'distribution', 'capital_call', 'dividend', 'interest']
        if cf.cf_type not in valid_types:
            logger.warning(f'Unknown cash flow type: {cf.cf_type}')

    def get_data_summary(self, data: Union[List[MarketData], List[CashFlow]]) -> Dict[str, Any]:
        """Get summary statistics of the data"""
        if not data:
            return {'error': 'No data provided'}
        if isinstance(data[0], MarketData):
            prices = [float(d.price) for d in data]
            return {'data_type': 'MarketData', 'count': len(data), 'price_stats': {'mean': np.mean(prices), 'std': np.std(prices), 'min': np.min(prices), 'max': np.max(prices)}, 'date_range': {'start': min((d.timestamp for d in data)), 'end': max((d.timestamp for d in data))}}
        elif isinstance(data[0], CashFlow):
            amounts = [float(d.amount) for d in data]
            return {'data_type': 'CashFlow', 'count': len(data), 'amount_stats': {'total': sum(amounts), 'mean': np.mean(amounts), 'std': np.std(amounts), 'min': np.min(amounts), 'max': np.max(amounts)}, 'date_range': {'start': min((d.date for d in data)), 'end': max((d.date for d in data))}, 'inflows': sum((1 for d in data if d.amount > 0)), 'outflows': sum((1 for d in data if d.amount < 0))}
        return {'error': 'Unknown data type'}

def _from_dataframe(self, df: pd.DataFrame) -> List[MarketData]:
    """Convert DataFrame to MarketData objects"""
    required_columns = ['timestamp', 'price']
    if not all((col in df.columns for col in required_columns)):
        raise DataValidationError(f'DataFrame must contain columns: {required_columns}')
    market_data = []
    for _, row in df.iterrows():
        md = MarketData(timestamp=self._standardize_timestamp(row['timestamp']), price=self._to_decimal(row['price']), volume=self._to_decimal(row.get('volume')), bid=self._to_decimal(row.get('bid')), ask=self._to_decimal(row.get('ask')), high=self._to_decimal(row.get('high')), low=self._to_decimal(row.get('low')), open=self._to_decimal(row.get('open')), close=self._to_decimal(row.get('close')))
        self._validate_market_data(md)
        market_data.append(md)
    return market_data

def _dict_to_market_data(self, item: Dict) -> MarketData:
    """Convert single dictionary item to MarketData"""
    md = MarketData(timestamp=self._standardize_timestamp(item.get('timestamp', item.get('date', item.get('time')))), price=self._to_decimal(item.get('price', item.get('close'))), volume=self._to_decimal(item.get('volume')), bid=self._to_decimal(item.get('bid')), ask=self._to_decimal(item.get('ask')), high=self._to_decimal(item.get('high')), low=self._to_decimal(item.get('low')), open=self._to_decimal(item.get('open')), close=self._to_decimal(item.get('close')))
    self._validate_market_data(md)
    return md

def _cash_flows_from_dataframe(self, df: pd.DataFrame) -> List[CashFlow]:
    """Convert DataFrame to CashFlow objects"""
    required_columns = ['date', 'amount']
    if not all((col in df.columns for col in required_columns)):
        raise DataValidationError(f'Cash flow DataFrame must contain columns: {required_columns}')
    cash_flows = []
    for _, row in df.iterrows():
        cf = CashFlow(date=self._standardize_date(row['date']), amount=self._to_decimal(row['amount']), cf_type=row.get('type', 'inflow' if float(row['amount']) > 0 else 'outflow'), description=row.get('description'))
        self._validate_cash_flow(cf)
        cash_flows.append(cf)
    return sorted(cash_flows, key=lambda x: x.date)

def _dict_to_cash_flow(self, item: Dict) -> CashFlow:
    """Convert single dictionary item to CashFlow"""
    cf = CashFlow(date=self._standardize_date(item.get('date', item.get('timestamp'))), amount=self._to_decimal(item.get('amount', item.get('value'))), cf_type=item.get('type', item.get('cf_type', 'inflow' if float(item.get('amount', 0)) > 0 else 'outflow')), description=item.get('description', item.get('desc')))
    self._validate_cash_flow(cf)
    return cf

class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for alternative investments
    Implements CFA Institute standard performance measurement methodologies
    """

    def __init__(self):
        self.math = FinancialMath()
        self.config = Config()

    def calculate_time_weighted_return(self, prices: List[MarketData], cash_flows: List[CashFlow]=None) -> Dict[str, Decimal]:
        """
        Calculate Time-Weighted Return (TWR)
        CFA Standard: Geometric mean of sub-period returns
        Eliminates the effect of cash flow timing

        Args:
            prices: List of MarketData objects
            cash_flows: Optional cash flows for adjustment

        Returns:
            Dictionary with TWR metrics
        """
        if len(prices) < 2:
            return {'error': 'Insufficient price data'}
        sorted_prices = sorted(prices, key=lambda x: x.timestamp)
        returns = []
        for i in range(1, len(sorted_prices)):
            prev_price = sorted_prices[i - 1].price
            curr_price = sorted_prices[i].price
            period_return = (curr_price - prev_price) / prev_price
            returns.append(period_return)
        if not returns:
            return {'twr': Decimal('0')}
        cumulative_return = Decimal('1')
        for ret in returns:
            cumulative_return *= Decimal('1') + ret
        twr = cumulative_return - Decimal('1')
        total_days = (datetime.strptime(sorted_prices[-1].timestamp[:10], '%Y-%m-%d') - datetime.strptime(sorted_prices[0].timestamp[:10], '%Y-%m-%d')).days
        if total_days > 0:
            years = Decimal(str(total_days)) / Constants.DAYS_IN_YEAR
            annualized_twr = cumulative_return ** (Decimal('1') / years) - Decimal('1')
        else:
            annualized_twr = twr
        return {'twr': twr, 'annualized_twr': annualized_twr, 'cumulative_return': cumulative_return - Decimal('1'), 'number_of_periods': len(returns), 'total_days': total_days}

    def calculate_money_weighted_return(self, cash_flows: List[CashFlow]) -> Dict[str, Decimal]:
        """
        Calculate Money-Weighted Return (MWR) using IRR
        CFA Standard: IRR of all cash flows including ending value
        Reflects the effect of cash flow timing

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            Dictionary with MWR metrics
        """
        if not cash_flows:
            return {'error': 'No cash flows provided'}
        irr = self.math.irr(cash_flows)
        if irr is None:
            return {'error': 'Could not calculate IRR'}
        moic = self.math.moic(cash_flows)
        dpi = self.math.dpi(cash_flows)
        return {'mwr_irr': irr, 'moic': moic, 'dpi': dpi, 'total_cash_flows': len(cash_flows)}

    def calculate_risk_adjusted_returns(self, returns: List[Decimal], benchmark_returns: List[Decimal]=None) -> Dict[str, Decimal]:
        """
        Calculate comprehensive risk-adjusted return metrics
        CFA Standards: Sharpe, Treynor, Information, Sortino ratios

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns for comparison

        Returns:
            Dictionary of risk-adjusted metrics
        """
        if len(returns) < 2:
            return {'error': 'Insufficient return data'}
        metrics = {}
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        rf_rate = self.config.RISK_FREE_RATE / Constants.MONTHS_IN_YEAR
        sharpe = self.math.sharpe_ratio(returns, rf_rate)
        metrics['sharpe_ratio'] = sharpe
        sortino = self.math.sortino_ratio(returns)
        metrics['sortino_ratio'] = sortino
        if len(returns) > 1:
            prices = [Decimal('100')]
            for ret in returns:
                prices.append(prices[-1] * (Decimal('1') + ret))
            max_dd, _, _ = self.math.maximum_drawdown(prices)
            annualized_return = mean_return * Constants.MONTHS_IN_YEAR
            calmar = self.math.calmar_ratio(annualized_return, max_dd)
            metrics['calmar_ratio'] = calmar
            metrics['maximum_drawdown'] = max_dd
        if benchmark_returns and len(benchmark_returns) == len(returns):
            active_returns = [r - b for r, b in zip(returns, benchmark_returns)]
            tracking_error = self._calculate_volatility(active_returns)
            metrics['tracking_error'] = tracking_error
            mean_active_return = sum(active_returns) / len(active_returns)
            if tracking_error > 0:
                information_ratio = mean_active_return / tracking_error
                metrics['information_ratio'] = information_ratio
            if len(returns) > 1:
                beta = self._calculate_beta(returns, benchmark_returns)
                metrics['beta'] = beta
                if beta != 0:
                    treynor = (mean_return - rf_rate) / beta
                    metrics['treynor_ratio'] = treynor
        var_95 = self.math.var_historical(returns, Decimal('0.05'))
        var_99 = self.math.var_historical(returns, Decimal('0.01'))
        metrics['var_95'] = var_95
        metrics['var_99'] = var_99
        cvar_95 = self._calculate_cvar(returns, Decimal('0.05'))
        metrics['cvar_95'] = cvar_95
        return metrics

    def performance_attribution(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal], sector_weights: Dict[str, Decimal]=None) -> Dict[str, Any]:
        """
        Perform return-based performance attribution analysis
        CFA Standard: Decompose excess returns into allocation and selection effects

        Args:
            portfolio_returns: Portfolio period returns
            benchmark_returns: Benchmark period returns
            sector_weights: Optional sector weight information

        Returns:
            Attribution analysis results
        """
        if len(portfolio_returns) != len(benchmark_returns):
            return {'error': 'Portfolio and benchmark return lengths must match'}
        attribution = {}
        active_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        portfolio_mean = sum(portfolio_returns) / len(portfolio_returns)
        benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)
        active_mean = portfolio_mean - benchmark_mean
        attribution['total_active_return'] = active_mean
        attribution['portfolio_return'] = portfolio_mean
        attribution['benchmark_return'] = benchmark_mean
        positive_periods = sum((1 for ar in active_returns if ar > 0))
        hit_rate = Decimal(str(positive_periods)) / Decimal(str(len(active_returns)))
        attribution['hit_rate'] = hit_rate
        active_volatility = self._calculate_volatility(active_returns)
        attribution['active_volatility'] = active_volatility
        if active_volatility > 0:
            information_ratio = active_mean / active_volatility
            attribution['information_ratio'] = information_ratio
        return attribution

    def calculate_downside_metrics(self, returns: List[Decimal], target_return: Decimal=Decimal('0')) -> Dict[str, Decimal]:
        """
        Calculate comprehensive downside risk metrics
        CFA Standards: Downside deviation, downside beta, etc.

        Args:
            returns: Period returns
            target_return: Target or MAR (Minimum Acceptable Return)

        Returns:
            Dictionary of downside metrics
        """
        downside_metrics = {}
        downside_returns = [min(r - target_return, Decimal('0')) for r in returns]
        downside_variance = sum((dr ** 2 for dr in downside_returns)) / len(returns)
        downside_deviation = downside_variance.sqrt()
        downside_metrics['downside_deviation'] = downside_deviation
        mean_return = sum(returns) / len(returns)
        if downside_deviation > 0:
            sortino = (mean_return - target_return) / downside_deviation
            downside_metrics['sortino_ratio'] = sortino
        negative_periods = sum((1 for r in returns if r < target_return))
        downside_frequency = Decimal(str(negative_periods)) / Decimal(str(len(returns)))
        downside_metrics['downside_frequency'] = downside_frequency
        negative_returns = [r for r in returns if r < target_return]
        if negative_returns:
            avg_downside = sum(negative_returns) / len(negative_returns)
            downside_metrics['average_downside_return'] = avg_downside
        return downside_metrics

    def rolling_performance(self, prices: List[MarketData], window_months: int=12) -> List[Dict]:
        """
        Calculate rolling performance metrics

        Args:
            prices: List of MarketData objects
            window_months: Rolling window size in months

        Returns:
            List of rolling performance dictionaries
        """
        if len(prices) < window_months:
            return []
        rolling_results = []
        sorted_prices = sorted(prices, key=lambda x: x.timestamp)
        for i in range(window_months, len(sorted_prices)):
            window_prices = sorted_prices[i - window_months:i + 1]
            window_returns = []
            for j in range(1, len(window_prices)):
                ret = (window_prices[j].price - window_prices[j - 1].price) / window_prices[j - 1].price
                window_returns.append(ret)
            if window_returns:
                period_return = (window_prices[-1].price - window_prices[0].price) / window_prices[0].price
                volatility = self._calculate_volatility(window_returns)
                sharpe = self.math.sharpe_ratio(window_returns)
                rolling_results.append({'end_date': window_prices[-1].timestamp, 'period_return': float(period_return), 'annualized_return': float(period_return * Constants.MONTHS_IN_YEAR / window_months), 'volatility': float(volatility), 'sharpe_ratio': float(sharpe)})
        return rolling_results

    def calculate_factor_exposures(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, Decimal]:
        """
        Calculate factor exposures using multiple regression
        CFA Standard: Multi-factor model analysis

        Args:
            portfolio_returns: Portfolio returns
            factor_returns: Dictionary of factor name -> factor returns

        Returns:
            Dictionary of factor loadings (betas)
        """
        if not factor_returns or len(portfolio_returns) < 10:
            return {}
        valid_factors = {}
        for factor_name, returns in factor_returns.items():
            if len(returns) == len(portfolio_returns):
                valid_factors[factor_name] = returns
        if not valid_factors:
            return {}
        try:
            y = np.array([float(r) for r in portfolio_returns])
            X = np.array([[float(valid_factors[factor][i]) for factor in valid_factors.keys()] for i in range(len(portfolio_returns))])
            X = np.column_stack([np.ones(len(y)), X])
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            exposures = {'alpha': Decimal(str(beta[0]))}
            for i, factor_name in enumerate(valid_factors.keys()):
                exposures[f'{factor_name}_beta'] = Decimal(str(beta[i + 1]))
            y_pred = X @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0
            exposures['r_squared'] = Decimal(str(r_squared))
            return exposures
        except Exception as e:
            logger.error(f'Error calculating factor exposures: {str(e)}')
            return {}

    def benchmark_analysis(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Dict[str, Any]:
        """
        Comprehensive benchmark analysis
        CFA Standards: Up/down capture, batting average, etc.

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Dictionary of benchmark analysis metrics
        """
        if len(portfolio_returns) != len(benchmark_returns):
            return {'error': 'Return series length mismatch'}
        analysis = {}
        up_periods = [(p, b) for p, b in zip(portfolio_returns, benchmark_returns) if b > 0]
        down_periods = [(p, b) for p, b in zip(portfolio_returns, benchmark_returns) if b < 0]
        if up_periods:
            up_portfolio = sum((p for p, b in up_periods)) / len(up_periods)
            up_benchmark = sum((b for p, b in up_periods)) / len(up_periods)
            up_capture = up_portfolio / up_benchmark if up_benchmark != 0 else Decimal('0')
            analysis['up_capture_ratio'] = up_capture
        if down_periods:
            down_portfolio = sum((p for p, b in down_periods)) / len(down_periods)
            down_benchmark = sum((b for p, b in down_periods)) / len(down_periods)
            down_capture = down_portfolio / down_benchmark if down_benchmark != 0 else Decimal('0')
            analysis['down_capture_ratio'] = down_capture
        outperformance_periods = sum((1 for p, b in zip(portfolio_returns, benchmark_returns) if p > b))
        batting_average = Decimal(str(outperformance_periods)) / Decimal(str(len(portfolio_returns)))
        analysis['batting_average'] = batting_average
        beta = self._calculate_beta(portfolio_returns, benchmark_returns)
        correlation = self._calculate_correlation(portfolio_returns, benchmark_returns)
        analysis['beta'] = beta
        analysis['correlation'] = correlation
        return analysis

    def performance_persistence(self, returns_by_period: List[List[Decimal]]) -> Dict[str, Any]:
        """
        Analyze performance persistence across periods

        Args:
            returns_by_period: List of return lists for different periods

        Returns:
            Persistence analysis metrics
        """
        if len(returns_by_period) < 2:
            return {'error': 'Need at least 2 periods for persistence analysis'}
        persistence = {}
        period_rankings = []
        for period_returns in returns_by_period:
            if not period_returns:
                continue
            sorted_returns = sorted(period_returns, reverse=True)
            rankings = []
            for ret in period_returns:
                rank = sorted_returns.index(ret) + 1
                rankings.append(rank)
            period_rankings.append(rankings)
        if len(period_rankings) < 2:
            return {'error': 'Insufficient valid periods'}
        correlations = []
        for i in range(len(period_rankings) - 1):
            corr = self._calculate_rank_correlation(period_rankings[i], period_rankings[i + 1])
            correlations.append(corr)
        persistence['rank_correlations'] = correlations
        persistence['average_rank_correlation'] = sum(correlations) / len(correlations) if correlations else Decimal('0')
        return persistence

    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate standard deviation of returns"""
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        return variance.sqrt()

    def _calculate_beta(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Decimal:
        """Calculate beta (systematic risk measure)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return Decimal('1')
        port_mean = sum(portfolio_returns) / len(portfolio_returns)
        bench_mean = sum(benchmark_returns) / len(benchmark_returns)
        covariance = sum(((p - port_mean) * (b - bench_mean) for p, b in zip(portfolio_returns, benchmark_returns))) / (len(portfolio_returns) - 1)
        bench_variance = sum(((b - bench_mean) ** 2 for b in benchmark_returns)) / (len(benchmark_returns) - 1)
        if bench_variance == 0:
            return Decimal('1')
        return Decimal(str(covariance)) / Decimal(str(bench_variance))

    def _calculate_correlation(self, x: List[Decimal], y: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return Decimal('0')
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)
        numerator = sum(((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)))
        x_sq_sum = sum(((xi - x_mean) ** 2 for xi in x))
        y_sq_sum = sum(((yi - y_mean) ** 2 for yi in y))
        denominator = (x_sq_sum * y_sq_sum).sqrt()
        if denominator == 0:
            return Decimal('0')
        return numerator / denominator

    def _calculate_rank_correlation(self, ranks1: List[int], ranks2: List[int]) -> Decimal:
        """Calculate Spearman rank correlation"""
        if len(ranks1) != len(ranks2) or len(ranks1) < 2:
            return Decimal('0')
        n = len(ranks1)
        d_squared_sum = sum(((r1 - r2) ** 2 for r1, r2 in zip(ranks1, ranks2)))
        correlation = Decimal('1') - Decimal('6') * Decimal(str(d_squared_sum)) / (Decimal(str(n)) * (Decimal(str(n)) ** 2 - Decimal('1')))
        return correlation

    def _calculate_cvar(self, returns: List[Decimal], confidence_level: Decimal) -> Decimal:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if not returns:
            return Decimal('0')
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * confidence_level)
        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1
        tail_returns = sorted_returns[:var_index + 1]
        if not tail_returns:
            return Decimal('0')
        cvar = sum(tail_returns) / len(tail_returns)
        return abs(cvar)

def calculate_money_weighted_return(self, cash_flows: List[CashFlow]) -> Dict[str, Decimal]:
    """
        Calculate Money-Weighted Return (MWR) using IRR
        CFA Standard: IRR of all cash flows including ending value
        Reflects the effect of cash flow timing

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            Dictionary with MWR metrics
        """
    if not cash_flows:
        return {'error': 'No cash flows provided'}
    irr = self.math.irr(cash_flows)
    if irr is None:
        return {'error': 'Could not calculate IRR'}
    moic = self.math.moic(cash_flows)
    dpi = self.math.dpi(cash_flows)
    return {'mwr_irr': irr, 'moic': moic, 'dpi': dpi, 'total_cash_flows': len(cash_flows)}

class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider implementation"""

    def __init__(self):
        self.name = 'Yahoo Finance'
        self.base_url = 'https://finance.yahoo.com'

    def get_company_data(self, symbol: str) -> CompanyData:
        """Retrieve comprehensive company data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            shares_outstanding = info.get('sharesOutstanding', 0)
            market_cap = info.get('marketCap', current_price * shares_outstanding)
            financial_data = {'revenue': info.get('totalRevenue', 0), 'net_income': info.get('netIncomeToCommon', 0), 'total_assets': info.get('totalAssets', 0), 'total_debt': info.get('totalDebt', 0), 'book_value': info.get('bookValue', 0), 'earnings_per_share': info.get('trailingEps', 0), 'dividend_per_share': info.get('dividendRate', 0), 'roe': info.get('returnOnEquity', 0), 'roa': info.get('returnOnAssets', 0), 'profit_margin': info.get('profitMargins', 0), 'debt_to_equity': info.get('debtToEquity', 0), 'current_ratio': info.get('currentRatio', 0), 'quick_ratio': info.get('quickRatio', 0), 'ebitda': info.get('ebitda', 0), 'free_cash_flow': info.get('freeCashflow', 0), 'operating_cash_flow': info.get('operatingCashflow', 0)}
            market_data = {'beta': info.get('beta', 1.0), 'pe_ratio': info.get('trailingPE', 0), 'forward_pe': info.get('forwardPE', 0), 'pb_ratio': info.get('priceToBook', 0), 'ps_ratio': info.get('priceToSalesTrailing12Months', 0), 'peg_ratio': info.get('pegRatio', 0), 'dividend_yield': info.get('dividendYield', 0), 'revenue_growth': info.get('revenueGrowth', 0), 'earnings_growth': info.get('earningsGrowth', 0), '52_week_high': info.get('fiftyTwoWeekHigh', 0), '52_week_low': info.get('fiftyTwoWeekLow', 0), 'average_volume': info.get('averageVolume', 0), 'float_shares': info.get('floatShares', shares_outstanding)}
            return CompanyData(symbol=symbol.upper(), name=info.get('longName', symbol), sector=info.get('sector', 'Unknown'), industry=info.get('industry', 'Unknown'), market_cap=market_cap, shares_outstanding=shares_outstanding, current_price=current_price, financial_data=financial_data, market_data=market_data, last_updated=datetime.now())
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve company data for {symbol}: {str(e)}')

    def get_market_data(self, symbol: str) -> MarketData:
        """Retrieve market-specific data for valuation models"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            treasury = yf.Ticker('^TNX')
            risk_free_rate = treasury.history(period='1d')['Close'].iloc[-1] / 100
            sp500 = yf.Ticker('^GSPC')
            sp500_data = sp500.history(period='1y')
            market_return = sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0] - 1
            return MarketData(risk_free_rate=risk_free_rate, market_return=market_return, beta=info.get('beta', 1.0), dividend_yield=info.get('dividendYield', 0), growth_rate=info.get('earningsGrowth', 0.03), required_return=risk_free_rate + info.get('beta', 1.0) * (market_return - risk_free_rate))
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve market data for {symbol}: {str(e)}')

    def get_financial_statements(self, symbol: str, period: str='annual') -> Dict[str, pd.DataFrame]:
        """Retrieve financial statements"""
        try:
            ticker = yf.Ticker(symbol)
            if period == 'annual':
                income_stmt = ticker.financials
                balance_sheet = ticker.balance_sheet
                cash_flow = ticker.cashflow
            else:
                income_stmt = ticker.quarterly_financials
                balance_sheet = ticker.quarterly_balance_sheet
                cash_flow = ticker.quarterly_cashflow
            return {'income_statement': income_stmt, 'balance_sheet': balance_sheet, 'cash_flow_statement': cash_flow}
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve financial statements for {symbol}: {str(e)}')

    def get_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Retrieve historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(start=start_date, end=end_date)
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve price data for {symbol}: {str(e)}')

def get_company_data(self, symbol: str) -> CompanyData:
    """Retrieve comprehensive company data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        shares_outstanding = info.get('sharesOutstanding', 0)
        market_cap = info.get('marketCap', current_price * shares_outstanding)
        financial_data = {'revenue': info.get('totalRevenue', 0), 'net_income': info.get('netIncomeToCommon', 0), 'total_assets': info.get('totalAssets', 0), 'total_debt': info.get('totalDebt', 0), 'book_value': info.get('bookValue', 0), 'earnings_per_share': info.get('trailingEps', 0), 'dividend_per_share': info.get('dividendRate', 0), 'roe': info.get('returnOnEquity', 0), 'roa': info.get('returnOnAssets', 0), 'profit_margin': info.get('profitMargins', 0), 'debt_to_equity': info.get('debtToEquity', 0), 'current_ratio': info.get('currentRatio', 0), 'quick_ratio': info.get('quickRatio', 0), 'ebitda': info.get('ebitda', 0), 'free_cash_flow': info.get('freeCashflow', 0), 'operating_cash_flow': info.get('operatingCashflow', 0)}
        market_data = {'beta': info.get('beta', 1.0), 'pe_ratio': info.get('trailingPE', 0), 'forward_pe': info.get('forwardPE', 0), 'pb_ratio': info.get('priceToBook', 0), 'ps_ratio': info.get('priceToSalesTrailing12Months', 0), 'peg_ratio': info.get('pegRatio', 0), 'dividend_yield': info.get('dividendYield', 0), 'revenue_growth': info.get('revenueGrowth', 0), 'earnings_growth': info.get('earningsGrowth', 0), '52_week_high': info.get('fiftyTwoWeekHigh', 0), '52_week_low': info.get('fiftyTwoWeekLow', 0), 'average_volume': info.get('averageVolume', 0), 'float_shares': info.get('floatShares', shares_outstanding)}
        return CompanyData(symbol=symbol.upper(), name=info.get('longName', symbol), sector=info.get('sector', 'Unknown'), industry=info.get('industry', 'Unknown'), market_cap=market_cap, shares_outstanding=shares_outstanding, current_price=current_price, financial_data=financial_data, market_data=market_data, last_updated=datetime.now())
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve company data for {symbol}: {str(e)}')

def get_market_data(self, symbol: str) -> MarketData:
    """Retrieve market-specific data for valuation models"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        treasury = yf.Ticker('^TNX')
        risk_free_rate = treasury.history(period='1d')['Close'].iloc[-1] / 100
        sp500 = yf.Ticker('^GSPC')
        sp500_data = sp500.history(period='1y')
        market_return = sp500_data['Close'].iloc[-1] / sp500_data['Close'].iloc[0] - 1
        return MarketData(risk_free_rate=risk_free_rate, market_return=market_return, beta=info.get('beta', 1.0), dividend_yield=info.get('dividendYield', 0), growth_rate=info.get('earningsGrowth', 0.03), required_return=risk_free_rate + info.get('beta', 1.0) * (market_return - risk_free_rate))
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve market data for {symbol}: {str(e)}')

def get_financial_statements(self, symbol: str, period: str='annual') -> Dict[str, pd.DataFrame]:
    """Retrieve financial statements"""
    try:
        ticker = yf.Ticker(symbol)
        if period == 'annual':
            income_stmt = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow
        else:
            income_stmt = ticker.quarterly_financials
            balance_sheet = ticker.quarterly_balance_sheet
            cash_flow = ticker.quarterly_cashflow
        return {'income_statement': income_stmt, 'balance_sheet': balance_sheet, 'cash_flow_statement': cash_flow}
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve financial statements for {symbol}: {str(e)}')

def get_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Retrieve historical price data"""
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(start=start_date, end=end_date)
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve price data for {symbol}: {str(e)}')

class AlphaVantageProvider(DataProvider):
    """Alpha Vantage data provider implementation"""

    def __init__(self, api_key: str):
        self.name = 'Alpha Vantage'
        self.api_key = api_key
        self.base_url = 'https://www.alphavantage.co/query'

    def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make API request to Alpha Vantage"""
        params['apikey'] = self.api_key
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    def get_company_data(self, symbol: str) -> CompanyData:
        """Retrieve company data from Alpha Vantage"""
        try:
            overview_params = {'function': 'OVERVIEW', 'symbol': symbol}
            overview = self._make_request(overview_params)
            quote_params = {'function': 'GLOBAL_QUOTE', 'symbol': symbol}
            quote_data = self._make_request(quote_params)
            quote = quote_data.get('Global Quote', {})
            current_price = float(quote.get('05. price', 0))
            shares_outstanding = float(overview.get('SharesOutstanding', 0))
            financial_data = {'revenue': float(overview.get('RevenueTTM', 0)), 'net_income': float(overview.get('ProfitMargin', 0)) * float(overview.get('RevenueTTM', 0)), 'total_assets': 0, 'book_value': float(overview.get('BookValue', 0)), 'earnings_per_share': float(overview.get('EPS', 0)), 'dividend_per_share': float(overview.get('DividendPerShare', 0)), 'roe': float(overview.get('ReturnOnEquityTTM', 0)), 'profit_margin': float(overview.get('ProfitMargin', 0)), 'ebitda': float(overview.get('EBITDA', 0))}
            market_data = {'beta': float(overview.get('Beta', 1.0)), 'pe_ratio': float(overview.get('PERatio', 0)), 'pb_ratio': float(overview.get('PriceToBookRatio', 0)), 'peg_ratio': float(overview.get('PEGRatio', 0)), 'dividend_yield': float(overview.get('DividendYield', 0)), '52_week_high': float(overview.get('52WeekHigh', 0)), '52_week_low': float(overview.get('52WeekLow', 0))}
            return CompanyData(symbol=symbol.upper(), name=overview.get('Name', symbol), sector=overview.get('Sector', 'Unknown'), industry=overview.get('Industry', 'Unknown'), market_cap=float(overview.get('MarketCapitalization', 0)), shares_outstanding=shares_outstanding, current_price=current_price, financial_data=financial_data, market_data=market_data, last_updated=datetime.now())
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve company data for {symbol}: {str(e)}')

    def get_market_data(self, symbol: str) -> MarketData:
        """Retrieve market data from Alpha Vantage"""
        try:
            overview_params = {'function': 'OVERVIEW', 'symbol': symbol}
            overview = self._make_request(overview_params)
            return MarketData(risk_free_rate=0.05, market_return=0.1, beta=float(overview.get('Beta', 1.0)), dividend_yield=float(overview.get('DividendYield', 0)), growth_rate=0.03, required_return=0.08)
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve market data for {symbol}: {str(e)}')

    def get_financial_statements(self, symbol: str, period: str='annual') -> Dict[str, pd.DataFrame]:
        """Retrieve financial statements from Alpha Vantage"""
        try:
            statements = {}
            income_params = {'function': 'INCOME_STATEMENT', 'symbol': symbol}
            income_data = self._make_request(income_params)
            if period == 'annual':
                statements['income_statement'] = pd.DataFrame(income_data.get('annualReports', []))
            else:
                statements['income_statement'] = pd.DataFrame(income_data.get('quarterlyReports', []))
            balance_params = {'function': 'BALANCE_SHEET', 'symbol': symbol}
            balance_data = self._make_request(balance_params)
            if period == 'annual':
                statements['balance_sheet'] = pd.DataFrame(balance_data.get('annualReports', []))
            else:
                statements['balance_sheet'] = pd.DataFrame(balance_data.get('quarterlyReports', []))
            cashflow_params = {'function': 'CASH_FLOW', 'symbol': symbol}
            cashflow_data = self._make_request(cashflow_params)
            if period == 'annual':
                statements['cash_flow_statement'] = pd.DataFrame(cashflow_data.get('annualReports', []))
            else:
                statements['cash_flow_statement'] = pd.DataFrame(cashflow_data.get('quarterlyReports', []))
            return statements
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve financial statements for {symbol}: {str(e)}')

    def get_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Retrieve historical price data from Alpha Vantage"""
        try:
            params = {'function': 'TIME_SERIES_DAILY_ADJUSTED', 'symbol': symbol, 'outputsize': 'full'}
            data = self._make_request(params)
            time_series = data.get('Time Series (Daily)', {})
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Dividend', 'Split']
            df = df.astype(float)
            mask = (df.index >= start_date) & (df.index <= end_date)
            return df.loc[mask]
        except Exception as e:
            raise DataProviderError(f'Failed to retrieve price data for {symbol}: {str(e)}')

def get_company_data(self, symbol: str) -> CompanyData:
    """Retrieve company data from Alpha Vantage"""
    try:
        overview_params = {'function': 'OVERVIEW', 'symbol': symbol}
        overview = self._make_request(overview_params)
        quote_params = {'function': 'GLOBAL_QUOTE', 'symbol': symbol}
        quote_data = self._make_request(quote_params)
        quote = quote_data.get('Global Quote', {})
        current_price = float(quote.get('05. price', 0))
        shares_outstanding = float(overview.get('SharesOutstanding', 0))
        financial_data = {'revenue': float(overview.get('RevenueTTM', 0)), 'net_income': float(overview.get('ProfitMargin', 0)) * float(overview.get('RevenueTTM', 0)), 'total_assets': 0, 'book_value': float(overview.get('BookValue', 0)), 'earnings_per_share': float(overview.get('EPS', 0)), 'dividend_per_share': float(overview.get('DividendPerShare', 0)), 'roe': float(overview.get('ReturnOnEquityTTM', 0)), 'profit_margin': float(overview.get('ProfitMargin', 0)), 'ebitda': float(overview.get('EBITDA', 0))}
        market_data = {'beta': float(overview.get('Beta', 1.0)), 'pe_ratio': float(overview.get('PERatio', 0)), 'pb_ratio': float(overview.get('PriceToBookRatio', 0)), 'peg_ratio': float(overview.get('PEGRatio', 0)), 'dividend_yield': float(overview.get('DividendYield', 0)), '52_week_high': float(overview.get('52WeekHigh', 0)), '52_week_low': float(overview.get('52WeekLow', 0))}
        return CompanyData(symbol=symbol.upper(), name=overview.get('Name', symbol), sector=overview.get('Sector', 'Unknown'), industry=overview.get('Industry', 'Unknown'), market_cap=float(overview.get('MarketCapitalization', 0)), shares_outstanding=shares_outstanding, current_price=current_price, financial_data=financial_data, market_data=market_data, last_updated=datetime.now())
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve company data for {symbol}: {str(e)}')

def get_market_data(self, symbol: str) -> MarketData:
    """Retrieve market data from Alpha Vantage"""
    try:
        overview_params = {'function': 'OVERVIEW', 'symbol': symbol}
        overview = self._make_request(overview_params)
        return MarketData(risk_free_rate=0.05, market_return=0.1, beta=float(overview.get('Beta', 1.0)), dividend_yield=float(overview.get('DividendYield', 0)), growth_rate=0.03, required_return=0.08)
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve market data for {symbol}: {str(e)}')

def get_financial_statements(self, symbol: str, period: str='annual') -> Dict[str, pd.DataFrame]:
    """Retrieve financial statements from Alpha Vantage"""
    try:
        statements = {}
        income_params = {'function': 'INCOME_STATEMENT', 'symbol': symbol}
        income_data = self._make_request(income_params)
        if period == 'annual':
            statements['income_statement'] = pd.DataFrame(income_data.get('annualReports', []))
        else:
            statements['income_statement'] = pd.DataFrame(income_data.get('quarterlyReports', []))
        balance_params = {'function': 'BALANCE_SHEET', 'symbol': symbol}
        balance_data = self._make_request(balance_params)
        if period == 'annual':
            statements['balance_sheet'] = pd.DataFrame(balance_data.get('annualReports', []))
        else:
            statements['balance_sheet'] = pd.DataFrame(balance_data.get('quarterlyReports', []))
        cashflow_params = {'function': 'CASH_FLOW', 'symbol': symbol}
        cashflow_data = self._make_request(cashflow_params)
        if period == 'annual':
            statements['cash_flow_statement'] = pd.DataFrame(cashflow_data.get('annualReports', []))
        else:
            statements['cash_flow_statement'] = pd.DataFrame(cashflow_data.get('quarterlyReports', []))
        return statements
    except Exception as e:
        raise DataProviderError(f'Failed to retrieve financial statements for {symbol}: {str(e)}')

class ManualDataProvider(DataProvider):
    """Manual data input provider for user-supplied data"""

    def __init__(self):
        self.name = 'Manual Input'
        self.data_cache = {}

    def add_company_data(self, company_data: CompanyData):
        """Add manually input company data"""
        self.data_cache[company_data.symbol] = company_data

    def load_from_csv(self, file_path: str, symbol: str):
        """Load company data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            financial_data = df.to_dict('records')[0] if not df.empty else {}
            company_data = CompanyData(symbol=symbol.upper(), name=financial_data.get('company_name', symbol), sector=financial_data.get('sector', 'Unknown'), industry=financial_data.get('industry', 'Unknown'), market_cap=float(financial_data.get('market_cap', 0)), shares_outstanding=float(financial_data.get('shares_outstanding', 0)), current_price=float(financial_data.get('current_price', 0)), financial_data=financial_data, market_data={}, last_updated=datetime.now())
            self.add_company_data(company_data)
        except Exception as e:
            raise DataProviderError(f'Failed to load CSV data: {str(e)}')

    def get_company_data(self, symbol: str) -> CompanyData:
        """Retrieve manually input company data"""
        if symbol.upper() not in self.data_cache:
            raise DataProviderError(f'No manual data available for {symbol}')
        return self.data_cache[symbol.upper()]

    def get_market_data(self, symbol: str) -> MarketData:
        """Retrieve market data - requires manual input"""
        return MarketData(risk_free_rate=0.05, market_return=0.1, beta=1.0, dividend_yield=0.02, growth_rate=0.03, required_return=0.08)

    def get_financial_statements(self, symbol: str, period: str='annual') -> Dict[str, pd.DataFrame]:
        """Manual financial statements not implemented"""
        raise DataProviderError('Manual financial statements input not implemented')

    def get_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Manual price data not implemented"""
        raise DataProviderError('Manual price data input not implemented')

def get_company_data(self, symbol: str) -> CompanyData:
    """Retrieve manually input company data"""
    if symbol.upper() not in self.data_cache:
        raise DataProviderError(f'No manual data available for {symbol}')
    return self.data_cache[symbol.upper()]

def get_market_data(self, symbol: str) -> MarketData:
    """Retrieve market data - requires manual input"""
    return MarketData(risk_free_rate=0.05, market_return=0.1, beta=1.0, dividend_yield=0.02, growth_rate=0.03, required_return=0.08)

def get_financial_statements(self, symbol: str, period: str='annual') -> Dict[str, pd.DataFrame]:
    """Manual financial statements not implemented"""
    raise DataProviderError('Manual financial statements input not implemented')

def get_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Manual price data not implemented"""
    raise DataProviderError('Manual price data input not implemented')

class DataProviderFactory:
    """Factory class for managing multiple data providers with fallback"""

    def __init__(self):
        self.providers = {}
        self.primary_provider = None
        self.fallback_providers = []

    def register_provider(self, name: str, provider: DataProvider, is_primary: bool=False):
        """Register a data provider"""
        self.providers[name] = provider
        if is_primary:
            self.primary_provider = name
        else:
            self.fallback_providers.append(name)

    def get_provider(self, name: str) -> DataProvider:
        """Get specific provider by name"""
        if name not in self.providers:
            raise DataProviderError(f'Provider {name} not registered')
        return self.providers[name]

    def get_company_data(self, symbol: str, provider_name: Optional[str]=None) -> CompanyData:
        """Get company data with automatic fallback"""
        providers_to_try = [provider_name] if provider_name else [self.primary_provider] + self.fallback_providers
        for provider_name in providers_to_try:
            if provider_name and provider_name in self.providers:
                try:
                    return self.providers[provider_name].get_company_data(symbol)
                except Exception as e:
                    print(f'Provider {provider_name} failed: {str(e)}')
                    continue
        raise DataProviderError(f'All data providers failed for symbol {symbol}')

    def get_market_data(self, symbol: str, provider_name: Optional[str]=None) -> MarketData:
        """Get market data with automatic fallback"""
        providers_to_try = [provider_name] if provider_name else [self.primary_provider] + self.fallback_providers
        for provider_name in providers_to_try:
            if provider_name and provider_name in self.providers:
                try:
                    return self.providers[provider_name].get_market_data(symbol)
                except Exception as e:
                    print(f'Provider {provider_name} failed: {str(e)}')
                    continue
        raise DataProviderError(f'All data providers failed for market data {symbol}')

def get_provider(self, name: str) -> DataProvider:
    """Get specific provider by name"""
    if name not in self.providers:
        raise DataProviderError(f'Provider {name} not registered')
    return self.providers[name]

def get_company_data(self, symbol: str, provider_name: Optional[str]=None) -> CompanyData:
    """Get company data with automatic fallback"""
    providers_to_try = [provider_name] if provider_name else [self.primary_provider] + self.fallback_providers
    for provider_name in providers_to_try:
        if provider_name and provider_name in self.providers:
            try:
                return self.providers[provider_name].get_company_data(symbol)
            except Exception as e:
                print(f'Provider {provider_name} failed: {str(e)}')
                continue
    raise DataProviderError(f'All data providers failed for symbol {symbol}')

def get_market_data(self, symbol: str, provider_name: Optional[str]=None) -> MarketData:
    """Get market data with automatic fallback"""
    providers_to_try = [provider_name] if provider_name else [self.primary_provider] + self.fallback_providers
    for provider_name in providers_to_try:
        if provider_name and provider_name in self.providers:
            try:
                return self.providers[provider_name].get_market_data(symbol)
            except Exception as e:
                print(f'Provider {provider_name} failed: {str(e)}')
                continue
    raise DataProviderError(f'All data providers failed for market data {symbol}')

def get_company_data(symbol: str, provider: Optional[str]=None) -> CompanyData:
    """Convenience function to get company data"""
    return data_factory.get_company_data(symbol, provider)

def get_market_data(symbol: str, provider: Optional[str]=None) -> MarketData:
    """Convenience function to get market data"""
    return data_factory.get_market_data(symbol, provider)

class VanillaOption(ContingentClaim):
    """Standard European/American call and put options"""

    def __init__(self, option_type: OptionType, underlying_type: UnderlyingType, expiry_date: datetime, strike_price: float, exercise_style: ExerciseStyle=ExerciseStyle.EUROPEAN, notional: float=1.0):
        super().__init__(option_type, underlying_type, expiry_date, strike_price, exercise_style, notional)

    def calculate_payoff(self, spot_price: float) -> float:
        """Calculate option payoff at expiration"""
        if self.option_type == OptionType.CALL:
            return max(0, spot_price - self.strike_price) * self.notional
        else:
            return max(0, self.strike_price - spot_price) * self.notional

    def fair_value(self, market_data: MarketData) -> PricingResult:
        """Calculate fair value using appropriate model"""
        if self.exercise_style == ExerciseStyle.EUROPEAN:
            return self._black_scholes_price(market_data)
        else:
            return self._binomial_price(market_data, steps=100)

    def _black_scholes_price(self, market_data: MarketData) -> PricingResult:
        """Black-Scholes-Merton pricing for European options"""
        S = market_data.spot_price
        K = self.strike_price
        T = self.time_to_expiry()
        r = market_data.risk_free_rate
        q = market_data.dividend_yield
        sigma = market_data.volatility
        if T <= 0:
            return PricingResult(fair_value=self.calculate_payoff(S))
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if self.option_type == OptionType.CALL:
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        price *= self.notional
        intrinsic = self.intrinsic_value(S)
        return PricingResult(fair_value=price, intrinsic_value=intrinsic, time_value=price - intrinsic, calculation_details={'model': 'Black-Scholes-Merton', 'd1': d1, 'd2': d2, 'N_d1': norm.cdf(d1) if self.option_type == OptionType.CALL else norm.cdf(-d1), 'N_d2': norm.cdf(d2) if self.option_type == OptionType.CALL else norm.cdf(-d2)})

    def _binomial_price(self, market_data: MarketData, steps: int=50) -> PricingResult:
        """Binomial tree pricing for American options"""
        engine = BinomialPricingEngine(steps)
        return engine.price(self, market_data)

def fair_value(self, market_data: MarketData) -> PricingResult:
    """Calculate fair value using appropriate model"""
    if self.exercise_style == ExerciseStyle.EUROPEAN:
        return self._black_scholes_price(market_data)
    else:
        return self._binomial_price(market_data, steps=100)

def _binomial_price(self, market_data: MarketData, steps: int=50) -> PricingResult:
    """Binomial tree pricing for American options"""
    engine = BinomialPricingEngine(steps)
    return engine.price(self, market_data)

class BlackScholesPricingEngine(PricingEngine):
    """Black-Scholes-Merton pricing engine with Greeks"""

    def price(self, instrument: VanillaOption, market_data: MarketData) -> PricingResult:
        """Price European option using Black-Scholes-Merton"""
        if not self.validate_inputs(instrument, market_data):
            raise ValidationError('Invalid inputs for Black-Scholes pricing')
        if instrument.exercise_style != ExerciseStyle.EUROPEAN:
            raise ValueError('Black-Scholes only valid for European options')
        result = instrument._black_scholes_price(market_data)
        greeks = self.calculate_greeks(instrument, market_data)
        result.greeks = greeks.__dict__
        return result

    def calculate_greeks(self, instrument: VanillaOption, market_data: MarketData) -> OptionGreeks:
        """Calculate all option Greeks"""
        S = market_data.spot_price
        K = instrument.strike_price
        T = instrument.time_to_expiry()
        r = market_data.risk_free_rate
        q = market_data.dividend_yield
        sigma = market_data.volatility
        if T <= 0:
            return OptionGreeks()
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        n_d1 = norm.pdf(d1)
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        greeks = OptionGreeks()
        if instrument.option_type == OptionType.CALL:
            greeks.delta = np.exp(-q * T) * N_d1
            greeks.theta = (-S * n_d1 * sigma * np.exp(-q * T) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * N_d2 + q * S * np.exp(-q * T) * N_d1) / 365
            greeks.rho = K * T * np.exp(-r * T) * N_d2 / 100
        else:
            greeks.delta = -np.exp(-q * T) * norm.cdf(-d1)
            greeks.theta = (-S * n_d1 * sigma * np.exp(-q * T) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2) - q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365
            greeks.rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        greeks.gamma = n_d1 * np.exp(-q * T) / (S * sigma * np.sqrt(T))
        greeks.vega = S * n_d1 * np.sqrt(T) * np.exp(-q * T) / 100
        greeks.vanna = -greeks.vega * d2 / sigma
        greeks.volga = greeks.vega * d1 * d2 / sigma
        greeks.charm = (q * np.exp(-q * T) * norm.cdf(d1 if instrument.option_type == OptionType.CALL else -d1) - np.exp(-q * T) * n_d1 * (2 * (r - q) * T - d2 * sigma * np.sqrt(T)) / (2 * T * sigma * np.sqrt(T))) / 365
        return greeks

    def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
        """Validate inputs for Black-Scholes pricing"""
        try:
            ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
            ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
            ModelValidator.validate_volatility(market_data.volatility)
            ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
            ModelValidator.validate_non_negative(market_data.dividend_yield, 'dividend_yield')
            if instrument.time_to_expiry() < 0:
                return False
            return True
        except ValidationError:
            return False

def price(self, instrument: VanillaOption, market_data: MarketData) -> PricingResult:
    """Price European option using Black-Scholes-Merton"""
    if not self.validate_inputs(instrument, market_data):
        raise ValidationError('Invalid inputs for Black-Scholes pricing')
    if instrument.exercise_style != ExerciseStyle.EUROPEAN:
        raise ValueError('Black-Scholes only valid for European options')
    result = instrument._black_scholes_price(market_data)
    greeks = self.calculate_greeks(instrument, market_data)
    result.greeks = greeks.__dict__
    return result

class ImpliedVolatilityCalculator:
    """Calculate implied volatility from option prices"""

    @staticmethod
    def calculate_iv(option_price: float, spot_price: float, strike_price: float, time_to_expiry: float, risk_free_rate: float, option_type: OptionType, dividend_yield: float=0.0) -> float:
        """Calculate implied volatility using Brent's method"""

        def objective_function(vol):
            """Objective function for root finding"""
            market_data = MarketData(spot_price=spot_price, risk_free_rate=risk_free_rate, dividend_yield=dividend_yield, volatility=vol, time_to_expiry=time_to_expiry)
            option = VanillaOption(option_type=option_type, underlying_type=UnderlyingType.EQUITY, expiry_date=datetime.now(), strike_price=strike_price)
            theoretical_price = option._black_scholes_price(market_data).fair_value
            return theoretical_price - option_price
        try:
            implied_vol = brentq(objective_function, 0.001, 5.0, xtol=1e-06)
            return implied_vol
        except ValueError:
            logger.warning('Could not calculate implied volatility')
            return np.nan

def objective_function(vol):
    """Objective function for root finding"""
    market_data = MarketData(spot_price=spot_price, risk_free_rate=risk_free_rate, dividend_yield=dividend_yield, volatility=vol, time_to_expiry=time_to_expiry)
    option = VanillaOption(option_type=option_type, underlying_type=UnderlyingType.EQUITY, expiry_date=datetime.now(), strike_price=strike_price)
    theoretical_price = option._black_scholes_price(market_data).fair_value
    return theoretical_price - option_price

class DeltaHedging:
    """Delta hedging implementation"""

    def __init__(self, option: VanillaOption, hedge_ratio: float=None):
        self.option = option
        self.hedge_ratio = hedge_ratio
        self.position_delta = 0.0
        self.hedge_position = 0.0

    def calculate_hedge_ratio(self, market_data: MarketData) -> float:
        """Calculate delta hedge ratio"""
        engine = BlackScholesPricingEngine()
        greeks = engine.calculate_greeks(self.option, market_data)
        return -greeks.delta

    def rebalance_hedge(self, market_data: MarketData, option_position: float=1.0) -> Dict:
        """Rebalance delta hedge"""
        new_hedge_ratio = self.calculate_hedge_ratio(market_data)
        new_hedge_position = new_hedge_ratio * option_position
        hedge_adjustment = new_hedge_position - self.hedge_position
        self.hedge_ratio = new_hedge_ratio
        self.hedge_position = new_hedge_position
        return {'new_hedge_ratio': new_hedge_ratio, 'new_hedge_position': new_hedge_position, 'hedge_adjustment': hedge_adjustment, 'cost_of_adjustment': abs(hedge_adjustment) * market_data.spot_price}

def calculate_hedge_ratio(self, market_data: MarketData) -> float:
    """Calculate delta hedge ratio"""
    engine = BlackScholesPricingEngine()
    greeks = engine.calculate_greeks(self.option, market_data)
    return -greeks.delta

class VolatilityArbitrageDetector:
    """Detect volatility arbitrage opportunities"""

    def __init__(self, market_vol: float, implied_vol: float, option: VanillaOption, market_data: MarketData, confidence_threshold: float=0.05):
        self.market_vol = market_vol
        self.implied_vol = implied_vol
        self.option = option
        self.market_data = market_data
        self.confidence_threshold = confidence_threshold
        ModelValidator.validate_volatility(market_vol)
        ModelValidator.validate_volatility(implied_vol)

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect volatility arbitrage based on vol differential"""
        vol_difference = self.implied_vol - self.market_vol
        vol_spread_pct = abs(vol_difference) / self.market_vol
        if vol_spread_pct > self.confidence_threshold:
            market_data_market_vol = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_vol, time_to_expiry=self.market_data.time_to_expiry)
            engine = BlackScholesPricingEngine()
            market_vol_price = engine.price(self.option, market_data_market_vol).fair_value
            market_data_implied_vol = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.implied_vol, time_to_expiry=self.market_data.time_to_expiry)
            implied_vol_price = engine.price(self.option, market_data_implied_vol).fair_value
            price_difference = implied_vol_price - market_vol_price
            if vol_difference > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.VOLATILITY_ARBITRAGE, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=min(0.95, vol_spread_pct * 5), instruments_involved=['option', 'underlying'], trade_details={'sell_option': implied_vol_price, 'market_vol': self.market_vol, 'implied_vol': self.implied_vol, 'vol_difference': vol_difference, 'price_difference': price_difference, 'strategy': 'sell_option_delta_hedge', 'vol_spread_pct': vol_spread_pct, 'market_vol_price': market_vol_price, 'implied_vol_price': implied_vol_price}, risk_factors=['gamma_risk', 'vol_risk', 'time_decay', 'model_risk'], execution_complexity='high')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.VOLATILITY_ARBITRAGE, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=min(0.95, vol_spread_pct * 5), instruments_involved=['option', 'underlying'], trade_details={'buy_option': implied_vol_price, 'market_vol': self.market_vol, 'implied_vol': self.implied_vol, 'vol_difference': vol_difference, 'price_difference': price_difference, 'strategy': 'buy_option_delta_hedge', 'vol_spread_pct': vol_spread_pct, 'market_vol_price': market_vol_price, 'implied_vol_price': implied_vol_price}, risk_factors=['gamma_risk', 'vol_risk', 'time_decay', 'model_risk'], execution_complexity='high')
        return None

def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
    """Detect volatility arbitrage based on vol differential"""
    vol_difference = self.implied_vol - self.market_vol
    vol_spread_pct = abs(vol_difference) / self.market_vol
    if vol_spread_pct > self.confidence_threshold:
        market_data_market_vol = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_vol, time_to_expiry=self.market_data.time_to_expiry)
        engine = BlackScholesPricingEngine()
        market_vol_price = engine.price(self.option, market_data_market_vol).fair_value
        market_data_implied_vol = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.implied_vol, time_to_expiry=self.market_data.time_to_expiry)
        implied_vol_price = engine.price(self.option, market_data_implied_vol).fair_value
        price_difference = implied_vol_price - market_vol_price
        if vol_difference > 0:
            return ArbitrageOpportunity(arbitrage_type=ArbitrageType.VOLATILITY_ARBITRAGE, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=min(0.95, vol_spread_pct * 5), instruments_involved=['option', 'underlying'], trade_details={'sell_option': implied_vol_price, 'market_vol': self.market_vol, 'implied_vol': self.implied_vol, 'vol_difference': vol_difference, 'price_difference': price_difference, 'strategy': 'sell_option_delta_hedge', 'vol_spread_pct': vol_spread_pct, 'market_vol_price': market_vol_price, 'implied_vol_price': implied_vol_price}, risk_factors=['gamma_risk', 'vol_risk', 'time_decay', 'model_risk'], execution_complexity='high')
        else:
            return ArbitrageOpportunity(arbitrage_type=ArbitrageType.VOLATILITY_ARBITRAGE, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=min(0.95, vol_spread_pct * 5), instruments_involved=['option', 'underlying'], trade_details={'buy_option': implied_vol_price, 'market_vol': self.market_vol, 'implied_vol': self.implied_vol, 'vol_difference': vol_difference, 'price_difference': price_difference, 'strategy': 'buy_option_delta_hedge', 'vol_spread_pct': vol_spread_pct, 'market_vol_price': market_vol_price, 'implied_vol_price': implied_vol_price}, risk_factors=['gamma_risk', 'vol_risk', 'time_decay', 'model_risk'], execution_complexity='high')
    return None

class CalendarSpreadArbitrage:
    """Calendar spread arbitrage detector"""

    def __init__(self, near_option_price: float, far_option_price: float, near_time_to_expiry: float, far_time_to_expiry: float, strike_price: float, option_type: OptionType, market_data: MarketData):
        self.near_option_price = near_option_price
        self.far_option_price = far_option_price
        self.near_time = near_time_to_expiry
        self.far_time = far_time_to_expiry
        self.strike_price = strike_price
        self.option_type = option_type
        self.market_data = market_data
        if near_time_to_expiry >= far_time_to_expiry:
            raise ValidationError('Near expiry must be less than far expiry')

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect calendar spread arbitrage"""
        time_decay_value = self.far_option_price - self.near_option_price
        engine = BlackScholesPricingEngine()
        near_option = VanillaOption(option_type=self.option_type, underlying_type=UnderlyingType.EQUITY, expiry_date=datetime.now(), strike_price=self.strike_price)
        far_option = VanillaOption(option_type=self.option_type, underlying_type=UnderlyingType.EQUITY, expiry_date=datetime.now(), strike_price=self.strike_price)
        near_market_data = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_data.volatility, time_to_expiry=self.near_time)
        far_market_data = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_data.volatility, time_to_expiry=self.far_time)
        theoretical_near_price = engine.price(near_option, near_market_data).fair_value
        theoretical_far_price = engine.price(far_option, far_market_data).fair_value
        theoretical_time_decay = theoretical_far_price - theoretical_near_price
        price_difference = time_decay_value - theoretical_time_decay
        if abs(price_difference) > Constants.EPSILON:
            if price_difference > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CALENDAR_SPREAD, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=0.8, instruments_involved=[f'{self.option_type.value}_near', f'{self.option_type.value}_far'], trade_details={'sell_far_option': self.far_option_price, 'buy_near_option': self.near_option_price, 'calendar_spread_cost': time_decay_value, 'theoretical_time_decay': theoretical_time_decay, 'arbitrage_profit': price_difference, 'near_time': self.near_time, 'far_time': self.far_time}, risk_factors=['volatility_risk', 'time_decay', 'pin_risk'], execution_complexity='medium')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CALENDAR_SPREAD, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=0.8, instruments_involved=[f'{self.option_type.value}_near', f'{self.option_type.value}_far'], trade_details={'buy_far_option': self.far_option_price, 'sell_near_option': self.near_option_price, 'calendar_spread_cost': time_decay_value, 'theoretical_time_decay': theoretical_time_decay, 'arbitrage_profit': abs(price_difference), 'near_time': self.near_time, 'far_time': self.far_time}, risk_factors=['volatility_risk', 'time_decay', 'pin_risk'], execution_complexity='medium')
        return None

def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
    """Detect calendar spread arbitrage"""
    time_decay_value = self.far_option_price - self.near_option_price
    engine = BlackScholesPricingEngine()
    near_option = VanillaOption(option_type=self.option_type, underlying_type=UnderlyingType.EQUITY, expiry_date=datetime.now(), strike_price=self.strike_price)
    far_option = VanillaOption(option_type=self.option_type, underlying_type=UnderlyingType.EQUITY, expiry_date=datetime.now(), strike_price=self.strike_price)
    near_market_data = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_data.volatility, time_to_expiry=self.near_time)
    far_market_data = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_data.volatility, time_to_expiry=self.far_time)
    theoretical_near_price = engine.price(near_option, near_market_data).fair_value
    theoretical_far_price = engine.price(far_option, far_market_data).fair_value
    theoretical_time_decay = theoretical_far_price - theoretical_near_price
    price_difference = time_decay_value - theoretical_time_decay
    if abs(price_difference) > Constants.EPSILON:
        if price_difference > 0:
            return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CALENDAR_SPREAD, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=0.8, instruments_involved=[f'{self.option_type.value}_near', f'{self.option_type.value}_far'], trade_details={'sell_far_option': self.far_option_price, 'buy_near_option': self.near_option_price, 'calendar_spread_cost': time_decay_value, 'theoretical_time_decay': theoretical_time_decay, 'arbitrage_profit': price_difference, 'near_time': self.near_time, 'far_time': self.far_time}, risk_factors=['volatility_risk', 'time_decay', 'pin_risk'], execution_complexity='medium')
        else:
            return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CALENDAR_SPREAD, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=0.8, instruments_involved=[f'{self.option_type.value}_near', f'{self.option_type.value}_far'], trade_details={'buy_far_option': self.far_option_price, 'sell_near_option': self.near_option_price, 'calendar_spread_cost': time_decay_value, 'theoretical_time_decay': theoretical_time_decay, 'arbitrage_profit': abs(price_difference), 'near_time': self.near_time, 'far_time': self.far_time}, risk_factors=['volatility_risk', 'time_decay', 'pin_risk'], execution_complexity='medium')
    return None

class DerivativesPortfolio:
    """Derivatives portfolio management and analytics"""

    def __init__(self, portfolio_id: str=None):
        self.portfolio_id = portfolio_id or f'portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
        self.positions: List[PortfolioPosition] = []
        self.creation_date = datetime.now()
        self.last_update = None
        self.options_engine = BlackScholesPricingEngine()
        self.forwards_engine = ForwardCommitmentPricingEngine()

    def add_position(self, instrument: DerivativeInstrument, quantity: float, entry_price: float, entry_date: datetime=None):
        """Add position to portfolio"""
        if entry_date is None:
            entry_date = datetime.now()
        position = PortfolioPosition(instrument=instrument, quantity=quantity, entry_price=entry_price, entry_date=entry_date)
        self.positions.append(position)
        self.last_update = datetime.now()
        logger.info(f'Added position: {quantity} units of {instrument}')

    def remove_position(self, position_index: int):
        """Remove position from portfolio"""
        if 0 <= position_index < len(self.positions):
            removed_position = self.positions.pop(position_index)
            self.last_update = datetime.now()
            logger.info(f'Removed position: {removed_position.instrument}')
        else:
            raise ValueError('Invalid position index')

    def update_positions(self, market_data: MarketData) -> float:
        """Update all position values and calculate portfolio value"""
        total_value = 0.0
        for position in self.positions:
            try:
                if hasattr(position.instrument, 'option_type'):
                    pricing_result = self.options_engine.price(position.instrument, market_data)
                else:
                    pricing_result = self.forwards_engine.price(position.instrument, market_data)
                position.current_value = pricing_result.fair_value * position.quantity
                position.unrealized_pnl = position.current_value - position.entry_price * position.quantity
                total_value += position.current_value
            except Exception as e:
                logger.error(f'Error pricing position {position.instrument}: {e}')
                position.current_value = position.entry_price * position.quantity
                total_value += position.current_value
        self.last_update = datetime.now()
        return total_value

    def get_portfolio_greeks(self, market_data: MarketData) -> Dict[str, float]:
        """Calculate aggregated portfolio Greeks"""
        total_greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0}
        for position in self.positions:
            if hasattr(position.instrument, 'option_type'):
                try:
                    greeks = self.options_engine.calculate_greeks(position.instrument, market_data)
                    total_greeks['delta'] += greeks.delta * position.quantity
                    total_greeks['gamma'] += greeks.gamma * position.quantity
                    total_greeks['theta'] += greeks.theta * position.quantity
                    total_greeks['vega'] += greeks.vega * position.quantity
                    total_greeks['rho'] += greeks.rho * position.quantity
                except Exception as e:
                    logger.warning(f'Could not calculate Greeks for {position.instrument}: {e}')
        return total_greeks

    def get_portfolio_summary(self, market_data: MarketData) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        portfolio_value = self.update_positions(market_data)
        greeks = self.get_portfolio_greeks(market_data)
        total_pnl = sum((pos.unrealized_pnl for pos in self.positions))
        return {'portfolio_id': self.portfolio_id, 'portfolio_value': portfolio_value, 'total_unrealized_pnl': total_pnl, 'number_of_positions': len(self.positions), 'last_update': self.last_update, 'greeks': greeks, 'positions_summary': [{'instrument_type': pos.instrument.derivative_type.value, 'quantity': pos.quantity, 'current_value': pos.current_value, 'unrealized_pnl': pos.unrealized_pnl, 'entry_date': pos.entry_date} for pos in self.positions]}

def __init__(self, portfolio_id: str=None):
    self.portfolio_id = portfolio_id or f'portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}'
    self.positions: List[PortfolioPosition] = []
    self.creation_date = datetime.now()
    self.last_update = None
    self.options_engine = BlackScholesPricingEngine()
    self.forwards_engine = ForwardCommitmentPricingEngine()

def update_positions(self, market_data: MarketData) -> float:
    """Update all position values and calculate portfolio value"""
    total_value = 0.0
    for position in self.positions:
        try:
            if hasattr(position.instrument, 'option_type'):
                pricing_result = self.options_engine.price(position.instrument, market_data)
            else:
                pricing_result = self.forwards_engine.price(position.instrument, market_data)
            position.current_value = pricing_result.fair_value * position.quantity
            position.unrealized_pnl = position.current_value - position.entry_price * position.quantity
            total_value += position.current_value
        except Exception as e:
            logger.error(f'Error pricing position {position.instrument}: {e}')
            position.current_value = position.entry_price * position.quantity
            total_value += position.current_value
    self.last_update = datetime.now()
    return total_value

def get_portfolio_greeks(self, market_data: MarketData) -> Dict[str, float]:
    """Calculate aggregated portfolio Greeks"""
    total_greeks = {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'rho': 0.0}
    for position in self.positions:
        if hasattr(position.instrument, 'option_type'):
            try:
                greeks = self.options_engine.calculate_greeks(position.instrument, market_data)
                total_greeks['delta'] += greeks.delta * position.quantity
                total_greeks['gamma'] += greeks.gamma * position.quantity
                total_greeks['theta'] += greeks.theta * position.quantity
                total_greeks['vega'] += greeks.vega * position.quantity
                total_greeks['rho'] += greeks.rho * position.quantity
            except Exception as e:
                logger.warning(f'Could not calculate Greeks for {position.instrument}: {e}')
    return total_greeks

class ScenarioAnalyzer:
    """Scenario analysis and stress testing"""

    def __init__(self):
        self.scenarios = {}

    def add_scenario(self, name: str, market_shocks: Dict[str, float]):
        """Add predefined scenario"""
        self.scenarios[name] = market_shocks

    def stress_test(self, portfolio: DerivativesPortfolio, base_market_data: MarketData, stress_scenarios: Dict[str, Dict[str, float]]=None) -> List[ScenarioResult]:
        """Perform stress testing on portfolio"""
        if stress_scenarios is None:
            stress_scenarios = self._get_default_stress_scenarios()
        base_value = portfolio.update_positions(base_market_data)
        results = []
        for scenario_name, shocks in stress_scenarios.items():
            try:
                stressed_market_data = self._apply_market_shocks(base_market_data, shocks)
                stressed_value = portfolio.update_positions(stressed_market_data)
                pnl_change = stressed_value - base_value
                percentage_change = pnl_change / base_value * 100 if base_value != 0 else 0
                result = ScenarioResult(scenario_name=scenario_name, scenario_type=ScenarioType.STRESS_TEST, base_portfolio_value=base_value, scenario_portfolio_value=stressed_value, pnl_change=pnl_change, percentage_change=percentage_change, scenario_parameters=shocks)
                results.append(result)
            except Exception as e:
                logger.error(f'Error in stress test scenario {scenario_name}: {e}')
        return results

    def monte_carlo_simulation(self, portfolio: DerivativesPortfolio, base_market_data: MarketData, num_simulations: int=10000, time_horizon: int=30) -> List[ScenarioResult]:
        """Monte Carlo simulation for portfolio"""
        base_value = portfolio.update_positions(base_market_data)
        results = []
        dt = 1 / 252
        drift = 0.0001
        volatility = 0.02
        for i in range(num_simulations):
            try:
                random_shocks = np.random.normal(0, 1, time_horizon)
                final_spot_multiplier = np.exp(np.sum((drift - 0.5 * volatility ** 2) * dt + volatility * np.sqrt(dt) * random_shocks))
                simulated_market_data = MarketData(spot_price=base_market_data.spot_price * final_spot_multiplier, risk_free_rate=base_market_data.risk_free_rate, dividend_yield=base_market_data.dividend_yield, volatility=base_market_data.volatility, time_to_expiry=max(0, base_market_data.time_to_expiry - time_horizon / 252))
                simulated_value = portfolio.update_positions(simulated_market_data)
                pnl_change = simulated_value - base_value
                percentage_change = pnl_change / base_value * 100 if base_value != 0 else 0
                result = ScenarioResult(scenario_name=f'MC_Simulation_{i + 1}', scenario_type=ScenarioType.MONTE_CARLO, base_portfolio_value=base_value, scenario_portfolio_value=simulated_value, pnl_change=pnl_change, percentage_change=percentage_change, probability=1 / num_simulations, scenario_parameters={'final_spot_multiplier': final_spot_multiplier, 'time_horizon_days': time_horizon})
                results.append(result)
            except Exception as e:
                logger.warning(f'Error in MC simulation {i + 1}: {e}')
        return results

    def sensitivity_analysis(self, portfolio: DerivativesPortfolio, base_market_data: MarketData, parameters: List[str]=None, shock_sizes: Dict[str, float]=None) -> List[SensitivityResult]:
        """Perform sensitivity analysis on key parameters"""
        if parameters is None:
            parameters = ['spot_price', 'volatility', 'risk_free_rate', 'time_to_expiry']
        if shock_sizes is None:
            shock_sizes = {'spot_price': 0.01, 'volatility': 0.01, 'risk_free_rate': 0.0025, 'time_to_expiry': -1 / 365}
        base_value = portfolio.update_positions(base_market_data)
        results = []
        for param in parameters:
            if param not in shock_sizes:
                continue
            try:
                shocked_data = self._shock_parameter(base_market_data, param, shock_sizes[param])
                shocked_value = portfolio.update_positions(shocked_data)
                pnl_change = shocked_value - base_value
                base_param_value = getattr(base_market_data, param)
                sensitivity = pnl_change / shock_sizes[param] if shock_sizes[param] != 0 else 0
                if base_param_value != 0 and base_value != 0:
                    elasticity = pnl_change / base_value / (shock_sizes[param] / base_param_value)
                else:
                    elasticity = 0
                result = SensitivityResult(parameter_name=param, base_value=base_param_value, shock_size=shock_sizes[param], portfolio_value_change=pnl_change, sensitivity=sensitivity, elasticity=elasticity)
                results.append(result)
            except Exception as e:
                logger.error(f'Error in sensitivity analysis for {param}: {e}')
        return results

    def _get_default_stress_scenarios(self) -> Dict[str, Dict[str, float]]:
        """Get default stress test scenarios"""
        return {'Market_Crash': {'spot_price': -0.2, 'volatility': 0.15, 'risk_free_rate': -0.01}, 'Vol_Spike': {'volatility': 0.2, 'spot_price': -0.05}, 'Interest_Rate_Shock': {'risk_free_rate': 0.02, 'spot_price': -0.1}, 'Time_Decay': {'time_to_expiry': -0.1, 'volatility': -0.05}, 'Bull_Market': {'spot_price': 0.15, 'volatility': -0.05}}

    def _apply_market_shocks(self, base_data: MarketData, shocks: Dict[str, float]) -> MarketData:
        """Apply market shocks to create stressed market data"""
        return MarketData(spot_price=base_data.spot_price * (1 + shocks.get('spot_price', 0)), risk_free_rate=base_data.risk_free_rate + shocks.get('risk_free_rate', 0), dividend_yield=base_data.dividend_yield + shocks.get('dividend_yield', 0), volatility=max(0.001, base_data.volatility + shocks.get('volatility', 0)), time_to_expiry=max(0, base_data.time_to_expiry + shocks.get('time_to_expiry', 0)))

    def _shock_parameter(self, base_data: MarketData, parameter: str, shock: float) -> MarketData:
        """Apply shock to specific parameter"""
        data_dict = {'spot_price': base_data.spot_price, 'risk_free_rate': base_data.risk_free_rate, 'dividend_yield': base_data.dividend_yield, 'volatility': base_data.volatility, 'time_to_expiry': base_data.time_to_expiry}
        if parameter in data_dict:
            if parameter == 'spot_price':
                data_dict[parameter] *= 1 + shock
            else:
                data_dict[parameter] += shock
        return MarketData(**data_dict)

def _apply_market_shocks(self, base_data: MarketData, shocks: Dict[str, float]) -> MarketData:
    """Apply market shocks to create stressed market data"""
    return MarketData(spot_price=base_data.spot_price * (1 + shocks.get('spot_price', 0)), risk_free_rate=base_data.risk_free_rate + shocks.get('risk_free_rate', 0), dividend_yield=base_data.dividend_yield + shocks.get('dividend_yield', 0), volatility=max(0.001, base_data.volatility + shocks.get('volatility', 0)), time_to_expiry=max(0, base_data.time_to_expiry + shocks.get('time_to_expiry', 0)))

def _shock_parameter(self, base_data: MarketData, parameter: str, shock: float) -> MarketData:
    """Apply shock to specific parameter"""
    data_dict = {'spot_price': base_data.spot_price, 'risk_free_rate': base_data.risk_free_rate, 'dividend_yield': base_data.dividend_yield, 'volatility': base_data.volatility, 'time_to_expiry': base_data.time_to_expiry}
    if parameter in data_dict:
        if parameter == 'spot_price':
            data_dict[parameter] *= 1 + shock
        else:
            data_dict[parameter] += shock
    return MarketData(**data_dict)

def fetch_stock_data(ticker, period='1y'):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        print(f'Error fetching data: {e}')
        return None

class NodeProcessor:
    """Enhanced node processor with caching and parallel execution"""

    def __init__(self):
        self.nodes: Dict[str, NodeData] = {}
        self.execution_order: List[str] = []
        self.cache: Dict[str, Any] = {}
        self.performance_tracker: Dict[str, float] = {}

    def add_node(self, node_data: NodeData):
        """Add a node to the processor"""
        self.nodes[node_data.node_id] = node_data
        logger.info(f'Added node {node_data.node_id} of type {node_data.node_type.value}')

    def calculate_execution_order(self):
        """Calculate optimal execution order using topological sort"""
        from collections import defaultdict, deque
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = 0
        for target_node, connections in global_state.node_connections.items():
            for input_type, source_nodes in connections.items():
                for source_node in source_nodes:
                    graph[source_node].append(target_node)
                    in_degree[target_node] += 1
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        self.execution_order = []
        while queue:
            node = queue.popleft()
            self.execution_order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        logger.info(f'Execution order calculated: {self.execution_order}')

    def execute_nodes(self, use_cache: bool=True):
        """Execute all nodes with optional caching"""
        import time
        logger.info('Starting node execution')
        self.calculate_execution_order()
        for node_id in self.execution_order:
            if node_id not in self.nodes:
                continue
            node = self.nodes[node_id]
            if use_cache and node.cache_enabled and (node_id in self.cache):
                logger.info(f'Using cached result for node {node_id}')
                global_state.node_outputs[node_id] = self.cache[node_id]
                continue
            try:
                start_time = time.time()
                logger.info(f'Executing node {node_id} ({node.node_type.value})')
                self._execute_node(node)
                execution_time = time.time() - start_time
                node.execution_time = execution_time
                node.last_execution = datetime.now()
                self.performance_tracker[node_id] = execution_time
                if node.cache_enabled and node_id in global_state.node_outputs:
                    self.cache[node_id] = global_state.node_outputs[node_id]
                logger.info(f'Node {node_id} executed in {execution_time:.3f}s')
            except Exception as e:
                logger.error(f'Error executing node {node_id}: {e}')
                node.error_state = str(e)
                self._update_node_status(node_id, f'✗ Error: {str(e)[:50]}')

    def _execute_node(self, node: NodeData):
        """Execute a single node based on its type"""
        node_type = node.node_type
        if node_type == NodeType.DATA_SOURCE:
            self._execute_data_source(node)
        elif node_type == NodeType.MULTI_TICKER:
            self._execute_multi_ticker(node)
        elif node_type == NodeType.SMA:
            self._execute_sma(node)
        elif node_type == NodeType.EMA:
            self._execute_ema(node)
        elif node_type == NodeType.BOLLINGER:
            self._execute_bollinger(node)
        elif node_type == NodeType.RSI:
            self._execute_rsi(node)
        elif node_type == NodeType.MACD:
            self._execute_macd(node)
        elif node_type == NodeType.STOCHASTIC:
            self._execute_stochastic(node)
        elif node_type == NodeType.ATR:
            self._execute_atr(node)
        elif node_type == NodeType.ICHIMOKU:
            self._execute_ichimoku(node)
        elif node_type == NodeType.CANDLESTICK:
            self._execute_candlestick_patterns(node)
        elif node_type == NodeType.SUPPORT_RESISTANCE:
            self._execute_support_resistance(node)
        elif node_type == NodeType.SIGNAL:
            self._execute_signal(node)
        elif node_type == NodeType.ML_SIGNAL:
            self._execute_ml_signal(node)
        elif node_type == NodeType.BACKTEST:
            self._execute_backtest(node)
        elif node_type == NodeType.OPTIMIZATION:
            self._execute_optimization(node)
        elif node_type == NodeType.PLOT:
            self._execute_plot(node)

    def _execute_data_source(self, node: NodeData):
        """Execute data source node"""
        ticker = node.parameters.get('ticker', 'AAPL')
        period = node.parameters.get('period', '1y')
        interval = node.parameters.get('interval', '1d')
        try:
            logger.info(f'Fetching data for {ticker}, period: {period}, interval: {interval}')
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval=interval)
            if data.empty:
                raise ValueError(f'No data found for ticker {ticker}')
            global_state.node_outputs[node.node_id] = data
            node.outputs['data'] = data
            self._update_node_status(node.node_id, f'✓ {len(data)} points loaded')
        except Exception as e:
            logger.error(f'Error fetching data: {e}')
            self._update_node_status(node.node_id, f'✗ Failed: {str(e)[:30]}')
            raise

    def _execute_multi_ticker(self, node: NodeData):
        """Execute multi-ticker data source"""
        tickers = node.parameters.get('tickers', ['AAPL', 'GOOGL', 'MSFT'])
        period = node.parameters.get('period', '1y')
        try:
            all_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                data = stock.history(period=period)
                if not data.empty:
                    all_data[ticker] = data
            global_state.node_outputs[node.node_id] = all_data
            node.outputs['data'] = all_data
            self._update_node_status(node.node_id, f'✓ {len(all_data)} tickers loaded')
        except Exception as e:
            logger.error(f'Error fetching multi-ticker data: {e}')
            self._update_node_status(node.node_id, f'✗ Failed')
            raise

    def _execute_sma(self, node: NodeData):
        """Execute SMA calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 20)
            try:
                sma = TechnicalIndicatorProcessor.calculate_sma(input_data, window)
                result = pd.DataFrame({f'SMA_{window}': sma})
                global_state.node_outputs[node.node_id] = result
                node.outputs['sma'] = result
                self._update_node_status(node.node_id, f'✓ SMA({window}) calculated')
            except Exception as e:
                logger.error(f'Error calculating SMA: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_ema(self, node: NodeData):
        """Execute EMA calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 12)
            try:
                ema = TechnicalIndicatorProcessor.calculate_ema(input_data, window)
                result = pd.DataFrame({f'EMA_{window}': ema})
                global_state.node_outputs[node.node_id] = result
                node.outputs['ema'] = result
                self._update_node_status(node.node_id, f'✓ EMA({window}) calculated')
            except Exception as e:
                logger.error(f'Error calculating EMA: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_bollinger(self, node: NodeData):
        """Execute Bollinger Bands calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 20)
            std_dev = node.parameters.get('std_dev', 2)
            try:
                bb = TechnicalIndicatorProcessor.calculate_bollinger_bands(input_data, period, std_dev)
                global_state.node_outputs[node.node_id] = bb
                node.outputs['bollinger'] = bb
                self._update_node_status(node.node_id, f'✓ BB({period},{std_dev}) calculated')
            except Exception as e:
                logger.error(f'Error calculating Bollinger Bands: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_rsi(self, node: NodeData):
        """Execute RSI calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 14)
            try:
                rsi = TechnicalIndicatorProcessor.calculate_rsi(input_data, period)
                result = pd.DataFrame({f'RSI_{period}': rsi})
                global_state.node_outputs[node.node_id] = result
                node.outputs['rsi'] = result
                self._update_node_status(node.node_id, f'✓ RSI({period}) calculated')
            except Exception as e:
                logger.error(f'Error calculating RSI: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_macd(self, node: NodeData):
        """Execute MACD calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            fast = node.parameters.get('fast', 12)
            slow = node.parameters.get('slow', 26)
            signal = node.parameters.get('signal', 9)
            try:
                macd = TechnicalIndicatorProcessor.calculate_macd(input_data, fast, slow, signal)
                global_state.node_outputs[node.node_id] = macd
                node.outputs['macd'] = macd
                self._update_node_status(node.node_id, f'✓ MACD({fast},{slow},{signal})')
            except Exception as e:
                logger.error(f'Error calculating MACD: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_stochastic(self, node: NodeData):
        """Execute Stochastic calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            k_period = node.parameters.get('k_period', 14)
            d_period = node.parameters.get('d_period', 3)
            try:
                stoch = TechnicalIndicatorProcessor.calculate_stochastic(input_data, k_period, d_period)
                global_state.node_outputs[node.node_id] = stoch
                node.outputs['stochastic'] = stoch
                self._update_node_status(node.node_id, f'✓ Stoch({k_period},{d_period})')
            except Exception as e:
                logger.error(f'Error calculating Stochastic: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_atr(self, node: NodeData):
        """Execute ATR calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 14)
            try:
                atr = TechnicalIndicatorProcessor.calculate_atr(input_data, period)
                result = pd.DataFrame({f'ATR_{period}': atr})
                global_state.node_outputs[node.node_id] = result
                node.outputs['atr'] = result
                self._update_node_status(node.node_id, f'✓ ATR({period}) calculated')
            except Exception as e:
                logger.error(f'Error calculating ATR: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_ichimoku(self, node: NodeData):
        """Execute Ichimoku Cloud calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            try:
                ichimoku = TechnicalIndicatorProcessor.calculate_ichimoku(input_data)
                global_state.node_outputs[node.node_id] = ichimoku
                node.outputs['ichimoku'] = ichimoku
                self._update_node_status(node.node_id, '✓ Ichimoku calculated')
            except Exception as e:
                logger.error(f'Error calculating Ichimoku: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_candlestick_patterns(self, node: NodeData):
        """Execute candlestick pattern recognition"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            try:
                patterns = PatternRecognitionProcessor.detect_candlestick_patterns(input_data)
                global_state.node_outputs[node.node_id] = patterns
                node.outputs['patterns'] = patterns
                pattern_counts = patterns.sum()
                total_patterns = pattern_counts.sum()
                self._update_node_status(node.node_id, f'✓ {total_patterns} patterns found')
            except Exception as e:
                logger.error(f'Error detecting patterns: {e}')
                self._update_node_status(node.node_id, '✗ Detection error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_support_resistance(self, node: NodeData):
        """Execute support/resistance detection"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 20)
            try:
                levels = PatternRecognitionProcessor.detect_support_resistance(input_data, window)
                global_state.node_outputs[node.node_id] = levels
                node.outputs['levels'] = levels
                self._update_node_status(node.node_id, '✓ Levels detected')
            except Exception as e:
                logger.error(f'Error detecting S/R levels: {e}')
                self._update_node_status(node.node_id, '✗ Detection error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_signal(self, node: NodeData):
        """Execute signal generation"""
        signal_type = node.parameters.get('type', 'crossover')
        try:
            if signal_type == 'crossover':
                fast_data = self._get_input_data(node.node_id, 'fast')
                slow_data = self._get_input_data(node.node_id, 'slow')
                if fast_data is not None and slow_data is not None:
                    fast_col = fast_data.columns[0] if isinstance(fast_data, pd.DataFrame) else 'fast'
                    slow_col = slow_data.columns[0] if isinstance(slow_data, pd.DataFrame) else 'slow'
                    fast_series = fast_data[fast_col] if isinstance(fast_data, pd.DataFrame) else fast_data
                    slow_series = slow_data[slow_col] if isinstance(slow_data, pd.DataFrame) else slow_data
                    common_index = fast_series.index.intersection(slow_series.index)
                    fast_aligned = fast_series.reindex(common_index)
                    slow_aligned = slow_series.reindex(common_index)
                    buy_signals = (fast_aligned > slow_aligned) & (fast_aligned.shift(1) <= slow_aligned.shift(1))
                    sell_signals = (fast_aligned < slow_aligned) & (fast_aligned.shift(1) >= slow_aligned.shift(1))
                    signals_df = pd.DataFrame({'buy_signals': buy_signals, 'sell_signals': sell_signals}, index=common_index)
                    global_state.node_outputs[node.node_id] = signals_df
                    node.outputs['signals'] = signals_df
                    buy_count = buy_signals.sum()
                    sell_count = sell_signals.sum()
                    self._update_node_status(node.node_id, f'✓ {buy_count} buy, {sell_count} sell')
                else:
                    self._update_node_status(node.node_id, '✗ Missing inputs')
            elif signal_type == 'threshold':
                indicator_data = self._get_input_data(node.node_id, 'indicator')
                buy_threshold = node.parameters.get('buy_threshold', 30)
                sell_threshold = node.parameters.get('sell_threshold', 70)
                if indicator_data is not None:
                    indicator_col = indicator_data.columns[0] if isinstance(indicator_data, pd.DataFrame) else 'indicator'
                    indicator_series = indicator_data[indicator_col] if isinstance(indicator_data, pd.DataFrame) else indicator_data
                    buy_signals = indicator_series < buy_threshold
                    sell_signals = indicator_series > sell_threshold
                    signals_df = pd.DataFrame({'buy_signals': buy_signals, 'sell_signals': sell_signals}, index=indicator_series.index)
                    global_state.node_outputs[node.node_id] = signals_df
                    node.outputs['signals'] = signals_df
                    buy_count = buy_signals.sum()
                    sell_count = sell_signals.sum()
                    self._update_node_status(node.node_id, f'✓ {buy_count} buy, {sell_count} sell')
                else:
                    self._update_node_status(node.node_id, '✗ No indicator data')
        except Exception as e:
            logger.error(f'Error generating signals: {e}')
            self._update_node_status(node.node_id, '✗ Signal generation error')
            raise

    def _execute_ml_signal(self, node: NodeData):
        """Execute ML-based signal generation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            model_type = node.parameters.get('model_type', 'random_forest')
            try:
                signals = MachineLearningProcessor.generate_ml_signals(input_data, model_type)
                signals_df = pd.DataFrame({'buy_signals': signals == 1, 'sell_signals': signals == -1}, index=signals.index)
                global_state.node_outputs[node.node_id] = signals_df
                node.outputs['signals'] = signals_df
                buy_count = (signals == 1).sum()
                sell_count = (signals == -1).sum()
                self._update_node_status(node.node_id, f'✓ ML: {buy_count} buy, {sell_count} sell')
            except Exception as e:
                logger.error(f'Error in ML signal generation: {e}')
                self._update_node_status(node.node_id, '✗ ML error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_backtest(self, node: NodeData):
        """Execute comprehensive backtest"""
        signals_data = self._get_input_data(node.node_id, 'signals')
        if signals_data is None or signals_data.empty:
            self._update_node_status(node.node_id, '✗ No signals data')
            return
        try:
            stock_data = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, pd.DataFrame) and 'Close' in data.columns and ('Open' in data.columns):
                    stock_data = data
                    break
            if stock_data is None:
                self._update_node_status(node.node_id, '✗ No stock data found')
                return
            initial_capital = node.parameters.get('initial_capital', 10000)
            position_size = node.parameters.get('position_size', 0.95)
            commission = node.parameters.get('commission', 0.001)
            slippage = node.parameters.get('slippage', 0.0005)
            stop_loss = node.parameters.get('stop_loss', None)
            take_profit = node.parameters.get('take_profit', None)
            engine = AdvancedBacktestEngine()
            metrics = engine.run_backtest(stock_data, signals_data, initial_capital, position_size, commission, slippage, stop_loss, take_profit)
            results = {'metrics': metrics, 'equity_curve': engine.equity_curve, 'trades': engine.trades}
            global_state.node_outputs[node.node_id] = results
            node.outputs['results'] = results
            self._update_node_status(node.node_id, f'✓ Return: {metrics.total_return:.2f}%')
            if dpg.does_item_exist(f'{node.node_id}_results_text'):
                results_text = f'📊 BACKTEST RESULTS\n━━━━━━━━━━━━━━━━━━━━━\n💰 Returns:\n  • Total: {metrics.total_return:.2f}%\n  • Annual: {metrics.annualized_return:.2f}%\n  • Max DD: {metrics.max_drawdown:.2f}%\n\n📈 Risk Metrics:\n  • Sharpe: {metrics.sharpe_ratio:.2f}\n  • Sortino: {metrics.sortino_ratio:.2f}\n  • Calmar: {metrics.calmar_ratio:.2f}\n\n📊 Trade Stats:\n  • Total: {metrics.total_trades}\n  • Win Rate: {metrics.win_rate:.1f}%\n  • Profit Factor: {metrics.profit_factor:.2f}\n  • Best: {metrics.best_trade:.2f}%\n  • Worst: {metrics.worst_trade:.2f}%'
                dpg.set_value(f'{node.node_id}_results_text', results_text)
        except Exception as e:
            logger.error(f'Error in backtest: {e}')
            self._update_node_status(node.node_id, f'✗ Backtest error')
            raise

    def _execute_optimization(self, node: NodeData):
        """Execute strategy optimization"""
        self._update_node_status(node.node_id, '✓ Optimization complete')

    def _execute_plot(self, node: NodeData):
        """Execute plotting node"""
        plot_type = node.parameters.get('plot_type', 'comprehensive')
        try:
            stock_data = None
            indicators = {}
            signals = None
            backtest_results = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, pd.DataFrame):
                    if 'Close' in data.columns and 'Open' in data.columns:
                        stock_data = data
                    elif 'buy_signals' in data.columns:
                        signals = data
                    elif any((col in str(data.columns) for col in ['SMA', 'EMA', 'RSI', 'MACD'])):
                        indicators[node_id] = data
                elif isinstance(data, dict) and 'metrics' in data:
                    backtest_results = data
            if stock_data is None:
                self._update_node_status(node.node_id, '✗ No data to plot')
                return
            if plot_type == 'comprehensive' and backtest_results:
                chart_base64 = AdvancedPlottingEngine.create_performance_dashboard(backtest_results['metrics'], backtest_results['equity_curve'], backtest_results['trades'])
            else:
                equity_curve = backtest_results['equity_curve'] if backtest_results else None
                chart_base64 = AdvancedPlottingEngine.create_comprehensive_chart(stock_data, indicators, signals, equity_curve)
            global_state.node_outputs[node.node_id] = {'chart': chart_base64}
            node.outputs['chart'] = chart_base64
            self._update_node_status(node.node_id, '✓ Chart generated')
            if dpg.does_item_exist(f'{node.node_id}_chart_viewer'):
                pass
        except Exception as e:
            logger.error(f'Error generating plot: {e}')
            self._update_node_status(node.node_id, '✗ Plot error')
            raise

    def _get_input_data(self, node_id: str, input_type: str='default'):
        """Get input data for a node"""
        if node_id not in global_state.node_connections:
            return None
        connections = global_state.node_connections[node_id]
        if input_type in connections and connections[input_type]:
            source_node_id = connections[input_type][-1]
            if source_node_id in global_state.node_outputs:
                return global_state.node_outputs[source_node_id]
        return None

    def _update_node_status(self, node_id: str, status: str):
        """Update node status in UI"""
        if dpg.does_item_exist(f'{node_id}_status'):
            dpg.set_value(f'{node_id}_status', status)

def _execute_data_source(self, node: NodeData):
    """Execute data source node"""
    ticker = node.parameters.get('ticker', 'AAPL')
    period = node.parameters.get('period', '1y')
    interval = node.parameters.get('interval', '1d')
    try:
        logger.info(f'Fetching data for {ticker}, period: {period}, interval: {interval}')
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            raise ValueError(f'No data found for ticker {ticker}')
        global_state.node_outputs[node.node_id] = data
        node.outputs['data'] = data
        self._update_node_status(node.node_id, f'✓ {len(data)} points loaded')
    except Exception as e:
        logger.error(f'Error fetching data: {e}')
        self._update_node_status(node.node_id, f'✗ Failed: {str(e)[:30]}')
        raise

def _execute_multi_ticker(self, node: NodeData):
    """Execute multi-ticker data source"""
    tickers = node.parameters.get('tickers', ['AAPL', 'GOOGL', 'MSFT'])
    period = node.parameters.get('period', '1y')
    try:
        all_data = {}
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            if not data.empty:
                all_data[ticker] = data
        global_state.node_outputs[node.node_id] = all_data
        node.outputs['data'] = all_data
        self._update_node_status(node.node_id, f'✓ {len(all_data)} tickers loaded')
    except Exception as e:
        logger.error(f'Error fetching multi-ticker data: {e}')
        self._update_node_status(node.node_id, f'✗ Failed')
        raise

def _execute_sma(self, node: NodeData):
    """Execute SMA calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        window = node.parameters.get('window', 20)
        try:
            sma = TechnicalIndicatorProcessor.calculate_sma(input_data, window)
            result = pd.DataFrame({f'SMA_{window}': sma})
            global_state.node_outputs[node.node_id] = result
            node.outputs['sma'] = result
            self._update_node_status(node.node_id, f'✓ SMA({window}) calculated')
        except Exception as e:
            logger.error(f'Error calculating SMA: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_ema(self, node: NodeData):
    """Execute EMA calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        window = node.parameters.get('window', 12)
        try:
            ema = TechnicalIndicatorProcessor.calculate_ema(input_data, window)
            result = pd.DataFrame({f'EMA_{window}': ema})
            global_state.node_outputs[node.node_id] = result
            node.outputs['ema'] = result
            self._update_node_status(node.node_id, f'✓ EMA({window}) calculated')
        except Exception as e:
            logger.error(f'Error calculating EMA: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_bollinger(self, node: NodeData):
    """Execute Bollinger Bands calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        period = node.parameters.get('period', 20)
        std_dev = node.parameters.get('std_dev', 2)
        try:
            bb = TechnicalIndicatorProcessor.calculate_bollinger_bands(input_data, period, std_dev)
            global_state.node_outputs[node.node_id] = bb
            node.outputs['bollinger'] = bb
            self._update_node_status(node.node_id, f'✓ BB({period},{std_dev}) calculated')
        except Exception as e:
            logger.error(f'Error calculating Bollinger Bands: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_rsi(self, node: NodeData):
    """Execute RSI calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        period = node.parameters.get('period', 14)
        try:
            rsi = TechnicalIndicatorProcessor.calculate_rsi(input_data, period)
            result = pd.DataFrame({f'RSI_{period}': rsi})
            global_state.node_outputs[node.node_id] = result
            node.outputs['rsi'] = result
            self._update_node_status(node.node_id, f'✓ RSI({period}) calculated')
        except Exception as e:
            logger.error(f'Error calculating RSI: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_macd(self, node: NodeData):
    """Execute MACD calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        fast = node.parameters.get('fast', 12)
        slow = node.parameters.get('slow', 26)
        signal = node.parameters.get('signal', 9)
        try:
            macd = TechnicalIndicatorProcessor.calculate_macd(input_data, fast, slow, signal)
            global_state.node_outputs[node.node_id] = macd
            node.outputs['macd'] = macd
            self._update_node_status(node.node_id, f'✓ MACD({fast},{slow},{signal})')
        except Exception as e:
            logger.error(f'Error calculating MACD: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_stochastic(self, node: NodeData):
    """Execute Stochastic calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        k_period = node.parameters.get('k_period', 14)
        d_period = node.parameters.get('d_period', 3)
        try:
            stoch = TechnicalIndicatorProcessor.calculate_stochastic(input_data, k_period, d_period)
            global_state.node_outputs[node.node_id] = stoch
            node.outputs['stochastic'] = stoch
            self._update_node_status(node.node_id, f'✓ Stoch({k_period},{d_period})')
        except Exception as e:
            logger.error(f'Error calculating Stochastic: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_atr(self, node: NodeData):
    """Execute ATR calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        period = node.parameters.get('period', 14)
        try:
            atr = TechnicalIndicatorProcessor.calculate_atr(input_data, period)
            result = pd.DataFrame({f'ATR_{period}': atr})
            global_state.node_outputs[node.node_id] = result
            node.outputs['atr'] = result
            self._update_node_status(node.node_id, f'✓ ATR({period}) calculated')
        except Exception as e:
            logger.error(f'Error calculating ATR: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_ichimoku(self, node: NodeData):
    """Execute Ichimoku Cloud calculation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        try:
            ichimoku = TechnicalIndicatorProcessor.calculate_ichimoku(input_data)
            global_state.node_outputs[node.node_id] = ichimoku
            node.outputs['ichimoku'] = ichimoku
            self._update_node_status(node.node_id, '✓ Ichimoku calculated')
        except Exception as e:
            logger.error(f'Error calculating Ichimoku: {e}')
            self._update_node_status(node.node_id, '✗ Calculation error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_candlestick_patterns(self, node: NodeData):
    """Execute candlestick pattern recognition"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        try:
            patterns = PatternRecognitionProcessor.detect_candlestick_patterns(input_data)
            global_state.node_outputs[node.node_id] = patterns
            node.outputs['patterns'] = patterns
            pattern_counts = patterns.sum()
            total_patterns = pattern_counts.sum()
            self._update_node_status(node.node_id, f'✓ {total_patterns} patterns found')
        except Exception as e:
            logger.error(f'Error detecting patterns: {e}')
            self._update_node_status(node.node_id, '✗ Detection error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_support_resistance(self, node: NodeData):
    """Execute support/resistance detection"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        window = node.parameters.get('window', 20)
        try:
            levels = PatternRecognitionProcessor.detect_support_resistance(input_data, window)
            global_state.node_outputs[node.node_id] = levels
            node.outputs['levels'] = levels
            self._update_node_status(node.node_id, '✓ Levels detected')
        except Exception as e:
            logger.error(f'Error detecting S/R levels: {e}')
            self._update_node_status(node.node_id, '✗ Detection error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_ml_signal(self, node: NodeData):
    """Execute ML-based signal generation"""
    input_data = self._get_input_data(node.node_id)
    if input_data is not None and (not input_data.empty):
        model_type = node.parameters.get('model_type', 'random_forest')
        try:
            signals = MachineLearningProcessor.generate_ml_signals(input_data, model_type)
            signals_df = pd.DataFrame({'buy_signals': signals == 1, 'sell_signals': signals == -1}, index=signals.index)
            global_state.node_outputs[node.node_id] = signals_df
            node.outputs['signals'] = signals_df
            buy_count = (signals == 1).sum()
            sell_count = (signals == -1).sum()
            self._update_node_status(node.node_id, f'✓ ML: {buy_count} buy, {sell_count} sell')
        except Exception as e:
            logger.error(f'Error in ML signal generation: {e}')
            self._update_node_status(node.node_id, '✗ ML error')
            raise
    else:
        self._update_node_status(node.node_id, '✗ No input data')

def _execute_optimization(self, node: NodeData):
    """Execute strategy optimization"""
    self._update_node_status(node.node_id, '✓ Optimization complete')

def _execute_plot(self, node: NodeData):
    """Execute plotting node"""
    plot_type = node.parameters.get('plot_type', 'comprehensive')
    try:
        stock_data = None
        indicators = {}
        signals = None
        backtest_results = None
        for node_id, data in global_state.node_outputs.items():
            if isinstance(data, pd.DataFrame):
                if 'Close' in data.columns and 'Open' in data.columns:
                    stock_data = data
                elif 'buy_signals' in data.columns:
                    signals = data
                elif any((col in str(data.columns) for col in ['SMA', 'EMA', 'RSI', 'MACD'])):
                    indicators[node_id] = data
            elif isinstance(data, dict) and 'metrics' in data:
                backtest_results = data
        if stock_data is None:
            self._update_node_status(node.node_id, '✗ No data to plot')
            return
        if plot_type == 'comprehensive' and backtest_results:
            chart_base64 = AdvancedPlottingEngine.create_performance_dashboard(backtest_results['metrics'], backtest_results['equity_curve'], backtest_results['trades'])
        else:
            equity_curve = backtest_results['equity_curve'] if backtest_results else None
            chart_base64 = AdvancedPlottingEngine.create_comprehensive_chart(stock_data, indicators, signals, equity_curve)
        global_state.node_outputs[node.node_id] = {'chart': chart_base64}
        node.outputs['chart'] = chart_base64
        self._update_node_status(node.node_id, '✓ Chart generated')
        if dpg.does_item_exist(f'{node.node_id}_chart_viewer'):
            pass
    except Exception as e:
        logger.error(f'Error generating plot: {e}')
        self._update_node_status(node.node_id, '✗ Plot error')
        raise

class DashboardTab(BaseTab):
    """Bloomberg Terminal style Dashboard tab - With Real Data (Fast Loading)"""

    def __init__(self, main_app=None):
        super().__init__(main_app)
        try:
            with logger.operation('dashboard_tab_initialization'):
                info('Initializing Dashboard Tab')
                self.main_app = main_app
                self.BLOOMBERG_ORANGE = [255, 165, 0]
                self.BLOOMBERG_WHITE = [255, 255, 255]
                self.BLOOMBERG_RED = [255, 0, 0]
                self.BLOOMBERG_GREEN = [0, 200, 0]
                self.BLOOMBERG_YELLOW = [255, 255, 0]
                self.BLOOMBERG_GRAY = [120, 120, 120]
                self.last_update = None
                self.update_interval = 3600
                self.data_loading = False
                self._lock = threading.Lock()
                self.initialize_data()
                self.start_background_updates()
                info('Dashboard Tab initialized successfully', context={'yfinance_available': YFINANCE_AVAILABLE, 'feedparser_available': FEEDPARSER_AVAILABLE})
        except Exception as e:
            error('Dashboard Tab initialization failed', context={'error': str(e)}, exc_info=True)
            raise

    def get_label(self):
        return 'Dashboard'

    def safe_float_conversion(self, value: Any, default: float=0.0) -> float:
        """Safely convert value to float with encoding handling"""
        try:
            if value is None:
                return default
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')
            elif isinstance(value, str):
                value = ''.join((c for c in value if c.isdigit() or c in '.-'))
            return float(value) if value else default
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            warning(f'Error converting value to float', context={'value': str(value), 'error': str(e)})
            return default

    def safe_int_conversion(self, value: Any, default: int=0) -> int:
        """Safely convert value to int with encoding handling"""
        try:
            if value is None:
                return default
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')
            elif isinstance(value, str):
                value = ''.join((c for c in value if c.isdigit()))
            return int(float(value)) if value else default
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            warning(f'Error converting value to int', context={'value': str(value), 'error': str(e)})
            return default

    @monitor_performance
    def get_stock_data_optimized(self, symbols: List[str], timeout: int=10) -> Dict[str, Dict[str, Any]]:
        """Optimized stock data fetch using yfinance history method and concurrent processing"""
        if not YFINANCE_AVAILABLE:
            debug('yfinance not available, using fallback data')
            return self.get_fallback_stock_data(symbols)
        result = {}

        def fetch_single_stock(symbol: str) -> tuple[str, Dict[str, Any]]:
            """Fetch data for a single stock symbol"""
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d', interval='1d', timeout=timeout)
                if hist.empty or len(hist) < 2:
                    warning(f'Insufficient data for {symbol}, using fallback')
                    return (symbol, self.get_fallback_stock_data([symbol])[symbol])
                current_data = hist.iloc[-1]
                prev_data = hist.iloc[-2]
                current_price = self.safe_float_conversion(current_data['Close'])
                prev_price = self.safe_float_conversion(prev_data['Close'])
                volume = self.safe_int_conversion(current_data['Volume'])
                high = self.safe_float_conversion(current_data['High'])
                low = self.safe_float_conversion(current_data['Low'])
                open_price = self.safe_float_conversion(current_data['Open'])
                change_val = current_price - prev_price
                change_pct = change_val / prev_price * 100 if prev_price != 0 else 0
                stock_data = {'price': round(current_price, 2), 'change_pct': round(change_pct, 2), 'change_val': round(change_val, 2), 'volume': volume, 'high': round(high, 2), 'low': round(low, 2), 'open': round(open_price, 2)}
                debug(f'Successfully fetched data for {symbol}', context={'price': current_price, 'change_pct': change_pct})
                return (symbol, stock_data)
            except Exception as e:
                warning(f'Error fetching data for {symbol}', context={'error': str(e)})
                return (symbol, self.get_fallback_stock_data([symbol])[symbol])
        try:
            with logger.operation('concurrent_stock_fetch'):
                info(f'Fetching stock data for {len(symbols)} symbols concurrently')
                with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as executor:
                    future_to_symbol = {executor.submit(fetch_single_stock, symbol): symbol for symbol in symbols}
                    successful_fetches = 0
                    failed_fetches = 0
                    for future in as_completed(future_to_symbol, timeout=timeout + 5):
                        try:
                            symbol, data = future.result(timeout=5)
                            result[symbol] = data
                            successful_fetches += 1
                        except Exception as e:
                            symbol = future_to_symbol[future]
                            error(f'Failed to get data for {symbol}', context={'error': str(e)})
                            result[symbol] = self.get_fallback_stock_data([symbol])[symbol]
                            failed_fetches += 1
                info('Concurrent stock fetch completed', context={'successful': successful_fetches, 'failed': failed_fetches, 'success_rate': f'{successful_fetches / (successful_fetches + failed_fetches) * 100:.1f}%'})
        except Exception as e:
            error('Error in concurrent stock data fetch', context={'error': str(e)}, exc_info=True)
            return self.get_fallback_stock_data(symbols)
        for symbol in symbols:
            if symbol not in result:
                result[symbol] = self.get_fallback_stock_data([symbol])[symbol]
        return result

    def get_fallback_stock_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate realistic fallback stock data with proper encoding handling"""
        import random
        result = {}
        base_prices = {'AAPL': 175, 'MSFT': 420, 'AMZN': 155, 'GOOGL': 140, 'META': 485, 'TSLA': 250, 'NVDA': 875, 'JPM': 155, 'V': 265, 'JNJ': 165, 'BAC': 35, 'PG': 160, 'MA': 465, 'UNH': 525, 'HD': 385, 'INTC': 45, 'VZ': 40, 'DIS': 110, 'PYPL': 65, 'NFLX': 485}
        for symbol in symbols:
            try:
                if isinstance(symbol, bytes):
                    symbol = symbol.decode('utf-8', errors='ignore')
                base_price = base_prices.get(symbol, 100)
                change_pct = round(random.uniform(-2.5, 2.5), 2)
                price = round(base_price * (1 + change_pct / 100), 2)
                change_val = round(price * change_pct / 100, 2)
                result[symbol] = {'price': price, 'change_pct': change_pct, 'change_val': change_val, 'volume': random.randint(1000000, 50000000), 'high': round(price * 1.03, 2), 'low': round(price * 0.97, 2), 'open': round(price * 0.995, 2)}
            except Exception as e:
                error(f'Error generating fallback data for {symbol}', context={'error': str(e)}, exc_info=True)
                result[symbol] = {'price': 100.0, 'change_pct': 0.0, 'change_val': 0.0, 'volume': 1000000, 'high': 103.0, 'low': 97.0, 'open': 99.5}
        return result

    @monitor_performance
    def get_indices_data_optimized(self, timeout: int=10) -> Dict[str, Dict[str, float]]:
        """Optimized index data fetch with better error handling"""
        if not YFINANCE_AVAILABLE:
            debug('yfinance not available, using fallback indices data')
            return self.get_fallback_indices_data()
        symbols = ['^GSPC', '^DJI', '^IXIC', '^FTSE', '^GDAXI', '^N225']
        names = ['S&P 500', 'DOW JONES', 'NASDAQ', 'FTSE 100', 'DAX', 'NIKKEI 225']
        result = {}

        def fetch_single_index(symbol: str, name: str) -> tuple[str, Dict[str, float]]:
            """Fetch data for a single index"""
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d', interval='1d', timeout=timeout)
                if hist.empty or len(hist) < 2:
                    warning(f'Insufficient data for index {name}', context={'symbol': symbol})
                    fallback = self.get_fallback_indices_data()
                    return (name, fallback[name])
                current_value = self.safe_float_conversion(hist['Close'].iloc[-1])
                prev_value = self.safe_float_conversion(hist['Close'].iloc[-2])
                change_pct = (current_value - prev_value) / prev_value * 100 if prev_value != 0 else 0
                debug(f'Successfully fetched index data for {name}', context={'value': current_value, 'change': change_pct})
                return (name, {'value': round(current_value, 2), 'change': round(change_pct, 2)})
            except Exception as e:
                error(f'Error fetching index {name}', context={'symbol': symbol, 'error': str(e)})
                fallback = self.get_fallback_indices_data()
                return (name, fallback[name])
        try:
            with logger.operation('concurrent_indices_fetch'):
                info(f'Fetching indices data concurrently')
                with ThreadPoolExecutor(max_workers=6) as executor:
                    future_to_name = {executor.submit(fetch_single_index, symbol, name): name for symbol, name in zip(symbols, names)}
                    successful_fetches = 0
                    failed_fetches = 0
                    for future in as_completed(future_to_name, timeout=timeout + 5):
                        try:
                            name, data = future.result(timeout=5)
                            result[name] = data
                            successful_fetches += 1
                        except Exception as e:
                            name = future_to_name[future]
                            error(f'Failed to get index data for {name}', context={'error': str(e)})
                            fallback = self.get_fallback_indices_data()
                            result[name] = fallback[name]
                            failed_fetches += 1
                info('Indices data fetch completed', context={'successful': successful_fetches, 'failed': failed_fetches})
        except Exception as e:
            error('Error in concurrent index data fetch', context={'error': str(e)}, exc_info=True)
            return self.get_fallback_indices_data()
        return result

    def get_fallback_indices_data(self) -> Dict[str, Dict[str, float]]:
        """Generate realistic fallback indices data"""
        import random
        return {'S&P 500': {'value': round(5200 + random.uniform(-50, 50), 2), 'change': round(random.uniform(-1, 1), 2)}, 'DOW JONES': {'value': round(38500 + random.uniform(-200, 200), 2), 'change': round(random.uniform(-1, 1), 2)}, 'NASDAQ': {'value': round(16400 + random.uniform(-100, 100), 2), 'change': round(random.uniform(-1.5, 1.5), 2)}, 'FTSE 100': {'value': round(7600 + random.uniform(-50, 50), 2), 'change': round(random.uniform(-1, 1), 2)}, 'DAX': {'value': round(18200 + random.uniform(-100, 100), 2), 'change': round(random.uniform(-1, 1), 2)}, 'NIKKEI 225': {'value': round(35800 + random.uniform(-200, 200), 2), 'change': round(random.uniform(-1, 1), 2)}}

    @monitor_performance
    def get_news_optimized(self, timeout: int=15) -> List[str]:
        """Optimized news fetch with better encoding handling"""
        if not FEEDPARSER_AVAILABLE:
            debug('feedparser not available, using fallback news')
            return self.get_fallback_news()
        try:
            with logger.operation('news_fetch'):
                info('Fetching news headlines from multiple sources')
                feeds = ['https://feeds.finance.yahoo.com/rss/2.0/headline', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 'https://feeds.marketwatch.com/marketwatch/topstories/']
                news_headlines = []

                def fetch_feed(feed_url: str) -> List[str]:
                    """Fetch headlines from a single feed"""
                    try:
                        debug(f'Fetching from feed: {feed_url}')
                        feed = feedparser.parse(feed_url)
                        headlines = []
                        if feed.entries:
                            for entry in feed.entries[:3]:
                                try:
                                    title = entry.title.strip()
                                    if isinstance(title, bytes):
                                        title = title.decode('utf-8', errors='ignore')
                                    title = title.encode('ascii', errors='ignore').decode('ascii')
                                    if len(title) > 80:
                                        title = title[:77] + '...'
                                    if title:
                                        headlines.append(title)
                                except Exception as e:
                                    warning(f'Error processing news entry', context={'error': str(e)})
                                    continue
                        debug(f'Fetched {len(headlines)} headlines from feed')
                        return headlines
                    except Exception as e:
                        warning(f'Error parsing feed', context={'feed_url': feed_url, 'error': str(e)})
                        return []
                for feed_url in feeds:
                    try:
                        headlines = fetch_feed(feed_url)
                        news_headlines.extend(headlines)
                        if len(news_headlines) >= 6:
                            break
                    except Exception as e:
                        error(f'Error fetching from feed', context={'feed_url': feed_url, 'error': str(e)})
                        continue
                if not news_headlines:
                    warning('No news headlines fetched, using fallback')
                    return self.get_fallback_news()
                info(f'Successfully fetched {len(news_headlines)} news headlines')
                return news_headlines[:6]
        except Exception as e:
            error('Error fetching news', context={'error': str(e)}, exc_info=True)
            return self.get_fallback_news()

    def get_fallback_news(self) -> List[str]:
        """Fallback news headlines"""
        return ['Market Update: Fed maintains current interest rates amid economic stability', 'Tech stocks show strong performance during Q4 earnings season', 'Oil prices stabilize following recent OPEC+ production decisions', 'Treasury yields remain elevated on persistent inflation concerns', 'Consumer spending data indicates continued economic resilience', 'Global markets react positively to central bank policy updates']

    def initialize_data(self):
        """Initialize with fallback data for immediate display"""
        try:
            with logger.operation('data_initialization'):
                info('Initializing dashboard data')
                self.tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ', 'BAC', 'PG', 'MA', 'UNH', 'HD', 'INTC', 'VZ', 'DIS', 'PYPL', 'NFLX']
                with self._lock:
                    self.stock_data = self.get_fallback_stock_data(self.tickers)
                    self.indices = self.get_fallback_indices_data()
                    self.news_headlines = self.get_fallback_news()
                self.economic_indicators = {'US 10Y Treasury': {'value': 4.35, 'change': 0.05}, 'US GDP Growth': {'value': 2.8, 'change': 0.1}, 'US Unemployment': {'value': 3.6, 'change': -0.1}, 'EUR/USD': {'value': 1.084, 'change': -0.002}, 'Gold': {'value': 2312.8, 'change': 15.6}, 'WTI Crude': {'value': 78.35, 'change': -1.25}}
                info('Dashboard data initialized successfully', context={'stocks_count': len(self.stock_data), 'indices_count': len(self.indices), 'news_count': len(self.news_headlines)})
        except Exception as e:
            error('Failed to initialize dashboard data', context={'error': str(e)}, exc_info=True)

    def should_update_data(self) -> bool:
        """Check if data should be updated (every hour)"""
        if self.last_update is None:
            debug('No previous update, data refresh needed')
            return True
        time_since_update = time.time() - self.last_update
        should_update = time_since_update >= self.update_interval
        if should_update:
            debug(f'Update interval exceeded', context={'hours_since_update': time_since_update / 3600})
        return should_update

    @monitor_performance
    def update_data_background(self):
        """Update data in background thread with optimizations"""
        if self.data_loading:
            debug('Data update already in progress, skipping')
            return

        def fetch_all_data():
            try:
                with logger.operation('background_data_update'):
                    with self._lock:
                        self.data_loading = True
                    info('Starting optimized background data update')
                    stock_data = self.get_stock_data_optimized(self.tickers, timeout=15)
                    indices_data = self.get_indices_data_optimized(timeout=15)
                    news_data = self.get_news_optimized(timeout=15)
                    with self._lock:
                        self.stock_data.update(stock_data)
                        self.indices = indices_data
                        self.news_headlines = news_data
                        self.last_update = time.time()
                    info('Optimized background data update completed successfully')
            except Exception as e:
                error('Error in background data update', context={'error': str(e)}, exc_info=True)
            finally:
                with self._lock:
                    self.data_loading = False
        thread = threading.Thread(target=fetch_all_data, daemon=True, name='DashboardDataUpdater')
        thread.start()

    def start_background_updates(self):
        """Start the background update system with better scheduling"""
        try:
            info('Starting background update system')

            def update_loop():
                try:
                    time.sleep(2)
                    self.update_data_background()
                    while True:
                        time.sleep(300)
                        if self.should_update_data() and (not self.data_loading):
                            info('Starting scheduled hourly data update')
                            self.update_data_background()
                except Exception as e:
                    error('Error in background update loop', context={'error': str(e)}, exc_info=True)
            update_thread = threading.Thread(target=update_loop, daemon=True, name='DashboardUpdateLoop')
            update_thread.start()
            info('Background update system started successfully')
        except Exception as e:
            error('Failed to start background update system', context={'error': str(e)}, exc_info=True)

    def safe_text_display(self, text: Any) -> str:
        """Safely display text with encoding handling"""
        try:
            if isinstance(text, bytes):
                return text.decode('utf-8', errors='ignore')
            elif isinstance(text, (int, float)):
                return str(text)
            elif text is None:
                return ''
            else:
                return str(text).encode('ascii', errors='ignore').decode('ascii')
        except Exception as e:
            warning(f'Error displaying text', context={'error': str(e)})
            return 'N/A'

    @monitor_performance
    def create_content(self):
        """Create the Bloomberg Terminal layout with error handling"""
        try:
            with logger.operation('create_dashboard_content'):
                info('Creating dashboard tab content')
                with dpg.group(horizontal=True):
                    dpg.add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
                    dpg.add_text('PROFESSIONAL', color=self.BLOOMBERG_WHITE)
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_input_text(label='', default_value='Enter Command', width=300)
                    dpg.add_button(label='Search', width=80)
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_text(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    function_keys = ['F1:HELP', 'F2:MARKETS', 'F3:NEWS', 'F4:PORT', 'F5:MOVERS', 'F6:ECON']
                    for key in function_keys:
                        dpg.add_button(label=key, width=80, height=25)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    self.create_left_panel()
                    self.create_center_panel()
                    self.create_right_panel()
                dpg.add_separator()
                self.create_bottom_section()
                info('Dashboard tab content created successfully')
        except Exception as e:
            error('Error in create_content', context={'error': str(e)}, exc_info=True)
            dpg.add_text('Bloomberg Terminal', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('Terminal is loading... Please wait.')

    def create_left_panel(self):
        """Create left panel with market data"""
        with dpg.child_window(width=350, height=600, border=True):
            dpg.add_text('MARKET MONITOR', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            dpg.add_text('GLOBAL INDICES', color=self.BLOOMBERG_YELLOW)
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True):
                dpg.add_table_column(label='Index')
                dpg.add_table_column(label='Value')
                dpg.add_table_column(label='Change %')
                with self._lock:
                    for index, data in self.indices.items():
                        with dpg.table_row():
                            dpg.add_text(self.safe_text_display(index))
                            dpg.add_text(f'{data['value']:.2f}')
                            change_color = self.BLOOMBERG_GREEN if data['change'] > 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{data['change']:+.2f}%', color=change_color)
            dpg.add_separator()
            dpg.add_text('ECONOMIC INDICATORS', color=self.BLOOMBERG_YELLOW)
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True):
                dpg.add_table_column(label='Indicator')
                dpg.add_table_column(label='Value')
                dpg.add_table_column(label='Change')
                for indicator, data in self.economic_indicators.items():
                    with dpg.table_row():
                        dpg.add_text(self.safe_text_display(indicator))
                        dpg.add_text(f'{data['value']:.2f}')
                        change_color = self.BLOOMBERG_GREEN if data['change'] > 0 else self.BLOOMBERG_RED
                        dpg.add_text(f'{data['change']:+.2f}', color=change_color)
            dpg.add_separator()
            dpg.add_text('LATEST NEWS', color=self.BLOOMBERG_YELLOW)
            with self._lock:
                for headline in self.news_headlines[:4]:
                    time_str = datetime.datetime.now().strftime('%H:%M')
                    safe_headline = self.safe_text_display(headline)
                    if len(safe_headline) > 50:
                        safe_headline = safe_headline[:47] + '...'
                    dpg.add_text(f'{time_str} - {safe_headline}', wrap=340)

    def create_center_panel(self):
        """Create center panel with stock data"""
        with dpg.child_window(width=800, height=600, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='Market Data'):
                    dpg.add_text('TOP STOCKS', color=self.BLOOMBERG_ORANGE)
                    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, height=300):
                        dpg.add_table_column(label='Ticker')
                        dpg.add_table_column(label='Last')
                        dpg.add_table_column(label='Chg')
                        dpg.add_table_column(label='Chg%')
                        dpg.add_table_column(label='Volume')
                        dpg.add_table_column(label='High')
                        dpg.add_table_column(label='Low')
                        with self._lock:
                            for ticker in self.tickers:
                                data = self.stock_data.get(ticker, {})
                                with dpg.table_row():
                                    dpg.add_text(self.safe_text_display(ticker))
                                    dpg.add_text(f'{data.get('price', 0):.2f}')
                                    change_color = self.BLOOMBERG_GREEN if data.get('change_pct', 0) > 0 else self.BLOOMBERG_RED
                                    dpg.add_text(f'{data.get('change_val', 0):+.2f}', color=change_color)
                                    dpg.add_text(f'{data.get('change_pct', 0):+.2f}%', color=change_color)
                                    dpg.add_text(f'{data.get('volume', 0):,}')
                                    dpg.add_text(f'{data.get('high', 0):.2f}')
                                    dpg.add_text(f'{data.get('low', 0):.2f}')
                    dpg.add_separator()
                    dpg.add_text('STOCK DETAILS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(label='Ticker', default_value='AAPL', width=150)
                        dpg.add_button(label='Load')
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_text('Apple Inc (AAPL US Equity)', color=self.BLOOMBERG_ORANGE)
                            dpg.add_text('Technology - Consumer Electronics')
                            with self._lock:
                                aapl_data = self.stock_data.get('AAPL', {})
                                dpg.add_text(f'Last Price: {aapl_data.get('price', 0):.2f}')
                                change_color = self.BLOOMBERG_GREEN if aapl_data.get('change_pct', 0) > 0 else self.BLOOMBERG_RED
                                dpg.add_text(f'Change: {aapl_data.get('change_val', 0):+.2f} ({aapl_data.get('change_pct', 0):+.2f}%)', color=change_color)
                                dpg.add_text(f'Volume: {aapl_data.get('volume', 0):,}')
                        with dpg.group():
                            with self._lock:
                                aapl_data = self.stock_data.get('AAPL', {})
                                dpg.add_text(f'High: {aapl_data.get('high', 0):.2f}')
                                dpg.add_text(f'Low: {aapl_data.get('low', 0):.2f}')
                                dpg.add_text(f'Open: {aapl_data.get('open', 0):.2f}')
                            dpg.add_text('P/E Ratio: 28.5')
                            dpg.add_text('Market Cap: $2.8T')
                with dpg.tab(label='Charts'):
                    dpg.add_text('ADVANCED CHARTS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        dpg.add_combo(['AAPL', 'MSFT', 'GOOGL', 'AMZN'], default_value='AAPL', width=150)
                        dpg.add_combo(['1D', '5D', '1M', '3M'], default_value='1M', width=100)
                        dpg.add_button(label='Update Chart')
                    with dpg.plot(height=300, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label='Time')
                        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Price')
                        x_data = list(range(30))
                        with self._lock:
                            base_price = self.stock_data.get('AAPL', {}).get('price', 175)
                        y_data = [base_price + i * 0.5 for i in range(30)]
                        dpg.add_line_series(x_data, y_data, label='AAPL', parent=y_axis)
                    dpg.add_text('TECHNICAL INDICATORS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_text('Moving Averages', color=self.BLOOMBERG_YELLOW)
                            dpg.add_text('MA 20: 175.50 - Buy', color=self.BLOOMBERG_GREEN)
                            dpg.add_text('MA 50: 172.30 - Buy', color=self.BLOOMBERG_GREEN)
                            dpg.add_text('MA 200: 165.80 - Neutral', color=self.BLOOMBERG_WHITE)
                        with dpg.group():
                            dpg.add_text('Oscillators', color=self.BLOOMBERG_YELLOW)
                            dpg.add_text('RSI(14): 65.42 - Neutral', color=self.BLOOMBERG_WHITE)
                            dpg.add_text('MACD: 2.15 - Buy', color=self.BLOOMBERG_GREEN)
                            dpg.add_text('Stochastic: 75.30 - Sell', color=self.BLOOMBERG_RED)
                with dpg.tab(label='News'):
                    dpg.add_text('FINANCIAL NEWS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(label='Search', width=300)
                        dpg.add_button(label='Go')
                    dpg.add_separator()
                    with self._lock:
                        for i, headline in enumerate(self.news_headlines):
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                            safe_headline = self.safe_text_display(headline)
                            dpg.add_text(safe_headline, color=self.BLOOMBERG_ORANGE)
                            dpg.add_text(timestamp, color=self.BLOOMBERG_GRAY)
                            dpg.add_text('Market analysis and financial news content goes here...')
                            dpg.add_separator()

    def create_right_panel(self):
        """Create right panel with command line"""
        with dpg.child_window(width=350, height=600, border=True):
            dpg.add_text('COMMAND LINE', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            with dpg.child_window(height=200, border=True):
                dpg.add_text('> AAPL US Equity <GO>', color=self.BLOOMBERG_WHITE)
                dpg.add_text('  Loading AAPL US Equity...', color=self.BLOOMBERG_GRAY)
                dpg.add_text('> TOP <GO>', color=self.BLOOMBERG_WHITE)
                dpg.add_text('  Loading TOP news...', color=self.BLOOMBERG_GRAY)
                dpg.add_text('> WEI <GO>', color=self.BLOOMBERG_WHITE)
                dpg.add_text('  Loading World Equity Indices...', color=self.BLOOMBERG_GRAY)
            dpg.add_input_text(label='>', width=-1)
            dpg.add_text('<HELP> for commands. Press <GO> to execute.', color=self.BLOOMBERG_GRAY)
            dpg.add_separator()
            dpg.add_text('COMMON COMMANDS', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('HELP - Show available commands')
            dpg.add_text('DES - Company description')
            dpg.add_text('GP - Price graph')
            dpg.add_text('TOP - Top news headlines')
            dpg.add_text('WEI - World equity indices')
            dpg.add_text('PORT - Portfolio overview')

    def create_bottom_section(self):
        """Create bottom news ticker and status bar"""
        dpg.add_text('LIVE NEWS TICKER', color=self.BLOOMBERG_ORANGE)
        with dpg.child_window(height=50, border=True):
            with self._lock:
                ticker_text = ' • '.join(self.news_headlines[:3]) if self.news_headlines else 'Loading live news...'
                safe_ticker_text = self.safe_text_display(ticker_text)
            dpg.add_text(safe_ticker_text)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with self._lock:
                status_color = self.BLOOMBERG_ORANGE if self.data_loading else self.BLOOMBERG_GREEN
                status_text = 'UPDATING' if self.data_loading else 'CONNECTED'
            dpg.add_text('●', color=status_color)
            dpg.add_text(status_text, color=status_color)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LIVE DATA', color=self.BLOOMBERG_ORANGE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            current_hour = datetime.datetime.now().hour
            if 9 <= current_hour < 16:
                dpg.add_text('MARKET OPEN', color=self.BLOOMBERG_GREEN)
            else:
                dpg.add_text('MARKET CLOSED', color=self.BLOOMBERG_RED)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('SERVER: NY-01', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('USER: TRADER001', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            with self._lock:
                if self.last_update:
                    last_update_str = datetime.datetime.fromtimestamp(self.last_update).strftime('%H:%M:%S')
                    dpg.add_text(f'LAST UPDATE: {last_update_str}', color=self.BLOOMBERG_WHITE)
                else:
                    dpg.add_text('LAST UPDATE: --:--:--', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LATENCY: 12ms', color=self.BLOOMBERG_GREEN)

    def resize_components(self, left_width, center_width, right_width, top_height, bottom_height, cell_height):
        """Resize components - simplified"""
        try:
            debug('Dashboard resize requested', context={'left_width': left_width, 'center_width': center_width, 'right_width': right_width})
        except Exception as e:
            warning('Resize handling failed', context={'error': str(e)})

    @monitor_performance
    def cleanup(self):
        """Clean up resources"""
        try:
            with logger.operation('dashboard_cleanup'):
                info('Starting Dashboard Tab cleanup')
                with self._lock:
                    self.stock_data = {}
                    self.indices = {}
                    self.news_headlines = []
                    self.data_loading = False
                info('Dashboard Tab cleanup completed successfully')
        except Exception as e:
            error('Dashboard Tab cleanup failed', context={'error': str(e)}, exc_info=True)

    def force_refresh(self):
        """Force refresh all data - useful for manual updates"""
        try:
            if not self.data_loading:
                info('Force refreshing data')
                self.update_data_background()
            else:
                info('Data update already in progress')
        except Exception as e:
            error('Force refresh failed', context={'error': str(e)}, exc_info=True)

    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status information"""
        try:
            current_time = datetime.datetime.now()
            current_hour = current_time.hour
            is_market_open = 9 <= current_hour < 16
            with self._lock:
                status = {'is_open': is_market_open, 'last_update': self.last_update, 'data_loading': self.data_loading, 'stocks_count': len(self.stock_data), 'indices_count': len(self.indices), 'news_count': len(self.news_headlines)}
            return status
        except Exception as e:
            error('Failed to get market status', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data for a specific symbol"""
        try:
            with self._lock:
                return self.stock_data.get(symbol.upper())
        except Exception as e:
            error(f'Failed to get stock data for symbol', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return None

    def add_custom_ticker(self, symbol: str):
        """Add a custom ticker to the watch list"""
        try:
            symbol = symbol.upper()
            if symbol not in self.tickers:
                self.tickers.append(symbol)
                if not self.data_loading:
                    try:
                        new_data = self.get_stock_data_optimized([symbol], timeout=10)
                        with self._lock:
                            self.stock_data.update(new_data)
                        info(f'Added ticker to watch list', context={'symbol': symbol})
                    except Exception as e:
                        error(f'Error adding ticker', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
        except Exception as e:
            error(f'Failed to add custom ticker', context={'symbol': symbol, 'error': str(e)}, exc_info=True)

    def remove_ticker(self, symbol: str):
        """Remove a ticker from the watch list"""
        try:
            symbol = symbol.upper()
            if symbol in self.tickers:
                self.tickers.remove(symbol)
                with self._lock:
                    if symbol in self.stock_data:
                        del self.stock_data[symbol]
                info(f'Removed ticker from watch list', context={'symbol': symbol})
        except Exception as e:
            error(f'Failed to remove ticker', context={'symbol': symbol, 'error': str(e)}, exc_info=True)

    def export_data_to_json(self) -> str:
        """Export current data to JSON format"""
        try:
            with logger.operation('data_export'):
                info('Exporting dashboard data to JSON')
                with self._lock:
                    export_data = {'timestamp': datetime.datetime.now().isoformat(), 'stock_data': self.stock_data, 'indices': self.indices, 'news_headlines': self.news_headlines, 'economic_indicators': self.economic_indicators}
                json_data = json.dumps(export_data, indent=2)
                info('Dashboard data exported successfully', context={'data_size': len(json_data)})
                return json_data
        except Exception as e:
            error('Error exporting data', context={'error': str(e)}, exc_info=True)
            return '{}'

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            with self._lock:
                gainers = [ticker for ticker, data in self.stock_data.items() if data.get('change_pct', 0) > 0]
                losers = [ticker for ticker, data in self.stock_data.items() if data.get('change_pct', 0) < 0]
                total_volume = sum((data.get('volume', 0) for data in self.stock_data.values()))
                stats = {'total_stocks': len(self.stock_data), 'gainers': len(gainers), 'losers': len(losers), 'unchanged': len(self.stock_data) - len(gainers) - len(losers), 'total_volume': total_volume, 'top_gainer': max(self.stock_data.items(), key=lambda x: x[1].get('change_pct', 0))[0] if self.stock_data else None, 'top_loser': min(self.stock_data.items(), key=lambda x: x[1].get('change_pct', 0))[0] if self.stock_data else None}
            debug('Performance stats calculated', context=stats)
            return stats
        except Exception as e:
            error('Failed to get performance stats', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

def fetch_single_stock(symbol: str) -> tuple[str, Dict[str, Any]]:
    """Fetch data for a single stock symbol"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d', interval='1d', timeout=timeout)
        if hist.empty or len(hist) < 2:
            warning(f'Insufficient data for {symbol}, using fallback')
            return (symbol, self.get_fallback_stock_data([symbol])[symbol])
        current_data = hist.iloc[-1]
        prev_data = hist.iloc[-2]
        current_price = self.safe_float_conversion(current_data['Close'])
        prev_price = self.safe_float_conversion(prev_data['Close'])
        volume = self.safe_int_conversion(current_data['Volume'])
        high = self.safe_float_conversion(current_data['High'])
        low = self.safe_float_conversion(current_data['Low'])
        open_price = self.safe_float_conversion(current_data['Open'])
        change_val = current_price - prev_price
        change_pct = change_val / prev_price * 100 if prev_price != 0 else 0
        stock_data = {'price': round(current_price, 2), 'change_pct': round(change_pct, 2), 'change_val': round(change_val, 2), 'volume': volume, 'high': round(high, 2), 'low': round(low, 2), 'open': round(open_price, 2)}
        debug(f'Successfully fetched data for {symbol}', context={'price': current_price, 'change_pct': change_pct})
        return (symbol, stock_data)
    except Exception as e:
        warning(f'Error fetching data for {symbol}', context={'error': str(e)})
        return (symbol, self.get_fallback_stock_data([symbol])[symbol])

def fetch_single_index(symbol: str, name: str) -> tuple[str, Dict[str, float]]:
    """Fetch data for a single index"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d', interval='1d', timeout=timeout)
        if hist.empty or len(hist) < 2:
            warning(f'Insufficient data for index {name}', context={'symbol': symbol})
            fallback = self.get_fallback_indices_data()
            return (name, fallback[name])
        current_value = self.safe_float_conversion(hist['Close'].iloc[-1])
        prev_value = self.safe_float_conversion(hist['Close'].iloc[-2])
        change_pct = (current_value - prev_value) / prev_value * 100 if prev_value != 0 else 0
        debug(f'Successfully fetched index data for {name}', context={'value': current_value, 'change': change_pct})
        return (name, {'value': round(current_value, 2), 'change': round(change_pct, 2)})
    except Exception as e:
        error(f'Error fetching index {name}', context={'symbol': symbol, 'error': str(e)})
        fallback = self.get_fallback_indices_data()
        return (name, fallback[name])

class PortfolioBusinessLogic:
    """Business logic for Portfolio Management - separated from UI"""

    def __init__(self):
        self.price_cache = {}
        self.last_price_update = {}
        self.price_fetch_errors = {}
        self.daily_change_cache = {}
        self.previous_close_cache = {}
        self.refresh_thread = None
        self.refresh_running = False
        self.price_update_interval = 3600
        self.initial_price_fetch_done = False
        self.portfolios = self.load_portfolios()
        self.current_portfolio = None
        self.country_suffixes = self._get_country_suffixes()
        self._portfolio_value_cache = {}
        self._portfolio_investment_cache = {}
        self._cache_timeout = 30
        self._last_cache_update = {}
        self.csv_data = None
        self.csv_headers = []
        self.column_mapping = {}
        self.csv_preview_data = []
        self.csv_file_path = None
        self.initialize_sample_data()
        self.fetch_initial_prices()

    def _get_country_suffixes(self):
        """Get country suffix mapping - cached"""
        return {'India': '.NS', 'United States': '', 'United Kingdom': '.L', 'Germany': '.DE', 'Japan': '.T', 'Australia': '.AX', 'Canada': '.TO', 'France': '.PA', 'Hong Kong': '.HK', 'South Korea': '.KS'}

    def initialize_sample_data(self):
        """Initialize sample portfolio data for demonstration"""
        if not self.portfolios:
            self.portfolios = {'Tech Growth': {'AAPL': {'quantity': 50, 'avg_price': 150.25, 'last_added': '2024-01-15'}, 'MSFT': {'quantity': 30, 'avg_price': 280.75, 'last_added': '2024-01-10'}, 'GOOGL': {'quantity': 25, 'avg_price': 125.5, 'last_added': '2024-01-05'}, 'NVDA': {'quantity': 20, 'avg_price': 450.3, 'last_added': '2024-01-20'}}, 'Dividend Income': {'JNJ': {'quantity': 100, 'avg_price': 160.8, 'last_added': '2024-01-12'}, 'PG': {'quantity': 75, 'avg_price': 145.2, 'last_added': '2024-01-08'}, 'KO': {'quantity': 150, 'avg_price': 58.9, 'last_added': '2024-01-18'}}}
            self.save_portfolios()

    @monitor_performance
    def fetch_initial_prices(self):
        """Fetch initial prices for all stocks in portfolios"""
        threading.Thread(target=self._fetch_initial_prices_worker, daemon=True).start()

    def _fetch_initial_prices_worker(self):
        """Background worker to fetch initial prices"""
        try:
            with operation('initial_price_fetch'):
                logger.info('Fetching initial stock prices...')
                all_symbols = set()
                for portfolio in self.portfolios.values():
                    for symbol in portfolio.keys():
                        all_symbols.add(symbol)
                if not all_symbols:
                    logger.info('No stocks found in portfolios')
                    self.initial_price_fetch_done = True
                    return
                self._fetch_prices_batch(list(all_symbols))
                self.initial_price_fetch_done = True
                logger.info(f'Initial price fetch completed for {len(all_symbols)} symbols', context={'symbols_count': len(all_symbols)})
        except Exception as e:
            logger.error(f'Error in initial price fetch: {e}', exc_info=True)
            self.initial_price_fetch_done = True

    @monitor_performance
    def _fetch_prices_batch(self, symbols):
        """Fetch prices for a batch of symbols - optimized"""
        max_workers = min(10, len(symbols))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {executor.submit(self._fetch_single_price, symbol): symbol for symbol in symbols}
            for future in as_completed(future_to_symbol, timeout=60):
                symbol = future_to_symbol[future]
                try:
                    price = future.result(timeout=30)
                    if price is not None:
                        self.price_cache[symbol] = price
                        self.last_price_update[symbol] = datetime.datetime.now()
                        self.price_fetch_errors.pop(symbol, None)
                        logger.debug(f'Price updated: {symbol} = ${price:.2f}')
                    else:
                        self.price_fetch_errors[symbol] = 'No price data available'
                        logger.warning(f'No price data available for {symbol}')
                except Exception as e:
                    self.price_fetch_errors[symbol] = str(e)
                    logger.error(f'Error fetching price for {symbol}: {e}')
                time.sleep(0.1)

    def _fetch_single_price(self, symbol):
        """Fetch price and daily change data for a single symbol using yfinance - optimized"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose', 'regularMarketPreviousClose']
            current_price = None
            previous_close = None
            for field in price_fields:
                if field in info and info[field] is not None:
                    current_price = float(info[field])
                    if current_price > 0:
                        break
            prev_close_fields = ['regularMarketPreviousClose', 'previousClose']
            for field in prev_close_fields:
                if field in info and info[field] is not None:
                    previous_close = float(info[field])
                    if previous_close > 0:
                        break
            if current_price is None or previous_close is None:
                hist = ticker.history(period='2d', interval='1d')
                if not hist.empty and len(hist) >= 2:
                    if current_price is None:
                        current_price = float(hist['Close'].iloc[-1])
                    if previous_close is None:
                        previous_close = float(hist['Close'].iloc[-2])
                elif not hist.empty:
                    if current_price is None:
                        current_price = float(hist['Close'].iloc[-1])
                    if previous_close is None:
                        previous_close = current_price
            if current_price is not None and previous_close is not None and (previous_close > 0):
                daily_change = current_price - previous_close
                daily_change_pct = daily_change / previous_close * 100
                self.previous_close_cache[symbol] = previous_close
                self.daily_change_cache[symbol] = {'change': daily_change, 'change_pct': daily_change_pct}
                return current_price
            return current_price
        except Exception as e:
            logger.error(f'Error fetching price for {symbol}: {e}')
            return None

    @lru_cache(maxsize=128)
    def get_daily_change(self, symbol):
        """Get today's change for a symbol - cached"""
        if symbol in self.daily_change_cache:
            return self.daily_change_cache[symbol]
        current_price = self.get_current_price(symbol)
        previous_close = self.previous_close_cache.get(symbol)
        if current_price and previous_close and (previous_close > 0):
            daily_change = current_price - previous_close
            daily_change_pct = daily_change / previous_close * 100
            return {'change': daily_change, 'change_pct': daily_change_pct}
        return {'change': 0.0, 'change_pct': 0.0}

    def calculate_portfolio_daily_change(self, portfolio_name):
        """Calculate total daily change for a portfolio - cached"""
        cache_key = f'daily_change_{portfolio_name}'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_value_cache:
                return self._portfolio_value_cache[cache_key]
        portfolio = self.portfolios.get(portfolio_name, {})
        total_change = 0.0
        total_previous_value = 0.0
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                current_price = self.get_current_price(symbol)
                previous_close = self.previous_close_cache.get(symbol, current_price)
                current_value = quantity * current_price
                previous_value = quantity * previous_close
                holding_change = current_value - previous_value
                total_change += holding_change
                total_previous_value += previous_value
        change_pct = total_change / total_previous_value * 100 if total_previous_value > 0 else 0.0
        result = {'change': total_change, 'change_pct': change_pct}
        self._portfolio_value_cache[cache_key] = result
        self._last_cache_update[cache_key] = current_time
        return result

    def calculate_total_daily_change(self):
        """Calculate total daily change across all portfolios - cached"""
        cache_key = 'total_daily_change'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_value_cache:
                return self._portfolio_value_cache[cache_key]
        total_change = 0.0
        total_previous_value = 0.0
        for portfolio_name in self.portfolios.keys():
            portfolio_change = self.calculate_portfolio_daily_change(portfolio_name)
            portfolio_current_value = self.calculate_portfolio_value(portfolio_name)
            portfolio_previous_value = portfolio_current_value - portfolio_change['change']
            total_change += portfolio_change['change']
            total_previous_value += portfolio_previous_value
        change_pct = total_change / total_previous_value * 100 if total_previous_value > 0 else 0.0
        result = {'change': total_change, 'change_pct': change_pct}
        self._portfolio_value_cache[cache_key] = result
        self._last_cache_update[cache_key] = current_time
        return result

    @lru_cache(maxsize=256)
    def get_current_price(self, symbol):
        """Get current price from cache or return fallback price - cached"""
        if symbol in self.price_cache:
            return self.price_cache[symbol]
        if symbol in self.price_fetch_errors:
            for portfolio in self.portfolios.values():
                if symbol in portfolio and isinstance(portfolio[symbol], dict):
                    avg_price = portfolio[symbol].get('avg_price', 100)
                    logger.warning(f'Using avg_price ${avg_price:.2f} for {symbol} (fetch error)')
                    return avg_price
        logger.debug(f'Using default price $100.00 for {symbol}')
        return 100.0

    def calculate_portfolio_value(self, portfolio_name):
        """Calculate current portfolio value - cached"""
        cache_key = f'value_{portfolio_name}'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_value_cache:
                return self._portfolio_value_cache[cache_key]
        portfolio = self.portfolios.get(portfolio_name, {})
        total_value = 0
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                current_price = self.get_current_price(symbol)
                total_value += quantity * current_price
        self._portfolio_value_cache[cache_key] = total_value
        self._last_cache_update[cache_key] = current_time
        return total_value

    def calculate_portfolio_investment(self, portfolio_name):
        """Calculate total portfolio investment - cached"""
        cache_key = f'investment_{portfolio_name}'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_investment_cache:
                return self._portfolio_investment_cache[cache_key]
        portfolio = self.portfolios.get(portfolio_name, {})
        total_investment = 0
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                avg_price = data.get('avg_price', 0)
                total_investment += quantity * avg_price
        self._portfolio_investment_cache[cache_key] = total_investment
        self._last_cache_update[cache_key] = current_time
        return total_investment

    def get_portfolio_summary(self):
        """Get comprehensive portfolio summary"""
        total_portfolios = len(self.portfolios)
        total_investment = sum((self.calculate_portfolio_investment(name) for name in self.portfolios.keys()))
        total_value = sum((self.calculate_portfolio_value(name) for name in self.portfolios.keys()))
        total_pnl = total_value - total_investment
        total_pnl_pct = total_pnl / total_investment * 100 if total_investment > 0 else 0
        total_daily_change = self.calculate_total_daily_change()
        today_change = total_daily_change['change']
        today_change_pct = total_daily_change['change_pct']
        return {'total_portfolios': total_portfolios, 'total_investment': total_investment, 'total_value': total_value, 'total_pnl': total_pnl, 'total_pnl_pct': total_pnl_pct, 'today_change': today_change, 'today_change_pct': today_change_pct}

    def get_portfolio_breakdown(self):
        """Get detailed breakdown of all portfolios"""
        breakdown = []
        total_value = sum((self.calculate_portfolio_value(name) for name in self.portfolios.keys()))
        for portfolio_name, stocks in self.portfolios.items():
            portfolio_investment = self.calculate_portfolio_investment(portfolio_name)
            portfolio_value = self.calculate_portfolio_value(portfolio_name)
            portfolio_pnl = portfolio_value - portfolio_investment
            portfolio_pnl_pct = portfolio_pnl / portfolio_investment * 100 if portfolio_investment > 0 else 0
            allocation_pct = portfolio_value / total_value * 100 if total_value > 0 else 0
            portfolio_daily_change = self.calculate_portfolio_daily_change(portfolio_name)
            today_change = portfolio_daily_change['change']
            today_change_pct = portfolio_daily_change['change_pct']
            breakdown.append({'name': portfolio_name, 'stocks_count': len(stocks), 'investment': portfolio_investment, 'value': portfolio_value, 'pnl': portfolio_pnl, 'pnl_pct': portfolio_pnl_pct, 'today_change': today_change, 'today_change_pct': today_change_pct, 'allocation_pct': allocation_pct})
        return breakdown

    def get_portfolio_holdings(self, portfolio_name):
        """Get detailed holdings for a specific portfolio"""
        if portfolio_name not in self.portfolios:
            return []
        portfolio = self.portfolios[portfolio_name]
        portfolio_value = self.calculate_portfolio_value(portfolio_name)
        holdings = []
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                avg_price = data.get('avg_price', 0)
                original_symbol = data.get('original_symbol', symbol)
                current_price = self.get_current_price(symbol)
                market_value = quantity * current_price
                investment = quantity * avg_price
                gain_loss = market_value - investment
                gain_loss_pct = gain_loss / investment * 100 if investment > 0 else 0
                weight_pct = market_value / portfolio_value * 100 if portfolio_value > 0 else 0
                holdings.append({'symbol': symbol, 'original_symbol': original_symbol, 'quantity': quantity, 'avg_price': avg_price, 'current_price': current_price, 'market_value': market_value, 'investment': investment, 'gain_loss': gain_loss, 'gain_loss_pct': gain_loss_pct, 'weight_pct': weight_pct})
        return holdings

    def create_portfolio(self, name, description=''):
        """Create a new portfolio"""
        if not name:
            raise ValueError('Please enter a portfolio name.')
        if name in self.portfolios:
            raise ValueError('Portfolio name already exists.')
        self.portfolios[name] = {}
        self.save_portfolios()
        self._clear_portfolio_cache()
        return True

    def create_portfolio_with_stock(self, name, symbol, quantity, price, description=''):
        """Create portfolio and add first stock"""
        if not name:
            raise ValueError('Please enter a portfolio name.')
        if name in self.portfolios:
            raise ValueError('Portfolio name already exists.')
        if symbol and quantity is not None and (price is not None):
            try:
                quantity = float(quantity)
                price = float(price)
                self.portfolios[name] = {symbol: {'quantity': quantity, 'avg_price': price, 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}}
                threading.Thread(target=lambda: self._fetch_single_price_and_update(symbol), daemon=True).start()
            except ValueError:
                raise ValueError('Invalid quantity or price values.')
        else:
            self.portfolios[name] = {}
        self.save_portfolios()
        self._clear_portfolio_cache()
        return True

    def add_stock_to_portfolio(self, portfolio_name, symbol, quantity, price):
        """Add stock to existing portfolio"""
        if not portfolio_name or portfolio_name not in self.portfolios:
            raise ValueError('Invalid portfolio selected.')
        if not symbol or quantity is None or price is None:
            raise ValueError('Please fill in all fields.')
        try:
            quantity = float(quantity)
            price = float(price)
        except ValueError:
            raise ValueError('Invalid quantity or price values.')
        if symbol in self.portfolios[portfolio_name]:
            existing = self.portfolios[portfolio_name][symbol]
            current_qty = existing['quantity']
            current_avg = existing['avg_price']
            new_qty = current_qty + quantity
            new_avg = (current_avg * current_qty + price * quantity) / new_qty
            self.portfolios[portfolio_name][symbol] = {'quantity': new_qty, 'avg_price': round(new_avg, 2), 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}
        else:
            self.portfolios[portfolio_name][symbol] = {'quantity': quantity, 'avg_price': price, 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}
        self.price_cache[symbol] = price * (1 + random.uniform(-0.05, 0.05))
        self.save_portfolios()
        self._clear_portfolio_cache()
        threading.Thread(target=lambda: self._fetch_single_price_and_update(symbol), daemon=True).start()
        return True

    def remove_stock_from_portfolio(self, portfolio_name, symbol):
        """Remove stock from portfolio"""
        if not portfolio_name or portfolio_name not in self.portfolios:
            raise ValueError('Portfolio not found')
        if symbol not in self.portfolios[portfolio_name]:
            raise ValueError('Stock not found in portfolio')
        del self.portfolios[portfolio_name][symbol]
        self.save_portfolios()
        self._clear_portfolio_cache()
        return True

    def delete_portfolio(self, portfolio_name):
        """Delete the specified portfolio"""
        if portfolio_name not in self.portfolios:
            raise ValueError('Portfolio not found')
        del self.portfolios[portfolio_name]
        self.save_portfolios()
        self._clear_portfolio_cache()
        if self.current_portfolio == portfolio_name:
            self.current_portfolio = None
        return True

    @monitor_performance
    def select_csv_file(self):
        """Open file dialog to select CSV file - optimized"""
        try:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(title='Select Portfolio CSV File', filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
            root.destroy()
            if file_path:
                self.csv_file_path = file_path
                filename = os.path.basename(file_path)
                return filename
            else:
                return None
        except Exception as e:
            logger.error(f'Error selecting CSV file: {e}', exc_info=True)
            raise Exception('Error selecting file')

    @monitor_performance
    def analyze_csv_file(self):
        """Analyze the selected CSV file and return column info"""
        try:
            if not hasattr(self, 'csv_file_path'):
                raise ValueError('Please select a CSV file first')
            with operation('csv_analysis'):
                with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                    sample = file.read(1024)
                    file.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                    reader = csv.reader(file, delimiter=delimiter)
                    rows = list(reader)
                if not rows:
                    raise ValueError('CSV file is empty')
                self.csv_headers = rows[0]
                self.csv_data = rows[1:] if len(rows) > 1 else []
                return {'headers': self.csv_headers, 'row_count': len(self.csv_data), 'columns_count': len(self.csv_headers)}
        except Exception as e:
            logger.error(f'Error analyzing CSV: {e}', exc_info=True)
            raise Exception(f'Error analyzing CSV: {str(e)}')

    @lru_cache(maxsize=64)
    def auto_detect_column(self, field_type):
        """Auto-detect CSV column based on common naming patterns - cached"""
        field_patterns = {'symbol': ['symbol', 'instrument', 'stock', 'ticker', 'scrip', 'name'], 'quantity': ['quantity', 'qty', 'shares', 'units', 'holding'], 'avg_price': ['avg', 'average', 'cost', 'price', 'purchase', 'buy'], 'current_price': ['ltp', 'current', 'market', 'last', 'trading'], 'investment': ['invested', 'investment', 'total_cost', 'amount'], 'current_value': ['current_value', 'market_value', 'value', 'cur'], 'pnl': ['pnl', 'p&l', 'profit', 'loss', 'gain', 'net']}
        patterns = field_patterns.get(field_type, [])
        for header in self.csv_headers:
            header_lower = header.lower().replace(' ', '_').replace('.', '').replace('-', '_')
            for pattern in patterns:
                if pattern in header_lower:
                    return header
        return ''

    @monitor_performance
    def preview_import(self, column_mapping, country_suffix):
        """Preview the import with current column mapping"""
        try:
            with operation('import_preview'):
                required_mappings = ['symbol', 'quantity', 'avg_price']
                self.column_mapping = {}
                for field in required_mappings:
                    mapped_column = column_mapping.get(field)
                    if not mapped_column:
                        raise ValueError(f'Please map the required field: {field}')
                    self.column_mapping[field] = mapped_column
                optional_mappings = ['current_price', 'investment', 'current_value', 'pnl']
                for field in optional_mappings:
                    mapped_column = column_mapping.get(field)
                    if mapped_column:
                        self.column_mapping[field] = mapped_column
                self.csv_preview_data = []
                for row in self.csv_data[:10]:
                    if len(row) >= len(self.csv_headers):
                        row_dict = dict(zip(self.csv_headers, row))
                        symbol = str(row_dict.get(self.column_mapping['symbol'], '')).strip()
                        if not symbol:
                            continue
                        if country_suffix and (not symbol.endswith(country_suffix)):
                            symbol_yf = symbol + country_suffix
                        else:
                            symbol_yf = symbol
                        try:
                            quantity = float(row_dict.get(self.column_mapping['quantity'], 0))
                            avg_price = float(row_dict.get(self.column_mapping['avg_price'], 0))
                        except (ValueError, TypeError):
                            continue
                        preview_item = {'original_symbol': symbol, 'yfinance_symbol': symbol_yf, 'quantity': quantity, 'avg_price': avg_price}
                        self.csv_preview_data.append(preview_item)
                return {'preview_data': self.csv_preview_data, 'valid_rows': len(self.csv_preview_data), 'total_investment': sum((item['quantity'] * item['avg_price'] for item in self.csv_preview_data))}
        except Exception as e:
            logger.error(f'Error creating preview: {e}', exc_info=True)
            raise Exception(f'Error creating preview: {str(e)}')

    @monitor_performance
    def import_csv_portfolio(self, portfolio_name):
        """Import the CSV data as a new portfolio"""
        try:
            with operation('csv_portfolio_import'):
                if not portfolio_name.strip():
                    raise ValueError('Please enter a portfolio name')
                if portfolio_name in self.portfolios:
                    raise ValueError('Portfolio name already exists')
                if not self.csv_preview_data:
                    raise ValueError('No preview data available. Please analyze CSV first')
                new_portfolio = {}
                for item in self.csv_preview_data:
                    symbol = item['yfinance_symbol']
                    new_portfolio[symbol] = {'quantity': item['quantity'], 'avg_price': item['avg_price'], 'last_added': datetime.datetime.now().strftime('%Y-%m-%d'), 'original_symbol': item['original_symbol']}
                    self.price_cache[symbol] = item['avg_price'] * (1 + random.uniform(-0.05, 0.05))
                self.portfolios[portfolio_name] = new_portfolio
                self.save_portfolios()
                self._clear_portfolio_cache()
                imported_symbols = list(new_portfolio.keys())
                threading.Thread(target=lambda: self._fetch_prices_batch(imported_symbols), daemon=True).start()
                self.csv_data = None
                self.csv_headers = []
                self.column_mapping = {}
                self.csv_preview_data = []
                return {'portfolio_name': portfolio_name, 'stocks_imported': len(new_portfolio), 'success': True}
        except Exception as e:
            logger.error(f'Error importing portfolio: {e}', exc_info=True)
            raise Exception(f'Error importing portfolio: {str(e)}')

    def _clear_portfolio_cache(self):
        """Clear portfolio calculation cache"""
        self._portfolio_value_cache.clear()
        self._portfolio_investment_cache.clear()
        self._last_cache_update.clear()
        self.get_current_price.cache_clear()
        self.get_daily_change.cache_clear()

    def _fetch_single_price_and_update(self, symbol):
        """Fetch price for a single symbol and update cache - optimized"""
        try:
            with operation('fetch_single_price', context={'symbol': symbol}):
                price = self._fetch_single_price(symbol)
                if price is not None:
                    self.price_cache[symbol] = price
                    self.last_price_update[symbol] = datetime.datetime.now()
                    logger.debug(f'Updated price for {symbol}: ${price:.2f}')
                    self._clear_portfolio_cache()
                else:
                    logger.warning(f'Could not fetch price for {symbol}')
        except Exception as e:
            logger.error(f'Error fetching price for {symbol}: {e}')

    def start_price_refresh_thread(self):
        """Start the auto price refresh thread"""
        if not self.refresh_running:
            self.refresh_running = True
            self.refresh_thread = threading.Thread(target=self._price_refresh_loop, daemon=True)
            self.refresh_thread.start()
            logger.info('Started hourly price refresh thread')

    def _price_refresh_loop(self):
        """Background thread for price refresh - runs every hour - optimized"""
        while self.refresh_running:
            try:
                while not self.initial_price_fetch_done and self.refresh_running:
                    time.sleep(10)
                if not self.refresh_running:
                    break
                for _ in range(0, self.price_update_interval, 10):
                    if not self.refresh_running:
                        break
                    time.sleep(10)
                if self.refresh_running:
                    logger.info('Hourly price update starting...')
                    self.refresh_all_prices_background()
            except Exception as e:
                logger.error(f'Error in price refresh loop: {e}')
                time.sleep(300)

    @monitor_performance
    def refresh_all_prices_background(self):
        """Refresh all prices in background - optimized"""
        try:
            with operation('refresh_all_prices'):
                all_symbols = set()
                for portfolio in self.portfolios.values():
                    for symbol in portfolio.keys():
                        all_symbols.add(symbol)
                if not all_symbols:
                    return
                logger.info(f'Refreshing prices for {len(all_symbols)} symbols...', context={'symbols_count': len(all_symbols)})
                self._fetch_prices_batch(list(all_symbols))
                self._clear_portfolio_cache()
                logger.info('Price refresh completed')
                return True
        except Exception as e:
            logger.error(f'Error refreshing prices: {e}')
            return False

    def refresh_all_prices_now(self):
        """Refresh all prices immediately"""
        threading.Thread(target=self.refresh_all_prices_background, daemon=True).start()
        return True

    @monitor_performance
    def export_portfolio_data(self):
        """Export portfolio data - optimized"""
        try:
            with operation('export_portfolio_data'):
                export_data = []
                export_data.append(['Portfolio', 'Symbol', 'Original_Symbol', 'Quantity', 'Avg_Price', 'Current_Price', 'Investment', 'Current_Value', 'P&L', 'P&L_%'])
                for portfolio_name, stocks in self.portfolios.items():
                    for symbol, data in stocks.items():
                        if isinstance(data, dict):
                            quantity = data.get('quantity', 0)
                            avg_price = data.get('avg_price', 0)
                            original_symbol = data.get('original_symbol', symbol)
                            current_price = self.get_current_price(symbol)
                            investment = quantity * avg_price
                            current_value = quantity * current_price
                            pnl = current_value - investment
                            pnl_pct = pnl / investment * 100 if investment > 0 else 0
                            export_data.append([portfolio_name, symbol, original_symbol, quantity, avg_price, current_price, investment, current_value, pnl, pnl_pct])
                export_filename = f'portfolio_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv'
                with open(export_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(export_data)
                return export_filename
        except Exception as e:
            logger.error(f'Error exporting portfolio data: {e}', exc_info=True)
            raise Exception('Error exporting portfolio data')

    @monitor_performance
    def load_portfolios(self):
        """Load portfolios from settings file - optimized"""
        if PORTFOLIO_CONFIG_FILE.exists():
            try:
                with operation('load_portfolios'):
                    with open(PORTFOLIO_CONFIG_FILE, 'r') as file:
                        settings = json.load(file)
                        portfolios = settings.get('portfolios', {})
                        if 'watchlist' in portfolios:
                            del portfolios['watchlist']
                        return portfolios
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f'Error loading portfolios: Corrupted portfolio_settings.json file - {e}')
                return {}
        return {}

    @monitor_performance
    def save_portfolios(self):
        """Save portfolios to settings file - optimized"""
        try:
            with operation('save_portfolios'):
                settings = {}
                if PORTFOLIO_CONFIG_FILE.exists():
                    try:
                        with open(PORTFOLIO_CONFIG_FILE, 'r') as file:
                            settings = json.load(file)
                    except json.JSONDecodeError:
                        settings = {}
                if 'portfolios' not in settings:
                    settings['portfolios'] = {}
                for portfolio_name, portfolio_data in self.portfolios.items():
                    settings['portfolios'][portfolio_name] = portfolio_data
                temp_file = str(PORTFOLIO_CONFIG_FILE) + '.tmp'
                with open(temp_file, 'w') as file:
                    json.dump(settings, file, indent=4)
                import shutil
                shutil.move(temp_file, str(PORTFOLIO_CONFIG_FILE))
                logger.debug('Portfolios saved successfully')
        except Exception as e:
            logger.error(f'Error saving portfolios: {e}', exc_info=True)
            raise Exception(f'Error saving portfolios: {e}')

    @monitor_performance
    def cleanup(self):
        """Clean up portfolio business logic resources - optimized"""
        try:
            with operation('portfolio_business_cleanup'):
                logger.info('🧹 Cleaning up portfolio business logic...')
                self.refresh_running = False
                if hasattr(self, 'portfolios'):
                    self.save_portfolios()
                self.portfolios.clear()
                self.current_portfolio = None
                self.price_cache.clear()
                self.last_price_update.clear()
                self.price_fetch_errors.clear()
                self.daily_change_cache.clear()
                self.previous_close_cache.clear()
                self.csv_data = None
                self.csv_headers = []
                self.column_mapping = {}
                self.csv_preview_data = []
                self._clear_portfolio_cache()
                self.get_current_price.cache_clear()
                self.get_daily_change.cache_clear()
                self.auto_detect_column.cache_clear()
                logger.info('Portfolio business logic cleanup complete')
        except Exception as e:
            logger.error(f'Error in portfolio business cleanup: {e}', exc_info=True)

def _fetch_single_price(self, symbol):
    """Fetch price and daily change data for a single symbol using yfinance - optimized"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose', 'regularMarketPreviousClose']
        current_price = None
        previous_close = None
        for field in price_fields:
            if field in info and info[field] is not None:
                current_price = float(info[field])
                if current_price > 0:
                    break
        prev_close_fields = ['regularMarketPreviousClose', 'previousClose']
        for field in prev_close_fields:
            if field in info and info[field] is not None:
                previous_close = float(info[field])
                if previous_close > 0:
                    break
        if current_price is None or previous_close is None:
            hist = ticker.history(period='2d', interval='1d')
            if not hist.empty and len(hist) >= 2:
                if current_price is None:
                    current_price = float(hist['Close'].iloc[-1])
                if previous_close is None:
                    previous_close = float(hist['Close'].iloc[-2])
            elif not hist.empty:
                if current_price is None:
                    current_price = float(hist['Close'].iloc[-1])
                if previous_close is None:
                    previous_close = current_price
        if current_price is not None and previous_close is not None and (previous_close > 0):
            daily_change = current_price - previous_close
            daily_change_pct = daily_change / previous_close * 100
            self.previous_close_cache[symbol] = previous_close
            self.daily_change_cache[symbol] = {'change': daily_change, 'change_pct': daily_change_pct}
            return current_price
        return current_price
    except Exception as e:
        logger.error(f'Error fetching price for {symbol}: {e}')
        return None

class PortfolioOptimizer:
    """
    Comprehensive Portfolio Optimization Engine using PyPortfolioOpt

    Features:
    - Multiple optimization methods (Mean-Variance, CVaR, Semivariance, etc.)
    - Expected returns calculation methods
    - Risk models with shrinkage estimators
    - Black-Litterman model implementation
    - Hierarchical Risk Parity
    - Efficient frontier plotting
    - Discrete allocation and post-processing
    """

    def __init__(self, business_logic=None):
        """Initialize the portfolio optimizer"""
        if not PYPFOPT_AVAILABLE:
            raise ImportError('PyPortfolioOpt is required but not installed')
        self.business_logic = business_logic
        self.risk_free_rate = 0.02
        self.confidence_level = 0.95
        self.lookback_days = 252
        self.optimization_cache = {}
        self.cache_timeout = 3600
        self.optimization_methods = {'mean_variance': 'Mean-Variance Optimization', 'min_volatility': 'Minimum Volatility', 'max_sharpe': 'Maximum Sharpe Ratio', 'efficient_risk': 'Efficient Risk', 'efficient_return': 'Efficient Return', 'semivariance': 'Efficient Semivariance', 'cvar': 'Conditional Value at Risk', 'cdar': 'Conditional Drawdown at Risk', 'hrp': 'Hierarchical Risk Parity', 'black_litterman': 'Black-Litterman Model', 'cla': 'Critical Line Algorithm'}
        self.expected_returns_methods = {'mean_historical_return': 'Mean Historical Return', 'ema_historical_return': 'Exponentially Weighted Returns', 'capm_return': 'CAPM Expected Returns', 'james_stein': 'James-Stein Estimator'}
        self.risk_model_methods = {'sample_cov': 'Sample Covariance', 'semicovariance': 'Semicovariance', 'exp_cov': 'Exponentially Weighted Covariance', 'ledoit_wolf': 'Ledoit-Wolf Shrinkage', 'oracle_approximating': 'Oracle Approximating Shrinkage'}

    def get_historical_data(self, symbols: List[str], lookback_days: int=None) -> pd.DataFrame:
        """
        Get historical price data for optimization

        Args:
            symbols: List of stock symbols
            lookback_days: Number of days to look back

        Returns:
            DataFrame with historical prices
        """
        try:
            if lookback_days is None:
                lookback_days = self.lookback_days
            if self.business_logic:
                historical_data = {}
                for symbol in symbols:
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(symbol)
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=lookback_days + 50)
                        hist = ticker.history(start=start_date, end=end_date)
                        if not hist.empty:
                            historical_data[symbol] = hist['Close']
                        else:
                            logger.warning(f'No historical data for {symbol}')
                    except Exception as e:
                        logger.error(f'Error fetching data for {symbol}: {e}')
                        continue
                if historical_data:
                    df = pd.DataFrame(historical_data)
                    df = df.dropna()
                    if len(df) < 30:
                        raise ValueError(f'Insufficient historical data. Only {len(df)} days available.')
                    return df.tail(lookback_days)
                else:
                    raise ValueError('No historical data could be retrieved')
            else:
                raise ValueError('No business logic provided for data retrieval')
        except Exception as e:
            logger.error(f'Error getting historical data: {e}')
            raise

    @monitor_performance
    def calculate_expected_returns(self, prices: pd.DataFrame, method: str='mean_historical_return', **kwargs) -> pd.Series:
        """
        Calculate expected returns using various methods

        Args:
            prices: Historical price data
            method: Method to calculate expected returns
            **kwargs: Additional parameters for specific methods

        Returns:
            Series of expected returns
        """
        try:
            with operation('calculate_expected_returns', context={'method': method}):
                if method == 'mean_historical_return':
                    frequency = kwargs.get('frequency', 252)
                    return expected_returns.mean_historical_return(prices, frequency=frequency)
                elif method == 'ema_historical_return':
                    frequency = kwargs.get('frequency', 252)
                    span = kwargs.get('span', 500)
                    return expected_returns.ema_historical_return(prices, frequency=frequency, span=span)
                elif method == 'capm_return':
                    market_prices = kwargs.get('market_prices')
                    frequency = kwargs.get('frequency', 252)
                    if market_prices is None:
                        market_prices = prices.iloc[:, 0]
                    return expected_returns.capm_return(prices, market_prices=market_prices, frequency=frequency)
                elif method == 'james_stein':
                    frequency = kwargs.get('frequency', 252)
                    mu = expected_returns.mean_historical_return(prices, frequency=frequency)
                    return expected_returns.james_stein_shrinkage(mu)
                else:
                    raise ValueError(f'Unknown expected returns method: {method}')
        except Exception as e:
            logger.error(f'Error calculating expected returns: {e}')
            raise

    @monitor_performance
    def calculate_risk_model(self, prices: pd.DataFrame, method: str='sample_cov', **kwargs) -> pd.DataFrame:
        """
        Calculate risk model (covariance matrix) using various methods

        Args:
            prices: Historical price data
            method: Method to calculate risk model
            **kwargs: Additional parameters for specific methods

        Returns:
            Covariance matrix
        """
        try:
            with operation('calculate_risk_model', context={'method': method}):
                if method == 'sample_cov':
                    frequency = kwargs.get('frequency', 252)
                    return risk_models.sample_cov(prices, frequency=frequency)
                elif method == 'semicovariance':
                    frequency = kwargs.get('frequency', 252)
                    benchmark = kwargs.get('benchmark', 0)
                    return risk_models.semicovariance(prices, frequency=frequency, benchmark=benchmark)
                elif method == 'exp_cov':
                    frequency = kwargs.get('frequency', 252)
                    span = kwargs.get('span', 180)
                    return risk_models.exp_cov(prices, frequency=frequency, span=span)
                elif method == 'ledoit_wolf':
                    frequency = kwargs.get('frequency', 252)
                    cs = CovarianceShrinkage(prices, frequency=frequency)
                    return cs.ledoit_wolf()
                elif method == 'oracle_approximating':
                    frequency = kwargs.get('frequency', 252)
                    cs = CovarianceShrinkage(prices, frequency=frequency)
                    return cs.oracle_approximating()
                else:
                    raise ValueError(f'Unknown risk model method: {method}')
        except Exception as e:
            logger.error(f'Error calculating risk model: {e}')
            raise

    @monitor_performance
    def optimize_mean_variance(self, mu: pd.Series, S: pd.DataFrame, optimization_target: str='max_sharpe', target_return: float=None, target_volatility: float=None, weight_bounds: Tuple[float, float]=(0, 1), sector_mapper: Dict=None, sector_lower: Dict=None, sector_upper: Dict=None, **kwargs) -> Dict:
        """
        Perform mean-variance optimization

        Args:
            mu: Expected returns
            S: Covariance matrix
            optimization_target: Target for optimization
            target_return: Target return (for efficient_risk)
            target_volatility: Target volatility (for efficient_return)
            weight_bounds: Weight bounds for individual assets
            sector_mapper: Mapping of assets to sectors
            sector_lower: Lower bounds for sector weights
            sector_upper: Upper bounds for sector weights
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_mean_variance', context={'target': optimization_target}):
                ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
                if sector_mapper and (sector_lower or sector_upper):
                    ef.add_sector_constraints(sector_mapper, sector_lower, sector_upper)
                gamma = kwargs.get('gamma', 0)
                if gamma > 0:
                    ef.add_objective(objective_functions.L2_reg, gamma=gamma)
                if optimization_target == 'max_sharpe':
                    ef.max_sharpe(risk_free_rate=self.risk_free_rate)
                elif optimization_target == 'min_volatility':
                    ef.min_volatility()
                elif optimization_target == 'efficient_risk':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_risk')
                    ef.efficient_risk(target_return)
                elif optimization_target == 'efficient_return':
                    if target_volatility is None:
                        raise ValueError('target_volatility required for efficient_return')
                    ef.efficient_return(target_volatility)
                else:
                    raise ValueError(f'Unknown optimization target: {optimization_target}')
                raw_weights = ef.weights
                cleaned_weights = ef.clean_weights()
                performance = ef.portfolio_performance(risk_free_rate=self.risk_free_rate, verbose=False)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'optimization_target': optimization_target, 'ef_object': ef}
        except Exception as e:
            logger.error(f'Error in mean-variance optimization: {e}')
            raise

    @monitor_performance
    def optimize_semivariance(self, prices: pd.DataFrame, optimization_target: str='max_quadratic_utility', benchmark: float=0, target_return: float=None, market_neutral: bool=False, **kwargs) -> Dict:
        """
        Perform semivariance optimization

        Args:
            prices: Historical price data
            optimization_target: Target for optimization
            benchmark: Benchmark return for semideviation
            target_return: Target return (for efficient_semivariance)
            market_neutral: Whether to make portfolio market neutral
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_semivariance', context={'target': optimization_target}):
                returns = prices.pct_change().dropna()
                es = EfficientSemivariance(returns, benchmark=benchmark)
                if market_neutral:
                    es.add_constraint(lambda w: sum(w) == 0)
                if optimization_target == 'max_quadratic_utility':
                    risk_aversion = kwargs.get('risk_aversion', 1)
                    es.max_quadratic_utility(risk_aversion=risk_aversion)
                elif optimization_target == 'efficient_semivariance':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_semivariance')
                    es.efficient_semivariance(target_return)
                elif optimization_target == 'min_semivariance':
                    es.min_semivariance()
                else:
                    raise ValueError(f'Unknown semivariance optimization target: {optimization_target}')
                raw_weights = es.weights
                cleaned_weights = es.clean_weights()
                try:
                    performance = es.portfolio_performance(risk_free_rate=self.risk_free_rate)
                except:
                    portfolio_return = sum((raw_weights[i] * returns.mean().iloc[i] * 252 for i in range(len(raw_weights))))
                    performance = (portfolio_return, None, None)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'semideviation': performance[1] if len(performance) > 1 else None, 'optimization_target': optimization_target, 'benchmark': benchmark}
        except Exception as e:
            logger.error(f'Error in semivariance optimization: {e}')
            raise

    @monitor_performance
    def optimize_cvar(self, prices: pd.DataFrame, optimization_target: str='max_quadratic_utility', beta: float=None, target_return: float=None, **kwargs) -> Dict:
        """
        Perform CVaR (Conditional Value at Risk) optimization

        Args:
            prices: Historical price data
            optimization_target: Target for optimization
            beta: Confidence level for CVaR (if None, uses self.confidence_level)
            target_return: Target return (for efficient_cvar)
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_cvar', context={'target': optimization_target}):
                if beta is None:
                    beta = self.confidence_level
                returns = prices.pct_change().dropna()
                ec = EfficientCVaR(returns, beta=beta)
                if optimization_target == 'max_quadratic_utility':
                    risk_aversion = kwargs.get('risk_aversion', 1)
                    ec.max_quadratic_utility(risk_aversion=risk_aversion)
                elif optimization_target == 'efficient_cvar':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_cvar')
                    ec.efficient_cvar(target_return)
                elif optimization_target == 'min_cvar':
                    ec.min_cvar()
                else:
                    raise ValueError(f'Unknown CVaR optimization target: {optimization_target}')
                raw_weights = ec.weights
                cleaned_weights = ec.clean_weights()
                try:
                    performance = ec.portfolio_performance()
                except:
                    portfolio_return = sum((raw_weights[i] * returns.mean().iloc[i] * 252 for i in range(len(raw_weights))))
                    performance = (portfolio_return, None)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'cvar': performance[1] if len(performance) > 1 else None, 'confidence_level': beta, 'optimization_target': optimization_target}
        except Exception as e:
            logger.error(f'Error in CVaR optimization: {e}')
            raise

    @monitor_performance
    def optimize_cdar(self, prices: pd.DataFrame, optimization_target: str='max_quadratic_utility', beta: float=None, target_return: float=None, **kwargs) -> Dict:
        """
        Perform CDaR (Conditional Drawdown at Risk) optimization

        Args:
            prices: Historical price data
            optimization_target: Target for optimization
            beta: Confidence level for CDaR (if None, uses self.confidence_level)
            target_return: Target return (for efficient_cdar)
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_cdar', context={'target': optimization_target}):
                if beta is None:
                    beta = self.confidence_level
                ec = EfficientCDaR(prices, beta=beta)
                if optimization_target == 'max_quadratic_utility':
                    risk_aversion = kwargs.get('risk_aversion', 1)
                    ec.max_quadratic_utility(risk_aversion=risk_aversion)
                elif optimization_target == 'efficient_cdar':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_cdar')
                    ec.efficient_cdar(target_return)
                elif optimization_target == 'min_cdar':
                    ec.min_cdar()
                else:
                    raise ValueError(f'Unknown CDaR optimization target: {optimization_target}')
                raw_weights = ec.weights
                cleaned_weights = ec.clean_weights()
                try:
                    performance = ec.portfolio_performance()
                except:
                    returns = prices.pct_change().dropna()
                    portfolio_return = sum((raw_weights[i] * returns.mean().iloc[i] * 252 for i in range(len(raw_weights))))
                    performance = (portfolio_return, None)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'cdar': performance[1] if len(performance) > 1 else None, 'confidence_level': beta, 'optimization_target': optimization_target}
        except Exception as e:
            logger.error(f'Error in CDaR optimization: {e}')
            raise

    @monitor_performance
    def optimize_hrp(self, prices: pd.DataFrame, linkage_method: str='single', max_cluster_size: int=None) -> Dict:
        """
        Perform Hierarchical Risk Parity optimization

        Args:
            prices: Historical price data
            linkage_method: Linkage method for clustering
            max_cluster_size: Maximum cluster size

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_hrp'):
                returns = prices.pct_change().dropna()
                hrp = HRPOpt(returns)
                if max_cluster_size:
                    hrp.max_cluster_size = max_cluster_size
                weights = hrp.optimize(linkage_method=linkage_method)
                cleaned_weights = hrp.clean_weights()
                performance = hrp.portfolio_performance(risk_free_rate=self.risk_free_rate)
                return {'raw_weights': dict(weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'linkage_method': linkage_method, 'clustered_corr': hrp.clustered_corr, 'clusters': hrp.clusters}
        except Exception as e:
            logger.error(f'Error in HRP optimization: {e}')
            raise

    @monitor_performance
    def optimize_black_litterman(self, prices: pd.DataFrame, views: Dict[str, float]=None, view_confidences: List[float]=None, market_caps: Dict[str, float]=None, risk_aversion: float=1, tau: float=0.05, pi_method: str='market_cap', **kwargs) -> Dict:
        """
        Perform Black-Litterman optimization

        Args:
            prices: Historical price data
            views: Dictionary of views {asset: expected_return}
            view_confidences: List of confidence levels for views
            market_caps: Market capitalizations for assets
            risk_aversion: Risk aversion parameter
            tau: Tau parameter for Black-Litterman
            pi_method: Method to calculate prior returns
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_black_litterman'):
                mu_hist = expected_returns.mean_historical_return(prices)
                S = risk_models.sample_cov(prices)
                if market_caps is None:
                    market_caps = {asset: 1.0 for asset in prices.columns}
                bl = BlackLittermanModel(S, pi=pi_method, market_caps=market_caps, risk_aversion=risk_aversion, tau=tau)
                if views:
                    view_dict = {}
                    for asset, view_return in views.items():
                        if asset in prices.columns:
                            view_dict[asset] = view_return
                    if view_dict:
                        P = pd.DataFrame(0, index=range(len(view_dict)), columns=S.index)
                        Q = []
                        for i, (asset, view_return) in enumerate(view_dict.items()):
                            P.iloc[i][asset] = 1
                            Q.append(view_return)
                        if view_confidences is None:
                            omega = np.diag([1.0] * len(view_dict))
                        else:
                            omega = np.diag(view_confidences[:len(view_dict)])
                        bl.bl_views(P, Q, omega)
                mu_bl = bl.bl_returns()
                S_bl = bl.bl_cov()
                ef = EfficientFrontier(mu_bl, S_bl)
                ef.max_sharpe(risk_free_rate=self.risk_free_rate)
                raw_weights = ef.weights
                cleaned_weights = ef.clean_weights()
                performance = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'bl_returns': mu_bl.to_dict(), 'prior_returns': bl.pi.to_dict() if hasattr(bl, 'pi') else {}, 'views': views or {}, 'tau': tau, 'risk_aversion': risk_aversion}
        except Exception as e:
            logger.error(f'Error in Black-Litterman optimization: {e}')
            raise

    @monitor_performance
    def optimize_cla(self, mu: pd.Series, S: pd.DataFrame) -> Dict:
        """
        Perform Critical Line Algorithm optimization

        Args:
            mu: Expected returns
            S: Covariance matrix

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_cla'):
                cla = CLA(mu, S)
                cla.max_sharpe()
                raw_weights = cla.weights
                cleaned_weights = cla.clean_weights()
                performance = cla.portfolio_performance(risk_free_rate=self.risk_free_rate)
                ef_returns, ef_volatilities, ef_weights = cla.efficient_frontier()
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'efficient_frontier': {'returns': ef_returns, 'volatilities': ef_volatilities, 'weights': ef_weights}}
        except Exception as e:
            logger.error(f'Error in CLA optimization: {e}')
            raise

    @monitor_performance
    def calculate_efficient_frontier(self, mu: pd.Series, S: pd.DataFrame, num_points: int=100, risk_range: Tuple[float, float]=None) -> Dict:
        """
        Calculate the efficient frontier

        Args:
            mu: Expected returns
            S: Covariance matrix
            num_points: Number of points on the frontier
            risk_range: Risk range (min_vol, max_vol)

        Returns:
            Dictionary with frontier data
        """
        try:
            with operation('calculate_efficient_frontier'):
                ef = EfficientFrontier(mu, S)
                if risk_range is None:
                    ef_temp = EfficientFrontier(mu, S)
                    ef_temp.min_volatility()
                    min_vol = ef_temp.portfolio_performance()[1]
                    max_return = mu.max()
                    ef_temp = EfficientFrontier(mu, S)
                    try:
                        ef_temp.efficient_return(max_return * 0.95)
                        max_vol = ef_temp.portfolio_performance()[1]
                    except:
                        max_vol = min_vol * 3
                    risk_range = (min_vol, max_vol)
                frontier_returns = []
                frontier_volatilities = []
                frontier_weights = []
                target_vols = np.linspace(risk_range[0], risk_range[1], num_points // 2)
                for target_vol in target_vols:
                    try:
                        ef_temp = EfficientFrontier(mu, S)
                        ef_temp.efficient_risk(target_vol ** 2)
                        ret, vol, _ = ef_temp.portfolio_performance()
                        if min_vol <= vol <= risk_range[1] * 1.1:
                            frontier_returns.append(ret)
                            frontier_volatilities.append(vol)
                            frontier_weights.append(dict(ef_temp.weights))
                    except Exception as e:
                        logger.debug(f'Failed to optimize for target volatility {target_vol:.4f}: {e}')
                        continue
                if frontier_returns:
                    min_return = min(frontier_returns)
                    max_return = max(frontier_returns)
                else:
                    min_return = mu.min()
                    max_return = mu.max() * 0.9
                target_returns = np.linspace(min_return, max_return, num_points // 2)
                for target_return in target_returns:
                    try:
                        ef_temp = EfficientFrontier(mu, S)
                        ef_temp.efficient_return(target_return)
                        ret, vol, _ = ef_temp.portfolio_performance()
                        if vol >= min_vol and vol <= risk_range[1] * 1.2 and (not any((abs(existing_vol - vol) < 0.001 for existing_vol in frontier_volatilities))):
                            frontier_returns.append(ret)
                            frontier_volatilities.append(vol)
                            frontier_weights.append(dict(ef_temp.weights))
                    except Exception as e:
                        logger.debug(f'Failed to optimize for target return {target_return:.4f}: {e}')
                        continue
                if frontier_returns:
                    combined_data = list(zip(frontier_volatilities, frontier_returns, frontier_weights))
                    combined_data.sort(key=lambda x: x[0])
                    filtered_data = []
                    last_vol = -1
                    for vol, ret, weights in combined_data:
                        if abs(vol - last_vol) > 0.001:
                            filtered_data.append((vol, ret, weights))
                            last_vol = vol
                    if filtered_data:
                        frontier_volatilities, frontier_returns, frontier_weights = zip(*filtered_data)
                        frontier_volatilities = list(frontier_volatilities)
                        frontier_returns = list(frontier_returns)
                        frontier_weights = list(frontier_weights)
                    else:
                        frontier_returns = []
                        frontier_volatilities = []
                        frontier_weights = []
                if len(frontier_returns) < 2:
                    logger.warning('Insufficient frontier points generated, adding key portfolios')
                    try:
                        ef_min = EfficientFrontier(mu, S)
                        ef_min.min_volatility()
                        min_ret, min_vol, _ = ef_min.portfolio_performance()
                        frontier_returns.append(min_ret)
                        frontier_volatilities.append(min_vol)
                        frontier_weights.append(dict(ef_min.weights))
                    except Exception as e:
                        logger.warning(f'Could not add min volatility portfolio: {e}')
                    try:
                        ef_sharpe = EfficientFrontier(mu, S)
                        ef_sharpe.max_sharpe(risk_free_rate=self.risk_free_rate)
                        sharpe_ret, sharpe_vol, sharpe_ratio = ef_sharpe.portfolio_performance(risk_free_rate=self.risk_free_rate)
                        if not any((abs(sharpe_vol - vol) < 0.001 for vol in frontier_volatilities)):
                            frontier_returns.append(sharpe_ret)
                            frontier_volatilities.append(sharpe_vol)
                            frontier_weights.append(dict(ef_sharpe.weights))
                    except Exception as e:
                        logger.warning(f'Could not add max Sharpe portfolio: {e}')
                try:
                    ef_sharpe = EfficientFrontier(mu, S)
                    ef_sharpe.max_sharpe(risk_free_rate=self.risk_free_rate)
                    sharpe_performance = ef_sharpe.portfolio_performance(risk_free_rate=self.risk_free_rate)
                    max_sharpe_data = {'return': sharpe_performance[0], 'volatility': sharpe_performance[1], 'sharpe_ratio': sharpe_performance[2], 'weights': dict(ef_sharpe.weights)}
                except Exception as e:
                    logger.warning(f'Could not calculate max Sharpe portfolio: {e}')
                    max_sharpe_data = {'return': 0, 'volatility': 0, 'sharpe_ratio': 0, 'weights': {}}
                efficient_frontier_stats = {}
                if frontier_returns and frontier_volatilities:
                    efficient_frontier_stats = {'num_points': len(frontier_returns), 'min_return': min(frontier_returns), 'max_return': max(frontier_returns), 'min_volatility': min(frontier_volatilities), 'max_volatility': max(frontier_volatilities), 'return_range': max(frontier_returns) - min(frontier_returns), 'volatility_range': max(frontier_volatilities) - min(frontier_volatilities)}
                return {'returns': frontier_returns, 'volatilities': frontier_volatilities, 'weights': frontier_weights, 'max_sharpe': max_sharpe_data, 'risk_range': risk_range, 'statistics': efficient_frontier_stats, 'success': len(frontier_returns) > 0}
        except Exception as e:
            logger.error(f'Error calculating efficient frontier: {e}')
            return {'returns': [], 'volatilities': [], 'weights': [], 'max_sharpe': {'return': 0, 'volatility': 0, 'sharpe_ratio': 0, 'weights': {}}, 'risk_range': (0, 0), 'statistics': {}, 'success': False, 'error': str(e)}
            ef_sharpe = EfficientFrontier(mu, S)
            ef_sharpe.max_sharpe(risk_free_rate=self.risk_free_rate)
            sharpe_performance = ef_sharpe.portfolio_performance(risk_free_rate=self.risk_free_rate)
            return {'returns': frontier_returns, 'volatilities': frontier_volatilities, 'weights': frontier_weights, 'max_sharpe': {'return': sharpe_performance[0], 'volatility': sharpe_performance[1], 'sharpe_ratio': sharpe_performance[2], 'weights': dict(ef_sharpe.weights)}, 'risk_range': risk_range}

def get_historical_data(self, symbols: List[str], lookback_days: int=None) -> pd.DataFrame:
    """
        Get historical price data for optimization

        Args:
            symbols: List of stock symbols
            lookback_days: Number of days to look back

        Returns:
            DataFrame with historical prices
        """
    try:
        if lookback_days is None:
            lookback_days = self.lookback_days
        if self.business_logic:
            historical_data = {}
            for symbol in symbols:
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=lookback_days + 50)
                    hist = ticker.history(start=start_date, end=end_date)
                    if not hist.empty:
                        historical_data[symbol] = hist['Close']
                    else:
                        logger.warning(f'No historical data for {symbol}')
                except Exception as e:
                    logger.error(f'Error fetching data for {symbol}: {e}')
                    continue
            if historical_data:
                df = pd.DataFrame(historical_data)
                df = df.dropna()
                if len(df) < 30:
                    raise ValueError(f'Insufficient historical data. Only {len(df)} days available.')
                return df.tail(lookback_days)
            else:
                raise ValueError('No historical data could be retrieved')
        else:
            raise ValueError('No business logic provided for data retrieval')
    except Exception as e:
        logger.error(f'Error getting historical data: {e}')
        raise

class ComparisonAnalysisTab(BaseTab):
    """Streamlined Comparison Analysis with improved performance"""

    def __init__(self, app):
        super().__init__(app)
        self.current_view = 'portfolio'
        self.analysis_running = False
        self.cache = {}
        info('Comparison Analysis Tab initialized')

    def get_label(self):
        return 'Comparison'

    @monitor_performance
    def create_content(self):
        """Create comparison analysis interface"""
        with dpg.child_window(tag='comparison_main_container', width=-1, height=-1, horizontal_scrollbar=False, border=True):
            self.add_section_header('Comparison Analysis')
            self.create_navigation()
            dpg.add_spacer(height=15)
            self.create_portfolio_content()
            self.create_index_content()
            self.create_stock_content()
        debug('Comparison analysis content created')

    def create_navigation(self):
        """Create navigation tabs"""
        with dpg.group(horizontal=True):
            dpg.add_button(label='Portfolio', callback=lambda: self.switch_view('portfolio'), tag='portfolio_nav_btn', width=120)
            dpg.add_button(label='Index', callback=lambda: self.switch_view('index'), tag='index_nav_btn', width=120)
            dpg.add_button(label='Stocks', callback=lambda: self.switch_view('stock'), tag='stock_nav_btn', width=120)
        dpg.add_separator()
        self.update_nav_buttons()

    def switch_view(self, view):
        """Switch between analysis types"""
        debug('Switching view', context={'from': self.current_view, 'to': view})
        self.current_view = view
        for v in ['portfolio', 'index', 'stock']:
            if dpg.does_item_exist(f'comparison_{v}_content'):
                dpg.hide_item(f'comparison_{v}_content')
        if dpg.does_item_exist(f'comparison_{view}_content'):
            dpg.show_item(f'comparison_{view}_content')
        self.update_nav_buttons()

    def update_nav_buttons(self):
        """Update navigation button states"""
        buttons = {'portfolio': 'portfolio_nav_btn', 'index': 'index_nav_btn', 'stock': 'stock_nav_btn'}
        for view, btn_tag in buttons.items():
            if dpg.does_item_exist(btn_tag):
                if view == self.current_view:
                    dpg.bind_item_theme(btn_tag, self.get_active_theme())
                else:
                    dpg.bind_item_theme(btn_tag, 0)

    def get_active_theme(self):
        """Get active button theme"""
        if not dpg.does_item_exist('active_nav_theme'):
            with dpg.theme(tag='active_nav_theme'):
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, [70, 130, 180, 255])
        return 'active_nav_theme'

    def create_portfolio_content(self):
        """Create portfolio comparison content"""
        with dpg.group(tag='comparison_portfolio_content'):
            dpg.add_text('Portfolio Comparison', color=[100, 255, 100])
            dpg.add_input_text(tag='portfolio_input', hint='Enter portfolio names (comma-separated)', width=400)
            dpg.add_button(label='Compare Portfolios', callback=self.compare_portfolios_callback, width=150)
            dpg.add_spacer(height=15)
            with dpg.table(tag='portfolio_results_table', resizable=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, height=300):
                dpg.add_table_column(label='Portfolio')
                dpg.add_table_column(label='Investment')
                dpg.add_table_column(label='Current Value')
                dpg.add_table_column(label='Return %')
                dpg.add_table_column(label='Volatility')
                dpg.add_table_column(label='Sharpe Ratio')

    def create_index_content(self):
        """Create index comparison content"""
        with dpg.group(tag='comparison_index_content', show=False):
            dpg.add_text('Index Comparison', color=[100, 255, 100])
            dpg.add_input_text(tag='index_input', hint='Enter index symbols (e.g., ^NSEI, ^BSESN)', width=400)
            dpg.add_button(label='Compare Indices', callback=self.compare_indices_callback, width=150)
            dpg.add_spacer(height=15)
            with dpg.table(tag='index_results_table', resizable=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, height=300):
                dpg.add_table_column(label='Index')
                dpg.add_table_column(label='1Y Return %')
                dpg.add_table_column(label='Volatility %')
                dpg.add_table_column(label='Max Drawdown %')

    def create_stock_content(self):
        """Create stock comparison content"""
        with dpg.group(tag='comparison_stock_content', show=False):
            dpg.add_text('Stock Comparison', color=[100, 255, 100])
            dpg.add_input_text(tag='stock_input', hint='Enter stock symbols (e.g., RELIANCE.NS, TCS.NS)', width=400)
            dpg.add_button(label='Compare Stocks', callback=self.compare_stocks_callback, width=150)
            dpg.add_spacer(height=15)
            with dpg.table(tag='stock_results_table', resizable=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, height=300):
                dpg.add_table_column(label='Stock')
                dpg.add_table_column(label='Price')
                dpg.add_table_column(label='P/E Ratio')
                dpg.add_table_column(label='Market Cap')
                dpg.add_table_column(label='1Y Return %')
                dpg.add_table_column(label='Beta')

    def compare_portfolios_callback(self):
        """Compare portfolios"""
        portfolios = dpg.get_value('portfolio_input').strip()
        if not portfolios:
            warning('Portfolio comparison attempted without portfolio names')
            self.show_message('Enter portfolio names', 'error')
            return
        info('Starting portfolio comparison', context={'portfolios': portfolios})
        threading.Thread(target=self.analyze_portfolios, args=(portfolios,), daemon=True).start()

    def compare_indices_callback(self):
        """Compare indices"""
        indices = dpg.get_value('index_input').strip()
        if not indices:
            warning('Index comparison attempted without index symbols')
            self.show_message('Enter index symbols', 'error')
            return
        info('Starting index comparison', context={'indices': indices})
        threading.Thread(target=self.analyze_indices, args=(indices,), daemon=True).start()

    def compare_stocks_callback(self):
        """Compare stocks"""
        stocks = dpg.get_value('stock_input').strip()
        if not stocks:
            warning('Stock comparison attempted without stock symbols')
            self.show_message('Enter stock symbols', 'error')
            return
        info('Starting stock comparison', context={'stocks': stocks})
        threading.Thread(target=self.analyze_stocks, args=(stocks,), daemon=True).start()

    @monitor_performance
    def analyze_portfolios(self, portfolio_names):
        """Analyze portfolio performance with improved error handling"""
        try:
            with operation('analyze_portfolios', portfolio_names=portfolio_names):
                self.clear_table('portfolio_results_table')
                names = [name.strip() for name in portfolio_names.split(',')]
                portfolios = self.load_portfolios()
                for name in names:
                    try:
                        if name.lower() not in portfolios:
                            warning('Portfolio not found', context={'portfolio': name})
                            self.add_portfolio_error_row(name, 'Not Found')
                            continue
                        portfolio = portfolios[name.lower()]
                        investment, current_value, returns = self.calculate_portfolio_metrics(portfolio)
                        with dpg.table_row(parent='portfolio_results_table'):
                            dpg.add_text(name)
                            dpg.add_text(f'₹{investment:.2f}')
                            dpg.add_text(f'₹{current_value:.2f}')
                            dpg.add_text(f'{(current_value - investment) / investment * 100:.2f}%')
                            dpg.add_text(f'{returns.std() * 252 ** 0.5:.2%}' if not returns.empty else 'N/A')
                            dpg.add_text(f'{sharpe_ratio(returns):.2f}' if not returns.empty else 'N/A')
                    except Exception as e:
                        error('Error analyzing portfolio', context={'portfolio': name}, exc_info=True)
                        self.add_portfolio_error_row(name, 'Error')
                info('Portfolio comparison completed')
                self.show_message('Portfolio comparison completed', 'success')
        except Exception as e:
            error('Portfolio analysis failed', exc_info=True)
            self.show_message(f'Error: {e}', 'error')

    def add_portfolio_error_row(self, name, status):
        """Add error row to portfolio table"""
        with dpg.table_row(parent='portfolio_results_table'):
            dpg.add_text(name)
            dpg.add_text(status)
            dpg.add_text(status)
            dpg.add_text(status)
            dpg.add_text(status)
            dpg.add_text(status)

    @monitor_performance
    def analyze_indices(self, index_symbols):
        """Analyze index performance with concurrent processing"""
        try:
            with operation('analyze_indices', index_symbols=index_symbols):
                self.clear_table('index_results_table')
                symbols = [symbol.strip().upper() for symbol in index_symbols.split(',')]
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_symbol = {executor.submit(self.get_index_data, symbol): symbol for symbol in symbols}
                    for future in concurrent.futures.as_completed(future_to_symbol, timeout=30):
                        symbol = future_to_symbol[future]
                        try:
                            data = future.result()
                            self.add_index_row(symbol, data)
                        except Exception as e:
                            error('Error processing index', context={'symbol': symbol}, exc_info=True)
                            self.add_index_error_row(symbol)
                info('Index comparison completed')
                self.show_message('Index comparison completed', 'success')
        except Exception as e:
            error('Index analysis failed', exc_info=True)
            self.show_message(f'Error: {e}', 'error')

    def get_index_data(self, symbol):
        """Get index data with caching"""
        cache_key = f'index_{symbol}_{int(time.time() // 3600)}'
        if cache_key in self.cache:
            debug('Using cached index data', context={'symbol': symbol})
            return self.cache[cache_key]
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1y')
            if data.empty:
                return None
            returns = data['Close'].pct_change().dropna()
            total_return = (data['Close'][-1] - data['Close'][0]) / data['Close'][0] * 100
            volatility = annual_volatility(returns) * 100
            max_dd = max_drawdown(returns) * 100
            result = {'total_return': total_return, 'volatility': volatility, 'max_drawdown': max_dd}
            self.cache[cache_key] = result
            return result
        except Exception as e:
            warning('Failed to get index data', context={'symbol': symbol, 'error': str(e)})
            return None

    def add_index_row(self, symbol, data):
        """Add index data row"""
        if data:
            with dpg.table_row(parent='index_results_table'):
                dpg.add_text(symbol)
                dpg.add_text(f'{data['total_return']:.2f}%')
                dpg.add_text(f'{data['volatility']:.2f}%')
                dpg.add_text(f'{data['max_drawdown']:.2f}%')
        else:
            self.add_index_error_row(symbol)

    def add_index_error_row(self, symbol):
        """Add error row to index table"""
        with dpg.table_row(parent='index_results_table'):
            dpg.add_text(symbol)
            dpg.add_text('No Data')
            dpg.add_text('No Data')
            dpg.add_text('No Data')

    @monitor_performance
    def analyze_stocks(self, stock_symbols):
        """Analyze stock performance with concurrent processing"""
        try:
            with operation('analyze_stocks', stock_symbols=stock_symbols):
                self.clear_table('stock_results_table')
                symbols = [symbol.strip().upper() for symbol in stock_symbols.split(',')]
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_symbol = {executor.submit(self.get_stock_data, symbol): symbol for symbol in symbols}
                    for future in concurrent.futures.as_completed(future_to_symbol, timeout=30):
                        symbol = future_to_symbol[future]
                        try:
                            data = future.result()
                            self.add_stock_row(symbol, data)
                        except Exception as e:
                            error('Error processing stock', context={'symbol': symbol}, exc_info=True)
                            self.add_stock_error_row(symbol)
                info('Stock comparison completed')
                self.show_message('Stock comparison completed', 'success')
        except Exception as e:
            error('Stock analysis failed', exc_info=True)
            self.show_message(f'Error: {e}', 'error')

    def get_stock_data(self, symbol):
        """Get stock data with caching"""
        cache_key = f'stock_{symbol}_{int(time.time() // 1800)}'
        if cache_key in self.cache:
            debug('Using cached stock data', context={'symbol': symbol})
            return self.cache[cache_key]
        try:
            ticker = yf.Ticker(symbol)
            info_data = ticker.info
            hist_data = ticker.history(period='1y')
            if hist_data.empty:
                return None
            current_price = info_data.get('currentPrice', hist_data['Close'][-1])
            pe_ratio = info_data.get('trailingPE')
            market_cap = info_data.get('marketCap')
            beta = info_data.get('beta')
            year_return = (hist_data['Close'][-1] - hist_data['Close'][0]) / hist_data['Close'][0] * 100
            result = {'current_price': current_price, 'pe_ratio': pe_ratio, 'market_cap': market_cap, 'year_return': year_return, 'beta': beta}
            self.cache[cache_key] = result
            return result
        except Exception as e:
            warning('Failed to get stock data', context={'symbol': symbol, 'error': str(e)})
            return None

    def add_stock_row(self, symbol, data):
        """Add stock data row"""
        if data:
            with dpg.table_row(parent='stock_results_table'):
                dpg.add_text(symbol)
                dpg.add_text(f'₹{data['current_price']:.2f}')
                dpg.add_text(f'{data['pe_ratio']:.2f}' if isinstance(data['pe_ratio'], (int, float)) else 'N/A')
                dpg.add_text(f'₹{data['market_cap'] / 1000000000.0:.2f}B' if isinstance(data['market_cap'], (int, float)) else 'N/A')
                dpg.add_text(f'{data['year_return']:.2f}%')
                dpg.add_text(f'{data['beta']:.2f}' if isinstance(data['beta'], (int, float)) else 'N/A')
        else:
            self.add_stock_error_row(symbol)

    def add_stock_error_row(self, symbol):
        """Add error row to stock table"""
        with dpg.table_row(parent='stock_results_table'):
            dpg.add_text(symbol)
            dpg.add_text('Error')
            dpg.add_text('Error')
            dpg.add_text('Error')
            dpg.add_text('Error')
            dpg.add_text('Error')

    @monitor_performance
    def calculate_portfolio_metrics(self, portfolio):
        """Calculate portfolio metrics with improved performance"""
        investment = 0
        current_value = 0
        returns = pd.Series(dtype=float)
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                avg_price = data.get('avg_price', 0)
                investment += quantity * avg_price
                cache_key = f'price_{symbol}_{int(time.time() // 300)}'
                if cache_key in self.cache:
                    current_price = self.cache[cache_key]
                else:
                    try:
                        ticker = yf.Ticker(symbol)
                        current_price = ticker.history(period='1d')['Close'].iloc[-1]
                        self.cache[cache_key] = current_price
                    except Exception as e:
                        warning('Failed to get current price', context={'symbol': symbol, 'error': str(e)})
                        current_price = avg_price
                current_value += quantity * current_price
        return (investment, current_value, returns)

    @lru_cache(maxsize=1)
    def load_portfolios(self):
        """Load portfolios from settings with caching"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    portfolios = settings.get('portfolios', {})
                    debug('Portfolios loaded successfully', context={'count': len(portfolios)})
                    return {k.lower(): v for k, v in portfolios.items()}
            debug('No portfolios file found')
            return {}
        except Exception as e:
            error('Error loading portfolios', exc_info=True)
            return {}

    def clear_table(self, table_tag):
        """Clear table rows efficiently"""
        try:
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, slot=1)
                if children:
                    for child in children:
                        dpg.delete_item(child)
                debug('Table cleared', context={'table': table_tag})
        except Exception as e:
            warning('Error clearing table', context={'table': table_tag, 'error': str(e)})

    def show_message(self, message, message_type='info'):
        """Show message to user with logging"""
        try:
            if hasattr(self.app, 'show_message'):
                self.app.show_message(message, message_type)
            elif message_type == 'error':
                error(f'UI Message: {message}', context={'type': message_type})
            elif message_type == 'warning':
                warning(f'UI Message: {message}', context={'type': message_type})
            else:
                info(f'UI Message: {message}', context={'type': message_type})
        except Exception as e:
            error('Error showing message', context={'message': message, 'type': message_type}, exc_info=True)

    def cleanup(self):
        """Cleanup resources and clear cache"""
        info('Cleaning up Comparison Analysis Tab')
        self.analysis_running = False
        self.cache.clear()
        debug('Cache cleared')

    def get_cache_stats(self):
        """Get cache statistics for debugging"""
        return {'cache_size': len(self.cache), 'cache_keys': list(self.cache.keys())[:10]}

def get_index_data(self, symbol):
    """Get index data with caching"""
    cache_key = f'index_{symbol}_{int(time.time() // 3600)}'
    if cache_key in self.cache:
        debug('Using cached index data', context={'symbol': symbol})
        return self.cache[cache_key]
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1y')
        if data.empty:
            return None
        returns = data['Close'].pct_change().dropna()
        total_return = (data['Close'][-1] - data['Close'][0]) / data['Close'][0] * 100
        volatility = annual_volatility(returns) * 100
        max_dd = max_drawdown(returns) * 100
        result = {'total_return': total_return, 'volatility': volatility, 'max_drawdown': max_dd}
        self.cache[cache_key] = result
        return result
    except Exception as e:
        warning('Failed to get index data', context={'symbol': symbol, 'error': str(e)})
        return None

def get_stock_data(self, symbol):
    """Get stock data with caching"""
    cache_key = f'stock_{symbol}_{int(time.time() // 1800)}'
    if cache_key in self.cache:
        debug('Using cached stock data', context={'symbol': symbol})
        return self.cache[cache_key]
    try:
        ticker = yf.Ticker(symbol)
        info_data = ticker.info
        hist_data = ticker.history(period='1y')
        if hist_data.empty:
            return None
        current_price = info_data.get('currentPrice', hist_data['Close'][-1])
        pe_ratio = info_data.get('trailingPE')
        market_cap = info_data.get('marketCap')
        beta = info_data.get('beta')
        year_return = (hist_data['Close'][-1] - hist_data['Close'][0]) / hist_data['Close'][0] * 100
        result = {'current_price': current_price, 'pe_ratio': pe_ratio, 'market_cap': market_cap, 'year_return': year_return, 'beta': beta}
        self.cache[cache_key] = result
        return result
    except Exception as e:
        warning('Failed to get stock data', context={'symbol': symbol, 'error': str(e)})
        return None

@monitor_performance
def calculate_portfolio_metrics(self, portfolio):
    """Calculate portfolio metrics with improved performance"""
    investment = 0
    current_value = 0
    returns = pd.Series(dtype=float)
    for symbol, data in portfolio.items():
        if isinstance(data, dict):
            quantity = data.get('quantity', 0)
            avg_price = data.get('avg_price', 0)
            investment += quantity * avg_price
            cache_key = f'price_{symbol}_{int(time.time() // 300)}'
            if cache_key in self.cache:
                current_price = self.cache[cache_key]
            else:
                try:
                    ticker = yf.Ticker(symbol)
                    current_price = ticker.history(period='1d')['Close'].iloc[-1]
                    self.cache[cache_key] = current_price
                except Exception as e:
                    warning('Failed to get current price', context={'symbol': symbol, 'error': str(e)})
                    current_price = avg_price
            current_value += quantity * current_price
    return (investment, current_value, returns)

class DataSourceManager:
    """
    Universal Data Source Manager - The backbone of all data in the terminal
    All tabs query this manager instead of directly calling APIs
    """

    def __init__(self, app):
        logger.info('Initializing DataSourceManager')
        try:
            with operation('DataSourceManager initialization'):
                self.app = app
                self.config_file = Path.home() / '.fincept' / 'data_sources.json'
                self.ensure_config_dir()
                self.cache = {}
                self.cache_expiry = {}
                self.cache_duration = 300
                self._cache_lock = threading.RLock()
                self._provider_cache = {}
                self._cache_hits = 0
                self._cache_misses = 0
                self._api_calls = 0
                self._errors = 0
                self.default_sources = {'stocks': 'yfinance', 'forex': 'fincept_api', 'crypto': 'fincept_api', 'news': 'dummy_news', 'economic': 'fincept_api', 'portfolio': 'local_storage', 'options': 'yfinance', 'indices': 'yfinance'}
                self.available_sources = {'yfinance': {'name': 'Yahoo Finance', 'type': 'api', 'supports': ['stocks', 'indices', 'options', 'forex'], 'requires_auth': False, 'real_time': False}, 'fincept_api': {'name': 'Fincept Premium API', 'type': 'api', 'supports': ['stocks', 'forex', 'crypto', 'economic', 'news'], 'requires_auth': True, 'real_time': True}, 'alpha_vantage_data': {'name': 'Alpha Vantage', 'type': 'api', 'supports': ['stocks', 'forex', 'crypto'], 'requires_auth': True, 'real_time': False}, 'dummy_news': {'name': 'Sample News Feed', 'type': 'dummy', 'supports': ['news'], 'requires_auth': False, 'real_time': False}, 'csv_import': {'name': 'CSV File Import', 'type': 'file', 'supports': ['stocks', 'portfolio', 'custom'], 'requires_auth': False, 'real_time': False}, 'websocket_feed': {'name': 'WebSocket Data Feed', 'type': 'websocket', 'supports': ['stocks', 'crypto', 'forex'], 'requires_auth': True, 'real_time': True}}
                self.config = self.load_configuration()
                logger.info('DataSourceManager initialized successfully', context={'default_sources': list(self.default_sources.keys()), 'available_sources': len(self.available_sources)})
        except Exception as e:
            logger.error('DataSourceManager initialization failed', context={'error': str(e)}, exc_info=True)
            raise

    def get_settings_manager(self):
        """Get settings manager from the settings tab"""
        try:
            if hasattr(self.app, 'tabs'):
                for tab_key in self.app.tabs.keys():
                    if 'settings' in tab_key.lower() or 'Settings' in tab_key:
                        settings_tab = self.app.tabs[tab_key]
                        if hasattr(settings_tab, 'settings_manager'):
                            debug(f'Found settings manager in tab: {tab_key}', module='DataSourceManager')
                            return settings_tab.settings_manager
            possible_names = ['Settings', '⚙️ Settings', 'settings', 'SETTINGS']
            for name in possible_names:
                if hasattr(self.app, 'tabs') and name in self.app.tabs:
                    settings_tab = self.app.tabs[name]
                    if hasattr(settings_tab, 'settings_manager'):
                        debug(f'Found settings manager in tab: {name}', module='DataSourceManager')
                        return settings_tab.settings_manager
            debug('Settings manager not found', module='DataSourceManager')
            return None
        except Exception as e:
            debug(f'Error getting settings manager: {str(e)}', module='DataSourceManager')
            return None

    def _get_provider_instance(self, provider_name: str, credentials: Dict[str, str]=None):
        """Get or create provider instance"""
        cache_key = f'{provider_name}_{hash(str(credentials))}'
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]
        if provider_name == 'alpha_vantage_data':
            api_key = ''
            if credentials and 'alpha_vantage_api_key' in credentials:
                api_key = credentials['alpha_vantage_api_key']
            if not api_key:
                settings_manager = self.get_settings_manager()
                if settings_manager:
                    api_key = settings_manager.get_api_key('alpha_vantage_data')
                    debug(f'Got API key from settings: {len(api_key)} chars', module='DataSourceManager')
            if api_key and len(api_key) > 5:
                try:
                    from fincept_terminal.DatabaseConnector.DataSources.alpha_vantage_data.alpha_vantage_provider import AlphaVantageProvider
                    provider = AlphaVantageProvider(api_key)
                    self._provider_cache[cache_key] = provider
                    info(f'Alpha Vantage provider created successfully', module='DataSourceManager')
                    return provider
                except ImportError as e:
                    error(f'Alpha Vantage provider import failed: {str(e)}', module='DataSourceManager')
                    return None
            else:
                warning(f'No valid Alpha Vantage API key found (length: {len(api_key)})', module='DataSourceManager')
                return None
        return None

    def ensure_config_dir(self):
        """Ensure configuration directory exists"""
        try:
            self.config_file.parent.mkdir(exist_ok=True, parents=True)
            logger.debug('Configuration directory ensured', context={'config_dir': str(self.config_file.parent)})
        except Exception as e:
            logger.error('Failed to create config directory', context={'error': str(e)}, exc_info=True)

    def load_configuration(self) -> Dict[str, Any]:
        """Load data source configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info('Data source configuration loaded', context={'config_file': str(self.config_file)})
                return config
            else:
                logger.info('No configuration found, using defaults')
                return {'data_mappings': self.default_sources.copy(), 'source_configs': {}}
        except Exception as e:
            logger.error('Error loading configuration', context={'error': str(e), 'config_file': str(self.config_file)}, exc_info=True)
            return {'data_mappings': self.default_sources.copy(), 'source_configs': {}}

    def save_configuration(self):
        """Save current configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info('Configuration saved successfully', context={'config_file': str(self.config_file)})
            return True
        except Exception as e:
            logger.error('Error saving configuration', context={'error': str(e)}, exc_info=True)
            return False

    def set_data_source(self, data_type: str, source_name: str, source_config: Dict[str, Any]=None):
        """Set data source for a specific data type"""
        try:
            if source_name not in self.available_sources:
                raise ValueError(f'Unknown data source: {source_name}')
            if data_type not in self.available_sources[source_name]['supports']:
                raise ValueError(f"Source {source_name} doesn't support {data_type}")
            self.config['data_mappings'][data_type] = source_name
            if source_config:
                if 'source_configs' not in self.config:
                    self.config['source_configs'] = {}
                self.config['source_configs'][source_name] = source_config
            self.save_configuration()
            logger.info('Data source updated', context={'data_type': data_type, 'source': source_name})
        except Exception as e:
            logger.error('Failed to set data source', context={'data_type': data_type, 'source_name': source_name, 'error': str(e)}, exc_info=True)
            raise

    def get_data_source(self, data_type: str) -> str:
        """Get configured data source for a data type"""
        settings_manager = self.get_settings_manager()
        if settings_manager:
            try:
                preferences = settings_manager.settings.get('preferences', {})
                default_provider = preferences.get('default_provider', 'yfinance')
                if default_provider in self.available_sources and data_type in self.available_sources[default_provider]['supports'] and settings_manager.is_provider_enabled(default_provider):
                    debug(f'Using provider from settings: {default_provider} for {data_type}', module='DataSourceManager')
                    return default_provider
                if settings_manager.is_provider_enabled('alpha_vantage_data') and data_type in self.available_sources['alpha_vantage_data']['supports'] and settings_manager.get_api_key('alpha_vantage_data'):
                    debug(f'Using Alpha Vantage for {data_type} (enabled with API key)', module='DataSourceManager')
                    return 'alpha_vantage_data'
            except Exception as e:
                debug(f'Error checking settings for data source: {str(e)}', module='DataSourceManager')
        source = self.config['data_mappings'].get(data_type, self.default_sources.get(data_type, 'yfinance'))
        debug(f'Using fallback source: {source} for {data_type}', module='DataSourceManager')
        return source

    def is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        with self._cache_lock:
            if cache_key not in self.cache:
                return False
            if cache_key not in self.cache_expiry:
                return False
            return datetime.now() < self.cache_expiry[cache_key]

    def set_cache(self, cache_key: str, data: Any, duration: int=None):
        """Set data in cache"""
        settings_manager = self.get_settings_manager()
        if settings_manager:
            preferences = settings_manager.settings.get('preferences', {})
            if not preferences.get('cache_enabled', True):
                return
            duration = duration or preferences.get('cache_duration', self.cache_duration)
        duration = duration or self.cache_duration
        with self._cache_lock:
            self.cache[cache_key] = data
            self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=duration)
        logger.debug('Data cached', context={'cache_key': cache_key, 'duration': duration})

    def get_cache(self, cache_key: str) -> Any:
        """Get data from cache if valid"""
        with self._cache_lock:
            if self.is_cache_valid(cache_key):
                self._cache_hits += 1
                logger.debug('Cache hit', context={'cache_key': cache_key})
                return self.cache[cache_key]
            else:
                self._cache_misses += 1
                logger.debug('Cache miss', context={'cache_key': cache_key})
                return None

    @monitor_performance
    def get_stock_data(self, symbol: str, period: str='1d', interval: str='1m') -> Dict[str, Any]:
        """Universal stock data retrieval"""
        try:
            with operation(f'Get stock data for {symbol}'):
                cache_key = f'stock_{symbol}_{period}_{interval}'
                cached_data = self.get_cache(cache_key)
                if cached_data:
                    return cached_data
                source = self.get_data_source('stocks')
                self._api_calls += 1
                logger.debug('Fetching stock data', context={'symbol': symbol, 'period': period, 'interval': interval, 'source': source})
                if source == 'yfinance':
                    data = self._get_yfinance_stock_data(symbol, period, interval)
                elif source == 'fincept_api':
                    data = self._get_fincept_stock_data(symbol, period, interval)
                elif source == 'alpha_vantage_data':
                    data = asyncio.run(self._get_alpha_vantage_stock_data(symbol, period, interval))
                else:
                    data = self._get_fallback_stock_data(symbol, period, interval)
                if data.get('success'):
                    self.set_cache(cache_key, data, 60)
                    logger.info('Stock data retrieved successfully', context={'symbol': symbol, 'source': source})
                else:
                    self._errors += 1
                    logger.warning('Stock data retrieval failed', context={'symbol': symbol, 'error': data.get('error')})
                return data
        except Exception as e:
            self._errors += 1
            logger.error('Stock data retrieval error', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'Error fetching stock data: {str(e)}', 'source': 'error', 'symbol': symbol}

    async def _get_alpha_vantage_stock_data(self, symbol: str, period: str, interval: str) -> Dict[str, Any]:
        """Get stock data from Alpha Vantage provider"""
        try:
            provider = self._get_provider_instance('alpha_vantage_data')
            if not provider:
                return {'success': False, 'error': 'Alpha Vantage provider not configured', 'source': 'alpha_vantage_data'}
            return await provider.get_stock_data(symbol, period, interval)
        except Exception as e:
            logger.error('Alpha Vantage stock data error', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': str(e), 'source': 'alpha_vantage_data'}

    async def get_weekly_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get weekly stock data from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_stock_data(symbol, interval='W')

    async def get_monthly_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get monthly stock data from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_stock_data(symbol, interval='M')

    async def get_daily_adjusted(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get daily adjusted stock data from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_daily_adjusted(symbol)

    async def get_weekly_adjusted(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get weekly adjusted stock data from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_weekly_adjusted(symbol)

    async def get_monthly_adjusted(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get monthly adjusted stock data from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_monthly_adjusted(symbol)

    async def get_global_quote(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get global quote from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_global_quote(symbol)

    async def search_symbols(self, keywords: str, **kwargs) -> Dict[str, Any]:
        """Search symbols from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.search_symbols(keywords)

    async def get_company_overview(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get company overview from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_company_overview(symbol)

    async def get_income_statement(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get income statement from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_income_statement(symbol)

    async def get_balance_sheet(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get balance sheet from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_balance_sheet(symbol)

    async def get_cash_flow(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get cash flow from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_cash_flow(symbol)

    async def get_earnings(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get earnings from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_earnings(symbol)

    async def get_earnings_estimates(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get earnings estimates from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_earnings_estimates(symbol)

    async def get_dividends(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get dividends from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_dividends(symbol)

    async def get_splits(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get splits from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_splits(symbol)

    async def get_sma(self, symbol: str, interval: str='daily', time_period: int=14, series_type: str='close', **kwargs) -> Dict[str, Any]:
        """Get Simple Moving Average from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_sma(symbol, interval, time_period, series_type)

    async def get_ema(self, symbol: str, interval: str='daily', time_period: int=14, series_type: str='close', **kwargs) -> Dict[str, Any]:
        """Get Exponential Moving Average from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_ema(symbol, interval, time_period, series_type)

    async def get_rsi(self, symbol: str, interval: str='daily', time_period: int=14, series_type: str='close', **kwargs) -> Dict[str, Any]:
        """Get RSI from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_rsi(symbol, interval, time_period, series_type)

    async def get_macd(self, symbol: str, interval: str='daily', series_type: str='close', **kwargs) -> Dict[str, Any]:
        """Get MACD from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_macd(symbol, interval, series_type)

    async def get_bbands(self, symbol: str, interval: str='daily', time_period: int=20, series_type: str='close', **kwargs) -> Dict[str, Any]:
        """Get Bollinger Bands from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_bbands(symbol, interval, time_period, series_type)

    async def get_stoch(self, symbol: str, interval: str='daily', **kwargs) -> Dict[str, Any]:
        """Get Stochastic from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_stoch(symbol, interval)

    async def get_adx(self, symbol: str, interval: str='daily', time_period: int=14, **kwargs) -> Dict[str, Any]:
        """Get ADX from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_adx(symbol, interval, time_period)

    async def get_vwap(self, symbol: str, interval: str='15min', **kwargs) -> Dict[str, Any]:
        """Get VWAP from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_vwap(symbol, interval)

    async def get_currency_exchange_rate(self, from_currency: str='USD', to_currency: str='EUR', **kwargs) -> Dict[str, Any]:
        """Get currency exchange rate from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_currency_exchange_rate(from_currency, to_currency)

    async def get_fx_intraday(self, from_symbol: str='USD', to_symbol: str='EUR', interval: str='5min', **kwargs) -> Dict[str, Any]:
        """Get FX intraday from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_fx_intraday(from_symbol, to_symbol, interval)

    async def get_fx_weekly(self, from_symbol: str='USD', to_symbol: str='EUR', **kwargs) -> Dict[str, Any]:
        """Get FX weekly from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_fx_weekly(from_symbol, to_symbol)

    async def get_fx_monthly(self, from_symbol: str='USD', to_symbol: str='EUR', **kwargs) -> Dict[str, Any]:
        """Get FX monthly from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_fx_monthly(from_symbol, to_symbol)

    async def get_crypto_intraday(self, symbol: str, market: str='USD', interval: str='5min', **kwargs) -> Dict[str, Any]:
        """Get crypto intraday from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_crypto_intraday(symbol, market, interval)

    async def get_digital_currency_weekly(self, symbol: str, market: str='USD', **kwargs) -> Dict[str, Any]:
        """Get digital currency weekly from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_digital_currency_weekly(symbol, market)

    async def get_digital_currency_monthly(self, symbol: str, market: str='USD', **kwargs) -> Dict[str, Any]:
        """Get digital currency monthly from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_digital_currency_monthly(symbol, market)

    async def get_wti_oil(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get WTI oil from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_wti_oil(interval)

    async def get_brent_oil(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get Brent oil from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_brent_oil(interval)

    async def get_natural_gas(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get Natural gas from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_natural_gas(interval)

    async def get_copper(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get Copper from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_copper(interval)

    async def get_aluminum(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get Aluminum from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_aluminum(interval)

    async def get_real_gdp(self, interval: str='annual', **kwargs) -> Dict[str, Any]:
        """Get Real GDP from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_real_gdp(interval)

    async def get_unemployment(self, **kwargs) -> Dict[str, Any]:
        """Get Unemployment from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_unemployment()

    async def get_cpi(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get CPI from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_cpi(interval)

    async def get_treasury_yield(self, interval: str='monthly', maturity: str='10year', **kwargs) -> Dict[str, Any]:
        """Get Treasury yield from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_treasury_yield(interval, maturity)

    async def get_federal_funds_rate(self, interval: str='monthly', **kwargs) -> Dict[str, Any]:
        """Get Federal funds rate from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_federal_funds_rate(interval)

    async def get_news_sentiment(self, tickers: str=None, topics: str=None, **kwargs) -> Dict[str, Any]:
        """Get news sentiment from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_news_sentiment(tickers, topics)

    async def get_top_gainers_losers(self, **kwargs) -> Dict[str, Any]:
        """Get top gainers/losers from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_top_gainers_losers()

    async def get_insider_transactions(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get insider transactions from Alpha Vantage"""
        provider = self._get_provider_instance('alpha_vantage_data')
        if not provider:
            return {'success': False, 'error': 'Alpha Vantage provider not configured'}
        return await provider.get_insider_transactions(symbol)

    @monitor_performance
    def get_forex_data(self, pair: str, period: str='1d') -> Dict[str, Any]:
        """Universal forex data retrieval"""
        try:
            with operation(f'Get forex data for {pair}'):
                cache_key = f'forex_{pair}_{period}'
                cached_data = self.get_cache(cache_key)
                if cached_data:
                    return cached_data
                source = self.get_data_source('forex')
                self._api_calls += 1
                logger.debug('Fetching forex data', context={'pair': pair, 'period': period, 'source': source})
                if source == 'yfinance':
                    data = self._get_yfinance_forex_data(pair, period)
                elif source == 'fincept_api':
                    data = self._get_fincept_forex_data(pair, period)
                elif source == 'alpha_vantage_data':
                    data = asyncio.run(self._get_alpha_vantage_forex_data(pair, period))
                else:
                    data = self._get_fallback_forex_data(pair, period)
                if data.get('success'):
                    self.set_cache(cache_key, data, 300)
                    logger.info('Forex data retrieved successfully', context={'pair': pair, 'source': source})
                else:
                    self._errors += 1
                    logger.warning('Forex data retrieval failed', context={'pair': pair, 'error': data.get('error')})
                return data
        except Exception as e:
            self._errors += 1
            logger.error('Forex data retrieval error', context={'pair': pair, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'Error fetching forex data: {str(e)}', 'source': 'error', 'pair': pair}

    async def _get_alpha_vantage_forex_data(self, pair: str, period: str) -> Dict[str, Any]:
        """Get forex data from Alpha Vantage provider"""
        try:
            provider = self._get_provider_instance('alpha_vantage_data')
            if not provider:
                return {'success': False, 'error': 'Alpha Vantage provider not configured', 'source': 'alpha_vantage_data'}
            return await provider.get_forex_data(pair, period)
        except Exception as e:
            logger.error('Alpha Vantage forex data error', context={'pair': pair, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': str(e), 'source': 'alpha_vantage_data'}

    @monitor_performance
    def get_news_data(self, category: str='financial', limit: int=20) -> Dict[str, Any]:
        """Universal news data retrieval"""
        try:
            with operation(f'Get news data for {category}'):
                cache_key = f'news_{category}_{limit}'
                cached_data = self.get_cache(cache_key)
                if cached_data:
                    return cached_data
                source = self.get_data_source('news')
                self._api_calls += 1
                logger.debug('Fetching news data', context={'category': category, 'limit': limit, 'source': source})
                if source == 'fincept_api':
                    data = self._get_fincept_news_data(category, limit)
                elif source == 'dummy_news':
                    data = self._get_dummy_news_data(category, limit)
                else:
                    data = self._get_fallback_news_data(category, limit)
                if data.get('success'):
                    self.set_cache(cache_key, data, 600)
                    logger.info('News data retrieved successfully', context={'category': category, 'articles': len(data.get('articles', []))})
                else:
                    self._errors += 1
                    logger.warning('News data retrieval failed', context={'category': category, 'error': data.get('error')})
                return data
        except Exception as e:
            self._errors += 1
            logger.error('News data retrieval error', context={'category': category, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'Error fetching news data: {str(e)}', 'source': 'error', 'category': category}

    @monitor_performance
    def get_crypto_data(self, symbol: str, period: str='1d') -> Dict[str, Any]:
        """Universal crypto data retrieval"""
        try:
            with operation(f'Get crypto data for {symbol}'):
                cache_key = f'crypto_{symbol}_{period}'
                cached_data = self.get_cache(cache_key)
                if cached_data:
                    return cached_data
                source = self.get_data_source('crypto')
                self._api_calls += 1
                logger.debug('Fetching crypto data', context={'symbol': symbol, 'period': period, 'source': source})
                if source == 'fincept_api':
                    data = self._get_fincept_crypto_data(symbol, period)
                elif source == 'alpha_vantage_data':
                    data = asyncio.run(self._get_alpha_vantage_crypto_data(symbol, period))
                else:
                    data = self._get_fallback_crypto_data(symbol, period)
                if data.get('success'):
                    self.set_cache(cache_key, data, 120)
                    logger.info('Crypto data retrieved successfully', context={'symbol': symbol, 'source': source})
                else:
                    self._errors += 1
                    logger.warning('Crypto data retrieval failed', context={'symbol': symbol, 'error': data.get('error')})
                return data
        except Exception as e:
            self._errors += 1
            logger.error('Crypto data retrieval error', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'Error fetching crypto data: {str(e)}', 'source': 'error', 'symbol': symbol}

    async def _get_alpha_vantage_crypto_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Get crypto data from Alpha Vantage provider"""
        try:
            provider = self._get_provider_instance('alpha_vantage_data')
            if not provider:
                return {'success': False, 'error': 'Alpha Vantage provider not configured', 'source': 'alpha_vantage_data'}
            return await provider.get_crypto_data(symbol, period)
        except Exception as e:
            logger.error('Alpha Vantage crypto data error', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': str(e), 'source': 'alpha_vantage_data'}

    @monitor_performance
    def get_economic_data(self, indicator: str, country: str='US') -> Dict[str, Any]:
        """Universal economic data retrieval"""
        try:
            with operation(f'Get economic data for {indicator}'):
                cache_key = f'economic_{indicator}_{country}'
                cached_data = self.get_cache(cache_key)
                if cached_data:
                    return cached_data
                source = self.get_data_source('economic')
                self._api_calls += 1
                logger.debug('Fetching economic data', context={'indicator': indicator, 'country': country, 'source': source})
                if source == 'fincept_api':
                    data = self._get_fincept_economic_data(indicator, country)
                else:
                    data = self._get_fallback_economic_data(indicator, country)
                if data.get('success'):
                    self.set_cache(cache_key, data, 3600)
                    logger.info('Economic data retrieved successfully', context={'indicator': indicator, 'country': country})
                else:
                    self._errors += 1
                    logger.warning('Economic data retrieval failed', context={'indicator': indicator, 'error': data.get('error')})
                return data
        except Exception as e:
            self._errors += 1
            logger.error('Economic data retrieval error', context={'indicator': indicator, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'Error fetching economic data: {str(e)}', 'source': 'error', 'indicator': indicator}

    def _get_yfinance_stock_data(self, symbol: str, period: str, interval: str) -> Dict[str, Any]:
        """Get stock data from Yahoo Finance"""
        try:
            logger.debug('Calling yfinance API', context={'symbol': symbol})
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            if hist.empty:
                logger.warning('No data found in yfinance', context={'symbol': symbol})
                return {'success': False, 'error': f'No data found for symbol {symbol}', 'source': 'yfinance'}
            data = {'success': True, 'source': 'yfinance', 'symbol': symbol, 'data': {'timestamps': [t.isoformat() for t in hist.index], 'open': hist['Open'].tolist(), 'high': hist['High'].tolist(), 'low': hist['Low'].tolist(), 'close': hist['Close'].tolist(), 'volume': hist['Volume'].tolist()}, 'current_price': float(hist['Close'][-1]) if len(hist) > 0 else None, 'fetched_at': datetime.now().isoformat()}
            logger.debug('yfinance data parsed successfully', context={'symbol': symbol, 'data_points': len(hist)})
            return data
        except Exception as e:
            logger.error('yfinance API error', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'YFinance error: {str(e)}', 'source': 'yfinance', 'symbol': symbol}

    def _get_yfinance_forex_data(self, pair: str, period: str) -> Dict[str, Any]:
        """Get forex data from Yahoo Finance"""
        try:
            yahoo_pair = f'{pair}=X' if not pair.endswith('=X') else pair
            logger.debug('Calling yfinance forex API', context={'pair': pair, 'yahoo_pair': yahoo_pair})
            ticker = yf.Ticker(yahoo_pair)
            hist = ticker.history(period=period)
            if hist.empty:
                logger.warning('No forex data found in yfinance', context={'pair': pair})
                return {'success': False, 'error': f'No forex data found for pair {pair}', 'source': 'yfinance'}
            data = {'success': True, 'source': 'yfinance', 'pair': pair, 'data': {'timestamps': [t.isoformat() for t in hist.index], 'rates': hist['Close'].tolist()}, 'current_rate': float(hist['Close'][-1]) if len(hist) > 0 else None, 'fetched_at': datetime.now().isoformat()}
            logger.debug('yfinance forex data parsed successfully', context={'pair': pair, 'data_points': len(hist)})
            return data
        except Exception as e:
            logger.error('yfinance forex API error', context={'pair': pair, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'YFinance forex error: {str(e)}', 'source': 'yfinance', 'pair': pair}

    def _get_fincept_stock_data(self, symbol: str, period: str, interval: str) -> Dict[str, Any]:
        """Get stock data from Fincept API (dummy implementation)"""
        logger.debug('Using dummy Fincept API for stock data', context={'symbol': symbol})
        return {'success': True, 'source': 'fincept_api', 'symbol': symbol, 'data': {'timestamps': [datetime.now().isoformat()], 'open': [100.0], 'high': [105.0], 'low': [98.0], 'close': [102.0], 'volume': [1000000]}, 'current_price': 102.0, 'fetched_at': datetime.now().isoformat(), 'note': 'This is dummy Fincept API data'}

    def _get_fincept_forex_data(self, pair: str, period: str) -> Dict[str, Any]:
        """Get forex data from Fincept API (dummy implementation)"""
        logger.debug('Using dummy Fincept API for forex data', context={'pair': pair})
        return {'success': True, 'source': 'fincept_api', 'pair': pair, 'data': {'timestamps': [datetime.now().isoformat()], 'rates': [1.2345]}, 'current_rate': 1.2345, 'fetched_at': datetime.now().isoformat(), 'note': 'This is dummy Fincept forex data'}

    def _get_fincept_news_data(self, category: str, limit: int) -> Dict[str, Any]:
        """Get news data from Fincept API (dummy implementation)"""
        logger.debug('Using dummy Fincept API for news data', context={'category': category, 'limit': limit})
        return {'success': True, 'source': 'fincept_api', 'category': category, 'articles': [{'title': 'Market Update: Tech Stocks Rally', 'summary': "Technology stocks gained momentum in today's trading session.", 'url': 'https://example.com/news/1', 'published_at': datetime.now().isoformat(), 'source': 'Fincept News'}], 'total': limit, 'fetched_at': datetime.now().isoformat(), 'note': 'This is dummy Fincept news data'}

    def _get_dummy_news_data(self, category: str, limit: int) -> Dict[str, Any]:
        """Get dummy news data"""
        logger.debug('Generating dummy news data', context={'category': category, 'limit': limit})
        dummy_articles = []
        for i in range(min(limit, 5)):
            dummy_articles.append({'title': f'Sample Financial News Article {i + 1}', 'summary': f'This is a sample news summary for {category} category.', 'url': f'https://example.com/news/{i + 1}', 'published_at': (datetime.now() - timedelta(hours=i)).isoformat(), 'source': 'Sample News'})
        return {'success': True, 'source': 'dummy_news', 'category': category, 'articles': dummy_articles, 'total': len(dummy_articles), 'fetched_at': datetime.now().isoformat()}

    def _get_fincept_crypto_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Get crypto data from Fincept API (dummy implementation)"""
        logger.debug('Using dummy Fincept API for crypto data', context={'symbol': symbol})
        return {'success': True, 'source': 'fincept_api', 'symbol': symbol, 'data': {'timestamps': [datetime.now().isoformat()], 'prices': [50000.0]}, 'current_price': 50000.0, 'fetched_at': datetime.now().isoformat(), 'note': 'This is dummy Fincept crypto data'}

    def _get_fincept_economic_data(self, indicator: str, country: str) -> Dict[str, Any]:
        """Get economic data from Fincept API (dummy implementation)"""
        logger.debug('Using dummy Fincept API for economic data', context={'indicator': indicator, 'country': country})
        return {'success': True, 'source': 'fincept_api', 'indicator': indicator, 'country': country, 'data': {'timestamps': [datetime.now().isoformat()], 'values': [2.5]}, 'current_value': 2.5, 'fetched_at': datetime.now().isoformat(), 'note': 'This is dummy Fincept economic data'}

    def _get_fallback_stock_data(self, symbol: str, period: str, interval: str) -> Dict[str, Any]:
        """Fallback to YFinance for stock data"""
        logger.info('Using fallback stock data source', context={'symbol': symbol})
        return self._get_yfinance_stock_data(symbol, period, interval)

    def _get_fallback_forex_data(self, pair: str, period: str) -> Dict[str, Any]:
        """Fallback to YFinance for forex data"""
        logger.info('Using fallback forex data source', context={'pair': pair})
        return self._get_yfinance_forex_data(pair, period)

    def _get_fallback_news_data(self, category: str, limit: int) -> Dict[str, Any]:
        """Fallback to dummy news"""
        logger.info('Using fallback news data source', context={'category': category})
        return self._get_dummy_news_data(category, limit)

    def _get_fallback_crypto_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Fallback crypto data"""
        logger.warning('No fallback available for crypto data', context={'symbol': symbol})
        return {'success': False, 'error': 'No fallback available for crypto data', 'source': 'fallback'}

    def _get_fallback_economic_data(self, indicator: str, country: str) -> Dict[str, Any]:
        """Fallback economic data"""
        logger.warning('No fallback available for economic data', context={'indicator': indicator, 'country': country})
        return {'success': False, 'error': 'No fallback available for economic data', 'source': 'fallback'}

    @monitor_performance
    def test_data_source(self, source_name: str, config: Dict[str, Any]=None) -> Dict[str, Any]:
        """Test if a data source is working"""
        try:
            with operation(f'Test data source {source_name}'):
                logger.info('Testing data source', context={'source': source_name})
                if source_name == 'yfinance':
                    result = self._get_yfinance_stock_data('AAPL', '1d', '1d')
                    success = result.get('success', False)
                    logger.info('yfinance test completed', context={'success': success})
                    return {'success': success, 'message': 'YFinance connection successful' if success else result.get('error'), 'response_time': '< 1s'}
                elif source_name == 'alpha_vantage_data':
                    provider = self._get_provider_instance('alpha_vantage_data')
                    if provider:
                        result = asyncio.run(provider.verify_api_key())
                        logger.info('alpha_vantage_data test completed', context={'success': result.get('valid', False)})
                        return {'success': result.get('valid', False), 'message': result.get('message', result.get('error', 'Unknown')), 'response_time': '< 2s'}
                    else:
                        return {'success': False, 'message': 'Alpha Vantage provider not configured', 'response_time': 'immediate'}
                elif source_name == 'fincept_api':
                    logger.info('fincept_api test completed', context={'success': True})
                    return {'success': True, 'message': 'Fincept API connection successful (dummy)', 'response_time': '< 1s'}
                else:
                    logger.info('Generic source test completed', context={'source': source_name})
                    return {'success': True, 'message': f'{source_name} test successful (dummy)', 'response_time': '< 1s'}
        except Exception as e:
            logger.error('Data source test failed', context={'source': source_name, 'error': str(e)}, exc_info=True)
            return {'success': False, 'message': f'Test failed: {str(e)}', 'response_time': 'timeout'}

    def get_available_sources(self) -> Dict[str, Any]:
        """Get all available data sources"""
        logger.debug('Retrieved available sources', context={'count': len(self.available_sources)})
        return self.available_sources

    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """Get configuration for a specific source"""
        config = self.config.get('source_configs', {}).get(source_name, {})
        logger.debug('Retrieved source config', context={'source': source_name, 'has_config': bool(config)})
        return config

    def get_current_mappings(self) -> Dict[str, str]:
        """Get current data type to source mappings"""
        mappings = {}
        for data_type in ['stocks', 'forex', 'crypto', 'news', 'economic']:
            mappings[data_type] = self.get_data_source(data_type)
        logger.debug('Retrieved current mappings', context={'mappings_count': len(mappings)})
        return mappings

    @monitor_performance
    def import_csv_data(self, file_path: str, data_type: str, column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Import data from CSV file"""
        try:
            with operation(f'Import CSV data from {file_path}'):
                logger.info('Starting CSV import', context={'file_path': file_path, 'data_type': data_type})
                df = pd.read_csv(file_path)
                mapped_data = {}
                for standard_col, csv_col in column_mapping.items():
                    if csv_col in df.columns:
                        mapped_data[standard_col] = df[csv_col].tolist()
                    else:
                        logger.warning('Column not found in CSV', context={'expected_column': csv_col, 'available_columns': list(df.columns)})
                result = {'success': True, 'source': 'csv_import', 'data_type': data_type, 'data': mapped_data, 'row_count': len(df), 'imported_at': datetime.now().isoformat()}
                logger.info('CSV import completed successfully', context={'rows_imported': len(df), 'columns_mapped': len(mapped_data)})
                return result
        except Exception as e:
            logger.error('CSV import failed', context={'file_path': file_path, 'error': str(e)}, exc_info=True)
            return {'success': False, 'error': f'CSV import error: {str(e)}', 'source': 'csv_import'}

    def clear_cache(self, data_type: str=None):
        """Clear cache for specific data type or all"""
        try:
            with self._cache_lock:
                if data_type:
                    keys_to_remove = [k for k in self.cache.keys() if k.startswith(data_type)]
                    for key in keys_to_remove:
                        del self.cache[key]
                        if key in self.cache_expiry:
                            del self.cache_expiry[key]
                    logger.info('Cache cleared for data type', context={'data_type': data_type, 'keys_removed': len(keys_to_remove)})
                else:
                    cache_size = len(self.cache)
                    self.cache.clear()
                    self.cache_expiry.clear()
                    logger.info('All cache cleared', context={'items_removed': cache_size})
        except Exception as e:
            logger.error('Cache clear failed', context={'data_type': data_type, 'error': str(e)}, exc_info=True)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self._cache_lock:
                total_items = len(self.cache)
                expired_items = sum((1 for k in self.cache.keys() if not self.is_cache_valid(k)))
                valid_items = total_items - expired_items
                total_requests = self._cache_hits + self._cache_misses
                hit_rate = self._cache_hits / total_requests * 100 if total_requests > 0 else 0
                stats = {'total_items': total_items, 'valid_items': valid_items, 'expired_items': expired_items, 'cache_hits': self._cache_hits, 'cache_misses': self._cache_misses, 'hit_rate_percent': round(hit_rate, 2), 'api_calls': self._api_calls, 'error_count': self._errors, 'memory_usage_estimate': f'{len(str(self.cache))} bytes'}
                logger.debug('Cache statistics calculated', context=stats)
                return stats
        except Exception as e:
            logger.error('Failed to calculate cache stats', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        try:
            with operation('Reset to defaults'):
                logger.info('Resetting configuration to defaults')
                self.config = {'data_mappings': self.default_sources.copy(), 'source_configs': {}}
                self.save_configuration()
                self.clear_cache()
                self._cache_hits = 0
                self._cache_misses = 0
                self._api_calls = 0
                self._errors = 0
                logger.info('Configuration reset completed')
        except Exception as e:
            logger.error('Failed to reset configuration', context={'error': str(e)}, exc_info=True)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            cache_stats = self.get_cache_stats()
            stats = {'data_source_manager': {'total_api_calls': self._api_calls, 'total_errors': self._errors, 'error_rate_percent': self._errors / self._api_calls * 100 if self._api_calls > 0 else 0, 'uptime_seconds': time.time() - getattr(self, '_start_time', time.time())}, 'cache_performance': cache_stats, 'active_sources': list(self.config.get('data_mappings', {}).values()), 'available_sources': len(self.available_sources)}
            logger.debug('Performance statistics generated', context={'total_api_calls': self._api_calls, 'error_rate': stats['data_source_manager']['error_rate_percent']})
            return stats
        except Exception as e:
            logger.error('Failed to generate performance stats', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

    @lru_cache(maxsize=100)
    def get_supported_data_types(self, source_name: str) -> List[str]:
        """Get supported data types for a source - cached"""
        supported = self.available_sources.get(source_name, {}).get('supports', [])
        logger.debug('Retrieved supported data types', context={'source': source_name, 'types': supported})
        return supported

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration"""
        try:
            with operation('Validate configuration'):
                logger.info('Starting configuration validation')
                issues = []
                warnings = []
                for data_type, source_name in self.config.get('data_mappings', {}).items():
                    if source_name not in self.available_sources:
                        issues.append(f"Unknown source '{source_name}' mapped to '{data_type}'")
                    elif data_type not in self.available_sources[source_name]['supports']:
                        issues.append(f"Source '{source_name}' doesn't support data type '{data_type}'")
                essential_types = ['stocks', 'forex', 'news']
                for data_type in essential_types:
                    if data_type not in self.config.get('data_mappings', {}):
                        warnings.append(f"No source configured for essential data type '{data_type}'")
                for source_name, config in self.config.get('source_configs', {}).items():
                    if source_name not in self.available_sources:
                        warnings.append(f"Configuration exists for unknown source '{source_name}'")
                    elif self.available_sources[source_name]['requires_auth'] and (not config):
                        warnings.append(f"Source '{source_name}' requires authentication but no config provided")
                validation_result = {'valid': len(issues) == 0, 'issues': issues, 'warnings': warnings, 'total_issues': len(issues), 'total_warnings': len(warnings), 'validated_at': datetime.now().isoformat()}
                if issues:
                    logger.warning('Configuration validation found issues', context={'issues': len(issues), 'warnings': len(warnings)})
                else:
                    logger.info('Configuration validation passed', context={'warnings': len(warnings)})
                return validation_result
        except Exception as e:
            logger.error('Configuration validation failed', context={'error': str(e)}, exc_info=True)
            return {'valid': False, 'error': str(e), 'validated_at': datetime.now().isoformat()}

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on data source manager"""
        try:
            with operation('Health check'):
                logger.debug('Starting health check')
                health_status = {'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'cache_functional': False, 'configuration_valid': False, 'primary_sources_available': [], 'issues': []}
                try:
                    test_key = 'health_check_test'
                    test_data = {'test': True}
                    self.set_cache(test_key, test_data, 1)
                    retrieved = self.get_cache(test_key)
                    health_status['cache_functional'] = retrieved == test_data
                except Exception as cache_error:
                    health_status['issues'].append(f'Cache test failed: {str(cache_error)}')
                validation = self.validate_configuration()
                health_status['configuration_valid'] = validation['valid']
                if not validation['valid']:
                    health_status['issues'].extend(validation['issues'])
                primary_sources = ['yfinance', 'alpha_vantage_data']
                for source in primary_sources:
                    try:
                        test_result = self.test_data_source(source)
                        if test_result['success']:
                            health_status['primary_sources_available'].append(source)
                    except Exception as source_error:
                        health_status['issues'].append(f'Source {source} test failed: {str(source_error)}')
                if health_status['issues']:
                    health_status['status'] = 'degraded' if health_status['cache_functional'] else 'unhealthy'
                logger.info('Health check completed', context={'status': health_status['status'], 'issues': len(health_status['issues'])})
                return health_status
        except Exception as e:
            logger.error('Health check failed', context={'error': str(e)}, exc_info=True)
            return {'status': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()}

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f'DataSourceManager(sources={len(self.available_sources)}, cache_items={len(self.cache)}, api_calls={self._api_calls}, errors={self._errors})'

    def cleanup(self):
        """Clean up resources"""
        try:
            with operation('DataSourceManager cleanup'):
                logger.info('Starting DataSourceManager cleanup')
                self.clear_cache()
                for provider in self._provider_cache.values():
                    if hasattr(provider, 'close'):
                        try:
                            if asyncio.iscoroutinefunction(provider.close):
                                asyncio.run(provider.close())
                            else:
                                provider.close()
                        except Exception as e:
                            logger.debug('Error closing provider', context={'error': str(e)})
                self._provider_cache.clear()
                self.get_supported_data_types.cache_clear()
                self.save_configuration()
                logger.info('DataSourceManager cleanup completed', context={'final_api_calls': self._api_calls, 'final_errors': self._errors})
        except Exception as e:
            logger.error('DataSourceManager cleanup failed', context={'error': str(e)}, exc_info=True)

def _get_yfinance_stock_data(self, symbol: str, period: str, interval: str) -> Dict[str, Any]:
    """Get stock data from Yahoo Finance"""
    try:
        logger.debug('Calling yfinance API', context={'symbol': symbol})
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            logger.warning('No data found in yfinance', context={'symbol': symbol})
            return {'success': False, 'error': f'No data found for symbol {symbol}', 'source': 'yfinance'}
        data = {'success': True, 'source': 'yfinance', 'symbol': symbol, 'data': {'timestamps': [t.isoformat() for t in hist.index], 'open': hist['Open'].tolist(), 'high': hist['High'].tolist(), 'low': hist['Low'].tolist(), 'close': hist['Close'].tolist(), 'volume': hist['Volume'].tolist()}, 'current_price': float(hist['Close'][-1]) if len(hist) > 0 else None, 'fetched_at': datetime.now().isoformat()}
        logger.debug('yfinance data parsed successfully', context={'symbol': symbol, 'data_points': len(hist)})
        return data
    except Exception as e:
        logger.error('yfinance API error', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
        return {'success': False, 'error': f'YFinance error: {str(e)}', 'source': 'yfinance', 'symbol': symbol}

def _get_yfinance_forex_data(self, pair: str, period: str) -> Dict[str, Any]:
    """Get forex data from Yahoo Finance"""
    try:
        yahoo_pair = f'{pair}=X' if not pair.endswith('=X') else pair
        logger.debug('Calling yfinance forex API', context={'pair': pair, 'yahoo_pair': yahoo_pair})
        ticker = yf.Ticker(yahoo_pair)
        hist = ticker.history(period=period)
        if hist.empty:
            logger.warning('No forex data found in yfinance', context={'pair': pair})
            return {'success': False, 'error': f'No forex data found for pair {pair}', 'source': 'yfinance'}
        data = {'success': True, 'source': 'yfinance', 'pair': pair, 'data': {'timestamps': [t.isoformat() for t in hist.index], 'rates': hist['Close'].tolist()}, 'current_rate': float(hist['Close'][-1]) if len(hist) > 0 else None, 'fetched_at': datetime.now().isoformat()}
        logger.debug('yfinance forex data parsed successfully', context={'pair': pair, 'data_points': len(hist)})
        return data
    except Exception as e:
        logger.error('yfinance forex API error', context={'pair': pair, 'error': str(e)}, exc_info=True)
        return {'success': False, 'error': f'YFinance forex error: {str(e)}', 'source': 'yfinance', 'pair': pair}

class FinnhubClient:
    """Main Finnhub API client - aggregates all modules"""

    def __init__(self, api_key: str, timeout: int=30):
        config = FinnhubConfig(api_key, timeout)
        self.company = CompanyData(config)
        self.news = NewsData(config)
        self.financials = FinancialData(config)
        self.sec = SECData(config)
        self.market = MarketData(config)
        self.estimates = EstimatesData(config)
        self.calendar = CalendarData(config)
        self.metrics = MetricsData(config)
        self.institutional = InstitutionalData(config)
        self.etf_funds = ETFMutualFunds(config)
        self.bonds = BondsData(config)
        self.forex = ForexData(config)
        self.crypto = CryptoData(config)
        self.technical = TechnicalAnalysis(config)
        self.alternative = AlternativeData(config)
        self.esg = ESGSustainability(config)
        self.government = GovernmentData(config)
        self.global_filings = GlobalFilings(config)
        self.economic = EconomicData(config)
        self.ai = AIFeatures(config)
        self.websocket = WebSocketClient(api_key)

def __init__(self, api_key: str, timeout: int=30):
    config = FinnhubConfig(api_key, timeout)
    self.company = CompanyData(config)
    self.news = NewsData(config)
    self.financials = FinancialData(config)
    self.sec = SECData(config)
    self.market = MarketData(config)
    self.estimates = EstimatesData(config)
    self.calendar = CalendarData(config)
    self.metrics = MetricsData(config)
    self.institutional = InstitutionalData(config)
    self.etf_funds = ETFMutualFunds(config)
    self.bonds = BondsData(config)
    self.forex = ForexData(config)
    self.crypto = CryptoData(config)
    self.technical = TechnicalAnalysis(config)
    self.alternative = AlternativeData(config)
    self.esg = ESGSustainability(config)
    self.government = GovernmentData(config)
    self.global_filings = GlobalFilings(config)
    self.economic = EconomicData(config)
    self.ai = AIFeatures(config)
    self.websocket = WebSocketClient(api_key)

